"""Example comparing residence times of CSTR and PFR reactors"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

from reactor_simulation import PlugFlow, StirredTank

# Constants
k = 0.1
Ca0 = 50
Xai = 0

# Example usage
orders = [0.25, 1, 2]
conversions = np.linspace(0.01, 0.99, 100)
fractional_change = [2, 1, 0, -0.5, -0.66]


plt.figure(figsize=(6, 6))  # Start plot


for n in orders:
    print(f"n = {n}")
    # Define the reactors
    reactor1 = StirredTank(order_of_reaction=n, kinetic_constant=k)
    reactor2 = PlugFlow(order_of_reaction=n, kinetic_constant=k)

    residence_time_1 = np.array([reactor1.residence_time(Xa, Ca0, Xai, 0) for Xa in conversions])
    print(residence_time_1)
    residence_time_2 = np.array([reactor2.residence_time(Xa, Ca0, Xai, 0) for Xa in conversions])

    tau_ratios = (residence_time_1) / (residence_time_2)

    plt.plot((1 - conversions), tau_ratios, label=f"n = {n}")
    color = plt.gca().lines[-1].get_color()  # Get color of the last line

    # plot with fractional change
    for ea in fractional_change:
        print(f"\tea = {ea}")
        residence_time_1 = np.array(
            [reactor1.residence_time(Xa, Ca0, Xai, epsilon=ea) for Xa in conversions]
        )
        print(residence_time_1)
        residence_time_2 = np.array(
            [reactor2.residence_time(Xa, Ca0, Xai, epsilon=ea) for Xa in conversions]
        )

        ea_ratios = (residence_time_1) / (residence_time_2)

        plt.plot((1 - conversions), ea_ratios, linestyle="--", color=color)

# Set labels
plt.xlabel(r"$(1-X_A)$", fontsize=14)
plt.ylabel(r"${\tau_{CSTR}}/{\tau_{PFR}}$", fontsize=14)
# Set axis to logarithmic scale
plt.yscale("log")
plt.xscale("log")
# Disable scientific notation for tick labels
plt.gca().yaxis.set_major_formatter(ScalarFormatter())
plt.gca().xaxis.set_major_formatter(ScalarFormatter())
# Set limits
# plt.ylim(, 2)
plt.xlim(0.01, 1)
# Set grid
plt.grid(True, which="both", linestyle="--", linewidth=0.5)
# Set legend
plt.legend()
# Show
plt.show()
