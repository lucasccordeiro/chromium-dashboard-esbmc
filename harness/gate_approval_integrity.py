# Harness: internals/approval_defs.py:_calc_gate_state — gate-approval integrity
#
# Security/integrity invariant (the crown-jewel property of the review workflow):
#   A gate is computed as APPROVED only if at least `threshold` genuine APPROVED
#   votes were cast — 1 for a ONE_LGTM gate, 3 for a THREE_LGTM gate — and no NA
#   vote is present.  In other words, the vote tally can never manufacture a
#   spurious approval (e.g. a 3-reviewer gate "approved" by a single reviewer, or
#   an approval with zero approving votes).
#
# Source model (verbatim logic, approval_defs.py:523-568, _calc_gate_state):
#   num_lgtms = counts[APPROVED] + counts[NA]
#   if (rule == ONE_LGTM and num_lgtms >= 1) or (rule == THREE_LGTM and num_lgtms >= 3):
#       if counts[NA] > 0:
#           return NA
#       else:
#           return APPROVED
# (The NA_SELF special case and the "most-recent review state" loop return only
# non-APPROVED states, so they cannot affect the APPROVED invariant; the NA_SELF
# branch is modelled for fidelity.)
#
# Who may cast an APPROVED vote is enforced separately in VotesAPI.do_post
# (require_permissions); this harness verifies the *tally* itself.
#
# Expected verdict: SUCCESSFUL — ESBMC proves no symbolic vote multiset yields
# APPROVED without >= threshold approving votes.  (Paired buggy harness shows the
# invariant is non-vacuous.)

ONE_LGTM = 1      # threshold for a one-LGTM gate
THREE_LGTM = 3    # threshold for a three-LGTM gate

# Vote / Gate state values (internals/review_models.py:Vote).
NA = 1
REVIEW_REQUESTED = 2
APPROVED = 5
NA_SELF = 10
NA_VERIFIED = 11
PREPARING = 0


def calc_gate_state(threshold, n_approved, n_na, n_na_self, n_na_verified, n_review):
    """Faithful model of _calc_gate_state, parameterised by vote counts.

    `threshold` is 1 (ONE_LGTM) or 3 (THREE_LGTM).  `n_review` aggregates the
    NEEDS_WORK/REVIEW_STARTED/REVIEW_REQUESTED/DENIED/INTERNAL_REVIEW/NA_REQUESTED
    votes (all non-APPROVED outcomes).  NO_RESPONSE votes are already excluded.
    """
    total = n_approved + n_na + n_na_self + n_na_verified + n_review

    # NA_SELF special case (ONE_LGTM only) — returns NA_SELF / NA_VERIFIED only.
    if n_na_self == 1 and threshold == ONE_LGTM:
        if total == 1:
            return NA_SELF
        if n_na_verified >= 1:
            return NA_VERIFIED

    num_lgtms = n_approved + n_na
    if (threshold == ONE_LGTM and num_lgtms >= 1) or (
        threshold == THREE_LGTM and num_lgtms >= 3
    ):
        if n_na > 0:
            return NA
        return APPROVED

    # Remaining branches return only non-APPROVED states.
    if n_review > 0:
        return REVIEW_REQUESTED
    if threshold == THREE_LGTM and num_lgtms >= 1:
        return REVIEW_REQUESTED
    return PREPARING


def main():
    threshold = nondet_int()        # noqa: F821
    n_approved = nondet_int()       # noqa: F821
    n_na = nondet_int()             # noqa: F821
    n_na_self = nondet_int()        # noqa: F821
    n_na_verified = nondet_int()    # noqa: F821
    n_review = nondet_int()         # noqa: F821

    # A gate has finitely many votes; bound each count (real gates have a handful).
    # This keeps the count arithmetic in range — the unbounded model would report
    # a spurious CWE-190 overflow on the sum, which is a modelling artifact, not a
    # property of _calc_gate_state.
    __ESBMC_assume(threshold == ONE_LGTM or threshold == THREE_LGTM)  # noqa: F821
    __ESBMC_assume(0 <= n_approved and n_approved <= 1000)        # noqa: F821
    __ESBMC_assume(0 <= n_na and n_na <= 1000)                    # noqa: F821
    __ESBMC_assume(0 <= n_na_self and n_na_self <= 1000)          # noqa: F821
    __ESBMC_assume(0 <= n_na_verified and n_na_verified <= 1000)  # noqa: F821
    __ESBMC_assume(0 <= n_review and n_review <= 1000)            # noqa: F821

    state = calc_gate_state(
        threshold, n_approved, n_na, n_na_self, n_na_verified, n_review
    )

    # Integrity invariant: an APPROVED gate required >= threshold approving votes
    # and carries no NA vote.
    if state == APPROVED:
        assert n_approved >= threshold
        assert n_na == 0


main()
