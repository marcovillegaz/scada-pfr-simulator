# ── App identity ─────────────────────────────────────────────────────────────
APP_VERSION = "1.0.0"          # semantic version — see CHANGELOG.md
APP_TITLE = f"PFR SCADA SIMULATOR v{APP_VERSION}"

# ── Timer / speed ────────────────────────────────────────────────────────────
TIMER_INTERVAL_MS = 50  # 20 Hz UI refresh
BASE_SIM_DT = 0.5  # sim-s per tick at speed=1

# ── PFR geometry ─────────────────────────────────────────────────────────────
import math as _math

PFR_LENGTH = 20.9  # m    tube length
PFR_DIAMETER = 0.005  # m    inner diameter (5 mm)
PFR_CROSS_AREA = _math.pi * (PFR_DIAMETER / 2) ** 2  # m²   π·(D/2)²  ≈ 1.96e-5
PFR_N_NODES = 50  # —    spatial nodes

# ── Fluid properties ─────────────────────────────────────────────────────────
FLUID_DENSITY = 1000.0  # kg/m3
HEAT_CAPACITY = 4180.0  # J/(kg.K)
AMBIENT_TEMP = 288.0  # K   feed stream temperature (IMPORTANT)

# ── Reaction kinetics  A + B -> Products,  r = k(T)*CA*CB  (2nd order) ───────
# Saponification of EtAc by NaOH. Literature: k(25 °C) ~ 0.10 L/(mol·s)
# = 1.0e-4 m3/(mol·s), Ea ~ 46 kJ/mol. Calibrated for the 20–50 °C operating
# envelope (HX hot water 60 °C, alarm band 20–40 °C):
#   Da = k*CA_in*tau  ->  X_out ~ 0.31 (20 °C) … 0.60 (40 °C) … 0.72 (50 °C)
REACTION_ORDER = 2.0  # kept for model flag; bimolecular handled in rhs
PRE_EXPONENTIAL_FACTOR = 1.1463e4  # k0  [m3/(mol.s)]
ACTIVATION_ENERGY = 46000  # Ea  [J/mol]

# ── Reaction thermodynamics ───────────────────────────────────────────────────
DHR = 0.0  # J/mol     heat of reaction (0 = isothermal)
# Wall heat loss to ambient — the bare tube is not perfectly insulated.
# For a thin tube the volumetric coefficient is  h_loss = U * (πDL)/(A·L) = 4U/D.
# U ≈ 10 W/(m2.K) (natural convection of a bare tube to still air), D = 5 mm
#   → h_loss = 4·10/0.005 = 8000 W/(m3.K).  Fluid cools toward T_amb along the
# tube, so T_out sits a little below T_in (visible gradient on the Graph tab).
H_LOSS = 8000.0  # W/(m3.K)  wall heat loss

# ── Feed streams (two independent flows) ─────────────────────────────────────
DEFAULT_FEED_A_FLOW = 1.6667e-6  # m3/s
DEFAULT_FEED_B_FLOW = 1.6667e-6  # m3/s
DEFAULT_CA_FEED = 0.1  # mol/L  (= 2000 mol/m3 inside the model)
DEFAULT_CB_FEED = 0.1  # mol/L
# At equal flows: CA_in = CB_in = 1.0 mol/L, u = 2e-4/0.01 = 0.02 m/s

# ── Heat exchanger (dynamic model, hot-water shell) ───────────────────────────
HX_VOLUME = 0.002  # m3   process-side holdup  ->  tau_hx = 10 s
T_HOT_WATER = 333.15  # K    (60 degC, constant)
UA_MAX = 100.0  # W/K  at full valve opening

# ── PID for HX outlet temperature (= PFR inlet T) ────────────────────────────
DEFAULT_T_SETPOINT = 293  # K  — PID setpoint for T_reactor
# Re-tuned for the recalibrated kinetics + non-adiabatic reactor. Chosen by
# closed-loop step tests (20→30→40 °C): all steps settle in ~450–570 s with ~0
# steady-state offset. NOTE: ~5–7 °C overshoot remains and is structural — the
# controlled variable t_reactor = (T_in + T_out)/2 includes the ~120 s
# transport-delayed outlet, so the loop has dead time that PID gains cannot
# remove (verified: overshoot is ~constant across a 12× range of Kp).
DEFAULT_PID_KP = 0.14   # valve / K
DEFAULT_PID_KI = 0.04   # valve / (K.s)
DEFAULT_PID_KD = 0.0

# ── Unit conversion ──────────────────────────────────────────────────────────
K2C = 273.15  # subtract from K to get °C

# ── Alarm thresholds ─────────────────────────────────────────────────────────
ALARM_TEMP_HIGH = 450.0  # K    (legacy — kept for engine compatibility)
ALARM_TEMP_LOW = 300.0  # K    (legacy — kept for engine compatibility)
ALARM_T_HIGH_C = 40  # °C   reactor outlet HIGH TEMP alarm
ALARM_T_LOW_C = 20  # °C   reactor outlet LOW TEMP alarm
ALARM_X_LOW = 0.20  # —    conversion LOW alarm (fraction, not %)

# ── CT-101 conductivity sensor ───────────────────────────────────────────────
CT101_CALIB_A = 156  # mS/cm per (mol/L)  — slope
CT101_CALIB_B = 1.6  # mS/cm              — background / offset
CT101_NOISE_STD = 0.05  # mS/cm

# ── TE-101 / TE-102 temperature sensors ──────────────────────────────────────
TE_NOISE_STD = 0.3  # K   Gaussian measurement noise on T_in / T_out readings

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
RTD_PULSE_DOSE_DEFAULT = 0.02   # mol -- default injected dose
RTD_STEP_C0_DEFAULT = 1.0       # mol/L -- default step feed concentration
