**Title:** FeaturesAPI silently accepts ?num=0 and returns empty results with HTTP 200

---

**Describe the bug**

When the `/api/v0/features` search endpoint receives `?num=0`, it returns an
**HTTP 200 OK** response with `features: []` and a non-zero `total_count`,
instead of rejecting the request with HTTP 400. The caller receives no signal
that the parameter value was invalid.

The root cause is that `basehandlers.get_int_arg()` only rejects values `< 0`;
zero passes through. `process_query_using_cache` then runs with `num=0`,
computes `sorted_id_list[start : start + 0] = []`, and returns the empty page.

**To Reproduce**

Steps to reproduce the behavior:

1. Send a GET request to the features API with `num=0`:
   ```
   GET /api/v0/features?num=0
   ```
2. Observe the response: `{"total_count": <N>, "features": []}` with HTTP 200.

Minimal standalone reproducer (no dependencies beyond Python stdlib):

```python
# Inline of basehandlers.py:182-197
def get_int_arg(val_str, default=None):
    val = val_str or default
    if val is None:
        return None
    try:
        num = int(val)
    except ValueError:
        return 'ABORT_400'
    if num < 0:
        return 'ABORT_400'
    return num          # 0 passes through

print(get_int_arg('0', default=100))   # prints 0 — admitted, no error

# Downstream pagination (search.py:471)
num = min(0, 1000)                     # = 0
page = list(range(5000))[0 : 0 + num] # = []
print({'total_count': 5000, 'features': page})
# → {'total_count': 5000, 'features': []}  HTTP 200
```

**Expected behavior**

A request with `?num=0` should be rejected with **HTTP 400 Bad Request**. The
number of results per page must be a positive integer; zero is not a meaningful
page size.

**Additional context**

- Affected files:
  - `api/features_api.py`, line 117
  - `framework/basehandlers.py`, line 193
- The fix is to add a positivity check after the `get_int_arg` call in
  `features_api.py`:
  ```python
  if num == 0:
      self.abort(400, msg='num must be a positive integer')
  ```
- Alternatively, `get_int_arg` could accept an optional `min_val` argument.
- Note: `?num=-1` is already correctly rejected (HTTP 400); only zero is missed.
- Found by [ESBMC](https://github.com/esbmc/esbmc) v8.3.0 bounded model
  checking on a symbolic harness
  (`harness/features_num_zero_silent_acceptance.py`). ESBMC assigned `num = 0`
  and produced the following counterexample (1 VCC, solver: Bitwuzla):

  ```
  State 1  num = 0

  Violated property:
    file features_num_zero_silent_acceptance.py line 61 function main
    assertion num > 0

  VERIFICATION FAILED
  ```

  Confirmed empirically with the standalone reproducer above.
