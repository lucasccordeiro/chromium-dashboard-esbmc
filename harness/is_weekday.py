# Harness: internals/slo.py:is_weekday
#
# Contract: is_weekday(d) returns True iff d.weekday() in {0,1,2,3,4} (Mon-Fri),
#           False for weekday in {5,6} (Sat-Sun).
#
# Stub: abstract datetime as its weekday() integer in [0,6].

from stubs import INT_BOUND


def is_weekday(weekday: int) -> bool:
    """Inline of slo.is_weekday: return weekday < 5."""
    return weekday < 5


def main():
    # Symbolic weekday in [0, 6].
    weekday = nondet_int()  # noqa: F821
    __ESBMC_assume(0 <= weekday <= 6)  # noqa: F821

    result = is_weekday(weekday)

    # Contract 1: result is True iff weekday is Mon-Fri (0-4).
    assert result == (weekday < 5)

    # Contract 2: Sat (5) and Sun (6) are never weekdays.
    if weekday >= 5:
        assert not result

    # Contract 3: Mon through Fri are always weekdays.
    if weekday < 5:
        assert result


main()
