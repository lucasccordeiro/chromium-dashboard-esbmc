# Harness: api/features_api.py:FeaturesAPI.do_patch — Finding G
#
# Source: features_api.py:549-552
#   body = self.get_json_param_dict()          # {} for missing/invalid JSON
#   if 'id' not in body['feature_changes']:    # unguarded dict access
#       self.abort(400, msg='Missing feature ID in feature updates')
#
# get_json_param_dict() returns the raw request JSON, or {} when the body is
# missing/invalid.  do_patch then indexes body['feature_changes'] with no
# presence guard, so a PATCH whose body lacks the `feature_changes` key (e.g.
# an empty body `{}`) raises KeyError.  APIHandler.patch() (basehandlers.py:285)
# has no `except` around the do_patch() call, so the KeyError propagates to
# Flask and becomes HTTP 500, not HTTP 400.  (The sibling `body['stages']`
# access at features_api.py:567 is the same class.)
#
# Same root cause as Finding A: bad user input reaches an uncaught exception in
# an api/ handler → HTTP 500 instead of the HTTP 400 the maintainer's convention
# requires (PR #6451: api/ code must self.abort(400, ...) on bad input).
#
# This harness models the body-shape gate and asserts the EXPECTED behaviour
# (missing key → HTTP 400).  The assertion fails because the unguarded access
# raises KeyError (HTTP 500) instead.
#
# Expected verdict: FAILED (assertion `code == 400` is violated via the
# exception path).
#
# Empirical reproduction:
#   PATCH /api/v0/features/123   body: {}
#   → HTTP 500 Internal Server Error  (expected: HTTP 400 Bad Request)
#
# Proposed fix:
#   if 'feature_changes' not in body:
#       self.abort(400, msg='Missing feature_changes')
#   (and default `body.get('stages', [])` for the sibling access).


HTTP_200 = 200
HTTP_400 = 400
HTTP_500 = 500


def features_do_patch(has_feature_changes: int, has_id: int) -> int:
    """Inline model of FeaturesAPI.do_patch body-shape handling.

    Returns the HTTP response code the handler would produce.
    """
    # features_api.py:552 — body['feature_changes'] accessed with NO presence
    # guard.  When the key is absent this raises KeyError in production.
    if not has_feature_changes:
        raise KeyError   # propagates as HTTP 500 (no except around do_patch).

    # features_api.py:552-557 — 'id' not in body['feature_changes'] → abort 400.
    if not has_id:
        return HTTP_400

    return HTTP_200


def main():
    has_feature_changes = nondet_int()  # noqa: F821  — is the key present?
    has_id = nondet_int()               # noqa: F821

    __ESBMC_assume(has_feature_changes == 0)  # noqa: F821  — malformed body, e.g. {}

    # Expected: a malformed body should yield HTTP 400.
    # Actual:   unguarded body['feature_changes'] raises KeyError → HTTP 500.
    try:
        code = features_do_patch(has_feature_changes, has_id)
        assert code == HTTP_400   # FAILS: the exception path is taken instead.
    except KeyError:
        assert False, "missing 'feature_changes' should have been an HTTP 400 abort"


main()
