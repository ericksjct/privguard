---
phase: 09-milestone-v1-0-audit-cleanup
plan: 03
subsystem: cli
tags: [cleanup, tomllib, toctou, exit-codes, refactor, regression-gate]

# Dependency graph
requires:
  - phase: 07-readme-hygiene
    provides: "privguard cleanup subcommand (cleanup.py) wired into the CLI with contract tests"
provides:
  - "Guarded _load_patterns reopen honoring the D-14 exit-code contract on TOCTOU read failure"
  - "Parameterized _format_dry_run (apply flag) replacing the fragile .replace() substitution"
  - "Dead-code-free _human_size (unreachable post-loop return removed)"
  - "Confirmed 252-passed / 1-skipped synthetic regression baseline after the edits"
affects: [milestone-v1-0-audit, cleanup, cli]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single D-14 exit-code contract: every guarded read routes through _err + raise SystemExit(2) with a reason code"
    - "Mode parameterization over string substitution for dual-header (dry-run/apply) formatters"

key-files:
  created: []
  modified:
    - privguard/cleanup.py

key-decisions:
  - "Mirrored _verify_repo_root's guarded-read idiom verbatim in _load_patterns (reused reason code pyproject_unreadable) instead of inventing a new code — one D-14 contract."
  - "Parameterized _format_dry_run with apply=False default so empty-apply state emits a graceful '[apply] nothing to clean.' instead of a misleading dry-run header."

patterns-established:
  - "Guarded-read template: try/except (OSError, tomllib.TOMLDecodeError) -> _err(...) -> raise SystemExit(2)"
  - "Dual-mode formatter via boolean flag controlling prefix/verb/trailer, not post-hoc .replace()"

requirements-completed: [MAINT-01]

# Metrics
duration: 3min
completed: 2026-06-12
---

# Phase 9 Plan 03: cleanup.py Audit Hardening Summary

**Guarded the `_load_patterns` TOCTOU reopen to honor the D-14 exit-code contract, parameterized `_format_dry_run` with an `apply` flag (dropping the fragile `.replace()`), removed the dead `_human_size` return, and re-confirmed the 252-passed / 1-skipped synthetic regression baseline.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-06-12T01:27:15Z
- **Completed:** 2026-06-12T01:30:07Z
- **Tasks:** 2 (Task 1 edits + Task 2 blocking regression gate)
- **Files modified:** 1

## Accomplishments
- **WR-01:** `_load_patterns` reopen of `pyproject.toml` is now wrapped in `try/except (OSError, tomllib.TOMLDecodeError)` routing through `_err("pyproject.toml unreadable", "pyproject_unreadable")` + `raise SystemExit(2)`. A TOCTOU read failure now surfaces as a sanitized `[CLEANUP] error` with exit code 2, not an unhandled traceback / exit 1. Mitigates threat T-09-05 (info disclosure) and T-09-06 (exit-code contract integrity).
- **WR-02:** `_format_dry_run` gained an `apply: bool = False` parameter that controls the `[dry-run]` / `[apply]` prefix, the `would delete` / `deleting` verb, and the `Run with --apply to delete.` trailer. The `main()` `--apply` branch now calls `_format_dry_run(matches, skips, apply=True)`; the brittle `.replace()` chain is gone. Mitigates threat T-09-07 (tampering / silent misleading header).
- **IN-01:** Removed the mathematically unreachable post-loop `return f"{n} B"` in `_human_size` (the GB iteration always returns). The in-`if` early return at the top of the function remains.
- **Task 2 BLOCKING gate:** Full `python -m pytest -q` exits 0 at **252 passed / 1 skipped** (the 1 skip is `test_cleanup_apply_refuses_symlinks`, guarded by `os.name == "nt"` on Windows). No regression from the edits.

## Task Commits

1. **Task 1: WR-01 guard + WR-02 parameterize + IN-01 dead-return removal** - `3cd66d5` (fix)

**Task 2** was a run-only blocking regression gate (no file edits), so it has no separate commit.

**Plan metadata:** _(final docs commit — see below)_

## Files Created/Modified
- `privguard/cleanup.py` - Guarded `_load_patterns` reopen; parameterized `_format_dry_run` with `apply` flag and removed the `.replace()` substitution in the `--apply` branch; deleted the unreachable `_human_size` return.

## Decisions Made
- Reused the existing `pyproject_unreadable` reason code (already used by `_verify_repo_root`) rather than minting a new one — keeps a single, consistent D-14 contract across both read sites.
- Defaulted the new parameter to `apply=False` so existing dry-run call sites are untouched and the empty-state apply path degrades gracefully to `[apply] nothing to clean.`.

## Deviations from Plan

None - plan executed exactly as written. All four edits applied via the verbatim OLD/NEW blocks in the plan, all grep acceptance criteria matched (except-guards=2, n-B-returns=1, replace-calls=0, apply=True=1, apply-param=1), and tests/test_cleanup.py was not modified.

## Issues Encountered
None. The repo's `rtk` output filter collapses pytest output to a summary line, so the full suite was run with `-p no:cacheprovider` and confirmed via exit code 0 and the `252 passed` summary; the cleanup contract subset showed `5 passed` (the 6th skips on Windows), matching the documented 1-skip baseline.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ROADMAP Phase 9 success criteria 4 (D-14 exit-code contract on the TOCTOU path, explicit apply/dry-run headers, dead-code removal) and 5 (synthetic regression gate green at the 252 passed / 1 skipped baseline) are met.
- MAINT-01 implementation is hardened; no follow-up work outstanding for this plan.

## TDD Gate Compliance
N/A - this is an `execute` plan (not `type: tdd`); Task 1 was `tdd="false"` and committed as a single `fix` commit. The regression gate (Task 2) ran the existing pre-phase test suite unmodified.

## Self-Check: PASSED

- FOUND: `.planning/phases/09-milestone-v1-0-audit-cleanup/09-03-SUMMARY.md`
- FOUND: commit `3cd66d5` (Task 1)
- FOUND: `privguard/cleanup.py`

---
*Phase: 09-milestone-v1-0-audit-cleanup*
*Completed: 2026-06-12*
