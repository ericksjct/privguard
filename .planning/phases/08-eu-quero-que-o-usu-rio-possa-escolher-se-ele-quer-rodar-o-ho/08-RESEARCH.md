# Phase 8: Hook Mode Selector - Research

**Researched:** 2026-05-24
**Domain:** Claude Code hook output schema / PII_GUARD_MODE extension
**Confidence:** HIGH (critical path verified against installed binary)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Research step MUST check whether Claude hook API has a prompt-replacement field. If yes: true mask mode (replace + exit 0). If no: fallback is block + show masked version (exit 2). Option 1 (pass-through via additionalContext) is REJECTED — PII would still reach Claude, violating fail-closed.
- **D-02:** Mode toggle (PII_GUARD_MODE) applies to UserPromptSubmit AND PreToolUse LLM orchestration check only. Protected-path blocking in PreToolUse is always unconditional.
- **D-03:** Valid values after this phase: `block` (default), `warn` (unchanged), `mask` (new). `scrub` is removed — falls through to block behavior. No alias, no deprecation warning (planner may optionally emit one stderr notice).
- **D-04:** If verify_mask() returns verified=False in mask mode: exit 2 (block) with reason_code=mask_verification_failed. Never pass through an unverified mask.

### Claude's Discretion

- Exact stderr format for block+show fallback (how masked version is displayed).
- Whether to emit a one-line scrub fallback notice.
- Whether warn mode is touched at all (it predates this phase).
- Test coverage: which file to extend, how many cases, as long as synthetic-only rule is followed.

### Deferred Ideas (OUT OF SCOPE)

- `--mode` flag on console script entry points (v2 candidate).
- Mask mode for warn (warn + show masked version, still non-protective).
- Interactive resubmit after showing masked version.
- Codex mask mode.

</user_constraints>

---

## Summary

The single most important research question — whether the Claude Code `UserPromptSubmit` hook output supports a prompt-replacement field — has been answered with high confidence by inspecting the installed Claude Code binary (v2.1.150). The answer is **NO: there is no prompt-replacement field.** The `UserPromptSubmit` `hookSpecificOutput` schema supports only `additionalContext` (which appends to model context, not replaces the prompt), `sessionTitle`, and `suppressOriginalPrompt`. The existing comment at lines 206-208 of `hooks.py` is correct and still applies.

This means the D-01 fallback path is the only valid implementation: mask mode must be implemented as **block + show masked version** (exit 2, emit masked prompt to stderr so user can resend manually). The true-replacement path is architecturally unavailable in Claude Code v2.1.150.

The Phase 8 implementation is otherwise straightforward: add a `mask` branch to the existing `if mode == ...` chain in `main_user_prompt()`, add mode awareness to the `inline_pii` check in `main_pre_tool()`, remove the `scrub` branch, and write new tests. All required supporting functions (`mask_text`, `verify_mask`, `_audit_log`, `_prompt_diagnostic`) are already in place.

**Primary recommendation:** Implement mask mode as block + show masked version. The implementation is a targeted extension to two functions. No new modules, no schema changes to the hook wiring.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Mode dispatch (block/warn/mask) | Hook adapter (Python) | — | PII_GUARD_MODE is read at hook execution time; Claude Code has no mode awareness |
| Prompt masking (mask_text + verify_mask) | Package core (privguard.masking) | — | Already implemented, no changes expected |
| Masked-version display | Hook stderr output | — | Block exit (2) already writes to stderr; masked version appended to same channel |
| Audit logging | Hook adapter (_audit_log) | — | Fire-and-forget JSON line; new reason codes slot in naturally |
| LLM orchestration PII check | PreToolUse hook branch | — | inline_pii check at lines 303-312 needs mode awareness added |
| Protected-path blocking | PreToolUse hook branch | — | Mode-agnostic by decision D-02; always blocks |

---

## MANDATORY: D-01 Answer — Does UserPromptSubmit Support Prompt Replacement?

### Answer: NO

**Evidence source:** Claude Code binary v2.1.150 (`@anthropic-ai/claude-code@2.1.150`), extracted from `C:/Users/Erick/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe`. [VERIFIED: binary inspection]

### Verified UserPromptSubmit hookSpecificOutput Schema

