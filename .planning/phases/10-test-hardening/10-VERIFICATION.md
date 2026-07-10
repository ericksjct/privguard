---
phase: 10-test-hardening
verified: 2026-07-09T00:00:00Z
status: human_needed
score: 4/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Run mutmut under WSL or CI against the scoped [tool.mutmut] targets (detection.py, policy.py, masking.py) — `python -m mutmut run` then `python -m mutmut results`."
    expected: "A mutation score is produced and recorded; any surviving mutants in checksum/decision code are converted into new tests appended to the Tier 1/2 suites (per 10-02 Task 3 done-criteria). This completes the second half of Success Criterion 4, which cannot run on win32 (boxed/mutmut#397, DECISAO D4)."
    why_human: "mutmut refuses to start on Windows (the only available host); the deliverable requires a WSL/CI environment this verifier cannot invoke. The deferral is honestly recorded, but the mutation-score deliverable is genuinely not yet produced."
  - test: "Review the fail-closed RISCO/DECISAO findings and decide follow-up fix threads: R1 (detector exception → exit 1 → non-blocking = FAIL-OPEN in Claude Code), D1 (no internal timeout watchdog), D2 (no input-size guard, clean oversized input is allowed), D3 (EMAIL regex super-linear ReDoS-class), R12 (SUS validator accepts unassigned CNS leading-digit ranges 3-6)."
    expected: "Acknowledge that the fail-closed promise is DISPROVEN for the exception and oversized-clean-input paths — the phase's job was to pin and surface these, not to fix them, but the milestone owner should schedule the fix threads. Note the ROADMAP goal wording ('every injected detector failure results in a block') describes the target state, not the pinned-and-documented current state."
    why_human: "Whether the surfaced fail-open paths are acceptable to ship or must be fixed before release is a product/risk decision, not a code-verification fact."
---

# Phase 10: Test Hardening (fail-closed first) Verification Report

**Phase Goal:** The fail-closed promise is proven, not assumed: every injected detector failure results in a block, every adversarial evasion vector is tested and documented (pass-throughs flagged RISCO, never silenced), checksum validators survive mutation and property-based testing, and a branch-coverage gate is enforced from a measured baseline.
**Verified:** 2026-07-09
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

The phase's explicit contract (from `handoff_lacunas.md`, both PLANs, and both SUMMARYs) is to **PIN current behavior with tests and NOT fix logic bugs** — every gap is surfaced as a RISCO/DECISAO item, never silenced. Verification is assessed against that contract: a criterion is met when the behavior is tested and honestly documented, not when the underlying bug is resolved. The one exception is Success Criterion 4's mutation half, which is an incomplete deliverable (deferred to WSL/CI), not a documented finding.

