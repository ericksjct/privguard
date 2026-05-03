---
phase: 04-codex-compatibility-evidence
plan: "01"
subsystem: codex-compatibility
tags: [codex, compatibility-matrix, claim-prevention, documentation, tdd]
dependency_graph:
  requires:
    - privguard/policy.py (SurfaceCapability, decide_policy)
    - privguard/masking.py (MaskResult contract reference)
    - privguard/detection.py (detect for policy tests)
  provides:
    - privguard/codex.py (CodexCompatibilityRow, CODEX_COMPATIBILITY, get_codex_compatibility)
    - docs/codex-compatibility.md (human-readable Codex assessment)
    - tests/test_codex_compatibility.py (CDX-01/CDX-02/CDX-03 matrix checks)
  affects:
    - .planning/REQUIREMENTS.md (CDX-01, CDX-02 satisfied)
tech_stack:
  added: []
  patterns:
    - Evidence-backed compatibility matrix (CodexCompatibilityRow dataclass)
    - Conservative labeling: experimental block-only, observe-only, unsupported
    - TDD: RED (failing import) -> GREEN (full implementation) -> tests pass
key_files:
  created:
    - privguard/codex.py
    - docs/codex-compatibility.md
    - tests/test_codex_compatibility.py
  modified: []
decisions:
  - "All 8 Codex surfaces labeled conservatively: 4 experimental block-only, 2 observe-only, 2 unsupported"
  - "No automatic_masking=True row; masking claim deferred until E2E outbound payload proof exists"
  - "SurfaceCapability vocabulary reused without extension; no new internal capability strings"
  - "docs/codex-compatibility.md and privguard/codex.py kept in sync via matrix alignment tests"
metrics:
  duration: "~10 minutes"
  completed: "2026-05-03T21:59:00Z"
  tasks_completed: 2
  files_created: 3
---

# Phase 4 Plan 1: Codex Compatibility Matrix and Assessment Summary

Evidence-backed Codex compatibility matrix with 8 labeled surfaces, conservative block-only/observe-only/unsupported labels, and automated CDX-01/CDX-02/CDX-03 claim-prevention tests — no automatic masking claim.

## What Was Built

### Task 1: Machine-readable Codex compatibility matrix (TDD)

Created `privguard/codex.py` with:

- `CodexCompatibilityRow` frozen dataclass with fields: `surface`, `support_label`, `surface_capability`, `privacy_action`, `evidence`, `tested_version_or_docs_date`, `automatic_masking`, `gaps`
- `CodexSupportLabel` vocabulary class (`EXPERIMENTAL_BLOCK_ONLY`, `OBSERVE_ONLY`, `UNSUPPORTED`)
- `CODEX_COMPATIBILITY` tuple — 8 rows covering all required Phase-04 surfaces:
  - `UserPromptSubmit prompt` — experimental block-only
  - `PreToolUse Bash` — experimental block-only
  - `PreToolUse apply_patch/Edit/Write` — experimental block-only
  - `PreToolUse MCP tool call` — experimental block-only
  - `PermissionRequest` — observe-only
  - `PostToolUse` — observe-only
  - `WebSearch and non-shell/non-MCP tools` — unsupported
  - `Automatic Codex masking rewrite` — unsupported
- `get_codex_compatibility()` public accessor

All rows map to existing `SurfaceCapability.ALL` values. No `automatic_masking=True` row exists.

Created `tests/test_codex_compatibility.py` with 13 tests covering:
- Row completeness (all required fields non-empty)
- Capability mapping (all values in `SurfaceCapability.ALL`)
- No rewrite-capable row without masking proof
- All 8 required surfaces present
- No `automatic_masking=True` row in Phase 04
- Policy behavior: block-only/observe-only/unsupported all block synthetic CPF hits via `decide_policy()`
- Doc alignment: all surfaces appear in `docs/codex-compatibility.md`
- Docs disclaimer present
- No false masking claim in docs
- `privguard/codex.py` source does not read protected files

TDD phases:
- RED commit `a0cf207`: failing import error (privguard.codex missing)
- GREEN commit `d7a63e9`: full implementation, 9/13 tests pass (4 doc-existence tests require Task 2)

### Task 2: Human-readable Codex compatibility assessment

Created `docs/codex-compatibility.md` with sections:
- Assessment Summary — states masking is unsupported, explains why
- Evidence Standard — three-part proof bar (official docs + local probe + synthetic E2E)
- Compatibility Matrix — mirrors all 8 `CODEX_COMPATIBILITY` rows with columns: Surface, Support label, SurfaceCapability, Evidence, Privacy action, Remaining gaps
- Unsupported Automatic Masking — hard constraint statement with upgrade conditions
- Remaining Gaps — 6 documented gaps with explicit upgrade path

After Task 2, all 13 tests pass.

## Verification

```
python -m pytest tests/test_codex_compatibility.py -q
# 13 passed
```

Broader regression check:
```
python -m pytest tests/ -q --ignore=tests/test_cli.py
# 99 passed
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed false-positive in test_codex_doc_does_not_read_protected_files**
- **Found during:** Task 1 GREEN phase
- **Issue:** The test was scanning its own source for literal strings like `open(".env"` — which appeared in the assert statement itself, causing a false failure
- **Fix:** Rewrote the test to scan `privguard/codex.py` source for `read_text()` / `open()` calls instead of the test file itself
- **Files modified:** `tests/test_codex_compatibility.py`
- **Commit:** `d7a63e9`

## Known Stubs

None. All matrix rows have evidence, and the docs surface names were manually verified against `CODEX_COMPATIBILITY` at write time. Tests enforce ongoing alignment.

## Threat Flags

No new security-relevant surfaces introduced beyond what is documented in the plan's threat model. `docs/codex-compatibility.md` and `privguard/codex.py` are documentation/metadata artifacts with no runtime network access or secret handling.

## Self-Check: PASSED

- `privguard/codex.py` exists: FOUND
- `docs/codex-compatibility.md` exists: FOUND
- `tests/test_codex_compatibility.py` exists: FOUND
- Commit `a0cf207` (test RED): FOUND
- Commit `d7a63e9` (feat GREEN): FOUND
- Commit `8d0ac19` (feat docs): FOUND
- `python -m pytest tests/test_codex_compatibility.py -q` → 13 passed: VERIFIED
