# pgatourPY

A Python client for the PGA Tour API. Access leaderboards, player stats, scorecards, shot tracking data, tee times, FedExCup standings, betting odds, broadcast schedules, news, and video highlights — all returned as pandas DataFrames.

## Installation

```bash
pip install git+https://github.com/WalrusQuant/pgatourPY.git
```

## Quick Start

```python
import pgatourpy as pga

# This week's tournament
tid = pga.pga_current_tournament()

# Current leaderboard
pga.pga_leaderboard(tid)

# Strokes Gained: Total rankings
pga.pga_stats("02675")

# Full player directory (2,700+ players)
pga.pga_players()

# Hole-by-hole scorecard
pga.pga_scorecard(tid, "34046")

# Shot-level tracking with coordinates
pga.pga_shot_details(tid, "34046", round=1)

# Full season schedule with dates, purse, champions
pga.pga_schedule(2026)
```

## Functions

### Live Tournament Data

| Function | Description |
|---|---|
| `pga_current_tournament(tour)` | This week's tournament ID from the PGA Tour web-config |
| `pga_leaderboard(tournament_id)` | Full leaderboard with scores, positions, movement, and cup ranks |
| `pga_current_leaders(tournament_id)` | Quick top-15 snapshot for in-progress tournaments |
| `pga_leaderboard_holes(tournament_id, round)` | Hole-by-hole scores for the whole field |
| `pga_field(tournament_id)` | Tournament field with OWGR, withdrawn, and alternate flags |
| `pga_field_stats(tournament_id, field_stat_type)` | Current-form or course-fit stats for the field |
| `pga_tee_times(tournament_id)` | Tee time groupings with start tees and player assignments |
| `pga_scorecard(tournament_id, player_id)` | Hole-by-hole scorecard with par, score, yardage, and status |
| `pga_shot_details(tournament_id, player_id, round)` | Shot-by-shot tracking data with coordinates, distances, and play-by-play |
| `pga_odds(tournament_id)` | Betting odds to win for the tournament field |
| `pga_odds_markets(tournament_id)` | Available betting-market catalog (To Win, matchups, finishes, …) |
| `pga_player_odds(tournament_id, player_id)` | FanDuel markets for one player |
| `pga_coverage(tournament_id)` | Broadcast and streaming schedule with networks and time windows |
| `pga_weather(tournament_id)` | Hourly and daily forecast |
| `pga_course_stats(tournament_id)` | Per-hole scoring averages for the host course |

### Statistics & Standings

| Function | Description |
|---|---|
| `pga_stats(stat_id, year, tour, event_query=None)` | Any of 400+ stats with full player rankings (2004–2026). Accepts a list of `stat_id` and/or `year` and loops client-side. |
| `pga_fedex_cup(year, tour, event_query=None)` | FedExCup standings with projected and official rankings |
| `pga_signature_standings(tour)` | Signature Event / Aon standings |
| `pga_priority_rankings(tour, year)` | Exemption / priority ranking categories |
| `pga_scorecard_comparison(tournament_id, player_ids, category)` | Head-to-head stat comparison between players |
| `pga_course_stats_overview(tour, year)` | Season course-stats hub |

### Players & Tournaments

| Function | Description |
|---|---|
| `pga_players(tour)` | Full player directory with name, country, age, and active status |
| `pga_tournaments(ids)` | Tournament metadata including location, courses, weather, and format |
| `pga_schedule(year, tour)` | Full season schedule with dates, purse, course, champion, and FedExCup points |
| `pga_tournament_overview(tournament_id)` | Overview tiles, defending champion, past champions |
| `pga_tournament_past_results(tournament_id, year)` | Historical finishes for an event |

### Player Profiles

| Function | Description |
|---|---|
| `pga_player_profile(player_id)` | Overview with career highlights, wins, earnings, world rank, bio basics |
| `pga_player_career(player_id)` | Career achievements: starts, cuts, wins, finish distribution, earnings |
| `pga_player_results(player_id, season)` | Tournament-by-tournament results. Omit `season` for every year, or pass one year / a list |
| `pga_player_stats(player_id)` | Full stat profile (131 stats with ranks) in a single call |
| `pga_player_bio(player_id)` | Biographical text, amateur highlights |
| `pga_player_tournament_status(player_id)` | Live tournament status (position, score, thru) if currently playing |

### Content

