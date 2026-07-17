from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSizePolicy
from PyQt6.QtCore import pyqtSignal

from engine.data_store import RTDSnapshot
from ui.widgets.rtd_diagram import RTDDiagramWidget
from ui.widgets.injection_panel import InjectionPanel
from ui.widgets.event_log_panel import EventLogPanel

_SIDEBAR_W  = 230
_SIDEBAR_BG = "#262626"
_SIDEBAR_BD = "#525252"


class RTDDiagramTab(QWidget):
    """Diagram tab for the RTD workspace: P&ID (left) + injection controls
    and event log (right sidebar). Mirrors DiagramTab's PFR layout, but the
    sidebar carries InjectionPanel instead of StatusCard -- there is no
    RTD-specific alarm concept, so EventLogPanel is used only for manual
    add_event() calls (its automatic alarm detection is PFR-only and is
    simply never invoked here)."""

    pulse_requested      = pyqtSignal(float)
    step_start_requested = pyqtSignal(float)
    step_stop_requested  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._diagram = RTDDiagramWidget(self)
        self._diagram.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        lay.addWidget(self._diagram, stretch=1)

        sidebar = QFrame()
        sidebar.setFixedWidth(_SIDEBAR_W)
        sidebar.setStyleSheet(
            f"QFrame {{background-color:{_SIDEBAR_BG};"
            f"border-left:1px solid {_SIDEBAR_BD};}}"
        )
        slay = QVBoxLayout(sidebar)
        slay.setContentsMargins(8, 12, 8, 12)
        slay.setSpacing(10)

        self._injection_panel = InjectionPanel(sidebar)
        self._event_log       = EventLogPanel(sidebar)

        slay.addWidget(self._injection_panel, stretch=0)
        slay.addWidget(self._event_log,       stretch=1)

        lay.addWidget(sidebar, stretch=0)

        self._injection_panel.pulse_requested.connect(self.pulse_requested)
        self._injection_panel.step_start_requested.connect(self.step_start_requested)
        self._injection_panel.step_stop_requested.connect(self.step_stop_requested)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_readings(self, snap: RTDSnapshot) -> None:
        self._diagram.update_readings(snap)
        self._injection_panel.set_pulse_enabled(not snap.injecting)

    def set_flow_display(self, Q_L_s: float) -> None:
        self._diagram.set_flow_display(Q_L_s)

    def get_params(self) -> dict:
        return self._diagram.get_params()

    def mark_params_clean(self) -> None:
        self._diagram.mark_params_clean()

    def add_event(self, sim_time: float, text: str, level: str = "info") -> None:
        self._event_log.add_event(sim_time, text, level)

    def clear_events(self) -> None:
        self._event_log.clear()

    def start_step_ui(self) -> None:
        self._injection_panel.start_step_ui()

    def stop_step_ui(self) -> None:
        self._injection_panel.stop_step_ui()

    def reset_injection_ui(self) -> None:
        self._injection_panel.reset()

    def start_band(self, kind: str, sim_time: float, tau: float) -> None:
        self._diagram.start_band(kind, sim_time, tau)

    def start_drain(self, sim_time: float, tau: float) -> None:
        self._diagram.start_drain(sim_time, tau)

    def advance_band(self, sim_time: float) -> None:
        self._diagram.advance_band(sim_time)

    def clear_band(self) -> None:
        self._diagram.clear_band()
