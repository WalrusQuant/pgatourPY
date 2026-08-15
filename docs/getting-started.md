# Getting Started

## Installation

```bash
pip install git+https://github.com/WalrusQuant/pgatourPY.git
```

## Tournament IDs

Most functions need a tournament ID in the format `{tour_code}{year}{number}`:

- `"R2026027"` — 2026 FedEx St. Jude Championship (PGA Tour)
- `"R2026011"` — 2026 THE PLAYERS Championship (PGA Tour)

Use `pga_current_tournament()` for this week's ID, or `pga_schedule()` to browse the season:

```python
import pgatourpy as pga

tid = pga.pga_current_tournament()
schedule = pga.pga_schedule(2026)
print(schedule[["tournament_id", "tournament_name", "display_date", "status"]])
```

## Tracking a Live Tournament

### Leaderboard

```python
tid = pga.pga_current_tournament()
lb = pga.pga_leaderboard(tid)
print(lb[["position", "display_name", "total", "thru"]])
```

For a quick top-15 snapshot:

```python
pga.pga_current_leaders(tid)
```

### Field

```python
pga.pga_field(tid)
```

### Tee Times

```python
tt = pga.pga_tee_times(tid)
print(tt[["round_number", "tee_time", "start_tee", "display_name"]])
```

### Tournament Metadata

```python
t = pga.pga_tournaments(tid)
print(t["tournament_name"].iloc[0])
print(t["weather_condition"].iloc[0])
```

### Broadcast Schedule

```python
pga.pga_coverage(tid)
```

### Odds

```python
pga.pga_odds(tid)
pga.pga_odds_markets(tid)
pga.pga_player_odds(tid, "34046")
pga.pga_field_stats(tid)
```

## Player Deep Dive

### Scorecard

```python
sc = pga.pga_scorecard(tid, "34046")
print(sc[["round_number", "hole_number", "par", "score", "status", "round_score"]])
```

### Shot-Level Tracking

```python
shots = pga.pga_shot_details(tid, "34046", round=1)
print(shots[["hole_number", "stroke_number", "play_by_play", "distance"]])
```

Coordinate columns are included for shot visualization (x, y, tourcastX, tourcastY, tourcastZ).

### Videos

```python
# Highlight clips
pga.pga_videos(player_ids=["34046"], tournament_id="027")

# Shot-by-shot video
pga.pga_tourcast_videos(tid, "34046", round=1)
```

!!! note
    `pga_videos()` uses the numeric tournament ID (`"027"`) without the tour code prefix.

### Hole-by-hole field scores

```python
holes = pga.pga_leaderboard_holes(tid)
```

### Weather and course stats

```python
pga.pga_weather(tid)
pga.pga_course_stats(tid)
```

### Tournament overview and past results

```python
pga.pga_tournament_overview(tid)
pga.pga_tournament_past_results(tid, year=2025)
```

## Player Profiles

### Profile Overview

```python
profile = pga.pga_player_profile("52955")  # Ludvig Aberg
print(profile["first_name"])   # "Ludvig"
print(profile["country"])      # "Sweden"
print(profile["highlights"])   # DataFrame: wins, FedExCup, world rank
print(profile["overview"])     # DataFrame: career/season/bio/stats
```

### Player Stats (130+ in One Call)

```python
stats = pga.pga_player_stats("52955")
print(stats[["stat_id", "title", "rank", "value", "category"]].head(10))
```

### Tournament Results

```python
results = pga.pga_player_results("52955")
print(results.groupby("season").size())
print(results[["tournament", "pos", "total", "to_par", "winnings"]])

# One season only
pga.pga_player_results("52955", season=2025)
```

### Career, Bio, and Tournament Status

```python
career = pga.pga_player_career("52955")
bio = pga.pga_player_bio("52955")
print(bio["text"][0][:200])  # First bio paragraph

# Is a player in the current tournament?
status = pga.pga_player_tournament_status("34046")
```

## Statistics

### Pulling Stats

```python
sg = pga.pga_stats("02675")  # SG: Total
print(sg[["rank", "player_name", "country"]].head())

# Metadata in attrs
print(sg.attrs["stat_title"])  # "SG: Total"
print(sg.attrs["tour_avg"])    # "0.000"
```

### Finding Stat IDs

```python
# Browse by category
putting = pga.STAT_IDS[pga.STAT_IDS["category"] == "Putting"]

# Search by name
driving = pga.STAT_IDS[
    pga.STAT_IDS["stat_name"].str.contains("Driving", case=False)
]

# All categories
print(pga.STAT_IDS["category"].unique())
```

### Common Stat IDs

| Stat ID | Stat |
|---------|------|
| `02675` | SG: Total |
| `02674` | SG: Tee-to-Green |
| `02567` | SG: Off-the-Tee |
| `02568` | SG: Approach the Green |
| `02569` | SG: Around-the-Green |
| `02564` | SG: Putting |
| `101`   | Driving Distance |
| `102`   | Driving Accuracy Percentage |
| `103`   | Greens in Regulation Percentage |
| `130`   | Scrambling |
| `104`   | Putting Average |
| `120`   | Scoring Average (Adjusted) |

### Historical Comparisons

```python
dd_2024 = pga.pga_stats("101", year=2024)
dd_2020 = pga.pga_stats("101", year=2020)
```

## FedExCup and other standings

```python
fc = pga.pga_fedex_cup(2026)
print(fc[["display_name", "this_week_rank", "projected_points"]].head())

pga.pga_signature_standings()
pga.pga_priority_rankings()
```

## Player Directory

```python
players = pga.pga_players("R")
active = players[players["is_active"] == True]

# Other tours
champions = pga.pga_players("S")
korn_ferry = pga.pga_players("H")
americas = pga.pga_players("Y")
```

## News

```python
news = pga.pga_news(limit=10)

# See categories
pga.pga_news_franchises()

# Filter by category
pga.pga_news(franchises=["power-rankings"], limit=5)
```
