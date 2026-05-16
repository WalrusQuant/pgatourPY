"""Tests for the snake_case/dedupe header helper."""

from pgatourpy._parse import make_unique_snake


def test_basic_snake_case():
    out = make_unique_snake(["First Name", "Last Name", "Avg. Distance"])
    assert out == ["first_name", "last_name", "avg_distance"]


def test_camel_case_boundaries():
    assert make_unique_snake(["roundStatusDisplay"]) == ["round_status_display"]
    assert make_unique_snake(["totalSort"]) == ["total_sort"]


def test_dedupe_collisions():
    out = make_unique_snake(["Rank", "Avg.", "Rank", "Rank"])
    assert out == ["rank", "avg", "rank_1", "rank_2"]


def test_punctuation_runs_collapse():
    out = make_unique_snake(["To Par!", "to-par"])
    assert out == ["to_par", "to_par_1"]


def test_empty_label_fallback():
    out = make_unique_snake(["", None, "Real"])
    assert out == ["col_0", "col_1", "real"]
