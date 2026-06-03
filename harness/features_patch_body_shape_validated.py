# Harness: api/features_api.py:FeaturesAPI.do_patch — Finding G (fix)
#
# Positive control / paired good harness for Finding G
# (`features_patch_missing_feature_changes_http500.py`).  Models the proposed
# fix: guard the body shape before indexing it.
#
#   body = self.get_json_param_dict()
#   if 'feature_changes' not in body:
#       self.abort(400, msg='Missing feature_changes')     # FIX
#   if 'id' not in body['feature_changes']:
#       self.abort(400, msg='Missing feature ID in feature updates')
#
# With the presence guard, every body shape produces a clean HTTP code — a
# malformed body (no `feature_changes`) yields HTTP 400, never an uncaught
# KeyError (HTTP 500).  This is the postcondition the buggy unguarded access
# violates.
#
# Expected verdict: SUCCESSFUL (Phase 1 and Phase 2).


HTTP_200 = 200
HTTP_400 = 400


def features_do_patch_fixed(has_feature_changes: int, has_id: int) -> int:
    """Model of do_patch with the body-shape presence guard added."""
    # Fix: guard presence before access → self.abort(400, ...).
    if not has_feature_changes:
        return HTTP_400
    if not has_id:
        return HTTP_400
    return HTTP_200


def main():
    has_feature_changes = nondet_int()  # noqa: F821
    has_id = nondet_int()               # noqa: F821

    code = features_do_patch_fixed(has_feature_changes, has_id)

    # The fixed handler always returns a clean HTTP code (never throws).
    assert code == HTTP_400 or code == HTTP_200
    # A malformed body (no feature_changes) is rejected with HTTP 400, not 500.
    if not has_feature_changes:
        assert code == HTTP_400


main()
