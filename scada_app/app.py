from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QLabel, QSlider,
    QInputDialog, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer

from constants import TIMER_INTERVAL_MS, BASE_SIM_DT, K2C

_ML_MIN = 60_000_000.0   # m³/s → mL/min

# Human-readable description for each parameter key + display formatter
_PARAM_FMT: dict[str, tuple[str, object]] = {
    'Qa0':           ('EtAc flow',   lambda v: f'{v * _ML_MIN:.1f} mL/min'),
    'Ca0':           ('EtAc conc',   lambda v: f'{v:.3f} mol/L'),
    'Qb0':           ('NaOH flow',   lambda v: f'{v * _ML_MIN:.1f} mL/min'),
    'Cb0':           ('NaOH conc',   lambda v: f'{v:.3f} mol/L'),
    'T_in_setpoint': ('PFR inlet T', lambda v: f'{v - K2C:.1f} C'),
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

_HEADER_H = 44
_FOOTER_H = 50

_DARK_BG   = "#262626"   # Ubuntu dark surface
_DARK_LINE = "#525252"   # Ubuntu border

# P&ID SVG natural size × 1.2 — 20 % larger, aspect ratio preserved
_SVG_W    = 1010   # 842 × 1.2
_SVG_H    = 714    # 595 × 1.2
_SIDEBAR_W = 230   # right sidebar width — must match diagram_tab._SIDEBAR_W


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PFR Reactor SCADA")
        self.setFixedSize(_SVG_W + _SIDEBAR_W, _SVG_H + _HEADER_H + _FOOTER_H)
        self._fullscreen = False

        self._engine         = SimulationEngine(self)
        self._speed_factor   = 1
        self._running        = False
        self._last_params: dict = {}   # tracks last applied params for diff-based events
        self._admin_unlocked = False

        self._build_ui()
        self._wire_signals()

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_INTERVAL_MS)
        self._timer.timeout.connect(self._on_timer_tick)

    # ── Top-level layout ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        vlay = QVBoxLayout(root)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        vlay.addWidget(self._make_header())
        vlay.addWidget(self._make_main(), stretch=1)
        vlay.addWidget(self._make_footer())

    # ── Header: tab buttons (left) + title (right) ───────────────────────────

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
        """)

        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(0)

        self._tab_btns: list[QPushButton] = []
        for idx, name in enumerate(("Diagram", "Graph", "Table")):
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
        lay.addWidget(QLabel("PFR Reactor SCADA Simulator"))
        return hdr

    # ── Main content: full-width tab widget ───────────────────────────────────

    def _make_main(self) -> QTabWidget:
        self._tabs = QTabWidget()
        self._tabs.tabBar().hide()

        self._diagram_tab = DiagramTab()
        self._graph_tab   = GraphTab()
        self._table_tab   = TableTab()
        self._admin_tab   = AdminTab()
        self._tabs.addTab(self._diagram_tab, "Diagram")
        self._tabs.addTab(self._graph_tab,   "Graph")
        self._tabs.addTab(self._table_tab,   "Table")
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
        sep.setStyleSheet("color: #525252; font-size: 16px;")

        self._lbl_status = QLabel("Stopped")
        self._lbl_status.setStyleSheet("color: #ff7b63; font-weight: bold;")

        self._lbl_sim_time = QLabel("0.0 s")
        self._lbl_sim_time.setStyleSheet("color: #E95420; font-weight: bold;")

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
        self._btn_go.style().unpolish(self._btn_go)
        self._btn_go.style().polish(self._btn_go)
        self._lbl_status.setText("Running")
        self._lbl_status.setStyleSheet("color: #57e389; font-weight: bold;")
        self._diagram_tab.add_event(0.0, "Simulation started", "info")
        self._timer.start()

    def _stop(self) -> None:
        self._timer.stop()
        self._running = False
        self._btn_go.setText("GO")
        self._btn_go.setObjectName("btn_go")
        self._btn_go.style().unpolish(self._btn_go)
        self._btn_go.style().polish(self._btn_go)
        self._lbl_status.setText("Stopped")
        self._lbl_status.setStyleSheet("color: #ff7b63; font-weight: bold;")
        snap = self._engine.get_snapshot()
        t = snap.sim_time if snap else 0.0
        self._diagram_tab.add_event(t, "Simulation stopped", "info")
        self._table_tab.update_on_stop(self._engine.data_store)
        self._switch_tab(2)

    def _on_reset_clicked(self) -> None:
        if self._running:
            self._stop()
        self._engine.reset()
        self._graph_tab.clear_plots()
        self._admin_tab.clear_plots()
        self._diagram_tab.clear_events()
        self._last_params = {}
        self._lbl_sim_time.setText("0.0 s")
        self._lbl_status.setText("Ready")
        self._lbl_status.setStyleSheet("color: #cd9309; font-weight: bold;")

    def _on_speed_changed(self, value: int) -> None:
        self._speed_factor = value
        self._lbl_speed.setText("1× (real-time)" if value == 1 else f"{value}×")

    def _on_apply_clicked(self) -> None:
        params = self._diagram_tab.get_params()
        self._engine.apply_parameters(params)
        self._diagram_tab.mark_params_clean()
        snap = self._engine.get_snapshot()
        t = snap.sim_time if snap else 0.0
        self._log_param_events(params, t)
        self._last_params = dict(params)

    def _log_param_events(self, params: dict, t: float) -> None:
        """Emit one descriptive event per parameter that actually changed."""
        changed = False
        for key, (name, fmt) in _PARAM_FMT.items():
            old = self._last_params.get(key)
            new = params.get(key)
            if new is None:
                continue
            if old is None or abs(old - new) > 1e-10:
                self._diagram_tab.add_event(t, f"{name} → {fmt(new)}", "info")
                changed = True
        if not changed:
            self._diagram_tab.add_event(t, "No parameter change", "info")

    def _on_pid_requested(self) -> None:
        p = self._engine.get_pid_params()
        dlg = PIDDialog(p["Kp"], p["Ki"], p["Kd"], parent=self)
        dlg.pid_changed.connect(self._engine.apply_parameters)
        dlg.exec()

    def _on_sensor_info_requested(self) -> None:
        SensorInfoDialog(parent=self).exec()

    def _on_reactor_info_requested(self) -> None:
        snap = self._engine.get_snapshot()
        ReactorInfoDialog(snap=snap, parent=self).exec()

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
        self._switch_tab(3)

    # ── Full-screen toggle (F11) ──────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_F11:
            if self._fullscreen:
                self.showNormal()
                self._fullscreen = False
            else:
                self.showFullScreen()
                self._fullscreen = True
        else:
            super().keyPressEvent(event)

    def _refresh_ui(self, snap: EngineSnapshot) -> None:
        self._diagram_tab.update_readings(snap)
        self._graph_tab.update_plots(self._engine.data_store)
        self._admin_tab.update_plots(self._engine.data_store)
        self._lbl_sim_time.setText(f"{snap.sim_time:.1f} s")
