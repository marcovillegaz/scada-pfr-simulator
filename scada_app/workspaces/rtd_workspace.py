from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QLabel, QSlider, QComboBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from constants import TIMER_INTERVAL_MS, RTD_BASE_SIM_DT, RTD_DEFAULT_SCENARIO, APP_TITLE

from engine.rtd_engine import RTDEngine
from engine.data_store import RTDSnapshot
from ui.tabs.rtd_diagram_tab import RTDDiagramTab
from ui.tabs.rtd_graph_tab import RTDGraphTab
from ui.tabs.rtd_table_tab import RTDTableTab
from ui.tabs.rtd_docs_tab import RTDDocsTab
from scenarios.loader import list_scenarios

_HEADER_H = 44
_FOOTER_H = 50

_DARK_BG   = "#262626"
_DARK_LINE = "#525252"


class RTDWorkspace(QWidget):
    """RTD (Experiencia 3) simulation workspace -- the tracer / residence-
    time-distribution tracer experiment, reached from the home screen.

    Structurally mirrors PFRWorkspace (own engine + timer + tabs + Home
    button), adapted for the RTD engine's tick pattern and injection
    actions instead of continuous setpoints.
    """

    home_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scenarios = list_scenarios()
        self._engine = RTDEngine(RTD_DEFAULT_SCENARIO, self)
        self._speed_factor = 1
        self._running = False
        self._plot_tick = 0

        self._build_ui()
        self._wire_signals()
        self._sync_diagram_to_engine()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer_tick)

    # ── Top-level layout ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        vlay.addWidget(self._make_header())
        vlay.addWidget(self._make_main(), stretch=1)
        vlay.addWidget(self._make_footer())

    # ── Header: Home + tab buttons + scenario picker ──────────────────────────

    def _make_header(self) -> QFrame:
        hdr = QFrame()
        hdr.setObjectName("header_bar")
        hdr.setFixedHeight(_HEADER_H)
        hdr.setStyleSheet(f"""
            QFrame#header_bar {{
                background-color: {_DARK_BG};
                border-bottom: 2px solid {_DARK_LINE};
            }}
            QLabel {{
                color: #eeeeec;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
            }}
            QPushButton#btn_tab {{
                background: transparent;
                border: none;
                border-bottom: 2px solid transparent;
                color: #adadad;
                font-size: 12px;
                font-weight: normal;
                padding: 0 16px;
                min-width: 0;
                border-radius: 0;
            }}
            QPushButton#btn_tab:hover {{
                color: #eeeeec;
                border-bottom: 2px solid #6e6e6e;
            }}
            QPushButton#btn_tab_active {{
                background: transparent;
                border: none;
                border-bottom: 2px solid #E95420;
                color: #E95420;
                font-size: 12px;
                font-weight: bold;
                padding: 0 16px;
                min-width: 0;
                border-radius: 0;
            }}
            QPushButton#btn_home {{
                background: transparent;
                border: none;
                border-right: 1px solid {_DARK_LINE};
                color: #adadad;
                font-size: 12px;
                font-weight: bold;
                padding: 0 16px;
                min-width: 0;
                border-radius: 0;
            }}
            QPushButton#btn_home:hover {{
                color: #E95420;
            }}
        """)

        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(0)

        btn_home = QPushButton("≡ Home")
        btn_home.setObjectName("btn_home")
        btn_home.setFixedHeight(_HEADER_H)
        btn_home.clicked.connect(self._on_home_clicked)
        lay.addWidget(btn_home)
        lay.addSpacing(10)

        self._tab_btns: list[QPushButton] = []
        for idx, name in enumerate(("Diagram", "Graph", "Table", "Docs")):
            btn = QPushButton(name)
            btn.setObjectName("btn_tab_active" if idx == 0 else "btn_tab")
            btn.setFixedHeight(_HEADER_H)
            btn.clicked.connect(lambda _, i=idx: self._switch_tab(i))
            self._tab_btns.append(btn)
            lay.addWidget(btn)

        lay.addStretch()

        lay.addWidget(QLabel("Plant:"))
        self._combo_scenario = QComboBox()
        for sc in self._scenarios:
            self._combo_scenario.addItem(sc.nombre, userData=sc.id)
        default_idx = next(
            (i for i, sc in enumerate(self._scenarios) if sc.id == RTD_DEFAULT_SCENARIO), 0
        )
        self._combo_scenario.setCurrentIndex(default_idx)
        self._combo_scenario.setFixedWidth(180)
        lay.addWidget(self._combo_scenario)
        lay.addSpacing(16)

        lay.addWidget(QLabel("RTD — Experiencia 3"))
        return hdr

    # ── Main content: full-width tab widget ───────────────────────────────────

    def _make_main(self) -> QTabWidget:
        self._tabs = QTabWidget()
        self._tabs.tabBar().hide()

        self._diagram_tab = RTDDiagramTab()
        self._graph_tab   = RTDGraphTab()
        self._table_tab   = RTDTableTab()
        self._docs_tab    = RTDDocsTab()
        self._tabs.addTab(self._diagram_tab, "Diagram")
        self._tabs.addTab(self._graph_tab,   "Graph")
        self._tabs.addTab(self._table_tab,   "Table")
        self._tabs.addTab(self._docs_tab,    "Docs")

        return self._tabs

    # ── Footer: GO / RESET / speed / status / sim time ───────────────────────

    def _make_footer(self) -> QFrame:
        ftr = QFrame()
        ftr.setObjectName("footer_bar")
        ftr.setFixedHeight(_FOOTER_H)
        ftr.setStyleSheet(f"""
            QFrame#footer_bar {{
                background-color: {_DARK_BG};
                border-top: 2px solid {_DARK_LINE};
            }}
            QLabel {{
                color: #adadad;
                font-size: 12px;
                background: transparent;
            }}
        """)

        lay = QHBoxLayout(ftr)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        self._btn_go = QPushButton("GO")
        self._btn_go.setObjectName("btn_go")
        self._btn_go.setFixedHeight(34)

        self._btn_reset = QPushButton("RESET")
        self._btn_reset.setObjectName("btn_reset")
        self._btn_reset.setFixedHeight(34)

        self._slider_speed = QSlider(Qt.Orientation.Horizontal)
        self._slider_speed.setRange(1, 100)
        self._slider_speed.setValue(1)
        self._slider_speed.setFixedWidth(150)
        self._slider_speed.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._slider_speed.setTickInterval(10)

        self._lbl_speed = QLabel("1×")
        self._lbl_speed.setFixedWidth(60)

        sep = QLabel("|")
        sep.setStyleSheet("color: #525252; font-size: 16px; background: transparent;")

        self._lbl_status = QLabel("Stopped")
        self._lbl_status.setStyleSheet("color: #ff7b63; font-weight: bold; background: transparent;")

        self._lbl_sim_time = QLabel("0.0 s")
        self._lbl_sim_time.setStyleSheet("color: #E95420; font-weight: bold; background: transparent;")

        self._btn_apply = QPushButton("Apply")
        self._btn_apply.setObjectName("btn_apply")
        self._btn_apply.setFixedHeight(34)

        lay.addWidget(self._btn_go)
        lay.addWidget(self._btn_reset)
        lay.addSpacing(16)
        lay.addWidget(QLabel("Speed:"))
        lay.addWidget(self._slider_speed)
        lay.addWidget(self._lbl_speed)
        lay.addSpacing(16)
        lay.addWidget(sep)
        lay.addWidget(QLabel("Status:"))
        lay.addWidget(self._lbl_status)
        lay.addSpacing(16)
        lay.addWidget(QLabel("Sim time:"))
        lay.addWidget(self._lbl_sim_time)
        lay.addStretch()
        lay.addWidget(self._btn_apply)

        return ftr

    # ── Tab switching ─────────────────────────────────────────────────────────

    def _switch_tab(self, index: int) -> None:
        self._tabs.setCurrentIndex(index)
        for i, btn in enumerate(self._tab_btns):
            btn.setObjectName("btn_tab_active" if i == index else "btn_tab")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _wire_signals(self) -> None:
        self._btn_go.clicked.connect(self._on_go_stop_clicked)
        self._btn_reset.clicked.connect(self._on_reset_clicked)
        self._slider_speed.valueChanged.connect(self._on_speed_changed)
        self._btn_apply.clicked.connect(self._on_apply_clicked)
        self._combo_scenario.currentIndexChanged.connect(self._on_scenario_changed)
        self._diagram_tab.pulse_requested.connect(self._on_pulse_requested)
        self._diagram_tab.step_start_requested.connect(self._on_step_start_requested)
        self._diagram_tab.step_stop_requested.connect(self._on_step_stop_requested)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_timer_tick(self) -> None:
        sim_dt = RTD_BASE_SIM_DT * self._speed_factor
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
        self._diagram_tab.clear_events()
        self._diagram_tab.clear_band()
        self._running = True
        self._btn_go.setText("STOP")
        self._btn_go.setObjectName("btn_stop")
        self._btn_go.style().unpolish(self._btn_go)
        self._btn_go.style().polish(self._btn_go)
        self._lbl_status.setText("Running")
        self._lbl_status.setStyleSheet("color: #57e389; font-weight: bold; background: transparent;")
        self._diagram_tab.add_event(0.0, f"Run started — {self._engine.scenario.nombre}", "info")
        self._apply_params()
        self._combo_scenario.setEnabled(False)
        self._timer.start()

    def _stop(self) -> None:
        self._timer.stop()
        self._running = False
        self._btn_go.setText("GO")
        self._btn_go.setObjectName("btn_go")
        self._btn_go.style().unpolish(self._btn_go)
        self._btn_go.style().polish(self._btn_go)
        self._lbl_status.setText("Stopped")
        self._lbl_status.setStyleSheet("color: #ff7b63; font-weight: bold; background: transparent;")
        snap = self._engine.get_snapshot()
        t = snap.sim_time if snap else 0.0
        self._diagram_tab.add_event(t, "Run stopped", "info")
        self._table_tab.update_on_stop(self._engine.data_store)
        self._combo_scenario.setEnabled(True)
        self._switch_tab(2)

    def _on_reset_clicked(self) -> None:
        if self._running:
            self._stop()
        self._engine.reset()
        self._graph_tab.clear_plots()
        self._diagram_tab.clear_events()
        self._diagram_tab.reset_injection_ui()
        self._diagram_tab.clear_band()
        self._sync_diagram_to_engine()
        self._lbl_sim_time.setText("0.0 s")
        self._lbl_status.setText("Ready")
        self._lbl_status.setStyleSheet("color: #cd9309; font-weight: bold; background: transparent;")

    def _on_speed_changed(self, value: int) -> None:
        self._speed_factor = value
        self._lbl_speed.setText(f"{value}×")

    def _on_apply_clicked(self) -> None:
        self._apply_params()

    def _apply_params(self) -> None:
        params = self._diagram_tab.get_params()
        self._engine.apply_parameters(params)
        self._diagram_tab.mark_params_clean()
        snap = self._engine.get_snapshot()
        t = snap.sim_time if snap else 0.0
        self._diagram_tab.add_event(t, f"Flow → {params['Q_mL_s']:.1f} mL/s", "info")

    def _on_scenario_changed(self, index: int) -> None:
        if self._running:
            self._stop()
        scenario_id = self._combo_scenario.itemData(index)
        self._engine.set_scenario(scenario_id)
        self._graph_tab.clear_plots()
        self._diagram_tab.clear_events()
        self._diagram_tab.reset_injection_ui()
        self._diagram_tab.clear_band()
        self._sync_diagram_to_engine()
        self._lbl_sim_time.setText("0.0 s")
        self._lbl_status.setText("Ready")
        self._lbl_status.setStyleSheet("color: #cd9309; font-weight: bold; background: transparent;")
        self._diagram_tab.add_event(0.0, f"Plant changed → {self._engine.scenario.nombre}", "info")

    def _on_pulse_requested(self, dose: float) -> None:
        self._engine.inject_pulse(dose)
        snap = self._engine.get_snapshot()
        t = snap.sim_time if snap else 0.0
        cost = self._engine.scenario.costos.pulso
        self._diagram_tab.add_event(t, f"Pulse injected — dose {dose:.3f} mol (cost +{cost:.0f})", "info")
        self._diagram_tab.start_band('pulse', t, self._engine.tau)

    def _on_step_start_requested(self, C0: float) -> None:
        self._engine.inject_step(C0)
        self._diagram_tab.start_step_ui()
        snap = self._engine.get_snapshot()
        t = snap.sim_time if snap else 0.0
        cost = self._engine.scenario.costos.escalon
        self._diagram_tab.add_event(t, f"Step injection started — C0 {C0:.2f} mol/L (cost +{cost:.0f})", "info")
        self._diagram_tab.start_band('step', t, self._engine.tau)

    def _on_step_stop_requested(self) -> None:
        self._engine.stop_injection()
        self._diagram_tab.stop_step_ui()
        snap = self._engine.get_snapshot()
        t = snap.sim_time if snap else 0.0
        self._diagram_tab.add_event(t, "Step injection stopped", "info")
        self._diagram_tab.start_drain(t, self._engine.tau)

    # ── Home navigation ────────────────────────────────────────────────────────

    def _on_home_clicked(self) -> None:
        self.pause()
        self.home_requested.emit()

    def pause(self) -> None:
        if self._running:
            self._stop()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _sync_diagram_to_engine(self) -> None:
        self._diagram_tab.set_flow_display(self._engine.Q_L_s)

    def _refresh_ui(self, snap: RTDSnapshot) -> None:
        self._diagram_tab.update_readings(snap)
        self._diagram_tab.advance_band(snap.sim_time)
        self._lbl_sim_time.setText(f"{snap.sim_time:.1f} s")

        self._plot_tick += 1
        if self._plot_tick % 2:
            return
        if self._tabs.currentWidget() is self._graph_tab:
            self._graph_tab.update_plots(self._engine.data_store)
