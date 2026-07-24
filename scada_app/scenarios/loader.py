"""
Scenario loader -- shared core for every module's scenario JSON, per
docs/shared/CONVENTION.md §3. Originally RTD-only; now also loads the PFR
module's scenario (see the "PFR module" section below), so PFR's physics is
no longer hardcoded in constants.py -- both modules are equally data-driven,
just with different visible/oculto shapes since only RTD has hidden truth
to protect (there's no pedagogical secret in a saponification PFR).

## RTD module (Experiencia 3)

Loads JSON scenarios with a schema-separated `visible` / `oculto` split, so
hidden hydrodynamic parameters are structurally hard to leak to the
student-facing UI — not just hidden by naming convention.

The separation is enforced by API shape, not by hoping nobody reads a
private attribute:

  - `Scenario` (returned by `load_scenario` / `list_scenarios`) carries only
    `visible`. It has no attribute, anywhere, that reaches the `oculto`
    block — there is no leak to plug because there is no path.
  - `build_rtd_model()` is the *only* function in this module that reads
    `oculto`. It consumes the hidden parameters immediately into a
    `PackedBedRTD` and returns the model — never the raw values.
  - `sensor_seed()` is a narrow, explicit exception: `Photocolorimeter`
    genuinely needs the seed for reproducible-but-secret noise (so a
    student can't discover and replay it to defeat the noise), so it is
    exposed on its own rather than folded into `Scenario`.

Within `visible`, reactor and sensor settings are also split by what they
describe, not just grouped together: `reactor` (V_L, Q_nominal_L_min) lives
in each plant's own JSON under `scenarios/plants/`, while `sensor` (AT-101's
calibration/sampling settings) is loaded once from the single shared
`scenarios/sensor.json` -- there is only one physical photocolorimeter in
the CIP rig, reading whichever reactor is currently isolated, so its
settings aren't a per-reactor property and shouldn't be duplicated three
times.

`sensor.json` itself carries the same `visible`/`oculto` split as a plant
file: the RNG seed for Photocolorimeter's noise is an instrument property,
not reactor physics, so it lives in `sensor.json`'s own `oculto` rather than
each plant's -- one seed, shared by every reactor. That's a deliberate
trade: previously each reactor had its own seed so two students on
different reactors couldn't compare raw noise patterns to defeat it; a
single shared instrument seed gives up that per-reactor differentiation in
exchange for the seed genuinely being an instrument setting, not duplicated
plant data. It stays in `oculto` regardless, because it must never be
readable -- a visible seed would let a student re-seed their own RNG,
predict the exact noise sequence, and subtract it out.

See tests/test_rtd_scenario_integrity.py for the structural checks that back
this up.
"""

from __future__ import annotations

import json
import sys
import os
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from reactor_simulation.models.packed_bed import PackedBedRTD
from resources import resource_path

# resource_path() resolves dev (project root) vs frozen (PyInstaller
# _MEIPASS) locations the same way diagram.svg does -- Path(__file__).parent
# would break in a frozen build, where this module's source lives inside a
# zipped archive, not on disk next to a real "plants" folder.
_DEFAULT_SCENARIOS_DIR = Path(resource_path("scada_app", "scenarios", "plants"))
_DEFAULT_SENSOR_PATH = Path(resource_path("scada_app", "scenarios", "sensor.json"))

# L/min -> L/s: JSON stores the pump's native unit (a real flow transmitter's
# spec sheet and totalizer both read L/min), the model integrates in L/s.
_L_MIN_TO_L_S = 1.0 / 60.0


@dataclass(frozen=True)
class ScenarioReactor:
    """Physical reactor/plant settings the student can see: geometry and
    nominal operating flow. No hydrodynamic truth."""
    V_L: float
    Q_nominal_L_min: float


@dataclass(frozen=True)
class ScenarioSensor:
    """AT-101 photocolorimeter settings the student can see: calibration,
    sampling rate, noise, and saturation. No hydrodynamic truth."""
    epsilon_b: float
    A_max: float
    dt_sample_s: float
    noise_std: float


