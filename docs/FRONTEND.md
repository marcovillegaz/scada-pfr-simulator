# SCADA Frontend — How It Works

This document explains how the UI is built and how the pieces talk to each other. No deep PyQt knowledge needed.

---

## The Big Picture

The frontend has three layers:

```
┌─────────────────────────────────────────────────────┐
│  UI Layer  (what the user sees and clicks)          │
│  MainWindow → header / diagram / graph / footer     │
├─────────────────────────────────────────────────────┤
│  Engine Layer  (simulation math)                    │
│  SimulationEngine → ticks every 50 ms               │
├─────────────────────────────────────────────────────┤
│  Data Layer  (history and snapshots)                │
│  DataStore → time-series  |  EngineSnapshot → now  │
└─────────────────────────────────────────────────────┘
```

The UI reads from the engine; the engine never knows the UI exists.

---

## Entry Point

```
main.py
  │
  ├── creates QApplication (the PyQt runtime)
  ├── applies the dark stylesheet (styles.py → SCADA_DARK)
  └── creates MainWindow and shows it
```

`main.py` also sets `QT_LOGGING_RULES=qt.svg.warning=false` to silence
benign Qt SVG warnings before Qt is even imported.

---

## MainWindow (app.py)

`MainWindow` is one big QWidget split into three horizontal bands:

```
┌──────────────────────────────────────────────────────┐  ← header (44 px)
│  [Diagram] [Graph] [Table]          PFR Reactor SCADA│
├──────────────────────────────────────────────────────┤
│                                                      │
│               main content area                      │  ← stretches
│         (only one tab visible at a time)             │
│                                                      │
├──────────────────────────────────────────────────────┤  ← footer (50 px)
│  [GO] [RESET]  Speed: ──  Status: …  Sim time: …  [Apply] │
└──────────────────────────────────────────────────────┘
```

### Header
- **Tab buttons** (Diagram / Graph / Table) are plain `QPushButton`s.
  Clicking one calls `_switch_tab(i)`, which changes the visible tab
  AND updates the button style (active = cyan underline).
- The native `QTabWidget` tab bar is hidden — the header buttons replace it.
- The title label sits on the right via `addStretch()`.

### Footer
| Widget         | Purpose                                                        |
| -------------- | -------------------------------------------------------------- |
| GO / STOP      | Starts or stops the simulation timer                           |
| RESET          | Resets the engine and clears the graph                         |
| Speed slider   | Multiplies simulation time-step (1× to 100×)                   |
| Status label   | Shows "Stopped / Running / Ready" in colour                    |
| Sim time label | Shows elapsed simulation seconds                               |
| Apply button   | Reads parameters from the overlay and sends them to the engine |

### The timer
`MainWindow` owns a `QTimer` set to fire every 50 ms (20 Hz).
Each tick:
1. Calls `engine.tick(sim_dt)` — advances the simulation one step.
2. Calls `engine.get_snapshot()` — gets the current state as an `EngineSnapshot`.
3. Passes the snapshot to `_refresh_ui()`, which updates the diagram and graph.

---

## Main Content — Tab Widget

Three tabs share the same area. Only the active one is visible.

```
QTabWidget (tab bar hidden)
  ├── DiagramTab   ← tab 0, shown on startup
  ├── GraphTab     ← tab 1
  └── TableTab     ← tab 2, auto-selected when simulation stops
```

---

## DiagramTab

`DiagramTab` is a thin wrapper. It exists only to give the `PFRDiagramWidget`
a tab-friendly home and to re-expose its public methods one level up:

```
DiagramTab
  └── PFRDiagramWidget  (does all the real work)
        ├── QSvgRenderer  ← renders P&ID.svg onto the canvas
        ├── ReadingsOverlay  ← floating box, top-right # 
        └── ParametersOverlay  ← floating box, bottom-right #
```

### PFRDiagramWidget in detail

**Painting the SVG**

`paintEvent` uses `QSvgRenderer` to draw `P&ID.svg` scaled to fit the widget
while keeping the aspect ratio (letterboxed). The math is in `_transform()`:

