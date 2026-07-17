from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import List

import pandas as pd

from constants import PLOT_BUFFER_SIZE


@dataclass(frozen=True)
class EngineSnapshot:
    sim_time:    float
    CA_out:      float   # mol/L — outlet concentration A
    CB_out:      float   # mol/L — outlet concentration B
    T_out:       float   # K     — PFR outlet temperature
    X_out:       float   # -     — fractional conversion of A
    CA_in:       float   # mol/L — mixed inlet concentration A
    CB_in:       float   # mol/L — mixed inlet concentration B
    T_in:        float   # K     — HX outlet = PFR inlet temperature
    T_reactor:   float   # K     — mean reactor temperature = (T_in + T_out) / 2
    T_setpoint:  float   # K     — PID setpoint for T_reactor
    valve:       float   # 0-1   — hot-water valve position (PID output)
    Qa0:         float   # m3/s  — feed A volumetric flow (before mixing)
    Qb0:         float   # m3/s  — feed B volumetric flow (before mixing)
    Q_in:        float   # m3/s  — total flow at PFR inlet
    velocity:    float   # m/s   — superficial velocity in PFR
    conductivity: float  # mS/cm — CT-101 reading
    CA_profile:  tuple   # (N,) mol/L
    CB_profile:  tuple   # (N,) mol/L
    T_profile:   tuple   # (N,) K


@dataclass(frozen=True)
class RTDSnapshot:
    """One tick of the RTD (Experiencia 3) engine. Deliberately carries no
    true concentration or hidden-model field -- only what the student is
    meant to see (docs/PLAN.md §5.4 GET /rtd/state: t, Q, A, cost)."""
    sim_time:   float   # s
    Q:          float   # L/s  — current flow rate (visible)
    absorbance: float   # -    — AIT-201 reading (Photocolorimeter output)
    injecting:  bool    # whether a pulse or step injection is in progress
    cost:       float   # accumulated cost for this run


class DataStore:
    def __init__(self, plot_buffer_size: int = PLOT_BUFFER_SIZE):
        self.plot_buffer: deque[EngineSnapshot] = deque(maxlen=plot_buffer_size)
        self.run_log: List[EngineSnapshot] = []

    def append(self, snap: EngineSnapshot) -> None:
        self.plot_buffer.append(snap)
        self.run_log.append(snap)

    def clear(self) -> None:
        self.plot_buffer.clear()
        self.run_log.clear()

    def to_dataframe(self) -> pd.DataFrame:
        """Returns scalar columns only (spatial profiles excluded)."""
        if not self.run_log:
            return pd.DataFrame()
        rows = [
            {
                'sim_time':   s.sim_time,
                'CA_out':     s.CA_out,
                'CB_out':     s.CB_out,
                'T_out':      s.T_out,
                'X_out':      s.X_out,
                'CA_in':      s.CA_in,
                'CB_in':      s.CB_in,
                'T_in':       s.T_in,
                'T_reactor':  s.T_reactor,
                'valve':      s.valve,
                'Qa0':        s.Qa0,
                'Qb0':        s.Qb0,
                'Q_in':       s.Q_in,
                'velocity':       s.velocity,
                'conductivity':   s.conductivity,
            }
            for s in self.run_log
        ]
        return pd.DataFrame(rows)
