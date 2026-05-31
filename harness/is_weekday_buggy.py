# Buggy harness: is_weekday — Saturday admitted as a weekday (off-by-one).
#
# Mutation: replace `weekday < 5` with `weekday <= 5`.
# Expected verdict: FAILED (Saturday triggers contract 2).

from stubs import INT_BOUND


def is_weekday_buggy(weekday: int) -> bool:
    """Buggy: <= 5 admits Saturday as a weekday."""
    return weekday <= 5


def main():
    weekday = nondet_int()  # noqa: F821
    __ESBMC_assume(0 <= weekday <= 6)  # noqa: F821

    result = is_weekday_buggy(weekday)

    # Contract: Sat (5) and Sun (6) are never weekdays.
    if weekday >= 5:
        assert not result   # FAILS for weekday=5 (Saturday).


main()
