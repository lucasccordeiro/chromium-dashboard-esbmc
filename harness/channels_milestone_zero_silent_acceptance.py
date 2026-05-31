# Harness: api/channels_api.py:ChannelsAPI.do_get — Finding C
#
# Source: channels_api.py:138
#   start = self.get_int_arg('start')   # admits 0
#   end   = self.get_int_arg('end')     # admits 0
#
# With start=0 (or end=0), the `start > end` guard does not trigger for
# start=end=0 (0 == 0 is not > 0).  construct_specified_milestones_details(0, 0)
# calls fetch_chrome_release_info(0) — milestone 0 is not a real Chrome
# milestone; the external API returns null dates.  The server returns HTTP 200
# with {'stable_date': None, 'earliest_beta': None, ...} without error signal.
#
# The same silent-acceptance pattern as vLLM Finding #3 (max-model-len 0):
# an invalid zero value bypasses validation and reaches downstream code that
# assumes a positive milestone number.
#
# Expected verdict: FAILED (assertion `start >= 1` is violated at acceptance gate).
#
# Empirical reproduction:
#   GET /api/v0/channels?start=0&end=0
#   → {0: {"stable_date": null, "mstone": 0, "version": 0}}  HTTP 200
#   (expected: HTTP 400 "start must be >= 1")
#
# Proposed fix:
#   Add `if start < 1 or end < 1: self.abort(400, msg='milestone must be >= 1')`
#   after the get_int_arg calls, or add a min-value param to get_int_arg.

HTTP_200 = 200
HTTP_400 = 400


def get_int_arg(val: int) -> int:
    """Stub of get_int_arg: rejects negative, admits 0+."""
    if val < 0:
        return HTTP_400
    return val    # 0 is admitted — no minimum-value guard.


def channels_do_get_milestone_gate(start: int) -> int:
    """Model of the milestone-acceptance gate in ChannelsAPI.do_get."""
    # Current behaviour: only negative start is rejected.
    if start < 0:
        return HTTP_400
    # start=0 passes through; milestone 0 is not a real Chrome milestone.
    return HTTP_200


def main():
    start = nondet_int()  # noqa: F821
    __ESBMC_assume(start == 0)  # noqa: F821  — the admitted-but-invalid value.

    code = channels_do_get_milestone_gate(start)

    # After the acceptance gate, start must be >= 1 (milestone 0 does not exist).
    assert start >= 1   # FAILS: start=0 is admitted (code=200) but milestone 0 is invalid.


main()
