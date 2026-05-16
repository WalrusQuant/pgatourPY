"""Shared pytest fixtures for pgatourPY.

The transport layer (`pgatourpy._api.graphql_request` and
`pgatourpy._api.rest_request`) is mocked so tests run fully offline.
Synthetic fixtures live in `tests/fixtures/<name>.json`.
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture by name (without extension)."""
    path = FIXTURE_DIR / f"{name}.json"
    return json.loads(path.read_text())


def compress_payload(obj) -> str:
    """Encode an object as the API does for *Compressed operations."""
    raw = json.dumps(obj).encode()
    return base64.b64encode(gzip.compress(raw)).decode()


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURE_DIR


@pytest.fixture
def mock_graphql(monkeypatch):
    """Returns a setter that patches graphql_request to return a fixture.

    Usage::

        def test_x(mock_graphql):
            mock_graphql({"foo": "bar"})  # static return
            mock_graphql(by_op={"StatDetails": {...}})  # by operation name
    """
    def _setter(value=None, *, by_op=None):
        if by_op is not None:
            def _impl(operation_name, variables=None):
                if operation_name not in by_op:
                    raise KeyError(
                        f"no mock fixture for graphql op {operation_name!r}"
                    )
                return by_op[operation_name]
            monkeypatch.setattr(
                "pgatourpy.client.graphql_request", _impl,
            )
        else:
            monkeypatch.setattr(
                "pgatourpy.client.graphql_request",
                lambda operation_name, variables=None: value,
            )
    return _setter


@pytest.fixture
def mock_rest(monkeypatch):
    """Returns a setter that patches rest_request to return a fixture.

    Usage::

        def test_x(mock_rest):
            mock_rest({"foo": "bar"})  # static return
            mock_rest(by_path={"player/list/R": {...}})  # exact path match
    """
    def _setter(value=None, *, by_path=None):
        if by_path is not None:
            def _impl(path):
                if path not in by_path:
                    raise KeyError(f"no mock fixture for rest path {path!r}")
                return by_path[path]
            monkeypatch.setattr(
                "pgatourpy.client.rest_request", _impl,
            )
        else:
            monkeypatch.setattr(
                "pgatourpy.client.rest_request",
                lambda path: value,
            )
    return _setter
