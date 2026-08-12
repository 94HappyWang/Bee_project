import sys
import os
import cv2
import logging
from PyQt5.QtWidgets import QApplication

from hmi.main_window import MainWindow
from utils.config import ConfigManager
from utils.test_video import create_sample_bee_corridor_video

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("BeeMain")


def ensure_video_source_valid():
    """Checks if default camera is available. If not, generates a synthetic sample video."""
    cfg = ConfigManager()
    src = cfg.get("camera_source", "0")

    # Check if webcam index 0 is valid
    if str(src).isdigit():
        cap = cv2.VideoCapture(int(src))
        if not cap.isOpened():
            cap.release()
            logger.warning(f"Camera index {src} not found on this machine! Generating sample test video...")
            sample_path = create_sample_bee_corridor_video()
            cfg.set("camera_source", sample_path)
        else:
            cap.release()


def main():
    logger.info("Starting Bee Entrance HMI Application (Module 2)...")
    ensure_video_source_valid()

    app = QApplication(sys.argv)
    app.setApplicationName("Beehive Entrance Visual Recognition System")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    # Ensure current working directory is project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    main()
