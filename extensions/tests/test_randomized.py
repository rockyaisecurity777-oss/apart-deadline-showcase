"""Property-style check on random IANA zones, fixed seed, paper-style grid."""
from __future__ import annotations

import os
import random
import sys
import unittest
from zoneinfo import ZoneInfo, available_timezones

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from extensions.grid import ZONES, load_paper_grid
from extensions.strategies import ensemble, fail_closed, round_trip, score

SEED = 20261119
SAMPLE = 24


def _candidate_zones():
    names = []
    skip = set(ZONES)
    for name in sorted(available_timezones()):
        if name in skip:
            continue
        if name.startswith(("Etc/", "SystemV/", "posix/", "right/")):
            continue
        if name in {"Factory", "localtime", "Universal", "UTC"}:
            continue
        try:
            ZoneInfo(name)
        except Exception:
            continue
        names.append(name)
    return names


class RandomizedZones(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = random.Random(SEED)
        pool = _candidate_zones()
        cls.pool_size = len(pool)
        cls.zones = tuple(rng.sample(pool, SAMPLE)) if len(pool) >= SAMPLE else tuple(pool)
        cls.grid = load_paper_grid(cls.zones)
        cls.failures = []
        unique = amb = 0
        unique_alarms = missed = silent_rt = silent_fc = 0
        for name, zone, wall, truth, kind in cls.grid:
            rt = round_trip(wall, zone)
            fc = fail_closed(wall, zone)
            en = ensemble(wall, zone)
            if score(rt, truth)[2]:
                silent_rt += 1
                cls.failures.append(("round_trip_silent", name, wall, truth, rt))
            if score(fc, truth)[2]:
                silent_fc += 1
                cls.failures.append(("fail_closed_silent", name, wall, truth, fc))
            if kind == "unique":
                unique += 1
                if en.flagged:
                    unique_alarms += 1
                    cls.failures.append(("false_alarm", name, wall, truth, en))
            else:
                amb += 1
                if not en.flagged:
                    missed += 1
                    cls.failures.append(("missed_alarm", name, wall, truth, en))
        cls.stats = {
            "zones": len(cls.zones),
            "pool": cls.pool_size,
            "labels": len(cls.grid),
            "unique": unique,
            "ambiguous": amb,
            "silent_rt": silent_rt,
            "silent_fc": silent_fc,
            "unique_alarms": unique_alarms,
            "missed": missed,
        }
        print(
            "randomized grid: "
            f"seed={SEED}, sampled {cls.stats['zones']} of {cls.stats['pool']} "
            f"eligible zones, {cls.stats['labels']} labels "
            f"({cls.stats['unique']} unique, {cls.stats['ambiguous']} gap/repeat)",
            flush=True,
        )
        if cls.failures:
            print(f"failures ({len(cls.failures)}): {cls.failures[:8]!r}", flush=True)

    def test_sample_size(self):
        self.assertEqual(self.stats["zones"], SAMPLE)
        self.assertEqual(self.stats["labels"], SAMPLE * 17520)

    def test_round_trip_silent_errors(self):
        self.assertEqual(self.stats["silent_rt"], 0)

    def test_fail_closed_silent_errors(self):
        self.assertEqual(self.stats["silent_fc"], 0)

    def test_ensemble_false_alarms(self):
        self.assertEqual(self.stats["unique_alarms"], 0)

    def test_ensemble_missed_ambiguous(self):
        # Honest: if a sampled zone has a gap/repeat on this half-hour grid
        # and the ensemble misses it, this fails and the list is printed.
        self.assertEqual(self.stats["missed"], 0)

    def test_report_zone_list(self):
        # Always print the sampled zones so RESULTS.md can cite them.
        print("sampled zones:", ", ".join(self.zones), flush=True)
        self.assertTrue(self.zones)


if __name__ == "__main__":
    unittest.main()
