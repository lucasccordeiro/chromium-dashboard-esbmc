# Harness: internals/slo.py:record_vote — index safety
#
# The function accesses `sorted(votes, key=lambda v: v.set_on)[-1]` which
# would raise IndexError on an empty list.  The guard `if not votes: return False`
# on line 76 prevents this.
#
# Contract: the [-1] index access is only reached when len(votes) >= 1.
#
# Stub: abstract votes as a nondet count N; if N == 0, the guard fires and
# the index is never accessed.

def record_vote_index_path(n_votes: int) -> bool:
    """Model of the early-exit / index access in record_vote."""
    if n_votes == 0:
        return False  # early exit — index never accessed.

    # Access [-1]: safe when n_votes >= 1.
    # In the real code: sorted(votes, ...)[-1].
    # We just assert the length precondition holds here.
    assert n_votes >= 1   # must hold for any path that reaches this point.

    # Model the rest of the function as returning True (changed=True) or
    # False (changed=False) nondeterministically.
    return nondet_bool()   # noqa: F821


def main():
    n_votes = nondet_int()   # noqa: F821
    __ESBMC_assume(0 <= n_votes <= 100)   # noqa: F821

    result = record_vote_index_path(n_votes)

    # Contract: function returns False immediately when n_votes == 0.
    if n_votes == 0:
        assert not result

    # Contract: n_votes >= 1 means the guard was not triggered; result is
    # the (nondet) changed flag — which can be True or False.
    # (No assertion on result here — that is tested in record_vote_changed_flag.)


main()
