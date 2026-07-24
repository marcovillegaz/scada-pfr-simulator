"""
Reactor Simulation Package

A modular chemical reactor simulation package designed with clear separation
of concerns, organized by physical ROLE (see docs/shared/CONVENTION.md for
the full module convention and how this package relates to the SCADA app):
- Models: Reactor/process models — each owns its own integrator (PFR, packed
  bed RTD, analytical PlugFlow/StirredTank/RecyclePlugFlow, ...)
- Kinetics: Reaction rate expressions and stoichiometry
- Actuators: Physical devices that modify boundary conditions (heater, pump,
  heat exchanger)
- Control: Control algorithms (PID, feedforward)
- Sensors: Measurement devices with realistic noise and delays
- Simulation: Orchestration, time integration, and experiment design

Usage Example:
    from reactor_simulation.models import ReactorState, PlugFlow, StirredTank
    from reactor_simulation.actuators import Heater, Pump
    from reactor_simulation.control import PIDController
    from reactor_simulation.sensors import Thermocouple, ConductivitySensor
    from reactor_simulation.simulation import Experiment
"""

__version__ = "0.1.0"

# Import key classes for convenience
from .models import (
    Reactor, PlugFlow, StirredTank, RecyclePlugFlow, ReactorState,
    PFRSimulator, PackedBedRTD, pulse_concentration,
)
from .kinetics import Reaction
from .actuators import Heater, HeatExchanger, HXDynamic, Pump
from .control import PIDController
from .sensors import Thermocouple, ConductivitySensor, Photocolorimeter
from .simulation import Experiment, StepPerturbation, RampPerturbation, SinusoidalPerturbation

__all__ = [
    # Models
    "Reactor",
    "PlugFlow",
    "StirredTank",
    "RecyclePlugFlow",
    "ReactorState",
    "PFRSimulator",
    "PackedBedRTD",
    "pulse_concentration",
    # Kinetics
    "Reaction",
    # Actuators
    "Heater",
    "HeatExchanger",
    "HXDynamic",
    "Pump",
    # Control
    "PIDController",
    # Sensors
    "Thermocouple",
    "ConductivitySensor",
    "Photocolorimeter",
    # Simulation
    "Experiment",
    "StepPerturbation",
    "RampPerturbation",
    "SinusoidalPerturbation",
]

