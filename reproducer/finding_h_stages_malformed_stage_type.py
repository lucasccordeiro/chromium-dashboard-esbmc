#!/usr/bin/env python3
"""
Empirical reproducer — Finding H
  api/stages_api.py:101  StagesAPI.do_post
  int(body['stage_type']['value']) is reached after a presence-only guard, so a
  malformed `stage_type` raises TypeError/KeyError/ValueError → HTTP 500.

Source (verbatim, GoogleChrome/chromium-dashboard @ 4294104b):
  # api/stages_api.py:98-101
  body = self.get_json_param_dict()
  if 'stage_type' not in body:
      self.abort(400, msg='Stage type not specified.')
  stage_type = int(body['stage_type']['value'])   ← shape/type NOT validated

Dependencies: none (pure Python stdlib).
"""

def do_post(body):
    """Inline of stages_api.py:98-101 (current code)."""
    if 'stage_type' not in body:
        return 400, 'Stage type not specified.'
    stage_type = int(body['stage_type']['value'])   # raises on malformed input
    return 200, stage_type


# Three malformed bodies that all pass the presence guard but crash the int():
cases = [
    ('{"stage_type": 5}',            {'stage_type': 5}),            # TypeError
    ('{"stage_type": {}}',           {'stage_type': {}}),           # KeyError
    ('{"stage_type": {"value": "abc"}}', {'stage_type': {'value': 'abc'}}),  # ValueError
]
for label, body in cases:
    try:
        do_post(body)
        raise AssertionError(f'expected an exception for {label}')
    except (TypeError, KeyError, ValueError) as e:
        print(f'do_post({label}) -> {type(e).__name__} -> propagates as HTTP 500')
print()

# Contrast — the fixed handler returns a clean 400.
def do_post_fixed(body):
    if 'stage_type' not in body:
        return 400, 'Stage type not specified.'
    st = body['stage_type']
    if not isinstance(st, dict) or 'value' not in st:
        return 400, 'Invalid stage_type.'
    try:
        return 200, int(st['value'])
    except (TypeError, ValueError):
        return 400, 'stage_type value was not an int.'


for label, body in cases:
    code, _ = do_post_fixed(body)
    print(f'fixed do_post({label}) -> HTTP {code}')
    assert code == 400
print()

print("CONFIRMED: POST /api/v0/features/<id>/stages with a malformed stage_type")
print("  raises TypeError/KeyError/ValueError -> HTTP 500 instead of HTTP 400.")
print()
print("Root cause: stages_api.py:99 guards only key presence, not shape/type;")
print("  stages_api.py:101 int(body['stage_type']['value']) then throws.")
print("  APIHandler.post (basehandlers.py:261) has no except around do_post.")
print()
print("Proposed fix: validate isinstance(st, dict) and 'value' in st, and wrap")
print("  int(st['value']) in try/except -> self.abort(400, ...).")