From the Zod schema embedded in the binary:

```
h.object({
  hookEventName: h.literal("UserPromptSubmit"),
  additionalContext: h.string().optional(),
  sessionTitle: h.string().describe("Set the session title (same effect as /rename)").optional(),
  suppressOriginalPrompt: h.boolean().describe(
    'When decision is "block", omit the original prompt from the block message'
  ).optional()
})
```

Human-readable documentation string also found in binary:

```json
"for UserPromptSubmit": {
  "hookEventName": "\"UserPromptSubmit\"",
  "additionalContext": "string (required)"
}
```

### What Each Field Does

| Field | Type | Effect |
|-------|------|--------|
| `additionalContext` | string, optional | Appended to model context as `hook_additional_context`. Does NOT replace the original prompt. PII in original prompt still reaches Claude. |
| `sessionTitle` | string, optional | Renames the session (same as `/rename`). No impact on prompt content. |
| `suppressOriginalPrompt` | boolean, optional | When `decision` is `"block"`, omits the original prompt from the blocking message shown to the user. Does not affect what Claude receives. |

### Runtime confirmation from binary code

The `AN6` function (hook output processor) for `UserPromptSubmit` case:
```javascript
case "UserPromptSubmit":
  M.additionalContext = H.hookSpecificOutput.additionalContext;
  M.sessionTitle = H.hookSpecificOutput.sessionTitle;
  M.suppressOriginalPrompt = H.hookSpecificOutput.suppressOriginalPrompt;
  break;
```

There is no `updatedPrompt`, `replacedPrompt`, `transformedPrompt`, or any equivalent field. The `updatedInput` field that allows input replacement exists only for `PreToolUse`, not `UserPromptSubmit`.

### Comparison: PreToolUse vs UserPromptSubmit

| Capability | PreToolUse | UserPromptSubmit |
|-----------|-----------|-----------------|
| Input replacement | YES — `updatedInput: object` replaces tool_input | NO — no equivalent field |
| Context injection | YES — `additionalContext` | YES — `additionalContext` (appends only) |
| Decision control | YES — `permissionDecision: allow/deny/ask/defer` | Only via top-level `decision: approve/block` |

### Implication for Phase 8

The only valid mask mode implementation is **block + show masked version**:
1. Detect PII in prompt → run `mask_text()` → run `verify_mask()`
2. If verified: exit 2 (block), write masked version to stderr for user to resend manually
3. If not verified: exit 2 (block) with `reason_code=mask_verification_failed`

The "true mask + allow" path (replace original prompt, exit 0) is architecturally unavailable.

---

## Standard Stack

### Core (no new dependencies)

| Module | Version | Purpose | Status |
|--------|---------|---------|--------|
| `privguard.masking` | current | `mask_text()`, `verify_mask()`, `MaskResult` | Already implemented, no changes |
| `privguard.hooks` | current | `main_user_prompt()`, `main_pre_tool()`, `_audit_log()`, `_prompt_diagnostic()` | Extend with mask branch |
| `privguard.diagnostics` | current | `format_hit_summary()`, `summarize_hits()` | Reuse for masked-version display |
| `privguard.detection` | current | `detect()`, `Hit` | Used by mask_text internally |

No new package dependencies are required for Phase 8. [VERIFIED: codebase inspection]

---

## Architecture Patterns

### Data Flow Diagram

```
UserPromptSubmit JSON (stdin)
        |
        v
main_user_prompt()
        |
        +--> detect(prompt) → no hits → audit(allow, no_pii) → exit 0
        |
        +--> hits found
              |
              +--> mode == "warn" → print JSON additionalContext warning → exit 0
              |
              +--> mode == "scrub" → [REMOVED] → emit optional notice → fall to block
              |
              +--> mode == "mask" ─────────────────────────────────────────────────┐
              |                                                                     |
              |    mask_text(prompt, hits) → MaskResult                            |
              |         |                                                           |
              |    verify_mask() returns False?                                     |
              |         YES → audit(block, mask_verification_failed) → stderr → exit 2
              |         NO  → audit(block, pii_masked) → stderr BLOQUEADO + masked version → exit 2
              |                                                                     |
              +--> mode == "block" (default) → audit(block, pii_detected) → stderr → exit 2


PreToolUse JSON (stdin)
        |
        v
main_pre_tool()
        |
        +--> unknown tool → block (unconditional, mode-agnostic)
        |
        +--> LLM orchestration tool (Agent/Task/TaskCreate/TaskUpdate)
        |         |
        |         +--> inline_pii check
        |               |
        |               +--> mode == "mask" → mask_text() + verify_mask()
        |               |         verified → audit(mask_allowed) → exit 0 [allow masked payload]
        |               |         not verified → audit(mask_verification_failed) → exit 2
        |               +--> mode != "mask" → mode == "warn" → exit 0 (non-protective)
        |               +--> mode == "block" (default) → exit 2
        |
        +--> protected path tool → block (unconditional, mode-agnostic)
        |
        +--> Bash/PowerShell → classify_command() → block if protected (unconditional)
```

