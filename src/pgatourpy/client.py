"""Public API functions for pgatourPY."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from pgatourpy._api import decompress_payload, graphql_request, rest_request

VALID_TOUR_CODES = {"R", "S", "H"}


def _validate_tour(tour: str) -> None:
    if tour not in VALID_TOUR_CODES:
        raise ValueError(
            f"Invalid tour code: {tour!r}. Must be one of {VALID_TOUR_CODES}"
        )


def _epoch_ms_to_datetime(ms: Any) -> datetime | None:
    """Convert epoch milliseconds to UTC datetime, or None."""
    if ms is None or (isinstance(ms, float) and pd.isna(ms)):
        return None
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def _safe_get(d: dict, *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dicts."""
    for key in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
        if d is default:
            return default
    return d


# ---------------------------------------------------------------------------
# Live Tournament Data
# ---------------------------------------------------------------------------


def pga_leaderboard(tournament_id: str) -> pd.DataFrame:
    """Get tournament leaderboard.

    Args:
        tournament_id: Tournament ID (e.g., "R2026475").

    Returns:
        DataFrame with one row per player.
    """
    data = graphql_request(
        "LeaderboardCompressedV3",
        {"leaderboardCompressedV3Id": tournament_id},
    )
    payload = _safe_get(data, "leaderboardCompressedV3", "payload")
    if not payload:
        return pd.DataFrame()

    parsed = decompress_payload(payload)
    players = parsed.get("players", [])
    if not players:
        return pd.DataFrame()

    rows = []
    for p in players:
        player = p.get("player", {})
        scoring = p.get("scoringData", {})
        rounds = scoring.get("rounds", [])
        row = {
            "player_id": player.get("id"),
            "first_name": player.get("firstName"),
            "last_name": player.get("lastName"),
            "display_name": player.get("displayName"),
            "country": player.get("country"),
            "position": scoring.get("position"),
            "total": scoring.get("total"),
            "total_sort": scoring.get("totalSort"),
            "thru": scoring.get("thru"),
            "score": scoring.get("score"),
            "score_sort": scoring.get("scoreSort"),
            "current_round": scoring.get("currentRound"),
            "player_state": scoring.get("playerState"),
        }
        for i, r in enumerate(rounds, 1):
            row[f"round_{i}"] = r
        rows.append(row)

    return pd.DataFrame(rows)


def pga_current_leaders(tournament_id: str) -> pd.DataFrame:
    """Get current leaders snapshot (top 15).

    Args:
        tournament_id: Tournament ID (e.g., "R2026475").

    Returns:
        DataFrame of current leaders.
    """
    data = graphql_request(
        "CurrentLeadersCompressed",
        {"tournamentId": tournament_id},
    )
    payload = _safe_get(data, "currentLeadersCompressed", "payload")
    if not payload:
        return pd.DataFrame()

    parsed = decompress_payload(payload)
    players = parsed.get("players", [])
    if not players:
        return pd.DataFrame()

    # Response is a flat list of dicts
    if isinstance(players, list) and isinstance(players[0], dict):
        rows = []
        for p in players:
            rows.append({
                "player_id": p.get("id"),
                "first_name": p.get("firstName"),
                "last_name": p.get("lastName"),
                "display_name": p.get("displayName"),
                "country": p.get("country"),
                "position": p.get("position"),
                "total_score": p.get("totalScore"),
                "thru": p.get("thru"),
                "round_score": p.get("roundScore"),
                "round_header": p.get("roundHeader"),
                "player_state": p.get("playerState"),
                "back_nine": p.get("backNine"),
                "group_number": p.get("groupNumber"),
            })
        return pd.DataFrame(rows)

    return pd.DataFrame(players)


