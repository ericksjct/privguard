---
phase: 10-test-hardening
plan: 01
subsystem: testing
tags: [pytest, pytest-cov, hypothesis, mutmut, fail-closed, redos, evasion, branch-coverage]

requires:
  - phase: 08-mask-mode
    provides: PII_GUARD_MODE selector and mask/block/warn hook decision paths
  - phase: 09-cleanup-hardening
    provides: cleanup.py fail-closed config-load path with sanitized reason codes
provides:
  - P1 fail-closed failure-injection suite (detector exception, missing [full] extra, slow detector, 10 MB input, malformed config)
  - P2 adversarial evasion suite (14 vectors, current behavior pinned, pass-throughs labeled RISCO)
  - P3 ReDoS latency-bound + input-size behavior suite (numeric linear, EMAIL super-linear DECISAO, no size guard DECISAO)
  - Branch-coverage baseline (86% total) recorded before any new test
  - dev optional-dependencies group (pytest, pytest-cov, hypothesis, mutmut)
affects: [10-02-plan, test-hardening-tier-2, detection-redos-fix-thread, evasion-hardening-thread]

tech-stack:
  added: [pytest-cov, hypothesis, mutmut]
  patterns:
    - "Tests pin CURRENT behavior; gaps become RISCO/DECISAO, no production code changed in a test-hardening plan"
    - "Hostile/evasion inputs derived programmatically at runtime from canonical synthetic fixtures, never new PII literals"
    - "Generous latency ceilings fence catastrophic-backtracking regressions without CI flake"

key-files:
  created:
    - tests/test_fail_closed_injection.py
    - tests/test_evasion_adversarial.py
    - tests/test_redos_size_guard.py
  modified:
    - pyproject.toml

key-decisions:
  - "No internal detector timeout exists — slow detector delays but still blocks; hung detector relies on Claude Code external timeout (fail-open their side). DECISAO: watchdog fix thread."
  - "No input-size guard — 10 MB / 2 MB inputs scanned in full (~8.5s / ~1.7s), no rejection. DECISAO: size cap fix thread."
  - "EMAIL regex is super-linear O(n^2) on long non-@ runs (13k ~0.4s, 26k ~1.6s, 52k ~7.2s). DECISAO: input-size guard + re2 migration."
  - "Detector exception escapes both hooks unhandled → exit 1 → non-blocking in Claude Code = FAIL-OPEN. RISCO: highest-severity gap."
  - "Missing presidio [full] extra cannot degrade the block path (hook runtime is stdlib-only) — proven, not a risk."

patterns-established:
  - "RISCO comment on test + matching SUMMARY entry for every documented pass-through; never xfail-and-forget"

requirements-completed: [TEST-07]

coverage:
  - id: D1
    description: "Branch-coverage baseline measured and recorded before any new test"
    requirement: TEST-07
    verification:
      - kind: unit
        ref: "pytest --cov=privguard --cov-branch (86% total, 252 passed / 1 skipped)"
        status: pass
    human_judgment: false
  - id: D2
    description: "P1 fail-closed failure-injection suite — five scenarios pinned"
    requirement: TEST-07
    verification:
      - kind: unit
        ref: "tests/test_fail_closed_injection.py (11 passed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "P2 adversarial evasion suite — 14 vectors, pass-throughs labeled RISCO"
    requirement: TEST-07
    verification:
      - kind: unit
        ref: "tests/test_evasion_adversarial.py (14 passed)"
        status: pass
    human_judgment: false
  - id: D4
    description: "P3 ReDoS latency bound + input-size behavior pinned; DECISAO items captured"
    requirement: TEST-07
    verification:
      - kind: unit
        ref: "tests/test_redos_size_guard.py (6 passed)"
        status: pass
    human_judgment: false

duration: 17min
completed: 2026-07-09
status: complete
---

# Phase 10 Plan 01: Test Hardening (Tier 1 — Fail-Closed First) Summary

**Failure-injection, adversarial-evasion, and ReDoS suites that prove the fail-closed promise instead of assuming it — 31 new tests pinning current behavior, surfacing one fail-open RISCO and three latency/robustness DECISAO items without touching production code.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-07-09T23:06:28Z
- **Completed:** 2026-07-09T23:23:23Z
- **Tasks:** 4
- **Files modified:** 4 (1 modified, 3 created)

## Branch-Coverage Baseline

Measured with `pytest --cov=privguard --cov-report=term-missing --cov-branch` **before** any new test (Task 0). Pre-existing suite: **252 passed / 1 skipped**.

| Module | Cover | Notes |
|--------|-------|-------|
| `privguard/detection.py` | 89% | missing branches below |
| `privguard/policy.py` | 93% | missing branches below |
| `privguard/masking.py` | 97% | line 44 |
| `privguard/hooks.py` | 78% | missing branches below |
| `privguard/cleanup.py` | 76% | error/skip branches |
| `privguard/cli.py` | 89% | 27-28, 42-43, 69-77, 210 |
| `privguard/diagnostics.py` | 89% | 124→126, 155→154, 165→164, 310→319, etc. |
| `privguard/codex.py` | 100% | — |
| **TOTAL** | **86%** | 1087 stmts, 424 branches, 127 miss, 69 brpart |

### Missing branches — target modules

- **detection.py:** 37, 50, 65, 73, 82, 89-90, 96, 105, 113, 117, 124, 136 (validator early-returns for wrong-length / repeated-digit inputs), 269-271 (name-hit surname/first branch)
- **policy.py:** 139, 176, 203, 241→250, 271, 288-290, 294, 298
- **masking.py:** 44 (`_normalize_hits` overlap-skip branch)
- **hooks.py:** 78-80, 110-114, 116-119, 127→125, 129, 136→135, 140, 202-210, 215-216, 224, 239, 325-330, 335-336, 345, 367, 371, 397, 403, 414-416 (help args, `_iter_path_values` dict/list recursion, `check_bash`, warn/mask branches, per-tool dispatch tails)

