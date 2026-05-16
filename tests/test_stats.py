"""Tests for `pga_stats` and `pga_fedex_cup` (vectorization, event_query)."""

from __future__ import annotations

import pandas as pd
import pytest

from pgatourpy import pga_fedex_cup, pga_stats
from tests.conftest import load_fixture


def test_stats_single_call(mock_graphql):
    mock_graphql(load_fixture("StatDetails"))
    df = pga_stats("02675", year=2026)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2  # tour-avg row filtered out
    assert "stat_id" in df.columns and (df["stat_id"] == "02675").all()
    assert "year" in df.columns and (df["year"] == 2026).all()
    # rank coerced to nullable int
    assert pd.api.types.is_integer_dtype(df["rank"])
    # dynamic-header dedupe: two "Rank" columns must not collide
    assert "rank_1" in df.columns
    # metadata preserved for single-call result
    assert df.attrs["stat_title"] == "SG: Total"


def test_stats_multi_stat_loops(mock_graphql):
    mock_graphql(load_fixture("StatDetails"))
    df = pga_stats(["02675", "02568"], year=2026)
    # 2 player rows per stat -> 4 rows total
    assert len(df) == 4
    assert sorted(df["stat_id"].unique().tolist()) == ["02568", "02675"]


def test_stats_multi_year_loops(mock_graphql):
    mock_graphql(load_fixture("StatDetails"))
    df = pga_stats("02675", year=[2025, 2026])
    assert len(df) == 4
    assert sorted(df["year"].unique().tolist()) == [2025, 2026]


def test_stats_multi_stat_multi_year(mock_graphql):
    mock_graphql(load_fixture("StatDetails"))
    df = pga_stats(["02675", "02568"], year=[2025, 2026])
    # 2 stats x 2 years x 2 player rows
    assert len(df) == 8


def test_stats_rejects_empty_stat_id():
    with pytest.raises(ValueError):
        pga_stats([], year=2026)
    with pytest.raises(ValueError):
        pga_stats("", year=2026)


def test_stats_event_query_passed(mock_graphql, monkeypatch):
    """event_query must reach the graphql variables dict."""
    captured = {}

    def fake(operation_name, variables=None):
        captured.update(variables or {})
        return load_fixture("StatDetails")

    monkeypatch.setattr("pgatourpy.client.graphql_request", fake)
    pga_stats("02675", year=2026, event_query="LAST_5")
    assert captured.get("eventQuery") == "LAST_5"


def test_stats_invalid_tour():
    with pytest.raises(ValueError):
        pga_stats("02675", year=2026, tour="X")


def test_fedex_cup(mock_graphql):
    mock_graphql(load_fixture("TourCupSplit"))
    df = pga_fedex_cup(year=2026)
    # Info row should be filtered out
    assert len(df) == 1
    assert df.iloc[0]["player_id"] == "39971"
    assert df.iloc[0]["projected_points"] == 3500


def test_fedex_cup_event_query(monkeypatch):
    captured = {}

    def fake(operation_name, variables=None):
        captured.update(variables or {})
        return load_fixture("TourCupSplit")

    monkeypatch.setattr("pgatourpy.client.graphql_request", fake)
    pga_fedex_cup(year=2026, event_query="LAST_5")
    assert captured.get("eventQuery") == "LAST_5"
