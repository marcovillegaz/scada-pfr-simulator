from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QPushButton, QFrame, QGroupBox, QHBoxLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal

from constants import DEFAULT_PID_KP, DEFAULT_PID_KI, DEFAULT_PID_KD


class TCInfoDialog(QDialog):
    """Equipment description panel for temperature controller TC-101."""

    configure_pid_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TC-101 — Equipment Info")
        self.setFixedWidth(400)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setSpacing(10)

        title = QLabel("TC-101  —  Temperature Controller")
        title.setStyleSheet("color:#E95420;font-weight:bold;font-size:13px;")
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2d3f50;")
        vlay.addWidget(sep)

        vlay.addWidget(self._instrument_box())
        vlay.addWidget(self._description_box())

        btn_row = QHBoxLayout()
        btn_pid = QPushButton("Configure PID Gains…")
        btn_pid.setObjectName("btn_apply")
        btn_pid.clicked.connect(self.configure_pid_requested)

        btn_close = QPushButton("Close")
        btn_close.setObjectName("btn_apply")
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(btn_pid)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        vlay.addLayout(btn_row)

    def _instrument_box(self) -> QGroupBox:
        box = QGroupBox("Instrument Data")
        form = QFormLayout(box)
        form.setSpacing(5)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        rows = [
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
        ]
        for field, value in rows:
            form.addRow(_lbl(field), _val(value))
        return box

    def _description_box(self) -> QGroupBox:
        box = QGroupBox("How it works")
        lay = QVBoxLayout(box)
        text = QLabel(
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
        )
        text.setWordWrap(True)
        text.setStyleSheet("color:#eeeeec;font-size:11px;")
        lay.addWidget(text)
        return box


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lbl(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet("color:#adadad;font-size:11px;")
    return l

def _val(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet("color:#eeeeec;font-size:11px;")
    return l
