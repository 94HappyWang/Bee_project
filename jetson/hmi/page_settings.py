from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QLabel, QPushButton,
    QDoubleSpinBox, QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal

from hmi.video_widget import VideoCanvasWidget
from utils.config import ConfigManager


class SettingsPage(QWidget):
    """Page 3: System Settings & Interactive Dual-Line Calibration Page."""

    settings_saved = pyqtSignal(dict)
    switch_to_dashboard = pyqtSignal()

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self._init_ui()
        self.load_config_to_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # ==========================================
        # LEFT PANEL: Interactive Calibration Canvas
        # ==========================================
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        title_lbl = QLabel("🎯 走廊雙邊界進出劃線即時調整區 (滑鼠拖曳點位校正)")
        title_lbl.setFont(QFont("Microsoft JhengHei UI", 14, QFont.Bold))
        title_lbl.setStyleSheet("color: #7F2424;")
        left_layout.addWidget(title_lbl)

        # Calibration Canvas
        self.video_canvas = VideoCanvasWidget(is_calibration_mode=True)
        left_layout.addWidget(self.video_canvas, stretch=1)

        note_lbl = QLabel("💡 提示：在畫面上直接使用滑鼠左鍵點擊並拖曳 [Line A 藍圓點] 或 [Line B 綠圓點] 即可即時校正線段位置。")
        note_lbl.setStyleSheet("color: #78726A; font-size: 13px;")
        left_layout.addWidget(note_lbl)

        # ==========================================
        # RIGHT PANEL: Options & Camera/Model Settings
        # ==========================================
        right_layout = QVBoxLayout()
        right_layout.setSpacing(14)

        # 1. System & Model Settings GroupBox
        grp_sys = QGroupBox("相機源與 YOLO 推論模型設定")
        vbox_sys = QVBoxLayout(grp_sys)
        vbox_sys.setSpacing(12)

        # Camera source
        row_cam = QHBoxLayout()
        lbl_cam = QLabel("相機/影片來源:")
        lbl_cam.setStyleSheet("color: #78726A; font-size: 14px;")
        self.txt_camera_src = QLineEdit("0")
        row_cam.addWidget(lbl_cam)
        row_cam.addWidget(self.txt_camera_src)
        vbox_sys.addLayout(row_cam)

        # Model Path
        row_model = QHBoxLayout()
        lbl_mod = QLabel("模型檔 (.engine/.onnx/.pt):")
        lbl_mod.setStyleSheet("color: #78726A; font-size: 14px;")
        self.txt_model_path = QLineEdit("best.pt")
        self.btn_browse_model = QPushButton("瀏覽...")
        self.btn_browse_model.setProperty("class", "ActionBtn")
        row_model.addWidget(lbl_mod)
        row_model.addWidget(self.txt_model_path)
        row_model.addWidget(self.btn_browse_model)
        vbox_sys.addLayout(row_model)

        # Conf Threshold & Timeout
        row_params = QHBoxLayout()
        lbl_conf = QLabel("信心度閥值:")
        lbl_conf.setStyleSheet("color: #78726A; font-size: 14px;")
        self.spn_conf = QDoubleSpinBox()
        self.spn_conf.setRange(0.05, 0.95)
        self.spn_conf.setSingleStep(0.05)
        self.spn_conf.setValue(0.30)
        row_params.addWidget(lbl_conf)
        row_params.addWidget(self.spn_conf)

        lbl_tout = QLabel("跨線超時(秒):")
        lbl_tout.setStyleSheet("color: #78726A; font-size: 14px;")
        self.spn_timeout = QDoubleSpinBox()
        self.spn_timeout.setRange(1.0, 30.0)
        self.spn_timeout.setValue(5.0)
        row_params.addWidget(lbl_tout)
        row_params.addWidget(self.spn_timeout)

        vbox_sys.addLayout(row_params)
        right_layout.addWidget(grp_sys)

        right_layout.addStretch()

        # Action Buttons
        btn_bar = QHBoxLayout()
        self.btn_save = QPushButton("💾 儲存設定並即時套用")
        self.btn_save.setProperty("class", "ActionBtn")

        self.btn_back = QPushButton("🔙 返回主畫面")
        self.btn_back.setProperty("class", "ActionBtn DangerBtn")

        btn_bar.addWidget(self.btn_save)
        btn_bar.addWidget(self.btn_back)
        right_layout.addLayout(btn_bar)

        # Assemble Main Layout (70% Left Video Canvas, 30% Right Panel)
        main_layout.addLayout(left_layout, stretch=7)
        main_layout.addLayout(right_layout, stretch=3)

        # Connect Signals
        self.btn_browse_model.clicked.connect(self._browse_model_file)
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_back.clicked.connect(self.switch_to_dashboard.emit)

    def load_config_to_ui(self):
        """Populates UI controls with values from ConfigManager."""
        line_a, line_b = self.config_manager.get_lines()
        self.txt_camera_src.setText(str(self.config_manager.get("camera_source", "0")))
        self.txt_model_path.setText(str(self.config_manager.get("model_path", "best.pt")))
        self.spn_conf.setValue(float(self.config_manager.get("conf_threshold", 0.3)))
        self.spn_timeout.setValue(float(self.config_manager.get("max_crossing_time", 5.0)))
        self.video_canvas.set_lines(line_a, line_b)

    def _browse_model_file(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self, "選取模型權重檔", "", "Model Files (*.engine *.onnx *.pt);;All Files (*)"
        )
        if filePath:
            self.txt_model_path.setText(filePath)

    def save_settings(self):
        """Saves settings to config.json and emits signal to update worker thread."""
        line_a = self.video_canvas.line_a
        line_b = self.video_canvas.line_b

        self.config_manager.set_lines(line_a, line_b, auto_save=False)
        self.config_manager.set("camera_source", self.txt_camera_src.text().strip(), auto_save=False)
        self.config_manager.set("model_path", self.txt_model_path.text().strip(), auto_save=False)
        self.config_manager.set("conf_threshold", self.spn_conf.value(), auto_save=False)
        self.config_manager.set("max_crossing_time", self.spn_timeout.value(), auto_save=False)
        self.config_manager.save()

        new_config = {
            "line_a": line_a,
            "line_b": line_b,
            "camera_source": self.txt_camera_src.text().strip(),
            "model_path": self.txt_model_path.text().strip(),
            "conf_threshold": self.spn_conf.value(),
            "max_crossing_time": self.spn_timeout.value()
        }

        self.settings_saved.emit(new_config)
        QMessageBox.information(self, "成功", "✅ 系統與雙邊界標記線設定已成功儲存並同步套用！")

    def update_preview_frame(self, frame):
        """Passes live frame to calibration canvas widget."""
        self.video_canvas.set_frame(frame)
