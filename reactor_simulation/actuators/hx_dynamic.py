"""
HXDynamic actuator

Single-node energy balance on a heat exchanger's process-side fluid, driven
by a valve position (0-1) rather than a utility-temperature setpoint.

This is a different control interface from `HeatExchanger` in the same
package -- not a duplicate. `HeatExchanger` commands a utility temperature
and lags toward it (first-order approximation of valve + fluid inertia);
`HXDynamic` commands a valve fraction directly and solves the process-side
energy balance exactly at each step. The two mirror the same split the
reactor models make between `PlugFlow`/`StirredTank` (steady-state,
teaching/script-mode) and `PFRSimulator` (dynamic, drives the live SCADA
engine): `HeatExchanger` is the general-purpose teaching actuator used in
`examples/`; `HXDynamic` is the one wired into `PFREngine`
(`scada_app/engine/pfr_engine.py`), matching the P&ID's valve-position
control and reading directly off the diagram/dialog UI.

Physics:
    dT/dt = (a - b*T) / m_cp
    T(dt) = T_ss + (T0 - T_ss) * exp(-b*dt/m_cp)
    where  a = Q*rho*cp*T_feed + UA*T_hw
           b = Q*rho*cp + UA
           T_ss = a/b

Exact analytic solution -- no ODE solver needed per tick.
"""

from __future__ import annotations

import math


class HXDynamic:
    """Single-node energy balance on the HX process-side fluid, valve-driven."""

    def __init__(self, V: float, rho: float, cp: float, T_hw: float,
                 UA_max: float, T_initial: float):
        self.V      = V
        self.rho    = rho
        self.cp     = cp
        self.T_hw   = T_hw
        self.UA_max = UA_max
        self.T      = T_initial   # current process-side temperature
        self._T_initial = T_initial

    def step(self, dt: float, valve: float, Q_total: float, T_feed: float) -> float:
        UA   = self.UA_max * max(0.0, min(1.0, valve))
        rcp  = self.rho * self.cp
        m_cp = self.V * rcp
        b    = Q_total * rcp + UA
        a    = Q_total * rcp * T_feed + UA * self.T_hw
        T_ss = a / b if b > 0 else T_feed
        self.T = T_ss + (self.T - T_ss) * math.exp(-b * dt / m_cp)
        return self.T

    def reset(self, T_initial: float | None = None) -> None:
        self.T = T_initial if T_initial is not None else self._T_initial
