from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt, pyqtSignal

from constants import APP_NAME, APP_VERSION, PFR_MODULE_NAME, RTD_MODULE_NAME

_CARD_W = 260
_CARD_H = 180


class _Card(QFrame):
    """Clickable home-screen tile. Disabled cards are inert (no hover/click)."""

    clicked = pyqtSignal()

    def __init__(self, title: str, subtitle: str, enabled: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("home_card")
        self.setFixedSize(_CARD_W, _CARD_H)
        self._enabled = enabled
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ArrowCursor
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(8)

        title_color = "#E95420" if enabled else "#7a7a7a"
        sub_color = "#adadad" if enabled else "#5c5c5c"

        t = QLabel(title)
        t.setWordWrap(True)
        t.setStyleSheet(f"color:{title_color};font-size:16px;font-weight:bold;background:transparent;")
        lay.addWidget(t)

        s = QLabel(subtitle)
        s.setWordWrap(True)
        s.setStyleSheet(f"color:{sub_color};font-size:11.5px;background:transparent;")
        lay.addWidget(s)
        lay.addStretch()

        hover_border = "#E95420" if enabled else "#525252"
        hover_bg = "#3a3a3a" if enabled else "#333333"
        self.setStyleSheet(f"""
            QFrame#home_card {{
                background-color: #333333;
                border: 1px solid #525252;
                border-radius: 8px;
            }}
            QFrame#home_card:hover {{
                border: 1px solid {hover_border};
                background-color: {hover_bg};
            }}
        """)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if self._enabled and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class HomeScreen(QWidget):
    """Landing screen — pick a simulation, open About, etc."""

    pfr_requested   = pyqtSignal()
    rtd_requested   = pyqtSignal()
    about_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(f"{APP_NAME} — Chemical Engineering Teaching Simulators")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#eeeeec;font-size:22px;font-weight:bold;background:transparent;")

        subtitle = QLabel(f"Universidad de Santiago de Chile (USACH)  ·  v{APP_VERSION}")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color:#adadad;font-size:12px;background:transparent;margin-bottom:32px;")

        root.addStretch()
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(24)

        # Top row: the two simulation modules. About sits on its own row below
        # -- it isn't a module, so it shouldn't read as a peer of PFR/RTD.
        modules = QHBoxLayout()
        modules.setSpacing(20)
        modules.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card_pfr = _Card(
            PFR_MODULE_NAME,
            "Plug-flow reactor: saponification kinetics, temperature control "
            "and conductivity sensing.",
            enabled=True,
        )
        self._card_rtd = _Card(
            RTD_MODULE_NAME,
            "Residence-time distribution: tracer stimulus–response test on a "
            "packed bed.",
            enabled=True,
        )

        self._card_pfr.clicked.connect(self.pfr_requested)
        self._card_rtd.clicked.connect(self.rtd_requested)

        modules.addWidget(self._card_pfr)
        modules.addWidget(self._card_rtd)

        modules_wrap = QWidget()
        modules_wrap.setLayout(modules)
        root.addWidget(modules_wrap)
        root.addSpacing(20)

        about_row = QHBoxLayout()
        about_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card_about = _Card(
            "About",
            "Author, project purpose, license, citation and version history.",
            enabled=True,
        )
        self._card_about.clicked.connect(self.about_requested)
        about_row.addWidget(self._card_about)

        about_wrap = QWidget()
        about_wrap.setLayout(about_row)
        root.addWidget(about_wrap)
        root.addStretch()
