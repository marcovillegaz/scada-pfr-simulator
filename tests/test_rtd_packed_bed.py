"""Numerical validation suite for reactor_simulation.models.packed_bed.PackedBedRTD.

This is the mandatory validation suite that must pass before any UI or
engine is wired to the model. Each test cross-references the equation it
verifies in docs/modules/rtd/fundamentals.md.

Reference scenario: V = 2.0 L, Q = 0.02 L/s -> tau = 100 s, N_m = 12, N_c = 2,
gamma = 0.30 -- all within the "healthy bed" calibration ranges.
"""

from __future__ import annotations

import numpy as np
import pytest

from reactor_simulation.models.packed_bed import PackedBedRTD, pulse_concentration

# numpy 2.0 renamed trapz -> trapezoid; fall back for older pinned installs
# (pyproject.toml declares numpy>=1.20.0 with no upper bound).
_trapz = getattr(np, "trapezoid", None) or np.trapz

# ── Reference scenario ──────────────────────────────────────────────────────

V = 2.0          # L
Q = 0.02         # L/s
TAU = V / Q      # 100 s
N_M = 12
N_C = 2
GAMMA = 0.30
T_PULSE = 1.0    # s, << TAU (ratio 0.01, well under the 0.05 rule of thumb — §2.1)
M_DOSE = 0.02    # mol -> C_p = 1.0 mol/L (eq. 29)


def _model(f, phi_d, k_ex, gamma=GAMMA, N_m=N_M, N_c=N_C, V=V, Q=Q):  # noqa: A002 (shadow ok, local scope)
    return PackedBedRTD(f=f, phi_d=phi_d, k_ex=k_ex, gamma=gamma,
                         N_m=N_m, N_c=N_c, V=V, Q=Q)


def _run_pulse(model, m=M_DOSE, t_pulse=T_PULSE, t_total=10 * TAU, n_eval=4000):
    """Deliver a rectangular pulse of dose m over t_pulse (eq. 29), then
    integrate the tail out to t_total. Two integrate_dense() segments --
    fast, since RK45 sub-steps internally regardless of the external segment
    span (this is the segmented-integration pattern, not a fixed-dt loop)."""
    Cp = pulse_concentration(m, model.Q, t_pulse)
    n1 = max(50, int(n_eval * t_pulse / t_total))
    t1, c1 = model.integrate_dense(t_pulse, Cp, n_eval=n1)
    t2, c2 = model.integrate_dense(t_total - t_pulse, 0.0, n_eval=n_eval)
    return np.concatenate([t1, t2]), np.concatenate([c1, c2])


def _run_step(model, C0, t_total=10 * TAU, n_eval=4000):
    return model.integrate_dense(t_total, C0, n_eval=n_eval)


def _moments(t, c):
    """First moment (mean residence time) and variance from a C(t) curve,
    via trapezoidal quadrature (eqs. 9-10, 14)."""
    area = _trapz(c, t)
    t_mean = _trapz(t * c, t) / area
    variance = _trapz((t - t_mean) ** 2 * c, t) / area
    return t_mean, variance, area


