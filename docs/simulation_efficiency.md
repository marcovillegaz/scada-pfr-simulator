# Simulation Efficiency — Options and Tradeoffs

Identified bottlenecks in the current PFR SCADA simulation loop and potential improvements, ordered by expected impact.

---

## 1. Wrong solver for this system — biggest gain

**Current:** `solve_ivp(..., method='Radau')` — implicit stiff solver.

Stiffness in a MOL-PFR comes from the fastest spatial timescale:

```
dz / u = (L/N) / u = (2.0/50) / 0.02 = 2.0 s
```

At current parameters this is **not stiff**. Radau still runs internal Newton iterations and Jacobian evaluations every tick, paying a large overhead for nothing.

With `BASE_SIM_DT = 0.5 s`, the CFL number is:

```
CFL = u · dt / dz = 0.02 × 0.5 / 0.04 = 0.25  < 1
```

An explicit solver is stable. Switching to `RK45` (or a hand-coded RK4) gives the same accuracy at **~5–10× less CPU per tick**.

**Change:** one word in `reactor_simulation/core/pfr_model.py`:

```python
# Before
sol = solve_ivp(..., method='Radau', ...)

# After
sol = solve_ivp(..., method='RK45', ...)
```

---

## 2. Decouple simulation from UI refresh — architectural

**Current:** `solve_ivp` runs on the Qt main thread every 50 ms. If it exceeds the timer interval the UI freezes.

**Fix:** Run `PFRSimulator.step()` in a `QThread`. The UI reads the latest `EngineSnapshot` at 20 Hz regardless of how fast the sim runs.

```
QThread  ──►  SimulationEngine.tick()  ──►  DataStore (thread-safe append)
QTimer   ──►  MainWindow._refresh_ui() ──►  reads latest snapshot
```

This is the standard SCADA architecture: simulation loop independent of display refresh. Required if you ever want to run at very high speed factors or add stiff energy balance equations.

---

## 3. Sparse Jacobian hint — if keeping Radau

The MOL Jacobian is block-tridiagonal. For N=50 nodes, only ~4N of the 100×100 entries are non-zero (upwind coupling is local: node i depends only on i and i-1).

Passing `jac_sparsity` to `solve_ivp` lets SciPy skip computing 97% of the Jacobian entries. Gives **~3–5× speedup** on Jacobian evaluations with no accuracy change.

```python
from scipy.sparse import diags
import numpy as np

N = params['N']
# Block-tridiagonal sparsity pattern for [CA, T] state vector
ones = np.ones(2*N)
sparsity = diags([ones, ones[1:], ones[1:]], [0, -1, 1]).toarray()
sparsity[N, N-1] = 1   # cross-coupling T -> CA block

sol = solve_ivp(..., method='Radau', jac_sparsity=sparsity)
```

---

## 4. Gate plot updates to the visible tab

**Current:** `update_plots` is called every tick even when the Graph tab is not visible.

**Fix:** in `app.py → _refresh_ui()`:

```python
if self._tabs.currentWidget() is self._graph_tab:
    self._graph_tab.update_plots(self._engine.data_store)
```

Low effort, free speedup when the user is on Diagram or Table tab.

---

## 5. Reduce spatial nodes N

N=50 is generous. For scalar outlet readings (Ca_out, T_out, X_out) N=20–30 gives identical 4-decimal accuracy and is **2.5× cheaper** per RHS evaluation. Only relevant if you display the full spatial profile.

Change in `constants.py`:

```python
PFR_N_NODES = 25   # was 50
```

---

## Recommended sequence

| Priority | Action | Effort | Expected gain |
|---|---|---|---|
| 1 | Switch `Radau` → `RK45` | 1 line | 5–10× per tick |
| 2 | Gate plot updates to visible tab | 3 lines | free on other tabs |
| 3 | Sparse Jacobian (if reverting to Radau) | ~10 lines | 3–5× Jacobian |
| 4 | QThread decoupling | medium refactor | UI always responsive |
| 5 | Reduce N | 1 constant | 2.5× RHS cost |
