from __future__ import annotations

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSpinBox,
)

from engine.data_store import DataStore

pg.setConfigOption("background", "#1e2832")
pg.setConfigOption("foreground", "#b0bec5")

_DEFAULT_WINDOW_S = 1800   # RTD runs span several tau (~100 s each) -- wider default window than the PFR graph


class RTDGraphTab(QWidget):
    """Live absorbance-vs-time plot -- the curve the student actually reads
    off the AIT-201 photocolorimeter. Single plot (mirrors GraphTab's
    pattern, just one variable instead of PFR's 2x2 grid)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._window_s = _DEFAULT_WINDOW_S
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        top = QHBoxLayout()
        top.addWidget(QLabel("Window:"))
        self._spin_window = QSpinBox()
        self._spin_window.setRange(200, 10800)
        self._spin_window.setValue(_DEFAULT_WINDOW_S)
        self._spin_window.setSuffix(" s")
        self._spin_window.setSingleStep(100)
        self._spin_window.setFixedWidth(100)
        self._spin_window.valueChanged.connect(self._on_window_changed)
        top.addWidget(self._spin_window)
        top.addStretch()
        btn_reset = QPushButton("Reset View")
        btn_reset.setFixedWidth(100)
        btn_reset.clicked.connect(self._reset_view)
        top.addWidget(btn_reset)
        layout.addLayout(top)

        self._plot = pg.PlotWidget(title="Absorbance — AIT-201")
        self._plot.setLabel("left", "A (—)")
        self._plot.setLabel("bottom", "Time (s)")
        self._plot.showGrid(x=True, y=True, alpha=0.3)
        self._plot.setMouseEnabled(x=False, y=True)
        self._plot.enableAutoRange(axis="y")
        self._plot.setDownsampling(auto=True, mode="peak")
        self._plot.setClipToView(True)
        self._curve = self._plot.plot(pen=pg.mkPen("#4fc3f7", width=2), name="A")
        layout.addWidget(self._plot)

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
        self._curve.setData(times, [s.absorbance for s in buf])
        self._plot.setXRange(t_start, t_end, padding=0)

    def clear_plots(self) -> None:
        self._curve.setData([], [])
        self._plot.enableAutoRange(axis="y")

    def _reset_view(self) -> None:
        self._plot.enableAutoRange(axis="y")
