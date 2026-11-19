# Post-sprint extensions (added 19 Nov 2026)

> **Showcase deck (10 slides, PDF):** [Showcase-deck.pdf](Showcase-deck.pdf). It is a visual summary of the method and all benchmark results. Added 19 Nov 2026, after the sprint; it is not part of the judged submission.

**This folder was added on 19 November 2026, after the Apart Research AI x Epistemics Research Sprint. It is not part of the judged submission.**

The judged experiment remains the unchanged files at the repository root: `clock_evidence.py`, `results.csv`, and `original/research-replication.zip`. Those files were not modified. Judges should still treat the 14 November report and that archive as the submission.

These extensions ask a follow-on question: if a system has to *resolve* a local wall-clock deadline to an instant, which policies avoid the silent errors the paper measured, and can more than one method be combined as a safety check?

## What is here

- `grid.py` — walks the paper's 2026 half-hour, eight-zone grid by importing `clock_evidence.oracle` and `clock_evidence.possible`. It does not edit the sprint code.
- `strategies.py` — the alternative resolvers (round trip, fail-closed, explicit earliest/latest/reject and shift-forward/reject policies, RFC 9557 offset-pinned storage, UTC normalisation with a confirmation flag, and a consensus ensemble).
- `rfc9557.py` — a small formatter/parser for timestamps such as `2026-11-15T23:59:00-12:00[Etc/GMT+12]`.
- `benchmark.py` — times and scores every strategy on the paper grid.
- `RESULTS.md` — comparison table from a real run, and a short “which to use when” note.
- `ARCHITECTURE.md` — a sketch of a deadline-resolution service.
- `tests/` — unit tests for each strategy, a full-grid ensemble check, a tzdata-version check, and a fixed-seed randomised test on other IANA zones.

Standard library only, Python 3.9 or later, with IANA time-zone data.

## How to run

From the repository root:

```
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s extensions/tests -v
python3 -m extensions.benchmark
```

The first command is the original nine post-sprint tests of the unchanged sprint code. The second is this folder. The benchmark reprints the comparison table.
