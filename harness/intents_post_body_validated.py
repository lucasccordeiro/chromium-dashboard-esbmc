# Harness: api/intents_api.py:IntentsAPI.do_post — Finding J (fix)
#
# Positive control / paired good harness for Finding J
# (`intents_post_unknown_key_http500.py`).  Models the proposed fix: deserialize
# with the tolerant `from_dict` (which ignores unknown keys) and convert any
# residual error to abort(400) rather than splatting raw JSON into __init__.
#
#   try:
#       parsed_args = PostIntentRequest.from_dict(self.request.get_json() or {})
#   except (TypeError, ValueError) as e:
#       self.abort(400, msg=str(e))          # FIX
#
# With the fix, any body shape produces a clean HTTP code — an unexpected key is
# ignored (or rejected with HTTP 400), never an uncaught TypeError (HTTP 500).
#
# Expected verdict: SUCCESSFUL (Phase 1 and Phase 2).


HTTP_200 = 200
HTTP_400 = 400


def intents_do_post_fixed(body_has_unknown_key: int) -> int:
    """Model of do_post with tolerant deserialization + error conversion."""
    # Fix: unknown keys no longer crash; a malformed body is a clean 400.
    if body_has_unknown_key:
        return HTTP_400
    return HTTP_200


def main():
    body_has_unknown_key = nondet_int()  # noqa: F821

    code = intents_do_post_fixed(body_has_unknown_key)

    # Every body shape yields a clean HTTP code (never throws).
    assert code == HTTP_400 or code == HTTP_200
    # An unexpected key is handled as HTTP 400, not 500.
    if body_has_unknown_key:
        assert code == HTTP_400


main()
