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
| `shipping_features_mstone_zero_silent_acceptance` | `shipping_features_mstone_zero_silent_acceptance.py` | **FAILED** | 1 | skipped | — | **Finding E — live bug** |
| `releasenotes_milestone_range_validated` | `releasenotes_milestone_range_validated.py` | SUCCESSFUL | 3 | SUCCESSFUL | 6 | positive control: correct milestone-range check |
| `metricsdata_num_zero_returns_all` | `metricsdata_num_zero_returns_all.py` | **FAILED** | 1 | skipped | — | **Finding F — live bug** |
| `metricsdata_num_limit_honored` | `metricsdata_num_limit_honored.py` | SUCCESSFUL | 2 | SUCCESSFUL | 2 | positive control: `if num is not None` honors the limit |
| `features_patch_missing_feature_changes_http500` | `features_patch_missing_feature_changes_http500.py` | **FAILED** | 1 | skipped | — | **Finding G — live bug** |
| `features_patch_body_shape_validated` | `features_patch_body_shape_validated.py` | SUCCESSFUL | 2 | SUCCESSFUL | 2 | positive control: body-shape guard returns 400, never 500 |
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

**Total targets: 38 (17 SUCCESSFUL + 21 FAILED, of which 7 FAILED are the live-bug
findings A/B/C/D/E/F/G). Every target matches its expected verdict; 0 deviations.**

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

