# Roadmap — deferred to v2

Items considered during the backend/test/docs refactor (see CHANGELOG's
Unreleased section and [shared/CONVENTION.md](shared/CONVENTION.md)) but
deliberately not built now, because the current two-module scale (PFR, RTD)
doesn't yet justify the added machinery. Revisit when a third module is
actually being added.

## 1. Full engine protocol + self-registering module registry

Today, adding a module means manually wiring its engine into a workspace,
its workspace into `app.py`'s `QStackedWidget`, and its card into
`HomeScreen`. `BaseEngine` (`scada_app/engine/base_engine.py`) standardizes
the engine *contract*, but nothing auto-discovers modules.

A v2 pass could add:
- A formal `Protocol` (or ABC) that a module registers against, bundling
  engine class + workspace class + display name + icon in one place.
- A module registry (e.g. a `MODULES: dict[str, ModuleSpec]` populated at
  import time, or entry-point-style discovery) that `HomeScreen` and
  `MainWindow` read to build their cards/pages, instead of the current
  hand-written `self._pfr = PFRWorkspace()` / `self._rtd = RTDWorkspace()`
  pattern in `app.py`.
- This is the point at which `PFR_DEFAULT_SCENARIO`/`RTD_DEFAULT_SCENARIO`
  and each module's scenario directory convention (`scenarios/<mod>/`)
  would become registry-driven lookups instead of per-module constants.

Worth doing once there are 3+ modules and the manual wiring starts feeling
repetitive; premature at 2.

## 2. Single-source in-app documentation

`scada_app/ui/tabs/docs_tab.py` (PFR, English) and `rtd_docs_tab.py` (RTD,
Spanish) are hardcoded Python building Qt widgets from shared primitives in
`_docs_helpers.py`. They do **not** read `docs/modules/<mod>/*.md` -- the
in-app docs and the developer/teacher markdown docs are maintained by hand,
separately, and can drift.

A v2 option: define a small markdown-subset renderer (or reuse a Qt-capable
one) and drive both doc tabs from the same `.md` source that
`docs/modules/<mod>/fundamentals.md` uses, so there's one source of truth
for the theory content instead of two. Deferred because:
- The current hand-authored tabs use rich formatting (equation blocks, tip
  callouts, section cards via `_docs_helpers.py`) that a generic renderer
  would need to replicate or approximate.
- RTD's in-app docs deliberately withhold the hidden scenario parameters
  that the full `fundamentals.md`/teacher reference doesn't need to hide --
  a shared source would need an explicit visible/redacted split baked in,
  not just a markdown file.

## 3. Reconsidering PFR scenario variety

PFR now loads from `scenarios/pfr/pfr_default.json` (see CHANGELOG), but
only one scenario ships -- there's no PFR analogue of RTD's `planta_a/b/c`
graduated-difficulty set yet. If a future assignment wants multiple PFR
configurations (different kinetics, different feed conditions), the loader
and `PFREngine.set_scenario()` already support it structurally; only the
additional JSON files and a scenario-picker UI element (mirroring RTD's, if
one exists, or a new one) would need to be added.
