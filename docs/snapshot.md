# Project Snapshot — Chemical Engineering Reactor Simulation
**Date:** 2026-06-18

---

## Overview

A modular Python package for simulating chemical reactors with realistic sensor noise, actuator dynamics, and PID control. Purpose: generate synthetic experimental data for educational use when physical equipment is unavailable.

**Version:** 0.1.0-alpha (not published)
**Branch:** main

---

## Current Git State

The project is mid-refactoring. The new package architecture has been fully written but **never committed**. The old flat root-level scripts have been deleted from the working tree but those deletions are also uncommitted.

### Staged / tracked changes (not yet committed)
| Status | File |
|--------|------|
| Modified | `README.md` |
| Modified | `requirements.txt` |
| Deleted  | `compare_reactors.py` |
| Deleted  | `nonideal_reactor.py` |
| Deleted  | `parallel_react2.py` |
| Deleted  | `parallel_reaction1.py` |
| Deleted  | `recycle_test.py` |
| Deleted  | `series_reactions.py` |
| Deleted  | `series_test.py` |

### Untracked (new, not yet added to git)
| File / Dir | Description |
|------------|-------------|
| `reactor_simulation/` | Entire new package (16 Python files) |
| `examples/` | 6 demonstration scripts |
| `tests/` | 3 test scripts |
| `pyproject.toml` | Package build config (setuptools) |
| `ARCHITECTURE.md` | Architecture diagram and design principles |
| `QUICKSTART.md` | Quick-start guide |
| `temperature_control_demo.png` | Generated plot artifact |

### Recent commit history
```
7231ff9  multiple reaction yield
90f3b90  parallel reaction excersice
5a22caa  nonideal reactor example
c7d4e6b  reaction in series examples
77f23ad  deleted
cd394de  compare two tipes of reactor by space times
c2dcd52  fractional yield test
a9c8e1c  RecicledPLugFLow subclass test
bc2f3e4  basis for raction class
b5d7789  deleted for order
```

---

## Package Structure

### New package — `reactor_simulation/` (untracked)

```
reactor_simulation/
├── __init__.py              # v0.1.0 — exports all public classes
├── core/
│   ├── reactor.py           # Reactor, PlugFlow, StirredTank, RecyclePlugFlow
│   ├── kinetics.py          # Reaction class, overall_yield_pfr, overall_yield_mfr
│   └── state.py             # ReactorState (C, T, P, F arrays)
├── actuators/
│   ├── heater.py            # Heater (power limits, first-order thermal inertia)
│   └── pump.py              # Pump (flow rate with ramp limits)
├── control/
│   └── pid.py               # PIDController (anti-windup, derivative filtering)
├── sensors/
│   ├── thermocouple.py      # Thermocouple (noise, lag, bias, range limits)
│   └── conductivity.py      # ConductivitySensor (drift, nonlinearity)
└── simulation/
    ├── experiment.py        # Experiment (time loop, perturbation dispatch, DataFrame log)
    └── perturbations.py     # StepPerturbation, RampPerturbation, SinusoidalPerturbation
```

### Legacy module — `reaction_kinetics/` (tracked, committed)

```
reaction_kinetics/
├── __init__.py
├── reaction.py              # Reaction class (older version)
├── reactor.py               # PlugFlow, StirredTank, RecyclePlugFlow (older version)
└── overall_yields.py        # Yield calculation utilities
```

This module is superseded by `reactor_simulation/` but still present. Tests in `tests/` still import from it.

---

## Key Classes

### Core
| Class | File | Purpose |
|-------|------|---------|
| `PlugFlow` | `core/reactor.py:40` | PFR — residence time via numerical quadrature (scipy.integrate.quad) |
| `StirredTank` | `core/reactor.py:78` | CSTR — algebraic residence time expression |
| `RecyclePlugFlow` | `core/reactor.py:112` | PFR with recycle stream, computes inlet conversion Xa_i = R/(R+1) * Xa_f |
| `ReactorState` | `core/state.py:11` | Holds C(species×space), T, P, F as numpy arrays |
| `Reaction` | `core/kinetics.py:13` | Wraps a kinetic expression lambda, has `reaction_rate()` and `plot_*()` |

### Actuators
| Class | File | Purpose |
|-------|------|---------|
| `Heater` | `actuators/heater.py:10` | Power → heat with first-order lag (τ=10 s default), efficiency 95% |
| `Pump` | `actuators/pump.py` | Flow rate control with ramp limits |

### Control
| Class | File | Purpose |
|-------|------|---------|
| `PIDController` | `control/pid.py:10` | Classic PID with anti-windup back-calculation and optional derivative filter |

### Sensors
| Class | File | Purpose |
|-------|------|---------|
| `Thermocouple` | `sensors/thermocouple.py:10` | Gaussian noise + first-order lag + bias + range saturation |
| `ConductivitySensor` | `sensors/conductivity.py` | Drift + nonlinearity (concentration proxy) |

### Simulation
| Class | File | Purpose |
|-------|------|---------|
| `Experiment` | `simulation/experiment.py:13` | Drives time loop; calls `update_function(t, dt)` and `log_function(t)` each step; returns DataFrame |

---

## Examples

| Script | What it demonstrates |
|--------|---------------------|
| `examples/temperature_control_demo.py` | Full closed-loop: CSTR + PID + Heater + Thermocouple + StepPerturbation |
| `examples/compare_reactors.py` | PFR vs CSTR volume comparison at same conversion |
| `examples/parallel_reaction1.py` | Parallel reaction selectivity |
| `examples/parallel_react2.py` | Parallel reaction yield optimization |
| `examples/series_reactions.py` | Series reaction kinetics and yield |
| `examples/nonideal_reactor.py` | Non-ideal reactor with RTD |

---

## Tests

| File | Imports from | Notes |
|------|-------------|-------|
| `tests/recycle_test.py` | `reaction_kinetics` (legacy) | Validates RecyclePlugFlow residence time and average rate |
| `tests/series_test.py` | `reaction_kinetics` (legacy) | Series reaction validation |
| `tests/pid_tets.py` | unknown | Filename has a typo (`tets` instead of `tests`) |

**Tests have not been run against the new `reactor_simulation` package.** They still point to the legacy module.

---

## Dependencies

```
numpy >= 1.20.0
scipy >= 1.7.0
matplotlib >= 3.4.0
pandas >= 1.3.0
```

Dev extras (pyproject.toml): `pytest`, `pytest-cov`, `black`, `flake8`, `ipython`

---

## Open Issues

| # | Issue | Priority |
|---|-------|----------|
| 1 | All new files are untracked — no commit captures the refactoring | High |
| 2 | Legacy `reaction_kinetics/` module coexists with new `reactor_simulation/` — unclear which is canonical | High |
| 3 | Tests still import from `reaction_kinetics/` — not updated for new package | Medium |
| 4 | `tests/pid_tets.py` has a typo in the filename | Low |
| 5 | `temperature_control_demo.png` is a generated file — not in `.gitignore` | Low |
| 6 | `pyproject.toml` references placeholder GitHub URLs (`yourusername`) | Low |

---

## Planned Extensions (from ARCHITECTURE.md)

1. Dynamic PFR with spatial discretization
2. Multi-component reactions
3. Heat transfer (jacket cooling, coils)
4. Pressure dynamics
5. Advanced control (MPC, feedforward)
6. Real-time visualization GUI
7. Parameter estimation tools
8. Fault injection (sensor failures)
9. Batch reactor operations
