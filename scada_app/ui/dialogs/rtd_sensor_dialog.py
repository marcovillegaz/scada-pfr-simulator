from __future__ import annotations

from PyQt6.QtWidgets import QGroupBox

from scenarios.loader import ScenarioSensor
from ui.dialogs._base import EquipmentInfoDialog, form_box, description_box


class RTDSensorInfoDialog(EquipmentInfoDialog):
    """Equipment description panel for photocolorimeter AT-101. Built only
    from ScenarioSensor's visible fields -- the RNG seed lives in
    sensor.json's own oculto block and is never attached to this object (see
    scenarios/loader.py's sensor_seed()), so there is no path to leak it."""

    def __init__(self, sensor: ScenarioSensor, parent=None):
        super().__init__("AT-101 — Equipment Info", width=400, parent=parent)
        self._add_title("AT-101  —  Photocolorimeter")
        self._layout.addWidget(self._instrument_box(sensor))
        self._layout.addWidget(description_box(
            "AT-101 is the single in-line photocolorimeter reading whichever "
            "reactor is currently isolated for CIP — it never returns "
            "concentration directly, only absorbance.\n\n"
            "A fixed-period sample is converted from concentration to "
            "absorbance via the Lambert-Beer law, a Gaussian noise term is "
            "added to replicate real instrument noise, and the reading is "
            "clipped at the linear range limit if it saturates.\n\n"
            "Converting the exported absorbance series back to concentration "
            "and reconstructing the residence-time-distribution curve E(t) "
            "is the student's job — see the Docs tab."
        ))
        self._finish_buttons()

    def _instrument_box(self, sensor: ScenarioSensor) -> QGroupBox:
        return form_box("Instrument Data", [
            ("Tag",                   "AT-101"),
            ("Type",                  "In-line Photocolorimeter"),
            ("Measurement principle", "Lambert-Beer absorbance,  A = ε·b·C"),
            ("Calibration (ε·b)",     f"{sensor.epsilon_b:.2f}  L/mg"),
            ("Linear range",          f"0 – {sensor.A_max:.2f}  AU"),
            ("Sampling period",       f"{sensor.dt_sample_s:.1f}  s"),
            ("Measurement noise",     f"σ ≈ {sensor.noise_std:.3f}  AU  (Gaussian)"),
            ("Shared across",         "R-102 / R-103 / R-104 (one physical unit)"),
        ])
