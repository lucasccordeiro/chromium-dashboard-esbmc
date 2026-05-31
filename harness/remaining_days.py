# Harness: internals/slo.py:remaining_days
#
# remaining_days(requested_on, slo_limit) = slo_limit - weekdays_between(...)
#
# We model weekdays_between as a nondet int in [0, MAX_DAYS], since its own
# contracts are verified separately (weekdays_between_approx,
# weekdays_between_loop).
#
# Contracts:
#   1. When weekdays_elapsed == 0: remaining == slo_limit.
#   2. When weekdays_elapsed > slo_limit: remaining < 0 (overdue).
#   3. When weekdays_elapsed == slo_limit: remaining == 0 (due today).

MAX_DAYS_LOCAL = 30
INT_BOUND = 1 << 10   # slo_limit realistic range: 1..30 weekdays


def remaining_days(slo_limit: int, weekdays_elapsed: int) -> int:
    """Model of slo.remaining_days with weekdays_between abstracted."""
    return slo_limit - weekdays_elapsed


def main():
    slo_limit = nondet_int()  # noqa: F821
    __ESBMC_assume(1 <= slo_limit <= MAX_DAYS_LOCAL)  # noqa: F821

    weekdays_elapsed = nondet_int()  # noqa: F821
    __ESBMC_assume(0 <= weekdays_elapsed <= MAX_DAYS_LOCAL)  # noqa: F821

    result = remaining_days(slo_limit, weekdays_elapsed)

    # Contract 1: zero elapsed -> remaining equals slo_limit.
    if weekdays_elapsed == 0:
        assert result == slo_limit

    # Contract 2: past deadline -> result is negative.
    if weekdays_elapsed > slo_limit:
        assert result < 0

    # Contract 3: on deadline -> result is zero.
    if weekdays_elapsed == slo_limit:
        assert result == 0

    # Contract 4: result = slo_limit - weekdays_elapsed (identity).
    assert result == slo_limit - weekdays_elapsed


main()
