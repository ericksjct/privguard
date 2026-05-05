---
phase: 05-synthetic-regression-gate
fixed_at: 2026-05-05T00:00:00Z
review_path: .planning/phases/05-synthetic-regression-gate/05-REVIEW.md
iteration: 2
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 05: Code Review Fix Report

**Fixed at:** 2026-05-05T00:00:00Z
**Source review:** .planning/phases/05-synthetic-regression-gate/05-REVIEW.md
**Iteration:** 2

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

Scope: All severities (Critical + Warning + Info). Iteration 2 expands the
fix scope to cover the two informational findings (IN-01, IN-02) that were
intentionally deferred in iteration 1. The three warning fixes (WR-01, WR-02,
WR-03) from iteration 1 were re-verified against the current source and
remain in place — their commit hashes are preserved below for traceability.

## Fixed Issues

### WR-01: `test_TEST_06_codex_claim_scan_reports_only_file_path_and_pattern` passes vacuously on wrong CWD

**Files modified:** `tests/test_v1_regression_gate.py`
**Commit:** dfdafc5 (iteration 1)
**Applied fix:** Added `assert files, "Safe file scan returned no files — check working directory and glob patterns"` immediately after the `_safe_text_files()` call in `test_TEST_06_codex_claim_scan_reports_only_file_path_and_pattern`. Mirrors the existing guard in `test_TEST_01_safe_source_scan_excludes_protected_paths_and_uses_synthetic_policy` so a non-standard CI working directory now produces a hard failure instead of a silent false-green. Re-verified in iteration 2: the assertion is present at lines 564–566 of the current source.

### WR-02: Claim-scanning implementations diverge — two forbidden patterns missing from regression gate

**Files modified:** `tests/test_v1_regression_gate.py`
**Commit:** c3e1696 (iteration 1)
**Applied fix:** Replaced the inlined 3-phrase forbidden list and inlined match/window logic in `test_TEST_06_codex_claim_scan_reports_only_file_path_and_pattern` with a delegation to `_find_unsupported_claims` and `_safe_text_files` from `test_codex_claim_gate` (REVIEW.md Option A). The regression gate now uses the same 5-pattern list and exact same allow-rules as the CDX-03 claim gate, eliminating divergence and preventing future widening of the coverage gap. Re-verified in iteration 2: the delegation import is present at lines 558–561, and the WR-01 `assert files` guard is preserved on the delegated `_cg_safe_files(_ROOT)` call.

### WR-03: Missing whitespace normalization on last-line fallback in `_find_unsupported_claims`

**Files modified:** `tests/test_codex_claim_gate.py`
**Commit:** 1f8f532 (iteration 1)
**Applied fix:** Updated the `else` branch of the two-line-window construction in `_find_unsupported_claims` to capture the raw fallback line into `raw_fallback` and then apply `_re.sub(r"\s+", " ", raw_fallback)` before assigning to `two_line_window`. Last-line matches now receive the same whitespace normalization as the multi-line branch, so an allowed disclaimer ending the file with tabs or double spaces no longer triggers a false violation. Re-verified in iteration 2: the normalized fallback assignment is present at lines 215–216 of the current source.

### IN-01: `import re as _re` inside function loop body

**Files modified:** `tests/test_codex_claim_gate.py`
**Commit:** 65dda94 (iteration 2)
**Applied fix:** Removed the `import re as _re` statement from inside the `for pattern in FORBIDDEN_CLAIM_PATTERNS` loop body in `_find_unsupported_claims`. The module already imports `re` at module level (line 26), so the in-loop import was redundant. Replaced it with a single `_re = re` alias declared once at the top of `_find_unsupported_claims`, immediately before the `text_lower`/`lines` setup. This preserves every existing `_re.sub(...)` call site without churn while eliminating the in-loop import code smell. An IN-01 reference comment was added in the function body for traceability. Verified via `python -c "import ast; ast.parse(...)"` syntax check — no parse errors.

### IN-02: `"redacted="` sentinel in `FORBIDDEN_OUTPUT` is fragile

**Files modified:** `tests/test_v1_regression_gate.py`
**Commit:** f80c031 (iteration 2)
**Applied fix:** Strengthened the `"redacted="` entry in `FORBIDDEN_OUTPUT` to the narrower `"redacted=True"` sentinel and added a multi-line comment explaining the specific serializer leakage pattern this entry guards against (a future hooks/diagnostics serializer echoing a redaction-state metadata field whose value carries the raw payload alongside it). The narrower form avoids false positives from unrelated keys such as `not_redacted=False` or `already_redacted=true` while still catching the leakage pattern of concern. Verified that no current source under `privguard/` emits `redacted` in any form, so narrowing the sentinel does not weaken the existing guarantee. Verified via `python -c "import ast; ast.parse(...)"` syntax check — no parse errors. Note: the related `tests/test_claude_hooks.py:55` and `tests/test_claude_phase_gate.py:41` still use `"redacted="` — those are scoped to their own phase gates and intentionally left untouched here.

---

_Fixed: 2026-05-05T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 2_
