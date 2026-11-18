#!/usr/bin/env sh
# One-command reproduction (post-sprint wrapper, added 18 Nov 2026).
set -eu
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
"$PY" --version
"$PY" -c "import zoneinfo,sys; print('tz search path:', zoneinfo.TZPATH)"
"$PY" clock_evidence.py > rerun.csv
if cmp -s results.csv rerun.csv; then echo "MATCH: rerun.csv is byte-identical to results.csv"; else echo "DIFFERENT: see diff results.csv rerun.csv"; exit 1; fi
"$PY" scripts/summarize.py rerun.csv
