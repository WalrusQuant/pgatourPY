"""Low-level API helpers for making requests to the PGA Tour API."""

from __future__ import annotations

import base64
import binascii
import gzip
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any

import httpx

GRAPHQL_URL = "https://orchestrator.pgatour.com/graphql"
REST_URL = "https://data-api.pgatour.com"
_DEFAULT_API_KEY = "da2-gsrx5bibzbb4njvhl7t37wqyl4"

USER_AGENT = "pgatourPY (https://github.com/WalrusQuant/pgatourPY)"

_RETRY_STATUS = {408, 429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_TIMEOUT_SECONDS = 30.0
_BACKOFF_BASE = 0.5

_QUERY_DIR = Path(__file__).parent / "graphql"
_QUERY_CACHE: dict[str, str] = {}

_MIN_INTERVAL = 0.1  # 10 req/s ceiling
_last_request_time: float = 0.0

logger = logging.getLogger("pgatourpy")


class PgaTourError(RuntimeError):
    """Raised when a PGA Tour API call fails in a way the caller may want to handle."""


def _api_key() -> str:
    """Return the API key, preferring the PGA_API_KEY env var if set."""
    return os.environ.get("PGA_API_KEY") or _DEFAULT_API_KEY


def _is_verbose() -> bool:
    """PGATOUR_VERBOSE truthy => log request envelopes at INFO level."""
    raw = os.environ.get("PGATOUR_VERBOSE", "").strip().lower()
    return raw not in ("", "0", "false", "no", "off")


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Accept": "application/graphql-response+json, application/json",
        "x-api-key": _api_key(),
        "x-pgat-platform": "web",
        "Origin": "https://www.pgatour.com",
        "Referer": "https://www.pgatour.com/",
        "User-Agent": USER_AGENT,
    }


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
    global _last_request_time
    now = time.monotonic()
    elapsed = now - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.monotonic()


def _request_with_retry(
    method: str,
    url: str,
    *,
    json_body: dict[str, Any] | None = None,
    context: str,
) -> httpx.Response:
    """Issue an HTTP request with bounded retries on transient failures."""
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        _throttle()
        try:
            resp = httpx.request(
                method,
                url,
                json=json_body,
                headers=_headers(),
                timeout=_TIMEOUT_SECONDS,
            )
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_exc = e
            logger.debug(
                "pgatourpy %s transport error on %s (attempt %d/%d): %s",
                context, url, attempt + 1, _MAX_RETRIES, e,
            )
            if attempt + 1 >= _MAX_RETRIES:
                raise PgaTourError(
                    f"transport error calling {context}: {e}"
                ) from e
            time.sleep(_BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 0.1))
            continue

        if resp.status_code in _RETRY_STATUS and attempt + 1 < _MAX_RETRIES:
            logger.debug(
                "pgatourpy %s got %d (attempt %d/%d), retrying",
                context, resp.status_code, attempt + 1, _MAX_RETRIES,
            )
            time.sleep(_BACKOFF_BASE * (2 ** attempt) + random.uniform(0, 0.1))
            continue

        return resp

    # Should be unreachable, but defend it.
    raise PgaTourError(
        f"exhausted retries calling {context}: {last_exc}"
    )


def _parse_json(resp: httpx.Response, context: str) -> Any:
    """Parse a JSON response body; raise a clear error if it isn't JSON."""
    try:
        return resp.json()
    except (ValueError, json.JSONDecodeError) as e:
        snippet = (resp.text or "")[:200].replace("\n", " ")
        raise PgaTourError(
            f"non-JSON response from {context} "
            f"(status={resp.status_code}): {snippet!r}"
        ) from e


def graphql_request(
    operation_name: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make a GraphQL request to the PGA Tour API."""
    query = _read_query(operation_name)
    payload = {
        "query": query,
        "variables": variables or {},
        "operationName": operation_name,
    }
    if _is_verbose():
        logger.info("pgatourpy graphql -> %s vars=%s", operation_name, variables)
    else:
        logger.debug("pgatourpy graphql -> %s vars=%s", operation_name, variables)

    context = f"GraphQL {operation_name}"
    resp = _request_with_retry(
        "POST", GRAPHQL_URL, json_body=payload, context=context,
    )

    if resp.status_code >= 400:
        snippet = (resp.text or "")[:200].replace("\n", " ")
        raise PgaTourError(
            f"{context} failed (status={resp.status_code}): {snippet!r}"
        )

    body = _parse_json(resp, context)

    if isinstance(body, dict) and body.get("errors"):
        msgs = "; ".join(
            e.get("message", "") for e in body["errors"] if isinstance(e, dict)
        )
        raise PgaTourError(f"PGA Tour GraphQL error ({operation_name}): {msgs}")

    return body.get("data", {}) if isinstance(body, dict) else {}


def rest_request(path: str) -> Any:
    """Make a REST GET request to the PGA Tour data API."""
    url = f"{REST_URL}/{path}"
    if _is_verbose():
        logger.info("pgatourpy rest -> %s", path)
    else:
        logger.debug("pgatourpy rest -> %s", path)

    context = f"REST {path}"
    resp = _request_with_retry("GET", url, context=context)

    if resp.status_code >= 400:
        snippet = (resp.text or "")[:200].replace("\n", " ")
        raise PgaTourError(
            f"{context} failed (status={resp.status_code}): {snippet!r}"
        )

    return _parse_json(resp, context)


def decompress_payload(payload: str) -> Any:
    """Decode a base64+gzip compressed payload from the API.

    Validates input and surfaces a clear error for each failure step
    (base64 decode, gunzip, JSON parse) instead of cryptic C-level
    messages.
    """
    if not isinstance(payload, str) or not payload:
        raise PgaTourError("decompress_payload: payload must be a non-empty string")
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as e:
        raise PgaTourError(f"failed to base64-decode payload: {e}") from e
    try:
        decompressed = gzip.decompress(raw)
    except (OSError, EOFError) as e:
        raise PgaTourError(f"failed to gunzip payload: {e}") from e
    try:
        return json.loads(decompressed)
    except json.JSONDecodeError as e:
        raise PgaTourError(f"failed to parse decompressed payload: {e}") from e
