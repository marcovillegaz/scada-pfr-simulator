"""Optional plotting helper for Reaction.

Kept out of the Reaction class (and out of kinetics/__init__.py's eager
imports) so importing reactor_simulation.kinetics doesn't pull in matplotlib
as a hard dependency of a physics class -- UI/visualization concerns don't
belong in the physics layer (see docs/shared/CONVENTION.md). Only script-mode
examples that want a quick plot need to import this module.
"""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt

from . import Reaction


def plot_concentration_vs_reaction_rate(reaction: Reaction, concentration_range) -> None:
    """Scatter-plot reaction rate vs. concentration for `reaction`."""
    reaction_rates = np.vectorize(reaction.reaction_rate)(concentration_range)

    plt.scatter(concentration_range, reaction_rates)
    plt.xlabel("Concentration")
    plt.ylabel("Reaction Rate")
    plt.title("Concentration vs Reaction Rate")
    plt.grid(True)
    plt.show()
