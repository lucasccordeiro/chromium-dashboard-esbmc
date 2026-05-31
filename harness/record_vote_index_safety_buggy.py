# Buggy: record_vote — drop the empty-votes guard.
# Expected verdict: FAILED (assert n_votes >= 1 fails when n_votes=0).


def record_vote_index_path_buggy(n_votes: int) -> bool:
    """Buggy: drops the `if not votes: return False` guard."""
    # No early exit — proceeds directly to index access.
    assert n_votes >= 1   # FAILS when n_votes = 0.
    return nondet_bool()   # noqa: F821


def main():
    n_votes = nondet_int()   # noqa: F821
    __ESBMC_assume(0 <= n_votes <= 100)   # noqa: F821

    record_vote_index_path_buggy(n_votes)


main()
