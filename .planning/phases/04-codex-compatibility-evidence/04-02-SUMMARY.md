---
phase: 04-codex-compatibility-evidence
plan: "02"
subsystem: codex-compatibility
tags: [codex, claim-prevention, tdd, testing, cdx-03]
dependency_graph:
  requires:
    - privguard/codex.py (CODEX_COMPATIBILITY, CodexCompatibilityRow from plan 04-01)
    - privguard/policy.py (SurfaceCapability for proof check)
    - docs/codex-compatibility.md (scanned for forbidden claim patterns)
  provides:
    - tests/test_codex_claim_gate.py (CDX-03 claim-prevention gate)
  affects:
    - .planning/REQUIREMENTS.md (CDX-03 satisfied)
tech_stack:
  added: []
  patterns:
    - Safe repository text scanning with explicit glob allowlists and path exclusions
    - Multi-line disclaimer detection via two-line whitespace-collapsed window
    - Grounded claim gate: positive claims allowed only when CODEX_COMPATIBILITY has verified proof
    - Self-exclusion of claim gate test files to prevent synthetic fixture self-flagging
key_files:
  created:
    - tests/test_codex_claim_gate.py
  modified: []
key_decisions:
  - "Excluded test_codex_claim_gate.py and test_codex_compatibility.py from the scan — both reference forbidden strings as test fixtures or assertion strings, not claims"
  - "Multi-line disclaimer in docs and codex.py handled via two-line window with whitespace collapse"
  - "Surface-name literals (e.g. surface='Automatic Codex masking rewrite') allowed in codex.py data fields — not a claim"
  - "Section-divider comments referencing surface name allowed in codex.py — not a claim"
  - "No weakening of FORBIDDEN_CLAIM_PATTERNS; only precise exemptions for negated/disclaimer/data contexts"
requirements_completed: [CDX-03]

# Metrics
duration: ~9min
completed: "2026-05-03T22:06:36Z"
tasks_completed: 2
files_created: 1
---

# Phase 4 Plan 2: Codex Claim Gate Summary

**CDX-03 repository claim-prevention gate scanning docs, privguard source, and config for unsupported automatic Codex masking claims, grounded in CODEX_COMPATIBILITY matrix proof**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-05-03T22:04:21Z
- **Completed:** 2026-05-03T22:06:36Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Created `tests/test_codex_claim_gate.py` with `FORBIDDEN_CLAIM_PATTERNS`, `ALLOWED_NEGATED_CLAIMS`, `_ALLOWED_SURFACE_NAME_LITERALS`, `_safe_text_files()`, `_has_verified_codex_masking_proof()`, `_find_unsupported_claims()`, and `test_codex_automatic_masking_claims_require_verified_matrix_proof`
- Claim gate scans `docs/**/*.md`, `privguard/**/*.py`, `tests/**/*.py`, `pyproject.toml`, and `AGENTS.md` while excluding `.env`, `data_sensivel`, `.planning`, `.git`, `__pycache__`, `.pytest_cache`, and pytest cache files
- Gate passes only when no forbidden automatic masking phrases are found OR when `CODEX_COMPATIBILITY` has a row with `automatic_masking=True` + `REWRITE_CAPABLE` + verified outbound replacement evidence
- All 4 gate tests pass; full Phase 04 suite (17 tests) passes together

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: add failing CDX-03 claim gate test** - `6d7a497` (test)
2. **Task 1 GREEN: implement CDX-03 claim gate with multi-line and surface-name handling** - `bbf9b60` (feat)
3. **Task 2: verification — 17 tests pass, no changes needed** — no new commit (no file changes)

## Files Created/Modified

- `tests/test_codex_claim_gate.py` — CDX-03 repository claim-prevention gate; scans safe text targets for unsupported automatic Codex masking claims; grounded in CODEX_COMPATIBILITY matrix proof

## Decisions Made

