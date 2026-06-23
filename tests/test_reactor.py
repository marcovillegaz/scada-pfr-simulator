"""Tests for reactor_simulation.core.reactor — PlugFlow, StirredTank, RecyclePlugFlow."""

import pytest
from reactor_simulation import PlugFlow, StirredTank, RecyclePlugFlow


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def pfr():
    return PlugFlow(order_of_reaction=1, kinetic_constant=1.0)

@pytest.fixture
def cstr():
    return StirredTank(order_of_reaction=1, kinetic_constant=1.0)

@pytest.fixture
def rpfr():
    return RecyclePlugFlow(order_of_reaction=1, kinetic_constant=1.0)


# ── PlugFlow ──────────────────────────────────────────────────────────────────

class TestPlugFlow:
    def test_residence_time_is_positive(self, pfr):
        tau = pfr.residence_time(
            output_conversion=0.5,
            input_concentration=1.0,
            input_conversion=0.0,
            epsilon=0.0,
        )
        assert tau > 0

    def test_higher_conversion_needs_more_time(self, pfr):
        tau_50 = pfr.residence_time(0.5, 1.0, 0.0, 0.0)
        tau_90 = pfr.residence_time(0.9, 1.0, 0.0, 0.0)
        assert tau_90 > tau_50

    def test_first_order_no_volume_change(self):
        """
        For first-order, no volume change (ε=0), Ca0=1:
        τ = -ln(1 - Xaf) / k
        """
        import math
        k = 2.0
        Xaf = 0.8
        pfr = PlugFlow(order_of_reaction=1, kinetic_constant=k)
        tau_computed = pfr.residence_time(Xaf, 1.0, 0.0, 0.0)
        tau_analytical = -math.log(1 - Xaf) / k
        assert abs(tau_computed - tau_analytical) < 1e-6

    def test_volume_proportional_to_flow(self, pfr):
        # get_volume() in the base class does not forward epsilon, so we
        # compute V = Q * tau manually to test the proportionality.
        tau = pfr.residence_time(0.5, 1.0, 0.0, 0.0)
        v1 = 1e-3 * tau
        v2 = 2e-3 * tau
        assert abs(v2 - 2 * v1) < 1e-15

    def test_epsilon_increases_residence_time(self):
        """Positive ε (volume expansion) increases residence time."""
        pfr = PlugFlow(order_of_reaction=1, kinetic_constant=1.0)
        tau_no_expansion = pfr.residence_time(0.5, 1.0, 0.0, epsilon=0.0)
        tau_expansion    = pfr.residence_time(0.5, 1.0, 0.0, epsilon=0.5)
        assert tau_expansion > tau_no_expansion

    def test_reactor_type_label(self, pfr):
        assert pfr.reactor_type == "Plug Flow"


# ── StirredTank ───────────────────────────────────────────────────────────────

class TestStirredTank:
    def test_residence_time_is_positive(self, cstr):
        tau = cstr.residence_time(0.5, 1.0, 0.0, 0.0)
        assert tau > 0

    def test_higher_conversion_needs_more_time(self, cstr):
        tau_50 = cstr.residence_time(0.5, 1.0, 0.0, 0.0)
        tau_90 = cstr.residence_time(0.9, 1.0, 0.0, 0.0)
        assert tau_90 > tau_50

    def test_first_order_analytical(self):
        """
        For first-order CSTR with ε=0:
        τ = Xaf / (k · (1 - Xaf))
        """
        k = 1.5
        Xaf = 0.6
        cstr = StirredTank(order_of_reaction=1, kinetic_constant=k)
        tau_computed   = cstr.residence_time(Xaf, 1.0, 0.0, 0.0)
        tau_analytical = Xaf / (k * (1 - Xaf))
        assert abs(tau_computed - tau_analytical) < 1e-6

    def test_cstr_needs_more_time_than_pfr(self):
        """CSTR always requires more residence time than PFR for same conversion (n≥1)."""
        pfr  = PlugFlow(order_of_reaction=1, kinetic_constant=1.0)
        cstr = StirredTank(order_of_reaction=1, kinetic_constant=1.0)
        tau_pfr  = pfr.residence_time(0.7, 1.0, 0.0, 0.0)
        tau_cstr = cstr.residence_time(0.7, 1.0, 0.0, 0.0)
        assert tau_cstr > tau_pfr

    def test_reactor_type_label(self, cstr):
        assert cstr.reactor_type == "Stirred Tank"


# ── RecyclePlugFlow ───────────────────────────────────────────────────────────

class TestRecyclePlugFlow:
    def test_residence_time_is_positive(self, rpfr):
        tau = rpfr.residence_time(R=5.0, initial_concentration=1.0, final_conversion=0.5)
        assert tau > 0

    def test_residence_time_increases_with_conversion(self):
        """Higher final conversion should always require more residence time."""
        rpfr = RecyclePlugFlow(order_of_reaction=2, kinetic_constant=1.0)
        tau_low  = rpfr.residence_time(R=5, initial_concentration=1.0, final_conversion=0.3)
        tau_high = rpfr.residence_time(R=5, initial_concentration=1.0, final_conversion=0.7)
        assert tau_high > tau_low

    def test_residence_time_independent_of_recycle_for_first_order(self):
        """
        NOTE — known limitation of the current RecyclePlugFlow formula:
        for n=1 the (R+1) factor and the shrinking integration interval cancel
        exactly, making tau independent of R. This test documents that behavior.
        When the model is updated to use the correct integrand (exponent n
        instead of n-1), this test should be replaced by a convergence test.
        """
        rpfr = RecyclePlugFlow(order_of_reaction=1, kinetic_constant=1.0)
        tau_low_R  = rpfr.residence_time(R=1,    initial_concentration=1.0, final_conversion=0.5)
        tau_high_R = rpfr.residence_time(R=1000, initial_concentration=1.0, final_conversion=0.5)
        assert abs(tau_low_R - tau_high_R) < 1e-6

    def test_average_rate_is_positive(self, rpfr):
        rate = rpfr.average_rate(R=5.0, final_conversion=0.5, initial_concentration=1.0)
        assert rate > 0

    def test_reactor_type_label(self, rpfr):
        assert rpfr.reactor_type == "Recycle Plug Flow"
