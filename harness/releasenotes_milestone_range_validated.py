# Harness: api/releasenotes_api.py:ReleaseNotesL10nAPI.do_get — positive control
#
# Source: releasenotes_api.py:37-51
#   start_milestone = self.get_int_arg('startMilestone')
#   end_milestone   = self.get_int_arg('endMilestone')
#   if start_milestone is None: self.abort(400, msg='Missing startMilestone')
#   if end_milestone   is None: self.abort(400, msg='Missing endMilestone')
#   if start_milestone <= 0 or end_milestone <= 0:
#       self.abort(400, msg='Milestones must be positive integers')
#   if start_milestone > end_milestone:
#       self.abort(400, msg='startMilestone must be <= endMilestone')
#
# This handler is the CANONICAL CORRECT shape of the milestone-range check —
# the exact fix proposed for Finding A (channels start > end -> bare ValueError
# -> HTTP 500) and Finding C (channels start=0 -> milestone 0 silently
# accepted).  Unlike channels_api.do_get, it (a) rejects non-positive
# milestones with a clean abort(400) and (b) rejects the inverted range with a
# clean abort(400) rather than a bare `raise ValueError`.
#
# Contract: every milestone value that survives the gate (code == 200) is a
# valid range — start >= 1, end >= 1, start <= end.  This is the postcondition
# Findings A and C violate; here it holds.
#
# Expected verdict: SUCCESSFUL (the gate admits only well-formed ranges).
# This target is the discriminating control: it shares the buggy targets'
# harness shape but asserts the property the buggy targets fail, so a
# SUCCESSFUL verdict here confirms the harness is non-vacuous.

HTTP_200 = 200
HTTP_400 = 400

INT_BOUND = 1 << 20   # wide bound covering realistic milestone numbers.


def get_int_arg(val: int) -> int:
    """Stub of get_int_arg: rejects negative, admits 0+ (returns the value)."""
    # Negatives are rejected upstream; the value reaching the handler is >= 0.
    return val


def releasenotes_gate(start: int, end: int) -> int:
    """Model of the milestone-range acceptance gate in ReleaseNotesL10nAPI."""
    # get_int_arg rejects negatives.
    if start < 0 or end < 0:
        return HTTP_400
    # Handler: reject non-positive milestones.
    if start <= 0 or end <= 0:
        return HTTP_400
    # Handler: reject inverted range.
    if start > end:
        return HTTP_400
    return HTTP_200


def main():
    start = nondet_int()  # noqa: F821
    end = nondet_int()    # noqa: F821
    __ESBMC_assume(-INT_BOUND <= start <= INT_BOUND)  # noqa: F821
    __ESBMC_assume(-INT_BOUND <= end <= INT_BOUND)    # noqa: F821

    code = releasenotes_gate(start, end)

    # Postcondition: any range that proceeds is well-formed.
    if code == HTTP_200:
        assert start >= 1
        assert end >= 1
        assert start <= end


main()
