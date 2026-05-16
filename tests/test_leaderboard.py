"""Tests for `pga_leaderboard` partial-row guards and sort-key coercion."""

from __future__ import annotations

import pandas as pd

from pgatourpy import pga_leaderboard
from tests.conftest import load_fixture


def test_leaderboard_basic(mock_graphql):
    mock_graphql(load_fixture("LeaderboardCompressedV3"))
    df = pga_leaderboard("R2026475")
    assert len(df) == 2  # full row + partial row
    assert {"player_id", "total", "total_sort", "score_sort"} <= set(df.columns)


def test_leaderboard_sort_keys_are_numeric(mock_graphql):
    """§14: totalSort/scoreSort coerced to numeric; display fields stay str."""
    mock_graphql(load_fixture("LeaderboardCompressedV3"))
    df = pga_leaderboard("R2026475")
    assert pd.api.types.is_float_dtype(df["total_sort"])
    assert pd.api.types.is_float_dtype(df["score_sort"])
    # display strings retain their formatting
    assert df.iloc[0]["total"] == "-12"
    assert df.iloc[0]["thru"] == "F"


def test_leaderboard_partial_row_does_not_crash(mock_graphql):
    """§15: missing player/scoring fields must not raise column-length errors."""
    mock_graphql(load_fixture("LeaderboardCompressedV3"))
    df = pga_leaderboard("R2026475")
    partial = df[df["player_id"] == "52955"].iloc[0]
    assert pd.isna(partial["first_name"])
    assert pd.isna(partial["total_sort"])
