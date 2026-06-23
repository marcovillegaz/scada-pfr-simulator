"""Tests for reactor_simulation.actuators — HeatExchanger and Pump."""

import pytest
from reactor_simulation import HeatExchanger, Pump


# ── HeatExchanger ─────────────────────────────────────────────────────────────

class TestHeatExchanger:
    def test_initial_utility_temp_is_minimum(self):
        hx = HeatExchanger(T_utility_min=300.0, T_utility_max=500.0)
        assert hx.T_utility_actual == pytest.approx(300.0)
        assert hx.T_utility_setpoint == pytest.approx(300.0)

    def test_custom_initial_temperature(self):
        hx = HeatExchanger(T_utility_min=300.0, T_utility_max=500.0, T_initial=350.0)
        assert hx.T_utility_actual == pytest.approx(350.0)

    def test_set_utility_temperature_clips_to_max(self):
        hx = HeatExchanger(T_utility_min=273.0, T_utility_max=500.0)
        hx.set_utility_temperature(9000.0)
        assert hx.T_utility_setpoint == pytest.approx(500.0)

    def test_set_utility_temperature_clips_to_min(self):
        hx = HeatExchanger(T_utility_min=273.0, T_utility_max=500.0)
        hx.set_utility_temperature(0.0)
        assert hx.T_utility_setpoint == pytest.approx(273.0)

    def test_heating_gives_positive_Q(self):
        """Utility hotter than process → Q > 0 (heat into process)."""
        hx = HeatExchanger(UA=100.0, time_constant=0.0, T_initial=500.0)
        hx.set_utility_temperature(500.0)
        Q = hx.update(T_process=300.0, dt=1.0)
        assert Q > 0

    def test_cooling_gives_negative_Q(self):
        """Utility colder than process → Q < 0 (heat out of process)."""
        hx = HeatExchanger(UA=100.0, time_constant=0.0, T_initial=273.15)
        hx.set_utility_temperature(273.15)
        Q = hx.update(T_process=350.0, dt=1.0)
        assert Q < 0

    def test_Q_magnitude_follows_UA_times_delta_T(self):
        """Q = UA * (T_utility - T_process) with no lag and no fouling."""
        UA = 150.0
        T_util = 450.0
        T_proc = 350.0
        hx = HeatExchanger(UA=UA, time_constant=0.0, T_initial=T_util)
        hx.set_utility_temperature(T_util)
        Q = hx.update(T_process=T_proc, dt=1.0)
        assert Q == pytest.approx(UA * (T_util - T_proc))

    def test_utility_temperature_lags_with_time_constant(self):
        hx = HeatExchanger(UA=100.0, T_utility_min=273.0, T_utility_max=500.0,
                           time_constant=50.0, T_initial=273.0)
        hx.set_utility_temperature(500.0)
        hx.update(T_process=300.0, dt=1.0)
        assert 273.0 < hx.T_utility_actual < 300.0  # still far from 500 K

    def test_utility_temperature_converges(self):
        hx = HeatExchanger(UA=100.0, time_constant=5.0,
                           T_utility_min=273.0, T_utility_max=600.0, T_initial=300.0)
        hx.set_utility_temperature(500.0)
        for _ in range(500):
            hx.update(T_process=300.0, dt=0.5)
        assert abs(hx.T_utility_actual - 500.0) < 0.1

    def test_fouling_reduces_UA(self):
        hx = HeatExchanger(UA=200.0, fouling_factor=0.5, time_constant=0.0, T_initial=500.0)
        assert hx.UA_effective == pytest.approx(100.0)

    def test_fouling_reduces_heat_flow(self):
        hx_clean  = HeatExchanger(UA=200.0, fouling_factor=0.0, time_constant=0.0, T_initial=500.0)
        hx_fouled = HeatExchanger(UA=200.0, fouling_factor=0.5, time_constant=0.0, T_initial=500.0)
        Q_clean  = hx_clean.get_heat_flow(T_process=300.0)
        Q_fouled = hx_fouled.get_heat_flow(T_process=300.0)
        assert Q_fouled == pytest.approx(Q_clean * 0.5)

    def test_get_heat_flow_does_not_advance_state(self):
        hx = HeatExchanger(UA=100.0, time_constant=10.0, T_initial=273.0)
        hx.set_utility_temperature(500.0)
        before = hx.T_utility_actual
        hx.get_heat_flow(T_process=300.0)
        assert hx.T_utility_actual == before  # state unchanged

    def test_reset_restores_initial_conditions(self):
        hx = HeatExchanger(T_utility_min=273.0, T_utility_max=500.0, time_constant=5.0)
        hx.set_utility_temperature(500.0)
        for _ in range(100):
            hx.update(T_process=300.0, dt=1.0)
        hx.reset()
        assert hx.T_utility_actual == pytest.approx(273.0)
        assert hx.T_utility_setpoint == pytest.approx(273.0)


# ── Pump ──────────────────────────────────────────────────────────────────────

class TestPump:
    def test_initial_state_is_zero(self):
        p = Pump()
        assert p.flow_setpoint == 0.0
        assert p.actual_flow == 0.0

    def test_set_flow_clips_to_max(self):
        p = Pump(max_flow=1e-3)
        p.set_flow(1.0)
        assert p.flow_setpoint == 1e-3

    def test_set_flow_clips_to_min(self):
        p = Pump(min_flow=1e-5)
        p.set_flow(-1.0)
        assert p.flow_setpoint == 1e-5

    def test_actual_flow_ramps_gradually(self):
        """Flow should not jump instantly — limited by max_ramp_rate."""
        p = Pump(max_flow=1e-3, max_ramp_rate=1e-4)
        p.set_flow(1e-3)
        p.update(dt=1.0)
        assert p.actual_flow <= 1e-4 + 1e-12  # only one ramp step

    def test_actual_flow_reaches_setpoint(self):
        p = Pump(max_flow=1e-3, max_ramp_rate=1e-4)
        p.set_flow(5e-4)
        for _ in range(100):
            p.update(dt=1.0)
        assert abs(p.actual_flow - 5e-4) < 1e-9

    def test_update_returns_actual_flow(self):
        p = Pump(max_flow=1e-3, max_ramp_rate=1e-4)
        p.set_flow(1e-4)
        flow = p.update(dt=1.0)
        assert flow == p.actual_flow

    def test_get_flow_matches_actual(self):
        p = Pump()
        p.set_flow(5e-4)
        p.update(dt=10.0)
        assert p.get_flow() == p.actual_flow

    def test_reset_zeroes_state(self):
        p = Pump(max_flow=1e-3)
        p.set_flow(1e-3)
        for _ in range(50):
            p.update(dt=1.0)
        p.reset()
        assert p.flow_setpoint == 0.0
        assert p.actual_flow == 0.0
