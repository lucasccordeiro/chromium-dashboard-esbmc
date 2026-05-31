# Buggy: is_eligible dispatch — swap privacy and testing routes.
# Expected verdict: FAILED (privacy gate returns is_testing_eligible result).
# Uses scalar args to avoid the nondet_bool list-access pitfall.

GATE_PRIVACY_ORIGIN_TRIAL = 1
GATE_PRIVACY_SHIP         = 2
GATE_TESTING_PLAN         = 3
GATE_TESTING_SHIP         = 4
GATE_ADOPTION_PLAN        = 5
GATE_ADOPTION_SHIP        = 6


def is_privacy_eligible(expl, lang, api_p, same) -> bool:
    return expl and (lang or api_p or same)


def is_testing_eligible(exist, common, err, inval, integ) -> bool:
    return exist and common and err and inval and integ


def is_adoption_eligible(upd, aligned, lead, mdn) -> bool:
    return upd and aligned and lead and mdn


def is_eligible_buggy(gate_type, expl, lang, api_p, same,
                      exist, common, err, inval, integ,
                      upd, aligned, lead, mdn) -> bool:
    """Buggy: privacy and testing routes are swapped."""
    is_privacy  = gate_type == GATE_PRIVACY_ORIGIN_TRIAL or gate_type == GATE_PRIVACY_SHIP
    is_testing  = gate_type == GATE_TESTING_PLAN or gate_type == GATE_TESTING_SHIP
    is_adoption = gate_type == GATE_ADOPTION_PLAN or gate_type == GATE_ADOPTION_SHIP
    if is_privacy:
        return is_testing_eligible(exist, common, err, inval, integ)  # WRONG
    if is_testing:
        return is_privacy_eligible(expl, lang, api_p, same)           # WRONG
    if is_adoption:
        return is_adoption_eligible(upd, aligned, lead, mdn)
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
    expl    = nondet_bool()   # noqa: F821
    lang    = nondet_bool()   # noqa: F821
    api_p   = nondet_bool()   # noqa: F821
    same    = nondet_bool()   # noqa: F821
    exist   = nondet_bool()   # noqa: F821
    common  = nondet_bool()   # noqa: F821
    err     = nondet_bool()   # noqa: F821
    inval   = nondet_bool()   # noqa: F821
    integ   = nondet_bool()   # noqa: F821
    upd     = nondet_bool()   # noqa: F821
    aligned = nondet_bool()   # noqa: F821
    lead    = nondet_bool()   # noqa: F821
    mdn     = nondet_bool()   # noqa: F821

    result = is_eligible_buggy(gate_type, expl, lang, api_p, same,
                               exist, common, err, inval, integ,
                               upd, aligned, lead, mdn)

    # Contract: privacy gates must use the privacy predicate.
    if gate_type == GATE_PRIVACY_ORIGIN_TRIAL or gate_type == GATE_PRIVACY_SHIP:
        # FAILS: is_eligible_buggy uses is_testing_eligible for privacy gates.
        assert result == is_privacy_eligible(expl, lang, api_p, same)


main()
