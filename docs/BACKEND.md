# reactor_simulation — Backend Reference

The `reactor_simulation` package contains all physics, control, and sensor
models. It is completely independent of PyQt and can be used in batch scripts,
Jupyter notebooks, or the SCADA app without modification.

See [MATH.md](MATH.md) for the governing equations and [FRONTEND.md](FRONTEND.md)
for how the SCADA engine uses this package.

---

## Design Philosophy

The package enforces a strict separation of concerns through five conceptual layers:

| Layer | Responsibility |
|---|---|
| **Core** | What the reactor *is* — concentrations, temperatures, kinetics |
| **Actuators** | How humans *change* boundary conditions — with inertia and rate limits |
| **Control** | How the system *responds* — acts on *measurements*, never on true state |
| **Sensors** | What instruments *think* is happening — noise, lag, drift, nonlinearity |
| **Simulation** | Orchestration — time loop, perturbations, data logging |

The key invariant: **controllers and sensors never access ground truth.** This
is what creates educational value — students observe the same discrepancies
between measured and true values that they would in a real plant.

---

## Package Structure

```
reactor_simulation/
├── __init__.py                ← public API re-exports
│
├── core/
│   ├── reactor.py             ← PlugFlow, StirredTank, RecyclePlugFlow (steady-state sizing)
│   ├── kinetics.py            ← Reaction, overall_yield_pfr, overall_yield_mfr
│   ├── state.py               ← ReactorState (generic state container)
│   └── pfr_model.py           ← PFRSimulator (dynamic MOL-PFR, used by SCADA engine)
│
├── actuators/
│   ├── heat_exchanger.py      ← HeatExchanger (utility-temperature driven, first-order lag)
│   ├── heater.py              ← Heater (power command with first-order thermal inertia)
│   └── pump.py                ← Pump (flow rate with ramp-rate limit)
│
├── control/
│   └── pid.py                 ← PIDController (anti-windup, derivative filter)
│
├── sensors/
│   ├── conductivity.py        ← ConductivitySensor (calibration curve, drift, noise)
│   ├── temperature.py         ← TemperatureSensor (Gaussian noise — TE-101/TE-102)
│   └── thermocouple.py        ← Thermocouple (lag + bias + noise + range saturation)
│
└── simulation/
    ├── experiment.py          ← Experiment (batch time loop → DataFrame)
    └── perturbations.py       ← StepPerturbation, RampPerturbation, SinusoidalPerturbation
```

---

## Information Flow

```
┌──────────────────────────────────────────────────────────────┐
│                       EXPERIMENT / ENGINE                    │
│              (Orchestration — drives the time loop)          │
└──────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼────────────────────┐
          ▼                   ▼                    ▼
    ┌──────────┐       ┌────────────┐       ┌──────────┐
    │  REACTOR │       │  ACTUATORS │       │  SENSORS │
    │  (Truth) │       │  (Devices) │◄──────│(Measure) │
    └──────────┘       └────────────┘       └──────────┘
          ▲                   │                    │
          └───────────────────┘                    ▼
                                            ┌──────────┐
                                            │CONTROLLER│
                                            │  (PID)   │
                                            └──────────┘
                                                  │
                                    (commands) ───┘
```

**Data flow each tick:**
1. Sensors measure the **true** reactor state → produce **measured** values
2. Controller reads **measured** values → outputs a command (e.g. valve position)
3. Actuator receives the command → modifies a boundary condition (e.g. HX temperature)
4. Reactor state evolves under the new boundary conditions
5. Repeat

---

## Class Reference

### core/pfr_model.py — `PFRSimulator`

The dynamic PFR used by the SCADA engine. Integrates the full PDE system
(mass + energy balances for species A, B, and temperature) using RK45.
See [MATH.md](MATH.md) for the governing equations.

```python
from reactor_simulation import PFRSimulator

sim = PFRSimulator(params)   # params dict — see MATH.md §Parameters
out = sim.step(dt_sim)       # advance dt_sim simulation seconds
sim.update_params({'T_in': new_T_in, 'CA_in': new_ca})  # change boundary conditions
sim.reset(params)            # restart from uniform initial conditions
```

`step()` returns a dict with keys: `t`, `CA_profile`, `CB_profile`, `T_profile`,
`CA_out`, `CB_out`, `T_out`, `X_out` (all in SI units — mol/m³ and K).

