"""Walk the paper's 2026 half-hour grid by importing clock_evidence, not by
editing it.

The label iterator is the same loop as clock_evidence.evaluate: start at
2026-01-01 00:00, step 30 minutes, stop when the year rolls over. Ground
truth comes from clock_evidence.oracle.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import clock_evidence as ce  # noqa: E402

ZONES = ce.ZONES
UTC = ce.UTC
possible = ce.possible
oracle = ce.oracle


def iter_paper_labels():
    """Every half-hour local label in 2026 (48 × 365 = 17,520)."""
    wall = datetime(2026, 1, 1)
    while wall.year == 2026:
        yield wall
        wall += timedelta(minutes=30)


def kind_of(truth):
    return ("gap", "unique", "repeated")[len(truth)]


def load_paper_grid(zone_names=None):
    """List of (zone_name, ZoneInfo, wall, truth_set, kind)."""
    from zoneinfo import ZoneInfo

    names = tuple(zone_names) if zone_names is not None else ZONES
    rows = []
    for name in names:
        zone = ZoneInfo(name)
        reference = oracle(zone)
        for wall in iter_paper_labels():
            truth = reference.get(wall, set())
            rows.append((name, zone, wall, truth, kind_of(truth)))
    return rows
