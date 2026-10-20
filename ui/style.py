ACCENT = "#ff6a1a"
ACCENT_2 = "#3ba7ff"
BG = "#15171c"
BG_PANEL = "#1c1f26"
BG_CARD = "#22262f"
BORDER = "#2d323c"
TEXT = "#e7e9ee"
TEXT_DIM = "#9aa1ad"
GREEN = "#3fd17f"
RED = "#ff5c5c"

STYLESHEET = f"""
* {{
    font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
    color: {TEXT};
}}
QMainWindow, QDialog, QWidget#root {{
    background-color: {BG};
}}
QWidget {{
    background-color: transparent;
}}
QDialog {{
    background-color: {BG};
}}
QFrame#sidebar {{
    background-color: {BG_PANEL};
    border-right: 1px solid {BORDER};
}}
QLabel#appTitle {{
    font-size: 18px;
    font-weight: 700;
    padding: 18px 16px 8px 16px;
    color: {TEXT};
}}
QLabel#appSubtitle {{
    font-size: 11px;
    color: {TEXT_DIM};
    padding: 0px 16px 14px 16px;
}}
QPushButton#navButton {{
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 0px;
    background-color: transparent;
    font-size: 13px;
    color: {TEXT_DIM};
}}
QPushButton#navButton:hover {{
    background-color: {BG_CARD};
    color: {TEXT};
}}
QPushButton#navButton:checked {{
    background-color: {BG_CARD};
    color: {ACCENT};
    border-left: 3px solid {ACCENT};
    font-weight: 600;
}}
QLabel#pageTitle {{
    font-size: 22px;
    font-weight: 700;
    padding: 4px 0 2px 0;
}}
QLabel#pageSubtitle {{
    color: {TEXT_DIM};
    font-size: 12px;
    padding-bottom: 10px;
}}
QFrame#card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QPushButton {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 14px;
    font-size: 12.5px;
}}
QPushButton:hover {{
    border-color: {ACCENT};
}}
QPushButton:pressed {{
    background-color: {BORDER};
}}
QPushButton#primary {{
    background-color: {ACCENT};
    border: none;
    color: #1a1a1a;
    font-weight: 700;
}}
QPushButton#primary:hover {{
    background-color: #ff7d38;
}}
QPushButton#danger {{
    border-color: {RED};
    color: {RED};
}}
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    font-size: 12.5px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{ border: none; }}
QSpinBox, QDoubleSpinBox {{
    background-color: #2a303c;
    border: 1.5px solid #454c5c;
    border-radius: 6px;
    padding: 4px 4px 4px 8px;
    font-size: 13.5px;
    font-weight: 700;
    color: #ffffff;
    min-width: 50px;
    min-height: 22px;
}}
QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {ACCENT_2};
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {ACCENT};
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    height: 12px;
    background-color: #363d4a;
    border-left: 1px solid #454c5c;
    border-top-right-radius: 6px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    height: 12px;
    background-color: #363d4a;
    border-left: 1px solid #454c5c;
    border-bottom-right-radius: 6px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover,
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {ACCENT};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {TEXT};
    width: 0; height: 0;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT};
    width: 0; height: 0;
}}
QTableWidget {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    gridline-color: {BORDER};
    selection-background-color: #33261a;
    selection-color: {TEXT};
}}
QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {TEXT_DIM};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    font-size: 11.5px;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    top: -1px;
}}
QTabBar::tab {{
    background: {BG_PANEL};
    padding: 8px 16px;
    border: 1px solid {BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
    color: {TEXT_DIM};
}}
QTabBar::tab:selected {{
    background: {BG_CARD};
    color: {ACCENT};
    font-weight: 600;
}}
QScrollArea {{ border: none; }}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 5px;
    min-height: 24px;
}}
QListWidget {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
QListWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {BORDER};
}}
QListWidget::item:selected {{
    background-color: #33261a;
    color: {ACCENT};
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {TEXT_DIM};
}}
QRadioButton, QCheckBox {{ font-size: 12.5px; }}
"""
