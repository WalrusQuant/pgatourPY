# pgatouR hardening — port notes for pgatourPY

Reference for porting the 2026-05-16 hardening pass from `pgatouR` (the R sibling
package) to `pgatourPY`. Every item below is something that was found by code
review, fixed in the R repo, and verified with live API calls + an offline test
suite. Suggested Python file targets are best guesses based on the layout I saw
(`src/pgatourpy/{_api,client,graphql,stat_ids}.py`); adjust to match the actual
module split.

---

## 1. The headline bug: stats wasn't vectorized

**Symptom.** A user couldn't request multiple stats in one call, and couldn't
request multiple years in one call. The R wrapper took `stat_id` and `year` as
scalars, even though calling code (the docs) implied vectors might work.

**Root cause.** The upstream `StatDetails` GraphQL operation only accepts a
single `statId: String!` and a single `year: Int`. There is **no** `[String!]`
or `[Int!]` list form, and no sibling operation that batches. The wrapper just
mirrored the scalar schema and didn't loop client-side.

**Fix.** Accept vectors of `stat_id` and `year`. When length > 1, loop
internally, call the API once per `(stat_id, year)` pair, and concatenate the
results with `stat_id` + `year` columns prepended so chunks are
distinguishable.

**Python port.**
- File: wherever `pga_stats` lives (likely `client.py` or a `stats.py`).
- Change the signature to accept `stat_id: str | list[str]` and
  `year: int | list[int] | None`.
- Extract the single-call body into a private helper (`_stats_one`), then
  loop with `itertools.product(stat_ids, years)`.
- Concatenate results with `pandas.concat([..., ignore_index=True])` or
  `polars.concat(..., how="diagonal")` (the diagonal mode tolerates
  per-stat column differences just like `vctrs::vec_rbind`).
- Validate input: non-empty list, no `None`/empty strings.
- Also expose an `event_query` parameter that passes through to the GraphQL
  variable `StatDetailEventQuery` — the upstream API supports it for
  "Last 5 events" / FedEx Fall filters. Same change for the FedExCup wrapper.

R reference: `R/stats.R` (whole file rewritten), `R/fedex_cup.R` (just the
new `event_query` argument).

---

## 2. Player-profile bugs found by review

These were in functions added in a recent commit. Mirror them in the Python
`pga_player_*` equivalents.

### 2a. `roundDisplay` was a phantom field

`pga_player_tournament_status` mapped `round_display = status$roundDisplay`,
but the GraphQL fragment returns **`roundStatusDisplay`** and
**`roundStatusColor`** — not `roundDisplay`. Result: the column was always
`NA` and two real fields were silently dropped.

Fix: map both `roundStatusDisplay → round_status_display` and
`roundStatusColor → round_status_color`. Keep the old `round_display` column
if you want backward compatibility, but populate it from `roundStatusDisplay`
or remove it entirely. Check the Python port's `graphql/getPlayerTournamentStatus.graphql`
fragment to confirm what fields it actually fetches.

### 2b. `pga_player_results` silently dropped seasons

Code was indexing `results_list[[1]]`, so when the API returned multiple
seasons of results, only the first was returned. No documentation said so.

Fix: iterate every element of the results array. Add a `season` column
populated from `season` / `year` / `displaySeason` / index. Use
`make_unique` on the dynamic header labels (see §3 below) to avoid
collisions when two API headers map to the same snake_case name.

### 2c. `pga_player_stats` returned numeric ranks as strings

`rank`, `value`, `field_average`, etc. were all coerced to `character`. At
minimum, `rank` should be integer. In Python, that means `pd.to_numeric`
or `pl.Int64` for the rank column. Decide per-field whether to coerce
value/field_average to float (depends on whether they always parse cleanly).

### 2d. `pga_player_profile` docstring lied about its return

The docstring claimed return fields (`summary`, `bio`) that didn't exist.
The function actually returns a flat dict-like with scalar bio fields plus
two tibbles (`highlights`, `overview`). Audit the Python docstring against
the actual return shape — easy review item.

### 2e. `do.call(rbind, …)` is wrong for heterogeneous rows

Several player functions accumulated single-row tibbles in a loop, then
`rbind`-ed them. This (a) is slow, and (b) breaks when columns differ across
rows. The R fix was `vctrs::vec_rbind()`, which fills missing columns with
NA. The Python equivalent is `pd.concat([…], ignore_index=True)` (handles
missing columns) or `pl.concat(…, how="diagonal")`. Make sure your loops
build a list of frames and concat once at the end, not concat-in-a-loop.

