import time
import logging
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from utils.infer_engine import InferEngine
from tracking.bee_tracker import BeeTracker
from tracking.line_counter import LineCounter

logger = logging.getLogger("VideoWorker")


class VideoInferenceWorker(QThread):
    """Worker QThread running video capture, YOLO inference, ByteTrack, and Dual-Line counting."""

    # Signals
    frame_processed = pyqtSignal(np.ndarray, dict)
    count_triggered = pyqtSignal(dict)
    status_changed = pyqtSignal(str)

    def __init__(self, source="0", model_path="yolo26s.pt", conf_thresh=0.3,
                 line_a=None, line_b=None, max_crossing_time=5.0):
        super().__init__()
        self.source = source
        self.model_path = model_path
        self.conf_thresh = conf_thresh

        # Components
        self.infer_engine = InferEngine(model_path=model_path, conf_thresh=conf_thresh)
        self.bee_tracker = BeeTracker()
        self.line_counter = LineCounter(line_a=line_a, line_b=line_b, max_crossing_time=max_crossing_time)

        # Controls
        self.is_running = False
        self.is_paused = False

        # FPS calculation
        self.fps = 0.0
        self.frame_count = 0
        self.fps_start_time = time.time()

    def run(self):
        """Main execution loop of the worker thread."""
        self.is_running = True
        self.is_paused = False

        # Parse source (int for camera index, str for video file/RTSP)
        src_val = int(self.source) if str(self.source).isdigit() else self.source
        cap = cv2.VideoCapture(src_val)

        if not cap.isOpened():
            logger.error(f"Failed to open video source: {self.source}")
            self.status_changed.emit(f"Error: Cannot open video source '{self.source}'")
            self.is_running = False
            return

        self.status_changed.emit("Status: Inferencing Active 🟢")
        self.fps_start_time = time.time()
        self.frame_count = 0

        while self.is_running:
            if self.is_paused:
                self.msleep(50)
                continue

            ret, frame = cap.read()
            if not ret:
                # If video file reached end, loop back to start
                if isinstance(src_val, str) and not src_val.startswith("rtsp://"):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    logger.warning("Video stream lost or ended.")
                    self.status_changed.emit("Status: Stream Disconnected 🔴")
                    break

            # 1. Run YOLO Detection & ByteTrack
            tracks = self.infer_engine.track_frame(frame, persist=True)

            # 2. Update Trajectories
            tracks = self.bee_tracker.update(tracks)

            # 3. Update Dual-Line Counter
            events = self.line_counter.update(tracks)

            # 4. Emit any IN/OUT crossing events
            for ev in events:
                self.count_triggered.emit(ev)

            # 5. Draw Visual Overlay (Boxes, Trajectories, Lines)
            drawn_frame = frame.copy()
            drawn_frame = self.bee_tracker.draw_tracks(drawn_frame, tracks)
            drawn_frame = self.line_counter.draw_lines(drawn_frame)

            # 6. Calculate FPS
            self.frame_count += 1
            elapsed = time.time() - self.fps_start_time
            if elapsed >= 1.0:
                self.fps = self.frame_count / elapsed
                self.frame_count = 0
                self.fps_start_time = time.time()

            # Compile stats
            counts = self.line_counter.get_counts()
            stats = {
                "in_count": counts["in_count"],
                "out_count": counts["out_count"],
                "net_count": counts["net_count"],
                "fps": round(self.fps, 1),
                "active_tracks": len(tracks)
            }

            # 7. Emit frame for PyQt GUI rendering
            self.frame_processed.emit(drawn_frame, stats)

            # Cap frame rate slightly to avoid excessive CPU usage
            self.msleep(10)

        cap.release()
        self.status_changed.emit("Status: Stopped ⏹")

    def pause_inference(self):
        self.is_paused = True
        self.status_changed.emit("Status: Paused ⏸")

    def resume_inference(self):
        self.is_paused = False
        self.status_changed.emit("Status: Inferencing Active 🟢")

    def stop_inference(self):
        self.is_running = False

    def reset_counts(self):
        self.line_counter.reset_counts()

    def set_lines(self, line_a, line_b):
        self.line_counter.set_lines(line_a, line_b)

    def reload_model(self, model_path, conf_thresh):
        self.model_path = model_path
        self.conf_thresh = conf_thresh
        self.infer_engine.conf_thresh = conf_thresh
        self.infer_engine.load_model(model_path)
