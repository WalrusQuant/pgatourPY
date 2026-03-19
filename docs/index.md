# pgatourPY

A Python client for the PGA Tour API. Access leaderboards, player stats, scorecards, shot tracking data, tee times, FedExCup standings, betting odds, broadcast schedules, news, and video highlights — all returned as pandas DataFrames.

## Installation

```bash
pip install git+https://github.com/WalrusQuant/pgatourPY.git
```

## Quick Start

```python
import pgatourpy as pga

# Current leaderboard
pga.pga_leaderboard("R2026475")

# Strokes Gained: Total rankings
pga.pga_stats("02675")

# Full player directory (2,400+ players)
pga.pga_players()

# Hole-by-hole scorecard
pga.pga_scorecard("R2026475", "39971")

# Shot-level tracking with coordinates
pga.pga_shot_details("R2026475", "39971", round=1)

# Full season schedule
pga.pga_schedule(2025)
```

## Functions Overview

### Live Tournament Data

| Function | Description |
|---|---|
| `pga_leaderboard()` | Full leaderboard with scores, positions, and round-by-round results |
| `pga_current_leaders()` | Quick top-15 snapshot for in-progress tournaments |
| `pga_tee_times()` | Tee time groupings with start tees and player assignments |
| `pga_scorecard()` | Hole-by-hole scorecard with par, score, yardage, and status |
| `pga_shot_details()` | Shot-by-shot tracking data with coordinates and play-by-play |
| `pga_odds()` | Betting odds to win for the tournament field |
| `pga_coverage()` | Broadcast and streaming schedule |

### Statistics & Standings

| Function | Description |
|---|---|
| `pga_stats()` | Any of 300+ stats with full player rankings (2004-2026) |
| `pga_fedex_cup()` | FedExCup standings with projected and official rankings |
| `pga_scorecard_comparison()` | Head-to-head stat comparison between players |

### Players & Tournaments

| Function | Description |
|---|---|
| `pga_players()` | Full player directory (2,400+ players) |
| `pga_tournaments()` | Tournament metadata including location, courses, weather |
| `pga_schedule()` | Season schedule with dates, purse, course, champion |

### Player Profiles

| Function | Description |
|---|---|
| `pga_player_profile()` | Overview with career highlights, wins, earnings, world rank, bio |
| `pga_player_career()` | Career achievements: starts, cuts, wins, finish distribution |
| `pga_player_results()` | Tournament-by-tournament results with round scores and earnings |
| `pga_player_stats()` | Full stat profile (131 stats with ranks) in a single call |
| `pga_player_bio()` | Biographical text and amateur highlights |
| `pga_player_tournament_status()` | Live tournament status if currently playing |

### Content

| Function | Description |
|---|---|
| `pga_news()` | News articles with filtering and pagination |
| `pga_news_franchises()` | Available news categories |
| `pga_videos()` | Player video highlights |
| `pga_tourcast_videos()` | Shot-by-shot video clips |

### Data

| Variable | Description |
|---|---|
| `STAT_IDS` | pandas DataFrame of 340 stat IDs with names and categories |

## Tour Codes

| Code | Tour |
|---|---|
| `"R"` | PGA Tour |
| `"S"` | PGA Tour Champions |
| `"H"` | Korn Ferry Tour |

## See Also

- [pgatouR](https://github.com/WalrusQuant/pgatouR) — R version of this package
