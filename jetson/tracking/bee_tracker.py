from collections import deque
import cv2
import numpy as np


class BeeTracker:
    """Manages active bee tracks, trajectories, and drawing visuals on video frames."""

    def __init__(self, max_history: int = 30):
        self.max_history = max_history
        # Trajectories mapping: track_id -> deque of (cx, cy)
        self.trajectories = {}

    def update(self, tracks: list):
        """Updates active tracks and records new trajectory centers.

        Args:
            tracks (list): List of track dicts from InferEngine.

        Returns:
            list: The updated tracks list with trajectory histories attached.
        """
        current_ids = set()
        for trk in tracks:
            tid = trk["id"]
            cx, cy = trk["center"]
            current_ids.add(tid)

            if tid not in self.trajectories:
                self.trajectories[tid] = deque(maxlen=self.max_history)
            self.trajectories[tid].append((cx, cy))
            trk["trajectory"] = list(self.trajectories[tid])

        # Cleanup trajectories for lost tracks
        lost_ids = set(self.trajectories.keys()) - current_ids
        for tid in lost_ids:
            del self.trajectories[tid]

        return tracks

    def draw_tracks(self, frame: np.ndarray, tracks: list, show_trajectory: bool = True):
        """Draws bounding boxes, IDs, and trajectory tail lines on frame.

        Args:
            frame (np.ndarray): OpenCV image frame.
            tracks (list): Active tracks.
            show_trajectory (bool): Whether to draw historical trajectory lines.
        """
        overlay = frame.copy()

        for trk in tracks:
            tid = trk["id"]
            x1, y1, x2, y2 = map(int, trk["bbox"])
            conf = trk["conf"]

            # Choose color based on ID
            color_hue = (tid * 37) % 180
            color_bgr = tuple(map(int, cv2.cvtColor(np.uint8([[[color_hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]))

            # 1. Draw Bounding Box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 2)

            # 2. Draw ID & Conf Tag
            label = f"Bee #{tid} ({conf:.2f})"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - 20), (x1 + w + 4, y1), color_bgr, -1)
            cv2.putText(frame, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

            # 3. Draw Trajectory Line
            if show_trajectory and tid in self.trajectories:
                pts = list(self.trajectories[tid])
                for i in range(1, len(pts)):
                    if pts[i - 1] is None or pts[i] is None:
                        continue
                    thickness = int(np.sqrt(self.max_history / float(i + 1)) * 1.5)
                    cv2.line(frame, pts[i - 1], pts[i], color_bgr, max(1, thickness))

        return frame
