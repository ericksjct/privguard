# Phase 3: Claude Enforcement - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers production Claude Code hook enforcement using the Phase 2 privacy core.
Claude prompts, tool calls, shell commands, and hook outputs must fail closed when sensitive
data, protected paths, risky exfiltration patterns, or unsafe diagnostics are detected.

The phase does not prove Codex support and does not add broad v2 integrations. Codex
compatibility evidence is Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Prompt Hook Behavior
- **D-01:** Claude `UserPromptSubmit` must block sensitive prompts by default when safe prompt
  rewrite is unavailable. The phase should not rely on `warn` or `scrub` as protective modes
  for external-provider use because they do not prove that Claude receives only the masked
  payload.
- **D-02:** If experimental warning or suggested-redaction behavior remains for local development,
  it must be clearly labeled non-protective and must not be the default Claude enforcement path.

### Tool Command Strictness
- **D-03:** Claude `PreToolUse` enforcement should be strict. It must deny protected-path
  references across read, search, edit, write, copy, archive, encode/decode, clipboard, and
  network-style command patterns when those commands could expose protected data.
- **D-04:** Protected path handling must stay path/classification based. The implementation must
  not read `.env`, dumps, credentials, or `data_sensivel/**` contents to validate blocking.

### Claude Validation Experience
- **D-05:** Add a safe Claude validation diagnostic, such as `privguard claude doctor`, that checks
  hook wiring, effective policy, environment/config expectations, and synthetic payload behavior.
- **D-06:** The validation flow must use only synthetic fixtures and must emit an audit-visible
  signal that the exercised payloads are synthetic. This marker should be present in structured
  diagnostics or test/audit output so reviewers can distinguish validation data from real
  protected data.
- **D-07:** Validation must not read protected files. It can verify that protected path strings are
  blocked by using synthetic paths such as `.env`, `data_sensivel/synthetic.csv`, and synthetic
  dump or credential filenames.

### Hook Output Contract
- **D-08:** Hook output should be developer-friendly but sanitized: include reason codes,
  detection categories, counts, offsets, policy action, and concise remediation hints.
- **D-09:** Hook stdout, stderr, and JSON responses must never include raw matched values, original
  prompt snippets, protected file contents, secret-looking strings, or redacted prompt text that
  could still resemble sensitive input.

### the agent's Discretion
- The planner may choose the exact CLI command shape and JSON schema for Claude diagnostics.
- The planner may decide whether to remove unsafe modes entirely or keep them behind explicit
  local-development labels, as long as default Claude protection blocks sensitive prompts.
- The planner may decide exact shell-pattern coverage and normalization helpers, provided the
  strict command categories above are covered by synthetic tests.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/REQUIREMENTS.md` - CLD-01 through CLD-05 define the Claude acceptance criteria.
- `.planning/ROADMAP.md` - Phase 3 goal and success criteria.
- `.planning/PROJECT.md` - Core privacy boundary, fail-closed default, and Claude-first
  integration direction.
- `.planning/STATE.md` - Recent decisions and blockers affecting Claude prompt rewrite safety.

### Prior phase decisions
- `.planning/phases/01-package-foundation/01-CONTEXT.md` - Locks package identity, flat
  `privguard/` layout, and thin Claude hook adapter direction.
- `.planning/phases/02-privacy-core/02-CONTEXT.md` - Locks fail-closed policy, irreversible
  masking, surface capability labels, and sanitized diagnostics.

### Existing implementation
- `privguard/hooks.py` - Current package-backed Claude hook handlers and known unsafe output
  surfaces to harden.
- `privguard/policy.py` - Protected path classification, surface capability labels, policy
  decisions, and command regexes.
- `privguard/detection.py` - Brazil-first detection contract and synthetic-sensitive entity types.
- `privguard/masking.py` - Irreversible masking and verification behavior.
- `privguard/diagnostics.py` - Sanitized hit summaries and diagnostic serialization helpers.
- `privguard/cli.py` - Existing CLI entry point where Claude diagnostics can be added.
- `hooks/pii_guard.py` - Thin `UserPromptSubmit` adapter that should remain compatible with
  Claude Code hook wiring.
- `hooks/pre_tool_guard.py` - Thin `PreToolUse` adapter that should remain compatible with
  Claude Code hook wiring.
- `.claude/settings.json` - Current Claude Code permissions and hook command wiring.

### Tests
- `tests/test_detection.py` - Synthetic detection fixture patterns.
- `tests/test_masking.py` - Masking verification expectations.
- `tests/test_policy.py` - Policy and protected path behavior.
- `tests/test_cli.py` - CLI behavior and sanitized output expectations.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `privguard.hooks.main_user_prompt()` and `main_pre_tool()` already centralize Claude hook
  behavior behind package code.
- `privguard.policy.classify_path()` and `is_sensitive_path()` already classify protected paths
  without reading file contents.
- `privguard.policy.decide_policy()` already models fail-closed behavior and surface capability
  labels that Phase 3 should apply to Claude surfaces.
- `privguard.diagnostics.format_hit_summary()` and `summarize_hits()` provide sanitized entity
  summaries suitable for hook output.

### Established Patterns
- Hook adapters under `hooks/` should remain stable file paths for `.claude/settings.json`.
- Runtime hook logic should stay dependency-light and fast.
- Diagnostics expose types, counts, offsets, scores, and reason codes rather than `Hit.value`.
- Tests and validation data must be synthetic-only.

### Integration Points
- `UserPromptSubmit` routes through `hooks/pii_guard.py` into `privguard.hooks.main_user_prompt()`.
- `PreToolUse` routes through `hooks/pre_tool_guard.py` into `privguard.hooks.main_pre_tool()`.
- `.claude/settings.json` currently matches `Read|Bash|Grep|Glob|Edit|Write`; Phase 3 planning
  should verify whether additional Claude tool names or PowerShell command payloads need coverage.
- CLI diagnostics should integrate through `privguard.cli:main` and the existing `privguard`
  console script.

</code_context>

<specifics>
## Specific Ideas

- User explicitly chose blocking sensitive prompts by default.
- User explicitly chose strict tool-command blocking.
- User wants a Claude validation diagnostic, but with an audit mechanism that signals validation
  payloads are synthetic.
- User chose developer-friendly sanitized hook messages instead of ultra-terse or JSON-only output.

</specifics>

<deferred>
## Deferred Ideas

- Codex interception and rewrite claims remain Phase 4.
- Additional IDE agents, LangChain, LlamaIndex, local proxy, and enterprise policy distribution
  remain v2 work.

</deferred>

---

*Phase: 03-claude-enforcement*
*Context gathered: 2026-05-03*
