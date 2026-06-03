# Harness: internals/approval_defs.py:_calc_gate_state — gate-approval integrity (BUGGY)
#
# Non-vacuity / negative control for `gate_approval_integrity.py`.  This is the
# same model with one realistic mutation injected into the THREE_LGTM threshold:
#
#     ... or (threshold == THREE_LGTM and num_lgtms >= 1)     # BUG: was >= 3
#
# i.e. a three-reviewer gate is reported APPROVED after a SINGLE approving vote.
# That would be a high-severity integrity bug — a feature could ship past a gate
# that requires three sign-offs with only one.  ESBMC must catch it.
#
# Expected verdict: FAILED — with threshold = THREE_LGTM, n_approved = 1, n_na = 0
# the mutated tally returns APPROVED while the invariant requires n_approved >= 3.

ONE_LGTM = 1
THREE_LGTM = 3

NA = 1
REVIEW_REQUESTED = 2
APPROVED = 5
NA_SELF = 10
NA_VERIFIED = 11
PREPARING = 0


def calc_gate_state_buggy(threshold, n_approved, n_na, n_na_self, n_na_verified, n_review):
    total = n_approved + n_na + n_na_self + n_na_verified + n_review

    if n_na_self == 1 and threshold == ONE_LGTM:
        if total == 1:
            return NA_SELF
        if n_na_verified >= 1:
            return NA_VERIFIED

    num_lgtms = n_approved + n_na
    # BUG: the THREE_LGTM threshold is >= 1 instead of >= 3.
    if (threshold == ONE_LGTM and num_lgtms >= 1) or (
        threshold == THREE_LGTM and num_lgtms >= 1
    ):
        if n_na > 0:
            return NA
        return APPROVED

    if n_review > 0:
        return REVIEW_REQUESTED
    return PREPARING


def main():
    threshold = nondet_int()        # noqa: F821
    n_approved = nondet_int()       # noqa: F821
    n_na = nondet_int()             # noqa: F821
    n_na_self = nondet_int()        # noqa: F821
    n_na_verified = nondet_int()    # noqa: F821
    n_review = nondet_int()         # noqa: F821

    __ESBMC_assume(threshold == ONE_LGTM or threshold == THREE_LGTM)  # noqa: F821
    __ESBMC_assume(0 <= n_approved and n_approved <= 1000)        # noqa: F821
    __ESBMC_assume(0 <= n_na and n_na <= 1000)                    # noqa: F821
    __ESBMC_assume(0 <= n_na_self and n_na_self <= 1000)          # noqa: F821
    __ESBMC_assume(0 <= n_na_verified and n_na_verified <= 1000)  # noqa: F821
    __ESBMC_assume(0 <= n_review and n_review <= 1000)            # noqa: F821

    state = calc_gate_state_buggy(
        threshold, n_approved, n_na, n_na_self, n_na_verified, n_review
    )

    # Same invariant — the mutated tally violates it for a 1-approve THREE_LGTM gate.
    if state == APPROVED:
        assert n_approved >= threshold   # FAILS: n_approved == 1 < 3 under the bug.
        assert n_na == 0


main()
