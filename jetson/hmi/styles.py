MUJI_THEME_QSS = """
/* ===================================================================
   MUJI Minimalist Rounded Warm Theme (無印良品柔和圓潤字體加大美學)
   Font Family: Quicksand, Nunito, Microsoft JhengHei UI (圓潤無襯線體)
   =================================================================== */

/* Global Application Background & Base Font */
QMainWindow, QWidget {
    background-color: #F5F2EB;
    color: #2D2B2A;
    font-family: "Quicksand", "Nunito", "Varela Round", "Microsoft JhengHei UI", "PingFang TC", sans-serif;
    font-size: 16px;
}

/* Header Navigation Bar */
#HeaderBar {
    background-color: #EAE6DD;
    border-bottom: 1px solid #DCD6CB;
    padding: 12px 24px;
}

#TitleLabel {
    font-size: 24px;
    font-weight: 800;
    color: #7F2424; /* MUJI Crimson Red */
    letter-spacing: 0.5px;
}

/* Navigation Buttons (Top Tab Pills - Enriched & Rounded) */
QPushButton.NavBtn {
    background-color: #DFDAD0;
    color: #55504A;
    border: 1px solid #D0C9BD;
    border-radius: 12px;
    padding: 10px 24px;
    font-size: 16px;
    font-weight: 700;
}

QPushButton.NavBtn:hover {
    background-color: #D3CCC0;
    color: #2D2B2A;
}

QPushButton.NavBtn:checked, QPushButton.NavBtn:pressed {
    background-color: #7F2424;
    color: #FFFFFF;
    border: 1px solid #7F2424;
}

/* Metric Display Cards (Soft Rounded Containers) */
QFrame.MetricCard {
    background-color: #FFFFFF;
    border: 1px solid #E3DDD3;
    border-radius: 16px;
    padding: 18px;
}

QLabel.MetricTitle {
    font-size: 15px;
    color: #78726A;
    font-weight: 700;
}

QLabel.MetricValue {
    font-size: 38px;
    font-weight: 800;
    margin-top: 4px;
}

QLabel#ValIn { color: #3B7A57; }      /* Muted Olive Sage Green for IN */
QLabel#ValOut { color: #BD463B; }     /* Soft Terracotta Rust Red for OUT */
QLabel#ValNet { color: #C48227; }     /* Warm Ochre Amber for NET */
QLabel#ValFps { color: #4B6584; }     /* Slate Dusty Blue for FPS */

/* Action Control Buttons */
QPushButton.ActionBtn {
    background-color: #4A4540; /* Muted Charcoal Brown */
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 12px 24px;
    font-weight: 700;
    font-size: 15px;
}

QPushButton.ActionBtn:hover {
    background-color: #383430;
}

QPushButton.ActionBtn:pressed {
    background-color: #262320;
}

QPushButton.DangerBtn {
    background-color: #A93226;
}

QPushButton.DangerBtn:hover {
    background-color: #8E2A20;
}

/* GroupBox and Inputs */
QGroupBox {
    font-weight: 800;
    font-size: 16px;
    border: 1px solid #DDD7CC;
    border-radius: 14px;
    background-color: #FFFFFF;
    margin-top: 14px;
    padding-top: 20px;
    color: #7F2424;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 12px;
    background-color: #FFFFFF;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #FAF8F5;
    border: 1px solid #D8D2C7;
    border-radius: 9px;
    color: #2D2B2A;
    padding: 10px 14px;
    font-size: 15px;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #7F2424;
    background-color: #FFFFFF;
}

/* Status Bar */
QStatusBar {
    background-color: #EAE6DD;
    color: #55504A;
    border-top: 1px solid #DCD6CB;
    font-size: 15px;
    padding: 6px 14px;
}
"""
