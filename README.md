# Chemical Reactor Simulation Package

A modular Python package for simulating chemical reactors with realistic sensor noise, actuator dynamics, and control systems. Designed for generating synthetic data for educational purposes.

## Design Philosophy

This package follows a strict separation of concerns:

1. **Physical State** (Core) - What the reactor IS
   - Concentration profiles, temperature, pressure
   - Reactor types: PFR, CSTR, Recycle PFR
   - Reaction kinetics

2. **Dynamics** - How it EVOLVES
   - Time integration
   - Material and energy balances

3. **Control** - How humans try to CONTROL it
   - PID controllers
   - Acts on measurements, not true states

4. **Measurement** - What sensors THINK is happening
   - Thermocouple (with noise, delay, bias)
   - Conductivity sensor (with drift, nonlinearity)
   - Sensors never return true values!

5. **Orchestration** - The experiment itself
   - Time loop management
   - Perturbations (step, ramp, sinusoidal)
   - Data logging

This separation makes the code scalable - adding heat transfer or a GUI becomes "Lego", not archaeological work.

## Package Structure

```
reactor_simulation/
├── core/              # Reactor physics and kinetics
│   ├── reactor.py     # Reactor classes (PFR, CSTR, etc.)
│   ├── kinetics.py    # Reaction rate expressions
│   └── state.py       # State variables
├── actuators/         # Physical devices (heater, pump)
│   ├── heater.py
│   └── pump.py
├── control/           # Control algorithms
│   └── pid.py         # PID controller
├── sensors/           # Measurement devices
│   ├── thermocouple.py
│   └── conductivity.py
└── simulation/        # Experiment orchestration
    ├── experiment.py
    └── perturbations.py
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

See `examples/temperature_control_demo.py` for a complete example showing:
- CSTR with temperature control
- PID controller acting on noisy sensor data
- Heater with thermal inertia
- Step change in setpoint

```python
from reactor_simulation import (
    ReactorState, Heater, PIDController, 
    Thermocouple, Experiment, StepPerturbation
)

# Create components
reactor_state = ReactorState(n_species=1)
heater = Heater(max_power=1000.0, efficiency=0.95)
thermocouple = Thermocouple(noise_std=0.5, bias=1.0)
pid = PIDController(Kp=50.0, Ki=5.0, Kd=10.0, setpoint=350.0)

# Run experiment
experiment = Experiment(time_step=0.5, total_time=200.0)
# ... define update and log functions
df = experiment.run(update_function, log_function)
```

## Examples

- `examples/temperature_control_demo.py` - Full closed-loop temperature control
- `examples/compare_reactors.py` - Compare PFR vs CSTR residence times
- `examples/parallel_reaction1.py` - Parallel reaction schemes
- `examples/series_reactions.py` - Series reaction kinetics

## Educational Use

This package is designed to generate realistic synthetic data for students when physical equipment is unavailable. Key features:

- **Sensor imperfections**: Noise, delay, and bias create realistic discrepancies
- **Actuator dynamics**: Heaters and pumps have inertia and rate limits
- **Control realism**: Controllers act on measurements, not true states
- **Perturbation testing**: Step, ramp, and sinusoidal inputs for system identification

## Future Extensions

The modular structure makes it easy to add:
- Heat transfer models (jacket cooling, coils)
- Pressure dynamics
- Multi-component reactions
- Spatial discretization for PFR
- Advanced control (MPC, feedforward)
- Real-time visualization GUI

