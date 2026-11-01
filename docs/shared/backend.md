# reactor_simulation — Backend Reference

The `reactor_simulation` package contains all physics, control, and sensor
models. It is completely independent of PyQt and can be used in batch scripts,
Jupyter notebooks, or the SCADA app without modification. It is organized by
physical **role**, not by teaching experience — see
[CONVENTION.md](CONVENTION.md) §1 for the two-axis principle (this package vs.
`scada_app/`, which is organized by module/experience).

See [modules/pfr/fundamentals.md](../modules/pfr/fundamentals.md) for the PFR
governing equations, [modules/rtd/fundamentals.md](../modules/rtd/fundamentals.md)
for the RTD theory, and [frontend.md](frontend.md) for how the SCADA engines
use this package.

---

## Design Philosophy

The package enforces a strict separation of concerns through five conceptual layers:

| Layer | Responsibility |
|---|---|
| **Models** | What the reactor/process *is* — concentrations, temperatures, kinetics |
| **Actuators** | How humans *change* boundary conditions — with inertia and rate limits |
| **Control** | How the system *responds* — acts on *measurements*, never on true state |
| **Sensors** | What instruments *think* is happening — noise, lag, drift, nonlinearity, saturation |
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
├── models/                    ← every reactor/process model, one file per model
│   ├── analytic.py            ← Reactor, PlugFlow, StirredTank, RecyclePlugFlow (steady-state sizing)
│   ├── state.py                ← ReactorState (generic state container)
│   ├── pfr.py                  ← PFRSimulator (dynamic MOL-PFR, drives the PFR module)
│   └── packed_bed.py           ← PackedBedRTD, pulse_concentration (compartment-network
│                                  RTD hidden ground truth, drives the RTD module)
│
├── kinetics/
│   ├── __init__.py             ← Reaction, overall_yield_pfr, overall_yield_mfr
│   └── plotting.py             ← plot_concentration_vs_reaction_rate (script-mode only,
│                                  kept out of __init__ so matplotlib isn't a hard import)
│
├── actuators/
│   ├── heat_exchanger.py       ← HeatExchanger (utility-temperature driven, first-order lag)
│   ├── hx_dynamic.py           ← HXDynamic (valve-driven, exact analytic energy balance;
│                                  drives the live SCADA PFR engine)
│   ├── heater.py               ← Heater (power command with first-order thermal inertia)
│   └── pump.py                 ← Pump (flow rate with ramp-rate limit)
│
├── control/
│   └── pid.py                  ← PIDController (anti-windup, derivative filter)
│
├── sensors/
│   ├── conductivity.py         ← ConductivitySensor (linear calibration curve, noise)
│   ├── temperature.py          ← TemperatureSensor (Gaussian noise — TE-101/TE-102)
│   ├── thermocouple.py         ← Thermocouple (lag + bias + noise + range saturation)
│   └── photocolorimeter.py     ← Photocolorimeter (fixed-sample-period absorbance
│                                  analyzer — AIT for the RTD tracer experiment)
│
└── simulation/
    ├── experiment.py           ← Experiment (batch time loop → DataFrame)
    └── perturbations.py        ← StepPerturbation, RampPerturbation, SinusoidalPerturbation
```

`analysis/` is a reserved, not-yet-existing package for RTD moments/E(t)
fitting or other post-run analysis — see `CONVENTION.md`'s note on why it's
not created empty.

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
    │  MODEL   │       │  ACTUATORS │       │  SENSORS │
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
1. Sensors measure the **true** model state → produce **measured** values
2. Controller reads **measured** values → outputs a command (e.g. valve position)
3. Actuator receives the command → modifies a boundary condition (e.g. HX temperature)
4. Model state evolves under the new boundary conditions
5. Repeat

---

## Class Reference

### models/pfr.py — `PFRSimulator`

The dynamic PFR used by the SCADA `PFREngine`. Integrates the full PDE system
(mass + energy balances for species A, B, and temperature) using RK45.
See [modules/pfr/fundamentals.md](../modules/pfr/fundamentals.md) for the governing equations.

```python
from reactor_simulation import PFRSimulator

sim = PFRSimulator(params)   # params dict — see fundamentals.md §Parameters
out = sim.step(dt_sim)       # advance dt_sim simulation seconds
sim.update_params({'T_in': new_T_in, 'CA_in': new_ca})  # change boundary conditions
sim.reset(params)            # restart from uniform initial conditions
```

`step()` returns a dict with keys: `t`, `CA_profile`, `CB_profile`, `T_profile`,
`CA_out`, `CB_out`, `T_out`, `X_out` (all in SI units — mol/m³ and K).

**Where to modify:**
- Rate expression: `pfr_rhs()` in `models/pfr.py`
- Spatial scheme: `_upwind()` in `models/pfr.py`
- Integrator (RK45 ↔ Radau): `step()` in `models/pfr.py`

---

### models/packed_bed.py — `PackedBedRTD`, `pulse_concentration`

The dynamic RTD model used by the SCADA `RTDEngine` — the hidden ground truth
behind the tracer experiment: a compartment network (main-path cascade +
bypass channel + dead zone) solved as a small linear ODE system, deliberately
*not* built on the PFR's Method-of-Lines/upwind engine (upwind numerical
diffusion would be the same order of magnitude as the physical dispersion
this module exists to measure). See
[modules/rtd/fundamentals.md](../modules/rtd/fundamentals.md) §5 for the full derivation.

```python
from reactor_simulation import PackedBedRTD, pulse_concentration

bed = PackedBedRTD(f=0.05, phi_d=0.10, k_ex=0.02, gamma=0.2,
                    N_m=12, N_c=2, V=1e-3, Q=1.67e-6)
c_out = bed.step(dt, c_in)          # integrate one segment, c_in held constant
c_out = bed.outlet_concentration()  # current C_out (eq. 28) — internal/test use only
bed.set_flow(new_Q)                 # change Q, preserving internal state
bed.reset()                         # zero-concentration bed at t=0

c_p = pulse_concentration(m=dose, Q=flow, t_pulse=width)  # rectangular-pulse C_p (eq. 29)
```

Only `Photocolorimeter`-filtered absorbance is meant to reach the student UI;
`outlet_concentration()` exists for internal use and test verification only.

**Where to modify:**
- Compartment RHS: `_rtd_rhs()` in `models/packed_bed.py` (eqs. 25–27)
- Volume/flow split (`phi_c = gamma * f`, etc.): `PackedBedRTD._rebuild()`

---

### models/analytic.py — `Reactor`, `PlugFlow`, `StirredTank`, `RecyclePlugFlow`

Steady-state reactor sizing tools. Used in the `examples/` scripts for
residence time and volume calculations; **not** used by either live SCADA
engine (which use `PFRSimulator` / `PackedBedRTD` instead).

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

### kinetics — `Reaction`, `overall_yield_pfr`, `overall_yield_mfr`

Wraps a kinetic expression as a callable object. Primarily used in the
steady-state examples. `plotting.py::plot_concentration_vs_reaction_rate` is a
separate, non-eagerly-imported module for a quick scatter plot in script mode
— kept out of `kinetics/__init__.py` so importing the package doesn't pull in
matplotlib as a hard dependency of the physics layer.

```python
from reactor_simulation import Reaction
from reactor_simulation.kinetics import overall_yield_pfr

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

### models/state.py — `ReactorState`

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

General heating/cooling device driven by a utility temperature command. Uses
a first-order lag approximation and is available for script-mode
simulations. The live SCADA PFR engine instead uses `HXDynamic`
(`actuators/hx_dynamic.py`), which takes a valve-position control interface
(matching the P&ID) and solves the HX energy balance exactly per tick — the
two coexist the same way the analytic reactor models coexist with
`PFRSimulator` (see `hx_dynamic.py`'s module docstring).

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

### actuators/hx_dynamic.py — `HXDynamic`

Single-node energy balance on the HX process-side fluid, driven by a valve
position (0–1) rather than a utility-temperature setpoint. Solved with an
exact analytic solution each tick — no ODE solver needed. Drives the live
`PFREngine` (`scada_app/engine/pfr_engine.py`), matching the P&ID's
valve-position control.

```python
from reactor_simulation import HXDynamic

hx = HXDynamic(V=0.002, rho=1000.0, cp=4180.0, T_hw=333.15,
               UA_max=100.0, T_initial=288.0)
T_hx = hx.step(dt=0.5, valve=0.6, Q_total=3.33e-6, T_feed=288.0)  # K
hx.reset()  # back to T_initial
```

`dT/dt = (a − b·T) / (V·ρ·cp)`, `a = Q·ρ·cp·T_feed + UA·T_hw`,
`b = Q·ρ·cp + UA`, `T_ss = a/b` — solved exactly as
`T(dt) = T_ss + (T0 − T_ss)·exp(−b·dt / (V·ρ·cp))`.

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
Always acts on **measured** values, never on true values. Shared by both
modules (PFR's HX loop; RTD has no controller today).

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
    a=156.0,            # mS/cm per (mol/L)
    b=1.6,              # mS/cm  — background offset
    noise_std=0.05,     # mS/cm
)
conductivity = ct101.measure(ca_out_mol_l)   # mS/cm
ct101.reset()   # no persistent state today — kept for API consistency
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

### sensors/photocolorimeter.py — `Photocolorimeter`

In-line absorbance analyzer (AIT) for the RTD tracer experiment — the
truth/data boundary for `RTDEngine`: it holds the exact, continuous outlet
concentration; the student only ever sees what crosses this class. Four
imperfections applied in order on every accepted sample: fixed-period
sampling → Lambert–Beer conversion (`A = ε·b·C`) → Gaussian noise →
linear-range saturation. See
[modules/rtd/fundamentals.md](../modules/rtd/fundamentals.md) §2.4.

```python
from reactor_simulation.sensors import Photocolorimeter

ait = Photocolorimeter(epsilon_b=1.2, dt_sample=1.0, noise_std=0.01,
                       A_max=2.0, seed=0)
A = ait.sample(true_concentration, dt)   # absorbance, held between samples
ait.reset()
```

Never returns concentration — there is no method to recover `C` from a reading.

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
Add a new file in `models/` (see `pfr.py` / `packed_bed.py` for the "owns its
own integrator" pattern), or subclass `Reactor` in `models/analytic.py` for a
steady-state sizing tool.

**Add a new sensor:**
Create a new file in `sensors/`. Implement a `measure()` or `sample()` method.
Never return the true value directly — always add at least one imperfection.

**Add a new reaction:**
Change the rate expression in `pfr_rhs()` (`models/pfr.py`). Update the state
vector size if adding a species (currently 3N: CA, CB, T).

**Add a new controller:**
Create a new file in `control/`. Implement `update(measured_value, dt)`. Output
goes to an actuator, never directly to the reactor.
