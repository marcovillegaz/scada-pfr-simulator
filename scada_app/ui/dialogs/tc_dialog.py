from __future__ import annotations

from PyQt6.QtWidgets import QGroupBox, QPushButton
from PyQt6.QtCore import pyqtSignal

from constants import DEFAULT_PID_KP, DEFAULT_PID_KI, DEFAULT_PID_KD
from ui.dialogs._base import EquipmentInfoDialog, form_box, description_box


class TCInfoDialog(EquipmentInfoDialog):
    """Equipment description panel for temperature controller TC-101."""

    configure_pid_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("TC-101 — Equipment Info", width=400, parent=parent)
        self._add_title("TC-101  —  Temperature Controller")
        self._layout.addWidget(self._instrument_box())
        self._layout.addWidget(description_box(
            "TC-101 continuously compares the mean reactor temperature "
            "(T_reactor) with the operator setpoint. The difference is the "
            "control error e = T_sp − T_reactor.\n\n"
            "The PID output v = Kp·e + Ki·∫e dt + Kd·de/dt determines the "
            "opening of hot-water valve V-101, clamped between 0 (closed) "
            "and 1 (fully open). A more open valve delivers more heat to "
            "E-101 / E-102 → higher T_in → higher T_reactor.\n\n"
            "Anti-windup: if the valve is already fully open and the reactor "
            "is still too cold, the integral term is frozen — this prevents "
            "integral wind-up and the overshoot that would follow when "
            "conditions finally improve.\n\n"
            "Use 'Configure PID Gains' to tune Kp, Ki and Kd interactively "
            "while the simulation is running."
        ))

        btn_pid = QPushButton("Configure PID Gains…")
        btn_pid.setObjectName("btn_apply")
        btn_pid.clicked.connect(self.configure_pid_requested)
        self._add_button(btn_pid)
        self._finish_buttons()

    def _instrument_box(self) -> QGroupBox:
        return form_box("Instrument Data", [
            ("Tag",                  "TC-101"),
            ("Type",                 "Temperature Controller"),
            ("Algorithm",            "PID with clamped anti-windup"),
            ("Controlled variable",  "T_reactor  (mean reactor temperature)"),
            ("Measurement",          "T_reactor = (T_in + T_out) / 2"),
            ("Manipulated variable", "Hot-water valve V-101  (0 – 100 %)"),
            ("Setpoint source",      "Operator  (T_setpoint box on diagram)"),
            ("Default Kp",           f"{DEFAULT_PID_KP}  valve / K"),
            ("Default Ki",           f"{DEFAULT_PID_KI}  valve / (K·s)"),
            ("Default Kd",           f"{DEFAULT_PID_KD}"),
        ])
