---
phase: 05-synthetic-regression-gate
fixed_at: 2026-05-05T21:41:51Z
review_path: .planning/phases/05-synthetic-regression-gate/05-REVIEW.md
iteration: 1
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 05: Code Review Fix Report

**Fixed at:** 2026-05-05T21:41:51Z
**Source review:** .planning/phases/05-synthetic-regression-gate/05-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 3
- Fixed: 3
- Skipped: 0

Scope: Critical + Warning severity. Info findings (IN-01, IN-02) intentionally
deferred per `fix_scope=critical_warning`.

## Fixed Issues

### WR-01: `test_TEST_06_codex_claim_scan_reports_only_file_path_and_pattern` passes vacuously on wrong CWD

**Files modified:** `tests/test_v1_regression_gate.py`
**Commit:** dfdafc5
**Applied fix:** Added `assert files, "Safe file scan returned no files — check working directory and glob patterns"` immediately after the `_safe_text_files()` call in `test_TEST_06_codex_claim_scan_reports_only_file_path_and_pattern`. Mirrors the existing guard in `test_TEST_01_safe_source_scan_excludes_protected_paths_and_uses_synthetic_policy` (line 208) so a non-standard CI working directory now produces a hard failure instead of a silent false-green.

### WR-02: Claim-scanning implementations diverge — two forbidden patterns missing from regression gate

**Files modified:** `tests/test_v1_regression_gate.py`
**Commit:** c3e1696
**Applied fix:** Replaced the inlined 3-phrase forbidden list and inlined match/window logic in `test_TEST_06_codex_claim_scan_reports_only_file_path_and_pattern` with a delegation to `_find_unsupported_claims` and `_safe_text_files` from `test_codex_claim_gate` (REVIEW.md Option A). The regression gate now uses the same 5-pattern list and exact same allow-rules as the CDX-03 claim gate, eliminating divergence and preventing future widening of the coverage gap. Verified via `import test_codex_claim_gate` smoke test that the helper exposes 5 patterns and both helper symbols. The `assert files` guard from WR-01 is preserved (now applied to `_cg_safe_files(_ROOT)`).

### WR-03: Missing whitespace normalization on last-line fallback in `_find_unsupported_claims`

**Files modified:** `tests/test_codex_claim_gate.py`
**Commit:** 1f8f532
**Applied fix:** Updated the `else` branch on line 208 of `_find_unsupported_claims` to capture the raw fallback line into `raw_fallback` and then apply `_re.sub(r"\s+", " ", raw_fallback)` before assigning to `two_line_window`. Last-line matches now receive the same whitespace normalization as the multi-line branch, so an allowed disclaimer ending the file with tabs or double spaces no longer triggers a false violation. Added inline comment referencing WR-03 for traceability.

---

_Fixed: 2026-05-05T21:41:51Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
