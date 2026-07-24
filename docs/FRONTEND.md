# SCADA Frontend — How It Works

This document explains the UI architecture, how each simulation engine ticks,
and how data flows from physics to screen.

**ChemEng SimLab** hosts multiple teaching modules behind one shell: a landing
screen where the student picks a module, and a per-module *workspace* that
owns that module's engine, tabs and controls. Today there are two modules —
**PFR** (plug-flow saponification reactor) and **RTD** (residence-time-
distribution / CIP tracer experiment) — with more planned.

See [BACKEND.md](BACKEND.md) and [MATH.md](MATH.md) for the PFR physics
package and governing equations, and [FUNDAMENTS_EXP3.md](FUNDAMENTS_EXP3.md)
for the RTD/CIP experiment's theory (moments, one-parameter models, the
hidden compartment-network ground truth).

---

## The Big Picture

The frontend has four layers:

```
┌──────────────────────────────────────────────────────────────┐
│  Shell Layer  (app chrome + routing)                         │
│  MainWindow → QStackedWidget → HomeScreen | Workspace | About │
├──────────────────────────────────────────────────────────────┤
│  UI Layer  (what the user sees and clicks, per workspace)    │
│  PFRWorkspace / RTDWorkspace → tabs → dialogs → widgets       │
├──────────────────────────────────────────────────────────────┤
│  Engine Layer  (simulation math, 20 Hz)                      │
│  PFREngine / RTDEngine → tick() → *Snapshot            │
├──────────────────────────────────────────────────────────────┤
│  Data Layer  (history and current state)                     │
│  DataStore (time-series ring buffer) | EngineSnapshot/RTDSnapshot │
└──────────────────────────────────────────────────────────────┘
```

The UI reads from the engine; the engine never knows the UI exists. Each
workspace owns its own engine instance and timer — the two modules never
share simulation state, only the shell chrome (window, routing) and a
handful of generic widgets (`DiagramBox`, `EventLogPanel`).

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

## App Shell — `app.py`

`MainWindow` (`QMainWindow`) is a thin shell: it owns only window chrome
(title, min/preferred size, screen-fit sizing, F11 fullscreen) and a
`QStackedWidget` of top-level pages. All simulation-specific logic —
timers, tabs, dialogs, engines — lives one level down, inside the
workspaces.

```python
self._stack = QStackedWidget()
self.setCentralWidget(self._stack)

self._home  = HomeScreen()
self._pfr   = PFRWorkspace()
self._rtd   = RTDWorkspace()
self._about = AboutView()

self._idx_home  = self._stack.addWidget(self._home)
self._idx_pfr   = self._stack.addWidget(self._pfr)
self._idx_rtd   = self._stack.addWidget(self._rtd)
self._idx_about = self._stack.addWidget(self._about)
```

All four pages are constructed up front (not lazily) and simply swapped via
`setCurrentIndex`. Navigation is entirely signal-driven — `MainWindow` wires
each page's request signal to a stack-index change, it never pokes into a
page's internals:

| Signal | Emitted by | Effect |
|---|---|---|
| `pfr_requested` | `HomeScreen` | `_stack.setCurrentIndex(self._idx_pfr)` |
| `rtd_requested` | `HomeScreen` | `_stack.setCurrentIndex(self._idx_rtd)` |
| `about_requested` | `HomeScreen` | `_stack.setCurrentIndex(self._idx_about)` |
| `home_requested` | `PFRWorkspace`, `RTDWorkspace`, `AboutView` | `_show_home()` → back to `HomeScreen` |

There is no `pfr_requested`/`rtd_requested` signal on the workspaces or on
`AboutView` — the only way back from any of the three non-home pages is
`home_requested`, i.e. every page other than Home is a dead end that returns
to Home rather than linking sideways to a sibling page.

### HomeScreen (`ui/home_screen.py`)

Landing screen: a title/subtitle and a row of three clickable `_Card`
tiles (`QFrame` subclasses with a `clicked` signal) — **PFR — Saponification
Reactor**, **RTD — Experiencia 3**, and **About**. Each card's `clicked`
signal is connected directly to the matching `*_requested` signal on
`HomeScreen` itself. Cards can be constructed `enabled=False` (greyed out,
inert to clicks) for modules that aren't ready yet — currently all three are
enabled.

### AboutView (`ui/about_view.py`)

