from __future__ import annotations

from PyQt6.QtWidgets import QGroupBox

from scenarios.loader import Scenario
from ui.dialogs._base import EquipmentInfoDialog, form_box, description_box


class RTDReactorInfoDialog(EquipmentInfoDialog):
    """Equipment description panel for one of the three CIP-isolable packed-
    bed columns (R-102/103/104). Deliberately built only from Scenario.visible
    -- there is no attribute path from Scenario to the hidden hydrodynamic
    truth (see scenarios/loader.py), so there is nothing here that could leak
    it even by accident."""

    def __init__(self, tag: str, scenario: Scenario, parent=None):
        super().__init__(f"{tag} — Equipment Info", width=380, parent=parent)
        self._add_title(f"{tag}  —  Packed-Bed Column")
        self._layout.addWidget(self._geometry_box(tag, scenario))
        self._layout.addWidget(description_box(
            "During CIP, this column is isolated from normal production and "
            "fed washing substance while the other two reactors stay online.\n\n"
            "The internal packing state (channeling, dead zones) is never "
            "shown directly — it can only be inferred by injecting a tracer "
            "and reading the outlet residence-time-distribution curve at "
            "AT-101.\n\n"
            "The nominal residence time τ = V/Q above is identical for all "
            "three columns by design, so any difference a student measures "
            "between them reflects the hidden state of the packing, not a "
            "difference in vessel size or flow setpoint."
        ))
        self._finish_buttons()

    def _geometry_box(self, tag: str, scenario: Scenario) -> QGroupBox:
        reactor = scenario.visible.reactor
        tau_s = reactor.V_L / (reactor.Q_nominal_L_min / 60.0)
        return form_box("Nameplate Data", [
            ("Tag",             tag),
            ("Service",         scenario.nombre),
            ("Type",            "Packed-bed column, CIP-isolable"),
            ("Nominal volume",  f"{reactor.V_L:.2f} L"),
            ("Nominal flow",    f"{reactor.Q_nominal_L_min:.2f} L/min"),
            ("Nominal τ = V/Q", f"{tau_s:.0f} s  ({tau_s / 60:.2f} min)"),
        ])
