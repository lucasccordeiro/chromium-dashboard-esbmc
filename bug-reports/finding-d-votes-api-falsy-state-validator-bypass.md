**Title:** VotesAPI returns HTTP 500 for a falsy `state` (0 or false) — get_param/get_int_param skip validation, set_vote raises a bare ValueError

---

**Describe the bug**

Submitting a vote (as an authenticated approver) with a **falsy** `state` value
(JSON `0` or `false`) causes an **HTTP 500 Internal Server Error** instead of a
clean **HTTP 400 Bad Request**.

`VotesAPI.do_post` parses the vote state with a validator
(`api/reviews_api.py:78`):

```python
new_state = self.get_int_param('state', validator=Vote.is_valid_state)
```

`Vote.is_valid_state(s)` returns `s in Vote.VOTE_VALUES`, whose keys are the
valid vote states `1..11` (`internals/review_models.py:172-174`); `0` is not a
valid vote state (`PREPARING = 0` is marked "Not used", `review_models.py:96`).

The intent is to reject any invalid `state` with HTTP 400 at the API boundary.
But both `get_param` and `get_int_param` guard their checks with a
`val and ...` short-circuit, so a **falsy** value bypasses validation entirely
(`framework/basehandlers.py`):

```python
# get_param (line 124)
if val and validator and not validator(val):   # falsy val -> validator skipped
    self.abort(400, ...)
# get_int_param (line 141)
if val and type(val) != int:                   # falsy val -> type check skipped
    self.abort(400, ...)
```

With `{"state": 0}`, `val = 0` is falsy: `Vote.is_valid_state` is never called
and the int type check is skipped, so the invalid `0` is returned. It then
passes `require_permissions` and `check_voting_rules` (for a user who is an
approver) and reaches `approval_defs.set_vote`, which re-validates and raises a
**bare** `ValueError` (`internals/approval_defs.py:466-467`):

```python
if not Vote.is_valid_state(new_state):
    raise ValueError('Invalid approval state')
```

Because the raise is bare (not `self.abort(400, ...)`) and `APIHandler.post`
has no `except ValueError` (`framework/basehandlers.py:275`), the exception
propagates to Flask as **HTTP 500**.

So the invalid value is *not* recorded — the `set_vote` guard backstops it — but
the caller receives a 500 instead of a 400. This is the same bare-raise → 500
mechanism as the `ChannelsAPI` `start > end` defect reported in
[#6441](https://github.com/GoogleChrome/chromium-dashboard/issues/6441).

**To Reproduce**

1. As an authenticated approver for a gate, POST a vote with `state` set to `0`:
   ```
   POST /api/v0/votes/<feature_id>/<gate_id>
   {"state": 0}
   ```
2. Observe **HTTP 500 Internal Server Error** (expected: HTTP 400).
   `{"state": false}` behaves identically.

Minimal standalone reproducer (no Flask/NDB — inlines the exact upstream logic
across `get_param`, `get_int_param`, and `set_vote`),
`reproducer/finding_d_state_validator_bypass.py`:

```python
VOTE_VALUES = {i: f'state_{i}' for i in range(1, 12)}   # valid states 1..11

def is_valid_state(s):
    return s in VOTE_VALUES

def get_param(body, name, required=True, validator=None):
    val = body.get(name)
    if required and val is None:
        raise Abort400('Missing %r' % name)
    if val and validator and not validator(val):   # :124 falsy val skips validator
        raise Abort400('Invalid %r' % name)
    return val

def get_int_param(body, name, validator=None):
    val = get_param(body, name, validator=validator)
    if val and type(val) != int:                    # :141 falsy val skips type check
        raise Abort400('%r not an int' % name)
    return val

def set_vote(new_state):                            # approval_defs.py:466-467
    if not is_valid_state(new_state):
        raise ValueError('Invalid approval state')  # bare raise -> HTTP 500
```

Output:

```
OK:  state=5  -> HTTP 200 (recorded)
BUG: state=0 -> helper accepts it, set_vote raises bare ValueError -> HTTP 500 (expected 400)
BUG: state=False -> helper accepts it, set_vote raises bare ValueError -> HTTP 500 (expected 400)
OK:  state=99 -> HTTP 400 (rejected at API boundary)
```

The non-falsy invalid value `99` is rejected cleanly with HTTP 400, confirming
the gap is specific to falsy values.

**Expected behavior**

A `state` that is not in `Vote.VOTE_VALUES` (including `0` and `false`) should be
rejected with **HTTP 400 Bad Request**. Validators and the int type check must
run for every present value, not only truthy ones.

**Additional context**

- Affected files:
  - `framework/basehandlers.py:124` (`get_param`) and `:141` (`get_int_param`)
  - `api/reviews_api.py:78` (`VotesAPI.do_post`)
  - `internals/approval_defs.py:466-467` (`set_vote` bare `raise ValueError`)
- Primary fix — test for presence rather than truthiness so falsy invalid
  values are rejected at the boundary:
  ```python
  # get_param
  if val is not None and validator and not validator(val):
      self.abort(400, ...)
  # get_int_param
  if val is not None and type(val) != int:
      self.abort(400, ...)
  ```
  (`get_param`'s `allowed` guard on line 126 has the same `val and ...` flaw.)
- Defense-in-depth: `set_vote` should `self.abort(400, ...)` (or callers should
  catch `ValueError`) rather than letting a bare `ValueError` become an HTTP 500
  — same remediation as
  [#6441](https://github.com/GoogleChrome/chromium-dashboard/issues/6441).
- Found by [ESBMC](https://github.com/esbmc/esbmc) v8.3.0 bounded model
  checking on a symbolic harness
  (`harness/votes_state_zero_validator_bypass.py`), which models the
  `get_param`/`get_int_param` acceptance gate. ESBMC assigned `state = 0` and
  produced the following counterexample (1 VCC, solver: Bitwuzla):

  ```
  State 1  state = 0

  Violated property:
    file votes_state_zero_validator_bypass.py line 90 function main
    assertion is_valid_state(state)

  VERIFICATION FAILED
  ```

  (The source assertion at line 90 is `assert is_valid_state(state)`.)
  Confirmed empirically with the standalone reproducer above.
