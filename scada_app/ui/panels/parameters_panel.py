from __future__ import annotations

from PyQt6.QtWidgets import (
    QGroupBox, QFormLayout, QDoubleSpinBox, QPushButton, QVBoxLayout,
)
from PyQt6.QtCore import pyqtSignal

from constants import (
    DEFAULT_FEED_CONCENTRATION, DEFAULT_FLOW_RATE, DEFAULT_SETPOINT,
    DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, DEFAULT_T_UTILITY_MAX,
)

DIRTY_STYLE = "background-color: #fff176; color: #333;"
CLEAN_STYLE = ""


class ParametersPanel(QGroupBox):
    parameters_applied = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__("Parameters", parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setSpacing(8)

        def spinbox(min_v, max_v, step, decimals, default) -> QDoubleSpinBox:
            sb = QDoubleSpinBox()
            sb.setRange(min_v, max_v)
            sb.setSingleStep(step)
            sb.setDecimals(decimals)
            sb.setValue(default)
            sb.valueChanged.connect(lambda _: self._mark_dirty(sb))
            return sb

        # ── Process group ────────────────────────────────────────────────
        process_box = QGroupBox("Process")
        process_layout = QVBoxLayout(process_box)
        process_layout.setSpacing(4)
        process_form = QFormLayout()
        process_form.setSpacing(4)

        self._spin_ca0      = spinbox(0.0,   10.0,   0.01, 3, DEFAULT_FEED_CONCENTRATION)
        self._spin_flow     = spinbox(0.0, 1000.0,   0.1,  2, DEFAULT_FLOW_RATE * 60000)
        self._spin_setpoint = spinbox(273.0, 600.0,  1.0,  1, DEFAULT_SETPOINT)

        process_form.addRow("Ca₀ (mol/L)",   self._spin_ca0)
        process_form.addRow("Flow (L/min)",  self._spin_flow)
        process_form.addRow("T Setpoint (K)", self._spin_setpoint)

        self._btn_apply_process = QPushButton("Apply")
        self._btn_apply_process.setObjectName("btn_apply")
        self._btn_apply_process.clicked.connect(self._on_apply_process)

        process_layout.addLayout(process_form)
        process_layout.addWidget(self._btn_apply_process)

        # ── Heat Exchanger & PID group ───────────────────────────────────
        heater_box = QGroupBox("Heat Exchanger & PID")
        heater_layout = QVBoxLayout(heater_box)
        heater_layout.setSpacing(4)
        heater_form = QFormLayout()
        heater_form.setSpacing(4)

        self._spin_maxpow = spinbox(273.0, 800.0, 1.0, 1, DEFAULT_T_UTILITY_MAX)
        self._spin_kp     = spinbox(0.0,  100.0,   0.1, 2, DEFAULT_KP)
        self._spin_ki     = spinbox(0.0,   50.0,  0.01, 3, DEFAULT_KI)
        self._spin_kd     = spinbox(0.0,   10.0, 0.001, 4, DEFAULT_KD)

        heater_form.addRow("T Util Max (K)", self._spin_maxpow)
        heater_form.addRow("Kp",             self._spin_kp)
        heater_form.addRow("Ki",             self._spin_ki)
        heater_form.addRow("Kd",             self._spin_kd)

        self._btn_apply_heater = QPushButton("Apply")
        self._btn_apply_heater.setObjectName("btn_apply")
        self._btn_apply_heater.clicked.connect(self._on_apply_heater)

        heater_layout.addLayout(heater_form)
        heater_layout.addWidget(self._btn_apply_heater)

        outer.addWidget(process_box)
        outer.addWidget(heater_box)

        self._process_spinboxes = [self._spin_ca0, self._spin_flow, self._spin_setpoint]
        self._heater_spinboxes  = [self._spin_maxpow, self._spin_kp, self._spin_ki, self._spin_kd]

    def _mark_dirty(self, sb: QDoubleSpinBox) -> None:
        sb.setStyleSheet(DIRTY_STYLE)

    def _clear_group(self, spinboxes: list) -> None:
        for sb in spinboxes:
            sb.setStyleSheet(CLEAN_STYLE)

    def _on_apply_process(self) -> None:
        params = {
            "feed_concentration": self._spin_ca0.value(),
            "flow_rate":          self._spin_flow.value() / 60000.0,
            "setpoint":           self._spin_setpoint.value(),
        }
        self._clear_group(self._process_spinboxes)
        self.parameters_applied.emit(params)

    def _on_apply_heater(self) -> None:
        params = {
            "T_utility_max": self._spin_maxpow.value(),
            "Kp":            self._spin_kp.value(),
            "Ki":            self._spin_ki.value(),
            "Kd":            self._spin_kd.value(),
        }
        self._clear_group(self._heater_spinboxes)
        self.parameters_applied.emit(params)
