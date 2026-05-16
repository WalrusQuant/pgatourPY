"""Tests for player directory, tournaments, and schedule endpoints."""

from __future__ import annotations

from pgatourpy import pga_players, pga_schedule, pga_tournaments
from tests.conftest import load_fixture


def test_players(mock_rest):
    mock_rest(load_fixture("players_R"))
    df = pga_players(tour="R")
    assert len(df) == 1
    assert df.iloc[0]["display_name"] == "Jordan Spieth"
    assert df.iloc[0]["age"] == 32


def test_tournaments(mock_graphql):
    mock_graphql(load_fixture("Tournaments"))
    df = pga_tournaments(["R2026475"])
    assert len(df) == 1
    row = df.iloc[0]
    assert row["tournament_name"] == "The Players Championship"
    assert row["weather_temp_f"] == 78
    # courses retained as list-column
    assert isinstance(row["courses"], list)
    assert row["courses"][0]["course_name"] == "TPC Sawgrass"


def test_tournaments_accepts_string_id(mock_graphql):
    mock_graphql(load_fixture("Tournaments"))
    df = pga_tournaments("R2026475")
    assert len(df) == 1


def test_schedule(mock_rest):
    mock_rest(load_fixture("schedule_R_2026"))
    df = pga_schedule(year=2026, tour="R")
    assert len(df) == 1
    assert df.iloc[0]["champion"] == "Jordan Spieth"
    assert df.iloc[0]["fedex_cup_points"] == "750"
