import numpy as np
import matplotlib.pyplot as plt

from reactor_simulation.control import PIDController


# ============================================================
# First-order dynamic plant
# ============================================================
# This class represents a generic first-order linear system:
#
#     τ dy(t)/dt + y(t) = K u(t)
#
# or equivalently:
#
#     dy(t)/dt = (-y(t) + K u(t)) / τ
#
# where:
#   y(t) : process variable (e.g. temperature, concentration surrogate)
#   u(t) : control input (e.g. heater power)
#   K    : static gain of the system
#   τ    : time constant (system inertia)
#
# Physically, this can represent:
#   - A lumped thermal mass (reactor + wall + fluid)
#   - A sensor with response delay
#   - A simplified actuator–process combination
#
# The system is integrated in time using an explicit Euler scheme.
# ============================================================
class FirstOrderPlant:
    def __init__(self, K=1.0, tau=5.0):
        self.K = K  # Static gain (steady-state sensitivity)
        self.tau = tau  # Time constant [s]
        self.y = 0.0  # Initial process variable

    def update(self, u, dt):
        """
        Update the plant state over one time step.

        Parameters
        ----------
        u : float
            Control input (manipulated variable)
        dt : float
            Time step [s]

        Returns
        -------
        y : float
            Updated process variable
        """
        # Differential equation:
        # dy/dt = (-y + K*u) / tau
        dy = (-self.y + self.K * u) / self.tau

        # Explicit Euler time integration:
        # y(t + dt) = y(t) + dy/dt * dt
        self.y += dy * dt

        return self.y


# PID instance
pid = PIDController(
    Kp=0.0,
    Ki=3.0,
    Kd=0.5,
    setpoint=1.0,
    output_min=-2,
    output_max=2,
    derivative_filter_tau=0.05,
)


# ============================================================
# Simulation parameters
# ============================================================
dt = 0.01  # Time step [s]
t_final = 50  # Total simulation time [s]
time = np.arange(0, t_final, dt)

# Plant instance
plant = FirstOrderPlant(K=1.0, tau=3.0)


# Data storage for analysis and plotting
y_history = []  # Process variable history
u_history = []  # Control signal history

# ============================================================
# Time integration loop
# ============================================================
# At each time step:
#   1) The PID computes the control action based on the current output
#   2) The plant state is updated using the control input
# ============================================================
for t in time:
    # Compute control action from PID
    u = pid.update(plant.y, dt)

    # Update plant dynamics
    y = plant.update(u, dt)

    # Store results
    y_history.append(y)
    u_history.append(u)


# ============================================================
# Visualization of results
# ============================================================
plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)
plt.plot(time, y_history, label="Process variable")
plt.axhline(pid.setpoint, linestyle="--", label="Setpoint")
plt.xlabel("Time [s]")
plt.ylabel("y")
plt.legend()
plt.grid()

plt.subplot(1, 2, 2)
plt.plot(time, u_history, label="Control output")
plt.xlabel("Time [s]")
plt.ylabel("u")
plt.legend()
plt.grid()

# plt.tight_layout()
plt.show()
