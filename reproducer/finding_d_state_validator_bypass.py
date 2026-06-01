#!/usr/bin/env python3
# Standalone reproducer for Finding D (chromium-dashboard @ d0d21c8).
#
# api/reviews_api.py:78  VotesAPI.do_post:
#   new_state = self.get_int_param('state', validator=Vote.is_valid_state)
#
# framework/basehandlers.py:124 (get_param) and :141 (get_int_param) both guard
# validation with a `val and ...` short-circuit, so a falsy `state` (JSON 0 or
# false) skips BOTH the Vote.is_valid_state validator and the int type check.
#
# The bypassed value is NOT recorded: internals/approval_defs.py:466-467
# (set_vote) re-checks `if not Vote.is_valid_state(new_state): raise ValueError`.
# That raise is bare (not self.abort(400, ...)), and APIHandler.post
# (basehandlers.py:275) has no `except ValueError`, so it propagates to Flask
# as HTTP 500 — the same bare-raise -> 500 mechanism as Finding A.
#
# This inlines the exact upstream logic (no Flask/NDB) and shows: (1) the
# helpers accept falsy invalid states, and (2) set_vote then raises a bare
# ValueError that would surface as HTTP 500 rather than a clean 400.

# Vote.VOTE_VALUES keys are the valid states 1..11 (NA .. NA_VERIFIED).
# PREPARING = 0 is explicitly "Not used" (review_models.py:96).
VOTE_VALUES = {i: f'state_{i}' for i in range(1, 12)}


def is_valid_state(new_state):
    """Vote.is_valid_state — verbatim semantics (review_models.py:172-174)."""
    return new_state in VOTE_VALUES


class Abort400(Exception):
    """Models self.abort(400, ...) — a clean Bad Request."""


def get_param(json_body, name, default=None, required=True, validator=None):
    """framework/basehandlers.py:116-128 — inlined verbatim logic."""
    val = json_body.get(name, default)
    if required and val is None:
        raise Abort400('Missing parameter %r' % name)
    if val and validator and not validator(val):     # :124 `val and` short-circuit
        raise Abort400('Invalid value for parameter %r' % name)
    return val


def get_int_param(json_body, name, validator=None):
    """framework/basehandlers.py:130-143 — inlined verbatim logic."""
    val = get_param(json_body, name, validator=validator)
    if val and type(val) != int:                     # :141 `val and` short-circuit
        raise Abort400('Parameter %r was not an int' % name)
    return val


def set_vote(new_state):
    """internals/approval_defs.py:466-467 — the downstream backstop.

    Note the bare `raise ValueError` (not self.abort(400, ...)).
    """
    if not is_valid_state(new_state):
        raise ValueError('Invalid approval state')
    return 'recorded state %r' % new_state


def submit_vote(json_body):
    """Model of VotesAPI.do_post: parse 'state', then set_vote.

    Returns the HTTP status that the client would observe.
    """
    try:
        new_state = get_int_param(json_body, 'state', validator=is_valid_state)
    except Abort400:
        return 400                       # clean rejection at the API boundary
    try:
        set_vote(new_state)
        return 200
    except ValueError:
        # Bare ValueError from set_vote; APIHandler.post has no except ValueError
        # (basehandlers.py:275), so Flask returns HTTP 500.
        return 500


def main():
    # Valid state: validated and recorded -> 200.
    assert submit_vote({'state': 5}) == 200
    print('OK:  state=5  -> HTTP 200 (recorded)')

    # Falsy invalid states bypass get_param/get_int_param validation, reach
    # set_vote, and trigger a bare ValueError -> HTTP 500 (expected: 400).
    for bad in (0, False):
        # The helper itself does NOT reject the value (proves the bypass):
        accepted = get_int_param({'state': bad}, 'state', validator=is_valid_state)
        assert not is_valid_state(accepted), 'helper accepted an invalid state'
        code = submit_vote({'state': bad})
        assert code == 500, f'expected 500, got {code}'
        print(f'BUG: state={bad!r} -> helper accepts it, set_vote raises bare '
              f'ValueError -> HTTP {code} (expected 400)')

    # A non-falsy invalid state IS rejected cleanly at the boundary (HTTP 400),
    # proving the gap is specific to falsy values.
    code = submit_vote({'state': 99})
    assert code == 400, f'expected 400, got {code}'
    print('OK:  state=99 -> HTTP 400 (rejected at API boundary)')


if __name__ == '__main__':
    main()
