import matplotlib.pyplot as plt
import numpy as np

from reaction_kinetics.overall_yields import *
from scipy.optimize import minimize_scalar


# Obtain the maximum expected C_S for isothermal operations

# System conditions
Ca_0 = 2

# Kinetic
r_R = lambda Ca: 1
r_S = lambda Ca: 2 * Ca
r_T = lambda Ca: Ca**2

phi = lambda Ca: r_S(Ca) / (r_R(Ca) + r_S(Ca) + r_T(Ca))


# Case 1: Mixed reactor (maximization of rectangle find Ca)

# Define rectangle area
""" rectangle = lambda Ca: phi(Ca) * (Ca_0 - Ca)
# Find the maximum rectangle
result = minimize_scalar(lambda Ca: -rectangle(Ca), bounds=(0, 10), method="bounded")
# Extract the maximum value and its position
Ca_max = result.x
phi_max = phi(Ca_max)
# Compute final concentration of S
Cs_f = overall_yield_mfr(phi, Ca_max) * (Ca_0 - Ca_max)
print("Concentration of S with MFR:", Cs_f) """

# Case 2: Pluf flow reactor 100% convertion

""" Cs_f = overall_yield_pfr(phi, Ca_0, 0) * (Ca_0 - 0)
print("Concentration of S with PFR:", Cs_f)
 """
# Case 3: PFR + MFR
result = minimize_scalar(lambda Ca: -phi(Ca), bounds=(0, 10), method="bounded")
Ca_max = result.x
phi_max = phi(Ca_max)

# MFR contribution
Cs_MFR = overall_yield_mfr(phi, Ca_max) * (Ca_0 - Ca_max)
print(Cs_MFR)
# PFR contribution
Cs_PFR = overall_yield_pfr(phi, Ca_max, 0) * (Ca_max - 0)
print(Cs_PFR)
Cs_F = Cs_PFR + Cs_MFR
print("Final concentration in multiple reactors:", Cs_F)


##################################################################
# Generate values to plot
Ca_values = np.linspace(0, Ca_0, 100)
phi_values = phi(Ca_values)
# Plot fractional yield curve
plt.plot(Ca_values, phi_values, label=r"$\phi(C_a)$")

# plt.plot(Ca_max, phi_max, "s", color="red")  # MFR maximum
# plt.plot(Ca_max, phi_max, "s", color="red")

plt.xlabel(r"$C_a$")
plt.ylabel(r"$\phi$")
plt.title("Plot of $\phi(C_a)$")
plt.legend()
plt.grid()
plt.show()
