# Harness: internals/slo.py:record_comment — initial-response idempotency
#
# Source (verbatim, d0d21c8), internals/slo.py:106-122:
#     def record_comment(feature, gate, user, approvers) -> bool:
#         if gate.requested_on is None:
#             return False            # Review has not been requested yet.
#         elif gate.responded_on is not None:
#             return False            # Already recorded the initial response.
#         else:
#             is_approver = permissions.can_review_gate(...)
#             if is_approver:
#                 gate.responded_on = now_utc()
#                 return True
#         return False
#
# record_comment records the *initial* reviewer response time exactly once.
# The two guards make it idempotent: once responded_on is set, every later
# call short-circuits to False without re-writing the field.
#
# Contract (Tier 4, row 15):
#   1. soundness/completeness: result is True  iff  requested_on is set AND
#      responded_on is unset AND the caller is an approver.
#   2. write-iff-true: gate.responded_on is mutated  iff  the call returns True.
#   3. idempotency: a True call sets responded_on, so an immediate second call
#      with the resulting state returns False — the initial response time is
#      never overwritten.
#
# Stub: requested_on / responded_on presence are nondet booleans (None vs set);
# can_review_gate's verdict is an independent nondet bool.  The model returns
# both the result and the post-call responded_on state to express contracts 2-3.


def record_comment(requested_set, responded_set, is_approver):
    """Structural model; returns (result, responded_set_after_call)."""
    if not requested_set:
        return False, responded_set        # requested_on is None
    if responded_set:
        return False, responded_set        # responded_on is not None
    if is_approver:
        return True, True                  # gate.responded_on = now_utc()
    return False, responded_set


def main():
    requested   = nondet_bool()   # noqa: F821 — gate.requested_on is set
    responded   = nondet_bool()   # noqa: F821 — gate.responded_on is set
    is_approver = nondet_bool()   # noqa: F821 — can_review_gate verdict

    result, responded_after = record_comment(requested, responded, is_approver)

    # Contract 1: True iff requested AND not-yet-responded AND approver.
    assert result == (requested and (not responded) and is_approver)

    # Contract 2: responded_on is written iff the call returned True
    # (otherwise the prior state is preserved unchanged).
    assert responded_after == (responded or result)

    # Contract 3: idempotency — replaying with the post-call state never
    # returns True a second time (the initial response is recorded once).
    result2, _ = record_comment(requested, responded_after, is_approver)
    assert not (result and result2)


main()
