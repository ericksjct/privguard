# Phase 8: Hook Mode Selector - Context

**Gathered:** 2026-05-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 lets users choose how the Claude Code hook responds when PII is detected in a
prompt: block entirely (current default) or mask the PII and allow the sanitized prompt
through — if the Claude hook API supports true prompt replacement.

The phase delivers:
1. A `mask` mode for `PII_GUARD_MODE` — true prompt replacement when the hook API supports
   it, or block + show-masked-version as a protective fallback.
2. Removal of the broken `scrub` mode (was always treated as block; this formalizes that).
3. The mode toggle applies to `UserPromptSubmit` and to the LLM orchestration PII check in
   `PreToolUse` (Agent/Task inputs).

The phase does **not**:
- Change `warn` mode (still non-protective pass-through, clearly labeled).
- Change protected-path blocking in `PreToolUse` (always blocks regardless of mode).
- Add a UI or dashboard for mode selection — the env var is the configuration surface.
- Change CLI masking behavior (`privguard mask` command is unaffected).

</domain>

<decisions>
## Implementation Decisions

### Masking Mode Semantics (what "mask without block" means)

- **D-01:** The research step MUST check whether the Claude hook API has added a
  prompt-replacement field (e.g. `transformedPrompt` or equivalent) since Phase 3.
  - **If replacement IS supported:** implement true mask mode — replace original prompt with
    the masked version, exit 0 (allow). Delivers "mask without block" while preserving
    fail-closed posture (PII never reaches Claude).
  - **If replacement is NOT supported:** fallback is **block + show masked version**
    (exit 2, block, but emit the masked prompt to stderr so the user can see a safe version
    and resend manually). This is option 2, NOT option 1.
  - **Option 1 (pass-through with `additionalContext` containing masked version) is explicitly
    rejected** — it is "warn-and-pass" under a different name, PII still reaches Claude,
    which violates fail-closed. This was already rejected for `scrub` in Phase 3.

### Surface Scope

- **D-02:** The mode toggle (`PII_GUARD_MODE`) applies to:
  - `UserPromptSubmit` (prompt PII detection → mask or block based on mode)
  - `PreToolUse` LLM orchestration check only — specifically the `inline_pii` detection on
    `Agent`/`Task`/`TaskCreate`/`TaskUpdate` tool inputs
  - **Protected path blocking in `PreToolUse` is NOT affected by the mode** — unknown tools,
    protected path reads/writes, glob/grep patterns, and risky Bash commands always block
    regardless of `PII_GUARD_MODE`.

### Mode Configuration

- **D-03:** Extend `PII_GUARD_MODE` env var with a `mask` value. Valid values after this phase:
  - `block` (default) — block when PII detected; behavior unchanged
  - `warn` — non-protective pass-through with `additionalContext` warning; behavior unchanged;
    clearly labeled `mode_scope=local_development_non_protective`
  - `mask` — true prompt replacement if hook API supports it; else block + show masked version
  - **`scrub` is removed** — it was always treated as block (the rewrite mechanism was never
    proven safe per Phase 3). No alias, no deprecation warning. If someone has
    `PII_GUARD_MODE=scrub` set, they will fall through to the default `block` behavior (or
    the planner may choose to emit a one-line stderr notice: "scrub mode removed, using block").

### Masking Failure Behavior

- **D-04:** If `mask_text()` runs and `verify_mask()` returns `verified=False` (PII still
  present in the masked output), the hook must **exit 2 (block)** with
  `reason_code=mask_verification_failed`. This applies in both mask mode outcomes (true
  replacement and block+show fallback). Never pass through an unverified mask. Consistent
  with Phase 2 masking verification contract and Phase 3 fail-closed posture.
  The `mask_verification_failed` reason code must appear in stderr diagnostics and in the
  `audit.log` entry (via `_audit_log`).

### Claude's Discretion

- **Exact stderr format for block+show fallback** — the planner chooses how to display the
  masked version (e.g. after the reason code line, or as a separate `[PII-GUARD MASKED VERSION]`
  block). Must be sanitized: no raw PII in output.
- **`scrub` fallback notice** — whether to emit a one-line stderr notice when `scrub` is set
  is at the planner's discretion. Must not show raw PII.
- **Whether `warn` mode is affected** — `warn` mode predates this phase and is already
  non-protective. The planner may leave it entirely untouched.
- **Test coverage for new `mask` mode paths** — the planner decides which test file to extend
  and how many new test cases to add, as long as the Phase 5 synthetic-only rule is followed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 8 scope sources
- `.planning/ROADMAP.md` §"Phase 8" — phase goal.
- `.planning/PROJECT.md` — Core value (no PII to external providers in clear text),
  fail-closed safety default, Brazil-first locale priority, synthetic-fixtures-only rule.
- `.planning/REQUIREMENTS.md` — Any requirements that apply to hook behavior.

### Locked prior decisions (carry forward, do not revisit)
- `.planning/phases/03-claude-enforcement/03-CONTEXT.md` — D-01 (block by default when safe
  rewrite unavailable), D-02 (non-protective modes must be clearly labeled), D-08/D-09
  (sanitized hook output — no raw matched values, no original prompt snippets in output).
- `.planning/phases/02-privacy-core/02-CONTEXT.md` — masking verification contract (must
  verify before trusting masked output), fail-closed policy.
- `.planning/phases/01-package-foundation/01-CONTEXT.md` — canonical name `privguard`,
  package-first code organization.

