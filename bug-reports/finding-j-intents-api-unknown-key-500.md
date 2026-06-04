# Finding J — upstream issue report (draft)

Ready-to-file GitHub issue for `GoogleChrome/chromium-dashboard`, formatted to the
repository's `bug_report.md` template. Verified against upstream `main` at commit
`3d6ec4bb` (2026-06-04). **Filed as [#6469](https://github.com/GoogleChrome/chromium-dashboard/issues/6469).**

- **Title:** `IntentsAPI` POST returns HTTP 500 (TypeError) for any unexpected key in the JSON body
- **Labels:** `bug`

---

**Describe the bug**

`POST /api/v0/features/<feature_id>/<stage_id>/intent` returns **HTTP 500 Internal
Server Error** instead of **HTTP 400 Bad Request** when the JSON body contains any
key other than `gate_id` / `intent_cc_emails`.

`IntentsAPI.do_post` (`api/intents_api.py:176`) splats the raw request JSON into
the generated model constructor:

```python
parsed_args = PostIntentRequest(**self.request.get_json())
```

`PostIntentRequest.__init__` (in `chromestatus_openapi`) accepts only:

```python
def __init__(self, gate_id=None, intent_cc_emails=None):
    ...
```

So any extra key raises `TypeError: PostIntentRequest.__init__() got an unexpected
keyword argument '<key>'` (the runtime is Python 3.13, which qualifies the name).
`APIHandler.post` (`framework/basehandlers.py:261`) has no `except`
around `do_post`, so the `TypeError` propagates to Flask as HTTP 500.

**To Reproduce**

Steps to reproduce the behavior:
1. As a signed-in user (the endpoint requires sign-in + XSRF) with edit access to
   the feature, POST to a stage that supports intent drafting (an Intent-Draft
   stage type — otherwise the request `400`s before reaching the crash; see
   Additional context), with a body containing an unexpected key:
   ```
   POST /api/v0/features/<feature_id>/<stage_id>/intent
   Content-Type: application/json

   {"gate_id": 3, "bogus": 1}
   ```
2. Observe **HTTP 500 Internal Server Error** (a `TypeError:
   PostIntentRequest.__init__() got an unexpected keyword argument 'bogus'`
   traceback) instead of HTTP 400.

**Expected behavior**

An unexpected body key should be ignored or rejected with **HTTP 400 Bad
Request**, not produce an HTTP 500.

**Additional context**

- Affected code (commit `3d6ec4bb`): `api/intents_api.py:176`;
  `framework/basehandlers.py:261` (`APIHandler.post` has no `except`).
- Reachability: line 176 is reached only after `do_post` validates the feature
  (line 148), the stage and that it belongs to the feature (154-156), that the
  stage type supports intent drafting (163-167, else `abort(400)`), and the
  user's edit permission (170-172). So the trigger requires an intent-supporting
  stage and edit access — but once there, the extra-key `TypeError` fires for any
  malformed body.
- Suggested fix — use the tolerant deserializer and convert residual errors:
  ```python
  try:
      parsed_args = PostIntentRequest.from_dict(self.request.get_json() or {})
  except (TypeError, ValueError) as e:
      self.abort(400, msg=str(e))
  ```
  (`from_dict` ignores unknown keys; the `or {}` also guards a null/empty body.)
- Same uncaught-exception → HTTP 500 class as PR #6451 and
  [#6464](https://github.com/GoogleChrome/chromium-dashboard/issues/6464); found by
  sweeping `api/` handlers for user input that reaches an uncaught exception.
  Confirmed with a standalone reproducer and an
  [ESBMC](https://github.com/esbmc/esbmc) bounded-model-checking harness.
