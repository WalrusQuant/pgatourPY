"""Generate synthetic test fixtures for pgatourPY.

These mirror the *shape* of real API responses so the parser tests can
run fully offline. Re-run this script to regenerate fixtures if the
schema changes:

    python scripts/generate_fixtures.py

The synthetic data is intentionally minimal — just enough to exercise
every branch in the parsers (multi-season results, dynamic-header
dedupe, empty-status contract, partial player rows, etc.).
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
OUT.mkdir(parents=True, exist_ok=True)


def _compress(obj: dict | list) -> str:
    return base64.b64encode(gzip.compress(json.dumps(obj).encode())).decode()


def _write(name: str, obj) -> None:
    (OUT / f"{name}.json").write_text(json.dumps(obj, indent=2))


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

leaderboard_inner = {
    "players": [
        {
            "player": {
                "id": "34046",
                "firstName": "Jordan",
                "lastName": "Spieth",
                "displayName": "Jordan Spieth",
                "shortName": "J. Spieth",
                "country": "USA",
                "countryFlag": "us",
                "amateur": False,
            },
            "scoringData": {
                "position": "T1",
                "total": "-12",
                "totalSort": "-12",
                "thru": "F",
                "score": "-3",
                "scoreSort": "-3",
                "currentRound": 4,
                "playerState": "ACTIVE",
                "teeTime": 1773928800000,
                "courseId": "513",
                "groupNumber": 34,
                "backNine": False,
                "movementDirection": "UP",
                "movementAmount": "2",
                "totalStrokes": "272",
                "official": "1",
                "projected": "1",
                "rounds": ["68", "70", "67", "67"],
            },
        },
        {
            # Partial row: missing some scoring fields and player fields
            "player": {"id": "52955"},
            "scoringData": {},
        },
    ]
}
_write("LeaderboardCompressedV3", {
    "leaderboardCompressedV3": {"payload": _compress(leaderboard_inner)}
})


# ---------------------------------------------------------------------------
# Tee times — exercises per-group concat
# ---------------------------------------------------------------------------

teetimes_inner = {
    "rounds": [
        {
            "roundInt": 1,
            "roundDisplay": "Round 1",
            "roundStatus": "Complete",
            "groups": [
                {
                    "groupNumber": 1,
                    "teeTime": 1773928800000,  # 2026-03-19
                    "startTee": 1,
                    "backNine": False,
                    "players": [
                        {"id": "p1", "firstName": "A", "lastName": "One", "displayName": "A One", "country": "USA"},
                        {"id": "p2", "firstName": "B", "lastName": "Two", "displayName": "B Two", "country": "USA"},
                        {"id": "p3", "firstName": "C", "lastName": "Three", "displayName": "C Three", "country": "CAN"},
                    ],
                },
                {
                    "groupNumber": 2,
                    "teeTime": 1773929400000,
                    "startTee": 10,
                    "backNine": True,
                    "players": [
                        {"id": "p4", "firstName": "D", "lastName": "Four", "displayName": "D Four", "country": "GBR"},
                    ],
                },
                # Empty group should be skipped
                {"groupNumber": 3, "teeTime": 1773930000000, "startTee": 1, "players": []},
            ],
        }
    ]
}
_write("TeeTimesCompressedV2", {
    "teeTimesCompressedV2": {"payload": _compress(teetimes_inner)}
})


# ---------------------------------------------------------------------------
# StatDetails — dynamic headers including duplicate "Rank" labels
# ---------------------------------------------------------------------------

stats_inner_one = {
    "statDetails": {
        "tourCode": "R",
        "year": 2026,
        "displaySeason": "2025-26",
        "statId": "02675",
        "statTitle": "SG: Total",
        "statDescription": "Strokes Gained: Total",
        "tourAvg": "0.0",
        "statHeaders": ["Rank", "Avg.", "Total SG", "Rounds", "Rank"],
        "rows": [
            {
                "__typename": "StatDetailsPlayer",
                "playerId": "39971",
                "playerName": "Jordan Spieth",
                "country": "USA",
                "countryFlag": "us",
                "rank": "1",
                "rankDiff": "0",
                "rankChangeTendency": "FLAT",
                "stats": [
                    {"statValue": "1"}, {"statValue": "2.50"},
                    {"statValue": "+50.5"}, {"statValue": "20"},
                    {"statValue": "5"},
                ],
            },
            {
                "__typename": "StatDetailsPlayer",
                "playerId": "52955",
                "playerName": "Ludvig Aberg",
                "country": "SWE",
                "rank": "2",
                "rankDiff": "1",
                "rankChangeTendency": "UP",
                "stats": [
                    {"statValue": "2"}, {"statValue": "2.10"},
                    {"statValue": "+42.0"}, {"statValue": "20"},
                    {"statValue": "8"},
                ],
            },
            {"__typename": "StatDetailTourAvg", "displayName": "TOUR Avg", "value": "0.0"},
        ],
    }
}
_write("StatDetails", stats_inner_one)

# A second-year variant used for multi-year tests
stats_inner_two = json.loads(json.dumps(stats_inner_one))
stats_inner_two["statDetails"]["year"] = 2025
stats_inner_two["statDetails"]["displaySeason"] = "2024-25"
_write("StatDetails_2025", stats_inner_two)


# ---------------------------------------------------------------------------
# TourCupSplit (FedExCup)
# ---------------------------------------------------------------------------

fedex_inner = {
    "tourCupSplit": {
        "id": "02671",
        "season": "2025-26",
        "officialPlayers": [
            {
                "__typename": "TourCupCombinedPlayer",
                "id": "39971",
                "firstName": "Jordan", "lastName": "Spieth",
                "displayName": "Jordan Spieth",
                "country": "USA", "countryFlag": "us",
                "thisWeekRank": 1, "previousWeekRank": 2,
                "rankingData": {
                    "projected": 1, "official": 1,
                    "movement": "UP", "movementAmount": 1,
                },
                "pointData": {"projected": 3500, "official": 3500},
            },
            {"__typename": "TourCupCombinedInfo", "text": "info row"},
        ],
        "projectedPlayers": [],
    }
}
_write("TourCupSplit", fedex_inner)


# ---------------------------------------------------------------------------
# Player profile / career / results / stats / bio / tournament status
# ---------------------------------------------------------------------------

_write("player_profile", {
    "playerId": "52955",
    "summaryData": {
        "summaryData": {
            "firstName": "Ludvig", "lastName": "Aberg",
            "country": "Sweden", "countryCode": "SWE",
            "born": "1999-11-09", "age": 26,
            "birthplace": "Eslov, Sweden",
            "college": "Texas Tech",
            "turnedPro": 2023,
            "careerHighlights": [
                {"title": "PGA TOUR Wins", "data": "3", "subTitle": "career"},
                {"title": "Top 10s", "data": "15", "subTitle": "career"},
            ],
        }
    },
    "overview": [
        {
            "type": "OVERVIEW_STATS",
            "items": [
                {
                    "title": "Season Stats",
                    "subtitle": "2025-26",
                    "elements": [
                        {"title": "Earnings", "data": "$5,000,000"},
                        {"title": "Wins", "data": "2"},
                    ],
                },
            ],
        }
    ],
})

_write("player_career", {
    "career": [
        {
            "tourCode": "R",
            "tourName": "PGA TOUR",
            "careerData": [
                {
                    "title": "Career",
                    "stats": [
                        {
                            "title": "Performance",
                            "data": [
                                {"label": "Wins", "data": "3"},
                                {"label": "Top 10s", "data": "15"},
                                {"label": "Starts", "data": "75"},
                            ],
                        }
                    ],
                }
            ],
        }
    ]
})

_write("player_results", {
    "resultsData": [
        {
            "season": "2025-26",
            "headers": [
                {"label": "Date"},
                {"label": "Tournament"},
                {"label": "Position"},
                {"groupLabel": "Round", "labels": ["1", "2", "3", "4"]},
                {"label": "Position"},  # intentional duplicate → must dedupe
            ],
            "data": [
                {
                    "tournamentId": "R2026475",
                    "fields": ["Mar 19", "The Players", "T1", "68", "70", "67", "67", "T1"],
                },
                {
                    "tournamentId": "R2026476",
                    "fields": ["Mar 26", "Valspar", "T5", "70", "69", "71", "68", "T5"],
                },
            ],
        },
        {
            "season": "2024-25",
            "headers": [
                {"label": "Date"},
                {"label": "Tournament"},
                {"label": "Position"},
            ],
            "data": [
                {
                    "tournamentId": "R2025475",
                    "fields": ["Mar 20", "The Players", "T3"],
                },
            ],
        },
    ]
})

_write("player_stats", {
    "stats": [
        {
            "statId": "02675",
            "title": "SG: Total",
            "rank": "1",
            "value": "2.50",
            "category": ["SG"],
            "aboveOrBelow": "ABOVE",
            "fieldAverage": "0.0",
            "supportingStat": {"description": "Rounds", "value": "20"},
            "supportingValue": {"description": "Total SG", "value": "50.5"},
        },
        {
            "statId": "02568",
            "title": "Driving Distance",
            "rank": "10",
            "value": "310.5",
            "category": ["DRIVING"],
            "aboveOrBelow": "ABOVE",
            "fieldAverage": "295.0",
            "supportingStat": {"description": "Drives", "value": "100"},
            "supportingValue": None,
        },
    ]
})

_write("player_bio", {
    "bio": {
        "elements": [
            "Para one of bio text.",
            "Para two of bio text.",
        ],
        "amateurHighlights": [
            "NCAA champion",
            "Walker Cup",
        ],
    },
    "widgets": [
        {
            "type": "PERSONAL",
            "title": "Personal",
            "items": [
                {"label": "Born", "value": "1999-11-09"},
                {"label": "Height", "value": "6'2\""},
            ],
        }
    ],
})

# Empty-status: every scalar field null
_write("player_tournament_status_empty", {
    "playerTournamentStatus": {
        "playerId": None,
        "tournamentId": None,
        "tournamentName": None,
        "roundStatusDisplay": None,
        "roundStatusColor": None,
        "roundDisplay": None,
        "roundStatus": None,
        "position": None,
        "thru": None,
        "teeTime": None,
        "score": None,
        "total": None,
        "displayMode": None,
    }
})

# Populated status with the new mappings
_write("player_tournament_status_active", {
    "playerTournamentStatus": {
        "playerId": "52955",
        "tournamentId": "R2026475",
        "tournamentName": "The Players Championship",
        "roundStatusDisplay": "Round 4 - F",
        "roundStatusColor": "green",
        "roundDisplay": "R4",
        "roundStatus": "F",
        "position": "T1",
        "thru": "F",
        "teeTime": 1773928800000,
        "score": "-3",
        "total": "-12",
        "displayMode": "LIVE",
    }
})


# ---------------------------------------------------------------------------
# Players directory (REST)
# ---------------------------------------------------------------------------

_write("players_R", {
    "players": [
        {
            "id": "39971", "tourCode": "R", "isPrimary": True, "isActive": True,
            "firstName": "Jordan", "lastName": "Spieth",
            "displayName": "Jordan Spieth", "shortName": "J. Spieth",
            "country": "USA", "countryFlag": "us",
            "playerBio": {"age": 32}, "primaryTour": "R",
        }
    ]
})


# ---------------------------------------------------------------------------
# Tournaments (GraphQL)
# ---------------------------------------------------------------------------

_write("Tournaments", {
    "tournaments": [
        {
            "id": "R2026475",
            "tournamentName": "The Players Championship",
            "tournamentStatus": "InProgress",
            "displayDate": "Mar 19 - 22, 2026",
            "seasonYear": "2026",
            "country": "USA", "state": "FL", "city": "Ponte Vedra Beach",
            "timezone": "America/New_York",
            "formatType": "STROKE_PLAY",
            "currentRound": 4,
            "roundStatus": "F",
            "roundDisplay": "R4",
            "roundStatusDisplay": "Round 4",
            "scoredLevel": "PGATOUR",
            "tournamentSiteURL": "https://www.pgatour.com/example",
            "beautyImage": "",
            "headshotBaseUrl": "",
            "weather": {
                "tempF": 78, "tempC": 25, "condition": "Sunny",
                "windSpeedMPH": "10", "humidity": 60,
            },
            "courses": [
                {"id": "c1", "courseName": "TPC Sawgrass", "courseCode": "TPC", "hostCourse": True},
            ],
        }
    ]
})


# ---------------------------------------------------------------------------
# Schedule (REST)
# ---------------------------------------------------------------------------

_write("schedule_R_2026", {
    "tournaments": [
        {
            "tournamentId": "R2026475",
            "name": "The Players Championship",
            "year": 2026, "month": 3,
            "displayDate": "Mar 19 - 22",
            "status": "InProgress",
            "purse": 25000000,
            "standings": {"value": "750"},
            "champions": [{"displayName": "Jordan Spieth"}],
            "championEarnings": 4500000,
            "courseData": {
                "name": "TPC Sawgrass", "city": "Ponte Vedra Beach",
                "stateCode": "FL", "country": "USA",
            },
            "tournamentSiteUrl": "https://www.pgatour.com/example",
        }
    ]
})


# ---------------------------------------------------------------------------
# Scorecard / shot details (compressed)
# ---------------------------------------------------------------------------

scorecard_inner = {
    "roundScores": [
        {
            "roundNumber": 1, "courseName": "TPC Sawgrass",
            "total": "68", "scoreToPar": "-4",
            "firstNine": {
                "holes": [
                    {"holeNumber": i, "par": 4, "score": "4", "status": "BIRDIE",
                     "yardage": 400, "roundScore": "-1", "sequenceNumber": i}
                    for i in range(1, 10)
                ]
            },
            "secondNine": {
                "holes": [
                    {"holeNumber": i, "par": 4, "score": "4", "status": "PAR",
                     "yardage": 400, "roundScore": "-4", "sequenceNumber": i}
                    for i in range(10, 19)
                ]
            },
        }
    ]
}
_write("ScorecardCompressedV3", {
    "scorecardCompressedV3": {"payload": _compress(scorecard_inner)}
})

# Empty shot-details (cut player)
_write("shotDetailsV4Compressed_empty", {
    "shotDetailsV4Compressed": {"payload": _compress({"holes": []})}
})

shot_inner = {
    "holes": [
        {
            "holeNumber": 1, "par": 4, "yardage": 400,
            "status": "BIRDIE", "score": "3",
            "strokes": [
                {
                    "strokeNumber": 1, "playByPlay": "Drive",
                    "distance": 300, "distanceRemaining": 100,
                    "strokeType": "DRIVE", "fromLocation": "TEE",
                    "toLocation": "FAIRWAY",
                    "fromLocationCode": "T", "toLocationCode": "F",
                    "finalStroke": False,
                    "overview": {
                        "leftToRightCoords": {
                            "fromCoords": {"x": 0, "y": 0, "tourcastX": 0, "tourcastY": 0, "tourcastZ": 0},
                            "toCoords": {"x": 300, "y": 10, "tourcastX": 300, "tourcastY": 10, "tourcastZ": 0},
                        },
                    },
                }
            ],
        }
    ]
}
_write("shotDetailsV4Compressed", {
    "shotDetailsV4Compressed": {"payload": _compress(shot_inner)}
})


# ---------------------------------------------------------------------------
# Misc — odds, coverage, news, videos, content/speed_rounds/odds_interactivity
# ---------------------------------------------------------------------------

_write("oddsToWinCompressed", {
    "oddsToWinCompressed": {"payload": _compress({
        "players": [
            {
                "playerId": "34046", "odds": "+1200", "displayName": "Jordan Spieth",
                "oddsSort": 13, "oddsDirection": "DOWN", "optionId": "1",
                "url": "https://example.com/odds/34046",
            },
            {
                "playerId": "52955", "odds": "+800", "displayName": "Ludvig Aberg",
                "oddsSort": 9, "oddsDirection": "UP", "optionId": "2",
                "url": "https://example.com/odds/52955",
            },
        ]
    })}
})

_write("Coverage", {
    "coverage": {
        "coverageType": [
            {
                "__typename": "BroadcastFullTelecast",
                "id": "c1", "streamTitle": "Featured Group",
                "roundNumber": 1, "startTime": 1773928800000,
                "endTime": 1773939600000, "liveStatus": "LIVE",
            },
            {"__typename": "Other"},
        ]
    }
})

_write("NewsArticles", {
    "newsArticles": {
        "articles": [
            {
                "id": "n1", "headline": "Spieth wins again",
                "teaserHeadline": "Spieth wins", "teaserContent": "Lorem",
                "url": "/news/1", "shareURL": "/share/1",
                "publishDate": 1773928800000, "updateDate": 1773929000000,
                "franchise": "PGA_TOUR", "franchiseDisplayName": "PGA TOUR",
                "articleImage": "",
                "author": {"firstName": "Jane", "lastName": "Doe"},
                "isLive": False, "aiGenerated": False,
                "articleFormType": "ARTICLE",
            }
        ]
    }
})

_write("NewsFranchises", {
    "newsFranchises": [
        {"franchise": "PGA_TOUR", "franchiseLabel": "PGA TOUR"},
        {"franchise": "FEATURED", "franchiseLabel": "Featured"},
    ]
})

_write("Videos", {
    "videos": [
        {
            "id": "v1", "title": "Highlight", "description": "Cool",
            "duration": 90, "category": "HIGHLIGHTS",
            "categoryDisplayName": "Highlights",
            "franchise": "PGA_TOUR", "franchiseDisplayName": "PGA TOUR",
            "holeNumber": 17, "roundNumber": 4, "shotNumber": 1,
            "shareUrl": "/share/v1", "thumbnail": "",
            "pubdate": 1773928800000,
            "tournamentId": "475", "tourCode": "R", "year": "2026",
        }
    ]
})

_write("TourcastVideos", {
    "tourcastVideos": [
        {
            "id": "tv1", "title": "Shot 1", "description": "",
            "duration": 30, "holeNumber": 1, "roundNumber": 4,
            "shotNumber": 1, "shareUrl": "/share/tv1", "thumbnail": "",
            "startsAt": 1773928800000, "endsAt": 1773928830000,
            "tournamentId": "R2026475", "tourCode": "R",
        }
    ]
})

_write("GenericContentCompressed", {
    "genericContentCompressed": {"payload": _compress({"slug": "demo", "blocks": []})}
})

_write("odds_interactivity", {"widgets": [{"id": "ow1"}], "enabled": True})

_write("speed_rounds_R", {"tour": "R", "videos": [{"id": "sr1", "title": "Speed round"}]})


# ---------------------------------------------------------------------------
# Scorecard stats comparison
# ---------------------------------------------------------------------------

_write("web_config", {
    "defaultTournaments": {
        "R": [{"id": "R2026027", "leaderboardId": "R2026027"}],
        "Y": [{"id": "Y2026018", "leaderboardId": "Y2026018"}],
        "S": [{"id": "S2026619", "leaderboardId": "S2026619"}],
        "H": [{"id": "H2026027", "leaderboardId": "H2026027"}],
    }
})

_write("player_results_pills", {
    "playerId": "52955",
    "resultPills": [
        {
            "label": "Season",
            "queryArg": "season",
            "options": [
                {"value": "2026", "label": "2026", "selected": True},
                {"value": "2025", "label": "2025", "selected": False},
            ],
        }
    ],
    "resultsData": [
        {
            "title": "Results & Scorecards",
            "headers": [{"label": "Tournament"}, {"label": "Position"}],
            "data": [
                {"tournamentId": "R2026027", "fields": ["FedEx St. Jude", "4"]},
            ],
        }
    ],
})

_write("player_results_2025", {
    "playerId": "52955",
    "resultPills": [
        {
            "label": "Season",
            "queryArg": "season",
            "options": [
                {"value": "2026", "label": "2026", "selected": False},
                {"value": "2025", "label": "2025", "selected": True},
            ],
        }
    ],
    "resultsData": [
        {
            "title": "Results & Scorecards",
            "headers": [{"label": "Tournament"}, {"label": "Position"}],
            "data": [
                {"tournamentId": "R2025007", "fields": ["Genesis", "1"]},
                {"tournamentId": "R2025027", "fields": ["St. Jude", "T10"]},
            ],
        }
    ],
})

_write("Field", {
    "field": {
        "tournamentName": "FedEx St. Jude Championship",
        "id": "R2026027",
        "lastUpdated": "2026-08-15",
        "players": [
            {
                "id": "52955", "firstName": "Ludvig", "lastName": "Aberg",
                "displayName": "Åberg, Ludvig", "shortName": "L. Åberg",
                "amateur": False, "country": "SWE", "countryFlag": "se",
                "qualifier": False, "alternate": False, "withdrawn": False,
                "status": "IN", "owgr": "16", "rankingPoints": "3.2",
            }
        ],
        "alternates": [
            {
                "id": "99999", "firstName": "Alt", "lastName": "Player",
                "displayName": "Player, Alt", "shortName": "A. Player",
                "amateur": False, "country": "USA", "countryFlag": "us",
                "qualifier": False, "alternate": True, "withdrawn": False,
                "status": "ALT", "owgr": None, "rankingPoints": None,
            }
        ],
    }
})

_write("FieldStats", {
    "fieldStats": {
        "tournamentId": "R2026027",
        "fieldStatType": "CURRENT_FORM",
        "statHeaders": [],
        "players": [
            {
                "__typename": "FieldStatCurrentForm",
                "playerId": "52955",
                "totalRounds": 12,
                "tournamentResults": [
                    {"name": "Wyndham", "position": "T5", "score": "-12", "season": 2026}
                ],
                "strokesGainedHeader": ["Total", "OTT"],
                "strokesGained": [
                    {"statId": "02675", "statValue": "1.20"},
                    {"statId": "02567", "statValue": "0.40"},
                ],
            }
        ],
    }
})

_write("LeaderboardHoleByHole", {
    "leaderboardHoleByHole": {
        "tournamentId": "R2026027",
        "tournamentName": "FedEx St. Jude Championship",
        "currentRound": 3,
        "holeHeaders": [{"holeNumber": 1, "hole": "1", "par": 4}],
        "playerData": [
            {
                "playerId": "52955",
                "out": "32", "in": "34", "total": "66", "totalToPar": "-4",
                "courseId": "513", "courseCode": "SW",
                "scores": [
                    {
                        "holeNumber": 1, "par": 4, "yardage": 434,
                        "sequenceNumber": 1, "score": "3", "status": "BIRDIE",
                        "roundScore": "-1",
                    }
                ],
            }
        ],
    }
})

_write("TournamentPastResults", {
    "tournamentPastResults": {
        "id": "R2026027",
        "availableSeasons": [{"year": 2025, "displaySeason": "2025"}],
        "players": [
            {
                "id": "52955",
                "position": "T10",
                "total": "268",
                "parRelativeScore": "-12",
                "additionalData": ["750"],
                "player": {
                    "id": "52955", "firstName": "Ludvig", "lastName": "Aberg",
                    "displayName": "Ludvig Aberg", "shortName": "L. Aberg",
                    "amateur": False, "country": "SWE", "countryFlag": "se",
                },
                "rounds": [
                    {"score": "66", "parRelativeScore": "-4"},
                    {"score": "68", "parRelativeScore": "-2"},
                ],
            }
        ],
    }
})

_write("TournamentOverview", {
    "tournamentOverview": {
        "ticketsURL": "https://example.com/tickets",
        "tourcastURL": "https://example.com/tourcast",
        "shareURL": "https://example.com/share",
        "eventGuideURL": "https://example.com/guide",
        "overview": [
            {"label": "Purse", "value": "$20,000,000", "detail": "Winner $3.6M"},
        ],
        "defendingChampion": {
            "playerId": "46046", "displayName": "Scottie Scheffler",
            "year": 2025, "displaySeason": "2025", "score": "-16",
            "total": "264", "title": "Defending Champion", "countryCode": "USA",
        },
        "pastChampions": [
            {
                "playerId": "46046", "displayName": "Scottie Scheffler",
                "year": 2025, "score": "-16", "total": "264",
                "title": None, "countryCode": "USA",
            }
        ],
    }
})

_write("Weather", {
    "weather": {
        "title": "Weather",
        "hourly": [
            {
                "title": "2 PM", "condition": "Sunny",
                "windDirection": "SW", "windSpeedMPH": "8", "windSpeedKPH": "13",
                "humidity": 40, "precipitation": "0%",
                "temperature": {"__typename": "StandardWeatherTemp", "tempF": 91, "tempC": 33},
            }
        ],
        "daily": [
            {
                "title": "Sat", "condition": "Partly Cloudy",
                "windDirection": "S", "windSpeedMPH": "10", "windSpeedKPH": "16",
                "humidity": 45, "precipitation": "10%",
                "temperature": {
                    "__typename": "RangeWeatherTemp",
                    "minTempF": 74, "minTempC": 23, "maxTempF": 93, "maxTempC": 34,
                },
            }
        ],
    }
})

_write("CourseStats", {
    "courseStats": {
        "tournamentId": "R2026027",
        "courses": [
            {
                "courseId": "513", "courseName": "TPC Southwind",
                "courseCode": "SW", "hostCourse": True,
                "roundHoleStats": [
                    {
                        "roundHeader": "R1", "roundNum": 1, "live": False,
                        "holeStats": [
                            {
                                "__typename": "CourseHoleStats",
                                "courseHoleNum": 1, "parValue": 4, "yards": 434,
                                "scoringAverage": "3.95", "scoringAverageDiff": "-0.05",
                                "eagles": 0, "birdies": 20, "pars": 40,
                                "bogeys": 9, "doubleBogey": 0, "rank": 12, "live": False,
                            }
                        ],
                    }
                ],
            }
        ],
    }
})

_write("CourseStatsOverview", {
    "courseStatsOverview": {
        "tourCode": "R", "year": 2026,
        "categories": [
            {
                "header": "Toughest Holes",
                "items": [
                    {
                        "displayName": "TPC Southwind #14",
                        "rank": 1,
                        "details": [
                            {"label": "Scoring Avg", "value": "4.35"},
                            {"label": "Par", "value": "4"},
                        ],
                    }
                ],
            }
        ],
    }
})

_write("SignatureStandings", {
    "signatureStandings": {
        "tournamentID": "R2026007",
        "infoTitle": "Aon Next 10",
        "official": {
            "title": "Official",
            "players": [
                {
                    "__typename": "SignaturePlayer",
                    "playerId": "52955", "displayName": "Ludvig Aberg",
                    "shortName": "L. Aberg", "countryName": "Sweden",
                    "countryFlag": "se", "started": True,
                    "projected": "8", "projectedPoints": "1200",
                    "movementAmount": "1", "movementDirection": "UP",
                },
                {"__typename": "SignatureInfoLine", "text": "cut line"},
            ],
        },
        "interim": {"players": []},
    }
})

_write("PriorityRankings", {
    "priorityRankings": {
        "tourCode": "R", "year": 2026, "displayYear": "2026",
        "throughText": "Wyndham Championship",
        "categories": [
            {
                "displayName": "Tournament Winners",
                "detail": "Winners from the past two seasons",
                "players": [
                    {"playerId": "46046", "displayName": "Scottie Scheffler"},
                ],
            }
        ],
    }
})

_write("odds_markets", {
    "availableMarkets": [
        {
            "id": 2574, "name": "Outright Winner", "book": "fanduel",
            "displayName": "To Win", "marketType": "ODDS_TO_WIN",
        },
        {
            "id": 2578, "name": "Matchup Props", "book": "fanduel",
            "displayName": "Matchups", "marketType": "MATCHUP",
        },
    ]
})

_write("player_odds", {
    "playerMarkets": [
        {
            "subMarketName": "Finish",
            "marketDisplayName": "Finishes",
            "marketType": "FINISH",
            "layoutType": "MAIN_TABLE",
            "oddsDataGroup": [
                {
                    "title": "Top 10 Finish (Incl. Ties)",
                    "odds": [{"odds": "+250", "label": "Yes"}],
                }
            ],
        }
    ]
})

_write("ScorecardStatsComparisonCategories", {
    "scorecardStatsComparison": {
        "tournamentId": "R2026475",
        "category": "SCORING",
        "categoryPills": [
            ["Scoring", "SCORING"],
            ["Driving", "DRIVING"],
        ],
    }
})

print(f"Wrote {len(list(OUT.glob('*.json')))} fixture files to {OUT}")
