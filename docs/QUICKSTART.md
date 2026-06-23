# Script (Batch) API — Quick Start

This guide covers the **script-mode API** (`reactor_simulation` package) used
by everything under `examples/`. To run the SCADA desktop app see
[README.md](../README.md). For full class documentation see [BACKEND.md](BACKEND.md).

---

## Installation

```bash
pip install -e .   # development mode — changes take effect immediately
```

## Running the SCADA App

```bash
python -m scada_app.main
```

---

## How the Batch Time Loop Works

`Experiment.run()` owns a blocking `for` loop. It ticks forward by a fixed
`time_step` until `total_time` is reached:

```
Experiment.run(update_function, log_function)
    └── for step in range(num_steps):
            1. perturbation.apply(t)       ← scheduled disturbances
            2. update_function(t, dt)      ← all physics live here
            3. data = log_function(t)      ← record variables
            4. current_time += dt
    └── return DataFrame
```

There is **no fixed location** for the ODEs. The caller writes an
`update_function(t, dt)` callback and puts all physics inside it. Each example
script defines its own equations. Reference:
`examples/temperature_control_demo.py`.

Typical structure:

```python
def update(t, dt):
    # 1. Sense
    measured_T = thermocouple.measure(state.temperature, dt)

    # 2. Control
    T_utility_cmd = pid.update(measured_T, dt)
    hx.set_utility_temperature(T_utility_cmd)

    # 3. Actuate
    Q = hx.update(state.temperature, dt)   # W
    F = pump.update(dt)                    # m³/s

    # 4. Mass balance  →  dCa/dt = (F/V)·(Ca_feed − Ca)
    Ca = state.get_concentration()
    dCa_dt = (F / V) * (Ca_feed - Ca)
    state.set_concentration(Ca + dCa_dt * dt)

    # 5. Energy balance  →  dT/dt = Q/(m·Cp) − UA·(T − T_amb)/(m·Cp)
    dT_dt = Q / (mass * Cp) - UA * (state.temperature - T_amb) / (mass * Cp)
    state.temperature += dT_dt * dt
```

To modify an equation, edit the corresponding line inside `update_function` in
the script you are running. No package file needs to change.

---

## Basic Import Pattern

```python
# Import individual submodules
from reactor_simulation.core import ReactorState, PlugFlow, StirredTank
from reactor_simulation.actuators import Heater, Pump
from reactor_simulation.control import PIDController
from reactor_simulation.sensors import Thermocouple, ConductivitySensor
from reactor_simulation.simulation import Experiment

# OR import everything at once from the top-level package
from reactor_simulation import (
    ReactorState, PlugFlow, StirredTank,
    Heater, Pump,
    PIDController,
    Thermocouple, ConductivitySensor,
    Experiment, StepPerturbation,
)
```

---

## Common Workflows

### 1. Steady-State Reactor Sizing

```python
from reactor_simulation.core import PlugFlow, StirredTank

pfr  = PlugFlow(order_of_reaction=1, kinetic_constant=0.1)
cstr = StirredTank(order_of_reaction=1, kinetic_constant=0.1)

tau_pfr  = pfr.residence_time(output_conversion=0.9, input_concentration=50,
                               input_conversion=0.0, epsilon=0.0)
tau_cstr = cstr.residence_time(output_conversion=0.9, input_concentration=50,
                                input_conversion=0.0, epsilon=0.0)
V = pfr.get_volume(volumetric_flow=1e-4, output_conversion=0.9,
                   input_concentration=50, input_conversion=0.0)
```

### 2. Dynamic Temperature Control (full closed loop)

```python
from reactor_simulation import (
    ReactorState, Heater, PIDController, Thermocouple, Experiment
)

state  = ReactorState()
state.temperature = 300.0        # K

heater = Heater(max_power=1000, efficiency=0.95)
sensor = Thermocouple(noise_std=0.5, bias=1.0)
pid    = PIDController(Kp=50, Ki=5, Kd=10, setpoint=350,
                       output_min=0.0, output_max=1000.0)

def update(t, dt):
    measured_T = sensor.measure(state.temperature, dt)
    power = pid.update(measured_T, dt)
    heater.power_setpoint = power
    heat = heater.update(dt)
    state.temperature += (heat / (10 * 4180)) * dt   # 10 kg water

def log(t):
    return {
        'T_true':     state.temperature,
        'T_measured': sensor.get_reading(),
        'power':      heater.actual_power,
    }

experiment = Experiment(time_step=0.5, total_time=200.0)
df = experiment.run(update, log)
df.to_csv('results.csv', index=False)
```

