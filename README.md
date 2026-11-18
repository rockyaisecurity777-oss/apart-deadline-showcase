# When a deadline has two answers

**Companion replication material** for the research report *"When a deadline has two answers"* by Ravi Kiran BR (JAMES AI Solutions).
It was submitted to Apart Research's **AI x Epistemics Research Sprint** (13–15 Nov 2026) in **Track 2: Trust Infrastructure**.

- Official project page: https://apartresearch.com/sprints/projects/when-a-deadline-has-two-answers-5jd93sdzzv
- Report PDF (as submitted, 4 pages): https://pys8vc40ox3z7qxp.public.blob.vercel-storage.com/submissions/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15/deadline-evidence-8CjTCaxwBr7yJZ2Gsx1gEoRfUqyTkn.pdf

> **Status:** The report was submitted on 16 Nov 2026 at 11:08 IST (05:38 UTC), before the 15 Nov 23:59 AoE deadline, and Apart sent a receipt.
> The experiment code and `results.csv` in this repo are the **unchanged sprint-time files** from `original/research-replication.zip`, created 14 Nov 2026.
> Everything else (this README, tests, `scripts/`, licence) was added **after the sprint**, on 18 Nov 2026, to package that material. It adds no new findings and does not change the submitted report.

## The problem
Imagine a notice that says *"1 November 2026, 01:30, New York."* Both **05:30 UTC and 06:30 UTC** match those words, because the clocks fall back an hour that night.
Now take *"8 March 2026, 02:30, New York."* **No instant** matches, because that hour is skipped.
An AI assistant that silently picks one answer, or invents one, adds a fact the source never stated. For an agent deciding whether a deadline has passed, that can change the action by an hour.

## Why it matters for AI trust and epistemics
Agents are increasingly asked to read deadlines and act on them: submit, pay, cancel or escalate. A trustworthy agent should return **exactly the set of instants the source supports**.
That means one instant when the source is clear, two when it is ambiguous, and none when the stated time doesn't exist. In the last two cases the agent should surface the uncertainty instead of guessing.
The report proposes a compact **evidence record** that a person or another agent can check: the quoted notice, the zone assumption, the time-zone database version and every candidate instant.

## Method (from the report)
- **Labels:** every half-hour local label in 2026 (48 × 365 = 17,520 per zone) for 8 zones. These are Los Angeles, New York, London, Berlin, Sydney, Lord Howe (a 30-minute DST shift), plus two fixed-offset controls, Kolkata and `Etc/GMT+12`. That gives **140,160 labels**.
- **Ground truth:** enumerate every UTC half-hour from 31 Dec 2025 to 1 Jan 2027, project each instant to local time and index the labels. A missing label has 0 valid instants and a repeated label has 2. A local time is never attached to a zone directly.
- **Methods compared:**
  - **Fixed offset:** the zone's offset at local noon on 14 Nov, applied to every label.
  - **Default fold:** attach the zone and convert once with `fold=0`, Python's default.
  - **Round trip:** try `fold=0` and `fold=1`, convert each to UTC and back, and keep only candidates that reproduce the original label.
- **Scoring:** a prediction counts as correct only if its set of instants exactly equals the ground-truth set.

## Results (Table 1, reproduced)
| Method | Wrong unique | Wrong gap | Wrong repeat | Total wrong |
|---|---|---|---|---|
| Fixed offset | 60,466 / 140,138 | 11 / 11 | 11 / 11 | 60,488 |
| Default fold | 0 / 140,138 | 11 / 11 | 11 / 11 | 22 |
| Round trip | 0 / 140,138 | 0 / 11 | 0 / 11 | **0** |

The default fold gives the right answer more than 99.98% of the time, yet it misses **every** case where the assistant should have flagged uncertainty. Only the round-trip check returned the correct set for all 140,160 labels.

### Real rerun output (18 Nov 2026, post-sprint, Python 3.13.5, IANA tzdata 2026f)
```
$ ./scripts/reproduce.sh
Python 3.13.5
tz search path: ('/usr/share/zoneinfo', '/usr/lib/zoneinfo', '/usr/share/lib/zoneinfo', '/etc/zoneinfo')
MATCH: rerun.csv is byte-identical to results.csv
Method                Wrong unique   Wrong gap  Wrong repeat  Total wrong
Fixed offset      60,466 / 140,138     11 / 11       11 / 11       60,488
Default fold           0 / 140,138     11 / 11       11 / 11           22
Round trip             0 / 140,138      0 / 11        0 / 11            0
Labels per method: 140,160
```
The report's own run used Python 3.14.6 and tzdata 2026e. The output was byte-identical across the two environments.

```
$ python3 scripts/worked_examples.py
New York 08 Mar 2026 02:30: 0 candidate(s) []
New York 01 Nov 2026 01:30: 2 candidate(s) ['2026-11-01 05:30 UTC', '2026-11-01 06:30 UTC']
15 Nov 2026 23:59 AoE = 16 Nov 11:59 UTC = 16 Nov 17:29 Asia/Kolkata
```

## Reproduce in one command
```
./scripts/reproduce.sh          # or: python3 clock_evidence.py > rerun.csv && diff results.csv rerun.csv
python3 -m unittest discover -s tests -v
```
It uses only the standard library and takes about 1 second. You need Python 3.9 or later with IANA time-zone data; on Windows, `pip install tzdata`.

## Repository layout
| Path | What it is | When |
|---|---|---|
| `clock_evidence.py` | The experiment, unchanged | sprint, 14 Nov 2026 |
| `results.csv` | Grouped result counts, unchanged | sprint, 14 Nov 2026 |
| `original/research-replication.zip` | The original archive, byte-for-byte | sprint, 14 Nov 2026 |
| `scripts/reproduce.sh`, `scripts/summarize.py`, `scripts/worked_examples.py` | Wrapper, Table 1 roll-up, worked-example check | post-sprint, 18 Nov 2026 |
| `tests/` | 9 unit tests of the unchanged code | post-sprint, 18 Nov 2026 |
| `PROVENANCE.md` | Hashes and timeline | post-sprint, 18 Nov 2026 |

## Limitations (from the report)
- The reference and the tested methods share the same time-zone database. Agreement shows internal consistency with that version; it cannot catch a wrong or outdated legal rule.
- **No LLM was tested.** Actual deadline adherence, user comprehension and production schedulers were not tested either. This measures a deterministic conversion component with known zone assignments.
- The zones were chosen to stress transitions. The 43% fixed-offset error rate must not be generalised to real deadline traffic.
- Out of scope: ambiguous abbreviations, scraping errors, date-only notices, policy changes and leap seconds.
- Dual use: someone could cherry-pick the later reading to justify a late action. Record both candidates and who resolved the ambiguity.
- The report states that an AI coding assistant generated the study design, code and text. No human review or independent replication is claimed in the report. The rerun above is a second machine run, not an independent human replication.

## Possible future work (not part of the submission)
- Test open-source LLMs on the same task (deadline text → set of candidate instants or a clarifying question), scored against this oracle.
- Use real deadline notices, with permission and independent labelling.

## Licence
Apache License 2.0. See `LICENSE`.
