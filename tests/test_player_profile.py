"""Tests for player-profile endpoints (the §2 bug-fix targets)."""

from __future__ import annotations

import pandas as pd

from pgatourpy import (
    pga_player_bio,
    pga_player_career,
    pga_player_profile,
    pga_player_results,
    pga_player_stats,
    pga_player_tournament_status,
)
from tests.conftest import load_fixture


def test_player_profile_shape(mock_rest):
    mock_rest(load_fixture("player_profile"))
    out = pga_player_profile("52955")
    assert out["first_name"] == "Ludvig"
    assert out["country"] == "Sweden"
    assert isinstance(out["highlights"], pd.DataFrame)
    assert isinstance(out["overview"], pd.DataFrame)
    assert len(out["highlights"]) == 2
    assert len(out["overview"]) == 2


def test_player_career(mock_rest):
    mock_rest(load_fixture("player_career"))
    df = pga_player_career("52955")
    assert len(df) == 3
    assert {"tour_code", "tour_name", "section", "widget", "label", "value"} <= set(df.columns)


def test_player_results_iterates_all_seasons(mock_rest):
    """§2b: must not drop seasons beyond the first."""
    mock_rest(load_fixture("player_results"))
    df = pga_player_results("52955")
    # 2 rows season 2025-26 + 1 row season 2024-25
    assert len(df) == 3
    assert set(df["season"].unique()) == {"2025-26", "2024-25"}


def test_player_results_dedupes_headers(mock_rest):
    """§3: duplicate 'Position' columns must dedupe to position, position_1."""
    mock_rest(load_fixture("player_results"))
    df = pga_player_results("52955")
    assert "position" in df.columns
    assert "position_1" in df.columns
    # group-prefixed round columns are snake-cased + uniqued
    assert "round_1" in df.columns
    assert "round_4" in df.columns


def test_player_stats_rank_is_int(mock_rest):
    """§2c: rank must be coerced to int."""
    mock_rest(load_fixture("player_stats"))
    df = pga_player_stats("52955")
    assert pd.api.types.is_integer_dtype(df["rank"])
    assert df.iloc[0]["rank"] == 1


def test_player_bio(mock_rest):
    mock_rest(load_fixture("player_bio"))
    out = pga_player_bio("52955")
    assert out["text"] == ["Para one of bio text.", "Para two of bio text."]
    assert out["amateur_highlights"] == ["NCAA champion", "Walker Cup"]
    assert isinstance(out["widgets"], pd.DataFrame)
    assert len(out["widgets"]) == 2


def test_player_tournament_status_empty(mock_graphql):
    """§16: all-null status must return an empty frame, not a 1-row all-NA frame."""
    mock_graphql(load_fixture("player_tournament_status_empty"))
    df = pga_player_tournament_status("52955")
    assert len(df) == 0


def test_player_tournament_status_active(mock_graphql):
    """§2a: roundStatusDisplay and roundStatusColor must be mapped."""
    mock_graphql(load_fixture("player_tournament_status_active"))
    df = pga_player_tournament_status("52955")
    assert len(df) == 1
    row = df.iloc[0]
    assert row["round_status_display"] == "Round 4 - F"
    assert row["round_status_color"] == "green"
    assert row["position"] == "T1"
    assert row["tournament_id"] == "R2026475"
