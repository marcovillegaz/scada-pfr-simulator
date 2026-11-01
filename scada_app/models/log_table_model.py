from __future__ import annotations

from typing import List, Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt

from engine.data_store import EngineSnapshot

_ML_MIN = 60_000_000.0  # m³/s → mL/min

# Columns are (attr, header, scale). `scale` multiplies the raw snapshot value
# for display — flows are stored in m³/s (~1.6e-6) and would round to 0.0000,
# so they are shown in mL/min.

# Student-facing column set (Table tab). A = NaOH, B = EtAc.
STUDENT_COLUMNS = [
    ("sim_time",     "Time (s)",              1.0),
    ("CA_in",        "Ca_in (mol/L) — NaOH",  1.0),
    ("CB_in",        "Cb_in (mol/L) — EtAc",  1.0),
    ("Qa0",          "Qa0 (mL/min) — NaOH",   _ML_MIN),
    ("Qb0",          "Qb0 (mL/min) — EtAc",   _ML_MIN),
    ("T_in",         "T_in (K)",              1.0),
    ("T_out",        "T_out (K)",             1.0),
    ("T_reactor",    "T_reactor (K)",         1.0),
    ("valve",        "Valve (-)",             1.0),
    ("conductivity", "Conductivity (mS/cm)",  1.0),
]

# Full internal-variable set (Admin tab).
ADMIN_COLUMNS = [
    ("sim_time",     "Time (s)",            1.0),
    ("Qa0",          "Qa0 (mL/min)",        _ML_MIN),
    ("Qb0",          "Qb0 (mL/min)",        _ML_MIN),
    ("Q_in",         "Q_in (mL/min)",       _ML_MIN),
    ("CA_in",        "Ca_in (mol/L)",       1.0),
    ("CB_in",        "Cb_in (mol/L)",       1.0),
    ("CA_out",       "Ca_out (mol/L)",      1.0),
    ("CB_out",       "Cb_out (mol/L)",      1.0),
    ("X_out",        "Xa_out (-)",          1.0),
    ("velocity",     "u (m/s)",             1.0),
    ("T_in",         "T_in (K)",            1.0),
    ("T_out",        "T_out (K)",           1.0),
    ("T_reactor",    "T_reactor (K)",       1.0),
    ("valve",        "Valve (-)",           1.0),
    ("conductivity", "Conductivity (mS/cm)", 1.0),
]

# Default kept for backward compatibility.
COLUMNS = STUDENT_COLUMNS

# RTD (Experiencia 3) columns -- operates on RTDSnapshot instead of
# EngineSnapshot, but LogTableModel reads columns via getattr() so the same
# class works unmodified for either.
RTD_COLUMNS = [
    ("sim_time",   "Time (s)",       1.0),
    ("Q",          "Q (L/s)",        1.0),
    ("absorbance", "Absorbance (-)", 1.0),
    ("injecting",  "Injecting",      1.0),
]


def export_frame(df, columns: list[tuple] | None = None):
    """Project a full ``DataStore.to_dataframe()`` onto a column set for export.

    Keeps only the (attr, header, scale) columns given -- by default the
    student-facing ones -- with the same headers and unit scaling the table
    shows, so an exported file never contains internal variables (true
    CA_out / CB_out / X_out, velocity, Q_in, T_setpoint).
    """
    cols = STUDENT_COLUMNS if columns is None else columns
    out = df[[attr for attr, _, _ in cols]].copy()
    for attr, _, scale in cols:
        if scale != 1.0:
            out[attr] = out[attr] * scale
    return out.rename(columns={attr: header for attr, header, _ in cols})


class LogTableModel(QAbstractTableModel):
    def __init__(
        self,
        snapshots: List[EngineSnapshot] | None = None,
        columns: list[tuple] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._data: List[EngineSnapshot] = snapshots or []
        self._columns = columns if columns is not None else STUDENT_COLUMNS

    def set_snapshots(self, snapshots: List[EngineSnapshot]) -> None:
        self.beginResetModel()
        self._data = snapshots
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        snap = self._data[index.row()]
        attr, _, scale = self._columns[index.column()]
        value = getattr(snap, attr)
        if isinstance(value, float):
            return f"{value * scale:.4f}"
        return str(value)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._columns[section][1]
        return str(section + 1)
