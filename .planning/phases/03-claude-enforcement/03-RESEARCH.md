# Phase 03: Claude Enforcement - Research

**Researched:** 2026-05-03 [VERIFIED: local date]
**Domain:** Claude Code hook enforcement, local privacy policy, synthetic diagnostics [VERIFIED: .planning/ROADMAP.md]
**Confidence:** HIGH for repository state and Claude hook mechanics; MEDIUM for future Claude Code tool-name coverage because Claude Code can add tool events over time. [VERIFIED: repo inspection] [CITED: https://code.claude.com/docs/en/hooks]

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
Phase 3 delivers production Claude Code hook enforcement using the Phase 2 privacy core.
Claude prompts, tool calls, shell commands, and hook outputs must fail closed when sensitive
data, protected paths, risky exfiltration patterns, or unsafe diagnostics are detected.

The phase does not prove Codex support and does not add broad v2 integrations. Codex
compatibility evidence is Phase 4.

- **D-01:** Claude `UserPromptSubmit` must block sensitive prompts by default when safe prompt
  rewrite is unavailable. The phase should not rely on `warn` or `scrub` as protective modes
  for external-provider use because they do not prove that Claude receives only the masked
  payload.
- **D-02:** If experimental warning or suggested-redaction behavior remains for local development,
  it must be clearly labeled non-protective and must not be the default Claude enforcement path.
- **D-03:** Claude `PreToolUse` enforcement should be strict. It must deny protected-path
  references across read, search, edit, write, copy, archive, encode/decode, clipboard, and
  network-style command patterns when those commands could expose protected data.
- **D-04:** Protected path handling must stay path/classification based. The implementation must
  not read `.env`, dumps, credentials, or `data_sensivel/**` contents to validate blocking.
- **D-05:** Add a safe Claude validation diagnostic, such as `privguard claude doctor`, that checks
  hook wiring, effective policy, environment/config expectations, and synthetic payload behavior.
- **D-06:** The validation flow must use only synthetic fixtures and must emit an audit-visible
  signal that the exercised payloads are synthetic. This marker should be present in structured
  diagnostics or test/audit output so reviewers can distinguish validation data from real
  protected data.
- **D-07:** Validation must not read protected files. It can verify that protected path strings are
  blocked by using synthetic paths such as `.env`, `data_sensivel/synthetic.csv`, and synthetic
  dump or credential filenames.
- **D-08:** Hook output should be developer-friendly but sanitized: include reason codes,
  detection categories, counts, offsets, policy action, and concise remediation hints.
- **D-09:** Hook stdout, stderr, and JSON responses must never include raw matched values, original
  prompt snippets, protected file contents, secret-looking strings, or redacted prompt text that
  could still resemble sensitive input.

### Claude's Discretion
- The planner may choose the exact CLI command shape and JSON schema for Claude diagnostics.
- The planner may decide whether to remove unsafe modes entirely or keep them behind explicit
  local-development labels, as long as default Claude protection blocks sensitive prompts.
- The planner may decide exact shell-pattern coverage and normalization helpers, provided the
  strict command categories above are covered by synthetic tests.

### Deferred Ideas (OUT OF SCOPE)
- Codex interception and rewrite claims remain Phase 4.
- Additional IDE agents, LangChain, LlamaIndex, local proxy, and enterprise policy distribution
  remain v2 work.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CLD-01 | Claude Code `UserPromptSubmit` integration blocks sensitive prompts when safe rewrite is unavailable. [VERIFIED: .planning/REQUIREMENTS.md] | Use `privguard.hooks.main_user_prompt()` as the entry point, default to block-only, and remove prompt-derived output. [VERIFIED: privguard/hooks.py] |
| CLD-02 | Claude Code `PreToolUse` integration blocks reads, searches, edits, writes, and shell commands that reference protected paths. [VERIFIED: .planning/REQUIREMENTS.md] | Reuse `classify_path()` and expand `main_pre_tool()` coverage to `MultiEdit`, notebook tools, and broad matcher coverage. [VERIFIED: privguard/policy.py] [CITED: https://code.claude.com/docs/en/hooks] |
| CLD-03 | Claude Code `PreToolUse` blocks command exfiltration patterns involving protected paths, network tools, archive tools, encoding tools, or clipboard commands. [VERIFIED: .planning/REQUIREMENTS.md] | Expand command classification beyond current read/network regexes to archive, encoding, copy, clipboard, and PowerShell aliases. [VERIFIED: privguard/hooks.py] |
| CLD-04 | Claude hook outputs never include raw matched values, original prompt snippets, protected file contents, or secret-looking substrings. [VERIFIED: .planning/REQUIREMENTS.md] | Current prompt hook emits `redacted=...`; Phase 3 must replace this with metadata-only diagnostics. [VERIFIED: privguard/hooks.py] |
| CLD-05 | Developer can validate Claude hook installation and effective policy without reading protected files. [VERIFIED: .planning/REQUIREMENTS.md] | Add `privguard claude doctor` using synthetic prompt and path strings only, plus an explicit synthetic audit marker. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md] |
</phase_requirements>

## Summary

Phase 3 should harden the existing package-backed Claude adapters, not replace them. `hooks/pii_guard.py` and `hooks/pre_tool_guard.py` are already thin adapters into `privguard.hooks`, `.claude/settings.json` already wires `UserPromptSubmit` and `PreToolUse`, and Phase 2 core modules already provide detection, protected-path classification, masking verification, policy decisions, and sanitized serializers. [VERIFIED: hooks/pii_guard.py] [VERIFIED: hooks/pre_tool_guard.py] [VERIFIED: .claude/settings.json] [VERIFIED: privguard/detection.py] [VERIFIED: privguard/policy.py] [VERIFIED: privguard/diagnostics.py]

The highest-risk implementation issue is output hygiene. Current `main_user_prompt()` includes `redacted={redacted}` in warning, scrub, and blocking output, which violates the Phase 3 lock that hook output must not include redacted prompt text. [VERIFIED: privguard/hooks.py] The second major risk is command coverage: current shell blocking checks read commands plus network commands, but Phase 3 explicitly requires copy, archive, encode/decode, clipboard, and broader exfiltration patterns. [VERIFIED: privguard/hooks.py] [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]

**Primary recommendation:** Keep the hook files as stable adapters, move all enforcement contracts into `privguard.hooks`/`privguard.policy`, emit metadata-only structured denial messages, and add `privguard claude doctor` plus synthetic hook tests before broadening command coverage. [VERIFIED: repo inspection]

## Project Constraints (from AGENTS.md)

- Raw sensitive data must stay local and must not be sent to external LLM providers. [VERIFIED: AGENTS.md]
- Brazilian sensitive data types are first-class for v1. [VERIFIED: AGENTS.md]
- v1 uses masking/blocking before submission, not deanonymization after response. [VERIFIED: AGENTS.md]
- If a client surface cannot be safely rewritten, block rather than silently allow clear text. [VERIFIED: AGENTS.md]
- Real sensitive datasets and `.env` values must not be read into planning docs, tests, examples, or commits. [VERIFIED: AGENTS.md]
- Current stack is Python, Microsoft Presidio optional extras, spaCy optional models, and lightweight hook scripts. [VERIFIED: AGENTS.md] [VERIFIED: pyproject.toml]
- GSD workflow says repo edits should happen through GSD entry points; this research file is a planning artifact for that workflow. [VERIFIED: AGENTS.md]
- `CLAUDE.md` does not exist in the repository, so there are no additional `CLAUDE.md` directives to enforce. [VERIFIED: local file check]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Prompt PII blocking | Local hook adapter / package runtime | Claude Code hook lifecycle | The submitted prompt enters through `UserPromptSubmit`; the local package must decide and block before Claude processes it. [VERIFIED: privguard/hooks.py] [CITED: https://code.claude.com/docs/en/hooks] |
| Protected file access blocking | Local hook adapter / package runtime | Claude Code permissions | `PreToolUse` receives tool name and input before execution; protected paths must be classified without file I/O. [VERIFIED: privguard/policy.py] [CITED: https://code.claude.com/docs/en/hooks] |
| Shell exfiltration blocking | Local hook adapter / policy module | Windows/PowerShell command parsing | Bash/PowerShell tool input is a command string; policy must classify risky command categories before execution. [VERIFIED: privguard/hooks.py] |
| Sanitized hook diagnostics | Package diagnostics layer | Hook stdout/stderr contract | `privguard.diagnostics` already strips `Hit.value` and `MaskResult.text`; hook output should use these serializers. [VERIFIED: privguard/diagnostics.py] |
| Claude doctor validation | CLI / package runtime | `.claude/settings.json` inspection | The CLI can inspect hook config and run synthetic hook payloads without reading protected files. [VERIFIED: privguard/cli.py] [VERIFIED: .claude/settings.json] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.14.3 installed, project requires `>=3.10` | Runtime for package, hooks, CLI, and tests | Existing package and hook code are Python and the installed interpreter runs the current tests. [VERIFIED: `python --version`] [VERIFIED: pyproject.toml] |
| privguard | 0.1.0 editable | Local package containing detection, masking, policy, diagnostics, CLI, and hook handlers | Phase 1/2 moved reusable behavior into importable modules; hook adapters already import it. [VERIFIED: `python -m pip show privguard`] [VERIFIED: hooks/pii_guard.py] |
| pytest | 9.0.2 installed; latest observed 9.0.3 | Automated synthetic regression tests | Existing tests are pytest tests and `python -m pytest tests` passes. [VERIFIED: `python -m pytest --version`] [VERIFIED: `python -m pytest tests`] |
| Claude Code | 2.1.126 installed | Hook host for `UserPromptSubmit` and `PreToolUse` | Phase 3 is Claude-specific and local `claude --version` is available. [VERIFIED: `claude --version`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| presidio-analyzer | 2.2.359 latest observed | Optional full PII analysis extra | Do not add as Phase 3 runtime dependency; hook path should remain lightweight. [VERIFIED: `pip index versions presidio-analyzer`] [VERIFIED: pyproject.toml] |
| presidio-anonymizer | 2.2.362 latest observed | Optional anonymization extra | Keep optional; Phase 3 blocks Claude surfaces rather than attempting safe prompt rewrite. [VERIFIED: `pip index versions presidio-anonymizer`] [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md] |
| spaCy | 3.8.13 latest observed | Optional NLP backend for full detection | Not needed for Phase 3 hook enforcement; default install has no dependencies. [VERIFIED: `pip index versions spacy`] [VERIFIED: pyproject.toml] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Exit code `2` denials | JSON `hookSpecificOutput.permissionDecision="deny"` | JSON gives richer structure for `PreToolUse`; exit code `2` is already working and official docs state it blocks `PreToolUse` and `UserPromptSubmit`. Plan can use either, but output must stay sanitized. [CITED: https://code.claude.com/docs/en/hooks] [VERIFIED: privguard/hooks.py] |
| `PreToolUse` matcher list | Matcher `"*"` | `"*"` catches current and future tools but may invoke the hook more often; official docs support omitted/`*` match-all semantics. [CITED: https://code.claude.com/docs/en/hooks] |
| Keeping `warn`/`scrub` | Remove non-blocking modes | Keeping them requires explicit non-protective labels and strict default; removing them reduces misuse risk. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md] |

**Installation:** no new runtime package should be added for Phase 3. [VERIFIED: pyproject.toml]

```bash
pip install -e .
python -m pytest tests
```

**Version verification:** local package/tool versions were checked with `python --version`, `python -m pip show privguard`, `python -m pytest --version`, `claude --version`, and `python -m pip index versions ...`. [VERIFIED: local commands]

## Architecture Patterns

### System Architecture Diagram

```text
User prompt
  -> Claude Code UserPromptSubmit hook
  -> hooks/pii_guard.py adapter
  -> privguard.hooks.main_user_prompt()
  -> privguard.detection.detect()
  -> if no hits: allow
  -> if hits and no verified rewrite capability: block with metadata-only stderr

Claude tool call
  -> Claude Code PreToolUse hook
  -> hooks/pre_tool_guard.py adapter
  -> privguard.hooks.main_pre_tool()
  -> branch by tool_name:
       Read/Edit/Write/MultiEdit/Notebook*: classify path inputs
       Glob/Grep: classify pattern/path inputs
       Bash/PowerShell: classify command categories and protected path references
       unknown/MCP/file-capable tools: fail closed or classify conservatively
  -> block or allow with sanitized reason metadata

Developer validation
  -> privguard claude doctor
  -> inspect .claude/settings.json
  -> run synthetic prompt/path/command payload checks through hook functions
  -> emit synthetic_data=true audit marker and metadata-only result
```

### Recommended Project Structure

```text
privguard/
├── hooks.py          # Claude hook policy orchestration and sanitized denial output
├── policy.py         # protected path, command category, and surface policy helpers
├── diagnostics.py    # metadata-only serializers
├── cli.py            # add claude doctor command group
└── detection.py      # existing lightweight synthetic-sensitive detection

hooks/
├── pii_guard.py      # stable UserPromptSubmit adapter
└── pre_tool_guard.py # stable PreToolUse adapter

tests/
├── test_claude_hooks.py      # hook JSON payloads, exit codes, sanitized output
├── test_claude_doctor.py     # synthetic doctor checks and audit marker
└── test_policy_commands.py   # command category coverage
```

### Pattern 1: Stable Adapter, Package-Owned Logic

**What:** Keep files under `hooks/` tiny and delegate behavior to `privguard.hooks`. [VERIFIED: hooks/pii_guard.py] [VERIFIED: hooks/pre_tool_guard.py]

**When to use:** Use for every Claude hook entry so `.claude/settings.json` paths stay stable across package refactors. [VERIFIED: .claude/settings.json]

**Example:**

```python
# Source: hooks/pre_tool_guard.py
from privguard.hooks import main_pre_tool

if __name__ == "__main__":
    raise SystemExit(main_pre_tool())
```

### Pattern 2: Metadata-Only Denial

**What:** Denials should include action, reason codes, categories/counts/offsets, and remediation, but never values or masked text. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]

**When to use:** Use for both stderr exit-code denials and JSON hook decisions. [CITED: https://code.claude.com/docs/en/hooks]

**Example:**

```python
# Recommended pattern derived from privguard.diagnostics.to_dict().
payload = {
    "action": "block",
    "reason_codes": ["pii_detected", "surface_block_only"],
    "detections": [{"kind": "BR_CPF", "start": 4, "end": 18, "score": 0.95}],
    "remediation": "Remove sensitive values or use synthetic data before retrying.",
}
```

### Pattern 3: Synthetic Doctor Probe

**What:** `privguard claude doctor` should inspect hook wiring and execute in-process synthetic payload checks against `main_user_prompt()`/`main_pre_tool()` or lower-level pure helpers. [VERIFIED: privguard/cli.py] [VERIFIED: privguard/hooks.py]

**When to use:** Use for CLD-05 validation without touching `.env` or `data_sensivel/**` contents. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]

**Example:**

```json
{
  "check": "synthetic_prompt_block",
  "synthetic_data": true,
  "synthetic_fixture_id": "CLD_SYNTH_PROMPT_CPF",
  "result": "pass",
  "reason_codes": ["pii_detected", "surface_block_only"]
}
```

### Anti-Patterns to Avoid

- **Printing `redacted=<...>` in hooks:** Redacted prompt text is still prompt-derived output and Phase 3 forbids it. [VERIFIED: privguard/hooks.py] [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]
- **Reading protected files during validation:** Protected path validation must classify strings only; current `classify_path()` is pure string logic and tests assert no `.read_text()` or `.open()` in `policy.py`. [VERIFIED: tests/test_policy.py] [VERIFIED: privguard/policy.py]
- **Using warning/scrub as Claude protection:** `UserPromptSubmit` stdout can be added as context for Claude; non-blocking output is not a safe masking guarantee. [CITED: https://code.claude.com/docs/en/hooks] [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]
- **Only matching `Read|Bash|Grep|Glob|Edit|Write`:** Claude Code docs list `MultiEdit`, notebook variants, web tools, and MCP tool naming patterns; a strict privacy hook should either match all tools or explicitly handle unknown file-capable names. [CITED: https://code.claude.com/docs/en/hooks] [VERIFIED: .claude/settings.json]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PII detection for Phase 3 hooks | A new hook-only detector | `privguard.detection.detect()` | It already contains Brazil-first validators, secret patterns, overlap handling, and tests. [VERIFIED: privguard/detection.py] [VERIFIED: tests/test_detection.py] |
| Sanitized serialization | String concatenation from `Hit` objects | `privguard.diagnostics.to_dict()` / `to_json()` / `format_hit_summary()` after removing redacted text | Existing serializers omit `Hit.value` and `MaskResult.text`. [VERIFIED: privguard/diagnostics.py] |
| Protected path detection | File reads or glob expansion | `privguard.policy.classify_path()` | It classifies `.env`, dumps, credentials, secrets, and `data_sensivel` by path string. [VERIFIED: privguard/policy.py] |
| Claude hook lifecycle semantics | Guessed hook behavior | Official Claude Code hook output and matcher contract | Exit code and JSON decision behavior are documented by Claude Code. [CITED: https://code.claude.com/docs/en/hooks] |
| Test sensitive samples | Real `.env`, dumps, or `data_sensivel` records | Synthetic CPF/CNPJ/secret/path fixtures | Project data hygiene forbids real sensitive values in tests and planning docs. [VERIFIED: AGENTS.md] |

**Key insight:** Phase 3 complexity is not PII recognition; it is enforcing the Claude boundary without leaking prompt-derived material through the hook feedback channel. [VERIFIED: repo inspection]

## Common Pitfalls

### Pitfall 1: Sanitized Placeholders Still Leak Prompt Shape

**What goes wrong:** Hook output includes `redacted=<BR_CPF>` or a masked prompt sentence. [VERIFIED: privguard/hooks.py]

**Why it happens:** Masking helpers return safe outbound payloads for rewrite-capable surfaces, but Claude prompt hooks are block-only in Phase 3. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]

**How to avoid:** Output only metadata: entity type, count, offsets, scores, reason codes, policy action, and remediation. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]

**Warning signs:** Any hook test asserts `<BR_CPF>` in stderr/stdout, or any hook message concatenates `redact()` output. [VERIFIED: privguard/hooks.py]

### Pitfall 2: Default `warn`/`scrub` Modes Become a False Safety Signal

**What goes wrong:** A user sets `PII_GUARD_MODE=warn` or `scrub` and believes Claude received a protected prompt. [VERIFIED: privguard/hooks.py]

**Why it happens:** Claude Code can inject `UserPromptSubmit` stdout as context, while the original prompt processing semantics are not proven as safe rewrite. [CITED: https://code.claude.com/docs/en/hooks]

**How to avoid:** Make `block` the only production default and label any non-blocking mode as local-development/non-protective. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]

**Warning signs:** CLI/help text says "scrub protects Claude prompts" or default environment allows warning mode. [ASSUMED]

### Pitfall 3: Shell Command Coverage Misses PowerShell and Exfil Variants

**What goes wrong:** A protected path is blocked for `cat .env` but allowed through `Compress-Archive .env`, `certutil -encode .env out.b64`, `Set-Clipboard (Get-Content .env)`, `Copy-Item .env`, or archive/network pipelines. [VERIFIED: privguard/hooks.py] [ASSUMED]

**Why it happens:** Current regexes cover read commands and network commands, but not copy/archive/encoding/clipboard categories. [VERIFIED: privguard/policy.py]

**How to avoid:** Add explicit command category regexes and tests per category, then use path-token extraction plus full-command protected-glob checks. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]

**Warning signs:** `EXFIL_CMDS` only contains network tools or tests cover only `curl`/`wget`. [VERIFIED: privguard/policy.py]

### Pitfall 4: Pytest Collection Outside `tests/` Fails on Local Cache Directories

**What goes wrong:** `python -m pytest` at repo root errors on inaccessible `pytest-cache-files-*` directories. [VERIFIED: local pytest run]

**Why it happens:** Root collection includes transient inaccessible cache directories because no pytest config limits collection. [VERIFIED: local pytest run] [VERIFIED: pyproject.toml]

**How to avoid:** Use `python -m pytest tests` for Phase 3 validation, or add pytest collection configuration to exclude cache directories. [VERIFIED: local pytest run]

**Warning signs:** PermissionError on `pytest-cache-files-*` during collection. [VERIFIED: local pytest run]

## Code Examples

### Claude Code PreToolUse Denial Shape

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "privguard blocked protected_path_env"
  }
}
```

Source: Claude Code docs document `permissionDecision: "deny"` for `PreToolUse` JSON decisions. [CITED: https://code.claude.com/docs/en/hooks]

### Current Sanitized Hit Serialization

```python
{
    "kind": value.kind,
    "start": value.start,
    "end": value.end,
    "score": value.score,
    "reason_code": value.reason_code,
    "source": value.source,
}
```

Source: `privguard.diagnostics.to_dict()` omits `Hit.value`. [VERIFIED: privguard/diagnostics.py]

### Current Unsafe Prompt Output to Remove

```python
sys.stderr.write(
    "[PII-GUARD BLOQUEADO] reason=pii_detected "
    f"detections={summary}; redacted={redacted}\n"
)
```

Source: Current `main_user_prompt()` prints masked prompt text and must be hardened. [VERIFIED: privguard/hooks.py]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Root scripts and standalone hook detector | Editable package with `privguard/` modules and thin `hooks/` adapters | Phase 1 completed 2026-05-02 [VERIFIED: .planning/STATE.md] | Phase 3 should edit package modules, not duplicate hook logic. [VERIFIED: hooks/pii_guard.py] |
| Hook-era PII guard could warn/scrub and print redacted payload | Phase 3 locked default block and no redacted hook output | Phase 3 context gathered 2026-05-03 [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md] | Planner must remove or gate unsafe modes and rewrite output contracts. [VERIFIED: privguard/hooks.py] |
| Policy tests only cover core protected paths and policy decisions | Phase 3 needs Claude hook JSON, command categories, exit codes, and doctor diagnostics | Phase 3 requirements pending [VERIFIED: .planning/REQUIREMENTS.md] | Add focused tests before/with implementation. [VERIFIED: tests/*.py] |
| Specific `PreToolUse` matcher list | Claude Code docs support `*`/omitted match-all and list additional tools/MCP patterns | Current docs checked 2026-05-03 [CITED: https://code.claude.com/docs/en/hooks] | Planner should broaden matcher strategy or explicitly justify exact tool list. [VERIFIED: .claude/settings.json] |

**Deprecated/outdated:**
- Treating `scrub` as protective for Claude prompts is out of scope for production Phase 3. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]
- Hook output that includes masked/redacted prompt text is incompatible with CLD-04. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: privguard/hooks.py]

## Candidate Plan Split

| Plan | Scope | Requirements |
|------|-------|--------------|
| 03-01 Harden prompt hook output and default blocking | Remove `redacted=` from all hook outputs, make block-only default explicit, add prompt hook tests for exit code and sanitized stderr/stdout. [VERIFIED: privguard/hooks.py] | CLD-01, CLD-04 |
| 03-02 Expand PreToolUse protected-path and command blocking | Broaden matcher/tool coverage, add command category helpers, test read/search/edit/write/copy/archive/encoding/clipboard/network patterns with synthetic paths. [VERIFIED: privguard/hooks.py] [VERIFIED: .claude/settings.json] | CLD-02, CLD-03, CLD-04 |
| 03-03 Add `privguard claude doctor` | Add CLI command group, inspect hook wiring, run synthetic payload probes, emit `synthetic_data=true` marker, and avoid protected file reads. [VERIFIED: privguard/cli.py] | CLD-05, CLD-04 |
| 03-04 Phase gate and collection hygiene | Add pytest collection config or document `python -m pytest tests`, run hook/CLI tests, and verify no raw synthetic values in outputs. [VERIFIED: local pytest run] | CLD-01..CLD-05 |

## Test Strategy

| Test Area | Required Cases | Command |
|-----------|----------------|---------|
| UserPromptSubmit | Sensitive synthetic CPF/secret blocks with exit `2`; clean prompt allows; malformed JSON fails open; no raw value or `<BR_CPF>` in stdout/stderr. [VERIFIED: requirements/context] | `python -m pytest tests/test_claude_hooks.py -q` |
| PreToolUse paths | `Read`, `Grep`, `Glob`, `Edit`, `Write`, `MultiEdit`, notebook path fields, Windows paths, quoted paths, relative traversal. [CITED: https://code.claude.com/docs/en/hooks] [VERIFIED: privguard/policy.py] | `python -m pytest tests/test_claude_hooks.py tests/test_policy.py -q` |
| Command exfiltration | Read, copy, archive, encode/decode, clipboard, network, and pipeline patterns with `.env` and `data_sensivel/synthetic.csv`. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md] | `python -m pytest tests/test_policy_commands.py -q` |
| Claude doctor | Missing/miswired hook config, effective mode, synthetic prompt block, synthetic protected path block, synthetic audit marker present. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md] | `python -m pytest tests/test_claude_doctor.py -q` |
| Output hygiene | Assert raw synthetic values, prompt snippets, protected file paths, secret-like substrings, and masked prompt text do not appear in hook or doctor output. [VERIFIED: .planning/REQUIREMENTS.md] | `python -m pytest tests -q` |

`workflow.nyquist_validation` is explicitly `false`, so the formal Nyquist Validation Architecture section is intentionally omitted. [VERIFIED: .planning/config.json]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Some users may misinterpret warning/scrub modes as protective unless labels are explicit. | Common Pitfalls | If wrong, labels are still harmless; if right, unclear labels create privacy risk. |
| A2 | Example shell bypasses such as `certutil`, `Set-Clipboard`, and `Compress-Archive` are relevant command patterns to test. | Common Pitfalls | If incomplete, planner should add more patterns during implementation review. |

## Open Questions (RESOLVED)

1. **RESOLVED: Prefer exit-code `2` denials with sanitized stderr for hook blocking; reserve JSON for CLI/doctor diagnostics.** [CITED: https://code.claude.com/docs/en/hooks]
   - Claude Code supports both exit code `2` and structured JSON decisions. [CITED: https://code.claude.com/docs/en/hooks]
   - Phase 03 plans keep the existing hook-denial shape simple and compatible with current adapters: blocked hook events return exit code `2` and emit metadata-only stderr. [VERIFIED: .planning/phases/03-claude-enforcement/03-01-PLAN.md] [VERIFIED: .planning/phases/03-claude-enforcement/03-02-PLAN.md]
   - `privguard claude doctor --json` remains the structured JSON surface for audit/diagnostic output, including `synthetic_data: true`. [VERIFIED: .planning/phases/03-claude-enforcement/03-03-PLAN.md]

2. **RESOLVED: Prefer matcher `"*"` for `PreToolUse` strict privacy coverage.** [CITED: https://code.claude.com/docs/en/hooks]
   - Current matcher is `Read|Bash|Grep|Glob|Edit|Write`, while docs list additional tools and MCP naming patterns. [VERIFIED: .claude/settings.json] [CITED: https://code.claude.com/docs/en/hooks]
   - Phase 03 Plan 03-02 instructs the executor to prefer matcher `"*"` and let `main_pre_tool()` return `0` for clearly irrelevant tools. If an explicit matcher is retained, it must at least include `Read|Bash|Grep|Glob|Edit|Write|MultiEdit|NotebookEdit|NotebookRead|PowerShell` and document why. [VERIFIED: .planning/phases/03-claude-enforcement/03-02-PLAN.md]

3. **RESOLVED: Non-blocking prompt modes may remain only behind explicit local-development/non-protective labels, or may be removed.**
   - The locked product decision is that they cannot be default protective modes. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]
   - Phase 03 Plan 03-01 allows either removal or retention behind explicit `local_development_non_protective` labeling, but in both cases outputs must remain metadata-only and must not include prompt-derived text. [VERIFIED: .planning/phases/03-claude-enforcement/03-01-PLAN.md]
   - This resolves the planning ambiguity while preserving the user's required safety default: sensitive Claude prompts block unless safe rewrite is proven. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Hook runtime and CLI | yes | 3.14.3 | None needed. [VERIFIED: `python --version`] |
| privguard editable install | CLI and hooks | yes | 0.1.0 | `python -m privguard.cli` if console script unavailable. [VERIFIED: `python -m pip show privguard`] |
| pytest | Tests | yes | 9.0.2 installed; 9.0.3 latest observed | Use installed version for Phase 3. [VERIFIED: `python -m pytest --version`] [VERIFIED: `pip index versions pytest`] |
| Claude Code CLI | Manual hook validation | yes | 2.1.126 | Unit tests can exercise hook functions without invoking Claude. [VERIFIED: `claude --version`] |
| Network/PyPI | Version discovery only | available during research | n/a | Not required for implementation if dependencies stay unchanged. [VERIFIED: pip index commands] |

**Missing dependencies with no fallback:** None found for Phase 3 planning. [VERIFIED: local commands]

**Missing dependencies with fallback:** Bare `python -m pytest` is blocked by inaccessible root cache directories; use `python -m pytest tests` or add pytest collection config. [VERIFIED: local pytest run]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No auth surface is added in Phase 3. [VERIFIED: phase scope] |
| V3 Session Management | no | No web/session surface is added in Phase 3. [VERIFIED: phase scope] |
| V4 Access Control | yes | Hook-level deny decisions for protected file/tool access. [VERIFIED: .planning/REQUIREMENTS.md] |
| V5 Input Validation | yes | Treat hook JSON and shell command strings as untrusted input; validate structure and classify paths without file I/O. [CITED: https://code.claude.com/docs/en/hooks] [VERIFIED: privguard/hooks.py] |
| V6 Cryptography | no | Phase 3 does not add reversible encryption or key storage. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md] |
| V9 Communications | yes | Goal is preventing clear-text sensitive data from reaching external LLM provider flows. [VERIFIED: AGENTS.md] |
| V10 Malicious Code | yes | Shell command blocking must cover exfiltration-style command patterns. [VERIFIED: .planning/REQUIREMENTS.md] |
| V12 Files and Resources | yes | Protected paths must be blocked before reads/searches/edits/writes. [VERIFIED: .planning/REQUIREMENTS.md] |
| V14 Configuration | yes | Doctor checks `.claude/settings.json` hook wiring and effective policy. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md] |

### Known Threat Patterns for Claude Hook Enforcement

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Prompt contains sensitive Brazilian identifier or secret | Information Disclosure | Block `UserPromptSubmit`; do not output prompt-derived text. [VERIFIED: .planning/REQUIREMENTS.md] |
| Tool reads `.env` or protected local data | Information Disclosure | `PreToolUse` path classification before tool execution. [VERIFIED: privguard/policy.py] |
| Shell command archives/encodes/copies protected files | Information Disclosure | Command category deny rules plus synthetic regression tests. [VERIFIED: .planning/phases/03-claude-enforcement/03-CONTEXT.md] |
| Hook feedback leaks sensitive values to Claude/user | Information Disclosure | Use diagnostics serializers that omit values and masked text. [VERIFIED: privguard/diagnostics.py] |
| Malformed hook JSON causes crash or fail-open confusion | Denial of Service / Bypass | Existing hooks return `0` on malformed JSON; tests should lock this behavior. [VERIFIED: privguard/hooks.py] [VERIFIED: AGENTS.md] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/03-claude-enforcement/03-CONTEXT.md` - locked Phase 3 decisions. [VERIFIED: file read]
- `.planning/REQUIREMENTS.md` - CLD-01 through CLD-05. [VERIFIED: file read]
- `.planning/ROADMAP.md` - Phase 3 goal and success criteria. [VERIFIED: file read]
- `.planning/STATE.md` - current project decisions and history. [VERIFIED: file read]
- `.planning/phases/02-privacy-core/02-CONTEXT.md` - Phase 2 core decisions. [VERIFIED: file read]
- `AGENTS.md` - project constraints and data hygiene. [VERIFIED: file read]
- `privguard/hooks.py`, `policy.py`, `detection.py`, `masking.py`, `diagnostics.py`, `cli.py` - current implementation surface. [VERIFIED: file read]
- `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, `.claude/settings.json`, `tests/*.py` - adapter/config/test surface. [VERIFIED: file read]
- Claude Code Hooks reference - hook lifecycle, matcher behavior, input/output, exit code behavior, JSON decisions, security considerations. [CITED: https://code.claude.com/docs/en/hooks]

### Secondary (MEDIUM confidence)
- Local package index checks for pytest, Presidio, and spaCy versions. [VERIFIED: pip index commands]

### Tertiary (LOW confidence)
- Shell bypass example set is representative, not exhaustive. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - local runtime, package, pytest, Claude CLI, and package index versions were checked. [VERIFIED: local commands]
- Architecture: HIGH - current adapters and package modules were read directly. [VERIFIED: file reads]
- Pitfalls: HIGH for current output and matcher gaps, MEDIUM for exhaustive command bypass coverage. [VERIFIED: privguard/hooks.py] [ASSUMED]

**Research date:** 2026-05-03 [VERIFIED: local date]
**Valid until:** 2026-05-10 for Claude Code hook semantics because Claude Code changes quickly; 2026-06-02 for local package architecture. [ASSUMED]
