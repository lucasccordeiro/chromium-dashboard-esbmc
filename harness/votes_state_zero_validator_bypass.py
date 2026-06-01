# Harness: api/reviews_api.py:VotesAPI.do_post — Finding D
#
# Source: reviews_api.py
#   new_state = self.get_int_param('state', validator=Vote.is_valid_state)
#
# basehandlers.get_int_param (framework/basehandlers.py) delegates to get_param
# and then type-checks the result:
#
#   def get_param(self, name, default=None, required=True, validator=None, ...):
#       val = json_body.get(name, default)
#       if required and val is None:
#           self.abort(400, ...)
#       if val and validator and not validator(val):   # <-- `val and` short-circuit
#           self.abort(400, ...)
#       ...
#       return val
#
#   def get_int_param(self, name, ..., validator=None, ...):
#       val = self.get_param(name, ..., validator=validator, ...)
#       if val and type(val) != int:                   # <-- `val and` short-circuit
#           self.abort(400, ...)
#       return val
#
# Vote.is_valid_state(s) == (s in Vote.VOTE_VALUES), whose keys are the valid
# vote states 1..11.  In particular is_valid_state(0) is False.
#
# Defect: a JSON body {"state": 0} makes `val = 0`, which is falsy.  BOTH the
# `val and validator and not validator(val)` guard in get_param AND the
# `val and type(val) != int` guard in get_int_param short-circuit on the falsy
# 0, so the Vote.is_valid_state validator is never consulted.  An invalid vote
# state 0 (== Gate.PREPARING, not a member of Vote.VOTE_VALUES) is returned from
# the helper instead of being rejected with HTTP 400 at the API boundary.
#
# This harness models the get_param/get_int_param acceptance gate only; it FAILS
# at state == 0, witnessing the validation bypass.  Downstream the invalid value
# is NOT recorded: approval_defs.set_vote re-checks is_valid_state and raises a
# bare ValueError (approval_defs.py:466-467).  Because that raise is bare (not
# self.abort) and APIHandler.post has no `except ValueError`, the observable
# symptom is HTTP 500 — the same bare-raise -> 500 mechanism as Finding A, not a
# recorded-bad-data bug.  See bug-reports/finding-d-...md for the full chain.
#
# Expected verdict: FAILED (the post-validation `is_valid` contract is violated
# at state == 0).
#
# Empirical reproduction:
#   POST /api/v0/votes ... {"state": 0}
#   → validator Vote.is_valid_state(0) is skipped; helper accepts state 0;
#     set_vote then raises a bare ValueError -> HTTP 500 (expected: HTTP 400).
#
# Proposed fix: drop the `val and` short-circuit so falsy values are still
# validated, e.g. `if val is not None and validator and not validator(val):`
# in get_param (and the analogous `val is not None` in get_int_param).

VALID_STATE_LO = 1     # Vote.VOTE_VALUES keys run 1..11 (NA .. NA_VERIFIED)
VALID_STATE_HI = 11


def is_valid_state(state: int) -> bool:
    """Model of Vote.is_valid_state: state in VOTE_VALUES (keys 1..11)."""
    return VALID_STATE_LO <= state <= VALID_STATE_HI


def get_int_param_state(state: int) -> bool:
    """Model the get_param + get_int_param pipeline for 'state'.

    Returns True if the value is accepted (no abort), False if aborted.
    The `state != 0` factor models Python truthiness of an int: the `val and`
    short-circuit skips the validator exactly when val is falsy (state == 0).
    """
    # required=True: val is None would abort — but an int 'state' is not None.
    # get_param validator guard: `if val and validator and not validator(val)`.
    if (state != 0) and (not is_valid_state(state)):
        return False   # abort 400
    # get_int_param type guard: `if val and type(val) != int` — state is an int,
    # so the type check never fires for int inputs.
    return True        # accepted


def main():
    # Symbolically explore a client-supplied integer 'state'.
    state = nondet_int()                         # noqa: F821
    __ESBMC_assume(0 <= state <= VALID_STATE_HI)  # noqa: F821

    accepted = get_int_param_state(state)

    # Contract: any accepted state must be a valid vote state.  The current
    # pipeline violates this — state == 0 is accepted but is_valid_state(0)
    # is False, so an invalid vote state is recorded.
    if accepted:
        assert is_valid_state(state)   # FAILS at state == 0


main()
