# Harness: internals/slo.py:weekdays_between — approximation branch
#
# When calendar_days > MAX_DAYS (30), the function returns
# `calendar_days * 5 // 7` instead of counting weekdays in a loop.
#
# Contract:
#   result = calendar_days * 5 // 7
#   result in [0, calendar_days]   (approximation never exceeds total days)
#
# Stub: abstract dates as nondet calendar_days > MAX_DAYS.

from stubs import MAX_DAYS, INT_BOUND

MAX_DAYS_LOCAL = 30


def weekdays_between_approx(calendar_days: int) -> int:
    """Inline of the approximation branch of slo.weekdays_between."""
    return calendar_days * 5 // 7


def main():
    calendar_days = nondet_int()  # noqa: F821
    __ESBMC_assume(MAX_DAYS_LOCAL < calendar_days <= INT_BOUND)  # noqa: F821

    result = weekdays_between_approx(calendar_days)

    # Contract 1: result equals the approximation formula.
    assert result == calendar_days * 5 // 7

    # Contract 2: approximation does not exceed total calendar days.
    assert 0 <= result <= calendar_days

    # Contract 3: result is non-negative (calendar_days > 0 by assumption).
    assert result >= 0


main()
