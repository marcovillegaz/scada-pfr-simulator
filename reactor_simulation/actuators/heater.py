"""
Heater actuator module

Converts electrical power to heat input with realistic dynamics
"""

from __future__ import annotations

import numpy as np


class Heater:
    """
    Heater actuator that converts electrical power to thermal energy

    Features:
    - Power limits (min/max)
    - First-order thermal inertia (optional)
    - Efficiency < 100%
    """

    def __init__(
        self,
        max_power=1000.0,  # W
        min_power=0.0,  # W
        efficiency=0.95,  # 95% efficient
        time_constant=10.0,  # seconds (thermal inertia)
    ):
        """
        Initialize heater

        Parameters:
            max_power: Maximum power output (W)
            min_power: Minimum power output (W)
            efficiency: Heat transfer efficiency (0-1)
            time_constant: First-order time constant for thermal inertia (s)
        """
        self.max_power = max_power
        self.min_power = min_power
        self.efficiency = efficiency
        self.time_constant = time_constant

        # Internal state
        self.power_setpoint = 0.0  # Commanded power
        self.actual_power = 0.0  # Actual power (accounting for inertia)

    def set_power(self, power):
        """
        Set heater power setpoint

        Parameters:
            power: Desired power (W)
        """
        # Apply saturation limits
        self.power_setpoint = np.clip(power, self.min_power, self.max_power)

    def update(self, dt):
        """
        Update heater state with first-order dynamics

        Parameters:
            dt: Time step (s)

        Returns:
            heat_output: Actual heat delivered to reactor (W)
        """
        # First-order lag
        alpha = dt / (self.time_constant + dt)
        self.actual_power += alpha * (self.power_setpoint - self.actual_power)

        # Return heat delivered (accounting for efficiency)
        return self.actual_power * self.efficiency

    def get_heat_flow(self):
        """Get current heat flow to reactor (W)"""
        return self.actual_power * self.efficiency

    def reset(self):
        """Reset heater to off state"""
        self.power_setpoint = 0.0
        self.actual_power = 0.0

    def __repr__(self):
        return (f"Heater(setpoint={self.power_setpoint:.1f} W, "
                f"actual={self.actual_power:.1f} W, "
                f"heat_out={self.get_heat_flow():.1f} W)")
