"""Tests for reactor_simulation.actuators.HXDynamic — the valve-driven,
exact-analytic-solution heat exchanger used by scada_app's PFREngine
(distinct from HeatExchanger, see hx_dynamic.py's module docstring)."""

import math

import pytest
from reactor_simulation import HXDynamic

_RHO = 1000.0   # kg/m3
_CP = 4180.0    # J/(kg.K)


def _hx(V=0.002, T_hw=333.15, UA_max=100.0, T_initial=288.0):
    return HXDynamic(V=V, rho=_RHO, cp=_CP, T_hw=T_hw, UA_max=UA_max, T_initial=T_initial)


class TestHXDynamic:
    def test_initial_temperature(self):
        hx = _hx(T_initial=290.0)
        assert hx.T == pytest.approx(290.0)

    def test_zero_valve_and_zero_flow_holds_temperature(self):
        """b = Q*rho*cp + UA = 0 -> exp(0) = 1 -> T unchanged regardless of dt."""
        hx = _hx(T_initial=295.0)
        hx.step(dt=50.0, valve=0.0, Q_total=0.0, T_feed=310.0)
        assert hx.T == pytest.approx(295.0)

    def test_zero_valve_with_flow_relaxes_toward_feed_temperature(self):
        """UA = 0 (valve closed) -> T_ss = T_feed regardless of T_hw.

        tau = V/Q = 0.002/1.6667e-6 = 1200 s here; run out to ~8*tau so the
        exponential relaxation is within tolerance of its steady state.
        """
        hx = _hx(T_initial=288.0)
        for _ in range(9600):
            hx.step(dt=1.0, valve=0.0, Q_total=1.6667e-6, T_feed=310.0)
        assert hx.T == pytest.approx(310.0, abs=0.05)

    def test_full_valve_converges_toward_weighted_steady_state(self):
        """Long integration at valve=1 -> T approaches the analytic T_ss."""
        Q = 3.3333e-6
        T_hw = 333.15
        T_feed = 288.0
        UA_max = 100.0
        hx = _hx(T_hw=T_hw, UA_max=UA_max, T_initial=T_feed)
        rcp = _RHO * _CP
        b = Q * rcp + UA_max
        a = Q * rcp * T_feed + UA_max * T_hw
        expected_T_ss = a / b
        for _ in range(5000):
            hx.step(dt=1.0, valve=1.0, Q_total=Q, T_feed=T_feed)
        assert hx.T == pytest.approx(expected_T_ss, rel=1e-3)

    def test_valve_above_one_clips_like_full_open(self):
        hx_over = _hx()
        hx_full = _hx()
        for _ in range(200):
            hx_over.step(dt=1.0, valve=5.0, Q_total=1e-6, T_feed=300.0)
            hx_full.step(dt=1.0, valve=1.0, Q_total=1e-6, T_feed=300.0)
        assert hx_over.T == pytest.approx(hx_full.T)

    def test_valve_below_zero_clips_like_closed(self):
        hx_under = _hx()
        hx_closed = _hx()
        for _ in range(200):
            hx_under.step(dt=1.0, valve=-3.0, Q_total=1e-6, T_feed=300.0)
            hx_closed.step(dt=1.0, valve=0.0, Q_total=1e-6, T_feed=300.0)
        assert hx_under.T == pytest.approx(hx_closed.T)

    def test_reset_restores_initial_temperature(self):
        hx = _hx(T_initial=288.0)
        hx.step(dt=10.0, valve=1.0, Q_total=1e-6, T_feed=350.0)
        assert hx.T != pytest.approx(288.0)
        hx.reset()
        assert hx.T == pytest.approx(288.0)

    def test_reset_with_explicit_temperature(self):
        hx = _hx(T_initial=288.0)
        hx.step(dt=10.0, valve=1.0, Q_total=1e-6, T_feed=350.0)
        hx.reset(T_initial=300.0)
        assert hx.T == pytest.approx(300.0)

    def test_step_returns_the_new_temperature(self):
        hx = _hx()
        result = hx.step(dt=1.0, valve=0.5, Q_total=1e-6, T_feed=300.0)
        assert result == pytest.approx(hx.T)
