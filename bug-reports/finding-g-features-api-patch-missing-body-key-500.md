# Finding G — upstream issue report

**Filed upstream:** [GoogleChrome/chromium-dashboard#6464](https://github.com/GoogleChrome/chromium-dashboard/issues/6464)
(open, 2026-06-03).

GitHub issue text for `GoogleChrome/chromium-dashboard`, formatted to the
repository's `bug_report.md` template. Verified against upstream `main` at commit
`4294104b` (2026-06-03).

- **Title:** `FeaturesAPI` PATCH returns HTTP 500 (KeyError) when the request body omits `feature_changes` or `stages`
- **Labels:** `bug`

---

**Describe the bug**

`PATCH /api/v0/features/<feature_id>` returns **HTTP 500 Internal Server Error**
instead of **HTTP 400 Bad Request** when the JSON request body does not contain
the expected top-level keys.

`FeaturesAPI.do_patch` (`api/features_api.py:549`) reads the body and then indexes
it with no presence guard:

```python
body = self.get_json_param_dict()          # returns {} for a missing/invalid body
if 'id' not in body['feature_changes']:    # line 552 — KeyError if 'feature_changes' is absent
    self.abort(400, msg='Missing feature ID in feature updates')
...
stage_ids = [s['id'] for s in body['stages'] if 'id' in s]   # line 567 — KeyError if 'stages' is absent
```

When `feature_changes` is missing, `body['feature_changes']` raises `KeyError`.
`APIHandler.patch` (`framework/basehandlers.py:285`) calls `do_patch` with no
surrounding `except`, so the exception propagates to Flask and becomes HTTP 500.

This follows the same convention as PR #6451 ("Give 400 for bad channel range."):
code in `api/` should `self.abort(400, …)` on bad user input rather than letting
an exception escape as a 500.

**To Reproduce**

Steps to reproduce the behavior:

1. As a signed-in user (the endpoint requires sign-in + XSRF), send a PATCH with a
   body that omits `feature_changes`:
   ```
   PATCH /api/v0/features/123
   Content-Type: application/json

   {}
   ```
2. Observe **HTTP 500 Internal Server Error** (a `KeyError: 'feature_changes'`
   traceback in the logs) instead of HTTP 400. This path is reached before the
   feature lookup and before permission validation, so any signed-in user can
   trigger it.
3. The `body['stages']` access (line 567) is the same defect, but it is gated: it
   is reached only for a body such as
   `{"feature_changes": {"id": <existing_feature_id>}}` **where the feature exists
   and the caller has edit permission** on it. In that case, omitting `stages`
   yields the same `KeyError` → HTTP 500.

**Expected behavior**

A body missing a required top-level key should be rejected with **HTTP 400 Bad
Request** and a clear message, not produce an HTTP 500.

**Additional context**

- Affected code (commit `4294104b`):
  - `api/features_api.py:552` — `body['feature_changes']` (also `:554`, `:580`)
  - `api/features_api.py:567` / `:570` — `body['stages']`
  - `framework/basehandlers.py:285` — `APIHandler.patch` has no `except` around
    `do_patch`; `get_json_param_dict` (`basehandlers.py:112-114`) returns `{}` for a
    missing/invalid body.
- Suggested fix:
  ```python
  if 'feature_changes' not in body:
      self.abort(400, msg='Missing feature_changes')
  # ...and for the stages access:
  for s in body.get('stages', []):
      ...
  ```
- Same class as the `ChannelsAPI` `?start > ?end` → HTTP 500 issue fixed in
  PR #6451; found by sweeping `api/` handlers for user input that reaches an
  uncaught exception. Confirmed with a minimal standalone reproducer and an
  [ESBMC](https://github.com/esbmc/esbmc) bounded-model-checking harness.
