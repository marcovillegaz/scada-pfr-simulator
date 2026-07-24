"""Tests for scada_app.engine.data_store.DataStore -- generic over snapshot
type (EngineSnapshot for PFR, RTDSnapshot for RTD). Regression coverage for
the to_dataframe() bug: it used to hardcode EngineSnapshot's field names, so
calling it on a store of RTDSnapshots raised AttributeError."""

import pytest

from engine.data_store import DataStore, EngineSnapshot, RTDSnapshot


def _engine_snapshot(**overrides) -> EngineSnapshot:
    defaults = dict(
        sim_time=0.0, CA_out=0.0, CB_out=0.0, T_out=290.0, X_out=0.0,
        CA_in=1.0, CB_in=1.0, T_in=290.0, T_reactor=290.0, T_setpoint=293.0,
        valve=0.5, Qa0=1e-6, Qb0=1e-6, Q_in=2e-6, velocity=0.1,
        conductivity=1.6, CA_profile=(1.0, 0.5), CB_profile=(1.0, 0.5),
        T_profile=(290.0, 290.0),
    )
    defaults.update(overrides)
    return EngineSnapshot(**defaults)


def _rtd_snapshot(**overrides) -> RTDSnapshot:
    defaults = dict(sim_time=0.0, Q=0.02, absorbance=0.0, injecting=False)
    defaults.update(overrides)
    return RTDSnapshot(**defaults)


class TestDataStoreBasics:
    def test_append_adds_to_both_buffer_and_log(self):
        store = DataStore()
        store.append(_rtd_snapshot(sim_time=1.0))
        assert len(store.run_log) == 1
        assert len(store.plot_buffer) == 1

    def test_clear_empties_both(self):
        store = DataStore()
        store.append(_rtd_snapshot())
        store.clear()
        assert len(store.run_log) == 0
        assert len(store.plot_buffer) == 0

    def test_plot_buffer_respects_maxlen(self):
        store = DataStore(plot_buffer_size=3)
        for i in range(5):
            store.append(_rtd_snapshot(sim_time=float(i)))
        assert len(store.plot_buffer) == 3
        assert len(store.run_log) == 5   # run_log is unbounded

    def test_to_dataframe_empty_store(self):
        store = DataStore()
        assert store.to_dataframe().empty


class TestToDataframeGenericOverSnapshotType:
    def test_engine_snapshot_excludes_spatial_profiles(self):
        store = DataStore()
        store.append(_engine_snapshot(sim_time=1.0, T_out=300.0))
        df = store.to_dataframe()
        assert list(df.columns) == [
            "sim_time", "CA_out", "CB_out", "T_out", "X_out", "CA_in",
            "CB_in", "T_in", "T_reactor", "T_setpoint", "valve", "Qa0",
            "Qb0", "Q_in", "velocity", "conductivity",
        ]
        assert "CA_profile" not in df.columns
        assert df.loc[0, "T_out"] == pytest.approx(300.0)

    def test_rtd_snapshot_does_not_raise(self):
        """Regression: to_dataframe() used to hardcode EngineSnapshot's
        fields and would raise AttributeError on RTDSnapshot rows."""
        store = DataStore()
        store.append(_rtd_snapshot(sim_time=1.0, absorbance=0.42, injecting=True))
        df = store.to_dataframe()
        assert list(df.columns) == ["sim_time", "Q", "absorbance", "injecting"]
        assert df.loc[0, "absorbance"] == pytest.approx(0.42)
        assert bool(df.loc[0, "injecting"]) is True

    def test_row_count_matches_run_log(self):
        store = DataStore()
        for i in range(4):
            store.append(_rtd_snapshot(sim_time=float(i)))
        assert len(store.to_dataframe()) == 4
