# ── App identity ─────────────────────────────────────────────────────────────
APP_VERSION = "1.0.0"          # semantic version — see CHANGELOG.md
APP_NAME = "ChemIng SimLab"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"

# ── Timer / speed ────────────────────────────────────────────────────────────
TIMER_INTERVAL_MS = 50  # 20 Hz UI refresh
BASE_SIM_DT = 0.5  # sim-s per tick at speed=1

# ── PFR physics (Experiencia 2) ───────────────────────────────────────────────
# Sourced from scenarios/pfr/<id>.json via scenarios.loader.load_pfr_scenario()
# -- PFR is data-driven the same way RTD is (docs/shared/CONVENTION.md), so
# this is no longer the source of truth, just a compatibility re-export: the
# flat names below let existing dialogs/panels/widgets/docs (reactor_dialog,
# hx_dialog, tc_dialog, parameters_panel, readings_panel, pfr_diagram,
# status_card, docs_tab) keep reading `from constants import PFR_LENGTH` etc.
# unchanged. PFREngine itself calls load_pfr_scenario() directly, not this
# module. New code should prefer the scenario object over these constants.
import math as _math
from scenarios.loader import load_pfr_scenario as _load_pfr_scenario

PFR_DEFAULT_SCENARIO = "pfr_default"
_pfr = _load_pfr_scenario(PFR_DEFAULT_SCENARIO)

# Geometry
PFR_LENGTH = _pfr.visible.geometry.length_m  # m    tube length
PFR_DIAMETER = _pfr.visible.geometry.diameter_m  # m    inner diameter (5 mm)
PFR_CROSS_AREA = _math.pi * (PFR_DIAMETER / 2) ** 2  # m²   π·(D/2)²  ≈ 1.96e-5
PFR_N_NODES = _pfr.visible.geometry.n_nodes  # —    spatial nodes

# Fluid properties
FLUID_DENSITY = _pfr.visible.fluid.density_kg_m3  # kg/m3
HEAT_CAPACITY = _pfr.visible.fluid.heat_capacity_J_kgK  # J/(kg.K)
AMBIENT_TEMP = _pfr.visible.fluid.ambient_temp_K  # K   feed stream temperature (IMPORTANT)

# Reaction kinetics  A + B -> Products,  r = k(T)*CA*CB  (2nd order).
# Saponification of EtAc by NaOH. Literature: k(25 °C) ~ 0.10 L/(mol·s)
# = 1.0e-4 m3/(mol·s), Ea ~ 46 kJ/mol. Calibrated for the 20–50 °C operating
# envelope (HX hot water 60 °C, alarm band 20–40 °C):
#   Da = k*CA_in*tau  ->  X_out ~ 0.31 (20 °C) … 0.60 (40 °C) … 0.72 (50 °C)
REACTION_ORDER = _pfr.visible.kinetics.reaction_order  # kept for model flag; bimolecular handled in rhs
PRE_EXPONENTIAL_FACTOR = _pfr.visible.kinetics.k0_m3_mol_s  # k0  [m3/(mol.s)]
ACTIVATION_ENERGY = _pfr.visible.kinetics.activation_energy_J_mol  # Ea  [J/mol]

# Reaction thermodynamics
DHR = _pfr.visible.kinetics.heat_of_reaction_J_mol  # J/mol     heat of reaction (0 = isothermal)
# Wall heat loss to ambient — the bare tube is not perfectly insulated.
# For a thin tube the volumetric coefficient is  h_loss = U * (πDL)/(A·L) = 4U/D.
# U ≈ 10 W/(m2.K) (natural convection of a bare tube to still air), D = 5 mm
#   → h_loss = 4·10/0.005 = 8000 W/(m3.K).  Fluid cools toward T_amb along the
# tube, so T_out sits a little below T_in (visible gradient on the Graph tab).
H_LOSS = _pfr.visible.kinetics.h_loss_W_m3K  # W/(m3.K)  wall heat loss

# Feed streams (two independent flows)
DEFAULT_FEED_A_FLOW = _pfr.visible.feed.Qa0_m3_s  # m3/s
DEFAULT_FEED_B_FLOW = _pfr.visible.feed.Qb0_m3_s  # m3/s
DEFAULT_CA_FEED = _pfr.visible.feed.Ca0_mol_L  # mol/L  (= 2000 mol/m3 inside the model)
DEFAULT_CB_FEED = _pfr.visible.feed.Cb0_mol_L  # mol/L
# At equal flows: CA_in = CB_in = 1.0 mol/L, u = 2e-4/0.01 = 0.02 m/s

# Heat exchanger (dynamic model, hot-water shell)
HX_VOLUME = _pfr.visible.heat_exchanger.volume_m3  # m3   process-side holdup  ->  tau_hx = 10 s
T_HOT_WATER = _pfr.visible.heat_exchanger.hot_water_temp_K  # K    (60 degC, constant)
UA_MAX = _pfr.visible.heat_exchanger.ua_max_W_K  # W/K  at full valve opening