```python
scale = min(widget_width / svg_width, widget_height / svg_height)
x_offset = (widget_width  - svg_width  * scale) / 2
y_offset  = (widget_height - svg_height * scale) / 2
```

This gives the pixel position and size of the SVG on screen.

**Floating overlays**

Both overlay boxes are child widgets of `PFRDiagramWidget`.
Every time the widget resizes, `_reposition_overlays()` uses the same
`_transform()` math to pin them to the SVG corners:

- `ReadingsOverlay` → top-right corner of the SVG area
- `ParametersOverlay` → bottom-right corner of the SVG area

Because they are children of the diagram widget, they always appear on top
of the SVG without any Z-order tricks.

**Hitboxes (future feature)**

`_HITBOXES` is a dict of named rectangles in normalised coordinates (0–1).
When the user clicks or hovers on the diagram, `_key_at()` checks if the
click lands inside a hitbox and fires the matching action (e.g., open the
PID tuning dialog). New clickable areas (yellow parameter boxes from the
future P&ID) just need a new entry in that dict.

---

## ReadingsOverlay

A dark `QFrame` with 11 label rows that display live sensor values.

`update_readings(snap: EngineSnapshot)` is called every timer tick
(20 Hz) and refreshes all labels from the snapshot.

```
T_hx  |  T_out  |  Valve  |  Ca_in  |  Cb_in
Ca_out | Cb_out  |  X_out  |  Conductivity  |  u  |  τ
```

---

## ParametersOverlay

A dark `QFrame` with 5 `QDoubleSpinBox` rows (editable inputs).

| Field | Unit shown | Sent to engine as |
| ----- | ---------- | ----------------- |
| Qa    | mL/min     | m³/s              |
| Ca    | mol/L      | mol/L             |
| Qb    | mL/min     | m³/s              |
| Cb    | mol/L      | mol/L             |
| T_sp  | °C         | K                 |

When a spinbox value changes, the box turns white (dirty state) to signal
there are pending unapplied changes.

When the user clicks **Apply** in the footer:
1. `get_params()` reads all spinbox values and converts units.
2. `engine.apply_parameters(params)` updates the running simulation.
3. `mark_clean()` restores the normal dark background on all spinboxes.

---

## How Data Flows — Summary

```
Timer (50 ms)
  │
  ▼
engine.tick(sim_dt)
  │
  ▼
engine.get_snapshot() ──► EngineSnapshot
                               │
              ┌────────────────┤
              │                │
              ▼                ▼
  ReadingsOverlay        GraphTab.update_plots()
  .update_readings()     (reads from DataStore,
  (updates 11 labels)     which the engine fills)
```

```
User clicks Apply
  │
  ▼
ParametersOverlay.get_params()   (reads spinboxes, converts units)
  │
  ▼
engine.apply_parameters(params)  (updates setpoints mid-simulation)
  │
  ▼
ParametersOverlay.mark_clean()   (removes white highlight)
```

```
User clicks GO
  │
  ▼
engine.data_store.clear()        (start fresh)
timer.start()                    (begins 20 Hz ticks)
button label changes to STOP

User clicks STOP
  │
  ▼
timer.stop()
TableTab.update_on_stop()        (loads full log into the table)
_switch_tab(2)                   (jumps to Table view automatically)
```

---

## File Map

```
scada_app/
├── main.py                       Entry point
├── app.py                        MainWindow — layout, timer, wiring
├── styles.py                     Global dark stylesheet
├── constants.py                  Physical defaults and unit conversions
│
├── engine/
│   ├── simulation_engine.py      tick(), apply_parameters(), get_snapshot()
│   └── data_store.py             EngineSnapshot, DataStore (time-series)
│
└── ui/
    ├── panels/
    │   └── readings_panel.py     ReadingsOverlay + ParametersOverlay
    ├── tabs/
    │   ├── diagram_tab.py        Thin wrapper around PFRDiagramWidget
    │   ├── graph_tab.py          pyqtgraph real-time plots
    │   └── table_tab.py          QTableView log
    ├── widgets/
    │   └── pfr_diagram.py        SVG renderer + overlay positioning + hitboxes
    └── dialogs/
        └── pid_dialog.py         PID tuning popup (Kp / Ki / Kd)
```
