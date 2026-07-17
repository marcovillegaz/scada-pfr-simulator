"""Photocolorimeter — in-line absorbance analyzer (AIT) for the RTD tracer
experiment (Experiencia 3). The truth/data boundary: the engine holds the
exact, continuous outlet concentration; the student only ever sees what
crosses this class. See docs/PLAN.md §5.2 and docs/FUNDAMENTS_EXP3.md §2.4.
"""

import numpy as np


class Photocolorimeter:
    """
    AIT — in-line photocolorimeter measuring absorbance of the tracer.

    CRITICAL (mirrors the other sensors in this package): this class never
    returns concentration. sample() takes the true concentration in and
    returns absorbance out; there is no method to recover C from a reading.

    Four layers, applied in order on every accepted sample (§5.2):
      1. Fixed-period sampling      — only draws a new reading every
                                       dt_sample seconds; between samples,
                                       repeated calls hold the last value
                                       (mirrors a real instrument's refresh
                                       rate).
      2. Lambert-Beer conversion    — A = epsilon_b * C          (eq. 8)
      3. Gaussian measurement noise — seeded, reproducible for grading
      4. Linear-range saturation    — clips at A_max, if enabled
    """

    def __init__(
        self,
        epsilon_b: float,
        dt_sample: float,
        noise_std: float = 0.01,
        A_max: float | None = None,
        seed: int | None = None,
    ):
        self._epsilon_b = epsilon_b
        self._dt_sample = dt_sample
        self._noise_std = noise_std
        self._A_max = A_max
        self._rng = np.random.default_rng(seed)

        # Force a sample on the first call regardless of the dt it's given.
        self._time_since_sample = float(dt_sample)
        self._last_reading = 0.0

    def sample(self, true_concentration: float, dt: float) -> float:
        """
        Advance dt seconds and return the current absorbance reading [—].

        Only draws a new noisy reading once dt_sample seconds have elapsed
        since the last one; calls in between return the held value.
        """
        self._time_since_sample += dt
        if self._time_since_sample >= self._dt_sample:
            self._time_since_sample = 0.0
            A = self._epsilon_b * true_concentration
            A += self._rng.normal(0.0, self._noise_std)
            A = max(0.0, A)
            if self._A_max is not None:
                A = min(A, self._A_max)
            self._last_reading = A
        return self._last_reading

    def reset(self) -> None:
        """Clear the held reading and force an immediate sample next call."""
        self._time_since_sample = float(self._dt_sample)
        self._last_reading = 0.0

    def __repr__(self) -> str:
        return (
            f"Photocolorimeter(A={self._last_reading:.4f}, "
            f"epsilon_b={self._epsilon_b:.3f}, dt_sample={self._dt_sample:.1f}s)"
        )
