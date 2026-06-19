"""
Core reactor physics module

Contains:
- Reactor base classes and implementations (PFR, CSTR, etc.)
- Reaction kinetics
- State variables
"""

from .reactor import Reactor, PlugFlow, StirredTank, RecyclePlugFlow
from .kinetics import Reaction
from .state import ReactorState

__all__ = [
    "Reactor",
    "PlugFlow",
    "StirredTank",
    "RecyclePlugFlow",
    "Reaction",
    "ReactorState",
]
