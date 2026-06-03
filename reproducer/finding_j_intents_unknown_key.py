#!/usr/bin/env python3
"""
Empirical reproducer — Finding J
  api/intents_api.py:176  IntentsAPI.do_post
  parsed_args = PostIntentRequest(**self.request.get_json())
  The OpenAPI model __init__ accepts only gate_id / intent_cc_emails, so any
  extra JSON key raises TypeError (unexpected kwarg) → HTTP 500.

Source (verbatim, GoogleChrome/chromium-dashboard @ 4294104b):
  # api/intents_api.py:176
  parsed_args = PostIntentRequest(**self.request.get_json())

  # chromestatus_openapi/models/post_intent_request.py
  class PostIntentRequest(Model):
      def __init__(self, gate_id=None, intent_cc_emails=None):
          ...

Dependencies: none (pure Python stdlib).
"""

class PostIntentRequest:
    """Stand-in for the OpenAPI model: __init__ accepts only these two kwargs."""
    def __init__(self, gate_id=None, intent_cc_emails=None):
        self.gate_id = gate_id
        self.intent_cc_emails = intent_cc_emails

    @classmethod
    def from_dict(cls, dikt):
        """Tolerant deserializer: ignores unknown keys (OpenAPI from_dict shape)."""
        known = {'gate_id', 'intent_cc_emails'}
        return cls(**{k: v for k, v in (dikt or {}).items() if k in known})


def do_post(request_json):
    """Inline of intents_api.py:176 (current code)."""
    parsed_args = PostIntentRequest(**request_json)   # TypeError on extra key
    return 200, parsed_args


body = {'gate_id': 3, 'bogus': 1}     # one unexpected key
try:
    do_post(body)
    raise AssertionError('expected TypeError')
except TypeError as e:
    print(f'do_post({body}) -> TypeError({e}) -> propagates as HTTP 500')
print()

# Contrast — the fixed handler (tolerant from_dict + error conversion) is clean.
def do_post_fixed(request_json):
    try:
        parsed_args = PostIntentRequest.from_dict(request_json or {})
    except (TypeError, ValueError) as e:
        return 400, str(e)
    return 200, parsed_args


code, _ = do_post_fixed(body)
print(f'fixed do_post({body}) -> HTTP {code} (unknown key ignored)')
assert code == 200
print()

print("CONFIRMED: POST .../intent with an unexpected JSON key raises TypeError")
print("  -> HTTP 500 instead of HTTP 400.")
print()
print("Root cause: intents_api.py:176 PostIntentRequest(**body) splats raw JSON")
print("  into an __init__ that accepts only gate_id/intent_cc_emails.")
print("  APIHandler.post (basehandlers.py:261) has no except around do_post.")
print()
print("Proposed fix: PostIntentRequest.from_dict(body or {}) inside try/except")
print("  -> self.abort(400, ...).")
