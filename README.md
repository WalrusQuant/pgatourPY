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

# Full season schedule with dates, purse, champions
pga.pga_schedule(2025)
```

## Functions

### Live Tournament Data

| Function | Description |
|---|---|
| `pga_leaderboard(tournament_id)` | Full leaderboard with scores, positions, and round-by-round results |
| `pga_current_leaders(tournament_id)` | Quick top-15 snapshot for in-progress tournaments |
| `pga_tee_times(tournament_id)` | Tee time groupings with start tees and player assignments |
| `pga_scorecard(tournament_id, player_id)` | Hole-by-hole scorecard with par, score, yardage, and status |
| `pga_shot_details(tournament_id, player_id, round)` | Shot-by-shot tracking data with coordinates, distances, and play-by-play |
| `pga_odds(tournament_id)` | Betting odds to win for the tournament field |
| `pga_coverage(tournament_id)` | Broadcast and streaming schedule with networks and time windows |

### Statistics & Standings

| Function | Description |
|---|---|
| `pga_stats(stat_id, year, tour)` | Any of 300+ stats with full player rankings (data from 2004-2026) |
| `pga_fedex_cup(year, tour)` | FedExCup standings with projected and official rankings |
| `pga_scorecard_comparison(tournament_id, player_ids, category)` | Head-to-head stat comparison between players |

### Players & Tournaments

| Function | Description |
|---|---|
| `pga_players(tour)` | Full player directory with name, country, age, and active status |
| `pga_tournaments(ids)` | Tournament metadata including location, courses, weather, and format |
| `pga_schedule(year, tour)` | Full season schedule with dates, purse, course, champion, and FedExCup points |

### Content

| Function | Description |
|---|---|
| `pga_news(tour, limit, offset)` | News articles with filtering by franchise, player, and pagination |
| `pga_news_franchises(tour)` | Available news categories for filtering |
| `pga_videos(player_ids, tournament_id)` | Player video highlights with filtering options |
| `pga_tourcast_videos(tournament_id, player_id, round)` | Shot-by-shot video clips for a player's round |

### Bundled Data

| Variable | Description |
|---|---|
| `STAT_IDS` | pandas DataFrame of 340 stat IDs with names, categories, and subcategories |

## Tour Codes

| Code | Tour |
|---|---|
| `"R"` | PGA Tour |
| `"S"` | PGA Tour Champions |
| `"H"` | Korn Ferry Tour |

## Examples

### Strokes Gained Analysis

```python
import pgatourpy as pga

sg_total = pga.pga_stats("02675")  # SG: Total
sg_ott = pga.pga_stats("02567")    # SG: Off-the-Tee
sg_app = pga.pga_stats("02568")    # SG: Approach
sg_putt = pga.pga_stats("02564")   # SG: Putting

# Metadata stored in DataFrame attrs
print(sg_total.attrs["stat_title"])  # "SG: Total"
print(sg_total.attrs["tour_avg"])    # "0.000"
```

### Finding Stats

```python
import pgatourpy as pga

# Browse by category
putting = pga.STAT_IDS[pga.STAT_IDS["category"] == "Putting"]

# Search by name
driving = pga.STAT_IDS[
    pga.STAT_IDS["stat_name"].str.contains("Driving", case=False)
]
```

### Live Tournament Tracking

```python
import pgatourpy as pga

tournament = pga.pga_tournaments("R2026475")
leaderboard = pga.pga_leaderboard("R2026475")
tee_times = pga.pga_tee_times("R2026475")
coverage = pga.pga_coverage("R2026475")
odds = pga.pga_odds("R2026475")

# Deep dive on a player
scorecard = pga.pga_scorecard("R2026475", "39971")
shots = pga.pga_shot_details("R2026475", "39971", round=1)
videos = pga.pga_tourcast_videos("R2026475", "39971", round=1)
```

### Season Schedule

```python
import pgatourpy as pga

schedule = pga.pga_schedule(2026)
print(schedule[["tournament_name", "display_date", "status", "purse"]])

# Past seasons
schedule_2025 = pga.pga_schedule(2025)
completed = schedule_2025[schedule_2025["status"] == "COMPLETED"]
print(completed[["tournament_name", "champion", "champion_earnings"]])
```

### Historical Data

```python
import pgatourpy as pga

dd_2024 = pga.pga_stats("101", year=2024)  # Driving Distance
dd_2020 = pga.pga_stats("101", year=2020)
dd_2015 = pga.pga_stats("101", year=2015)
```

## API Details

This package wraps the PGA Tour's GraphQL and REST APIs:

- **GraphQL endpoint:** `https://orchestrator.pgatour.com/graphql`
- **REST endpoint:** `https://data-api.pgatour.com`
- **Authentication:** Uses a public API key embedded in the PGA Tour frontend (no user authentication required)
- **Rate limiting:** Built-in throttling at 10 requests/second
- **HTTP client:** [httpx](https://www.python-httpx.org/) (sync)

Several endpoints return gzip+base64 compressed payloads. The package handles decompression transparently.

## Dependencies

- [httpx](https://www.python-httpx.org/) — HTTP client
- [pandas](https://pandas.pydata.org/) — DataFrames

## License

MIT

## See Also

- [pgatouR](https://github.com/WalrusQuant/pgatouR) — R version of this package
