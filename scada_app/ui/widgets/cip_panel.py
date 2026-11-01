from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal

from constants import RTD_REACTORS

_BG = "rgba(38,38,38,220)"
_BD = "#525252"
_TITLE_SS  = "color:#E95420;font-size:10px;font-weight:bold;background:transparent;border:none;"
_STATUS_SS = "color:#eeeeec;font-size:10px;background:transparent;border:none;"
_SEP_SS    = "color:#525252;background:#525252;max-height:1px;border:none;"

_BTN_IDLE_SS = (
    "QPushButton{background:#3a3a3a;color:#adadad;border:1px solid #525252;"
    "border-radius:3px;padding:4px;}"
    "QPushButton:hover{color:#eeeeec;border-color:#6e6e6e;}"
)
_BTN_ACTIVE_SS = (
    "QPushButton{background:#E95420;color:#ffffff;border:1px solid #E95420;"
    "border-radius:3px;padding:4px;font-weight:bold;}"
)


class CIPPanel(QFrame):
    """
    CIP (Clean-In-Place) protocol controls: one toggle button per reactor
    (R-102/103/104) to isolate it for washing, plus a status line.

    Selecting a reactor is the CIP equivalent of the old scenario picker --
    it switches which packed-bed model (plant) the RTD engine runs and
    which CIP diagram is shown. With no reactor selected the plant sits in
    normal operation (all three reactors online, no injection available).
    """

    reactor_selected = pyqtSignal(str)   # scenario_id; '' = back to normal operation

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setStyleSheet(
            f"QFrame{{background-color:{_BG};border:1px solid {_BD};border-radius:4px;}}"
        )
        self._active_reactor = ""   # tag, '' = normal operation
        self._reactor_btns: dict[str, QPushButton] = {}
        self._scenario_by_tag: dict[str, str] = {
            tag: scenario_id for tag, scenario_id, _svg in RTD_REACTORS
        }
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(10, 7, 10, 7)
        vlay.setSpacing(6)

        title = QLabel("CIP PROTOCOL")
        title.setStyleSheet(_TITLE_SS)
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(_SEP_SS)
        vlay.addWidget(sep)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        for tag, _scenario_id, _svg in RTD_REACTORS:
            btn = QPushButton(tag)
            btn.setStyleSheet(_BTN_IDLE_SS)
            btn.clicked.connect(lambda _, t=tag: self._on_reactor_clicked(t))
            btn_row.addWidget(btn)
            self._reactor_btns[tag] = btn
        vlay.addLayout(btn_row)

        self._lbl_status = QLabel("System: Normal operation")
        self._lbl_status.setStyleSheet(_STATUS_SS)
        self._lbl_status.setWordWrap(True)
        vlay.addWidget(self._lbl_status)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_reactor_clicked(self, tag: str) -> None:
        # Clicking the already-active reactor deselects it (back to normal).
        new_active = "" if tag == self._active_reactor else tag
        self._active_reactor = new_active
        self._refresh_buttons()
        self.reactor_selected.emit(self._scenario_by_tag.get(new_active, ""))

    def _refresh_buttons(self) -> None:
        for tag, btn in self._reactor_btns.items():
            btn.setStyleSheet(_BTN_ACTIVE_SS if tag == self._active_reactor else _BTN_IDLE_SS)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_status_text(self, text: str) -> None:
        self._lbl_status.setText(text)

    def set_reactor_buttons_enabled(self, enabled: bool) -> None:
        """Disable switching reactors while a run is in progress -- mirrors
        the old plant combo's disable-while-running behaviour."""
        for btn in self._reactor_btns.values():
            btn.setEnabled(enabled)

    def reset(self) -> None:
        self._active_reactor = ""
        self._refresh_buttons()
        self._lbl_status.setText("System: Normal operation")
