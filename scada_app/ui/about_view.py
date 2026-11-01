from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFrame
from PyQt6.QtCore import pyqtSignal

from ui.tabs.about_tab import AboutTab

_HEADER_H = 44
_DARK_BG   = "#262626"
_DARK_LINE = "#525252"


class AboutView(QWidget):
    """Shared About page, reached from the home screen (not per-simulation)."""

    home_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        hdr = QFrame()
        hdr.setObjectName("header_bar")
        hdr.setFixedHeight(_HEADER_H)
        hdr.setStyleSheet(f"""
            QFrame#header_bar {{
                background-color: {_DARK_BG};
                border-bottom: 2px solid {_DARK_LINE};
            }}
            QPushButton#btn_home {{
                background: transparent;
                border: none;
                color: #adadad;
                font-size: 12px;
                font-weight: bold;
                padding: 0 16px;
                min-width: 0;
                border-radius: 0;
            }}
            QPushButton#btn_home:hover {{
                color: #E95420;
            }}
        """)
        hlay = QHBoxLayout(hdr)
        hlay.setContentsMargins(14, 0, 14, 0)
        btn_home = QPushButton("≡ Home")
        btn_home.setObjectName("btn_home")
        btn_home.setFixedHeight(_HEADER_H)
        btn_home.clicked.connect(self.home_requested)
        hlay.addWidget(btn_home)
        hlay.addStretch()
        lay.addWidget(hdr)

        lay.addWidget(AboutTab(self), stretch=1)
