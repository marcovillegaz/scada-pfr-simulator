from __future__ import annotations

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFileDialog, QSizePolicy,
)
from PyQt6.QtCore import Qt

from constants import K2C, ALARM_T_HIGH_C, ALARM_T_LOW_C, ALARM_X_LOW
from engine.data_store import EngineSnapshot

_BG = "rgba(38,38,38,220)"
_BD = "#525252"

_MAX_EVENTS = 12

# Auto-detected alarm conditions (key, condition_fn, full label)
_ALARM_DEFS: dict[str, tuple] = {
    "HIGH_TEMP": (lambda s: (s.T_out - K2C) > ALARM_T_HIGH_C,                     "High Temperature"),
    "LOW_TEMP":  (lambda s: (s.T_out - K2C) < ALARM_T_LOW_C and s.sim_time > 10,  "Low Temperature"),
    "LOW_CONV":  (lambda s: s.X_out < ALARM_X_LOW and s.sim_time > 60,             "Low Conversion"),
}

_LEVEL_COLOR = {
    "alarm": "#e01b24",   # Ubuntu error red
    "clr":   "#26A269",   # Ubuntu success green
    "info":  "#adadad",   # Ubuntu secondary text
}


class EventLogPanel(QFrame):
    """
    Scrollable list of process events and alarms (max 12 entries).
    Sized by its parent container — suitable for both overlay and sidebar use.

    External API:
        add_event(sim_time, text, level="info")   — called from app layer
        update_readings(snap)                      — called every tick
        clear()                                    — called on reset
    Alarm thresholds read from constants.py: ALARM_T_HIGH_C, ALARM_T_LOW_C, ALARM_X_LOW.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            f"QFrame{{background-color:{_BG};border:1px solid {_BD};border-radius:4px;}}"
        )
        self._events: list[tuple[str, str, str]] = []   # (ts_str, text, level)
        self._prev_alarms: set[str] = set()
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(8, 6, 8, 6)
        vlay.setSpacing(3)

        # ── Title row + Export button ─────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(4)

        title = QLabel("EVENT LOG")
        title.setStyleSheet(
            "color:#E95420;font-size:10px;font-weight:bold;"
            "background:transparent;border:none;"
        )
        hdr.addWidget(title)
        hdr.addStretch()

        export_btn = QPushButton("Export")
        export_btn.setFixedHeight(17)
        export_btn.setStyleSheet(
            "QPushButton{font-size:9px;padding:0 6px;min-width:0;border-radius:2px;"
            "background:#37474f;border:1px solid #546e7a;color:#b0bec5;}"
            "QPushButton:hover{background:#455a64;}"
        )
        export_btn.clicked.connect(self._on_export)
        hdr.addWidget(export_btn)
        vlay.addLayout(hdr)

        # ── Separator ─────────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2d3f50;background:#2d3f50;max-height:1px;border:none;")
        vlay.addWidget(sep)

        # ── Scrollable event rows ─────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._scroll.setStyleSheet(
            "QScrollArea{background:transparent;border:none;}"
            "QScrollArea > QWidget > QWidget{background:transparent;}"
        )

        container = QWidget()
        container.setStyleSheet("background:transparent;")
        clay = QVBoxLayout(container)
        clay.setContentsMargins(0, 1, 0, 1)
        clay.setSpacing(2)

        self._rows: list[QLabel] = []
        for _ in range(_MAX_EVENTS):
            lbl = QLabel("")
            lbl.setStyleSheet(
                "color:#546e7a;font-size:9px;background:transparent;border:none;"
            )
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            clay.addWidget(lbl)
            self._rows.append(lbl)

        clay.addStretch()
        self._scroll.setWidget(container)
        vlay.addWidget(self._scroll)

    # ── Public API ────────────────────────────────────────────────────────────

    def add_event(self, sim_time: float, text: str, level: str = "info") -> None:
        self._events.append((f"{sim_time:5.1f}s", text, level))
        if len(self._events) > _MAX_EVENTS:
            self._events = self._events[-_MAX_EVENTS:]
        self._refresh_rows()
        self._scroll.verticalScrollBar().setValue(0)   # newest always visible

    def update_readings(self, snap: EngineSnapshot) -> None:
        current = {k for k, (cond, _) in _ALARM_DEFS.items() if cond(snap)}
        for k in sorted(current - self._prev_alarms):
            self.add_event(snap.sim_time, _ALARM_DEFS[k][1] + " Alarm", "alarm")
        for k in sorted(self._prev_alarms - current):
            self.add_event(snap.sim_time, _ALARM_DEFS[k][1] + " Cleared", "clr")
        self._prev_alarms = current

    def clear(self) -> None:
        self._events.clear()
        self._prev_alarms.clear()
        self._refresh_rows()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _refresh_rows(self) -> None:
        recent = list(reversed(self._events))   # newest at top
        for i, lbl in enumerate(self._rows):
            if i < len(recent):
                ts, text, level = recent[i]
                color = _LEVEL_COLOR.get(level, "#90a4ae")
                lbl.setText(f"{ts}  {text}")
                lbl.setStyleSheet(
                    f"color:{color};font-size:9px;background:transparent;border:none;"
                )
            else:
                lbl.setText("")
                lbl.setStyleSheet(
                    "color:#546e7a;font-size:9px;background:transparent;border:none;"
                )

    def _on_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Event Log", "event_log.txt", "Text files (*.txt)"
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write("SCADA Event Log\n")
            f.write("=" * 40 + "\n")
            for ts, text, level in self._events:   # oldest → newest
                tag = {"alarm": "ALM", "clr": "CLR", "info": "INF"}.get(level, "INF")
                f.write(f"[{tag}] {ts}  {text}\n")
