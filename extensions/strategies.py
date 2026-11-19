"""Alternative deadline-resolution strategies. Post-sprint, 19 Nov 2026.

Each strategy takes a naive local wall time and a ZoneInfo and returns a
Decision: a set of UTC instants plus whether the method flagged the input
instead of silently committing to an answer.
"""
from __future__ import annotations

from dataclasses import dataclass

from .grid import UTC, possible
from .rfc9557 import format_rfc9557, parse_rfc9557


@dataclass(frozen=True)
class Decision:
    instants: frozenset
    flagged: bool
    reason: str = ""


def first_fold(wall, zone):
    """Python default: attach the zone and convert once with fold=0."""
    instant = wall.replace(tzinfo=zone, fold=0).astimezone(UTC)
    return Decision(frozenset({instant}), False, "first_fold")


def round_trip(wall, zone):
    """The paper's method: keep only instants that convert back to the wall."""
    return Decision(frozenset(possible(wall, zone)), False, "round_trip")


def fail_closed(wall, zone):
    """Flag and refuse to guess when the wall time is a gap or a repeat."""
    found = possible(wall, zone)
    if len(found) == 1:
        return Decision(frozenset(found), False, "unique")
    if len(found) == 0:
        return Decision(frozenset(), True, "gap")
    return Decision(frozenset(), True, "repeat")


def _shift_forward(wall, zone):
    """RFC/java.time-style gap repair: move the local time later by the gap.

    In a gap, fold=0 and fold=1 are both imaginary and are separated by the
    length of the gap (PEP 495). Adding that length to the wall lands on the
    first real local time after the transition. Then round-trip it.
    """
    a = wall.replace(tzinfo=zone, fold=0).astimezone(UTC)
    b = wall.replace(tzinfo=zone, fold=1).astimezone(UTC)
    delta = abs(a - b)
    if delta.total_seconds() == 0:
        return possible(wall, zone)
    return possible(wall + delta, zone)


def policy_explicit(wall, zone, on_repeat="reject", on_gap="reject"):
    """Explicit policy for repeats (earliest / latest / reject) and gaps
    (shift_forward / reject). Silent picks are not flagged; rejects are.
    """
    found = possible(wall, zone)
    if len(found) == 1:
        return Decision(frozenset(found), False, "unique")
    if len(found) == 0:
        if on_gap == "reject":
            return Decision(frozenset(), True, "gap_reject")
        if on_gap == "shift_forward":
            shifted = _shift_forward(wall, zone)
            return Decision(frozenset(shifted), False, "gap_shift_forward")
        raise ValueError(f"unknown on_gap policy: {on_gap}")
    if on_repeat == "reject":
        return Decision(frozenset(), True, "repeat_reject")
    if on_repeat == "earliest":
        return Decision(frozenset({min(found)}), False, "repeat_earliest")
    if on_repeat == "latest":
        return Decision(frozenset({max(found)}), False, "repeat_latest")
    raise ValueError(f"unknown on_repeat policy: {on_repeat}")


def offset_pinned(wall, zone):
    """If the zone determines a single offset, store RFC 9557 and re-parse it.

    On a gap there is no valid offset to pin. On a repeat the wall time alone
    does not choose an offset. Both are flagged. This measures what a stored
    offset+zone representation would buy on this grid, without inventing an
    offset the source did not supply.
    """
    found = possible(wall, zone)
    if len(found) != 1:
        reason = "gap_no_offset" if len(found) == 0 else "repeat_needs_offset"
        return Decision(frozenset(), True, reason)
    instant = next(iter(found))
    text = format_rfc9557(instant, zone)
    parsed = parse_rfc9557(text)
    if parsed != instant:
        return Decision(frozenset({parsed}), False, "pin_mismatch")
    return Decision(frozenset({parsed}), False, "pinned")


def utc_normalize(wall, zone):
    """Convert to UTC at entry. Ambiguous or nonexistent walls need a human
    to confirm (or correct) before anything is stored. Confirmation is
    simulated as a flag; this method does not invent an instant.
    """
    found = possible(wall, zone)
    if len(found) == 1:
        return Decision(frozenset(found), False, "stored_utc")
    if len(found) == 0:
        return Decision(frozenset(), True, "confirm_gap")
    return Decision(frozenset(), True, "confirm_repeat")


# Methods whose committed instant sets agree on unique labels and diverge
# on gaps or repeats. first_fold is the paper's default-fold baseline.
ENSEMBLE_MEMBERS = (
    "round_trip",
    "first_fold",
    "earliest_reject",
    "latest_reject",
    "fail_closed",
)


def _named(name, wall, zone):
    if name == "round_trip":
        return round_trip(wall, zone)
    if name == "first_fold":
        return first_fold(wall, zone)
    if name == "fail_closed":
        return fail_closed(wall, zone)
    if name == "earliest_reject":
        return policy_explicit(wall, zone, on_repeat="earliest", on_gap="reject")
    if name == "latest_reject":
        return policy_explicit(wall, zone, on_repeat="latest", on_gap="reject")
    raise KeyError(name)


def ensemble(wall, zone, members=ENSEMBLE_MEMBERS):
    """Flag a safety alarm when member methods do not return the same set.

    The Decision.instants are the paper round-trip set (the exact set of
    supported instants). flagged means at least two members disagreed.
    """
    sets = []
    for name in members:
        sets.append(_named(name, wall, zone).instants)
    disagree = len(set(sets)) > 1
    truthish = frozenset(possible(wall, zone))
    return Decision(truthish, disagree, "disagreement" if disagree else "consensus")


def score(decision, truth):
    """Return (wrong, flagged, silent_error) as 0/1 booleans-as-ints.

    wrong: returned set != oracle set.
    flagged: the method refused to silently commit.
    silent_error: wrong and not flagged (the operational failure).
    """
    wrong = decision.instants != frozenset(truth)
    flagged = bool(decision.flagged)
    silent_error = wrong and not flagged
    return wrong, flagged, silent_error
