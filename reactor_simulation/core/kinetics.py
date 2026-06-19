"""
Reaction kinetics module

Handles reaction rate expressions and stoichiometry
"""

import inspect
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad


class Reaction:
    """Represents a chemical reaction with kinetic expression"""
    
    def __init__(
        self,
        reaction_type,
        stoichiometry,
        expression,
        fractional_change=0,
    ):
        self.reaction_type = reaction_type
        self.stoichiometry = stoichiometry
        self.expression = expression
        self.fractional_change = fractional_change

    def print_expression(self):
        """Print the kinetic expression source code"""
        expression_source = inspect.getsource(self.expression).strip()
        print(f"Kinetic of {self}: {expression_source}")

    def reaction_rate(self, input_value):
        """Calculate reaction rate for given input"""
        return self.expression(input_value)

    def plot_concentration_vs_reaction_rate(self, concentration_range):
        """Plot concentration vs reaction rate"""
        # Apply the reaction rate to the concentration array
        reaction_rates = np.vectorize(self.reaction_rate)(concentration_range)

        plt.scatter(concentration_range, reaction_rates)
        plt.xlabel("Concentration")
        plt.ylabel("Reaction Rate")
        plt.title("Concentration vs Reaction Rate")
        plt.grid(True)
        plt.show()


def overall_yield_pfr(phi, Ca_0, Ca_f):
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


def overall_yield_mfr(phi, Ca_f):
    """
    Compute overall yield for MFR reactor
    
    Parameters:
        phi (function): Function representing the reaction rate fraction φ(Ca)
        Ca_f (float): Final concentration of A
        
    Returns:
        float: Overall yield (Phi_m)
    """
    return phi(Ca_f)
