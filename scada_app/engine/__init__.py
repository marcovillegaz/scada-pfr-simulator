"""
Engine package -- one tick engine per teaching module, sharing BaseEngine's
contract (see docs/shared/CONVENTION.md). Curated so consumers import from
here instead of deep-pathing into individual engine modules.
"""

from .base_engine import BaseEngine
from .pfr_engine import PFREngine
from .rtd_engine import RTDEngine
from .data_store import DataStore, EngineSnapshot, RTDSnapshot

__all__ = [
    "BaseEngine",
    "PFREngine",
    "RTDEngine",
    "DataStore",
    "EngineSnapshot",
    "RTDSnapshot",
]
