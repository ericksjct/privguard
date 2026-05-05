---
phase: 05-synthetic-regression-gate
plan: 1
subsystem: tests
tags: [regression-gate, synthetic-fixtures, output-hygiene, fail-closed, pytest]
dependency_graph:
  requires:
    - 04-02 (Codex compatibility matrix and claim gate)
    - 03-04 (Claude hook enforcement)
    - 02-04 (Privacy core masking/policy)
  provides:
    - v1 synthetic regression gate: tests/test_v1_regression_gate.py
    - TEST-01..TEST-06 auditable traceability in a single pytest-native file
  affects:
    - tests/test_codex_claim_gate.py (added test_v1_regression_gate.py to exclusions)
tech_stack:
  added: []
  patterns:
    - shared forbidden-output corpus with _assert_forbidden_values_absent()
    - in-process hook invocation via io.StringIO + monkeypatch
    - explicit allowlist safe scanner with _is_excluded() + _safe_text_files()
    - two-line window Codex claim scanner for multi-line disclaimer detection
key_files:
  created:
    - tests/test_v1_regression_gate.py
  modified:
    - tests/test_codex_claim_gate.py
decisions:
  - pytest-native aggregate gate in one focused file per D-01/D-02
  - inline synthetic constants per D-04/D-06; no shared fixture module added
  - _is_excluded() excludes test_v1_regression_gate.py from Codex claim scans
  - two-line window in Codex claim scanner handles multi-line disclaimers in docs
metrics:
  duration: "~12min"
  completed: "2026-05-05"
  tasks: 3
  files: 2
---

# Phase 05 Plan 01: Synthetic Regression Gate Summary

## One-liner

pytest-native v1 regression gate with TEST-01..TEST-06 traceability covering synthetic-only fixtures, cross-surface output hygiene, Claude hook invocation, protected path normalization, and fail-closed policy/masking behavior.

## What Was Built

Created `tests/test_v1_regression_gate.py` — a focused aggregate gate with 18 tests that prove v1 privacy behavior from package core through CLI, Claude hooks, Codex compatibility labels, and failure paths using only synthetic fixtures.

### TEST-01: Synthetic Fixture Policy and Safe Scanner
- `test_TEST_01_safe_source_scan_excludes_protected_paths_and_uses_synthetic_policy` — verifies that `_safe_text_files()` using explicit allowlist globs (`docs/**/*.md`, `privguard/**/*.py`, `tests/**/*.py`, `pyproject.toml`, `AGENTS.md`) excludes all protected components: `.git`, `.planning`, `data_sensivel`, `__pycache__`, `.pytest_cache`, pytest-cache-files- dirs, `.env`, `.env.*`

### TEST-03: Brazilian Identifier Validity, Overlap, and Lookalikes
- `test_TEST_03_identifier_validity_overlap_and_lookalikes_are_represented` — validates CPF/CNPJ with valid checksums are detected; invalid checksum lookalikes are not; secret lookalike (`sk-test-...`) produces a secret-type hit but no BR identifier; additional identifiers (CNH, PIS, SUS) are covered

### TEST-04: Protected Path Normalization
- `test_TEST_04_protected_path_normalization_is_project_root_traceable` — validates 8 path forms: posix, project-root-relative `./data_sensivel/...`, traversal `privguard/../data_sensivel/...`, Windows mixed-separator, Windows backslash, quoted Windows, `.env`, `.env.local` — all via `classify_path()` string-only, no file reads

### TEST-02: Cross-Surface Output Hygiene (4 tests)
- CLI scan `--json` output contains counts but not raw CPF value
- CLI mask `--json` output excludes both raw value and `<BR_CPF>` placeholders from JSON diagnostics
- `to_json()`/`format_text()` for detection reports and mask results exclude raw values and masked payload text
- `MaskResult` metadata serialization excludes raw secret and `<TOKEN>` placeholder

### TEST-05: Claude Hook Coverage (5 tests)
- Prompt hook blocks synthetic PII with exit 2 and sanitized output
- PreToolUse hook blocks protected path Read call with sanitized output
- Malformed JSON causes both hooks to fail open (exit 0) with empty output
- `warn`/`scrub` modes labeled `local_development_non_protective` with sanitized output
- Invalid threshold values (`nan`, `inf`, `-1`, `2`, `not-a-number`) fall back to default

### TEST-06: Fail-Closed Failure Paths (6 tests)
- Unverified `MaskResult` (verified=False) never produces `PolicyAction.ALLOW`
- All non-rewrite-capable surfaces (UNKNOWN, EXTERNAL, UNSUPPORTED, OBSERVE_ONLY, BLOCK_ONLY) block with sensitive hits
- `redact()` with empty hits on sensitive text raises `ValueError` with sanitized message (no raw CPF in exception text)
- `mask_text()` with explicitly empty hits on sensitive text produces `verified=False` and `residual_detection`
- `CODEX_COMPATIBILITY` has no `automatic_masking=True` rows
- Codex claim scan with two-line window correctly handles multi-line disclaimers; failure message is path+pattern only

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Inline synthetic constants (no shared fixture module) | Auditability — each test's fixture value is visible at the test site per D-04/D-05 |
| Exclude `test_v1_regression_gate.py` from Codex claim scanner | Gate file contains forbidden phrases as test data strings, not real claims — same policy as `test_codex_claim_gate.py` |
| Two-line window in Codex claim scanner | `docs/codex-compatibility.md` splits the canonical disclaimer across two lines; single-line check falsely flagged it |
| `_is_excluded()` added to both gate files | Symmetric exclusion: both `test_codex_claim_gate.py` and `test_v1_regression_gate.py` exclude each other's gate files |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two-line window required for Codex claim scanner**
- **Found during:** Task 3 GREEN phase
- **Issue:** `docs/codex-compatibility.md` contains the canonical disclaimer ("automatic Codex masking\nis unsupported until...") split across two lines; single-line check triggered a false positive violation
- **Fix:** Added two-line window logic matching the approach in `test_codex_claim_gate.py`
- **Files modified:** `tests/test_v1_regression_gate.py`
- **Commit:** 59511da

**2. [Rule 1 - Bug] CDX-03 gate scanned test_v1_regression_gate.py**
- **Found during:** Task 3 final full suite run
- **Issue:** Existing `test_codex_claim_gate.py` scanner picked up forbidden claim phrases inside `test_v1_regression_gate.py`'s test fixture strings and raised a false violation
- **Fix:** Added `test_v1_regression_gate.py` to the `_is_excluded()` exclusion set in `test_codex_claim_gate.py`
- **Files modified:** `tests/test_codex_claim_gate.py`
- **Commit:** 59511da

## Known Stubs

None — all tests produce real behavior assertions against the live package APIs.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes were introduced. The gate only adds test code that reads safe allowlisted files and calls existing package APIs.

## Self-Check: PASSED

- `tests/test_v1_regression_gate.py` exists: FOUND
- `tests/test_codex_claim_gate.py` modified: FOUND
- Commit 981742c (Task 1): FOUND
- Commit 7afaceb (Task 2): FOUND
- Commit 59511da (Task 3): FOUND
- 134 total tests pass: VERIFIED (`python -m pytest tests -q`)
- TEST-01 through TEST-06 strings present in gate file: VERIFIED