About is **shell-level**, not a PFR-only tab anymore. `AboutView` is a small
wrapper: a 44 px header with a single "≡ Home" button (emits
`home_requested`) plus the existing `AboutTab` (`ui/tabs/about_tab.py`,
unchanged — author/contact, purpose, license, citation, version history)
filling the rest of the page. It is only reachable from `HomeScreen`'s About
card; neither workspace links to it directly.

### Pausing on navigation

Both workspaces expose a `pause()` method that stops the simulation timer if
it's running, called from their own `_on_home_clicked()` handler before
emitting `home_requested`. This means leaving to Home always stops a running
simulation — the student never returns to a workspace with a run that kept
ticking unattended in the background.

---

## PFR Workspace — `workspaces/pfr_workspace.py`

`PFRWorkspace` is essentially the old `MainWindow` content moved one level
down: it owns the `PFREngine`, the 20 Hz `QTimer`, and its own
header/tabs/footer. Structurally it is a `QWidget` split into three
horizontal bands:

```
┌──────────────────────────────────────────────────────────────────┐  ← header (44 px)
│  ≡ Home │ [Diagram] [Graph] [Table] [Docs] [Admin]  ChemEng SimLab │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│              main content area (one tab visible)                 │  ← stretches
│                                                                    │
├──────────────────────────────────────────────────────────────────┤  ← footer (50 px)
│  [GO/STOP]  [RESET]  Speed: ──  Status: …  Sim time: …  [Apply]   │
└──────────────────────────────────────────────────────────────────┘
```

### Header

A "≡ Home" button (calls `pause()` then emits `home_requested`) followed by
four `QPushButton` tab selectors — **Diagram / Graph / Table / Docs** — plus
a fifth, **Admin**, which is password-gated (see below). Clicking a tab
button calls `_switch_tab(i)`, which changes the visible tab and restyles
the active button (cyan underline). The native `QTabWidget` tab bar is
hidden — header buttons replace it. `About` is **not** one of these buttons
any more; it moved to shell level (see App Shell above).

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

`PFRWorkspace` owns a `QTimer` set to fire every `TIMER_INTERVAL_MS` = 50 ms
(20 Hz). Each tick (`_on_timer_tick`):
1. `engine.tick(sim_dt)` — advances the simulation by `BASE_SIM_DT × speed`.
2. `engine.get_snapshot()` — reads the current `EngineSnapshot`.
3. `_refresh_ui(snap)` — updates live diagram readings every tick (so alarms
   stay live), but throttles the expensive plot redraw (`GraphTab` /
   `AdminTab`) to every other tick (~10 Hz) and only for the **currently
   visible** tab.

### Admin gating

The Admin tab button starts as `"Admin [locked]"`. Clicking it opens a
`QInputDialog` password prompt (password: **12345**); on success
`_admin_unlocked` is set for the remainder of the session, the button label
drops to `"Admin"`, and the tab switches. Unlocking persists for the life of
the `PFRWorkspace` instance (i.e. until the app restarts) — leaving to Home
and coming back does not re-lock it.

### Tab Overview

```
QTabWidget (tab bar hidden — replaced by header buttons)
  ├── 0  DiagramTab   ← P&ID with inline editing and event log
  ├── 1  GraphTab     ← 2×2 real-time pyqtgraph plots
  ├── 2  TableTab     ← student data table, auto-shown on STOP
  ├── 3  DocsTab      ← in-app documentation (6 sub-tabs)
  └── 4  AdminTab     ← password-protected; conversion plot + full variable table
```

### Tab 0 — DiagramTab

Thin wrapper around `PFRDiagramWidget`. Re-exposes its public methods one
level up.

#### PFRDiagramWidget (`ui/widgets/pfr_diagram.py`)

Renders the P&ID SVG (`images/pfr/diagram.svg`), positions clickable
`DiagramBox` widgets over equipment, and displays live sensor readings as
inline editable labels.

**SVG rendering:**
`paintEvent` uses `QSvgRenderer` to draw the diagram letterboxed in the
widget. `_transform()` computes the scale and offsets:

```python
scale    = min(widget_w / svg_w, widget_h / svg_h)
x_offset = (widget_w − svg_w * scale) / 2
y_offset = (widget_h − svg_h * scale) / 2
```

**Hitboxes and DiagramBox widgets:**
`_HITBOXES` is a dict of named rectangles in normalised (0–1) coordinates.
PNG masks in `images/pfr/masks/` define the pixel shape of each clickable
region. On click or hover, `_key_at()` identifies the hitbox and fires the
matching action (open a dialog, highlight a parameter box, etc.).

