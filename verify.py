# chromium-dashboard ESBMC-Python verification orchestrator.
#
# Single source of truth for: target name -> entry script -> ESBMC args
# -> expected verdict, per phase.
#
# Phases (same scheme as the vLLM and AWS-Neuron PoCs):
#   Phase 1: default flags. Functional contracts via `assert`.
#   Phase 2: --overflow-check. CWE-190 / CWE-369 on integer arithmetic.
#
# A target with `safety_expected=None` skips Phase 2 (used for buggy
# variants whose Phase 1 already FAILS).

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.abspath(__file__))
HARNESS_DIR = os.path.join(ROOT, "harness")
ESBMC = os.environ.get("ESBMC", "esbmc")

_SAFETY: tuple[str, ...] = ("--overflow-check",)


@dataclass
class Target:
    name: str
    entry: str                                  # filename under harness/
    esbmc_args: tuple[str, ...] = ()            # extra Phase-1 args
    expected: str | None = "SUCCESSFUL"         # Phase-1 verdict, None to skip
    safety_args: tuple[str, ...] = _SAFETY      # extra Phase-2 args
    safety_expected: str | None = "SUCCESSFUL"  # Phase-2 verdict, None to skip


TARGETS: list[Target] = [
    # --- Tier 1: pure date/integer arithmetic helpers ---

    Target(
        # is_weekday: returns True iff weekday in {0,1,2,3,4}.
        # Contract: d.weekday() < 5 ↔ Mon-Fri.
        name="is_weekday",
        entry="is_weekday.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="is_weekday_buggy",
        entry="is_weekday_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # weekdays_between approximation branch:
        # calendar_days > MAX_DAYS => result = calendar_days * 5 // 7.
        # Contract: result in [0, calendar_days].
        name="weekdays_between_approx",
        entry="weekdays_between_approx.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="weekdays_between_approx_buggy",
        entry="weekdays_between_approx_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # weekdays_between loop branch:
        # calendar_days <= MAX_DAYS. Loop invariant: 0 <= counter <= MAX_DAYS.
        name="weekdays_between_loop",
        entry="weekdays_between_loop.py",
        esbmc_args=("--unwind", "32"),
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="weekdays_between_loop_buggy",
        entry="weekdays_between_loop_buggy.py",
        esbmc_args=("--unwind", "32"),
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # remaining_days: slo_limit - weekdays_between(...).
        # Contract: negative when overdue; equals slo_limit when elapsed=0.
        name="remaining_days",
        entry="remaining_days.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="remaining_days_buggy",
        entry="remaining_days_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # diff_days: (t1 - t2).days — can be negative.
        # diff_weeks: diff_days // 7 — safe (divisor 7 != 0).
        # Contract: diff_weeks * 7 <= diff_days < (diff_weeks + 1) * 7.
        name="diff_days_and_weeks",
        entry="diff_days_and_weeks.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="diff_days_and_weeks_buggy",
        entry="diff_days_and_weeks_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),

    # --- Tier 2: API input-validation live-bug-class targets ---
    # Each FAILED verdict is the expected and meaningful result —
    # the counterexample IS the defect report.

    Target(
        # Finding A: channels_api.py:146
        # if start > end: raise ValueError  (bare — not self.abort(400,...))
        # APIHandler.get() has no except ValueError → Flask returns HTTP 500.
        # Contract: response_code should be 400, but the bare raise gives 500.
        name="channels_start_gt_end_bare_valueerror",
        entry="channels_start_gt_end_bare_valueerror.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # Finding B: features_api.py:117
        # get_int_arg('num') admits 0 (not < 0); process_query runs with num=0
        # and returns empty features list with HTTP 200 (no 400 error signal).
        # Contract: num > 0 should be enforced; assertion fails at num=0.
        name="features_num_zero_silent_acceptance",
        entry="features_num_zero_silent_acceptance.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # Finding C: channels_api.py:138
        # get_int_arg('start') admits 0; milestone 0 is not a real Chrome
        # milestone. Returns null dates with HTTP 200 without error signal.
        # Contract: start >= 1 should be enforced; assertion fails at start=0.
        name="channels_milestone_zero_silent_acceptance",
        entry="channels_milestone_zero_silent_acceptance.py",
        expected="FAILED",
        safety_expected=None,
    ),

    # --- Tier 3: self-certify logic contracts ---

    Target(
        # is_privacy_eligible: explanation AND (any polyfill type).
        name="is_privacy_eligible",
        entry="is_privacy_eligible.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="is_privacy_eligible_buggy",
        entry="is_privacy_eligible_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # is_testing_eligible: all five coverage fields set.
        name="is_testing_eligible",
        entry="is_testing_eligible.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="is_testing_eligible_buggy",
        entry="is_testing_eligible_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # is_adoption_eligible: all four adoption fields set.
        name="is_adoption_eligible",
        entry="is_adoption_eligible.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="is_adoption_eligible_buggy",
        entry="is_adoption_eligible_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # is_eligible dispatch: gate_type routes to the correct predicate.
        name="is_eligible_dispatch",
        entry="is_eligible_dispatch.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="is_eligible_dispatch_buggy",
        entry="is_eligible_dispatch_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),

    # --- Tier 4: SLO state-machine invariants ---

    Target(
        # record_vote index safety: sorted(votes, ...)[-1] only reached
        # when votes is non-empty (guarded by `if not votes: return False`).
        name="record_vote_index_safety",
        entry="record_vote_index_safety.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="record_vote_index_safety_buggy",
        entry="record_vote_index_safety_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # record_vote changed-flag invariant: `changed` is True iff at least
        # one gate field was mutated, and never toggles True -> False.
        name="record_vote_changed_flag",
        entry="record_vote_changed_flag.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="record_vote_changed_flag_buggy",
        entry="record_vote_changed_flag_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # record_comment idempotency: records the initial response time once.
        # True iff requested_on set, responded_on unset, and caller is approver;
        # responded_on written iff True; a True call makes the next call False.
        name="record_comment_idempotent",
        entry="record_comment_idempotent.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="record_comment_idempotent_buggy",
        entry="record_comment_idempotent_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
    Target(
        # Overdue detection arithmetic:
        # remaining == -1  <->  newly overdue (1 weekday past deadline)
        # remaining == -slo_limit  <->  long overdue
        name="overdue_detection",
        entry="overdue_detection.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="overdue_detection_buggy",
        entry="overdue_detection_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),

    # --- Tier 5: milestone arithmetic ---

    Target(
        # get_next_release_number / get_previous_release_number round-trip.
        # Chrome milestone 82 was skipped; both helpers must agree on that skip.
        # Contract: for all n in [1, 200], n != 82:
        #   next(prev(n)) == n  AND  prev(next(n)) == n
        name="milestone_skip_round_trip",
        entry="milestone_skip_round_trip.py",
        expected="SUCCESSFUL",
        safety_expected="SUCCESSFUL",
    ),
    Target(
        name="milestone_skip_round_trip_buggy",
        entry="milestone_skip_round_trip_buggy.py",
        expected="FAILED",
        safety_expected=None,
    ),
]


def _verdict_from_output(out: str) -> str:
    if "VERIFICATION SUCCESSFUL" in out:
        return "SUCCESSFUL"
    if "VERIFICATION FAILED" in out:
        return "FAILED"
    return "ERROR"


_VCC_RE = re.compile(r"Generated (\d+) VCC\(s\)")


def _vcc_count(out: str) -> int | None:
    m = _VCC_RE.search(out)
    return int(m.group(1)) if m else None


def _run_esbmc(entry: str, args: tuple[str, ...]) -> tuple[str, int | None, str]:
    cmd = [ESBMC, *args, entry]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, cwd=HARNESS_DIR
    )
    output = proc.stdout + proc.stderr
    return _verdict_from_output(output), _vcc_count(output), output[-400:]


def _phase_label(phase: int) -> str:
    return f"Phase {phase}"


def _run_target(target: Target, phases: tuple[int, ...]) -> int:
    failures = 0
    for phase in phases:
        if phase == 1:
            expected = target.expected
            extra_args = target.esbmc_args
        else:
            expected = target.safety_expected
            extra_args = target.esbmc_args + target.safety_args
        if expected is None:
            print(f"  [{_phase_label(phase)}] skipped")
            continue
        verdict, vcc, tail = _run_esbmc(target.entry, extra_args)

        vacuous = verdict == "SUCCESSFUL" and vcc == 0
        ok = verdict == expected and not vacuous

        if vacuous:
            marker = "FAIL (vacuous: 0 VCCs)"
        elif ok:
            marker = "PASS"
        else:
            marker = "FAIL"

        vcc_str = "?" if vcc is None else str(vcc)
        cmd_str = shlex.join((ESBMC, *extra_args, target.entry))
        print(
            f"  [{_phase_label(phase)}] {marker}: "
            f"verdict={verdict} vcc={vcc_str} expected={expected}  "
            f"({cmd_str})"
        )
        if not ok:
            failures += 1
            print(f"      tail: {tail!r}")
    return failures


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("1", "2", "all"), default="all")
    ap.add_argument("--only", nargs="*", default=None,
                    help="restrict to target names")
    args = ap.parse_args()

    if args.phase == "all":
        phases: tuple[int, ...] = (1, 2)
    else:
        phases = (int(args.phase),)

    selected = TARGETS
    if args.only:
        selected = [t for t in TARGETS if t.name in set(args.only)]
        if not selected:
            print(f"no matching targets in {args.only!r}", file=sys.stderr)
            return 2

    total_failures = 0
    for t in selected:
        print(f"== {t.name} ==")
        total_failures += _run_target(t, phases)
    print()
    print(f"total failures: {total_failures}")
    return 1 if total_failures else 0


if __name__ == "__main__":
    sys.exit(main())
