---
phase: 04-codex-compatibility-evidence
verified: 2026-05-04T00:00:00Z
status: passed
score: 6/6
overrides_applied: 0
---

# Phase 4: Codex Compatibility Evidence Verification Report

**Phase Goal:** Codex support is represented honestly through tested interception evidence, capability labels, and no automatic masking claims until raw payload replacement is proven.
**Verified:** 2026-05-04T00:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Developer can read a current Codex compatibility assessment that states which prompt and tool interception options were verified. | VERIFIED | `docs/codex-compatibility.md` exists with `# Codex Compatibility`, `## Assessment Summary`, `## Evidence Standard`, `## Compatibility Matrix`, `## Remaining Gaps`; 8 surfaces documented with labels, evidence sources, and gaps. |
| 2 | Developer can see each Codex surface labeled as supported, experimental, block-only, or unsupported with evidence. | VERIFIED | All 8 surfaces in `CODEX_COMPATIBILITY` have non-empty `support_label`, `surface_capability`, `evidence`, `tested_version_or_docs_date`, and `gaps`. Labels are `experimental block-only` (4), `observe-only` (2), `unsupported` (2). Matrix mirrored verbatim in `docs/codex-compatibility.md`. |
| 3 | Developer cannot enable or encounter a claim of automatic Codex masking unless a tested integration proves raw outbound payloads are replaced before provider submission. | VERIFIED | `tests/test_codex_claim_gate.py` scans `docs/**/*.md`, `privguard/**/*.py`, `tests/**/*.py`, `pyproject.toml`, and `AGENTS.md`; fails when forbidden claim patterns appear and `_has_verified_codex_masking_proof()` returns False. No `automatic_masking=True` row exists. Gate passes (0 violations found). 17/17 tests pass. |
| 4 | Developer cannot encounter unsupported automatic Codex masking claims in safe repository text. (CDX-03 plan 02 truth) | VERIFIED | `test_codex_automatic_masking_claims_require_verified_matrix_proof` passes with 0 violations found across all 19 scanned files. `docs/codex-compatibility.md` contains no phrase `Codex masks prompts automatically`. |
| 5 | Any future Codex automatic masking claim must be backed by a matrix row with verified outbound replacement proof. (CDX-03 plan 02 truth) | VERIFIED | `_has_verified_codex_masking_proof()` requires `automatic_masking=True`, `REWRITE_CAPABLE`, and `"verified outbound payload replacement"` in evidence. Currently returns False; gate fails on positive claims unless this condition is met. Test 3 (`test_positive_claim_without_matrix_proof_is_flagged`) confirms the gate catches violations. |
| 6 | Claim-gate diagnostics do not expose synthetic raw values, protected paths, or prompt snippets. (CDX-03 plan 02 truth) | VERIFIED | Failure message in `test_codex_automatic_masking_claims_require_verified_matrix_proof` reports only file path and pattern name — no raw line content. `test_safe_file_scan_excludes_protected_paths` passes, confirming `.env`, `data_sensivel`, `.planning`, `.git`, and `__pycache__` are excluded. |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `privguard/codex.py` | Machine-readable Codex compatibility rows | VERIFIED | 277 lines. Exports `CodexCompatibilityRow`, `CodexSupportLabel`, `CODEX_SUPPORT_LABELS`, `CODEX_COMPATIBILITY` (8 rows), `get_codex_compatibility()`. Imports `SurfaceCapability` from `.policy`. No `automatic_masking=True` row. |
| `docs/codex-compatibility.md` | Human-readable Codex assessment and compatibility matrix | VERIFIED | 128 lines. Contains `# Codex Compatibility`, `## Compatibility Matrix`, `codex-cli 0.128.0`, canonical disclaimer `automatic Codex masking is unsupported until verified outbound payload replacement is proven`, and no phrase `Codex masks prompts automatically`. |
| `tests/test_codex_compatibility.py` | Automated CDX-01/CDX-02 matrix checks | VERIFIED | 237 lines. Contains `test_codex_matrix_rows_are_complete_and_conservative`. Imports `CODEX_COMPATIBILITY` from `privguard.codex`. 13 tests — all pass. |
| `tests/test_codex_claim_gate.py` | Repository claim-prevention gate for CDX-03 | VERIFIED | 329 lines. Contains `FORBIDDEN_CLAIM_PATTERNS`, `ALLOWED_NEGATED_CLAIMS`, `test_codex_automatic_masking_claims_require_verified_matrix_proof`. Excludes `.env`, `data_sensivel`, `.planning`, `.git`, `pytest-cache-files-`. 4 tests — all pass. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `docs/codex-compatibility.md` | `privguard/codex.py` | same surface names and labels | WIRED | All 8 `CODEX_COMPATIBILITY` surface strings appear in `docs/codex-compatibility.md` table. `test_codex_doc_contains_all_matrix_surfaces` verifies and passes. |
| `tests/test_codex_compatibility.py` | `privguard.codex.CODEX_COMPATIBILITY` | direct import | WIRED | Line 19: `from privguard.codex import CODEX_COMPATIBILITY, CodexCompatibilityRow, get_codex_compatibility`. Import confirmed importable (`python -c "from privguard.codex import CODEX_COMPATIBILITY; print(len(CODEX_COMPATIBILITY))"` → 8). |
| `privguard/codex.py` | `privguard.policy.SurfaceCapability` | row surface_capability values | WIRED | Line 20: `from .policy import SurfaceCapability`. All 8 rows use `SurfaceCapability.BLOCK_ONLY`, `SurfaceCapability.OBSERVE_ONLY`, or `SurfaceCapability.UNSUPPORTED`. `test_codex_matrix_capabilities_map_to_surface_capability_all` verifies and passes. |
| `tests/test_codex_claim_gate.py` | `privguard.codex.CODEX_COMPATIBILITY` | direct import | WIRED | Line 25: `from privguard.codex import CODEX_COMPATIBILITY`. Used in `_has_verified_codex_masking_proof()`. |
| `tests/test_codex_claim_gate.py` | `docs/codex-compatibility.md` | safe text scan via `docs/**/*.md` glob | WIRED | `_safe_text_files(pathlib.Path("."))` includes `docs/codex-compatibility.md` (confirmed programmatically — 19 files scanned, docs/codex-compatibility.md present). Pattern `"codex-compatibility.md"` does not appear as a literal string; file is reached by glob. |

