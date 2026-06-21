from __future__ import annotations

import os

from PyQt6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QLabel, QDoubleSpinBox, QAbstractSpinBox,
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPainter, QCursor, QColor
from PyQt6.QtCore import Qt, QRect, QRectF, pyqtSignal

from constants import (
    K2C,
    DEFAULT_FEED_A_FLOW, DEFAULT_FEED_B_FLOW,
    DEFAULT_CA_FEED, DEFAULT_CB_FEED,
    DEFAULT_T_IN_SETPOINT,
)
from engine.data_store import EngineSnapshot
from ui.panels.readings_panel import ReadingsOverlay
from ui.widgets.status_card import StatusCard
from ui.widgets.event_log_panel import EventLogPanel

_SVG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 '..', '..', '..', 'images', 'P&ID.svg')
)

_OVERLAY_MARGIN = 10
_FRAME_MARGIN   = 14
_DIAGRAM_BG     = QColor(0xE9, 0xF1, 0xF5)
_ML_MIN         = 60_000_000.0

# ── Action hitboxes (parent widget handles mouse events) ──────────────────────

_ACTION_BOXES: dict[str, str] = {
    'conductivity_indicator': 'sensor_info',
    'heater_pump_valve':      'pid',
    'temp_controller':        'pid',
    # PFR reactor body — approximate; refine with a mask SVG
    'pfr_tube':               'reactor_info',
}

_HITBOXES: dict[str, QRectF] = {
    'conductivity_indicator': QRectF(0.6479, 0.7041, 0.0352, 0.0497),
    'heater_pump_valve':      QRectF(0.2431, 0.7432, 0.0847, 0.0521),
    'temp_controller':        QRectF(0.5951, 0.5243, 0.0352, 0.0497),
    # PFR reactor body — approximate; refine with a mask SVG
    'pfr_tube':               QRectF(0.3200, 0.2200, 0.2400, 0.5000),
}

# ── Editable value boxes ──────────────────────────────────────────────────────
# (min, max, step, decimals, default, format_string)

_EDITABLE_CFG: dict[str, tuple] = {
    'Qa':                     (0.001, 600.0, 0.1, 2, DEFAULT_FEED_A_FLOW * _ML_MIN, '{:.2f}'),
    'Ca':                     (0.0,    20.0, 0.1, 3, DEFAULT_CA_FEED,               '{:.3f}'),
    'Qb':                     (0.001, 600.0, 0.1, 2, DEFAULT_FEED_B_FLOW * _ML_MIN, '{:.2f}'),
    'Cb':                     (0.0,    20.0, 0.1, 3, DEFAULT_CB_FEED,               '{:.3f}'),
    'tsp':                    (5.0,    89.0, 1.0, 1, DEFAULT_T_IN_SETPOINT - K2C,   '{:.1f}'),
    'water_tank_temperature': (20.0,  100.0, 1.0, 1, 90.0,                          '{:.1f}'),
}

_EDITABLE_RECTS: dict[str, QRectF] = {
    'Qa':                     QRectF(0.2277, 0.1985, 0.0673, 0.0333),
    'Ca':                     QRectF(0.0593, 0.1985, 0.0673, 0.0333),
    'Qb':                     QRectF(0.2277, 0.4789, 0.0673, 0.0333),
    'Cb':                     QRectF(0.0593, 0.4789, 0.0673, 0.0333),
    'tsp':                    QRectF(0.5792, 0.4828, 0.0673, 0.0333),
    'water_tank_temperature': QRectF(0.0816, 0.8057, 0.0673, 0.0333),
}

# ── Read-only display boxes ───────────────────────────────────────────────────

_READONLY_RECTS: dict[str, QRectF] = {
    'conductivity_box': QRectF(0.6323, 0.8086, 0.0673, 0.0333),
    'valve_indicator':  QRectF(0.2889, 0.7054, 0.0673, 0.0333),
}

_READONLY_FMT: dict[str, str] = {
    'conductivity_box': '{:.4f}',
    'valve_indicator':  '{:.1f}',
}


# ── DiagramBox ────────────────────────────────────────────────────────────────

