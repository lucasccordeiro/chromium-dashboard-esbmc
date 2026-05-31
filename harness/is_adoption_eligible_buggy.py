# Buggy: is_adoption_eligible — drop adoption_lead_time check.
# Expected verdict: FAILED (lead_time=False does not prevent True result).


def is_adoption_eligible_buggy(
    adoption_fields_up_to_date: bool,
    adoption_style_aligned: bool,
    adoption_lead_time: bool,     # noqa: ARG001 — unused in buggy version
    adoption_mdn_drafted: bool,
) -> bool:
    """Buggy: drops the adoption_lead_time check."""
    return (
        adoption_fields_up_to_date
        and adoption_style_aligned
        and adoption_mdn_drafted
    )


def main():
    up_to_date  = nondet_bool()   # noqa: F821
    aligned     = nondet_bool()   # noqa: F821
    lead_time   = nondet_bool()   # noqa: F821
    mdn_drafted = nondet_bool()   # noqa: F821

    result = is_adoption_eligible_buggy(up_to_date, aligned, lead_time, mdn_drafted)

    # Contract: lead_time unset => not eligible.
    if not lead_time:
        assert not result   # FAILS when up_to_date, aligned, mdn_drafted are all True.


main()
