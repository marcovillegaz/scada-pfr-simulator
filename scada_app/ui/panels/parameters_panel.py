from __future__ import annotations

from PyQt6.QtWidgets import (
    QGroupBox, QFormLayout, QDoubleSpinBox, QVBoxLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal

from constants import (
    DEFAULT_FEED_A_FLOW, DEFAULT_FEED_B_FLOW,
    DEFAULT_CA_FEED, DEFAULT_CB_FEED,
    DEFAULT_T_IN_SETPOINT,
    K2C,
)

_ML_MIN = 60_000_000.0  # m³/s → mL/min

DIRTY_STYLE = "background-color: #ffffff; color: #111111; border: 1px solid #90caf9;"
CLEAN_STYLE = ""

_PANEL_STYLE = """
    QGroupBox#params_panel {
        background-color: #0d1b26;
        border: 1px solid #4fc3f7;
        border-radius: 6px;
        color: #4fc3f7;
        font-weight: bold;
        font-size: 12px;
        padding-top: 18px;
    }
    QGroupBox#params_panel::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: #4fc3f7;
    }
    QGroupBox {
        background-color: #0d1b26;
        border: 1px solid #2d3f50;
        border-radius: 4px;
        color: #78909c;
        font-size: 11px;
        font-weight: bold;
        margin-top: 6px;
        padding-top: 12px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 4px;
    }
    QLabel {
        color: #cfd8dc;
        font-size: 11px;
    }
    QDoubleSpinBox {
        background-color: #1c2733;
        border: 1px solid #546e7a;
        color: #80cbc4;
        padding: 2px 4px;
        border-radius: 2px;
        font-size: 11px;
    }
    QDoubleSpinBox:focus {
        border: 1px solid #4fc3f7;
    }
"""


class ParametersPanel(QGroupBox):
    parameters_applied = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__("Parameters", parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("params_panel")
        self.setStyleSheet(_PANEL_STYLE)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setSpacing(6)
        outer.setContentsMargins(8, 4, 8, 8)

        def sb(min_v, max_v, step, dec, default) -> QDoubleSpinBox:
            w = QDoubleSpinBox()
            w.setRange(min_v, max_v)
            w.setSingleStep(step)
            w.setDecimals(dec)
            w.setValue(default)
            w.valueChanged.connect(lambda _: w.setStyleSheet(DIRTY_STYLE))
            return w

        # ── Feed A ───────────────────────────────────────────────────────────
        grp_a, form_a = self._group("Feed A")
        self._spin_qa = sb(0.001, 600.0, 0.1, 2, DEFAULT_FEED_A_FLOW * _ML_MIN)
        self._spin_ca = sb(0.0,    20.0, 0.1, 3, DEFAULT_CA_FEED)
        form_a.addRow("Qa  (mL/min)", self._spin_qa)
        form_a.addRow("Ca  (mol/L)",  self._spin_ca)
        outer.addWidget(grp_a)

        # ── Feed B ───────────────────────────────────────────────────────────
        grp_b, form_b = self._group("Feed B")
        self._spin_qb = sb(0.001, 600.0, 0.1, 2, DEFAULT_FEED_B_FLOW * _ML_MIN)
        self._spin_cb = sb(0.0,    20.0, 0.1, 3, DEFAULT_CB_FEED)
        form_b.addRow("Qb  (mL/min)", self._spin_qb)
        form_b.addRow("Cb  (mol/L)",  self._spin_cb)
        outer.addWidget(grp_b)

        # ── HX Temperature Setpoint ──────────────────────────────────────────
        grp_pid, form_pid = self._group("HX Setpoint")
        self._spin_tsp = sb(5.0, 89.0, 1.0, 1, DEFAULT_T_IN_SETPOINT - K2C)
        form_pid.addRow("T_sp  (°C)", self._spin_tsp)
        outer.addWidget(grp_pid)

        self._all_spins = [
            self._spin_qa, self._spin_ca,
            self._spin_qb, self._spin_cb,
            self._spin_tsp,
        ]

    def _group(self, title: str):
        box  = QGroupBox(title)
        vlay = QVBoxLayout(box)
        vlay.setSpacing(3)
        form = QFormLayout()
        form.setSpacing(3)
        vlay.addLayout(form)
        return box, form

    # ── Public API ────────────────────────────────────────────────────────────

    def apply_all(self) -> None:
        """Emit parameters_applied with all current values and clear dirty state."""
        self.parameters_applied.emit(self.get_current_params())
        for spin in self._all_spins:
            spin.setStyleSheet(CLEAN_STYLE)

    def get_current_params(self) -> dict:
        return {
            'Qa0':           self._spin_qa.value() / _ML_MIN,
            'Ca0':           self._spin_ca.value(),
            'Qb0':           self._spin_qb.value() / _ML_MIN,
            'Cb0':           self._spin_cb.value(),
            'T_in_setpoint': self._spin_tsp.value() + K2C,
        }
