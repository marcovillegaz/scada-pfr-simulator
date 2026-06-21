# Ubuntu Yaru-Dark inspired palette
# Primary accent : #E95420  (Ubuntu orange)
# Secondary      : #77216F  (Ubuntu aubergine)
# Focus/active   : #3584e4  (GNOME blue)
# Success        : #26A269
# Warning        : #cd9309
# Error          : #e01b24

SCADA_DARK = """
QMainWindow, QWidget {
    background-color: #2d2d2d;
    color: #eeeeec;
    font-family: "Segoe UI", "Ubuntu", "Cantarell", sans-serif;
    font-size: 10pt;
}
QGroupBox {
    border: 1px solid #525252;
    border-radius: 6px;
    margin-top: 10px;
    color: #E95420;
    font-weight: bold;
    font-size: 10pt;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QDoubleSpinBox, QSpinBox {
    background-color: #3d3d3d;
    border: 1px solid #6e6e6e;
    color: #eeeeec;
    padding: 2px 4px;
    border-radius: 4px;
    selection-background-color: #E95420;
    selection-color: #ffffff;
}
QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #3584e4;
}
QPushButton {
    background-color: #4a4a4a;
    border: 1px solid #6e6e6e;
    color: #eeeeec;
    padding: 4px 14px;
    border-radius: 4px;
    min-width: 60px;
}
QPushButton:hover   { background-color: #5c5c5c; border-color: #888888; }
QPushButton:pressed { background-color: #3d3d3d; }
QPushButton#btn_go    { background-color: #215732; color: #ffffff; font-weight: bold; border-color: #26A269; }
QPushButton#btn_go:hover { background-color: #26A269; }
QPushButton#btn_stop  { background-color: #8b1a1a; color: #ffffff; font-weight: bold; border-color: #e01b24; }
QPushButton#btn_stop:hover { background-color: #e01b24; }
QPushButton#btn_reset { background-color: #4a1a52; color: #ffffff; border-color: #77216F; }
QPushButton#btn_reset:hover { background-color: #77216F; }
QPushButton#btn_apply { background-color: #1a3d6e; color: #ffffff; font-weight: bold; border-color: #3584e4; }
QPushButton#btn_apply:hover { background-color: #3584e4; }
QLabel#value_label {
    color: #E95420;
    font-size: 11pt;
    font-weight: bold;
}
QLabel#reading_name   { color: #adadad; }
QLabel#separator_label { color: #6e6e6e; font-size: 9pt; }
QTableView {
    background-color: #3d3d3d;
    alternate-background-color: #444444;
    gridline-color: #525252;
    selection-background-color: #E95420;
    selection-color: #ffffff;
    border: 1px solid #525252;
    border-radius: 4px;
}
QHeaderView::section {
    background-color: #4a4a4a;
    color: #adadad;
    border: none;
    border-right: 1px solid #525252;
    padding: 4px;
    font-weight: bold;
}
QTabWidget::pane { border: none; }
QTabBar::tab {
    background: #3d3d3d;
    color: #adadad;
    padding: 6px 18px;
    border: 1px solid #525252;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected { background: #4a4a4a; color: #ffffff; }
QTabBar::tab:hover    { background: #444444; color: #e0e0e0; }
QSlider::groove:horizontal {
    background: #4a4a4a;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #E95420;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #c34113; border-radius: 3px; }
QSplitter::handle { background-color: #525252; }
QScrollBar:vertical {
    background: #3d3d3d;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #6e6e6e;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #adadad; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #3d3d3d;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #6e6e6e;
    border-radius: 5px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QDialog { background-color: #2d2d2d; }
"""