**Upstream fix**: a maintainer opened
[PR #6451](https://github.com/GoogleChrome/chromium-dashboard/pull/6451)
("Give 400 for bad channel range.", open as of 2026-06-03) resolving Finding A, which replaces
`raise ValueError` with `self.abort(400, 'start is greater than end')` — the
fix we proposed — and adds a regression test asserting HTTP 400. The PR body
states the project convention directly: `api/` code should `self.abort(400, …)`
on bad user input rather than rely on a generic `except` in `basehandlers.py`,
"because such an `except` might mask coding errors."

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

### Finding D — `reviews_api.py:78` `VotesAPI.do_post` — falsy `state` (0/false) → HTTP 500 via bypassed validation + bare `ValueError` ([#6447](https://github.com/GoogleChrome/chromium-dashboard/issues/6447))

**Source**: `api/reviews_api.py:78` (`VotesAPI.do_post`),
`framework/basehandlers.py:124,141` (`get_param`, `get_int_param`),
`internals/approval_defs.py:466-467` (`set_vote`)

```python
new_state = self.get_int_param('state', validator=Vote.is_valid_state)
```

Both `get_param` (line 124, `if val and validator and not validator(val)`) and
`get_int_param` (line 141, `if val and type(val) != int`) guard validation with
a `val and ...` short-circuit.  A falsy `state` (JSON `0` or `false`) skips both
the `Vote.is_valid_state` validator and the int type check, so the invalid value
is returned from the helper instead of being rejected with HTTP 400.
`is_valid_state(0)` is False (valid states are `1..11`; `0 == Gate.PREPARING`).

The bypassed value is **not** recorded: `approval_defs.set_vote` re-checks and
raises a **bare** `ValueError('Invalid approval state')` (lines 466-467).  Since
the raise is bare (not `self.abort(400, ...)`) and `APIHandler.post`
(`basehandlers.py:275`) has no `except ValueError`, the caller receives
**HTTP 500** instead of HTTP 400 — the same bare-raise → 500 mechanism as
Finding A.

**ESBMC counterexample** (`votes_state_zero_validator_bypass.py`, models the
helper acceptance gate, Phase 1 FAILED, 1 VCC):

```
Violated property:
  file votes_state_zero_validator_bypass.py
  assertion is_valid_state(state)

  state = 0  (validator short-circuited by `val and ...`; accepted by helper)
```

Confirmed empirically under CPython
(`reproducer/finding_d_state_validator_bypass.py`), which models the full chain:

```
OK:  state=5  -> HTTP 200 (recorded)
BUG: state=0 -> helper accepts it, set_vote raises bare ValueError -> HTTP 500 (expected 400)
BUG: state=False -> helper accepts it, set_vote raises bare ValueError -> HTTP 500 (expected 400)
OK:  state=99 -> HTTP 400 (rejected at API boundary)
```

The non-falsy invalid `state=99` is rejected cleanly (HTTP 400), confirming the
gap is specific to falsy values.

**Proposed fix**: test presence rather than truthiness —
`if val is not None and validator and not validator(val):` in `get_param`
and `if val is not None and type(val) != int:` in `get_int_param`
(the `allowed` guard on line 126 has the same flaw).  Defense-in-depth:
`set_vote` should `self.abort(400, ...)` rather than raise a bare `ValueError`.

**Upstream fix**: a maintainer opened
[PR #6452](https://github.com/GoogleChrome/chromium-dashboard/pull/6452)
("Fix validation of 0 int parameters.", open as of 2026-06-03) resolving Finding D, which changes
both `get_param` guards from `if val and …` to `if val is not None and …` (the
`validator` and `allowed` checks) — the exact fix we proposed. The PR body
states the principle: "We should validate whenever an expected int parameter is
found, even if it is 0." This rejects the falsy `state` at the API boundary, so
`set_vote`'s bare `ValueError` is no longer reached on this path. Two notes: the
patch leaves `get_int_param`'s own `if val and type(val) != int:` short-circuit
unchanged (latent, but moot for this finding once `get_param` rejects the value)
and does not apply the defense-in-depth `abort(400)` in `set_vote`.

**Severity**: validation-bypass → HTTP 500 defect — same bare-raise → 500 class
as Finding A.

---

### Finding E — `shipping_features_api.py:58` `ShippingFeaturesAPI.do_get` — `?mstone=0` silent-acceptance (HTTP 200 empty page)

**Source**: `api/shipping_features_api.py:58`, `framework/basehandlers.py:182`

```python
milestone = self.get_int_arg('mstone')
if milestone is None:
    self.abort(400, msg='No milestone provided.')
shipping_stages = self._get_shipping_stages(milestone)
if len(shipping_stages) == 0:
    return {'complete_features': [], 'incomplete_features': []}   # HTTP 200
```

`get_int_arg('mstone')` rejects `< 0` but admits `0`.  The handler guards only
`milestone is None`, and `0 is None` is `False`, so `?mstone=0` passes.
`_get_shipping_stages(0)` queries `Stage.milestones.*_first == 0`; no stage
ships at milestone 0, so the query returns `[]` and `do_get` takes the
`len == 0` early return — **HTTP 200** with empty feature lists and no error
signal.  The `is None` guard shows the author handled the missing-parameter
case but not the invalid-zero case.

**ESBMC counterexample** (`shipping_features_mstone_zero_silent_acceptance.py`,
Phase 1 FAILED, 1 VCC):

```
Violated property:
  file shipping_features_mstone_zero_silent_acceptance.py
  assertion mstone >= 1

  mstone = 0  (admitted by get_int_arg; do_get returns empty lists, HTTP 200)
```

Confirmed empirically under CPython
(`reproducer/finding_e_shipping_mstone_zero.py`).

**Proposed fix**: add `if milestone < 1: self.abort(400, msg='Milestone number
must be >= 1')` after the `is None` guard, or give `get_int_arg` a `min_value`
parameter — which would fix Findings B, C, and E at a single site.

**Severity**: silent-acceptance defect — same `get_int_arg`-admits-`0` class as
Findings B and C, in a fifth endpoint.

---

### Finding F — `metricsdata.py:199` `FeatureHandler.get_template_data` — `?num=0` returns all datapoints (HTTP 200; inverse of B)

**Source**: `api/metricsdata.py:199-212`, `framework/basehandlers.py:182`

```python
num = self.get_int_arg('num')           # admits 0 (rejects only < 0)
if num and not self.should_refresh():   # num=0 is falsy → cache path skipped
    ...
properties = self.fetch_all_datapoints()
if num:                                 # num=0 is falsy → slice skipped
    properties = properties[:num]
return _datapoints_to_json_dicts(properties)   # → returns ALL, HTTP 200
```

`get_int_arg('num')` rejects `< 0` but admits `0`.  The result is then bounded
with `if num:` — a truthiness guard, not a presence guard — so for `num = 0` the
`properties[:num]` slice is skipped and the handler returns the **full** datapoint
set with **HTTP 200**.  This is the mirror image of Finding B (`features` `?num=0`
→ *empty* page): here `?num=0` returns *everything*, so a caller requesting "top 0"
receives the entire dataset.  It combines the `get_int_arg`-admits-`0` class
(B/C/E) with the falsy-guard short-circuit class (`if num:`, the same shape as
Finding D's `if val and …`).

**ESBMC counterexample** (`metricsdata_num_zero_returns_all.py`,
Phase 1 FAILED, 1 VCC):

```
Violated property:
  file metricsdata_num_zero_returns_all.py
  assertion result_len <= num

  num = 0, n_total > 0  (slice skipped; all n_total datapoints returned, HTTP 200)
```

The paired good harness `metricsdata_num_limit_honored.py` models the fix
(`if num is not None:`) and verifies `len(result) <= num` for every admitted
`num >= 0` — SUCCESSFUL in both phases (positive control). Confirmed empirically
under CPython (`reproducer/finding_f_metricsdata_num_zero.py`).

**Proposed fix**: replace `if num:` with `if num is not None:` so a provided
limit (including `0`) always bounds the result.

**Severity**: silent-acceptance defect — same benign class as Finding B (#6442,
closed won't-fix), so **not filed upstream** as a standalone bug.

---

### Finding G — `features_api.py:552` `FeaturesAPI.do_patch` — malformed PATCH body → KeyError → HTTP 500 (not 400)

**Source**: `api/features_api.py:549-557`, `framework/basehandlers.py:285`

```python
body = self.get_json_param_dict()          # {} for missing/invalid JSON
if 'id' not in body['feature_changes']:    # unguarded dict access → KeyError
    self.abort(400, msg='Missing feature ID in feature updates')
...
stage_ids = [s['id'] for s in body['stages'] if 'id' in s]   # sibling KeyError (:567)
```

`get_json_param_dict()` returns the raw request JSON, or `{}` for a
missing/invalid body. `do_patch` then indexes `body['feature_changes']` with no
presence guard, so a `PATCH /api/v0/features/<id>` whose body lacks the
`feature_changes` key — including an empty `{}` — raises `KeyError`.
`APIHandler.patch` (`basehandlers.py:285-289`) calls `do_patch` with **no
`except`**, so the exception propagates to Flask and becomes **HTTP 500** instead
of the HTTP 400 the maintainer's `api/` convention requires.

This is the same bare-exception class as Finding A — the one the maintainer fixed
in [PR #6451](https://github.com/GoogleChrome/chromium-dashboard/pull/6451) —
found by sweeping every `api/` handler for user input that reaches an uncaught
exception. The endpoint requires sign-in + XSRF, so the surface is any
authenticated user. The sibling `body['stages']` access at line 567 is the same
class (KeyError when `stages` is omitted).

**ESBMC counterexample** (`features_patch_missing_feature_changes_http500.py`,
Phase 1 FAILED, 1 VCC):

```
Violated property:
  file features_patch_missing_feature_changes_http500.py
  assertion: missing 'feature_changes' should have been an HTTP 400 abort

  has_feature_changes = 0  (body lacks the key; do_patch raises KeyError → 500)
```

The paired good harness `features_patch_body_shape_validated.py` models the fix
(presence guard before access) and verifies every body shape yields a clean HTTP
code (400 for a malformed body, never an uncaught exception) — SUCCESSFUL in both
phases. Confirmed empirically under CPython
(`reproducer/finding_g_features_patch_missing_key.py`).

**Proposed fix**: `if 'feature_changes' not in body: self.abort(400, msg='Missing
feature_changes')` before the access, and default `body.get('stages', [])` for
the line-567 sibling.

**Severity**: bare-exception → HTTP 500 defect — same class as Finding A
([PR #6451](https://github.com/GoogleChrome/chromium-dashboard/pull/6451)), which
the maintainer accepted and fixed. Filed upstream as
[GoogleChrome/chromium-dashboard#6464](https://github.com/GoogleChrome/chromium-dashboard/issues/6464).

---

### Positive control — `releasenotes_api.py:37-51` `ReleaseNotesL10nAPI.do_get` — milestone-range check done correctly

**Source**: `api/releasenotes_api.py:37-51`

```python
start_milestone = self.get_int_arg('startMilestone')
end_milestone   = self.get_int_arg('endMilestone')
if start_milestone is None: self.abort(400, msg='Missing startMilestone')
if end_milestone   is None: self.abort(400, msg='Missing endMilestone')
if start_milestone <= 0 or end_milestone <= 0:
    self.abort(400, msg='Milestones must be positive integers')
if start_milestone > end_milestone:
    self.abort(400, msg='startMilestone must be <= endMilestone')
```

This is the canonical correct shape of the milestone-range check: it rejects
non-positive milestones **and** the inverted range with a clean `abort(400)` —
exactly the fix proposed for Findings A and C, but already present here.  The
target verifies the postcondition Findings A/C violate: every range that
proceeds (`code == 200`) satisfies `start >= 1`, `end >= 1`, `start <= end`.

**ESBMC verdict** (`releasenotes_milestone_range_validated.py`,
Phase 1 SUCCESSFUL 3 VCCs, Phase 2 SUCCESSFUL 6 VCCs): the gate admits only
well-formed ranges; the postcondition holds.  Because this target shares the
buggy Findings' harness shape but asserts the property they fail, the
SUCCESSFUL verdict confirms the buggy harnesses are non-vacuous (the assertion
is reachable and genuinely discriminating).
