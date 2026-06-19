# Execution Mode: Batch Script

The script mode runs a complete simulation offline and produces a Pandas DataFrame. It is used by everything under `examples/`.

---

## Who drives the clock

`Experiment.run()` in `reactor_simulation/simulation/experiment.py` owns a blocking `for` loop. It ticks forward by a fixed `time_step` until `total_time` is reached.

```
Experiment.run(update_function, log_function)
    └── for step in range(num_steps):
            1. perturbation.apply(t)       ← scheduled disturbances
            2. update_function(t, dt)      ← all physics live here
            3. data = log_function(t)      ← record variables
            4. current_time += dt
    └── return DataFrame
```

---

## Where the phenomenological equations live

There is **no fixed location**. The caller passes an `update_function(t, dt)` callback, and all ODEs are written inside that function. Each example script defines its own equations.

Reference implementation: `examples/temperature_control_demo.py`

Typical structure of `update_function`:

```python
def update(t, dt):
    # 1. Sense
    measured_T = thermocouple.measure(state.temperature, dt)

    # 2. Control
    T_utility_cmd = pid.update(measured_T, dt)
    hx.set_utility_temperature(T_utility_cmd)

    # 3. Actuate
    Q = hx.update(state.temperature, dt)          # W
    F = pump.update(dt)                           # m³/s

    # 4. Mass balance  →  dCa/dt = (F/V)·(Ca_feed − Ca)
    Ca = state.get_concentration()
    dCa_dt = (F / V) * (Ca_feed - Ca)
    state.set_concentration(Ca + dCa_dt * dt)

    # 5. Energy balance  →  dT/dt = Q/(m·Cp) − UA·(T − T_amb)/(m·Cp)
    dT_dt = Q / (mass * Cp)
    dT_dt -= UA * (state.temperature - T_amb) / (mass * Cp)
    state.temperature += dT_dt * dt
```

To modify an equation, edit the corresponding line inside `update_function` in the script you are running. No package file needs to change.

---

## How perturbations work

Perturbation objects are registered on the `Experiment` instance before `run()` is called. On each tick the loop calls `perturbation.apply(t)`, which uses `setattr` to mutate a target object's attribute at a scheduled time.

```python
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
df = experiment.run(update, log)
```

| Class | File | Behavior |
|---|---|---|
| `StepPerturbation` | `simulation/perturbations.py:33` | One-time jump at `step_time` |
| `RampPerturbation` | `simulation/perturbations.py:76` | Linear ramp over `duration` seconds |
| `SinusoidalPerturbation` | `simulation/perturbations.py:128` | Continuous sinusoid after `start_time` |

Perturbations can target any object attribute: `pid.setpoint`, `pump.flow_setpoint`, `hx.T_utility_max`, etc.

---

## Output

`Experiment.run()` returns a Pandas DataFrame where each row is one time step and each column is a variable returned by `log_function`. The `time` column is added automatically.

```python
def log(t):
    return {
        'T_true':     state.temperature,
        'T_measured': thermocouple.get_reading(),
        'Ca':         state.get_concentration(),
        'Q':          hx.last_heat_output,
        'pid_p':      pid.get_components()['P'],
    }

df = experiment.run(update, log)
df.to_csv('results.csv', index=False)
```

---

## Entry points

| File | What it shows |
|---|---|
| `examples/temperature_control_demo.py` | Full closed-loop: HeatExchanger + PID + Thermocouple + StepPerturbation |
| `examples/compare_reactors.py` | PFR vs CSTR volume at the same conversion (steady-state, no time loop) |
| `examples/parallel_reaction1.py` | Parallel reaction selectivity |
| `examples/parallel_react2.py` | Parallel reaction yield optimisation |
| `examples/series_reactions.py` | Series reaction kinetics and yield |
| `examples/nonideal_reactor.py` | Non-ideal reactor with RTD |

---

## Where to go to change the physics

| What to change | Where |
|---|---|
| Mass balance ODE | `update_function` in the script (e.g. `temperature_control_demo.py`) |
| Energy balance ODE | Same `update_function` |
| Heat exchanger dynamics (lag on T_utility) | `reactor_simulation/actuators/heat_exchanger.py` |
| Pump ramp-rate model | `reactor_simulation/actuators/pump.py` |
| Thermocouple lag / noise / bias | `reactor_simulation/sensors/thermocouple.py` |
| PID algorithm (anti-windup, derivative filter) | `reactor_simulation/control/pid.py` |
| Reaction rate expression | `reactor_simulation/core/kinetics.py` — `Reaction.expression` lambda |
| Reactor volume / residence time | `reactor_simulation/core/reactor.py` — `PlugFlow`, `StirredTank`, `RecyclePlugFlow` |
