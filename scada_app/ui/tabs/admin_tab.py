from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCheckBox, QLabel, QSplitter,
)
from PyQt6.QtCore import Qt

from constants import K2C
from engine.data_store import DataStore


class AdminTab(QWidget):
    """
    Password-protected admin/debug tab — 2 × 2 plot grid.

    Left column  (concentrations):
        Top    — CA_in & CB_in vs time  (toggle per curve)
        Bottom — Xa_out vs time

    Right column (process control):
        Top    — T_out & T_hx vs time
        Bottom — Valve opening 0–1 vs time
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 4, 6, 6)
        root.setSpacing(4)

        title = QLabel("Admin Debug View")
        title.setStyleSheet(
            "color:#E95420;font-size:11px;font-weight:bold;background:transparent;"
        )
        root.addWidget(title)

        # ── Outer horizontal splitter: left col | right col ───────────────────
        h_split = QSplitter(Qt.Orientation.Horizontal)

        # ── LEFT COLUMN ───────────────────────────────────────────────────────
        left_split = QSplitter(Qt.Orientation.Vertical)

        # Top-left: CA_in / CB_in
        ca_cb_widget = QWidget()
        ca_cb_lay = QVBoxLayout(ca_cb_widget)
        ca_cb_lay.setContentsMargins(0, 0, 0, 0)
        ca_cb_lay.setSpacing(2)

        tog = QHBoxLayout()
        tog.setSpacing(10)
        tog.addWidget(QLabel("Show:"))
        self._chk_ca_in = QCheckBox("CA_in")
        self._chk_cb_in = QCheckBox("CB_in")
        for chk in (self._chk_ca_in, self._chk_cb_in):
            chk.setChecked(True)
            chk.setStyleSheet("color:#eeeeec;font-size:10px;")
            chk.toggled.connect(self._refresh_visibility)
            tog.addWidget(chk)
        tog.addStretch()
        ca_cb_lay.addLayout(tog)

        self._plot_ca_cb = pg.PlotWidget(title="Inlet Concentrations")
        self._plot_ca_cb.setLabel("left", "Concentration (mol/L)")
        self._plot_ca_cb.setLabel("bottom", "Time (s)")
        self._plot_ca_cb.addLegend()
        self._plot_ca_cb.showGrid(x=True, y=True, alpha=0.3)
        self._plot_ca_cb.setMouseEnabled(x=True, y=True)
        self._plot_ca_cb.enableAutoRange()
        self._curve_ca_in = self._plot_ca_cb.plot(
            pen=pg.mkPen("#E95420", width=2), name="CA_in")
        self._curve_cb_in = self._plot_ca_cb.plot(
            pen=pg.mkPen("#80cbc4", width=2), name="CB_in")
        ca_cb_lay.addWidget(self._plot_ca_cb)
        left_split.addWidget(ca_cb_widget)

        # Bottom-left: Xa_out
        self._plot_xa = pg.PlotWidget(title="Conversion")
        self._plot_xa.setLabel("left", "Xa_out (–)")
        self._plot_xa.setLabel("bottom", "Time (s)")
        self._plot_xa.showGrid(x=True, y=True, alpha=0.3)
        self._plot_xa.setMouseEnabled(x=True, y=True)
        self._plot_xa.enableAutoRange()
        self._curve_xa_out = self._plot_xa.plot(
            pen=pg.mkPen("#eeeeec", width=2), name="Xa_out")
        left_split.addWidget(self._plot_xa)

        left_split.setSizes([300, 200])
        h_split.addWidget(left_split)

        # ── RIGHT COLUMN ──────────────────────────────────────────────────────
        right_split = QSplitter(Qt.Orientation.Vertical)

        # Top-right: Temperature
        self._plot_temp = pg.PlotWidget(title="Temperature")
        self._plot_temp.setLabel("left", "T (°C)")
        self._plot_temp.setLabel("bottom", "Time (s)")
        self._plot_temp.addLegend()
        self._plot_temp.showGrid(x=True, y=True, alpha=0.3)
        self._plot_temp.setMouseEnabled(x=True, y=True)
        self._plot_temp.enableAutoRange()
        self._curve_t_out = self._plot_temp.plot(
            pen=pg.mkPen("#4fc3f7", width=2), name="T_out")
        self._curve_t_hx = self._plot_temp.plot(
            pen=pg.mkPen("#ffcc02", width=1,
                         style=Qt.PenStyle.DashLine), name="T_hx")
        right_split.addWidget(self._plot_temp)

        # Bottom-right: Valve
        self._plot_valve = pg.PlotWidget(title="Valve Opening")
        self._plot_valve.setLabel("left", "Valve (–)")
        self._plot_valve.setLabel("bottom", "Time (s)")
        self._plot_valve.showGrid(x=True, y=True, alpha=0.3)
        self._plot_valve.setMouseEnabled(x=True, y=False)
        self._plot_valve.setYRange(0.0, 1.0, padding=0.05)
        self._curve_valve = self._plot_valve.plot(
            pen=pg.mkPen("#E95420", width=2), name="Valve")
        right_split.addWidget(self._plot_valve)

        right_split.setSizes([300, 200])
        h_split.addWidget(right_split)

        h_split.setSizes([500, 500])
        root.addWidget(h_split, stretch=1)

    # ── Visibility toggles ────────────────────────────────────────────────────

    def _refresh_visibility(self) -> None:
        self._curve_ca_in.setVisible(self._chk_ca_in.isChecked())
        self._curve_cb_in.setVisible(self._chk_cb_in.isChecked())

    # ── Public API ────────────────────────────────────────────────────────────

    def update_plots(self, data_store: DataStore) -> None:
        buf = data_store.plot_buffer
        if len(buf) < 2:
            return
        times = [s.sim_time for s in buf]

        self._curve_ca_in.setData(times,  [s.CA_in        for s in buf])
        self._curve_cb_in.setData(times,  [s.CB_in        for s in buf])
        self._curve_xa_out.setData(times, [s.X_out        for s in buf])
        self._curve_t_out.setData(times,  [s.T_out - K2C  for s in buf])
        self._curve_t_hx.setData(times,   [s.T_hx  - K2C  for s in buf])
        self._curve_valve.setData(times,  [s.valve        for s in buf])

    def clear_plots(self) -> None:
        for c in (self._curve_ca_in, self._curve_cb_in, self._curve_xa_out,
                  self._curve_t_out, self._curve_t_hx, self._curve_valve):
            c.setData([], [])
        for p in (self._plot_ca_cb, self._plot_xa, self._plot_temp):
            p.enableAutoRange()
