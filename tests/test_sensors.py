"""Tests for reactor_simulation.sensors — Thermocouple and ConductivitySensor."""

import pytest
import numpy as np
from reactor_simulation import Thermocouple, ConductivitySensor


# ── Thermocouple ──────────────────────────────────────────────────────────────

class TestThermocouple:
    def test_initial_reading_is_ambient(self):
        tc = Thermocouple()
        assert tc.reading == pytest.approx(298.15)

    def test_measurement_approaches_true_temperature(self):
        """After many steps the filtered reading should converge to true temp."""
        tc = Thermocouple(noise_std=0.0, time_constant=2.0, bias=0.0, seed=0)
        for _ in range(200):
            tc.measure(true_temperature=400.0, dt=0.5)
        assert abs(tc.reading - 400.0) < 0.5

    def test_bias_shifts_reading(self):
        tc = Thermocouple(noise_std=0.0, time_constant=0.0, bias=5.0, seed=0)
        reading = tc.measure(true_temperature=300.0, dt=1.0)
        assert abs(reading - 305.0) < 0.01

    def test_reading_clipped_to_max(self):
        tc = Thermocouple(noise_std=0.0, time_constant=0.0,
                          bias=0.0, max_temp=350.0, seed=0)
        reading = tc.measure(true_temperature=600.0, dt=1.0)
        assert reading <= 350.0

    def test_reading_clipped_to_min(self):
        tc = Thermocouple(noise_std=0.0, time_constant=0.0,
                          bias=0.0, min_temp=200.0, seed=0)
        # Force very low reading via large negative bias
        tc2 = Thermocouple(noise_std=0.0, time_constant=0.0,
                           bias=-200.0, min_temp=200.0, seed=0)
        reading = tc2.measure(true_temperature=300.0, dt=1.0)
        assert reading >= 200.0

    def test_noise_std_zero_gives_deterministic_result(self):
        tc = Thermocouple(noise_std=0.0, time_constant=0.0, bias=0.0, seed=0)
        r1 = tc.measure(350.0, dt=1.0)
        tc2 = Thermocouple(noise_std=0.0, time_constant=0.0, bias=0.0, seed=0)
        r2 = tc2.measure(350.0, dt=1.0)
        assert r1 == r2

    def test_seed_makes_noise_reproducible(self):
        tc1 = Thermocouple(noise_std=1.0, time_constant=0.0, bias=0.0, seed=42)
        tc2 = Thermocouple(noise_std=1.0, time_constant=0.0, bias=0.0, seed=42)
        readings1 = [tc1.measure(300.0, dt=1.0) for _ in range(20)]
        readings2 = [tc2.measure(300.0, dt=1.0) for _ in range(20)]
        assert readings1 == readings2

    def test_lag_means_reading_lags_behind(self):
        """With a long time constant, one step should not reach true temp."""
        tc = Thermocouple(noise_std=0.0, time_constant=100.0, bias=0.0, seed=0)
        reading = tc.measure(true_temperature=500.0, dt=1.0)
        assert reading < 400.0  # still far from 500 K after one step

    def test_get_reading_no_new_noise(self):
        """get_reading() should return the same value on repeated calls."""
        tc = Thermocouple(noise_std=5.0, seed=0)
        tc.measure(300.0, dt=1.0)
        r1 = tc.get_reading()
        r2 = tc.get_reading()
        assert r1 == r2

    def test_reset_returns_to_initial(self):
        tc = Thermocouple(seed=0)
        for _ in range(50):
            tc.measure(500.0, dt=1.0)
        tc.reset(initial_temp=298.15)
        assert tc.reading == pytest.approx(298.15)

    def test_calibrate_changes_bias(self):
        tc = Thermocouple(bias=0.0)
        tc.calibrate(new_bias=3.0)
        assert tc.bias == 3.0


# ── ConductivitySensor ────────────────────────────────────────────────────────

class TestConductivitySensor:
    def test_measurement_is_nonnegative(self):
        sensor = ConductivitySensor(seed=0)
        cond = sensor.measure(true_concentration=0.5, temperature=300.0, dt=1.0)
        assert cond >= 0.0

    def test_higher_concentration_gives_higher_conductivity(self):
        sensor = ConductivitySensor(noise_std=0.0, seed=0)
        c1 = sensor.measure(0.5, dt=0.0)
        c2 = sensor.measure(2.0, dt=0.0)
        assert c2 > c1

    def test_default_linear_calibration(self):
        """Default params: a=0, b=1, c=0 → conductivity = concentration (no noise)."""
        sensor = ConductivitySensor(noise_std=0.0, seed=0)
        cond = sensor.measure(true_concentration=3.0, dt=0.0)
        assert abs(cond - 3.0) < 1e-9

    def test_inverse_calibration_recovers_concentration(self):
        """concentration_from_conductivity should invert measure() (no noise, no drift)."""
        sensor = ConductivitySensor(
            calibration_params={'a': 0.0, 'b': 2.5, 'c': 0.1},
            noise_std=0.0,
            drift_rate=0.0,
            seed=0,
        )
        true_conc = 1.5
        cond = sensor.measure(true_conc, temperature=None, dt=0.0)
        recovered = sensor.concentration_from_conductivity(cond, temperature=None)
        assert abs(recovered - true_conc) < 1e-6

    def test_temperature_correction_increases_with_temp(self):
        """Higher temperature → higher conductivity (positive coefficient)."""
        sensor = ConductivitySensor(
            temperature_coefficient=0.02,
            reference_temperature=298.15,
            noise_std=0.0,
            seed=0,
        )
        cond_cold = sensor.measure(1.0, temperature=298.15, dt=0.0)
        sensor2 = ConductivitySensor(
            temperature_coefficient=0.02,
            reference_temperature=298.15,
            noise_std=0.0,
            seed=0,
        )
        cond_hot = sensor2.measure(1.0, temperature=350.0, dt=0.0)
        assert cond_hot > cond_cold

    def test_drift_accumulates_over_time(self):
        sensor = ConductivitySensor(drift_rate=1.0, noise_std=0.0, seed=0)
        c1 = sensor.measure(1.0, dt=3600.0)   # 1 hour → drift = 1.0 mS/cm
        assert sensor.accumulated_drift == pytest.approx(1.0)

    def test_reset_clears_drift(self):
        sensor = ConductivitySensor(drift_rate=1.0, noise_std=0.0, seed=0)
        sensor.measure(1.0, dt=3600.0)
        sensor.reset()
        assert sensor.accumulated_drift == 0.0
        assert sensor.total_time == 0.0

    def test_recalibrate_updates_params_and_resets(self):
        sensor = ConductivitySensor(drift_rate=1.0, noise_std=0.0, seed=0)
        sensor.measure(1.0, dt=3600.0)
        new_params = {'a': 0.1, 'b': 2.0, 'c': 0.5}
        sensor.recalibrate(new_params)
        assert sensor.calibration_params == new_params
        assert sensor.accumulated_drift == 0.0
