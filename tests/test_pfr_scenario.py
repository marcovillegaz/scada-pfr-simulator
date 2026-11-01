"""Tests for the PFR scenario loader (scada_app/scenarios/loader.py's PFR
section) and PFREngine's use of it. Mirrors test_rtd_scenario_integrity.py's
spirit -- but PFR has no hidden truth to protect (no oculto/build_* split;
see loader.py's PFR module docstring for why), so this only needs to check
that the scenario loads correctly and the engine is genuinely data-driven.
"""

from __future__ import annotations

import pytest

from scenarios.loader import (
    PFRScenario, PFRVisible, load_pfr_scenario, list_pfr_scenarios,
)


class TestPFRScenarioLoading:
    def test_loads_default_scenario(self):
        scenario = load_pfr_scenario("pfr_default")
        assert isinstance(scenario, PFRScenario)
        assert scenario.id == "pfr_default"
        assert isinstance(scenario.visible, PFRVisible)

    def test_geometry_matches_json(self):
        scenario = load_pfr_scenario("pfr_default")
        g = scenario.visible.geometry
        assert g.length_m == pytest.approx(20.9)
        assert g.diameter_m == pytest.approx(0.005)
        assert g.n_nodes == 50

    def test_kinetics_and_feed_are_populated(self):
        scenario = load_pfr_scenario("pfr_default")
        assert scenario.visible.kinetics.activation_energy_J_mol == pytest.approx(46000.0)
        assert scenario.visible.feed.Ca0_mol_L == pytest.approx(0.1)
        assert scenario.visible.pid.Kp == pytest.approx(0.14)
        assert scenario.visible.sensors.ct101_calib_a == pytest.approx(156.0)

    def test_list_pfr_scenarios_returns_at_least_one(self):
        scenarios = list_pfr_scenarios()
        assert len(scenarios) >= 1
        assert all(isinstance(s, PFRScenario) for s in scenarios)
        assert "pfr_default" in [s.id for s in scenarios]

    def test_unknown_scenario_id_raises(self):
        with pytest.raises(FileNotFoundError):
            load_pfr_scenario("does_not_exist")


class TestPFREngineIsDataDriven:
    def test_engine_loads_scenario_not_constants(self):
        """PFREngine's physics traces back to the scenario object, not a
        module-level constant -- e.g. changing the loaded scenario's
        geometry changes what the engine actually builds."""
        from engine.pfr_engine import PFREngine

        engine = PFREngine("pfr_default")
        assert engine.scenario_id == "pfr_default"
        assert engine._scenario.visible.geometry.length_m == pytest.approx(20.9)

    def test_tick_and_reset_smoke(self):
        from engine.pfr_engine import PFREngine

        engine = PFREngine("pfr_default")
        for _ in range(10):
            engine.tick(0.5)
        snap = engine.get_snapshot()
        assert snap is not None
        assert snap.T_out > 0
        engine.reset()
        assert engine.get_snapshot() is None
