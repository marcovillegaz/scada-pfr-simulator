import matplotlib.pyplot as plt
import numpy as np

from reaction_kinetics.overall_yields import *

# Kinetic constants
k1 = 11
k2 = 3.2

# Concentrations in feed stream
Ca_0 = 19
Cb_0 = 1
Xa = 0.9  # Final converstion
Ca_f = Ca_0 * (1 - Xa)  # Final molar concentration (mol/L)

# Define lambda functions
# Stoichiometric relationship for Cb
# Cb = lambda Ca: np.maximum(Cb_0 - (Ca_0 - Ca), 0)
Cb = lambda Ca: 1

# Kinetic expression for multiple reactions.
r_R = lambda Ca: k1 * (Ca**1.5) * (Cb(Ca) ** 0.3)
r_S = lambda Ca: k2 * (Ca**0.5) * (Cb(Ca) ** 1.8)


# Intantaneous fraction of R in base of A
phi = lambda Ca: r_R(Ca) / (r_R(Ca) + r_S(Ca))

# Overall fractional yield of R in base of A
Phi_p = overall_yield_pfr(phi, Ca_0, Ca_f)
Phi_m = overall_yield_mfr(phi, Ca_f)

print(f"Overall Yield (Phi_p): {Phi_p:.4f}")
print(f"Overall Yield (Phi_m): {Phi_m:.4f}")


# Plotting instantaneus fractional yields
Ca_values = np.linspace(0, Ca_0, 100)
phi_values = phi(Ca_values)

# Plot the result
plt.plot(Ca_values, phi_values, label=r"$\phi(C_a)$")
plt.xlabel(r"$C_a$")
plt.ylabel(r"$\phi$")
plt.title("Plot of $\phi(C_a)$")
plt.legend()
plt.grid()
plt.show()
