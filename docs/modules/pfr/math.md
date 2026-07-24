# Mathematical Model — PFR Module (ChemEng SimLab)

This document contains all governing equations for the dynamic PFR simulation.
Implementation lives in `reactor_simulation/core/pfr_model.py` and constants
are defined in `scada_app/constants.py`.

---

## 1. System Overview

The simulated plant is a **plug flow reactor** preceded by a **heat exchanger**:

```
TK-101 (NaOH) ──┐
                 ├──► Mixing Node ──► HX ──► PFR ──► CT-101 (conductivity)
TK-102 (EtAc) ──┘                           │
                                             TE-101 (T_in)  TE-102 (T_out)
```

**Reaction:** NaOH (A) + EtAc (B) → NaAc + EtOH (saponification, 2nd order)

---

## 2. Mixing Node

Two independent feed streams are combined before entering the HX:

```
Q_in  = Qa0 + Qb0                            [m³/s]
CA_in = Ca0 · Qa0 / Q_in                     [mol/m³]  (after unit conversion)
CB_in = Cb0 · Qb0 / Q_in                     [mol/m³]
u     = Q_in / A_cross                        [m/s]
```

where `A_cross = π·(D/2)²` is the tube cross-sectional area.

---

## 3. Heat Exchanger (HX)

The HX is modelled as a single well-mixed node (process-side holdup V_hx).
The energy balance has an **exact analytic solution** (no ODE solver):

```
dT_hx/dt = (a − b·T_hx) / (V_hx · ρ · cp)

where:
    a = Q_in · ρ · cp · T_feed  +  UA · T_hw
    b = Q_in · ρ · cp  +  UA_eff

Exact solution over one tick Δt:
    T_hx(t + Δt) = T_ss + (T_hx(t) − T_ss) · exp(−b · Δt / (V_hx · ρ · cp))
    T_ss = a / b   (steady-state temperature)
```

`UA_eff = UA_max · valve`,  where `valve ∈ [0, 1]` is the PID output.
The HX outlet temperature `T_hx` becomes the PFR inlet temperature `T_in`.

**Default parameters:**

| Symbol | Value | Unit | Description |
|---|---|---|---|
| `V_hx` | 0.002 | m³ | Process-side holdup |
| `T_hw` | 333.15 | K (60 °C) | Hot-water temperature |
| `UA_max` | 100 | W/K | Overall heat transfer at full valve opening |

---

## 4. PFR — Mass Balance (species A and B)

Conservation of species along the reactor axis (no axial dispersion):

```
∂CA/∂t = −u · ∂CA/∂z − rA
∂CB/∂t = −u · ∂CB/∂z − rA
```

- `CA(z, t)`, `CB(z, t)` — concentrations [mol/m³]
- `u` — superficial velocity [m/s]
- `rA` — volumetric reaction rate [mol/(m³·s)] (same for A and B — 1:1 stoichiometry)
- Boundary condition (inlet): `CA(0, t) = CA_in(t)`, `CB(0, t) = CB_in(t)`
- Initial condition: uniform profile at `CA_in`, `CB_in`

---

## 5. PFR — Energy Balance

Non-adiabatic reactor: the bare tube loses heat to the ambient through its wall.

```
ρ·cp · ∂T/∂t = −ρ·cp·u · ∂T/∂z  +  (−ΔHr)·rA  −  h_loss·(T − T_amb)
```

- `T(z, t)` — fluid temperature [K]
- `ΔHr` — heat of reaction [J/mol] (negative = exothermic; set to 0 for isothermal)
- `h_loss = U_loss · (4/D)` — volumetric heat loss coefficient [W/(m³·K)]
- `T_amb` — ambient temperature [K] (also the feed temperature)
- Boundary condition (inlet): `T(0, t) = T_in(t)` (HX outlet)
- Initial condition: uniform profile at `T_in`

**Physical basis for h_loss:**
For a bare tube with U_loss ≈ 10 W/(m²·K) (natural convection to still air) and
D = 5 mm: `h_loss = 4 × 10 / 0.005 = 8000 W/(m³·K)`.

---

## 6. Reaction Kinetics — Arrhenius + Bimolecular

```
k(T) = k₀ · exp(−Ea / (R · T))
rA   = k(T) · CA · CB
```

- `k₀` — pre-exponential factor [m³/(mol·s)]
- `Ea` — activation energy [J/mol]
- `R` = 8.314 J/(mol·K)

**Calibrated values** (literature saponification, recalibrated for the 20–50 °C
operating envelope):

| Parameter | Value | Unit |
|---|---|---|
| `k₀` | 1.1463 × 10⁴ | m³/(mol·s) |
| `Ea` | 46 000 | J/mol |

Resulting conversion (at `CA_in = CB_in = 50 mol/m³`, default flows):
`X ≈ 31 %` at 20 °C → `X ≈ 60 %` at 40 °C → `X ≈ 72 %` at 50 °C.

---

## 7. Method of Lines (MOL) Discretization

