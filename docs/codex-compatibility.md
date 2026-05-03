# Codex Compatibility

**Assessment date:** 2026-05-03
**Local Codex CLI:** codex-cli 0.128.0
**npm package:** @openai/codex 0.128.0 (modified 2026-05-01)
**Official docs evidence:** OpenAI Codex hooks docs checked 2026-05-03

---

## Assessment Summary

OpenAI Codex CLI (`codex-cli 0.128.0`) provides feature-flagged hooks that allow
blocking on certain prompt and tool-use surfaces. However, **automatic Codex masking
is unsupported until verified outbound payload replacement is proven**.

Current evidence supports conservative `experimental block-only` labels for prompt
and selected tool-use hook events. No surface has been labeled `rewrite-capable` or
`automatic masking` because:

1. Official Codex hook documentation does not describe a supported mechanism for
   replacing the outbound prompt or tool payload before provider submission.
2. The `updatedInput` and related rewrite fields are documented as reserved or
   unsupported in the cited hook events.
3. No synthetic end-to-end test has proven that the outbound payload equals
   `mask_text(payload).text` before any external provider submission.

All privguard privacy standards from Phase 2 (fail-closed policy, verified masking,
sanitized diagnostics) and Phase 3 (block not rewrite for unproven surfaces) apply
to Codex surfaces without relaxation.

---

## Evidence Standard

A positive Codex support claim requires all three:

1. **Official/current documentation** from `https://developers.openai.com/codex/hooks`
   confirming the hook event and its fields.
2. **Local installed-Codex evidence** — version observed via `codex --version`.
3. **Synthetic end-to-end proof** — a pytest test proving the specific surface
   intercepts a synthetic payload before any external provider submission.

Documentation-only or repository-issue-only signals are not sufficient for a
positive supported masking claim (D-02).

If a surface cannot prove pre-provider payload replacement, the correct label is
`block-only` or `experimental block-only`, not `automatic masking` (D-05).

---

## Compatibility Matrix

The machine-readable source of truth is `privguard/codex.py` (`CODEX_COMPATIBILITY`).
Every row below mirrors a `CodexCompatibilityRow` from that module.

| Surface | Support label | SurfaceCapability | Evidence | Privacy action | Remaining gaps |
|---------|---------------|-------------------|----------|----------------|----------------|
| UserPromptSubmit prompt | experimental block-only | block-only | OpenAI Codex hooks docs 2026-05-03; local codex-cli 0.128.0 | block_sensitive_prompt_when_hook_observed | no verified outbound payload rewrite; no no-provider synthetic interception proof recorded |
| PreToolUse Bash | experimental block-only | block-only | OpenAI Codex hooks docs 2026-05-03; local codex-cli 0.128.0 | block_protected_path_or_inline_pii_in_bash_command | incomplete shell coverage for newer unified_exec path; no verified outbound payload rewrite; Windows shell behavior not confirmed |
| PreToolUse apply_patch/Edit/Write | experimental block-only | block-only | OpenAI Codex hooks docs 2026-05-03; local codex-cli 0.128.0 | block_protected_path_edit_when_event_payload_exposes_path | payload shape for file contents not confirmed via local fixture; no verified outbound payload rewrite; apply_patch alias coverage not locally verified |
| PreToolUse MCP tool call | experimental block-only | block-only | OpenAI Codex hooks docs 2026-05-03; local codex-cli 0.128.0 | block_known_payload_schemas_or_conservative_string_scan | MCP schemas vary by server; false-negative risk for opaque args; no verified outbound payload rewrite |
| PermissionRequest | observe-only | observe-only | OpenAI Codex hooks docs 2026-05-03; local codex-cli 0.128.0 | secondary_deny_signal_not_primary_privacy_boundary | commands not requiring approval bypass this event; cannot substitute for PreToolUse as primary privacy boundary |
| PostToolUse | observe-only | observe-only | OpenAI Codex hooks docs 2026-05-03; local codex-cli 0.128.0 | observe_only_cannot_undo_prior_tool_side_effects | cannot protect data already exfiltrated by prior tool execution; not a pre-exfiltration control |
| WebSearch and non-shell/non-MCP tools | unsupported | unsupported | OpenAI Codex hooks docs 2026-05-03: incomplete non-shell/non-MCP coverage documented; local codex-cli 0.128.0 | do_not_claim_protection_unsupported_surface | no hook interception documented for WebSearch or other non-shell/non-MCP paths; requires future official support before any privacy protection label upgrade |
| Automatic Codex masking rewrite | unsupported | unsupported | OpenAI Codex hooks docs 2026-05-03: updatedInput and rewrite fields reserved/unsupported; local codex-cli 0.128.0 | do_not_claim_masking | requires proof outbound payload equals verified masked payload before provider submission; no synthetic E2E test proves payload == mask_text(payload).text pre-submission |

---

## Unsupported Automatic Masking

**automatic Codex masking is unsupported until verified outbound payload replacement is proven.**

This statement is a hard constraint on all privguard documentation, CLI help text, and
package metadata. No file in this repository may claim that Codex automatically masks
prompts or tool payloads unless:

- A `CodexCompatibilityRow` with `automatic_masking=True` exists in `CODEX_COMPATIBILITY`, AND
- A pytest test proves that the outbound payload equals `mask_text(payload).text` before
  any external provider submission for that specific surface.

Currently no such row or test exists. All Codex surfaces in Phase 04 are labeled
`block-only`, `observe-only`, or `unsupported` — never `rewrite-capable`.

---

## Remaining Gaps

The following gaps apply across all current Codex surfaces:

1. **No synthetic end-to-end interception proof.** No pytest test has exercised a
   Codex hook in a fully offline/synthetic mode without authenticated model execution
   or external provider submission. Until such a test exists, block-capable surfaces
   remain `experimental block-only` rather than proven `block-only`.

2. **No outbound payload rewrite proof.** No Codex surface currently provides a
   documented or tested mechanism to replace the outbound prompt or tool payload
   before provider submission. This gap prevents any `rewrite-capable` or automatic
   masking label.

3. **Incomplete shell tool coverage.** Official Codex docs note incomplete shell
   interception for the newer `unified_exec` path. `PreToolUse Bash` cannot be
   claimed as universal shell protection.

4. **Variable MCP payload schemas.** MCP tool call payloads vary by server. A
   conservative string scan may miss PII in opaque or server-specific arg shapes.

5. **Windows behavior unverified.** Local probing on Windows for shell hook behavior
   has not been confirmed. Linux/macOS behavior is assumed from docs.

6. **`apply_patch` alias coverage unverified.** Whether Codex consistently maps
   `Edit` and `Write` tool names to `apply_patch` in hook payloads has not been
   verified via a local fixture.

### Upgrade path

A surface can be upgraded from `experimental block-only` to `block-only` after:
- A no-provider synthetic interception test passes for that surface.

A surface can be upgraded to `rewrite-capable` only after:
- Outbound payload replacement is proven AND
- A synthetic E2E test confirms `outbound_payload == mask_text(original).text`.

---

*Machine-readable source: `privguard/codex.py` (`CODEX_COMPATIBILITY`)*
*Requirements: CDX-01, CDX-02, CDX-03 in `.planning/REQUIREMENTS.md`*
*Phase context: `.planning/phases/04-codex-compatibility-evidence/04-CONTEXT.md`*
