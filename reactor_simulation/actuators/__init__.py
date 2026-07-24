"""
Actuators module

Physical devices that modify boundary conditions (not state directly):
- Heater: Converts electrical power to heat input
- HeatExchanger: Utility-temperature-driven HX with first-order lag
  (general-purpose, used in examples/ script-mode teaching)
- HXDynamic: Valve-driven HX with an exact analytic energy balance
  (drives the live SCADA PFR engine -- see hx_dynamic.py's module docstring
  for why both HX models coexist)
- Pump: Sets flow rate

Actuators have physical inertia and limitations
"""

from .heater import Heater
from .heat_exchanger import HeatExchanger
from .hx_dynamic import HXDynamic
from .pump import Pump

__all__ = ["Heater", "HeatExchanger", "HXDynamic", "Pump"]
