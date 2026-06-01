#!/usr/bin/env python3
"""
Empirical reproducer — ESBMC tool bug (not a chromium-dashboard bug)
  Filed upstream: https://github.com/esbmc/esbmc/issues/5022

ESBMC's Python frontend does not stably store list-comprehension elements.
A value read out of a `[... for ...]` list through a function-parameter alias
is re-materialised as a fresh symbolic value, so two reads diverge.  A pure
function called twice on the same, unmodified comprehension-built list returns
different results, and the tautology `p(ans) == p(ans)` is reported FAILED.

Symptom: spurious `VERIFICATION FAILED` (a false alarm) — NOT a false
SUCCESSFUL.  Divergent reads give the solver more freedom to violate equality
assertions, so the failure mode is a missed proof, not a missed bug.

Verified: ESBMC 8.3.0, master b259f8a (2026-06-01), Bitwuzla 0.9.0 AND Z3.

Run:
  esbmc esbmc_list_comprehension_divergence.py
    -> VERIFICATION FAILED   (the bug: `return_value$_p$1 != return_value$_p$2`)

Control (swap ONLY the comprehension for a literal -> SUCCESSFUL):
  def main():
      ans = [nondet_bool(), nondet_bool()]   # literal, not a comprehension
      assert p(ans) == p(ans)

Fixed in esbmc/esbmc#5023 (merged 2026-06-01, commit 27585275).
The harnesses in ../harness/is_eligible_dispatch*.py now use list
comprehensions directly.  This file is kept as a regression reproducer.

`nondet_bool` is an ESBMC-Python intrinsic (deliberately undefined at the Python
level), so static checkers flag it — same as every entry file under ../harness/.
An inline `TYPE_CHECKING` stub cannot be used here: ESBMC's frontend rejects it
("Variable 'TYPE_CHECKING' is not defined").
"""


def p(a) -> bool:
    return a[0] and a[1]


def main():
    ans = [nondet_bool() for _ in range(2)]   # noqa: F821  (ESBMC intrinsic)
    # p is pure and `ans` is never mutated, so this is a tautology.
    # ESBMC reports FAILED: the two calls observe independent nondet draws.
    assert p(ans) == p(ans)


main()