`DiagramBox` (also defined in this file) sits directly on the SVG canvas at
positions derived from `_transform()`. It shows live readings (conductivity,
temperatures, flow, setpoint) and turns white/orange-tinted when the user
edits a value pending Apply. `RTDDiagramWidget` reuses this same class for
its one editable flow box and its read-only absorbance readout — see the
RTD Workspace section below.

**Status card** (`ui/widgets/status_card.py`): a compact summary widget in
the diagram corner showing current alarms and run state.

**Alarm indicator** (`ui/widgets/alarm_indicator.py`): per-variable coloured
indicator — green (normal), yellow (warning), red (alarm).

**Event log panel** (`ui/widgets/event_log_panel.py`): unbounded scrolling
log of all parameter changes and alarm transitions. Alarm entries use 0.5 °C
/ 0.02 hysteresis deadband to suppress chatter from sensor noise. This
widget is shared with the RTD workspace, but only for manual `add_event()`
calls — its automatic `update_readings()` alarm-detection path (driven by
`EngineSnapshot`-specific thresholds) is PFR-only and is simply never
invoked from `RTDWorkspace`.

### Tab 1 — GraphTab (`ui/tabs/graph_tab.py`)

2×2 pyqtgraph grid, redrawn at ~10 Hz only when visible:

| Position | Plot | Curves |
|---|---|---|
| Top-left | Temperature | T_in, T_out, T_reactor + **setpoint line**; per-curve visibility checkboxes |
| Top-right | Valve % | HX valve opening (0–100 %) |
| Bottom-left | Feed flows | Qa0, Qb0, Q_in |
| Bottom-right | Conductivity + inlet concentrations | CT-101 (left axis), CA_in / CB_in (right twin axis) |

All plots use `setDownsampling(auto, peak)` and `setClipToView(True)` for
performance.

### Tab 2 — TableTab (`ui/tabs/table_tab.py`)

`QTableView` backed by `LogTableModel` (`models/log_table_model.py`), using
its default `STUDENT_COLUMNS`.

- **Student columns:** time, Ca_in, Cb_in, Qa0, Qb0, T_in, T_out, T_reactor,
  valve, conductivity
- **Flow display:** all flows stored in m³/s internally; per-column scale
  factors display them in mL/min in the table
- **Auto-shown** when simulation stops (`_switch_tab(2)` called on STOP)
- **Export:** CSV or Excel via toolbar buttons

`LogTableModel` is generic over any snapshot dataclass — it reads columns
via `getattr(snap, attr)` — so the same class also backs `RTDTableTab` with
a different column set (`RTD_COLUMNS`, see RTD Workspace below).

### Tab 3 — DocsTab (`ui/tabs/docs_tab.py`)

Six `QTextBrowser`-style sub-tabs of in-app documentation:

1. User Guide
2. Mass Balance
3. Energy Balance
4. Kinetics
5. Control Loop
6. Sensors

### Tab 4 — AdminTab (`ui/tabs/admin_tab.py`)

Password-protected (see "Admin gating" above). Unlocked once per session.

Left panel: Conversion vs time plot with twin axis for `CA_in` / `CB_in`.
Right panel: full internal variable table (all `EngineSnapshot` fields,
`ADMIN_COLUMNS`) with CSV / Excel export.

### About — moved out

`AboutTab` (`ui/tabs/about_tab.py`) still exists and is unchanged in
content, but `PFRWorkspace` no longer hosts it as a tab. It is now reached
only via the shell-level `AboutView` from `HomeScreen`'s About card (see App
Shell section).

### Dialogs (`ui/dialogs/`) — PFR

Opened by clicking hitboxes on the PFR P&ID diagram:

| Dialog | File | Opens when clicking |
|---|---|---|
| `PIDDialog` | `pid_dialog.py` | Temperature controller (TIC-101) |
| `ReactorDialog` | `reactor_dialog.py` | PFR tube (reactor body hitbox) |
| `SensorDialog` | `sensor_dialog.py` | CT-101 conductivity transmitter |
| `HXDialog` | `hx_dialog.py` | Heat exchanger (HX-101) |
| `TCDialog` | `tc_dialog.py` | TE-101 / TE-102 thermocouple elements |

Each dialog reads current engine state on open and calls
`engine.apply_parameters()` on Accept.

### Simulation Engine Tick — `engine/pfr_engine.py`

