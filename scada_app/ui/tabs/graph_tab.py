from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QSplitter, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt

from engine.data_store import DataStore

pg.setConfigOption("background", "#1e2832")
pg.setConfigOption("foreground", "#b0bec5")


class GraphTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Reset-view button
        btn_row = QHBoxLayout()
        btn_reset_view = QPushButton("Reset View")
        btn_reset_view.setFixedWidth(100)
        btn_reset_view.clicked.connect(self._reset_view)
        btn_row.addStretch()
        btn_row.addWidget(btn_reset_view)
        layout.addLayout(btn_row)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        # ── Temperature plot ─────────────────────────────────────────────
        self._plot_temp = pg.PlotWidget(title="Temperature")
        self._plot_temp.setLabel("left", "Temperature (K)")
        self._plot_temp.setLabel("bottom", "Time (s)")
        self._plot_temp.addLegend()
        self._plot_temp.showGrid(x=True, y=True, alpha=0.3)

        self._curve_true  = self._plot_temp.plot(pen=pg.mkPen("#4fc3f7", width=2),              name="T True")
        self._curve_meas  = self._plot_temp.plot(pen=pg.mkPen("#ef9a9a", width=2, style=Qt.PenStyle.DashLine), name="T Meas")
        self._curve_sp    = self._plot_temp.plot(pen=pg.mkPen("#a5d6a7", width=1, style=Qt.PenStyle.DotLine),  name="Setpoint")

        # ── Heat flow plot ───────────────────────────────────────────────
        self._plot_power = pg.PlotWidget(title="Heat Flow (+ heating / − cooling)")
        self._plot_power.setLabel("left", "Q (W)")
        self._plot_power.setLabel("bottom", "Time (s)")
        self._plot_power.showGrid(x=True, y=True, alpha=0.3)
        self._curve_power = self._plot_power.plot(pen=pg.mkPen("#ffcc02", width=2), name="Q (W)")

        # ── Concentration plot ───────────────────────────────────────────
        self._plot_conc = pg.PlotWidget(title="Concentration")
        self._plot_conc.setLabel("left", "Ca (mol/L)")
        self._plot_conc.setLabel("bottom", "Time (s)")
        self._plot_conc.showGrid(x=True, y=True, alpha=0.3)
        self._curve_conc = self._plot_conc.plot(pen=pg.mkPen("#ce93d8", width=2), name="Ca")

        splitter.addWidget(self._plot_temp)
        splitter.addWidget(self._plot_power)
        splitter.addWidget(self._plot_conc)
        splitter.setSizes([200, 100, 100])

        self._auto_range = True

    def update_plots(self, data_store: DataStore) -> None:
        buf = data_store.plot_buffer
        if len(buf) < 2:
            return

        times = [s.sim_time for s in buf]
        self._curve_true.setData(times,  [s.true_temp           for s in buf])
        self._curve_meas.setData(times,  [s.measured_temp        for s in buf])
        self._curve_sp.setData(times,    [s.setpoint             for s in buf])
        self._curve_power.setData(times, [s.heat_flow            for s in buf])
        self._curve_conc.setData(times,  [s.concentration        for s in buf])

        if self._auto_range:
            self._plot_temp.enableAutoRange()
            self._plot_power.enableAutoRange()
            self._plot_conc.enableAutoRange()
            self._auto_range = False

    def clear_plots(self) -> None:
        for c in (self._curve_true, self._curve_meas, self._curve_sp,
                  self._curve_power, self._curve_conc):
            c.setData([], [])
        self._auto_range = True

    def _reset_view(self) -> None:
        self._plot_temp.enableAutoRange()
        self._plot_power.enableAutoRange()
        self._plot_conc.enableAutoRange()
