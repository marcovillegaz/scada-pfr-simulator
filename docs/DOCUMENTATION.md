# reactor_simulation — Developer Documentation

This document describes every class in the `reactor_simulation` package: what it does physically, every parameter you can change, every method you can call, and exactly where to go when you want to modify a model.

Run the test suite after any modification to confirm nothing is broken:

```bash
pytest tests/ -v
```

---

## Package Map

```
reactor_simulation/
├── core/
│   ├── reactor.py      ← Reactor, PlugFlow, StirredTank, RecyclePlugFlow
│   ├── kinetics.py     ← Reaction, overall_yield_pfr, overall_yield_mfr
│   └── state.py        ← ReactorState
├── actuators/
│   ├── heater.py       ← Heater
│   └── pump.py         ← Pump
├── control/
│   └── pid.py          ← PIDController
└── sensors/
    ├── thermocouple.py ← Thermocouple
    └── conductivity.py ← ConductivitySensor
```

---

## core/reactor.py

### `Reactor` (base class)

All reactor types inherit from this. You never instantiate it directly.

| Attribute | Type | Description |
|-----------|------|-------------|
| `order_of_reaction` | `float` | Reaction order `n` |
| `kinetic_constant` | `float` | Rate constant `k` |
| `reactor_type` | `str` | Set by each subclass |

**Method: `get_volume(volumetric_flow, output_conversion, input_concentration, input_conversion)`**

Calls `residence_time()` then multiplies by flow. Returns reactor volume in m³ (if flow is in m³/s).

---

### `PlugFlow` — Plug Flow Reactor (PFR)

Models an ideal tubular reactor with no axial mixing. Every fluid element travels in plug flow.

```python
from reactor_simulation import PlugFlow

pfr = PlugFlow(order_of_reaction=1, kinetic_constant=0.5)
```

**Constructor parameters:**

| Parameter | Unit | Description |
|-----------|------|-------------|
| `order_of_reaction` | — | `n` in `-rA = k·CA^n` |
| `kinetic_constant` | depends on `n` | `k` in the rate expression |

**Method: `residence_time(output_conversion, input_concentration, input_conversion, epsilon)`**

Returns the residence time τ (s) needed to go from `input_conversion` to `output_conversion`.

| Argument | Symbol | Description |
|----------|--------|-------------|
| `output_conversion` | Xaf | Final fractional conversion |
| `input_concentration` | Ca0 | Feed concentration (mol/L) |
| `input_conversion` | Xai | Inlet conversion (0 for fresh feed) |
| `epsilon` | ε | Fractional volume change `(V_final - V_initial) / V_initial`. Use `0` if no volume change. |

**Physics — what happens inside:**

The design equation for a PFR is:

```
τ = Ca0 · ∫[Xai to Xaf] dXa / (-rA)
```

For a power-law rate `-rA = k · Ca^n = k · Ca0^n · (1-Xa)^n / (1+ε·Xa)^n`, this becomes:

```
τ = (1 / (k · Ca0^(n-1))) · ∫[Xai to Xaf] ((1 + ε·Xa) / (1 - Xa))^n dXa
```

The integral is solved numerically with `scipy.integrate.quad`.

**Where to modify:**
- **Change rate expression**: modify the lambda inside `integrate.quad` in `PlugFlow.residence_time()` (`reactor.py`, line ~69)
- **Add temperature dependence (Arrhenius)**: replace `k` with `k0 * exp(-Ea / (R * T))` and add `T` as a parameter
- **Add multiple reactions**: create a subclass that sums contributions from each reaction

**Example:**

```python
pfr = PlugFlow(order_of_reaction=2, kinetic_constant=0.1)
tau = pfr.residence_time(
    output_conversion=0.90,
    input_concentration=2.0,
    input_conversion=0.0,
    epsilon=0.0,
)
V = pfr.get_volume(
    volumetric_flow=1e-4,
    output_conversion=0.90,
    input_concentration=2.0,
    input_conversion=0.0,
)
```

---

### `StirredTank` — CSTR

Models a perfectly mixed tank reactor. Exit concentration equals tank concentration.

```python
from reactor_simulation import StirredTank

cstr = StirredTank(order_of_reaction=1, kinetic_constant=0.5)
```

Same constructor parameters as `PlugFlow`.

**Method: `residence_time(output_conversion, input_concentration, input_conversion, epsilon)`**

Same signature as `PlugFlow`. Returns the CSTR residence time using the algebraic Damköhler equation (no integration needed):

```
τ = Xaf · ((1 + ε·Xaf) / (1 - Xaf))^n / (k · Ca0^(n-1))
```

