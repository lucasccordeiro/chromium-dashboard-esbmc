#!/usr/bin/env python3
# Standalone reproducer for Finding D.
#
# api/reviews_api.py:VotesAPI.do_post does:
#   new_state = self.get_int_param('state', validator=Vote.is_valid_state)
#
# Both framework/basehandlers.py:get_param and get_int_param use a `val and ...`
# short-circuit that skips validation for falsy values.  A JSON body
# {"state": 0} (or {"state": false}) is falsy, so Vote.is_valid_state is never
# consulted and an invalid vote state is accepted.
#
# This inlines the exact upstream logic (no Flask/NDB needed) and shows that
# state 0 and state False slip through unvalidated.

# Vote.VOTE_VALUES keys are the valid states 1..11 (NA .. NA_VERIFIED).
VOTE_VALUES = {i: f'state_{i}' for i in range(1, 12)}


def is_valid_state(new_state):
    """Vote.is_valid_state — verbatim semantics."""
    return new_state in VOTE_VALUES


class Abort400(Exception):
    pass


def get_param(json_body, name, default=None, required=True, validator=None):
    """framework/basehandlers.py:get_param — inlined verbatim logic."""
    val = json_body.get(name, default)
    if required and val is None:
        raise Abort400('Missing parameter %r' % name)
    if val and validator and not validator(val):     # <-- `val and` short-circuit
        raise Abort400('Invalid value for parameter %r' % name)
    return val


def get_int_param(json_body, name, validator=None):
    """framework/basehandlers.py:get_int_param — inlined verbatim logic."""
    val = get_param(json_body, name, validator=validator)
    if val and type(val) != int:                     # <-- `val and` short-circuit
        raise Abort400('Parameter %r was not an int' % name)
    return val


def submit_vote(json_body):
    """Model of VotesAPI.do_post's state-parsing step."""
    new_state = get_int_param(json_body, 'state', validator=is_valid_state)
    return new_state


def main():
    # Valid state: accepted, validates correctly.
    assert submit_vote({'state': 5}) == 5

    # Invalid state 0: SHOULD be rejected (is_valid_state(0) is False) but the
    # `val and` short-circuit skips the validator, so it is accepted.
    accepted = submit_vote({'state': 0})
    assert accepted == 0
    assert not is_valid_state(accepted), 'state 0 is not a valid vote state'
    print('BUG: state=0 accepted; is_valid_state(0) =', is_valid_state(accepted))

    # Invalid state False (JSON false): also slips through, returned as a bool.
    accepted_bool = submit_vote({'state': False})
    assert accepted_bool is False
    print('BUG: state=false accepted; type =', type(accepted_bool).__name__,
          'is_valid_state =', is_valid_state(accepted_bool))

    # A non-falsy invalid state IS correctly rejected, proving the gap is
    # specific to falsy values.
    try:
        submit_vote({'state': 99})
        print('ERROR: state=99 should have been rejected')
    except Abort400 as e:
        print('OK: state=99 correctly rejected ->', e)


if __name__ == '__main__':
    main()
