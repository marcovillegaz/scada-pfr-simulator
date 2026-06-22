# Changelog

All notable changes to the **PFR SCADA Simulator** are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and the
project follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

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
