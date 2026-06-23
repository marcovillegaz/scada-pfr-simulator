import inspect
import numpy as np
import matplotlib.pyplot as plt


class Reaction:
    def __init__(
        self,
        raction_type,
        stoichiometry,
        expression,
        fractional_change=0,
    ):
        self.raction_type = raction_type
        self.expression = expression
        self.fractional_change = fractional_change

    def print_expression(self):
        expression_source = inspect.getsource(self.expression).strip()
        print(f"Kinetic of {self}: {expression_source}")

    def reaction_rate(self, input_value):
        return self.expression(input_value)

    def plot_concentration_vs_reaction_rate(self, concentration_range):
        # Apply the vectorized_reaction_rate method to the concentration array
        reaction_rates = self.reaction.vectorized_reaction_rate(concentration_range)

        # Create a scatter plot of concentration vs reaction rate
        plt.scatter(concentration_range, reaction_rates)
        plt.xlabel("Concentration")
        plt.ylabel("Reaction Rate")
        plt.title("Concentration vs Reaction Rate")
        plt.grid(True)
        plt.show()