### Recommended Structure

No new files needed. All changes are in:

```
privguard/
├── hooks.py          # Add mask branch to main_user_prompt(); add mode to main_pre_tool() inline_pii
tests/
├── test_claude_hooks.py  # Extend with mask mode tests
```

### Pattern 1: Mask Branch in main_user_prompt()

```python
# After the existing warn branch, before the default block:
if mode == "mask":
    mask_result = mask_text(prompt, hits=hits)
    if not mask_result.verified:
        _audit_log(
            event="UserPromptSubmit",
            action="block",
            reason_code="mask_verification_failed",
        )
        sys.stderr.write(
            "[PII-GUARD BLOQUEADO] "
            + _prompt_diagnostic(action="block", reason_code="mask_verification_failed", hits=hits)
            + "\n"
        )
        return 2
    _audit_log(event="UserPromptSubmit", action="block", reason_code="pii_masked")
    sys.stderr.write(
        "[PII-GUARD BLOQUEADO] "
        + _prompt_diagnostic(action="block", reason_code="pii_masked", hits=hits)
        + "\n"
    )
    sys.stderr.write("[PII-GUARD VERSAO MASCARADA]\n")
    sys.stderr.write(mask_result.text + "\n")
    sys.stderr.write("[Reenvie o prompt acima com os valores mascarados]\n")
    return 2
```

### Pattern 2: scrub Branch Removal

```python
# Remove the scrub branch entirely.
# Optional: emit a one-line notice before falling to default block:
if mode == "scrub":
    sys.stderr.write("[PII-GUARD] scrub mode removido, usando block\n")
    # Fall through to default block behavior below
```

### Pattern 3: Mode-Aware inline_pii in main_pre_tool()

```python
# In the LLM orchestration branch (lines 303-312), add mode awareness:
if tool in _LLM_ORCHESTRATION_TOOLS:
    threshold = _inline_threshold()
    mode = os.environ.get("PII_GUARD_MODE", "block")
    for text in _iter_text_values(tool_input):
        hits = list(detect(text, min_score=threshold))
        if not hits:
            continue
        if mode == "warn":
            # Non-protective pass-through for local development
            break  # or continue — existing behavior
        if mode == "mask":
            mask_result = mask_text(text, hits=hits)
            if not mask_result.verified:
                return _deny_pre_tool(
                    reason_code="mask_verification_failed",
                    category="llm_orchestration",
                    command_count=1,
                )
            # verified mask — allow through (mask_text result not forwarded due to no updatedInput for Task)
            # updatedInput is PreToolUse-only; for LLM orchestration we can only block or allow
            # Allow means the original PII-containing text still goes through — same as warn
            # Therefore mask mode for LLM orchestration = BLOCK with mask shown (consistent with D-01)
            return _deny_pre_tool(
                reason_code="pii_masked",
                category="llm_orchestration",
                command_count=1,
            )
        # Default: block
        return _deny_pre_tool(
            reason_code="inline_pii",
            category="llm_orchestration",
            command_count=1,
        )
    return 0
```

**Important nuance for PreToolUse LLM orchestration mask mode:** Even though `PreToolUse` supports `updatedInput` for tool input replacement, the LLM orchestration path collects arbitrary text values from across the entire `tool_input` dict. There is no way to reconstruct a clean `tool_input` with only the masked text without knowing which exact field contained PII. For consistency and safety, mask mode in `inline_pii` should also **block** (not attempt true replacement), mirroring the UserPromptSubmit behavior. The planner should decide whether to show the masked text in the denial message.

