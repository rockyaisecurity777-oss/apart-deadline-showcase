"""Minimal RFC 9557 / ISO 8601-1 offset+zone formatter and parser.

Example: 2026-11-15T23:59:00-12:00[Etc/GMT+12]

Standard library only. Used to show that a stored offset plus a zone name
round-trips to one instant when the offset is valid for that zone.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc

_PATTERN = re.compile(
    r"^(?P<local>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    r"(?P<off>[+-]\d{2}:\d{2})"
    r"\[(?P<zone>[A-Za-z0-9_+\-/]+)\]$"
)


def _format_offset(delta):
    total = int(delta.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hours, rem = divmod(total, 3600)
    minutes = rem // 60
    return f"{sign}{hours:02d}:{minutes:02d}"


def format_rfc9557(instant, zone):
    """Format a timezone-aware UTC (or other) instant in zone as RFC 9557."""
    if instant.tzinfo is None:
        raise ValueError("instant must be timezone-aware")
    aware = instant.astimezone(zone)
    key = getattr(zone, "key", None) or str(zone)
    return f"{aware.strftime('%Y-%m-%dT%H:%M:%S')}{_format_offset(aware.utcoffset())}[{key}]"


def parse_rfc9557(text):
    """Parse an RFC 9557 string and check that the offset matches the zone.

    Returns the UTC instant. Raises ValueError if the string is malformed or
    the offset is not the zone's offset at that instant (ambiguous or invalid).
    """
    match = _PATTERN.match(text)
    if not match:
        raise ValueError(f"not an RFC 9557 offset+zone timestamp: {text!r}")
    local = datetime.fromisoformat(match.group("local"))
    off_raw = match.group("off")
    sign = 1 if off_raw[0] == "+" else -1
    hours = int(off_raw[1:3])
    minutes = int(off_raw[4:6])
    declared = timedelta(hours=sign * hours, minutes=sign * minutes)
    zone = ZoneInfo(match.group("zone"))
    instant = (local - declared).replace(tzinfo=UTC)
    actual = instant.astimezone(zone)
    if actual.utcoffset() != declared:
        raise ValueError(
            f"offset {off_raw} does not match {match.group('zone')} at {text}"
        )
    if actual.replace(tzinfo=None) != local:
        raise ValueError(f"local time mismatch when applying zone in {text}")
    return instant
