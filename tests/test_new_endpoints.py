"""Tests for 0.3.0 wrappers: field, holes, weather, standings, odds v2."""

from __future__ import annotations

import pandas as pd

from pgatourpy import (
    pga_course_stats,
    pga_course_stats_overview,
    pga_field,
    pga_field_stats,
    pga_leaderboard_holes,
    pga_odds_markets,
    pga_player_odds,
    pga_priority_rankings,
    pga_signature_standings,
    pga_tournament_overview,
    pga_tournament_past_results,
    pga_weather,
)
from tests.conftest import load_fixture


def test_field(mock_graphql):
    mock_graphql(load_fixture("Field"))
    df = pga_field("R2026027")
    assert len(df) == 2
    assert df.iloc[0]["player_id"] == "52955"
    assert df.iloc[0]["owgr"] == "16"
    assert bool(df.iloc[1]["alternate"]) is True
    assert df.attrs["tournament_name"] == "FedEx St. Jude Championship"


def test_field_stats(mock_graphql):
    mock_graphql(load_fixture("FieldStats"))
    df = pga_field_stats("R2026027")
    assert len(df) == 1
    assert df.iloc[0]["player_id"] == "52955"
    assert df.iloc[0]["last_event"] == "Wyndham"
    assert "sg_total" in df.columns


def test_leaderboard_holes(mock_graphql):
    mock_graphql(load_fixture("LeaderboardHoleByHole"))
    df = pga_leaderboard_holes("R2026027", round=3)
    assert len(df) == 1
    assert df.iloc[0]["player_id"] == "52955"
    assert df.iloc[0]["hole_number"] == 1
    assert df.iloc[0]["status"] == "BIRDIE"
    assert df.attrs["current_round"] == 3


def test_tournament_past_results(mock_graphql):
    mock_graphql(load_fixture("TournamentPastResults"))
    df = pga_tournament_past_results("R2026027", year=2025)
    assert len(df) == 1
    assert df.iloc[0]["position"] == "T10"
    assert df.iloc[0]["round_1"] == "66"


def test_tournament_overview(mock_graphql):
    mock_graphql(load_fixture("TournamentOverview"))
    out = pga_tournament_overview("R2026027")
    assert out["defending_champion"]["display_name"] == "Scottie Scheffler"
    assert len(out["overview"]) == 1
    assert len(out["past_champions"]) == 1
    assert out["tickets_url"].startswith("https://")


def test_weather(mock_graphql):
    mock_graphql(load_fixture("Weather"))
    df = pga_weather("R2026027")
    assert set(df["horizon"]) == {"hourly", "daily"}
    assert df.loc[df["horizon"] == "hourly", "temp_f"].iloc[0] == 91
    assert df.loc[df["horizon"] == "daily", "max_temp_f"].iloc[0] == 93


def test_course_stats(mock_graphql):
    mock_graphql(load_fixture("CourseStats"))
    df = pga_course_stats("R2026027")
    assert len(df) == 1
    assert df.iloc[0]["course_name"] == "TPC Southwind"
    assert df.iloc[0]["hole_number"] == 1


def test_course_stats_overview(mock_graphql):
    mock_graphql(load_fixture("CourseStatsOverview"))
    df = pga_course_stats_overview()
    assert len(df) == 2
    assert df.iloc[0]["category"] == "Toughest Holes"


def test_signature_standings(mock_graphql):
    mock_graphql(load_fixture("SignatureStandings"))
    df = pga_signature_standings()
    assert len(df) == 1
    assert df.iloc[0]["player_id"] == "52955"
    assert df.iloc[0]["table"] == "official"


def test_priority_rankings(mock_graphql):
    mock_graphql(load_fixture("PriorityRankings"))
    df = pga_priority_rankings()
    assert len(df) == 1
    assert df.iloc[0]["display_name"] == "Scottie Scheffler"
    assert df.attrs["through"] == "Wyndham Championship"


def test_odds_markets(mock_rest):
    mock_rest(load_fixture("odds_markets"))
    df = pga_odds_markets("R2026027")
    assert len(df) == 2
    assert df.iloc[0]["display_name"] == "To Win"


def test_player_odds(mock_rest):
    mock_rest(load_fixture("player_odds"))
    df = pga_player_odds("R2026027", "52955")
    assert len(df) == 1
    assert df.iloc[0]["odds"] == "+250"
    assert isinstance(df, pd.DataFrame)
