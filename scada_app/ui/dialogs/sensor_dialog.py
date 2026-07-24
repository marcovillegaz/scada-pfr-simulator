from __future__ import annotations

from PyQt6.QtWidgets import QGroupBox

from ui.dialogs._base import EquipmentInfoDialog, form_box, description_box


class SensorInfoDialog(EquipmentInfoDialog):
    """Equipment description panel for conductivity transmitter CT-101."""

    def __init__(self, parent=None):
        super().__init__("CT-101 — Equipment Info", width=400, parent=parent)
        self._add_title("CT-101  —  Conductivity Transmitter")
        self._layout.addWidget(self._instrument_box())
        self._layout.addWidget(self._calibration_box())
        self._layout.addWidget(description_box(
            "Two platinum electrodes are flush-mounted in the outlet pipe. "
            "The transmitter applies a 1 kHz AC excitation across the electrodes "
            "and measures the resulting current. The impedance of the solution "
            "drops as the ionic concentration rises — the instrument converts this "
            "to conductivity in mS/cm.\n\n"
            "As the saponification reaction proceeds, sodium acetate (NaAc) "
            "accumulates in the outlet stream. NaAc is a strong electrolyte, so "
            "conductivity rises with conversion. The linear calibration model "
            "(σ = A · C_A + B) converts the conductivity reading back to the "
            "residual NaOH concentration C_A at the reactor outlet.\n\n"
            "A small Gaussian noise term is added to each reading to replicate "
            "real-world instrument noise — observe the slight fluctuation on "
            "the Graph tab while the simulation runs."
        ))
        self._finish_buttons()

    def _instrument_box(self) -> QGroupBox:
        return form_box("Instrument Data", [
            ("Tag",                    "CT-101"),
            ("Type",                   "Conductivity Transmitter"),
            ("Brand",                  "Mettler Toledo"),
            ("Model",                  "Thornton 200CR"),
            ("Measurement principle",  "Two-electrode conductometric"),
            ("Electrode material",     "Platinum (Pt), epoxy-sealed"),
            ("Range",                  "0 – 20 mS/cm"),
            ("Accuracy",               "± 0.5 %  full scale"),
            ("Temp. compensation",     "Automatic, 0 – 50 °C  (NTC element)"),
            ("Output",                 "4 – 20 mA  (linear over range)"),
            ("Process connection",     "Inline, 1/2\" NPT, flush-mount"),
        ])

    def _calibration_box(self) -> QGroupBox:
        return form_box("Calibration Model", [
            ("Model",        "σ  =  A · C_A  +  B"),
            ("A  (slope)",   "factory-calibrated"),
            ("B  (offset)",  "factory-calibrated"),
            ("Valid range",  "0 – 0.1 mol/L  (NaOH in product stream)"),
        ])
