# Harness: internals/ot_process_reminders.py:diff_days / diff_weeks
#
# diff_days(t1, t2)  = (t1 - t2).days           — can be negative
# diff_weeks(t1, t2) = diff_days(t1, t2) // 7   — safe (7 != 0)
#
# Contracts:
#   1. diff_weeks * 7 <= diff_days < (diff_weeks + 1) * 7  (floor-division property)
#   2. Division by 7 is safe (7 is a non-zero literal).
#   3. diff_weeks can be negative when t1 < t2 (not a bug — documented).

INT_BOUND = 1 << 14   # covers ±16 384 days (~45 years)


def diff_days(days_raw: int) -> int:
    """Inline of diff_days: (t1-t2).days abstracted as nondet integer."""
    return days_raw


def diff_weeks(days_raw: int) -> int:
    """Inline of diff_weeks: diff_days // 7."""
    return diff_days(days_raw) // 7


def main():
    days_raw = nondet_int()  # noqa: F821
    __ESBMC_assume(-INT_BOUND <= days_raw <= INT_BOUND)  # noqa: F821

    d = diff_days(days_raw)
    w = diff_weeks(days_raw)

    # Contract 1: floor-division relationship.
    assert w * 7 <= d
    assert d < (w + 1) * 7

    # Contract 2 (implicit via Phase 2 --overflow-check): no division-by-zero
    # (7 is a literal constant, never zero).

    # Contract 3: negative diff_days produces non-positive diff_weeks.
    if d < 0:
        assert w <= 0


main()
