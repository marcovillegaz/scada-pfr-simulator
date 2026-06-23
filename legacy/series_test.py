import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt


# Define the system of differential equations
def reaction_in_series(t, y, k1, k2):
    A, B, C = y
    dA_dt = -k1 * A**0.5
    dB_dt = k1 * A - k2 * B**2
    dC_dt = k2 * B
    return [dA_dt, dB_dt, dC_dt]


# Parameters
k1 = 0.2  # rate constant for A -> B (1/s)
k2 = 0.1  # rate constant for B -> C (1/s)

# Initial concentrations
A0 = 1.0  # initial concentration of A (mol/L)
B0 = 0.0  # initial concentration of B (mol/L)
C0 = 0.0  # initial concentration of C (mol/L)

t_span = (0, 50)  # time range in seconds
t_eval = np.linspace(t_span[0], t_span[1], 500)  # time points for solution

# Solve the system of equations
solution = solve_ivp(
    reaction_in_series,
    t_span,
    [A0, B0, C0],
    args=(k1, k2),
    t_eval=t_eval,
    method="RK45",
)

# Extract time and concentrations
time = solution.t
A = solution.y[0]
B = solution.y[1]
C = solution.y[2]

# Plot the results
plt.figure(figsize=(8, 5))
plt.plot(time, A, label="[A] (Reactant)")
plt.plot(time, B, label="[B] (Intermediate)")
plt.plot(time, C, label="[C] (Product)")
plt.xlabel("Time (s)")
plt.ylabel("Concentration (mol/L)")
plt.title("First-Order Reaction in Series")
plt.legend()
plt.grid()
plt.show()
