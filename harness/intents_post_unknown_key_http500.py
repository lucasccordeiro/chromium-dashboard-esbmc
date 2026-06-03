# Harness: api/intents_api.py:IntentsAPI.do_post — Finding J
#
# Source: intents_api.py:176
#   parsed_args = PostIntentRequest(**self.request.get_json())
#
# PostIntentRequest is an OpenAPI-generated model whose __init__ accepts only
# `gate_id` and `intent_cc_emails`
# (chromestatus_openapi/models/post_intent_request.py:
#   def __init__(self, gate_id=None, intent_cc_emails=None): ...).
# Splatting the raw request JSON with `**self.request.get_json()` means any JSON
# body containing an unexpected key raises
#   TypeError: __init__() got an unexpected keyword argument '<key>'.
# APIHandler.post (basehandlers.py:261) has no `except` around do_post(), so the
# TypeError propagates to Flask and becomes HTTP 500, not HTTP 400.
#
# Same bare-exception class as Finding A / G (PR #6451 convention).
#
# Expected verdict: FAILED (assertion `code == 400` violated via the exception
# path).
#
# Empirical reproduction:
#   POST /api/v0/features/1/2/intent   body: {"gate_id": 3, "bogus": 1}
#   → HTTP 500 Internal Server Error  (expected: HTTP 400 Bad Request)
#
# Proposed fix:
#   use the tolerant deserializer and convert errors, e.g.
#   try:
#       parsed_args = PostIntentRequest.from_dict(self.request.get_json() or {})
#   except (TypeError, ValueError) as e:
#       self.abort(400, msg=str(e))


HTTP_200 = 200
HTTP_400 = 400


def intents_do_post(body_has_unknown_key: int) -> int:
    """Inline model of IntentsAPI.do_post argument parsing (current code)."""
    # intents_api.py:176 — PostIntentRequest(**body): an unexpected key raises.
    if body_has_unknown_key:
        raise TypeError   # unexpected keyword argument → HTTP 500.

    return HTTP_200


def main():
    body_has_unknown_key = nondet_int()  # noqa: F821  — extra JSON key present?

    __ESBMC_assume(body_has_unknown_key == 1)  # noqa: F821  — client sent an extra key

    # Expected: an unrecognized body key should yield HTTP 400.
    # Actual:   PostIntentRequest(**body) raises TypeError → HTTP 500.
    try:
        code = intents_do_post(body_has_unknown_key)
        assert code == HTTP_400   # FAILS: the exception path is taken instead.
    except TypeError:
        assert False, "unexpected body key should have been an HTTP 400 abort"


main()