### Anti-Patterns to Avoid

- **Passing masked text via additionalContext and exiting 0:** This sends both the original PII prompt AND the masked version to Claude, violating fail-closed. Explicitly rejected in D-01.
- **Using `scrub` alias:** The `scrub` mode comment at lines 206-208 explains why it was never safe. Remove it entirely.
- **Returning masked text via stdout JSON for UserPromptSubmit:** The `hookSpecificOutput.additionalContext` only appends to context; it does not replace the original prompt. The original prompt with PII is still submitted.
- **Assuming `updatedInput` is available for UserPromptSubmit:** It is not. Only `PreToolUse` supports `updatedInput`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PII detection | Custom regex masking | `mask_text()` in `privguard.masking` | Already handles overlap, normalization, verification |
| Mask verification | Re-running detect() manually | `verify_mask()` in `privguard.masking` | Checks both original value presence AND residual detection |
| Hit formatting | Custom diagnostic strings | `format_hit_summary()` + `summarize_hits()` | Already sanitized (no raw values), already tested |
| Audit entries | Custom JSON writing | `_audit_log()` in `privguard.hooks` | Fire-and-forget, never raises, correct format |

---

## Common Pitfalls

### Pitfall 1: additionalContext Confusion
**What goes wrong:** Developer assumes printing masked text to `hookSpecificOutput.additionalContext` + exit 0 constitutes safe masking.
**Why it happens:** The field name suggests it adds context "instead of" the original. It does not — the original prompt is ALSO submitted.
**How to avoid:** Exit 2 always when PII is detected in mask mode. The masked text is for the user to resend, not for Claude to receive.
**Warning signs:** Any code path that sets `additionalContext` to masked text and returns 0 in mask mode.

### Pitfall 2: verify_mask() Failure Silently Passing
**What goes wrong:** mask_text() returns verified=False but the code still emits the masked text and exits 0.
**Why it happens:** Forgetting the D-04 requirement that mask verification failure = exit 2.
**How to avoid:** Always check `mask_result.verified` before deciding exit code.
**Warning signs:** Any mask mode path that exits 0 without checking `mask_result.verified`.

### Pitfall 3: Masked Text Contains PII in stderr Output
**What goes wrong:** mask_result.text still contains PII (verify_mask returned False) but the code emits it to stderr anyway.
**Why it happens:** Emitting mask_result.text before checking verified status.
**How to avoid:** Only write `mask_result.text` to stderr if `mask_result.verified` is True.
**Warning signs:** Test that checks forbidden values in stderr output catches raw CPF in mask_verification_failed path.

### Pitfall 4: scrub Mode Test Still Passing
**What goes wrong:** The existing test `test_non_blocking_prompt_modes_are_labeled_non_protective_and_sanitized` is parametrized over `["warn", "scrub"]`. After scrub removal, this test needs updating.
**Why it happens:** Forgetting to update the test parametrize list.
**How to avoid:** Update parametrize to `["warn"]` only after removing the scrub branch.
**Warning signs:** Test passes for scrub but should either be removed or changed to assert scrub → block behavior.

### Pitfall 5: PreToolUse LLM orchestration mask mode allows PII through
**What goes wrong:** In mask mode, the inline_pii check finds hits, calls mask_text(), and then exits 0 because "it was masked." But the original PII-containing text in tool_input is what gets sent to Claude — there's no updatedInput mechanism for Task/Agent prompts.
**Why it happens:** Assuming PreToolUse updatedInput works for all tool types.
**How to avoid:** For LLM orchestration tools, mask mode should block (with optional masked-text display in the denial), same as for UserPromptSubmit.
**Warning signs:** Any code path in the LLM orchestration branch that exits 0 after masking.

---

## Code Examples

### MaskResult Contract (verified from masking.py)

```python
@dataclass(frozen=True)
class MaskResult:
    text: str                     # The masked version of the input
    changed: bool                 # True if any substitutions were made
    verified: bool                # True if verify_mask() passed
    verification_status: str      # "verified" or "failed"
    reason_codes: tuple[str, ...] # e.g., ("checksum_valid", "mask_verified")
    hits: tuple[Hit, ...]         # The hits that were masked
```