The reactor is divided into N = 50 equally-spaced nodes:

```
dz = L / N,    z_i = i · dz,    i = 0, 1, ..., N−1
```

Convective terms are approximated with **first-order upwind differences**
(mandatory for hyperbolic systems — ensures stability):

```
∂CA/∂z |_i  ≈  (CA[i] − CA[i−1]) / dz    for i = 1, ..., N−1
∂CA/∂z |_0  ≈  (CA[0] − CA_in)   / dz    (boundary node)
```

Same scheme for CB and T. This transforms the PDE system into a system of
`3N` ODEs in time:

```
dCA[i]/dt = −u · (CA[i] − CA[i−1]) / dz  −  rA[i]
dCB[i]/dt = −u · (CB[i] − CB[i−1]) / dz  −  rA[i]
dT[i]/dt  = −u · (T[i]  − T[i−1])  / dz
            + (−ΔHr) · rA[i] / (ρ · cp)
            − h_loss · (T[i] − T_amb) / (ρ · cp)
```

**Do not use central differences** — they produce unphysical oscillations in
pure convection systems (Gibbs phenomenon).

---

## 8. Numerical Integration

`scipy.integrate.solve_ivp` with method **`RK45`** (explicit Runge-Kutta,
4th-order accurate, adaptive step size).

**CFL stability check** (for explicit solvers):

```
CFL = u · Δt / Δz = u · dt / (L/N)
```

At default parameters (`u ≈ 0.02 m/s`, `Δt = 0.5 s`, `L/N = 0.418 m`):
`CFL ≈ 0.024 << 1` — well within the stability limit. The `solve_ivp` adaptive
stepper handles this automatically.

**Tolerances:** `rtol = 1×10⁻⁴`, `atol = 1×10⁻⁶`.

---

## 9. Sensor Models

### CT-101 — Conductivity Sensor

Linear calibration curve with additive Gaussian noise:

```
σ = A · CA_out  +  B  +  N(0, σ_noise)
```

| Parameter | Value | Unit |
|---|---|---|
| A | 156 | mS/cm per (mol/L) |
| B | 1.6 | mS/cm |
| σ_noise | 0.05 | mS/cm |

Note: `CA_out` must be in mol/L (not mol/m³) when applying these coefficients.

### TE-101 / TE-102 — Temperature Sensors

Additive Gaussian noise on the reported reading; the PFR and PID controller
use the **true** temperature:

```
T_measured = T_true  +  N(0, σ_T)     σ_T = 0.3 K
```

---

## 10. PID Controller

Discrete-time PI(D) with clamped conditional anti-windup:

```
e[k]  = setpoint − y_measured[k]
P     = Kp · e[k]
I    += Ki · e[k] · dt             (only when not saturated, or error drives output inward)
D     = Kd · (e[k] − e[k−1]) / dt (filtered by derivative_filter_tau if > 0)
u[k]  = clip(P + I + D, u_min, u_max)
```

**Defaults for the SCADA HX loop:**

| Parameter | Value |
|---|---|
| Kp | 0.14 valve/K |
| Ki | 0.04 valve/(K·s) |
| Kd | 0.0 |
| output_min | 0.0 (closed) |
| output_max | 1.0 (fully open) |
| setpoint | 293 K (20 °C, cold start) |

**Known structural limitation:** The controlled variable is `T_reactor = (T_in + T_out)/2`.
Because `T_out` includes ~120 s of transport delay through the PFR, the loop
has inherent dead time that causes 5–7 °C overshoot on setpoint steps. This
overshoot is **not removable by retuning** — it is constant across a 12× range
of Kp. Removing it would require controlling `T_in` directly.

---

## 11. Full Parameter Table

| Symbol | Name | Value | Unit |
|---|---|---|---|
| `L` | Reactor length | 20.9 | m |
| `D` | Tube inner diameter | 0.005 | m |
| `A_cross` | Cross-sectional area | π·(D/2)² ≈ 1.96×10⁻⁵ | m² |
| `N` | Spatial nodes | 50 | — |
| `ρ` | Fluid density | 1000 | kg/m³ |
| `cp` | Heat capacity | 4180 | J/(kg·K) |
| `T_amb` | Ambient / feed temperature | 288 | K (15 °C) |
| `k₀` | Pre-exponential factor | 1.1463×10⁴ | m³/(mol·s) |
| `Ea` | Activation energy | 46 000 | J/mol |
| `ΔHr` | Heat of reaction | 0 | J/mol (isothermal) |
| `h_loss` | Wall heat loss coefficient | 8 000 | W/(m³·K) |
| `Qa0` | Feed A (NaOH) default flow | 1.667×10⁻⁶ | m³/s (0.1 mL/s) |
| `Qb0` | Feed B (EtAc) default flow | 1.667×10⁻⁶ | m³/s |
| `Ca0` | Feed A concentration | 0.1 | mol/L |
| `Cb0` | Feed B concentration | 0.1 | mol/L |
