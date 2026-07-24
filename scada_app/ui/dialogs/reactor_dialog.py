from __future__ import annotations

from PyQt6.QtWidgets import QGroupBox

from constants import (
    PFR_LENGTH, PFR_DIAMETER, PFR_N_NODES, PFR_CROSS_AREA,
    H_LOSS, AMBIENT_TEMP, K2C,
)
from ui.dialogs._base import EquipmentInfoDialog, form_box, description_box


class ReactorInfoDialog(EquipmentInfoDialog):
    """Equipment description panel for the PFR reactor R-101."""

    def __init__(self, parent=None):
        super().__init__("R-101 — Equipment Info", width=380, parent=parent)
        self._add_title("R-101  —  Plug Flow Reactor (PFR)")
        self._layout.addWidget(self._geometry_box())
        self._layout.addWidget(self._kinetics_box())
        self._layout.addWidget(self._heat_loss_box())
        self._layout.addWidget(description_box(
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
        ))
        self._finish_buttons()

    def _geometry_box(self) -> QGroupBox:
        V = PFR_LENGTH * PFR_CROSS_AREA
        return form_box("Geometry", [
            ("Type",           "Plug Flow Reactor (tubular)"),
            ("Length",         f"{PFR_LENGTH:.2f} m"),
            ("Inner diameter", f"{PFR_DIAMETER * 1000:.1f} mm"),
            ("Cross-section",  f"{PFR_CROSS_AREA:.4e} m²"),
            ("Volume",         f"{V * 1e6:.2f} mL  ({V:.4e} m³)"),
            ("Spatial nodes",  f"{PFR_N_NODES}  (MOL integration)"),
        ])

    def _kinetics_box(self) -> QGroupBox:
        return form_box("Reaction Kinetics", [
            ("Reaction", "A  +  B  →  Products"),
            ("Rate law", "rA = k(T) · CA_in · CB_in   (2nd order)"),
            ("k(T)",     "k₀ · exp(−Ea / R·T)   (Arrhenius)"),
        ])

    def _heat_loss_box(self) -> QGroupBox:
        # Volumetric loss coefficient for a thin tube:  h_loss = 4U/D  ->  U = h_loss·D/4
        U = H_LOSS * PFR_DIAMETER / 4.0
        return form_box("Heat Losses (non-adiabatic)", [
            ("Model",               "q_loss = h_loss · (T − T_amb)"),
            ("h_loss (volumetric)", f"{H_LOSS:.0f}  W/(m³·K)"),
            ("≈ overall U",         f"{U:.0f}  W/(m²·K)   (bare tube, h_loss = 4U/D)"),
            ("Ambient T_amb",       f"{AMBIENT_TEMP - K2C:.0f} °C"),
        ])
