from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QTabWidget,
    QVBoxLayout, QHBoxLayout, QToolBar, QPushButton,
    QLabel, QSlider, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer

from constants import TIMER_INTERVAL_MS, BASE_SIM_DT
from engine.simulation_engine import SimulationEngine
from engine.data_store import EngineSnapshot
from ui.panels.readings_panel import ReadingsPanel
from ui.panels.parameters_panel import ParametersPanel
from ui.tabs.diagram_tab import DiagramTab
from ui.tabs.graph_tab import GraphTab
from ui.tabs.table_tab import TableTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PFR Reactor SCADA Simulator")
        self.resize(1280, 780)

        self._engine       = SimulationEngine(self)
        self._speed_factor = 1
        self._running      = False

        self._build_toolbar()
        self._build_central()
        self._wire_signals()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer_tick)

    # ── Toolbar ──────────────────────────────────────────────────────────────
    def _build_toolbar(self) -> None:
        tb = QToolBar("Controls", self)
        tb.setMovable(False)
        tb.setFloatable(False)
        self.addToolBar(tb)

        self._btn_go = QPushButton("GO")
        self._btn_go.setObjectName("btn_go")
        self._btn_go.setFixedWidth(70)

        self._btn_reset = QPushButton("RESET")
        self._btn_reset.setObjectName("btn_reset")
        self._btn_reset.setFixedWidth(70)

        speed_lbl = QLabel("  Speed:")
        self._slider_speed = QSlider(Qt.Orientation.Horizontal)
        self._slider_speed.setRange(1, 100)
        self._slider_speed.setValue(1)
        self._slider_speed.setFixedWidth(160)
        self._slider_speed.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._slider_speed.setTickInterval(10)

        self._lbl_speed = QLabel("1x (real-time)")
        self._lbl_speed.setFixedWidth(110)

        sep = QLabel("   |   Status: ")
        self._lbl_status = QLabel("Stopped")
        self._lbl_status.setStyleSheet("color: #ef9a9a; font-weight: bold;")

        sim_time_lbl = QLabel("   Sim time: ")
        self._lbl_sim_time = QLabel("0.0 s")
        self._lbl_sim_time.setStyleSheet("color: #4fc3f7; font-weight: bold;")

        for w in (self._btn_go, self._btn_reset, speed_lbl,
                  self._slider_speed, self._lbl_speed,
                  sep, self._lbl_status,
                  sim_time_lbl, self._lbl_sim_time):
            tb.addWidget(w)

    # ── Central layout ────────────────────────────────────────────────────────
    def _build_central(self) -> None:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # Left: tab widget
        self._tabs = QTabWidget()
        self._diagram_tab = DiagramTab()
        self._graph_tab   = GraphTab()
        self._table_tab   = TableTab()
        self._tabs.addTab(self._diagram_tab, "Diagram")
        self._tabs.addTab(self._graph_tab,   "Graph")
        self._tabs.addTab(self._table_tab,   "Table")

        # Right: readings + parameters
        right = QWidget()
        right.setFixedWidth(230)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 4, 4, 4)
        self._readings_panel    = ReadingsPanel()
        self._parameters_panel  = ParametersPanel()
        right_layout.addWidget(self._readings_panel)
        right_layout.addWidget(self._parameters_panel)
        right_layout.addStretch()

        splitter.addWidget(self._tabs)
        splitter.addWidget(right)
        splitter.setSizes([1050, 230])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

    # ── Signal wiring ─────────────────────────────────────────────────────────
    def _wire_signals(self) -> None:
        self._btn_go.clicked.connect(self._on_go_stop_clicked)
        self._btn_reset.clicked.connect(self._on_reset_clicked)
        self._slider_speed.valueChanged.connect(self._on_speed_changed)
        self._parameters_panel.parameters_applied.connect(self._on_params_applied)

    # ── Slots ─────────────────────────────────────────────────────────────────
    def _on_timer_tick(self) -> None:
        sim_dt = BASE_SIM_DT * self._speed_factor
        self._engine.tick(sim_dt)
        snap = self._engine.get_snapshot()
        if snap is not None:
            self._refresh_ui(snap)

    def _on_go_stop_clicked(self) -> None:
        if self._running:
            self._stop()
        else:
            self._go()

    def _go(self) -> None:
        self._engine.data_store.clear()
        self._graph_tab.clear_plots()
        self._running = True
        self._btn_go.setText("STOP")
        self._btn_go.setObjectName("btn_stop")
        self._btn_go.setStyleSheet("")  # force stylesheet re-evaluation
        self._btn_go.setObjectName("btn_stop")
        self._apply_btn_style()
        self._lbl_status.setText("Running")
        self._lbl_status.setStyleSheet("color: #a5d6a7; font-weight: bold;")
        self._timer.start()

    def _stop(self) -> None:
        self._timer.stop()
        self._running = False
        self._btn_go.setText("GO")
        self._apply_btn_style()
        self._lbl_status.setText("Stopped")
        self._lbl_status.setStyleSheet("color: #ef9a9a; font-weight: bold;")
        self._table_tab.update_on_stop(self._engine.data_store)
        # Switch to Table tab so student sees data immediately
        self._tabs.setCurrentWidget(self._table_tab)

    def _apply_btn_style(self) -> None:
        if self._running:
            self._btn_go.setObjectName("btn_stop")
        else:
            self._btn_go.setObjectName("btn_go")
        # Force Qt to re-apply stylesheet for objectName change
        self._btn_go.style().unpolish(self._btn_go)
        self._btn_go.style().polish(self._btn_go)

    def _on_reset_clicked(self) -> None:
        if self._running:
            self._stop()
        self._engine.reset()
        self._graph_tab.clear_plots()
        self._lbl_sim_time.setText("0.0 s")
        self._lbl_status.setText("Ready")
        self._lbl_status.setStyleSheet("color: #ffcc02; font-weight: bold;")

    def _on_speed_changed(self, value: int) -> None:
        self._speed_factor = value
        if value == 1:
            self._lbl_speed.setText("1x (real-time)")
        else:
            self._lbl_speed.setText(f"{value}x")

    def _on_params_applied(self, params: dict) -> None:
        self._engine.apply_parameters(params)

    def _refresh_ui(self, snap: EngineSnapshot) -> None:
        self._readings_panel.update(snap)
        self._diagram_tab.update_readings(snap)
        self._graph_tab.update_plots(self._engine.data_store)
        self._lbl_sim_time.setText(f"{snap.sim_time:.1f} s")
