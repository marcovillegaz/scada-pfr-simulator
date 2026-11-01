"""Headless tick/snapshot/reset/apply_parameters coverage for PFREngine and
RTDEngine -- previously untested despite being the code the app actually
runs every 50 ms. Both engines
are QObject subclasses but need no QApplication/event loop to construct or
tick -- they do no widget/timer work themselves.
"""

from __future__ import annotations

import pytest

from constants import PFR_DEFAULT_SCENARIO, RTD_DEFAULT_SCENARIO, FLOW_RAMP_DURATION
from engine import PFREngine, RTDEngine


# ── PFREngine ────────────────────────────────────────────────────────────────

class TestPFREngineLifecycle:
    def test_tick_produces_a_snapshot(self):
        engine = PFREngine(PFR_DEFAULT_SCENARIO)
        assert engine.get_snapshot() is None
        engine.tick(0.5)
        snap = engine.get_snapshot()
        assert snap is not None
        assert snap.sim_time > 0.0

    def test_reset_clears_snapshot_and_data_store(self):
        engine = PFREngine(PFR_DEFAULT_SCENARIO)
        for _ in range(5):
            engine.tick(0.5)
        assert len(engine.data_store.run_log) == 5
        engine.reset()
        assert engine.get_snapshot() is None
        assert len(engine.data_store.run_log) == 0

    def test_apply_parameters_updates_concentration_immediately(self):
        engine = PFREngine(PFR_DEFAULT_SCENARIO)
        engine.apply_parameters({'Ca0': 0.5})
        assert engine._Ca0 == pytest.approx(0.5)

    def test_apply_parameters_setpoint_updates_pid(self):
        engine = PFREngine(PFR_DEFAULT_SCENARIO)
        engine.apply_parameters({'T_setpoint': 300.0})
        params = engine.get_pid_params()
        assert params['T_setpoint'] == pytest.approx(300.0)

    def test_apply_parameters_gains_update_pid(self):
        engine = PFREngine(PFR_DEFAULT_SCENARIO)
        engine.apply_parameters({'Kp': 0.5, 'Ki': 0.1, 'Kd': 0.01})
        params = engine.get_pid_params()
        assert params['Kp'] == pytest.approx(0.5)
        assert params['Ki'] == pytest.approx(0.1)
        assert params['Kd'] == pytest.approx(0.01)

    def test_flow_setpoint_ramps_rather_than_jumping(self):
        """Qa0/Qb0 changes ramp over FLOW_RAMP_DURATION rather than applying
        instantly -- apply_parameters schedules a ramp, it doesn't set
        self._Qa0 directly (unlike Ca0/Cb0 above)."""
        engine = PFREngine(PFR_DEFAULT_SCENARIO)
        original_Qa0 = engine._Qa0
        target = original_Qa0 * 3
        engine.apply_parameters({'Qa0': target})
        # Immediately after applying, the ramp has barely started.
        assert engine._Qa0 == pytest.approx(original_Qa0)
        # Advance well past the ramp duration -- should reach the target.
        for _ in range(int(FLOW_RAMP_DURATION) + 5):
            engine.tick(1.0)
        assert engine._Qa0 == pytest.approx(target, rel=1e-3)

    def test_reset_restores_scenario_defaults(self):
        engine = PFREngine(PFR_DEFAULT_SCENARIO)
        default_Ca0 = engine._Ca0
        engine.apply_parameters({'Ca0': default_Ca0 + 1.0})
        engine.tick(0.5)
        engine.reset()
        assert engine._Ca0 == pytest.approx(default_Ca0)


# ── RTDEngine ────────────────────────────────────────────────────────────────

class TestRTDEngineLifecycle:
    def test_tick_produces_a_snapshot(self):
        engine = RTDEngine(RTD_DEFAULT_SCENARIO)
        assert engine.get_snapshot() is None
        engine.tick(1.0)
        snap = engine.get_snapshot()
        assert snap is not None
        assert snap.injecting is False

    def test_reset_clears_snapshot_and_data_store(self):
        engine = RTDEngine(RTD_DEFAULT_SCENARIO)
        for _ in range(4):
            engine.tick(1.0)
        assert len(engine.data_store.run_log) == 4
        engine.reset()
        assert engine.get_snapshot() is None
        assert len(engine.data_store.run_log) == 0

    def test_inject_pulse_flags_injecting_then_clears(self):
        engine = RTDEngine(RTD_DEFAULT_SCENARIO)
        engine.inject_pulse(m=1.0, t_pulse=2.0)
        engine.tick(1.0)
        assert engine.get_snapshot().injecting is True
        # Past the pulse width, injection should have auto-stopped.
        engine.tick(5.0)
        assert engine.get_snapshot().injecting is False

    def test_inject_step_stays_on_until_stopped(self):
        engine = RTDEngine(RTD_DEFAULT_SCENARIO)
        engine.inject_step(C0=1.0)
        for _ in range(10):
            engine.tick(1.0)
        assert engine.get_snapshot().injecting is True
        engine.stop_injection()
        engine.tick(1.0)
        assert engine.get_snapshot().injecting is False

    def test_apply_parameters_changes_flow(self):
        engine = RTDEngine(RTD_DEFAULT_SCENARIO)
        engine.apply_parameters({'Q_L_min': 3.0})
        assert engine.Q_L_s == pytest.approx(3.0 / 60.0)

    def test_set_scenario_switches_and_resets(self):
        engine = RTDEngine(RTD_DEFAULT_SCENARIO)
        engine.tick(1.0)
        engine.set_scenario('planta_b')
        assert engine.scenario_id == 'planta_b'
        assert engine.scenario.id == 'planta_b'
        assert engine.get_snapshot() is None   # reset() cleared it
        # Engine still works after switching.
        engine.tick(1.0)
        assert engine.get_snapshot() is not None

    def test_tau_is_positive_and_derived_from_visible_data(self):
        engine = RTDEngine(RTD_DEFAULT_SCENARIO)
        assert engine.tau > 0.0
        assert engine.tau == pytest.approx(
            engine.scenario.visible.reactor.V_L / engine.Q_L_s
        )
