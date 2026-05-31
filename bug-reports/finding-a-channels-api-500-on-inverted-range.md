**Title:** ChannelsAPI returns HTTP 500 instead of HTTP 400 when ?start > ?end

---

**Describe the bug**

When the `/api/v0/channels` endpoint receives a request where the `start` query
parameter is greater than `end` (e.g. `?start=5&end=3`), the server responds
with **HTTP 500 Internal Server Error** instead of **HTTP 400 Bad Request**.

The root cause is a bare `raise ValueError` at `api/channels_api.py:146` that
is not caught anywhere in the dispatch chain (`APIHandler.get()` in
`framework/basehandlers.py:251` has no `except ValueError` wrapper), so Flask
converts it to a 500.

**To Reproduce**

Steps to reproduce the behavior:

1. Send a GET request to the channels API with an inverted range:
   ```
   GET /api/v0/channels?start=5&end=3
   ```
2. Observe the HTTP response status code — it is 500, not 400.

Minimal standalone reproducer (requires only `flask`):

```python
from flask import Flask
app = Flask(__name__)

@app.route('/api/v0/channels')
def channels_get():
    start, end = 5, 3
    if start > end:
        raise ValueError   # mirrors channels_api.py:146
    return {}

with app.test_client() as client:
    resp = client.get('/api/v0/channels?start=5&end=3')
    print(resp.status_code)   # prints 500
```

**Expected behavior**

The server should return **HTTP 400 Bad Request** with a message such as
`"start must be <= end"`, consistent with how other invalid parameters are
handled via `self.abort(400, ...)`.

**Additional context**

- Affected file: `api/channels_api.py`, line 146.
- The one-line fix is to replace `raise ValueError` with
  `self.abort(400, msg='start must be <= end')`.
- Found by [ESBMC](https://github.com/esbmc/esbmc) v8.3.0 bounded model
  checking on a symbolic harness
  (`harness/channels_start_gt_end_bare_valueerror.py`). ESBMC explored all
  positive integer pairs `(start, end)` with `start > end` and produced the
  following counterexample (2 VCCs, solver: Bitwuzla):

  ```
  State 1  start = 4611686018427387906
  State 2  end   = 2

  Violated property:
    file channels_start_gt_end_bare_valueerror.py line 71 function main
    bare ValueError should have been an HTTP 400 abort

  VERIFICATION FAILED
  ```

  The large `start` value is ESBMC's arbitrary symbolic witness; the property
  fires for any `start > end > 0`. Confirmed empirically with the Flask
  reproducer above.