**Where to modify:**
- Rate expression: `pfr_rhs()` in `core/pfr_model.py:55–57`
- Spatial scheme: `_upwind()` in `core/pfr_model.py:29–33`
- Integrator (RK45 ↔ Radau): `step()` in `core/pfr_model.py:82`

---

### core/reactor.py — `PlugFlow`, `StirredTank`, `RecyclePlugFlow`

Steady-state reactor sizing tools. Used in the `examples/` scripts for
residence time and volume calculations; **not** used by the SCADA engine
(which uses `PFRSimulator` instead).

```python
from reactor_simulation import PlugFlow, StirredTank

pfr  = PlugFlow(order_of_reaction=1, kinetic_constant=0.5)
cstr = StirredTank(order_of_reaction=1, kinetic_constant=0.5)

tau_pfr  = pfr.residence_time(output_conversion=0.9, input_concentration=2.0,
                               input_conversion=0.0, epsilon=0.0)
tau_cstr = cstr.residence_time(output_conversion=0.9, input_concentration=2.0,
                                input_conversion=0.0, epsilon=0.0)
V = pfr.get_volume(volumetric_flow=1e-4, output_conversion=0.9,
                   input_concentration=2.0, input_conversion=0.0)
```

`RecyclePlugFlow` adds a recycle ratio `R` (recycle flow / product flow); inlet
conversion is automatically computed as `Xa_i = R/(R+1) · Xa_f`.

**Where to modify:**
- Rate law: the lambda inside `integrate.quad` in each `residence_time()` method
- Add temperature dependence: replace `k` with `k0 * exp(-Ea / (R * T))`

---

### core/kinetics.py — `Reaction`, `overall_yield_pfr`, `overall_yield_mfr`

Wraps a kinetic expression as a callable object. Primarily used in the
steady-state examples.

```python
from reactor_simulation import Reaction
from reactor_simulation.core.kinetics import overall_yield_pfr

rxn = Reaction(
    reaction_type="irreversible",
    stoichiometry={"A": -1, "B": 1},
    expression=lambda Ca: 0.5 * Ca,   # first-order rate
    fractional_change=0,
)
rate = rxn.reaction_rate(Ca=1.5)

phi = lambda Ca: Ca / (Ca + 2.0)      # fractional yield of desired product
y   = overall_yield_pfr(phi, Ca_0=5.0, Ca_f=1.0)
```

---

### core/state.py — `ReactorState`

Generic state container used by the batch simulation API. Holds concentration,
temperature, pressure, and flow as NumPy arrays.

```python
from reactor_simulation import ReactorState

state = ReactorState(n_species=2, n_spatial_points=10)
state.temperature = 320.0
state.set_concentration(1.5, species_idx=0, position_idx=0)
c = state.get_outlet_concentration(species_idx=0)
```

**Where to modify:**
- Add new state variables (pH, viscosity): add attributes in `__init__` and `copy()`

---

### actuators/heat_exchanger.py — `HeatExchanger`

General heating/cooling device driven by a utility temperature command. The
SCADA engine uses its own `HXDynamic` (inline in `simulation_engine.py`) which
uses the exact analytic solution for the HX energy balance; this class uses the
first-order lag approximation and is available for script-mode simulations.

```python
from reactor_simulation.actuators import HeatExchanger

hx = HeatExchanger(UA=500.0, T_utility_min=273.15, T_utility_max=400.0,
                   time_constant=10.0)
hx.set_utility_temperature(350.0)  # K
Q = hx.update(T_process=300.0, dt=0.5)  # W, positive = into process
```

`Q = UA_eff × (T_utility_actual − T_process)`. `T_utility_actual` lags behind
the commanded setpoint with first-order dynamics (τ = `time_constant`).

---

### actuators/heater.py — `Heater`

Converts a power command (W) to delivered heat with first-order thermal inertia.

```python
from reactor_simulation import Heater

heater = Heater(max_power=5000.0, efficiency=0.90, time_constant=8.0)
heater.power_setpoint = 3000.0
heat_out = heater.update(dt=0.5)   # W delivered to the process
```

First-order lag: `α = dt / (τ + dt);  actual_power += α × (setpoint − actual)`.

---

### actuators/pump.py — `Pump`

Flow rate control with a ramp-rate limit — cannot step instantaneously.

```python
from reactor_simulation import Pump

pump = Pump(max_flow=5e-4, min_flow=0.0, max_ramp_rate=5e-5)
pump.flow_setpoint = 2e-4          # m³/s
actual_flow = pump.update(dt=0.5)  # m³/s, ramped toward setpoint
```

---

### control/pid.py — `PIDController`

