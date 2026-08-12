import os
import time
import glob
import cv2
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton,
    QDoubleSpinBox, QLineEdit, QFileDialog, QGroupBox, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

from hmi.video_widget import VideoCanvasWidget
from utils.config import ConfigManager


class CapturePage(QWidget):
    """Page 3: Live Field Dataset Photo Capture & Sampling Page."""

    switch_to_dashboard = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager

        self.latest_raw_frame = None
        self.is_auto_capturing = False
        self.session_capture_count = 0
        self.last_capture_time = 0.0

        # Snapshot folder default
        default_dir = os.path.abspath(os.path.join("data", "captured_dataset"))
        self.save_dir = self.config_manager.get("capture_save_dir", default_dir)
        os.makedirs(self.save_dir, exist_ok=True)

        self._init_ui()

        # Timer for auto-capture countdown and trigger
        self.capture_timer = QTimer(self)
        self.capture_timer.setInterval(100)  # Check every 100ms
        self.capture_timer.timeout.connect(self._check_auto_capture)

        self.update_folder_count()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(14)

        # ==========================================
        # LEFT PANEL: 100% Live Stream Preview Canvas
        # ==========================================
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.video_canvas = VideoCanvasWidget(is_calibration_mode=False)
        left_layout.addWidget(self.video_canvas, stretch=1)

        # ==========================================
        # RIGHT PANEL: Capture Controls & Folder Stats
        # ==========================================
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)

        # Title
        lbl_title = QLabel("📷 現場訓練集影像採樣與攝影")
        lbl_title.setFont(QFont("Microsoft JhengHei UI", 15, QFont.Bold))
        lbl_title.setStyleSheet("color: #7F2424;")
        right_layout.addWidget(lbl_title)

        # Section 1: Capture Statistics Cards (2 Cards)
        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(8)

        self.card_session = self._create_card("本次連拍張數", "0 張", "ValSession")
        self.card_folder = self._create_card("資料夾總照片數", "0 張", "ValFolder")

        stats_grid.addWidget(self.card_session)
        stats_grid.addWidget(self.card_folder)
        right_layout.addLayout(stats_grid)

        # Section 2: Timer & Folder Settings GroupBox
        grp_settings = QGroupBox("⚙️ 定時拍攝與路徑設定")
        vbox_set = QVBoxLayout(grp_settings)
        vbox_set.setSpacing(10)

        # Interval SpinBox
        row_interval = QHBoxLayout()
        lbl_int = QLabel("拍攝時間間隔 (秒):")
        lbl_int.setStyleSheet("color: #78726A; font-size: 15px;")
        self.spn_interval = QDoubleSpinBox()
        self.spn_interval.setRange(0.5, 60.0)
        self.spn_interval.setValue(2.0)
        self.spn_interval.setSingleStep(0.5)
        row_interval.addWidget(lbl_int)
        row_interval.addStretch()
        row_interval.addWidget(self.spn_interval)
        vbox_set.addLayout(row_interval)

        # Save Directory Path
        lbl_dir = QLabel("照片儲存目錄:")
        lbl_dir.setStyleSheet("color: #78726A; font-size: 15px;")
        vbox_set.addWidget(lbl_dir)

        row_dir = QHBoxLayout()
        self.txt_save_dir = QLineEdit(self.save_dir)
        self.btn_browse_dir = QPushButton("📁 選擇...")
        row_dir.addWidget(self.txt_save_dir)
        row_dir.addWidget(self.btn_browse_dir)
        vbox_set.addLayout(row_dir)

        # Countdown status label
        self.lbl_countdown = QLabel("狀態: 等待啟動採樣")
        self.lbl_countdown.setAlignment(Qt.AlignCenter)
        self.lbl_countdown.setFont(QFont("Microsoft JhengHei UI", 15, QFont.Bold))
        self.lbl_countdown.setStyleSheet("color: #78726A; margin-top: 5px;")
        vbox_set.addWidget(self.lbl_countdown)

        right_layout.addWidget(grp_settings)

        right_layout.addStretch()

        # Section 3: Capture Action Control Buttons
        ctrl_box = QFrame()
        ctrl_box.setProperty("class", "MetricCard")
        vbox_ctrl = QVBoxLayout(ctrl_box)
        vbox_ctrl.setSpacing(8)

        self.btn_single_snap = QPushButton("📸 立即手動拍攝單張")
        self.btn_single_snap.setProperty("class", "ActionBtn")

        self.btn_toggle_auto = QPushButton("▶ 開始自動定時採樣")
        self.btn_toggle_auto.setProperty("class", "ActionBtn")
        self.btn_toggle_auto.setStyleSheet("background-color: #3B7A57;")

        self.btn_open_folder = QPushButton("📂 開啟照片儲存資料夾")
        self.btn_open_folder.setProperty("class", "ActionBtn")

        vbox_ctrl.addWidget(self.btn_single_snap)
        vbox_ctrl.addWidget(self.btn_toggle_auto)
        vbox_ctrl.addWidget(self.btn_open_folder)

        right_layout.addWidget(ctrl_box)

        # Assemble Main Layout
        main_layout.addLayout(left_layout, stretch=7)
        main_layout.addLayout(right_layout, stretch=3)

        # Connect signals
        self.btn_browse_dir.clicked.connect(self._browse_save_dir)
        self.btn_single_snap.clicked.connect(self.take_single_snapshot)
        self.btn_toggle_auto.clicked.connect(self.toggle_auto_capture)
        self.btn_open_folder.clicked.connect(self._open_folder_in_explorer)

    def _create_card(self, title, init_val, val_obj_name):
        card = QFrame()
        card.setProperty("class", "MetricCard")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(10, 8, 10, 8)

        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "MetricTitle")

        lbl_val = QLabel(init_val)
        lbl_val.setObjectName(val_obj_name)
        lbl_val.setFont(QFont("Microsoft JhengHei UI", 16, QFont.Bold))
        lbl_val.setStyleSheet("color: #7F2424; margin-top: 4px;")

        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_val)
        return card

    def update_preview_frame(self, frame: np.ndarray):
        """Receives live frame from worker thread for preview and snapshot."""
        if frame is not None:
            self.latest_raw_frame = frame.copy()
            self.video_canvas.set_frame(frame)

    def _browse_save_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "選擇照片儲存目錄", self.save_dir)
        if dir_path:
            self.save_dir = dir_path
            self.txt_save_dir.setText(dir_path)
            self.config_manager.set("capture_save_dir", dir_path)
            self.update_folder_count()

    def update_folder_count(self):
        """Counts total JPG/PNG images in the current save directory."""
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        jpgs = glob.glob(os.path.join(self.save_dir, "*.jpg")) + glob.glob(os.path.join(self.save_dir, "*.png"))
        count = len(jpgs)
        self.card_folder.findChild(QLabel, "ValFolder").setText(f"{count} 張")

    def take_single_snapshot(self):
        """Captures a single high-quality frame image to disk."""
        if self.latest_raw_frame is None:
            QMessageBox.warning(self, "警告", "目前無有效相機畫面，無法拍攝！")
            return

        target_dir = self.txt_save_dir.text().strip()
        os.makedirs(target_dir, exist_ok=True)

        now_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"bee_sample_{now_str}.jpg"
        filepath = os.path.join(target_dir, filename)

        try:
            # Save raw BGR frame as high quality JPEG (95% compression quality)
            cv2.imwrite(filepath, self.latest_raw_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            self.session_capture_count += 1
            self.card_session.findChild(QLabel, "ValSession").setText(f"{self.session_capture_count} 張")
            self.update_folder_count()
            self.lbl_countdown.setText(f"已拍攝: {filename}")
            self.lbl_countdown.setStyleSheet("color: #3B7A57; font-weight: bold;")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"無法儲存照片: {e}")

    def toggle_auto_capture(self):
        """Starts or stops automatic timed capturing."""
        if not self.is_auto_capturing:
            self.is_auto_capturing = True
            self.last_capture_time = time.time()
            self.capture_timer.start()
            self.btn_toggle_auto.setText("⏹ 停止自動連拍")
            self.btn_toggle_auto.setStyleSheet("background-color: #BD463B;")
            self.lbl_countdown.setText("自動連拍運行中 🟢")
            self.lbl_countdown.setStyleSheet("color: #3B7A57; font-weight: bold;")
        else:
            self.is_auto_capturing = False
            self.capture_timer.stop()
            self.btn_toggle_auto.setText("▶ 開始自動定時採樣")
            self.btn_toggle_auto.setStyleSheet("background-color: #3B7A57;")
            self.lbl_countdown.setText("狀態: 已停止採樣 ⏹")
            self.lbl_countdown.setStyleSheet("color: #78726A; font-weight: bold;")

    def _check_auto_capture(self):
        """Timer callback checking whether interval seconds have elapsed."""
        if not self.is_auto_capturing:
            return

        interval = self.spn_interval.value()
        now = time.time()
        elapsed = now - self.last_capture_time
        remaining = max(0.0, interval - elapsed)

        self.lbl_countdown.setText(f"下次拍攝倒數: {remaining:.1f} 秒")

        if elapsed >= interval:
            self.take_single_snapshot()
            self.last_capture_time = time.time()

    def _open_folder_in_explorer(self):
        target_dir = self.txt_save_dir.text().strip()
        os.makedirs(target_dir, exist_ok=True)
        try:
            os.startfile(target_dir)
        except Exception as e:
            QMessageBox.warning(self, "無法開啟", f"無法直接打開目錄: {e}")
