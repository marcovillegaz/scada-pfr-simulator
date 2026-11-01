"""
Pump actuator module

Controls volumetric flow rate with realistic constraints
"""

from __future__ import annotations

import numpy as np


class Pump:
    """
    Pump actuator that sets volumetric flow rate

    Features:
    - Flow rate limits (min/max)
    - Ramp rate limits (acceleration/deceleration)
    - Optional noise/variation
    """

    def __init__(
        self,
        max_flow=0.001,  # m³/s (1 L/s)
        min_flow=0.0,  # m³/s
        max_ramp_rate=0.0001,  # m³/s² (limits acceleration)
    ):
        """
        Initialize pump

        Parameters:
            max_flow: Maximum flow rate (m³/s)
            min_flow: Minimum flow rate (m³/s)
            max_ramp_rate: Maximum rate of change (m³/s per second)
        """
        self.max_flow = max_flow
        self.min_flow = min_flow
        self.max_ramp_rate = max_ramp_rate

        # Internal state
        self.flow_setpoint = 0.0  # Commanded flow
        self.actual_flow = 0.0  # Actual flow (accounting for ramp limits)

    def set_flow(self, flow):
        """
        Set pump flow setpoint

        Parameters:
            flow: Desired flow rate (m³/s)
        """
        # Apply saturation limits
        self.flow_setpoint = np.clip(flow, self.min_flow, self.max_flow)

    def update(self, dt):
        """
        Update pump state with ramp rate limiting

        Parameters:
            dt: Time step (s)

        Returns:
            actual_flow: Actual flow rate (m³/s)
        """
        # Calculate desired change
        delta_flow = self.flow_setpoint - self.actual_flow

        # Apply ramp rate limit
        max_change = self.max_ramp_rate * dt
        delta_flow = np.clip(delta_flow, -max_change, max_change)

        # Update actual flow
        self.actual_flow += delta_flow

        return self.actual_flow

    def get_flow(self):
        """Get current flow rate (m³/s)"""
        return self.actual_flow

    def reset(self):
        """Reset pump to off state"""
        self.flow_setpoint = 0.0
        self.actual_flow = 0.0

    def __repr__(self):
        return (f"Pump(setpoint={self.flow_setpoint*1000:.2f} L/s, "
                f"actual={self.actual_flow*1000:.2f} L/s)")
