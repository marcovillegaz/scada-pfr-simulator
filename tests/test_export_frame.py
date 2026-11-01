"""The Table-tab export must match what the student sees (hotfix 2.0.1).

``DataStore.to_dataframe()`` exports every scalar field of ``EngineSnapshot``,
including true noise-free outlet values. ``export_frame`` projects it onto
``STUDENT_COLUMNS`` so the CSV/Excel files never carry those internal values.
"""

from __future__ import annotations

import pytest

from constants import PFR_DEFAULT_SCENARIO
from engine import PFREngine
from models.log_table_model import ADMIN_COLUMNS, STUDENT_COLUMNS, export_frame

HIDDEN = ("CA_out", "CB_out", "X_out", "velocity", "Q_in", "T_setpoint")


@pytest.fixture(scope="module")
def full_df():
    engine = PFREngine(PFR_DEFAULT_SCENARIO)
    for _ in range(5):
        engine.tick(0.5)
    return engine.data_store.to_dataframe()


def test_full_frame_does_contain_internal_variables(full_df):
    """Guards the premise: if this fails the export test below proves nothing."""
    for name in HIDDEN:
        assert name in full_df.columns


def test_student_export_has_exactly_the_table_columns(full_df):
    out = export_frame(full_df)
    assert list(out.columns) == [header for _, header, _ in STUDENT_COLUMNS]
    assert len(out) == len(full_df)


def test_student_export_leaks_no_internal_variable(full_df):
    out = export_frame(full_df)
    text = " ".join(out.columns).lower()
    for name in HIDDEN:
        assert name.lower() not in text
    # Hidden quantities are not smuggled in under another header either.
    assert "xa_out" not in text and "ca_out" not in text and "cb_out" not in text


def test_student_export_applies_the_table_unit_scaling(full_df):
    out = export_frame(full_df)
    expected = full_df["Qa0"] * 60_000_000.0  # m3/s -> mL/min, as in the table
    assert out["Qa0 (mL/min) — NaOH"].tolist() == pytest.approx(expected.tolist())


def test_admin_columns_still_export_the_internal_variables(full_df):
    out = export_frame(full_df, ADMIN_COLUMNS)
    assert "Xa_out (-)" in out.columns
    assert "Ca_out (mol/L)" in out.columns
