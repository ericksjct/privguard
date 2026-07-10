---
phase: 11-fail-closed-hardening
plan: 01
subsystem: security-core
tags: [fail-closed, redos, input-size-guard, cns-validator, hooks, detection]

requires:
  - phase: 10-test-hardening
    provides: P1 fail-closed injection suite (R1), P3 ReDoS/size suite (D2/D3), P6 checksum edges (R12)
provides:
  - Fail-closed exception wrapper on both hook entry points (reason_code=detector_error, exit 2)
  - Hook-boundary input-size guard (MAX_INPUT_CHARS, reason_code=input_too_large)
  - Backtracking-safe EMAIL regex (atomic groups + RFC-5321 length bounds, linear scan)
  - CNS leading-digit range enforcement in valida_cartao_sus
affects: [detection-redos-fix-thread, evasion-hardening-thread]

tech-stack:
  added: []
  patterns:
    - "One shared fail-closed wrapper at both console-script entry points; catch Exception (not BaseException) so KeyboardInterrupt/SystemExit still propagate"
    - "Untrusted-input size cap enforced at the hook boundary only; detect() stays uncapped for the CLI scan/mask path"
    - "Atomic groups + RFC length bounds convert an O(n^2) find-anywhere regex to linear by making every failed word-boundary start O(1)"

key-files:
  created:
    - .planning/phases/11-fail-closed-hardening/11-01-SUMMARY.md
  modified:
    - privguard/hooks.py
    - privguard/detection.py
    - tests/test_fail_closed_injection.py
    - tests/test_redos_size_guard.py
    - tests/test_checksum_edges.py

key-decisions:
  - "MAX_INPUT_CHARS default = 1_000_000 (1 MB), env override PII_GUARD_MAX_INPUT_CHARS parsed defensively (fall back on ValueError / non-positive)"
  - "EMAIL quadratic was O(n) word-boundary start positions x O(n) scan-to-end, NOT internal backtracking; atomic groups alone did not fix it (3.5s -> 3.2s at 36k). RFC-5321 length bounds ({1,64} local, {1,63} label, {2,255} tail) make each failed start O(1) -> linear (72k ~24ms)"
  - "Size guard lives at the hook boundary only; detect() intentionally uncapped so the CLI scan/mask path still processes large files without truncation"
  - "CNS leading-digit guard runs before the checksum: accept 1,2 (definitive) and 7,8,9 (provisional); reject 0 and 3-6"

requirements-completed: [DET-07]

metrics:
  duration: 11min
  completed: 2026-07-10
  tasks: 5
  files_modified: 5

status: complete
---

# Phase 11 Plan 01: Fail-Closed Hardening (Security Core) Summary

**A crashing or overwhelmed detector now BLOCKS instead of leaking PII: fail-closed exception wrapper on both hooks (exit 2 / detector_error), a 1 MB hook-boundary input-size guard (input_too_large), a linear atomic+length-bounded EMAIL regex, and CNS leading-digit range enforcement — full suite green under the 84% coverage gate with the FP corpus rate held at 0.0.**

## What Changed

### Task 1 — R1 fail-closed exception wrapper (`hooks.py`)
Added `_run_fail_closed(impl, *, event)` and renamed the hook bodies to `_main_user_prompt_impl` / `_main_pre_tool_impl`; the public `main_user_prompt` / `main_pre_tool` (console-script entry points + `__init__` re-exports) now delegate through the wrapper. Any `Exception` is caught → `_audit_log(action="block", reason_code="detector_error")`, a fixed sanitized stderr line, and `return 2`. `BaseException` (KeyboardInterrupt/SystemExit) is deliberately **not** caught. Previously an exception escaped → interpreter exit 1 → non-blocking in Claude Code = fail-open.

### Task 2 — D2 input-size guard (`hooks.py`)
Added module constant `MAX_INPUT_CHARS = 1_000_000`, `_max_input_chars()` (env `PII_GUARD_MAX_INPUT_CHARS`, parsed defensively like `_inline_threshold`), and `_too_large(s)`. Guards fire **before** any regex scan on: the prompt (`_main_user_prompt_impl` → `deny("PII-GUARD", "input_too_large")`), each `_iter_text_values` value on LLM-orchestration tools, and the Bash/PowerShell command (`_deny_pre_tool(reason_code="input_too_large", ...)`). `detect()` itself is left uncapped so the CLI scan/mask path still handles large files.

### Task 3 — D3 backtracking-safe EMAIL regex (`detection.py`)
Replaced `\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b` with `\b(?>[\w.+-]{1,64})@(?>[\w-]{1,63})\.(?>[\w.-]{2,255})\b`. The plan's atomic-only form did not remove the quadratic (the cost is O(n) word-boundary start positions each scanning O(n) to end, not internal backtracking) — RFC-5321 length bounds cap each failed start to O(1), yielding linear scaling (72k hostile chars ~24 ms vs ~7 s at 52 k pre-fix). Canonical synthetic emails still match; no detection semantics widened.

