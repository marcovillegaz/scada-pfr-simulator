"""
Control module

Controllers that act on measurements (not true states):
- PID: Proportional-Integral-Derivative controller
- Feedforward: Model-based control

CRITICAL: Controllers act on sensor readings, not reality!
This creates realistic discrepancies for educational purposes
"""

from .pid import PIDController

__all__ = ["PIDController"]
