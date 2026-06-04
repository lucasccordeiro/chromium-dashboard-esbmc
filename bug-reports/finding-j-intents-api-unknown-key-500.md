# Finding J — upstream issue report (draft)

Ready-to-file GitHub issue for `GoogleChrome/chromium-dashboard`, formatted to the
repository's `bug_report.md` template. Verified against upstream `main` at commit
`3d6ec4bb` (2026-06-04). **Not yet filed.**

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

So any extra key raises `TypeError: __init__() got an unexpected keyword argument
'<key>'`. `APIHandler.post` (`framework/basehandlers.py:261`) has no `except`
around `do_post`, so the `TypeError` propagates to Flask as HTTP 500.

**To Reproduce**

Steps to reproduce the behavior:
1. As a signed-in user (the endpoint requires sign-in + XSRF) with edit access,
   send a body with an unexpected key:
   ```
   POST /api/v0/features/1/2/intent
   Content-Type: application/json

   {"gate_id": 3, "bogus": 1}
   ```
2. Observe **HTTP 500 Internal Server Error** (a `TypeError: __init__() got an
   unexpected keyword argument 'bogus'` traceback) instead of HTTP 400.

**Expected behavior**

An unexpected body key should be ignored or rejected with **HTTP 400 Bad
Request**, not produce an HTTP 500.

**Additional context**

- Affected code (commit `3d6ec4bb`): `api/intents_api.py:176`;
  `framework/basehandlers.py:261` (`APIHandler.post` has no `except`).
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
