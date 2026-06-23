"""
Actuators module

Physical devices that modify boundary conditions (not state directly):
- Heater: Converts electrical power to heat input
- Pump: Sets flow rate
- Cooling jacket: Heat removal

Actuators have physical inertia and limitations
"""

from .heater import Heater
from .heat_exchanger import HeatExchanger
from .pump import Pump

__all__ = ["Heater", "HeatExchanger", "Pump"]
