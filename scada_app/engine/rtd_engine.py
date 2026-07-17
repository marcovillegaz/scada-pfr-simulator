from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from PyQt6.QtCore import QObject

from reactor_simulation.sensors import Photocolorimeter
from reactor_simulation.rtd import pulse_concentration

from scenarios.loader import build_rtd_model, scenario_seed, load_scenario, Scenario

from constants import RTD_PULSE_WIDTH_S
from engine.data_store import DataStore, RTDSnapshot

_ML_S_TO_L_S = 1.0 / 1000.0


class RTDEngine(QObject):
    """
    RTD (Experiencia 3) tick engine -- the analogue of SimulationEngine for
    the tracer / residence-time-distribution experiment.

    Owns the hidden-truth PackedBedRTD model and the Photocolorimeter that
    filters it into student-visible absorbance. Injections (pulse / step)
    are boundary conditions applied to PackedBedRTD.step(dt, c_in): the same
    segmented-integration pattern SimulationEngine uses for the PFR, just
    with the tracer inlet concentration as the thing that changes tick to
    tick instead of temperature/flow setpoints.
    """

    def __init__(self, scenario_id: str, parent=None):
        super().__init__(parent)
        self.data_store = DataStore()
        self._last_snap: RTDSnapshot | None = None

        self.scenario_id = scenario_id
        self._scenario: Scenario = load_scenario(scenario_id)

        self._injection_c_in = 0.0    # current inlet boundary condition (tracer)
        self._injecting = False
        self._pulse_remaining = 0.0   # s left in an active rectangular pulse
        self._cost = 0.0              # accumulated cost (pricing wired in Phase 6)

        self._init_objects()

    def _init_objects(self) -> None:
        self._model = build_rtd_model(self.scenario_id)
        seed = scenario_seed(self.scenario_id)
        v = self._scenario.visible
        self._sensor = Photocolorimeter(
            epsilon_b=v.epsilon_b,
            dt_sample=v.dt_sample_s,
            noise_std=v.noise_std,
            A_max=v.A_max,
            seed=seed,
        )

    @property
    def scenario(self) -> Scenario:
        return self._scenario

    @property
    def Q_L_s(self) -> float:
        """Current flow rate (L/s) -- for the diagram's flow display after a
        scenario load or reset. Not a leak: this is the visible flow
        setpoint, not a hidden model parameter."""
        return self._model.Q

    @property
    def tau(self) -> float:
        """Nominal mean residence time V/Q (s). Derived purely from visible
        V and Q -- not the hidden RTD shape -- so it's safe to drive the
        diagram's cosmetic tracer-band animation."""
        return self._model.tau

    # ── Main tick ─────────────────────────────────────────────────────────────

    def tick(self, sim_dt: float) -> None:
        if self._pulse_remaining > 0.0:
            this_dt = min(sim_dt, self._pulse_remaining)
            self._pulse_remaining -= this_dt
            c_out = self._model.step(this_dt, self._injection_c_in)
            if self._pulse_remaining <= 0.0:
                # Pulse ends inside this tick -- integrate the remainder at
                # c_in=0 so the rectangular pulse width stays exact
                # regardless of tick granularity.
                self._injection_c_in = 0.0
                self._injecting = False
                remainder = sim_dt - this_dt
                if remainder > 0.0:
                    c_out = self._model.step(remainder, 0.0)
        else:
            c_out = self._model.step(sim_dt, self._injection_c_in)

        absorbance = self._sensor.sample(c_out, sim_dt)

        self._last_snap = RTDSnapshot(
            sim_time=self._model.t,
            Q=self._model.Q,
            absorbance=absorbance,
            injecting=self._injecting,
            cost=self._cost,
        )
        self.data_store.append(self._last_snap)

    def get_snapshot(self) -> RTDSnapshot | None:
        return self._last_snap

    # ── Injection API ────────────────────────────────────────────────────────

    def inject_pulse(self, m: float, t_pulse: float = RTD_PULSE_WIDTH_S) -> None:
        """Rectangular pulse of dose m over t_pulse seconds (eq. 29)."""
        self._injection_c_in = pulse_concentration(m, self._model.Q, t_pulse)
        self._pulse_remaining = t_pulse
        self._injecting = True
        self._cost += self._scenario.costos.pulso

    def inject_step(self, C0: float) -> None:
        """Open the tracer feed: constant C_in = C0 until stop_injection()."""
        self._injection_c_in = C0
        self._pulse_remaining = 0.0
        self._injecting = True
        self._cost += self._scenario.costos.escalon

    def stop_injection(self) -> None:
        self._injection_c_in = 0.0
        self._pulse_remaining = 0.0
        self._injecting = False

    # ── Parameter updates ─────────────────────────────────────────────────────

    def apply_parameters(self, params: dict) -> None:
        if 'Q_mL_s' in params:
            self._model.set_flow(params['Q_mL_s'] * _ML_S_TO_L_S)

    def set_scenario(self, scenario_id: str) -> None:
        """Switch to a different plant/scenario. Resets the run."""
        self.scenario_id = scenario_id
        self._scenario = load_scenario(scenario_id)
        self.reset()

    def reset(self) -> None:
        self.stop_injection()
        self._cost = 0.0
        self._init_objects()
        self.data_store.clear()
        self._last_snap = None
