"""Temperature sensor — additive Gaussian measurement noise (TE-101 / TE-102)."""

import numpy as np


class TemperatureSensor:
    """
    Temperature transmitter (thermocouple / RTD).

    Mirrors :class:`ConductivitySensor`: a simple measurement model that adds
    Gaussian noise (and an optional fixed calibration bias) to the true process
    temperature, so the reported reading is never the exact value.

        T_measured = T_true + bias + N(0, noise_std)   [K]
    """

    def __init__(
        self,
        noise_std: float = 0.3,
        bias: float = 0.0,
        seed: int | None = None,
    ):
        self._noise_std = noise_std
        self._bias = bias
        self._rng = np.random.default_rng(seed)

    def measure(self, temperature: float) -> float:
        """Return a noisy temperature reading [K] for the given true value."""
        return float(temperature + self._bias + self._rng.normal(0.0, self._noise_std))

    def reset(self) -> None:
        """No persistent state — kept for API consistency."""
