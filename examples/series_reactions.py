"""
For the reactions in series of first order:
    A -> R -> S
"""

import numpy as np
import matplotlib.pyplot as plt

# Define constants
k1 = 0.2  # Rate constant for A -> R (1/s)
k2 = 0.3  # # Rate constant for R -> S (1/s)

A0 = 1.0  # concentration of A (mol/L) at t = 0

# Define concentration of A as a function of time using a lambda function
A_t = lambda t: A0 * np.exp(-k1 * t)  # Vectorized function
R_t = lambda t: (A0 * k1) * (np.exp(-k1 * t) / (k2 - k1) + np.exp(-k2 * t) / (k1 - k2))
S_t = lambda t: A0 * (
    1 + (k2 / (k1 - k2)) * np.exp(-k1 * t) + (k1 / (k2 - k1)) * np.exp(-k2 * t)
)


# Define time array
t = np.linspace(0, 50, 500)  # Time points (0 to 50 seconds)

# Evaluate the concentration of A at each time point
A_conc = A_t(t)
R_conc = R_t(t)
S_conc = S_t(t)

# maximon cocnentration of R
t_max = np.log(k2 / k1) / (k2 - k1)
R_max = A0 * (k1 / k2) ** (k2 / (k2 - k1))


# Plot the concentration of A over time
plt.figure(figsize=(8, 5))
plt.plot(t, A_conc, label="[A](t)", color="blue")
plt.plot(t, R_conc, label="[R](t)", color="red")
plt.plot(t, S_conc, label="[S](t)", color="green")
plt.plot(t_max, R_max, "s", color="orange")

plt.xlabel("Time (t)")
plt.ylabel("Concentration of A [A](t)")
plt.title("Concentration of A as a Function of Time")
plt.grid(True)
plt.legend()
plt.show()
