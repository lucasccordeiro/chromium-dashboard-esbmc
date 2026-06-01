# Harness: internals/slo.py:record_vote — changed-flag invariant
#
# Source (verbatim, d0d21c8), internals/slo.py:51-103.  `changed` starts False
# and is set True at exactly five mutation sites, each paired with a real gate
# field write:
#     1. REQUESTING + requested_on is None   -> gate.requested_on   = ...
#     2. RESPONSE   + responded_on is None   -> gate.responded_on   = ...   (+ maybe requested_on)
#     3. finished_rework                      -> gate.needs_work_elapsed / needs_work_started_on
#     4. sent_back_for_rework                 -> gate.needs_work_started_on = ...
#     5. resolved   + resolved_on is None    -> gate.resolved_on    = ...
# `changed` is never assigned False after init.  Two early exits return False
# with no mutation: `if not votes` and `latest_state == NO_RESPONSE`.
#
# Contract (Tier 4, row 12):
#   (a) soundness/completeness: changed is True  iff  at least one gate field
#       was mutated;
#   (b) monotonicity: changed never reverts to False once set (no spurious
#       True -> False toggle) — a corollary of (a) here, since `changed` is the
#       disjunction of the five branch flags.
#
# Stub: each branch's fully-evaluated guard (state matches AND the relevant
# field condition holds) is abstracted as an independent nondet bool.  The
# branches are sequential `if`s upstream (not elif), so they fire independently.
# `fields_written` is a witness counter incremented at each real field write.


def record_vote_changed(no_votes, no_response,
                        b_request, b_respond, b_finished, b_sentback, b_resolved):
    """Structural model of record_vote's `changed` bookkeeping."""
    if no_votes:
        return False, 0          # `if not votes: return False`
    if no_response:
        return False, 0          # NO_RESPONSE never changes SLO state

    changed = False
    fields_written = 0

    if b_request:                # requested_on is None & REQUESTING
        fields_written += 1      # gate.requested_on = latest_vote.set_on
        changed = True

    if b_respond:                # responded_on is None & RESPONSE
        fields_written += 1      # gate.responded_on = ... (+ maybe requested_on)
        changed = True

    if b_finished:               # finished_rework
        fields_written += 1      # gate.needs_work_elapsed / needs_work_started_on
        changed = True

    if b_sentback:               # sent_back_for_rework
        fields_written += 1      # gate.needs_work_started_on = latest_vote.set_on
        changed = True

    if b_resolved:               # resolved & resolved_on is None
        fields_written += 1      # gate.resolved_on = latest_vote.set_on
        changed = True

    return changed, fields_written


def main():
    no_votes   = nondet_bool()   # noqa: F821
    no_response = nondet_bool()  # noqa: F821
    b_request  = nondet_bool()   # noqa: F821
    b_respond  = nondet_bool()   # noqa: F821
    b_finished = nondet_bool()   # noqa: F821
    b_sentback = nondet_bool()   # noqa: F821
    b_resolved = nondet_bool()   # noqa: F821

    changed, fields_written = record_vote_changed(
        no_votes, no_response,
        b_request, b_respond, b_finished, b_sentback, b_resolved)

    # Contract: changed is True iff at least one gate field was mutated.
    # Monotonicity (no spurious True -> False toggle) is subsumed here, since
    # `changed` is only ever assigned True; the buggy variant breaks exactly
    # this by resetting changed=False after a field write.
    assert changed == (fields_written >= 1)


main()
