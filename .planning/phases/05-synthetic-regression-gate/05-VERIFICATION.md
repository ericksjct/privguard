---
phase: 05-synthetic-regression-gate
verified: 2026-05-05T00:00:00Z
status: passed
score: 5/5
overrides_applied: 0
---

# Phase 5: Synthetic Regression Gate — Verification Report

**Phase Goal:** The full v1 surface is covered by synthetic tests proving no raw sensitive values leak through outputs, logs, hooks, masks, or failures.
**Verified:** 2026-05-05
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Developer can run `python -m pytest tests -q` and the v1 privacy gate passes using only synthetic fixtures. | VERIFIED | 134 tests pass, 18 in `tests/test_v1_regression_gate.py` specifically. Gate file contains TEST-01..TEST-06 strings in function names and module docstring. |
| 2 | Raw synthetic CPF/CNPJ/token/path/prompt/command values never appear in CLI output, hook output, diagnostics JSON/text, masked metadata, or selected failure messages. | VERIFIED | `_assert_forbidden_values_absent()` is applied to all surfaces in TEST-02 and TEST-05 tests. FORBIDDEN_OUTPUT corpus covers CPF, CNPJ, fake secrets, protected paths, placeholders, and prompt snippets. |
| 3 | Representative valid/invalid Brazilian identifiers, overlap handling, false-positive lookalikes, and protected path normalization cases are covered in the v1 gate. | VERIFIED | `test_TEST_03_identifier_validity_overlap_and_lookalikes_are_represented` covers valid CPF/CNPJ, invalid checksum lookalikes, secret lookalikes, and additional BR identifiers (CNH, PIS, SUS). `test_TEST_04_protected_path_normalization_is_project_root_traceable` covers 8 path forms including Windows, mixed-separator, traversal, quoted, and project-root-relative. |
| 4 | Claude hook prompt/tool payloads, malformed JSON, policy modes, exit codes, and sanitized output are exercised without running real Claude. | VERIFIED | 5 TEST-05 tests: prompt hook blocks PII (exit 2), PreToolUse blocks protected path (exit 2), malformed JSON fails open (exit 0, empty output), warn/scrub modes labeled non-protective, invalid thresholds fall back to default. All use in-process `io.StringIO` + monkeypatch. |
| 5 | Detection, masking, configuration, client capability, and Codex automatic-masking claim failures remain fail-closed. | VERIFIED | 6 TEST-06 tests: unverified MaskResult blocks even on REWRITE_CAPABLE surface; all 5 non-rewrite-capable surfaces block; `redact()` raises sanitized ValueError with empty hits; `mask_text()` with empty hits produces `verified=False`; CODEX_COMPATIBILITY has zero `automatic_masking=True` rows; Codex claim scan finds no violations in safe repo text. |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/test_v1_regression_gate.py` | Phase 5 pytest-native v1 synthetic regression gate | VERIFIED | File exists, 627 lines, 18 test functions. Contains TEST-01 through TEST-06 traceability in module docstring and function names. |
| `tests/test_v1_regression_gate.py` | Shared forbidden-output corpus and `_assert_forbidden_values_absent()` | VERIFIED | `FORBIDDEN_OUTPUT` tuple (17 values) defined at module level; `_assert_forbidden_values_absent()` defined at line 95; called in 5 separate test functions. |
| `tests/test_v1_regression_gate.py` | Safe allowlisted source scanner excluding protected paths | VERIFIED | `_is_excluded()` defined at line 118, excludes `.git`, `.planning`, `data_sensivel`, `__pycache__`, `.pytest_cache`, `pytest-cache-files-*`, `.env`, `.env.*`. `_safe_text_files()` defined at line 140, uses explicit allowlist globs. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_v1_regression_gate.py` | `privguard.cli.main` | direct in-process CLI calls with capsys | WIRED | `cli_main(["scan", "--json", ...])` at line 313; `cli_main(["mask", "--json", ...])` at line 325. |
| `tests/test_v1_regression_gate.py` | `privguard.hooks.main_user_prompt` / `main_pre_tool` | `io.StringIO` stdin and monkeypatch | WIRED | `main_user_prompt()` called at line 188 via `_run_user_prompt()` helper; `main_pre_tool()` called at line 197 via `_run_pre_tool()` helper. Both invoked in 5 TEST-05 tests. |
| `tests/test_v1_regression_gate.py` | `privguard.policy.decide_policy` | fail-closed capability assertions | WIRED | `decide_policy(SurfaceCapability.REWRITE_CAPABLE, ...)` at line 482; `decide_policy(capability, hits=...)` at line 500 iterating all 5 non-rewrite-capable surfaces. |
| `tests/test_v1_regression_gate.py` | `privguard.codex.CODEX_COMPATIBILITY` and Codex claim scan | safe claim/source scan without protected files | WIRED | `CODEX_COMPATIBILITY` imported at line 25 and iterated at line 539. `_safe_text_files()` used in Codex claim scanner at line 564. |

---

### Data-Flow Trace (Level 4)

