# Changelog

All notable changes to **ChemEng SimLab** (formerly "PFR SCADA Simulator") are
documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project follows
[Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## [Unreleased]

## [2.0.1] — 2026-10-31

### Fixed
- **Table-tab export no longer leaks internal variables.** Export CSV / Export
  Excel wrote every scalar field of `EngineSnapshot`, including the true,
  noise-free `CA_out`, `CB_out` and `X_out` (plus `velocity`, `Q_in`,
  `T_setpoint`), letting a student skip the conductivity calibration. They now
  export only the columns the table shows (`STUDENT_COLUMNS`, same headers and
  units) through the new `models.log_table_model.export_frame`; the Admin tab
  keeps the full export.
- CT-101 texts (sensor dialog, Docs tab) now state that conductivity
  **decreases** with conversion, consistent with the σ = a·C_NaOH + b model,
  and the Docs-tab tips were corrected. "Factory calibration" wording removed:
  the operator builds the calibration.

## [2.0.0] — 2026-07-24

### Changed
- Renamed the project from **PFR SCADA Simulator** to **ChemEng SimLab**
  (Chemical Engineering, corrected from an earlier working name), reflecting
  that it now hosts multiple lab modules (PFR, RTD/CIP) rather than only the
  plug-flow reactor. The build artifact is now `ChemEng_SimLab.exe`; internal
  package names (`scada_app`, `reactor_simulation`) are unchanged.
- Reorganized `reactor_simulation` by physical role (`models/`, `kinetics/`,
  `actuators/`, `control/`, `sensors/`, `simulation/`) instead of mixing
  reactor-type and experiment-named packages; added `docs/shared/CONVENTION.md`
  documenting the module convention for PFR, RTD, and future modules.
- Added `scada_app/engine/base_engine.py::BaseEngine`, the shared tick/
  snapshot/parameter/reset contract; renamed `SimulationEngine` to
  `PFREngine` to match `RTDEngine`'s naming.
- PFR is now data-driven via `scenarios/pfr/pfr_default.json`, matching how
  RTD already loaded its physics from scenario JSON.
- `DataStore.to_dataframe()` is now generic over snapshot type (previously
  hardcoded to PFR's fields, which broke the RTD run export).
- Moved the `reactor_simulation` package reference from
  `docs/modules/pfr/backend.md` to `docs/shared/backend.md` (it documents the
  shared library, not a PFR-specific artifact) and corrected it to match the
  `models/`/`kinetics/` reorg above — it had drifted since, still describing
  the pre-reorg `core/` layout and missing `HXDynamic`, `PackedBedRTD`, and
  `Photocolorimeter`. Renamed `docs/modules/pfr/math.md` to `fundamentals.md`
  so both modules' theory docs share one name. Rewrote `docs/README.md`'s
  index to match.
- Home screen: dropped "Experiencia N" wording in favor of the module names
  ("PFR Simulation" / "RTD Analysis") used consistently in the home cards,
  each workspace's header, and the window title; PFR and RTD cards now sit on
  their own row above About.
- Reconciled version numbers: the app (`APP_VERSION`) and the `reactor_simulation`
  library (`__version__`, `pyproject.toml`) had drifted to 1.0.0 / 0.1.0
  respectively. Library bumped to 1.0.0 to reflect the role-based reorg above.

## [1.0.0] — 2026-06-21

First stable release — a SCADA-style simulator of a tubular plug-flow reactor
(PFR) running the saponification of ethyl acetate by sodium hydroxide, built to
replace a hands-on reaction-kinetics laboratory.

### Added
- **About tab** — project context, author/contact, license, citation, tech
  stack, and this version history.
- **Process model**
  - Dynamic PFR (method of lines, RK45) with bimolecular 2nd-order kinetics.
  - Dynamic heat exchanger with PID-controlled hot-water valve.
  - Reactor **heat loss to ambient** (non-adiabatic, `h_loss = 4U/D`).
- **Sensors with realistic measurement noise**
  - CT-101 conductivity transmitter (tracks residual NaOH).
  - TE-101 / TE-102 temperature transmitters (Gaussian noise).
- **Diagram tab** — interactive P&ID, live readings, status overlay, and an
  unbounded scrolling event log with alarm hysteresis.
- **Graph tab** — 2×2 live plots: temperature (with setpoint line and per-curve
  visibility toggles), valve %, feed flows, and conductivity with inlet
  concentrations on a twin axis.
- **Table tab** — student-facing data table with CSV/Excel export.
- **Admin tab** — password-protected conversion plot plus a full
  internal-variable table with export.
- **Docs tab** — mass balance, kinetics, heat transfer, and sensor theory.

### Notes
- Models are simplified for teaching; results are illustrative, not
  plant-accurate.
