# Harness: api/reviews_api.py:VotesAPI.require_permissions — vote authorization
#
# Security/authorization invariant for who may cast which gate vote.  Faithful
# model of require_permissions (reviews_api.py:135-160):
#
#   is_requesting_review = new_state in (REVIEW_REQUESTED, NA_REQUESTED)
#   is_approving         = new_state in Gate.APPROVED_STATES  # {NA, APPROVED, NA_SELF, NA_VERIFIED}
#   if is_requesting_review and is_editor:                 return  # allowed
#   if is_approving and is_editor and self_certify.is_eligible(gate): return  # allowed
#   if is_approver:                                        return  # allowed
#   self.abort(403, ...)                                            # otherwise denied
#
# Two derived security properties (NOT restatements of the code — consequences
# that must follow if the predicate is correct):
#   (A) Only an approver may cast a NEGATIVE verdict — DENIED / NEEDS_WORK /
#       REVIEW_STARTED / INTERNAL_REVIEW (these are neither a review request nor
#       an approving state, so the only accepting branch is `is_approver`).
#   (B) A non-approver may reach an APPROVING state only as a self-certify-eligible
#       editor (no editor can self-approve a gate they aren't eligible to certify).
#
# Expected verdict: SUCCESSFUL — ESBMC proves both properties for every vote
# state and every (editor, approver, eligible) combination.  (Paired buggy
# harness drops the self-certify check and is caught.)

# Vote state values (internals/review_models.py:Vote).
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
    # Gate.APPROVED_STATES = [NA, APPROVED, NA_SELF, NA_VERIFIED]
    return s == NA or s == APPROVED or s == NA_SELF or s == NA_VERIFIED


def is_requesting_state(s):
    return s == REVIEW_REQUESTED or s == NA_REQUESTED


def vote_allowed(new_state, is_editor, is_approver, self_certify_eligible):
    """Faithful model of require_permissions: True == accepted, False == abort 403."""
    if is_requesting_state(new_state) and is_editor:
        return True
    if is_approving_state(new_state) and is_editor and self_certify_eligible:
        return True
    if is_approver:
        return True
    return False


def main():
    new_state = nondet_int()             # noqa: F821
    is_editor = nondet_int()             # noqa: F821  (0/1)
    is_approver = nondet_int()           # noqa: F821  (0/1)
    self_certify_eligible = nondet_int()  # noqa: F821  (0/1)

    __ESBMC_assume(1 <= new_state and new_state <= 11)  # noqa: F821  any vote state
    __ESBMC_assume(is_editor == 0 or is_editor == 1)              # noqa: F821
    __ESBMC_assume(is_approver == 0 or is_approver == 1)          # noqa: F821
    __ESBMC_assume(self_certify_eligible == 0 or self_certify_eligible == 1)  # noqa: F821

    allowed = vote_allowed(new_state, is_editor, is_approver, self_certify_eligible)

    negative_verdict = (
        new_state == DENIED
        or new_state == NEEDS_WORK
        or new_state == REVIEW_STARTED
        or new_state == INTERNAL_REVIEW
    )

    # (A) A negative verdict can only be cast by an approver.
    if allowed and negative_verdict:
        assert is_approver == 1

    # (B) A non-approver reaching an approving state must be an eligible editor.
    if allowed and is_approving_state(new_state) and is_approver == 0:
        assert is_editor == 1
        assert self_certify_eligible == 1


main()
