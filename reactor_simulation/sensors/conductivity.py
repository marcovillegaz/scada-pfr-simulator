"""Conductivity sensor — linear calibration curve with Gaussian noise."""

import numpy as np


class ConductivitySensor:
    """
    Conductivity sensor for concentration measurement.

    Calibration curve:  σ = a · C + b   [mS/cm],  C in mol/L
    Output:             σ_measured = max(0, σ + N(0, noise_std))

    Typical saponification outlet defaults (NaOH consumed):
        a = 12.0  mS·cm⁻¹/(mol/L)
        b = 0.05  mS/cm  (background / electrode offset)
    """

    def __init__(
        self,
        a: float = 12.0,
        b: float = 0.05,
        noise_std: float = 0.005,
        seed: int | None = None,
    ):
        self._a = a
        self._b = b
        self._noise_std = noise_std
        self._rng = np.random.default_rng(seed)

    def measure(self, concentration: float) -> float:
        """Return noisy conductivity reading for the given concentration [mol/L]."""
        sigma = self._a * concentration + self._b
        return float(max(0.0, sigma + self._rng.normal(0.0, self._noise_std)))

    def reset(self) -> None:
        """No persistent state — kept for API consistency."""
