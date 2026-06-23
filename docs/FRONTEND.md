# SCADA Frontend — How It Works

This document explains the UI architecture, how the simulation engine ticks, and
how data flows from physics to screen.

See [BACKEND.md](BACKEND.md) for the physics package and [MATH.md](MATH.md) for
the governing equations.

---

## The Big Picture

The frontend has three layers:

```
┌──────────────────────────────────────────────────────────┐
│  UI Layer  (what the user sees and clicks)               │
│  MainWindow → 6 tabs → dialogs → widgets                 │
├──────────────────────────────────────────────────────────┤
│  Engine Layer  (simulation math, 20 Hz)                  │
│  SimulationEngine → tick() → EngineSnapshot              │
├──────────────────────────────────────────────────────────┤
│  Data Layer  (history and current state)                 │
│  DataStore (time-series ring buffer) | EngineSnapshot    │
└──────────────────────────────────────────────────────────┘
```

The UI reads from the engine; the engine never knows the UI exists.

---

## Entry Point — `main.py`

```
main.py
  │
  ├── sets QT_LOGGING_RULES=qt.svg.warning=false  (silences benign SVG warnings)
  ├── creates QApplication
  ├── applies dark stylesheet  (styles.py → SCADA_DARK)
  ├── creates MainWindow and shows it
  └── SCADA_SELFTEST env hook:  if set, app.quit() after window creation
                                used to verify the frozen PyInstaller build
```

---

## MainWindow — `app.py`

`MainWindow` is a `QWidget` split into three horizontal bands:

```
┌──────────────────────────────────────────────────────────────┐  ← header (44 px)
│  [Diagram] [Graph] [Table] [Docs] [About] [Admin]  PFR v1.0 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│              main content area (one tab visible)            │  ← stretches
│                                                              │
├──────────────────────────────────────────────────────────────┤  ← footer (50 px)
│  [GO/STOP]  [RESET]  Speed: ──  Status: …  Sim time: …  [Apply] │
└──────────────────────────────────────────────────────────────┘
```

### Header

Six `QPushButton` tab selectors. Clicking one calls `_switch_tab(i)`, which
changes the visible tab and updates the active button style (cyan underline).
The native `QTabWidget` tab bar is hidden — header buttons replace it.

### Footer

| Widget | Purpose |
|---|---|
| GO / STOP | Starts or stops the simulation timer |
| RESET | Resets the engine and clears all plots |
| Speed slider | Multiplies `BASE_SIM_DT` (1× to 100×) |
| Status label | Shows "Stopped / Running / Ready" in colour |
| Sim time label | Shows elapsed simulation seconds |
| Apply | Reads the P&ID parameter overlay and sends values to the engine |

### The Timer

`MainWindow` owns a `QTimer` set to fire every 50 ms (20 Hz). Each tick:
1. `engine.tick(sim_dt)` — advances the simulation by `BASE_SIM_DT × speed`.
2. `engine.get_snapshot()` — reads the current `EngineSnapshot`.
3. `_refresh_ui(snap)` — updates only the **currently visible tab** (performance:
   no idle redraws on hidden tabs). Diagram readings update every tick regardless
   to keep alarms live.

---

## Tab Overview

```
QTabWidget (tab bar hidden — replaced by header buttons)
  ├── 0  DiagramTab   ← P&ID with inline editing and event log
  ├── 1  GraphTab     ← 2×2 real-time pyqtgraph plots
  ├── 2  TableTab     ← student data table, auto-shown on STOP
  ├── 3  DocsTab      ← in-app documentation (6 sub-tabs)
  ├── 4  AboutTab     ← author, license, citation, version history
  └── 5  AdminTab     ← password-protected; conversion plot + full variable table
```

---

## Tab 0 — DiagramTab

Thin wrapper around `PFRDiagramWidget`. Re-exposes its public methods one level up.

### PFRDiagramWidget (`ui/widgets/pfr_diagram.py`)

Renders the P&ID SVG, positions clickable `DiagramBox` widgets over equipment,
and displays live sensor readings as inline editable labels.

**SVG rendering:**
`paintEvent` uses `QSvgRenderer` to draw `diagram.svg` letterboxed in the widget.
`_transform()` computes the scale and offsets:

```python
scale    = min(widget_w / svg_w, widget_h / svg_h)
x_offset = (widget_w − svg_w * scale) / 2
y_offset = (widget_h − svg_h * scale) / 2
```

**Hitboxes and DiagramBox widgets:**
`_HITBOXES` is a dict of named rectangles in normalised (0–1) coordinates.
PNG masks in `images/masks/` define the pixel shape of each clickable region.
On click or hover, `_key_at()` identifies the hitbox and fires the matching action
(open a dialog, highlight a parameter box, etc.).

`DiagramBox` widgets sit directly on the SVG canvas at positions derived from
`_transform()`. They show live readings (conductivity, temperatures, flow, setpoint)
and turn white when the user edits a value pending Apply.

**Status card** (`ui/widgets/status_card.py`): a compact summary widget in the
diagram corner showing current alarms and run state.

