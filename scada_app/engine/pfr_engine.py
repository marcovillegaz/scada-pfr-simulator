from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from reactor_simulation import PFRSimulator, PIDController, HXDynamic

from reactor_simulation.sensors import ConductivitySensor, TemperatureSensor

from constants import (
    PFR_LENGTH, PFR_N_NODES, PFR_CROSS_AREA,
    FLUID_DENSITY, HEAT_CAPACITY, AMBIENT_TEMP,
    PRE_EXPONENTIAL_FACTOR, ACTIVATION_ENERGY, DHR, H_LOSS,
    DEFAULT_FEED_A_FLOW, DEFAULT_FEED_B_FLOW,
    DEFAULT_CA_FEED, DEFAULT_CB_FEED,
    HX_VOLUME, T_HOT_WATER, UA_MAX,
    DEFAULT_T_SETPOINT, DEFAULT_PID_KP, DEFAULT_PID_KI, DEFAULT_PID_KD,
    CT101_CALIB_A, CT101_CALIB_B, CT101_NOISE_STD, TE_NOISE_STD,
    FLOW_RAMP_DURATION,
)
from engine.base_engine import BaseEngine
from engine.data_store import EngineSnapshot

_L_TO_M3 = 1e-3           # 1 mol/L = 1000 mol/m3 → divide by this factor inverted
_MOL_L_TO_MOL_M3 = 1000.0


class PFREngine(BaseEngine):
    """
    PFR (Experiencia 2) tick engine -- the saponification reactor: two feed
    streams mixed into a dynamic heat exchanger and a Method-of-Lines plug
    flow reactor, with a PID controlling the HX valve on measured reactor
    temperature. See docs/shared/CONVENTION.md for how this relates to
    RTDEngine and BaseEngine's shared contract.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_snap: EngineSnapshot | None = None

        # Controllable inputs
        self._Qa0       = DEFAULT_FEED_A_FLOW    # m3/s  — feed A flow (before mixing)
        self._Qb0       = DEFAULT_FEED_B_FLOW    # m3/s  — feed B flow (before mixing)
        self._Ca0       = DEFAULT_CA_FEED        # mol/L — feed A concentration (tank TK-101)
        self._Cb0       = DEFAULT_CB_FEED        # mol/L — feed B concentration (tank TK-102)
        self._t_sp      = DEFAULT_T_SETPOINT     # K — PID setpoint for T_reactor

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
        self._hx   = HXDynamic(HX_VOLUME, FLUID_DENSITY, HEAT_CAPACITY, T_HOT_WATER, UA_MAX, AMBIENT_TEMP)
        self._pid  = PIDController(
            Kp=DEFAULT_PID_KP, Ki=DEFAULT_PID_KI, Kd=DEFAULT_PID_KD,
            setpoint=self._t_sp,
            output_min=0.0, output_max=1.0,
        )
        self._pfr  = PFRSimulator(self._build_pfr_params())
        self._ct101 = ConductivitySensor(CT101_CALIB_A, CT101_CALIB_B, CT101_NOISE_STD)
        self._te101 = TemperatureSensor(TE_NOISE_STD)   # T_in  reading (HX outlet)
        self._te102 = TemperatureSensor(TE_NOISE_STD)   # T_out reading (PFR outlet)
        self._prev_valve = 0.0   # valve applied to HX at the previous tick

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

        # 1. HX: advance temperature using the valve set at the previous tick
        t_in = self._hx.step(sim_dt, self._prev_valve, Q_total, AMBIENT_TEMP)

        # 2. PFR: update boundary conditions then integrate
        self._pfr.update_params({
            'CA_in': ca_in_m3,
            'CB_in': cb_in_m3,
            'T_in':  t_in,
            'u':     u,
        })
        out = self._pfr.step(sim_dt)

        # 3. PID: measure mean reactor temperature, produce valve for next tick
        t_reactor = (t_in + out['T_out']) / 2.0
        self._prev_valve = self._pid.update(t_reactor, sim_dt)

        # Convert profiles mol/m3 -> mol/L
        ca_profile = tuple(v / _MOL_L_TO_MOL_M3 for v in out['CA_profile'])
        cb_profile = tuple(v / _MOL_L_TO_MOL_M3 for v in out['CB_profile'])
        t_profile  = tuple(out['T_profile'])

        # CT-101 tracks residual NaOH (= reactant A) in the product stream
        ca_out_mol_l = out['CA_out'] / _MOL_L_TO_MOL_M3
        conductivity = self._ct101.measure(ca_out_mol_l)

        # TE-101 / TE-102 report noisy temperatures; the PFR/PID use true values
        t_in_meas  = self._te101.measure(t_in)
        t_out_meas = self._te102.measure(out['T_out'])

        self._last_snap = EngineSnapshot(
            sim_time=out['t'],
            CA_out=ca_out_mol_l,
            CB_out=out['CB_out'] / _MOL_L_TO_MOL_M3,
            T_out=t_out_meas,
            X_out=out['X_out'],
            CA_in=ca_in_m3 / _MOL_L_TO_MOL_M3,
            CB_in=cb_in_m3 / _MOL_L_TO_MOL_M3,
            T_in=t_in_meas,
            T_reactor=t_reactor,
            T_setpoint=self._t_sp,
            valve=self._prev_valve,
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
        if 'T_setpoint' in params:
            self._t_sp = params['T_setpoint']
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
            'T_setpoint': self._t_sp,
        }

    def reset(self) -> None:
        self._Qa0        = DEFAULT_FEED_A_FLOW
        self._Qb0        = DEFAULT_FEED_B_FLOW
        self._Ca0        = DEFAULT_CA_FEED
        self._Cb0        = DEFAULT_CB_FEED
        self._t_sp       = DEFAULT_T_SETPOINT
        self._prev_valve = 0.0
        self._ramp.clear()
        self._hx.reset()
        self._pid.reset()
        self._pid.set_setpoint(self._t_sp)
        self._pfr.reset(self._build_pfr_params())
        self._ct101.reset()
        self._te101.reset()
        self._te102.reset()
        self._clear_run()
