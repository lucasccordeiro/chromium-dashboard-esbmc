# Finding H — upstream issue report (draft)

Ready-to-file GitHub issue for `GoogleChrome/chromium-dashboard`, formatted to the
repository's `bug_report.md` template. Verified against upstream `main` at commit
`3d6ec4bb` (2026-06-04). **Not yet filed.**

- **Title:** `StagesAPI` POST returns HTTP 500 for a malformed `stage_type` (TypeError/KeyError/ValueError)
- **Labels:** `bug`

---

**Describe the bug**

`POST /api/v0/features/<feature_id>/stages` returns **HTTP 500 Internal Server
Error** instead of **HTTP 400 Bad Request** when the JSON body's `stage_type` is
present but not a `{"value": <int>}` object.

`StagesAPI.do_post` (`api/stages_api.py:98-101`) guards only that the key exists,
then converts its nested `value` unconditionally:

```python
body = self.get_json_param_dict()
if 'stage_type' not in body:
    self.abort(400, msg='Stage type not specified.')
stage_type = int(body['stage_type']['value'])   # line 101 — shape/type not validated
```

`int(body['stage_type']['value'])` raises:
- `TypeError` if `body['stage_type']` is not subscriptable by `'value'` (e.g. `{"stage_type": 5}` or `{"stage_type": "x"}`);
- `KeyError` if it is a dict without `value` (e.g. `{"stage_type": {}}`);
- `ValueError` if `value` is a non-numeric string (e.g. `{"stage_type": {"value": "abc"}}`).

`APIHandler.post` (`framework/basehandlers.py:261`) calls `do_post` with no
surrounding `except`, so the exception propagates to Flask as HTTP 500. This
follows the same convention as PR #6451: `api/` code should `self.abort(400, …)`
on bad input.

**To Reproduce**

Steps to reproduce the behavior:
1. As a signed-in user (the endpoint requires sign-in + XSRF) with edit access to
   the feature, send:
   ```
   POST /api/v0/features/123/stages
   Content-Type: application/json

   {"stage_type": {}}
   ```
2. Observe **HTTP 500 Internal Server Error** (a `KeyError: 'value'` traceback)
   instead of HTTP 400. `{"stage_type": 5}` (TypeError) and
   `{"stage_type": {"value": "abc"}}` (ValueError) trigger the same 500.

**Expected behavior**

A malformed `stage_type` should be rejected with **HTTP 400 Bad Request**.

**Additional context**

- Affected code (commit `3d6ec4bb`): `api/stages_api.py:101`;
  `framework/basehandlers.py:261` (`APIHandler.post` has no `except` around
  `do_post`).
- Suggested fix:
  ```python
  st = body['stage_type']
  if not isinstance(st, dict) or 'value' not in st:
      self.abort(400, msg='Invalid stage_type.')
  try:
      stage_type = int(st['value'])
  except (TypeError, ValueError):
      self.abort(400, msg='stage_type value was not an int.')
  ```
- Same class as the `ChannelsAPI` `?start > ?end` → HTTP 500 issue fixed in
  PR #6451 and the `FeaturesAPI` PATCH issue ([#6464](https://github.com/GoogleChrome/chromium-dashboard/issues/6464)).
  Found by sweeping `api/` handlers for user input that reaches an uncaught
  exception; confirmed with a standalone reproducer and an
  [ESBMC](https://github.com/esbmc/esbmc) bounded-model-checking harness.
