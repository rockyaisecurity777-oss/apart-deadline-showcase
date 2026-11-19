"""Benchmark the post-sprint strategies on the paper's 8-zone 2026 grid."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from extensions.grid import ZONES, iter_paper_labels, kind_of, load_paper_grid, oracle
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

STRATEGIES = (
    ("round_trip", lambda w, z: round_trip(w, z)),
    ("fail_closed", lambda w, z: fail_closed(w, z)),
    (
        "policy_earliest_shift",
        lambda w, z: policy_explicit(w, z, on_repeat="earliest", on_gap="shift_forward"),
    ),
    (
        "policy_latest_shift",
        lambda w, z: policy_explicit(w, z, on_repeat="latest", on_gap="shift_forward"),
    ),
    (
        "policy_earliest_reject",
        lambda w, z: policy_explicit(w, z, on_repeat="earliest", on_gap="reject"),
    ),
    (
        "policy_latest_reject",
        lambda w, z: policy_explicit(w, z, on_repeat="latest", on_gap="reject"),
    ),
    (
        "policy_reject_reject",
        lambda w, z: policy_explicit(w, z, on_repeat="reject", on_gap="reject"),
    ),
    ("offset_pinned", lambda w, z: offset_pinned(w, z)),
    ("utc_normalize", lambda w, z: utc_normalize(w, z)),
    ("ensemble", lambda w, z: ensemble(w, z)),
    # Paper baseline, for comparison only.
    ("first_fold_baseline", lambda w, z: first_fold(w, z)),
)


def tzdata_version():
    path = "/usr/share/zoneinfo/tzdata.zi"
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("# version"):
                    return line.strip().split()[-1]
    return "unknown"


def run_one(name, fn, grid):
    totals = Counter()
    by_kind = defaultdict(Counter)
    t0 = time.perf_counter()
    for _zname, zone, wall, truth, kind in grid:
        decision = fn(wall, zone)
        wrong, flagged, silent = score(decision, truth)
        totals["labels"] += 1
        totals["wrong"] += wrong
        totals["flagged"] += flagged
        totals["silent_error"] += silent
        by_kind[kind]["labels"] += 1
        by_kind[kind]["wrong"] += wrong
        by_kind[kind]["flagged"] += flagged
        by_kind[kind]["silent_error"] += silent
    elapsed = time.perf_counter() - t0
    return {
        "name": name,
        "labels": totals["labels"],
        "wrong": totals["wrong"],
        "flagged": totals["flagged"],
        "silent_error": totals["silent_error"],
        "runtime_sec": round(elapsed, 4),
        "by_kind": {k: dict(v) for k, v in by_kind.items()},
    }


def run_benchmark():
    grid = load_paper_grid()
    results = [run_one(name, fn, grid) for name, fn in STRATEGIES]
    # Ensemble catch-rate on the paper's 22 / 140,138 split.
    unique = gap = repeated = 0
    unique_alarm = gap_alarm = repeated_alarm = 0
    for _n, zone, wall, truth, kind in grid:
        alarmed = ensemble(wall, zone).flagged
        if kind == "unique":
            unique += 1
            unique_alarm += alarmed
        elif kind == "gap":
            gap += 1
            gap_alarm += alarmed
        else:
            repeated += 1
            repeated_alarm += alarmed
    summary = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "python": sys.version.split()[0],
        "tzdata": tzdata_version(),
        "zones": list(ZONES),
        "labels": len(grid),
        "unique": unique,
        "gap": gap,
        "repeated": repeated,
        "ensemble_alarms": {
            "unique": unique_alarm,
            "gap": gap_alarm,
            "repeated": repeated_alarm,
            "ambiguous_caught": gap_alarm + repeated_alarm,
            "ambiguous_total": gap + repeated,
            "unique_false_alarms": unique_alarm,
        },
        "strategies": results,
    }
    return summary


def as_table(summary):
    lines = [
        "Strategy | Wrong (set ≠ oracle) | Flagged | Silent errors | Runtime (s)",
        "---|---:|---:|---:|---:",
    ]
    for row in summary["strategies"]:
        lines.append(
            f"{row['name']} | {row['wrong']:,} | {row['flagged']:,} | "
            f"{row['silent_error']:,} | {row['runtime_sec']:.4f}"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", metavar="PATH", help="write raw results JSON")
    args = parser.parse_args()
    summary = run_benchmark()
    print(f"Python {summary['python']}, tzdata {summary['tzdata']}")
    print(
        f"Grid: {summary['labels']:,} labels, {summary['unique']:,} unique, "
        f"{summary['gap']} gap, {summary['repeated']} repeat"
    )
    print()
    print(as_table(summary))
    ens = summary["ensemble_alarms"]
    print()
    print(
        "Ensemble: caught "
        f"{ens['ambiguous_caught']}/{ens['ambiguous_total']} ambiguous labels; "
        f"false alarms on unique labels: {ens['unique_false_alarms']}"
    )
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
            fh.write("\n")
        print(f"Wrote {args.json}")


if __name__ == "__main__":
    main()
