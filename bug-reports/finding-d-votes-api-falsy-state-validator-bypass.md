**Title:** VotesAPI accepts an invalid vote state of 0 (or false) — get_param/get_int_param skip validation for falsy values

---

**Describe the bug**

`VotesAPI.do_post` reads the vote state with a validator:

```python
new_state = self.get_int_param('state', validator=Vote.is_valid_state)
```

`Vote.is_valid_state(s)` returns `s in Vote.VOTE_VALUES`, whose keys are the
valid vote states `1..11`. State `0` is **not** a valid vote state (it equals
`Gate.PREPARING`).

However, both `get_param` and `get_int_param` guard their validation with a
`val and ...` short-circuit, so **falsy** values bypass validation entirely:

```python
# framework/basehandlers.py
def get_param(self, name, default=None, required=True, validator=None, allowed=None):
    ...
    if val and validator and not validator(val):   # falsy val -> validator skipped
        self.abort(400, ...)
    ...
    return val

def get_int_param(self, name, ..., validator=None, ...):
    val = self.get_param(name, ..., validator=validator, ...)
    if val and type(val) != int:                    # falsy val -> type check skipped
        self.abort(400, ...)
    return val
```

With a JSON body `{"state": 0}`, `val = 0` is falsy: the `Vote.is_valid_state`
validator is never called and the int type check is skipped. The invalid state
`0` is returned and flows into `approval_defs.set_vote(...)`, recording a
malformed vote state. A body `{"state": false}` behaves the same way and even
returns a Python `bool` where an `int` is expected.

**To Reproduce**

1. POST a vote with `state` set to `0`:
   ```
   POST /api/v0/votes/<feature_id>/<gate_id>
   {"state": 0}
   ```
2. The request is accepted instead of being rejected with HTTP 400, and an
   invalid vote state is recorded.

Minimal standalone reproducer (no Flask/NDB needed — inlines the exact upstream
logic), `reproducer/finding_d_state_validator_bypass.py`:

```python
VOTE_VALUES = {i: f'state_{i}' for i in range(1, 12)}  # valid states 1..11

def is_valid_state(s):
    return s in VOTE_VALUES

def get_param(body, name, required=True, validator=None):
    val = body.get(name)
    if required and val is None:
        raise Abort400('Missing %r' % name)
    if val and validator and not validator(val):   # falsy val skips validator
        raise Abort400('Invalid %r' % name)
    return val

def get_int_param(body, name, validator=None):
    val = get_param(body, name, validator=validator)
    if val and type(val) != int:                    # falsy val skips type check
        raise Abort400('%r not an int' % name)
    return val

get_int_param({'state': 0}, 'state', validator=is_valid_state)      # returns 0
get_int_param({'state': False}, 'state', validator=is_valid_state)  # returns False
get_int_param({'state': 99}, 'state', validator=is_valid_state)     # correctly aborts
```

Output:

```
BUG: state=0 accepted; is_valid_state(0) = False
BUG: state=false accepted; type = bool is_valid_state = False
OK: state=99 correctly rejected -> Invalid value for parameter 'state'
```

The non-falsy invalid value `99` is correctly rejected, confirming the gap is
specific to falsy values.

**Expected behavior**

A `state` that is not in `Vote.VOTE_VALUES` (including `0` and `false`) should
be rejected with **HTTP 400 Bad Request**. Validators and the int type check
must run for every present value, not only truthy ones.

**Additional context**

- Affected files:
  - `api/reviews_api.py` (`VotesAPI.do_post`)
  - `framework/basehandlers.py` (`get_param`, `get_int_param`)
- The fix is to test for presence rather than truthiness:
  ```python
  # get_param
  if val is not None and validator and not validator(val):
      self.abort(400, ...)
  # get_int_param
  if val is not None and type(val) != int:
      self.abort(400, ...)
  ```
  (`get_param`'s `allowed` guard has the same `val and ...` short-circuit and
  should be fixed the same way.)
- Found by [ESBMC](https://github.com/esbmc/esbmc) v8.3.0 bounded model
  checking on a symbolic harness
  (`harness/votes_state_zero_validator_bypass.py`). ESBMC assigned `state = 0`
  and produced the following counterexample (1 VCC, solver: Bitwuzla):

  ```
  State 1  state = 0

  Violated property:
    file votes_state_zero_validator_bypass.py line 85 function main
    assertion is_valid_state(state)

  VERIFICATION FAILED
  ```

  Confirmed empirically with the standalone reproducer above.
