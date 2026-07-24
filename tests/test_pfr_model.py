"""Tests for reactor_simulation.models.pfr.PFRSimulator -- the dynamic
Method-of-Lines PFR model that drives the live PFREngine. Previously
untested: test_reactor.py only covers the *analytic* PlugFlow model, not
this time-stepping engine, despite it being the physics the app actually
runs (see docs/NEXT_STEPS.md's coverage-gap note).
"""

from __future__ import annotations

import numpy as np
import pytest

from reactor_simulation.models.pfr import PFRSimulator


def _params(**overrides) -> dict:
    p = dict(
        N=10, L=1.0, u=0.1,
        CA_in=1.0, CB_in=1.0,
        T_in=300.0, T_amb=300.0,
        h_loss=0.0,
        k0=0.0, Ea=0.0, dHr=0.0,
        rho=1000.0, cp=4180.0,
    )
    p.update(overrides)
    return p


class TestInitialState:
    def test_state_starts_uniform_at_inlet_values(self):
        sim = PFRSimulator(_params(CA_in=2.0, CB_in=3.0, T_in=310.0, N=5))
        N = 5
        assert np.allclose(sim.state[:N], 2.0)
        assert np.allclose(sim.state[N:2 * N], 3.0)
        assert np.allclose(sim.state[2 * N:], 310.0)
        assert sim.t == pytest.approx(0.0)

    def test_x_out_zero_with_zero_inlet_concentration(self):
        """X_out's ternary guards CA_in=0 -> 0.0 rather than dividing by zero."""
        sim = PFRSimulator(_params(CA_in=0.0))
        out = sim.step(1.0)
        assert out['X_out'] == pytest.approx(0.0)


class TestNoReactionIsSteadyState:
    """k0=0 (no reaction) + h_loss=0 (adiabatic) + T_in=T_amb: nothing should
    change, since the profile starts already equal to the inlet boundary
    condition everywhere -- a pure-convection sanity check."""

    def test_concentrations_and_temperature_unchanged(self):
        sim = PFRSimulator(_params())
        out = sim.step(5.0)
        assert out['CA_out'] == pytest.approx(1.0, rel=1e-3)
        assert out['CB_out'] == pytest.approx(1.0, rel=1e-3)
        assert out['T_out'] == pytest.approx(300.0, rel=1e-3)
        assert out['X_out'] == pytest.approx(0.0, abs=1e-3)


class TestReactionConsumesReactants:
    def test_conversion_increases_with_reaction(self):
        """k0 > 0 -> some A is consumed by the time it reaches the outlet."""
        sim = PFRSimulator(_params(k0=0.1))
        tau = 1.0 / 0.1   # L/u
        out = sim.step(tau)
        assert out['CA_out'] < 1.0
        assert out['CB_out'] < 1.0
        assert out['X_out'] > 0.0

    def test_reaction_releases_heat_when_exothermic(self):
        """Negative dHr (exothermic) with adiabatic walls -> outlet T rises
        above the isothermal-inlet baseline."""
        sim = PFRSimulator(_params(k0=0.1, dHr=-50000.0))
        tau = 1.0 / 0.1
        out = sim.step(tau)
        assert out['T_out'] > 300.0

    def test_wall_heat_loss_cools_the_reactor(self):
        """h_loss > 0 with T_amb below T_in pulls the outlet temperature down
        even with no reaction heat (dHr=0)."""
        sim = PFRSimulator(_params(h_loss=8000.0, T_amb=280.0, T_in=300.0))
        out = sim.step(5.0)
        assert out['T_out'] < 300.0

    def test_higher_k0_gives_more_conversion(self):
        tau = 1.0 / 0.1
        sim_slow = PFRSimulator(_params(k0=0.05))
        sim_fast = PFRSimulator(_params(k0=0.5))
        out_slow = sim_slow.step(tau)
        out_fast = sim_fast.step(tau)
        assert out_fast['X_out'] > out_slow['X_out']


class TestUpdateParamsAndReset:
    def test_update_params_changes_inlet_boundary_condition(self):
        """Segmented integration: update_params mid-run changes CA_in for
        subsequent steps without resetting internal state (the same pattern
        both PFREngine and RTDEngine rely on for boundary-condition changes
        mid-tick)."""
        sim = PFRSimulator(_params(k0=0.0))
        sim.step(1.0)
        sim.update_params({'CA_in': 5.0})
        # After enough transit time, the outlet should reflect the new inlet.
        tau = 1.0 / 0.1
        out = sim.step(2 * tau)
        assert out['CA_out'] == pytest.approx(5.0, rel=1e-2)

    def test_reset_without_params_restores_initial_profile(self):
        sim = PFRSimulator(_params(k0=0.1))
        sim.step(5.0)
        assert sim.t > 0.0
        sim.reset()
        assert sim.t == pytest.approx(0.0)
        N = sim.params['N']
        assert np.allclose(sim.state[:N], 1.0)   # CA_in
        assert np.allclose(sim.state[2 * N:], 300.0)   # T_in

    def test_reset_with_new_params_uses_them(self):
        sim = PFRSimulator(_params())
        sim.step(1.0)
        sim.reset(_params(CA_in=7.0, N=10))
        N = sim.params['N']
        assert np.allclose(sim.state[:N], 7.0)
        assert sim.t == pytest.approx(0.0)

    def test_update_params_does_not_reset_time_or_state(self):
        sim = PFRSimulator(_params())
        sim.step(3.0)
        t_before = sim.t
        sim.update_params({'h_loss': 100.0})
        assert sim.t == pytest.approx(t_before)
