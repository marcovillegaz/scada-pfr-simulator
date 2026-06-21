from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QGridLayout, QLabel
from PyQt6.QtCore import Qt

from constants import (
    PFR_LENGTH, K2C, AMBIENT_TEMP,
    ALARM_T_HIGH_C, ALARM_X_LOW,
)
from engine.data_store import EngineSnapshot

_BG = "rgba(15,22,30,215)"
_BD = "#37474f"

_LABEL_SS = "color:#546e7a;font-size:9px;background:transparent;border:none;"
_VALUE_SS = "color:#cfd8dc;font-size:9px;font-weight:bold;background:transparent;border:none;"
_TITLE_SS = "color:#4fc3f7;font-size:9px;font-weight:bold;background:transparent;border:none;"
_SEP_SS   = "color:#2d3f50;background:#2d3f50;max-height:1px;border:none;"
_UNIT_SS  = "color:#455a64;font-size:8px;background:transparent;border:none;"

_T_AMBIENT_C = AMBIENT_TEMP - K2C   # 25.0 °C — static feed stream temperature


class StatusCard(QFrame):
    """
    Live KPI summary overlay: Conversion, Reactor Temp, Residence Time, T ambient.
    Drop into any QWidget — position with move(); hide() to remove it.
    Badge colour driven by ALARM_T_HIGH_C / ALARM_X_LOW from constants.py.
    """

    FIXED_W = 185
    FIXED_H = 115

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self.FIXED_W, self.FIXED_H)
        self.setStyleSheet(
            f"QFrame {{background-color:{_BG};border:1px solid {_BD};border-radius:4px;}}"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(8, 5, 8, 5)
        vlay.setSpacing(3)

        title = QLabel("PROCESS STATUS")
        title.setStyleSheet(_TITLE_SS)
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(_SEP_SS)
        vlay.addWidget(sep)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(2)
        grid.setHorizontalSpacing(4)
        grid.setColumnStretch(1, 1)

        self._val_x   = self._kpi_row(grid, 0, "Conversion",     "%")
        self._val_t   = self._kpi_row(grid, 1, "Reactor Temp",   "°C")
        self._val_tau = self._kpi_row(grid, 2, "Residence time", "s")
        # T ambient is static — set once, never updated from snapshot
        self._kpi_row(grid, 3, "T ambient", "°C",
                      static_value=f"{_T_AMBIENT_C:.1f}")
        vlay.addLayout(grid)

        self._badge = QLabel("●  —")
        self._badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._badge.setStyleSheet(
            "color:#546e7a;font-size:9px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        vlay.addWidget(self._badge)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _kpi_row(
        grid: QGridLayout,
        row: int,
        name: str,
        unit: str,
        static_value: str | None = None,
    ) -> QLabel | None:
        lbl_n = QLabel(name)
        lbl_n.setStyleSheet(_LABEL_SS)

        lbl_v = QLabel(static_value if static_value else "—")
        lbl_v.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl_v.setStyleSheet(_VALUE_SS)

        lbl_u = QLabel(unit)
        lbl_u.setStyleSheet(_UNIT_SS)

        grid.addWidget(lbl_n, row, 0)
        grid.addWidget(lbl_v, row, 1)
        grid.addWidget(lbl_u, row, 2)

        return None if static_value else lbl_v

    # ── Public API ────────────────────────────────────────────────────────────

    def update_readings(self, snap: EngineSnapshot) -> None:
        tau = PFR_LENGTH / snap.velocity if snap.velocity > 0 else 0.0
        X   = snap.X_out * 100
        T   = snap.T_out - K2C
        self._val_x.setText(f"{X:.1f}")
        self._val_t.setText(f"{T:.1f}")
        self._val_tau.setText(f"{tau:.1f}")
        self._update_badge(X, T)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _update_badge(self, X_pct: float, T_C: float) -> None:
        if T_C > ALARM_T_HIGH_C:
            text, color = "HIGH TEMP", "#ef5350"
        elif X_pct < ALARM_X_LOW * 100:
            text, color = "LOW CONV", "#ffa726"
        else:
            text, color = "ON-SPEC", "#66bb6a"
        self._badge.setText(f"●  {text}")
        self._badge.setStyleSheet(
            f"color:{color};font-size:9px;font-weight:bold;"
            "background:transparent;border:none;"
        )