class DiagramBox(QFrame):
    """
    Tiny value box overlaid on a P&ID diagram box area.

    editable=True  → yellow background; click to edit inline via spinbox;
                     cyan border signals a pending (not-yet-applied) change.
    editable=False → blue-gray background; updated from live sensor readings.
    """

    _BG_CLEAN    = "#fffde7"   # yellow — editable, value matches engine
    _BG_DIRTY    = "#fff9c4"   # pale — editable, change pending Apply
    _BG_ACTIVE   = "#ffffff"   # white — spinbox focused
    _BG_READONLY = "#e3f2fd"   # light blue — read-only

    _BR_CLEAN    = "#f9a825"   # amber border — clean editable
    _BR_DIRTY    = "#4fc3f7"   # cyan border  — dirty / active
    _BR_READONLY = "#90caf9"   # blue border  — read-only

    def __init__(self, editable: bool, fmt: str = "{:.2f}", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._editable = editable
        self._fmt      = fmt
        self._dirty    = False
        self._value    = 0.0
        self._build_ui()
        self._refresh_style()
        if editable:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _build_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 0, 2, 0)
        lay.setSpacing(0)

        self._label = QLabel("—")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            "font-size: 10px; color: #212121; background: transparent;"
        )
        lay.addWidget(self._label)

        if self._editable:
            self._spin = QDoubleSpinBox()
            self._spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            self._spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._spin.setStyleSheet(
                "font-size: 10px; color: #212121; border: none; background: transparent;"
            )
            self._spin.hide()
            self._spin.editingFinished.connect(self._commit)
            lay.addWidget(self._spin)

    def configure(self, min_v, max_v, step, dec, default) -> None:
        self._value = default
        self._label.setText(self._fmt.format(default))
        if self._editable:
            self._spin.setRange(min_v, max_v)
            self._spin.setSingleStep(step)
            self._spin.setDecimals(dec)
            self._spin.setValue(default)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_value(self, v: float) -> None:
        """For read-only boxes: update the displayed value every tick."""
        self._value = v
        if not (self._editable and self._spin.isVisible()):
            self._label.setText(self._fmt.format(v))

    def get_value(self) -> float:
        return self._value

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def mark_clean(self) -> None:
        self._dirty = False
        self._refresh_style()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _refresh_style(self) -> None:
        if not self._editable:
            bg, br = self._BG_READONLY, self._BR_READONLY
            bw = 1
        elif self._dirty:
            bg, br = self._BG_DIRTY, self._BR_DIRTY
            bw = 2
        else:
            bg, br = self._BG_CLEAN, self._BR_CLEAN
            bw = 1
        self.setStyleSheet(
            f"QFrame{{background:{bg};border:{bw}px solid {br};border-radius:2px;}}"
        )

    def mousePressEvent(self, event) -> None:
        if self._editable and event.button() == Qt.MouseButton.LeftButton:
            self._enter_edit()
        super().mousePressEvent(event)

    def _enter_edit(self) -> None:
        if self._spin.isVisible():
            return
        self._spin.setValue(self._value)
        self._label.hide()
        self._spin.show()
        self._spin.setFocus()
        self._spin.selectAll()
        self.setStyleSheet(
            f"QFrame{{background:{self._BG_ACTIVE};"
            f"border:2px solid {self._BR_DIRTY};border-radius:2px;}}"
        )

    def _commit(self) -> None:
        """Called when Enter is pressed or the spinbox loses focus."""
        self._value = self._spin.value()
        self._label.setText(self._fmt.format(self._value))
        self._spin.hide()
        self._label.show()
        self._dirty = True
        self._refresh_style()


# ── PFRDiagramWidget ──────────────────────────────────────────────────────────