### Observable Truths (Success Criteria)

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Branch-coverage baseline measured and recorded before any new test | ✓ VERIFIED | 10-01-SUMMARY records 86% total with per-module breakdown + missing-branch lists. Git order confirms ordering: baseline commit `d51ec91` ("record branch-coverage baseline") precedes all test commits (`2efbdff`, `575a8f7`, `939b56a`, …). Current measured coverage 86.70% is consistent. |
| 2 | Every injected detector failure results in a block — zero exception-to-allow paths | ✓ VERIFIED (as deliverable) | `test_fail_closed_injection.py` (11 tests, green) covers all 5 injected failures: exception, missing Presidio `[full]`, slow detector, 10 MB input, malformed config. Presidio-absent, slow, malformed-config, and PII-bearing 10 MB all block (exit 2). **The literal "always blocks" promise is DISPROVEN and surfaced**: exception → exit 1 → fail-open (R1, highest severity); clean 10 MB → allowed, no size guard (D2). Both are pinned by explicit assertions with `# RISCO`/`# DECISAO` comments matching the SUMMARY — surfaced, not silenced. See Human Verification for the risk decision. |
| 3 | Every evasion vector tested; pass-throughs are RISCO | ✓ VERIFIED | `test_evasion_adversarial.py` (14 tests, green). All ROADMAP-named vectors covered: homoglyphs (fullwidth detected; Cyrillic pass-through R2), zero-width (R3), combining (R4), fragmentation (R5, R6), encoding (base64/hex/URL R7-R9), concatenation (R10, R11), code fence/markdown/comment (detected). Every pass-through carries a `# RISCO:` comment matching the SUMMARY RISCO list; no xfail, no skip. |
| 4 | Mutation score reported + survivors→tests; hypothesis properties hold | ⚠️ PARTIAL → human_needed | **Hypothesis half VERIFIED**: `test_checksum_properties.py` (5 tests, green) — valid CPF/CNPJ always detected, invalid never, `mask(mask(x))==mask(x)`, lenient ⊇ strict; strategies compute check digits at runtime (no hardcoded PII). **Mutation half NOT delivered**: mutmut cannot run on win32 (boxed/mutmut#397); D4 records the attempted command + exact error and stages scoped `[tool.mutmut]` config. Deferral is HONEST (not silent), but no score exists and no survivor-tests were added. Requires WSL/CI (human action). |
| 5 | `--cov-fail-under` (branch) active from baseline; pre-existing suite passes | ✓ VERIFIED | `pyproject.toml` addopts = `--cov=privguard --cov-branch --cov-fail-under=84`; `[tool.coverage.run] branch=true`. Live run: `Required test coverage of 84% reached. Total coverage: 86.70%` → **326 passed, 1 skipped**. Floor 84 is set from the measured 86% baseline (few points below for headroom, documented), not guessed. |

**Score:** 4/5 truths verified (SC4 partial — mutation half deferred to WSL/CI, hypothesis half verified)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------ | ------- |
| `tests/test_fail_closed_injection.py` | P1 failure-injection suite | ✓ VERIFIED | 262 lines, 11 tests, all 5 scenarios + `assert_no_prompt_derived_text` on every path. Real assertions, no stubs. |
| `tests/test_evasion_adversarial.py` | P2 evasion suite | ✓ VERIFIED | 160 lines, 14 tests. Vectors derived at runtime from canonical fixtures. |
| `tests/test_redos_size_guard.py` | P3 ReDoS/size suite | ✓ VERIFIED | 107 lines, 6 tests. Latency bounds asserted; EMAIL super-linear + no-size-guard pinned as DECISAO. |
| `tests/test_checksum_properties.py` | P5 hypothesis suite | ✓ VERIFIED | 165 lines, 5 property tests, derandomized FAST profile. |
| `tests/test_checksum_edges.py` | P6 boundary suite | ✓ VERIFIED | 147 lines, 33 tests. Repeated-seq, DV=0, SUS ranges (R12), plate resolution. |
| `tests/test_false_positive_corpus.py` | P7 FP corpus | ✓ VERIFIED | 114 lines, 5 tests. 20-doc benign corpus, FP rate 0.0 asserted, overlap determinism over 5 runs, non-trivial guard. |
| `pyproject.toml` | dev-deps + coverage gate + mutmut config | ✓ VERIFIED | `[project.optional-dependencies].dev`, addopts with `--cov-fail-under=84`, `[tool.coverage.run]`, scoped `[tool.mutmut]`. |

All production symbols the tests depend on exist: `detect`, `valida_cpf`, `valida_cnpj`, `valida_cartao_sus` (`privguard/detection.py`), `mask_text` (`privguard/masking.py`).

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full suite green under enforced gate | `python -m pytest -q` | 326 passed, 1 skipped in 32.7s | ✓ PASS |
| Coverage gate enforced from config | (same run) | `Required test coverage of 84% reached. Total coverage: 86.70%` | ✓ PASS |
| Phase task commits present | `git log --oneline` | All 8 commits present (d51ec91, 2efbdff, 575a8f7, 939b56a, cadcade, 12d8e3b, 2bea80d, d70c3c8) | ✓ PASS |
| SUMMARY pass/skip claim accurate | run vs SUMMARY | Claimed 326/1 skipped == observed | ✓ PASS |
| mutmut on win32 | (documented) | Refuses to run (boxed/mutmut#397) — D4 | ? SKIP → human |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| TEST-07 | 10-01, 10-02 | Fail-closed / evasion / robustness test hardening with enforced coverage gate | ✓ SATISFIED (mutation half pending WSL/CI) | SC1-3,5 verified; SC4 hypothesis verified, mutation deferred (D4) |

### Anti-Patterns Found

None. No `TODO`/`FIXME`/`XXX`/`TBD`/`HACK`, no `xfail`, no `pytest.skip`, no stub returns in any of the six test files. `# RISCO:`/`# DECISAO` comments are the project's documented finding markers, each cross-referenced in the SUMMARY RISCO/DECISAO tables — auditable, not debt. The lone "xfail" string is in a docstring stating the discipline ("never xfail-and-forget").

### Human Verification Required

1. **Complete SC4 mutation score under WSL/CI** — `python -m mutmut run` against the staged `[tool.mutmut]` targets, then convert any surviving mutants in checksum/decision code to tests. Cannot run on the win32 host (boxed/mutmut#397, D4). This is the only genuinely incomplete deliverable.
2. **Risk decision on surfaced fail-open findings** — R1 (exception → exit 1 → non-blocking = FAIL-OPEN), D1 (no timeout watchdog), D2 (no input-size guard), D3 (EMAIL ReDoS-class), R12 (SUS leading-digit range). The phase correctly pinned and documented these; whether they block release is a product/risk call.

### Gaps Summary

No gaps in the phase's own pin-not-fix contract: every injected failure, evasion vector, and checksum edge has a green test that pins current behavior, every pass-through/fail-open is surfaced as a referenced RISCO/DECISAO (never silenced), the coverage gate is enforced from a measured baseline, and the pre-existing suite is intact (326 passed / 1 skipped). Status is `human_needed` rather than `passed` for two reasons: (1) SC4's mutation-score half is a real, not-yet-produced deliverable honestly deferred to WSL/CI (D4) — there is no later milestone phase to catch it; (2) the ROADMAP goal asserts the fail-closed promise "is proven," but the phase's actual (correct) finding is that the promise is DISPROVEN on the exception and clean-oversized-input paths — the milestone owner should acknowledge that divergence and schedule the R1/D2 fix threads.

---

_Verified: 2026-07-09_
_Verifier: Claude (gsd-verifier)_
