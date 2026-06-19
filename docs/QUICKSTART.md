# Quick Start Guide - Reactor Simulation Package

## Installation

```bash
# From the project root directory
pip install -e .
```

This installs the package in development mode, allowing you to modify the code and see changes immediately.

## Basic Import Pattern

```python
# Import individual components
from reactor_simulation.core import ReactorState, PlugFlow, StirredTank
from reactor_simulation.actuators import Heater, Pump
from reactor_simulation.control import PIDController
from reactor_simulation.sensors import Thermocouple, ConductivitySensor
from reactor_simulation.simulation import Experiment

# OR import everything at once
from reactor_simulation import (
    ReactorState, PlugFlow, StirredTank,
    Heater, Pump,
    PIDController,
    Thermocouple, ConductivitySensor,
    Experiment, StepPerturbation
)
```

## Common Workflows

### 1. Steady-State Reactor Comparison (existing examples)

```python
from reactor_simulation.core import PlugFlow, StirredTank

# Create reactors
pfr = PlugFlow(order_of_reaction=1, kinetic_constant=0.1)
cstr = StirredTank(order_of_reaction=1, kinetic_constant=0.1)

# Calculate residence times
tau_pfr = pfr.residence_time(Xa=0.9, Ca0=50, Xai=0, epsilon=0)
tau_cstr = cstr.residence_time(Xa=0.9, Ca0=50, Xai=0, epsilon=0)

print(f"PFR residence time: {tau_pfr:.2f} s")
print(f"CSTR residence time: {tau_cstr:.2f} s")
```

### 2. Dynamic Temperature Control

```python
from reactor_simulation import (
    ReactorState, Heater, PIDController, 
    Thermocouple, Experiment
)

# Setup
reactor = ReactorState()
reactor.temperature = 300.0  # K

heater = Heater(max_power=1000, efficiency=0.95)
sensor = Thermocouple(noise_std=0.5, bias=1.0)
pid = PIDController(Kp=50, Ki=5, Kd=10, setpoint=350)

# Dynamics
def update(t, dt):
    measured_T = sensor.measure(reactor.temperature, dt)
    power = pid.update(measured_T, dt)
    heater.set_power(power)
    heat = heater.update(dt)
    
    # Simple energy balance
    reactor.temperature += (heat / (10 * 4180)) * dt  # 10 kg water

# Logging
def log(t):
    return {
        'T_true': reactor.temperature,
        'T_measured': sensor.get_reading(),
        'power': heater.actual_power
    }

# Run
experiment = Experiment(time_step=0.5, total_time=100)
df = experiment.run(update, log, verbose=True)
```

### 3. Adding Perturbations

```python
from reactor_simulation import StepPerturbation, RampPerturbation

# Step change in setpoint at t=50s
step = StepPerturbation(
    target_object=pid,
    attribute_name='setpoint',
    initial_value=350,
    final_value=360,
    step_time=50
)
experiment.add_perturbation(step)

# Ramp flow rate from 0.001 to 0.002 m³/s over 20 seconds
ramp = RampPerturbation(
    target_object=pump,
    attribute_name='flow_setpoint',
    start_value=0.001,
    end_value=0.002,
    start_time=30,
    duration=20
)
experiment.add_perturbation(ramp)
```

### 4. Working with Sensors

```python
from reactor_simulation import Thermocouple, ConductivitySensor

# Thermocouple with realistic imperfections
tc = Thermocouple(
    noise_std=0.5,      # 0.5 K measurement noise
    time_constant=2.0,  # 2 second thermal lag
    bias=1.0,           # 1 K calibration error
    seed=42             # For reproducibility
)

# Measure temperature
measured = tc.measure(true_temperature=350.0, dt=0.1)

# Conductivity sensor for concentration
cond = ConductivitySensor(
    calibration_params={'a': 0, 'b': 1.5, 'c': 0.1},  # Linear: 1.5*C + 0.1
    noise_std=0.01,
    drift_rate=0.001  # Drifts 0.001 mS/cm per hour
)

# Measure and convert back
conductivity = cond.measure(true_concentration=1.0, dt=0.1)
estimated_conc = cond.concentration_from_conductivity(conductivity)
```

## Plotting Results

```python
import matplotlib.pyplot as plt

# After running experiment
df = experiment.run(update, log)

# Create plots
fig, axes = plt.subplots(2, 1, figsize=(10, 8))

# Temperature
axes[0].plot(df['time'], df['T_true'], label='True')
axes[0].plot(df['time'], df['T_measured'], label='Measured')
axes[0].set_ylabel('Temperature (K)')
axes[0].legend()
axes[0].grid(True)

# Power
axes[1].plot(df['time'], df['power'])
axes[1].set_xlabel('Time (s)')
axes[1].set_ylabel('Heater Power (W)')
axes[1].grid(True)

plt.tight_layout()
plt.show()
```

## Running Examples

```bash
# Navigate to examples directory
cd examples

# Run temperature control demo
python temperature_control_demo.py

# Run reactor comparison
python compare_reactors.py
```

## Tips

1. **Always use `dt` in sensor and actuator updates** - they need time step for dynamics
2. **Controllers act on measurements, not truth** - this is intentional for realism
3. **Log both true and measured values** - to show discrepancies to students
4. **Use `seed` parameter in sensors** - for reproducible "random" noise
5. **Start simple, add complexity gradually** - get basic loop working first

## Common Patterns

### Pattern 1: Closed-Loop Control
```
Reactor (truth) → Sensor (measures) → Controller (acts) → Actuator (modifies) → Reactor
```

### Pattern 2: Open-Loop Testing
```
Perturbation → Actuator → Reactor → Sensor → Log data
```

### Pattern 3: System Identification
```
Apply step/ramp → Measure response → Analyze dynamics → Tune controller
```

## Troubleshooting

**Import errors?**
- Make sure you installed the package: `pip install -e .`
- Or add parent directory to path: `sys.path.append('..')`

**Plots not showing?**
- Use `plt.show()` at the end
- Or save to file: `plt.savefig('output.png')`

**Simulation unstable?**
- Reduce time step (dt)
- Check PID gains (try lower values)
- Add saturation limits

**Getting weird results?**
- Check sensor bias/noise settings
- Verify actuator limits
- Print intermediate values for debugging
