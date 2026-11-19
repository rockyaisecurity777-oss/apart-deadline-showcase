# Comparison results (post-sprint)

Added 19 November 2026. These numbers are not part of the judged submission. They come from a run on the same 2026 half-hour grid and eight zones as the paper, by importing `clock_evidence.oracle` and `clock_evidence.possible`.

**Run:** 19 Nov 2026, 10:43:14 IST (Asia/Kolkata). Python 3.13.5, IANA tzdata 2026f. 140,160 labels (140,138 unique, 11 gap, 11 repeat). Reproduce with `python3 -m extensions.benchmark` from the repository root. Runtimes are one timed pass on this machine and will vary.

## How the columns are scored

- **Wrong:** the method’s returned set of UTC instants is not exactly the oracle set. A fail-closed reject on a repeated label returns the empty set, which is “wrong” as a set reconstruction (the oracle has two instants) but is not a silent error.
- **Flagged:** the method refused to silently commit (reject, confirmation, missing offset, or ensemble alarm).
- **Silent error:** wrong and not flagged. This is the operational failure the paper measured: inventing or dropping an instant without saying so.

## Paper grid, all strategies

| Strategy | What it does | Wrong | Flagged | Silent errors | Runtime (s) |
|---|---|---:|---:|---:|---:|
| round_trip | Paper method: keep instants that convert back to the wall | 0 | 0 | 0 | 0.5471 |
| fail_closed | Flag and return nothing on gap or repeat; convert uniques | 11 | 22 | 0 | 0.5269 |
| policy_earliest_shift | Repeats: earliest instant. Gaps: shift the wall later by the gap (java.time `ofLocal`-style) | 22 | 0 | 22 | 0.5961 |
| policy_latest_shift | Repeats: latest instant. Gaps: shift-forward | 22 | 0 | 22 | 0.5259 |
| policy_earliest_reject | Repeats: earliest. Gaps: reject | 11 | 11 | 11 | 0.5085 |
| policy_latest_reject | Repeats: latest. Gaps: reject | 11 | 11 | 11 | 0.5201 |
| policy_reject_reject | Reject both gaps and repeats (same behaviour as fail-closed) | 11 | 22 | 0 | 0.5837 |
| offset_pinned | If the zone fixes one offset, store and re-parse RFC 9557; otherwise flag | 11 | 22 | 0 | 1.4769 |
| utc_normalize | Convert uniques to UTC; require confirmation on the 22 ambiguous labels | 11 | 22 | 0 | 0.4906 |
| ensemble | Alarm when member methods disagree; return the round-trip set | 0 | 22 | 0 | 2.1122 |
| first_fold_baseline | Paper’s default-fold method, for comparison | 22 | 0 | 22 | 0.2607 |

The 11 “wrong” counts on fail-closed, offset-pinned, utc_normalize, and the reject/reject policy are exactly the 11 repeated labels: those methods flag the case and return no instants, so they do not reconstruct the two-instant set. They have **0 silent errors**. The 11 unique-side conversions are exact in every method in this table.

Default fold, and the two shift-forward policies, silently err on all 22 gap and repeat labels. Earliest-or-latest with reject still silently picks one of the two repeated instants (11 silent errors) while correctly refusing the 11 gaps.

### Ensemble, specifically

Members: round trip, default fold, earliest-with-reject, latest-with-reject, and fail-closed.

- Alarms on gaps: 11 / 11
- Alarms on repeats: 11 / 11
- **Caught 22 / 22** of the paper’s ambiguous labels
- **False alarms on unique labels: 0 / 140,138**

Because the ensemble returns the round-trip set, it is also exact as a set reconstruction (0 wrong, 0 silent errors) and uses the flag only as an alarm.

### UTC normalisation: how many inputs need confirmation

On this grid, **22 of 140,160** labels (the 11 gaps and 11 repeats) would need a human confirmation step. The other 140,138 can be stored as a single UTC instant without asking.

### Offset-pinned representation

Every unique label produced an RFC 9557 string that parsed back to the same instant, including the paper’s AoE example `2026-11-15T23:59:00-12:00[Etc/GMT+12]`. The 22 gap and repeat labels cannot be pinned from a wall time and a zone alone, and were flagged. An offset that does not match the zone (for example, a summer offset in January) is rejected.

## Randomised zones (beyond the paper’s eight)

A property-style test (`extensions/tests/test_randomized.py`) used seed `20261119`, drew 24 zones from 553 eligible IANA names (the paper’s eight zones and `Etc/*` were excluded), and ran the same 2026 half-hour grid: **24 zones × 17,520 = 420,480 labels**, of which 420,450 were unique and 30 were gaps or repeats.

Sampled zones: Pacific/Easter, Pacific/Wake, Antarctica/Casey, Africa/El_Aaiun, Asia/Dili, GMT0, CST6CDT, America/Anguilla, Asia/Khandyga, Africa/Tripoli, America/Punta_Arenas, Asia/Makassar, Africa/Khartoum, Pacific/Galapagos, Pacific/Ponape, Atlantic/Jan_Mayen, Asia/Sakhalin, America/Argentina/Buenos_Aires, Africa/Bamako, Asia/Anadyr, Antarctica/Troll, Pacific/Bougainville, America/Argentina/Cordoba, America/Nome.

On that sample: round-trip silent errors 0, fail-closed silent errors 0, ensemble missed ambiguous labels 0, ensemble false alarms 0. This is still a half-hour grid, so a zone whose only 2026 transition is off that grid would not appear as a gap or repeat here.

## tzdata

The Table 1 property (round trip has 0 silent errors on the paper grid) still held on IANA tzdata **2026f**, the version on this machine. The judged report used 2026e. The sprint `results.csv` remained byte-identical on 2026f in earlier reruns; this extension run did not rewrite that file.

## Which to use when

- **To report what the source actually supports:** use round trip, and show the set (zero, one, or two instants). That is the paper’s contract.
- **In a scheduler that must not guess:** use fail-closed, or UTC normalisation with a confirmation step, and keep an audit record. On this grid that means asking the user on 22 labels and converting the rest automatically.
- **If the source can store an offset at capture time (calendar invite, log, API):** store RFC 9557 (offset plus zone). Later reads do not have to solve a fold. You still need a policy for historical data that has only a local label.
- **If a product policy must pick a side (some calendar stacks do):** name the policy (earliest, latest, or shift-forward) and log it. Do not hide it behind a language default. Those policies still have silent errors against the exact-set contract.
- **As a production safety net:** run the ensemble over independent methods and alarm on disagreement. On this grid it caught every ambiguous label and raised no false alarm on a unique label. It is a check, not a substitute for the round-trip set.

The judged PDF is unchanged. These figures can help a reviewer or an Apart Studio / Fellowship discussion; they are not a revised official result.

## Limits

The oracle and the methods still share one tzdata version. Confirmation is simulated as a flag, not a real UI. The half-hour grid will miss transitions that do not fall on a half-hour. The randomised sample is 24 zones, not the whole IANA set. No LLM or real-notice corpus was tested. None of this was in the 14 November submission.
