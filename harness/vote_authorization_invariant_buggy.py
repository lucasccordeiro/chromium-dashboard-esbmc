# Harness: api/reviews_api.py:VotesAPI.require_permissions — vote authorization (BUGGY)
#
# Non-vacuity / negative control for `vote_authorization_invariant.py`.  Same model
# with one realistic mutation: the approving branch drops the self-certify check,
#
#     if is_approving_state(new_state) and is_editor:        # BUG: lost `and self_certify_eligible`
#         return True
#
# i.e. ANY feature editor could self-approve ANY gate, even one they are not
# eligible to self-certify — a high-severity privilege-escalation of the review
# process.  ESBMC must catch it via property (B).
#
# Expected verdict: FAILED — with an approving state, is_editor=1, is_approver=0,
# self_certify_eligible=0, the mutated predicate accepts the vote while property
# (B) requires self_certify_eligible == 1.

NA = 1
REVIEW_REQUESTED = 2
REVIEW_STARTED = 3
NEEDS_WORK = 4
APPROVED = 5
DENIED = 6
NO_RESPONSE = 7
INTERNAL_REVIEW = 8
NA_REQUESTED = 9
NA_SELF = 10
NA_VERIFIED = 11


def is_approving_state(s):
    return s == NA or s == APPROVED or s == NA_SELF or s == NA_VERIFIED


def is_requesting_state(s):
    return s == REVIEW_REQUESTED or s == NA_REQUESTED


def vote_allowed_buggy(new_state, is_editor, is_approver, self_certify_eligible):
    if is_requesting_state(new_state) and is_editor:
        return True
    # BUG: self-certify eligibility check dropped — any editor may approve.
    if is_approving_state(new_state) and is_editor:
        return True
    if is_approver:
        return True
    return False


def main():
    new_state = nondet_int()             # noqa: F821
    is_editor = nondet_int()             # noqa: F821
    is_approver = nondet_int()           # noqa: F821
    self_certify_eligible = nondet_int()  # noqa: F821

    __ESBMC_assume(1 <= new_state and new_state <= 11)  # noqa: F821
    __ESBMC_assume(is_editor == 0 or is_editor == 1)              # noqa: F821
    __ESBMC_assume(is_approver == 0 or is_approver == 1)          # noqa: F821
    __ESBMC_assume(self_certify_eligible == 0 or self_certify_eligible == 1)  # noqa: F821

    allowed = vote_allowed_buggy(new_state, is_editor, is_approver, self_certify_eligible)

    negative_verdict = (
        new_state == DENIED
        or new_state == NEEDS_WORK
        or new_state == REVIEW_STARTED
        or new_state == INTERNAL_REVIEW
    )

    if allowed and negative_verdict:
        assert is_approver == 1

    # Property (B) — violated by the dropped self-certify check.
    if allowed and is_approving_state(new_state) and is_approver == 0:
        assert is_editor == 1
        assert self_certify_eligible == 1   # FAILS: editor self-approves without eligibility.


main()
