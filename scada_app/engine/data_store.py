from __future__ import annotations

import dataclasses
from collections import deque
from dataclasses import dataclass
from typing import List

import pandas as pd

from constants import PLOT_BUFFER_SIZE


@dataclass(frozen=True)
class EngineSnapshot:
    sim_time: float
    true_temp: float
    measured_temp: float
    setpoint: float
    concentration: float
    measured_concentration: float
    flow_rate: float
    heat_flow: float
    pid_p: float
    pid_i: float
    pid_d: float


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
        if not self.run_log:
            return pd.DataFrame()
        return pd.DataFrame([dataclasses.asdict(s) for s in self.run_log])
