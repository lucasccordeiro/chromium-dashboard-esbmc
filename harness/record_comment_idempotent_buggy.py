# Buggy: record_comment — missing the `responded_on is not None` guard.
# Expected verdict: FAILED (idempotency / write-once contract broken).
#
# Mutation: drop the `elif gate.responded_on is not None: return False` branch.
# The function now re-records the response whenever the caller is an approver,
# overwriting the initial response time on every subsequent call.
#
# Counterexample: requested=True, responded=True, is_approver=True.
#   Correct record_comment -> False (response already recorded).
#   Buggy version          -> True  (overwrites responded_on),
# so result != (requested AND not responded AND is_approver).


def record_comment_buggy(requested_set, responded_set, is_approver):
    if not requested_set:
        return False, responded_set
    # BUG: missing `if responded_set: return False, responded_set`
    if is_approver:
        return True, True
    return False, responded_set


def main():
    requested   = nondet_bool()   # noqa: F821
    responded   = nondet_bool()   # noqa: F821
    is_approver = nondet_bool()   # noqa: F821

    result, _ = record_comment_buggy(requested, responded, is_approver)

    # FAILS at requested=True, responded=True, is_approver=True:
    # buggy returns True but the contract expects False (already responded).
    assert result == (requested and (not responded) and is_approver)


main()
