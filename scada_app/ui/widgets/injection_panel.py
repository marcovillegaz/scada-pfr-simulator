from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal

from constants import RTD_PULSE_DOSE_DEFAULT, RTD_STEP_C0_DEFAULT

_BG = "rgba(38,38,38,220)"
_BD = "#525252"
_TITLE_SS = "color:#E95420;font-size:10px;font-weight:bold;background:transparent;border:none;"
_LABEL_SS = "color:#adadad;font-size:10px;background:transparent;border:none;"
_SEP_SS   = "color:#525252;background:#525252;max-height:1px;border:none;"


class InjectionPanel(QFrame):
    """
    Tracer injection controls: pulse dose + Inject button, step
    concentration + Start/Stop toggle.

    Deliberately a sidebar panel rather than an SVG diagram overlay --
    "inject pulse" / "start step" are momentary actions, not editable
    setpoints, so they don't fit the diagram's Apply-pending DiagramBox
    pattern (see ui/widgets/rtd_diagram.py).
    """

    pulse_requested       = pyqtSignal(float)   # dose (mol)
    step_start_requested  = pyqtSignal(float)   # C0 (mol/L)
    step_stop_requested   = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(
            f"QFrame{{background-color:{_BG};border:1px solid {_BD};border-radius:4px;}}"
        )
        self._step_active = False
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(10, 7, 10, 7)
        vlay.setSpacing(6)

        title = QLabel("TRACER INJECTION")
        title.setStyleSheet(_TITLE_SS)
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(_SEP_SS)
        vlay.addWidget(sep)

        # ── Pulse ──
        pulse_row = QHBoxLayout()
        pulse_row.addWidget(self._label("Dose (mol):"))
        self._spin_dose = QDoubleSpinBox()
        self._spin_dose.setRange(0.001, 1.0)
        self._spin_dose.setDecimals(3)
        self._spin_dose.setSingleStep(0.001)
        self._spin_dose.setValue(RTD_PULSE_DOSE_DEFAULT)
        pulse_row.addWidget(self._spin_dose)
        vlay.addLayout(pulse_row)

        self._btn_pulse = QPushButton("Inject Pulse")
        self._btn_pulse.clicked.connect(self._on_pulse_clicked)
        vlay.addWidget(self._btn_pulse)

        # ── Step ──
        step_row = QHBoxLayout()
        step_row.addWidget(self._label("C0 (mol/L):"))
        self._spin_c0 = QDoubleSpinBox()
        self._spin_c0.setRange(0.01, 10.0)
        self._spin_c0.setDecimals(2)
        self._spin_c0.setSingleStep(0.1)
        self._spin_c0.setValue(RTD_STEP_C0_DEFAULT)
        step_row.addWidget(self._spin_c0)
        vlay.addLayout(step_row)

        self._btn_step = QPushButton("Start Step")
        self._btn_step.clicked.connect(self._on_step_clicked)
        vlay.addWidget(self._btn_step)

    @staticmethod
    def _label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(_LABEL_SS)
        return lbl

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_pulse_clicked(self) -> None:
        self.pulse_requested.emit(self._spin_dose.value())

    def _on_step_clicked(self) -> None:
        if self._step_active:
            self.step_stop_requested.emit()
        else:
            self.step_start_requested.emit(self._spin_c0.value())

    # ── Public API ────────────────────────────────────────────────────────────

    def set_pulse_enabled(self, enabled: bool) -> None:
        """Disable re-injecting a pulse while any injection (pulse or step)
        is already in progress -- driven every tick from RTDSnapshot.injecting."""
        self._btn_pulse.setEnabled(enabled)

    def start_step_ui(self) -> None:
        self._step_active = True
        self._btn_step.setText("Stop Step")

    def stop_step_ui(self) -> None:
        self._step_active = False
        self._btn_step.setText("Start Step")

    def reset(self) -> None:
        self.stop_step_ui()
        self._btn_pulse.setEnabled(True)
