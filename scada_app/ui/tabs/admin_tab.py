from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSplitter, QSpinBox, QTableView, QPushButton, QFileDialog,
)
from PyQt6.QtCore import Qt

from engine.data_store import DataStore
from models.log_table_model import LogTableModel, ADMIN_COLUMNS

_DEFAULT_WINDOW_S = 600


class AdminTab(QWidget):
    """
    Password-protected admin/debug tab.

    Left  — conversion Xa_out vs time (rolling window, like the Graph tab).
    Right — full internal-variable table (populated on STOP) with CSV/Excel export.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._window_s = _DEFAULT_WINDOW_S
        self._df = None
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

        h_split = QSplitter(Qt.Orientation.Horizontal)
        h_split.addWidget(self._build_left())
        h_split.addWidget(self._build_right())
        h_split.setSizes([550, 450])
        root.addWidget(h_split, stretch=1)

    def _build_left(self) -> QWidget:
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)

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
        lay.addLayout(top)

        self._plot_xa = pg.PlotWidget(title="Conversion & Inlet Concentrations")
        self._plot_xa.setLabel("left", "Xa_out (–)")
        self._plot_xa.setLabel("bottom", "Time (s)")
        self._plot_xa.showGrid(x=True, y=True, alpha=0.3)
        self._plot_xa.setMouseEnabled(x=False, y=True)
        self._plot_xa.enableAutoRange(axis="y")
        legend = self._plot_xa.addLegend()
        self._plot_xa.setDownsampling(auto=True, mode="peak")
        self._plot_xa.setClipToView(True)
        self._curve_xa_out = self._plot_xa.plot(
            pen=pg.mkPen("#eeeeec", width=2), name="Xa_out")

        # Twin right axis for inlet concentrations (mol/L)
        plot_item = self._plot_xa.plotItem
        self._conc_vb = pg.ViewBox()
        plot_item.showAxis("right")
        plot_item.scene().addItem(self._conc_vb)
        plot_item.getAxis("right").linkToView(self._conc_vb)
        plot_item.getAxis("right").setLabel("C (mol/L)")
        self._conc_vb.setXLink(plot_item)

        self._curve_ca_in = pg.PlotCurveItem(pen=pg.mkPen("#E95420", width=1))
        self._curve_cb_in = pg.PlotCurveItem(pen=pg.mkPen("#80cbc4", width=1))
        self._conc_vb.addItem(self._curve_ca_in)
        self._conc_vb.addItem(self._curve_cb_in)
        legend.addItem(self._curve_ca_in, "Ca_in")
        legend.addItem(self._curve_cb_in, "Cb_in")

        def _sync_views() -> None:
            self._conc_vb.setGeometry(plot_item.vb.sceneBoundingRect())
            self._conc_vb.linkedViewChanged(plot_item.vb, self._conc_vb.XAxis)

        plot_item.vb.sigResized.connect(_sync_views)

        lay.addWidget(self._plot_xa)
        return wrap

    def _build_right(self) -> QWidget:
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self._status_lbl = QLabel("Run the simulation and press STOP to load data.")
        self._status_lbl.setStyleSheet("color:#adadad;font-size:10px;")
        lay.addWidget(self._status_lbl)

        self._model = LogTableModel(columns=ADMIN_COLUMNS)
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        lay.addWidget(self._table, stretch=1)

        btn_row = QHBoxLayout()
        self._btn_csv = QPushButton("Export CSV")
        self._btn_excel = QPushButton("Export Excel")
        self._btn_csv.setEnabled(False)
        self._btn_excel.setEnabled(False)
        self._btn_csv.clicked.connect(self._export_csv)
        self._btn_excel.clicked.connect(self._export_excel)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_csv)
        btn_row.addWidget(self._btn_excel)
        lay.addLayout(btn_row)
        return wrap

    # ── Slots ───────────────────────────────────────────────────────────────────

    def _on_window_changed(self, value: int) -> None:
        self._window_s = value

    # ── Public API ────────────────────────────────────────────────────────────

    def update_plots(self, data_store: DataStore) -> None:
        buf = data_store.plot_buffer
        if len(buf) < 2:
            return
        times = [s.sim_time for s in buf]
        t_end = times[-1]
        t_start = t_end - self._window_s
        self._curve_xa_out.setData(times, [s.X_out for s in buf])
        self._curve_ca_in.setData(times, [s.CA_in for s in buf])
        self._curve_cb_in.setData(times, [s.CB_in for s in buf])
        self._plot_xa.setXRange(t_start, t_end, padding=0)

    def update_on_stop(self, data_store: DataStore) -> None:
        snapshots = list(data_store.run_log)
        self._model.set_snapshots(snapshots)
        self._df = data_store.to_dataframe()
        n = len(snapshots)
        self._status_lbl.setText(f"{n} rows logged.")
        enabled = n > 0
        self._btn_csv.setEnabled(enabled)
        self._btn_excel.setEnabled(enabled)
        self._table.resizeColumnsToContents()

    def clear_plots(self) -> None:
        self._curve_xa_out.setData([], [])
        self._curve_ca_in.setData([], [])
        self._curve_cb_in.setData([], [])
        self._plot_xa.enableAutoRange(axis="y")
        self._conc_vb.enableAutoRange(axis="y")

    # ── Export ──────────────────────────────────────────────────────────────────

    def _export_csv(self) -> None:
        if self._df is None or self._df.empty:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "reactor_internal.csv", "CSV files (*.csv)")
        if path:
            self._df.to_csv(path, index=False)

    def _export_excel(self) -> None:
        if self._df is None or self._df.empty:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Excel", "reactor_internal.xlsx", "Excel files (*.xlsx)")
        if path:
            self._df.to_excel(path, index=False)
