"""
Reactor physics module

Contains reactor base class and specific implementations.
Reactors hold state variables and know about kinetics, but do NOT know about:
- How temperature is controlled
- How sensors measure
- How actuators work
"""

import numpy as np
import scipy.integrate as integrate

R_GAS = 8.314  # J/(mol·K)


class Reactor:
    """Base class for all reactor types"""

    def __init__(self, order_of_reaction, kinetic_constant, activation_energy=0.0):
        self.order_of_reaction = order_of_reaction
        self.kinetic_constant = kinetic_constant  # k0 pre-exponential factor (or isothermal k)
        self.activation_energy = activation_energy  # Ea in J/mol (0 = isothermal)
        self.reactor_type = None

    def rate_constant(self, T=None):
        """
        Return k(T) via Arrhenius: k0 * exp(-Ea / (R * T)).
        When activation_energy=0 or T is None, returns kinetic_constant unchanged.
        """
        if self.activation_energy == 0.0 or T is None:
            return self.kinetic_constant
        return self.kinetic_constant * np.exp(-self.activation_energy / (R_GAS * T))

    def reaction_rate(self, Ca, T):
        """
        Power-law rate: -rA = k(T) * Ca^n
        Returns consumption rate in the same units as Ca per unit time.
        """
        return self.rate_constant(T) * Ca**self.order_of_reaction

    def residence_time(self):
        """Calculate residence time - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses should implement this method")

    def get_volume(self, volumetric_flow, output_conversion, input_concentration, input_conversion):
        """Calculate reactor volume from flow and conversions"""
        residence_time = self.residence_time(
            output_conversion,
            input_concentration,
            input_conversion,
        )
        volume = volumetric_flow * residence_time
        return volume


class PlugFlow(Reactor):
    """Plug Flow Reactor (PFR) - ideal tubular reactor with no axial mixing"""

    def __init__(self, order_of_reaction, kinetic_constant, activation_energy=0.0):
        super().__init__(order_of_reaction, kinetic_constant, activation_energy)
        self.reactor_type = "Plug Flow"

    def residence_time(
        self,
        output_conversion,
        input_concentration,
        input_conversion,
        epsilon,
        T=None,
    ):
        """
        Calculate residence time for PFR.

        Parameters:
            output_conversion: Final conversion (Xaf)
            input_concentration: Initial concentration (Ca0)
            input_conversion: Initial conversion (Xai)
            epsilon: Fractional volume change
            T: Temperature (K). When provided, k is computed via Arrhenius.
        """
        n = self.order_of_reaction
        k = self.rate_constant(T)
        Ca0 = input_concentration
        Xaf = output_conversion
        Xai = input_conversion

        integral, _ = integrate.quad(
            lambda Xa: ((1 + epsilon * Xa) / (1 - Xa)) ** n,
            Xai,
            Xaf,
        )

        return (1 / (k * Ca0 ** (n - 1))) * integral


# FUTURE
class StirredTank(Reactor):
    """Continuous Stirred Tank Reactor (CSTR) - perfectly mixed reactor"""

    def __init__(self, order_of_reaction, kinetic_constant, activation_energy=0.0):
        super().__init__(order_of_reaction, kinetic_constant, activation_energy)
        self.reactor_type = "Stirred Tank"

    def residence_time(
        self,
        output_conversion,
        input_concentration,
        input_conversion,
        epsilon,
        T=None,
    ):
        """
        Calculate residence time for CSTR.

        Parameters:
            output_conversion: Final conversion (Xaf)
            input_concentration: Initial concentration (Ca0)
            input_conversion: Initial conversion (Xai)
            epsilon: Fractional volume change
            T: Temperature (K). When provided, k is computed via Arrhenius.
        """
        n = self.order_of_reaction
        k = self.rate_constant(T)
        Ca0 = input_concentration
        Xaf = output_conversion
        Xai = input_conversion

        return (1 / (k * Ca0 ** (n - 1))) * (Xaf * (((1 + epsilon * Xaf) / (1 - Xaf)) ** n))


# FUTURE
class RecyclePlugFlow(Reactor):
    """Plug Flow Reactor with recycle stream"""

    def __init__(self, order_of_reaction, kinetic_constant, activation_energy=0.0):
        super().__init__(order_of_reaction, kinetic_constant, activation_energy)
        self.reactor_type = "Recycle Plug Flow"

    def residence_time(self, R, initial_concentration, final_conversion):
        """
        Calculate residence time for PFR with recycle

        Parameters:
            R: Recycle ratio
            initial_concentration: Initial concentration (Ca0)
            final_conversion: Final conversion (Xa_f)
        """
        Ca0 = initial_concentration
        Xa_f = final_conversion
        Xa_i = (R / (R + 1)) * Xa_f
        n = self.order_of_reaction
        k = self.kinetic_constant

        integral, _ = integrate.quad(
            lambda Xa: 1 / ((k * (Ca0 * (1 - Xa)) ** (n - 1))),
            Xa_i,
            Xa_f,
        )
        tau = Ca0 * (R + 1) * integral
        return tau

    def average_rate(self, R, final_conversion, initial_concentration):
        """Calculate average reaction rate"""
        Ca0 = initial_concentration
        Xa_f = final_conversion
        Xa_i = (R / (R + 1)) * Xa_f
        n = self.order_of_reaction
        k = self.kinetic_constant

        integral, _ = integrate.quad(
            lambda Xa: 1 / ((k * (Ca0 * (1 - Xa)) ** (n - 1))),
            Xa_i,
            Xa_f,
        )

        av_rate = integral / (Xa_f - Xa_i)
        return av_rate
