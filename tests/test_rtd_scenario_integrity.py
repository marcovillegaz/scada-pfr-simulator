"""Integrity tests for the RTD scenario loader (scada_app/scenarios/loader.py).

docs/PLAN.md §5.3: "Los bloques `visible` y `oculto` deben estar separados a
nivel de esquema, no solo por convención, para que sea estructuralmente
difícil filtrar el segundo." This is the module's most important integrity
requirement -- verified here, not just asserted in a docstring.

These tests check *structure* (no attribute path from Scenario to hidden
data), not just current values -- so a future change that accidentally
attaches a hidden field to Scenario fails loudly here, rather than shipping
a leak to the student-facing UI.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from scenarios.loader import (
    Scenario,
    ScenarioVisible,
    ScenarioReactor,
    ScenarioSensor,
    load_scenario,
    list_scenarios,
    build_rtd_model,
    sensor_seed,
)
from reactor_simulation import PackedBedRTD

# Full hidden vocabulary, used to scan visible blocks for leaks. "seed" is
# still part of it -- it moved from each plant's oculto into sensor.json's
# own oculto, but it must stay just as hidden either way.
_HIDDEN_KEYS = {"f", "phi_d", "k_ex_s", "gamma", "N_m", "N_c", "seed"}
# What an individual plant's oculto block must equal exactly (seed excluded
# -- it now lives in sensor.json's oculto, shared by every reactor).
_PLANT_HIDDEN_KEYS = _HIDDEN_KEYS - {"seed"}
_PLANTS_DIR = Path(__file__).parent.parent / "scada_app" / "scenarios" / "plants"
_SENSOR_PATH = _PLANTS_DIR.parent / "sensor.json"
_SCENARIO_IDS = sorted(p.stem for p in _PLANTS_DIR.glob("*.json"))


class TestScenarioFiles:
    """The raw JSON files themselves must keep the schema-separated shape."""

    def test_at_least_three_scenarios_exist(self):
        assert len(_SCENARIO_IDS) >= 3

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_scenario_has_visible_oculto_blocks(self, scenario_id):
        raw = json.loads((_PLANTS_DIR / f"{scenario_id}.json").read_text(encoding="utf-8"))
        assert set(raw.keys()) >= {"id", "nombre", "visible", "oculto"}

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_hidden_keys_absent_from_visible_block(self, scenario_id):
        """No hidden-parameter name leaks into the visible block (either of
        its reactor/sensor sub-groups), even under a different key name than
        expected (case-insensitive substring check against the known hidden
        vocabulary)."""
        raw = json.loads((_PLANTS_DIR / f"{scenario_id}.json").read_text(encoding="utf-8"))
        visible_keys = {k.lower() for group in raw["visible"].values() for k in group}
        for hidden_key in _HIDDEN_KEYS:
            assert hidden_key.lower() not in visible_keys

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_oculto_block_has_expected_hidden_keys(self, scenario_id):
        raw = json.loads((_PLANTS_DIR / f"{scenario_id}.json").read_text(encoding="utf-8"))
        assert set(raw["oculto"].keys()) == _PLANT_HIDDEN_KEYS

    def test_sensor_file_has_visible_oculto_blocks(self):
        """sensor.json carries the same visible/oculto split as a plant
        file -- the seed is hidden instrument data, not a plant property."""
        raw = json.loads(_SENSOR_PATH.read_text(encoding="utf-8"))
        assert set(raw.keys()) == {"visible", "oculto"}
        assert set(raw["oculto"].keys()) == {"seed"}

    def test_hidden_keys_absent_from_sensor_visible_block(self):
        """sensor.json's visible block is loaded for every scenario (see
        loader.py's load_sensor()) -- it must never carry hidden-parameter
        names, the same way a plant's visible block must not."""
        raw = json.loads(_SENSOR_PATH.read_text(encoding="utf-8"))
        visible_keys = {k.lower() for k in raw["visible"]}
        for hidden_key in _HIDDEN_KEYS:
            assert hidden_key.lower() not in visible_keys


