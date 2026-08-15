# pgatourPY 0.3.0

Both the R review and the Python live probe (2026-08-15, St. Jude `R2026027`) agree: shipped wrappers are healthy. This is a coverage + hygiene pass.

## Phase 1 — Hygiene

- [x] Allow tour code `Y` in `VALID_TOUR_CODES`
- [x] Add `config_request` + `pga_current_tournament(tour="R") -> str`
- [x] Fix `pga_player_results` to use `?season=` and loop `resultPills`
- [x] Snake-case `pga_odds` columns
- [x] Regen `STAT_IDS` from live `StatOverview`
- [x] Refresh README / docs IDs and counts
- [x] Offline tests + fixtures for the above

## Phase 2 — New wrappers

- [x] `pga_field` / `pga_field_stats`
- [x] `pga_leaderboard_holes`
- [x] `pga_tournament_past_results`
- [x] `pga_tournament_overview` / `pga_weather`
- [x] `pga_course_stats` / `pga_course_stats_overview`
- [x] `pga_signature_standings`
- [x] `pga_priority_rankings`

## Phase 3 — Richer leaderboard

- [x] Additive columns: tee time, movement, amateur, cup ranks, total strokes, group, course
- [x] Update leaderboard fixture + tests

## Phase 4 — Odds v2

- [x] `pga_odds_markets(tournament_id)`
- [x] `pga_player_odds(tournament_id, player_id)`

## Release

- [x] CHANGELOG 0.3.0
- [x] Version bump `0.3.0`
- [x] Offline tests (85 passed)
- [x] Live smoke against St. Jude
- [ ] Commit (waiting on you)

## Review (2026-08-15)

Live smoke after the implementation:

| Call | Result |
|---|---|
| `pga_current_tournament()` | `R2026027` |
| `pga_current_tournament("Y")` | `Y2026018` |
| `pga_players("Y")` | 531 |
| `pga_player_results("52955")` | 76 rows, seasons 2022–2026 |
| `pga_leaderboard` | 69 × 29, includes `tee_time` + `movement_direction` |
| `pga_field` | 69 players, OWGR present |
| `pga_leaderboard_holes` | 1,225 rows / 69 players |
| `pga_odds` | snake_case columns, 66 rows |
| `pga_odds_markets` | To Win, Matchup, Finishes, Groups, Player Props, 3 Ball, Nationality |
| `pga_weather` | 12 hourly + 7 daily |
| `pga_priority_rankings` | 33 populated categories, through Wyndham |
| `STAT_IDS` | 467 |

Known leftover: `pga_player_odds` flattens only the first line inside each odds group. Fine for a first cut; can deepen if you start using player props.
