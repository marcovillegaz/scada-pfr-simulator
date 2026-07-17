"""Tests for reactor_simulation.sensors.Photocolorimeter — the truth/data
boundary for the RTD tracer experiment (docs/PLAN.md §5.2)."""

import pytest

from reactor_simulation import Photocolorimeter


class TestPhotocolorimeter:

    def test_lambert_beer_no_noise(self):
        """eq. 8: A = epsilon_b * C, with noise disabled and dt >= dt_sample
        so the first call always samples."""
        sensor = Photocolorimeter(epsilon_b=0.85, dt_sample=2.0, noise_std=0.0, seed=0)
        A = sensor.sample(true_concentration=1.0, dt=2.0)
        assert A == pytest.approx(0.85)

    def test_higher_concentration_gives_higher_absorbance(self):
        s1 = Photocolorimeter(epsilon_b=0.85, dt_sample=2.0, noise_std=0.0, seed=0)
        s2 = Photocolorimeter(epsilon_b=0.85, dt_sample=2.0, noise_std=0.0, seed=0)
        A_low = s1.sample(true_concentration=0.5, dt=2.0)
        A_high = s2.sample(true_concentration=2.0, dt=2.0)
        assert A_high > A_low

    def test_fixed_period_sampling_holds_between_samples(self):
        """Before dt_sample has elapsed, repeated calls return the same
        held reading even if the true concentration changes underneath."""
        sensor = Photocolorimeter(epsilon_b=1.0, dt_sample=5.0, noise_std=0.0, seed=0)
        first = sensor.sample(true_concentration=1.0, dt=5.0)   # forces first sample
        held = sensor.sample(true_concentration=99.0, dt=1.0)   # well under dt_sample
        assert held == first

    def test_fixed_period_sampling_updates_after_period(self):
        sensor = Photocolorimeter(epsilon_b=1.0, dt_sample=5.0, noise_std=0.0, seed=0)
        sensor.sample(true_concentration=1.0, dt=5.0)   # forces first sample -> A=1.0
        updated = sensor.sample(true_concentration=2.0, dt=5.0)  # elapsed >= dt_sample again
        assert updated == pytest.approx(2.0)

    def test_saturation_clips_to_A_max(self):
        sensor = Photocolorimeter(
            epsilon_b=1.0, dt_sample=1.0, noise_std=0.0, A_max=1.0, seed=0,
        )
        A = sensor.sample(true_concentration=5.0, dt=1.0)  # unsaturated would be 5.0
        assert A == pytest.approx(1.0)

    def test_no_saturation_when_A_max_none(self):
        sensor = Photocolorimeter(
            epsilon_b=1.0, dt_sample=1.0, noise_std=0.0, A_max=None, seed=0,
        )
        A = sensor.sample(true_concentration=5.0, dt=1.0)
        assert A == pytest.approx(5.0)

    def test_reading_never_negative(self):
        sensor = Photocolorimeter(epsilon_b=0.0, dt_sample=1.0, noise_std=10.0, seed=1)
        for _ in range(50):
            A = sensor.sample(true_concentration=0.0, dt=1.0)
            assert A >= 0.0

    def test_seed_makes_noise_reproducible(self):
        s1 = Photocolorimeter(epsilon_b=1.0, dt_sample=1.0, noise_std=0.05, seed=42)
        s2 = Photocolorimeter(epsilon_b=1.0, dt_sample=1.0, noise_std=0.05, seed=42)
        readings1 = [s1.sample(1.0, dt=1.0) for _ in range(20)]
        readings2 = [s2.sample(1.0, dt=1.0) for _ in range(20)]
        assert readings1 == readings2

    def test_different_seeds_diverge(self):
        s1 = Photocolorimeter(epsilon_b=1.0, dt_sample=1.0, noise_std=0.05, seed=1)
        s2 = Photocolorimeter(epsilon_b=1.0, dt_sample=1.0, noise_std=0.05, seed=2)
        readings1 = [s1.sample(1.0, dt=1.0) for _ in range(20)]
        readings2 = [s2.sample(1.0, dt=1.0) for _ in range(20)]
        assert readings1 != readings2

    def test_reset_forces_immediate_resample(self):
        sensor = Photocolorimeter(epsilon_b=1.0, dt_sample=5.0, noise_std=0.0, seed=0)
        sensor.sample(true_concentration=1.0, dt=5.0)
        sensor.reset()
        # Immediately after reset, a call with dt < dt_sample should still
        # sample (reset primes _time_since_sample = dt_sample).
        A = sensor.sample(true_concentration=3.0, dt=0.1)
        assert A == pytest.approx(3.0)

    def test_no_concentration_getter_exists(self):
        """Structural check: nothing on this class can hand back the true
        concentration -- only sample() exists, and it returns absorbance."""
        sensor = Photocolorimeter(epsilon_b=1.0, dt_sample=1.0, seed=0)
        public_methods = [m for m in dir(sensor) if not m.startswith("_")]
        assert public_methods == sorted({"sample", "reset"})
