"""
Reactor Simulation Package

A modular chemical reactor simulation package designed with clear separation of concerns:
- Core: Physical state and reactor dynamics
- Actuators: Physical devices that modify boundary conditions (heater, pump)
- Control: Control algorithms (PID, feedforward)
- Sensors: Measurement devices with realistic noise and delays
- Simulation: Orchestration, time integration, and experiment design

Usage Example:
    from reactor_simulation.core import ReactorState, PlugFlow, StirredTank
    from reactor_simulation.actuators import Heater, Pump
    from reactor_simulation.control import PIDController
    from reactor_simulation.sensors import Thermocouple, ConductivitySensor
    from reactor_simulation.simulation import Experiment
"""

__version__ = "0.1.0"

# Import key classes for convenience
from .core import Reactor, PlugFlow, StirredTank, RecyclePlugFlow, Reaction, ReactorState, PFRSimulator
from .actuators import Heater, HeatExchanger, Pump
from .control import PIDController
from .sensors import Thermocouple, ConductivitySensor, Photocolorimeter
from .simulation import Experiment, StepPerturbation, RampPerturbation, SinusoidalPerturbation
from .rtd import PackedBedRTD, pulse_concentration

__all__ = [
    # Core
    "Reactor",
    "PlugFlow",
    "StirredTank",
    "RecyclePlugFlow",
    "Reaction",
    "ReactorState",
    # Actuators
    "Heater",
    "HeatExchanger",
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
    # Dynamic PFR
    "PFRSimulator",
    # RTD (Experiencia 3)
    "PackedBedRTD",
    "pulse_concentration",
]

