---
phase: 08-eu-quero-que-o-usu-rio-possa-escolher-se-ele-quer-rodar-o-ho
plan: 01
subsystem: hooks
tags: [python, pii, masking, claude-code, hooks, privguard]

# Dependency graph
requires:
  - phase: 02-privacy-core
    provides: mask_text(), verify_mask(), MaskResult — masking primitives used in new hook branches
  - phase: 03-claude-enforcement
    provides: hooks.py structure, _audit_log, _prompt_diagnostic, _deny_pre_tool, existing mode dispatch

provides:
  - mask branch in main_user_prompt(): block + show masked version (exit 2) when PII_GUARD_MODE=mask
  - mask branch in main_pre_tool() LLM orchestration: mode-aware inline_pii check (warn/mask/block)
  - scrub notice that falls through to default block (replaces old scrub_unsupported error block)
  - Four new pytest tests covering mask mode paths

affects: [08-02, phase-09, any future hook surface extension]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "mask mode = block + show masked version (exit 2); no pass-through path for PII"
    - "verified gate before any write of mask_result.text to stderr"
    - "mode dispatch chain: warn → mask → default block (scrub falls through to default)"
    - "mode-aware LLM orchestration: warn continues, mask blocks, block blocks"

key-files:
  created: []
  modified:
    - privguard/hooks.py
    - tests/test_claude_hooks.py

key-decisions:
  - "mask mode always exits 2 (block) — no exit 0 path when PII found; true replacement unavailable in Claude Code v2.1.150"
  - "scrub branch replaced by one-line notice that falls through to default block (no return in scrub branch)"
  - "_prompt_diagnostic called without mode= kwarg in mask branch — mode_scope=local_development_non_protective must not appear on protective paths"
  - "Non-PII text legitimately appears in mask_result.text (masked version shown to user); only RAW_CPF must be absent"
  - "mask mode in LLM orchestration (main_pre_tool) also blocks — no updatedInput available for Agent/Task tools"

patterns-established:
  - "Pattern mask-verified-gate: if not mask_result.verified: return 2 — always check before writing mask_result.text to stderr"
  - "Pattern mode-aware-pre-tool: read PII_GUARD_MODE inside LLM orchestration branch; protected-path branches remain mode-agnostic"

requirements-completed: []

# Metrics
duration: 18min
completed: 2026-05-26
---

# Phase 08 Plan 01: Hook Mode Selector — mask branch + mode-aware pre_tool Summary

**mask mode added to hooks.py: UserPromptSubmit blocks with verified masked version on stderr (exit 2); PreToolUse LLM orchestration dispatch extended with warn/mask/block; scrub branch replaced by one-line notice**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-26T01:47:29Z
- **Completed:** 2026-05-26T02:05:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `from .masking import mask_text` import to hooks.py
- Replaced old multi-line `scrub` block with a one-line stderr notice (`[PII-GUARD] modo scrub removido, usando block`) that falls through to default block — no `return`, no `scrub_unsupported` reason code
- Added `mask` branch in `main_user_prompt()`: calls `mask_text(prompt, hits=hits)`, checks `mask_result.verified`, blocks with `reason_code=pii_masked` (verified) or `reason_code=mask_verification_failed` (unverified); only writes masked text to stderr after verification gate
- Added mode-aware `inline_pii` check in `main_pre_tool()`: reads `PII_GUARD_MODE`, `warn` continues, `mask` calls `mask_text()`/blocks with `pii_masked` or `mask_verification_failed`, default blocks with `inline_pii`; protected-path and Bash branches unchanged
- Updated `test_non_blocking_prompt_modes_are_labeled_non_protective_and_sanitized` parametrize from `["warn", "scrub"]` to `["warn"]`
- Added 4 new pytest tests: mask success, mask verification failure, clean prompt in mask mode, pre_tool mask mode (parametrized over 4 LLM orchestration tools)
- All 45 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add mask import and mask branch to main_user_prompt()** - `6e70628` (feat)
2. **Task 2: Add mode-aware inline_pii check in main_pre_tool() + mask mode tests** - `1f42959` (feat)

## Files Created/Modified

- `privguard/hooks.py` — added mask_text import, scrub notice fallthrough, mask branch in main_user_prompt(), mode-aware LLM orchestration block in main_pre_tool()
- `tests/test_claude_hooks.py` — removed scrub from parametrize, added 4 new mask mode tests

## Decisions Made

- mask mode always exits 2: the Claude Code v2.1.150 hook schema has no prompt-replacement field for UserPromptSubmit (`additionalContext` only appends, never replaces). D-01 fallback is the only valid path.
- _prompt_diagnostic called without `mode=` kwarg in mask branch — the kwarg adds `mode_scope=local_development_non_protective` which is only correct for warn (non-protective) paths; mask is protective.
- Non-PII surrounding text legitimately appears in `mask_result.text` shown to user — only `RAW_CPF` must be absent from output.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Overly strict PROMPT_SNIPPET assertion in mask success test**
- **Found during:** Task 2 (new mask mode tests)
- **Issue:** The test asserted `PROMPT_SNIPPET not in output` for the mask success case, but `mask_result.text` (the masked version shown to the user) legitimately contains the non-PII surrounding text — "analise o cadastro" is not PII and will appear in the masked output.
- **Fix:** Removed the `PROMPT_SNIPPET not in output` assertion; added a clarifying comment explaining that non-PII text is intentional in the masked version. The invariant `RAW_CPF not in output` is sufficient to prove no PII leaks.
- **Files modified:** tests/test_claude_hooks.py
- **Verification:** 45 tests pass; no raw CPF appears in mask mode output
- **Committed in:** 1f42959 (Task 2 commit)

**2. [Rule 1 - Bug] scrub parametrize removal (Pitfall 4 from PATTERNS.md)**
- **Found during:** Task 2 (running existing tests after scrub removal)
- **Issue:** `test_non_blocking_prompt_modes_are_labeled_non_protective_and_sanitized` was parametrized over `["warn", "scrub"]`; after scrub branch removal, the scrub test case failed because it no longer emits `local_development_non_protective`.
- **Fix:** Updated parametrize to `["warn"]` only, as specified in PATTERNS.md Pitfall 4.
- **Files modified:** tests/test_claude_hooks.py
- **Verification:** 45 tests pass
- **Committed in:** 1f42959 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 — both pre-documented in PATTERNS.md as expected pitfalls)
**Impact on plan:** Both fixes were anticipated in PATTERNS.md. No scope creep.

## Issues Encountered

None beyond the two expected pitfalls documented in PATTERNS.md.

## User Setup Required

None - no external service configuration required. Set `PII_GUARD_MODE=mask` in environment to activate mask mode.

## Next Phase Readiness

- Plan 08-01 complete: hooks.py has mask branch in both main_user_prompt() and main_pre_tool()
- Ready for 08-02 (if it exists — test coverage extension or CLI documentation)
- All 45 existing tests pass; 4 new mask mode tests added

---
*Phase: 08-eu-quero-que-o-usu-rio-possa-escolher-se-ele-quer-rodar-o-ho*
*Completed: 2026-05-26*
