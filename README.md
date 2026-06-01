# chromium-dashboard ESBMC-Python verification PoC

A proof-of-concept applying [ESBMC](https://github.com/esbmc/esbmc)'s
Python frontend to [GoogleChrome/chromium-dashboard](https://github.com/GoogleChrome/chromium-dashboard) —
the Google App Engine backend that tracks Chrome platform feature proposals,
origin trials, review gates, and shipping decisions.

Modelled on the
[vLLM PoC](https://github.com/lucasccordeiro/vllm) and
[AWS-Neuron PoC](https://github.com/lucasccordeiro/AWS-Neuron).

## Status

**26 verification targets** across four tiers — pure date/integer arithmetic
helpers (`is_weekday`, `weekdays_between`, `remaining_days`, `diff_days`,
`diff_weeks`), HTTP API input-validation paths, self-certify boolean
contracts (`is_privacy_eligible`, `is_testing_eligible`,
`is_adoption_eligible`, `is_eligible`), and SLO gate state-machine
invariants (`record_vote` index safety, overdue-detection arithmetic).
`make verify` (26 entries × two phases) completes in under 30 seconds
with 0 failures.

**Three live API-validation findings** confirmed by ESBMC counterexamples
and empirical reproduction (full traces in [`REPORT.md`](./REPORT.md)):

| Finding | Source | Admitted value | Downstream effect | Issue |
|---|---|---|---|---|
| A | `api/channels_api.py:146` | `?start > ?end` | Bare `raise ValueError` → Flask returns **HTTP 500** instead of HTTP 400 | [#6441](https://github.com/GoogleChrome/chromium-dashboard/issues/6441) |
| B | `api/features_api.py:117` | `?num=0` | `get_int_arg` admits 0 → **silent empty page** (HTTP 200, no error signal) | [#6442](https://github.com/GoogleChrome/chromium-dashboard/issues/6442) |
| C | `api/channels_api.py:138` | `?start=0` / `?end=0` | Milestone 0 accepted → **null dates** returned (HTTP 200, no error signal) | [#6443](https://github.com/GoogleChrome/chromium-dashboard/issues/6443) |

**Worked example — Finding B (`?num=0` silent-acceptance, [#6442](https://github.com/GoogleChrome/chromium-dashboard/issues/6442)).**
`GET /api/v0/features?num=0` is a reasonable user mistake (or a fuzzer
input), but `basehandlers.get_int_arg` only rejects negative values
(`if num < 0: self.abort(400, ...)`); zero is admitted.
`process_query_using_cache` then runs with `num=0`, reaches
`sorted_id_list[start : start + 0]` → `[]`, and responds
`{"total_count": 5000, "features": []}` with HTTP 200 — empty results,
no indication to the caller that the parameter was invalid.
The `harness/features_num_zero_silent_acceptance.py` ESBMC counterexample
is the bug witness (`assertion num > 0` violated at `num = 0`).
Proposed fix: add `if num == 0: self.abort(400, msg='num must be positive')`
after the `get_int_arg` call, mirroring the already-present negative guard.
Same silent-acceptance pattern as vLLM Findings #5 and #6
(`--max-logprobs <negative>`, `--long-prefill-token-threshold <negative>`).

**Finding A — bare `raise ValueError` (HTTP 500 not 400, [#6441](https://github.com/GoogleChrome/chromium-dashboard/issues/6441)).**
`api/channels_api.py:146` raises `ValueError` directly when
`?start > ?end`, but `APIHandler.get()` has no `except ValueError` wrapper,
so the bare raise propagates to Flask and produces an **HTTP 500 Internal
Server Error** rather than the HTTP 400 Bad Request the caller expects.
The `harness/channels_start_gt_end_bare_valueerror.py` counterexample pins
this: `assertion False` fires on the `except ValueError` path.
Proposed fix: replace `raise ValueError` with
`self.abort(400, msg='start must be <= end')`.
Same class as vLLM Finding #4 (bare `AssertionError` in `BlockPool.__init__`
instead of a clean `ValueError`).

**Finding C — milestone 0 accepted, null dates returned ([#6443](https://github.com/GoogleChrome/chromium-dashboard/issues/6443)).**
`api/channels_api.py:138–139` reads `?start` and `?end` through the same
`get_int_arg` that passes zero for Finding B. With `start=end=0` the
`start > end` guard (line 146) does not fire; `fetch_chrome_release_info(0)`
is called for a milestone that does not exist, and the server returns
`{"0": {"stable_date": null, …}}` with HTTP 200. Chrome milestone numbers
are 1-based; milestone 0 has no schedule data.
Proposed fix: add `if start < 1 or end < 1: self.abort(400, msg='milestone must be >= 1')`.

**ESBMC-Python bug encountered and fixed upstream.**
`nondet_bool()` inside a list comprehension produced a fresh symbolic
variable on each element access, causing spurious `VERIFICATION FAILED`
verdicts. Documented in [`REPORT.md`](./REPORT.md) and filed as
[esbmc/esbmc#5022](https://github.com/esbmc/esbmc/issues/5022).
Fixed in [esbmc/esbmc#5023](https://github.com/esbmc/esbmc/pull/5023)
(merged 2026-06-01); the `is_eligible_dispatch` harnesses now use list
comprehensions directly.

## Quickstart

```
make verify                          # both phases, every target
make phase1                          # functional contracts only
make phase2                          # --overflow-check only
make verify-only T=is_weekday        # single target

# With a non-PATH ESBMC binary:
make verify ESBMC=/path/to/esbmc
```

Requires ESBMC built from master at or after commit `27585275`
(PR #5023, 2026-06-01) for list-comprehension targets; ESBMC 8.3.0
release for all other targets.

## Layout

```
harness/
  stubs.py                              # nondet primitives + shared constants
  is_weekday.py                         # internals/slo.py:31           (SUCCESSFUL)
  is_weekday_buggy.py                   #   Saturday admitted as weekday (FAILED)
  weekdays_between_approx.py            # internals/slo.py:41 approx    (SUCCESSFUL)
  weekdays_between_approx_buggy.py      #   6/7 instead of 5/7          (FAILED)
  weekdays_between_loop.py              # internals/slo.py:44 loop       (SUCCESSFUL)
  weekdays_between_loop_buggy.py        #   counter init at 1            (FAILED)
  remaining_days.py                     # internals/slo.py:65            (SUCCESSFUL)
  remaining_days_buggy.py               #   subtraction reversed         (FAILED)
  diff_days_and_weeks.py                # internals/ot_process_reminders.py:368 (SUCCESSFUL)
  diff_days_and_weeks_buggy.py          #   //8 instead of //7           (FAILED)
  channels_start_gt_end_bare_valueerror.py  # Finding A — live bug       (FAILED)
  features_num_zero_silent_acceptance.py    # Finding B — live bug       (FAILED)
  channels_milestone_zero_silent_acceptance.py  # Finding C — live bug   (FAILED)
  is_privacy_eligible.py                # internals/self_certify.py:73   (SUCCESSFUL)
  is_privacy_eligible_buggy.py          #   explanation check dropped    (FAILED)
  is_testing_eligible.py                # internals/self_certify.py:82   (SUCCESSFUL)
  is_testing_eligible_buggy.py          #   integration check dropped    (FAILED)
  is_adoption_eligible.py               # internals/self_certify.py:93   (SUCCESSFUL)
  is_adoption_eligible_buggy.py         #   lead_time check dropped      (FAILED)
  is_eligible_dispatch.py               # internals/self_certify.py:103  (SUCCESSFUL)
  is_eligible_dispatch_buggy.py         #   privacy↔testing routes swapped  (FAILED)
  record_vote_index_safety.py           # internals/slo.py:73 index guard (SUCCESSFUL)
  record_vote_index_safety_buggy.py     #   empty-votes guard dropped    (FAILED)
  overdue_detection.py                  # internals/reminders.py:463     (SUCCESSFUL)
  overdue_detection_buggy.py            #   <= instead of ==             (FAILED)
verify.py                   # manifest + two-phase driver
Makefile                    # make verify / phase1 / phase2 / verify-only
REPORT.md                   # per-target results + finding traces + pitfall notes
ROADMAP.md                  # tiered plan: targets, rationale, recommended sequence
```

## Targets

| Target | Entry | Phase 1 VCCs | Phase 2 VCCs |
|---|---|---|---|
| `is_weekday` | `is_weekday.py` | 3 ✓ | 4 ✓ |
| `is_weekday_buggy` | `is_weekday_buggy.py` | 1 ✗ | — |
| `weekdays_between_approx` | `weekdays_between_approx.py` | 3 ✓ | 14 ✓ |
| `weekdays_between_approx_buggy` | `weekdays_between_approx_buggy.py` | 1 ✗ | — |
| `weekdays_between_loop` | `weekdays_between_loop.py` | 36 ✓ | 100 ✓ |
| `weekdays_between_loop_buggy` | `weekdays_between_loop_buggy.py` | 3 ✗ | — |
| `remaining_days` | `remaining_days.py` | 4 ✓ | 7 ✓ |
| `remaining_days_buggy` | `remaining_days_buggy.py` | 1 ✗ | — |
| `diff_days_and_weeks` | `diff_days_and_weeks.py` | 3 ✓ | 11 ✓ |
| `diff_days_and_weeks_buggy` | `diff_days_and_weeks_buggy.py` | 2 ✗ | — |
| `channels_start_gt_end_bare_valueerror` | `channels_start_gt_end_bare_valueerror.py` | **2 ✗ (Finding A)** | — |
| `features_num_zero_silent_acceptance` | `features_num_zero_silent_acceptance.py` | **1 ✗ (Finding B)** | — |
| `channels_milestone_zero_silent_acceptance` | `channels_milestone_zero_silent_acceptance.py` | **1 ✗ (Finding C)** | — |
| `is_privacy_eligible` | `is_privacy_eligible.py` | 4 ✓ | 4 ✓ |
| `is_privacy_eligible_buggy` | `is_privacy_eligible_buggy.py` | 1 ✗ | — |
| `is_testing_eligible` | `is_testing_eligible.py` | 7 ✓ | 7 ✓ |
| `is_testing_eligible_buggy` | `is_testing_eligible_buggy.py` | 1 ✗ | — |
| `is_adoption_eligible` | `is_adoption_eligible.py` | 6 ✓ | 6 ✓ |
| `is_adoption_eligible_buggy` | `is_adoption_eligible_buggy.py` | 1 ✗ | — |
| `is_eligible_dispatch` | `is_eligible_dispatch.py` | 3 ✓ | 3 ✓ |
| `is_eligible_dispatch_buggy` | `is_eligible_dispatch_buggy.py` | 1 ✗ | — |
| `record_vote_index_safety` | `record_vote_index_safety.py` | 2 ✓ | 2 ✓ |
| `record_vote_index_safety_buggy` | `record_vote_index_safety_buggy.py` | 1 ✗ | — |
| `overdue_detection` | `overdue_detection.py` | 3 ✓ | 10 ✓ |
| `overdue_detection_buggy` | `overdue_detection_buggy.py` | 1 ✗ | — |

✓ = SUCCESSFUL (expected), ✗ = FAILED (expected). Buggy targets skip Phase 2.

## Two-phase verification

| Phase | Flags | Catches |
|---|---|---|
| 1 | (default) | Functional contracts via `assert`: bounds, monotonicity, dispatch routing, gate invariants. |
| 2 | `--overflow-check` | CWE-190 (signed overflow), CWE-369 (division-by-zero) on integer arithmetic. |

A buggy target whose Phase 1 already fails skips Phase 2.

## Provenance

- **ESBMC**: https://github.com/esbmc/esbmc — master `27585275` (PR #5023,
  2026-06-01), default Bitwuzla solver.
- **chromium-dashboard**: https://github.com/GoogleChrome/chromium-dashboard —
  pinned at commit `d0d21c8` (2026-05-26).