# PID for HX outlet temperature (= PFR inlet T)
DEFAULT_T_SETPOINT = _pfr.visible.pid.setpoint_K  # K  — PID setpoint for T_reactor
# Re-tuned for the recalibrated kinetics + non-adiabatic reactor. Chosen by
# closed-loop step tests (20→30→40 °C): all steps settle in ~450–570 s with ~0
# steady-state offset. NOTE: ~5–7 °C overshoot remains and is structural — the
# controlled variable t_reactor = (T_in + T_out)/2 includes the ~120 s
# transport-delayed outlet, so the loop has dead time that PID gains cannot
# remove (verified: overshoot is ~constant across a 12× range of Kp).
DEFAULT_PID_KP = _pfr.visible.pid.Kp  # valve / K
DEFAULT_PID_KI = _pfr.visible.pid.Ki  # valve / (K.s)
DEFAULT_PID_KD = _pfr.visible.pid.Kd

# ── Unit conversion ──────────────────────────────────────────────────────────
K2C = 273.15  # subtract from K to get °C

# ── Alarm thresholds ─────────────────────────────────────────────────────────
ALARM_TEMP_HIGH = 450.0  # K    (legacy — kept for engine compatibility)
ALARM_TEMP_LOW = 300.0  # K    (legacy — kept for engine compatibility)
ALARM_T_HIGH_C = 40  # °C   reactor outlet HIGH TEMP alarm
ALARM_T_LOW_C = 20  # °C   reactor outlet LOW TEMP alarm
ALARM_X_LOW = 0.20  # —    conversion LOW alarm (fraction, not %)

# ── CT-101 conductivity sensor (from pfr_default.json, see note above) ───────
CT101_CALIB_A = _pfr.visible.sensors.ct101_calib_a  # mS/cm per (mol/L)  — slope
CT101_CALIB_B = _pfr.visible.sensors.ct101_calib_b  # mS/cm              — background / offset
CT101_NOISE_STD = _pfr.visible.sensors.ct101_noise_std  # mS/cm

# ── TE-101 / TE-102 temperature sensors (from pfr_default.json) ──────────────
TE_NOISE_STD = _pfr.visible.sensors.te_noise_std  # K   Gaussian measurement noise on T_in / T_out readings

# ── P&ID scene ───────────────────────────────────────────────────────────────
SCENE_W = 800
SCENE_H = 500

# ── Live plot rolling window ─────────────────────────────────────────────────
PLOT_BUFFER_SIZE = 24000  # 1200 s at 20 Hz

# ── Flow ramp ─────────────────────────────────────────────────────────────────
FLOW_RAMP_DURATION = 30.0  # s — linear ramp time when a flow setpoint changes

# ── RTD module (Experiencia 3) ────────────────────────────────────────────────
# tau ~ 100 s for the default scenario -- much slower than the PFR's ~10 s
# transport delay, so a larger sim_dt per tick keeps a run inside a
# classroom session without needing a separate real-time definition.
RTD_BASE_SIM_DT = 1.0        # sim-s per tick at speed=1 (20 Hz UI -> 20x accel.)
RTD_DEFAULT_SCENARIO = "planta_a"
RTD_PULSE_WIDTH_S = 1.5      # s -- rectangular pulse width (Delta t_p), << tau
# Tracer dosing is mass-based (mg / mg-L), matching a real dye tracer (e.g.
# Brilliant Blue FCF) rather than an abstract molar dose -- see sensor.json's
# epsilon_b, calibrated as a mass-basis Lambert-Beer constant to match.
RTD_PULSE_DOSE_DEFAULT = 10.0   # mg -- default injected dose
RTD_STEP_C0_DEFAULT = 6.0       # mg/L -- default step feed concentration

# ── CIP (Clean-In-Place) protocol ────────────────────────────────────────────
# The RTD tracer experiment is framed as CIP validation: the student isolates
# one of three parallel reactors for washing, then injects tracer to read the
# packing-bed state via the AT-101 washout curve. Each reactor tag maps 1:1 to
# a scenario (its packed-bed model) and to the CIP diagram that shows it
# isolated for washing.
RTD_REACTORS: tuple[tuple[str, str, str], ...] = (
    # (reactor tag, scenario id, CIP diagram filename)
    ('R-102', 'planta_a', 'cip_r102.svg'),
    ('R-103', 'planta_b', 'cip_r103.svg'),
    ('R-104', 'planta_c', 'cip_r104.svg'),
)
RTD_NORMAL_SVG = 'rtd_normal_operation.svg'   # default view: no reactor selected
RTD_V106_OVERLAY_SVG = 'overlay_v106_green.svg'   # painted on top while injecting
