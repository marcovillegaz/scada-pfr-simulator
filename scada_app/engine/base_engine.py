"""
Shared engine contract every module engine (PFREngine, RTDEngine, and any
future module's engine) implements. See docs/shared/CONVENTION.md for the
full module convention this codifies.

A module engine orchestrates `reactor_simulation` objects behind a uniform
tick/snapshot/parameter/reset interface so the workspaces, tabs, and widgets
that drive it don't need to know which module they're talking to. It owns no
physics itself -- physics lives in reactor_simulation; the engine composes it.
"""
from __future__ import annotations

from PyQt6.QtCore import QObject

from engine.data_store import DataStore


class BaseEngine(QObject):
    """Base class for a module's tick engine.

    Concrete subclasses must implement:
        _init_objects()          -- build this module's domain objects
        tick(sim_dt)             -- advance one simulation step, produce a
                                     Snapshot, and store it via self.data_store
        apply_parameters(params) -- accept a dict of student-editable inputs
        reset()                  -- return to the module's initial state

    `get_snapshot()` and `_clear_run()` are shared here since every engine's
    implementation of them is identical.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_store = DataStore()
        self._last_snap = None

    # ── Shared ────────────────────────────────────────────────────────────────

    def get_snapshot(self):
        """Return the most recent snapshot, or None before the first tick."""
        return self._last_snap

    def _clear_run(self) -> None:
        """Common tail of reset(): drop the buffered run and last snapshot.
        Subclasses call this after restoring their own domain state."""
        self.data_store.clear()
        self._last_snap = None

    # ── Subclass contract ────────────────────────────────────────────────────

    def _init_objects(self) -> None:
        """Construct this module's reactor_simulation objects (models,
        sensors, actuators, controllers)."""
        raise NotImplementedError

    def tick(self, sim_dt: float) -> None:
        """Advance the simulation by sim_dt seconds and store a new
        snapshot in self.data_store."""
        raise NotImplementedError

    def apply_parameters(self, params: dict) -> None:
        """Apply a dict of student-editable parameter updates."""
        raise NotImplementedError

    def reset(self) -> None:
        """Return the engine to its initial state (see _clear_run())."""
        raise NotImplementedError