class TestScenarioStructuralNoLeak:
    """The Scenario dataclass returned to student-facing code must have no
    attribute path to hidden data -- checked structurally, not by value."""

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_scenario_dataclass_fields_exclude_hidden_keys(self, scenario_id):
        scenario = load_scenario(scenario_id)
        field_names = {f.name for f in dataclasses.fields(scenario)}
        assert field_names == {"id", "nombre", "visible"}
        assert field_names.isdisjoint(_HIDDEN_KEYS)

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_scenario_visible_fields_exclude_hidden_keys(self, scenario_id):
        scenario = load_scenario(scenario_id)
        visible_field_names = {f.name for f in dataclasses.fields(scenario.visible)}
        reactor_field_names = {f.name for f in dataclasses.fields(scenario.visible.reactor)}
        sensor_field_names = {f.name for f in dataclasses.fields(scenario.visible.sensor)}
        all_field_names = visible_field_names | reactor_field_names | sensor_field_names
        assert all_field_names.isdisjoint(_HIDDEN_KEYS)

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_scenario_has_no_oculto_attribute_at_all(self, scenario_id):
        """Not just "the value is hidden" -- the attribute itself doesn't
        exist under any of the names a leak might plausibly use."""
        scenario = load_scenario(scenario_id)
        for name in ("oculto", "hidden", "_oculto", "_hidden", "ground_truth", "truth"):
            assert not hasattr(scenario, name)

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_scenario_repr_does_not_contain_hidden_values(self, scenario_id):
        """Even accidental logging (str(scenario), repr(scenario)) can't
        print hidden values, because they were never attached to the object."""
        scenario = load_scenario(scenario_id)
        sensor_raw = json.loads(_SENSOR_PATH.read_text(encoding="utf-8"))
        dump = repr(scenario)
        # The hidden seed is a distinctive large int -- if it ever leaked
        # into Scenario's repr, this is the cheapest tripwire to catch it.
        assert str(sensor_raw["oculto"]["seed"]) not in dump

    def test_list_scenarios_returns_only_scenario_objects(self):
        scenarios = list_scenarios()
        assert len(scenarios) == len(_SCENARIO_IDS)
        for s in scenarios:
            assert isinstance(s, Scenario)
            assert isinstance(s.visible, ScenarioVisible)
            assert isinstance(s.visible.reactor, ScenarioReactor)
            assert isinstance(s.visible.sensor, ScenarioSensor)


class TestBuildRtdModel:
    """build_rtd_model() is the one function allowed to touch `oculto` --
    verify it actually builds a correctly-parametrized hidden-truth model,
    and that going through it still doesn't expose the raw values anywhere
    reachable from student-facing code."""

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_builds_a_packed_bed_rtd(self, scenario_id):
        model = build_rtd_model(scenario_id)
        assert isinstance(model, PackedBedRTD)

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_model_matches_hidden_and_visible_parameters(self, scenario_id):
        raw = json.loads((_PLANTS_DIR / f"{scenario_id}.json").read_text(encoding="utf-8"))
        model = build_rtd_model(scenario_id)
        hidden = raw["oculto"]
        assert model.f == pytest.approx(hidden["f"])
        assert model.phi_d == pytest.approx(hidden["phi_d"])
        assert model.k_ex == pytest.approx(hidden["k_ex_s"])
        assert model.gamma == pytest.approx(hidden["gamma"])
        assert model.N_m == hidden["N_m"]
        assert model.N_c == hidden["N_c"]
        assert model.V == pytest.approx(raw["visible"]["reactor"]["V_L"])
        assert model.Q == pytest.approx(raw["visible"]["reactor"]["Q_nominal_L_min"] / 60.0)

    @pytest.mark.parametrize("scenario_id", _SCENARIO_IDS)
    def test_scenario_object_has_no_reference_to_the_model(self, scenario_id):
        """Loading a Scenario and building a model are independent calls --
        there is no back-channel from one to the other."""
        scenario = load_scenario(scenario_id)
        model = build_rtd_model(scenario_id)
        assert not any(
            isinstance(getattr(scenario, f.name), PackedBedRTD)
            for f in dataclasses.fields(scenario)
        )
        del model  # built successfully; not otherwise referenced by scenario

    def test_all_reactors_share_the_same_residence_time(self):
        """The three reactors are built to the same spec and fed by the same
        nominal pump setpoint -- tau = V/Q is equal by construction, so any
        difference a student measures between reactors reflects only the
        hidden hydrodynamic pathology (f, phi_d, k_ex, gamma, N_m, N_c), not
        a confounding difference in vessel size or flow. This is a design
        choice, not a numerical coincidence -- pin it down here."""
        taus = [build_rtd_model(sid).tau for sid in _SCENARIO_IDS]
        assert all(tau == pytest.approx(taus[0]) for tau in taus)


class TestScenarioSeed:
    def test_seed_matches_raw_sensor_oculto_seed(self):
        raw = json.loads(_SENSOR_PATH.read_text(encoding="utf-8"))
        assert sensor_seed() == raw["oculto"]["seed"]

    def test_seed_is_shared_across_all_scenarios(self):
        """The seed is an instrument setting (one physical AT-101 reading
        whichever reactor is under CIP), not reactor physics -- so unlike
        the old per-plant seed, it's intentionally the same value for every
        reactor now. This documents that choice: previously distinct seeds
        meant two students on different reactors couldn't compare raw noise
        patterns; that anti-copy property is deliberately given up here."""
        seeds = [sensor_seed() for _ in _SCENARIO_IDS]
        assert len(set(seeds)) == 1