Classic PID with clamped conditional anti-windup and optional derivative filter.
Always acts on **measured** values, never on true values.

```python
from reactor_simulation import PIDController

pid = PIDController(
    Kp=0.14, Ki=0.04, Kd=0.0,
    setpoint=303.15,     # K (30 °C)
    output_min=0.0,
    output_max=1.0,
    derivative_filter_tau=0.0,
)
valve = pid.update(measured_T, dt)   # float in [output_min, output_max]
pid.set_setpoint(313.15)             # change setpoint at runtime
pid.set_gains(Kp=0.20)              # change one or more gains at runtime
comps = pid.get_components()         # {'P': ..., 'I': ..., 'D': ...}
pid.reset()                          # clear integral and derivative state
```

**Anti-windup:** clamped conditional integration — the integral term only
accumulates when the output is not saturated *and* the error is in the
direction that would drive the output away from saturation.

**Where to modify:**
- Anti-windup strategy: `pid.py` around the saturation check
- Derivative filter: `derivative_filter_tau` — set > 0 to enable

---

### sensors/conductivity.py — `ConductivitySensor`

Estimates concentration via a linear calibration curve with additive noise.

```python
from reactor_simulation import ConductivitySensor

ct101 = ConductivitySensor(
    calib_a=156.0,      # mS/cm per (mol/L)
    calib_b=1.6,        # mS/cm  — background offset
    noise_std=0.05,     # mS/cm
)
conductivity = ct101.measure(ca_out_mol_l)   # mS/cm
ct101.reset()
```

The calibration curve is `σ = A·C + B`. `A` and `B` can be validated against
simulation output by running at known `CA_out` values and checking σ.

---

### sensors/temperature.py — `TemperatureSensor`

Simple Gaussian noise model. Used by the SCADA engine as TE-101 (T_in) and
TE-102 (T_out). The PFR and PID use **true** temperatures; only the reported
readings are noisy.

```python
from reactor_simulation.sensors import TemperatureSensor

te = TemperatureSensor(noise_std=0.3)   # K
t_measured = te.measure(true_temperature)
te.reset()
```

---

### sensors/thermocouple.py — `Thermocouple`

Full thermocouple model with **four imperfections** applied in order:
thermal lag → calibration bias → Gaussian noise → range saturation.

```python
from reactor_simulation import Thermocouple

tc = Thermocouple(noise_std=1.0, time_constant=3.0, bias=2.5,
                  min_temp=250.0, max_temp=600.0, seed=0)
t_measured = tc.measure(true_temperature, dt)
```

**Where to modify:**
- Add dead-time: store a `deque` of past readings, return value from N steps ago
- Non-Gaussian noise: replace `rng.normal()` with `rng.laplace()` or spike model

---

### simulation/experiment.py — `Experiment`

Batch time loop. Calls `update_function(t, dt)` and `log_function(t)` each step,
then returns a Pandas DataFrame. Used by all `examples/` scripts.

```python
from reactor_simulation import Experiment, StepPerturbation

experiment = Experiment(time_step=0.5, total_time=200.0)
experiment.add_perturbation(
    StepPerturbation(target_object=pid, attribute_name='setpoint',
                     initial_value=303.15, final_value=313.15, step_time=50.0)
)
df = experiment.run(update_function, log_function)
df.to_csv('results.csv', index=False)
```

---

### simulation/perturbations.py — `StepPerturbation`, `RampPerturbation`, `SinusoidalPerturbation`

Registered on an `Experiment` and applied automatically each tick via `setattr`.
Can target any object attribute: `pid.setpoint`, `pump.flow_setpoint`, etc.

| Class | Behaviour |
|---|---|
| `StepPerturbation` | One-time jump at `step_time` |
| `RampPerturbation` | Linear ramp from `start_value` to `end_value` over `duration` seconds |
| `SinusoidalPerturbation` | Continuous sinusoid after `start_time` |

---

## How to Extend

**Add a new reactor type:**
Subclass `Reactor` in `core/reactor.py` and implement `residence_time()`.

**Add a new sensor:**
Create a new file in `sensors/`. Implement a `measure()` method. Never return
the true value directly — always add at least one imperfection.

**Add a new reaction:**
Change the rate expression in `pfr_rhs()` (`core/pfr_model.py:55–57`). Update
the state vector size if adding a species (currently 3N: CA, CB, T).

**Add a new controller:**
Create a new file in `control/`. Implement `update(measured_value, dt)`. Output
goes to an actuator, never directly to the reactor.
