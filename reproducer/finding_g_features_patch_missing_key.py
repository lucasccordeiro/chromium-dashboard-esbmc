#!/usr/bin/env python3
"""
Empirical reproducer — Finding G
  api/features_api.py:552  FeaturesAPI.do_patch
  body['feature_changes'] is indexed with no presence guard, so a PATCH whose
  body lacks the `feature_changes` key (e.g. `{}`) raises KeyError → HTTP 500.

Source (verbatim, GoogleChrome/chromium-dashboard @ d0d21c8):
  # api/features_api.py:549-557  FeaturesAPI.do_patch
  def do_patch(self, **kwargs):
      body = self.get_json_param_dict()          # {} for missing/invalid JSON
      if 'id' not in body['feature_changes']:    ← KeyError if key absent
          self.abort(400, msg='Missing feature ID in feature updates')
      ...
      stage_ids = [s['id'] for s in body['stages'] if 'id' in s]   ← sibling KeyError

  # framework/basehandlers.py:285-290  APIHandler.patch
  def patch(self, *args, **kwargs):
      self.require_signed_in_and_xsrf_token()
      headers = self.get_headers()
      handler_data = self.do_patch(*args, **kwargs)   ← no try/except → 500
      return self.defensive_jsonify(handler_data), headers

Dependencies: none (pure Python stdlib).
"""

# ── Step 1: get_json_param_dict returns {} for a missing/invalid body ─────

def get_json_param_dict(raw_json):
    """Inline of basehandlers.get_json_param_dict: request.get_json(...) or {}."""
    return raw_json or {}


# ── Step 2: do_patch indexes body['feature_changes'] with no guard ────────

def do_patch(raw_json):
    """Inline of features_api.py:549-557 body-shape handling (current code)."""
    body = get_json_param_dict(raw_json)
    # features_api.py:552 — unguarded dict access.
    if 'id' not in body['feature_changes']:
        return 400, 'Missing feature ID in feature updates'
    return 200, 'ok'


# Malformed body: empty object, no `feature_changes` key.
raised = False
try:
    do_patch({})
except KeyError as e:
    raised = True
    print(f"do_patch(body={{}}) raised KeyError({e}) → propagates as HTTP 500")

assert raised, 'expected KeyError on missing feature_changes'
print()

# ── Step 3: contrast — the fixed guard returns a clean 400 ────────────────

def do_patch_fixed(raw_json):
    """With a body-shape presence guard added."""
    body = get_json_param_dict(raw_json)
    if 'feature_changes' not in body:           # FIX
        return 400, 'Missing feature_changes'
    if 'id' not in body['feature_changes']:
        return 400, 'Missing feature ID in feature updates'
    return 200, 'ok'


code, msg = do_patch_fixed({})
print(f'fixed do_patch(body={{}}) → HTTP {code} ({msg})')
assert code == 400
print()

# ── Summary ───────────────────────────────────────────────────────────────

print("CONFIRMED: PATCH /api/v0/features/<id> with body {} raises KeyError ->")
print("  HTTP 500 Internal Server Error instead of HTTP 400 Bad Request.")
print()
print("Root cause:")
print("  features_api.py:552 indexes body['feature_changes'] with no presence")
print("  guard; APIHandler.patch (basehandlers.py:285) has no except around")
print("  do_patch, so the KeyError propagates to Flask as HTTP 500.")
print()
print("Proposed fix:")
print("  if 'feature_changes' not in body:")
print("      self.abort(400, msg='Missing feature_changes')")
print("  (and default body.get('stages', []) for the :567 sibling access).")
