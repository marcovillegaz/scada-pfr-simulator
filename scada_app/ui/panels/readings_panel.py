from __future__ import annotations

from PyQt6.QtWidgets import QGroupBox, QGridLayout, QLabel
from PyQt6.QtCore import Qt

from engine.data_store import EngineSnapshot


class ReadingsPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Live Readings", parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QGridLayout(self)
        layout.setColumnMinimumWidth(1, 90)

        def row(label: str, row_idx: int) -> QLabel:
            lbl_name = QLabel(label)
            lbl_name.setObjectName("reading_name")
            lbl_val  = QLabel("—")
            lbl_val.setObjectName("value_label")
            lbl_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(lbl_name, row_idx, 0)
            layout.addWidget(lbl_val,  row_idx, 1)
            return lbl_val

        self._lbl_t_meas  = row("T Measured (K)",   0)
        self._lbl_t_true  = row("T True (K)",        1)
        self._lbl_sp      = row("Setpoint (K)",      2)
        self._lbl_conc    = row("Ca (mol/L)",        3)
        self._lbl_flow    = row("Flow (L/min)",      4)
        self._lbl_power   = row("Heat Flow (W)",     5)

        sep = QLabel("── PID ──")
        sep.setObjectName("separator_label")
        sep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sep, 6, 0, 1, 2)

        self._lbl_pid_p = row("P component", 7)
        self._lbl_pid_i = row("I component", 8)
        self._lbl_pid_d = row("D component", 9)

        layout.setRowStretch(10, 1)

    def update(self, snap: EngineSnapshot) -> None:
        self._lbl_t_meas.setText(f"{snap.measured_temp:.2f}")
        self._lbl_t_true.setText(f"{snap.true_temp:.2f}")
        self._lbl_sp.setText(f"{snap.setpoint:.2f}")
        self._lbl_conc.setText(f"{snap.concentration:.4f}")
        self._lbl_flow.setText(f"{snap.flow_rate * 60000:.3f}")  # m³/s → L/min
        self._lbl_power.setText(f"{snap.heat_flow:.1f}")
        self._lbl_pid_p.setText(f"{snap.pid_p:.2f}")
        self._lbl_pid_i.setText(f"{snap.pid_i:.2f}")
        self._lbl_pid_d.setText(f"{snap.pid_d:.2f}")
