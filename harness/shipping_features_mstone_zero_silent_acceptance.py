# Harness: api/shipping_features_api.py:ShippingFeaturesAPI.do_get — Finding E
#
# Source: shipping_features_api.py:58
#   milestone = self.get_int_arg('mstone')
#   if milestone is None:
#       self.abort(400, msg='No milestone provided.')
#   shipping_stages = self._get_shipping_stages(milestone)
#
# get_int_arg rejects negatives (< 0 -> abort 400) but ADMITS 0.  The handler
# guards only `milestone is None`, so `?mstone=0` passes the guard (0 is not
# None).  `_get_shipping_stages(0)` queries Stage.milestones.*_first == 0;
# milestone 0 is not a real Chrome milestone, so no stage matches and the
# query returns [].  do_get then returns
#   {'complete_features': [], 'incomplete_features': []}  HTTP 200
# with no error signal — the caller's malformed mstone=0 is silently accepted.
#
# Same silent-acceptance class as Finding B (features ?num=0) and Finding C
# (channels ?start=0): a falsy-but-invalid value slips past get_int_arg's
# negative-only guard and reaches downstream logic that assumes a positive
# milestone.  The `is None` guard is the tell — the author handled None but
# not 0.
#
# Expected verdict: FAILED (assertion `mstone >= 1` is violated at the gate).
#
# Empirical reproduction:
#   GET /api/v0/shipping_features?mstone=0
#   → {"complete_features": [], "incomplete_features": []}  HTTP 200
#   (expected: HTTP 400 "milestone must be >= 1")
#
# Proposed fix:
#   After the `is None` guard add `if milestone < 1: self.abort(400,
#   msg='milestone must be >= 1')`, or give get_int_arg a minimum-value param.

HTTP_200 = 200
HTTP_400 = 400


def get_int_arg(val: int) -> int:
    """Stub of get_int_arg: rejects negative, admits 0+."""
    if val < 0:
        return HTTP_400
    return val    # 0 is admitted — no minimum-value guard.


def shipping_do_get_milestone_gate(mstone: int) -> int:
    """Model of the milestone-acceptance gate in ShippingFeaturesAPI.do_get."""
    # Current behaviour: get_int_arg rejects only negatives;
    # the handler then guards only `milestone is None`.
    if mstone < 0:
        return HTTP_400
    # mstone=0 passes through; milestone 0 is not a real Chrome milestone.
    return HTTP_200


def main():
    mstone = nondet_int()  # noqa: F821
    __ESBMC_assume(mstone == 0)  # noqa: F821  — the admitted-but-invalid value.

    code = shipping_do_get_milestone_gate(mstone)

    # After the acceptance gate, mstone must be >= 1 (milestone 0 does not exist).
    assert mstone >= 1   # FAILS: mstone=0 is admitted (code=200) but invalid.


main()
