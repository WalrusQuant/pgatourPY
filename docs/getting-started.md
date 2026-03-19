# Getting Started

## Installation

```bash
pip install git+https://github.com/WalrusQuant/pgatourPY.git
```

## Tournament IDs

Most functions need a tournament ID in the format `{tour_code}{year}{number}`:

- `"R2026475"` — 2026 Valspar Championship (PGA Tour)
- `"R2026003"` — 2026 WM Phoenix Open (PGA Tour)

Use `pga_schedule()` to discover tournament IDs:

```python
import pgatourpy as pga

schedule = pga.pga_schedule(2026)
print(schedule[["tournament_id", "tournament_name", "display_date", "status"]])
```

## Tracking a Live Tournament

### Leaderboard

```python
lb = pga.pga_leaderboard("R2026475")
print(lb[["position", "display_name", "total", "thru"]])
```

For a quick top-15 snapshot:

```python
pga.pga_current_leaders("R2026475")
```

### Tee Times

```python
tt = pga.pga_tee_times("R2026475")
print(tt[["round_number", "tee_time", "start_tee", "display_name"]])
```

### Tournament Metadata

```python
t = pga.pga_tournaments("R2026475")
print(t["tournament_name"].iloc[0])  # "Valspar Championship"
print(t["weather_condition"].iloc[0])  # "DAY_PARTLY_CLOUDY"
```

### Broadcast Schedule

```python
pga.pga_coverage("R2026475")
```

### Odds

```python
pga.pga_odds("R2026475")
```

## Player Deep Dive

### Scorecard

```python
sc = pga.pga_scorecard("R2026475", "39971")
print(sc[["round_number", "hole_number", "par", "score", "status", "round_score"]])
```

### Shot-Level Tracking

```python
shots = pga.pga_shot_details("R2026475", "39971", round=1)
print(shots[["hole_number", "stroke_number", "play_by_play", "distance"]])
```

Coordinate columns are included for shot visualization (x, y, tourcastX, tourcastY, tourcastZ).

### Videos

```python
# Highlight clips
pga.pga_videos(player_ids=["39971"], tournament_id="475")

# Shot-by-shot video
pga.pga_tourcast_videos("R2026475", "39971", round=1)
```

!!! note
    `pga_videos()` uses the numeric tournament ID (`"475"`) without the tour code prefix.

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

## FedExCup Standings

```python
fc = pga.pga_fedex_cup(2026)
print(fc[["display_name", "this_week_rank", "projected_points"]].head())
```

## Player Directory

```python
players = pga.pga_players("R")
active = players[players["is_active"] == True]

# Other tours
champions = pga.pga_players("S")
korn_ferry = pga.pga_players("H")
```

## News

```python
news = pga.pga_news(limit=10)

# See categories
pga.pga_news_franchises()

# Filter by category
pga.pga_news(franchises=["power-rankings"], limit=5)
```
