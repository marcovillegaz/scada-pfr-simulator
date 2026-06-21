from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QPushButton, QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt

from constants import (
    PFR_LENGTH, PFR_DIAMETER, PFR_N_NODES, PFR_CROSS_AREA,
    K2C,
)
from engine.data_store import EngineSnapshot


class ReactorInfoDialog(QDialog):
    """Equipment info panel for the PFR reactor."""

    def __init__(self, snap: EngineSnapshot | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PFR Reactor — Equipment Info")
        self.setFixedWidth(360)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._build_ui(snap)

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build_ui(self, snap: EngineSnapshot | None) -> None:
        vlay = QVBoxLayout(self)
        vlay.setSpacing(10)

        title = QLabel("Plug Flow Reactor  (PFR-101)")
        title.setStyleSheet("color:#E95420;font-weight:bold;font-size:13px;")
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2d3f50;")
        vlay.addWidget(sep)

        vlay.addWidget(self._geometry_box())
        vlay.addWidget(self._operating_box(snap))

        close_btn = QPushButton("Close")
        close_btn.setObjectName("btn_apply")
        close_btn.clicked.connect(self.accept)
        vlay.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _geometry_box(self) -> QGroupBox:
        box = QGroupBox("Geometry")
        form = QFormLayout(box)
        form.setSpacing(5)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        V = PFR_LENGTH * PFR_CROSS_AREA
        rows = [
            ("Type",          "Plug Flow Reactor"),
            ("Length",        f"{PFR_LENGTH:.2f} m"),
            ("Diameter",      f"{PFR_DIAMETER*1000:.1f} mm"),
            ("Cross-section", f"{PFR_CROSS_AREA:.4e} m²"),
            ("Volume",        f"{V*1e6:.2f} mL  ({V:.4e} m³)"),
            ("Spatial nodes", f"{PFR_N_NODES}"),
        ]
        for field, value in rows:
            form.addRow(_lbl(field), _val(value))
        return box

    def _operating_box(self, snap: EngineSnapshot | None) -> QGroupBox:
        box = QGroupBox("Operating Conditions")
        form = QFormLayout(box)
        form.setSpacing(5)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        if snap is not None:
            Q_total = (snap.Qa0 + snap.Qb0) * 60_000_000    # mL/min
            u       = snap.velocity                          # m/s
            tau     = PFR_LENGTH / u if u > 0 else float("inf")
            T_in    = snap.T_hx  - K2C
            T_out   = snap.T_out - K2C
            X_out   = snap.X_out * 100
            rows = [
                ("Q total",  f"{Q_total:.2f} mL/min"),
                ("u",        f"{u:.4f} m/s"),
                ("τ  (L/u)", f"{tau:.2f} s"),
                ("T in",     f"{T_in:.2f} °C"),
                ("T out",    f"{T_out:.2f} °C"),
                ("X out",    f"{X_out:.2f} %"),
            ]
        else:
            rows = [
                ("Q total",  "—"),
                ("u",        "—"),
                ("τ  (L/u)", "—"),
                ("T in",     "—"),
                ("T out",    "—"),
                ("X out",    "—"),
            ]
        for field, value in rows:
            form.addRow(_lbl(field), _val(value))
        return box


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lbl(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet("color:#adadad;font-size:11px;")
    return l

def _val(text: str) -> QLabel:
    l = QLabel(text)
    l.setStyleSheet("color:#eeeeec;font-size:11px;")
    return l