def pga_tee_times(tournament_id: str) -> pd.DataFrame:
    """Get tee times for a tournament.

    Args:
        tournament_id: Tournament ID (e.g., "R2026475").

    Returns:
        DataFrame with one row per player per round.
    """
    data = graphql_request(
        "TeeTimesCompressedV2",
        {"teeTimesCompressedV2Id": tournament_id},
    )
    payload = _safe_get(data, "teeTimesCompressedV2", "payload")
    if not payload:
        return pd.DataFrame()

    parsed = decompress_payload(payload)
    rounds = parsed.get("rounds", [])
    if not rounds:
        return pd.DataFrame()

    rows = []
    for rnd in rounds:
        round_num = rnd.get("roundInt")
        round_display = rnd.get("roundDisplay")
        round_status = rnd.get("roundStatus")
        for group in rnd.get("groups", []):
            tee_time = _epoch_ms_to_datetime(group.get("teeTime"))
            for player in group.get("players", []):
                rows.append({
                    "round_number": round_num,
                    "round_display": round_display,
                    "round_status": round_status,
                    "group_number": group.get("groupNumber"),
                    "tee_time": tee_time,
                    "start_tee": group.get("startTee"),
                    "back_nine": group.get("backNine", False),
                    "player_id": player.get("id"),
                    "first_name": player.get("firstName"),
                    "last_name": player.get("lastName"),
                    "display_name": player.get("displayName"),
                    "country": player.get("country"),
                })

    return pd.DataFrame(rows)


def pga_scorecard(tournament_id: str, player_id: str) -> pd.DataFrame:
    """Get hole-by-hole scorecard.

    Args:
        tournament_id: Tournament ID (e.g., "R2026475").
        player_id: Player ID (e.g., "39971").

    Returns:
        DataFrame with one row per hole per round.
    """
    data = graphql_request(
        "ScorecardCompressedV3",
        {"tournamentId": tournament_id, "playerId": player_id},
    )
    payload = _safe_get(data, "scorecardCompressedV3", "payload")
    if not payload:
        return pd.DataFrame()

    parsed = decompress_payload(payload)
    round_scores = parsed.get("roundScores", [])
    if not round_scores:
        return pd.DataFrame()

    rows = []
    for rnd in round_scores:
        round_num = rnd.get("roundNumber")
        course_name = rnd.get("courseName")
        round_total = rnd.get("total")
        round_stp = rnd.get("scoreToPar")

        for nine_key in ("firstNine", "secondNine"):
            nine = rnd.get(nine_key, {})
            if not nine:
                continue
            for hole in nine.get("holes", []):
                rows.append({
                    "round_number": round_num,
                    "hole_number": hole.get("holeNumber"),
                    "par": hole.get("par"),
                    "score": hole.get("score"),
                    "status": hole.get("status"),
                    "yardage": hole.get("yardage"),
                    "round_score": hole.get("roundScore"),
                    "sequence_number": hole.get("sequenceNumber"),
                    "course_name": course_name,
                    "round_total": round_total,
                    "round_score_to_par": round_stp,
                })

    return pd.DataFrame(rows)


def pga_shot_details(
    tournament_id: str,
    player_id: str,
    round: int,
    *,
    include_radar: bool = False,
) -> pd.DataFrame:
    """Get shot-level tracking data with coordinates.

    Args:
        tournament_id: Tournament ID (e.g., "R2026475").
        player_id: Player ID (e.g., "39971").
        round: Round number (1-4).
        include_radar: Include radar data.

    Returns:
        DataFrame with one row per stroke.
    """
    data = graphql_request(
        "shotDetailsV4Compressed",
        {
            "tournamentId": tournament_id,
            "playerId": player_id,
            "round": int(round),
            "includeRadar": include_radar,
        },
    )
    payload = _safe_get(data, "shotDetailsV4Compressed", "payload")
    if not payload:
        return pd.DataFrame()

    parsed = decompress_payload(payload)
    holes = parsed.get("holes", [])
    if not holes:
        return pd.DataFrame()

    rows = []
    for hole in holes:
        hole_num = hole.get("holeNumber")
        par = hole.get("par")
        yardage = hole.get("yardage")
        hole_status = hole.get("status")
        hole_score = hole.get("score")

        for stroke in hole.get("strokes", []):
            row = {
                "hole_number": hole_num,
                "par": par,
                "yardage": yardage,
                "hole_status": hole_status,
                "hole_score": hole_score,
                "stroke_number": stroke.get("strokeNumber"),
                "play_by_play": stroke.get("playByPlay"),
                "distance": stroke.get("distance"),
                "distance_remaining": stroke.get("distanceRemaining"),
                "stroke_type": stroke.get("strokeType"),
                "from_location": stroke.get("fromLocation"),
                "to_location": stroke.get("toLocation"),
                "from_location_code": stroke.get("fromLocationCode"),
                "to_location_code": stroke.get("toLocationCode"),
                "final_stroke": stroke.get("finalStroke"),
            }
            # Flatten coordinate data from overview
            overview = stroke.get("overview", {})
            if isinstance(overview, dict):
                for coord_key in ("leftToRightCoords", "bottomToTopCoords"):
                    coords = overview.get(coord_key, {})
                    if isinstance(coords, dict):
                        for point in ("fromCoords", "toCoords"):
                            pt = coords.get(point, {})
                            if isinstance(pt, dict):
                                prefix = f"{coord_key}.{point}"
                                for k in ("x", "y", "tourcastX", "tourcastY", "tourcastZ"):
                                    row[f"{prefix}.{k}"] = pt.get(k)
            rows.append(row)

    return pd.DataFrame(rows)


