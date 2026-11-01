from __future__ import annotations

from collections import deque
from dataclasses import dataclass, fields
from typing import Generic, List, TypeVar, Union

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
    meant to see (t, Q, A -- see scada_app/scenarios/loader.py's
    visible/oculto split)."""
    sim_time:   float   # s
    Q:          float   # L/s  — current flow rate (visible)
    absorbance: float   # -    — AIT-201 reading (Photocolorimeter output)
    injecting:  bool    # whether a pulse or step injection is in progress


Snapshot = Union[EngineSnapshot, RTDSnapshot]
SnapT = TypeVar("SnapT", bound=Snapshot)


class DataStore(Generic[SnapT]):
    """Ring-buffer + full run log for one engine's ticks. Generic over
    whichever Snapshot dataclass the owning engine produces -- every module
    (PFR, RTD, future ones) shares this same store rather than each needing
    its own."""

    def __init__(self, plot_buffer_size: int = PLOT_BUFFER_SIZE):
        self.plot_buffer: deque[SnapT] = deque(maxlen=plot_buffer_size)
        self.run_log: List[SnapT] = []

    def append(self, snap: SnapT) -> None:
        self.plot_buffer.append(snap)
        self.run_log.append(snap)

    def clear(self) -> None:
        self.plot_buffer.clear()
        self.run_log.clear()

    def to_dataframe(self) -> pd.DataFrame:
        """Scalar columns only, in declaration order -- array/tuple fields
        (e.g. PFR's spatial CA/CB/T profiles) are excluded. Derived from
        whichever dataclass self.run_log actually holds, so this works for
        any module's Snapshot type without a per-module override."""
        if not self.run_log:
            return pd.DataFrame()
        sample = self.run_log[0]
        scalar_fields = [
            f.name for f in fields(sample)
            if not isinstance(getattr(sample, f.name), (tuple, list))
        ]
        rows = [
            {name: getattr(s, name) for name in scalar_fields}
            for s in self.run_log
        ]
        return pd.DataFrame(rows)
