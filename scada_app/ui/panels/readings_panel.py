from __future__ import annotations

from PyQt6.QtWidgets import QFrame, QGridLayout, QLabel, QDoubleSpinBox
from PyQt6.QtCore import Qt, QTimer

from constants import (
    PFR_LENGTH, K2C,
    DEFAULT_FEED_A_FLOW, DEFAULT_FEED_B_FLOW,
    DEFAULT_CA_FEED, DEFAULT_CB_FEED,
    DEFAULT_T_IN_SETPOINT,
)
from engine.data_store import EngineSnapshot

_ML_MIN          = 60_000_000.0
_SPIN_DIRTY      = "background-color: #ffffff; color: #111111; border: 1px solid #90caf9;"
_SPIN_CLEAN      = ""
_SPIN_HIGHLIGHT  = ("background-color: #0d2233; color: #4fc3f7;"
                    " border: 2px solid #4fc3f7; border-radius: 2px;")
_HIGHLIGHT_MS    = 1500   # highlight duration in milliseconds

_OVERLAY_STYLE = """
    QFrame#{name} {{
        background-color: #0d1b26;
        border: 1px solid #4fc3f7;
        border-radius: 6px;
    }}
    QLabel               {{ color: #cfd8dc; font-size: 11px; }}
    QLabel#ov_title      {{ color: #4fc3f7; font-weight: bold;
                            font-size: 12px; padding-bottom: 3px; }}
    QLabel#ov_value      {{ color: #80cbc4; }}
    QDoubleSpinBox {{
        background-color: #1c2733;
        border: 1px solid #546e7a;
        color: #80cbc4;
        padding: 2px 2px;
        border-radius: 2px;
        font-size: 11px;
        max-width: 68px;
    }}
    QDoubleSpinBox:focus {{ border: 1px solid #4fc3f7; }}
"""


