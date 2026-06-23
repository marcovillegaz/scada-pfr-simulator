"""
Simulation module

Orchestration of reactor experiments:
- Time loop management
- Numerical integration
- Perturbations (step, ramp, sinusoidal, random)
- Data logging
- Experiment design

This is the "lab bench" - it coordinates all other components
"""

from .experiment import Experiment
from .perturbations import StepPerturbation, RampPerturbation, SinusoidalPerturbation

__all__ = ["Experiment", "StepPerturbation", "RampPerturbation", "SinusoidalPerturbation"]
