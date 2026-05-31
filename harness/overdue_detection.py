# Harness: internals/reminders.py:get_overdue_gates_and_features — overdue detection
#
# The overdue detection compares `remaining_days(...)` against -1 and -slo_limit:
#
#   if initial_remaining == -1:            → newly overdue (1 weekday past deadline)
#   elif initial_remaining == -slo_limit:  → long overdue  (slo_limit weekdays past)
#
# Contract:
#   1. `remaining == -1` iff exactly 1 weekday past deadline.
#   2. `remaining == -slo_limit` iff exactly slo_limit weekdays past deadline.
#   3. These two cases are mutually exclusive when slo_limit > 1.
#
# remaining_days = slo_limit - weekdays_elapsed.
# So `remaining == -k` iff `weekdays_elapsed == slo_limit + k`.

MAX_DAYS_LOCAL = 30


def remaining_days(slo_limit: int, weekdays_elapsed: int) -> int:
    return slo_limit - weekdays_elapsed


def classify_overdue(slo_limit: int, weekdays_elapsed: int):
    """Model of the overdue-detection branch in get_overdue_gates_and_features."""
    remaining = remaining_days(slo_limit, weekdays_elapsed)
    newly_overdue = (remaining == -1)
    long_overdue  = (remaining == -slo_limit)
    return newly_overdue, long_overdue


def main():
    slo_limit        = nondet_int()   # noqa: F821
    weekdays_elapsed = nondet_int()   # noqa: F821
    __ESBMC_assume(1 <= slo_limit <= MAX_DAYS_LOCAL)           # noqa: F821
    __ESBMC_assume(0 <= weekdays_elapsed <= 2 * MAX_DAYS_LOCAL)   # noqa: F821

    newly, long = classify_overdue(slo_limit, weekdays_elapsed)

    remaining = slo_limit - weekdays_elapsed

    # Contract 1: newly_overdue iff exactly 1 weekday past deadline.
    assert newly == (weekdays_elapsed == slo_limit + 1)

    # Contract 2: long_overdue iff exactly slo_limit weekdays past deadline.
    assert long == (weekdays_elapsed == 2 * slo_limit)

    # Contract 3: mutually exclusive when slo_limit > 1 (i.e. -1 != -slo_limit).
    if slo_limit > 1:
        assert not (newly and long)


main()