@dataclass(frozen=True)
class ScenarioVisible:
    """Everything the student's Diagram/Graph/Table tabs are allowed to
    read, grouped by what it describes -- the reactor/plant vs. the AT-101
    sensor measuring it."""
    reactor: ScenarioReactor
    sensor: ScenarioSensor


@dataclass(frozen=True)
class Scenario:
    """Student-facing scenario metadata.

    Deliberately carries no hidden parameters — there is no attribute path
    from a Scenario instance to the ground truth (f, phi_d, k_ex, gamma,
    N_m, N_c). Hidden data lives only in the raw JSON and is read solely by
    build_rtd_model(), which consumes it into a model and returns that.
    """
    id: str
    nombre: str
    visible: ScenarioVisible


def _scenario_path(scenario_id: str, scenarios_dir: str | Path | None = None) -> Path:
    base = Path(scenarios_dir) if scenarios_dir is not None else _DEFAULT_SCENARIOS_DIR
    return base / f"{scenario_id}.json"


def _load_raw(scenario_id: str, scenarios_dir: str | Path | None = None) -> dict:
    path = _scenario_path(scenario_id, scenarios_dir)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _sensor_path(scenarios_dir: str | Path | None = None) -> Path:
    """sensor.json sits next to the plants/ directory, not inside it -- one
    shared file, not one per scenario."""
    if scenarios_dir is None:
        return _DEFAULT_SENSOR_PATH
    return Path(scenarios_dir).parent / "sensor.json"


