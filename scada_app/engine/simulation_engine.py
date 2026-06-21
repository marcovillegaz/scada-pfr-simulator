from __future__ import annotations

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from PyQt6.QtCore import QObject

from reactor_simulation import PFRSimulator, PIDController

from reactor_simulation.sensors import ConductivitySensor

from constants import (
    PFR_LENGTH, PFR_N_NODES, PFR_CROSS_AREA,
    FLUID_DENSITY, HEAT_CAPACITY, AMBIENT_TEMP,
    PRE_EXPONENTIAL_FACTOR, ACTIVATION_ENERGY, DHR, H_LOSS,
    DEFAULT_FEED_A_FLOW, DEFAULT_FEED_B_FLOW,
    DEFAULT_CA_FEED, DEFAULT_CB_FEED,
    HX_VOLUME, T_HOT_WATER, UA_MAX,
    DEFAULT_T_IN_SETPOINT, DEFAULT_PID_KP, DEFAULT_PID_KI, DEFAULT_PID_KD,
    CT101_CALIB_A, CT101_CALIB_B, CT101_NOISE_STD,
    FLOW_RAMP_DURATION,
)
from engine.data_store import DataStore, EngineSnapshot

_L_TO_M3 = 1e-3           # 1 mol/L = 1000 mol/m3 → divide by this factor inverted
_MOL_L_TO_MOL_M3 = 1000.0


class HXDynamic:
    """
    Single-node energy balance on the HX process-side fluid.

    Analytic solution (exact, no solver needed):
        dT/dt = (a - b*T) / m_cp
        T(dt) = T_ss + (T0 - T_ss) * exp(-b*dt/m_cp)
        where  a = Q*rho*cp*T_feed + UA*T_hw
               b = Q*rho*cp + UA
               T_ss = a/b
    """

    def __init__(self, V: float, rho: float, cp: float, T_hw: float, UA_max: float):
        self.V      = V
        self.rho    = rho
        self.cp     = cp
        self.T_hw   = T_hw
        self.UA_max = UA_max
        self.T      = AMBIENT_TEMP   # current process-side temperature

    def step(self, dt: float, valve: float, Q_total: float, T_feed: float) -> float:
        UA   = self.UA_max * max(0.0, min(1.0, valve))
        rcp  = self.rho * self.cp
        m_cp = self.V * rcp
        b    = Q_total * rcp + UA
        a    = Q_total * rcp * T_feed + UA * self.T_hw
        T_ss = a / b if b > 0 else T_feed
        self.T = T_ss + (self.T - T_ss) * math.exp(-b * dt / m_cp)
        return self.T

    def reset(self) -> None:
        self.T = AMBIENT_TEMP


