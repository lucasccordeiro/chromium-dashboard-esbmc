# Buggy: overdue detection — use `<= -1` instead of `== -1` for newly_overdue.
# This would flag long-overdue gates as newly-overdue too.
# Expected verdict: FAILED (contract 3: mutually exclusive check fails).

MAX_DAYS_LOCAL = 30


def remaining_days(slo_limit: int, weekdays_elapsed: int) -> int:
    return slo_limit - weekdays_elapsed


def classify_overdue_buggy(slo_limit: int, weekdays_elapsed: int):
    """Buggy: uses <= instead of == for newly_overdue."""
    remaining = remaining_days(slo_limit, weekdays_elapsed)
    newly_overdue = (remaining <= -1)   # WRONG: should be == -1.
    long_overdue  = (remaining == -slo_limit)
    return newly_overdue, long_overdue


def main():
    slo_limit        = nondet_int()   # noqa: F821
    weekdays_elapsed = nondet_int()   # noqa: F821
    __ESBMC_assume(1 <= slo_limit <= MAX_DAYS_LOCAL)           # noqa: F821
    __ESBMC_assume(0 <= weekdays_elapsed <= 2 * MAX_DAYS_LOCAL)   # noqa: F821

    newly, long = classify_overdue_buggy(slo_limit, weekdays_elapsed)

    # Contract 1: newly_overdue iff exactly 1 weekday past deadline.
    assert newly == (weekdays_elapsed == slo_limit + 1)   # FAILS: <= matches more cases.


main()
