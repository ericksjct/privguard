---
phase: 02-privacy-core
plan: 01
subsystem: detection
tags: [python, stdlib, pii, brazil, validators, pytest]

requires:
  - phase: 01-package-foundation
    provides: Importable privguard package modules and lightweight detection foundation
provides:
  - Canonical stdlib-only Brazilian identifier and secret-like value detection contract
  - Immutable detection hits with reason codes and source metadata
  - Detection reports with sanitized-capable counts
  - Canonical validator lookup for optional recognizer parity
affects: [02-privacy-core, masking, policy, diagnostics, cli, claude-enforcement]

tech-stack:
  added: []
  patterns:
    - Frozen detection result dataclasses
    - Canonical checksum validator registry
    - Deterministic overlap selection by confidence, span length, and start

key-files:
  created: [tests/test_detection.py]
  modified: [privguard/detection.py]

key-decisions:
  - "Kept the default detection core stdlib-only and did not import optional Presidio dependencies."
  - "Made package validators the canonical checksum source for lightweight and optional recognizer paths."
  - "Kept raw hit values internal while exposing report counts and metadata suitable for sanitized diagnostics."

patterns-established:
  - "DetectionReport aggregates hits as a tuple and counts by entity kind without serializing raw values."
  - "PatternEntry carries score, validator, and reason-code metadata for deterministic detection behavior."

requirements-completed: [DET-01, DET-02, DET-03, DET-04, DET-06]

duration: 6min
completed: 2026-05-02
---

# Phase 02 Plan 01: Shared Detection Contract Summary

**Stdlib-only Brazil-first detector with canonical checksum validators, secret patterns, sanitized report metadata, and deterministic overlap semantics**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-02T14:19:45Z
- **Completed:** 2026-05-02T14:25:23Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Expanded `privguard.detection` with checksum-backed CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS, RG-like, phone, CEP, old-plate, Mercosul-plate, API-key, token, password-assignment, database-URL, and sensitive env-assignment detection.
- Added `Hit` reason-code/source metadata and `DetectionReport` via `analyze_text()` for sanitized-capable downstream diagnostics.
- Added canonical validator lookup helpers so optional recognizer adapters can reuse package validators without importing optional dependencies on the default hot path.
- Added synthetic pytest coverage for DET-01, DET-02, DET-03, DET-04, and DET-06, including invalid checksum lookalikes and overlap ordering.

## Task Commits

Each task should be committed atomically, but git writes are blocked in this workspace:

1. **Task 1: Expand canonical detection validators and patterns** - unavailable (`git add` cannot create `.git/index.lock`)
2. **Task 2: Lock overlap and Presidio-parity semantics to package validators** - unavailable (`git add` cannot create `.git/index.lock`)

**Plan metadata:** unavailable for the same git index permission blocker.

## Files Created/Modified

- `privguard/detection.py` - Canonical detection API, validators, pattern registry, overlap handling, reports, and validator lookup helpers.
- `tests/test_detection.py` - Synthetic-only pytest coverage for Brazilian identifiers, secrets, invalid lookalikes, sanitized report counts, overlap semantics, and validator parity.

## Decisions Made

- Kept Presidio as optional/reference only; no mandatory import was added to the package core.
- Used reason codes such as `checksum_valid`, `checksum_invalid`, `secret_token`, `secret_assignment`, and `database_url` to support sanitized diagnostics.
- Preserved one public detection behavior through `detect()` and `analyze_text()` instead of adding user-facing light/full modes.

## Deviations from Plan

### Auto-fixed Issues

None - implementation stayed within the planned task scope.

---

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope expansion; the only unresolved execution issue is git metadata writing.

## Issues Encountered

- Git commit operations failed because the workspace cannot create `.git/index.lock`: `fatal: Unable to create '.../.git/index.lock': Permission denied`. Code and tests were completed and verified, but task commits and the final metadata commit could not be created from this environment.
- `pytest` passed but emitted a cache warning because it could not create `.pytest_cache` entries under the workspace. This did not affect test execution.

## Verification

- `python -m pytest tests/test_detection.py -q` - PASS (`13 passed`)
- `python -m compileall privguard` - PASS
- `python -c "import pathlib; text=pathlib.Path('tests/test_detection.py').read_text(encoding='utf-8'); assert '.env' not in text or 'data_sensivel' not in text"` - PASS
- `python -c "import privguard.detection as d; assert callable(d.detect); assert callable(d.analyze_text)"` - PASS
- `python -c "import pathlib; text=pathlib.Path('privguard/detection.py').read_text(encoding='utf-8').lower(); assert 'presidio' not in text or 'import presidio' not in text"` - PASS

## Known Stubs

None.

## Threat Flags

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

The detection core is ready for Plan 02-02 masking and diagnostics work after the local git index permission blocker is resolved and the required commits can be created.

## Self-Check: FAILED

- **Files:** `privguard/detection.py`, `tests/test_detection.py`, and this summary exist.
- **Commits:** Missing because git index writes are blocked by local permissions.

---
*Phase: 02-privacy-core*
*Completed: 2026-05-02*