| Function | Description |
|---|---|
| `pga_news(tour, limit, offset)` | News articles with filtering by franchise, player, and pagination |
| `pga_news_franchises(tour)` | Available news categories for filtering |
| `pga_videos(player_ids, tournament_id)` | Player video highlights with filtering options |
| `pga_tourcast_videos(tournament_id, player_id, round)` | Shot-by-shot video clips for a player's round |
| `pga_content(path)` | Generic CMS content fragment (raw parsed JSON) |
| `pga_odds_interactivity()` | Odds widget configuration (raw parsed JSON) |
| `pga_speed_rounds(tour)` | Speed-rounds video index (raw parsed JSON) |

### Bundled Data

| Variable | Description |
|---|---|
| `STAT_IDS` | pandas DataFrame of 400+ stat IDs with names, categories, and subcategories |

## Tour Codes

| Code | Tour |
|---|---|
| `"R"` | PGA Tour |
| `"S"` | PGA Tour Champions |
| `"H"` | Korn Ferry Tour |
| `"Y"` | PGA Tour Americas |

## Examples

### Player Profiles

```python
import pgatourpy as pga

# Full profile overview
profile = pga.pga_player_profile("52955")  # Ludvig Aberg
print(profile["first_name"])   # "Ludvig"
print(profile["highlights"])   # DataFrame: wins, FedExCup rank, world rank
print(profile["overview"])     # DataFrame: career/season/bio/stats summary

# 131 stats in one call
stats = pga.pga_player_stats("52955")
print(stats[["stat_id", "title", "rank", "value"]].head(10))

# Tournament results across every season the API returns
results = pga.pga_player_results("52955")
print(results.groupby("season").size())
print(results.head())  # columns are snake_cased API headers, deduped

# Career, bio, tournament status
career = pga.pga_player_career("52955")
bio = pga.pga_player_bio("52955")
status = pga.pga_player_tournament_status("34046")  # if playing
```

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

tid = pga.pga_current_tournament()
tournament = pga.pga_tournaments(tid)
leaderboard = pga.pga_leaderboard(tid)
field = pga.pga_field(tid)
tee_times = pga.pga_tee_times(tid)
coverage = pga.pga_coverage(tid)
odds = pga.pga_odds(tid)

# Deep dive on a player
scorecard = pga.pga_scorecard(tid, "34046")
shots = pga.pga_shot_details(tid, "34046", round=1)
videos = pga.pga_tourcast_videos(tid, "34046", round=1)
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

### Multi-stat / multi-year requests

`pga_stats` accepts a list of stat IDs and/or years. Because the upstream
GraphQL operation only takes one `(stat_id, year)` per call, the wrapper
loops client-side and concatenates. Every row carries `stat_id` and
`year` columns so chunks remain distinguishable.

```python
import pgatourpy as pga

# One stat across five seasons
hist = pga.pga_stats("02675", year=[2022, 2023, 2024, 2025, 2026])

# Four SG categories for the current season
sg = pga.pga_stats(["02675", "02567", "02568", "02564"])

# Use Tour's "Last 5 events" filter
last5 = pga.pga_stats("02675", event_query="LAST_5")
```

## API Details

This package wraps the PGA Tour's GraphQL and REST APIs:

- **GraphQL endpoint:** `https://orchestrator.pgatour.com/graphql`
- **REST endpoint:** `https://data-api.pgatour.com`
- **Config endpoint:** `https://orchestrator-config.pgatour.com` (this week's tournament IDs)
- **Authentication:** Uses a public API key embedded in the PGA Tour frontend (no user authentication required)
- **Rate limiting:** Built-in throttling at 10 requests/second
- **HTTP client:** [httpx](https://www.python-httpx.org/) (sync)

Several endpoints return gzip+base64 compressed payloads. The package handles decompression transparently.

## Configuration

| Environment variable | Purpose |
|---|---|
| `PGA_API_KEY` | Override the embedded public API key. Useful if the PGA Tour rotates the frontend key. |
| `PGATOUR_VERBOSE` | Truthy (`1`, `true`, `yes`, …) elevates request envelope logs to `INFO`. |

For finer control, the package logs through the `pgatourpy` logger:

```python
import logging
logging.getLogger("pgatourpy").setLevel(logging.DEBUG)
```

All transport, parse, and decompression failures raise `pgatourpy.PgaTourError`
with a message that names the operation and failure step.

Requests time out after 30 seconds and retry up to 3 times with exponential
backoff on transient failures (408, 429, 5xx, network errors).

## Dependencies

- [httpx](https://www.python-httpx.org/) — HTTP client
- [pandas](https://pandas.pydata.org/) — DataFrames

## License

MIT

## See Also

- [pgatouR](https://github.com/WalrusQuant/pgatouR) — R version of this package