**Alarm indicator** (`ui/widgets/alarm_indicator.py`): per-variable coloured
indicator — green (normal), yellow (warning), red (alarm).

**Event log panel** (`ui/widgets/event_log_panel.py`): unbounded scrolling log
of all parameter changes and alarm transitions. Alarm entries use 0.5 °C / 0.02
hysteresis deadband to suppress chatter from sensor noise.

---

## Tab 1 — GraphTab (`ui/tabs/graph_tab.py`)

2×2 pyqtgraph grid, redrawn at ~10 Hz only when visible:

| Position | Plot | Curves |
|---|---|---|
| Top-left | Temperature | T_in, T_out, T_reactor + **setpoint line**; per-curve visibility checkboxes |
| Top-right | Valve % | HX valve opening (0–100 %) |
| Bottom-left | Feed flows | Qa0, Qb0, Q_in |
| Bottom-right | Conductivity + inlet concentrations | CT-101 (left axis), CA_in / CB_in (right twin axis) |

All plots use `setDownsampling(auto, peak)` and `setClipToView(True)` for performance.

---

## Tab 2 — TableTab (`ui/tabs/table_tab.py`)

`QTableView` backed by `LogTableModel` (`models/log_table_model.py`).

- **Student columns:** time, T_in, T_out, T_reactor, valve %, Qa0, Qb0, Q_in,
  CA_in, CB_in, CA_out, CB_out, X_out, conductivity
- **Flow display:** all flows stored in m³/s internally; per-column scale factors
  display them in mL/min in the table
- **Auto-shown** when simulation stops (`_switch_tab(2)` called on STOP)
- **Export:** CSV or Excel via toolbar buttons

---

## Tab 3 — DocsTab (`ui/tabs/docs_tab.py`)

Six `QTextBrowser` sub-tabs of in-app documentation:

1. Model Overview
2. Reaction Kinetics
3. PID Control
4. Sensors
5. How to Use
6. User Guide (Diagram / Graph / Table usability)

---

## Tab 4 — AboutTab (`ui/tabs/about_tab.py`)

Static tab with:
- Author and contact (LinkedIn + email — clickable `QLabel` links)
- Project purpose and tech stack
- Disclaimer
- License (MIT)
- How-to-cite section
- Version history

---

## Tab 5 — AdminTab (`ui/tabs/admin_tab.py`)

Password-protected (password: **12345**). Unlocked once per session.

Left panel: Conversion vs time plot with twin axis for `CA_in` / `CB_in`.
Right panel: full internal variable table (all `EngineSnapshot` fields) with
CSV / Excel export.

---

## Dialogs (`ui/dialogs/`)

Opened by clicking hitboxes on the P&ID diagram:

| Dialog | File | Opens when clicking |
|---|---|---|
| `PIDDialog` | `pid_dialog.py` | Temperature controller (TIC-101) |
| `ReactorDialog` | `reactor_dialog.py` | PFR tube (reactor body hitbox) |
| `SensorDialog` | `sensor_dialog.py` | CT-101 conductivity transmitter |
| `HXDialog` | `hx_dialog.py` | Heat exchanger (HX-101) |
| `TCDialog` | `tc_dialog.py` | TE-101 / TE-102 thermocouple elements |

Each dialog reads current engine state on open and calls `engine.apply_parameters()`
on Accept.

---

## Simulation Engine Tick — `engine/simulation_engine.py`

`SimulationEngine.tick(sim_dt)` is called 20 Hz and executes the full physics
loop in this order:

```
1. Advance any active flow ramps (Qa0, Qb0 ramp linearly over FLOW_RAMP_DURATION = 30 s)

2. Compute mixing node
     Q_in  = Qa0 + Qb0
     CA_in = Ca0 · Qa0 / Q_in   (mol/m³)
     CB_in = Cb0 · Qb0 / Q_in
     u     = Q_in / A_cross      (m/s)

3. HX step (exact analytic solution)
     T_ss = (Q·ρ·cp·T_feed + UA·T_hw) / (Q·ρ·cp + UA)
     T_hx = T_ss + (T_hx_prev − T_ss) · exp(−(Q·ρ·cp + UA)·dt / (V·ρ·cp))
     → T_in = T_hx

4. PFR step (RK45, 3N ODEs: CA, CB, T per node)
     update_params({CA_in, CB_in, T_in, u})
     out = pfr.step(sim_dt)
     → CA_profile, CB_profile, T_profile, CA_out, CB_out, T_out, X_out

5. PID step
     T_reactor = (T_in + T_out) / 2
     valve = pid.update(T_reactor, sim_dt)   → [0.0, 1.0]
     (valve is applied to HX at the NEXT tick via self._prev_valve)

6. Sensors
     CT-101:  conductivity = A · CA_out_L + B + N(0, σ_ct)
     TE-101:  T_in_meas   = T_in  + N(0, σ_te)
     TE-102:  T_out_meas  = T_out + N(0, σ_te)
     (TE readings are shown in the UI; PFR and PID use true values)

7. Package EngineSnapshot and append to DataStore
```

