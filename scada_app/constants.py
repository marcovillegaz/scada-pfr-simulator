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
REACTION_ORDER = 2.0  # kept for model flag; bimolecular handled in rhs
PRE_EXPONENTIAL_FACTOR = 7.3e-2  # k0  [m3/(mol.s)]
ACTIVATION_ENERGY = 34694  # Ea  [J/mol]
# k(350 K) ~ 1.03e-5 m3/(mol.s) | Da = k*CA_in*tau ~ 1.03 -> X_ss ~ 63 %

# ── Reaction thermodynamics ───────────────────────────────────────────────────
DHR = 0.0  # J/mol     heat of reaction (0 = isothermal)
H_LOSS = 0.0  # W/(m3.K)  wall heat loss   (0 = adiabatic)

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
DEFAULT_T_IN_SETPOINT = 293  # K
DEFAULT_PID_KP = 0.02  # valve / K
DEFAULT_PID_KI = 0.005  # valve / (K.s)
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

# ── P&ID scene ───────────────────────────────────────────────────────────────
SCENE_W = 800
SCENE_H = 500

# ── Live plot rolling window ─────────────────────────────────────────────────
PLOT_BUFFER_SIZE = 24000  # 1200 s at 20 Hz

# ── Flow ramp ─────────────────────────────────────────────────────────────────
FLOW_RAMP_DURATION = 30.0  # s — linear ramp time when a flow setpoint changes
