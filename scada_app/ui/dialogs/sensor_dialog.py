from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QPushButton, QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt

class SensorInfoDialog(QDialog):
    """Equipment description panel for conductivity transmitter CT-101."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CT-101 — Equipment Info")
        self.setFixedWidth(400)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setSpacing(10)

        title = QLabel("CT-101  —  Conductivity Transmitter")
        title.setStyleSheet("color:#E95420;font-weight:bold;font-size:13px;")
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2d3f50;")
        vlay.addWidget(sep)

        vlay.addWidget(self._instrument_box())
        vlay.addWidget(self._calibration_box())
        vlay.addWidget(self._description_box())

        close_btn = QPushButton("Close")
        close_btn.setObjectName("btn_apply")
        close_btn.clicked.connect(self.accept)
        vlay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _instrument_box(self) -> QGroupBox:
        box = QGroupBox("Instrument Data")
        form = QFormLayout(box)
        form.setSpacing(5)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        rows = [
            ("Tag",               "CT-101"),
            ("Type",              "Conductivity Transmitter"),
            ("Brand",             "Mettler Toledo"),
            ("Model",             "Thornton 200CR"),
            ("Measurement principle", "Two-electrode conductometric"),
            ("Electrode material","Platinum (Pt), epoxy-sealed"),
            ("Range",             "0 – 20 mS/cm"),
            ("Accuracy",          "± 0.5 %  full scale"),
            ("Temp. compensation","Automatic, 0 – 50 °C  (NTC element)"),
            ("Output",            "4 – 20 mA  (linear over range)"),
            ("Process connection","Inline, 1/2\" NPT, flush-mount"),
        ]
        for field, value in rows:
            form.addRow(_lbl(field), _val(value))
        return box

    def _calibration_box(self) -> QGroupBox:
        box = QGroupBox("Calibration Model")
        form = QFormLayout(box)
        form.setSpacing(5)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        rows = [
            ("Model",             "σ  =  A · C_A  +  B"),
            ("A  (slope)",        "factory-calibrated"),
            ("B  (offset)",       "factory-calibrated"),
            ("Valid range",       "0 – 0.1 mol/L  (NaOH in product stream)"),
        ]
        for field, value in rows:
            form.addRow(_lbl(field), _val(value))
        return box

    def _description_box(self) -> QGroupBox:
        box = QGroupBox("How it works")
        lay = QVBoxLayout(box)
        text = QLabel(
            "Two platinum electrodes are flush-mounted in the outlet pipe. "
            "The transmitter applies a 1 kHz AC excitation across the electrodes "
            "and measures the resulting current. The impedance of the solution "
            "drops as the ionic concentration rises — the instrument converts this "
            "to conductivity in mS/cm.\n\n"
            "As the saponification reaction proceeds, sodium acetate (NaAc) "
            "accumulates in the outlet stream. NaAc is a strong electrolyte, so "
            "conductivity rises with conversion. The linear calibration model "
            "(σ = A · C_A + B) converts the conductivity reading back to the "
            "residual NaOH concentration C_A at the reactor outlet.\n\n"
            "A small Gaussian noise term is added to each reading to replicate "
            "real-world instrument noise — observe the slight fluctuation on "
            "the Graph tab while the simulation runs."
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
