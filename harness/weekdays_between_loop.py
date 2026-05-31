# Harness: internals/slo.py:weekdays_between — loop branch
#
# When calendar_days <= MAX_DAYS, the function counts weekdays in a loop.
# Loop invariant: 0 <= weekday_counter <= MAX_DAYS.
# The loop guard `weekday_counter < MAX_DAYS` ensures the counter never
# exceeds MAX_DAYS regardless of input.
#
# Stub: abstract the day-step sequence as a nondet weekday sequence.
# We model the loop directly — IS_WEEKDAY(d) abstracted as nondet bool
# per iteration — because modelling datetime.astimezone is not feasible.

MAX_DAYS_LOCAL = 30


def weekdays_between_loop(calendar_days: int) -> int:
    """Model of the loop branch of slo.weekdays_between.

    Instead of stepping through datetime objects, we accept a nondet
    sequence of per-day is_weekday flags.  ESBMC symbolically explores
    all flag assignments.
    """
    weekday_counter = 0
    for _ in range(calendar_days):
        if weekday_counter >= MAX_DAYS_LOCAL:
            break
        # Each day is symbolically either a weekday or a weekend day.
        day_is_weekday = nondet_bool()  # noqa: F821
        if day_is_weekday:
            weekday_counter += 1
        # Loop invariant maintained after each step.
        assert 0 <= weekday_counter <= MAX_DAYS_LOCAL
    return weekday_counter


def main():
    calendar_days = nondet_int()  # noqa: F821
    __ESBMC_assume(0 <= calendar_days <= MAX_DAYS_LOCAL)  # noqa: F821

    result = weekdays_between_loop(calendar_days)

    # Post-condition: result is bounded by MAX_DAYS.
    assert 0 <= result <= MAX_DAYS_LOCAL

    # Post-condition: result cannot exceed calendar_days.
    assert result <= calendar_days


main()
