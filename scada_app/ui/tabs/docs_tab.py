from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from constants import CT101_CALIB_A, CT101_CALIB_B, CT101_NOISE_STD
from ui.tabs._docs_helpers import (
    narrative as _narrative,
    equation as _equation,
    tip as _tip,
    section as _section,
    scroll_tab as _scroll_tab,
)


# ── Sub-tab builders ──────────────────────────────────────────────────────────

def _tab_mass_balance() -> QScrollArea:
    mixing = _section(
        "Mixing Node",
        _narrative(
            "Before entering the reactor, the two feed streams — NaOH (Feed A) "
            "and EtAc (Feed B) — are combined at a mixing node. The inlet "
            "concentrations depend on how much of each stream you send: if you "
            "increase Qa0 while keeping Qb0 fixed, you dilute CA_in and the "
            "reaction will slow down."
        ),
        _equation(
            "CA_in = (Ca0 · Qa0) / (Qa0 + Qb0)    [mol/L]\n"
            "CB_in = (Cb0 · Qb0) / (Qa0 + Qb0)    [mol/L]\n"
            "Q_in  =  Qa0 + Qb0                    [mL/min]"
        ),
    )

    pfr = _section(
        "Inside the Reactor — PFR Species Balance",
        _narrative(
            "The reactor is modelled as a plug flow reactor (PFR): fluid moves "
            "along the tube axis without mixing back. At every axial position z, "
            "the concentration changes because (1) the flowing fluid carries "
            "material past that point and (2) the reaction consumes A and B."
        ),
        _equation(
            "∂CA/∂t = −u · ∂CA/∂z  −  rA\n"
            "∂CB/∂t = −u · ∂CB/∂z  −  rA"
        ),
        _narrative(
            "The simulator solves this system using the Method of Lines (MOL): "
            "the tube is divided into N = 50 spatial nodes, each treated as an "
            "ODE in time. Upwind finite differences are used for the spatial "
            "derivative, which is physically correct for convection-dominated flow."
        ),
        _equation(
            "Upwind: ∂CA/∂z|ᵢ = (CA[i] − CA[i−1]) / Δz    Δz = L / N"
        ),
        _tip(
            "Try increasing the flow rate (Qa0 + Qb0): higher velocity u means "
            "shorter residence time → less reaction → lower conversion Xa. "
            "Check the Graph tab to see the effect."
        ),
    )

    conversion = _section(
        "Conversion",
        _narrative(
            "Conversion Xa tells you what fraction of reactant A has been "
            "consumed from inlet to outlet. It is the main performance metric "
            "for the reactor."
        ),
        _equation(
            "Xa = 1  −  CA_out / CA_in"
        ),
    )

    return _scroll_tab(mixing, pfr, conversion)


def _tab_energy_balance() -> QScrollArea:
    hx = _section(
        "Pre-heating — Heat Exchangers E-101 / E-102",
        _narrative(
            "Before mixing, each feed stream passes through a shell-and-tube "
            "heat exchanger that pre-heats it with hot water (60 °C). "
            "TC-101 controls valve V-101 to set the fraction of heat "
            "transferred. The more open the valve, the higher the heat "
            "transfer coefficient UA and the warmer the fluid at the outlet."
        ),
        _equation(
            "UA = UA_max · v(t)         v ∈ [0, 1]  (valve position)\n"
            "\n"
            "T_in(t) = T_ss + (T_in,0 − T_ss) · exp(−b · t / m_cp)\n"
            "  b    = Q_in · ρ · cp  +  UA\n"
            "  T_ss = (Q_in · ρ · cp · T_amb  +  UA · T_hw) / b"
        ),
        _tip(
            "T_ss is the steady-state temperature the HX would reach if "
            "conditions stayed fixed. Higher valve opening → higher T_ss → "
            "higher T_in. The time constant τ_HX = m_cp / b decreases at "
            "higher flow rates."
        ),
    )

    pfr_e = _section(
        "Inside the Reactor — Energy Balance",
        _narrative(
            "Temperature also evolves along the tube axis as the reaction "
            "releases or absorbs heat. In this simulation the saponification "
            "is modelled as thermally neutral (ΔHr = 0) with no wall losses, "
            "so the temperature profile is flat once T_in is set. This is a "
            "simplification — in a real reactor the reaction is mildly "
            "exothermic and the temperature would rise slightly along the tube."
        ),
        _equation(
            "ρ · cp · ∂T/∂t = −ρ · cp · u · ∂T/∂z  +  (−ΔHr) · rA\n"
            "                                          (ΔHr = 0, current model)"
        ),
    )

    t_reactor = _section(
        "Mean Reactor Temperature",
        _narrative(
            "TC-101 needs a single number to represent 'the reactor temperature'. "
            "The simulation estimates it as the average of the inlet and outlet "
            "temperatures — a reasonable approximation for a near-isothermal "
            "reactor. This is the value shown on the diagram and on the graph."
        ),
        _equation(
            "T_reactor = (T_in + T_out) / 2      [°C]"
        ),
        _tip(
            "Set T_setpoint on the diagram and press Apply. Watch T_reactor "
            "approach the setpoint as TC-101 adjusts the valve. Try a large "
            "step change to observe the closed-loop response."
        ),
    )

    return _scroll_tab(hx, pfr_e, t_reactor)


