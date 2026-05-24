# Phase 8: Hook Mode Selector - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-24
**Phase:** 08-hook-mode-selector
**Areas discussed:** What masking mode actually does, Scope, Mode config, Failure behavior

---

## What masking mode actually does

| Option | Description | Selected |
|--------|-------------|----------|
| Non-protective convenience mode | Exit 0 (allow). Inject masked version via additionalContext. PII still reaches Claude — non-protective. Clearly labeled. | |
| Block + show masked version | Exit 2 (block). Emit masked prompt to stderr so user can see safe version and manually resend. Protective. | |
| Promote scrub to true mask (research first) | Research whether Claude Code added a prompt-replacement field. If yes, implement true replacement. If no, use option 2 as fallback. | ✓ |

**User's choice:** Option 3 — research first, with explicit condition: if research confirms no true replacement, fallback is option 2 (block+show), NOT option 1 (pass-through with PII still present).

**Notes:** User explained the rationale clearly — option 1 is "warn-and-pass" under a different name (already rejected for violating fail-closed). Option 2 is "block-with-help" (still block). Option 3 is the only path that can deliver the literal promise of "mask without block". If the hook API gained a replacement field, that's the right answer. Deserves a research step before deciding.

---

## Scope: which surfaces get a mode toggle

| Option | Description | Selected |
|--------|-------------|----------|
| Prompt only (UserPromptSubmit) | Mode toggle only affects UserPromptSubmit. PreToolUse always blocks. | |
| Prompt + LLM orchestration inputs | Mode toggle affects UserPromptSubmit AND inline_pii check on Agent/Task inputs. Protected path blocking always blocks. | ✓ |
| Prompt + all PreToolUse PII checks | Broadest coverage — affects UserPromptSubmit AND all PII-related PreToolUse checks. | |

**User's choice:** Prompt + LLM orchestration inputs.

**Notes:** Protected path blocking in PreToolUse is always unconditional — mixing path security semantics with PII masking semantics would be risky.

---

## Mode config mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Extend PII_GUARD_MODE with 'mask'; deprecate scrub | Add mask value. Remove scrub. warn stays. Clean, minimal. | ✓ |
| Extend PII_GUARD_MODE with 'mask'; keep scrub as alias | Add mask, keep scrub as deprecated alias mapping to mask. | |
| New env var PII_GUARD_HOOK_MODE | Separate var for hook behavior. Clean separation but two vars to document. | |

**User's choice:** Extend PII_GUARD_MODE with 'mask'; deprecate (remove) scrub.

**Notes:** scrub was always treated as block — it was a broken promise from the start. Removing it is clean. warn stays as-is.

---

## Failure behavior in mask mode

| Option | Description | Selected |
|--------|-------------|----------|
| Fail closed — block anyway | If verify_mask fails, exit 2 (block) regardless of mode. | |
| Warn and pass — emit verification failure but allow | Exit 0, include verification failure in diagnostics. (User noted this contradicts the mode intent.) | |
| Block and explain — same as fail-closed but with explicit reason code | Exit 2 (block) with reason_code=mask_verification_failed in diagnostics and audit log. | ✓ |

**User's choice:** Block and explain — explicit mask_verification_failed reason code.

**Notes:** Practically identical to pure fail-closed, but the specific reason code makes audit logs more readable when verification failures occur.

---

## Claude's Discretion

- Exact stderr format for block+show fallback (how to display the masked version)
- Whether to emit a one-line notice when scrub mode is set (scrub removed → default block)
- Whether warn mode output is changed at all
- Test coverage: which files to extend and number of new test cases

## Deferred Ideas

- `--mode` flag on console script entry points (per-hook CLI flag vs global env var)
- "warn + show masked version" variant of warn mode
- Interactive resubmit flow after showing masked version
- Codex mask mode (deferred until Phase 4 evidence extended)
