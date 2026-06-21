from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QHBoxLayout, QLabel, QSpinBox,
)
from PyQt6.QtCore import Qt

from constants import K2C, ALARM_T_LOW_C, ALARM_T_HIGH_C
from engine.data_store import DataStore

pg.setConfigOption("background", "#1e2832")
pg.setConfigOption("foreground", "#b0bec5")

_DEFAULT_WINDOW_S = 600
_TEMP_Y_MIN       = 10.0   # °C
_TEMP_Y_MAX       = 50.0   # °C
_ML_MIN           = 60_000_000.0   # m³/s → mL/min


class GraphTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._window_s = _DEFAULT_WINDOW_S
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Top bar ──────────────────────────────────────────────────────────
        top = QHBoxLayout()
        top.addWidget(QLabel("Window:"))
        self._spin_window = QSpinBox()
        self._spin_window.setRange(200, 1200)
        self._spin_window.setValue(_DEFAULT_WINDOW_S)
        self._spin_window.setSuffix(" s")
        self._spin_window.setSingleStep(50)
        self._spin_window.setFixedWidth(90)
        self._spin_window.valueChanged.connect(self._on_window_changed)
        top.addWidget(self._spin_window)
        top.addStretch()
        btn_reset = QPushButton("Reset View")
        btn_reset.setFixedWidth(100)
        btn_reset.clicked.connect(self._reset_view)
        top.addWidget(btn_reset)
        layout.addLayout(top)

        # ── Temperature plot (fixed Y: 10–100 °C) ────────────────────────────
        self._plot_temp = pg.PlotWidget(title="Temperature")
        self._plot_temp.setLabel("left", "T (°C)")
        self._plot_temp.setLabel("bottom", "Time (s)")
        self._plot_temp.addLegend()
        self._plot_temp.showGrid(x=True, y=True, alpha=0.3)
        self._plot_temp.setMouseEnabled(x=False, y=False)
        self._plot_temp.setYRange(_TEMP_Y_MIN, _TEMP_Y_MAX, padding=0)

        # Operational temperature band
        _op_band = pg.LinearRegionItem(
            values=[ALARM_T_LOW_C, ALARM_T_HIGH_C],
            orientation='horizontal',
            brush=pg.mkBrush(38, 162, 105, 35),
            pen=pg.mkPen('#26A269', width=1, style=Qt.PenStyle.DashLine),
            movable=False,
        )
        self._plot_temp.addItem(_op_band)

        self._curve_t_hx  = self._plot_temp.plot(
            pen=pg.mkPen("#ffcc02", width=1, style=Qt.PenStyle.DashLine), name="T_hx")
        self._curve_t_out = self._plot_temp.plot(
            pen=pg.mkPen("#4fc3f7", width=2), name="T_out")

        # ── Flows plot (auto Y) ───────────────────────────────────────────────
        self._plot_flows = pg.PlotWidget(title="Feed Flows")
        self._plot_flows.setLabel("left", "Q (mL/min)")
        self._plot_flows.setLabel("bottom", "Time (s)")
        self._plot_flows.addLegend()
        self._plot_flows.showGrid(x=True, y=True, alpha=0.3)
        self._plot_flows.setMouseEnabled(x=False, y=True)
        self._plot_flows.enableAutoRange(axis='y')

        self._curve_qa = self._plot_flows.plot(
            pen=pg.mkPen("#E95420", width=2), name="Q_EtAc")
        self._curve_qb = self._plot_flows.plot(
            pen=pg.mkPen("#80cbc4", width=2), name="Q_NaOH")

        # ── Conductivity plot (auto Y) ────────────────────────────────────────
        self._plot_ct = pg.PlotWidget(title="Conductivity — CT-101")
        self._plot_ct.setLabel("left", "σ (mS/cm)")
        self._plot_ct.setLabel("bottom", "Time (s)")
        self._plot_ct.showGrid(x=True, y=True, alpha=0.3)
        self._plot_ct.setMouseEnabled(x=False, y=True)
        self._plot_ct.enableAutoRange(axis='y')

        self._curve_ct = self._plot_ct.plot(
            pen=pg.mkPen("#eeeeec", width=2), name="CT-101")

        layout.addWidget(self._plot_temp,  stretch=1)
        layout.addWidget(self._plot_flows, stretch=1)
        layout.addWidget(self._plot_ct,    stretch=1)

    def _on_window_changed(self, value: int) -> None:
        self._window_s = value

    def update_plots(self, data_store: DataStore) -> None:
        buf = data_store.plot_buffer
        if len(buf) < 2:
            return

        times   = [s.sim_time for s in buf]
        t_end   = times[-1]
        t_start = t_end - self._window_s

        self._curve_t_hx.setData(times,  [s.T_hx  - K2C for s in buf])
        self._curve_t_out.setData(times, [s.T_out  - K2C for s in buf])
        self._curve_qa.setData(times,    [s.Qa0 * _ML_MIN for s in buf])
        self._curve_qb.setData(times,    [s.Qb0 * _ML_MIN for s in buf])
        self._curve_ct.setData(times,    [s.conductivity  for s in buf])

        self._plot_temp.setXRange(t_start, t_end, padding=0)
        self._plot_flows.setXRange(t_start, t_end, padding=0)
        self._plot_ct.setXRange(t_start, t_end, padding=0)

    def clear_plots(self) -> None:
        for c in (self._curve_t_hx, self._curve_t_out,
                  self._curve_qa, self._curve_qb, self._curve_ct):
            c.setData([], [])
        self._plot_flows.enableAutoRange(axis='y')
        self._plot_ct.enableAutoRange(axis='y')

    def _reset_view(self) -> None:
        self._plot_temp.setYRange(_TEMP_Y_MIN, _TEMP_Y_MAX, padding=0)
        self._plot_flows.enableAutoRange(axis='y')
        self._plot_ct.enableAutoRange(axis='y')
