from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel, QGroupBox
from PyQt6.QtCore import Qt

"""Widget-building helpers shared by docs_tab.py (PFR) and rtd_docs_tab.py
(RTD) -- both in-app documentation browsers compose their sub-tabs from the
same narrative/equation/tip/section/scroll-tab primitives."""


def narrative(text: str, rich: bool = False) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    if rich:
        lbl.setTextFormat(Qt.TextFormat.RichText)
    lbl.setStyleSheet("color:#eeeeec;font-size:12px;line-height:150%;")
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lbl


def equation(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(False)
    lbl.setStyleSheet(
        "color:#fdd835;font-family:Consolas,monospace;font-size:12px;"
        "background:#1e2a35;border-radius:4px;padding:8px;"
    )
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lbl


def tip(text: str) -> QLabel:
    lbl = QLabel(f"→  {text}")
    lbl.setWordWrap(True)
    lbl.setStyleSheet("color:#80cbc4;font-size:11px;font-style:italic;")
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lbl


def section(title: str, *widgets) -> QGroupBox:
    box = QGroupBox(title)
    lay = QVBoxLayout(box)
    lay.setSpacing(8)
    for w in widgets:
        lay.addWidget(w)
    return box


def scroll_tab(*groups) -> QScrollArea:
    inner = QWidget()
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(14, 14, 14, 14)
    lay.setSpacing(12)
    for g in groups:
        lay.addWidget(g)
    lay.addStretch()

    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setWidget(inner)
    area.setStyleSheet("QScrollArea{border:none;background:#1e2a35;}")
    return area