- Excluded `test_codex_claim_gate.py` and `test_codex_compatibility.py` from the scan scope — both files legitimately reference forbidden strings as test fixtures and assertion messages, not as product claims. Scanning them would cause permanent false positives.
- Multi-line disclaimer in `docs/codex-compatibility.md` and `privguard/codex.py` (sentence split across two lines) is handled by checking a two-line window with whitespace collapsed to single spaces, so `automatic codex masking\n    is unsupported until...` matches the canonical allowed disclaimer.
- Surface name string literals like `surface="Automatic Codex masking rewrite"` in `privguard/codex.py` are data values (the matrix surface name), not claims. Added `_ALLOWED_SURFACE_NAME_LITERALS` to recognize quoted variants.
- Section-divider comments in `privguard/codex.py` (e.g. `# Automatic Codex masking rewrite`) are documentation markers, not claims. Allowed via `is_section_divider_comment` check.
- Docstring/comment negation `CDX-03: No automatic Codex masking claim until...` is explicitly allowed via `ALLOWED_NEGATED_CLAIMS` entry `"no automatic codex masking claim"`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Multi-line disclaimer in docs not matched by naive line-only checker**
- **Found during:** Task 1 GREEN phase
- **Issue:** `docs/codex-compatibility.md` has `**automatic Codex masking` on one line and `is unsupported until verified outbound payload replacement is proven**` on the next. The naive single-line check couldn't match the allowed disclaimer, causing a false violation.
- **Fix:** Added two-line window check with whitespace collapse (`_re.sub(r"\s+", " ", line1 + " " + line2)`) so split sentences are matched correctly.
- **Files modified:** `tests/test_codex_claim_gate.py`
- **Commit:** `bbf9b60`

**2. [Rule 1 - Bug] Gate test self-flagged on synthetic fixture strings**
- **Found during:** Task 1 GREEN phase (iterative)
- **Issue:** The scanner includes `tests/**/*.py`; `test_codex_claim_gate.py` and `test_codex_compatibility.py` contain the forbidden strings as test fixture values and assertion messages, causing self-flagging.
- **Fix:** Added `name in {"test_codex_claim_gate.py", "test_codex_compatibility.py"}` to `_is_excluded()` so the gate test files are excluded from the repository scan.
- **Files modified:** `tests/test_codex_claim_gate.py`
- **Commit:** `bbf9b60`

**3. [Rule 1 - Bug] Surface name data fields and section comments triggered forbidden pattern**
- **Found during:** Task 1 GREEN phase (iterative)
- **Issue:** `privguard/codex.py` has `surface="Automatic Codex masking rewrite"` as a data field and `# Automatic Codex masking rewrite` as a section comment. These are matrix metadata, not claims, but matched `automatic codex masking`.
- **Fix:** Added `_ALLOWED_SURFACE_NAME_LITERALS` for quoted string variants and `is_section_divider_comment` check for `# ...` lines containing the surface name.
- **Files modified:** `tests/test_codex_claim_gate.py`
- **Commit:** `bbf9b60`

---

**Total deviations:** 3 auto-fixed (all Rule 1 — bugs in the naive claim detection logic)
**Impact on plan:** All fixes were necessary to achieve a correct gate that distinguishes real claims from negated disclaimers, data field values, and test fixtures. No FORBIDDEN_CLAIM_PATTERNS were weakened.

## Issues Encountered

The main challenge was that legitimate uses of the forbidden pattern strings exist throughout the codebase — in disclaimers, surface-name data fields, comments, and test fixtures — all of which are explicitly NOT false claims. The detection logic required several targeted exemptions to avoid false positives while keeping the gate strict against actual positive masking claims.

## Known Stubs

None. The gate is fully wired to `CODEX_COMPATIBILITY` and scans actual repository files.

## Threat Flags

No new security-relevant surfaces introduced. `tests/test_codex_claim_gate.py` is a test-only artifact that reads source files for content analysis but does not expose sensitive data or create network endpoints.

## Self-Check: PASSED

- `tests/test_codex_claim_gate.py` exists: FOUND
- Commit `6d7a497` (test RED): FOUND
- Commit `bbf9b60` (feat GREEN): FOUND
- `python -m pytest tests/test_codex_claim_gate.py -q` → 4 passed: VERIFIED
- `python -m pytest tests/test_codex_compatibility.py tests/test_codex_claim_gate.py -q` → 17 passed: VERIFIED
- `FORBIDDEN_CLAIM_PATTERNS` in test_codex_claim_gate.py: FOUND
- `ALLOWED_NEGATED_CLAIMS` in test_codex_claim_gate.py: FOUND
- `test_codex_automatic_masking_claims_require_verified_matrix_proof` in test_codex_claim_gate.py: FOUND
- Exclusions for `.env`, `data_sensivel`, `.planning`, `.git`, `pytest-cache-files-`: FOUND

## Next Phase Readiness

- CDX-03 satisfied: claim-prevention gate blocks unsupported automatic Codex masking claims
- Phase 04 complete: matrix (04-01) + claim gate (04-02) deliver the full Codex evidence artifact
- No blockers for subsequent phases

---
*Phase: 04-codex-compatibility-evidence*
*Completed: 2026-05-03*
