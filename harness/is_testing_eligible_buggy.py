# Buggy: is_testing_eligible — drop the covers_integration check.
# Expected verdict: FAILED (integration=False does not prevent True result).


def is_testing_eligible_buggy(
    covers_existence: bool,
    covers_common_cases: bool,
    covers_errors: bool,
    covers_invalidation: bool,
    covers_integration: bool,  # noqa: ARG001 — unused in buggy version
) -> bool:
    """Buggy: drops the covers_integration check."""
    return (
        covers_existence
        and covers_common_cases
        and covers_errors
        and covers_invalidation
    )


def main():
    existence    = nondet_bool()   # noqa: F821
    common       = nondet_bool()   # noqa: F821
    errors       = nondet_bool()   # noqa: F821
    invalidation = nondet_bool()   # noqa: F821
    integration  = nondet_bool()   # noqa: F821

    result = is_testing_eligible_buggy(existence, common, errors, invalidation, integration)

    # Contract: if covers_integration is not set, should not be eligible.
    if not integration:
        assert not result   # FAILS when the other four fields are all True.


main()
