"""Tests for content endpoints: news, videos, content, odds_interactivity, speed_rounds."""

from __future__ import annotations

import pandas as pd

from pgatourpy import (
    pga_content,
    pga_news,
    pga_news_franchises,
    pga_odds_interactivity,
    pga_speed_rounds,
    pga_tourcast_videos,
    pga_videos,
)
from tests.conftest import load_fixture


def test_news(mock_graphql):
    mock_graphql(load_fixture("NewsArticles"))
    df = pga_news(tour="R")
    assert len(df) == 1
    assert df.iloc[0]["headline"] == "Spieth wins again"
    assert pd.api.types.is_datetime64_any_dtype(df["publish_date"])


def test_news_franchises(mock_graphql):
    mock_graphql(load_fixture("NewsFranchises"))
    df = pga_news_franchises(tour="R")
    assert len(df) == 2
    assert list(df.columns) == ["franchise", "franchise_label"]


def test_videos(mock_graphql):
    mock_graphql(load_fixture("Videos"))
    df = pga_videos(tour="R")
    assert len(df) == 1
    assert df.iloc[0]["title"] == "Highlight"


def test_tourcast_videos(mock_graphql):
    mock_graphql(load_fixture("TourcastVideos"))
    df = pga_tourcast_videos("R2026475", "39971", round=4)
    assert len(df) == 1
    assert df.iloc[0]["hole_number"] == 1


def test_content_returns_raw_json(mock_graphql):
    """§8: pga_content returns raw parsed JSON (schema varies)."""
    mock_graphql(load_fixture("GenericContentCompressed"))
    out = pga_content("/some/path")
    assert isinstance(out, dict)
    assert out["slug"] == "demo"


def test_content_no_payload_returns_none(mock_graphql):
    mock_graphql({"genericContentCompressed": {"payload": None}})
    assert pga_content("/missing") is None


def test_odds_interactivity(mock_rest):
    mock_rest(load_fixture("odds_interactivity"))
    out = pga_odds_interactivity()
    assert isinstance(out, dict)
    assert out["enabled"] is True


def test_speed_rounds(mock_rest):
    mock_rest(load_fixture("speed_rounds_R"))
    out = pga_speed_rounds(tour="R")
    assert isinstance(out, dict)
    assert out["videos"][0]["title"] == "Speed round"
