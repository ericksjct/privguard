---
phase: 03-claude-enforcement
plan: 03
subsystem: claude-diagnostics
tags: [claude, privacy, doctor, cli, synthetic-tests]
requires:
  - phase: 03-claude-enforcement
    plan: 01
    provides: metadata-only prompt hook diagnostics
  - phase: 03-claude-enforcement
    plan: 02
    provides: strict PreToolUse path and command blocking
provides:
  - Safe `privguard claude doctor` diagnostics with synthetic-only probes
  - Metadata-only hook wiring validation for `.claude/settings.json`
  - Sanitized JSON and human doctor output with audit-visible synthetic markers
affects: [claude-enforcement, synthetic-regression-gate, cli-diagnostics]
tech-stack:
  added: []
  patterns:
    - metadata-only CLI diagnostics
    - synthetic-only doctor probes
    - protected-settings-path rejection before config reads
key-files:
  created:
    - tests/test_claude_doctor.py
    - tests/fixtures/claude_missing_hooks_settings.json
  modified:
    - privguard/diagnostics.py
    - privguard/cli.py
key-decisions:
  - "Claude doctor reports only check names, result states, reason codes, counts, kinds, categories, and booleans."
  - "The `--settings` option rejects protected path strings before attempting to open settings metadata."
patterns-established:
  - "CLI doctor output includes `synthetic_data=true` / `\"synthetic_data\": true` and never prints synthetic fixture values."
  - "Doctor probes use package detection, policy, path, and command classifiers directly instead of invoking external hook processes."
requirements-completed: [CLD-04, CLD-05]
duration: 4min
completed: 2026-05-03
---

# Phase 03 Plan 03: Safe Claude Doctor Diagnostics Summary

**Synthetic-only Claude doctor diagnostics validate hook wiring and effective blocking policy without reading protected files.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-03T20:35:04Z
- **Completed:** 2026-05-03T20:39:06Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `privguard claude doctor` with JSON and human output modes.
- Added metadata-only doctor report helpers that inspect `.claude/settings.json` hook wiring and run synthetic prompt/path/command probes.
- Added synthetic regression tests proving doctor output includes audit markers and omits raw CPF, fake secret, protected path, command, prompt, and redacted placeholder strings.
- Added a protected `--settings` path guard so doctor cannot be used to read `.env` or protected data paths.

## Task Commits

Task commits could not be created because Git cannot create `.git/index.lock` in this environment:

1. **Task 1: Add Claude doctor CLI tests** - not committed
2. **Task 2: Implement metadata-only Claude doctor** - not committed

Expected commit messages once Git index writes are available:

- `test(03-03): add Claude doctor CLI tests`
- `feat(03-03): implement Claude doctor diagnostics`
- `docs(03-03): complete safe Claude doctor diagnostics plan`

## Files Created/Modified

- `tests/test_claude_doctor.py` - Synthetic CLI doctor tests for JSON/text output, failed hook wiring, protected settings paths, and output hygiene.
- `tests/fixtures/claude_missing_hooks_settings.json` - Synthetic metadata fixture for missing Claude hook wiring.
- `privguard/diagnostics.py` - Metadata-only Claude doctor report construction, hook wiring checks, synthetic policy probes, and text rendering.
- `privguard/cli.py` - Nested `claude doctor` argparse command with `--json` and `--settings` options.

## Decisions Made

- Doctor checks use in-process package helpers instead of shelling out to hook adapters, keeping validation deterministic and avoiding protected file reads.
- Doctor output omits hook command strings and settings paths; it reports wiring booleans and reason codes only.
- The configurable settings path is rejected if it classifies as protected before any open/read attempt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Avoided pytest temp-directory permission failure in RED tests**
- **Found during:** Task 1 (Add Claude doctor CLI tests)
- **Issue:** `tmp_path` setup failed because the local pytest temp root under `AppData\\Local\\Temp` is not accessible.
- **Fix:** Replaced the temporary settings file with a checked-in synthetic fixture under `tests/fixtures/`.
- **Files modified:** `tests/test_claude_doctor.py`, `tests/fixtures/claude_missing_hooks_settings.json`
- **Verification:** `python -m pytest tests/test_claude_doctor.py -q` reached the intended RED failure for the missing CLI command.
- **Commit:** not committed; Git index writes are denied.

**2. [Rule 3 - Blocking] Removed diagnostics/policy circular import**
- **Found during:** Task 2 (Implement metadata-only Claude doctor)
- **Issue:** Importing policy helpers at `privguard.diagnostics` module load time created a circular import because `policy.py` already imports diagnostic serializers.
- **Fix:** Moved policy imports into the specific doctor helper functions that need them.
- **Files modified:** `privguard/diagnostics.py`
- **Verification:** `python -m pytest tests/test_claude_doctor.py tests/test_cli.py -q` passed.
- **Commit:** not committed; Git index writes are denied.

**3. [Rule 2 - Missing Critical] Blocked protected `--settings` paths**
- **Found during:** Task 2 (Implement metadata-only Claude doctor)
- **Issue:** A user-supplied `--settings` value could point at a protected path, contradicting the doctor privacy boundary.
- **Fix:** Added protected path classification before settings reads and a synthetic regression test for `.env`.
- **Files modified:** `privguard/diagnostics.py`, `tests/test_claude_doctor.py`
- **Verification:** `python -m pytest tests/test_claude_doctor.py tests/test_cli.py -q` passed.
- **Commit:** not committed; Git index writes are denied.

**Total deviations:** 3 auto-fixed (2 blocking, 1 missing critical). **Impact:** All fixes preserve the planned doctor behavior and strengthen the privacy boundary.

## Issues Encountered

- Git commit operations are blocked by `fatal: Unable to create 'C:/Users/Erick/Documents/projetos/privguard/.git/index.lock': Permission denied`.
- `privacy-guard claude doctor --json` could not be run because the console wrapper is not on PATH in this environment. `python -m privguard.cli claude doctor --json` succeeds, and tests exercise `privguard.cli:main`.
- `python -m pytest` reports a non-blocking pytest cache warning because `.pytest_cache` cannot create one cache file; tests still pass.

## Verification

- `python -m pytest tests/test_claude_doctor.py -q` - PASSED, 4 passed.
- `python -m pytest tests/test_claude_doctor.py tests/test_cli.py -q` - PASSED, 15 passed.
- `python -m privguard.cli claude doctor --json` - PASSED, emitted sanitized JSON with `"synthetic_data": true`.
- Stub scan across changed files - PASSED, no TODO/FIXME/placeholder/stub patterns found.

## Known Stubs

None.

## Threat Flags

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The doctor implementation and verification are complete for CLD-04 and CLD-05. GSD commit and state-update gates remain blocked until Git can create `.git/index.lock`.

## Self-Check: FAILED

- **Files exist:** PASSED
  - `tests/test_claude_doctor.py`
  - `tests/fixtures/claude_missing_hooks_settings.json`
  - `privguard/diagnostics.py`
  - `privguard/cli.py`
  - `.planning/phases/03-claude-enforcement/03-03-SUMMARY.md`
- **Verification commands:** PASSED
  - `python -m pytest tests/test_claude_doctor.py tests/test_cli.py -q`
  - `python -m privguard.cli claude doctor --json`
- **Commits exist:** FAILED
  - Task 1 commit missing because Git index writes are denied.
  - Task 2 commit missing because Git index writes are denied.
  - Metadata commit missing because Git index writes are denied.

---
*Phase: 03-claude-enforcement*
*Completed: 2026-05-03*
