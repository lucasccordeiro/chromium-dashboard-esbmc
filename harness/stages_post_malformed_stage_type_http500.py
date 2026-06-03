# Harness: api/stages_api.py:StagesAPI.do_post — Finding H
#
# Source: stages_api.py:98-101
#   body = self.get_json_param_dict()
#   if 'stage_type' not in body:
#       self.abort(400, msg='Stage type not specified.')
#   stage_type = int(body['stage_type']['value'])   # shape/type NOT validated
#
# The guard checks only that the `stage_type` KEY is present, not that its value
# is a `{"value": <int>}` dict.  `int(body['stage_type']['value'])` then raises:
#   - TypeError  if body['stage_type'] is not subscriptable by 'value'
#                (e.g. {"stage_type": 5} or {"stage_type": "x"});
#   - KeyError   if it is a dict without 'value' (e.g. {"stage_type": {}});
#   - ValueError if 'value' is a non-numeric string (e.g. {"value": "abc"}).
# APIHandler.post (basehandlers.py:261) has no `except` around do_post(), so the
# exception propagates to Flask and becomes HTTP 500, not HTTP 400.
#
# Same bare-exception class as Finding A / G — the maintainer-accepted PR #6451
# convention requires self.abort(400, ...) on bad input.
#
# Expected verdict: FAILED (assertion `code == 400` violated via the exception
# path).
#
# Empirical reproduction:
#   POST /api/v0/features/123/stages   body: {"stage_type": {}}
#   → HTTP 500 Internal Server Error  (expected: HTTP 400 Bad Request)
#
# Proposed fix:
#   st = body['stage_type']
#   if not isinstance(st, dict) or 'value' not in st:
#       self.abort(400, msg='Invalid stage_type.')
#   try:
#       stage_type = int(st['value'])
#   except (TypeError, ValueError):
#       self.abort(400, msg='stage_type value was not an int.')


HTTP_200 = 200
HTTP_400 = 400


def stages_do_post(has_stage_type: int, value_is_intish: int) -> int:
    """Inline model of StagesAPI.do_post stage_type handling (current code)."""
    # stages_api.py:99 — presence guard only.
    if not has_stage_type:
        return HTTP_400

    # stages_api.py:101 — int(body['stage_type']['value']) with no shape/type
    # validation.  A malformed stage_type raises here in production.
    if not value_is_intish:
        raise ValueError   # models the TypeError/KeyError/ValueError → HTTP 500.

    return HTTP_200


def main():
    has_stage_type = nondet_int()   # noqa: F821  — is the key present?
    value_is_intish = nondet_int()  # noqa: F821  — is it a {value:int} dict?

    __ESBMC_assume(has_stage_type == 1)   # noqa: F821  — key present (guard passes)
    __ESBMC_assume(value_is_intish == 0)  # noqa: F821  — but the value is malformed

    # Expected: a malformed stage_type should yield HTTP 400.
    # Actual:   int(body['stage_type']['value']) raises → HTTP 500.
    try:
        code = stages_do_post(has_stage_type, value_is_intish)
        assert code == HTTP_400   # FAILS: the exception path is taken instead.
    except ValueError:
        assert False, "malformed stage_type should have been an HTTP 400 abort"


main()
