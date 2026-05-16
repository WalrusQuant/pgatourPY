"""Parsing utilities for pgatourPY."""

from __future__ import annotations

import re
from collections.abc import Sequence

_CAMEL_BOUNDARY = re.compile(r"([a-z0-9])([A-Z])")
_NON_ALNUM_RUN = re.compile(r"[^a-z0-9]+")


def _snake(label: str) -> str:
    """Convert a label to snake_case.

    Handles camelCase boundaries and replaces runs of non-alphanumeric
    characters with a single underscore. Always lowercased; leading and
    trailing underscores are stripped.
    """
    if label is None:
        return ""
    s = _CAMEL_BOUNDARY.sub(r"\1_\2", str(label)).lower()
    s = _NON_ALNUM_RUN.sub("_", s).strip("_")
    return s


def make_unique_snake(labels: Sequence[str]) -> list[str]:
    """Convert labels to snake_case and dedupe collisions.

    The PGA Tour API returns free-form display strings as column labels
    (e.g. "To Par", "Avg. Distance"). The same label can appear more than
    once in a single response (FedEx vs. World "Rank"). We snake-case
    every label and disambiguate duplicates by appending `_1`, `_2`, …

    Empty / falsy snake_case results fall back to ``col_<index>``.
    """
    out: list[str] = []
    seen: dict[str, int] = {}
    for i, raw in enumerate(labels):
        base = _snake(raw) or f"col_{i}"
        count = seen.get(base, 0)
        if count == 0:
            out.append(base)
        else:
            out.append(f"{base}_{count}")
        seen[base] = count + 1
    return out