`PFREngine.tick(sim_dt)` is called 20 Hz and executes the full
physics loop in this order:

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

### EngineSnapshot — `engine/data_store.py`

A frozen `dataclass` produced every PFR tick and stored in `DataStore` (a
`deque` of length `PLOT_BUFFER_SIZE = 24000` ≈ 20 min at 20 Hz):

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
| `CA_profile`, `CB_profile`, `T_profile` | mol/L / K | Full spatial profiles (N = 50 points) |

`DataStore.to_dataframe()` (scalar columns only, profiles excluded) is
specific to `EngineSnapshot`'s field set — it is PFR-only. `RTDTableTab`
builds its own dataframe instead of reusing it (see below).

---

## RTD Workspace — `workspaces/rtd_workspace.py`

`RTDWorkspace` is the new second module — a residence-time-distribution
(RTD) tracer experiment framed as a **CIP (Clean-In-Place) validation**
task: the student isolates one of three parallel packed-bed reactors
(R-102 / R-103 / R-104) for washing, injects a tracer (pulse or step), and
reads the outlet absorbance curve back from photocolorimeter AT-101 to
diagnose the reactor's hidden hydrodynamic state (channeling, dead zones).

It structurally mirrors `PFRWorkspace` — own engine, own 20 Hz `QTimer`,
own header/tabs/footer, same Home-button pattern — but adapted for
injection *actions* instead of continuous setpoints, and for a
reactor-selection step that has no PFR equivalent.

```
┌──────────────────────────────────────────────────────────────────┐  ← header (44 px)
│  ≡ Home │ [Diagram] [Graph] [Table] [Docs]   CIP Protocol — Exp. 3 │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│              main content area (one tab visible)                 │  ← stretches
│                                                                    │
├──────────────────────────────────────────────────────────────────┤  ← footer (50 px)
│  [GO/STOP]  [RESET]  Speed: ──  Status: …  Sim time: …  [Apply]   │
└──────────────────────────────────────────────────────────────────┘
```

There is no Admin tab and no per-tab password gate in RTD — the hidden
ground truth is protected structurally instead, at the scenario-loading
layer (see below), not by a UI lock.

### Tab Overview

```
QTabWidget (tab bar hidden — replaced by header buttons)
  ├── 0  RTDDiagramTab  ← CIP P&ID + reactor selection + tracer injection + event log
  ├── 1  RTDGraphTab    ← single absorbance-vs-time pyqtgraph plot
  ├── 2  RTDTableTab    ← student data table, auto-shown on STOP
  └── 3  RTDDocsTab     ← in-app documentation (7 sub-tabs)
```

### Tab 0 — RTDDiagramTab (`ui/tabs/rtd_diagram_tab.py`)

Same left-diagram / right-sidebar layout as `DiagramTab`, but the sidebar
stacks three widgets instead of one:

```
┌───────────────────────────────┬───────────────┐
│                                │  CIPPanel     │
│                                ├───────────────┤
│      RTDDiagramWidget          │  Injection    │
│      (P&ID, stretch=1)         │  Panel        │
│                                ├───────────────┤
│                                │  EventLogPanel│
│                                │  (stretch=1)  │
└───────────────────────────────┴───────────────┘
```

- **CIPPanel** (`ui/widgets/cip_panel.py`) — one toggle button per reactor
  (R-102/R-103/R-104) to isolate it for washing, plus a status label.
  Selecting a reactor is the CIP equivalent of an old scenario picker: it
  switches which packed-bed model the `RTDEngine` runs and which CIP SVG
  diagram is shown. Clicking the already-active reactor deselects it,
  returning to *normal operation* (all three reactors online, no injection
  possible). **Note:** CIPPanel only contains reactor-selection buttons and
  the status label — it has no "wash"/"Inject Washing Substance" button;
  tracer injection is entirely handled by `InjectionPanel`.
- **InjectionPanel** (`ui/widgets/injection_panel.py`) — tracer injection
  controls: a dose spinbox (mg) + "Inject Pulse" button, and a
  concentration spinbox (mg/L) + "Start Step"/"Stop Step" toggle button.
  Deliberately a sidebar panel rather than a diagram overlay, since these
  are momentary actions, not editable setpoints — they don't fit the
  diagram's Apply-pending `DiagramBox` pattern. Disabled as a whole while no
  reactor is selected (`set_injection_enabled(False)`); the pulse button
  specifically is also disabled while any injection is already in progress
  (driven every tick from `RTDSnapshot.injecting`).
