# Buggy: weekdays_between loop — initialise counter at 1 instead of 0.
# With weekday_counter = 1 and calendar_days = 0 the loop body never runs,
# so the function returns 1, violating the postcondition result <= calendar_days.
# Expected verdict: FAILED (result <= calendar_days violated at calendar_days=0).

MAX_DAYS_LOCAL = 30


def weekdays_between_loop_buggy(calendar_days: int) -> int:
    """Buggy: starts counter at 1 instead of 0."""
    weekday_counter = 1   # off-by-one initialisation
    for _ in range(calendar_days):
        if weekday_counter >= MAX_DAYS_LOCAL:
            break
        day_is_weekday = nondet_bool()  # noqa: F821
        if day_is_weekday:
            weekday_counter += 1
    return weekday_counter


def main():
    calendar_days = nondet_int()  # noqa: F821
    __ESBMC_assume(0 <= calendar_days <= MAX_DAYS_LOCAL)  # noqa: F821

    result = weekdays_between_loop_buggy(calendar_days)

    # Postcondition: result cannot exceed calendar_days.
    # FAILS when calendar_days=0: result=1 > 0.
    assert result <= calendar_days


main()
