from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QLabel, QSlider,
    QInputDialog, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from constants import TIMER_INTERVAL_MS, BASE_SIM_DT, K2C, APP_TITLE

_ML_MIN = 60_000_000.0   # m³/s → mL/min

# Human-readable description for each parameter key + display formatter
_PARAM_FMT: dict[str, tuple[str, object]] = {
    'Qa0':           ('NaOH flow',   lambda v: f'{v * _ML_MIN:.1f} mL/min'),
    'Ca0':           ('NaOH conc',   lambda v: f'{v:.3f} mol/L'),
    'Qb0':           ('EtAc flow',   lambda v: f'{v * _ML_MIN:.1f} mL/min'),
    'Cb0':           ('EtAc conc',   lambda v: f'{v:.3f} mol/L'),
    'T_setpoint':    ('Reactor T setpoint', lambda v: f'{v - K2C:.1f} C'),
    'Kp':            ('PID Kp',      lambda v: f'{v:.4f}'),
    'Ki':            ('PID Ki',      lambda v: f'{v:.4f}'),
    'Kd':            ('PID Kd',      lambda v: f'{v:.4f}'),
}
from engine.simulation_engine import SimulationEngine
from engine.data_store import EngineSnapshot
from ui.tabs.diagram_tab import DiagramTab
from ui.tabs.graph_tab import GraphTab
from ui.tabs.table_tab import TableTab
from ui.tabs.admin_tab import AdminTab
from ui.dialogs.pid_dialog import PIDDialog
from ui.dialogs.sensor_dialog import SensorInfoDialog
from ui.dialogs.reactor_dialog import ReactorInfoDialog
from ui.dialogs.hx_dialog import HXInfoDialog
from ui.dialogs.tc_dialog import TCInfoDialog
from ui.tabs.docs_tab import DocsTab

_HEADER_H = 44
_FOOTER_H = 50

_DARK_BG   = "#262626"   # Ubuntu dark surface
_DARK_LINE = "#525252"   # Ubuntu border


