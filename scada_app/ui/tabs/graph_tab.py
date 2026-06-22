from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt

from constants import K2C, ALARM_T_LOW_C, ALARM_T_HIGH_C
from engine.data_store import DataStore

pg.setConfigOption("background", "#1e2832")
pg.setConfigOption("foreground", "#b0bec5")

_DEFAULT_WINDOW_S = 600
_TEMP_Y_MIN = 10.0  # °C
_TEMP_Y_MAX = 50.0  # °C
_CT_Y_MIN = 0.0     # mS/cm — CT-101 instrument range
_CT_Y_MAX = 20.0    # mS/cm
_ML_MIN = 60_000_000.0  # m³/s → mL/min


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
        self._spin_window.setRange(200, 3600)
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

        # ── 2 × 2 plot grid ───────────────────────────────────────────────────
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(4)
        grid.addWidget(self._build_temp_panel(),   0, 0)
        grid.addWidget(self._build_valve_plot(),   1, 0)
        grid.addWidget(self._build_flows_plot(),   0, 1)
        grid.addWidget(self._build_ct_plot(),      1, 1)
        layout.addLayout(grid)

        # Decimate to the visible pixels — keeps redraws fast with a full buffer.
        for p in (self._plot_temp, self._plot_valve, self._plot_flows, self._plot_ct):
            p.setDownsampling(auto=True, mode="peak")
            p.setClipToView(True)

    # ── Plot builders ──────────────────────────────────────────────────────────

    def _build_temp_panel(self) -> QWidget:
        """(1,1) Temperature — T_in, T_out, T_reactor, setpoint + visibility toggles."""
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

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
            orientation="horizontal",
            brush=pg.mkBrush(38, 162, 105, 35),
            pen=pg.mkPen("#26A269", width=1, style=Qt.PenStyle.DashLine),
            movable=False,
        )
        self._plot_temp.addItem(_op_band)

        self._curve_t_in = self._plot_temp.plot(
            pen=pg.mkPen("#ffcc02", width=1, style=Qt.PenStyle.DotLine), name="T_in"
        )
        self._curve_t_out = self._plot_temp.plot(
            pen=pg.mkPen("#4fc3f7", width=2), name="T_out"
        )
        self._curve_t_reactor = self._plot_temp.plot(
            pen=pg.mkPen("#57e389", width=2, style=Qt.PenStyle.DashLine), name="T_reactor"
        )
        self._curve_t_sp = self._plot_temp.plot(
            pen=pg.mkPen("#E95420", width=1, style=Qt.PenStyle.DashLine), name="T_sp"
        )

        # ── Per-curve visibility checkboxes ───────────────────────────────────
        toggles = QHBoxLayout()
        toggles.setSpacing(10)
        toggles.addWidget(QLabel("Show:"))
        self._temp_curves = {
            "T_in":      self._curve_t_in,
            "T_out":     self._curve_t_out,
            "T_reactor": self._curve_t_reactor,
            "T_sp":      self._curve_t_sp,
        }
        for name, curve in self._temp_curves.items():
            chk = QCheckBox(name)
            chk.setChecked(True)
            chk.setStyleSheet("color:#cfd8dc;font-size:10px;")
            chk.toggled.connect(curve.setVisible)
            toggles.addWidget(chk)
        toggles.addStretch()

        lay.addLayout(toggles)
        lay.addWidget(self._plot_temp)
        return panel

    def _build_valve_plot(self) -> pg.PlotWidget:
        """(2,1) Valve opening % vs time."""
        self._plot_valve = pg.PlotWidget(title="Valve Opening — V-101")
        self._plot_valve.setLabel("left", "Valve (%)")
        self._plot_valve.setLabel("bottom", "Time (s)")
        self._plot_valve.showGrid(x=True, y=True, alpha=0.3)
        self._plot_valve.setMouseEnabled(x=False, y=False)
        self._plot_valve.setYRange(0.0, 100.0, padding=0.05)
        self._curve_valve = self._plot_valve.plot(
            pen=pg.mkPen("#E95420", width=2), name="Valve"
        )
        return self._plot_valve

    def _build_flows_plot(self) -> pg.PlotWidget:
        """(1,2) Flow rate — Qa0 (P-102, NaOH), Qb0 (P-103, EtAc), Q_in."""
        self._plot_flows = pg.PlotWidget(title="Feed Flows")
        self._plot_flows.setLabel("left", "Q (mL/min)")
        self._plot_flows.setLabel("bottom", "Time (s)")
        self._plot_flows.addLegend()
        self._plot_flows.showGrid(x=True, y=True, alpha=0.3)
        self._plot_flows.setMouseEnabled(x=False, y=True)
        self._plot_flows.enableAutoRange(axis="y")

        self._curve_qa = self._plot_flows.plot(pen=pg.mkPen("#E95420", width=2), name="Q_NaOH")
        self._curve_qb = self._plot_flows.plot(pen=pg.mkPen("#80cbc4", width=2), name="Q_EtAc")
        self._curve_q_in = self._plot_flows.plot(
            pen=pg.mkPen("#eeeeec", width=1, style=Qt.PenStyle.DashLine), name="Q_in"
        )
        return self._plot_flows

    def _build_ct_plot(self) -> pg.PlotWidget:
        """(2,2) Conductivity (left axis) + inlet conc Ca_in/Cb_in (right axis)."""
        self._plot_ct = pg.PlotWidget(title="Conductivity — CT-101")
        self._plot_ct.setLabel("left", "σ (mS/cm)")
        self._plot_ct.setLabel("bottom", "Time (s)")
        self._plot_ct.showGrid(x=True, y=True, alpha=0.3)
        self._plot_ct.setMouseEnabled(x=False, y=False)
        self._plot_ct.setYRange(_CT_Y_MIN, _CT_Y_MAX, padding=0)
        legend = self._plot_ct.addLegend()

        self._curve_ct = self._plot_ct.plot(pen=pg.mkPen("#eeeeec", width=2), name="CT-101")

        # Twin right axis for inlet concentrations (mol/L)
        plot_item = self._plot_ct.plotItem
        self._ct_conc_vb = pg.ViewBox()
        plot_item.showAxis("right")
        plot_item.scene().addItem(self._ct_conc_vb)
        plot_item.getAxis("right").linkToView(self._ct_conc_vb)
        plot_item.getAxis("right").setLabel("C (mol/L)")
        self._ct_conc_vb.setXLink(plot_item)

        self._curve_ca_in = pg.PlotCurveItem(pen=pg.mkPen("#E95420", width=1))
        self._curve_cb_in = pg.PlotCurveItem(pen=pg.mkPen("#80cbc4", width=1))
        self._ct_conc_vb.addItem(self._curve_ca_in)
        self._ct_conc_vb.addItem(self._curve_cb_in)
        legend.addItem(self._curve_ca_in, "Ca_in")
        legend.addItem(self._curve_cb_in, "Cb_in")

        # Keep the twin viewbox geometry synced to the main plot
        def _sync_views() -> None:
            self._ct_conc_vb.setGeometry(plot_item.vb.sceneBoundingRect())
            self._ct_conc_vb.linkedViewChanged(plot_item.vb, self._ct_conc_vb.XAxis)

        plot_item.vb.sigResized.connect(_sync_views)
        return self._plot_ct

    # ── Slots ───────────────────────────────────────────────────────────────────

    def _on_window_changed(self, value: int) -> None:
        self._window_s = value

    def update_plots(self, data_store: DataStore) -> None:
        buf = data_store.plot_buffer
        if len(buf) < 2:
            return

        times = [s.sim_time for s in buf]
        t_end = times[-1]
        t_start = t_end - self._window_s

        self._curve_t_in.setData(times, [s.T_in - K2C for s in buf])
        self._curve_t_out.setData(times, [s.T_out - K2C for s in buf])
        self._curve_t_reactor.setData(times, [s.T_reactor - K2C for s in buf])
        self._curve_t_sp.setData(times, [s.T_setpoint - K2C for s in buf])
        self._curve_valve.setData(times, [s.valve * 100.0 for s in buf])
        self._curve_qa.setData(times, [s.Qa0 * _ML_MIN for s in buf])
        self._curve_qb.setData(times, [s.Qb0 * _ML_MIN for s in buf])
        self._curve_q_in.setData(times, [s.Q_in * _ML_MIN for s in buf])
        self._curve_ct.setData(times, [s.conductivity for s in buf])
        self._curve_ca_in.setData(times, [s.CA_in for s in buf])
        self._curve_cb_in.setData(times, [s.CB_in for s in buf])

        for plot in (self._plot_temp, self._plot_valve, self._plot_flows, self._plot_ct):
            plot.setXRange(t_start, t_end, padding=0)

    def clear_plots(self) -> None:
        for c in (
            self._curve_t_in,
            self._curve_t_out,
            self._curve_t_reactor,
            self._curve_t_sp,
            self._curve_valve,
            self._curve_qa,
            self._curve_qb,
            self._curve_q_in,
            self._curve_ct,
            self._curve_ca_in,
            self._curve_cb_in,
        ):
            c.setData([], [])
        self._plot_flows.enableAutoRange(axis="y")
        self._plot_ct.setYRange(_CT_Y_MIN, _CT_Y_MAX, padding=0)
        self._ct_conc_vb.enableAutoRange(axis="y")

    def _reset_view(self) -> None:
        self._plot_temp.setYRange(_TEMP_Y_MIN, _TEMP_Y_MAX, padding=0)
        self._plot_valve.setYRange(0.0, 100.0, padding=0.05)
        self._plot_flows.enableAutoRange(axis="y")
        self._plot_ct.setYRange(_CT_Y_MIN, _CT_Y_MAX, padding=0)
        self._ct_conc_vb.enableAutoRange(axis="y")
