"""Tests for internal utilities and data."""

from datetime import datetime, timezone

from pgatourpy._api import decompress_payload
from pgatourpy.client import _epoch_ms_to_datetime, _safe_get, _validate_tour
from pgatourpy.stat_ids import STAT_IDS

import pytest


def test_validate_tour_accepts_valid():
    _validate_tour("R")
    _validate_tour("S")
    _validate_tour("H")


def test_validate_tour_rejects_invalid():
    with pytest.raises(ValueError):
        _validate_tour("X")
    with pytest.raises(ValueError):
        _validate_tour("pga")


def test_safe_get():
    d = {"a": {"b": {"c": 42}}}
    assert _safe_get(d, "a", "b", "c") == 42
    assert _safe_get(d, "a", "b") == {"c": 42}
    assert _safe_get(d, "a", "z") is None
    assert _safe_get(d, "missing") is None
    assert _safe_get(d, "missing", default="fallback") == "fallback"


def test_epoch_ms_to_datetime():
    # 2026-03-19 12:00:00 UTC
    dt = _epoch_ms_to_datetime(1773928800000)
    assert isinstance(dt, datetime)
    assert dt.tzinfo == timezone.utc
    assert dt.year == 2026

    assert _epoch_ms_to_datetime(None) is None


def test_stat_ids_loaded():
    assert len(STAT_IDS) > 200
    assert list(STAT_IDS.columns) == [
        "stat_id", "stat_name", "category", "subcategory"
    ]
    assert "02675" in STAT_IDS["stat_id"].values


def test_decompress_roundtrip():
    import base64
    import gzip
    import json

    original = {"test": "data", "number": 42}
    compressed = base64.b64encode(
        gzip.compress(json.dumps(original).encode())
    ).decode()
    result = decompress_payload(compressed)
    assert result == original
