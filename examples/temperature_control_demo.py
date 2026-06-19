"""
Example: Simple CSTR with Temperature Control

Demonstrates the full architecture:
- Reactor (CSTR with simple kinetics)
- Actuator (Heater)
- Controller (PID temperature control)
- Sensor (Thermocouple with noise and delay)
- Experiment (Orchestration with perturbations)

This shows how sensors lie, controllers act on measurements (not truth),
and actuators have inertia - creating realistic discrepancies for students.
"""

import numpy as np
import matplotlib.pyplot as plt

from reactor_simulation.core import ReactorState
from reactor_simulation.actuators import Heater
from reactor_simulation.control import PIDController
from reactor_simulation.sensors import Thermocouple
from reactor_simulation.simulation import Experiment, StepPerturbation

# === System Setup ===

# Create reactor state
reactor_state = ReactorState(n_species=1, n_spatial_points=1)
reactor_state.temperature = 350.0  # K (initial temperature)
reactor_state.set_concentration(1.0, species_idx=0)  # 1 mol/L

# Create actuator (heater)
heater = Heater(
    max_power=10000.0,  # W
    efficiency=0.95,
    time_constant=5.0,  # 5 seconds thermal inertia
)

# Create sensor (thermocouple with imperfections)
thermocouple = Thermocouple(
    noise_std=0.5,  # 0.5 K noise
    time_constant=5.0,  # 2 seconds thermal lag
    bias=1.0,  # 1 K calibration error
    seed=42,
)

# Create controller (PID)
pid = PIDController(
    Kp=3.0,
    Ki=1.5,
    Kd=0.0,
    setpoint=350.0,  # Target 350 K
    output_min=0.0,
    output_max=2000.0,
)

# Create experiment
experiment = Experiment(
    time_step=1,
    total_time=10000.0,
)

# Add step change in setpoint at t=100s
experiment.add_perturbation(
    StepPerturbation(
        target_object=pid,
        attribute_name="setpoint",
        initial_value=350.0,
        final_value=350.0,
        step_time=0.0,
    )
)

# Add step change in setpoint at t=100s
experiment.add_perturbation(
    StepPerturbation(
        target_object=pid,
        attribute_name="setpoint",
        initial_value=350.0,
        final_value=360.0,
        step_time=2000.0,
    )
)

experiment.add_perturbation(
    StepPerturbation(
        target_object=pid,
        attribute_name="setpoint",
        initial_value=360.0,
        final_value=370.0,
        step_time=5000.0,
    )
)

# === Dynamics ===

# System parameters
reactor_volume = 0.01  # m³ (10 liters)
heat_capacity = 4180.0  # J/(kg·K) - water-like
mass = 10.0  # kg


def update_system(t, dt):
    """Update system dynamics for one time step"""

    # 1. Measure temperature (sensor reading, not true value!)
    measured_temp = thermocouple.measure(reactor_state.temperature, dt)

    # 2. Controller acts on MEASURED temperature (this is key!)
    heater_power = pid.update(measured_temp, dt)

    # 3. Set actuator
    heater.set_power(heater_power)

    # 4. Get actual heat input (actuator has inertia)
    heat_input = heater.update(dt)

    # 5. Update reactor temperature (simple energy balance)
    # dT/dt = Q / (m * Cp)
    dT_dt = heat_input / (mass * heat_capacity)

    # Add some heat loss to environment (ambient = 298 K)
    heat_transfer_coeff = 25.0  # W/K
    heat_loss = heat_transfer_coeff * (reactor_state.temperature - 298.0)
    dT_dt -= heat_loss / (mass * heat_capacity)

    # Euler integration
    reactor_state.temperature += dT_dt * dt
    reactor_state.time += dt


def log_data(t):
    """Log data for plotting"""
    measured_temp = thermocouple.get_reading()

    return {
        "true_temperature": reactor_state.temperature,
        "measured_temperature": measured_temp,
        "setpoint": pid.setpoint,
        "heater_power": heater.actual_power,
        "heat_output": heater.get_heat_flow(),
    }


# === Run Experiment ===

print("Running temperature control experiment...")
df = experiment.run(update_system, log_data, verbose=True)

# === Plot Results ===

fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Temperature plot
ax1 = axes[0]
ax1.plot(df["time"], df["true_temperature"], "b-", linewidth=2, label="True Temperature")
ax1.plot(
    df["time"],
    df["measured_temperature"],
    "r--",
    linewidth=1.5,
    label="Measured (Sensor)",
    alpha=0.7,
)
ax1.plot(df["time"], df["setpoint"], "g:", linewidth=2, label="Setpoint")
ax1.set_ylabel("Temperature (K)", fontsize=12)
ax1.legend(loc="best")
ax1.grid(True, alpha=0.3)
ax1.set_title(
    "CSTR Temperature Control - Demonstrating Sensor Imperfections", fontsize=14, fontweight="bold"
)

# Heater power plot
ax2 = axes[1]
ax2.plot(df["time"], df["heater_power"], "r-", linewidth=2, label="Heater Power")
ax2.plot(
    df["time"],
    df["heat_output"],
    "b--",
    linewidth=1.5,
    label="Heat Output (with efficiency)",
    alpha=0.7,
)
ax2.set_xlabel("Time (s)", fontsize=12)
ax2.set_ylabel("Power (W)", fontsize=12)
ax2.legend(loc="best")
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("temperature_control_demo.png", dpi=150)
plt.show()

print("\nExperiment complete!")
print(f"Final true temperature: {df['true_temperature'].iloc[-1]:.2f} K")
print(f"Final measured temperature: {df['measured_temperature'].iloc[-1]:.2f} K")
print(f"Sensor bias: {thermocouple.bias:.2f} K")
print(
    f"Measurement error: {df['measured_temperature'].iloc[-1] - df['true_temperature'].iloc[-1]:.2f} K"
)
