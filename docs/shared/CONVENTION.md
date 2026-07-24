# Module Convention

This document is the contract every teaching module (PFR, RTD, and whatever
comes next — CSTR, a bioreactor, etc.) follows. It exists so adding a new
module is a checklist, not a design decision each time.

It codifies two things: where code lives (the two-axis principle below), and
the shape every module's engine takes (`BaseEngine`).

---

## 1. The two-axis principle

The codebase has two top-level packages with **deliberately different**
organizing axes. Confusing them is the single biggest source of the
inconsistency this convention fixes.

### `reactor_simulation/` — organized by physical ROLE

This is the domain/physics library. It has no knowledge of "PFR" or "RTD" as
*experiences* — only of reactor types, sensors, actuators, and control
algorithms as physical concepts. It is consumed by two callers: the SCADA app
and the standalone `examples/` scripts (see `docs/QUICKSTART.md`).

```
reactor_simulation/
  models/       # every reactor/process model — each owns its own integrator
    pfr.py          PFRSimulator      (dynamic Method-of-Lines PFR)
    packed_bed.py    PackedBedRTD      (compartment-network packed bed)
    analytic.py      PlugFlow, StirredTank, RecyclePlugFlow, Reactor
    state.py         ReactorState
    # future: cstr.py, bioreactor.py, ...
  kinetics/     # reaction rate laws (Reaction, overall_yield_pfr/mfr)
  sensors/      # ConductivitySensor, TemperatureSensor, Thermocouple, Photocolorimeter
  actuators/    # Pump, HXDynamic (dynamic heat exchanger), Heater
  control/      # PIDController
  simulation/   # Experiment, Perturbation — orchestration for script-mode use
  analysis/     # RESERVED — RTD moments/E(t) fitting, or other post-run
                # analysis, once such code exists in Python. Today this
                # analysis is deliberately the student's job (export → Excel);
                # do not create this package empty.
```

Rule: **reactor-type names only** in this package — `pfr`, `packed_bed`,
`cstr`. Never an experience/course name (`rtd`, `exp3`). A new physical model
is a new file in `models/`; it does not imply a new subpackage.

### `scada_app/` — organized by EXPERIENCE/module

This is the PyQt6 frontend. Its organizing unit is the teaching
experience/module — "PFR" (Experiencia 2), "RTD" (Experiencia 3), and future
ones. Each module *composes* library pieces; it does not implement physics.

```
scada_app/
  engine/<mod>_engine.py     # <Mod>Engine(BaseEngine) — orchestration only
  scenarios/<mod>/*.json     # this module's data (see §3)
  workspaces/<mod>_workspace.py
  ui/tabs/, ui/widgets/, ui/dialogs/   # <mod>-prefixed where module-specific
  images/<mod>/              # this module's diagram/P&ID assets
  docs/modules/<mod>/        # this module's docs (see docs/shared for the
                              # docs-tree convention)
```

This is the axis that answers "where does the next module go?": a new
reactor type gets a `models/<type>.py` in the library, and a new *module*
(engine + scenarios + workspace + docs) in the app.

---

## 2. Engine contract — `BaseEngine`

Every module's engine subclasses `scada_app/engine/base_engine.py::BaseEngine`
(a `QObject`). The shared contract:

```python
class BaseEngine(QObject):
    def __init__(self, scenario_id: str, parent=None): ...
    def tick(self, sim_dt: float) -> None: ...
    def get_snapshot(self) -> Snapshot | None: ...
    def apply_parameters(self, params: dict) -> None: ...
    def reset(self) -> None: ...
    data_store: DataStore
```

Rules:
- **Construction is data-driven**: `<Mod>Engine(scenario_id)`. No engine reads
  bare physics constants from `constants.py` — see §3. A module with no hidden
  truth (e.g. PFR) still loads its scenario JSON; its `oculto` block is simply
  empty/absent.
- `constants.py` only holds genuinely app-global values: identity (app name,
  version), timers, UI scene geometry, plot buffer size — never physics.
- Subclasses implement `_init_objects()` to compose `reactor_simulation`
  objects and produce their own `Snapshot` dataclass in `tick()`.
- No embedded domain classes in engine files. If an engine needs a physical
  component not yet in `reactor_simulation`, that component belongs in
  `reactor_simulation/actuators|sensors|models/`, imported by the engine —
  never defined inline (see the `HXDynamic` fix in this same refactor pass).

## 3. Scenario data

Physics parameters for a module live in `scada_app/scenarios/<mod>/*.json`,
loaded through the shared loader core in `scada_app/scenarios/loader.py`. The
`visible` / `oculto` schema split (student-safe vs. hidden ground truth) is
mandatory for any module with pedagogically hidden parameters; modules with no
hidden truth simply have an empty `oculto`. See `scenarios/loader.py`'s own
docstring for why the split is enforced structurally, not by convention.

## 4. Package hygiene

- Every package (`reactor_simulation`, its subpackages, `scada_app.engine`,
  `scada_app.scenarios`) curates its public API in `__init__.py` via
  `__all__`. No deep-path imports into a module's internals from outside it.
- No `sys.path.insert` hacks. Both packages are installed
  (`pyproject.toml`); import them as packages.
- `DataStore` is generic over snapshot type — it must not assume any one
  module's field names (see the `to_dataframe()` fix in this refactor pass).

## 5. Assets and docs

- Runtime images: `images/<mod>/` (bundled by the PyInstaller spec). Design
  references that are not loaded by code (mockups, mask overlays used only for
  authoring) live under `images/_design/` instead, so packaging always bundles
  exactly the runtime set.
- Docs: `docs/modules/<mod>/{fundamentals,math,backend,frontend}.md`. Shared,
  module-agnostic material (this file, architecture overviews, build
  instructions) lives in `docs/shared/`.

## 6. Adding a new module — checklist

1. `reactor_simulation/models/<type>.py` — the physics, if new.
2. `scada_app/scenarios/<mod>/*.json` (+ loader support if the schema needs a
   new shape).
3. `scada_app/engine/<mod>_engine.py` — `<Mod>Engine(BaseEngine)`.
4. `scada_app/engine/data_store.py` — a `<Mod>Snapshot` frozen dataclass.
5. `scada_app/workspaces/<mod>_workspace.py` + tabs/widgets/dialogs as needed.
6. `images/<mod>/` for its diagram assets.
7. `docs/modules/<mod>/` — fundamentals, math, backend, frontend notes.

Deferred (see `docs/ROADMAP_V2.md`): a formal engine protocol + registry so
the home screen auto-discovers modules instead of each being wired in by
hand.
