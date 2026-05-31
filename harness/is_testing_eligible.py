# Harness: internals/self_certify.py:is_testing_eligible
#
# Contract: True iff ALL five coverage fields are set.
# Source: self_certify.py:82-90.

def is_testing_eligible(
    covers_existence: bool,
    covers_common_cases: bool,
    covers_errors: bool,
    covers_invalidation: bool,
    covers_integration: bool,
) -> bool:
    """Inline of self_certify.is_testing_eligible."""
    return (
        covers_existence
        and covers_common_cases
        and covers_errors
        and covers_invalidation
        and covers_integration
    )


def main():
    existence    = nondet_bool()   # noqa: F821
    common       = nondet_bool()   # noqa: F821
    errors       = nondet_bool()   # noqa: F821
    invalidation = nondet_bool()   # noqa: F821
    integration  = nondet_bool()   # noqa: F821

    result = is_testing_eligible(existence, common, errors, invalidation, integration)

    # Contract 1: any unset field means not eligible.
    if not existence:
        assert not result
    if not common:
        assert not result
    if not errors:
        assert not result
    if not invalidation:
        assert not result
    if not integration:
        assert not result

    # Contract 2: all fields set means eligible.
    if existence and common and errors and invalidation and integration:
        assert result

    # Contract 3: identity.
    assert result == (existence and common and errors and invalidation and integration)


main()
