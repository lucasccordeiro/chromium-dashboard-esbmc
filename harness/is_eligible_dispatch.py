# Harness: internals/self_certify.py:is_eligible
#
# Contract: gate_type dispatch routes to the correct predicate.
#
# ESBMC-Python pitfall: nondet_bool() in a list comprehension gives a fresh
# variable on each access, so the same ans[i] yields different values in
# is_eligible() vs the post-call assertion.  Fix: use explicit scalar vars
# passed as individual arguments; each call site receives the same values.
#
# Gate type constants (mirrors core_enums.py):
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


def is_eligible(gate_type, expl, lang, api_p, same,
                exist, common, err, inval, integ,
                upd, aligned, lead, mdn) -> bool:
    """Inline of self_certify.is_eligible with scalar arguments."""
    is_privacy  = gate_type == GATE_PRIVACY_ORIGIN_TRIAL or gate_type == GATE_PRIVACY_SHIP
    is_testing  = gate_type == GATE_TESTING_PLAN or gate_type == GATE_TESTING_SHIP
    is_adoption = gate_type == GATE_ADOPTION_PLAN or gate_type == GATE_ADOPTION_SHIP
    if is_privacy:
        return is_privacy_eligible(expl, lang, api_p, same)
    if is_testing:
        return is_testing_eligible(exist, common, err, inval, integ)
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

    # Symbolic scalar answer fields.
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

    result = is_eligible(gate_type, expl, lang, api_p, same,
                         exist, common, err, inval, integ,
                         upd, aligned, lead, mdn)

    # Contract: privacy gates call is_privacy_eligible.
    if gate_type == GATE_PRIVACY_ORIGIN_TRIAL or gate_type == GATE_PRIVACY_SHIP:
        assert result == is_privacy_eligible(expl, lang, api_p, same)

    # Contract: testing gates call is_testing_eligible.
    if gate_type == GATE_TESTING_PLAN or gate_type == GATE_TESTING_SHIP:
        assert result == is_testing_eligible(exist, common, err, inval, integ)

    # Contract: adoption gates call is_adoption_eligible.
    if gate_type == GATE_ADOPTION_PLAN or gate_type == GATE_ADOPTION_SHIP:
        assert result == is_adoption_eligible(upd, aligned, lead, mdn)


main()
