# Changelog

All notable changes to pgatourPY are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-05-16

A correctness, robustness, and test-coverage pass ported from the sibling
R package (`pgatouR` 0.2.0). The headline change is that `pga_stats` now
accepts vectors of stat IDs and years.

### Breaking changes

- **`pga_player_tournament_status`**: when the API returns a status object
  whose scalar fields are all `null` ("player not currently in a tournament"),
  this function now returns an empty `DataFrame` instead of a 1-row
  all-`None` `DataFrame`. Callers should use `len(df) > 0` to detect the
  "currently playing" condition.
- **`pga_player_tournament_status`**: the phantom `round_display` column
  (which was always `None` because the GraphQL fragment doesn't return
  `roundDisplay` from that path) is now joined by correctly-mapped
  `round_status_display` and `round_status_color` columns. The old
  `round_display` column is retained but is now populated only when the
  upstream fragment actually returns it.
- **`pga_player_stats`**: `rank` is now an `Int64` nullable integer instead
  of a string. Code that compared against string `"1"` must compare
  against `1`.
- **`pga_leaderboard`**: `total_sort` and `score_sort` are now float
  columns instead of strings. Display columns (`total`, `score`, `thru`)
  remain strings — see §14 of `PGATOUR_R_HARDENING_NOTES.md`.
- **`pga_stats`**: every row now carries a `stat_id` and `year` column.
  Existing callers that selected by column position rather than name may
  need to adjust.

### New features

- **`pga_stats`** now accepts `stat_id: str | list[str]` and
  `year: int | list[int] | None`. The upstream `StatDetails` GraphQL
  operation only takes one `(statId, year)` per call, so multi-input
  requests loop client-side and concatenate.
- **`pga_stats` and `pga_fedex_cup`** gained an `event_query` keyword
  argument forwarded to the GraphQL `StatDetailEventQuery` variable
  ("Last 5 events", FedEx Fall filters, etc).
- **`pga_content(path)`** — wraps the `GenericContentCompressed`
  GraphQL operation, returns raw parsed JSON.
- **`pga_odds_interactivity()`** — `GET /odds/interactivity`.
- **`pga_speed_rounds(tour)`** — `GET /content/watch/speedRounds/{tour}`.
- **`PGA_API_KEY`** environment variable overrides the embedded public
  API key, so the package keeps working if the upstream rotates it.
- **`PGATOUR_VERBOSE`** environment variable (truthy = anything other
  than empty / `0` / `false` / `no` / `off`) elevates request envelope
  logs to `INFO`. The `pgatourpy` logger also emits at `DEBUG` regardless;
  enable it with `logging.getLogger("pgatourpy").setLevel(logging.DEBUG)`.
- **`PgaTourError`** is now exported. All transport, parse, and
  decompression failures raise this rather than bare `RuntimeError` /
  `OSError`, with a message that names the operation and step.

### Bug fixes

- **`pga_player_results`** now iterates every season in `resultsData`
  (previously dropped all but the first), and adds a `season` column.
  Dynamic header labels (including duplicate `Position` columns) are now
  deduplicated by the new `_make_unique_snake` helper.
- **`pga_player_tournament_status`** now maps the real
  `roundStatusDisplay` and `roundStatusColor` fields from the GraphQL
  fragment (previously mapped a phantom `roundDisplay` field that always
  came back as `null`).
- **`pga_player_stats`** coerces `rank` to nullable `Int64`.
- **`pga_player_profile`** docstring now matches the actual return shape.
- **`pga_shot_details`** explicitly guards against `null` / `[]` / non-dict
  `holes` payloads — relevant for cut players and untracked rounds.
- **`pga_leaderboard`** uses `.get()`-with-fallback on every player and
  scoringData field; partial player rows no longer raise.

### Robustness / performance

- **Transport**: requests now retry up to 3 times with exponential
  backoff on 408 / 429 / 5xx and on `httpx.TransportError` /
  `TimeoutException`. The 30s timeout is preserved.
- **JSON parsing**: every `.json()` call is wrapped — a non-JSON 200
  response now raises `PgaTourError` with the operation name, status
  code, and a body snippet instead of a cryptic `JSONDecodeError`.
- **Decompression**: `decompress_payload` validates input (non-empty
  string) and raises a clear error at each failure step (base64
  decode, gunzip, JSON parse). Invalid base64 is rejected via
  `validate=True` so garbage doesn't silently propagate.
- **`pga_tee_times`** now builds one `DataFrame` per group (broadcasting
  group-level fields) and concatenates once at the end, instead of
  appending one dict per player.

### Testing / infra

- **69 offline tests** across 8 test files. The transport functions
  (`graphql_request`, `rest_request`) are mocked via `pytest` fixtures
  in `tests/conftest.py`, and synthetic API responses live in
  `tests/fixtures/`. Regenerate with `python scripts/generate_fixtures.py`.
- **CI**: `.github/workflows/test.yaml` runs `pytest` on Ubuntu and
  macOS across Python 3.10–3.13 for every push and pull request.

## [0.1.0]

Initial release.
