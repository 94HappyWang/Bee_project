import os
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QStatusBar, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from hmi.styles import MUJI_THEME_QSS
from hmi.page_dashboard import DashboardPage
from hmi.page_capture import CapturePage
from hmi.page_settings import SettingsPage
from hmi.worker_thread import VideoInferenceWorker
from utils.config import ConfigManager
from utils.logger import LoggerManager

logger = logging.getLogger("MainWindow")


class MainWindow(QMainWindow):
    """Main HMI Window combining Dashboard, Capture, and Settings pages via QStackedWidget."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("蜜蜂進出視覺辨識與計數系統 - Module 2 HMI")
        self.resize(1280, 768)

        # Managers
        self.config_manager = ConfigManager()
        self.logger_manager = LoggerManager(
            db_path=self.config_manager.get("db_path", "data/bee_logs.sqlite"),
            csv_path=self.config_manager.get("csv_path", "data/bee_logs.csv")
        )

        self.worker_thread = None

        # Build UI
        self._init_ui()
        self.setStyleSheet(MUJI_THEME_QSS)

        # Do NOT auto-start worker thread on open. Wait for user to click Start.
        self.status_bar.showMessage("系統就緒 - 請點選 [▶ 啟動推論] 按鈕開始視訊串流與進出計數 🟢")

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ==========================================
        # 1. TOP HEADER NAVIGATION BAR (3 TABS)
        # ==========================================
        header_bar = QWidget()
        header_bar.setObjectName("HeaderBar")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(15, 8, 15, 8)
        header_layout.setSpacing(10)

        title_lbl = QLabel("🐝 蜜蜂進出視覺辨識與計數系統")
        title_lbl.setObjectName("TitleLabel")
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        # Nav Buttons (3 Pages)
        self.btn_nav_dash = QPushButton("📊 即時監控主頁")
        self.btn_nav_dash.setProperty("class", "NavBtn")
        self.btn_nav_dash.setCheckable(True)
        self.btn_nav_dash.setChecked(True)

        self.btn_nav_cap = QPushButton("📷 現場拍攝採樣")
        self.btn_nav_cap.setProperty("class", "NavBtn")
        self.btn_nav_cap.setCheckable(True)

        self.btn_nav_set = QPushButton("⚙️ 標記與系統設定")
        self.btn_nav_set.setProperty("class", "NavBtn")
        self.btn_nav_set.setCheckable(True)

        header_layout.addWidget(self.btn_nav_dash)
        header_layout.addWidget(self.btn_nav_cap)
        header_layout.addWidget(self.btn_nav_set)

        root_layout.addWidget(header_bar)

        # ==========================================
        # 2. CENTRAL QSTACKEDWIDGET (3 PAGES)
        # ==========================================
        self.stacked_widget = QStackedWidget()

        # Instantiate Pages
        self.page_dashboard = DashboardPage()
        self.page_capture = CapturePage(self.config_manager)
        self.page_settings = SettingsPage(self.config_manager)

        self.stacked_widget.addWidget(self.page_dashboard)  # Index 0
        self.stacked_widget.addWidget(self.page_capture)    # Index 1
        self.stacked_widget.addWidget(self.page_settings)   # Index 2

        root_layout.addWidget(self.stacked_widget, stretch=1)

        # ==========================================
        # 3. BOTTOM STATUS BAR
        # ==========================================
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Connect Navigation
        self.btn_nav_dash.clicked.connect(self.show_dashboard_page)
        self.btn_nav_cap.clicked.connect(self.show_capture_page)
        self.btn_nav_set.clicked.connect(self.show_settings_page)

        self.page_dashboard.switch_to_settings.connect(self.show_settings_page)
        self.page_settings.switch_to_dashboard.connect(self.show_dashboard_page)

        # Connect Dashboard Controls
        self.page_dashboard.toggle_run_requested.connect(self.toggle_worker_run)
        self.page_dashboard.stop_reset_requested.connect(self.stop_and_reset_counts)

        self.page_settings.settings_saved.connect(self.apply_new_settings)

    def show_dashboard_page(self):
        self.stacked_widget.setCurrentIndex(0)
        self.btn_nav_dash.setChecked(True)
        self.btn_nav_cap.setChecked(False)
        self.btn_nav_set.setChecked(False)

    def show_capture_page(self):
        self.stacked_widget.setCurrentIndex(1)
        self.btn_nav_dash.setChecked(False)
        self.btn_nav_cap.setChecked(True)
        self.btn_nav_set.setChecked(False)

    def show_settings_page(self):
        self.stacked_widget.setCurrentIndex(2)
        self.btn_nav_dash.setChecked(False)
        self.btn_nav_cap.setChecked(False)
        self.btn_nav_set.setChecked(True)

    def init_worker_thread(self):
        """Prepares the VideoInferenceWorker thread instance."""
        line_a, line_b = self.config_manager.get_lines()

        self.worker_thread = VideoInferenceWorker(
            source=self.config_manager.get("camera_source", "0"),
            model_path=self.config_manager.get("model_path", "best.pt"),
            conf_thresh=float(self.config_manager.get("conf_threshold", 0.3)),
            line_a=line_a,
            line_b=line_b,
            max_crossing_time=float(self.config_manager.get("max_crossing_time", 5.0))
        )

        # Connect Signals
        self.worker_thread.frame_processed.connect(self.handle_frame_processed)
        self.worker_thread.count_triggered.connect(self.handle_count_triggered)
        self.worker_thread.status_changed.connect(self.status_bar.showMessage)

    def toggle_worker_run(self):
        """Toggles between Start/Resume and Pause for worker thread."""
        if self.worker_thread is None:
            self.init_worker_thread()

        if not self.worker_thread.isRunning():
            self.worker_thread.start()
            self.page_dashboard.set_running_state(is_running=True, is_paused=False)
        elif self.worker_thread.is_paused:
            self.worker_thread.resume_inference()
            self.page_dashboard.set_running_state(is_running=True, is_paused=False)
        else:
            self.worker_thread.pause_inference()
            self.page_dashboard.set_running_state(is_running=True, is_paused=True)

    def handle_frame_processed(self, frame, stats):
        """Dispatches processed frames to active page canvas."""
        idx = self.stacked_widget.currentIndex()
        if idx == 0:
            self.page_dashboard.update_frame(frame, stats)
        elif idx == 1:
            self.page_capture.update_preview_frame(frame)
        elif idx == 2:
            self.page_settings.update_preview_frame(frame)

    def handle_count_triggered(self, event_data):
        """Logs IN/OUT event asynchronously to SQLite/CSV and updates activity rate indicator."""
        logged_ev = self.logger_manager.log_event(
            bee_id=event_data["bee_id"],
            direction=event_data["direction"],
            duration=event_data["duration"]
        )
        self.page_dashboard.register_event_for_rate(logged_ev)

    def stop_and_reset_counts(self):
        """Stops inference stream and resets today's counts upon user confirmation."""
        reply = QMessageBox.question(
            self, "確認停止並重置", "確定要停止推論並重置清空今日的蜜蜂進出累計計數嗎？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.stop_inference()
            if self.worker_thread:
                self.worker_thread.reset_counts()

            self.logger_manager.reset_today_counts()
            self.page_dashboard.set_running_state(is_running=False, is_paused=False)
            self.status_bar.showMessage("⏹ 已停止推論並完成今日計數歸零重置 🔴", 5000)

    def apply_new_settings(self, new_config):
        """Applies newly saved settings to worker thread dynamically."""
        if self.worker_thread:
            self.worker_thread.set_lines(new_config["line_a"], new_config["line_b"])
            self.worker_thread.reload_model(new_config["model_path"], new_config["conf_threshold"])
        self.status_bar.showMessage("✅ 已即時套用新劃線與模型設定！", 5000)

    def closeEvent(self, event):
        """Gracefully terminates worker thread on exit."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop_inference()
            self.worker_thread.wait(2000)
        event.accept()
