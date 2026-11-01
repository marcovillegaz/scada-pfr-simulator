"""
Reaction kinetics module

Handles reaction rate expressions and stoichiometry. Plotting is deliberately
not a method here -- see plotting.py's module docstring for why (UI concerns
don't belong in the physics layer, per docs/shared/CONVENTION.md).
"""

from __future__ import annotations

import inspect
from typing import Callable

from scipy.integrate import quad


class Reaction:
    """Represents a chemical reaction with kinetic expression"""

    def __init__(
        self,
        reaction_type: str,
        stoichiometry: dict,
        expression: Callable[[float], float],
        fractional_change: float = 0,
    ):
        self.reaction_type = reaction_type
        self.stoichiometry = stoichiometry
        self.expression = expression
        self.fractional_change = fractional_change

    def print_expression(self) -> None:
        """Print the kinetic expression source code"""
        expression_source = inspect.getsource(self.expression).strip()
        print(f"Kinetic of {self}: {expression_source}")

    def reaction_rate(self, input_value: float) -> float:
        """Calculate reaction rate for given input"""
        return self.expression(input_value)


def overall_yield_pfr(phi: Callable[[float], float], Ca_0: float, Ca_f: float) -> float:
    """
    Compute overall yield for PFR reactor

    Parameters:
        phi (function): Function representing the reaction rate fraction φ(Ca)
        Ca_0 (float): Initial concentration of A
        Ca_f (float): Final concentration of A

    Returns:
        float: Overall yield (Phi_p)
    """
    integral, _ = quad(phi, Ca_0, Ca_f)
    return (1 / (Ca_f - Ca_0)) * integral


def overall_yield_mfr(phi: Callable[[float], float], Ca_f: float) -> float:
    """
    Compute overall yield for MFR reactor

    Parameters:
        phi (function): Function representing the reaction rate fraction φ(Ca)
        Ca_f (float): Final concentration of A

    Returns:
        float: Overall yield (Phi_m)
    """
    return phi(Ca_f)
