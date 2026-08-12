import time
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel, QPushButton, QProgressBar, QGridLayout
)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal

from hmi.video_widget import VideoCanvasWidget


class DashboardPage(QWidget):
    """Page 1: Main Real-time Video Monitoring & High-Level Bee Activity Statistics Dashboard Page."""

    # Control Signals
    toggle_run_requested = pyqtSignal()
    stop_reset_requested = pyqtSignal()
    switch_to_settings = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recent_events_window = []  # Timestamps of recent events for rate calculation
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(14)

        # ==========================================
        # LEFT PANEL: 100% Dedicated Live Video Canvas
        # ==========================================
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # Video Canvas (Aspect Ratio Preserved & Fully Responsive)
        self.video_canvas = VideoCanvasWidget(is_calibration_mode=False)
        left_layout.addWidget(self.video_canvas, stretch=1)

        # ==========================================
        # RIGHT PANEL: Activity Statistics & Action Controls
        # ==========================================
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)

        # Section 1: Main Metric Cards (2x2 Grid)
        metrics_grid1 = QHBoxLayout()
        metrics_grid1.setSpacing(8)
        self.card_in = self._create_card("今日累計進入 (IN)", "0 隻", "ValIn")
        self.card_out = self._create_card("今日累計外出 (OUT)", "0 隻", "ValOut")
        metrics_grid1.addWidget(self.card_in)
        metrics_grid1.addWidget(self.card_out)

        metrics_grid2 = QHBoxLayout()
        metrics_grid2.setSpacing(8)
        self.card_net = self._create_card("蜂巢淨估算 (NET)", "0 隻", "ValNet")
        self.card_fps = self._create_card("推論速度 (FPS)", "0.0", "ValFps")
        metrics_grid2.addWidget(self.card_net)
        metrics_grid2.addWidget(self.card_fps)

        right_layout.addLayout(metrics_grid1)
        right_layout.addLayout(metrics_grid2)

        # Section 2: Real-time Activity Rate & Active Tracks
        activity_box = QFrame()
        activity_box.setProperty("class", "MetricCard")
        vbox_act = QVBoxLayout(activity_box)
        vbox_act.setSpacing(8)

        lbl_act_title = QLabel("📊 蜂群動態與流量速率指標")
        lbl_act_title.setFont(QFont("Microsoft JhengHei UI", 15, QFont.Bold))
        lbl_act_title.setStyleSheet("color: #7F2424;")
        vbox_act.addWidget(lbl_act_title)

        # Active tracked bees count
        row_active = QHBoxLayout()
        lbl_active_name = QLabel("目前走廊追蹤蜜蜂數:")
        lbl_active_name.setStyleSheet("color: #78726A; font-size: 15px;")
        self.lbl_active_val = QLabel("0 隻")
        self.lbl_active_val.setFont(QFont("Microsoft JhengHei UI", 18, QFont.Bold))
        self.lbl_active_val.setStyleSheet("color: #2D2B2A;")
        row_active.addWidget(lbl_active_name)
        row_active.addStretch()
        row_active.addWidget(self.lbl_active_val)
        vbox_act.addLayout(row_active)

        # 1-min activity rate
        row_rate = QHBoxLayout()
        lbl_rate_name = QLabel("近 1 分鐘進出頻率:")
        lbl_rate_name.setStyleSheet("color: #78726A; font-size: 15px;")
        self.lbl_rate_val = QLabel("0 次/分")
        self.lbl_rate_val.setFont(QFont("Microsoft JhengHei UI", 18, QFont.Bold))
        self.lbl_rate_val.setStyleSheet("color: #C48227;")
        row_rate.addWidget(lbl_rate_name)
        row_rate.addStretch()
        row_rate.addWidget(self.lbl_rate_val)
        vbox_act.addLayout(row_rate)

        # Activity level progress bar
        lbl_level_name = QLabel("蜂群活動強度 (Activity Level):")
        lbl_level_name.setStyleSheet("color: #78726A; font-size: 15px; margin-top: 5px;")
        vbox_act.addWidget(lbl_level_name)

        self.bar_activity = QProgressBar()
        self.bar_activity.setRange(0, 100)
        self.bar_activity.setValue(0)
        self.bar_activity.setTextVisible(False)
        self.bar_activity.setStyleSheet("""
            QProgressBar {
                border: 1px solid #D8D2C7;
                border-radius: 9px;
                background-color: #EAE6DD;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3B7A57, stop:0.5 #C48227, stop:1 #BD463B);
                border-radius: 7px;
            }
        """)
        vbox_act.addWidget(self.bar_activity)

        self.lbl_activity_status = QLabel("狀態: 平穩 / 低活動量")
        self.lbl_activity_status.setAlignment(Qt.AlignCenter)
        self.lbl_activity_status.setFont(QFont("Microsoft JhengHei UI", 15, QFont.Bold))
        self.lbl_activity_status.setStyleSheet("color: #3B7A57;")
        vbox_act.addWidget(self.lbl_activity_status)

        right_layout.addWidget(activity_box)

        # Section 3: Offline Data Auto-Save Notice
        db_info_box = QFrame()
        db_info_box.setProperty("class", "MetricCard")
        vbox_db = QVBoxLayout(db_info_box)
        vbox_db.setContentsMargins(12, 8, 12, 8)

        lbl_db_info = QLabel("💾 離線資料庫自動儲存中")
        lbl_db_info.setFont(QFont("Microsoft JhengHei UI", 14, QFont.Bold))
        lbl_db_info.setStyleSheet("color: #3B7A57;")

        lbl_db_desc = QLabel("後台已非同步自動將數據寫入 SQLite 與 CSV 供科研大數據分析。")
        lbl_db_desc.setWordWrap(True)
        lbl_db_desc.setStyleSheet("color: #78726A; font-size: 14px; line-height: 1.4;")

        vbox_db.addWidget(lbl_db_info)
        vbox_db.addWidget(lbl_db_desc)
        right_layout.addWidget(db_info_box)

        right_layout.addStretch()

        # Section 4: Streamlined Control Panel (Start/Pause Toggle & Combined Stop/Reset Button)
        ctrl_box = QFrame()
        ctrl_box.setProperty("class", "MetricCard")
        vbox_ctrl = QVBoxLayout(ctrl_box)
        vbox_ctrl.setContentsMargins(10, 10, 10, 10)
        vbox_ctrl.setSpacing(8)

        lbl_ctrl_title = QLabel("⚙️ 系統控制與操作選單")
        lbl_ctrl_title.setFont(QFont("Microsoft JhengHei UI", 14, QFont.Bold))
        lbl_ctrl_title.setStyleSheet("color: #7F2424;")
        vbox_ctrl.addWidget(lbl_ctrl_title)

        grid_btns = QGridLayout()
        grid_btns.setSpacing(8)

        # 1. Combined Start/Pause Button
        self.btn_toggle_run = QPushButton("▶ 啟動推論")
        self.btn_toggle_run.setProperty("class", "ActionBtn")
        self.btn_toggle_run.setStyleSheet("background-color: #3B7A57;")

        # 2. Combined Stop & Reset Button
        self.btn_stop_reset = QPushButton("🔄 停止並重置計數")
        self.btn_stop_reset.setProperty("class", "ActionBtn DangerBtn")

        # 3. Settings Button
        self.btn_settings = QPushButton("⚙️ 劃線標記設定")
        self.btn_settings.setProperty("class", "ActionBtn")

        grid_btns.addWidget(self.btn_toggle_run, 0, 0)
        grid_btns.addWidget(self.btn_stop_reset, 0, 1)
        grid_btns.addWidget(self.btn_settings, 1, 0, 1, 2)

        vbox_ctrl.addLayout(grid_btns)
        right_layout.addWidget(ctrl_box)

        # Assemble Main Layout (70% Left Video Canvas, 30% Right Panel)
        main_layout.addLayout(left_layout, stretch=7)
        main_layout.addLayout(right_layout, stretch=3)

        # Connect button signals
        self.btn_toggle_run.clicked.connect(self.toggle_run_requested.emit)
        self.btn_stop_reset.clicked.connect(self.stop_reset_requested.emit)
        self.btn_settings.clicked.connect(self.switch_to_dashboard_event)

    def set_running_state(self, is_running: bool, is_paused: bool):
        """Updates the text and style of the single combined Start/Pause toggle button."""
        if is_running and not is_paused:
            self.btn_toggle_run.setText("⏸ 暫停推論")
            self.btn_toggle_run.setStyleSheet("background-color: #C48227;")  # Warm Amber for Pause
        elif is_paused:
            self.btn_toggle_run.setText("▶ 繼續推論")
            self.btn_toggle_run.setStyleSheet("background-color: #3B7A57;")  # Olive Green for Resume
        else:
            self.btn_toggle_run.setText("▶ 啟動推論")
            self.btn_toggle_run.setStyleSheet("background-color: #3B7A57;")  # Olive Green for Start

    def switch_to_dashboard_event(self):
        self.switch_to_settings.emit()

    def _create_card(self, title, init_val, val_obj_name):
        card = QFrame()
        card.setProperty("class", "MetricCard")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(10, 8, 10, 8)

        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "MetricTitle")

        lbl_val = QLabel(init_val)
        lbl_val.setObjectName(val_obj_name)
        lbl_val.setProperty("class", "MetricValue")

        vbox.addWidget(lbl_title)
        vbox.addWidget(lbl_val)
        return card

    def update_frame(self, frame: np.ndarray, stats: dict):
        """Updates video canvas frame and metrics display."""
        self.video_canvas.set_frame(frame)

        # Update card values
        self.card_in.findChild(QLabel, "ValIn").setText(f"{stats.get('in_count', 0)} 隻")
        self.card_out.findChild(QLabel, "ValOut").setText(f"{stats.get('out_count', 0)} 隻")

        net = stats.get("net_count", 0)
        net_str = f"+{net} 隻" if net > 0 else f"{net} 隻"
        self.card_net.findChild(QLabel, "ValNet").setText(net_str)

        self.card_fps.findChild(QLabel, "ValFps").setText(str(stats.get("fps", 0.0)))
        self.lbl_active_val.setText(f"{stats.get('active_tracks', 0)} 隻")

    def register_event_for_rate(self, event: dict):
        """Registers crossing event to update 1-minute activity rate indicator."""
        now = time.time()
        self.recent_events_window.append(now)
        # Purge events older than 60 seconds
        self.recent_events_window = [t for t in self.recent_events_window if (now - t) <= 60.0]

        rate_per_min = len(self.recent_events_window)
        self.lbl_rate_val.setText(f"{rate_per_min} 次/分")

        # Update activity bar (scaled 0 to 60 events/min)
        level_percent = min(100, int((rate_per_min / 40.0) * 100))
        self.bar_activity.setValue(level_percent)

        if rate_per_min < 10:
            self.lbl_activity_status.setText("狀態: 平穩 / 低活動量")
            self.lbl_activity_status.setStyleSheet("color: #3B7A57; font-weight: bold;")
        elif rate_per_min < 30:
            self.lbl_activity_status.setText("狀態: 中等流動頻率 🐝")
            self.lbl_activity_status.setStyleSheet("color: #C48227; font-weight: bold;")
        else:
            self.lbl_activity_status.setText("狀態: 蜂群極高進出活躍 🔥")
            self.lbl_activity_status.setStyleSheet("color: #BD463B; font-weight: bold;")
