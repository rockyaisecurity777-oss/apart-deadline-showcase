"""Full-grid checks for the ensemble and the paper reference method."""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from extensions.grid import load_paper_grid
from extensions.strategies import (
    ensemble,
    fail_closed,
    offset_pinned,
    round_trip,
    score,
    utc_normalize,
)


class PaperGrid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.grid = load_paper_grid()
        cls.unique = [row for row in cls.grid if row[4] == "unique"]
        cls.ambiguous = [row for row in cls.grid if row[4] != "unique"]

    def test_grid_counts_match_the_paper(self):
        self.assertEqual(len(self.grid), 140160)
        self.assertEqual(len(self.unique), 140138)
        self.assertEqual(len(self.ambiguous), 22)
        gaps = sum(1 for row in self.grid if row[4] == "gap")
        repeats = sum(1 for row in self.grid if row[4] == "repeated")
        self.assertEqual(gaps, 11)
        self.assertEqual(repeats, 11)

    def test_round_trip_has_zero_errors(self):
        silent = 0
        for _n, zone, wall, truth, _k in self.grid:
            silent += score(round_trip(wall, zone), truth)[2]
        self.assertEqual(silent, 0)

    def test_ensemble_catches_every_ambiguous_label(self):
        missed = 0
        for _n, zone, wall, _truth, _k in self.ambiguous:
            if not ensemble(wall, zone).flagged:
                missed += 1
        self.assertEqual(missed, 0)

    def test_ensemble_has_zero_false_alarms_on_unique_labels(self):
        alarms = 0
        for _n, zone, wall, _truth, _k in self.unique:
            if ensemble(wall, zone).flagged:
                alarms += 1
        self.assertEqual(alarms, 0)

    def test_fail_closed_and_utc_normalize_flag_exactly_the_22(self):
        for fn in (fail_closed, utc_normalize, offset_pinned):
            flagged_unique = flagged_amb = silent = 0
            for _n, zone, wall, truth, kind in self.grid:
                d = fn(wall, zone)
                silent += score(d, truth)[2]
                if d.flagged:
                    if kind == "unique":
                        flagged_unique += 1
                    else:
                        flagged_amb += 1
            self.assertEqual(flagged_unique, 0, fn.__name__)
            self.assertEqual(flagged_amb, 22, fn.__name__)
            self.assertEqual(silent, 0, fn.__name__)


if __name__ == "__main__":
    unittest.main()
