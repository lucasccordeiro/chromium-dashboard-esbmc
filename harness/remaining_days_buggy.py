# Buggy: remaining_days — negate: returns weekdays_elapsed - slo_limit.
# Expected verdict: FAILED (contract 1: when elapsed=0, result=-slo_limit != slo_limit).

MAX_DAYS_LOCAL = 30


def remaining_days_buggy(slo_limit: int, weekdays_elapsed: int) -> int:
    """Buggy: returns elapsed - limit instead of limit - elapsed."""
    return weekdays_elapsed - slo_limit


def main():
    slo_limit = nondet_int()  # noqa: F821
    __ESBMC_assume(1 <= slo_limit <= MAX_DAYS_LOCAL)  # noqa: F821

    weekdays_elapsed = nondet_int()  # noqa: F821
    __ESBMC_assume(0 <= weekdays_elapsed <= MAX_DAYS_LOCAL)  # noqa: F821

    result = remaining_days_buggy(slo_limit, weekdays_elapsed)

    # Contract 1: zero elapsed -> remaining equals slo_limit.
    if weekdays_elapsed == 0:
        assert result == slo_limit   # FAILS: result is -slo_limit.


main()
