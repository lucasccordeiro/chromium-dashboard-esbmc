# Harness: internals/self_certify.py:is_adoption_eligible
#
# Contract: True iff ALL four adoption fields are set.
# Source: self_certify.py:93-100.

def is_adoption_eligible(
    adoption_fields_up_to_date: bool,
    adoption_style_aligned: bool,
    adoption_lead_time: bool,
    adoption_mdn_drafted: bool,
) -> bool:
    """Inline of self_certify.is_adoption_eligible."""
    return (
        adoption_fields_up_to_date
        and adoption_style_aligned
        and adoption_lead_time
        and adoption_mdn_drafted
    )


def main():
    up_to_date  = nondet_bool()   # noqa: F821
    aligned     = nondet_bool()   # noqa: F821
    lead_time   = nondet_bool()   # noqa: F821
    mdn_drafted = nondet_bool()   # noqa: F821

    result = is_adoption_eligible(up_to_date, aligned, lead_time, mdn_drafted)

    # Contract 1: any unset field means not eligible.
    if not up_to_date:
        assert not result
    if not aligned:
        assert not result
    if not lead_time:
        assert not result
    if not mdn_drafted:
        assert not result

    # Contract 2: all fields set means eligible.
    if up_to_date and aligned and lead_time and mdn_drafted:
        assert result

    # Contract 3: identity.
    assert result == (up_to_date and aligned and lead_time and mdn_drafted)


main()
