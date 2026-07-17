"""
RTD module — residence-time-distribution tracer experiment (Experiencia 3).

Compartment-network model of a packed bed with hidden hydrodynamic
pathologies (channeling, dead zone). See docs/FUNDAMENTS_EXP3.md for the
mathematical derivation and docs/PLAN.md for the module plan.
"""

from .packed_bed import PackedBedRTD, pulse_concentration

__all__ = [
    "PackedBedRTD",
    "pulse_concentration",
]