class SimulationEngine(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_store = DataStore()
        self._last_snap: EngineSnapshot | None = None

        # Controllable inputs
        self._Qa0       = DEFAULT_FEED_A_FLOW    # m3/s  — feed A flow (before mixing)
        self._Qb0       = DEFAULT_FEED_B_FLOW    # m3/s  — feed B flow (before mixing)
        self._Ca0       = DEFAULT_CA_FEED        # mol/L — feed A concentration (tank TK-101)
        self._Cb0       = DEFAULT_CB_FEED        # mol/L — feed B concentration (tank TK-102)
        self._t_sp      = DEFAULT_T_IN_SETPOINT  # K — PID setpoint

        # Active flow ramps: key → (start_val, target_val, duration, elapsed)
        self._ramp: dict = {}

        self._init_objects()

    # ── Derived mixing quantities ─────────────────────────────────────────────
    def _mix(self) -> tuple[float, float, float, float]:
        """Returns (CA_in mol/m3, CB_in mol/m3, u m/s, Q_in m3/s)."""
        Q = self._Qa0 + self._Qb0
        if Q == 0:
            return 0.0, 0.0, 0.0, 0.0
        ca_in = self._Ca0 * _MOL_L_TO_MOL_M3 * self._Qa0 / Q
        cb_in = self._Cb0 * _MOL_L_TO_MOL_M3 * self._Qb0 / Q
        u     = Q / PFR_CROSS_AREA
        return ca_in, cb_in, u, Q

    def _build_pfr_params(self) -> dict:
        ca_in, cb_in, u, _ = self._mix()
        return {
            'N':      PFR_N_NODES,
            'L':      PFR_LENGTH,
            'u':      u,
            'CA_in':  ca_in,
            'CB_in':  cb_in,
            'T_in':   self._hx.T,
            'T_amb':  AMBIENT_TEMP,
            'h_loss': H_LOSS,
            'k0':     PRE_EXPONENTIAL_FACTOR,
            'Ea':     ACTIVATION_ENERGY,
            'dHr':    DHR,
            'rho':    FLUID_DENSITY,
            'cp':     HEAT_CAPACITY,
        }

    def _init_objects(self) -> None:
        self._hx   = HXDynamic(HX_VOLUME, FLUID_DENSITY, HEAT_CAPACITY, T_HOT_WATER, UA_MAX)
        self._pid  = PIDController(
            Kp=DEFAULT_PID_KP, Ki=DEFAULT_PID_KI, Kd=DEFAULT_PID_KD,
            setpoint=self._t_sp,
            output_min=0.0, output_max=1.0,
        )
        self._pfr  = PFRSimulator(self._build_pfr_params())
        self._ct101 = ConductivitySensor(CT101_CALIB_A, CT101_CALIB_B, CT101_NOISE_STD)

    # ── Main tick ─────────────────────────────────────────────────────────────
    def tick(self, sim_dt: float) -> None:
        # Advance any active flow ramps before computing the mix
        for key in list(self._ramp):
            sv, tv, dur, elapsed = self._ramp[key]
            elapsed = min(elapsed + sim_dt, dur)
            val = sv + (tv - sv) * (elapsed / dur)
            if key == 'Qa0':
                self._Qa0 = val
            elif key == 'Qb0':
                self._Qb0 = val
            if elapsed >= dur:
                del self._ramp[key]
            else:
                self._ramp[key] = (sv, tv, dur, elapsed)

        ca_in_m3, cb_in_m3, u, Q_total = self._mix()

        # 1. PID: measure HX outlet → compute valve
        valve = self._pid.update(self._hx.T, sim_dt)

        # 2. HX: advance temperature with new valve position
        t_hx = self._hx.step(sim_dt, valve, Q_total, AMBIENT_TEMP)

        # 3. PFR: update boundary conditions then integrate
        self._pfr.update_params({
            'CA_in': ca_in_m3,
            'CB_in': cb_in_m3,
            'T_in':  t_hx,
            'u':     u,
        })
        out = self._pfr.step(sim_dt)

        # Convert profiles mol/m3 -> mol/L
        ca_profile = tuple(v / _MOL_L_TO_MOL_M3 for v in out['CA_profile'])
        cb_profile = tuple(v / _MOL_L_TO_MOL_M3 for v in out['CB_profile'])
        t_profile  = tuple(out['T_profile'])

        cb_out_mol_l = out['CB_out'] / _MOL_L_TO_MOL_M3
        conductivity = self._ct101.measure(cb_out_mol_l)

        self._last_snap = EngineSnapshot(
            sim_time=out['t'],
            CA_out=out['CA_out'] / _MOL_L_TO_MOL_M3,
            CB_out=cb_out_mol_l,
            T_out=out['T_out'],
            X_out=out['X_out'],
            CA_in=ca_in_m3 / _MOL_L_TO_MOL_M3,
            CB_in=cb_in_m3 / _MOL_L_TO_MOL_M3,
            T_hx=t_hx,
            valve=valve,
            Qa0=self._Qa0,
            Qb0=self._Qb0,
            Q_in=Q_total,
            velocity=u,
            conductivity=conductivity,
            CA_profile=ca_profile,
            CB_profile=cb_profile,
            T_profile=t_profile,
        )
        self.data_store.append(self._last_snap)

    def get_snapshot(self) -> EngineSnapshot | None:
        return self._last_snap

    # ── Parameter updates ─────────────────────────────────────────────────────
    def apply_parameters(self, params: dict) -> None:
        if 'Qa0' in params:
            self._ramp['Qa0'] = (self._Qa0, params['Qa0'], FLOW_RAMP_DURATION, 0.0)
        if 'Qb0' in params:
            self._ramp['Qb0'] = (self._Qb0, params['Qb0'], FLOW_RAMP_DURATION, 0.0)
        if 'Ca0' in params:
            self._Ca0 = params['Ca0']
        if 'Cb0' in params:
            self._Cb0 = params['Cb0']
        if 'T_in_setpoint' in params:
            self._t_sp = params['T_in_setpoint']
            self._pid.set_setpoint(self._t_sp)
        if 'Kp' in params or 'Ki' in params or 'Kd' in params:
            self._pid.set_gains(
                Kp=params.get('Kp'),
                Ki=params.get('Ki'),
                Kd=params.get('Kd'),
            )
        if 'h_loss' in params:
            self._pfr.update_params({'h_loss': params['h_loss']})

    def get_pid_params(self) -> dict:
        return {
            'Kp': self._pid.Kp,
            'Ki': self._pid.Ki,
            'Kd': self._pid.Kd,
            'T_in_setpoint': self._t_sp,
        }

    def reset(self) -> None:
        self._Qa0     = DEFAULT_FEED_A_FLOW
        self._Qb0     = DEFAULT_FEED_B_FLOW
        self._Ca0     = DEFAULT_CA_FEED
        self._Cb0     = DEFAULT_CB_FEED
        self._t_sp    = DEFAULT_T_IN_SETPOINT
        self._ramp.clear()
        self._hx.reset()
        self._pid.reset()
        self._pid.set_setpoint(self._t_sp)
        self._pfr.reset(self._build_pfr_params())
        self._ct101.reset()
        self.data_store.clear()
        self._last_snap = None
