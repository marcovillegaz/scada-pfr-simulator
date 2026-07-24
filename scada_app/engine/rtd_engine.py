from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from reactor_simulation.sensors import Photocolorimeter
from reactor_simulation.models.packed_bed import pulse_concentration

from scenarios.loader import build_rtd_model, sensor_seed, load_scenario, Scenario

from constants import RTD_PULSE_WIDTH_S
from engine.base_engine import BaseEngine
from engine.data_store import RTDSnapshot

_L_MIN_TO_L_S = 1.0 / 60.0


class RTDEngine(BaseEngine):
    """
    RTD (Experiencia 3) tick engine -- the analogue of PFREngine for the
    tracer / residence-time-distribution experiment.

    Owns the hidden-truth PackedBedRTD model and the Photocolorimeter that
    filters it into student-visible absorbance. Injections (pulse / step)
    are boundary conditions applied to PackedBedRTD.step(dt, c_in): the same
    segmented-integration pattern PFREngine uses for the PFR, just with the
    tracer inlet concentration as the thing that changes tick to tick
    instead of temperature/flow setpoints. See docs/shared/CONVENTION.md for
    BaseEngine's shared contract.
    """

    def __init__(self, scenario_id: str, parent=None):
        super().__init__(parent)
        self._last_snap: RTDSnapshot | None = None

        self.scenario_id = scenario_id
        self._scenario: Scenario = load_scenario(scenario_id)

        self._injection_c_in = 0.0    # current inlet boundary condition (tracer)
        self._injecting = False
        self._pulse_remaining = 0.0   # s left in an active rectangular pulse

        self._init_objects()

    def _init_objects(self) -> None:
        self._model = build_rtd_model(self.scenario_id)
        seed = sensor_seed()
        s = self._scenario.visible.sensor
        self._sensor = Photocolorimeter(
            epsilon_b=s.epsilon_b,
            dt_sample=s.dt_sample_s,
            noise_std=s.noise_std,
            A_max=s.A_max,
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
        )
        self.data_store.append(self._last_snap)

    # ── Injection API ────────────────────────────────────────────────────────

    def inject_pulse(self, m: float, t_pulse: float = RTD_PULSE_WIDTH_S) -> None:
        """Rectangular pulse of dose m over t_pulse seconds (eq. 29)."""
        self._injection_c_in = pulse_concentration(m, self._model.Q, t_pulse)
        self._pulse_remaining = t_pulse
        self._injecting = True

    def inject_step(self, C0: float) -> None:
        """Open the tracer feed: constant C_in = C0 until stop_injection()."""
        self._injection_c_in = C0
        self._pulse_remaining = 0.0
        self._injecting = True

    def stop_injection(self) -> None:
        self._injection_c_in = 0.0
        self._pulse_remaining = 0.0
        self._injecting = False

    # ── Parameter updates ─────────────────────────────────────────────────────

    def apply_parameters(self, params: dict) -> None:
        if 'Q_L_min' in params:
            self._model.set_flow(params['Q_L_min'] * _L_MIN_TO_L_S)

    def set_scenario(self, scenario_id: str) -> None:
        """Switch to a different plant/scenario. Resets the run."""
        self.scenario_id = scenario_id
        self._scenario = load_scenario(scenario_id)
        self.reset()

    def reset(self) -> None:
        self.stop_injection()
        self._init_objects()
        self._clear_run()
