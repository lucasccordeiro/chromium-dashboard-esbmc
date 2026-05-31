**Title:** ChannelsAPI silently accepts ?start=0 / ?end=0 and returns null milestone data with HTTP 200

---

**Describe the bug**

When the `/api/v0/channels` endpoint receives `?start=0` or `?end=0`, it
returns an **HTTP 200 OK** response containing null dates
(`stable_date: null`, `earliest_beta: null`, etc.) instead of rejecting the
request with HTTP 400. Milestone 0 is not a real Chrome milestone.

The root cause is the same as in the `?num=0` bug in `FeaturesAPI`:
`basehandlers.get_int_arg()` only rejects values `< 0`, so zero passes through.
The `start > end` guard at line 146 does not fire for `start = end = 0`.
`construct_specified_milestones_details(0, 0)` then calls
`fetch_chrome_release_info(0)`, which returns placeholder null data.

**To Reproduce**

Steps to reproduce the behavior:

1. Send a GET request with `start=0` and `end=0`:
   ```
   GET /api/v0/channels?start=0&end=0
   ```
2. Observe the response with HTTP 200:
   ```json
   {"0": {"stable_date": null, "earliest_beta": null, "latest_beta": null,
          "mstone": 0, "version": 0}}
   ```

Minimal standalone reproducer (no dependencies beyond Python stdlib):

```python
# get_int_arg admits 0 (inline of basehandlers.py:182-197)
def get_int_arg(val_str):
    val = val_str
    num = int(val)
    if num < 0:
        return 'ABORT_400'
    return num

start, end = get_int_arg('0'), get_int_arg('0')
print(start, end)           # 0 0 — both admitted
print(start > end)          # False — guard not triggered

# fetch_chrome_release_info fallback for mstone=0 (fetchchannels.py:144-151)
response = {0: {'stable_date': None, 'earliest_beta': None,
                'latest_beta': None, 'mstone': 0, 'version': 0}}
print(response)             # null dates, HTTP 200
```

**Expected behavior**

A request with `?start=0` or `?end=0` should be rejected with **HTTP 400 Bad
Request**. Chrome milestone numbers start at 1; milestone 0 has no schedule
data.

**Additional context**

- Affected files:
  - `api/channels_api.py`, lines 138–139
  - `framework/basehandlers.py`, line 193
- The fix is to add a minimum-value check after the `get_int_arg` calls:
  ```python
  if start < 1 or end < 1:
      self.abort(400, msg='Milestone numbers must be >= 1')
  ```
- Shares the same root cause as the `FeaturesAPI ?num=0` bug
  (`get_int_arg` lacking a positivity guard); could be filed as a single issue.
- Found by [ESBMC](https://github.com/esbmc/esbmc) v8.3.0 bounded model
  checking on a symbolic harness
  (`harness/channels_milestone_zero_silent_acceptance.py`). ESBMC assigned
  `start = 0` and produced the following counterexample (1 VCC, solver: Bitwuzla):

  ```
  State 1  start = 0

  Violated property:
    file channels_milestone_zero_silent_acceptance.py line 55 function main
    assertion start >= 1

  VERIFICATION FAILED
  ```

  Confirmed empirically with the standalone reproducer above.
