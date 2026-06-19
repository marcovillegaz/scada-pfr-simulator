# Execution Mode: Real-time SCADA

The SCADA mode runs the simulation live inside a Qt desktop application. The clock is driven by a `QTimer`; physics advance one Euler step per tick and results are pushed immediately to the UI.

---

## Who drives the clock

`QTimer` in `scada_app/app.py` fires every `TIMER_INTERVAL_MS` milliseconds. Each tick calls `SimulationEngine.tick(sim_dt)` where `sim_dt = BASE_SIM_DT * speed_factor`.

```
QTimer (every TIMER_INTERVAL_MS ms)
    └── MainWindow._on_timer_tick()
            └── SimulationEngine.tick(sim_dt)   ← all physics here
            └── MainWindow._refresh_ui(snap)    ← update panels, graphs, table
```

Speed is controlled by a UI slider that multiplies `BASE_SIM_DT`. The wall-clock tick rate stays fixed; only the simulated time per tick changes.

---

## Where the phenomenological equations live

All ODEs are hard-coded inside `SimulationEngine.tick()` at `scada_app/engine/simulation_engine.py`.

### Full tick sequence

```python
# simulation_engine.py — SimulationEngine.tick(dt)

# 1. Thermocouple reads true temperature (with lag, bias, noise)
measured_T = self._tc.measure(self._state.temperature, dt)

# 2. PID outputs a utility temperature command
T_utility_cmd = self._pid.update(measured_T, dt)
self._hx.set_utility_temperature(T_utility_cmd)

# 3. Heat exchanger advances its first-order lag → Q = UA·(T_util − T_proc)
Q = self._hx.update(self._state.temperature, dt)       # W (+heat, −cool)

# 4. Pump advances its ramp-rate limit → actual flow
F = self._pump.update(dt)                              # m³/s
self._state.flow_rate = F

# 5. MASS BALANCE (Euler)
#    dCa/dt = (F / V) · (Ca_feed − Ca)
Ca = self._state.get_concentration()
dCa_dt = (F / REACTOR_VOLUME) * (self._feed_concentration - Ca)
self._state.set_concentration(Ca + dCa_dt * dt)

# 6. ENERGY BALANCE (Euler)
#    dT/dt = Q / (m·Cp)  −  UA·(T − T_amb) / (m·Cp)
dT_dt  =  Q / (MASS * HEAT_CAPACITY)
dT_dt -= HEAT_TRANSFER_COEFF * (self._state.temperature - AMBIENT_TEMP) / (MASS * HEAT_CAPACITY)
self._state.temperature += dT_dt * dt
self._state.time        += dt

# 7. Conductivity sensor reads concentration proxy
conductivity  = self._cond.measure(Ca, self._state.temperature, dt)
measured_conc = self._cond.concentration_from_conductivity(conductivity, self._state.temperature)

# 8. Package snapshot → DataStore (ring buffer for plots / table)
self._last_snap = EngineSnapshot(...)
self.data_store.append(self._last_snap)
```

### Phenomenological equations at a glance

| Equation | Symbol form | File : line |
|---|---|---|
| Mass balance | `dCa/dt = (F/V)·(Ca_in − Ca)` | `simulation_engine.py:92–96` |
| Energy balance | `dT/dt = Q/(m·Cp) − h·(T−T_amb)/(m·Cp)` | `simulation_engine.py:99–101` |
| Heat exchanger lag | `dT_util/dt = (T_cmd − T_util) / τ_hx` | `actuators/heat_exchanger.py` |
| Pump ramp | `ΔF = clip(F_cmd − F, −ṙ·dt, +ṙ·dt)` | `actuators/pump.py` |
| Thermocouple lag | `α = dt/(τ+dt); reading += α·(T_true − reading)` | `sensors/thermocouple.py` |
| Conductivity curve | `σ = a·C² + b·C + c` (+ temp correction + drift + noise) | `sensors/conductivity.py` |

---

## How perturbations work

There is **no automated perturbation system** in SCADA mode. Disturbances enter only through the UI:

```
ParametersPanel (user edits fields + clicks Apply)
    └── parameters_applied signal (dict)
            └── SimulationEngine.apply_parameters(params)
                    ├── self._feed_concentration = params['feed_concentration']
                    ├── self._pump.set_flow(params['flow_rate'])
                    ├── self._pid.set_setpoint(params['setpoint'])
                    ├── self._pid.set_gains(Kp, Ki, Kd)
                    └── self._hx.T_utility_max = params['T_utility_max']
```

All changes are instantaneous from the engine's perspective (no scheduling, no time-based trigger). To simulate a step disturbance, the user manually changes a parameter while the simulation is running.

---

## Physical constants

All constants used in the ODEs are defined in `scada_app/constants.py`:

| Constant | Symbol | Role |
|---|---|---|
| `REACTOR_VOLUME` | V | Denominator of mass balance |
| `MASS` | m | Denominator of energy balance |
| `HEAT_CAPACITY` | Cp | Denominator of energy balance |
| `HEAT_TRANSFER_COEFF` | UA (wall loss) | Heat loss term in energy balance |
| `AMBIENT_TEMP` | T_amb | Reference for wall heat loss |
| `BASE_SIM_DT` | dt₀ | Base time step before speed multiplier |
| `TIMER_INTERVAL_MS` | — | Wall-clock tick interval (ms) |

---

## Data flow through the UI

```
SimulationEngine.tick()
    └── EngineSnapshot (dataclass)
            ├── ReadingsPanel       ← live numeric displays
            ├── DiagramTab          ← PFR diagram with colour-coded temperature
            ├── GraphTab            ← real-time pyqtgraph plots
            └── TableTab            ← populated on STOP with full DataStore
```

`DataStore` is a ring buffer (`collections.deque`) of `EngineSnapshot` objects. `GraphTab` reads the entire buffer every tick to redraw curves. `TableTab` converts it to a DataFrame on stop.

---

## Entry point

```bash
cd scada_app
python main.py
```

---

## Where to go to change the physics

| What to change | Where |
|---|---|
| Mass balance ODE | `scada_app/engine/simulation_engine.py:92–96` |
| Energy balance ODE | `scada_app/engine/simulation_engine.py:99–101` |
| Physical constants (V, m, Cp, UA) | `scada_app/constants.py` |
| Heat exchanger dynamics | `reactor_simulation/actuators/heat_exchanger.py` |
| Pump ramp-rate model | `reactor_simulation/actuators/pump.py` |
| Thermocouple lag / noise / bias | `reactor_simulation/sensors/thermocouple.py` |
| PID algorithm (anti-windup, derivative filter) | `reactor_simulation/control/pid.py` |
| What parameters the user can change at runtime | `scada_app/ui/panels/parameters_panel.py` + `SimulationEngine.apply_parameters()` |
| Logged variables per snapshot | `scada_app/engine/data_store.py` — `EngineSnapshot` dataclass |
