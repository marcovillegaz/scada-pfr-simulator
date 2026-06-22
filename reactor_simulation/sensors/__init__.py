"""
Sensors module

Measurement devices with realistic imperfections:
- Thermocouple: Temperature measurement with noise, delay, bias
- Conductivity sensor: Concentration measurement via conductivity
- pH sensor: pH measurement
- Pressure transducer: Pressure measurement

CRITICAL: Sensors never return the true value!
They return noisy, delayed, and potentially biased measurements
This is essential for realistic simulation and education
"""

from .thermocouple import Thermocouple
from .conductivity import ConductivitySensor
from .temperature import TemperatureSensor

__all__ = ["Thermocouple", "ConductivitySensor", "TemperatureSensor"]
