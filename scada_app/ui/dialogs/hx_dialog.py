from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QPushButton, QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt

from constants import HX_VOLUME, UA_MAX, T_HOT_WATER, K2C


class HXInfoDialog(QDialog):
    """Equipment description panel for heat exchangers E-101 / E-102."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("E-101 / E-102 — Equipment Info")
        self.setFixedWidth(420)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setSpacing(10)

        title = QLabel("E-101 / E-102  —  Shell & Tube Heat Exchangers")
        title.setStyleSheet("color:#E95420;font-weight:bold;font-size:13px;")
        title.setWordWrap(True)
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2d3f50;")
        vlay.addWidget(sep)

        vlay.addWidget(self._design_box())
        vlay.addWidget(self._description_box())

        close_btn = QPushButton("Close")
        close_btn.setObjectName("btn_apply")
        close_btn.clicked.connect(self.accept)
        vlay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _design_box(self) -> QGroupBox:
        box = QGroupBox("Design Parameters")
        form = QFormLayout(box)
        form.setSpacing(5)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        rows = [
            ("Type",              "Shell & tube, single pass"),
            ("Configuration",     "Two units in parallel  (E-101 ∥ E-102)"),
            ("E-101 duty",        "Pre-heats Feed A  (Qa0, NaOH stream)"),
            ("E-102 duty",        "Pre-heats Feed B  (Qb0, EtAc stream)"),
            ("Utility",           f"Hot water  —  T = {T_HOT_WATER - K2C:.0f} °C  (shared supply)"),
            ("UA  max (combined)", f"{UA_MAX:.0f} W/K  (at full valve opening)"),
            ("Process holdup",    f"{HX_VOLUME * 1e3:.0f} L  (per unit, combined model)"),
            ("Control valve",     "V-101  —  hot-water flow  0 – 100 %"),
        ]
        for field, value in rows:
            form.addRow(_lbl(field), _val(value))
        return box

    def _description_box(self) -> QGroupBox:
        box = QGroupBox("How it works")
        lay = QVBoxLayout(box)
        text = QLabel(
            "Feed A (NaOH) and Feed B (EtAc) enter through separate pre-heaters "
            "E-101 and E-102 respectively. Both units draw from the same hot-water "
            "supply (60 °C) controlled by a single valve V-101.\n\n"
            "Opening the valve increases the heat transfer coefficient UA, "
            "raising the outlet temperature T_in of both streams. The heated "
            "streams then recombine at the mixing node before entering "
            "reactor R-101.\n\n"
            "The simulation models E-101 and E-102 as a single lumped heat "
            "exchanger node. Both streams are assumed to reach the same T_in "
            "at the mixing point — a valid approximation when the two flows "
            "are similar and the exchangers are thermally matched.\n\n"
            "TC-101 closes the control loop: it reads T_reactor and adjusts "
            "V-101 to maintain the operator setpoint."
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
