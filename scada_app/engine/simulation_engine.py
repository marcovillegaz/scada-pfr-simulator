from __future__ import annotations

import sys
import os

# Ensure the project root is on the path so reactor_simulation is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from PyQt6.QtCore import QObject

from reactor_simulation import (
    ReactorState, HeatExchanger, Pump, PIDController,
    Thermocouple, ConductivitySensor, PlugFlow,
)

from constants import (
    REACTOR_VOLUME, HEAT_CAPACITY, MASS, HEAT_TRANSFER_COEFF, AMBIENT_TEMP,
    DEFAULT_FEED_CONCENTRATION, DEFAULT_FLOW_RATE, DEFAULT_INITIAL_TEMP,
    DEFAULT_KP, DEFAULT_KI, DEFAULT_KD, DEFAULT_SETPOINT,
    DEFAULT_HX_UA, DEFAULT_T_UTILITY_MIN, DEFAULT_T_UTILITY_MAX,
    REACTION_ORDER, PRE_EXPONENTIAL_FACTOR, ACTIVATION_ENERGY,
)
from engine.data_store import DataStore, EngineSnapshot


class SimulationEngine(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_store = DataStore()
        self._last_snap: EngineSnapshot | None = None
        self._feed_concentration = DEFAULT_FEED_CONCENTRATION
        self._init_objects()

    def _init_objects(self) -> None:
        self._state = ReactorState(n_species=1, n_spatial_points=1)
        self._state.temperature = DEFAULT_INITIAL_TEMP
        self._state.set_concentration(DEFAULT_FEED_CONCENTRATION)

        # Heat exchanger — PID commands utility temperature; Q = UA*(T_util - T_proc)
        self._hx = HeatExchanger(
            UA=DEFAULT_HX_UA,
            T_utility_min=DEFAULT_T_UTILITY_MIN,
            T_utility_max=DEFAULT_T_UTILITY_MAX,
            time_constant=5.0,
            T_initial=DEFAULT_T_UTILITY_MIN,
        )
        self._pump = Pump(
            max_flow=0.001,
            min_flow=0.0,
            max_ramp_rate=0.0001,
        )
        self._pump.set_flow(DEFAULT_FLOW_RATE)

        # PID output is utility temperature (K)
        self._pid = PIDController(
            Kp=DEFAULT_KP,
            Ki=DEFAULT_KI,
            Kd=DEFAULT_KD,
            setpoint=DEFAULT_SETPOINT,
            output_min=DEFAULT_T_UTILITY_MIN,
            output_max=DEFAULT_T_UTILITY_MAX,
        )
        self._pfr = PlugFlow(
            order_of_reaction=REACTION_ORDER,
            kinetic_constant=PRE_EXPONENTIAL_FACTOR,
            activation_energy=ACTIVATION_ENERGY,
        )

        self._tc = Thermocouple(
            noise_std=0.5,
            time_constant=5.0,
            bias=1.0,
            seed=42,
        )
        self._cond = ConductivitySensor(
            noise_std=0.01,
            drift_rate=0.0,
        )

    def tick(self, sim_dt: float) -> None:
        dt = sim_dt

        # 1. Measure temperature
        measured_temp = self._tc.measure(self._state.temperature, dt)

        # 2. PID outputs a utility temperature command (K)
        T_utility_cmd = self._pid.update(measured_temp, dt)
        self._hx.set_utility_temperature(T_utility_cmd)

        # 3. Heat exchanger computes Q = UA*(T_util - T_process)
        heat_input = self._hx.update(self._state.temperature, dt)

        # 4. Pump
        actual_flow = self._pump.update(dt)
        self._state.flow_rate = actual_flow

        # 5. Concentration — convection + reaction (Arrhenius k(T))
        #    dCa/dt = (F/V)·(Ca_feed − Ca) − k(T)·Ca^n
        Ca = self._state.get_concentration()
        if REACTOR_VOLUME > 0:
            r = self._pfr.reaction_rate(Ca, self._state.temperature)
            dCa_dt = (actual_flow / REACTOR_VOLUME) * (self._feed_concentration - Ca) - r
        else:
            dCa_dt = 0.0
        self._state.set_concentration(Ca + dCa_dt * dt)

        # 6. Energy balance (Euler) — heat_input can be negative (cooling)
        dT_dt  = heat_input / (MASS * HEAT_CAPACITY)
        dT_dt -= HEAT_TRANSFER_COEFF * (self._state.temperature - AMBIENT_TEMP) / (MASS * HEAT_CAPACITY)
        self._state.temperature += dT_dt * dt
        self._state.time += dt

        # 7. Conductivity sensor
        conductivity = self._cond.measure(
            self._state.get_concentration(), self._state.temperature, dt
        )
        try:
            measured_conc = self._cond.concentration_from_conductivity(
                conductivity, self._state.temperature
            )
        except Exception:
            measured_conc = self._state.get_concentration()

        pid_comp = self._pid.get_components()

        self._last_snap = EngineSnapshot(
            sim_time=self._state.time,
            true_temp=self._state.temperature,
            measured_temp=measured_temp,
            setpoint=self._pid.setpoint,
            concentration=self._state.get_concentration(),
            measured_concentration=float(measured_conc),
            flow_rate=actual_flow,
            heat_flow=heat_input,          # W — positive=heating, negative=cooling
            pid_p=pid_comp["P"],
            pid_i=pid_comp["I"],
            pid_d=pid_comp["D"],
        )
        self.data_store.append(self._last_snap)

    def get_snapshot(self) -> EngineSnapshot | None:
        return self._last_snap

    def apply_parameters(self, params: dict) -> None:
        if "feed_concentration" in params:
            self._feed_concentration = params["feed_concentration"]
        if "flow_rate" in params:
            self._pump.set_flow(params["flow_rate"])
        if "setpoint" in params:
            self._pid.set_setpoint(params["setpoint"])
        self._pid.set_gains(
            Kp=params.get("Kp"),
            Ki=params.get("Ki"),
            Kd=params.get("Kd"),
        )
        if "T_utility_max" in params:
            self._hx.T_utility_max = params["T_utility_max"]
            self._pid.output_max = params["T_utility_max"]

    def reset(self) -> None:
        self._feed_concentration = DEFAULT_FEED_CONCENTRATION
        self._init_objects()
        self.data_store.clear()
        self._last_snap = None
