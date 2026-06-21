from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt


_INFO: list[tuple[str, str]] = [
    ("Tag",               "CT-101"),
    ("Type",              "Conductivity transmitter"),
    ("Brand",             "—"),
    ("Model",             "—"),
    ("Serial no.",        "—"),
    ("Measurement range", "0 – 20 mS/cm"),
    ("Last calibration",  "—"),
    ("Next calibration",  "—"),
]


class SensorInfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CT-101 — Sensor Information")
        self.setFixedWidth(340)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setSpacing(10)

        title = QLabel("Conductivity Sensor  CT-101")
        title.setStyleSheet("color: #4fc3f7; font-weight: bold; font-size: 13px;")
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2d3f50;")
        vlay.addWidget(sep)

        form = QFormLayout()
        form.setSpacing(6)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        for field, value in _INFO:
            lbl_field = QLabel(field)
            lbl_field.setStyleSheet("color: #78909c; font-size: 11px;")
            lbl_value = QLabel(value)
            lbl_value.setStyleSheet("color: #cfd8dc; font-size: 11px;")
            form.addRow(lbl_field, lbl_value)
        vlay.addLayout(form)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("btn_apply")
        close_btn.clicked.connect(self.accept)
        vlay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
