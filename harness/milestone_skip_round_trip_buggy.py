# Buggy: get_next_release_number jumps to 84 instead of 83.
# This breaks the round-trip at n == 83:
#   prev(83) == 81, next(81) == 84 ≠ 83  → Contract 1 violated.
# Expected verdict: FAILED.

MAX_MILESTONE = 200


def get_next_release_number_buggy(version_num: int) -> int:
    if version_num == 81:
        return 84   # wrong: should be 83
    return version_num + 1


def get_previous_release_number(version_num: int) -> int:
    if version_num == 83:
        return 81
    return version_num - 1


def main():
    n = nondet_int()                         # noqa: F821
    __ESBMC_assume(1 <= n <= MAX_MILESTONE)  # noqa: F821
    __ESBMC_assume(n != 82)                  # noqa: F821

    # Contract 1: prev → next round-trip — FAILS at n == 83.
    assert get_next_release_number_buggy(get_previous_release_number(n)) == n


main()