### 3. Adding Perturbations

Perturbation objects are registered on the `Experiment` before `run()`.
On each tick the loop calls `perturbation.apply(t)`, which uses `setattr` to
mutate a target object's attribute at a scheduled time.

```python
from reactor_simulation import StepPerturbation, RampPerturbation

# Step change: setpoint 350 K → 370 K at t = 50 s
experiment.add_perturbation(
    StepPerturbation(
        target_object=pid,
        attribute_name='setpoint',
        initial_value=350,
        final_value=370,
        step_time=50,
    )
)

# Ramp flow from 1e-3 to 2e-3 m³/s over 20 s starting at t = 30 s
experiment.add_perturbation(
    RampPerturbation(
        target_object=pump,
        attribute_name='flow_setpoint',
        start_value=1e-3,
        end_value=2e-3,
        start_time=30,
        duration=20,
    )
)
```

| Class | File | Behaviour |
|---|---|---|
| `StepPerturbation` | `simulation/perturbations.py` | One-time jump at `step_time` |
| `RampPerturbation` | `simulation/perturbations.py` | Linear ramp over `duration` seconds |
| `SinusoidalPerturbation` | `simulation/perturbations.py` | Continuous sinusoid after `start_time` |

Perturbations can target any object attribute: `pid.setpoint`,
`pump.flow_setpoint`, `hx.T_utility_max`, etc.

### 4. Working with Sensors

```python
from reactor_simulation import Thermocouple, ConductivitySensor

# Thermocouple: lag + bias + noise + range saturation
tc = Thermocouple(noise_std=0.5, time_constant=2.0, bias=1.0, seed=42)
t_meas = tc.measure(true_temperature=350.0, dt=0.1)

# Conductivity sensor: calibration curve + noise
cond = ConductivitySensor(calib_a=156.0, calib_b=1.6, noise_std=0.05)
conductivity = cond.measure(ca_out_mol_l=0.04)
```

---

## Plotting Results

```python
import matplotlib.pyplot as plt

df = experiment.run(update, log)

fig, axes = plt.subplots(2, 1, figsize=(10, 8))
axes[0].plot(df['time'], df['T_true'],     label='True')
axes[0].plot(df['time'], df['T_measured'], label='Measured', alpha=0.7)
axes[0].set_ylabel('Temperature (K)')
axes[0].legend(); axes[0].grid(True)

axes[1].plot(df['time'], df['power'])
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Heater Power (W)')
axes[1].grid(True)

plt.tight_layout()
plt.show()
```

---

## Example Scripts

| Script | What it demonstrates |
|---|---|
| `examples/temperature_control_demo.py` | Full closed loop: HX + PID + Thermocouple + StepPerturbation |
| `examples/compare_reactors.py` | PFR vs CSTR volume at the same conversion (steady-state) |
| `examples/parallel_reaction1.py` | Parallel reaction selectivity |
| `examples/parallel_react2.py` | Parallel reaction yield optimisation |
| `examples/series_reactions.py` | Series reaction kinetics and yield |
| `examples/nonideal_reactor.py` | Non-ideal reactor with RTD |

```bash
# Run from the project root
python examples/temperature_control_demo.py
python examples/compare_reactors.py
```

---

## Common Patterns

**Pattern 1 — Closed-Loop Control:**
```
Reactor (truth) → Sensor (measures) → Controller (acts) → Actuator (modifies) → Reactor
```

**Pattern 2 — Open-Loop Testing:**
```
Perturbation → Actuator → Reactor → Sensor → Log data
```

**Pattern 3 — System Identification:**
```
Apply step/ramp → Measure response → Fit model → Tune controller
```

---

## Troubleshooting

**Import errors** — run `pip install -e .` from the project root, or add the
parent directory to path: `sys.path.append('..')`.

**Simulation unstable** — reduce `time_step`; check PID gains (try lower Kp/Ki);
verify actuator saturation limits.

**Unexpected results** — log both true and measured values to spot
sensor/controller discrepancies; print intermediate values inside `update()`.
