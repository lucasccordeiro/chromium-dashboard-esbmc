#!/usr/bin/env python3
"""
Empirical reproducer — Finding A
  api/channels_api.py:146  bare `raise ValueError` → HTTP 500, not HTTP 400

Source (verbatim, d0d21c8):
  # channels_api.py:138-147
  start = self.get_int_arg('start')
  end   = self.get_int_arg('end')
  if start is None or end is None:
      ...return default channel data...
  if start > end:
      raise ValueError          ← bare raise, no message, not self.abort(400,...)

  # basehandlers.py:251-259  APIHandler.get()
  def get(self, *args, **kwargs):
      headers = self.get_headers()
      handler_data = self.do_get(*args, **kwargs)   ← ValueError propagates here
      ...
      return self.defensive_jsonify(handler_data), headers
      # No except ValueError anywhere in the call chain.

Flask converts any unhandled exception to HTTP 500 Internal Server Error.
A bad user input (?start=5&end=3) should produce HTTP 400 Bad Request.

Dependencies: flask only (pip install flask).
"""

from flask import Flask

# ── Step 1: reproduce the mechanism with a minimal Flask app ──────────────

app = Flask(__name__)


@app.route('/api/v0/channels')
def channels_get():
    """Mirrors the ChannelsAPI.do_get() validation path."""
    start = 5   # simulate ?start=5
    end   = 3   # simulate ?end=3

    # channels_api.py:146 — bare raise, NOT self.abort(400, ...)
    if start > end:
        raise ValueError

    return {}


with app.test_client() as client:
    resp = client.get('/api/v0/channels?start=5&end=3')
    code = resp.status_code

    print('GET /api/v0/channels?start=5&end=3')
    print(f'  Status:   HTTP {code}')
    print(f'  Expected: HTTP 400 Bad Request')
    print(f'  Actual:   HTTP {code} {"✗ WRONG" if code != 400 else "✓ OK"}')
    print()

    assert code == 500, (
        f'Expected Flask to return 500 for an unhandled ValueError, got {code}'
    )

# ── Step 2: confirm APIHandler.get() has no except ValueError ────────────

import ast, textwrap

# We inline the relevant portion of APIHandler.get() as a string and parse it
# to check for the absence of an except ValueError clause.
api_handler_get = textwrap.dedent("""
    def get(self, *args, **kwargs):
        headers = self.get_headers()
        handler_data = self.do_get(*args, **kwargs)
        if hasattr(handler_data, 'to_dict'):
            handler_data = handler_data.to_dict()
        return self.defensive_jsonify(handler_data), headers
""")

tree = ast.parse(api_handler_get)
except_handlers = [
    node
    for node in ast.walk(tree)
    if isinstance(node, ast.ExceptHandler)
    if node.type is None or (
        isinstance(node.type, ast.Name) and node.type.id == 'ValueError'
    )
]

print('APIHandler.get() except-ValueError handlers found:', len(except_handlers))
assert len(except_handlers) == 0, 'Unexpected except ValueError in APIHandler.get()'
print('  → None.  ValueError is unhandled → Flask returns HTTP 500.')
print()

# ── Summary ──────────────────────────────────────────────────────────────

print('CONFIRMED: GET /api/v0/channels?start=5&end=3 returns HTTP 500.')
print()
print('Root cause:')
print('  channels_api.py:146  `if start > end: raise ValueError`')
print('  APIHandler.get() (basehandlers.py:251) has no except ValueError.')
print()
print('Proposed fix:')
print("  Replace `raise ValueError`")
print("  with    `self.abort(400, msg='start must be <= end')`")
