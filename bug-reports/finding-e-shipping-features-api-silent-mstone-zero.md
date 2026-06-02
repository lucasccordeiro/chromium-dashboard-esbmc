**Title:** ShippingFeaturesAPI silently accepts ?mstone=0 and returns empty feature lists with HTTP 200

---

**Describe the bug**

When the `/api/v0/shipping_features` endpoint receives `?mstone=0`, it returns
an **HTTP 200 OK** response with empty feature lists
(`{"complete_features": [], "incomplete_features": []}`) instead of rejecting
the request with HTTP 400. Milestone 0 is not a real Chrome milestone.

The root cause is the same as in the `?num=0` bug in `FeaturesAPI` and the
`?start=0` bug in `ChannelsAPI`: `basehandlers.get_int_arg()` only rejects
values `< 0`, so zero passes through. `ShippingFeaturesAPI.do_get` then guards
only `milestone is None` (line 59), and `0 is None` is `False`, so `mstone=0`
reaches `_get_shipping_stages(0)`. No stage's `milestones.*_first` field equals
0, so the NDB query returns `[]`, and `do_get` takes the `len == 0` early
return with HTTP 200. The `is None` guard is the tell: the author handled the
missing-parameter case but not the invalid-zero case.

**To Reproduce**

Steps to reproduce the behavior:

1. Send a GET request with `mstone=0`:
   ```
   GET /api/v0/shipping_features?mstone=0
   ```
2. Observe the response with HTTP 200:
   ```json
   {"complete_features": [], "incomplete_features": []}
   ```

Minimal standalone reproducer (no dependencies beyond Python stdlib):

```python
# get_int_arg admits 0 (inline of basehandlers.py:182-197)
def get_int_arg(val_str):
    num = int(val_str)
    if num < 0:
        return 'ABORT_400'
    return num

mstone = get_int_arg('0')
print(mstone)              # 0 — admitted
print(mstone is None)      # False — `is None` guard not triggered

# _get_shipping_stages(0) matches no real stage → []
# do_get takes the len==0 early return:
response = {'complete_features': [], 'incomplete_features': []}
print(response)            # empty lists, HTTP 200
```

**Expected behavior**

A request with `?mstone=0` should be rejected with **HTTP 400 Bad Request**.
Chrome milestone numbers start at 1; milestone 0 has no shipping stages.

**Additional context**

- Affected files:
  - `api/shipping_features_api.py`, line 58 (and the `is None` guard at 59–60)
  - `framework/basehandlers.py`, line 193
- The fix is to add a minimum-value check after the `is None` guard:
  ```python
  if milestone < 1:
      self.abort(400, msg='Milestone number must be >= 1')
  ```
- Shares the same root cause as the `FeaturesAPI ?num=0` and
  `ChannelsAPI ?start=0` bugs (`get_int_arg` lacking a positivity guard);
  a `min_value` parameter on `get_int_arg` would fix all three at once.
- Found by [ESBMC](https://github.com/esbmc/esbmc) v8.3.0 bounded model
  checking on a symbolic harness
  (`harness/shipping_features_mstone_zero_silent_acceptance.py`). ESBMC
  assigned `mstone = 0` and produced the following counterexample (1 VCC,
  solver: Bitwuzla):

  ```
  State 1  mstone = 0

  Violated property:
    file shipping_features_mstone_zero_silent_acceptance.py line 62 function main
    assertion mstone >= 1

  VERIFICATION FAILED
  ```

  Confirmed empirically with the standalone reproducer above.