class TestPackedBedRTD:

    # 1. Tracer conservation ────────────────────────────────────────────────

    def test_tracer_conservation(self):
        """eq. 5: integral(Q*C_out dt) = m_injected, within 1%, to t -> 10*tau."""
        model = _model(f=0.15, phi_d=0.15, k_ex=0.002)
        t, c = _run_pulse(model)
        recovered = model.Q * _trapz(c, t)
        assert recovered == pytest.approx(M_DOSE, rel=0.01)

    # 2. Normalization ───────────────────────────────────────────────────────

    def test_normalization(self):
        """eq. 1/4: integral(E dt) = 1 over the same observation window."""
        model = _model(f=0.15, phi_d=0.15, k_ex=0.002)
        t, c = _run_pulse(model)
        area = _trapz(c, t)
        E = c / area
        assert _trapz(E, t) == pytest.approx(1.0, rel=0.01)

    # 3. First moment without pathology ─────────────────────────────────────

    def test_first_moment_no_pathology(self):
        """eq. 11: with f=0, phi_d=0 -> t_bar_m = tau + t_pulse/2, within 1%.

        This is the test that catches the phi_c-constant defect described in
        docs/modules/rtd/fundamentals.md §5.1: if phi_c were an independent parameter
        instead of gamma*f, f=0 would still leave a channel volume with no
        flow through it -- an undeclared second dead zone -- and t_bar_m
        would fall short of tau even with phi_d=0.
        """
        model = _model(f=0.0, phi_d=0.0, k_ex=0.0)
        t, c = _run_pulse(model)
        t_mean, _, _ = _moments(t, c)
        expected = TAU + T_PULSE / 2
        assert t_mean == pytest.approx(expected, rel=0.01)

    # 4. First moment with dead zone, full window ───────────────────────────

    def test_first_moment_dead_zone_full_window(self):
        """eq. 34: with k_ex > 0 and a long window (10*tau), t_bar_m -> tau.

        k_ex is chosen so tau_d = 1/k_ex = tau, i.e. the 10*tau window is
        10*tau_d -- long enough that essentially all of the dead-zone tail
        is captured (see §7: the commonly "measured" volume-muerto is a
        truncation artefact of a finite observation window, not a model
        property).
        """
        model = _model(f=0.0, phi_d=0.15, k_ex=0.01)
        t, c = _run_pulse(model, t_total=10 * TAU)
        t_mean, _, _ = _moments(t, c)
        assert t_mean == pytest.approx(TAU, rel=0.01)

    # 5. Variance without pathology ─────────────────────────────────────────

    def test_variance_no_pathology(self):
        """eq. 17: with f=0, phi_d=0 -> sigma^2 ~ tau^2/N_m, within 2%.

        Compared against sigma^2 (not sigma_theta^2 = sigma^2/t_bar_m^2): the
        pulse-width displacement of t_bar_m makes sigma_theta^2 differ from
        1/N_m by ~2% on its own, which would be a false negative here.
        """
        model = _model(f=0.0, phi_d=0.0, k_ex=0.0)
        t, c = _run_pulse(model)
        _, variance, _ = _moments(t, c)
        expected = TAU ** 2 / N_M
        assert variance == pytest.approx(expected, rel=0.02)

    # 5b. Volume-split identity ──────────────────────────────────────────────

    @pytest.mark.parametrize("f,phi_d,gamma", [
        (0.15, 0.15, 0.30),
        (0.25, 0.10, 0.40),
        (0.0,  0.20, 0.30),   # f=0: the phi_c-constant defect surfaces here too
    ])
    def test_volume_split_identity(self, f, phi_d, gamma):
        """eq. 33: with k_ex=0, t_bar_m = V*(1-phi_d)/Q + t_pulse/2 for any
        f and gamma -- independent of how the swept volume is split between
        main path and channel. The most sensitive test for volume-accounting
        bugs in the f/phi_c/gamma reparametrization (§5.1)."""
        model = _model(f=f, phi_d=phi_d, k_ex=0.0, gamma=gamma)
        t, c = _run_pulse(model, t_total=10 * TAU)
        t_mean, _, _ = _moments(t, c)
        expected = V * (1 - phi_d) / Q + T_PULSE / 2
        assert t_mean == pytest.approx(expected, rel=0.01)

    # 6. Pulse-step consistency ──────────────────────────────────────────────

    def test_pulse_step_consistency(self):
        """eqs. 6-7: F(t) from a step response matches the cumulative
        integral of E(t) from a pulse response, within sampling tolerance."""
        model_pulse = _model(f=0.15, phi_d=0.15, k_ex=0.002)
        t_p, c_p = _run_pulse(model_pulse, t_total=10 * TAU)
        area = _trapz(c_p, t_p)
        E = c_p / area
        F_from_pulse = np.concatenate([
            [0.0],
            np.cumsum((E[1:] + E[:-1]) / 2 * np.diff(t_p)),
        ])

        C0 = 1.0
        model_step = _model(f=0.15, phi_d=0.15, k_ex=0.002)
        t_s, c_s = _run_step(model_step, C0=C0, t_total=10 * TAU)
        F_from_step = c_s / C0

        # Compare on a common, coarser grid -- cumulative trapz amplifies
        # small grid-alignment differences near the origin.
        t_common = np.linspace(0, 8 * TAU, 200)
        F_p = np.interp(t_common, t_p, F_from_pulse)
        F_s = np.interp(t_common, t_s, F_from_step)
        assert np.max(np.abs(F_p - F_s)) < 0.03

    # 7. Segmented-integration independence ──────────────────────────────────

    def test_segmented_integration_independence(self):
        """A run executed as one big step() call must match the same run
        chopped into many small step() calls -- with Q perturbed away and
        restored mid-run -- as long as the boundary condition (c_in) itself
        never changes. Mirrors how PFREngine ticks the PFR in small
        segments."""
        params = dict(f=0.15, phi_d=0.15, k_ex=0.002, gamma=0.30,
                      N_m=N_M, N_c=N_C, V=V, Q=Q)
        tail = 5 * TAU - T_PULSE

        ref = PackedBedRTD(**params)
        Cp = pulse_concentration(M_DOSE, ref.Q, T_PULSE)
        ref.step(T_PULSE, Cp)
        ref.step(tail, 0.0)
        c_ref = ref.outlet_concentration()

        test_model = PackedBedRTD(**params)
        test_model.step(T_PULSE, Cp)
        dt = 5.0
        elapsed = 0.0
        while elapsed < tail:
            this_dt = min(dt, tail - elapsed)
            if abs(elapsed - tail / 2) < dt:
                test_model.set_flow(Q * 1.5)   # perturb...
                test_model.set_flow(Q)          # ...and restore before stepping
            test_model.step(this_dt, 0.0)
            elapsed += this_dt
        c_test = test_model.outlet_concentration()

        assert c_test == pytest.approx(c_ref, rel=1e-3)
        assert test_model.t == pytest.approx(ref.t, rel=1e-9)


class TestPackedBedRTDEdgeCases:
    """Singularities called out in docs/modules/rtd/fundamentals.md §5.1:
    f=0 (no channel flow) and phi_d=0 (no dead zone) must not raise or
    produce NaNs."""

    def test_zero_bypass_fraction(self):
        model = _model(f=0.0, phi_d=0.10, k_ex=0.002)
        c_out = model.step(TAU, 1.0)
        assert np.isfinite(c_out)
        assert model.v_c == 0.0

    def test_zero_dead_zone(self):
        model = _model(f=0.15, phi_d=0.0, k_ex=0.002)
        c_out = model.step(TAU, 1.0)
        assert np.isfinite(c_out)
        assert model.V_d == 0.0
        assert model.q_ex == 0.0

    def test_zero_bypass_and_dead_zone(self):
        model = _model(f=0.0, phi_d=0.0, k_ex=0.0)
        c_out = model.step(TAU, 1.0)
        assert np.isfinite(c_out)