**Where to modify:**
- **Change rate law**: replace the return expression in `StirredTank.residence_time()` (`reactor.py`, line ~107)
- **Non-power-law kinetics**: replace `((1 + ε·Xaf) / (1 - Xaf))^n` with the evaluated rate expression at exit conditions

---

### `RecyclePlugFlow` — PFR with Recycle

A PFR where part of the product stream is mixed back into the feed. The recycle ratio `R` controls behavior: `R=0` is a pure PFR, `R→∞` approaches a CSTR.

```python
from reactor_simulation import RecyclePlugFlow

rpfr = RecyclePlugFlow(order_of_reaction=1, kinetic_constant=0.5)
```

**Method: `residence_time(R, initial_concentration, final_conversion)`**

| Argument | Symbol | Description |
|----------|--------|-------------|
| `R` | R | Recycle ratio = (recycle flow) / (product flow) |
| `initial_concentration` | Ca0 | Fresh feed concentration (mol/L) |
| `final_conversion` | Xa_f | Overall final conversion |

The inlet conversion to the PFR section is automatically computed as:

```
Xa_i = R / (R + 1) * Xa_f
```

**Method: `average_rate(R, final_conversion, initial_concentration)`**

Returns the average reaction rate across the reactor. Useful for comparing with CSTR/PFR performance.

**Where to modify:**
- **Rate expression**: modify the lambda in `integrate.quad` inside both `residence_time` and `average_rate` (`reactor.py`, lines ~134 and ~150)

---

## core/kinetics.py

### `Reaction`

Wraps any kinetic expression as a callable object.

```python
from reactor_simulation import Reaction

rxn = Reaction(
    reaction_type="irreversible",
    stoichiometry={"A": -1, "B": 1},
    expression=lambda Ca: 0.5 * Ca,      # first-order rate
    fractional_change=0,
)
rate = rxn.reaction_rate(Ca=1.5)         # → 0.75
```

| Parameter | Description |
|-----------|-------------|
| `reaction_type` | Label string (e.g. `"irreversible"`, `"reversible"`) |
| `stoichiometry` | Dict of species → stoichiometric coefficient |
| `expression` | Callable `f(Ca) → rate`. **This is what you modify to change kinetics.** |
| `fractional_change` | ε for volume change |

**Where to modify:**
- **Rate law**: replace the `expression` lambda. Examples:
  - First order: `lambda Ca: k * Ca`
  - Second order: `lambda Ca: k * Ca**2`
  - Langmuir-Hinshelwood: `lambda Ca: k * Ca / (1 + K * Ca)`
  - Reversible: `lambda Ca: k_f * Ca - k_r * Cb` (needs closure over `Cb`)

---

### `overall_yield_pfr(phi, Ca_0, Ca_f)` and `overall_yield_mfr(phi, Ca_f)`

Module-level functions that compute the overall yield of a desired product.

| Argument | Description |
|----------|-------------|
| `phi` | Callable `φ(Ca) → fractional yield of desired product at concentration Ca` |
| `Ca_0` | Initial concentration |
| `Ca_f` | Final concentration |

```python
from reactor_simulation.core.kinetics import overall_yield_pfr, overall_yield_mfr

phi = lambda Ca: Ca / (Ca + 2.0)   # example selectivity function

yield_pfr = overall_yield_pfr(phi, Ca_0=5.0, Ca_f=1.0)
yield_mfr = overall_yield_mfr(phi, Ca_f=1.0)
```

---

## core/state.py

### `ReactorState`

Holds the current physical state of the reactor. This is the "ground truth" that sensors measure (imperfectly) and actuators modify.

```python
from reactor_simulation import ReactorState

state = ReactorState(n_species=2, n_spatial_points=10)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `n_species` | `1` | Number of chemical species tracked |
| `n_spatial_points` | `1` | Spatial discretization. Use `1` for CSTR, `>1` for discretized PFR |

| Attribute | Default | Units |
|-----------|---------|-------|
| `concentration` | zeros array `(n_species, n_spatial_points)` | mol/L |
| `temperature` | `298.15` | K |
| `pressure` | `101325.0` | Pa |
| `flow_rate` | `0.0` | m³/s |
| `time` | `0.0` | s |

**Key methods:**

| Method | Description |
|--------|-------------|
| `set_concentration(value, species_idx=0, position_idx=0)` | Set concentration of species at position |
| `get_concentration(species_idx=0, position_idx=0)` | Get concentration at position |
| `get_outlet_concentration(species_idx=0)` | Last spatial point (outlet) |
| `get_average_concentration(species_idx=0)` | Spatial average |
| `copy()` | Deep copy of entire state |

**Where to modify:**
- **Add new state variables** (e.g. pH, viscosity): add new attributes in `__init__` and update `copy()`
- **Multi-species tracking**: increase `n_species` and index with `species_idx`
- **Spatial discretization**: increase `n_spatial_points` and implement PDE updates externally

---

## actuators/heater.py

### `Heater`

Converts a power command (W) into actual heat delivered to the reactor, with first-order thermal inertia.

```python
from reactor_simulation import Heater

