# chromium-dashboard / ESBMC-Python PoC — verification roadmap

Companion to [`REPORT.md`](./REPORT.md) (per-target verification record).
This file is the **forward-looking** planning artifact: what targets to add
next, in what order, with what blockers.

Pinned upstream: `GoogleChrome/chromium-dashboard @ d0d21c8` (2026-05-26).
Verifier: ESBMC 8.3.0+ (post-PR #4683, Python `__ESBMC_unreachable` support).

---

## Context and approach

chromium-dashboard is a Google App Engine Python web application that manages
the lifecycle of Chrome platform features (API proposals, origin trials,
shipping decisions, and review gates).  The Python backend has three natural
verification surfaces:

1. **Pure integer / date arithmetic helpers** — SLO weekday counting, latency
   calculations, milestone arithmetic.  These are self-contained functions
   with no I/O or ORM interaction; ESBMC can verify them directly with
   abstract integer inputs.

2. **API input-validation gaps** — HTTP query/JSON parameters accepted by
   `basehandlers.get_int_arg` / `get_int_param` that bypass validation and
   reach downstream arithmetic or logic with unexpected values (same bug class
   as the vLLM CLI-parameter audit that produced eight live findings).

3. **Logic contracts** — Boolean gate-eligibility predicates, SLO state-machine
   invariants, and overdue-detection arithmetic.  Each has a clear precondition
   / postcondition pair that ESBMC can check symbolically.

Each target produces a "good" harness (`SUCCESSFUL`) and a paired "buggy"
harness (`FAILED`).  The buggy harness serves two roles: (a) it proves the
harness is non-vacuous (i.e., the asserted property actually discriminates),
and (b) it is the counterexample that documents the defect when a live bug is
found.

---

## Method

Same two-phase scheme as the vLLM and AWS-Neuron PoCs:

- **Phase 1** — ESBMC's default flags.  Functional contracts via plain
  `assert`.  Verdict `SUCCESSFUL` means all assertions hold on all
  symbolically-explored paths; `FAILED` means ESBMC found a counterexample.
- **Phase 2** — `--overflow-check` appended.  Checks for CWE-190 (integer
  overflow) and CWE-369 (division by zero) on every arithmetic operation.

Each phase run is guarded by a VCC-count check: a `SUCCESSFUL` verdict with
0 VCCs generated is flagged as **vacuous** — the harness never reached any
user-level assertion and provides no real verification value.

External dependencies (Flask request objects, NDB datastore, Redis cache,
HTTP calls) are stubbed with nondet stubs: ESBMC-Python intrinsics
`nondet_int()` and `__ESBMC_assume(...)` constrain symbolic values to the
range that real callers would supply.

---

## Already covered

| Family | Targets | Notes |
|---|---|---|
| Tier 1 — pure arithmetic | `is_weekday`, `weekdays_between_approx`, `weekdays_between_loop`, `remaining_days`, `diff_days_and_weeks` (5 pairs) | All Phase 1 + Phase 2 SUCCESSFUL; buggy variants all FAILED. One harness fix required during run: loop-buggy mutation changed from "drop cap" (structurally undetectable at `calendar_days ≤ 30`) to "init counter=1" (caught at `calendar_days=0`). |
| Tier 2 — API validation | `channels_start_gt_end_bare_valueerror`, `features_num_zero_silent_acceptance`, `channels_milestone_zero_silent_acceptance` | All Phase 1 FAILED as expected — counterexamples are the defect witnesses. Three live bugs confirmed; see REPORT.md Findings A/B/C. |
| Tier 3 — self-certify contracts | `is_privacy_eligible`, `is_testing_eligible`, `is_adoption_eligible`, `is_eligible_dispatch` (4 pairs) | All Phase 1 + Phase 2 SUCCESSFUL; buggy variants all FAILED. Dispatch harness originally required scalar-arg workaround for esbmc/esbmc#5022; restored to list comprehension after upstream fix in esbmc/esbmc#5023 (2026-06-01). |
| Tier 4 — SLO state machine | `record_vote_index_safety`, `record_vote_changed_flag`, `overdue_detection` (3 pairs) | All Phase 1 + Phase 2 SUCCESSFUL; buggy variants all FAILED. Row 12 (`changed`-flag invariant) models the five field-mutation sites of `record_vote`; the buggy variant exercises a spurious `True → False` toggle. |

---

## Tier 1 — Pure date/integer arithmetic helpers

These functions have no I/O or ORM calls; they are self-contained over integer
inputs.  No new stub infrastructure is needed.

| # | Target | Source | Properties | New stubs |
|---|---|---|---|---|
| 1 | `is_weekday` | `internals/slo.py:31` | Returns True iff `weekday ∈ {0,1,2,3,4}` (Mon–Fri); False for Sat–Sun `{5,6}` | Abstract `datetime.weekday()` as nondet int in `[0, 6]` |
| 2 | `weekdays_between` — approx branch | `internals/slo.py:41` | When `calendar_days > MAX_DAYS`: result = `calendar_days * 5 // 7`; result ∈ `[0, calendar_days]` | Abstract dates as nondet int `calendar_days > 30` |
| 3 | `weekdays_between` — loop branch | `internals/slo.py:44` | Loop invariant `0 ≤ weekday_counter ≤ MAX_DAYS`; result bounded by `MAX_DAYS` | Abstract dates as nondet int `0 ≤ calendar_days ≤ 30` |
| 4 | `remaining_days` | `internals/slo.py:65` | `result = slo_limit − weekdays_between(...)`; negative when overdue | Abstract `weekdays_between` result as nondet int in `[0, MAX_DAYS]` |
| 5 | `diff_days` | `internals/ot_process_reminders.py:371` | `(t1 − t2).days` — value can be negative (t1 < t2); floor division `// 7` is safe (7 ≠ 0) | Abstract `(t1 − t2).days` as nondet int |
| 6 | `diff_weeks` | `internals/ot_process_reminders.py:368` | `diff_weeks * 7 ≤ diff_days < (diff_weeks + 1) * 7`; `diff_weeks` can be negative | Same |

Each row ships two `verify.py` targets: `<name>` (SUCCESSFUL) and
`<name>_buggy` (FAILED).  The buggy variant mutations are:
- Row 1: replace `< 5` with `<= 5` (Saturday admitted as weekday).
- Row 2: drop the `> MAX_DAYS` branch check (approximation applied always).
- Row 3: remove the `weekday_counter < MAX_DAYS` loop guard.
- Row 4: negate the subtraction (`weekdays_between + slo_limit`).
- Row 5: use `//` instead of integer subtraction (wrong semantics).
- Row 6: divide by 8 instead of 7.

---

## Tier 2 — API input-validation hunts (live-bug-class targets)

Mirrors the vLLM CLI-parameter audit.  HTTP query-string arguments serve the
same role as vLLM's `--flag <value>`: they are user-controlled integers that
reach arithmetic / logic code with minimal server-side validation.

The key audit surface is `framework/basehandlers.py:get_int_arg`:

```python
def get_int_arg(self, name, default=None) -> int | None:
    val = self.request.args.get(name, default) or default
    if val is None:
        return None
    try:
        num = int(val)
    except ValueError:
        self.abort(400, ...)
    if num < 0:
        self.abort(400, ...)  # rejects negatives
    return num               # ADMITS 0 — no positivity guard
```

`get_int_arg` rejects values `< 0` but **admits `0`** with no error.  The
analogous gap in vLLM (`SkipValidation[int]` fields without `gt=0`) produced
eight live findings.

### Finding A — `ChannelsAPI.do_get`: `start > end` raises bare `ValueError` (HTTP 500 not 400)

**Source**: `api/channels_api.py:146`

```python
if start > end:
    raise ValueError          # bare — not self.abort(400, ...)
```

`APIHandler.get()` (the Flask dispatch shim, `framework/basehandlers.py:251`)
has no `except ValueError` wrapper.  A bare `ValueError` propagates to Flask
and produces an **HTTP 500 Internal Server Error** instead of the clean
**HTTP 400 Bad Request** the caller expects.  The analogous defect in vLLM
is Finding #4 (`BlockPool.__init__` bare `AssertionError`).

**ESBMC harness**: model nondet `start`, `end` with `start > 0, end > 0,
start > end`; assert `response_code == 400`.  The assertion fails →
counterexample names the failing inputs.

**Empirical reproduction**:

```python
from api.channels_api import ChannelsAPI
# Simulate ?start=5&end=3 → start > end → ValueError raised, not self.abort(400)
# Flask catches unhandled ValueError as 500; client sees Internal Server Error.
```

**Proposed fix**: replace `raise ValueError` with `self.abort(400, msg='start must be <= end')`.

**Severity**: UX defect — same class as vLLM #4.

---

### Finding B — `FeaturesAPI.do_search`: `?num=0` silent-acceptance → empty page without 400

**Source**: `api/features_api.py:117`, `framework/basehandlers.py:182`

```python
num = self.get_int_arg('num', search.DEFAULT_RESULTS_PER_PAGE)
# get_int_arg admits 0 (not < 0).
```

With `num=0`, `process_query_using_cache` runs normally, reaches
`sorted_id_list[start : start + 0]` → empty list `[]`, and returns
`{'total_count': N, 'features': []}` with HTTP 200.  The caller requested
0 results per page, got 0 results, and received no signal that the value
was invalid.

Same silent-acceptance pattern as vLLM Findings #5 (`--max-logprobs <negative>`)
and #6 (`--long-prefill-token-threshold <negative>`): a malformed API
parameter is admitted, produces a confusing (here: empty) response, and
the user receives no 400 error.

**ESBMC harness**: model `num = 0`; assert `num > 0` after the acceptance
gate.  The assertion fails → counterexample is the witness.

**Empirical reproduction**:

```python
# Simulate GET /api/v0/features?num=0
# Response: {"total_count": 5000, "features": []}  HTTP 200
# Expected: {"error": "num must be > 0"} HTTP 400
```

**Proposed fix**: add a `> 0` check in `get_int_arg` (or a specific
`if num == 0: self.abort(400, ...)` in `do_search`).

**Severity**: silent-acceptance defect — same class as vLLM #5, #6.

---

### Finding C — `ChannelsAPI.do_get`: `?start=0&end=0` → milestone 0 accepted, null dates

**Source**: `api/channels_api.py:138`

```python
start = self.get_int_arg('start')   # admits 0
end   = self.get_int_arg('end')     # admits 0
```

`get_int_arg` admits 0.  With `start = end = 0`, the `start > end` guard
does not trigger (0 == 0).  `construct_specified_milestones_details(0, 0)`
calls `fetchchannels.fetch_chrome_release_info(0)`, which makes an HTTP
request for milestone 0 — not a real Chrome milestone.  The external API
returns either an error or a record with all dates as `None`.  The server
returns HTTP 200 with null dates.

**ESBMC harness**: model nondet `start`; assert `start > 0` after
the acceptance gate.  Assertion fails → counterexample `start = 0`.

**Proposed fix**: tighten `get_int_arg` callers in `ChannelsAPI.do_get`
to reject 0, or add a `start >= 1` check after the args are parsed.

**Severity**: silent-acceptance defect — same class as vLLM Finding #3.

---

### Summary table — Tier 2

| Finding | Source | Admitted value | Downstream effect | Fix shape |
|---|---|---|---|---|
| A | `channels_api.py:146` | `start > end` | Bare `ValueError` → HTTP 500 | Replace `raise ValueError` with `self.abort(400, ...)` |
| B | `features_api.py:117` | `num=0` | Empty page, HTTP 200, no error signal | `if num == 0: self.abort(400, ...)` or `get_int_arg` positivity guard |
| C | `channels_api.py:138` | `start=0` / `end=0` | Milestone 0 queried; null dates returned | Add `>= 1` check after param parsing |

---

## Tier 3 — Self-certify logic contracts

`internals/self_certify.py` implements a boolean eligibility predicate for
each of three gate families.  The contracts are small, pure boolean functions
with no I/O; ESBMC can exhaustively verify them over symbolic boolean inputs.

| # | Target | Source | Properties | Buggy mutation |
|---|---|---|---|---|
| 7 | `is_privacy_eligible` | `self_certify.py:73` | True iff `explanation AND (language_polyfill OR api_polyfill OR same_origin_css)` | Drop the `explanation` check |
| 8 | `is_testing_eligible` | `self_certify.py:82` | True iff ALL five coverage fields set | Drop one field check |
| 9 | `is_adoption_eligible` | `self_certify.py:93` | True iff ALL four adoption fields set | Drop one field check |
| 10 | `is_eligible` dispatch | `self_certify.py:103` | Gate-type dispatch is complete and routes to the correct predicate for every `gate_type` in `CERTIFIABLE_GATE_TYPES` | Swap privacy → testing check |

Stubs: abstract all `SurveyAnswers` boolean fields as nondet booleans; gate
type as nondet int constrained to the `CERTIFIABLE_GATE_TYPES` set.

---

## Tier 4 — SLO state-machine invariants

| # | Target | Source | Properties |
|---|---|---|---|
| 11 | `record_vote` index safety | `slo.py:73` | `sorted(votes, ...)[-1]` is only reached when `votes` is non-empty (guarded by the `if not votes: return False` early exit) |
| 12 | `record_vote` changed-flag | `slo.py:73` | `changed` is `True` iff at least one gate field was mutated; the flag is monotone within a single call (no spurious `True → False` toggle) |
| 13 | Overdue detection arithmetic | `reminders.py:463` | `initial_remaining == -1` ↔ exactly 1 weekday past deadline (newly overdue); `initial_remaining == -slo_limit` ↔ exactly `slo_limit` weekdays past deadline (long overdue) |

---

## Recommended sequence

1. **Tier 1** in rows 1–6 order — fast wins, each verifiable without stubs,
   establishes `verify.py` + `Makefile` infrastructure, confirms ESBMC-Python
   works on this codebase.
2. **Tier 2 Finding A** — highest severity (HTTP 500 vs 400); smallest harness.
3. **Tier 2 Findings B & C** — silent-acceptance defects; harness shape is
   identical to vLLM Findings #5/#6.
4. **Tier 3** (rows 7–10) — pure boolean, fast to verify, interesting dispatch contract.
5. **Tier 4** (rows 11–13) — state-machine invariants; need minimal Gate/Vote stubs.

---

## Out of scope

- **Flask routing and HTTP protocol layer** — ESBMC-Python models single-threaded
  Python; WSGI dispatch, middleware, and Flask internals are outside scope.
- **NDB datastore queries** — modelled as nondet stubs (symbolic result sets)
  rather than verified for datastore correctness.
- **Redis cache** — modelled as a no-op (cache miss on every symbolic run).
- **External HTTP calls** (`requests.get`, Gemini API, Chromium release schedule
  API) — stubbed to nondet or concrete safe-return values.
- **JavaScript / TypeScript frontend** — ESBMC verifies Python only.
- **Concurrency** — App Engine handles requests sequentially per instance;
  ESBMC-Python models single-threaded execution, which is appropriate here.
