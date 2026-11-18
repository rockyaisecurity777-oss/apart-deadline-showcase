"""Post-sprint tests (added 18 Nov 2026). They test the unchanged sprint code; run with
`python3 -m unittest discover -s tests -v` (or `pytest`)."""
import csv
import io
import os
import sys
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import clock_evidence as ce  # noqa: E402
from summarize import table1  # noqa: E402

UTC = timezone.utc
NY = ZoneInfo("America/New_York")


class PossibleInstants(unittest.TestCase):
    def test_spring_forward_gap_has_no_instant(self):
        self.assertEqual(ce.possible(datetime(2026, 3, 8, 2, 30), NY), set())

    def test_fall_back_repeat_has_two_instants(self):
        self.assertEqual(ce.possible(datetime(2026, 11, 1, 1, 30), NY),
                         {datetime(2026, 11, 1, 5, 30, tzinfo=UTC),
                          datetime(2026, 11, 1, 6, 30, tzinfo=UTC)})

    def test_ordinary_time_has_one_instant(self):
        self.assertEqual(ce.possible(datetime(2026, 7, 1, 12, 0), NY),
                         {datetime(2026, 7, 1, 16, 0, tzinfo=UTC)})

    def test_lord_howe_half_hour_shift(self):
        lh = ZoneInfo("Australia/Lord_Howe")
        oracle = ce.oracle(lh)
        gaps = [w for w in self._labels() if w not in oracle]
        repeats = [w for w, s in oracle.items() if len(s) == 2]
        self.assertEqual(len(gaps), 1)
        self.assertEqual(len(repeats), 1)
        for w in gaps:
            self.assertEqual(ce.possible(w, lh), set())
        for w in repeats:
            self.assertEqual(ce.possible(w, lh), oracle[w])

    def test_aoe_sprint_deadline(self):
        aoe = datetime(2026, 11, 15, 23, 59, tzinfo=ZoneInfo("Etc/GMT+12"))
        self.assertEqual(aoe.astimezone(UTC), datetime(2026, 11, 16, 11, 59, tzinfo=UTC))
        kol = aoe.astimezone(ZoneInfo("Asia/Kolkata"))
        self.assertEqual((kol.day, kol.hour, kol.minute), (16, 17, 29))

    @staticmethod
    def _labels():
        from datetime import timedelta
        w = datetime(2026, 1, 1)
        while w.year == 2026:
            yield w
            w += timedelta(minutes=30)


class FullReplication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ce.evaluate()
        cls.output = buf.getvalue()

    def test_output_matches_committed_results(self):
        with open(os.path.join(ROOT, "results.csv"), newline="") as fh:
            expected = list(csv.reader(fh))
        self.assertEqual(list(csv.reader(io.StringIO(self.output))), expected)

    def test_every_zone_has_17520_labels_per_method(self):
        totals = {}
        for row in list(csv.DictReader(io.StringIO(self.output))):
            key = row["zone"], row["method"]
            totals[key] = totals.get(key, 0) + int(row["count"])
        self.assertEqual(len(totals), 8 * 3)
        self.assertTrue(all(v == 17520 for v in totals.values()))

    def test_table1_numbers(self):
        t = table1(os.path.join(ROOT, "results.csv"))
        self.assertEqual(t["fixed"], {"unique": (60466, 140138), "gap": (11, 11), "repeated": (11, 11)})
        self.assertEqual(t["first_fold"], {"unique": (0, 140138), "gap": (11, 11), "repeated": (11, 11)})
        self.assertEqual(t["round_trip"], {"unique": (0, 140138), "gap": (0, 11), "repeated": (0, 11)})


class OriginalArchive(unittest.TestCase):
    def test_root_files_identical_to_sprint_archive(self):
        import hashlib
        import zipfile
        with zipfile.ZipFile(os.path.join(ROOT, "original", "research-replication.zip")) as z:
            for name in ("clock_evidence.py", "results.csv"):
                with open(os.path.join(ROOT, name), "rb") as fh:
                    self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),
                                     hashlib.sha256(fh.read()).hexdigest(), name)


if __name__ == "__main__":
    unittest.main()
