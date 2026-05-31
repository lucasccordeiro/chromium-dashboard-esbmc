# Stub library for the chromium-dashboard ESBMC-Python PoC.
#
# Imported by every entry script under harness/.  Same conventions as the
# vLLM and AWS-Neuron PoCs.
#
# Philosophy:
#   - Model only what a target *reads*.  Do not invent behaviour.
#   - Preconditions are `__ESBMC_assume(...)`.  Postconditions are `assert`.
#
# DO NOT define `nondet_int`, `nondet_bool`, or `__ESBMC_assume` as runtime
# Python functions.  Those names are ESBMC-Python intrinsics; a runtime def
# makes the symbolic value concrete (always 0 / False / no-op), the harness
# vacuous, and ESBMC silently reports VERIFICATION SUCCESSFUL with 0 VCCs.
# The TYPE_CHECKING guard below gives type checkers the signatures without
# putting executable code in ESBMC's path.

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    def nondet_int() -> int: ...
    def nondet_bool() -> bool: ...
    def __ESBMC_assume(_c: bool) -> None: ...  # noqa: N802

# --- Shared constants ---

# chromium-dashboard SLO constants (mirrors internals/slo.py).
MAX_DAYS = 30           # Maximum weekday count returned by weekdays_between().

# chromium-dashboard search constants (mirrors internals/search.py).
DEFAULT_RESULTS_PER_PAGE = 100
MAX_RESULTS_PER_PAGE = 1000

# Wide bound for integer inputs (covers realistic milestone numbers,
# day-count differences, and SLO limits).
INT_BOUND = 1 << 20     # 1 048 576 — more than enough for date arithmetic.
