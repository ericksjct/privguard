# Phase 3: Claude Enforcement - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-03
**Phase:** 03-Claude Enforcement
**Areas discussed:** Prompt hook behavior, Tool command strictness, Claude validation experience, Hook output contract

---

## Prompt Hook Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Block only by default | Block sensitive Claude prompts until real prompt rewrite is proven. | yes |
| Keep warn for local experimentation | Warn may remain only as non-protective local behavior. | |
| Keep scrub as suggested redaction | Suggested redaction is unsafe unless original payload replacement is proven. | |

**User's choice:** Block.
**Notes:** The assistant explained that warning or suggested masking may still allow the original
prompt to reach Claude. User selected blocking as the default.

---

## Tool Command Strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Strict shell blocking | Deny protected-path references across read, search, copy, archive, encode, clipboard, and network-style commands. | yes |
| Moderate blocking | Focus on read, search, and network exfiltration. | |
| Minimal blocking | Keep current categories and improve sanitization/tests only. | |

**User's choice:** 2A - strict shell blocking.
**Notes:** Downstream planning should broaden bypass-oriented synthetic tests without reading
protected files.

---

## Claude Validation Experience

| Option | Description | Selected |
|--------|-------------|----------|
| Safe CLI doctor | Add a `privguard claude doctor` style diagnostic using synthetic payload behavior. | yes |
| Manual commands only | Keep validation as documented shell commands. | |
| CLI diagnostic plus setup docs | Add both CLI diagnostic and generated setup docs. | |

**User's choice:** 3A, with an added audit requirement.
**Notes:** User requested a mechanism for audit output to signal that validation payloads are
synthetic data. This becomes a planning requirement: diagnostics and audit/test output should make
the synthetic nature of validation data explicit.

---

## Hook Output Contract

| Option | Description | Selected |
|--------|-------------|----------|
| Very terse | Only reason codes, entity counts/types, offsets, and exit code guidance. | |
| Developer-friendly sanitized output | Include sanitized remediation hints without raw snippets or redacted prompt text. | yes |
| Structured-first | Prefer JSON diagnostics everywhere possible. | |

**User's choice:** 4B - developer-friendly sanitized output.
**Notes:** Messages can help the developer understand what to do, but must not include raw matched
values, prompt snippets, protected contents, secret-looking substrings, or redacted prompt text.

---

## the agent's Discretion

- Exact CLI command shape and JSON diagnostic schema.
- Whether unsafe hook modes are removed or retained under explicit local-development labels.
- Exact shell-pattern coverage details, as long as strict command categories are tested.

## Deferred Ideas

- Codex compatibility evidence remains Phase 4.
- Broader IDE-agent and framework integrations remain v2.