### verify_mask() Contract (verified from masking.py)

```python
# Returns: (verified: bool, reason_codes: tuple[str, ...])
# Returns False if:
#   - Any original hit value is still present in masked text
#   - Residual detection finds new PII in masked text (excluding safe placeholder assignments)
# Returns True with:
#   - ("no_sensitive_hits",) if no hits were passed
#   - ("mask_verified",) if all checks pass
```

### Existing _audit_log() signature (verified from hooks.py)

```python
def _audit_log(
    *,
    event: str,       # "UserPromptSubmit" or "PreToolUse"
    action: str,      # "block", "allow", "warn"
    reason_code: str, # e.g. "pii_detected", "mask_verification_failed", "pii_masked"
    category: str = "",
    log_path: "pathlib.Path | None" = None,
) -> None: ...
```

New reason codes to add:
- `pii_masked` — mask mode: mask verified, prompt blocked with masked version shown
- `mask_verification_failed` — mask mode: verify_mask returned False, prompt blocked

### Existing test infrastructure to extend (verified from test_claude_hooks.py)

```python
def run_user_prompt(
    monkeypatch: pytest.MonkeyPatch,
    payload: object | str,
    *,
    mode: str | None = None,
) -> int: ...
# mode=None deletes PII_GUARD_MODE (uses default "block")
# mode="mask" sets PII_GUARD_MODE=mask
```

---

## Existing Hook Mode Dispatch — Current State

From `hooks.py` `main_user_prompt()` (lines 194-228):

```
mode = os.environ.get("PII_GUARD_MODE", "block")

if mode == "warn":      → audit warn, print JSON additionalContext, exit 0
if mode == "scrub":     → audit block scrub_unsupported, stderr, exit 2  [TO REMOVE]
# default block:        → audit block pii_detected, stderr, exit 2
```

The `scrub` comment at lines 206-208 states:
> "scrub cannot replace the original prompt via additionalContext (it only appends, leaking clear-text). Treat scrub as block until Claude exposes a documented prompt-replacement mechanism."

This research confirms: that mechanism still does not exist in v2.1.150. Scrub removal is clean.

---

## PreToolUse LLM Orchestration Path — Current State

From `hooks.py` `main_pre_tool()` (lines 303-312):

```python
if tool in _LLM_ORCHESTRATION_TOOLS:
    threshold = _inline_threshold()
    for text in _iter_text_values(tool_input):
        if detect(text, min_score=threshold):
            return _deny_pre_tool(
                reason_code="inline_pii",
                category="llm_orchestration",
                command_count=1,
            )
    return 0
```

Currently mode-agnostic (always blocks). D-02 requires adding mode awareness here: mask mode should attempt mask+verify but still block (no true replacement available for Task/Agent inputs). Warn mode may pass through (existing behavior for non-protective local development).

---

## Test Coverage Gaps

### Existing test coverage (verified from test_claude_hooks.py)

| Test | Modes covered | Status |
|------|--------------|--------|
| `test_user_prompt_blocks_synthetic_cpf_by_default` | block (default) | Passes |
| `test_non_blocking_prompt_modes_are_labeled_non_protective_and_sanitized` | warn, scrub | Needs update: scrub → removed |
| `test_pre_tool_blocks_llm_orchestration_payload_pii_without_echo` | block (default) | Passes |

### New tests needed for mask mode

| Test | What to assert |
|------|---------------|
| `test_user_prompt_mask_mode_blocks_and_shows_masked_version` | exit 2, stderr contains "VERSAO MASCARADA" or equivalent, masked text present, no raw PII in output |
| `test_user_prompt_mask_mode_verification_failure_blocks_without_masked_text` | exit 2, reason=mask_verification_failed, no raw PII in output, no unverified mask emitted |
| `test_user_prompt_mask_mode_clean_prompt_allows` | exit 0, no output (no PII detected, mask mode irrelevant) |
| `test_pre_tool_mask_mode_llm_orchestration_blocks_and_shows_reason` | exit 2, category=llm_orchestration, reason=pii_masked or mask_verification_failed |
| `test_non_blocking_prompt_modes_updated` | parametrize over ["warn"] only after scrub removal |

