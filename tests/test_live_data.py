"""Tests for live-data endpoints: tee times, scorecard, shot details, odds, coverage."""

from __future__ import annotations

import pandas as pd

from pgatourpy import (
    pga_coverage,
    pga_odds,
    pga_scorecard,
    pga_scorecard_comparison,
    pga_shot_details,
    pga_tee_times,
)
from tests.conftest import load_fixture


def test_tee_times(mock_graphql):
    mock_graphql(load_fixture("TeeTimesCompressedV2"))
    df = pga_tee_times("R2026475")
    # 3 players in group 1 + 1 in group 2 + 0 in empty group
    assert len(df) == 4
    assert set(df["group_number"].unique()) == {1, 2}
    # tee_time coerced to datetime
    assert pd.api.types.is_datetime64_any_dtype(df["tee_time"])


def test_scorecard(mock_graphql):
    mock_graphql(load_fixture("ScorecardCompressedV3"))
    df = pga_scorecard("R2026475", "39971")
    assert len(df) == 18
    assert set(df["round_number"].unique()) == {1}


def test_shot_details(mock_graphql):
    mock_graphql(load_fixture("shotDetailsV4Compressed"))
    df = pga_shot_details("R2026475", "39971", round=1)
    assert len(df) == 1
    # flattened coordinate columns present
    assert "leftToRightCoords.fromCoords.x" in df.columns


def test_shot_details_empty_returns_empty_df(mock_graphql):
    """§6: cut players / untracked rounds return [], not a crash."""
    mock_graphql(load_fixture("shotDetailsV4Compressed_empty"))
    df = pga_shot_details("R2026475", "99999", round=1)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0


def test_odds(mock_graphql):
    mock_graphql(load_fixture("oddsToWinCompressed"))
    df = pga_odds("R2026475")
    assert len(df) == 2
    assert "id" in df.columns


def test_coverage(mock_graphql):
    mock_graphql(load_fixture("Coverage"))
    df = pga_coverage("R2026475")
    assert len(df) == 1
    assert df.iloc[0]["coverage_type"] == "BroadcastFullTelecast"
    assert pd.api.types.is_datetime64_any_dtype(df["start_time"])


def test_scorecard_comparison(mock_graphql):
    mock_graphql(load_fixture("ScorecardStatsComparisonCategories"))
    df = pga_scorecard_comparison("R2026475", ["39971", "52955"])
    assert len(df) == 2
    assert list(df.columns) == ["display_text", "category"]
