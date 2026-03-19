"""Low-level API helpers for making requests to the PGA Tour API."""

from __future__ import annotations

import base64
import gzip
import json
import time
from pathlib import Path
from typing import Any

import httpx

GRAPHQL_URL = "https://orchestrator.pgatour.com/graphql"
REST_URL = "https://data-api.pgatour.com"
API_KEY = "da2-gsrx5bibzbb4njvhl7t37wqyl4"

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/graphql-response+json, application/json",
    "x-api-key": API_KEY,
    "x-pgat-platform": "web",
    "Origin": "https://www.pgatour.com",
    "Referer": "https://www.pgatour.com/",
}

USER_AGENT = "pgatourPY (https://github.com/WalrusQuant/pgatourPY)"

_QUERY_DIR = Path(__file__).parent / "graphql"
_QUERY_CACHE: dict[str, str] = {}

# Simple rate limiter: minimum seconds between requests
_MIN_INTERVAL = 0.1  # 10 req/s
_last_request_time: float = 0.0


def _read_query(operation_name: str) -> str:
    """Read a GraphQL query from the graphql/ directory, with caching."""
    if operation_name in _QUERY_CACHE:
        return _QUERY_CACHE[operation_name]
    path = _QUERY_DIR / f"{operation_name}.graphql"
    if not path.exists():
        raise FileNotFoundError(f"GraphQL query not found: {path}")
    query = path.read_text()
    _QUERY_CACHE[operation_name] = query
    return query


def _throttle() -> None:
    """Enforce rate limiting."""
    global _last_request_time
    now = time.monotonic()
    elapsed = now - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


def graphql_request(
    operation_name: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make a GraphQL request to the PGA Tour API."""
    _throttle()
    query = _read_query(operation_name)
    payload = {
        "query": query,
        "variables": variables or {},
        "operationName": operation_name,
    }
    resp = httpx.post(
        GRAPHQL_URL,
        json=payload,
        headers={**HEADERS, "User-Agent": USER_AGENT},
        timeout=30.0,
    )
    resp.raise_for_status()
    body = resp.json()

    if "errors" in body and body["errors"]:
        msgs = "; ".join(e.get("message", "") for e in body["errors"])
        raise RuntimeError(f"PGA Tour GraphQL error ({operation_name}): {msgs}")

    return body.get("data", {})


def rest_request(path: str) -> Any:
    """Make a REST GET request to the PGA Tour data API."""
    _throttle()
    resp = httpx.get(
        f"{REST_URL}/{path}",
        headers={"User-Agent": USER_AGENT},
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json()


def decompress_payload(payload: str) -> Any:
    """Decode a base64+gzip compressed payload from the API."""
    raw = base64.b64decode(payload)
    decompressed = gzip.decompress(raw)
    return json.loads(decompressed)
