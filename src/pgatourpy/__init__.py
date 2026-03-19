"""pgatourPY — Python client for the PGA Tour API."""

from pgatourpy.client import (
    pga_coverage,
    pga_current_leaders,
    pga_fedex_cup,
    pga_leaderboard,
    pga_news,
    pga_news_franchises,
    pga_odds,
    pga_players,
    pga_schedule,
    pga_scorecard,
    pga_scorecard_comparison,
    pga_shot_details,
    pga_stats,
    pga_tee_times,
    pga_tourcast_videos,
    pga_tournaments,
    pga_videos,
)
from pgatourpy.stat_ids import STAT_IDS

__version__ = "0.1.0"

__all__ = [
    "pga_coverage",
    "pga_current_leaders",
    "pga_fedex_cup",
    "pga_leaderboard",
    "pga_news",
    "pga_news_franchises",
    "pga_odds",
    "pga_players",
    "pga_schedule",
    "pga_scorecard",
    "pga_scorecard_comparison",
    "pga_shot_details",
    "pga_stats",
    "pga_tee_times",
    "pga_tourcast_videos",
    "pga_tournaments",
    "pga_videos",
    "STAT_IDS",
]
