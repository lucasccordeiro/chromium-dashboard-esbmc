# Harness: api/stages_api.py:StagesAPI.do_post — Finding H (fix)
#
# Positive control / paired good harness for Finding H
# (`stages_post_malformed_stage_type_http500.py`).  Models the proposed fix:
# validate the shape/type of `stage_type` before converting it.
#
#   if 'stage_type' not in body:
#       self.abort(400, msg='Stage type not specified.')
#   st = body['stage_type']
#   if not isinstance(st, dict) or 'value' not in st:
#       self.abort(400, msg='Invalid stage_type.')          # FIX
#   try:
#       stage_type = int(st['value'])
#   except (TypeError, ValueError):
#       self.abort(400, msg='stage_type value was not an int.')   # FIX
#
# With the shape/type guard, every request body produces a clean HTTP code — a
# malformed stage_type yields HTTP 400, never an uncaught exception (HTTP 500).
#
# Expected verdict: SUCCESSFUL (Phase 1 and Phase 2).


HTTP_200 = 200
HTTP_400 = 400


def stages_do_post_fixed(has_stage_type: int, value_is_intish: int) -> int:
    """Model of do_post with stage_type shape/type validation added."""
    if not has_stage_type:
        return HTTP_400
    # Fix: reject a malformed stage_type with abort(400) instead of int()-ing it.
    if not value_is_intish:
        return HTTP_400
    return HTTP_200


def main():
    has_stage_type = nondet_int()   # noqa: F821
    value_is_intish = nondet_int()  # noqa: F821

    code = stages_do_post_fixed(has_stage_type, value_is_intish)

    # Every body shape yields a clean HTTP code (never throws).
    assert code == HTTP_400 or code == HTTP_200
    # A malformed stage_type is rejected with HTTP 400, not 500.
    if not value_is_intish:
        assert code == HTTP_400


main()
