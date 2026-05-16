"""Tests for the transport layer (`pgatourpy._api`)."""

from __future__ import annotations

import base64
import gzip
import json
import os

import pytest

from pgatourpy import _api
from pgatourpy._api import PgaTourError, _api_key, _is_verbose, decompress_payload


def test_api_key_default(monkeypatch):
    monkeypatch.delenv("PGA_API_KEY", raising=False)
    assert _api_key() == _api._DEFAULT_API_KEY


def test_api_key_env_override(monkeypatch):
    monkeypatch.setenv("PGA_API_KEY", "rotated-key-123")
    assert _api_key() == "rotated-key-123"


def test_api_key_empty_env_falls_back(monkeypatch):
    monkeypatch.setenv("PGA_API_KEY", "")
    assert _api_key() == _api._DEFAULT_API_KEY


@pytest.mark.parametrize("val,expected", [
    ("", False), ("0", False), ("false", False), ("no", False), ("off", False),
    ("FALSE", False), ("1", True), ("true", True), ("yes", True), ("anything", True),
])
def test_is_verbose(monkeypatch, val, expected):
    monkeypatch.setenv("PGATOUR_VERBOSE", val)
    assert _is_verbose() is expected


def test_decompress_roundtrip():
    original = {"hello": "world", "n": [1, 2, 3]}
    payload = base64.b64encode(gzip.compress(json.dumps(original).encode())).decode()
    assert decompress_payload(payload) == original


def test_decompress_rejects_empty():
    with pytest.raises(PgaTourError, match="non-empty"):
        decompress_payload("")


def test_decompress_rejects_non_string():
    with pytest.raises(PgaTourError, match="non-empty"):
        decompress_payload(None)  # type: ignore[arg-type]


def test_decompress_invalid_base64():
    with pytest.raises(PgaTourError, match="base64"):
        decompress_payload("@@@@@@@@@@@@@@@@@@@")


def test_decompress_valid_base64_not_gzip():
    payload = base64.b64encode(b"plaintext, not gzipped").decode()
    with pytest.raises(PgaTourError, match="gunzip"):
        decompress_payload(payload)


def test_decompress_valid_gzip_not_json():
    payload = base64.b64encode(gzip.compress(b"not-json")).decode()
    with pytest.raises(PgaTourError, match="parse"):
        decompress_payload(payload)
