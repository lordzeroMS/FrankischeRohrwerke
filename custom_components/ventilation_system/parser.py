from __future__ import annotations

import re
from typing import Any

NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


def value_as_text(value: Any) -> str | None:
    """Normalize structured XML values to stripped text."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        for item in value:
            text = value_as_text(item)
            if text:
                return text
        return None
    if isinstance(value, dict):
        text = value.get("#text") or value.get("text")
        if text:
            stripped = str(text).strip()
            return stripped or None
        for nested in value.values():
            text = value_as_text(nested)
            if text:
                return text
        return None
    stripped = str(value).strip()
    return stripped or None


def extract_number(value: Any) -> str | None:
    """Return the numeric portion of a structured value."""
    text = value_as_text(value)
    if not text:
        return None
    match = NUMBER_RE.search(text)
    if not match:
        return None
    return match.group(0)


def as_float(value: Any) -> float | None:
    """Convert ventilation XML values to floats."""
    numeric = extract_number(value)
    if numeric is None:
        return None
    try:
        return float(numeric.replace(",", "."))
    except ValueError:
        return None


def as_int(value: Any) -> int | None:
    """Convert ventilation XML values to ints."""
    numeric = extract_number(value)
    if numeric is None:
        return None
    try:
        return int(float(numeric.replace(",", ".")))
    except ValueError:
        return None


def stage_value(value: Any) -> int | None:
    """Extract the stage number from text like 'Stufe2 Abwesend'."""
    text = value_as_text(value)
    if not text:
        return None
    lower = text.lower()
    if "stufe" in lower:
        try:
            return int(lower.split("stufe")[1].split()[0])
        except (IndexError, ValueError):
            return None
    return as_int(text)