### Key implementation files (read before planning)
- `privguard/hooks.py` — `main_user_prompt()` (mode dispatch at line 194), `main_pre_tool()`
  (LLM orchestration PII check at line 303), `_prompt_diagnostic()`, `_audit_log()`.
- `privguard/masking.py` — `mask_text()`, `verify_mask()`, `MaskResult` — already tested,
  no changes expected.
- `privguard/detection.py` — `detect()`, `Hit` — used by mask_text internally.
- `privguard/diagnostics.py` — `format_hit_summary()`, `summarize_hits()` — used in hook output.
- `tests/test_hooks.py` (if it exists) — existing hook test coverage to extend.
- `.claude/settings.json` — hook wiring; check if mode can be passed as an arg to the
  console script, which would be an alternative to env var only.

### Phase 3 verification (for hook API behavior evidence)
- `.planning/phases/03-claude-enforcement/03-VERIFICATION.md` — What was verified about the
  Claude hook output contract; what scrub mode failed on.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`mask_text()` + `verify_mask()` in `privguard/masking.py`** — already implemented,
  tested, and used by CLI commands. Phase 8 hooks into this without changing it.
- **`_inline_threshold()` in `privguard/hooks.py`** — shared threshold helper; reusable
  for the mask path.
- **`_audit_log()` in `privguard/hooks.py`** — fire-and-forget audit; already has `action`
  and `reason_code` fields. The new `mask_verification_failed` reason code slots in naturally.
- **`_prompt_diagnostic()` in `privguard/hooks.py`** — formats the hook stderr line; can be
  extended or reused for the block+show masked output format.
- **`format_hit_summary()` + `summarize_hits()` in `privguard/diagnostics.py`** — sanitized
  hit output; reusable for masked-version diagnostics.

### Established Patterns
- **`PII_GUARD_MODE` env var dispatch** — already in `main_user_prompt()` at line 194.
  Mode handling is a simple `if mode == ...` chain. Add `mask` as a new branch.
- **Exit code 2 = block, exit 0 = allow** — Claude Code hook convention; never change this.
- **Sanitized diagnostics** — reason codes, counts, offsets only; never raw hit values,
  never original prompt snippets.
- **`mode_scope=local_development_non_protective`** — label pattern for warn mode; any
  future non-protective mode must carry this label.
- **Synthetic-only tests** — all test fixtures must use fake Brazilian IDs, fake secrets.

### Integration Points
- `main_user_prompt()` — add `mask` branch after the existing `warn` branch; remove or
  handle `scrub` branch.
- `main_pre_tool()` — add mode awareness to the `inline_pii` check (lines 303-312); the
  `unknown_tool`, `protected_path`, and Bash `classify_command` branches stay mode-agnostic.
- `_audit_log()` — new `reason_code` values: `mask_allowed` (if true replacement succeeds),
  `mask_verification_failed` (if verify_mask fails in mask mode).
- Console scripts in `pyproject.toml` — if the hook command supports `--mode` as an arg
  (rather than only env var), the planner must update the script definitions.

</code_context>

<specifics>
## Specific Ideas

- **D-01 research gate:** The planner/researcher MUST verify whether the Claude Code
  `UserPromptSubmit` hook output schema has a prompt-replacement field before choosing the
  mask mode implementation path. Check the Claude Code hooks documentation and/or the hook
  JSON schema. This is the deciding factor between true mask mode and block+show fallback.
- **`scrub` removal note:** `scrub` was never documented as the correct masking path — the
  Phase 3 comment at line 206-208 in hooks.py already explains why it falls back to block.
  Removal is clean. If backward compatibility matters, the planner may emit one stderr line
  when `scrub` is detected: `[PII-GUARD] scrub mode removed, defaulting to block`.
- **Block+show masked version format (fallback):** Something like:
  ```
  [PII-GUARD BLOQUEADO] reason=pii_detected action=block event=UserPromptSubmit ...
  [PII-GUARD VERSÃO MASCARADA] <CPF> trabalhou em <NOME_COMPLETO> desde 2023
  Reenvie o prompt acima com os valores mascarados.
  ```
  Exact format is planner discretion, but must never include the original raw values.
- **Audit log for mask success:** On successful mask+allow (if true replacement is
  supported), audit entry should record `action=mask_allowed` with `reason_code=pii_masked`
  or `reason_code=mask_verified` — the planner picks the clearest name.

</specifics>

<deferred>
## Deferred Ideas

- **`--mode` flag on console script entry points** — allowing `PII_GUARD_MODE` to be set
  per-hook-line in `.claude/settings.json` (`"command": "privguard-user-prompt --mode mask"`)
  instead of as a global env var. Useful for per-project configuration but adds CLI parsing
  complexity. Candidate for v2.
- **Mask mode for `warn`** — a "warn + show masked version" variant that is still
  non-protective but more informative than the current warn output. Not requested; deferred.
- **Interactive resubmit** — a Claude Code hook that, after showing the masked version,
  prompts the user to confirm resubmission. Requires richer hook interactivity than v1
  Claude Code supports today.
- **Codex mask mode** — applying the same mode toggle to Codex surfaces. Deferred until
  Phase 4 interception and rewrite evidence is extended.

</deferred>

---

*Phase: 08-eu-quero-que-o-usu-rio-possa-escolher-se-ele-quer-rodar-o-ho*
*Context gathered: 2026-05-24*
