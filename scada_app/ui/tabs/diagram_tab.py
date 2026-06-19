from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from engine.data_store import EngineSnapshot
from ui.widgets.pfr_diagram import PFRDiagramWidget


class DiagramTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._diagram = PFRDiagramWidget(self)
        layout.addWidget(self._diagram)

    def update_readings(self, snap: EngineSnapshot) -> None:
        self._diagram.update_readings(snap)
