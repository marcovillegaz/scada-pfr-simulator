"""
Reactor models

Every reactor/process model lives here, one file per model, organized by
physical type — not by teaching experience (see docs/shared/CONVENTION.md).
Each model owns its own integrator ("step logic is the unit's, not the
caller's").

- analytic.py  — Reactor, PlugFlow, StirredTank, RecyclePlugFlow (steady-state
                 analytical sizing models)
- state.py     — ReactorState (state-vector helper for the analytical models)
- pfr.py       — PFRSimulator (dynamic Method-of-Lines PFR, the model behind
                 the PFR/Experiencia 2 module)
- packed_bed.py — PackedBedRTD, pulse_concentration (compartment-network
                 packed bed with hidden hydrodynamic pathologies, the model
                 behind the RTD/Experiencia 3 module)

Future reactor types (CSTR, bioreactor, ...) are new files here, not new
subpackages.
"""

from .analytic import Reactor, PlugFlow, StirredTank, RecyclePlugFlow
from .state import ReactorState
from .pfr import PFRSimulator
from .packed_bed import PackedBedRTD, pulse_concentration

__all__ = [
    "Reactor",
    "PlugFlow",
    "StirredTank",
    "RecyclePlugFlow",
    "ReactorState",
    "PFRSimulator",
    "PackedBedRTD",
    "pulse_concentration",
]