def _tab_kinetics() -> QScrollArea:
    reaction = _section(
        "The Reaction",
        _narrative(
            "The simulator models the saponification of ethyl acetate (EtAc) "
            "by sodium hydroxide (NaOH). This classic second-order reaction is "
            "widely used in teaching labs because the ionic product — sodium "
            "acetate (NaAc) — is electrically conductive, enabling real-time "
            "conversion monitoring with a simple conductivity probe (CT-101)."
        ),
        _equation(
            "NaOH  +  EtAc  →  NaAc  +  EtOH\n"
            "  A    +   B   →  Products\n"
            "                          (A = NaOH,  B = EtAc)"
        ),
    )

    rate = _section(
        "Rate Law — 2nd Order Bimolecular",
        _narrative(
            "The reaction rate depends on how often A and B molecules collide. "
            "It is proportional to both concentrations simultaneously — doubling "
            "both CA_in and CB_in would quadruple the rate. This is why the "
            "stoichiometric ratio (equal feeds) gives the fastest reaction for "
            "a given total flow."
        ),
        _equation(
            "rA = k(T) · CA · CB          [mol/(m³·s)]"
        ),
    )

    arrhenius = _section(
        "Temperature Effect — Arrhenius",
        _narrative(
            "Higher temperature means more energetic molecular collisions, so "
            "a larger fraction can overcome the activation energy barrier. The "
            "Arrhenius equation captures this exponential dependence. Even a "
            "modest increase in T_reactor can significantly raise k(T) and "
            "therefore the conversion Xa."
        ),
        _equation(
            "k(T) = k₀ · exp(−Ea / (R · T))\n"
            "  R  = 8.314  J/(mol·K)  (gas constant)"
        ),
        _narrative(
            "k₀ and Ea are kinetic parameters determined from laboratory "
            "experiments. They are fixed inside the simulation engine."
        ),
        _tip(
            "Raise T_setpoint by 10 °C and observe the increase in Xa on "
            "the Graph tab. Then try reducing the flow rate at the same "
            "temperature — two independent ways to increase conversion."
        ),
    )

    numerical = _section(
        "Numerical Integration",
        _narrative(
            "At each simulation tick the PFR ODE system is integrated in time "
            "using the Runge-Kutta 45 solver from SciPy. The state vector "
            "has 3 × N = 150 entries (N concentration profiles for CA, CB, T)."
        ),
        _equation(
            "solver : scipy.solve_ivp, method='RK45'\n"
            "rtol   = 1×10⁻⁴,  atol = 1×10⁻⁶\n"
            "state  : y = [CA₀…CA_{N−1}, CB₀…CB_{N−1}, T₀…T_{N−1}]   (3N)"
        ),
    )

    return _scroll_tab(reaction, rate, arrhenius, numerical)


