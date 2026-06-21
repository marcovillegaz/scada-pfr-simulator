from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QPushButton,
    QHBoxLayout, QLabel, QSpinBox,
)
from PyQt6.QtCore import Qt

from constants import K2C
from engine.data_store import DataStore

pg.setConfigOption("background", "#1e2832")
pg.setConfigOption("foreground", "#b0bec5")

_DEFAULT_WINDOW_S = 120
_TEMP_Y_MIN       = 10.0   # °C
_TEMP_Y_MAX       = 100.0  # °C


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
        self._spin_window.setRange(10, 600)
        self._spin_window.setValue(_DEFAULT_WINDOW_S)
        self._spin_window.setSuffix(" s")
        self._spin_window.setSingleStep(10)
        self._spin_window.setFixedWidth(80)
        self._spin_window.valueChanged.connect(self._on_window_changed)
        top.addWidget(self._spin_window)
        top.addStretch()
        btn_reset = QPushButton("Reset View")
        btn_reset.setFixedWidth(100)
        btn_reset.clicked.connect(self._reset_view)
        top.addWidget(btn_reset)
        layout.addLayout(top)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # ── Temperature plot (fixed Y: 10–100 °C) ───────────────────────────
        self._plot_temp = pg.PlotWidget(title="Temperature")
        self._plot_temp.setLabel("left", "T (°C)")
        self._plot_temp.setLabel("bottom", "Time (s)")
        self._plot_temp.addLegend()
        self._plot_temp.showGrid(x=True, y=True, alpha=0.3)
        self._plot_temp.setMouseEnabled(x=False, y=False)
        self._plot_temp.setYRange(_TEMP_Y_MIN, _TEMP_Y_MAX, padding=0)

        self._curve_t_hx  = self._plot_temp.plot(
            pen=pg.mkPen("#ffcc02", width=1, style=Qt.PenStyle.DashLine), name="T_hx")
        self._curve_t_out = self._plot_temp.plot(
            pen=pg.mkPen("#4fc3f7", width=2), name="T_out")

        # ── Concentration plot (auto Y) ──────────────────────────────────────
        self._plot_conc = pg.PlotWidget(title="Outlet Concentration")
        self._plot_conc.setLabel("left", "C (mol/L)")
        self._plot_conc.setLabel("bottom", "Time (s)")
        self._plot_conc.addLegend()
        self._plot_conc.showGrid(x=True, y=True, alpha=0.3)
        self._plot_conc.setMouseEnabled(x=False, y=True)
        self._plot_conc.getPlotItem().setAutoVisible(y=True)
        self._plot_conc.enableAutoRange(axis='y')

        self._curve_ca_out = self._plot_conc.plot(
            pen=pg.mkPen("#ce93d8", width=2), name="Ca_out")
        self._curve_cb_out = self._plot_conc.plot(
            pen=pg.mkPen("#80cbc4", width=2), name="Cb_out")

        splitter.addWidget(self._plot_temp)
        splitter.addWidget(self._plot_conc)
        splitter.setSizes([200, 200])

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
        self._curve_ca_out.setData(times,[s.CA_out        for s in buf])
        self._curve_cb_out.setData(times,[s.CB_out        for s in buf])

        self._plot_temp.setXRange(t_start, t_end, padding=0)
        self._plot_conc.setXRange(t_start, t_end, padding=0)

    def clear_plots(self) -> None:
        for c in (self._curve_t_hx, self._curve_t_out,
                  self._curve_ca_out, self._curve_cb_out):
            c.setData([], [])
        # Temperature Y stays fixed; only reset concentration auto-range
        self._plot_conc.enableAutoRange(axis='y')

    def _reset_view(self) -> None:
        self._plot_temp.setYRange(_TEMP_Y_MIN, _TEMP_Y_MAX, padding=0)
        self._plot_conc.enableAutoRange(axis='y')
