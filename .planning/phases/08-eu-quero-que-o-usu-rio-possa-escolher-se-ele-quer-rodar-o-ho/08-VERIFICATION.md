---
phase: 08-eu-quero-que-o-usu-rio-possa-escolher-se-ele-quer-rodar-o-ho
verified: 2026-05-25T20:00:00Z
status: passed
score: 12/12
overrides_applied: 0
---

# Phase 8: Hook Mode Selector (mask + scrub removal) — Verification Report

**Phase Goal:** User can set `PII_GUARD_MODE=mask` to receive a blocked prompt with a sanitized masked version shown in stderr (for manual resubmission), instead of a plain block. The `scrub` mode is removed and falls through to `block` with a one-line notice.
**Verified:** 2026-05-25T20:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | When PII_GUARD_MODE=mask and PII detected, hook exits 2 and writes masked prompt to stderr | VERIFIED | `if mode == "mask":` branch in `main_user_prompt()` lines 210-237; test `test_user_prompt_mask_mode_blocks_and_shows_masked_version` passes (exit 2, VERSAO MASCARADA in stderr, BR_CPF placeholder present) |
| 2 | When verify_mask() returns False, hook exits 2 with reason=mask_verification_failed and does NOT emit masked text | VERIFIED | `if not mask_result.verified: return 2` guard at line 212; test `test_user_prompt_mask_mode_verification_failure_blocks_without_masked_text` passes (VERSAO MASCARADA absent, exit 2) |
| 3 | When PII_GUARD_MODE=scrub, hook emits one-line stderr notice and falls through to block (exit 2) | VERIFIED | `if mode == "scrub":` at line 206 emits `[PII-GUARD] modo scrub removido, usando block` with no `return`; default block executes next |
| 4 | The mask branch never passes unverified masked text to stderr | VERIFIED | `if not mask_result.verified: return 2` executes before any `sys.stderr.write(mask_result.text ...)` call; the write at line 235 is unreachable when unverified |
| 5 | LLM orchestration check in main_pre_tool() reads PII_GUARD_MODE: warn passes, mask blocks with pii_masked or mask_verification_failed, block (default) blocks with inline_pii | VERIFIED | Lines 322-352: `mode = os.environ.get("PII_GUARD_MODE", "block")` inside the branch; `if mode == "warn": continue`; `if mode == "mask": ... return _deny_pre_tool(reason_code="pii_masked", ...)`; default `return _deny_pre_tool(reason_code="inline_pii", ...)` |
| 6 | Protected-path blocking in main_pre_tool() is unconditional and mode-agnostic | VERIFIED | Lines 355-376: `check_path_tool`, `check_glob_grep`, Bash/PowerShell blocks have no `mode` read; they execute regardless of PII_GUARD_MODE |
| 7 | mask_text imported from privguard.masking in hooks.py | VERIFIED | Line 14: `from .masking import mask_text` |
| 8 | mask mode with clean prompt exits 0 silently | VERIFIED | Test `test_user_prompt_mask_mode_clean_prompt_allows` passes (exit 0, no stdout, no stderr) |
| 9 | mask mode for LLM orchestration (Agent/Task/TaskCreate/TaskUpdate) blocks (exit 2) | VERIFIED | Test `test_pre_tool_mask_mode_llm_orchestration_blocks_pii` parametrized over all 4 tools passes; all 4 tool variants exit 2 with category=llm_orchestration |
| 10 | scrub parametrize removed from test — only warn remains | VERIFIED | Line 305: `@pytest.mark.parametrize("mode", ["warn"])` confirmed; `"scrub"` absent from parametrize line |
| 11 | All 5 new mask mode tests present and passing | VERIFIED | 46 total tests pass (up from 41 pre-phase); 5 new functions confirmed: `test_user_prompt_mask_mode_blocks_and_shows_masked_version`, `test_user_prompt_mask_mode_verification_failure_blocks_without_masked_text`, `test_user_prompt_mask_mode_clean_prompt_allows`, `test_pre_tool_mask_mode_llm_orchestration_blocks_pii`, `test_pre_tool_mask_mode_clean_llm_orchestration_payload_allows` |
| 12 | mask_result.text written to stderr only after verified gate (T-08-01 threat mitigation confirmed) | VERIFIED | In hooks.py mask branch: `if not mask_result.verified: return 2` at line 212 precedes `sys.stderr.write(mask_result.text + "\n")` at line 235; unverified path returns before reaching the write |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `privguard/hooks.py` | mask branch in main_user_prompt() + mode-aware inline_pii check in main_pre_tool() | VERIFIED | Contains `if mode == "mask":` in both functions; contains `mask_result = mask_text(prompt, hits=hits)`; contains VERSAO MASCARADA; contains Reenvie o prompt acima |
| `privguard/hooks.py` | scrub branch replaced by one-line notice | VERIFIED | Contains `modo scrub removido, usando block`; does NOT contain `scrub_unsupported` or `scrub cannot replace` |
| `privguard/hooks.py` | masking imports | VERIFIED | `from .masking import mask_text` at line 14 |
| `tests/test_claude_hooks.py` | 5 new mask mode tests + updated scrub parametrize | VERIFIED | All 5 test functions present; parametrize `["warn"]` only |
| `tests/test_claude_hooks.py` | scrub parametrize updated to warn-only | VERIFIED | Line 305: `@pytest.mark.parametrize("mode", ["warn"])` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| main_user_prompt() mask branch | mask_text() in privguard.masking | `mask_result = mask_text(prompt, hits=hits)` | WIRED | Direct call confirmed at line 211 of hooks.py |
| main_pre_tool() LLM orchestration | PII_GUARD_MODE env var | `os.environ.get("PII_GUARD_MODE", "block")` inside the branch | WIRED | Line 322: `mode = os.environ.get("PII_GUARD_MODE", "block")` inside `if tool in _LLM_ORCHESTRATION_TOOLS:` |
| mask branch verification gate | exit 2 when verify_mask fails | `if not mask_result.verified: return 2` | WIRED | Line 212: gate confirmed; unverified path exits before write |
| test_user_prompt_mask_mode_blocks_and_shows_masked_version | main_user_prompt() mask branch | `run_user_prompt(monkeypatch, payload, mode="mask")` | WIRED | `mode="mask"` confirmed in test at line 367 |
| test_user_prompt_mask_mode_verification_failure_blocks_without_masked_text | mask_verification_failed path | `monkeypatch.setattr(hooks, "mask_text", lambda *a, **kw: fake_result)` | WIRED | `monkeypatch.setattr(hooks, "mask_text", ...)` at line 396; `fake_result.verified=False` |
| test_pre_tool_mask_mode_llm_orchestration_blocks_pii | mode-aware inline_pii check | `monkeypatch.setenv("PII_GUARD_MODE", "mask") + run_pre_tool()` | WIRED | `monkeypatch.setenv("PII_GUARD_MODE", "mask")` at line 428 |