- **EventLogPanel** — same shared widget as PFR's Diagram tab, used here
  only via manual `add_event()` calls (see PFR Workspace section above).

#### RTDDiagramWidget (`ui/widgets/rtd_diagram.py`)

Renders the CIP P&ID SVG and reuses `DiagramBox` from `pfr_diagram.py` for
its one editable value (flow, L/min) and one read-only value (AT-101
absorbance reading). It differs from `PFRDiagramWidget` in a few ways:

- **Multiple SVG renderers, not one.** `self._renderers` is a dict keyed by
  mode: `''` → `images/rtd/rtd_normal_operation.svg` (all reactors online),
  plus one renderer per reactor scenario →
  `images/rtd/cip_r10{2,3,4}.svg`. `set_mode(scenario_id)` swaps which
  renderer is active and shows/hides the flow box (only present as artwork
  on the CIP diagrams, not on the normal-operation view).
- **A wash-valve overlay.** `images/rtd/overlay_v106_green.svg` is painted
  on top of the active CIP diagram whenever an injection is in progress
  (`_wash_valve_active`, driven from `RTDSnapshot.injecting`).
- **Reactor-selection and sensor hitboxes are click-through info, not
  editable boxes.** Clicking a reactor body or the AT-101 bubble emits
  `reactor_info_requested(scenario_id)` / `sensor_info_requested()` to open
  that equipment's info dialog — mirrors `PFRDiagramWidget`'s hitbox
  pattern, but reactor *selection* for CIP happens through `CIPPanel`'s
  buttons in the sidebar, not by clicking the diagram.
- **A cosmetic tracer-band overlay.** `start_band()` / `advance_band()` /
  `start_drain()` / `clear_band()` animate a coloured band moving through
  the active reactor's body, timed purely by the nominal `tau = V/Q` (both
  visible quantities) — never by the hidden RTD shape, so it cannot leak
  dead-zone/bypass truth. A `'pulse'` band rides left-to-right once and
  disappears past `progress ≥ 1.2`; a `'step'` band fills from the inlet and
  holds at full; a `'drain'` band empties back out after the step stops.

### Tab 1 — RTDGraphTab (`ui/tabs/rtd_graph_tab.py`)

Single pyqtgraph plot — absorbance A(t) from AIT-101 — rather than PFR's
2×2 grid, since RTD has only one measured channel. Uses a much wider
default window (`_DEFAULT_WINDOW_S = 1800` s) than PFR's graph, because RTD
runs span several τ (~100 s each). Same `setDownsampling`/`setClipToView`
performance pattern; a "Reset View" button re-enables y autorange.

### Tab 2 — RTDTableTab (`ui/tabs/rtd_table_tab.py`)

`QTableView` backed by the same `LogTableModel` class as PFR's `TableTab`,
but constructed with `RTD_COLUMNS` instead of `STUDENT_COLUMNS`
(`LogTableModel` is generic over any snapshot type via `getattr()`).
`DataStore.to_dataframe()` is likewise generic (derives columns from
whichever Snapshot dataclass the store holds, via `dataclasses.fields()`),
so `RTDTableTab` calls it directly for export. Export: CSV or Excel, same
as PFR.

### Tab 3 — RTDDocsTab (`ui/tabs/rtd_docs_tab.py`)

Seven sub-tabs, structurally mirroring `docs_tab.py`'s pattern (section-card
groups inside a scroll area), sourced from `docs/FUNDAMENTS_EXP3.md`:

1. User Guide
2. Fundamentos (age/residence time, the two ideal limiting cases)
3. Estímulo–Respuesta (pulse vs. step injection theory)
4. Medición (Lambert–Beer, AT-101 calibration/noise/saturation)
5. Momentos y Diagnóstico (first/second moments, qualitative signatures)
6. Modelos de Un Parámetro (tanks-in-series, axial dispersion)
7. Compartimientos y Datos (combined-model concept + full data-processing sequence)

Deliberately teaches the general RTD analysis toolkit without exposing the
simulator's hidden per-reactor parameters — those stay behind `Scenario`'s
visible/oculto split no matter how much theory surrounds them (see
Scenario Loading below).

### Dialogs (`ui/dialogs/`) — RTD

| Dialog | File | Opens when clicking |
|---|---|---|
| `RTDReactorInfoDialog` | `rtd_reactor_dialog.py` | Any reactor body (R-102/103/104), whether or not it's currently selected for CIP |
| `RTDSensorInfoDialog` | `rtd_sensor_dialog.py` | AT-101 photocolorimeter bubble |