The gate file contains no UI-rendering components — it is a pure test module. All "data" is synthetic inline constants flowing directly into package API calls and then into assertions. No data source produces empty or hardcoded values that would make the tests hollow.

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `test_v1_regression_gate.py` | `SYNTH_CPF`, `SYNTH_CNPJ`, etc. | Inline synthetic constants | Flows into real package APIs (`detect`, `classify_path`, `cli_main`, hook entry points) | FLOWING |
| `test_v1_regression_gate.py` | `CODEX_COMPATIBILITY` | `privguard.codex` module (imported) | Live package data structure, 8 rows verified to have 0 `automatic_masking=True` entries | FLOWING |
| `test_v1_regression_gate.py` | `_safe_text_files()` output | `pathlib.Path.glob()` on allowlisted paths | Real filesystem listing; test asserts non-empty result | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 18 gate tests pass | `python -m pytest tests/test_v1_regression_gate.py -q` | 18 passed | PASS |
| Full 134-test suite passes | `python -m pytest tests -q` | 134 passed | PASS |
| CODEX_COMPATIBILITY has no automatic_masking=True rows | Python module import check | 0 rows | PASS |
| test_v1_regression_gate.py excluded from Codex claim gate | grep in test_codex_claim_gate.py | Found at line 102 | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| TEST-01 | 05-01-PLAN.md | Test suite uses only synthetic Brazilian PII, fake secrets, and fake protected paths. | SATISFIED | Module docstring explicitly declares synthetic-only policy. `_safe_text_files()` uses explicit allowlists. `test_TEST_01_safe_source_scan_excludes_protected_paths_and_uses_synthetic_policy` verifies scanner exclusions pass. |
| TEST-02 | 05-01-PLAN.md | Tests assert raw sensitive fixture values never appear in stdout, stderr, logs, hook JSON, masked payloads, or exception messages. | SATISFIED | `FORBIDDEN_OUTPUT` corpus defined. `_assert_forbidden_values_absent()` called in 5 tests. CLI JSON, hook output, diagnostics, masked metadata, and exception messages are all covered. |
| TEST-03 | 05-01-PLAN.md | Tests cover valid/invalid Brazilian identifiers, overlap handling, and false-positive lookalikes. | SATISFIED | `test_TEST_03_identifier_validity_overlap_and_lookalikes_are_represented` covers valid CPF/CNPJ, invalid checksum lookalikes (not detected), secret lookalike producing TOKEN hit, additional BR identifiers (CNH, PIS, SUS). |
| TEST-04 | 05-01-PLAN.md | Tests cover protected path normalization for Windows paths, mixed separators, relative traversal, quoted paths, and project-root-relative paths. | SATISFIED | `test_TEST_04_protected_path_normalization_is_project_root_traceable` covers 8 explicit path forms, including posix, `./data_sensivel/...`, `privguard/../data_sensivel/...`, Windows mixed-separator traversal, Windows backslash, quoted Windows path, `.env`, `.env.local`. All assert `reason_code`. |
| TEST-05 | 05-01-PLAN.md | Tests cover Claude prompt and tool hook JSON payloads, malformed input, exit codes, policy modes, and sanitized output. | SATISFIED | 5 TEST-05 tests via in-process hook invocation: PII blocks at exit 2 with sanitized output, protected-path blocks at exit 2, malformed JSON fails open at exit 0 with empty output, warn/scrub modes labeled `local_development_non_protective`, invalid thresholds fall back to default and still block. |
| TEST-06 | 05-01-PLAN.md | Tests cover fail-closed behavior when detection, masking, configuration, or client capability validation fails. | SATISFIED | 6 TEST-06 tests: unverified MaskResult never allows, 5 non-rewrite-capable surfaces block, `redact()` raises sanitized ValueError, `mask_text()` with empty hits is unverified, CODEX_COMPATIBILITY has 0 automatic_masking rows, Codex claim scan reports path+pattern only. |

**All 6 requirements (TEST-01 through TEST-06) are SATISFIED.**

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

No TODOs, stubs, placeholder implementations, or hardcoded empty returns found. The three comments at lines 332, 351, and 371 referencing "placeholder" describe the tested behavior (placeholders forbidden in JSON surfaces) and are not stubs.

---

### Human Verification Required

None. All 5 roadmap success criteria are verifiable programmatically. The gate tests exercise real package API calls, hook invocations, and filesystem scans using pytest capsys/monkeypatch. All 134 tests pass without requiring external services, network access, or visual inspection.

---

## Gaps Summary

No gaps. All must-haves verified. Phase goal achieved.

The gate file `tests/test_v1_regression_gate.py` exists with 18 substantive tests that are wired to the live package APIs. The full test suite (134 tests) passes. TEST-01 through TEST-06 have direct function-name and docstring traceability. The safe scanner is correctly scoped. The forbidden-output corpus is applied across CLI, hook, diagnostics, masked metadata, and failure surfaces. Fail-closed behavior is confirmed for all non-rewrite-capable surfaces and unverified masking states.

---

_Verified: 2026-05-05T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
