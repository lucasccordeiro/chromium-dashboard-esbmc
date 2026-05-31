# Buggy: diff_weeks — divide by 8 instead of 7.
# Expected verdict: FAILED (floor-division property violated).

INT_BOUND = 1 << 14


def diff_weeks_buggy(days_raw: int) -> int:
    """Buggy: uses 8 instead of 7."""
    return days_raw // 8


def main():
    days_raw = nondet_int()  # noqa: F821
    __ESBMC_assume(-INT_BOUND <= days_raw <= INT_BOUND)  # noqa: F821

    w = diff_weeks_buggy(days_raw)

    # Contract: w * 7 <= days_raw < (w+1)*7 — FAILS with //8.
    assert w * 7 <= days_raw
    assert days_raw < (w + 1) * 7


main()
