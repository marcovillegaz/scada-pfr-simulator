SCADA_DARK = """
QMainWindow, QWidget {
    background-color: #1e2832;
    color: #e0e0e0;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 10pt;
}
QGroupBox {
    border: 1px solid #37474f;
    border-radius: 4px;
    margin-top: 10px;
    color: #80cbc4;
    font-weight: bold;
    font-size: 10pt;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QDoubleSpinBox, QSpinBox {
    background-color: #263238;
    border: 1px solid #546e7a;
    color: #e0e0e0;
    padding: 2px 4px;
    border-radius: 2px;
}
QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #4fc3f7;
}
QPushButton {
    background-color: #37474f;
    border: 1px solid #546e7a;
    color: #e0e0e0;
    padding: 4px 14px;
    border-radius: 3px;
    min-width: 60px;
}
QPushButton:hover  { background-color: #455a64; }
QPushButton:pressed { background-color: #263238; }
QPushButton#btn_go    { background-color: #1b5e20; color: #ffffff; font-weight: bold; }
QPushButton#btn_go:hover { background-color: #2e7d32; }
QPushButton#btn_stop  { background-color: #b71c1c; color: #ffffff; font-weight: bold; }
QPushButton#btn_stop:hover { background-color: #c62828; }
QPushButton#btn_reset { background-color: #4a148c; color: #ffffff; }
QPushButton#btn_reset:hover { background-color: #6a1b9a; }
QPushButton#btn_apply { background-color: #0d47a1; color: #ffffff; font-weight: bold; }
QPushButton#btn_apply:hover { background-color: #1565c0; }
QLabel#value_label {
    color: #4fc3f7;
    font-size: 11pt;
    font-weight: bold;
}
QLabel#reading_name { color: #90a4ae; }
QLabel#separator_label { color: #546e7a; font-size: 9pt; }
QTableView {
    background-color: #263238;
    alternate-background-color: #2b3a42;
    gridline-color: #37474f;
    selection-background-color: #0d47a1;
    selection-color: #ffffff;
    border: 1px solid #37474f;
}
QHeaderView::section {
    background-color: #37474f;
    color: #b0bec5;
    border: none;
    padding: 4px;
    font-weight: bold;
}
QTabWidget::pane { border: 1px solid #37474f; }
QTabBar::tab {
    background: #263238;
    color: #90a4ae;
    padding: 6px 18px;
    border: 1px solid #37474f;
    border-bottom: none;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
}
QTabBar::tab:selected { background: #37474f; color: #e0e0e0; }
QTabBar::tab:hover    { background: #2e3f4a; }
QSlider::groove:horizontal {
    background: #37474f;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #4fc3f7;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}
QSlider::sub-page:horizontal { background: #1565c0; border-radius: 3px; }
QSplitter::handle { background-color: #37474f; }
QScrollBar:vertical {
    background: #263238;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #546e7a;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""
