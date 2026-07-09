---
phase: 10-test-hardening
plan: 02
subsystem: testing
tags: [pytest, hypothesis, mutmut, property-based, checksum, false-positive, branch-coverage, cov-fail-under]

requires:
  - phase: 10-test-hardening
    plan: 01
    provides: dev optional-deps (pytest-cov, hypothesis, mutmut) installed; 86% branch-coverage baseline; Tier 1 suites green (283 passed)
provides:
  - P5 hypothesis property suite over CPF/CNPJ validators and masking idempotence/superset invariants
  - P6 checksum boundary suite (repeated-sequence blacklist, DV=0 branch, SUS leading-digit ranges, plate format resolution)
  - P7 synthetic false-positive corpus with measured (0.0) FP rate and deterministic overlap resolution
  - Enforced branch-coverage gate (--cov-fail-under=84) in pyproject.toml
  - Scoped [tool.mutmut] config + DECISAO to run mutation testing under WSL/CI (mutmut has no native win32 support)
affects: [test-hardening-tier-3, sus-leading-digit-fix-thread, mutation-testing-ci-thread]

tech-stack:
  added: []
  patterns:
    - "Hypothesis strategies COMPUTE valid CPF/CNPJ check digits at runtime rather than hardcoding PII literals"
    - "Fixed derandomized Hypothesis profile (max_examples capped, deadline disabled) keeps property tests fast and CI-stable"
    - "Coverage gate floor set a few points below the measured baseline for headroom, not guessed"

key-files:
  created:
    - tests/test_checksum_properties.py
    - tests/test_checksum_edges.py
    - tests/test_false_positive_corpus.py
  modified:
    - pyproject.toml

key-decisions:
  - "mutmut refuses to run natively on Windows (boxed/mutmut#397) — mutation score deferred to WSL/CI; scoped [tool.mutmut] config staged so the run is unattended. DECISAO D4."
  - "SUS card validator enforces only length(15) and weighted-sum % 11 == 0 — no CNS leading-digit range check, so unassigned ranges (3-6) with a valid checksum are accepted. RISCO R12."
  - "Repeated-sequence CPFs/CNPJs are ALREADY blacklisted by the validators' cpf==cpf[0]*11 / cnpj==cnpj[0]*14 guards — no gap, pinned as positive behavior."
  - "Coverage gate set to --cov-fail-under=84 (branch): below the 86% 10-01 baseline and 87% post-10-02 measurement for CI headroom."

requirements-completed: [TEST-07]

coverage:
  - id: D5
    description: "P5 property-based validator + masking invariants hold with no false counterexamples"
    requirement: TEST-07
    verification:
      - kind: unit
        ref: "tests/test_checksum_properties.py (5 passed)"
        status: pass
    human_judgment: false
  - id: D6
    description: "P6 checksum boundary/blacklist edges pinned; SUS leading-digit gap surfaced as RISCO"
    requirement: TEST-07
    verification:
      - kind: unit
        ref: "tests/test_checksum_edges.py (33 passed)"
        status: pass
    human_judgment: false
  - id: D7
    description: "P7 FP corpus with measured (0.0) rate + deterministic overlap resolution"
    requirement: TEST-07
    verification:
      - kind: unit
        ref: "tests/test_false_positive_corpus.py (5 passed)"
        status: pass
    human_judgment: false
  - id: D8
    description: "Branch-coverage gate enforced from pyproject and full suite passes under it"
    requirement: TEST-07
    verification:
      - kind: unit
        ref: "pytest -q → 'Required test coverage of 84% reached. Total coverage: 86.70%' (326 passed / 1 skipped)"
        status: pass
    human_judgment: false

duration: 11min
completed: 2026-07-09
status: complete
---

# Phase 10 Plan 02: Test Hardening (Tier 2 — Bugs That Pass Green) Summary

**Property-based validator testing, checksum boundary pins, a measured (0.0) false-positive corpus, and an enforced branch-coverage gate (--cov-fail-under=84) — 43 new tests surfacing one new validation RISCO (SUS leading-digit) and deferring mutation scoring to WSL/CI, with no production code changed.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-07-09T23:32:13Z
- **Completed:** 2026-07-09T23:43:11Z
- **Tasks:** 4
- **Files modified:** 4 (1 modified, 3 created)

## Coverage Gate

Full suite after the 10-02 suites: **326 passed / 1 skipped**, branch coverage **86.70%** (rounded 87%, up from the 86% 10-01 baseline; `detection.py` 90% → 92%).

The gate is now enforced from `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "--cov=privguard --cov-branch --cov-fail-under=84"

[tool.coverage.run]
branch = true
source = ["privguard"]
```

Floor **84%** is a few points below the measured baseline (86%) and current value (87%) to fence regressions without CI flake. Gate run output: `Required test coverage of 84% reached. Total coverage: 86.70%`.

## Mutation Testing (P4) — deferred to WSL/CI (DECISAO D4)

- **Command attempted:** `python -m mutmut run` (also `python -m mutmut version`)
- **Output (both):** `To run mutmut on Windows, please use the WSL. Native windows support is tracked in issue https://github.com/boxed/mutmut/issues/397`
- mutmut refuses to start on win32; it is not skipped silently. A scoped `[tool.mutmut]` config (`paths_to_mutate = detection.py, policy.py, masking.py`; `tests_dir = tests/`) is committed so the scored run executes unattended under WSL or CI.
- **Consequence:** no mutation score is available on this host and no surviving mutants were identified, so no survivor-mutant tests were appended this plan. Converting survivors into tests is part of the WSL/CI follow-up (D4).

