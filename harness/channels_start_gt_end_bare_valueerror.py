# Harness: api/channels_api.py:ChannelsAPI.do_get — Finding A
#
# Source: channels_api.py:146
#   if start > end:
#       raise ValueError          # bare — not self.abort(400, msg=...)
#
# APIHandler.get() has no `except ValueError` wrapper
# (framework/basehandlers.py:251-259), so an unhandled ValueError
# propagates to Flask and becomes HTTP 500, not HTTP 400.
#
# This harness models the validation gate and asserts the EXPECTED
# behaviour (raise ValueError → HTTP 400).  The assertion fails because
# the bare raise produces HTTP 500 instead.
#
# Expected verdict: FAILED (assertion `response_code == 400` is violated).
#
# Empirical reproduction:
#   GET /api/v0/channels?start=5&end=3
#   → HTTP 500 Internal Server Error  (expected: HTTP 400 Bad Request)
#
# Proposed fix:
#   replace `raise ValueError` with `self.abort(400, msg='start must be <= end')`


HTTP_200 = 200
HTTP_400 = 400
HTTP_500 = 500


def get_int_arg(val: int) -> int:
    """Stub of basehandlers.get_int_arg: rejects negatives, admits 0+."""
    if val < 0:
        # self.abort(400) — modelled as returning the error code.
        return HTTP_400
    return val


def channels_do_get(start: int, end: int) -> int:
    """Inline model of ChannelsAPI.do_get validation path.

    Returns the HTTP response code the handler would produce.
    """
    # get_int_arg validates: admits 0 and positive, rejects negative.
    if start < 0 or end < 0:
        return HTTP_400

    # channels_api.py:146: bare raise — NOT self.abort(400, ...).
    if start > end:
        raise ValueError   # propagates as HTTP 500 in production.

    return HTTP_200


def main():
    start = nondet_int()  # noqa: F821
    end = nondet_int()    # noqa: F821

    # Constrain to the range get_int_arg admits: 0 and positive.
    __ESBMC_assume(start > 0)   # noqa: F821
    __ESBMC_assume(end > 0)     # noqa: F821
    __ESBMC_assume(start > end)  # trigger the validation branch.

    # Expected: server should return HTTP 400 for invalid input.
    # Actual:   bare raise ValueError → Flask returns HTTP 500.
    # Assert the expected behaviour; ESBMC will find the counterexample.
    try:
        code = channels_do_get(start, end)
        assert code == HTTP_400   # FAILS: code would be HTTP_500 (via exception path).
    except ValueError:
        # The bare raise reaches here in the model; HTTP 500 is the real outcome.
        assert False, "bare ValueError should have been an HTTP 400 abort"


main()
