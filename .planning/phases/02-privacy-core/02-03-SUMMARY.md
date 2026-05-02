---
phase: 02-privacy-core
plan: 03
subsystem: policy
tags: [python, policy, protected-paths, fail-closed, diagnostics, pytest]

requires:
  - phase: 02-privacy-core
    plan: 01
    provides: Detection hits and reports
  - phase: 02-privacy-core
    plan: 02
    provides: MaskResult and sanitized diagnostics
provides:
  - Protected path classification without file IO
  - Surface capability labels and fail-closed policy decisions
  - Sanitized policy/path decision serialization
affects: [02-privacy-core, cli, claude-enforcement, codex-evidence]

tech-stack:
  added: []
  patterns:
    - Frozen policy/path dataclasses
    - String-only protected path normalization
    - Capability-driven fail-closed decisions

key-files:
  created: [tests/test_policy.py]
  modified: [privguard/policy.py, privguard/diagnostics.py]

key-decisions:
  - "Path classification remains string-only and never opens, stats, or expands protected paths."
  - "Unknown and external surfaces block by default in strict mode unless verified masked output is provided."
  - "Policy diagnostics expose action, capability, counts, and reason codes only."

patterns-established:
  - "PathClassification carries protected status, category, and sanitized reason code."
  - "PolicyDecision carries allow/action plus sanitized reason codes for downstream adapters."

requirements-completed: [DET-05, MASK-04, POL-01, POL-02, POL-03, POL-04]

duration: 6min
completed: 2026-05-02
---

# Phase 02 Plan 03: Protected Path and Policy Summary

**String-only protected path classification and shared fail-closed policy decisions**

## Performance

- **Duration:** 6 min
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added `PathClassification` and `classify_path()` for `.env`, `.env.*`, protected data directories, dumps, credential-like files, and secret-like filenames.
- Preserved `is_sensitive_path()` as a compatibility wrapper for existing hooks.
- Added `SurfaceCapability`, `PolicyMode`, `PolicyAction`, `PolicyDecision`, and `decide_policy()`.
- Encoded strict fail-closed behavior for unknown/external surfaces and safe handling for unverified masks.
- Kept policy/path decisions sanitized and compatible with `privguard.diagnostics.to_dict()` and `to_json()`.
- Added synthetic-only tests for path normalization, protected path blocking, surface capabilities, incomplete masks, and diagnostic leak resistance.

## Task Commits

Commit is pending manual execution because the Codex sandbox cannot write `.git/index.lock` in this workspace.

1. **Task 1: Expand protected-path classification** - pending manual commit
2. **Task 2: Add surface capability and fail-closed decisions** - pending manual commit
3. **Task 3: Ensure policy diagnostics remain sanitized** - pending manual commit

## Files Created/Modified

- `privguard/policy.py` - Path classification, capability constants, policy decisions, and compatibility wrappers.
- `tests/test_policy.py` - Synthetic policy/path tests.
- `privguard/diagnostics.py` - Existing dataclass serialization now covers policy/path metadata safely.

## Decisions Made

- Used enum-like string constants to keep CLI/hook integration simple and stable.
- Treated protected paths as an immediate block before surface capability policy.
- Kept permissive mode available only as an explicit non-default escape hatch for unknown clean surfaces.

## Deviations from Plan

### Auto-fixed Issues

None.

---

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope expansion.

## Issues Encountered

- Codex still cannot create `.git/index.lock`; commit must be created from the user's PowerShell.
- Pytest emitted a cache warning due local cache directory permissions; tests passed.

## Verification

- `python -m pytest tests/test_policy.py tests/test_masking.py tests/test_detection.py -q` - PASS (`30 passed`)
- `python -m compileall privguard` - PASS
- `python -c "from privguard.policy import classify_path, is_sensitive_path; c=classify_path('safe/example.txt'); assert hasattr(c, 'is_protected'); assert is_sensitive_path('safe/example.txt') is False"` - PASS
- `python -c "from privguard.policy import SurfaceCapability, decide_policy; assert hasattr(SurfaceCapability, 'UNKNOWN') or 'unknown' in str(SurfaceCapability)"` - PASS

## Known Stubs

None.

## Threat Flags

None.

## User Setup Required

Run `commit-02-03.ps1` from a PowerShell session that can write to `.git`.

## Next Phase Readiness

Plan 02-04 can wire detection, masking, policy, and diagnostics into CLI commands and package exports.

## Self-Check: PASSED

- **Files:** All planned source and test files exist.
- **Tests:** Planned verification commands passed.
- **Commits:** Pending manual commit due sandbox `.git` permissions.

---
*Phase: 02-privacy-core*
*Completed: 2026-05-02*