### Phase gate test (test_claude_phase_gate.py)
This file uses `monkeypatch.delenv("PII_GUARD_MODE", raising=False)` which exercises default block mode. No changes needed unless the planner adds a mask mode gate test.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|-----------------|--------------|--------|
| `scrub` mode as notional mask path | Removed; was always block | This phase | Clean removal, no alias needed |
| Block-only enforcement | Block + warn (non-protective) + mask (block+show) | This phase | Three explicit modes with clear contracts |
| `additionalContext` prompt injection considered for masking | Confirmed architecturally impossible for replacement | Phase 3 comment + Phase 8 research | Block+show is the only safe path |

**Deprecated:**
- `scrub` mode: was never a real masking path (Phase 3 comment at lines 206-208 documents why). Removal is the correct action.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | For PreToolUse LLM orchestration tools, mask mode should block (not allow) even after a verified mask, because there is no mechanism to forward the masked text to the Task/Agent tool input. [ASSUMED] | PreToolUse LLM orchestration path | If PreToolUse updatedInput works for all tool types (not just file tools), a true replacement path might be possible for inline_pii. However, given the text is extracted by `_iter_text_values()` across arbitrary nested fields, reassembly is not straightforward. Planner should verify. |

**All other claims in this research are VERIFIED or CITED from the installed binary or codebase.**

---

## Open Questions

1. **Does mask mode for inline_pii (PreToolUse LLM orchestration) show the masked text in the denial message?**
   - What we know: The denial goes through `_deny_pre_tool()` which writes to stderr with reason/category/count only.
   - What's unclear: D-02 says apply mode toggle to inline_pii check; it does not specify whether to show masked version in the denial.
   - Recommendation: Planner decides. Consistent with UserPromptSubmit behavior would be to show the masked version, but the denial format is different. Simplest safe default: just block with `reason=pii_masked` and no masked text shown (user can resend after removing PII from Agent/Task invocation manually).

2. **Should scrub→block fallback emit a stderr notice?**
   - What we know: D-03 says "planner may choose to emit one-line stderr notice."
   - What's unclear: Whether backward-compat notice is worth the extra code path.
   - Recommendation: Emit it. One line: `[PII-GUARD] modo scrub removido, usando block`. Low cost, helps users who had `PII_GUARD_MODE=scrub` configured.

---

## Environment Availability

Step 2.6: SKIPPED — Phase 8 is a pure code change to `privguard/hooks.py` and `tests/test_claude_hooks.py`. No external tools, services, or runtimes beyond the existing Python environment are required.

---

## Sources

### Primary (HIGH confidence)
- `C:/Users/Erick/AppData/Roaming/npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe` (v2.1.150) — binary inspection via Python `re.findall` string extraction. Verified: Zod schema for UserPromptSubmit hookSpecificOutput, AN6 function processing logic, full hook output field documentation string.
- `privguard/hooks.py` — verified: scrub comment lines 206-208, mode dispatch structure, `_audit_log` signature, `_prompt_diagnostic` signature, `inline_pii` check lines 303-312.
- `privguard/masking.py` — verified: `MaskResult` dataclass, `mask_text()` signature, `verify_mask()` contract and return values.
- `tests/test_claude_hooks.py` — verified: existing mode test coverage, `run_user_prompt` helper, forbidden output lists.

### Secondary (MEDIUM confidence)
- `.planning/phases/03-claude-enforcement/03-VERIFICATION.md` — evidence that scrub was blocked in Phase 3 due to lack of proven safe rewrite mechanism; this research confirms the mechanism still does not exist.

---

## Metadata

**Confidence breakdown:**
- D-01 answer (no prompt-replacement): HIGH — verified from installed binary Zod schema and runtime processing code
- Standard stack / no new deps: HIGH — verified from hooks.py and masking.py
- Architecture patterns: HIGH — derived directly from verified code
- Test gaps: HIGH — verified from test_claude_hooks.py content
- PreToolUse LLM orchestration mask semantics: MEDIUM — one ASSUMED claim about updatedInput scope

**Research date:** 2026-05-24
**Valid until:** 2026-08-24 (stable — Claude Code hook schema changes infrequently; re-verify if upgrading beyond v2.1.150)