class PFRDiagramWidget(QWidget):
    pid_change_requested      = pyqtSignal()
    sensor_info_requested     = pyqtSignal()
    reactor_info_requested    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

        self._renderer = QSvgRenderer(_SVG_PATH, self)
        vb = self._renderer.viewBoxF()
        self._vb_w = vb.width()  or 842.0
        self._vb_h = vb.height() or 595.0

        self._hover_key: str | None = None

        # ReadingsOverlay — kept in code for internal tracking; hidden from students.
        # Set self._overlay.show() here to re-enable in a future debug/admin mode.
        self._overlay = ReadingsOverlay(self)
        self._overlay.hide()

        # Editable parameter boxes
        self._editable_boxes: dict[str, DiagramBox] = {}
        for key, (mn, mx, step, dec, default, fmt) in _EDITABLE_CFG.items():
            box = DiagramBox(editable=True, fmt=fmt, parent=self)
            box.configure(mn, mx, step, dec, default)
            self._editable_boxes[key] = box

        # Read-only display boxes
        self._readonly_boxes: dict[str, DiagramBox] = {}
        for key, fmt in _READONLY_FMT.items():
            box = DiagramBox(editable=False, fmt=fmt, parent=self)
            self._readonly_boxes[key] = box

        # Upper-right overlay panels (each is independently hide()-able)
        self._status_card = StatusCard(self)
        self._event_log   = EventLogPanel(self)

    # ── Coordinate helpers ────────────────────────────────────────────────────

    def _transform(self) -> tuple[float, float, float]:
        avail_w = self.width()  - 2 * _FRAME_MARGIN
        avail_h = self.height() - 2 * _FRAME_MARGIN
        sc = min(avail_w / self._vb_w, avail_h / self._vb_h)
        ox = (self.width()  - self._vb_w * sc) / 2.0
        oy = (self.height() - self._vb_h * sc) / 2.0
        return sc, ox, oy

    def _svgrect(self, r: QRectF) -> QRect:
        sc, ox, oy = self._transform()
        return QRect(
            int(ox + r.x() * self._vb_w * sc),
            int(oy + r.y() * self._vb_h * sc),
            max(1, int(r.width()  * self._vb_w * sc)),
            max(1, int(r.height() * self._vb_h * sc)),
        )

    def _key_at(self, pos) -> str | None:
        for key, r in _HITBOXES.items():
            if self._svgrect(r).contains(pos):
                return key
        return None

    # ── Child positioning ─────────────────────────────────────────────────────

    def _reposition_children(self) -> None:
        sc, ox, oy = self._transform()

        # Hidden readings overlay — keep positioned but invisible
        svg_right = ox + self._vb_w * sc
        self._overlay.adjustSize()
        self._overlay.move(
            int(svg_right - self._overlay.width()  - _OVERLAY_MARGIN),
            int(oy + _OVERLAY_MARGIN),
        )

        # Upper-right overlay panels anchored to SVG right edge
        card_x = int(svg_right - StatusCard.FIXED_W - _OVERLAY_MARGIN)
        card_y = int(oy + _OVERLAY_MARGIN)
        self._status_card.move(card_x, card_y)
        self._event_log.move(card_x, card_y + StatusCard.FIXED_H + 4)

        for key, box in self._editable_boxes.items():
            box.setGeometry(self._svgrect(_EDITABLE_RECTS[key]))

        for key, box in self._readonly_boxes.items():
            box.setGeometry(self._svgrect(_READONLY_RECTS[key]))

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), _DIAGRAM_BG)
        sc, ox, oy = self._transform()
        self._renderer.render(p, QRectF(ox, oy, self._vb_w * sc, self._vb_h * sc))

        if self._hover_key:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(79, 195, 247, 60))
            p.drawRect(self._svgrect(_HITBOXES[self._hover_key]))

    # ── Events ────────────────────────────────────────────────────────────────

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_children()

    def mouseMoveEvent(self, event) -> None:
        key = self._key_at(event.pos())
        if key != self._hover_key:
            self._hover_key = key
            self.setCursor(QCursor(
                Qt.CursorShape.PointingHandCursor if key
                else Qt.CursorShape.ArrowCursor
            ))
            self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        key = self._key_at(event.pos())
        if key is None:
            return
        action = _ACTION_BOXES.get(key)
        if action == 'pid':
            self.pid_change_requested.emit()
        elif action == 'sensor_info':
            self.sensor_info_requested.emit()
        elif action == 'reactor_info':
            self.reactor_info_requested.emit()

    # ── Public API ────────────────────────────────────────────────────────────

    def update_readings(self, snap: EngineSnapshot) -> None:
        self._overlay.update_readings(snap)
        self._readonly_boxes['conductivity_box'].set_value(snap.conductivity)
        self._readonly_boxes['valve_indicator'].set_value(snap.valve * 100)
        self._status_card.update_readings(snap)
        self._event_log.update_readings(snap)

    def add_event(self, sim_time: float, text: str, level: str = "info") -> None:
        self._event_log.add_event(sim_time, text, level)

    def clear_events(self) -> None:
        self._event_log.clear()

    def get_params(self) -> dict:
        eb = self._editable_boxes
        return {
            'Qa':            eb['Qa'].get_value()  / _ML_MIN,
            'CA_feed':       eb['Ca'].get_value(),
            'Qb':            eb['Qb'].get_value()  / _ML_MIN,
            'CB_feed':       eb['Cb'].get_value(),
            'T_in_setpoint': eb['tsp'].get_value() + K2C,
        }

    def mark_params_clean(self) -> None:
        for box in self._editable_boxes.values():
            box.mark_clean()