---

### Data-Flow Trace (Level 4)

Not applicable — all artifacts are documentation, data-class definitions, and test files. No dynamic data rendering or user-facing UI components.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase 04 test suite passes | `python -m pytest tests/test_codex_compatibility.py tests/test_codex_claim_gate.py -q` | 17 passed | PASS |
| Broader regression check | `python -m pytest tests/ -q --ignore=tests/test_cli.py` | 103 passed | PASS |
| `privguard.codex` module is importable with 8 rows | `python -c "from privguard.codex import CODEX_COMPATIBILITY; print(len(CODEX_COMPATIBILITY))"` | 8 | PASS |
| No `automatic_masking=True` row | `python -c "from privguard.codex import CODEX_COMPATIBILITY; print(sum(1 for r in CODEX_COMPATIBILITY if r.automatic_masking))"` | 0 | PASS |
| No `rewrite-capable` row | `python -c "from privguard.codex import CODEX_COMPATIBILITY; print(sum(1 for r in CODEX_COMPATIBILITY if r.surface_capability=='rewrite-capable'))"` | 0 | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| CDX-01 | 04-01-PLAN.md | Project documents the current Codex interception options and whether prompt/tool payloads can be blocked or rewritten before provider submission. | SATISFIED | `docs/codex-compatibility.md` documents all 8 surfaces with interception status, evidence, and gaps. `tests/test_codex_compatibility.py` enforces row completeness and doc alignment. |
| CDX-02 | 04-01-PLAN.md | Project includes a compatibility matrix that marks Codex support as supported, experimental, block-only, or unsupported with evidence. | SATISFIED | `privguard/codex.py` `CODEX_COMPATIBILITY` contains 8 rows with `support_label`, `surface_capability`, `evidence`, and `tested_version_or_docs_date`. Matrix uses labels `experimental block-only`, `observe-only`, `unsupported`. `test_codex_matrix_capabilities_map_to_surface_capability_all` enforces valid labels. |
| CDX-03 | 04-02-PLAN.md | Guard does not claim automatic Codex masking until a tested integration proves raw payloads are replaced before submission. | SATISFIED | `tests/test_codex_claim_gate.py` scans safe repository files for forbidden claim patterns and fails unless `_has_verified_codex_masking_proof()` returns True. Currently returns False; no violations found. 4 claim-gate tests pass. |

All 3 phase 4 requirements (CDX-01, CDX-02, CDX-03) fully satisfied.

---

### Anti-Patterns Found

No blockers, warnings, or notable anti-patterns found.

- No TODO/FIXME/PLACEHOLDER comments in any phase 4 artifact.
- No stub returns (`return null`, `return []`, `return {}`).
- `privguard/codex.py` contains no `open()` or `read_text()` calls (verified by `test_codex_doc_does_not_read_protected_files`).
- No raw sensitive data in test files — synthetic CPF `123.456.789-09` and fake token `sk-test-abcdefghijklmnopqrstuvwxyz` are correctly contained in test fixtures and excluded from claim-gate scan scope.

---

### Human Verification Required

None. All must-haves are verifiable programmatically. The test suite provides automated enforcement of all CDX-01/CDX-02/CDX-03 requirements.

---

### Gaps Summary

No gaps. All 6 observable truths verified, all 4 artifacts present and substantive, all 5 key links wired, all 3 requirements satisfied, 17/17 phase tests pass, 103/103 regression tests pass.

---

_Verified: 2026-05-04T00:00:00Z_
_Verifier: Claude (gsd-verifier)_