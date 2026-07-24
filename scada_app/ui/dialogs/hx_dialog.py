from __future__ import annotations

from PyQt6.QtWidgets import QGroupBox

from constants import HX_VOLUME, UA_MAX, T_HOT_WATER, K2C
from ui.dialogs._base import EquipmentInfoDialog, form_box, description_box


class HXInfoDialog(EquipmentInfoDialog):
    """Equipment description panel for heat exchangers E-101 / E-102."""

    def __init__(self, parent=None):
        super().__init__("E-101 / E-102 — Equipment Info", width=420, parent=parent)
        self._add_title("E-101 / E-102  —  Shell & Tube Heat Exchangers")
        self._layout.addWidget(self._design_box())
        self._layout.addWidget(description_box(
            "Feed A (NaOH) and Feed B (EtAc) enter through separate pre-heaters "
            "E-101 and E-102 respectively. Both units draw from the same hot-water "
            "supply (60 °C) controlled by a single valve V-101.\n\n"
            "Opening the valve increases the heat transfer coefficient UA, "
            "raising the outlet temperature T_in of both streams. The heated "
            "streams then recombine at the mixing node before entering "
            "reactor R-101.\n\n"
            "The simulation models E-101 and E-102 as a single lumped heat "
            "exchanger node. Both streams are assumed to reach the same T_in "
            "at the mixing point — a valid approximation when the two flows "
            "are similar and the exchangers are thermally matched.\n\n"
            "TC-101 closes the control loop: it reads T_reactor and adjusts "
            "V-101 to maintain the operator setpoint."
        ))
        self._finish_buttons()

    def _design_box(self) -> QGroupBox:
        return form_box("Design Parameters", [
            ("Type",               "Shell & tube, single pass"),
            ("Configuration",      "Two units in parallel  (E-101 ∥ E-102)"),
            ("E-101 duty",         "Pre-heats Feed A  (Qa0, NaOH stream)"),
            ("E-102 duty",         "Pre-heats Feed B  (Qb0, EtAc stream)"),
            ("Utility",            f"Hot water  —  T = {T_HOT_WATER - K2C:.0f} °C  (shared supply)"),
            ("UA  max (combined)", f"{UA_MAX:.0f} W/K  (at full valve opening)"),
            ("Process holdup",     f"{HX_VOLUME * 1e3:.0f} L  (per unit, combined model)"),
            ("Control valve",      "V-101  —  hot-water flow  0 – 100 %"),
        ])