---

## 3. Collision-safe column names from dynamic API headers

Several endpoints (`StatDetails.statHeaders`, the player-results header
array) return free-form display strings as column labels — e.g. "To Par",
"Avg. Distance", "Rank" (which appears twice in the same response for
FedEx vs. World rankings).

The old R code did `to_snake_case(gsub("[^a-zA-Z0-9 ]", "", x))`, which
- left spaces unconverted (output: `"to par"` not `"to_par"`),
- and didn't deduplicate, so two `"Rank"` headers became two columns
  with the literal same name → the assembled tibble was malformed.

New helper `make_unique_snake(x)`:
1. camelCase → snake_case
2. replace runs of any non-alphanumeric character with `_`
3. strip leading/trailing underscores
4. `make.unique(..., sep = "_")` so duplicates become `rank`, `rank_1`, …

**Python port.** Add `_make_unique_snake(labels: Sequence[str]) -> list[str]`
in a `parse.py` / utility module. Reuse for every dynamic-header parse site.
Suggested impl: regex `re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", x).lower()`
then `re.sub(r"[^a-z0-9]+", "_", x).strip("_")` then dedupe by appending
`_1`, `_2`, … (write the dedupe yourself or use `pandas.io.parsers.base_parser._dedup_names`).

R reference: `R/utils-parse.R::make_unique_snake`.

---

## 4. Transport hardening

The R transport (`pga_graphql_request`, `pga_rest_request`) had three latent
problems. All three apply to the Python `_api.py` equivalents.

### 4a. Hardcoded public API key with no override

The `x-api-key` is a public key embedded in the PGA Tour frontend. If they
rotate it, every installed copy of the package silently breaks with 401s.

**Fix.** Add an env-var fallback. R code:
```r
pga_api_key <- function() {
  key <- Sys.getenv("PGA_API_KEY", unset = "")
  if (nzchar(key)) key else .pga_api_key_default
}
```

**Python port.**
```python
_DEFAULT_API_KEY = "da2-gsrx5bibzbb4njvhl7t37wqyl4"
def _api_key() -> str:
    return os.environ.get("PGA_API_KEY") or _DEFAULT_API_KEY
```

### 4b. No timeout, no retry on transient failures

R had `req_throttle(rate=10)` but no `req_timeout` and no `req_retry`. A
hung CDN connection would block forever; a single 503 would permanently
fail the call.

**Fix in R.**
```r
req |>
  req_timeout(30) |>
  req_retry(max_tries = 3, is_transient = \(r) status %in% c(408, 429, 500, 502, 503, 504))
```

**Python port.**
- If using `httpx`: `httpx.Client(timeout=30.0)` and wrap the call with
  `tenacity.retry(stop=stop_after_attempt(3), retry=retry_if_exception_type(...) | retry_if_result(lambda r: r.status_code in {408,429,500,502,503,504}), wait=wait_exponential())`.
- If using `requests`: configure a `urllib3.Retry` adapter with
  `total=3, backoff_factor=0.5, status_forcelist=(408, 429, 500, 502, 503, 504)`.

### 4c. Non-JSON 200 responses crashed with a parse error instead of an HTTP error

The R code suppressed `httr2`'s automatic error parsing (`req_error(\(r) FALSE)`)
so it could distinguish GraphQL `errors` arrays from real HTTP errors. That's
correct — but it meant that a 200-status response with a non-JSON body
(misconfigured CDN, HTML error page from an intermediary) crashed at
`resp_body_json()` with a cryptic parse error instead of a meaningful one.

**Fix.** Wrap the JSON parse in a `tryCatch` that surfaces a clear error
naming the operation/path and the status code. In R it's `pga_parse_json(resp, context)`.

**Python port.** Wrap whatever `.json()` call you make in `try / except
JSONDecodeError`, and raise a custom exception with the operation name +
status code + a snippet of the actual body.

---

## 5. Decompression hardening

Several `*Compressed` GraphQL operations return base64-encoded gzip JSON.
The R decompressor was a 3-line function with no input validation. The
failure modes (empty string, non-base64, valid base64 of non-gzip data,
valid gzip of non-JSON data) all surfaced as cryptic C-level messages like
`internal error -3 in inflateEnd`.

