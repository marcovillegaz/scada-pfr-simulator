from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

from engine.data_store import EngineSnapshot
from ui.widgets.pfr_diagram import PFRDiagramWidget


class DiagramTab(QWidget):
    pid_change_requested      = pyqtSignal()
    sensor_info_requested     = pyqtSignal()
    reactor_info_requested    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._diagram = PFRDiagramWidget(self)
        layout.addWidget(self._diagram)
        self._diagram.pid_change_requested.connect(self.pid_change_requested)
        self._diagram.sensor_info_requested.connect(self.sensor_info_requested)
        self._diagram.reactor_info_requested.connect(self.reactor_info_requested)

    def update_readings(self, snap: EngineSnapshot) -> None:
        self._diagram.update_readings(snap)

    def get_params(self) -> dict:
        return self._diagram.get_params()

    def mark_params_clean(self) -> None:
        self._diagram.mark_params_clean()

    def add_event(self, sim_time: float, text: str, level: str = "info") -> None:
        self._diagram.add_event(sim_time, text, level)

    def clear_events(self) -> None:
        self._diagram.clear_events()