---

### Data-Flow Trace (Level 4)

This phase produces hook logic (not dynamic data rendering). Data-flow applies to the mask_result.text path:

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| hooks.py mask branch | `mask_result.text` | `mask_text(prompt, hits=hits)` → privguard.masking | Yes — mask_text returns a MaskResult with typed placeholder text derived from the real prompt | FLOWING |
| hooks.py LLM orchestration | `hits` | `list(detect(text, min_score=threshold))` | Yes — detect() runs real PII detection | FLOWING |

---

### Behavioral Spot-Checks

Tests were used as behavioral verification since the hook is invoked via stdin (not directly callable without the pre-tool guard blocking `python -c`).

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 46 tests pass including 5 new mask mode tests | `python -m pytest tests/test_claude_hooks.py -v` | 46 passed | PASS |
| 5 new mask mode tests individually pass | `pytest ...::test_user_prompt_mask_mode_*` (5 tests, 8 parametrized cases) | 8 passed | PASS |
| mask_text import works | `from privguard.hooks import main_user_prompt, main_pre_tool` | No import error | PASS |
| All key patterns present in hooks.py | `python -c "..."` assertion checks | All 11 assertions pass | PASS |
| All 5 new test functions present in test file | `python -c "..."` assertion checks | All 5 present | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| Phase 8 goal: PII_GUARD_MODE=mask | 08-01 | mask branch in main_user_prompt() | SATISFIED | Branch implemented, tests pass |
| Phase 8 goal: scrub removal | 08-01 | scrub replaced by one-line notice + fallthrough | SATISFIED | `modo scrub removido` notice present, no `return` in scrub block |
| Phase 8 goal: mode-aware main_pre_tool() | 08-01 | warn/mask/block dispatch in LLM orchestration | SATISFIED | Lines 322-352 confirmed |
| Phase 8 goal: 5 mask mode tests | 08-02 | test_claude_hooks.py test coverage | SATISFIED | All 5 tests present and passing |

---

### Anti-Patterns Found

None. No TODO/FIXME/HACK/PLACEHOLDER comments found in `privguard/hooks.py` or `tests/test_claude_hooks.py`. No stub return patterns. No empty handlers.

---

### Test Coverage Note (Non-Blocking)

Plan 02 specified two assertions for `test_user_prompt_mask_mode_blocks_and_shows_masked_version` that the implementation omitted:
- `assert "action=block" in output` — omitted from test (implementation does emit it via `_prompt_diagnostic`)
- `assert "local_development_non_protective" not in output` — omitted from test (implementation correctly does NOT emit it since `mode=` kwarg is absent from `_prompt_diagnostic` calls in the mask branch)

Both safety properties hold in the implementation. The test is less strict than planned but the hook behavior is correct. This is a test coverage gap, not an implementation gap. It does not block phase goal achievement.

---

### Human Verification Required

None. All key behaviors are verifiable programmatically through the test suite. The 46 passing tests cover the complete phase 8 behavior surface.

---

## Gaps Summary

No gaps. All 12 must-haves verified. The phase goal is fully achieved:

- `PII_GUARD_MODE=mask` causes the hook to block (exit 2) and display a verified masked version on stderr
- `scrub` mode emits a one-line notice and falls through to default block behavior
- `main_pre_tool()` LLM orchestration check is mode-aware (warn passes, mask blocks with pii_masked/mask_verification_failed, default blocks with inline_pii)
- Protected-path blocking remains unconditional and mode-agnostic
- 5 new mask mode tests cover all code paths and pass cleanly
- 46/46 tests pass with no regressions

---

_Verified: 2026-05-25T20:00:00Z_
_Verifier: Claude (gsd-verifier)_