def _load_raw_sensor(scenarios_dir: str | Path | None = None) -> dict:
    with open(_sensor_path(scenarios_dir), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_sensor(scenarios_dir: str | Path | None = None) -> ScenarioSensor:
    """Load the AT-101 photocolorimeter's visible settings -- global across
    every reactor/plant (see module docstring)."""
    raw = _load_raw_sensor(scenarios_dir)
    return ScenarioSensor(**raw["visible"])


def load_scenario(scenario_id: str, scenarios_dir: str | Path | None = None) -> Scenario:
    """Load a scenario's student-facing metadata (visible only)."""
    raw = _load_raw(scenario_id, scenarios_dir)
    return Scenario(
        id=raw["id"],
        nombre=raw["nombre"],
        visible=ScenarioVisible(
            reactor=ScenarioReactor(**raw["visible"]["reactor"]),
            sensor=load_sensor(scenarios_dir),
        ),
    )


def list_scenarios(scenarios_dir: str | Path | None = None) -> list[Scenario]:
    """List all bundled scenarios (visible metadata only) — safe to hand
    directly to a scenario-picker UI."""
    base = Path(scenarios_dir) if scenarios_dir is not None else _DEFAULT_SCENARIOS_DIR
    return [
        load_scenario(path.stem, scenarios_dir=base)
        for path in sorted(base.glob("*.json"))
    ]


def build_rtd_model(scenario_id: str, scenarios_dir: str | Path | None = None) -> PackedBedRTD:
    """
    Build the hidden-truth PackedBedRTD for a scenario.

    This is the only function in this module allowed to read the `oculto`
    block. The raw hidden values are used to construct the model and then
    go out of scope — they never leave this function as data.
    """
    raw = _load_raw(scenario_id, scenarios_dir)
    hidden = raw["oculto"]
    reactor = ScenarioReactor(**raw["visible"]["reactor"])
    Q_L_s = reactor.Q_nominal_L_min * _L_MIN_TO_L_S
    return PackedBedRTD(
        f=hidden["f"],
        phi_d=hidden["phi_d"],
        k_ex=hidden["k_ex_s"],
        gamma=hidden["gamma"],
        N_m=hidden["N_m"],
        N_c=hidden["N_c"],
        V=reactor.V_L,
        Q=Q_L_s,
    )


def sensor_seed(scenarios_dir: str | Path | None = None) -> int:
    """The RNG seed for Photocolorimeter -- one shared instrument setting,
    read from sensor.json's own `oculto` (so the noise sequence can't be
    discovered and replayed to defeat it), not from any individual plant's
    `oculto`. Exposed narrowly, on its own, rather than folding `oculto`
    into Scenario."""
    raw = _load_raw_sensor(scenarios_dir)
    return int(raw["oculto"]["seed"])


# ═══════════════════════════════════════════════════════════════════════════
# PFR module (Experiencia 2)
# ═══════════════════════════════════════════════════════════════════════════
#
# No hidden truth to protect here -- the saponification kinetics and reactor
# geometry are not a pedagogical secret the way RTD's hydrodynamic pathology
# is, so PFRScenario carries only `visible` and there is no `oculto`/build_*
# split. The physics still lives in one JSON file per scenario (today just
# `pfr_default.json`), read through this same loader, so PFR and RTD are
# symmetric in *how* their data is sourced even though PFR's schema is
# simpler.

_DEFAULT_PFR_SCENARIOS_DIR = Path(resource_path("scada_app", "scenarios", "pfr"))


@dataclass(frozen=True)
class PFRGeometry:
    length_m: float
    diameter_m: float
    n_nodes: int


@dataclass(frozen=True)
class PFRFluid:
    density_kg_m3: float
    heat_capacity_J_kgK: float
    ambient_temp_K: float


@dataclass(frozen=True)
class PFRKinetics:
    reaction_order: float
    k0_m3_mol_s: float
    activation_energy_J_mol: float
    heat_of_reaction_J_mol: float
    h_loss_W_m3K: float


@dataclass(frozen=True)
class PFRFeed:
    Qa0_m3_s: float
    Qb0_m3_s: float
    Ca0_mol_L: float
    Cb0_mol_L: float


@dataclass(frozen=True)
class PFRHeatExchanger:
    volume_m3: float
    hot_water_temp_K: float
    ua_max_W_K: float


@dataclass(frozen=True)
class PFRPID:
    setpoint_K: float
    Kp: float
    Ki: float
    Kd: float


@dataclass(frozen=True)
class PFRSensors:
    ct101_calib_a: float
    ct101_calib_b: float
    ct101_noise_std: float
    te_noise_std: float


@dataclass(frozen=True)
class PFRVisible:
    geometry: PFRGeometry
    fluid: PFRFluid
    kinetics: PFRKinetics
    feed: PFRFeed
    heat_exchanger: PFRHeatExchanger
    pid: PFRPID
    sensors: PFRSensors


@dataclass(frozen=True)
class PFRScenario:
    id: str
    nombre: str
    visible: PFRVisible


def load_pfr_scenario(
    scenario_id: str = "pfr_default",
    scenarios_dir: str | Path | None = None,
) -> PFRScenario:
    """Load a PFR scenario's physics from its JSON file. PFREngine calls
    this directly (mirroring RTDEngine's use of build_rtd_model/
    load_scenario) so its parameters are genuinely scenario-driven, not
    module-level constants."""
    base = Path(scenarios_dir) if scenarios_dir is not None else _DEFAULT_PFR_SCENARIOS_DIR
    raw = _load_raw(scenario_id, base)
    v = raw["visible"]
    return PFRScenario(
        id=raw["id"],
        nombre=raw["nombre"],
        visible=PFRVisible(
            geometry=PFRGeometry(**v["geometry"]),
            fluid=PFRFluid(**v["fluid"]),
            kinetics=PFRKinetics(**v["kinetics"]),
            feed=PFRFeed(**v["feed"]),
            heat_exchanger=PFRHeatExchanger(**v["heat_exchanger"]),
            pid=PFRPID(**v["pid"]),
            sensors=PFRSensors(**v["sensors"]),
        ),
    )


def list_pfr_scenarios(scenarios_dir: str | Path | None = None) -> list[PFRScenario]:
    """List all bundled PFR scenarios. Only one ships today
    (pfr_default), but this mirrors list_scenarios() so adding a second
    PFR scenario later needs no loader changes."""
    base = Path(scenarios_dir) if scenarios_dir is not None else _DEFAULT_PFR_SCENARIOS_DIR
    return [
        load_pfr_scenario(path.stem, scenarios_dir=base)
        for path in sorted(base.glob("*.json"))
    ]
