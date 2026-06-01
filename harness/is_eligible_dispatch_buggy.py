# Buggy: is_eligible dispatch — swap privacy and testing routes.
# Expected verdict: FAILED (privacy gate returns is_testing_eligible result).

GATE_PRIVACY_ORIGIN_TRIAL = 1
GATE_PRIVACY_SHIP         = 2
GATE_TESTING_PLAN         = 3
GATE_TESTING_SHIP         = 4
GATE_ADOPTION_PLAN        = 5
GATE_ADOPTION_SHIP        = 6

N_FIELDS = 13


def is_privacy_eligible(ans) -> bool:
    return ans[0] and (ans[1] or ans[2] or ans[3])


def is_testing_eligible(ans) -> bool:
    return ans[4] and ans[5] and ans[6] and ans[7] and ans[8]


def is_adoption_eligible(ans) -> bool:
    return ans[9] and ans[10] and ans[11] and ans[12]


def is_eligible_buggy(gate_type, ans) -> bool:
    """Buggy: privacy and testing routes are swapped."""
    is_privacy  = gate_type == GATE_PRIVACY_ORIGIN_TRIAL or gate_type == GATE_PRIVACY_SHIP
    is_testing  = gate_type == GATE_TESTING_PLAN or gate_type == GATE_TESTING_SHIP
    is_adoption = gate_type == GATE_ADOPTION_PLAN or gate_type == GATE_ADOPTION_SHIP
    if is_privacy:
        return is_testing_eligible(ans)  # WRONG
    if is_testing:
        return is_privacy_eligible(ans)  # WRONG
    if is_adoption:
        return is_adoption_eligible(ans)
    return False


def main():
    gate_type = nondet_int()   # noqa: F821
    __ESBMC_assume(   # noqa: F821
        gate_type == GATE_PRIVACY_ORIGIN_TRIAL
        or gate_type == GATE_PRIVACY_SHIP
        or gate_type == GATE_TESTING_PLAN
        or gate_type == GATE_TESTING_SHIP
        or gate_type == GATE_ADOPTION_PLAN
        or gate_type == GATE_ADOPTION_SHIP
    )

    ans = [nondet_bool() for _ in range(N_FIELDS)]   # noqa: F821

    result = is_eligible_buggy(gate_type, ans)

    # Contract: privacy gates must use the privacy predicate.
    if gate_type == GATE_PRIVACY_ORIGIN_TRIAL or gate_type == GATE_PRIVACY_SHIP:
        # FAILS: is_eligible_buggy uses is_testing_eligible for privacy gates.
        assert result == is_privacy_eligible(ans)


main()