**Fix.** Validate input (non-empty character scalar), then `tryCatch` each
stage (base64 → gunzip → JSON parse) with a clear error message naming
the failure step.

**Python port.** The equivalent is something like:
```python
def _decompress(payload: str) -> Any:
    if not isinstance(payload, str) or not payload:
        raise ValueError("payload must be a non-empty string")
    try:
        raw = base64.b64decode(payload)
    except (binascii.Error, ValueError) as e:
        raise PgaTourError(f"failed to base64-decode payload: {e}") from e
    try:
        decompressed = gzip.decompress(raw)
    except OSError as e:
        raise PgaTourError(f"failed to gunzip payload: {e}") from e
    try:
        return json.loads(decompressed)
    except json.JSONDecodeError as e:
        raise PgaTourError(f"failed to parse decompressed payload: {e}") from e
```

R reference: `R/utils-decompress.R`.

---

## 6. Defensive guards against empty list-shaped fields

When the upstream API returns "no data," it sometimes uses `null`, sometimes
`[]`, sometimes `{}`. After JSON parsing with `simplifyVector=TRUE`, R sees:

- `null` → `NULL` (OK, handled by `is.null()`)
- `[]`   → empty list (the booby trap — not null, not a data.frame)
- `[{...}]` → data.frame (the happy path)

The old guards used `if (is.null(x) || nrow(x) == 0)`, but `nrow(empty_list)`
returns `NULL`, and `NULL == 0` is `logical(0)`, which inside `||` becomes
NA → "missing value where TRUE/FALSE needed" crash. This bit `pga_shot_details`
specifically when a player had no shot data for that round.

**Fix.** Use the pattern:
```r
if (is.null(x) || length(x) == 0 || !is.data.frame(x) || nrow(x) == 0)
  return(tibble())
```

**Python port.** Less load-bearing because `json.loads` keeps `[]` as a
Python list and `{}` as a dict — no silent shape changes from a deserializer.
But: if you're using pandas DataFrames downstream, double-check guards in
`pga_shot_details` and similar: "no holes" might be `None` or `[]` or
`{"holes": []}` depending on the operation. Test with a fixture from a
player who didn't make the cut / wasn't tracked.

R reference: `R/shot_details.R:36-39`.

---

## 7. Performance: don't allocate one frame per leaf row

`pga_tee_times` was building one tibble per *player* inside a 4-deep loop
(rounds → groups → players → row). For a full field that's ~600
allocations per call, plus an O(n²) final `rbind`.

**Fix.** Build one tibble per *group* using `rep()` to broadcast the
group-level fields across all players in that group, then concat all
group-frames once at the end with `vec_rbind`.

**Python port.** Same idea: per group, build a dict-of-lists where each
value is length `n_players`, then `pd.DataFrame(dict)`. Concat all
group-frames once at the end. R reference: `R/tee_times.R`.

---

## 8. Missing endpoints (API coverage gaps)

The reference at `pgatour_api_docs.md` lists 17 GraphQL operations and 9
REST endpoints. R was missing one GraphQL op and two REST endpoints
(all low-value, but worth adding for completeness):

| Operation / endpoint | Returns | Notes |
|---|---|---|
| `GenericContentCompressed` (GraphQL) | CMS content fragments | Schema varies by `path`. Return as raw parsed JSON, not a DataFrame. |
| `GET /odds/interactivity` | Odds widget config | Return as raw parsed JSON. |
| `GET /content/watch/speedRounds/{tour}` | Speed-rounds video index | Return as raw parsed JSON. |

R reference: `R/content.R`, `inst/graphql/GenericContentCompressed.graphql`.

Multi-stat / multi-year is NOT a missing endpoint — the API genuinely
doesn't support batching. Client-side looping is the only path.

---

## 9. Offline test strategy

The R repo had no real test coverage (one helper-only file). Now it has 79
tests across 9 files, all offline.

**Approach.**
1. Capture real API responses **once** to fixture files. Script:
   `data-raw/fixtures.R` in the R repo loops every endpoint and saves the
   parsed body to `tests/testthat/fixtures/<name>.rds`. Re-runnable when
   the upstream schema changes.
2. In tests, mock the two transport functions (`pga_graphql_request`,
   `pga_rest_request`) using `testthat::local_mocked_bindings` so they
   return the fixture instead of hitting the network.
