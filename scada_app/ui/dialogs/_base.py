from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QPushButton, QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt

"""Shared chrome + field/value styling for the equipment "nameplate data"
popups opened from the P&ID diagrams (ReactorInfoDialog, SensorInfoDialog,
HXInfoDialog, TCInfoDialog, RTDReactorInfoDialog, RTDSensorInfoDialog) --
every one of those dialogs was an independent copy of this exact pattern."""


def lbl(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet("color:#adadad;font-size:11px;")
    return l


def val(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet("color:#eeeeec;font-size:11px;")
    return l


def form_box(title: str, rows: list[tuple[str, str]]) -> QGroupBox:
    """A QGroupBox of right-aligned field/value rows."""
    box = QGroupBox(title)
    form = QFormLayout(box)
    form.setSpacing(5)
    form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
    for field, value in rows:
        form.addRow(lbl(field), val(value))
    return box


def description_box(text: str, title: str = "How it works") -> QGroupBox:
    box = QGroupBox(title)
    lay = QVBoxLayout(box)
    label = QLabel(text)
    label.setWordWrap(True)
    label.setStyleSheet("color:#eeeeec;font-size:11px;")
    lay.addWidget(label)
    return box


class EquipmentInfoDialog(QDialog):
    """Base for equipment-info popups: fixed-width, no context-help button,
    an orange title + separator, and a right-aligned button row.

    Subclasses call `_add_title(text)`, add content via
    `self._layout.addWidget(...)`, optionally call `_add_button(btn)` for
    extra buttons left of Close, then call `_finish_buttons()` last.
    """

    def __init__(self, window_title: str, width: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setFixedWidth(width)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(10)
        self._btn_row: QHBoxLayout | None = None

    def _add_title(self, text: str) -> None:
        title = QLabel(text)
        title.setStyleSheet("color:#E95420;font-weight:bold;font-size:13px;")
        title.setWordWrap(True)
        self._layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2d3f50;")
        self._layout.addWidget(sep)

    def _add_button(self, button: QPushButton) -> None:
        if self._btn_row is None:
            self._btn_row = QHBoxLayout()
        self._btn_row.addWidget(button)

    def _finish_buttons(self) -> None:
        close_btn = QPushButton("Close")
        close_btn.setObjectName("btn_apply")
        close_btn.clicked.connect(self.accept)

        if self._btn_row is not None:
            self._btn_row.addStretch()
            self._btn_row.addWidget(close_btn)
            self._layout.addLayout(self._btn_row)
        else:
            self._layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