class PFRWorkspace(QWidget):
    """PFR SCADA simulation workspace — everything the student sees once they
    pick 'PFR SCADA Simulator' from the home screen.

    Owns the simulation engine, timer and all PFR-specific tabs/dialogs.
    Documentation stays local to this workspace (Docs tab); About lives at
    the shell/home level and is reached via the Home button.
    """

    home_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._engine         = SimulationEngine(self)
        self._speed_factor   = 1
        self._running        = False
        self._last_params: dict = {}   # tracks last applied params for diff-based events
        self._first_apply = True        # first Apply logs all params regardless of change
        self._admin_unlocked = False
        self._plot_tick = 0             # throttles plot redraw to ~10 Hz

        self._build_ui()
        self._wire_signals()

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

    # ── Header: Home + tab buttons (left) + title (right) ────────────────────

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

        # Admin tab button — password-protected
        self._btn_admin = QPushButton("Admin [locked]")
        self._btn_admin.setObjectName("btn_tab")
        self._btn_admin.setFixedHeight(_HEADER_H)
        self._btn_admin.clicked.connect(self._on_admin_requested)
        self._tab_btns.append(self._btn_admin)
        lay.addWidget(self._btn_admin)

        lay.addStretch()
        lay.addWidget(QLabel(APP_TITLE))
        return hdr

    # ── Main content: full-width tab widget ───────────────────────────────────

    def _make_main(self) -> QTabWidget:
        self._tabs = QTabWidget()
        self._tabs.tabBar().hide()

        self._diagram_tab = DiagramTab()
        self._graph_tab   = GraphTab()
        self._table_tab   = TableTab()
        self._docs_tab    = DocsTab()
        self._admin_tab   = AdminTab()
        self._tabs.addTab(self._diagram_tab, "Diagram")
        self._tabs.addTab(self._graph_tab,   "Graph")
        self._tabs.addTab(self._table_tab,   "Table")
        self._tabs.addTab(self._docs_tab,    "Docs")
        self._tabs.addTab(self._admin_tab,   "Admin")

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

        self._lbl_speed = QLabel("1× (real-time)")
        self._lbl_speed.setFixedWidth(110)

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
        self._diagram_tab.pid_change_requested.connect(self._on_pid_requested)
        self._diagram_tab.sensor_info_requested.connect(self._on_sensor_info_requested)
        self._diagram_tab.reactor_info_requested.connect(self._on_reactor_info_requested)
        self._diagram_tab.hx_info_requested.connect(self._on_hx_info_requested)
        self._diagram_tab.tc_info_requested.connect(self._on_tc_info_requested)

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
        self._admin_tab.clear_plots()
        self._diagram_tab.clear_events()
        self._running = True
        self._btn_go.setText("STOP")
        self._btn_go.setObjectName("btn_stop")
        self._btn_go.style().unpolish(self._btn_go)
        self._btn_go.style().polish(self._btn_go)
        self._lbl_status.setText("Running")
        self._lbl_status.setStyleSheet("color: #57e389; font-weight: bold; background: transparent;")
        self._diagram_tab.add_event(0.0, "Simulation started", "info")
        # Apply + log the parameters in effect at the start of the run
        self._last_params = {}
        self._apply_params(0.0, force_all=True)
        self._first_apply = False
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
        self._diagram_tab.add_event(t, "Simulation stopped", "info")
        self._table_tab.update_on_stop(self._engine.data_store)
        self._admin_tab.update_on_stop(self._engine.data_store)
        self._switch_tab(2)

    def _on_reset_clicked(self) -> None:
        if self._running:
            self._stop()
        self._engine.reset()
        self._graph_tab.clear_plots()
        self._admin_tab.clear_plots()
        self._diagram_tab.clear_events()
        self._last_params = {}
        self._first_apply = True
        self._lbl_sim_time.setText("0.0 s")
        self._lbl_status.setText("Ready")
        self._lbl_status.setStyleSheet("color: #cd9309; font-weight: bold; background: transparent;")

    def _on_speed_changed(self, value: int) -> None:
        self._speed_factor = value
        self._lbl_speed.setText("1× (real-time)" if value == 1 else f"{value}×")

    def _on_apply_clicked(self) -> None:
        self._apply_params(force_all=self._first_apply)
        self._first_apply = False

    def _apply_params(self, t: float | None = None, force_all: bool = False) -> None:
        """Push current panel parameters to the engine and log them."""
        params = self._diagram_tab.get_params()
        self._engine.apply_parameters(params)
        self._diagram_tab.mark_params_clean()
        if t is None:
            snap = self._engine.get_snapshot()
            t = snap.sim_time if snap else 0.0
        self._log_param_events(params, t, force_all=force_all)
        self._last_params.update(params)

    def _log_param_events(self, params: dict, t: float, force_all: bool = False) -> None:
        """Emit one descriptive event per supplied parameter.

        With force_all=True, every supplied parameter is logged regardless of
        whether it changed (used for the first Apply). Otherwise only the
        parameters that differ from their last applied value are logged.
        """
        changed = False
        for key, (name, fmt) in _PARAM_FMT.items():
            new = params.get(key)
            if new is None:
                continue
            old = self._last_params.get(key)
            if force_all or old is None or abs(old - new) > 1e-10:
                self._diagram_tab.add_event(t, f"{name} → {fmt(new)}", "info")
                changed = True
        if not changed:
            self._diagram_tab.add_event(t, "No parameter change", "info")

    def _on_pid_requested(self) -> None:
        p = self._engine.get_pid_params()
        dlg = PIDDialog(p["Kp"], p["Ki"], p["Kd"], parent=self)
        dlg.pid_changed.connect(self._on_pid_changed)
        dlg.exec()

    def _on_pid_changed(self, pid: dict) -> None:
        self._engine.apply_parameters(pid)
        snap = self._engine.get_snapshot()
        t = snap.sim_time if snap else 0.0
        self._log_param_events(pid, t)
        self._last_params.update(pid)

    def _on_sensor_info_requested(self) -> None:
        SensorInfoDialog(parent=self).exec()

    def _on_reactor_info_requested(self) -> None:
        ReactorInfoDialog(parent=self).exec()

    def _on_hx_info_requested(self) -> None:
        HXInfoDialog(parent=self).exec()

    def _on_tc_info_requested(self) -> None:
        dlg = TCInfoDialog(parent=self)
        dlg.configure_pid_requested.connect(self._on_pid_requested)
        dlg.exec()

    def _on_admin_requested(self) -> None:
        if not self._admin_unlocked:
            pw, ok = QInputDialog.getText(
                self, "Admin Access", "Password:",
                QLineEdit.EchoMode.Password,
            )
            if not ok:
                return
            if pw != "12345":
                QMessageBox.warning(self, "Access Denied", "Incorrect password.")
                return
            self._admin_unlocked = True
            self._btn_admin.setText("Admin")
        self._switch_tab(4)

    # ── Home navigation ────────────────────────────────────────────────────────

    def _on_home_clicked(self) -> None:
        self.pause()
        self.home_requested.emit()

    def pause(self) -> None:
        """Stop the simulation if running. Called when leaving to Home so the
        student doesn't come back to a run that kept ticking unattended."""
        if self._running:
            self._stop()

    def _refresh_ui(self, snap: EngineSnapshot) -> None:
        # Cheap, every tick: keeps live readings, indicators and alarms current.
        self._diagram_tab.update_readings(snap)
        self._lbl_sim_time.setText(f"{snap.sim_time:.1f} s")

        # Expensive plot redraws: throttle to ~10 Hz and only the visible tab.
        self._plot_tick += 1
        if self._plot_tick % 2:
            return
        current = self._tabs.currentWidget()
        if current is self._graph_tab:
            self._graph_tab.update_plots(self._engine.data_store)
        elif current is self._admin_tab:
            self._admin_tab.update_plots(self._engine.data_store)