def pga_odds(tournament_id: str) -> pd.DataFrame:
    """Get odds to win for a tournament.

    Args:
        tournament_id: Tournament ID (e.g., "R2026475").

    Returns:
        DataFrame with player odds data.
    """
    data = graphql_request(
        "oddsToWinCompressed",
        {"tournamentId": tournament_id},
    )
    payload = _safe_get(data, "oddsToWinCompressed", "payload")
    if not payload:
        return pd.DataFrame()

    parsed = decompress_payload(payload)

    for key in ("players", "odds", "rows"):
        if key in parsed:
            return pd.json_normalize(parsed[key])

    if isinstance(parsed, list):
        return pd.json_normalize(parsed)

    return pd.DataFrame()


def pga_coverage(tournament_id: str) -> pd.DataFrame:
    """Get broadcast/streaming coverage info.

    Args:
        tournament_id: Tournament ID (e.g., "R2026475").

    Returns:
        DataFrame of coverage entries.
    """
    data = graphql_request("Coverage", {"tournamentId": tournament_id})
    coverage = _safe_get(data, "coverage")
    if not coverage:
        return pd.DataFrame()

    items = coverage.get("coverageType", [])
    broadcast_types = {
        "BroadcastFullTelecast",
        "BroadcastFeaturedGroup",
        "BroadcastFeaturedHole",
    }
    items = [i for i in items if i.get("__typename") in broadcast_types]
    if not items:
        return pd.DataFrame()

    rows = []
    for item in items:
        rows.append({
            "coverage_type": item.get("__typename"),
            "id": item.get("id"),
            "stream_title": item.get("streamTitle"),
            "round_number": item.get("roundNumber"),
            "start_time": _epoch_ms_to_datetime(item.get("startTime")),
            "end_time": _epoch_ms_to_datetime(item.get("endTime")),
            "live_status": item.get("liveStatus"),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Statistics & Standings
# ---------------------------------------------------------------------------


def pga_stats(
    stat_id: str,
    year: int | None = None,
    tour: str = "R",
) -> pd.DataFrame:
    """Get PGA Tour statistics.

    Args:
        stat_id: Stat ID (e.g., "02675" for SG: Total).
        year: Season year. Defaults to current season.
        tour: Tour code. Defaults to "R".

    Returns:
        DataFrame with player rankings. Metadata available via
        ``df.attrs`` (stat_title, stat_description, tour_avg, year).
    """
    _validate_tour(tour)
    variables: dict[str, Any] = {"tourCode": tour, "statId": stat_id}
    if year is not None:
        variables["year"] = int(year)

    data = graphql_request("StatDetails", variables)
    details = data.get("statDetails")
    if not details:
        return pd.DataFrame()

    all_rows = details.get("rows", [])
    if not all_rows:
        return pd.DataFrame()

    player_rows = [r for r in all_rows if r.get("__typename") == "StatDetailsPlayer"]
    if not player_rows:
        return pd.DataFrame()

    stat_headers = details.get("statHeaders", [])

    rows = []
    for pr in player_rows:
        row = {
            "rank": pr.get("rank"),
            "rank_diff": pr.get("rankDiff"),
            "rank_change_tendency": pr.get("rankChangeTendency"),
            "player_id": pr.get("playerId"),
            "player_name": pr.get("playerName"),
            "country": pr.get("country"),
            "country_flag": pr.get("countryFlag"),
        }
        stats = pr.get("stats", [])
        for i, header in enumerate(stat_headers):
            val = stats[i].get("statValue") if i < len(stats) else None
            row[header] = val
        rows.append(row)

    df = pd.DataFrame(rows)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce").astype("Int64")
    df.attrs["stat_title"] = details.get("statTitle")
    df.attrs["stat_description"] = details.get("statDescription")
    df.attrs["tour_avg"] = details.get("tourAvg")
    df.attrs["year"] = details.get("year")
    df.attrs["display_season"] = details.get("displaySeason")
    return df


def pga_fedex_cup(
    year: int | None = None,
    tour: str = "R",
) -> pd.DataFrame:
    """Get FedExCup standings.

    Args:
        year: Season year. Defaults to current year.
        tour: Tour code. Defaults to "R".

    Returns:
        DataFrame with player standings.
    """
    _validate_tour(tour)
    if year is None:
        year = datetime.now().year

    data = graphql_request(
        "TourCupSplit",
        {"tourCode": tour, "id": "02671", "year": int(year)},
    )
    cup = data.get("tourCupSplit")
    if not cup:
        return pd.DataFrame()

    players = cup.get("projectedPlayers") or cup.get("officialPlayers") or []
    player_rows = [
        p for p in players if p.get("__typename") == "TourCupCombinedPlayer"
    ]
    if not player_rows:
        return pd.DataFrame()

    rows = []
    for p in player_rows:
        rows.append({
            "player_id": p.get("id"),
            "first_name": p.get("firstName"),
            "last_name": p.get("lastName"),
            "display_name": p.get("displayName"),
            "country": p.get("country"),
            "country_flag": p.get("countryFlag"),
            "this_week_rank": p.get("thisWeekRank"),
            "previous_week_rank": p.get("previousWeekRank"),
            "projected_rank": _safe_get(p, "rankingData", "projected"),
            "official_rank": _safe_get(p, "rankingData", "official"),
            "projected_points": _safe_get(p, "pointData", "projected"),
            "official_points": _safe_get(p, "pointData", "official"),
            "movement": _safe_get(p, "rankingData", "movement"),
            "movement_amount": _safe_get(p, "rankingData", "movementAmount"),
        })

    return pd.DataFrame(rows)


def pga_scorecard_comparison(
    tournament_id: str,
    player_ids: list[str],
    category: str = "SCORING",
) -> pd.DataFrame:
    """Get scorecard stat comparison between players.

    Args:
        tournament_id: Tournament ID (e.g., "R2026475").
        player_ids: List of player IDs to compare.
        category: Comparison category (e.g., "SCORING", "DRIVING").

    Returns:
        DataFrame of comparison category pills.
    """
    data = graphql_request(
        "ScorecardStatsComparisonCategories",
        {
            "tournamentId": tournament_id,
            "playerIds": player_ids,
            "category": category,
        },
    )
    comparison = _safe_get(data, "scorecardStatsComparison")
    if not comparison:
        return pd.DataFrame()

    pills = comparison.get("categoryPills", [])
    if not pills:
        return pd.DataFrame([{
            "tournament_id": comparison.get("tournamentId"),
            "category": comparison.get("category"),
        }])

    df = pd.DataFrame(pills)
    df.columns = ["display_text", "category"]
    df.attrs["tournament_id"] = comparison.get("tournamentId")
    df.attrs["selected_category"] = comparison.get("category")
    return df


# ---------------------------------------------------------------------------
# Players & Tournaments
# ---------------------------------------------------------------------------


def pga_players(tour: str = "R") -> pd.DataFrame:
    """Get PGA Tour player directory.

    Args:
        tour: Tour code. Defaults to "R".

    Returns:
        DataFrame with one row per player.
    """
    _validate_tour(tour)
    resp = rest_request(f"player/list/{tour}")
    players = resp.get("players", [])
    if not players:
        return pd.DataFrame()

    rows = []
    for p in players:
        rows.append({
            "player_id": p.get("id"),
            "tour_code": p.get("tourCode"),
            "is_primary": p.get("isPrimary"),
            "is_active": p.get("isActive"),
            "first_name": p.get("firstName"),
            "last_name": p.get("lastName"),
            "display_name": p.get("displayName"),
            "short_name": p.get("shortName"),
            "country": p.get("country"),
            "country_flag": p.get("countryFlag"),
            "age": _safe_get(p, "playerBio", "age"),
            "primary_tour": p.get("primaryTour"),
        })

    return pd.DataFrame(rows)


def pga_tournaments(ids: str | list[str]) -> pd.DataFrame:
    """Get tournament metadata.

    Args:
        ids: One or more tournament IDs (e.g., "R2026475").

    Returns:
        DataFrame with one row per tournament.
    """
    if isinstance(ids, str):
        ids = [ids]

    data = graphql_request("Tournaments", {"ids": ids})
    tournaments = data.get("tournaments", [])
    if not tournaments:
        return pd.DataFrame()

    rows = []
    for t in tournaments:
        weather = t.get("weather") or {}
        rows.append({
            "id": t.get("id"),
            "tournament_name": t.get("tournamentName"),
            "tournament_status": t.get("tournamentStatus"),
            "display_date": t.get("displayDate"),
            "season_year": t.get("seasonYear"),
            "country": t.get("country"),
            "state": t.get("state"),
            "city": t.get("city"),
            "timezone": t.get("timezone"),
            "format_type": t.get("formatType"),
            "current_round": t.get("currentRound"),
            "round_status": t.get("roundStatus"),
            "round_display": t.get("roundDisplay"),
            "round_status_display": t.get("roundStatusDisplay"),
            "scored_level": t.get("scoredLevel"),
            "tournament_site_url": t.get("tournamentSiteURL"),
            "beauty_image": t.get("beautyImage"),
            "headshot_base_url": t.get("headshotBaseUrl"),
            "weather_temp_f": weather.get("tempF"),
            "weather_temp_c": weather.get("tempC"),
            "weather_condition": weather.get("condition"),
            "weather_wind_mph": weather.get("windSpeedMPH"),
            "weather_humidity": weather.get("humidity"),
            "courses": [
                {
                    "id": c.get("id"),
                    "course_name": c.get("courseName"),
                    "course_code": c.get("courseCode"),
                    "host_course": c.get("hostCourse"),
                }
                for c in (t.get("courses") or [])
            ],
        })

    return pd.DataFrame(rows)


def pga_schedule(
    year: int | None = None,
    tour: str = "R",
) -> pd.DataFrame:
    """Get season schedule.

    Args:
        year: Season year. Defaults to current year.
        tour: Tour code. Defaults to "R".

    Returns:
        DataFrame with one row per tournament including dates, purse,
        course, champion, and FedExCup points.
    """
    _validate_tour(tour)
    if year is None:
        year = datetime.now().year

    resp = rest_request(f"schedule/{tour}/{year}")
    tournaments = resp.get("tournaments", [])
    if not tournaments:
        return pd.DataFrame()

    rows = []
    for t in tournaments:
        champions = t.get("champions") or []
        champion_name = champions[0].get("displayName") if champions else None
        course = t.get("courseData") or {}
        standings = t.get("standings") or {}

        rows.append({
            "tournament_id": t.get("tournamentId"),
            "tournament_name": t.get("name"),
            "year": t.get("year"),
            "month": t.get("month"),
            "display_date": t.get("displayDate"),
            "status": t.get("status"),
            "purse": t.get("purse"),
            "fedex_cup_points": standings.get("value"),
            "champion": champion_name,
            "champion_earnings": t.get("championEarnings"),
            "course_name": course.get("name"),
            "city": course.get("city"),
            "state": course.get("stateCode"),
            "country": course.get("country"),
            "tournament_site_url": t.get("tournamentSiteUrl"),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Player Profiles
# ---------------------------------------------------------------------------


def pga_player_profile(player_id: str) -> dict:
    """Get player profile overview.

    Returns career highlights, wins, earnings, world ranking,
    FedExCup standing, and bio basics.

    Args:
        player_id: Player ID (e.g., "52955" for Ludvig Aberg).

    Returns:
        Dict with player info, ``highlights`` DataFrame, and
        ``overview`` DataFrame.
    """
    resp = rest_request(f"player/profiles/{player_id}")
    summary = _safe_get(resp, "summaryData", "summaryData") or {}

    highlights = pd.DataFrame([
        {
            "title": h.get("title"),
            "value": h.get("data"),
            "subtitle": h.get("subTitle"),
        }
        for h in summary.get("careerHighlights", [])
    ])

    overview_rows = []
    for section in resp.get("overview", []):
        if section.get("type") == "OVERVIEW_STATS":
            for item in section.get("items", []):
                for el in item.get("elements", []):
                    overview_rows.append({
                        "section": item.get("title"),
                        "subtitle": item.get("subtitle"),
                        "title": el.get("title"),
                        "value": el.get("data"),
                    })
    overview = pd.DataFrame(overview_rows) if overview_rows else pd.DataFrame()

    return {
        "player_id": resp.get("playerId"),
        "first_name": summary.get("firstName"),
        "last_name": summary.get("lastName"),
        "country": summary.get("country"),
        "country_code": summary.get("countryCode"),
        "born": summary.get("born"),
        "age": summary.get("age"),
        "birthplace": summary.get("birthplace"),
        "college": summary.get("college"),
        "turned_pro": summary.get("turnedPro"),
        "highlights": highlights,
        "overview": overview,
    }


def pga_player_career(player_id: str) -> pd.DataFrame:
    """Get player career data.

    Returns career achievements including starts, cuts, wins,
    finish distribution, and earnings.

    Args:
        player_id: Player ID.

    Returns:
        DataFrame of career statistics.
    """
    resp = rest_request(f"player/profiles/{player_id}/career")
    career_list = resp.get("career", [])
    if not career_list:
        return pd.DataFrame()

    rows = []
    for tour_data in career_list:
        tour_code = tour_data.get("tourCode")
        tour_name = tour_data.get("tourName")
        for section in tour_data.get("careerData", []):
            section_title = section.get("title")
            for widget in section.get("stats", []):
                widget_title = widget.get("title")
                for item in widget.get("data", []):
                    rows.append({
                        "tour_code": tour_code,
                        "tour_name": tour_name,
                        "section": section_title,
                        "widget": widget_title,
                        "label": item.get("label"),
                        "value": item.get("data"),
                    })

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def pga_player_results(player_id: str) -> pd.DataFrame:
    """Get player tournament results.

    Returns tournament-by-tournament results for the current season
    including round scores, finish position, FedExCup points, and earnings.

    Args:
        player_id: Player ID.

    Returns:
        DataFrame with one row per tournament.
    """
    resp = rest_request(f"player/profiles/{player_id}/results")
    results_list = resp.get("resultsData", [])
    if not results_list:
        return pd.DataFrame()

    results = results_list[0]
    headers = results.get("headers", [])
    data_rows = results.get("data", [])
    if not data_rows:
        return pd.DataFrame()

    # Build header labels
    header_labels = []
    for h in headers:
        if "label" in h:
            header_labels.append(h["label"])
        elif "labels" in h:
            prefix = h.get("groupLabel", "")
            for sub in h["labels"]:
                header_labels.append(f"{prefix} {sub}".strip())

    rows = []
    for d in data_rows:
        fields = d.get("fields", [])
        row = {"tournament_id": d.get("tournamentId")}
        for i, val in enumerate(fields):
            col = header_labels[i] if i < len(header_labels) else f"field_{i}"
            # Convert to snake_case
            col = col.lower().replace(" ", "_").replace("-", "_")
            row[col] = val
        rows.append(row)

    return pd.DataFrame(rows)


def pga_player_stats(player_id: str) -> pd.DataFrame:
    """Get player stats profile.

    Returns a player's full statistical profile with ranks and values
    for 130+ stats in a single call.

    Args:
        player_id: Player ID.

    Returns:
        DataFrame with one row per stat.
    """
    resp = rest_request(f"player/profiles/{player_id}/stats")
    stats = resp.get("stats", [])
    if not stats:
        return pd.DataFrame()

    rows = []
    for s in stats:
        cats = s.get("category", [])
        rows.append({
            "stat_id": s.get("statId"),
            "title": s.get("title"),
            "rank": s.get("rank"),
            "value": s.get("value"),
            "category": ", ".join(cats) if cats else None,
            "above_or_below": s.get("aboveOrBelow"),
            "field_average": s.get("fieldAverage"),
            "supporting_stat_desc": _safe_get(s, "supportingStat", "description"),
            "supporting_stat_value": _safe_get(s, "supportingStat", "value"),
            "supporting_value_desc": _safe_get(s, "supportingValue", "description"),
            "supporting_value_value": _safe_get(s, "supportingValue", "value"),
        })

    return pd.DataFrame(rows)


def pga_player_bio(player_id: str) -> dict:
    """Get player bio.

    Returns biographical text, amateur highlights, and widget data.

    Args:
        player_id: Player ID.

    Returns:
        Dict with ``text`` (list of paragraphs), ``amateur_highlights``
        (list of strings), and ``widgets`` DataFrame.
    """
    resp = rest_request(f"player/profiles/{player_id}/bio")
    bio = resp.get("bio", {})
    widgets = resp.get("widgets", [])

    bio_text = [e for e in bio.get("elements", []) if isinstance(e, str)]
    amateur = [e for e in bio.get("amateurHighlights", []) if isinstance(e, str)]

    widget_rows = []
    for w in widgets:
        for item in w.get("items", []):
            widget_rows.append({
                "widget_type": w.get("type"),
                "widget_title": w.get("title"),
                "label": item.get("label"),
                "value": item.get("value"),
            })

    return {
        "text": bio_text,
        "amateur_highlights": amateur,
        "widgets": pd.DataFrame(widget_rows) if widget_rows else pd.DataFrame(),
    }


def pga_player_tournament_status(player_id: str) -> pd.DataFrame:
    """Get player tournament status.

    Returns the player's status in the current tournament (if playing).

    Args:
        player_id: Player ID.

    Returns:
        DataFrame with one row, or empty if not in current tournament.
    """
    data = graphql_request(
        "getPlayerTournamentStatus",
        {"playerId": player_id},
    )
    status = data.get("playerTournamentStatus")
    if not status:
        return pd.DataFrame()

    return pd.DataFrame([{
        "player_id": status.get("playerId"),
        "tournament_id": status.get("tournamentId"),
        "tournament_name": status.get("tournamentName"),
        "position": status.get("position"),
        "thru": status.get("thru"),
        "score": status.get("score"),
        "total": status.get("total"),
        "round_display": status.get("roundDisplay"),
        "round_status": status.get("roundStatus"),
        "tee_time": status.get("teeTime"),
        "display_mode": status.get("displayMode"),
    }])


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------


def pga_news(
    tour: str = "R",
    franchises: list[str] | None = None,
    player_ids: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
) -> pd.DataFrame:
    """Get news articles.

    Args:
        tour: Tour code. Defaults to "R".
        franchises: Filter by franchise categories.
        player_ids: Filter by player IDs.
        limit: Max articles. Defaults to 20.
        offset: Pagination offset.

    Returns:
        DataFrame with one row per article.
    """
    _validate_tour(tour)
    variables: dict[str, Any] = {
        "tour": tour,
        "limit": limit,
        "offset": offset,
    }
    if franchises:
        variables["franchises"] = franchises
    if player_ids:
        variables["playerIds"] = player_ids

    data = graphql_request("NewsArticles", variables)
    articles = _safe_get(data, "newsArticles", "articles") or []
    if not articles:
        return pd.DataFrame()

    rows = []
    for a in articles:
        author = a.get("author") or {}
        rows.append({
            "id": a.get("id"),
            "headline": a.get("headline"),
            "teaser_headline": a.get("teaserHeadline"),
            "teaser_content": a.get("teaserContent"),
            "url": a.get("url"),
            "share_url": a.get("shareURL"),
            "publish_date": _epoch_ms_to_datetime(a.get("publishDate")),
            "update_date": _epoch_ms_to_datetime(a.get("updateDate")),
            "franchise": a.get("franchise"),
            "franchise_display_name": a.get("franchiseDisplayName"),
            "article_image": a.get("articleImage"),
            "author_first": author.get("firstName"),
            "author_last": author.get("lastName"),
            "is_live": a.get("isLive"),
            "ai_generated": a.get("aiGenerated"),
            "article_form_type": a.get("articleFormType"),
        })

    return pd.DataFrame(rows)


def pga_news_franchises(tour: str = "R") -> pd.DataFrame:
    """Get news franchise/category list.

    Args:
        tour: Tour code. Defaults to "R".

    Returns:
        DataFrame with franchise and label columns.
    """
    data = graphql_request(
        "NewsFranchises",
        {"tourCode": tour, "allFranchises": False},
    )
    franchises = data.get("newsFranchises", [])
    if not franchises:
        return pd.DataFrame()

    return pd.DataFrame([
        {
            "franchise": f.get("franchise"),
            "franchise_label": f.get("franchiseLabel"),
        }
        for f in franchises
    ])


def pga_videos(
    player_ids: list[str] | None = None,
    tournament_id: str | None = None,
    tour: str = "R",
    season: str | None = None,
    franchises: list[str] | None = None,
    limit: int = 18,
    offset: int = 0,
) -> pd.DataFrame:
    """Get player video highlights.

    Args:
        player_ids: Player IDs to filter by.
        tournament_id: Tournament ID (numeric part only, e.g., "475").
        tour: Tour code. Defaults to "R".
        season: Season year as string.
        franchises: Franchise filters.
        limit: Max videos. Defaults to 18.
        offset: Pagination offset.

    Returns:
        DataFrame of videos.
    """
    variables: dict[str, Any] = {
        "tourCode": tour,
        "limit": limit,
        "offset": offset,
    }
    if player_ids:
        variables["playerIds"] = player_ids
    if tournament_id:
        variables["tournamentId"] = tournament_id
    if season:
        variables["season"] = season
    if franchises:
        variables["franchises"] = franchises

    data = graphql_request("Videos", variables)
    videos = data.get("videos", [])
    if not videos:
        return pd.DataFrame()

    rows = []
    for v in videos:
        rows.append({
            "id": v.get("id"),
            "title": v.get("title"),
            "description": v.get("description"),
            "duration_secs": v.get("duration"),
            "category": v.get("category"),
            "category_display_name": v.get("categoryDisplayName"),
            "franchise": v.get("franchise"),
            "franchise_display_name": v.get("franchiseDisplayName"),
            "hole_number": v.get("holeNumber"),
            "round_number": v.get("roundNumber"),
            "shot_number": v.get("shotNumber"),
            "share_url": v.get("shareUrl"),
            "thumbnail": v.get("thumbnail"),
            "pub_date": _epoch_ms_to_datetime(v.get("pubdate")),
            "tournament_id": v.get("tournamentId"),
            "tour_code": v.get("tourCode"),
            "year": v.get("year"),
        })

    return pd.DataFrame(rows)


def pga_tourcast_videos(
    tournament_id: str,
    player_id: str,
    round: int,
    *,
    hole: int | None = None,
    shot: int | None = None,
) -> pd.DataFrame:
    """Get shot-by-shot video clips for a player round.

    Args:
        tournament_id: Tournament ID (e.g., "R2026475").
        player_id: Player ID.
        round: Round number.
        hole: Specific hole number.
        shot: Specific shot number.

    Returns:
        DataFrame of video clips.
    """
    variables: dict[str, Any] = {
        "tournamentId": tournament_id,
        "playerId": player_id,
        "round": int(round),
    }
    if hole is not None:
        variables["hole"] = int(hole)
    if shot is not None:
        variables["shot"] = int(shot)

    data = graphql_request("TourcastVideos", variables)
    videos = data.get("tourcastVideos", [])
    if not videos:
        return pd.DataFrame()

    rows = []
    for v in videos:
        rows.append({
            "id": v.get("id"),
            "title": v.get("title"),
            "description": v.get("description"),
            "duration_secs": v.get("duration"),
            "hole_number": v.get("holeNumber"),
            "round_number": v.get("roundNumber"),
            "shot_number": v.get("shotNumber"),
            "share_url": v.get("shareUrl"),
            "thumbnail": v.get("thumbnail"),
            "starts_at": _epoch_ms_to_datetime(v.get("startsAt")),
            "ends_at": _epoch_ms_to_datetime(v.get("endsAt")),
            "tournament_id": v.get("tournamentId"),
            "tour_code": v.get("tourCode"),
        })

    return pd.DataFrame(rows)