heater = Heater(max_power=5000.0, efficiency=0.90, time_constant=8.0)
```

| Parameter | Default | Units | Description |
|-----------|---------|-------|-------------|
| `max_power` | `1000.0` | W | Maximum allowed power |
| `min_power` | `0.0` | W | Minimum allowed power |
| `efficiency` | `0.95` | — | Fraction of electrical power converted to heat |
| `time_constant` | `10.0` | s | First-order lag time constant τ |

| Attribute | Description |
|-----------|-------------|
| `power_setpoint` | Commanded power after saturation clipping (W) |
| `actual_power` | Power currently delivered (W), lags behind setpoint |

**Method: `update(dt) → heat_output`**

Advances the heater state one time step. The first-order lag is:

```
α = dt / (τ + dt)
actual_power += α · (power_setpoint - actual_power)
heat_output = actual_power · efficiency
```

**Where to modify:**
- **Change lag model**: replace the first-order lag in `update()` with a second-order system or dead-time model (`heater.py`, line ~66)
- **Add heat loss from element**: subtract a loss term proportional to `actual_power` or element temperature
- **Add on/off hysteresis**: add a `_state` flag that only turns on above a threshold and off below another

---

## actuators/pump.py

### `Pump`

Controls volumetric flow rate with a ramp-rate limit (cannot change instantly).

```python
from reactor_simulation import Pump

pump = Pump(max_flow=5e-4, min_flow=0.0, max_ramp_rate=5e-5)
```

| Parameter | Default | Units | Description |
|-----------|---------|-------|-------------|
| `max_flow` | `0.001` | m³/s | Maximum flow rate |
| `min_flow` | `0.0` | m³/s | Minimum flow rate |
| `max_ramp_rate` | `0.0001` | m³/s² | Maximum rate of change per second |

**Method: `update(dt) → actual_flow`**

Ramp-rate limiting:

```
delta_flow = clip(flow_setpoint - actual_flow, -max_ramp_rate·dt, +max_ramp_rate·dt)
actual_flow += delta_flow
```

**Where to modify:**
- **Faster response**: increase `max_ramp_rate`
- **Add flow noise**: add `rng.normal(0, noise_std)` to the return value in `update()`
- **Add cavitation model**: set `actual_flow = 0` if setpoint drops below a threshold too quickly

---

## control/pid.py

### `PIDController`

Classic PID controller with anti-windup and optional derivative filtering. Always acts on **measured values**, never on true values.

```python
from reactor_simulation import PIDController

