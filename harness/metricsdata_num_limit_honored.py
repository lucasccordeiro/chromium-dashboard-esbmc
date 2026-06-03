# Harness: api/metricsdata.py:FeatureHandler.get_template_data — Finding F (fix)
#
# Positive control / paired good harness for Finding F
# (`metricsdata_num_zero_returns_all.py`).  Models the proposed fix: bound the
# result with a presence guard rather than a truthiness guard.
#
#   properties = self.fetch_all_datapoints()
#   if num is not None:          # FIX: honor a provided limit, even num == 0
#       properties = properties[:num]
#
# With the fix, a provided `num` (any value >= 0 admitted by get_int_arg) always
# bounds the result, so len(result) <= num holds for every admitted num —
# including num == 0, which now yields the empty top-0 list instead of the full
# dataset.  This is the contract the buggy `if num:` guard violates.
#
# Expected verdict: SUCCESSFUL (Phase 1 and Phase 2).

def feature_handler_num_result_fixed(num: int, n_total: int) -> int:
    """Result size with the proposed fix (num always treated as a limit)."""
    result_len = n_total          # fetch_all_datapoints() returns every datapoint
    # Fix: `if num is not None:` — num is provided here, so the slice always runs.
    result_len = num if num < n_total else n_total   # properties[:num]
    return result_len


def main():
    num = nondet_int()        # noqa: F821  — any value admitted by get_int_arg
    n_total = nondet_int()    # noqa: F821  — datapoints present in the datastore
    __ESBMC_assume(num >= 0)       # noqa: F821  — get_int_arg admits 0 and positives
    __ESBMC_assume(n_total >= 0)   # noqa: F821

    result_len = feature_handler_num_result_fixed(num, n_total)

    # The provided limit bounds the response for every admitted num, incl. 0.
    assert result_len <= num   # holds for all num >= 0
    assert result_len >= 0


main()
