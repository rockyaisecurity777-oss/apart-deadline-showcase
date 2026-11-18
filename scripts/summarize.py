"""Post-sprint helper (added 18 Nov 2026): roll results.csv up into the paper's Table 1.

Usage: python3 scripts/summarize.py [results.csv]
"""
import csv
import sys
from collections import Counter

LABELS = {"fixed": "Fixed offset", "first_fold": "Default fold", "round_trip": "Round trip"}


def table1(path):
    counts = Counter()
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            counts[row["method"], row["source_time_type"], row["result"]] += int(row["count"])
    out = {}
    for method in LABELS:
        cells = {}
        for kind in ("unique", "gap", "repeated"):
            total = sum(v for (m, k, _), v in counts.items() if m == method and k == kind)
            cells[kind] = (counts[method, kind, "error"], total)
        out[method] = cells
    return out


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "results.csv"
    t = table1(path)
    print(f"{'Method':<14}{'Wrong unique':>20}{'Wrong gap':>12}{'Wrong repeat':>14}{'Total wrong':>13}")
    for method, cells in t.items():
        fmt = lambda c: f"{c[0]:,} / {c[1]:,}"
        total = sum(c[0] for c in cells.values())
        print(f"{LABELS[method]:<14}{fmt(cells['unique']):>20}{fmt(cells['gap']):>12}"
              f"{fmt(cells['repeated']):>14}{total:>13,}")
    labels = sum(c[1] for c in t["fixed"].values())
    print(f"Labels per method: {labels:,}")


if __name__ == "__main__":
    main()
