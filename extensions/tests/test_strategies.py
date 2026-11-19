"""Unit tests for every post-sprint resolution strategy."""
from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from zoneinfo import ZoneInfo

from extensions.rfc9557 import format_rfc9557, parse_rfc9557
from extensions.strategies import (
    ensemble,
    fail_closed,
    first_fold,
    offset_pinned,
    policy_explicit,
    round_trip,
    score,
    utc_normalize,
)
from clock_evidence import possible

UTC = timezone.utc
NY = ZoneInfo("America/New_York")
GAP = datetime(2026, 3, 8, 2, 30)
REPEAT = datetime(2026, 11, 1, 1, 30)
ORDINARY = datetime(2026, 7, 1, 12, 0)
ORDINARY_UTC = datetime(2026, 7, 1, 16, 0, tzinfo=UTC)
REPEAT_EARLY = datetime(2026, 11, 1, 5, 30, tzinfo=UTC)
REPEAT_LATE = datetime(2026, 11, 1, 6, 30, tzinfo=UTC)


class RoundTrip(unittest.TestCase):
    def test_ordinary(self):
        d = round_trip(ORDINARY, NY)
        self.assertFalse(d.flagged)
        self.assertEqual(d.instants, frozenset({ORDINARY_UTC}))

    def test_gap_empty(self):
        d = round_trip(GAP, NY)
        self.assertFalse(d.flagged)
        self.assertEqual(d.instants, frozenset())

    def test_repeat_both(self):
        d = round_trip(REPEAT, NY)
        self.assertFalse(d.flagged)
        self.assertEqual(d.instants, frozenset({REPEAT_EARLY, REPEAT_LATE}))


class FailClosed(unittest.TestCase):
    def test_ordinary_passes(self):
        d = fail_closed(ORDINARY, NY)
        self.assertFalse(d.flagged)
        self.assertEqual(d.instants, frozenset({ORDINARY_UTC}))

    def test_gap_flagged(self):
        d = fail_closed(GAP, NY)
        self.assertTrue(d.flagged)
        self.assertEqual(d.instants, frozenset())
        self.assertEqual(d.reason, "gap")

    def test_repeat_flagged(self):
        d = fail_closed(REPEAT, NY)
        self.assertTrue(d.flagged)
        self.assertEqual(d.instants, frozenset())
        self.assertEqual(d.reason, "repeat")

    def test_no_silent_error_on_examples(self):
        for wall, truth in (
            (ORDINARY, {ORDINARY_UTC}),
            (GAP, set()),
            (REPEAT, {REPEAT_EARLY, REPEAT_LATE}),
        ):
            _wrong, flagged, silent = score(fail_closed(wall, NY), truth)
            self.assertFalse(silent)
            if wall is ORDINARY:
                self.assertFalse(flagged)
            else:
                self.assertTrue(flagged)


class PolicyExplicit(unittest.TestCase):
    def test_earliest_repeat(self):
        d = policy_explicit(REPEAT, NY, on_repeat="earliest", on_gap="reject")
        self.assertFalse(d.flagged)
        self.assertEqual(d.instants, frozenset({REPEAT_EARLY}))

    def test_latest_repeat(self):
        d = policy_explicit(REPEAT, NY, on_repeat="latest", on_gap="reject")
        self.assertFalse(d.flagged)
        self.assertEqual(d.instants, frozenset({REPEAT_LATE}))

    def test_reject_repeat(self):
        d = policy_explicit(REPEAT, NY, on_repeat="reject", on_gap="reject")
        self.assertTrue(d.flagged)
        self.assertEqual(d.instants, frozenset())

    def test_reject_gap(self):
        d = policy_explicit(GAP, NY, on_repeat="earliest", on_gap="reject")
        self.assertTrue(d.flagged)
        self.assertEqual(d.instants, frozenset())

    def test_shift_forward_gap_lands_on_real_time(self):
        d = policy_explicit(GAP, NY, on_repeat="earliest", on_gap="shift_forward")
        self.assertFalse(d.flagged)
        self.assertEqual(len(d.instants), 1)
        instant = next(iter(d.instants))
        local = instant.astimezone(NY).replace(tzinfo=None)
        # 02:30 does not exist; a 1-hour shift lands at 03:30.
        self.assertEqual(local, datetime(2026, 3, 8, 3, 30))
        self.assertEqual(possible(local, NY), {instant})

    def test_ordinary_ignores_policy(self):
        for on_repeat in ("earliest", "latest", "reject"):
            for on_gap in ("shift_forward", "reject"):
                d = policy_explicit(ORDINARY, NY, on_repeat=on_repeat, on_gap=on_gap)
                self.assertEqual(d.instants, frozenset({ORDINARY_UTC}))
                self.assertFalse(d.flagged)


class OffsetPinned(unittest.TestCase):
    def test_ordinary_round_trips(self):
        d = offset_pinned(ORDINARY, NY)
        self.assertFalse(d.flagged)
        self.assertEqual(d.instants, frozenset({ORDINARY_UTC}))
        text = format_rfc9557(ORDINARY_UTC, NY)
        self.assertIn("[America/New_York]", text)
        self.assertEqual(parse_rfc9557(text), ORDINARY_UTC)

    def test_aoe_example(self):
        aoe = ZoneInfo("Etc/GMT+12")
        instant = datetime(2026, 11, 16, 11, 59, tzinfo=UTC)
        text = format_rfc9557(instant, aoe)
        self.assertEqual(text, "2026-11-15T23:59:00-12:00[Etc/GMT+12]")
        self.assertEqual(parse_rfc9557(text), instant)

    def test_wrong_offset_rejected(self):
        # EDT offset used in January (EST should be -05:00).
        with self.assertRaises(ValueError):
            parse_rfc9557("2026-01-15T12:00:00-04:00[America/New_York]")

    def test_gap_and_repeat_flagged(self):
        self.assertTrue(offset_pinned(GAP, NY).flagged)
        self.assertTrue(offset_pinned(REPEAT, NY).flagged)

    def test_malformed_rejected(self):
        with self.assertRaises(ValueError):
            parse_rfc9557("not-a-timestamp")


class UtcNormalize(unittest.TestCase):
    def test_ordinary_stored(self):
        d = utc_normalize(ORDINARY, NY)
        self.assertFalse(d.flagged)
        self.assertEqual(d.instants, frozenset({ORDINARY_UTC}))

    def test_gap_needs_confirmation(self):
        d = utc_normalize(GAP, NY)
        self.assertTrue(d.flagged)
        self.assertEqual(d.reason, "confirm_gap")

    def test_repeat_needs_confirmation(self):
        d = utc_normalize(REPEAT, NY)
        self.assertTrue(d.flagged)
        self.assertEqual(d.reason, "confirm_repeat")


class EnsembleExamples(unittest.TestCase):
    def test_ordinary_no_alarm(self):
        d = ensemble(ORDINARY, NY)
        self.assertFalse(d.flagged)
        self.assertEqual(d.instants, frozenset({ORDINARY_UTC}))

    def test_gap_alarm(self):
        d = ensemble(GAP, NY)
        self.assertTrue(d.flagged)

    def test_repeat_alarm(self):
        d = ensemble(REPEAT, NY)
        self.assertTrue(d.flagged)

    def test_first_fold_silently_wrong_on_gap(self):
        d = first_fold(GAP, NY)
        self.assertFalse(d.flagged)
        self.assertEqual(len(d.instants), 1)
        _w, _f, silent = score(d, set())
        self.assertTrue(silent)


if __name__ == "__main__":
    unittest.main()
