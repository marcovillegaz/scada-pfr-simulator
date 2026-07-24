from __future__ import annotations

from PyQt6.QtWidgets import QWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPainter, QColor, QCursor
from PyQt6.QtCore import Qt, QRect, QRectF, pyqtSignal

from constants import RTD_REACTORS, RTD_NORMAL_SVG, RTD_V106_OVERLAY_SVG
from engine.data_store import RTDSnapshot
from ui.widgets.pfr_diagram import DiagramBox
from resources import resource_path

_FRAME_MARGIN = 14
_DIAGRAM_BG   = QColor(0xE9, 0xF1, 0xF5)

_L_S_TO_L_MIN   = 60.0   # engine Q (L/s, the model's integration unit) -> displayed flow box (L/min)

# ── Editable value boxes: (min, max, step, decimals, default, format) ────────
# Flow box reads L/min (matches the hand-drawn "flow [L/min]" label under
# P-104 in the new CIP diagrams, and the scenario JSON's own Q_nominal_L_min)
# -- the same unit a real pump/flow-transmitter spec sheet would use. Only
# the model's internal integration (PackedBedRTD) works in L/s; that
# conversion happens once at the engine boundary (see rtd_engine.py), not
# here.
_EDITABLE_CFG: dict[str, tuple] = {
    'Q': (0.1, 6.0, 0.05, 2, 1.2, '{:.2f}'),
}
_EDITABLE_RECTS: dict[str, QRectF] = {
    'Q': QRectF(0.191, 0.611, 0.067, 0.033),
}

# ── Read-only display boxes: absorbance readout sits in the blank space
# just above the AT-101 sensor circle ───────────────────────────────────────
_READONLY_FMT: dict[str, str] = {
    'absorbance': '{:.4f}',
}
_READONLY_RECTS: dict[str, QRectF] = {
    'absorbance': QRectF(0.72, 0.34, 0.09, 0.05),
}

# ── Tracer band overlay (purely visual, timed by the nominal tau = V/Q --
# both visible quantities, no hidden RTD shape leaked) -- one horizontal
# rect per reactor body, inlet on the left / outlet on the right. Only
# drawn while a reactor is selected for CIP; normal operation shows none.
_REACTOR_BAND_RECTS: dict[str, QRectF] = {
    scenario_id: rect
    for (_tag, scenario_id, _svg), rect in zip(
        RTD_REACTORS,
        (
            QRectF(0.403, 0.230, 0.194, 0.050),   # R-102, top row
            QRectF(0.403, 0.474, 0.194, 0.050),   # R-103, middle row
            QRectF(0.403, 0.718, 0.194, 0.050),   # R-104, bottom row
        ),
    )
}
_BAND_PULSE_COLOR = QColor(0x5c, 0x4a, 0x8a, 205)
_BAND_FILL_COLOR  = QColor(0x5c, 0x4a, 0x8a, 110)

# ── Equipment info hitboxes (parent widget handles mouse events, mirrors
# PFRDiagramWidget's hitbox pattern) ──────────────────────────────────────────
# Reactor hitboxes reuse the tracer-band rects: each reactor body's on-screen
# position is fixed across every diagram mode (normal + all 3 CIP variants),
# so one click target per reactor works everywhere, not just when that
# reactor is the active CIP selection. The sensor hitbox sits over the AT-101
# instrument bubble in the artwork, just below its absorbance readout box
# (which is its own child widget and would otherwise swallow the click).
_REACTOR_HITBOXES = _REACTOR_BAND_RECTS
_SENSOR_HITBOX = QRectF(0.72, 0.395, 0.09, 0.05)
_HOVER_COLOR = QColor(79, 195, 247, 60)


