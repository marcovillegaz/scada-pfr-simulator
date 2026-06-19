from __future__ import annotations

from typing import List, Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

from engine.data_store import EngineSnapshot

COLUMNS = [
    ("sim_time",             "Time (s)"),
    ("true_temp",            "T True (K)"),
    ("measured_temp",        "T Meas (K)"),
    ("setpoint",             "Setpoint (K)"),
    ("concentration",        "Ca (mol/L)"),
    ("measured_concentration","Ca Meas (mol/L)"),
    ("flow_rate",            "Flow (m³/s)"),
    ("heater_power_actual",  "Heater (W)"),
    ("pid_p",                "PID P"),
    ("pid_i",                "PID I"),
    ("pid_d",                "PID D"),
]


class LogTableModel(QAbstractTableModel):
    def __init__(self, snapshots: List[EngineSnapshot] | None = None, parent=None):
        super().__init__(parent)
        self._data: List[EngineSnapshot] = snapshots or []

    def set_snapshots(self, snapshots: List[EngineSnapshot]) -> None:
        self.beginResetModel()
        self._data = snapshots
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        snap = self._data[index.row()]
        attr, _ = COLUMNS[index.column()]
        value = getattr(snap, attr)
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return COLUMNS[section][1]
        return str(section + 1)
