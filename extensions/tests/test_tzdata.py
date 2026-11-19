"""Record and check the current IANA tzdata version against Table 1."""
from __future__ import annotations

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from extensions.benchmark import tzdata_version
from extensions.grid import load_paper_grid
from extensions.strategies import round_trip, score


class TzdataRobustness(unittest.TestCase):
    def test_tzdata_version_is_recorded(self):
        version = tzdata_version()
        self.assertTrue(version and version != "unknown", version)
        # This box, at the time of writing, ships 2026f. Do not fail if a
        # later image has a newer file; just require that we can read one.
        self.assertRegex(version, r"^\d{4}[a-z]$")
        print(f"tzdata version under test: {version}", flush=True)

    def test_table1_still_holds_on_this_tzdata(self):
        # Same check the paper reports: round trip has 0 errors on the grid;
        # default-fold uniqueness is checked via clock_evidence's own tests.
        silent = 0
        for _n, zone, wall, truth, _k in load_paper_grid():
            silent += score(round_trip(wall, zone), truth)[2]
        self.assertEqual(silent, 0)


if __name__ == "__main__":
    unittest.main()