## Measured False-Positive Rate (P7)

- Benign PT-BR developer corpus of **20 documents** (code snippets, docs prose, version numbers `1.2.3`, dates, issue IDs `ABC-123`, PR refs `#456`).
- **Measured FP rate: 0.000** (0 documents with hits, 0 total hits), asserted under a `0.05` ceiling for headroom. The one candidate FP found during authoring (a private IP `192.168.x.x`) was a genuine `IP_PRIVADO` detection, not a false positive, and was excluded from the benign corpus.
- Overlap resolution (CPF vs phone, boleto vs PIS, CNPJ) is deterministic across 5 repeated runs.

## Consolidated Phase RISCO / DECISAO List (Tiers 1 + 2)

### RISCO (correctness gaps — Fixer threads)

| # | Vector / Gap | Current behavior | Source |
|---|--------------|------------------|--------|
| R1 | Detector raises exception (both hooks) | Escapes unhandled → exit 1 → **non-blocking = FAIL-OPEN** (highest severity) | 10-01 |
| R2–R11 | Evasion vectors (Cyrillic/zero-width/combining homoglyphs, cross-line & whitespace fragmentation, base64/hex/URL encoding, string/f-string concatenation) | pass-through (undetected) — consistent with a stdlib regex scanner (no normalize/decode/dataflow stage) | 10-01 |
| **R12** | **SUS card leading-digit range** | `valida_cartao_sus` checks only length 15 + weighted-sum % 11 == 0; **unassigned CNS ranges (3–6) with a valid checksum are accepted**. Fix thread: add a leading-digit range guard. | **10-02** |

### DECISAO (design tradeoffs / infra — candidate threads)

| # | Decision | Evidence | Source |
|---|----------|----------|--------|
| D1 | No internal detector timeout | slow detector still blocks; a hung detector relies on Claude Code's external timeout (fail-open their side). Watchdog fix thread. | 10-01 |
| D2 | No input-size guard | 10 MB / 2 MB inputs scanned in full (~8.5s / ~1.7s), no rejection. Size cap fix thread. | 10-01 |
| D3 | EMAIL regex super-linear (ReDoS-class) | ~O(n²) on long non-`@` runs (52k ≈ 7.2s); numeric patterns linear. Input-size guard + re2 migration. | 10-01 |
| **D4** | **mutmut has no native Windows support** | `python -m mutmut run` → boxed/mutmut#397; run under WSL/CI, config staged. | **10-02** |

### Positive findings pinned (NOT risks)

- Repeated-sequence CPFs/CNPJs (`111.111.111-11` … `000.000.000-00`) are already blacklisted by the validators' `== d*len` guards — no blacklist gap.
- Property invariants hold with no counterexamples: valid CPF/CNPJ always detected; invalid-checksum 11-digit strings never detected as CPF; `mask(mask(x)) == mask(x)`; lenient ⊇ strict coverage.
- Old-plate vs Mercosul formats do not overlap; resolution is deterministic.
- FP rate 0.0 on the benign corpus.

## Task Commits

1. **Task 0: P5 hypothesis properties** — `cadcade` (test)
2. **Task 1: P6 checksum boundary + blacklist edges** — `12d8e3b` (test)
3. **Task 2: P7 FP corpus + deterministic overlap** — `2bea80d` (test)
4. **Task 3: P4 mutation config + coverage gate + WSL/CI DECISAO** — `d70c3c8` (test)

_All four tasks are `type="auto" tdd="false"`; each is a single test/config commit._

## Files Created/Modified

- `tests/test_checksum_properties.py` — P5 property suite (5 tests)
- `tests/test_checksum_edges.py` — P6 boundary suite (33 tests)
- `tests/test_false_positive_corpus.py` — P7 FP corpus + overlap suite (5 tests)
- `pyproject.toml` — enforced branch-coverage gate, `[tool.coverage.run]`, scoped `[tool.mutmut]`

## Deviations from Plan

None — plan executed as written. The plan anticipated the mutmut/Windows outcome ("if it fails to run on win32, record a DECISAO … capture the attempted command + error"); D4 is that recorded outcome, not a deviation. The SUS leading-digit RISCO (R12) is a Task 1 pinned gap, exactly the kind the plan asked to surface rather than fix.

## Known Stubs

None. No placeholder/stub code was introduced; all new artifacts are tests and config.

## Next Phase Readiness

- Tiers 1 + 2 complete and green: full suite **326 passed / 1 skipped** under the enforced gate.
- Handoff "critério de pronto" items 1–5 satisfied for Tiers 1–2: baseline recorded (10-01), Tiers 1–2 green, `--cov-fail-under` active, mutation score reported as a WSL/CI DECISAO with evidence, and every pass-through surfaced as RISCO/DECISAO.
- Open fix threads: R1 (detector-exception fail-open), R12 (SUS leading-digit range), D1 (timeout watchdog), D2 (input-size guard), D3 (EMAIL re2 migration), D4 (mutmut under WSL/CI + survivor-mutant tests).

---
*Phase: 10-test-hardening*
*Completed: 2026-07-09*

## Self-Check: PASSED

All three test files, `pyproject.toml`, and the SUMMARY exist on disk; all four task commits (cadcade, 12d8e3b, 2bea80d, d70c3c8) present in git history.
