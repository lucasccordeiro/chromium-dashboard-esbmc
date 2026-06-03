**Title:** FeatureHandler (metricsdata) silently accepts ?num=0 and returns all datapoints with HTTP 200

> **Note:** This is the same benign `get_int_arg`-admits-`0` class as the
> `FeaturesAPI ?num=0` report ([#6442](https://github.com/GoogleChrome/chromium-dashboard/issues/6442)),
> which was **closed won't-fix** ("returns a well-defined result, no harm"). It
> is recorded here for completeness but is **not filed upstream** as a standalone
> issue, since the maintainer's #6442 rationale applies equally.

---

**Describe the bug**

When a feature-metrics endpoint backed by `FeatureHandler.get_template_data`
(`api/metricsdata.py:199`) receives `?num=0`, it returns **HTTP 200 OK** with the
**entire** datapoint set instead of an empty "top-0" list (or HTTP 400). A caller
requesting the top 0 properties receives every property.

The root cause is twofold:
1. `basehandlers.get_int_arg()` only rejects values `< 0`, so `0` passes through.
2. `get_template_data` bounds the result with `if num:` — a truthiness guard, not
   a presence guard. For `num = 0` the guard is falsy, so the
   `properties = properties[:num]` slice is skipped and `fetch_all_datapoints()`'s
   full result is returned.

This is the mirror image of the `FeaturesAPI ?num=0` bug: there `?num=0` yields an
*empty* page; here it yields *everything*. It also shares the falsy-guard
short-circuit shape of the `VotesAPI` `state=0` bug (`if val and …`).

**To Reproduce**

1. Send a GET request with `num=0` to a `FeatureHandler`-backed metrics endpoint:
   ```
   GET /api/v0/data/featurepopularity?num=0
   ```
2. Observe an HTTP 200 response containing **all** datapoints rather than the
   requested top-0 (empty) list.

Minimal standalone reproducer (no dependencies beyond Python stdlib):

```python
# get_int_arg admits 0 (inline of basehandlers.py:182-197)
def get_int_arg(val_str):
    num = int(val_str)
    if num < 0:
        return 'ABORT_400'
    return num

def get_template_data(num_arg, all_datapoints):
    num = get_int_arg(num_arg)        # 0 — admitted
    properties = list(all_datapoints)
    if num:                           # 0 is falsy → slice skipped
        properties = properties[:num]
    return properties

print(get_template_data('0', ['a', 'b', 'c']))   # ['a', 'b', 'c'] — all, not []
```

**Expected behavior**

`?num=0` should either return an empty top-0 list or be rejected with HTTP 400 —
not the full dataset. A provided page-size limit should bound the response.

**Additional context**

- Affected files:
  - `api/metricsdata.py`, lines 199–212 (`FeatureHandler.get_template_data`)
  - `framework/basehandlers.py`, line 193 (`get_int_arg` admits 0)
- The fix is to bound the result with a presence guard rather than a truthiness
  guard:
  ```python
  if num is not None:
      properties = properties[:num]
  ```
  (The earlier `if num and not self.should_refresh():` cache guard has the same
  `num=0` blind spot.)
- Shares the same root cause as the `FeaturesAPI ?num=0` ([#6442](https://github.com/GoogleChrome/chromium-dashboard/issues/6442))
  and `ChannelsAPI ?start=0` ([#6443](https://github.com/GoogleChrome/chromium-dashboard/issues/6443))
  bugs; a `min_value` parameter on `get_int_arg` would address the class.
- Found by [ESBMC](https://github.com/esbmc/esbmc) v8.3.0 bounded model checking
  on a symbolic harness (`harness/metricsdata_num_zero_returns_all.py`). ESBMC
  assigned `num = 0`, `n_total > 0` and produced the following counterexample
  (1 VCC, solver: Bitwuzla):

  ```
  State 1  num = 0, n_total = 1

  Violated property:
    file metricsdata_num_zero_returns_all.py function main
    assertion result_len <= num

  VERIFICATION FAILED
  ```

  Confirmed empirically with the standalone reproducer above.
