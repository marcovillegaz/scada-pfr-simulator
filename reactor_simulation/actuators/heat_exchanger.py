"""
HeatExchanger actuator

General heating/cooling device driven by utility temperature.

Physics:
    Q = UA_eff * (T_utility - T_process)

    Q > 0  →  heat flows into the process  (heating, e.g. steam jacket)
    Q < 0  →  heat flows out of the process (cooling, e.g. cooling water)

The controllable input is the utility temperature T_utility (K), which
represents the temperature of the heating/cooling medium as seen at the
exchanger surface.  In a real plant this is set by the control valve that
adjusts steam pressure or coolant flow rate.
"""

import numpy as np


class HeatExchanger:
    """
    General heat exchanger for heating or cooling.

    Parameters
    ----------
    UA : float
        Overall heat transfer coefficient × area (W/K).
        Combine U and A here because they are inseparable without geometry data.
    T_utility_min : float
        Minimum allowable utility temperature (K).
        Lower limit on what the control valve can achieve.
    T_utility_max : float
        Maximum allowable utility temperature (K).
        Upper limit on what the control valve can achieve.
    time_constant : float
        First-order lag on T_utility_actual (s).
        Models valve and fluid thermal inertia.
    fouling_factor : float
        Fractional reduction of UA due to fouling (0–1).
        UA_eff = UA * (1 - fouling_factor).
    T_initial : float or None
        Initial utility temperature (K).  Defaults to T_utility_min.
    """

    def __init__(
        self,
        UA: float = 100.0,
        T_utility_min: float = 273.15,
        T_utility_max: float = 500.0,
        time_constant: float = 10.0,
        fouling_factor: float = 0.0,
        T_initial: float = None,
    ):
        self.UA = UA
        self.T_utility_min = T_utility_min
        self.T_utility_max = T_utility_max
        self.time_constant = time_constant
        self.fouling_factor = np.clip(fouling_factor, 0.0, 1.0)

        T_init = T_initial if T_initial is not None else T_utility_min
        self.T_utility_setpoint = float(T_init)
        self.T_utility_actual   = float(T_init)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def UA_effective(self) -> float:
        """UA degraded by fouling."""
        return self.UA * (1.0 - self.fouling_factor)

    # ── Control interface ─────────────────────────────────────────────────────

    def set_utility_temperature(self, T_utility: float) -> None:
        """
        Command the utility temperature (K).

        Clips to [T_utility_min, T_utility_max].
        The actual temperature lags behind with first-order dynamics.
        """
        self.T_utility_setpoint = float(
            np.clip(T_utility, self.T_utility_min, self.T_utility_max)
        )

    # ── Time-step methods ─────────────────────────────────────────────────────

    def update(self, T_process: float, dt: float) -> float:
        """
        Advance state by dt and return the instantaneous heat flow (W).

        Parameters
        ----------
        T_process : float
            Current process-side temperature (K).
        dt : float
            Time step (s).

        Returns
        -------
        float
            Q (W) — positive = heat into process, negative = heat out.
        """
        alpha = dt / (self.time_constant + dt)
        self.T_utility_actual += alpha * (self.T_utility_setpoint - self.T_utility_actual)
        return self.get_heat_flow(T_process)

    def get_heat_flow(self, T_process: float) -> float:
        """
        Return instantaneous heat flow Q (W) without advancing state.

        Q = UA_eff * (T_utility_actual - T_process)
        """
        return self.UA_effective * (self.T_utility_actual - T_process)

    # ── Housekeeping ──────────────────────────────────────────────────────────

    def reset(self, T_initial: float = None) -> None:
        """Reset utility temperature to initial conditions."""
        T_init = T_initial if T_initial is not None else self.T_utility_min
        self.T_utility_setpoint = float(T_init)
        self.T_utility_actual   = float(T_init)

    def __repr__(self) -> str:
        return (
            f"HeatExchanger(UA={self.UA:.1f} W/K, "
            f"T_util={self.T_utility_actual:.1f} K, "
            f"T_util_sp={self.T_utility_setpoint:.1f} K)"
        )
