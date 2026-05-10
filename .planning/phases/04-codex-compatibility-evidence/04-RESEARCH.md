# Phase 04: Codex Compatibility Evidence - Research

**Researched:** 2026-05-03
**Domain:** Codex CLI hook compatibility, privacy support labels, claim-prevention tests
**Confidence:** HIGH for conservative block-only guidance; LOW for any automatic Codex masking claim

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Codex compatibility uses a strict proof bar. A positive support claim needs current
  official/documented Codex behavior, local installed-Codex probing where feasible, and synthetic
  end-to-end evidence for the specific surface being labeled.
- **D-02:** Documentation-only or repo-issue-only signals may inform the assessment, but they are
  not enough for a positive supported masking claim.
- **D-03:** If a Codex surface cannot be exercised locally or cannot prove pre-provider payload
  replacement, the matrix must label it conservatively and explain the missing evidence.
- **D-04:** All prior criteria used for the shared privacy core and Claude enforcement apply to
  Codex too: fail closed by default, synthetic-only validation, sanitized diagnostics, protected
  path handling without file reads, and no raw matched values in outputs.
- **D-05:** If Codex can block a surface but cannot prove rewrite before provider submission, the
  correct label is block-only or experimental block-only, not automatic masking.
- **D-06:** If hook/event coverage, Windows behavior, tool coverage, or version behavior is
  uncertain, the label must remain experimental or unsupported with the uncertainty stated plainly.
- **D-07:** Automatic Codex masking can be claimed only for a surface where tests prove the outbound
  payload equals the verified masked payload before any external-provider submission.
- **D-08:** Phase 4 should deliver documentation, a compatibility matrix, and automated tests or
  checks that prevent overstated Codex masking claims.
- **D-09:** A Codex doctor-style CLI command is optional, not required. Add one only if the planner
  finds a stable local Codex surface that can be validated safely with synthetic probes.
- **D-10:** The compatibility artifact should be auditable: each row should list the surface, support
  label, evidence source, tested version or docs date where available, privacy action, and remaining
  gaps.

### Claude's Discretion
- The planner may choose the exact file name/location for the Codex compatibility assessment, as
  long as it is easy to find from project docs and included in tests or claim checks.
- The planner may decide whether claim-prevention checks scan Markdown docs, package metadata, CLI
  help text, or all of these.
- The planner may decide whether local Codex probing is a script, pytest fixture, CLI subcommand, or
  manual evidence appendix, provided positive labels still require strict proof.

### Deferred Ideas (OUT OF SCOPE)
- `privguard codex doctor` is deferred to planner discretion; add it only if a stable local Codex
  validation surface exists.
