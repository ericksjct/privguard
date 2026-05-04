---
phase: 04-codex-compatibility-evidence
reviewed: 2026-05-04T23:21:25Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - docs/codex-compatibility.md
  - privguard/codex.py
  - tests/test_codex_compatibility.py
  - tests/test_codex_claim_gate.py
findings:
  critical: 0
  warning: 1
  info: 2
  total: 3
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-05-04T23:21:25Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Reviewed the Codex compatibility evidence document, machine-readable matrix, and claim-gate tests for conservative Codex support claims, protected-file read risks, and unsupported automatic masking claims. The matrix and docs avoid claiming automatic Codex masking, local `codex --version` matches `codex-cli 0.128.0`, and the targeted tests pass. One claim-gate blind spot could allow unsupported masking claims when proof wording appears only in a row's gaps.

## Warnings

### WR-01: Claim Gate Treats Gap Text As Verified Masking Proof

**File:** `tests/test_codex_claim_gate.py:144`
**Issue:** `_has_verified_codex_masking_proof()` accepts `"verified outbound payload replacement"` from `" ".join(row.evidence + row.gaps)`. A future row with `automatic_masking=True` and `REWRITE_CAPABLE` could satisfy the gate by putting the proof phrase in `gaps`, including wording such as "verified outbound payload replacement not proven". That weakens CDX-03 because positive Codex automatic masking claims could be allowed without evidence-backed proof.
**Fix:** Require the proof phrase in `row.evidence` only, and add a regression test proving the same phrase in `row.gaps` does not unlock the gate.

```python
def _has_verified_codex_masking_proof() -> bool:
    for row in CODEX_COMPATIBILITY:
        if (
            row.automatic_masking is True
            and row.surface_capability == SurfaceCapability.REWRITE_CAPABLE
            and any("verified outbound payload replacement" in item for item in row.evidence)
        ):
            return True
    return False
```

## Info

### IN-01: Claim Gate Does Not Scan README-style Top-Level Markdown

**File:** `tests/test_codex_claim_gate.py:112-118`
**Issue:** The safe scan covers `docs/**/*.md`, Python source/tests, `pyproject.toml`, and `AGENTS.md`, but not top-level Markdown such as `README.md` or package-facing documentation files. If future Codex support marketing text lands in a root README, the gate would not catch unsupported automatic masking claims there.
**Fix:** Extend `_safe_text_files()` to include explicit safe root Markdown files intended for users, for example `README.md` and `CHANGELOG.md`, while keeping `.planning`, `.env*`, and `data_sensivel` excluded.

### IN-02: Unused Test Imports And Fixture Constant

**File:** `tests/test_codex_compatibility.py:15-17`
**Issue:** `TYPE_CHECKING` and `pytest` are imported but unused, and `_SYNTHETIC_FAKE_TOKEN` at line 128 is unused. This is minor cleanup, but it can distract from the privacy-focused assertions in a test file whose value is claim enforcement.
**Fix:** Remove the unused imports and fixture constant unless token coverage is added in a dedicated assertion.

---

_Reviewed: 2026-05-04T23:21:25Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
