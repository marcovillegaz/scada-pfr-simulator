from __future__ import annotations

from PyQt6.QtWidgets import QWidget
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPainter, QColor
from PyQt6.QtCore import QRect, QRectF

from engine.data_store import RTDSnapshot
from ui.widgets.pfr_diagram import DiagramBox
from resources import resource_path

_SVG_PATH = resource_path('images', 'rtd_diagram.svg')

_FRAME_MARGIN = 14
_DIAGRAM_BG   = QColor(0xE9, 0xF1, 0xF5)

_L_S_TO_ML_S = 1000.0

# ── Editable value boxes: (min, max, step, decimals, default, format) ────────
_EDITABLE_CFG: dict[str, tuple] = {
    'Q': (1.0, 100.0, 0.5, 1, 20.0, '{:.1f}'),   # mL/s, overwritten from scenario on load
}
_EDITABLE_RECTS: dict[str, QRectF] = {
    'Q': QRectF(0.13125, 0.904, 0.0875, 0.048),
}

# ── Read-only display boxes ───────────────────────────────────────────────────
_READONLY_FMT: dict[str, str] = {
    'absorbance': '{:.4f}',
}
_READONLY_RECTS: dict[str, QRectF] = {
    'absorbance': QRectF(0.70625, 0.32, 0.0875, 0.048),
}

# ── Tracer band overlay (purely visual, timed by the nominal tau = V/Q — both
# visible quantities, no hidden RTD shape leaked) ─────────────────────────────
# Column body in normalized SVG coords (rect x=368 y=86 w=104 h=316 / 800x500
# viewBox); inlet is at the bottom (progress=0), outlet at the top (progress=1).
_COLUMN_RECT = QRectF(0.46, 0.172, 0.13, 0.632)
_BAND_PULSE_COLOR = QColor(0x5c, 0x4a, 0x8a, 205)   # matches TI-201 tracer color
_BAND_FILL_COLOR  = QColor(0x5c, 0x4a, 0x8a, 110)


class RTDDiagramWidget(QWidget):
    """
    P&ID for the RTD tracer experiment (R-201 packed bed column).

    Deliberately lighter than PFRDiagramWidget: two overlay boxes (flow
    setpoint, absorbance reading) and no click-through equipment dialogs --
    injection controls live in the sidebar InjectionPanel instead of as
    diagram overlays, since "inject pulse" / "start step" are momentary
    actions rather than editable setpoints.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)

        self._renderer = QSvgRenderer(_SVG_PATH, self)
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

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), _DIAGRAM_BG)
        sc, ox, oy = self._transform()
        self._renderer.render(p, QRectF(ox, oy, self._vb_w * sc, self._vb_h * sc))
        self._paint_band(p)

    def _paint_band(self, p: QPainter) -> None:
        if self._band_kind is None or self._band_progress is None:
            return
        col_rect = self._svgrect(_COLUMN_RECT)
        p.save()
        p.setClipRect(col_rect)
        if self._band_kind in ('step', 'drain'):
            frac = max(0.0, min(1.0, self._band_progress))
            fill_h = int(col_rect.height() * frac)
            band_rect = QRect(col_rect.x(), col_rect.bottom() - fill_h, col_rect.width(), fill_h)
            p.fillRect(band_rect, _BAND_FILL_COLOR)
        else:  # pulse -- a single band riding up through the column
            band_h = max(8, int(col_rect.height() * 0.10))
            center_y = col_rect.bottom() - int(col_rect.height() * self._band_progress)
            band_rect = QRect(col_rect.x(), center_y - band_h // 2, col_rect.width(), band_h)
            p.fillRect(band_rect, _BAND_PULSE_COLOR)
        p.restore()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reposition_children()

    # ── Public API ────────────────────────────────────────────────────────────

    def update_readings(self, snap: RTDSnapshot) -> None:
        self._readonly_boxes['absorbance'].set_value(snap.absorbance)

    def set_flow_display(self, Q_L_s: float) -> None:
        """Set the Q box to reflect the engine's current flow (e.g. after a
        scenario load or reset), without marking it dirty."""
        box = self._editable_boxes['Q']
        box.configure(1.0, 100.0, 0.5, 1, Q_L_s * _L_S_TO_ML_S)

    def get_params(self) -> dict:
        return {'Q_mL_s': self._editable_boxes['Q'].get_value()}

    def mark_params_clean(self) -> None:
        for box in self._editable_boxes.values():
            box.mark_clean()

    # ── Tracer band overlay ──────────────────────────────────────────────────
    # Purely cosmetic: timed by the nominal tau = V/Q (both visible), not by
    # the hidden RTD shape, so this never leaks dead-zone/bypass truth -- it
    # just gives the student a sense of "the tracer is moving through now".

    def start_band(self, kind: str, sim_time: float, tau: float) -> None:
        """Start a band animation for a new injection. kind: 'pulse' rides a
        single band up through the column and off; 'step' fills from the
        bottom and holds once full."""
        self._band_kind = kind
        self._band_start_t = sim_time
        self._band_tau = max(tau, 0.1)
        self._band_progress = 0.0
        self.update()

    def start_drain(self, sim_time: float, tau: float) -> None:
        """Transition a full 'step' fill into draining back out, over the
        same nominal tau, after the step injection is stopped."""
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
