from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import pyqtSignal

from engine.data_store import EngineSnapshot
from ui.widgets.pfr_diagram import PFRDiagramWidget
from ui.widgets.status_card import StatusCard
from ui.widgets.event_log_panel import EventLogPanel

_SIDEBAR_W   = 230
_SIDEBAR_BG  = "#262626"
_SIDEBAR_BD  = "#525252"


class DiagramTab(QWidget):
    pid_change_requested      = pyqtSignal()
    sensor_info_requested     = pyqtSignal()
    reactor_info_requested    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # ── P&ID diagram (fixed width = SVG natural width) ────────────────────
        self._diagram = PFRDiagramWidget(self)
        self._diagram.setMaximumWidth(1010)
        self._diagram.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        lay.addWidget(self._diagram, stretch=0)

        # ── Right sidebar ─────────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(_SIDEBAR_W)
        sidebar.setStyleSheet(
            f"QFrame {{background-color:{_SIDEBAR_BG};"
            f"border-left:1px solid {_SIDEBAR_BD};}}"
        )

        slay = QVBoxLayout(sidebar)
        slay.setContentsMargins(8, 12, 8, 12)
        slay.setSpacing(10)

        self._status_card = StatusCard(sidebar)
        self._event_log   = EventLogPanel(sidebar)

        slay.addWidget(self._status_card, stretch=0)
        slay.addWidget(self._event_log,   stretch=1)

        lay.addWidget(sidebar, stretch=0)

        # ── Signal forwarding ─────────────────────────────────────────────────
        self._diagram.pid_change_requested.connect(self.pid_change_requested)
        self._diagram.sensor_info_requested.connect(self.sensor_info_requested)
        self._diagram.reactor_info_requested.connect(self.reactor_info_requested)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_readings(self, snap: EngineSnapshot) -> None:
        self._diagram.update_readings(snap)
        self._status_card.update_readings(snap)
        self._event_log.update_readings(snap)

    def get_params(self) -> dict:
        return self._diagram.get_params()

    def mark_params_clean(self) -> None:
        self._diagram.mark_params_clean()

    def add_event(self, sim_time: float, text: str, level: str = "info") -> None:
        self._event_log.add_event(sim_time, text, level)

    def clear_events(self) -> None:
        self._event_log.clear()