def _tab_control() -> QScrollArea:
    overview = _section(
        "What is TC-101 controlling?",
        _narrative(
            "TC-101 is a PID controller whose job is to keep T_reactor at the "
            "operator setpoint (the T_setpoint box on the diagram). It does "
            "this by adjusting how far valve V-101 is open. More valve opening "
            "→ more hot water through E-101/E-102 → higher T_in → "
            "higher T_reactor."
        ),
    )

    pid = _section(
        "PID Algorithm",
        _equation(
            "e(t)  = T_sp − T_reactor             (control error)\n"
            "\n"
            "v(t)  = Kp · e  +  Ki · ∫e dt  +  Kd · de/dt\n"
            "v     = clip(v, 0, 1)                (valve position, 0–100%)"
        ),
        _narrative(
            "Kp (proportional) reacts to the current error — the larger the "
            "deviation, the stronger the correction. Ki (integral) eliminates "
            "steady-state offset by accumulating the error over time. Kd "
            "(derivative) anticipates changes by reacting to the rate at which "
            "the error is growing or shrinking."
        ),
        _tip(
            "Tune the gains live via the TC-101 menu → 'Configure PID Gains'. "
            "Try a large Kp to see faster response but more overshoot. "
            "Increase Ki slowly to eliminate steady-state offset."
        ),
    )

    antiwindup = _section(
        "Anti-Windup",
        _narrative(
            "If the valve is already fully open (v = 1) and the reactor is "
            "still too cold, there is nothing more the controller can do — but "
            "the integral term keeps accumulating. When conditions improve and "
            "the valve finally starts closing, the accumulated integral causes "
            "a large overshoot. The anti-windup logic prevents this by "
            "freezing the integral whenever the output is saturated in the "
            "same direction as the error."
        ),
        _equation(
            "if (v ≥ 1  AND  e > 0):  integral is frozen\n"
            "if (v ≤ 0  AND  e < 0):  integral is frozen"
        ),
    )

    ramp = _section(
        "Flow Changes — Smooth Ramp",
        _narrative(
            "When you change Qa0 or Qb0 and press Apply, the engine does not "
            "step the flow instantly. It ramps linearly over 30 seconds to "
            "avoid a large step disturbance to the reactor. The controller "
            "still responds during the ramp — watch the valve position "
            "indicator update gradually on the diagram."
        ),
        _equation(
            "Q(t) = Q_prev + (Q_new − Q_prev) · (t / 30)    for t ∈ [0, 30 s]"
        ),
    )

    return _scroll_tab(overview, pid, antiwindup, ramp)


def _tab_sensors() -> QScrollArea:
    ct101 = _section(
        "CT-101 — Conductivity Transmitter",
        _narrative(
            "You cannot measure concentration directly and continuously in real "
            "time. Instead, CT-101 measures the electrical conductivity of the "
            "outlet stream. As the saponification proceeds, sodium acetate "
            "(NaAc) accumulates — NaAc is a strong electrolyte, so conductivity "
            "rises with conversion. A factory calibration curve converts the "
            "conductivity reading back to the residual NaOH concentration C_A "
            "at the reactor outlet."
        ),
        _equation(
            f"σ  =  A · CA_out  +  B              [mS/cm]\n"
            f"  A  = {CT101_CALIB_A}  mS·cm⁻¹ / (mol/L)  — slope\n"
            f"  B  = {CT101_CALIB_B}  mS/cm               — background offset"
        ),
        _narrative(
            "Every reading includes a small Gaussian noise term to replicate "
            "real instrument behaviour — notice the slight fluctuation on the "
            "Graph tab while the simulation runs."
        ),
        _equation(
            f"σ_meas = max(0,  σ + N(0, {CT101_NOISE_STD}))    [mS/cm]"
        ),
        _tip(
            "Increase Qb0 to dilute the NaOH feed — watch conductivity drop "
            "as conversion falls. Raise T_setpoint — watch conductivity rise "
            "as higher temperature accelerates the reaction."
        ),
    )

    te = _section(
        "TE-101 / TE-102 — Temperature Elements",
        _narrative(
            "The P&ID shows two temperature elements: TE-101 at the reactor "
            "inlet and TE-102 at the outlet. In this simulation both are "
            "computed directly from the model with no sensor noise or delay. "
            "T_reactor — the controlled variable for TC-101 — is their average."
        ),
        _equation(
            "TE-101  →  T_in     (HX outlet  =  PFR inlet)\n"
            "TE-102  →  T_out    (PFR outlet)\n"
            "T_reactor = (T_in + T_out) / 2    [°C]"
        ),
        _narrative(
            "All three temperatures are plotted on the Admin tab for diagnostic "
            "purposes. In normal operation only T_reactor is visible on the "
            "main diagram."
        ),
    )

    return _scroll_tab(ct101, te)


