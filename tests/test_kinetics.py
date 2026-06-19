"""Tests for reactor_simulation.core.kinetics — Reaction, overall_yield functions."""

import pytest
from reactor_simulation import Reaction
from reactor_simulation.core.kinetics import overall_yield_pfr, overall_yield_mfr


class TestReaction:
    def test_reaction_rate_calls_expression(self):
        rxn = Reaction(
            reaction_type="irreversible",
            stoichiometry={"A": -1},
            expression=lambda Ca: 2.0 * Ca,
        )
        assert rxn.reaction_rate(3.0) == pytest.approx(6.0)

    def test_first_order_rate(self):
        k = 0.5
        rxn = Reaction("irreversible", {"A": -1}, lambda Ca: k * Ca)
        assert rxn.reaction_rate(4.0) == pytest.approx(2.0)

    def test_second_order_rate(self):
        k = 0.3
        rxn = Reaction("irreversible", {"A": -2}, lambda Ca: k * Ca ** 2)
        assert rxn.reaction_rate(2.0) == pytest.approx(0.3 * 4.0)

    def test_langmuir_hinshelwood_rate(self):
        k, K = 1.0, 2.0
        rxn = Reaction("surface", {"A": -1}, lambda Ca: k * Ca / (1 + K * Ca))
        Ca = 1.0
        expected = k * Ca / (1 + K * Ca)
        assert rxn.reaction_rate(Ca) == pytest.approx(expected)

    def test_stoichiometry_stored(self):
        stoich = {"A": -1, "B": 2}
        rxn = Reaction("irreversible", stoich, lambda Ca: Ca)
        assert rxn.stoichiometry == stoich

    def test_fractional_change_default(self):
        rxn = Reaction("irreversible", {"A": -1}, lambda Ca: Ca)
        assert rxn.fractional_change == 0


class TestOverallYield:
    def test_pfr_yield_constant_selectivity(self):
        """If φ(Ca)=1 everywhere, overall PFR yield = 1."""
        phi = lambda Ca: 1.0
        y = overall_yield_pfr(phi, Ca_0=5.0, Ca_f=1.0)
        assert abs(y - 1.0) < 1e-6

    def test_mfr_yield_constant_selectivity(self):
        """If φ(Ca)=1 everywhere, MFR yield = 1."""
        phi = lambda Ca: 1.0
        y = overall_yield_mfr(phi, Ca_f=2.0)
        assert abs(y - 1.0) < 1e-6

    def test_pfr_yield_is_between_0_and_1(self):
        phi = lambda Ca: Ca / (Ca + 1.0)
        y = overall_yield_pfr(phi, Ca_0=5.0, Ca_f=0.5)
        assert 0.0 < y < 1.0

    def test_mfr_yield_is_between_0_and_1(self):
        phi = lambda Ca: Ca / (Ca + 1.0)
        y = overall_yield_mfr(phi, Ca_f=1.0)
        assert 0.0 < y < 1.0

    def test_pfr_yield_higher_than_mfr_for_decreasing_selectivity(self):
        """
        When φ decreases with Ca, PFR (which integrates over the full range)
        gives a higher overall yield than MFR (which evaluates φ only at Ca_f).
        """
        phi = lambda Ca: Ca / (Ca + 1.0)   # decreasing as Ca drops
        Ca_0, Ca_f = 5.0, 0.5
        y_pfr = overall_yield_pfr(phi, Ca_0, Ca_f)
        y_mfr = overall_yield_mfr(phi, Ca_f)
        assert y_pfr > y_mfr
