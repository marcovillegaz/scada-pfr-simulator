from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QPushButton, QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt

from constants import (
    PFR_LENGTH, PFR_DIAMETER, PFR_N_NODES, PFR_CROSS_AREA,
    H_LOSS, AMBIENT_TEMP, K2C,
)


class ReactorInfoDialog(QDialog):
    """Equipment description panel for the PFR reactor R-101."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("R-101 — Equipment Info")
        self.setFixedWidth(380)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )
        self._build_ui()

    def _build_ui(self) -> None:
        vlay = QVBoxLayout(self)
        vlay.setSpacing(10)

        title = QLabel("R-101  —  Plug Flow Reactor (PFR)")
        title.setStyleSheet("color:#E95420;font-weight:bold;font-size:13px;")
        vlay.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#2d3f50;")
        vlay.addWidget(sep)

        vlay.addWidget(self._geometry_box())
        vlay.addWidget(self._kinetics_box())
        vlay.addWidget(self._heat_loss_box())
        vlay.addWidget(self._description_box())

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
            ("Type",          "Plug Flow Reactor (tubular)"),
            ("Length",        f"{PFR_LENGTH:.2f} m"),
            ("Inner diameter",f"{PFR_DIAMETER * 1000:.1f} mm"),
            ("Cross-section", f"{PFR_CROSS_AREA:.4e} m²"),
            ("Volume",        f"{V * 1e6:.2f} mL  ({V:.4e} m³)"),
            ("Spatial nodes", f"{PFR_N_NODES}  (MOL integration)"),
        ]
        for field, value in rows:
            form.addRow(_lbl(field), _val(value))
        return box

    def _kinetics_box(self) -> QGroupBox:
        box = QGroupBox("Reaction Kinetics")
        form = QFormLayout(box)
        form.setSpacing(5)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        rows = [
            ("Reaction",  "A  +  B  →  Products"),
            ("Rate law",  "rA = k(T) · CA_in · CB_in   (2nd order)"),
            ("k(T)",      "k₀ · exp(−Ea / R·T)   (Arrhenius)"),
        ]
        for field, value in rows:
            form.addRow(_lbl(field), _val(value))
        return box

    def _heat_loss_box(self) -> QGroupBox:
        box = QGroupBox("Heat Losses (non-adiabatic)")
        form = QFormLayout(box)
        form.setSpacing(5)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        # Volumetric loss coefficient for a thin tube:  h_loss = 4U/D  ->  U = h_loss·D/4
        U = H_LOSS * PFR_DIAMETER / 4.0
        rows = [
            ("Model",            "q_loss = h_loss · (T − T_amb)"),
            ("h_loss (volumetric)", f"{H_LOSS:.0f}  W/(m³·K)"),
            ("≈ overall U",      f"{U:.0f}  W/(m²·K)   (bare tube, h_loss = 4U/D)"),
            ("Ambient T_amb",    f"{AMBIENT_TEMP - K2C:.0f} °C"),
        ]
        for field, value in rows:
            form.addRow(_lbl(field), _val(value))
        return box

    def _description_box(self) -> QGroupBox:
        box = QGroupBox("How it works")
        lay = QVBoxLayout(box)
        text = QLabel(
            "Feed streams A (NaOH) and B (EtAc) are mixed and pre-heated in "
            "HX-101 before entering the reactor at the bottom.\n\n"
            "The reaction proceeds along the tube axis; concentrations and "
            "temperature are computed at each spatial node using the method of "
            "lines (MOL) with RK45 integration. Higher temperature increases the "
            "rate constant (Arrhenius) and therefore the conversion Xₐ.\n\n"
            "The tube is not perfectly insulated, so it loses heat to the "
            "surroundings along its length — the outlet temperature T_out sits a "
            "little below the inlet T_in, and the controller opens the hot-water "
            "valve further to hold the mean reactor temperature at setpoint."
        )
        text.setWordWrap(True)
        text.setStyleSheet("color:#eeeeec;font-size:11px;")
        lay.addWidget(text)
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
