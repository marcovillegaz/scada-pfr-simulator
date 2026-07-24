"""
PackedBedRTD — compartment-network model of hydrodynamic non-idealities in a
packed bed, for the residence-time-distribution (RTD) tracer experiment.

Combined model of Levenspiel: a main path (cascade of N_m CSTRs) in parallel
with a bypass channel (cascade of N_c CSTRs), plus a dead zone exchanging
with one tank of the main path. See docs/FUNDAMENTS_EXP3.md §5 for the full
derivation; this is the *hidden ground truth* the RTD module holds back from
the student — only Photocolorimeter-filtered measurements are meant to reach
the UI (outlet_concentration() exists for internal use and test verification
only).

Deliberately NOT built on the PFR's Method-of-Lines + upwind engine
(pfr_model.py): upwind numerical diffusion would be the same order of
magnitude as the physical dispersion this module exists to measure, making
the effective Péclet number uncontrollable (see docs/PLAN.md §2). This is
instead a small linear, non-stiff ODE system with no spatial discretization.

State vector: y = [C_1..C_Nm, C_1^c..C_Nc^c, C_d]   (size N_m + N_c + 1)

Units are SI-consistent but unit-system-agnostic (any consistent system
works, e.g. L and L/s, matching the lab-facing JSON scenarios):
    C            concentration (mass or moles / volume)
    V, Q         volume, volume/time
    f            — (fraction, dimensionless)
    phi_d, phi_c — (fraction, dimensionless)
    k_ex         1/time
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp


def _rtd_rhs(t: float, y: np.ndarray, params: dict) -> np.ndarray:
    """RHS of the compartment network (eqs. 25-27 in FUNDAMENTS_EXP3.md)."""
    N_m  = params['N_m']
    N_c  = params['N_c']
    j    = params['j']
    Q_m  = params['Q_m']
    Q_c  = params['Q_c']
    v_m  = params['v_m']
    v_c  = params['v_c']
    q_ex = params['q_ex']
    V_d  = params['V_d']
    c_in = params['c_in']

    main = y[:N_m]
    chan = y[N_m:N_m + N_c]
    Cd   = y[N_m + N_c]

    # Main path — cascade of N_m CSTRs (eq. 26). The dead zone couples only
    # into tank j (delta_ij in the paper); j defaults to an interior tank
    # (N_m // 2) so the tail doesn't depend on a boundary artefact.
    dmain = np.zeros(N_m)
    if N_m > 0 and v_m > 0:
        prev = c_in
        for i in range(N_m):
            Ci = main[i]
            dmain[i] = Q_m * (prev - Ci) / v_m
            if i == j:
                dmain[i] += q_ex * (Cd - Ci) / v_m
            prev = Ci

    # Bypass channel — cascade of N_c CSTRs (eq. 25). Decoupled (v_c == 0)
    # when f=0: the channel then carries no flow, and its state is
    # irrelevant since it is weighted by f=0 in the outlet mix (eq. 28).
    dchan = np.zeros(N_c)
    if N_c > 0 and v_c > 0:
        prev = c_in
        for k in range(N_c):
            Ck = chan[k]
            dchan[k] = Q_c * (prev - Ck) / v_c
            prev = Ck

    # Dead zone — no net flow, only exchange with tank j (eq. 27). Decoupled
    # (V_d == 0) when phi_d=0: q_ex is then 0 too, so the state stays inert.
    dCd = q_ex * (main[j] - Cd) / V_d if (V_d > 0 and N_m > 0) else 0.0

    return np.concatenate([dmain, dchan, [dCd]])


class PackedBedRTD:
    """
    Compartment-network RTD model — the hidden ground truth behind the RTD
    tracer experiment. Owns its own integrator (solve_ivp / RK45), following
    the same pattern as PFRSimulator (reactor_simulation/core/pfr_model.py):
    a `step(dt, ...)` that integrates one segment and carries the internal
    state forward, so the caller can change the boundary condition tick by
    tick without losing the profile in between.

    Parameters
    ----------
    f : float
        Fraction of Q that bypasses through the channel (0-1).
    phi_d : float
        Fraction of V occupied by the dead zone (0-1).
    k_ex : float
        Dead-zone exchange coefficient (1/time).
    gamma : float
        Channel time ratio tau_c/tau; fixes phi_c = gamma * f (eq. 23a).
        NOT an independent parameter — see FUNDAMENTS_EXP3.md §5.1 for why a
        constant phi_c is a bug: it would turn the channel into an
        undeclared second dead zone as f -> 0, breaking eq. 33 (see
        tests/test_rtd_packed_bed.py::test_volume_split_identity).
    N_m : int
        Number of CSTRs in the main path (hidden truth, typically 10-15).
    N_c : int
        Number of CSTRs in the bypass channel (hidden truth, typically 1-3).
    V : float
        Total vessel volume.
    Q : float
        Feed volumetric flow rate.
    j : int or None
        0-indexed main-path tank the dead zone couples to. Defaults to
        N_m // 2 (an interior tank, so the tail doesn't depend on a
        boundary artefact — see PLAN.md §5.1).
    """

    def __init__(
        self,
        f: float,
        phi_d: float,
        k_ex: float,
        gamma: float,
        N_m: int,
        N_c: int,
        V: float,
        Q: float,
        j: int | None = None,
    ):
        self.f = f
        self.phi_d = phi_d
        self.k_ex = k_ex
        self.gamma = gamma
        self.N_m = N_m
        self.N_c = N_c
        self.V = V
        self.Q = Q
        self.j = j if j is not None else N_m // 2

        self._rebuild()
        self.reset()

    # ── Derived quantities ────────────────────────────────────────────────────

    def _rebuild(self) -> None:
        """Recompute the flow/volume split from (f, phi_d, gamma, N_m, N_c,
        V, Q). Called on construction and whenever Q changes (set_flow)."""
        self.phi_c = self.gamma * self.f                       # eq. 23a
        self.V_m = self.V * (1 - self.phi_d - self.phi_c)       # eq. 23b
        self.V_c = self.phi_c * self.V
        self.V_d = self.phi_d * self.V
        self.v_m = self.V_m / self.N_m if self.N_m > 0 else 0.0
        self.v_c = self.V_c / self.N_c if (self.N_c > 0 and self.f > 0) else 0.0
        self.q_ex = self.k_ex * self.V_d                        # eq. 24
        self.Q_m = (1 - self.f) * self.Q                        # eq. 22
        self.Q_c = self.f * self.Q
        self.tau = self.V / self.Q if self.Q > 0 else float('inf')

    def set_flow(self, Q: float) -> None:
        """Change Q, preserving internal state (segmented integration —
        mirrors PFRSimulator.update_params for a mid-run setpoint change)."""
        self.Q = Q
        self._rebuild()

    # ── Time-step ──────────────────────────────────────────────────────────────

    def step(self, dt: float, c_in: float) -> float:
        """
        Integrate one segment with c_in held constant as the inlet boundary
        condition (eq. 29). Only the boundary condition changes between
        segments — the internal profile carries over. This is the same
        segmented-integration pattern PFREngine uses for the PFR, and
        is how injections (pulse / step) get built up tick by tick by the
        caller: hold c_in at C_p for the pulse width, then drop it to 0.

        Returns the new outlet_concentration().
        """
        if dt <= 0:
            return self.outlet_concentration()
        sol = solve_ivp(
            _rtd_rhs, [self.t, self.t + dt], self.y,
            args=(self._rhs_params(c_in),), method='RK45',
            rtol=1e-8, atol=1e-10,
        )
        if not sol.success:
            raise RuntimeError(f"PackedBedRTD integration failed: {sol.message}")
        self.y = sol.y[:, -1]
        self.t += dt
        return self.outlet_concentration()

    def integrate_dense(self, dt: float, c_in: float, n_eval: int = 200):
        """
        Like step(), but also returns the dense (t, C_out) trajectory across
        the segment instead of only the final value. Used for analysis,
        plotting, and the numerical-validation tests in
        tests/test_rtd_packed_bed.py (moment integration needs the whole
        curve, not just an endpoint).
        """
        if dt <= 0:
            return np.array([self.t]), np.array([self.outlet_concentration()])
        t_eval = np.linspace(self.t, self.t + dt, n_eval)
        sol = solve_ivp(
            _rtd_rhs, [self.t, self.t + dt], self.y,
            args=(self._rhs_params(c_in),), method='RK45',
            t_eval=t_eval, rtol=1e-8, atol=1e-10,
        )
        if not sol.success:
            raise RuntimeError(f"PackedBedRTD integration failed: {sol.message}")
        self.y = sol.y[:, -1]
        self.t += dt
        c_out = self._outlet_from_state(sol.y)
        return t_eval, c_out

    def _rhs_params(self, c_in: float) -> dict:
        return {
            'N_m': self.N_m, 'N_c': self.N_c, 'j': self.j,
            'Q_m': self.Q_m, 'Q_c': self.Q_c,
            'v_m': self.v_m, 'v_c': self.v_c,
            'q_ex': self.q_ex, 'V_d': self.V_d,
            'c_in': c_in,
        }

    # ── Output ─────────────────────────────────────────────────────────────────

    def outlet_concentration(self) -> float:
        """C_out (eq. 28). Internal use / test verification only — the
        student-facing measurement is Photocolorimeter's absorbance, not
        this exact value (see docs/PLAN.md §5.2)."""
        return float(self._outlet_from_state(self.y.reshape(-1, 1))[0])

    def _outlet_from_state(self, y_matrix: np.ndarray) -> np.ndarray:
        """Vectorized eq. 28 over a (n_states, n_times) trajectory matrix."""
        n = y_matrix.shape[1]
        C_Nm = y_matrix[self.N_m - 1, :] if self.N_m > 0 else np.zeros(n)
        C_Nc = (y_matrix[self.N_m + self.N_c - 1, :]
                if (self.N_c > 0 and self.f > 0) else np.zeros(n))
        return self.f * C_Nc + (1 - self.f) * C_Nm

    # ── Housekeeping ──────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset to a clean (zero-concentration) bed at t=0."""
        self.t = 0.0
        self.y = np.zeros(self.N_m + self.N_c + 1)

    def __repr__(self) -> str:
        return (
            f"PackedBedRTD(f={self.f:.3f}, phi_d={self.phi_d:.3f}, "
            f"N_m={self.N_m}, N_c={self.N_c}, tau={self.tau:.1f})"
        )


def pulse_concentration(m: float, Q: float, t_pulse: float) -> float:
    """C_p for a rectangular pulse of width t_pulse delivering dose m at flow
    Q (eq. 29: m = Q * C_p * t_pulse)."""
    return m / (Q * t_pulse)
