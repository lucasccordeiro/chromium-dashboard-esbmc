# Buggy: weekdays_between approximation branch.
# Mutation: multiply by 6 instead of 5 — wrong formula.
# Expected verdict: FAILED (result != calendar_days * 5 // 7).

from stubs import INT_BOUND

MAX_DAYS_LOCAL = 30


def weekdays_between_approx_buggy(calendar_days: int) -> int:
    """Buggy: uses 6/7 instead of 5/7."""
    return calendar_days * 6 // 7


def main():
    calendar_days = nondet_int()  # noqa: F821
    __ESBMC_assume(MAX_DAYS_LOCAL < calendar_days <= INT_BOUND)  # noqa: F821

    result = weekdays_between_approx_buggy(calendar_days)

    # The correct formula is 5/7; assert that — FAILS when buggy 6/7 differs.
    assert result == calendar_days * 5 // 7


main()
