# chromium-dashboard / ESBMC-Python PoC — verification record

Per-target verification results.  See [`ROADMAP.md`](./ROADMAP.md) for the
planning rationale.

Pinned upstream: `GoogleChrome/chromium-dashboard @ d0d21c8` (2026-05-26).
Verifier: ESBMC 8.3.0+.

---

## Target index

| Name | Entry | Phase 1 | VCCs | Phase 2 | VCCs | Notes |
|---|---|---|---|---|---|---|
| `is_weekday` | `is_weekday.py` | SUCCESSFUL | 3 | SUCCESSFUL | 4 | |
| `is_weekday_buggy` | `is_weekday_buggy.py` | FAILED | 1 | skipped | — | Saturday admitted as weekday |
| `weekdays_between_approx` | `weekdays_between_approx.py` | SUCCESSFUL | 3 | SUCCESSFUL | 14 | |
| `weekdays_between_approx_buggy` | `weekdays_between_approx_buggy.py` | FAILED | 1 | skipped | — | `6/7` instead of `5/7` |
| `weekdays_between_loop` | `weekdays_between_loop.py` | SUCCESSFUL | 36 | SUCCESSFUL | 100 | `--unwind 32` |
| `weekdays_between_loop_buggy` | `weekdays_between_loop_buggy.py` | FAILED | 3 | skipped | — | counter init at 1 → result > calendar_days |
| `remaining_days` | `remaining_days.py` | SUCCESSFUL | 4 | SUCCESSFUL | 7 | |
| `remaining_days_buggy` | `remaining_days_buggy.py` | FAILED | 1 | skipped | — | subtraction reversed |
| `diff_days_and_weeks` | `diff_days_and_weeks.py` | SUCCESSFUL | 3 | SUCCESSFUL | 11 | |
| `diff_days_and_weeks_buggy` | `diff_days_and_weeks_buggy.py` | FAILED | 2 | skipped | — | `//8` instead of `//7` |
| `channels_start_gt_end_bare_valueerror` | `channels_start_gt_end_bare_valueerror.py` | **FAILED** | 2 | skipped | — | **Finding A — live bug** |
| `features_num_zero_silent_acceptance` | `features_num_zero_silent_acceptance.py` | **FAILED** | 1 | skipped | — | **Finding B — live bug** |
| `channels_milestone_zero_silent_acceptance` | `channels_milestone_zero_silent_acceptance.py` | **FAILED** | 1 | skipped | — | **Finding C — live bug** |
| `votes_state_zero_validator_bypass` | `votes_state_zero_validator_bypass.py` | **FAILED** | 1 | skipped | — | **Finding D — live bug** |
| `is_privacy_eligible` | `is_privacy_eligible.py` | SUCCESSFUL | 4 | SUCCESSFUL | 4 | |
| `is_privacy_eligible_buggy` | `is_privacy_eligible_buggy.py` | FAILED | 1 | skipped | — | explanation check dropped |
| `is_testing_eligible` | `is_testing_eligible.py` | SUCCESSFUL | 7 | SUCCESSFUL | 7 | |
| `is_testing_eligible_buggy` | `is_testing_eligible_buggy.py` | FAILED | 1 | skipped | — | integration check dropped |
| `is_adoption_eligible` | `is_adoption_eligible.py` | SUCCESSFUL | 6 | SUCCESSFUL | 6 | |
| `is_adoption_eligible_buggy` | `is_adoption_eligible_buggy.py` | FAILED | 1 | skipped | — | lead_time check dropped |
| `is_eligible_dispatch` | `is_eligible_dispatch.py` | SUCCESSFUL | 3 | SUCCESSFUL | 3 | list comprehension (esbmc/esbmc#5023) |
| `is_eligible_dispatch_buggy` | `is_eligible_dispatch_buggy.py` | FAILED | 1 | skipped | — | privacy↔testing routes swapped |
| `record_vote_index_safety` | `record_vote_index_safety.py` | SUCCESSFUL | 2 | SUCCESSFUL | 2 | |
| `record_vote_index_safety_buggy` | `record_vote_index_safety_buggy.py` | FAILED | 1 | skipped | — | empty-votes guard dropped |
| `record_vote_changed_flag` | `record_vote_changed_flag.py` | SUCCESSFUL | 1 | SUCCESSFUL | 6 | `changed` ⇔ ≥1 field mutated; monotone |
| `record_vote_changed_flag_buggy` | `record_vote_changed_flag_buggy.py` | FAILED | 1 | skipped | — | spurious `changed = False` reset in resolved branch |
| `record_comment_idempotent` | `record_comment_idempotent.py` | SUCCESSFUL | 3 | SUCCESSFUL | 3 | initial response recorded once; write-iff-true; idempotent |
| `record_comment_idempotent_buggy` | `record_comment_idempotent_buggy.py` | FAILED | 1 | skipped | — | `responded_on is not None` guard dropped → re-records |
| `overdue_detection` | `overdue_detection.py` | SUCCESSFUL | 3 | SUCCESSFUL | 10 | |
| `overdue_detection_buggy` | `overdue_detection_buggy.py` | FAILED | 1 | skipped | — | `<= -1` instead of `== -1` |
| `milestone_skip_round_trip` | `milestone_skip_round_trip.py` | SUCCESSFUL | 2 | SUCCESSFUL | 6 | |
| `milestone_skip_round_trip_buggy` | `milestone_skip_round_trip_buggy.py` | FAILED | 1 | skipped | — | `next` jumps to 84 instead of 83 |

**Total targets: 32 (14 SUCCESSFUL + 18 FAILED, of which 4 FAILED are the live-bug
findings A/B/C/D). Every target matches its expected verdict; 0 deviations.**

---

## ESBMC-Python bug encountered and fixed upstream

### List comprehension / nondet_bool ([esbmc/esbmc#5022](https://github.com/esbmc/esbmc/issues/5022), fixed in [esbmc/esbmc#5023](https://github.com/esbmc/esbmc/pull/5023))

`[nondet_bool() for _ in range(N)]` created a list, but ESBMC-Python did not
stably store the comprehension's elements: reading `ans[i]` through a
function-parameter alias re-materialised a fresh nondet variable rather than
returning the stored element.  When the same list was passed to two separate
function calls (`is_eligible(gate_type, ans)` and then
`is_privacy_eligible(ans)`), the two calls saw independent nondet draws — the
assertion `result == predicate(ans)` became a comparison of independent
symbolic values.

**Symptom:** spurious `VERIFICATION FAILED` (a false alarm), not a false
SUCCESSFUL.  Reproduced under both Bitwuzla and Z3 on ESBMC 8.3.0 / master
`b259f8a`; minimal case in
[`reproducer/esbmc_list_comprehension_divergence.py`](./reproducer/esbmc_list_comprehension_divergence.py).
Distinct from the closed #3836 (spurious out-of-bounds, fixed by #3839).

**Status:** fixed in [esbmc/esbmc#5023](https://github.com/esbmc/esbmc/pull/5023)
(merged 2026-06-01, commit `27585275`).  `get_argument_type` now recovers
`list[T]` for a name bound to an empty-literal comprehension by inspecting the
first `.append(arg)` in the enclosing scope.  The `is_eligible_dispatch`
harnesses have been updated to use list comprehensions directly.

---

## Findings

### Finding A — `channels_api.py:146` — bare `raise ValueError` produces HTTP 500 ([#6441](https://github.com/GoogleChrome/chromium-dashboard/issues/6441))

**Source**: `api/channels_api.py:146`

```python
if start > end:
    raise ValueError           # bare — not self.abort(400, msg=...)
```

`APIHandler.get()` (`framework/basehandlers.py:251`) has no `except
ValueError` wrapper; the bare raise propagates to Flask and becomes
**HTTP 500 Internal Server Error** instead of HTTP 400 Bad Request.

**ESBMC counterexample** (`channels_start_gt_end_bare_valueerror.py`,
Phase 1 FAILED, 2 VCCs):

```
Violated property:
  file channels_start_gt_end_bare_valueerror.py
  assertion False  ("bare ValueError should have been an HTTP 400 abort")

  start = any positive int, end = any positive int, start > end
```

**Proposed fix**: replace `raise ValueError` with
`self.abort(400, msg='start must be <= end')`.

**Severity**: UX defect — same class as vLLM Finding #4 (bare AssertionError
in BlockPool instead of a clean ValueError).

---

### Finding B — `features_api.py:117` — `?num=0` silent-acceptance ([#6442](https://github.com/GoogleChrome/chromium-dashboard/issues/6442))

**Source**: `api/features_api.py:117`, `framework/basehandlers.py:182`

`get_int_arg('num')` rejects `num < 0` but admits `num = 0`.
With `num=0`, `process_query_using_cache` runs and returns
`{'total_count': N, 'features': []}` with HTTP 200 — empty page,
no 400 error.

**ESBMC counterexample** (`features_num_zero_silent_acceptance.py`,
Phase 1 FAILED, 1 VCC):

```
Violated property:
  file features_num_zero_silent_acceptance.py
  assertion num > 0

  num = 0  (admitted by get_int_arg; returns HTTP 200 with empty features)
```

**Proposed fix**: add `if num == 0: self.abort(400, msg='num must be positive')`
after the `get_int_arg` call, or tighten `get_int_arg` with a `> 0` guard.

**Severity**: silent-acceptance defect — same class as vLLM Findings #5 and #6.

---

### Finding C — `channels_api.py:138` — `?start=0` milestone 0 accepted ([#6443](https://github.com/GoogleChrome/chromium-dashboard/issues/6443))

**Source**: `api/channels_api.py:138`

`get_int_arg('start')` and `get_int_arg('end')` admit 0.
With `start=end=0`, the `start > end` guard does not trigger;
`fetch_chrome_release_info(0)` is called — milestone 0 is not a real
Chrome milestone, and the API returns null dates with HTTP 200.

**ESBMC counterexample** (`channels_milestone_zero_silent_acceptance.py`,
Phase 1 FAILED, 1 VCC):

```
Violated property:
  file channels_milestone_zero_silent_acceptance.py
  assertion start >= 1

  start = 0  (admitted by get_int_arg; returns null dates HTTP 200)
```

**Proposed fix**: add `if start < 1 or end < 1: self.abort(400, msg='milestone must be >= 1')`
after the args are parsed.

**Severity**: silent-acceptance defect — same class as vLLM Finding #3
(`--max-model-len 0` propagating to the scheduler).

---

### Finding D — `reviews_api.py` `VotesAPI.do_post` — `state=0`/`false` bypasses `Vote.is_valid_state` (not yet filed)

**Source**: `api/reviews_api.py` (`VotesAPI.do_post`),
`framework/basehandlers.py` (`get_param`, `get_int_param`)

```python
new_state = self.get_int_param('state', validator=Vote.is_valid_state)
```

Both `get_param` (`if val and validator and not validator(val)`) and
`get_int_param` (`if val and type(val) != int`) guard validation with a
`val and ...` short-circuit.  A falsy `state` (JSON `0` or `false`) skips
both the `Vote.is_valid_state` validator and the int type check.
`is_valid_state(0)` is False (valid states are `1..11`), yet `0` is accepted
and recorded as a vote state.

**ESBMC counterexample** (`votes_state_zero_validator_bypass.py`,
Phase 1 FAILED, 1 VCC):

```
Violated property:
  file votes_state_zero_validator_bypass.py
  assertion is_valid_state(state)

  state = 0  (validator short-circuited by `val and ...`; accepted)
```

Confirmed empirically under CPython
(`reproducer/finding_d_state_validator_bypass.py`): `state=0` and `state=false`
are accepted, while the non-falsy invalid `state=99` is correctly rejected.

**Proposed fix**: test presence rather than truthiness —
`if val is not None and validator and not validator(val):` in `get_param`
and `if val is not None and type(val) != int:` in `get_int_param`
(the `allowed` guard in `get_param` has the same flaw).

**Severity**: silent-acceptance / validation-bypass defect — same class as
Findings A/B/C and vLLM Finding #3.