(Tier 2 plan 10-02 targets these branches directly; a `--cov-fail-under` gate is deferred to 10-02 per plan scope.)

## RISCO List (evasion + fail-closed pass-throughs)

| # | Vector / Gap | Current behavior | Test |
|---|--------------|------------------|------|
| R1 | Detector raises exception (UserPromptSubmit + PreToolUse) | Exception escapes unhandled → exit 1 → **non-blocking = FAIL-OPEN** | test_fail_closed_injection.py::test_*_detector_exception_escapes_unhandled |
| R2 | Cyrillic homoglyph digits in CPF | pass-through (undetected) | test_evasion_adversarial.py::test_cyrillic_homoglyph_cpf_passes_through |
| R3 | Zero-width chars inside CPF | pass-through | test_zero_width_chars_inside_cpf_pass_through |
| R4 | Combining chars on CPF digits | pass-through | test_combining_chars_on_cpf_digits_pass_through |
| R5 | CPF fragmented across lines | pass-through | test_cpf_fragmented_across_lines_passes_through |
| R6 | Whitespace injected between digits | pass-through | test_whitespace_injected_between_digits_passes_through |
| R7 | Base64-encoded secret | pass-through (no decode-and-rescan stage) | test_base64_encoded_secret_passes_through |
| R8 | Hex-encoded secret | pass-through | test_hex_encoded_secret_passes_through |
| R9 | URL/percent-encoded secret | pass-through | test_url_encoded_secret_passes_through |
| R10 | String concatenation `"a" + "b"` CPF | pass-through (static scan never reassembles) | test_string_concatenation_cpf_passes_through |
| R11 | f-string concatenation CPF | pass-through | test_fstring_concatenation_cpf_passes_through |

R1 is the highest-severity item: a crashing detector is fail-open in Claude Code because only exit code 2 blocks. R2–R11 are detection-recall gaps consistent with a stdlib regex scanner (no normalization / decode / dataflow stage). Detected (not RISCO): fullwidth digits, code fence, markdown link, code comment.

## DECISAO List (candidate fix threads)

| # | Decision | Evidence |
|---|----------|----------|
| D1 | No internal detector timeout | slow detector (0.3s sleep) still blocks; a *hung* detector relies on Claude Code's external hook timeout, treated as non-blocking on their side. Watchdog that maps timeout→block is a fix thread. |
| D2 | No input-size guard | 10 MB prompt scanned in full (~8.5s) then blocks (with PII) or allows (clean); 2 MB scanned (~1.7s), CPF still detected. No rejection of oversized input. Fix thread: cap input length before regex. |
| D3 | EMAIL regex super-linear (ReDoS-class) | `\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b` on a long non-`@` run scales ~O(n²): 13k ~0.4s, 26k ~1.6s, 52k ~7.2s. Numeric patterns are linear. Fix thread: input-size guard + migrate risky patterns to `re2` (no backtracking). |

R1 (detector-exception fail-open) is also a fix-thread candidate; recorded as RISCO above because it is a correctness gap, not a design tradeoff.

## Task Commits

1. **Task 0: Baseline + dev-deps** — `d51ec91` (test)
2. **Task 1: P1 fail-closed failure injection** — `2efbdff` (test)
3. **Task 2: P2 adversarial evasion** — `575a8f7` (test)
4. **Task 3: P3 ReDoS + input-size behavior** — `939b56a` (test)

_All four tasks are `type="auto" tdd="false"`; each is a single test/config commit._

## Files Created/Modified

- `pyproject.toml` — added `[project.optional-dependencies].dev` (pytest, pytest-cov, hypothesis, mutmut)
- `tests/test_fail_closed_injection.py` — P1 suite (11 tests)
- `tests/test_evasion_adversarial.py` — P2 suite (14 tests)
- `tests/test_redos_size_guard.py` — P3 suite (6 tests)

## Decisions Made

See DECISAO List above. No production logic was changed — the handoff and plan explicitly forbid fixes in this plan; every gap is a RISCO/DECISAO for a separate Fixer thread.

## Deviations from Plan

None - plan executed exactly as written.

The plan anticipated the P3 outcome ("if any regex proves backtracking-risky, record re2 migration as a DECISAO"); the EMAIL super-linear finding is recorded as DECISAO D3 accordingly, not a deviation.

## Issues Encountered

- The `rtk` command proxy raised a `ValueError` rendering a 50k-character pytest parametrize ID. Resolved by adding explicit short `ids=` to the numeric parametrize; running via plain `python -m pytest` was unaffected. No test logic changed.

## Next Phase Readiness

- Tier 1 (P1–P3) complete and green: full suite **283 passed** (252 baseline + 31 new).
- Plan 10-02 (Tier 2) can proceed: property-based validators, checksum edges, FP corpus, mutation testing, and the `--cov-fail-under` branch-coverage gate (baseline 86% recorded here as the floor reference).
- Open fix threads for a separate track: R1 (detector-exception fail-open), D1 (timeout watchdog), D2 (input-size guard), D3 (EMAIL re2 migration).

---
*Phase: 10-test-hardening*
*Completed: 2026-07-09*

## Self-Check: PASSED

All three test files and the SUMMARY exist on disk; all four task commits (d51ec91, 2efbdff, 575a8f7, 939b56a) present in git history.