# ── DocsTab ───────────────────────────────────────────────────────────────────

def _tab_user_guide() -> QScrollArea:
    diagram = _section(
        "Diagram Tab — Running the Simulation",
        _narrative(
            "The Diagram tab is the main control screen — an interactive P&ID of "
            "the process. Use the footer controls to drive the run:"
        ),
        _narrative(
            "•  <b>GO / STOP</b> — start or stop the simulation. STOP also loads "
            "the run into the Table tab.<br>"
            "•  <b>RESET</b> — clear the run, plots and event log and return to "
            "initial conditions.<br>"
            "•  <b>Speed slider</b> — run faster than real time (1× to 100×) to "
            "reach steady state quickly.<br>"
            "•  <b>Apply</b> — push your edited parameters to the running model."
        ),
        _narrative(
            "<b>Editing parameters.</b> The amber boxes on the diagram are "
            "editable — click one, type a value, and press Enter. A box turns "
            "orange to show a pending change; press <b>Apply</b> to commit it. The "
            "editable inputs are the two feed flows (Qa0, Qb0), the two feed "
            "concentrations (Ca0, Cb0) and the reactor temperature setpoint (T_sp)."
        ),
        _narrative(
            "<b>Readings &amp; status.</b> The blue boxes show live readings "
            "(conductivity, valve %, reactor temperature, water-tank temperature). "
            "The right sidebar shows a status card and a scrolling <b>event log</b> "
            "that records parameter changes and raises alarms."
        ),
        _tip(
            "Click equipment on the diagram to open its info dialog — the reactor, "
            "heat exchanger and conductivity transmitter each have one. The "
            "temperature controller opens the PID tuning dialog."
        ),
    )

    graph = _section(
        "Graph Tab — Live Trends",
        _narrative(
            "The Graph tab shows four live plots updated as the simulation runs:"
        ),
        _narrative(
            "•  <b>Temperature</b> — inlet (T_in), outlet (T_out), mean reactor "
            "temperature (T_reactor) and the setpoint (T_sp).<br>"
            "•  <b>Valve opening</b> — the hot-water valve position (%).<br>"
            "•  <b>Feed flows</b> — Qa0, Qb0 and the total inlet flow Q_in.<br>"
            "•  <b>Conductivity</b> — the CT-101 reading, with the inlet "
            "concentrations on the right-hand axis."
        ),
        _narrative(
            "Use the <b>Window</b> control to set how many seconds of history are "
            "shown, the temperature <b>Show:</b> checkboxes to hide or reveal "
            "individual curves, and <b>Reset View</b> to restore the default axes."
        ),
    )

    table = _section(
        "Table Tab — Data &amp; Export",
        _narrative(
            "Press <b>STOP</b> to load the completed run into the Table tab as a "
            "row-per-sample table (time, concentrations, flows, temperatures, "
            "valve and conductivity)."
        ),
        _narrative(
            "Use <b>Export CSV</b> or <b>Export Excel</b> to save the data for "
            "analysis in your spreadsheet or plotting tool of choice."
        ),
        _tip(
            "A typical workflow: set your feeds and setpoint, press GO, let the "
            "run reach steady state (speed it up if needed), press STOP, then "
            "export the data from the Table tab."
        ),
    )

    return _scroll_tab(diagram, graph, table)


class DocsTab(QWidget):
    """Six sub-tabs with student-facing explanations and a usage guide."""

    def __init__(self, parent=None):
        super().__init__(parent)
        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.setSpacing(0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #1e2a35;
            }
            QTabBar::tab {
                background: #262626;
                color: #adadad;
                padding: 6px 18px;
                font-size: 12px;
                border: none;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected {
                color: #E95420;
                border-bottom: 2px solid #E95420;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                color: #eeeeec;
            }
        """)

        tabs.addTab(_tab_user_guide(),     "User Guide")
        tabs.addTab(_tab_mass_balance(),   "Mass Balance")
        tabs.addTab(_tab_energy_balance(), "Energy Balance")
        tabs.addTab(_tab_kinetics(),       "Kinetics")
        tabs.addTab(_tab_control(),        "Control Loop")
        tabs.addTab(_tab_sensors(),        "Sensors")

        vlay.addWidget(tabs)