### Task 4 — R12 CNS leading-digit range (`detection.py`)
`valida_cartao_sus` now rejects unassigned CNS leading digits before the checksum: `if cartao[0] not in "12789": return False`. Length(15) + weighted-sum % 11 checks unchanged.

### Task 5 — Full gate + reconciliation
Ran the full suite under `--cov-fail-under=84` and reconciled stale phase-10 pins (docstrings/headers) to the fixed behavior.

## Reason Codes / Constants Added

| Item | Value |
|------|-------|
| `reason_code=detector_error` | fail-closed on any detector `Exception` (both hooks, exit 2) |
| `reason_code=input_too_large` | oversized untrusted input at the hook boundary (exit 2) |
| `MAX_INPUT_CHARS` | `1_000_000` (1 MB); env override `PII_GUARD_MAX_INPUT_CHARS` |
| EMAIL regex | `\b(?>[\w.+-]{1,64})@(?>[\w-]{1,63})\.(?>[\w.-]{2,255})\b` |

## Phase-10 Tests Flipped

| Origin | Old pin | New assertion |
|--------|---------|---------------|
| R1 | `test_user_prompt_detector_exception_escapes_unhandled` (raises, exit 1) | `test_user_prompt_detector_exception_blocks_fail_closed` (exit 2, detector_error) + new `test_user_prompt_base_exception_not_swallowed` |
| R1 | `test_pre_tool_detector_exception_escapes_unhandled` | `test_pre_tool_detector_exception_blocks_fail_closed` (exit 2, detector_error) |
| D2 | `test_10mb_prompt_with_pii_blocks_without_crash` (reason=pii_detected) | `test_10mb_prompt_with_pii_blocks_on_size_guard` (reason=input_too_large) |
| D2 | `test_10mb_clean_prompt_currently_allowed_no_size_guard` (exit 0) | `test_10mb_clean_prompt_blocked_by_size_guard` (exit 2, input_too_large) |
| D3 | `test_email_bait_is_super_linear_documented_behavior` | `test_email_bait_scales_linearly_after_atomic_fix` (asserts linear, <4x on 2x input) |
| D3 | `test_email_bait_completes_under_generous_bound` (3s ceiling) | same test, tightened to 1s |
| D2/D3 | `test_oversized_input_has_no_size_guard_and_still_detects` | `test_detect_has_no_size_cap_for_the_cli_path` (comment reconciled: guard is at the hook, detect stays uncapped by design) |
| R12 | `test_sus_out_of_range_leading_digit_still_accepted` (3-6 accepted) | `test_sus_out_of_range_leading_digit_rejected` (3-6 rejected) |

## Verification

- `python -m pytest -q`: **327 passed, 1 skipped**, coverage **86.72%** (≥ `--cov-fail-under=84`). Baseline entering the plan was 326 passed / 1 skipped (net +1 from the added BaseException-propagation test).
- Detector exception → exit 2 on both hooks; oversized input → exit 2 `input_too_large`; EMAIL scan linear (72k ~24 ms); SUS range enforced.
- `tests/test_false_positive_corpus.py`: FP rate **0.0** (asserts `docs_with_hits == 0`) — unchanged. The EMAIL bounds and SUS range guard can only reduce matches, never add, so the corpus is unaffected.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] EMAIL atomic-group regex alone did not meet the linear must-have**
- **Found during:** Task 3
- **Issue:** The plan's suggested `\b(?>[\w.+-]+)@(?>[\w-]+)\.(?>[\w.-]{2,})\b` was still quadratic (measured 3.16 s at 36 k hostile chars vs 3.56 s for the old regex). The O(n^2) cost is the outer engine retrying O(n) valid `\b` start positions, each atomically scanning O(n) to end — atomic groups only forbid *internal* backtracking, which was never the bottleneck.
- **Fix:** Added RFC-5321 length bounds (`{1,64}` local, `{1,63}` domain label, `{2,255}` tail) so every failed start fails in O(1). Result is linear: 18k ~6 ms, 36k ~12 ms, 72k ~24 ms. Bounds are correctness-preserving (RFC max lengths); all canonical synthetic emails still match.
- **Files modified:** privguard/detection.py, tests/test_redos_size_guard.py
- **Commit:** 65ff0ef

## Task Commits

1. **Task 1: R1 fail-closed wrapper** — `80ff206` (fix)
2. **Task 2: D2 input-size guard** — `2c6ad16` (fix)
3. **Task 3: D3 EMAIL regex** — `65ff0ef` (fix)
4. **Task 4: R12 SUS range** — `a963179` (fix)
5. **Task 5: reconcile phase-10 pins** — `d343c06` (test)

## Known Stubs

None.

---
*Phase: 11-fail-closed-hardening*
*Completed: 2026-07-10*

## Self-Check: PASSED

SUMMARY.md + both source files present on disk; all five task commits (80ff206, 2c6ad16, 65ff0ef, a963179, d343c06) present in git history.
