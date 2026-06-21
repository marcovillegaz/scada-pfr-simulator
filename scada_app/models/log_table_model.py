from __future__ import annotations

from typing import List, Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

from engine.data_store import EngineSnapshot

COLUMNS = [
    ("sim_time", "Time (s)"),
    ("CA_out",   "Ca_out (mol/L)"),
    ("CB_out",   "Cb_out (mol/L)"),
    ("T_out",    "T_out (K)"),
    ("X_out",    "X_out (-)"),
    ("T_hx",     "T_hx (K)"),
    ("valve",    "Valve (-)"),
    ("CA_in",    "Ca_in (mol/L)"),
    ("CB_in",    "Cb_in (mol/L)"),
    ("Qa0",      "Qa0 (m3/s)"),
    ("Qb0",      "Qb0 (m3/s)"),
    ("Q_in",     "Q_in (m3/s)"),
    ("velocity",     "u (m/s)"),
    ("conductivity", "Conductivity (mS/cm)"),
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
