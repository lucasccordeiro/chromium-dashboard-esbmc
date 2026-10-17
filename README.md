# chromium-dashboard Veribee ESBMC-Python verification PoC

Applies Veribee [ESBMC](https://github.com/esbmc/esbmc)'s Python frontend to
[GoogleChrome/chromium-dashboard](https://github.com/GoogleChrome/chromium-dashboard),
the App Engine backend that tracks Chrome feature proposals, origin trials,
review gates, and shipping decisions. Modelled on the
[vLLM](https://github.com/lucasccordeiro/vllm) and
[AWS-Neuron](https://github.com/lucasccordeiro/AWS-Neuron) PoCs.

## Status

**48 verification targets** in five tiers (`verify.py` is the manifest):

1. Date/integer helpers — `internals/slo.py`, `ot_process_reminders.py`.
2. API input validation — the findings below, positive controls, and two
   review/approval security invariants.
3. Self-certify eligibility contracts — `internals/self_certify.py`.
4. SLO gate state machine — `record_vote`, `record_comment`, overdue detection.
5. Milestone arithmetic — next/previous release-number round trip.

Each correct target is paired with a seeded-bug variant (`*_buggy.py`) or a
fixed-behaviour control (`*_validated.py`) that ESBMC must reject or accept,
so no proof passes vacuously.

**Security invariants proven sound (no bug).** `_calc_gate_state`
(`internals/approval_defs.py`) returns `APPROVED` only with at least the
threshold of genuine `APPROVED` votes (1 for `ONE_LGTM`, 3 for `THREE_LGTM`)
and no `NA` vote. `require_permissions` (`api/reviews_api.py`) lets only an
approver cast a negative verdict, and lets a non-approver reach an approving
state only as a self-certify-eligible editor.

**Ten API-validation findings**, each with an ESBMC counterexample and a
CPython reproducer. Three are fixed upstream with the fix we proposed.

| Finding | Source | Input | Effect | Issue | Upstream fix |
|---|---|---|---|---|---|
| A | `api/channels_api.py:146` | `?start > ?end` | Bare `ValueError` → HTTP 500, not 400 | [#6441](https://github.com/GoogleChrome/chromium-dashboard/issues/6441) | [PR #6451](https://github.com/GoogleChrome/chromium-dashboard/pull/6451) (merged) |
| B | `api/features_api.py:117` | `?num=0` | `get_int_arg` admits 0 → empty page, HTTP 200 | [#6442](https://github.com/GoogleChrome/chromium-dashboard/issues/6442) | closed, won't fix (benign) |
| C | `api/channels_api.py:138` | `?start=0` / `?end=0` | Milestone 0 accepted → null dates, HTTP 200 | [#6443](https://github.com/GoogleChrome/chromium-dashboard/issues/6443) | [PR #6656](https://github.com/GoogleChrome/chromium-dashboard/pull/6656) (merged) |
| D | `api/reviews_api.py:78` | `{"state": 0}` / `false` | Falsy value skips `Vote.is_valid_state` → bare `ValueError` → HTTP 500 | [#6447](https://github.com/GoogleChrome/chromium-dashboard/issues/6447) | [PR #6452](https://github.com/GoogleChrome/chromium-dashboard/pull/6452) (merged) |
| E | `api/shipping_features_api.py:58` | `?mstone=0` | Guard checks only `is None` → empty lists, HTTP 200 | not filed | — |
| F | `api/metricsdata.py:199` | `?num=0` | `if num:` skips the slice → all datapoints, HTTP 200 | not filed (B class) | — |
| G | `api/features_api.py:552` | PATCH without `feature_changes` | `KeyError` → HTTP 500, not 400 | [#6464](https://github.com/GoogleChrome/chromium-dashboard/issues/6464) | — |
| H | `api/stages_api.py:101` | malformed `stage_type` | `TypeError`/`KeyError`/`ValueError` → HTTP 500, not 400 | not filed | — |
| I | `api/comments_api.py:175` | PATCH unknown `commentId` | `None.deleted_by` → HTTP 500, not 404 | [#6468](https://github.com/GoogleChrome/chromium-dashboard/issues/6468) | — |
| J | `api/intents_api.py:176` | POST body with an extra key | `PostIntentRequest(**body)` `TypeError` → HTTP 500, not 400 | [#6469](https://github.com/GoogleChrome/chromium-dashboard/issues/6469) | — |

Root causes, proposed fixes, and full traces are in [`REPORT.md`](./REPORT.md).
Upstream issue texts are in [`bug-reports/`](./bug-reports/).

**ESBMC bug found along the way.** `nondet_bool()` inside a list comprehension
produced a fresh symbolic value on each access and caused spurious failures
([esbmc/esbmc#5022](https://github.com/esbmc/esbmc/issues/5022)). It was fixed
upstream in [esbmc/esbmc#5023](https://github.com/esbmc/esbmc/pull/5023).

## Requirements

- Python 3.
- ESBMC built from master at or after `27585275` (PR #5023, 2026-06-01). The
  list-comprehension targets need it; ESBMC 8.3.0 is enough for all others.

## Usage

```
make verify                    # both phases, every target
make phase1                    # functional contracts only
make phase2                    # --overflow-check only
make verify-only T=is_weekday  # single target
make verify ESBMC=/path/to/esbmc
```

A full run takes under 30 seconds. It exits non-zero if any verdict differs
from the expected one in `verify.py`.

| Phase | ESBMC flags | Checks |
|---|---|---|
| 1 | (default) | Functional contracts written as `assert` |
| 2 | `--overflow-check` | Signed overflow (CWE-190) and division by zero (CWE-369) |

A target that is expected to fail in Phase 1 skips Phase 2.

## Layout

```
harness/      ESBMC targets; stubs.py holds the nondet primitives
reproducer/   CPython reproducers for each finding
bug-reports/  Upstream issue texts, one per finding
verify.py     Target manifest (entry, flags, expected verdict) and driver
Makefile      Wrappers around verify.py
REPORT.md     Per-target results, finding traces, ESBMC pitfalls
ROADMAP.md    Target plan and rationale
```

## Provenance

- ESBMC: master `27585275` (2026-06-01), default Bitwuzla solver.
- chromium-dashboard: commit `d0d21c8` (2026-05-26).