pid = PIDController(
    Kp=5.0,
    Ki=0.5,
    Kd=0.1,
    setpoint=380.0,
    output_min=0.0,
    output_max=5000.0,
    derivative_filter_tau=2.0,
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `Kp` | `1.0` | Proportional gain |
| `Ki` | `0.1` | Integral gain |
| `Kd` | `0.01` | Derivative gain |
| `setpoint` | `0.0` | Target value |
| `output_min` | `0.0` | Lower saturation limit |
| `output_max` | `100.0` | Upper saturation limit |
| `derivative_filter_tau` | `0.0` | First-order filter on derivative (0 = no filter) |

**Method: `update(measured_value, dt) → output`**

Full PID with anti-windup back-calculation:

```
error = setpoint - measured_value
P = Kp · error
integral += error · dt  →  I = Ki · integral
D = Kd · d(error)/dt   (optionally filtered)
output = clip(P + I + D, output_min, output_max)

# Anti-windup: if saturated, back-calculate integral
if saturated:
    integral = (output_saturated - P - D) / Ki
```

**Method: `get_components() → {'P': float, 'I': float, 'D': float}`**

Returns the current contribution of each term. Useful for tuning visualization.

**Where to modify:**
- **Change to PI only**: set `Kd=0` or remove the derivative block
- **Add setpoint weighting**: replace `error` in P term with `β·setpoint - measured_value`
- **Add feedforward**: add a `feedforward` argument to `update()` and add it to the output before saturation
- **Change anti-windup strategy**: the current method is back-calculation. Alternative: clamping (`if saturated: integral -= error * dt`)

---

## sensors/thermocouple.py

### `Thermocouple`

Temperature sensor with three imperfections layered in order: thermal lag → calibration bias → Gaussian noise → range saturation.

```python
from reactor_simulation import Thermocouple

tc = Thermocouple(
    noise_std=1.0,
    time_constant=3.0,
    bias=2.5,
    min_temp=250.0,
    max_temp=600.0,
    seed=0,
)
```

| Parameter | Default | Units | Description |
|-----------|---------|-------|-------------|
| `noise_std` | `0.5` | K | Standard deviation of Gaussian noise |
| `time_constant` | `2.0` | s | First-order thermal lag τ |
| `bias` | `0.0` | K | Constant calibration offset |
| `min_temp` | `0.0` | K | Lower measurement limit |
| `max_temp` | `500.0` | K | Upper measurement limit |
| `seed` | `None` | — | Random seed for reproducibility |

**Method: `measure(true_temperature, dt) → measured_temperature`**

```
# 1. Thermal lag (first-order)
α = dt / (τ + dt)
reading += α · (true_temperature - reading)

# 2. Calibration bias
reading_biased = reading + bias

# 3. Gaussian noise
measurement = reading_biased + N(0, noise_std)

# 4. Range saturation
measurement = clip(measurement, min_temp, max_temp)
```

**Method: `get_reading() → float`**

Returns `self.reading + self.bias` — the last filtered+biased value without adding new noise. Safe to call between time steps.

**Where to modify:**
- **Add dead-time delay**: store a `deque` of past readings and return a value from N steps ago
- **Add drift**: accumulate `drift_rate * dt` to `self.reading` each call
- **Non-Gaussian noise**: replace `rng.normal()` with `rng.laplace()` for heavier tails, or add occasional spikes
- **Make bias time-varying**: replace `self.bias` with `self.bias + drift_factor * self.total_time`

---

## sensors/conductivity.py

### `ConductivitySensor`

Estimates concentration by measuring electrical conductivity. Applies a calibration curve, temperature correction, drift, and noise.

```python
from reactor_simulation import ConductivitySensor

sensor = ConductivitySensor(
    calibration_params={'a': 0.1, 'b': 2.0, 'c': 0.05},
    noise_std=0.02,
    temperature_coefficient=0.02,
    reference_temperature=298.15,
    drift_rate=0.001,
    seed=7,
)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `calibration_params` | `{'a':0,'b':1,'c':0}` | Coefficients for `σ = a·C² + b·C + c` |
| `noise_std` | `0.01` | Noise std dev (mS/cm) |
| `temperature_coefficient` | `0.02` | Conductivity change per K above reference (2%/K typical) |
| `reference_temperature` | `298.15` | Calibration temperature (K) |
| `drift_rate` | `0.0` | Drift per hour (mS/cm/h) |
| `seed` | `None` | Random seed |

**Method: `measure(true_concentration, temperature, dt) → conductivity`**

```
σ = a·C² + b·C + c                          # calibration curve
σ *= 1 + temp_coeff · (T - T_ref)           # temperature correction
σ += drift_rate · total_hours               # drift
σ += N(0, noise_std)                        # noise
σ = max(0, σ)                               # physical lower bound
```

**Method: `concentration_from_conductivity(conductivity, temperature) → concentration`**

Inverts the calibration curve. Removes temperature correction and drift, then solves the quadratic `a·C² + b·C + c = σ`.

**Where to modify:**
- **Change calibration curve**: update `calibration_params` (set `a=0` for linear, `a≠0` for quadratic)
- **Change drift model**: replace the linear drift `drift_rate * total_time` with exponential saturation
- **Add cross-sensitivity** to temperature in a non-linear way: modify the `temp_correction` factor
- **Recalibrate at runtime**: call `sensor.recalibrate(new_params)` — this also resets accumulated drift

---

## How to Run Tests

```bash
# From the project root
pytest tests/ -v

# Run a single test file
pytest tests/test_reactor.py -v

# Run with coverage report
pytest tests/ --cov=reactor_simulation --cov-report=term-missing
```

---

## How to Modify a Model — Workflow

1. **Identify the class** using the map above.
2. **Make your change** in the relevant file under `reactor_simulation/`.
3. **Run the tests**: `pytest tests/ -v`. All tests should pass.
4. **Run the SCADA app** to see the effect: `python scada_app/main.py`.

**Example: change the heater from first-order lag to instant response**

In `reactor_simulation/actuators/heater.py`, replace:

```python
# Before (first-order lag)
alpha = dt / (self.time_constant + dt)
self.actual_power += alpha * (self.power_setpoint - self.actual_power)
```

with:

```python
# After (instant)
self.actual_power = self.power_setpoint
```

Then run `pytest tests/test_actuators.py -v` to confirm the heater tests still pass.