3. One test file per endpoint family. Tests assert tibble class, expected
   columns, expected dtypes, and (where applicable) row counts that prove
   loops happened.

**Python port.**
- Fixture capture: write `tests/conftest.py` helpers and a `scripts/capture_fixtures.py`
  that mirrors `data-raw/fixtures.R`. Save as JSON or pickle to
  `tests/fixtures/`.
- Mocking: use `pytest-mock` to patch `pgatourpy._api.graphql_request` and
  `pgatourpy._api.rest_request` to return loaded fixtures. The cleanest
  pattern is a fixture factory:
  ```python
  @pytest.fixture
  def mock_graphql(mocker, request):
      def _mock(name: str):
          fixture = json.loads((FIXTURES / f"{name}.json").read_text())
          mocker.patch("pgatourpy._api.graphql_request", return_value=fixture)
      return _mock
  ```
- Make sure the parsing layer of every function actually goes through the
  mocked transport — anything that does its own HTTP outside `_api.py`
  will be untestable.

**One subtle test pitfall:** since a single fixture is returned for *every*
call to the mocked transport, a multi-stat-multi-year test that expects
distinct `year` values across chunks will fail (every chunk has the same
fixture's year). Instead, test that the row count scales: `len(multi) == 2 *
len(single)`.

R reference: `tests/testthat/helper-fixtures.R`, `data-raw/fixtures.R`, and
the 9 `test-*.R` files for the assertion patterns.

---

## 10. Things that don't port

- The R repo had a vignette (`getting-started.Rmd`) being executed by
  R CMD check, which made the check break whenever the API shape drifted.
  We moved it to `vignettes/articles/` so pkgdown still serves it but
  the build doesn't run it. The Python equivalent (mkdocs articles in
  `docs/`) doesn't have this problem — mkdocs doesn't execute Python by
  default. Just be aware of it if you ever add a Jupyter notebook to docs.
- `vctrs::vec_rbind` is an R thing. In Python use `pd.concat` or
  `pl.concat(..., how="diagonal")`.
- The `%||%` operator: use `x or default` or `x if x is not None else default`.

---

## 11. CI for tests

The R repo had a `pkgdown.yaml` workflow but nothing actually running the
tests on push / PR. Added an `R-CMD-check.yaml` based on the standard
`r-lib/actions` template that runs on macOS-latest and ubuntu-latest
against R release, devel, and oldrel-1.

**Python port.** Same playbook with `pytest`:
- `.github/workflows/test.yaml` that runs on push and PR.
- Matrix over Python 3.10 / 3.11 / 3.12 / 3.13.
- Run `uv pip install -e .[dev]` or whatever the install command is, then
  `pytest -ra`.
- If you use `nox` or `tox`, run that instead.

The point: the offline test suite is only useful if it gates merges. Don't
skip this.

---

## 12. Verbose / debug mode

A `PGATOUR_VERBOSE` env var (truthy = anything other than empty / `0` /
`false` / `no` / `off`) makes both transports log their operation name and
variables / path before sending the request. Implemented in
`R/utils-api.R::pga_is_verbose()`. Useful when an upstream change
produces unexpected data and you need to see what was actually requested.

**Python port.** Pick one of:
- Use `logging` properly: `logger = logging.getLogger("pgatourpy")`,
  emit `logger.debug(...)` for each request, and let users do
  `logging.basicConfig(level=logging.DEBUG)` or
  `logging.getLogger("pgatourpy").setLevel(logging.DEBUG)`. This is the
  Pythonic answer and probably the right one.
- If you want parity with R: `PGATOUR_VERBOSE` env var check, write to
  `sys.stderr`. Less Pythonic but matches the R UX.

I'd lean toward `logging`. It composes with whatever logging infra the
user already has, and the env-var pattern (`PGATOUR_LOG_LEVEL=DEBUG`)
falls out naturally if you want it.

---

## 13. `%||%` portability

R-specific: `%||%` only landed in base R 4.4, but the package declares
`Depends: R (>= 4.1.0)`. Fixed by defining `%||%` locally in
`R/utils-parse.R`.

**Python port.** Non-issue. `x or default` and the walrus / ternary work
on every supported Python version.

---

## 14. Numeric sort keys vs display strings

The PGA Tour API returns scoring fields in two flavors:
- **Display strings**: `total = "-12"`, `score = "+2"`, `thru = "F"` or
  `"7:00 AM"`. These are intentionally character; do not parse.
- **Sort keys**: `totalSort`, `scoreSort`. These look like numbers
  (`"-12"`, `"2"`) but are sortable. R now coerces them with
  `as.numeric()` so callers can do arithmetic. The original wrapper
  returned them as character.

**Python port.** Audit `pga_leaderboard` and any other parser that
surfaces "...Sort" fields — they should be numeric (float or int as
appropriate). Display fields stay as `str`.

---

## 15. The `pga_leaderboard` partial-response guard

`pga_leaderboard` was constructing a `tibble()` with bare references
like `player_info$id`, `player_info$firstName`, no `%||%`. If the API
ever returns a player row missing one of those fields, `tibble()` errors
with column-length mismatch.

R fix: build a length-n `NA_character_` vector once and `%||%`-fallback
every column.

**Python port.** With pandas, you can build with
`df = pd.DataFrame({"player_id": player_info.get("id", pd.NA), ...})`,
but `.get()` on a column-like object isn't the same as on a dict. The
realistic pattern is:
```python
def _col(d, key, default=pd.NA):
    return d[key] if key in d else [default] * len(d)
```
or use pydantic models that fill missing fields with `None` so every
column is guaranteed to be the same length downstream.

---

## 16. Empty-status contract

`pga_player_tournament_status` used to return a 1-row tibble of all-NA
when the API said "player isn't in a tournament right now" (the status
object exists but every scalar field is `null`). Now it returns zero
rows in that case, so callers can do `if (nrow(res) > 0) ...` instead
of `if (nrow(res) > 0 && !is.na(res$position)) ...`.

**Python port.** Same audit: if the parser ever wraps a "no data"
response into a 1-row all-`None` DataFrame, change it to an empty
DataFrame. Pick the contract explicitly and document it.

---

## 17. NEWS / CHANGELOG

Added `NEWS.md` to the R repo with a structured entry for the
hardening release (Breaking changes, New features, Bug fixes,
Robustness / performance, Testing / infra). Users on upgrade will read
this; don't skip it.

**Python port.** Add a `CHANGELOG.md` (or use one if it exists) with
the same structure. The audience is the same — users finding out what
broke when they upgrade.

---

## Refreshed checklist for the Python port

- [ ] Vectorize `pga_stats(stat_id, year)` — accept lists, loop internally,
      add `stat_id` + `year` columns.
- [ ] Add `event_query` argument to `pga_stats` and `pga_fedex_cup`.
- [ ] Fix `pga_player_tournament_status`: map `roundStatusDisplay` and
      `roundStatusColor`; return empty when all scalar fields are null.
- [ ] Fix `pga_player_results`: iterate all seasons, add `season` column,
      dedupe header names.
- [ ] Fix `pga_player_stats`: coerce `rank` to int.
- [ ] Audit `pga_player_profile` docstring vs actual return shape.
- [ ] Replace any in-loop `pd.concat` with build-list-then-concat-once.
- [ ] Add `_make_unique_snake` helper, use everywhere dynamic header
      strings become columns.
- [ ] Add `PGA_API_KEY` env-var override.
- [ ] Add 30s timeout + 3-try retry on 408/429/5xx to the transport.
- [ ] Wrap `.json()` parsing in try/except with a custom error.
- [ ] Harden the decompressor: input validation + clear per-step errors.
- [ ] Add guards for empty-list-shaped "no data" responses (test with a
      cut player + a round with no shot tracking).
- [ ] Speed up `pga_tee_times`: per-group frames, single concat.
- [ ] Add `pga_content`, `pga_odds_interactivity`, `pga_speed_rounds`.
- [ ] Capture fixtures, mock transports in tests, write one test file
      per endpoint family.
- [ ] **Add a CI workflow that runs the test suite on push/PR.**
- [ ] **Add structured logging (probably via `logging`) for request-level
      debug visibility.**
- [ ] **Coerce sort-key fields (`totalSort`, `scoreSort`) to numeric;
      leave display strings as `str`.**
- [ ] **Guard `pga_leaderboard` against partial player rows.**
- [ ] **Make `pga_player_tournament_status` return an empty frame when
      the API has no real data, not a 1-row all-null frame.**
- [ ] **Maintain a `CHANGELOG.md` so users see what changed on upgrade.**

---

## Quick checklist for the Python port

- [ ] Vectorize `pga_stats(stat_id, year)` — accept lists, loop internally,
      add `stat_id` + `year` columns.
- [ ] Add `event_query` argument to `pga_stats` and `pga_fedex_cup`.
- [ ] Fix `pga_player_tournament_status`: map `roundStatusDisplay` and
      `roundStatusColor`.
- [ ] Fix `pga_player_results`: iterate all seasons, add `season` column,
      dedupe header names.
- [ ] Fix `pga_player_stats`: coerce `rank` to int.
- [ ] Audit `pga_player_profile` docstring vs actual return shape.
- [ ] Replace any in-loop `pd.concat` with build-list-then-concat-once.
- [ ] Add `_make_unique_snake` helper, use everywhere dynamic header
      strings become columns.
- [ ] Add `PGA_API_KEY` env-var override.
- [ ] Add 30s timeout + 3-try retry on 408/429/5xx to the transport.
- [ ] Wrap `.json()` parsing in try/except with a custom error.
- [ ] Harden the decompressor: input validation + clear per-step errors.
- [ ] Add guards for empty-list-shaped "no data" responses (test with a
      cut player + a round with no shot tracking).
- [ ] Speed up `pga_tee_times`: per-group frames, single concat.
- [ ] Add `pga_content`, `pga_odds_interactivity`, `pga_speed_rounds`.
- [ ] Capture fixtures, mock transports in tests, write one test file
      per endpoint family.

---

## Files changed in the R repo (for cross-reference)

```
M  .Rbuildignore                 # CLAUDE.md, vignettes/ excluded; dead README.Rmd line removed
M  DESCRIPTION                   # +vctrs; -knitr/rmarkdown/VignetteBuilder
M  NAMESPACE
M  NEWS.md                       # 0.2.0 entry
M  R/fedex_cup.R                 # event_query arg
M  R/leaderboard.R               # %||% guards + numeric sort keys
M  R/pgatouR-package.R           # imports: vctrs, req_timeout, req_retry
M  R/player_profile.R            # all 6 bugs from §2; empty-status contract
M  R/scorecard.R                 # removed dead is.list(holes) branch
M  R/shot_details.R              # empty-list guard, vec_rbind
M  R/stats.R                     # vectorization + event_query
M  R/tee_times.R                 # per-group frames
M  R/tournaments.R               # vec_rbind for courses list-column
M  R/utils-api.R                 # timeout, retry, env-var key, json safety, verbose
M  R/utils-decompress.R          # input validation + clear errors
M  R/utils-parse.R               # make_unique_snake helper, local %||%
A  R/content.R                   # pga_content, pga_odds_interactivity, pga_speed_rounds
A  inst/graphql/GenericContentCompressed.graphql
A  data-raw/fixtures.R           # fixture capture script
A  tests/testthat/helper-fixtures.R
A  tests/testthat/test-{stats,player-profile,leaderboard,scorecard,
                          tournaments,players,news-videos,compressed,
                          decompress,content}.R
A  tests/testthat/fixtures/      # 27 .rds files, ~450KB total
A  .github/workflows/R-CMD-check.yaml
R  vignettes/getting-started.Rmd -> vignettes/articles/getting-started.Rmd
M  CLAUDE.md                     # rewritten for new architecture
M  README.md                     # multi-stat/year examples, new endpoints, env-var note
```

Final state: 89 tests pass, `R CMD check` is clean (0 errors / 0 warnings /
1 trivial NOTE), all without network access. CI runs the check matrix on
push and PR across macOS, Ubuntu, and R release/devel/oldrel-1.

Commit log (oldest first):
```
chore(deps): add vctrs, register httr2 timeout/retry imports
fix: correctness bugs in player_profile, shot_details, scorecard
feat(stats): vectorize pga_stats, expose event_query filter
refactor: harden transport and decompression
perf: build pga_tee_times per-group instead of per-player
feat: add pga_content, pga_odds_interactivity, pga_speed_rounds
test: add offline test suite backed by API fixtures
chore: restructure long-form guide as a pkgdown article
docs: rewrite CLAUDE.md and refresh README for hardened package
ci: add R-CMD-check workflow
test: cover pga_content, pga_odds_interactivity, pga_speed_rounds
fix: harden tournaments + leaderboard parsers, drop dead Rbuildignore entry
feat: add PGATOUR_VERBOSE debug mode and back-port %||% locally
fix: return zero rows from pga_player_tournament_status when no status
docs: add NEWS.md entry for the hardening release
```
