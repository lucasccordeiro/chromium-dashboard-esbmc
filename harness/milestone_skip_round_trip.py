# Harness: internals/ot_process_reminders.py — milestone-skip round-trip
#
# Chrome milestone 82 was skipped in the release sequence.  Two helpers
# navigate the sequence:
#
#   get_next_release_number(n): n == 81 → 83, else n + 1
#   get_previous_release_number(n): n == 83 → 81, else n - 1
#
# Contracts (for all n in [1, 200], n ≠ 82):
#   1. next(prev(n)) == n   — prev then next recovers n
#   2. prev(next(n)) == n   — next then prev recovers n
#
# n == 82 is excluded: it is the skipped milestone and is not a valid
# input to either function in production code.

MAX_MILESTONE = 200


def get_next_release_number(version_num: int) -> int:
    if version_num == 81:
        return 83
    return version_num + 1


def get_previous_release_number(version_num: int) -> int:
    if version_num == 83:
        return 81
    return version_num - 1


def main():
    n = nondet_int()                         # noqa: F821
    __ESBMC_assume(1 <= n <= MAX_MILESTONE)  # noqa: F821
    __ESBMC_assume(n != 82)                  # noqa: F821 — skipped milestone

    # Contract 1: prev → next round-trip.
    assert get_next_release_number(get_previous_release_number(n)) == n

    # Contract 2: next → prev round-trip.
    assert get_previous_release_number(get_next_release_number(n)) == n


main()