- Broad IDE-agent support, local proxy mode, LangChain/LlamaIndex adapters, and enterprise policy
  distribution remain v2 work.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CDX-01 | Project documents current Codex interception options and whether prompt/tool payloads can be blocked or rewritten before provider submission. | Codex hooks docs show feature-flagged hooks, `UserPromptSubmit` prompt input, block decisions, `PreToolUse`/`PostToolUse` tool coverage limits, and unsupported rewrite fields. [CITED: https://developers.openai.com/codex/hooks] |
| CDX-02 | Project includes a compatibility matrix that marks Codex support as supported, experimental, block-only, or unsupported with evidence. | Existing `SurfaceCapability` labels already provide the internal vocabulary; the matrix should map user labels to `rewrite-capable`, `block-only`, `observe-only`, `unsupported`, `unknown`, or `external`. [VERIFIED: privguard/policy.py] |
| CDX-03 | Guard does not claim automatic Codex masking until a tested integration proves raw payloads are replaced before submission. | Current Codex hook docs support blocking but do not document supported tool-call payload rewrite, and `updatedInput`/related fields are reserved or unsupported in the cited events. [CITED: https://developers.openai.com/codex/hooks] |
</phase_requirements>

## Summary

Phase 04 should be planned as an evidence and claim-control phase, not as a Codex masking implementation. [VERIFIED: 04-CONTEXT.md] Codex CLI is installed locally as `codex-cli 0.128.0`, and the current npm registry reports `@openai/codex` version `0.128.0` modified on 2026-05-01. [VERIFIED: local `codex --version`; VERIFIED: `npm view @openai/codex version time.modified --json`]

The official Codex CLI docs state that the CLI runs locally from the terminal and can inspect repos, edit files, and run commands. [CITED: https://developers.openai.com/codex/cli] The official hooks docs state that Codex hooks are feature-flagged with `features.codex_hooks = true`, can run from repo/user config layers, and include turn-scoped `PreToolUse`, `PermissionRequest`, `PostToolUse`, `UserPromptSubmit`, and `Stop`. [CITED: https://developers.openai.com/codex/hooks]

**Primary recommendation:** Plan docs plus a checked compatibility matrix and pytest claim gate; classify Codex prompt blocking as block-capable where proven, classify tool interception as experimental block-only, and classify automatic Codex masking as unsupported until a future test proves pre-provider raw payload replacement. [VERIFIED: 04-CONTEXT.md; CITED: https://developers.openai.com/codex/hooks]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Codex compatibility assessment | Documentation / policy metadata | Tests | The deliverable is an auditable statement of current support and evidence, not runtime interception. [VERIFIED: 04-CONTEXT.md] |
| Support-label enforcement | Package policy layer | Tests | `SurfaceCapability` and `decide_policy()` already own fail-closed capability decisions. [VERIFIED: privguard/policy.py] |
| Claim-prevention gate | Tests | Documentation | The planner should add tests that fail on unsupported Codex masking claims in docs/CLI-visible strings. [VERIFIED: 04-CONTEXT.md] |
| Optional Codex probe | CLI / script | Tests | A `privguard codex doctor` command is optional and should exist only if it can exercise a stable synthetic surface without reading protected data. [VERIFIED: 04-CONTEXT.md] |

## Standard Stack

### Core

| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| Python | 3.14.3 local | Implement matrix helpers, CLI diagnostics, and pytest gates. | Current project package and tests are Python. [VERIFIED: local `python --version`; VERIFIED: pyproject.toml] |
| pytest | 9.0.2 local | Claim-prevention and compatibility matrix tests. | Existing tests use pytest, and focused Phase 2/3 policy gates pass locally. [VERIFIED: local `python -m pytest --version`; VERIFIED: tests/test_policy.py; VERIFIED: tests/test_claude_phase_gate.py] |
| privguard policy core | local package | Reuse `SurfaceCapability`, `PolicyAction`, `decide_policy()`, protected path classification, and fail-closed behavior. | Prior phases already locked these semantics for integrations. [VERIFIED: privguard/policy.py; VERIFIED: 02-CONTEXT.md; VERIFIED: 03-CONTEXT.md] |
| OpenAI Codex CLI | 0.128.0 local | Probe installed Codex version and documented hook/config behavior where feasible. | Positive Codex labels require local probing when feasible. [VERIFIED: local `codex --version`; VERIFIED: 04-CONTEXT.md] |

### Supporting

| Library / Tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| npm | 11.12.1 local | Verify current published `@openai/codex` version metadata. | Use only for version/evidence checks, not for runtime privacy logic. [VERIFIED: local `npm --version`; VERIFIED: `npm view @openai/codex ...`] |
| Markdown document | n/a | Human-readable Codex compatibility assessment. | Required for CDX-01 and developer-facing evidence. [VERIFIED: REQUIREMENTS.md] |
| JSON or Python constant matrix | n/a | Machine-readable support rows consumed by tests/CLI. | Prevents doc-only drift and enables claim gates. [ASSUMED] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Matrix + tests | Direct Codex hook implementation | Direct implementation would imply protection claims that current evidence does not support for rewrite-capable masking. [CITED: https://developers.openai.com/codex/hooks; VERIFIED: 04-CONTEXT.md] |
| Optional `privguard codex doctor` | Documentation-only appendix | A doctor command is useful only if it avoids real provider submission and can be stable under local Codex config. [VERIFIED: 04-CONTEXT.md; ASSUMED] |
| Markdown-only claims | Machine-readable matrix | Markdown-only claims are easier to overstate and harder to test. [ASSUMED] |

**Installation:** No new runtime dependency is required for Phase 04 if the planner keeps the matrix in Python/JSON and uses existing pytest. [VERIFIED: pyproject.toml; VERIFIED: tests directory]

## Codex Surface Matrix Considerations

| Codex Surface | Evidence | Recommended Label | Privacy Action | Gaps |
|---------------|----------|-------------------|----------------|------|
| CLI user prompt via `UserPromptSubmit` | Hook input includes `prompt`; docs show `decision: "block"` and exit code 2 blocking. [CITED: https://developers.openai.com/codex/hooks] | `block-only` after synthetic local hook test; otherwise `experimental block-only`. [VERIFIED: 04-CONTEXT.md] | Block sensitive prompt; do not claim rewrite/masking. [VERIFIED: 03-CONTEXT.md] | Need local synthetic E2E evidence for installed version. [VERIFIED: 04-CONTEXT.md] |
| `PreToolUse` Bash | Docs show matcher support for `Bash` and tool input via `tool_input.command`; docs also say shell interception is incomplete for newer `unified_exec`. [CITED: https://developers.openai.com/codex/hooks] | `experimental block-only`. [CITED: https://developers.openai.com/codex/hooks] | Block protected paths and inline PII when event is observed. [VERIFIED: privguard/policy.py] | Not complete enough for universal tool protection claim. [CITED: https://developers.openai.com/codex/hooks] |
| `PreToolUse` `apply_patch` / Edit / Write aliases | Docs say `apply_patch` can match `Edit` and `Write`; input reports canonical `tool_name: "apply_patch"`. [CITED: https://developers.openai.com/codex/hooks] | `experimental block-only`. [CITED: https://developers.openai.com/codex/hooks] | Block protected-path edits if the event payload exposes paths/patch safely. [ASSUMED] | Need local payload-shape fixture before planner writes adapter logic. [ASSUMED] |
| MCP tool calls | Docs list MCP tool names as matchable and tool args in `tool_input`. [CITED: https://developers.openai.com/codex/hooks] | `experimental block-only`. [CITED: https://developers.openai.com/codex/hooks] | Block only for known payload schemas or conservative string scan of args. [ASSUMED] | MCP schemas vary by server; false-negative risk if args are opaque. [ASSUMED] |
| `PermissionRequest` | Docs allow deny decisions for approval requests, but it runs only when Codex is about to ask for approval. [CITED: https://developers.openai.com/codex/hooks] | `observe/approval-gate only`, not masking support. [CITED: https://developers.openai.com/codex/hooks] | Use as a secondary deny signal, not as primary privacy boundary. [ASSUMED] | Commands that do not request approval will not hit this event. [CITED: https://developers.openai.com/codex/hooks] |
| `PostToolUse` | Docs say it runs after supported tools and cannot undo side effects. [CITED: https://developers.openai.com/codex/hooks] | `observe-only`. [CITED: https://developers.openai.com/codex/hooks] | May sanitize future context, but cannot protect the already-executed tool action. [CITED: https://developers.openai.com/codex/hooks] | Not a pre-exfiltration control. [CITED: https://developers.openai.com/codex/hooks] |
| `WebSearch` / non-shell non-MCP tools | Docs say these are not intercepted by current `PostToolUse` coverage and mention incomplete shell interception. [CITED: https://developers.openai.com/codex/hooks] | `unsupported` for privacy enforcement. [CITED: https://developers.openai.com/codex/hooks] | Do not claim protection. [VERIFIED: 04-CONTEXT.md] | Need future official support before upgrade. [ASSUMED] |
| Automatic prompt/tool masking rewrite | Docs show blocking and context addition; cited tool rewrite fields are reserved/unsupported or fail open/closed depending event. [CITED: https://developers.openai.com/codex/hooks] | `unsupported`. [CITED: https://developers.openai.com/codex/hooks] | No automatic Codex masking claim. [VERIFIED: 04-CONTEXT.md] | Requires proof outbound payload equals `mask_text().text` before provider submission. [VERIFIED: privguard/masking.py; VERIFIED: 04-CONTEXT.md] |

## Architecture Patterns

### System Architecture Diagram

```text
Official Codex docs + local Codex probe + existing privguard policy
        |
        v
Evidence classification rules
        |
        v
Machine-readable compatibility matrix
        |
        +--> Human compatibility assessment for CDX-01/CDX-02
        |
        +--> Pytest claim gate for CDX-03
                  |
                  v
        Blocks unsupported "automatic Codex masking" claims
```

### Recommended Project Structure

```text
docs/
  codex-compatibility.md        # Human-readable assessment. [ASSUMED]
privguard/
  codex.py                      # Optional matrix constants/helpers if planner wants package API. [ASSUMED]
  diagnostics.py                # Optional codex doctor report if stable local probing is feasible. [VERIFIED: privguard/diagnostics.py]
  cli.py                        # Optional `privguard codex doctor` subcommand. [VERIFIED: privguard/cli.py]
tests/
  test_codex_compatibility.py   # Matrix semantics and evidence fields. [ASSUMED]
  test_codex_claim_gate.py      # Prevent unsupported automatic masking claims. [ASSUMED]
```

### Pattern 1: Capability Rows Must Map To Policy Labels

**What:** Each matrix row should include `surface`, `support_label`, `surface_capability`, `evidence`, `tested_version_or_docs_date`, `privacy_action`, and `gaps`. [VERIFIED: 04-CONTEXT.md]

**When to use:** Use this for every Codex prompt/tool surface, including unsupported surfaces. [VERIFIED: 04-CONTEXT.md]

**Example:**

```python
CODEX_COMPATIBILITY = [
    {
        "surface": "UserPromptSubmit prompt",
        "support_label": "block-only",
        "surface_capability": SurfaceCapability.BLOCK_ONLY,
        "privacy_action": "block_sensitive_prompt",
        "evidence": ["OpenAI Codex hooks docs 2026-05-03", "local codex-cli 0.128.0 probe"],
        "automatic_masking": False,
        "gaps": ["no verified outbound payload rewrite"],
    },
]
```

Source: existing `SurfaceCapability` vocabulary and Phase 04 matrix requirement. [VERIFIED: privguard/policy.py; VERIFIED: 04-CONTEXT.md]

### Pattern 2: Claim Gate Should Deny Unsupported Marketing Language

**What:** Add a pytest scan over repo docs and CLI-visible strings that fails if Codex is described as automatic masking/rewrite-capable without an allowlisted matrix row proving `automatic_masking=True`. [ASSUMED]

**When to use:** Use this for CDX-03, because the requirement is to prevent improper claims as much as to document current status. [VERIFIED: REQUIREMENTS.md]

**Example:**

```python
FORBIDDEN_CLAIMS = (
    "Codex automatic masking",
    "automatic Codex masking",
    "Codex rewrite-capable",
)
```

Source: CDX-03 and Phase 04 decisions. [VERIFIED: REQUIREMENTS.md; VERIFIED: 04-CONTEXT.md]

### Anti-Patterns to Avoid

- **Using docs-only evidence for `rewrite-capable`:** The user explicitly rejected documentation-only positive masking claims. [VERIFIED: 04-CONTEXT.md]
- **Treating `PostToolUse` as protection:** Codex docs say post-tool hooks run after the tool and cannot undo side effects. [CITED: https://developers.openai.com/codex/hooks]
- **Reading `.env` or `data_sensivel/**` during probes:** Prior phases require protected path handling without reading protected contents. [VERIFIED: 02-CONTEXT.md; VERIFIED: 03-CONTEXT.md]
- **Claiming `PreToolUse` covers all tool paths:** Codex docs state incomplete shell interception and no interception for WebSearch/non-shell/non-MCP paths in the cited coverage discussion. [CITED: https://developers.openai.com/codex/hooks]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Support vocabulary | New Codex-only labels with different semantics | Map user-facing labels to `SurfaceCapability` | The existing policy model already encodes fail-closed behavior. [VERIFIED: privguard/policy.py] |
| Mask verification | Custom string replacement checks | `mask_text()` and `verify_mask()` | These are already tested to reject original-value residuals and residual detections. [VERIFIED: privguard/masking.py; VERIFIED: tests/test_masking.py] |
| Sanitized output | Ad hoc JSON dumps of hook payloads | `diagnostics.to_dict()` / `to_json()` patterns | Existing serializers omit raw `Hit.value` and dataclass text fields. [VERIFIED: privguard/diagnostics.py] |
| Protected path proof | Opening protected files | `classify_path()` / `classify_command()` with synthetic paths | Policy tests already assert path classification without file I/O. [VERIFIED: tests/test_policy.py] |

**Key insight:** Codex compatibility is a claims-integrity problem until a stable rewrite surface is proven; custom masking glue would increase false confidence without satisfying CDX-03. [VERIFIED: 04-CONTEXT.md]

## Candidate Plan Split

| Plan | Scope | Likely Files |
|------|-------|--------------|
| 04-01 | Create Codex compatibility matrix and human-readable assessment. | `docs/codex-compatibility.md`, optional `privguard/codex.py`, `tests/test_codex_compatibility.py`. [ASSUMED] |
| 04-02 | Add CDX-03 claim-prevention gate and sanitize/evidence assertions. | `tests/test_codex_claim_gate.py`, maybe update README/docs if present. [ASSUMED] |
| 04-03 | Optional local Codex probe/doctor only if planner can exercise stable synthetic hooks without provider submission. | `privguard/diagnostics.py`, `privguard/cli.py`, `tests/test_codex_doctor.py`, optional `.codex/hooks.json.example`. [ASSUMED] |

Planner note: keep 04-03 optional because Phase 04 decisions say doctor is discretionary and only justified if a stable local surface exists. [VERIFIED: 04-CONTEXT.md]

## Test Strategy For CDX-01/CDX-02/CDX-03

| Requirement | Test Type | What to Assert |
|-------------|-----------|----------------|
| CDX-01 | Documentation/matrix test | Every documented Codex surface row has evidence source, docs date or tested version, block/rewrite capability, privacy action, and gaps. [VERIFIED: REQUIREMENTS.md; VERIFIED: 04-CONTEXT.md] |
| CDX-02 | Unit test | Every row maps to an approved `SurfaceCapability`, and user-facing labels are one of supported/experimental/block-only/unsupported with conservative mapping. [VERIFIED: privguard/policy.py; VERIFIED: REQUIREMENTS.md] |
| CDX-03 | Repo text claim gate | No docs/CLI/package strings claim automatic Codex masking unless the machine-readable matrix contains a row with `automatic_masking=True` and proof fields. [VERIFIED: REQUIREMENTS.md; VERIFIED: 04-CONTEXT.md] |
| CDX-03 | Policy behavior test | Codex rows without `automatic_masking=True` should resolve to block/unsupported behavior for sensitive synthetic hits. [VERIFIED: privguard/policy.py; VERIFIED: tests/test_policy.py] |
| Output hygiene | Regression test | Synthetic CPF, fake token, prompt snippets, protected paths, and masked placeholders should not appear in diagnostic outputs unless explicitly safe. [VERIFIED: tests/test_claude_phase_gate.py; VERIFIED: 03-CONTEXT.md] |

Focused verification already run during research: `python -m pytest tests/test_policy.py tests/test_claude_phase_gate.py -q` passed 12 tests with one pytest cache warning. [VERIFIED: local pytest run]

## Common Pitfalls

### Pitfall 1: Overstating Prompt Blocking As Masking
**What goes wrong:** A blocked Codex prompt is described as masked Codex support. [VERIFIED: 04-CONTEXT.md]
**Why it happens:** `UserPromptSubmit` can block, but the cited docs do not prove replacement of the prompt before provider submission. [CITED: https://developers.openai.com/codex/hooks]
**How to avoid:** Label prompt protection as `block-only` unless synthetic E2E evidence proves outbound replacement. [VERIFIED: 04-CONTEXT.md]
**Warning signs:** Documentation says "automatic Codex masking" or "Codex rewrite-capable" without matrix proof. [VERIFIED: REQUIREMENTS.md]

### Pitfall 2: Treating Hook Coverage As Complete
**What goes wrong:** Planner assumes `PreToolUse` protects every shell/file/search path. [ASSUMED]
**Why it happens:** Codex docs list supported events but also state incomplete shell interception and non-interception for some non-shell/non-MCP tools. [CITED: https://developers.openai.com/codex/hooks]
**How to avoid:** Matrix rows must include remaining gaps and conservative labels. [VERIFIED: 04-CONTEXT.md]
**Warning signs:** A single "Codex supported" row covers all CLI behavior. [ASSUMED]

### Pitfall 3: Unsafe Local Probing
**What goes wrong:** A probe reads `.env` or `data_sensivel/**` to prove blocking. [ASSUMED]
**Why it happens:** Protected-path checks are confused with content checks. [VERIFIED: 02-CONTEXT.md]
**How to avoid:** Use synthetic strings such as `.env`, `data_sensivel/synthetic.csv`, and fake CPF/token values only. [VERIFIED: 03-CONTEXT.md; VERIFIED: privguard/diagnostics.py]
**Warning signs:** Test/probe code calls `read_text()` or `open()` on protected paths. [VERIFIED: tests/test_policy.py]

## Threat Model Considerations

| Threat | STRIDE | Standard Mitigation |
|--------|--------|---------------------|
| False support claim causes user to paste real CPF/CNPJ/secrets into Codex | Information Disclosure | Claim-prevention tests and conservative matrix labels. [VERIFIED: REQUIREMENTS.md; VERIFIED: 04-CONTEXT.md] |
| Tool path bypass through unsupported Codex tool surface | Information Disclosure | Label unsupported/incomplete surfaces explicitly and block only where event is observed. [CITED: https://developers.openai.com/codex/hooks] |
| Hook diagnostics leak raw matched values | Information Disclosure | Reuse sanitized diagnostics and Phase 03 forbidden-output pattern. [VERIFIED: privguard/diagnostics.py; VERIFIED: tests/test_claude_phase_gate.py] |
| Protected file contents read during validation | Information Disclosure | Validate by path classification using synthetic paths only. [VERIFIED: tests/test_policy.py; VERIFIED: 03-CONTEXT.md] |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | tests/package code | yes | 3.14.3 | none needed. [VERIFIED: local `python --version`] |
| pytest | claim gates | yes | 9.0.2 | none needed. [VERIFIED: local `python -m pytest --version`] |
| Codex CLI | local probing | yes | codex-cli 0.128.0 | If probing cannot run safely, document local command evidence only and keep labels conservative. [VERIFIED: local `codex --version`] |
| npm | registry version check | yes | 11.12.1 | Use official docs date if npm is unavailable. [VERIFIED: local `npm --version`] |
| repo `.codex/` config | project-local hook probing | no | n/a | Use example config/docs or temp test config; do not assume project hooks are installed. [VERIFIED: local `.codex` check] |

**Missing dependencies with no fallback:** None for docs/matrix/tests. [VERIFIED: local environment audit]

**Missing dependencies with fallback:** Project-local `.codex/` config is absent; fallback is documentation plus optional generated example/probe. [VERIFIED: local `.codex` check]

## Validation Architecture

Nyquist validation is explicitly disabled in `.planning/config.json`, so the formal Validation Architecture section is omitted from planner requirements. [VERIFIED: .planning/config.json]

Even with Nyquist disabled, Phase 04 should add pytest checks because CDX-03 is a regression-prevention requirement. [VERIFIED: REQUIREMENTS.md]

## Security Domain

Security enforcement is not explicitly disabled in `.planning/config.json`, so security considerations apply. [VERIFIED: .planning/config.json]

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | Phase 04 should not touch Codex auth files or tokens. [ASSUMED] |
| V3 Session Management | no | No session management implementation is planned. [ASSUMED] |
| V4 Access Control | yes | Use fail-closed support labels and do not claim protection for unsupported surfaces. [VERIFIED: privguard/policy.py; VERIFIED: 04-CONTEXT.md] |
| V5 Input Validation | yes | Synthetic prompt/tool/path strings should be classified through existing detection and policy APIs. [VERIFIED: privguard/policy.py; VERIFIED: privguard/masking.py] |
| V6 Cryptography | no | v1 masking is irreversible and does not introduce key management. [VERIFIED: 02-CONTEXT.md] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A JSON or Python constant matrix is the best machine-readable compatibility artifact. | Standard Stack / Architecture Patterns | Planner may choose Markdown-only and weaken claim gates. |
| A2 | Optional Codex doctor can be skipped unless stable synthetic hook probing is feasible without provider submission. | Candidate Plan Split | Planner might overinvest in fragile local automation. |
| A3 | MCP payload schemas vary enough that conservative string scanning may be needed. | Codex Surface Matrix Considerations | Tests may miss server-specific protected path fields. |
| A4 | Repo text claim scanning over docs/CLI strings is sufficient for CDX-03 in Phase 04. | Test Strategy | Future packaging metadata or generated docs may need additional scan targets. |

## Open Questions (RESOLVED)

1. **Can installed Codex `0.128.0` exercise hooks in a fully offline/synthetic way without provider submission?**
   - What we know: `codex --help`, `codex exec --help`, and `codex --version` run locally. [VERIFIED: local Codex commands]
   - What's unclear: Whether a hook probe can validate `UserPromptSubmit`/`PreToolUse` without authenticated model execution or external provider submission. [ASSUMED]
   - Recommendation: Do not require `privguard codex doctor` unless planner confirms a safe probe path. [VERIFIED: 04-CONTEXT.md]
   - RESOLVED: Treat offline synthetic hook probing as unproven for Phase 04 planning. Do not plan
     a required `privguard codex doctor` command, and do not label any Codex prompt/tool surface as
     proven `block-only` based only on the local CLI version. Use `experimental block-only` for
     block-capable hooks until execution adds an explicit no-provider synthetic interception proof.

2. **Where should the compatibility matrix live?**
   - What we know: The project currently has `privguard/` package modules and pytest tests. [VERIFIED: pyproject.toml; VERIFIED: tests directory]
   - What's unclear: Whether product docs will later have a canonical docs folder. [ASSUMED]
   - Recommendation: Put human docs in `docs/codex-compatibility.md` and machine-readable rows in `privguard/codex.py` unless planner prefers a JSON file. [ASSUMED]
   - RESOLVED: Use `docs/codex-compatibility.md` for the human assessment and `privguard/codex.py`
     for the machine-readable source of truth, with tests checking that the two stay aligned.

3. **Should the matrix use "supported" at all for Codex in Phase 04?**
   - What we know: The user requested supported/experimental/block-only/unsupported labels, but automatic masking is unproven. [VERIFIED: REQUIREMENTS.md; VERIFIED: 04-CONTEXT.md]
   - What's unclear: Whether "supported block-only" is acceptable wording for `UserPromptSubmit` after local proof. [ASSUMED]
   - Recommendation: Prefer "block-only" over "supported" for current Codex surfaces to avoid ambiguity. [VERIFIED: 04-CONTEXT.md]
   - RESOLVED: Do not use `supported` for Codex surfaces in Phase 04. Use `experimental block-only`
     for prompt/tool pre-use hooks unless the execution plan adds explicit synthetic interception
     proof, `observe-only` for post/approval-style events, and `unsupported` for automatic masking
     and uncovered tool paths.

## Sources

### Primary (HIGH confidence)
- `.planning/phases/04-codex-compatibility-evidence/04-CONTEXT.md` - locked user decisions and deliverable shape. [VERIFIED: local file]
- `.planning/REQUIREMENTS.md` - CDX-01 through CDX-03. [VERIFIED: local file]
- `.planning/phases/02-privacy-core/02-CONTEXT.md` - fail-closed labels, masking, diagnostics. [VERIFIED: local file]
- `.planning/phases/03-claude-enforcement/03-CONTEXT.md` - block-not-rewrite precedent and synthetic validation standard. [VERIFIED: local file]
- `privguard/policy.py`, `privguard/masking.py`, `privguard/diagnostics.py`, `privguard/cli.py` - current implementation contracts. [VERIFIED: local files]
- OpenAI Codex CLI docs: https://developers.openai.com/codex/cli - CLI local operation and install/upgrade guidance. [CITED: official docs]
- OpenAI Codex hooks docs: https://developers.openai.com/codex/hooks - hook events, config, blocking, limitations, and unsupported fields. [CITED: official docs]
- Local Codex version: `codex-cli 0.128.0`; npm package version: `0.128.0`, modified `2026-05-01T13:36:47.764Z`. [VERIFIED: local commands]

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` - prior Codex risk framing, treated as historical starting point only. [VERIFIED: local file]

### Tertiary (LOW confidence)
- No unverified web/community sources were used for final recommendations. [VERIFIED: research process]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new runtime stack is needed, and local versions were probed. [VERIFIED: local commands]
- Architecture: HIGH - deliverables map directly to locked Phase 04 decisions and existing policy/masking code. [VERIFIED: 04-CONTEXT.md; VERIFIED: privguard/policy.py]
- Codex automatic masking: LOW - current evidence does not prove rewrite before provider submission. [CITED: https://developers.openai.com/codex/hooks; VERIFIED: 04-CONTEXT.md]
- Tool interception completeness: MEDIUM-LOW - official docs document supported hooks but also document incomplete shell/non-shell coverage. [CITED: https://developers.openai.com/codex/hooks]

**Research date:** 2026-05-03
**Valid until:** 2026-05-10 for Codex hook behavior because Codex CLI releases frequently. [VERIFIED: npm modified date 2026-05-01]

## RESEARCH COMPLETE

**Phase:** 04 - codex-compatibility-evidence
**Confidence:** HIGH for conservative planning; LOW for any rewrite-capable Codex claim

### Key Findings
- Codex CLI and hooks are documented officially, and the installed local CLI is `codex-cli 0.128.0`. [VERIFIED: local command; CITED: https://developers.openai.com/codex/cli]
- `UserPromptSubmit` can block a prompt, but current evidence supports block-only labeling, not automatic masking. [CITED: https://developers.openai.com/codex/hooks]
- `PreToolUse` can observe some tool calls, but official docs identify incomplete shell coverage and unsupported non-shell/non-MCP interception. [CITED: https://developers.openai.com/codex/hooks]
- Phase 04 should add an auditable matrix and tests that prevent unsupported automatic Codex masking claims. [VERIFIED: 04-CONTEXT.md; VERIFIED: REQUIREMENTS.md]

### File Created
`.planning/phases/04-codex-compatibility-evidence/04-RESEARCH.md`

### Ready for Planning
Research complete. Planner can now create PLAN.md files.