**What the user can change at runtime** (via Apply button or dialogs):

| Parameter | Engine attribute | Ramp? |
|---|---|---|
| Qa0 (feed A flow) | `_Qa0` | Yes — 30 s linear ramp |
| Qb0 (feed B flow) | `_Qb0` | Yes — 30 s linear ramp |
| Ca0 (feed A conc) | `_Ca0` | No (instantaneous) |
| Cb0 (feed B conc) | `_Cb0` | No |
| T setpoint | `_t_sp`, `_pid.setpoint` | No |
| Kp, Ki, Kd | `_pid` gains | No |
| h_loss | `_pfr` params | No |

---

## EngineSnapshot — `engine/data_store.py`

A frozen `dataclass` produced every tick and stored in `DataStore` (a `deque`
of length `PLOT_BUFFER_SIZE = 24000` ≈ 20 min at 20 Hz):

| Field | Unit | Description |
|---|---|---|
| `sim_time` | s | Simulation elapsed time |
| `CA_out`, `CB_out` | mol/L | Outlet concentrations |
| `T_in`, `T_out` | K | **Measured** (noisy) inlet/outlet temperatures |
| `T_reactor` | K | True mean reactor temperature `(T_in_true + T_out_true)/2` |
| `T_setpoint` | K | Current PID setpoint |
| `X_out` | — | NaOH conversion `1 − CA_out/CA_in` |
| `valve` | — | HX valve position [0–1] |
| `Qa0`, `Qb0`, `Q_in` | m³/s | Feed and total flow rates |
| `velocity` | m/s | Superficial velocity in the PFR |
| `conductivity` | mS/cm | CT-101 reading |
| `CA_profile`, `CB_profile`, `T_profile` | mol/m³ / K | Full spatial profiles (N = 50 points) |

---

## Data Flow Summary

```
QTimer (50 ms / 20 Hz)
  │
  ├──► engine.tick(sim_dt)
  │         └── produces EngineSnapshot → appended to DataStore
  │
  └──► _refresh_ui(snap)
            ├── DiagramTab.update_readings(snap)    ← live labels, every tick
            ├── GraphTab.update_plots(data_store)   ← only if tab visible, ~10 Hz
            ├── AdminTab.update_plots(data_store)   ← only if tab visible
            └── StatusCard.update(snap)             ← alarm state
```

```
User edits P&ID box → clicks Apply
  │
  ├── DiagramBox.get_params()          (reads SpinBoxes, converts units)
  └── engine.apply_parameters(params)  (updates engine setpoints, triggers ramps)
```

```
User clicks STOP
  │
  ├── timer.stop()
  ├── TableTab.update_on_stop()        (loads full DataStore → QTableView)
  └── _switch_tab(2)                   (auto-jumps to Table)
```

---

## File Map

```
scada_app/
│
├── main.py                        Entry point; SCADA_SELFTEST hook
├── app.py                         MainWindow — layout, timer, wiring, _refresh_ui
├── styles.py                      Global dark stylesheet (SCADA_DARK)
├── constants.py                   All physical constants and UI defaults
├── resources.py                   resource_path() — dev/frozen asset resolution
│
├── engine/
│   ├── simulation_engine.py       SimulationEngine: tick(), apply_parameters(), reset()
│   │                              HXDynamic (analytic HX model, inline)
│   └── data_store.py              EngineSnapshot (dataclass), DataStore (deque)
│
├── models/
│   └── log_table_model.py         LogTableModel (QAbstractTableModel)
│                                  STUDENT_COLUMNS / ADMIN_COLUMNS + per-column scale
│
└── ui/
    │
    ├── panels/
    │   ├── parameters_panel.py    ParametersOverlay (SpinBox panel for Apply)
    │   └── readings_panel.py      ReadingsOverlay (live numeric label grid)
    │
    ├── tabs/
    │   ├── diagram_tab.py         Thin wrapper around PFRDiagramWidget
    │   ├── graph_tab.py           2×2 pyqtgraph plots
    │   ├── table_tab.py           QTableView + export buttons
    │   ├── docs_tab.py            6 sub-tab documentation browser
    │   ├── about_tab.py           Author / license / citation / changelog
    │   └── admin_tab.py           Password gate + conversion plot + full table
    │
    ├── widgets/
    │   ├── pfr_diagram.py         SVG renderer, hitboxes, DiagramBox positioning
    │   ├── event_log_panel.py     Unbounded scrolling event log with alarm hysteresis
    │   ├── alarm_indicator.py     Per-variable coloured alarm indicator
    │   └── status_card.py         Compact run-state + alarm summary card
    │
    └── dialogs/
        ├── pid_dialog.py          PID gains + setpoint (TIC-101)
        ├── reactor_dialog.py      PFR geometry + heat loss parameters
        ├── sensor_dialog.py       CT-101 conductivity transmitter
        ├── hx_dialog.py           Heat exchanger (HX-101)
        └── tc_dialog.py           TE-101 / TE-102 thermocouple elements
```
