# Harness: internals/self_certify.py:is_eligible
#
# Contract: gate_type dispatch routes to the correct predicate.
#
# Gate type constants (mirrors core_enums.py):
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


def is_eligible(gate_type, ans) -> bool:
    """Inline of self_certify.is_eligible."""
    is_privacy  = gate_type == GATE_PRIVACY_ORIGIN_TRIAL or gate_type == GATE_PRIVACY_SHIP
    is_testing  = gate_type == GATE_TESTING_PLAN or gate_type == GATE_TESTING_SHIP
    is_adoption = gate_type == GATE_ADOPTION_PLAN or gate_type == GATE_ADOPTION_SHIP
    if is_privacy:
        return is_privacy_eligible(ans)
    if is_testing:
        return is_testing_eligible(ans)
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

    result = is_eligible(gate_type, ans)

    # Contract: privacy gates call is_privacy_eligible.
    if gate_type == GATE_PRIVACY_ORIGIN_TRIAL or gate_type == GATE_PRIVACY_SHIP:
        assert result == is_privacy_eligible(ans)

    # Contract: testing gates call is_testing_eligible.
    if gate_type == GATE_TESTING_PLAN or gate_type == GATE_TESTING_SHIP:
        assert result == is_testing_eligible(ans)

    # Contract: adoption gates call is_adoption_eligible.
    if gate_type == GATE_ADOPTION_PLAN or gate_type == GATE_ADOPTION_SHIP:
        assert result == is_adoption_eligible(ans)


main()
