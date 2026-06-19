# Reactor Simulation Package - Architecture

## Project Structure

```
chemical-engineering/
│
├── reactor_simulation/          # Main package
│   ├── __init__.py              # Package initialization with imports
│   │
│   ├── core/                    # PHYSICS - What the reactor IS
│   │   ├── __init__.py
│   │   ├── reactor.py           # Reactor classes (PFR, CSTR, RecyclePFR)
│   │   ├── kinetics.py          # Reaction rate expressions
│   │   └── state.py             # State variables (C, T, P, F)
│   │
│   ├── actuators/               # BOUNDARY CONDITIONS - Physical devices
│   │   ├── __init__.py
│   │   ├── heater.py            # Heat input with inertia
│   │   └── pump.py              # Flow rate with ramp limits
│   │
│   ├── control/                 # CONTROL - How humans boss it around
│   │   ├── __init__.py
│   │   └── pid.py               # PID controller (acts on measurements!)
│   │
│   ├── sensors/                 # MEASUREMENT - What sensors think
│   │   ├── __init__.py
│   │   ├── thermocouple.py      # Temperature with noise, delay, bias
│   │   └── conductivity.py      # Concentration via conductivity
│   │
│   └── simulation/              # ORCHESTRATION - The lab bench
│       ├── __init__.py
│       ├── experiment.py        # Time loop, integration, logging
│       └── perturbations.py     # Step, ramp, sinusoidal inputs
│
├── examples/                    # Example scripts
│   ├── README.md
│   ├── temperature_control_demo.py  # Full system demonstration
│   ├── compare_reactors.py          # PFR vs CSTR comparison
│   ├── parallel_reaction1.py
│   ├── parallel_react2.py
│   ├── series_reactions.py
│   └── nonideal_reactor.py
│
├── tests/                       # Test scripts
│   ├── README.md
│   ├── recycle_test.py
│   └── series_test.py
│
├── README.md                    # Main documentation
├── setup.py                     # Package installation
├── requirements.txt             # Dependencies
└── ARCHITECTURE.md             # This file
```

## Design Principles

### 1. Separation of Concerns

**Core** (reactor.py, kinetics.py, state.py)
- Contains the "truth" - actual physical state
- Knows: C(z,t), T(t), P(t), kinetics r(C,T)
- Does NOT know: how sensors measure, how controllers work

**Actuators** (heater.py, pump.py)
- Modify boundary conditions (NOT state directly)
- Have physical limitations: inertia, saturation, ramp rates
- Convert commands → physical effects

**Control** (pid.py)
- Acts on MEASUREMENTS, not truth
- Outputs go to actuators
- Critical: Creates realistic discrepancies for students

**Sensors** (thermocouple.py, conductivity.py)
- Never return true values
- Add: noise, delay, bias, drift, nonlinearity
- This is where "reality" diverges from measurements

**Simulation** (experiment.py, perturbations.py)
- The "lab bench" - orchestrates everything
- Manages time loop, integration, logging
- Applies perturbations for testing

### 2. Information Flow

```
┌─────────────────────────────────────────────────────────┐
│                    EXPERIMENT                            │
│                  (Orchestration)                         │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │ REACTOR │    │ ACTUATORS│    │ SENSORS  │
    │ (Truth) │    │ (Devices)│    │ (Measure)│
    └─────────┘    └──────────┘    └──────────┘
          ▲               │               │
          │               │               ▼
          │               │         ┌──────────┐
          │               │         │CONTROLLER│
          │               │         │  (PID)   │
          │               │         └──────────┘
          │               │               │
          └───────────────┴───────────────┘
```

**Data Flow:**
1. Sensors measure TRUE state → produce MEASURED values
2. Controller reads MEASURED values → outputs commands
3. Actuators receive commands → modify boundary conditions
4. Reactor state evolves based on boundary conditions
5. Repeat

**Key Insight:** Controller never sees truth! This creates educational value.

### 3. Scalability

Adding new features is modular:

**Add new reactor type:**
- Create new class in `core/reactor.py`
- Inherits from `Reactor` base class
- Implement `residence_time()` method

**Add new sensor:**
- Create new file in `sensors/`
- Implement `measure()` method
- Add imperfections (noise, delay, etc.)

**Add new controller:**
- Create new file in `control/`
- Implement `update()` method
- Acts on measurements

**Add heat transfer:**
- Extend `ReactorState` in `core/state.py`
- Add energy balance to reactor dynamics
- Create `JacketCooling` in `actuators/`

**Add GUI:**
- Create new `visualization/` module
- Import from existing modules
- No modification to existing code needed

## Usage Pattern

```python
# 1. Create components (Lego blocks)
reactor = ReactorState(n_species=1)
heater = Heater(max_power=1000)
sensor = Thermocouple(noise_std=0.5)
controller = PIDController(Kp=50, Ki=5, Kd=10)

# 2. Define dynamics
def update(t, dt):
    measured = sensor.measure(reactor.temperature, dt)
    power = controller.update(measured, dt)
    heater.set_power(power)
    heat = heater.update(dt)
    reactor.temperature += (heat / mass / Cp) * dt

# 3. Define logging
def log(t):
    return {
        'T_true': reactor.temperature,
        'T_measured': sensor.get_reading(),
        'power': heater.actual_power,
    }

# 4. Run experiment
experiment = Experiment(time_step=0.5, total_time=200)
df = experiment.run(update, log)
```

## Educational Value

Students learn:
1. **Sensor imperfections matter** - noise, delay, bias create errors
2. **Controllers act on measurements** - not on truth
3. **Actuators have dynamics** - can't change instantly
4. **System identification** - use perturbations to learn dynamics
5. **Real vs ideal** - textbook models vs realistic behavior

## Next Steps

Potential extensions (in order of priority):
1. ✅ Basic structure (DONE)
2. Add dynamic PFR with spatial discretization
3. Add multi-component reactions
4. Add heat transfer (jacket, coils)
5. Add pressure dynamics
6. Add advanced control (MPC, feedforward)
7. Add real-time visualization
8. Add parameter estimation tools
9. Add fault injection (sensor failures, etc.)
10. Add batch reactor operations
