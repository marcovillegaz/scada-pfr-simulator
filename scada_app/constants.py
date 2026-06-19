# Physics — match temperature_control_demo.py exactly
REACTOR_VOLUME      = 0.01    # m³
HEAT_CAPACITY       = 4180.0  # J/(kg·K)
MASS                = 10.0    # kg
HEAT_TRANSFER_COEFF = 25.0    # W/K
AMBIENT_TEMP        = 298.0   # K

# Default initial conditions
DEFAULT_FEED_CONCENTRATION = 1.0     # mol/L
DEFAULT_FLOW_RATE          = 1e-4    # m³/s
DEFAULT_INITIAL_TEMP       = 350.0   # K
DEFAULT_KP                 = 3.0
DEFAULT_KI                 = 1.5
DEFAULT_KD                 = 0.0
DEFAULT_SETPOINT           = 400.0   # K
DEFAULT_HX_UA              = 200.0   # W/K  — overall UA of the heat exchanger
DEFAULT_T_UTILITY_MIN      = 273.15  # K    — minimum utility temperature (ice water)
DEFAULT_T_UTILITY_MAX      = 500.0   # K    — maximum utility temperature (steam)

# Reaction kinetics (PFR, first-order A → B, Arrhenius)
REACTION_ORDER         = 1.0      # n
PRE_EXPONENTIAL_FACTOR = 10.0     # k0  [1/s] for first-order
ACTIVATION_ENERGY      = 20000.0  # Ea  [J/mol]
# k(350 K) ≈ 0.010 /s  |  k(400 K) ≈ 0.024 /s  →  clear temp effect on conversion

# Timer / speed
TIMER_INTERVAL_MS = 50   # 20 Hz UI refresh
BASE_SIM_DT       = 0.05 # sim-s per tick at speed=1 → true real-time

# Alarm thresholds
ALARM_TEMP_HIGH = 450.0  # K
ALARM_TEMP_LOW  = 300.0  # K

# P&ID scene (logical coordinate space)
SCENE_W = 800
SCENE_H = 500

# Live plot rolling window
PLOT_BUFFER_SIZE = 6000  # 300 s at 20 Hz
