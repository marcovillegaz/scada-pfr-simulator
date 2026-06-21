from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox, QVBoxLayout,
    QLabel,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont


class PIDDialog(QDialog):
    """
    Popup dialog for editing PID controller gains (Kp, Ki, Kd).
    Opened when the user clicks the P-103/valve hitbox on the P&ID diagram.
    Emits pid_changed(dict) on OK; emits nothing on Cancel.
    """

    pid_changed = pyqtSignal(dict)

    def __init__(self, kp: float, ki: float, kd: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("HX Temperature Controller — PID Gains")
        self.setFixedWidth(280)
        self._build_ui(kp, ki, kd)

    def _build_ui(self, kp: float, ki: float, kd: float) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        hint = QLabel("Adjust the PID gains for the hot-water valve controller.\n"
                       "Changes apply immediately on OK.")
        hint.setWordWrap(True)
        hint.setFont(QFont("Consolas", 8))
        layout.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(6)

        def sb(val: float, lo: float, hi: float, step: float, dec: int) -> QDoubleSpinBox:
            w = QDoubleSpinBox()
            w.setRange(lo, hi)
            w.setSingleStep(step)
            w.setDecimals(dec)
            w.setValue(val)
            return w

        self._spin_kp = sb(kp, 0.0, 10.0, 0.005, 4)
        self._spin_ki = sb(ki, 0.0,  5.0, 0.001, 4)
        self._spin_kd = sb(kd, 0.0,  2.0, 0.001, 4)

        form.addRow("Kp  (valve / K)",    self._spin_kp)
        form.addRow("Ki  (valve / K·s)",  self._spin_ki)
        form.addRow("Kd  (valve · s / K)", self._spin_kd)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_ok(self) -> None:
        self.pid_changed.emit({
            'Kp': self._spin_kp.value(),
            'Ki': self._spin_ki.value(),
            'Kd': self._spin_kd.value(),
        })
        self.accept()
