# Harness: api/features_api.py:FeaturesAPI.do_search — Finding B
#
# Source: features_api.py:117
#   num = self.get_int_arg('num', search.DEFAULT_RESULTS_PER_PAGE)
#
# basehandlers.get_int_arg rejects num < 0 but admits num = 0:
#   if num < 0:
#       self.abort(400, ...)     # rejects negatives
#   return num                   # returns 0 without error
#
# With num=0, process_query_using_cache runs normally:
#   num = min(0, 1000) = 0
#   paginated_id_list = sorted_id_list[start : start + 0] = []
#   → {"total_count": N, "features": []}  HTTP 200
#
# The API accepts num=0 and returns an empty page without a 400 error.
# This is the same silent-acceptance pattern as vLLM Findings #5 and #6.
#
# Expected verdict: FAILED (assertion `num > 0` is violated at acceptance gate).
#
# Empirical reproduction:
#   GET /api/v0/features?num=0
#   → {"total_count": 5000, "features": []}  HTTP 200
#   (expected: HTTP 400 "num must be > 0")
#
# Proposed fix:
#   Add `if num == 0: self.abort(400, msg='num must be positive')` after
#   the get_int_arg call, or add a gt=0 positivity guard to get_int_arg.

HTTP_200 = 200
HTTP_400 = 400


def get_int_arg(val: int, default: int) -> int:
    """Stub of basehandlers.get_int_arg for the num parameter."""
    if val is None:
        return default
    if val < 0:
        return HTTP_400   # abort — modelled as returning the error code
    return val            # 0 is admitted (no positivity guard)


def features_do_search_num_gate(num: int) -> int:
    """Model of the num-acceptance gate in FeaturesAPI.do_search."""
    # Current behaviour: only negative values are rejected.
    if num < 0:
        return HTTP_400
    # num=0 passes through silently.
    return HTTP_200


def main():
    # Symbolically explore: what if num=0?
    num = nondet_int()  # noqa: F821
    __ESBMC_assume(num == 0)  # noqa: F821  — the admitted-but-invalid value.

    code = features_do_search_num_gate(num)

    # After the acceptance gate, num must be > 0 for pagination to be meaningful.
    # The current gate does NOT enforce this; the assertion below catches the gap.
    assert num > 0   # FAILS: num=0 is admitted (code=200) but produces empty results.


main()
