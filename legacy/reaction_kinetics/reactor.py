import numpy as np
import scipy.integrate as integrate


class Reactor:
    def __init__(self, order_of_reaction, kinetic_constant):
        self.order_of_reaction = order_of_reaction
        self.kinetic_constant = kinetic_constant
        self.reactor_type = None  # Default to None, subclasses can set this

    def residence_time(self):
        # This method will be overridden by child classes
        raise NotImplementedError("Subclasses should implement this method")

    def get_volume(
        self, volumetric_flow, output_conversion, input_concentration, input_conversion
    ):
        residence_time = self.residence_time(
            output_conversion,
            input_concentration,
            input_conversion,
        )
        volume = volumetric_flow * residence_time
        return volume

    def get_flow(self):
        pass


class PlugFlow(Reactor):
    def __init__(self, order_of_reaction, kinetic_constant):
        super().__init__(order_of_reaction, kinetic_constant)
        self.reactor_type = "Plug Flow"

    def residence_time(
        self,
        output_conversion,
        input_concentration,
        input_conversion,
        epsilon,
    ):
        # Redifinition of variable for better manipulation
        n = self.order_of_reaction
        k = self.kinetic_constant
        Ca0 = input_concentration
        Xaf = output_conversion
        Xai = input_conversion

        integral, _ = integrate.quad(
            lambda Xa: ((1 + epsilon * Xa) / (1 - Xa)) ** n,
            Xai,
            Xaf,
        )

        return (1 / (k * Ca0 ** (n - 1))) * integral


class StirredTank(Reactor):
    def __init__(self, order_of_reaction, kinetic_constant):
        super().__init__(order_of_reaction, kinetic_constant)
        self.reactor_type = "Stirred Tank"

    def residence_time(
        self,
        output_conversion,
        input_concentration,
        input_conversion,
        epsilon,
    ):
        # Redifinition of variable for better manipulation
        n = self.order_of_reaction
        k = self.kinetic_constant
        Ca0 = input_concentration
        Xaf = output_conversion
        Xai = input_conversion

        return (1 / (k * Ca0 ** (n - 1))) * (
            Xaf * (((1 + epsilon * Xaf) / (1 - Xaf)) ** n)
        )


class RecyclePlugFlow(Reactor):
    def __init__(self, order_of_reaction, kinetic_constant):
        super().__init__(order_of_reaction, kinetic_constant)
        self.reactor_type = "Recycle Plug Flow"

    def residence_time(self, R, initial_cocnentration, final_conversion):
        Ca0 = initial_cocnentration
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

    def avarage_rate(self, R, final_conversion, initial_cocnentration):
        Ca0 = initial_cocnentration
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
