---
phase: 02-privacy-core
plan: 02
subsystem: masking-diagnostics
tags: [python, masking, diagnostics, sanitized-output, pytest]

requires:
  - phase: 02-privacy-core
    plan: 01
    provides: Canonical detection hits and reports
provides:
  - Irreversible typed placeholder masking through MaskResult
  - Post-mask verification for original value remnants and residual detections
  - Sanitized text and JSON diagnostic serializers
affects: [02-privacy-core, policy, cli, claude-enforcement]

tech-stack:
  added: []
  patterns:
    - Frozen result dataclasses
    - Metadata-only diagnostic serializers
    - Explicit mask verification status and reason codes

key-files:
  created: [privguard/diagnostics.py, tests/test_masking.py]
  modified: [privguard/masking.py, privguard/__init__.py]

key-decisions:
  - "Kept masking irreversible; no deanonymization map, decrypt path, or original-to-placeholder mapping is returned."
  - "Kept masked payload text out of diagnostics; it is only returned by the explicit masking API."
  - "Preserved redact() as a compatibility wrapper over mask_text()."

patterns-established:
  - "MaskResult carries masked text plus verification metadata for downstream policy decisions."
  - "diagnostics.to_dict() treats Hit.value and MaskResult.text as sensitive and omits them."

requirements-completed: [MASK-01, MASK-02, MASK-03, POL-04]

duration: 5min
completed: 2026-05-02
---

# Phase 02 Plan 02: Masking and Diagnostics Summary

**Irreversible typed masking with verification and sanitized diagnostics**

## Performance

- **Duration:** 5 min
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `MaskResult`, `mask_text()`, and `verify_mask()` in `privguard.masking`.
- Kept `redact()` import-compatible while routing it through the richer masking contract.
- Added post-mask verification that fails if original hit values remain or if residual detection finds sensitive leftovers.
- Added `privguard.diagnostics` with metadata-only `to_dict()`, `to_json()`, `format_text()`, `summarize_hits()`, and `format_hit_summary()`.
- Exported stable Phase 2 masking and diagnostic helpers from `privguard.__init__`.
- Added synthetic-only tests proving placeholders replace sensitive spans and diagnostics do not expose raw values or masked payload text.

## Task Commits

Commit is pending manual execution because the Codex sandbox cannot write `.git/index.lock` in this workspace.

1. **Task 1: Add irreversible mask result and verification** - pending manual commit
2. **Task 2: Add sanitized diagnostic serializers** - pending manual commit

## Files Created/Modified

- `privguard/masking.py` - MaskResult, mask_text(), verify_mask(), and compatibility redact().
- `privguard/diagnostics.py` - Sanitized serializers and human-readable metadata formatting.
- `privguard/__init__.py` - Public exports for detection, masking, and diagnostics.
- `tests/test_masking.py` - Synthetic-only masking and diagnostic leak tests.

## Decisions Made

- Mask verification returns explicit status and reason codes instead of silently treating partial output as safe.
- Diagnostic serialization omits `Hit.value` and `MaskResult.text` by construction.
- No reversible state or downstream user-choice UI was added; client enforcement remains for later phases.

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

- `python -m pytest tests/test_masking.py tests/test_detection.py -q` - PASS (`20 passed`)
- `python -m compileall privguard` - PASS
- `python -c "from privguard.diagnostics import to_json, format_text; from privguard.masking import mask_text, redact; assert callable(to_json); assert callable(format_text); assert callable(mask_text); assert callable(redact)"` - PASS

## Known Stubs

None.

## Threat Flags

None.

## User Setup Required

Run `commit-02-02.ps1` from a PowerShell session that can write to `.git`.

## Next Phase Readiness

Plan 02-03 can consume `MaskResult`, `verify_mask()`, and sanitized diagnostics after the manual commit is created.

## Self-Check: PASSED

- **Files:** All planned source and test files exist.
- **Tests:** Planned verification commands passed.
- **Commits:** Pending manual commit due sandbox `.git` permissions.

---
*Phase: 02-privacy-core*
*Completed: 2026-05-02*
