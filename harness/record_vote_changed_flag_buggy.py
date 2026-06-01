# Buggy: record_vote changed-flag — spurious True -> False toggle.
# Expected verdict: FAILED.
#
# Mutation: the `resolved` branch writes gate.resolved_on (a real field
# mutation) but then resets `changed = False` instead of setting it True.
# When an earlier branch already set changed=True, this reverts it: the flag
# no longer reflects that fields were mutated, violating both the iff contract
# and monotonicity (no spurious True -> False toggle).


def record_vote_changed_buggy(no_votes, no_response,
                              b_request, b_respond, b_finished, b_sentback, b_resolved):
    if no_votes:
        return False, 0
    if no_response:
        return False, 0

    changed = False
    fields_written = 0

    if b_request:
        fields_written += 1
        changed = True

    if b_respond:
        fields_written += 1
        changed = True

    if b_finished:
        fields_written += 1
        changed = True

    if b_sentback:
        fields_written += 1
        changed = True

    if b_resolved:
        fields_written += 1
        changed = False          # BUG: should be `changed = True`

    return changed, fields_written


def main():
    no_votes   = nondet_bool()   # noqa: F821
    no_response = nondet_bool()  # noqa: F821
    b_request  = nondet_bool()   # noqa: F821
    b_respond  = nondet_bool()   # noqa: F821
    b_finished = nondet_bool()   # noqa: F821
    b_sentback = nondet_bool()   # noqa: F821
    b_resolved = nondet_bool()   # noqa: F821

    changed, fields_written = record_vote_changed_buggy(
        no_votes, no_response,
        b_request, b_respond, b_finished, b_sentback, b_resolved)

    # FAILS: e.g. b_request=True, b_resolved=True -> fields_written=2 but
    # changed=False, so changed != (fields_written >= 1).
    assert changed == (fields_written >= 1)


main()
