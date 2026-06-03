# Harness: api/metricsdata.py:FeatureHandler.get_template_data — Finding F
#
# Source: api/metricsdata.py:199-212 (FeatureHandler at :144)
#   num = self.get_int_arg('num')          # admits 0 (rejects only < 0)
#   if num and not self.should_refresh():   # num=0 is falsy → cache path skipped
#       ...
#   properties = self.fetch_all_datapoints()
#   if num:                                 # num=0 is falsy → slice skipped
#       properties = properties[:num]
#   return _datapoints_to_json_dicts(properties)
#
# basehandlers.get_int_arg rejects num < 0 but admits num = 0 (basehandlers.py:193).
# The handler then bounds the result with `if num:` — a truthiness guard, not a
# presence guard.  For num=0 the guard is falsy, so the `properties[:num]` slice
# is skipped and the handler returns the FULL datapoint set with HTTP 200.
#
# This is the *inverse* of Finding B: there `?num=0` yields an empty page; here
# `?num=0` yields the entire dataset — a caller asking for "top 0" gets everything.
# It combines the get_int_arg-admits-0 class (Findings B/C/E) with the falsy-guard
# short-circuit class (`if num:`, same shape as Finding D's `if val and ...`).
#
# Contract: when a caller supplies a page-size limit `num`, the response must
# contain at most `num` datapoints (len(result) <= num).  The current `if num:`
# guard violates this at num=0.
#
# Expected verdict: FAILED (assertion `result_len <= num` violated at num=0).
#
# Empirical reproduction:
#   GET /api/v0/data/featurepopularity?num=0
#   → all N datapoints, HTTP 200   (expected: empty list, or HTTP 400)
#
# Proposed fix:
#   Replace `if num:` with `if num is not None:` so a provided limit (incl. 0) is
#   always honored, or give get_int_arg a minimum-value guard for this caller.

HTTP_400 = 400


def get_int_arg(val: int) -> int:
    """Stub of basehandlers.get_int_arg: rejects negative, admits 0+."""
    if val < 0:
        return HTTP_400
    return val            # 0 is admitted — no minimum-value guard.


def feature_handler_num_result(num: int, n_total: int) -> int:
    """Result size of FeatureHandler.get_template_data (current code).

    Models `properties = fetch_all_datapoints(); if num: properties = properties[:num]`
    on a cache miss with should_refresh() == False.
    """
    result_len = n_total          # fetch_all_datapoints() returns every datapoint
    if num:                       # num=0 is falsy → slice skipped → return all
        result_len = num if num < n_total else n_total   # properties[:num]
    return result_len


def main():
    num = nondet_int()        # noqa: F821  — the ?num query parameter
    n_total = nondet_int()    # noqa: F821  — datapoints present in the datastore
    __ESBMC_assume(num == 0)       # noqa: F821  — admitted-but-invalid value
    __ESBMC_assume(n_total > 0)    # noqa: F821  — at least one datapoint exists

    result_len = feature_handler_num_result(num, n_total)

    # A caller-supplied limit must bound the response. The current guard does not
    # enforce this for num=0; the assertion below catches the gap.
    assert result_len <= num   # FAILS: num=0 returns all n_total > 0 datapoints.


main()
