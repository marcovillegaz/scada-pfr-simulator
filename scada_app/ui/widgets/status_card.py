from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QGridLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt

from constants import (
    PFR_LENGTH, K2C, AMBIENT_TEMP,
    ALARM_T_HIGH_C, ALARM_X_LOW,
)
from engine.data_store import EngineSnapshot

_BG = "rgba(38,38,38,220)"
_BD = "#525252"

_LABEL_SS = "color:#adadad;font-size:10px;background:transparent;border:none;"
_VALUE_SS = "color:#eeeeec;font-size:11px;font-weight:bold;background:transparent;border:none;"
_TITLE_SS = "color:#E95420;font-size:10px;font-weight:bold;background:transparent;border:none;"
_SEP_SS   = "color:#525252;background:#525252;max-height:1px;border:none;"
_UNIT_SS  = "color:#6e6e6e;font-size:9px;background:transparent;border:none;"

_T_AMBIENT_C = AMBIENT_TEMP - K2C   # 25.0 °C — static feed stream temperature


class StatusCard(QFrame):
    """
    Live KPI summary panel: Conversion, Reactor Temp, Residence Time, T ambient.
    Sized by its parent container — suitable for both overlay and sidebar use.
    Badge colour driven by ALARM_T_HIGH_C / ALARM_X_LOW from constants.py.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(
            f"QFrame {{background-color:{_BG};border:1px solid {_BD};border-radius:4px;}}"
        )
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(10, 7, 10, 7)
        vlay.setSpacing(4)

        title = QLabel("PROCESS STATUS")
        title.setStyleSheet(_TITLE_SS)
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(_SEP_SS)
        vlay.addWidget(sep)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setVerticalSpacing(3)
        grid.setHorizontalSpacing(6)
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
            "color:#546e7a;font-size:10px;font-weight:bold;"
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
            text, color = "HIGH TEMP", "#e01b24"
        elif X_pct < ALARM_X_LOW * 100:
            text, color = "LOW CONV",  "#cd9309"
        else:
            text, color = "ON-SPEC",   "#26A269"
        self._badge.setText(f"●  {text}")
        self._badge.setStyleSheet(
            f"color:{color};font-size:10px;font-weight:bold;"
            "background:transparent;border:none;"
        )
