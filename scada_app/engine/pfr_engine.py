from __future__ import annotations

import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from reactor_simulation import PFRSimulator, PIDController, HXDynamic

from reactor_simulation.sensors import ConductivitySensor, TemperatureSensor

from constants import FLOW_RAMP_DURATION
from scenarios.loader import load_pfr_scenario, PFRScenario
from engine.base_engine import BaseEngine
from engine.data_store import EngineSnapshot

_MOL_L_TO_MOL_M3 = 1000.0


class PFREngine(BaseEngine):
    """
    PFR (Experiencia 2) tick engine -- the saponification reactor: two feed
    streams mixed into a dynamic heat exchanger and a Method-of-Lines plug
    flow reactor, with a PID controlling the HX valve on measured reactor
    temperature. See docs/shared/CONVENTION.md for how this relates to
    RTDEngine and BaseEngine's shared contract.

    Data-driven the same way RTDEngine is: physics comes from a
    scenarios/pfr/<id>.json scenario (loaded here, not from constants.py --
    see scada_app/scenarios/loader.py's PFR section for why there's no
    visible/oculto split for this module).
    """

    def __init__(self, scenario_id: str, parent=None):
        super().__init__(parent)
        self._last_snap: EngineSnapshot | None = None

        self.scenario_id = scenario_id
        self._scenario: PFRScenario = load_pfr_scenario(scenario_id)
        self._cross_area = math.pi * (self._scenario.visible.geometry.diameter_m / 2) ** 2

        # Controllable inputs
        v = self._scenario.visible
        self._Qa0       = v.feed.Qa0_m3_s    # m3/s  — feed A flow (before mixing)
        self._Qb0       = v.feed.Qb0_m3_s    # m3/s  — feed B flow (before mixing)
        self._Ca0       = v.feed.Ca0_mol_L   # mol/L — feed A concentration (tank TK-101)
        self._Cb0       = v.feed.Cb0_mol_L   # mol/L — feed B concentration (tank TK-102)
        self._t_sp      = v.pid.setpoint_K   # K — PID setpoint for T_reactor

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
        u     = Q / self._cross_area
        return ca_in, cb_in, u, Q

    def _build_pfr_params(self) -> dict:
        ca_in, cb_in, u, _ = self._mix()
        v = self._scenario.visible
        return {
            'N':      v.geometry.n_nodes,
            'L':      v.geometry.length_m,
            'u':      u,
            'CA_in':  ca_in,
            'CB_in':  cb_in,
            'T_in':   self._hx.T,
            'T_amb':  v.fluid.ambient_temp_K,
            'h_loss': v.kinetics.h_loss_W_m3K,
            'k0':     v.kinetics.k0_m3_mol_s,
            'Ea':     v.kinetics.activation_energy_J_mol,
            'dHr':    v.kinetics.heat_of_reaction_J_mol,
            'rho':    v.fluid.density_kg_m3,
            'cp':     v.fluid.heat_capacity_J_kgK,
        }

    def _init_objects(self) -> None:
        v = self._scenario.visible
        self._hx   = HXDynamic(
            v.heat_exchanger.volume_m3, v.fluid.density_kg_m3, v.fluid.heat_capacity_J_kgK,
            v.heat_exchanger.hot_water_temp_K, v.heat_exchanger.ua_max_W_K, v.fluid.ambient_temp_K,
        )
        self._pid  = PIDController(
            Kp=v.pid.Kp, Ki=v.pid.Ki, Kd=v.pid.Kd,
            setpoint=self._t_sp,
            output_min=0.0, output_max=1.0,
        )
        self._pfr  = PFRSimulator(self._build_pfr_params())
        self._ct101 = ConductivitySensor(v.sensors.ct101_calib_a, v.sensors.ct101_calib_b, v.sensors.ct101_noise_std)
        self._te101 = TemperatureSensor(v.sensors.te_noise_std)   # T_in  reading (HX outlet)
        self._te102 = TemperatureSensor(v.sensors.te_noise_std)   # T_out reading (PFR outlet)
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
        t_in = self._hx.step(sim_dt, self._prev_valve, Q_total, self._scenario.visible.fluid.ambient_temp_K)

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

    def set_scenario(self, scenario_id: str) -> None:
        """Switch to a different PFR scenario. Resets the run. Only one
        scenario ships today, but this mirrors RTDEngine.set_scenario()."""
        self.scenario_id = scenario_id
        self._scenario = load_pfr_scenario(scenario_id)
        self._cross_area = math.pi * (self._scenario.visible.geometry.diameter_m / 2) ** 2
        self.reset()

    def reset(self) -> None:
        v = self._scenario.visible
        self._Qa0        = v.feed.Qa0_m3_s
        self._Qb0        = v.feed.Qb0_m3_s
        self._Ca0        = v.feed.Ca0_mol_L
        self._Cb0        = v.feed.Cb0_mol_L
        self._t_sp       = v.pid.setpoint_K
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