class ReadingsOverlay(QFrame):
    """Dark floating panel — live sensor readings, top-right of diagram."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("readings_overlay")
        self.setStyleSheet(_OVERLAY_STYLE.format(name="readings_overlay"))
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        layout.setColumnMinimumWidth(1, 76)

        title = QLabel("Live Readings")
        title.setObjectName("ov_title")
        layout.addWidget(title, 0, 0, 1, 2)

        def row(label: str, idx: int) -> QLabel:
            name = QLabel(label)
            val  = QLabel("—")
            val.setObjectName("ov_value")
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(name, idx + 1, 0)
            layout.addWidget(val,  idx + 1, 1)
            return val

        self._lbl_t_hx    = row("T_hx  (°C)",         0)
        self._lbl_t_out   = row("T_out  (°C)",         1)
        self._lbl_valve   = row("Valve  (%)",           2)
        self._lbl_ca_in   = row("Ca_in  (mol/L)",      3)
        self._lbl_cb_in   = row("Cb_in  (mol/L)",      4)
        self._lbl_ca_out  = row("Ca_out (mol/L)",      5)
        self._lbl_cb_out  = row("Cb_out (mol/L)",      6)
        self._lbl_x_out   = row("X_out  (-)",          7)
        self._lbl_conduct = row("Conduct. (mS/cm)",    8)
        self._lbl_u       = row("u  (m/s)",            9)
        self._lbl_tau     = row("τ = L/u  (s)",       10)

        self.adjustSize()

    def update_readings(self, snap: EngineSnapshot) -> None:
        tau = PFR_LENGTH / snap.velocity if snap.velocity > 0 else float("inf")
        self._lbl_t_hx.setText(f"{snap.T_hx    - K2C:.1f}")
        self._lbl_t_out.setText(f"{snap.T_out   - K2C:.1f}")
        self._lbl_valve.setText(f"{snap.valve   * 100:.1f}")
        self._lbl_ca_in.setText(f"{snap.CA_in:.4f}")
        self._lbl_cb_in.setText(f"{snap.CB_in:.4f}")
        self._lbl_ca_out.setText(f"{snap.CA_out:.4f}")
        self._lbl_cb_out.setText(f"{snap.CB_out:.4f}")
        self._lbl_x_out.setText(f"{snap.X_out:.4f}")
        self._lbl_conduct.setText(f"{snap.conductivity:.4f}")
        self._lbl_u.setText(f"{snap.velocity:.4f}")
        self._lbl_tau.setText(f"{tau:.1f}")


# Backward-compat alias so any existing import of ReadingsPanel still works.
ReadingsPanel = ReadingsOverlay


class ParametersOverlay(QFrame):
    """Dark floating panel — editable process parameters, bottom-right of diagram."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("params_overlay")
        self.setStyleSheet(_OVERLAY_STYLE.format(name="params_overlay"))
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)
        layout.setColumnMinimumWidth(1, 72)

        title = QLabel("Parameters")
        title.setObjectName("ov_title")
        layout.addWidget(title, 0, 0, 1, 2)

        def row(label: str, idx: int,
                min_v, max_v, step, dec, default) -> QDoubleSpinBox:
            lbl  = QLabel(label)
            spin = QDoubleSpinBox()
            spin.setRange(min_v, max_v)
            spin.setSingleStep(step)
            spin.setDecimals(dec)
            spin.setValue(default)
            spin.valueChanged.connect(lambda _: spin.setStyleSheet(_SPIN_DIRTY))
            layout.addWidget(lbl,  idx + 1, 0)
            layout.addWidget(spin, idx + 1, 1)
            return spin

        self._spin_qa  = row("Qa  (mL/min)", 0, 0.001, 600.0, 0.1, 2,
                             DEFAULT_FEED_A_FLOW * _ML_MIN)
        self._spin_ca  = row("Ca  (mol/L)",  1, 0.0,   20.0,  0.1, 3,
                             DEFAULT_CA_FEED)
        self._spin_qb  = row("Qb  (mL/min)", 2, 0.001, 600.0, 0.1, 2,
                             DEFAULT_FEED_B_FLOW * _ML_MIN)
        self._spin_cb  = row("Cb  (mol/L)",  3, 0.0,   20.0,  0.1, 3,
                             DEFAULT_CB_FEED)
        self._spin_tsp = row("T_sp  (°C)",   4, 5.0,   89.0,  1.0, 1,
                             DEFAULT_T_IN_SETPOINT - K2C)

        self._all_spins = [
            self._spin_qa, self._spin_ca,
            self._spin_qb, self._spin_cb,
            self._spin_tsp,
        ]
        self._spin_map = {
            'qa':  self._spin_qa,
            'ca':  self._spin_ca,
            'qb':  self._spin_qb,
            'cb':  self._spin_cb,
            'tsp': self._spin_tsp,
        }
        self.adjustSize()

    def highlight_row(self, key: str) -> None:
        """Briefly flash the spinbox matching key with a cyan border."""
        spin = self._spin_map.get(key)
        if spin is None:
            return
        was_dirty = spin.styleSheet() == _SPIN_DIRTY
        spin.setStyleSheet(_SPIN_HIGHLIGHT)
        QTimer.singleShot(
            _HIGHLIGHT_MS,
            lambda: spin.setStyleSheet(_SPIN_DIRTY if was_dirty else _SPIN_CLEAN),
        )

    def get_params(self) -> dict:
        return {
            'Qa0':           self._spin_qa.value()  / _ML_MIN,
            'Ca0':           self._spin_ca.value(),
            'Qb0':           self._spin_qb.value()  / _ML_MIN,
            'Cb0':           self._spin_cb.value(),
            'T_in_setpoint': self._spin_tsp.value() + K2C,
        }

    def mark_clean(self) -> None:
        for spin in self._all_spins:
            spin.setStyleSheet(_SPIN_CLEAN)