class RTDDiagramWidget(QWidget):
    """
    P&ID for the CIP (Clean-In-Place) protocol built on the RTD tracer
    engine: three parallel reactors (R-102/103/104), one isolated at a time
    for washing. Selecting a reactor swaps in its CIP diagram (and its
    packed-bed scenario); with none selected the plant shows normal
    operation and injection is unavailable.

    Lighter than PFRDiagramWidget in one respect: reactor selection and
    injection controls live in the sidebar (CIPPanel / InjectionPanel)
    instead of as diagram overlays. It does share PFRDiagramWidget's
    click-through equipment-info hitbox pattern, though -- clicking a
    reactor body or the AT-101 bubble opens that equipment's info dialog.
    """

    reactor_info_requested = pyqtSignal(str)   # scenario_id
    sensor_info_requested  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

        # One renderer per mode: '' = normal operation, else scenario_id.
        self._renderers: dict[str, QSvgRenderer] = {
            '': QSvgRenderer(resource_path('images', 'rtd', RTD_NORMAL_SVG), self),
        }
        for _tag, scenario_id, svg_name in RTD_REACTORS:
            self._renderers[scenario_id] = QSvgRenderer(
                resource_path('images', 'rtd', svg_name), self
            )
        self._mode = ''   # '' = normal operation, else the active scenario_id
        self._overlay_v106 = QSvgRenderer(
            resource_path('images', 'rtd', RTD_V106_OVERLAY_SVG), self
        )
        self._wash_valve_active = False

        vb = self._renderer.viewBoxF()
        self._vb_w = vb.width()  or 800.0
        self._vb_h = vb.height() or 500.0

        self._editable_boxes: dict[str, DiagramBox] = {}
        for key, (mn, mx, step, dec, default, fmt) in _EDITABLE_CFG.items():
            box = DiagramBox(editable=True, fmt=fmt, parent=self)
            box.configure(mn, mx, step, dec, default)
            self._editable_boxes[key] = box

        self._readonly_boxes: dict[str, DiagramBox] = {}
        for key, fmt in _READONLY_FMT.items():
            box = DiagramBox(editable=False, fmt=fmt, parent=self)
            self._readonly_boxes[key] = box

        # Tracer band overlay state -- see start_band()/advance_band().
        self._band_kind: str | None = None   # None | 'pulse' | 'step' | 'drain'
        self._band_start_t = 0.0
        self._band_tau = 1.0
        self._band_progress: float | None = None

        # Start in normal operation: no reactor selected, flow box hidden.
        self._editable_boxes['Q'].setVisible(False)

        # Equipment info hitboxes -- ('reactor', scenario_id) | ('sensor', '') | None
        self._hover_key: tuple[str, str] | None = None

    @property
    def _renderer(self) -> QSvgRenderer:
        return self._renderers[self._mode]

    # ── Mode switching ────────────────────────────────────────────────────────

    def set_mode(self, scenario_id: str) -> None:
        """Switch the diagram to normal operation (scenario_id='') or to the
        CIP view for the given reactor's scenario. The flow box only exists
        as artwork on the CIP diagrams, so it's hidden in normal operation;
        AT-101's absorbance readout is present in every view."""
        if scenario_id not in self._renderers:
            scenario_id = ''
        self._mode = scenario_id
        self._editable_boxes['Q'].setVisible(scenario_id != '')
        self.clear_band()
        self.update()

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

    def _reposition_children(self) -> None:
        for key, box in self._editable_boxes.items():
            box.setGeometry(self._svgrect(_EDITABLE_RECTS[key]))
        for key, box in self._readonly_boxes.items():
            box.setGeometry(self._svgrect(_READONLY_RECTS[key]))

    def _key_at(self, pos) -> tuple[str, str] | None:
        if self._svgrect(_SENSOR_HITBOX).contains(pos):
            return ('sensor', '')
        for scenario_id, rect in _REACTOR_HITBOXES.items():
            if self._svgrect(rect).contains(pos):
                return ('reactor', scenario_id)
        return None

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), _DIAGRAM_BG)
        sc, ox, oy = self._transform()
        target = QRectF(ox, oy, self._vb_w * sc, self._vb_h * sc)
        self._renderer.render(p, target)
        if self._wash_valve_active:
            self._overlay_v106.render(p, target)
        self._paint_band(p)
        if self._hover_key:
            kind, scenario_id = self._hover_key
            rect = _SENSOR_HITBOX if kind == 'sensor' else _REACTOR_HITBOXES[scenario_id]
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(_HOVER_COLOR)
            p.drawRect(self._svgrect(rect))

    def _paint_band(self, p: QPainter) -> None:
        if self._band_kind is None or self._band_progress is None:
            return
        rect = _REACTOR_BAND_RECTS.get(self._mode)
        if rect is None:
            return
        col_rect = self._svgrect(rect)
        p.save()
        p.setClipRect(col_rect)
        if self._band_kind in ('step', 'drain'):
            frac = max(0.0, min(1.0, self._band_progress))
            fill_w = int(col_rect.width() * frac)
            band_rect = QRect(col_rect.x(), col_rect.y(), fill_w, col_rect.height())
            p.fillRect(band_rect, _BAND_FILL_COLOR)
        else:  # pulse -- a single band riding left-to-right through the reactor
            band_w = max(8, int(col_rect.width() * 0.10))
            center_x = col_rect.x() + int(col_rect.width() * self._band_progress)
            band_rect = QRect(center_x - band_w // 2, col_rect.y(), band_w, col_rect.height())
            p.fillRect(band_rect, _BAND_PULSE_COLOR)
        p.restore()

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
        kind, scenario_id = key
        if kind == 'sensor':
            self.sensor_info_requested.emit()
        else:
            self.reactor_info_requested.emit(scenario_id)

    # ── Public API ────────────────────────────────────────────────────────────

    def update_readings(self, snap: RTDSnapshot) -> None:
        self._readonly_boxes['absorbance'].set_value(snap.absorbance)
        if snap.injecting != self._wash_valve_active:
            self._wash_valve_active = snap.injecting
            self.update()

    def set_flow_display(self, Q_L_s: float) -> None:
        """Set the Q box to reflect the engine's current flow (e.g. after a
        scenario load or reset), without marking it dirty."""
        box = self._editable_boxes['Q']
        box.configure(0.1, 6.0, 0.05, 2, Q_L_s * _L_S_TO_L_MIN)

    def get_params(self) -> dict:
        return {'Q_L_min': self._editable_boxes['Q'].get_value()}

    def mark_params_clean(self) -> None:
        for box in self._editable_boxes.values():
            box.mark_clean()

    # ── Tracer band overlay ──────────────────────────────────────────────────
    # Purely cosmetic: timed by the nominal tau = V/Q (both visible), not by
    # the hidden RTD shape, so this never leaks dead-zone/bypass truth -- it
    # just gives the student a sense of "the tracer is moving through now".
    # Only drawn when a reactor is selected (self._mode is a scenario_id).

    def start_band(self, kind: str, sim_time: float, tau: float) -> None:
        """Start a band animation for a new injection. kind: 'pulse' rides a
        single band through the active reactor and off; 'step' fills from
        the inlet and holds once full."""
        if self._mode not in _REACTOR_BAND_RECTS:
            return
        self._band_kind = kind
        self._band_start_t = sim_time
        self._band_tau = max(tau, 0.1)
        self._band_progress = 0.0
        self.update()

    def start_drain(self, sim_time: float, tau: float) -> None:
        """Transition a full 'step' fill into draining back out, over the
        same nominal tau, after the step injection is stopped."""
        if self._mode not in _REACTOR_BAND_RECTS:
            return
        self._band_kind = 'drain'
        self._band_start_t = sim_time
        self._band_tau = max(tau, 0.1)
        self._band_progress = 1.0
        self.update()

    def advance_band(self, sim_time: float) -> None:
        if self._band_kind is None:
            return
        progress = (sim_time - self._band_start_t) / self._band_tau
        if self._band_kind == 'pulse':
            if progress >= 1.2:
                self.clear_band()
                return
            self._band_progress = progress
        elif self._band_kind == 'step':
            self._band_progress = min(progress, 1.0)
        else:  # 'drain'
            if progress >= 1.0:
                self.clear_band()
                return
            self._band_progress = 1.0 - progress
        self.update()

    def clear_band(self) -> None:
        self._band_kind = None
        self._band_progress = None
        self.update()
