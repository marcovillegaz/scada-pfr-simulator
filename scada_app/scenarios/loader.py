"""
Scenario loader for the RTD module (Experiencia 3).

Loads JSON scenarios with a schema-separated `visible` / `oculto` split
(docs/PLAN.md §5.3), so hidden hydrodynamic parameters are structurally hard
to leak to the student-facing UI — not just hidden by naming convention.

The separation is enforced by API shape, not by hoping nobody reads a
private attribute:

  - `Scenario` (returned by `load_scenario` / `list_scenarios`) carries only
    `visible` and `costos`. It has no attribute, anywhere, that reaches the
    `oculto` block — there is no leak to plug because there is no path.
  - `build_rtd_model()` is the *only* function in this module that reads
    `oculto`. It consumes the hidden parameters immediately into a
    `PackedBedRTD` and returns the model — never the raw values.
  - `scenario_seed()` is a narrow, explicit exception: `Photocolorimeter`
    genuinely needs the seed for reproducible-but-secret noise (so a
    student can't discover and replay it to defeat the noise), so it is
    exposed on its own rather than folded into `Scenario`.

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

from reactor_simulation.rtd import PackedBedRTD
from resources import resource_path

# resource_path() resolves dev (project root) vs frozen (PyInstaller
# _MEIPASS) locations the same way diagram.svg does -- Path(__file__).parent
# would break in a frozen build, where this module's source lives inside a
# zipped archive, not on disk next to a real "plants" folder.
_DEFAULT_SCENARIOS_DIR = Path(resource_path("scada_app", "scenarios", "plants"))

# mL/s -> L/s, since scenario volumes are declared in liters (V_L)
_ML_S_TO_L_S = 1.0 / 1000.0


@dataclass(frozen=True)
class ScenarioVisible:
    """Everything the student's Diagram/Graph/Table tabs are allowed to
    read: geometry, calibration, sampling rate. No hydrodynamic truth."""
    V_L: float
    Q_nominal_mL_s: float
    epsilon_b: float
    A_max: float
    dt_sample_s: float
    noise_std: float


@dataclass(frozen=True)
class ScenarioCosts:
    pulso: float
    escalon: float
    hora_planta: float
    presupuesto: float


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
    costos: ScenarioCosts


def _scenario_path(scenario_id: str, scenarios_dir: str | Path | None = None) -> Path:
    base = Path(scenarios_dir) if scenarios_dir is not None else _DEFAULT_SCENARIOS_DIR
    return base / f"{scenario_id}.json"


def _load_raw(scenario_id: str, scenarios_dir: str | Path | None = None) -> dict:
    path = _scenario_path(scenario_id, scenarios_dir)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_scenario(scenario_id: str, scenarios_dir: str | Path | None = None) -> Scenario:
    """Load a scenario's student-facing metadata (visible + costos only)."""
    raw = _load_raw(scenario_id, scenarios_dir)
    return Scenario(
        id=raw["id"],
        nombre=raw["nombre"],
        visible=ScenarioVisible(**raw["visible"]),
        costos=ScenarioCosts(**raw["costos"]),
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
    visible = ScenarioVisible(**raw["visible"])
    Q_L_s = visible.Q_nominal_mL_s * _ML_S_TO_L_S
    return PackedBedRTD(
        f=hidden["f"],
        phi_d=hidden["phi_d"],
        k_ex=hidden["k_ex_s"],
        gamma=hidden["gamma"],
        N_m=hidden["N_m"],
        N_c=hidden["N_c"],
        V=visible.V_L,
        Q=Q_L_s,
    )


def scenario_seed(scenario_id: str, scenarios_dir: str | Path | None = None) -> int:
    """The RNG seed for Photocolorimeter. Lives in `oculto` (so the noise
    sequence can't be discovered and replayed to defeat it), but the sensor
    genuinely needs it for reproducible grading — exposed narrowly, on its
    own, rather than folding all of `oculto` into Scenario."""
    raw = _load_raw(scenario_id, scenarios_dir)
    return int(raw["oculto"]["seed"])
