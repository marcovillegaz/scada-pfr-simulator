from __future__ import annotations

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPolygon, QFont
from PyQt6.QtCore import Qt, QPoint


class AlarmIndicator(QWidget):
    def __init__(self, label: str = "!", parent=None):
        super().__init__(parent)
        self._label   = label
        self._active  = False
        self.setFixedSize(36, 32)
        self.hide()

    def set_active(self, active: bool) -> None:
        if active != self._active:
            self._active = active
            self.setVisible(active)
            self.update()

    def paintEvent(self, event) -> None:
        if not self._active:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        triangle = QPolygon([
            QPoint(18, 2),
            QPoint(35, 30),
            QPoint(1,  30),
        ])
        p.setBrush(QColor("#FFC107"))
        p.setPen(QColor("#FF6F00"))
        p.drawPolygon(triangle)

        p.setPen(QColor("#333"))
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        p.setFont(font)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._label)
