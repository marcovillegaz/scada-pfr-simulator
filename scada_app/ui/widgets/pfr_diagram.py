from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygon
from PyQt6.QtCore import Qt, QRect, QPoint, QSize

from constants import SCENE_W, SCENE_H, ALARM_TEMP_HIGH, ALARM_TEMP_LOW
from engine.data_store import EngineSnapshot
from ui.widgets.alarm_indicator import AlarmIndicator


# ── Scene-space geometry constants ──────────────────────────────────────────
_TANK_X, _TANK_Y, _TANK_W, _TANK_H = 20, 150, 70, 200

_PIPE_Y       = 250
_PFR_X        = 150
_TUBE_W       = 320
_TUBE_H       = 36
_TUBE_GAP     = 10
_TUBE_ROWS    = [180, 230, 280]

_HEATER_X, _HEATER_Y, _HEATER_W, _HEATER_H = 195, 350, 265, 55

_OUTLET_X1, _OUTLET_X2 = 470, 560
_PRODUCT_X, _PRODUCT_Y, _PRODUCT_W, _PRODUCT_H = 560, 200, 70, 100

# Label scene anchors (top-left of each label in scene coords)
_LBL_T_TRUE  = (160, 162)
_LBL_T_MEAS  = (160, 178)
_LBL_POWER   = (200, 356)
_LBL_SP      = (340, 356)
_LBL_CONC    = (465, 215)
_LBL_FLOW    = (465, 233)


class PFRDiagramWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(500, 320)
        self._scale  = 1.0
        self._offset = QPoint(0, 0)

        self._build_labels()
        self._build_alarms()

    # ── Construction ────────────────────────────────────────────────────────
    def _build_labels(self) -> None:
        def lbl(color="#4fc3f7", bold=False) -> QLabel:
            l = QLabel("—", self)
            s = f"color:{color}; background:transparent;"
            if bold:
                s += "font-weight:bold;"
            l.setStyleSheet(s)
            l.setFont(QFont("Consolas", 8))
            return l

        self._lbl_t_true = lbl("#4fc3f7", bold=True)
        self._lbl_t_meas = lbl("#ef9a9a")
        self._lbl_power  = lbl("#ffcc02", bold=True)
        self._lbl_sp     = lbl("#a5d6a7")
        self._lbl_conc   = lbl("#ce93d8", bold=True)
        self._lbl_flow   = lbl("#80cbc4")

    def _build_alarms(self) -> None:
        self._alarm_high = AlarmIndicator("HIGH T", self)
        self._alarm_low  = AlarmIndicator("LOW T",  self)

    # ── Coordinate transform ─────────────────────────────────────────────────
    def _compute_transform(self) -> None:
        w, h = self.width(), self.height()
        sx = w / SCENE_W
        sy = h / SCENE_H
        self._scale = min(sx, sy)
        ox = (w - SCENE_W * self._scale) / 2
        oy = (h - SCENE_H * self._scale) / 2
        self._offset = QPoint(int(ox), int(oy))

    def _s(self, x: int, y: int, w: int = 0, h: int = 0) -> QRect:
        """Scene rect → widget rect."""
        sc = self._scale
        ox, oy = self._offset.x(), self._offset.y()
        return QRect(
            int(ox + x * sc), int(oy + y * sc),
            int(w * sc) if w else 1,
            int(h * sc) if h else 1,
        )

    def _sp(self, x: int, y: int) -> QPoint:
        sc = self._scale
        return QPoint(int(self._offset.x() + x * sc),
                       int(self._offset.y() + y * sc))

    # ── Resize ───────────────────────────────────────────────────────────────
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._compute_transform()
        self._reposition_overlays()

    def _reposition_overlays(self) -> None:
        anchors = [
            (self._lbl_t_true, _LBL_T_TRUE),
            (self._lbl_t_meas, _LBL_T_MEAS),
            (self._lbl_power,  _LBL_POWER),
            (self._lbl_sp,     _LBL_SP),
            (self._lbl_conc,   _LBL_CONC),
            (self._lbl_flow,   _LBL_FLOW),
        ]
        for lbl, (sx, sy) in anchors:
            p = self._sp(sx, sy)
            lbl.move(p)
            lbl.adjustSize()

        # Alarm indicators
        p_high = self._sp(160, 320)
        p_low  = self._sp(240, 320)
        self._alarm_high.move(p_high)
        self._alarm_low.move(p_low)

    # ── Paint ────────────────────────────────────────────────────────────────
    def paintEvent(self, event) -> None:
        self._compute_transform()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        p.fillRect(self.rect(), QColor("#1e2832"))

        self._draw_tank(p)
        self._draw_pfr_tubes(p)
        self._draw_heater(p)
        self._draw_pipes(p)
        self._draw_product(p)
        self._draw_labels_static(p)

    def _draw_tank(self, p: QPainter) -> None:
        r = self._s(_TANK_X, _TANK_Y, _TANK_W, _TANK_H)
        p.setBrush(QBrush(QColor("#1a3a5c")))
        p.setPen(QPen(QColor("#4fc3f7"), 2))
        p.drawRect(r)
        p.setPen(QPen(QColor("#b0bec5")))
        p.setFont(QFont("Consolas", 7))
        p.drawText(self._s(_TANK_X, _TANK_Y - 16, _TANK_W, 14),
                   Qt.AlignmentFlag.AlignCenter, "Feed Tank")

    def _draw_pfr_tubes(self, p: QPainter) -> None:
        p.setBrush(QBrush(QColor("#0d47a1")))
        p.setPen(QPen(QColor("#42a5f5"), 2))
        for ty in _TUBE_ROWS:
            r = self._s(_PFR_X, ty, _TUBE_W, _TUBE_H)
            p.drawRoundedRect(r, 5, 5)

        # PFR label
        p.setPen(QPen(QColor("#b0bec5")))
        p.setFont(QFont("Consolas", 7))
        p.drawText(self._s(_PFR_X, _TUBE_ROWS[0] - 16, _TUBE_W, 14),
                   Qt.AlignmentFlag.AlignCenter, "PFR")

    def _draw_heater(self, p: QPainter) -> None:
        r = self._s(_HEATER_X, _HEATER_Y, _HEATER_W, _HEATER_H)
        p.setBrush(QBrush(QColor("#7f1010")))
        p.setPen(QPen(QColor("#ef5350"), 2))
        p.drawRect(r)
        p.setPen(QPen(QColor("#ffcdd2")))
        p.setFont(QFont("Consolas", 7))
        p.drawText(r, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, "Heater")

    def _draw_pipes(self, p: QPainter) -> None:
        pen = QPen(QColor("#78909c"), max(2, int(3 * self._scale)))
        p.setPen(pen)

        # Feed → PFR inlet
        p.drawLine(self._sp(_TANK_X + _TANK_W, _PIPE_Y),
                   self._sp(_PFR_X, _PIPE_Y))

        # PFR outlet → product
        p.drawLine(self._sp(_PFR_X + _TUBE_W, _PIPE_Y),
                   self._sp(_OUTLET_X2, _PIPE_Y))

        # Flow arrow (right-pointing)
        self._draw_arrow(p, self._sp(_TANK_X + _TANK_W + 5, _PIPE_Y),
                         self._sp(_PFR_X - 5, _PIPE_Y))
        self._draw_arrow(p, self._sp(_PFR_X + _TUBE_W + 5, _PIPE_Y),
                         self._sp(_OUTLET_X2 - 5, _PIPE_Y))

        # Heater connector lines to tubes
        p.setPen(QPen(QColor("#ef5350"), 1))
        mid_tube_y = _TUBE_ROWS[1] + _TUBE_H // 2
        p.drawLine(self._sp(_HEATER_X + _HEATER_W // 2, _HEATER_Y),
                   self._sp(_HEATER_X + _HEATER_W // 2, mid_tube_y + _TUBE_H // 2))

    def _draw_arrow(self, p: QPainter, p1: QPoint, p2: QPoint) -> None:
        dx = p2.x() - p1.x()
        if dx <= 0:
            return
        mx = (p1.x() + p2.x()) // 2
        my = p1.y()
        size = max(5, int(8 * self._scale))
        arrow = QPolygon([
            QPoint(mx + size, my),
            QPoint(mx, my - size // 2),
            QPoint(mx, my + size // 2),
        ])
        p.setBrush(QBrush(QColor("#78909c")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPolygon(arrow)
        p.setPen(QPen(QColor("#78909c"), max(2, int(3 * self._scale))))

    def _draw_product(self, p: QPainter) -> None:
        r = self._s(_PRODUCT_X, _PRODUCT_Y, _PRODUCT_W, _PRODUCT_H)
        p.setBrush(QBrush(QColor("#1b5e20")))
        p.setPen(QPen(QColor("#66bb6a"), 2))
        p.drawRect(r)
        p.setPen(QPen(QColor("#b0bec5")))
        p.setFont(QFont("Consolas", 7))
        p.drawText(self._s(_PRODUCT_X, _PRODUCT_Y - 16, _PRODUCT_W, 14),
                   Qt.AlignmentFlag.AlignCenter, "Product")

    def _draw_labels_static(self, p: QPainter) -> None:
        p.setPen(QPen(QColor("#90a4ae")))
        p.setFont(QFont("Consolas", 7))
        p.drawText(self._sp(_LBL_T_TRUE[0] - 50, _LBL_T_TRUE[1]), "T_true:")
        p.drawText(self._sp(_LBL_T_MEAS[0] - 50, _LBL_T_MEAS[1]), "T_meas:")
        p.drawText(self._sp(_LBL_POWER[0] - 45,  _LBL_POWER[1]),  "Power:")
        p.drawText(self._sp(_LBL_SP[0] - 30,     _LBL_SP[1]),     "SP:")
        p.drawText(self._sp(_LBL_CONC[0] - 40,   _LBL_CONC[1]),   "Ca:")
        p.drawText(self._sp(_LBL_FLOW[0] - 40,   _LBL_FLOW[1]),   "Q:")

    # ── Public update ────────────────────────────────────────────────────────
    def update_readings(self, snap: EngineSnapshot) -> None:
        self._lbl_t_true.setText(f"{snap.true_temp:.1f} K")
        self._lbl_t_meas.setText(f"{snap.measured_temp:.1f} K")
        self._lbl_power.setText(f"{snap.heat_flow:.0f} W")
        self._lbl_sp.setText(f"{snap.setpoint:.1f} K")
        self._lbl_conc.setText(f"{snap.concentration:.4f} mol/L")
        self._lbl_flow.setText(f"{snap.flow_rate * 60000:.2f} L/min")

        for lbl in (self._lbl_t_true, self._lbl_t_meas, self._lbl_power,
                    self._lbl_sp, self._lbl_conc, self._lbl_flow):
            lbl.adjustSize()

        self._alarm_high.set_active(snap.true_temp > ALARM_TEMP_HIGH)
        self._alarm_low.set_active(snap.true_temp  < ALARM_TEMP_LOW)