Both are read-only nameplate/instrument-data dialogs (no Apply/parameter
path — RTD has nothing analogous to PFR's editable PID/HX/reactor dialogs).
`RTDReactorInfoDialog` loads its scenario fresh via `load_scenario()` rather
than reading `RTDEngine`'s currently-active scenario, so a student can
inspect any of the three columns' nameplate data without first selecting it
for CIP.

### RTD Engine Tick — `engine/rtd_engine.py`

`RTDEngine.tick(sim_dt)` is the RTD analogue of `PFREngine.tick()`.
It advances the hidden-truth `PackedBedRTD` model (from
`reactor_simulation.models.packed_bed`) with the tracer inlet concentration as the
boundary condition that changes tick to tick — the same segmented-
integration pattern the PFR uses for temperature/flow setpoints, applied
here to injections:

```
1. If a rectangular pulse is active (self._pulse_remaining > 0):
     this_dt = min(sim_dt, pulse_remaining)
     pulse_remaining -= this_dt
     c_out = model.step(this_dt, injection_c_in)
     if pulse_remaining <= 0:
         # Pulse ends inside this tick — integrate the remainder at
         # c_in = 0 so the rectangular pulse width stays exact regardless
         # of tick granularity.
         injection_c_in = 0.0
         injecting = False
         c_out = model.step(sim_dt - this_dt, 0.0)   # if remainder > 0
   Else (no active pulse — normal operation or an open step injection):
     c_out = model.step(sim_dt, injection_c_in)

2. Sensor sampling
     absorbance = photocolorimeter.sample(c_out, sim_dt)
     (Lambert–Beer A = ε·b·C + Gaussian noise, clipped at A_max)

3. Package RTDSnapshot and append to DataStore
```

**Injection API** (called from `RTDWorkspace`'s sidebar signal handlers):

| Method | Effect |
|---|---|
| `inject_pulse(m, t_pulse=RTD_PULSE_WIDTH_S)` | Rectangular pulse: sets `injection_c_in` via `pulse_concentration(m, Q, t_pulse)`, arms `_pulse_remaining = t_pulse` |
| `inject_step(C0)` | Opens the tracer feed: constant `injection_c_in = C0` until `stop_injection()` |
| `stop_injection()` | Zeroes `injection_c_in`, clears any pending pulse, `injecting = False` |

**Parameter/scenario API:**

| Method | Effect |
|---|---|
| `apply_parameters({'Q_L_min': v})` | `model.set_flow(v / 60)` — updates the visible flow setpoint (L/min → L/s) |
| `set_scenario(scenario_id)` | Reloads `Scenario`, rebuilds the hidden model, resets the run |
| `reset()` | Stops any injection, rebuilds model + sensor, clears `DataStore` |

Two read-only properties expose visible-only derived quantities to the UI:
`Q_L_s` (current flow, for the diagram's flow display after a scenario load
or reset) and `tau` (nominal `V/Q`, used only to time the cosmetic
tracer-band animation — never derived from the hidden RTD shape).

### RTDSnapshot — `engine/data_store.py`

A frozen `dataclass` produced every RTD tick and stored in the same
`DataStore` class PFR uses (generic ring buffer):

| Field | Unit | Description |
|---|---|---|
| `sim_time` | s | Simulation elapsed time |
| `Q` | L/s | Current flow rate (visible) |
| `absorbance` | — | AIT-101 reading (Photocolorimeter output) |
| `injecting` | bool | Whether a pulse or step injection is in progress |

`RTDSnapshot` is deliberately minimal — it carries no true concentration or
hidden-model field, only what the student is meant to see (mirrors
`docs/PLAN.md` §5.4's `GET /rtd/state: t, Q, A`). There is no path from a
snapshot back to the hidden compartment-network truth.

### Scenario Loading — `scenarios/loader.py`, `scenarios/__init__.py`

RTD scenarios are JSON files under `scada_app/scenarios/plants/*.json`
(`planta_a` / `planta_b` / `planta_c`, one per CIP-isolable reactor), plus a
shared `scada_app/scenarios/sensor.json` for the one physical AT-101
instrument. Each JSON file is split into a `visible` block and an `oculto`
(hidden) block, and — critically — the split is enforced by **API shape**,
not just by naming convention:

- `Scenario` (returned by `load_scenario()` / `list_scenarios()`) carries
  only `visible` data (`ScenarioVisible` → `ScenarioReactor` +
  `ScenarioSensor`). There is no attribute path from a `Scenario` instance
  to `oculto` — there is no leak to plug because there is no path.
- `build_rtd_model(scenario_id)` is the **only** function allowed to read
  `oculto`. It reads the hidden hydrodynamic parameters (`f`, `phi_d`,
  `k_ex`, `gamma`, `N_m`, `N_c`) directly into a `PackedBedRTD` instance and
  returns the model — the raw values never leave the function as data.
- `sensor_seed()` is a narrow, deliberate exception: `Photocolorimeter`
  needs an RNG seed for reproducible-but-secret measurement noise, so it's
  exposed on its own rather than folded into `Scenario`. It always reads
  `sensor.json`'s `oculto.seed` — one instrument-level seed shared by all
  three reactors (not a per-plant value), so it stays out of student reach
  regardless of which reactor is under study.

```python
@dataclass(frozen=True)
class ScenarioReactor:      # V_L, Q_nominal_L_min
class ScenarioSensor:       # epsilon_b, A_max, dt_sample_s, noise_std
class ScenarioVisible:      # reactor: ScenarioReactor, sensor: ScenarioSensor
class Scenario:              # id, nombre, visible: ScenarioVisible — no hidden path
```

Public functions: `load_scenario(scenario_id)`, `load_sensor()`,
`list_scenarios()` (all visible-only, safe to hand to UI code directly),
`build_rtd_model(scenario_id)` and `sensor_seed()` (the only two functions
that ever touch `oculto`). `tests/test_rtd_scenario_integrity.py` contains
structural checks that back this separation up (e.g. asserting `Scenario`
has no attribute path to hidden fields).

`RTDEngine` is the sole consumer of `build_rtd_model()` and `sensor_seed()`
— the UI layer (workspace, tabs, dialogs) only ever touches `Scenario` and
its visible sub-dataclasses.

---

## Data Flow Summary

### Shell navigation

```
HomeScreen card clicked
  │
  ├── pfr_requested / rtd_requested / about_requested
  └── MainWindow._stack.setCurrentIndex(...)   ← swaps the visible page

Workspace/About "≡ Home" button clicked
  │
  ├── workspace.pause()            (stops the timer if running)
  └── home_requested → MainWindow._show_home()
```

### PFR tick loop

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

### RTD tick loop

```
QTimer (50 ms / 20 Hz)
  │
  ├──► engine.tick(sim_dt)
  │         └── produces RTDSnapshot → appended to DataStore
  │
  └──► _refresh_ui(snap)
            ├── RTDDiagramTab.update_readings(snap)   ← absorbance label, wash overlay, every tick
            ├── RTDDiagramTab.advance_band(sim_time)  ← cosmetic tracer-band animation, every tick
            ├── CIPPanel status text                  ← "washing"/"idle", every tick while a reactor is active
            └── RTDGraphTab.update_plots(data_store)  ← only if tab visible, ~10 Hz
```

```
User clicks a CIP reactor button (R-102/103/104)
  │
  ├── CIPPanel.reactor_selected(scenario_id)   ('' if deselecting)
  ├── engine.set_scenario(scenario_id)         (reloads Scenario, rebuilds hidden model, resets run)
  ├── RTDDiagramTab.set_mode(scenario_id)       (swaps CIP SVG, shows/hides flow box)
  └── RTDDiagramTab.set_injection_enabled(True) (InjectionPanel becomes usable)
```

```
User sets dose/C0 → clicks Inject Pulse / Start Step
  │
  ├── InjectionPanel.pulse_requested(dose) / step_start_requested(C0)
  ├── engine.inject_pulse(dose) / engine.inject_step(C0)
  └── RTDDiagramTab.start_band('pulse'|'step', sim_time, engine.tau)
```

```
User clicks STOP
  │
  ├── timer.stop()
  ├── RTDTableTab.update_on_stop()      (loads full DataStore → QTableView)
  └── _switch_tab(2)                    (auto-jumps to Table)
```

---

## File Map

```
scada_app/
│
├── main.py                        Entry point; SCADA_SELFTEST hook
├── app.py                         MainWindow — shell chrome, QStackedWidget routing
├── styles.py                      Global dark stylesheet (SCADA_DARK)
├── constants.py                   All physical constants and UI defaults (PFR + RTD/CIP)
├── resources.py                   resource_path() — dev/frozen asset resolution
│
├── engine/
│   ├── pfr_engine.py       PFREngine: tick(), apply_parameters(), reset() (PFR)
│   │                              HXDynamic (analytic HX model, inline)
│   ├── rtd_engine.py              RTDEngine: tick(), inject_pulse()/inject_step()/stop_injection(),
│   │                              apply_parameters(), set_scenario(), reset() (RTD)
│   └── data_store.py              EngineSnapshot, RTDSnapshot (dataclasses), DataStore (deque)
│
├── models/
│   └── log_table_model.py         LogTableModel (QAbstractTableModel, generic via getattr())
│                                  STUDENT_COLUMNS / ADMIN_COLUMNS / RTD_COLUMNS + per-column scale
│
├── scenarios/
│   ├── __init__.py                Re-exports loader's public API
│   ├── loader.py                  Scenario/ScenarioReactor/ScenarioSensor (visible-only dataclasses),
│   │                              load_scenario(), list_scenarios(), build_rtd_model(), sensor_seed()
│   ├── sensor.json                Shared AT-101 visible+oculto settings
│   └── plants/
│       ├── planta_a.json          R-102 scenario (visible + oculto)
│       ├── planta_b.json          R-103 scenario
│       └── planta_c.json          R-104 scenario
│
└── ui/
    │
    ├── home_screen.py              HomeScreen — landing page, module-selector cards
    ├── about_view.py                AboutView — shell-level Home-button wrapper around AboutTab
    │
    ├── panels/
    │   ├── parameters_panel.py    ParametersOverlay (SpinBox panel for Apply) — PFR
    │   └── readings_panel.py      ReadingsOverlay (live numeric label grid) — PFR
    │
    ├── tabs/
    │   ├── diagram_tab.py         Thin wrapper around PFRDiagramWidget
    │   ├── graph_tab.py           2×2 pyqtgraph plots (PFR)
    │   ├── table_tab.py           QTableView + export buttons (PFR, STUDENT_COLUMNS)
    │   ├── docs_tab.py            6 sub-tab documentation browser (PFR)
    │   ├── about_tab.py           Author / license / citation / changelog (hosted by AboutView)
    │   ├── admin_tab.py           Password gate + conversion plot + full table (PFR only)
    │   ├── rtd_diagram_tab.py     P&ID + CIPPanel + InjectionPanel + EventLogPanel (RTD)
    │   ├── rtd_graph_tab.py       Single absorbance-vs-time pyqtgraph plot (RTD)
    │   ├── rtd_table_tab.py       QTableView + export buttons (RTD, RTD_COLUMNS)
    │   └── rtd_docs_tab.py        7 sub-tab documentation browser (RTD)
    │
    ├── widgets/
    │   ├── pfr_diagram.py         PFRDiagramWidget + DiagramBox (shared editable/read-only value box)
    │   ├── rtd_diagram.py         RTDDiagramWidget — multi-mode CIP SVG, tracer-band overlay, reuses DiagramBox
    │   ├── cip_panel.py           CIPPanel — reactor-selection buttons + status label (RTD)
    │   ├── injection_panel.py     InjectionPanel — pulse/step tracer injection controls (RTD)
    │   ├── event_log_panel.py     Unbounded scrolling event log with alarm hysteresis (shared PFR/RTD)
    │   ├── alarm_indicator.py     Per-variable coloured alarm indicator (PFR)
    │   └── status_card.py         Compact run-state + alarm summary card (PFR)
    │
    └── dialogs/
        ├── pid_dialog.py          PID gains + setpoint (TIC-101) — PFR
        ├── reactor_dialog.py      PFR geometry + heat loss parameters — PFR
        ├── sensor_dialog.py       CT-101 conductivity transmitter — PFR
        ├── hx_dialog.py           Heat exchanger (HX-101) — PFR
        ├── tc_dialog.py           TE-101 / TE-102 thermocouple elements — PFR
        ├── rtd_reactor_dialog.py  Reactor nameplate data (R-102/103/104) — RTD, read-only
        └── rtd_sensor_dialog.py   AT-101 photocolorimeter instrument data — RTD, read-only

workspaces/
├── pfr_workspace.py                PFRWorkspace — header/tabs/footer/timer/engine wiring, Admin gate
└── rtd_workspace.py                RTDWorkspace — header/tabs/footer/timer/engine wiring, CIP + injection flow
```
