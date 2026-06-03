**Title:** FeaturesAPI.do_patch returns HTTP 500 (KeyError) for a PATCH body missing `feature_changes`

---

**Describe the bug**

`PATCH /api/v0/features/<feature_id>` returns **HTTP 500 Internal Server Error**
instead of **HTTP 400 Bad Request** when the request body omits the
`feature_changes` key (for example, an empty body `{}`).

`FeaturesAPI.do_patch` (`api/features_api.py:549-552`) reads the body and then
indexes `body['feature_changes']` with no presence guard:

```python
body = self.get_json_param_dict()          # returns {} for a missing/invalid body
if 'id' not in body['feature_changes']:    # KeyError when 'feature_changes' is absent
    self.abort(400, msg='Missing feature ID in feature updates')
```

When `feature_changes` is absent, `body['feature_changes']` raises `KeyError`.
`APIHandler.patch` (`framework/basehandlers.py:285-289`) calls `do_patch` with no
surrounding `except`, so the exception propagates to Flask and becomes HTTP 500.

This matches the convention established in PR #6451 ("Give 400 for bad channel
range."): code in `api/` should call `self.abort(400, "...")` on bad user input
rather than letting an exception escape as a 500.

The sibling access `body['stages']` at `api/features_api.py:567` has the same
problem (a body that includes `feature_changes` but omits `stages`).

**To Reproduce**

1. As a signed-in user (the endpoint requires sign-in + XSRF), send:
   ```
   PATCH /api/v0/features/123
   Content-Type: application/json

   {}
   ```
2. Observe **HTTP 500 Internal Server Error** (a `KeyError: 'feature_changes'`
   traceback) instead of HTTP 400.

Minimal standalone reproducer (no dependencies beyond Python stdlib):

```python
def get_json_param_dict(raw_json):
    return raw_json or {}

def do_patch(raw_json):
    body = get_json_param_dict(raw_json)
    if 'id' not in body['feature_changes']:   # KeyError if key absent
        return 400
    return 200

do_patch({})   # raises KeyError('feature_changes') -> HTTP 500
```

**Expected behavior**

A body missing `feature_changes` should be rejected with **HTTP 400 Bad Request**
and a clear message, not produce an HTTP 500.

**Additional context**

- Affected files:
  - `api/features_api.py`, line 552 (`body['feature_changes']`) and line 567
    (`body['stages']`)
  - `framework/basehandlers.py`, line 285 (`APIHandler.patch` has no `except`
    around `do_patch`)
- Suggested fix:
  ```python
  if 'feature_changes' not in body:
      self.abort(400, msg='Missing feature_changes')
  # ... and for the stages access:
  for s in body.get('stages', []):
      ...
  ```
- Same class as the `ChannelsAPI` `?start > ?end` → HTTP 500 issue fixed in
  PR #6451; found by sweeping `api/` handlers for user input that reaches an
  uncaught exception.
- Found by [ESBMC](https://github.com/esbmc/esbmc) v8.3.0 bounded model checking
  on a symbolic harness
  (`harness/features_patch_missing_feature_changes_http500.py`). ESBMC modelled
  the body-shape gate and produced a counterexample on the missing-key path
  (1 VCC, solver: Bitwuzla):

  ```
  State 1  has_feature_changes = 0

  Violated property:
    file features_patch_missing_feature_changes_http500.py function main
    assertion: missing 'feature_changes' should have been an HTTP 400 abort

  VERIFICATION FAILED
  ```

  Confirmed empirically with the standalone reproducer above.
