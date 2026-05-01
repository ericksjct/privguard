# Feature Landscape

**Domain:** Local privacy guard package for LLM/code-agent terminal and IDE workflows
**Researched:** 2026-05-01
**Scope:** Features dimension for v1 roadmap planning
**Overall confidence:** HIGH for Claude Code and local codebase needs; MEDIUM for Codex compatibility until its interception surface is validated.

## Executive Position

v1 should be a local, fail-closed privacy guard that protects outbound LLM/code-agent interactions before any raw sensitive content can reach an external provider. The core product is not a general Presidio demo, a SaaS proxy, or a reversible anonymization framework. It is a developer-workflow safety layer for terminal and IDE agents, starting with Claude Code because the repository already has working prompt and tool hooks.

The minimum credible v1 must combine three protections: automatic masking where the integration surface can safely rewrite content, blocking where rewriting cannot be guaranteed, and safe output behavior so the guard itself never leaks the matched values it detected. Brazilian PII and local secrets must be first-class, especially CPF, CNPJ, Brazilian documents, bank/account-like data, phone/CEP/address signals, API keys, `.env` values, credential files, dumps, and sensitive project paths.

## Table Stakes

Features users expect. Missing = product feels incomplete or unsafe.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Automatic masking before external provider submission | This is the core value: raw sensitive data must not reach Anthropic, OpenAI, or other remote providers. | High | Implement only on surfaces where the submitted payload can truly be rewritten. If a hook can only warn or attach context, fail closed instead of claiming masking. |
| Fail-closed blocking when masking is not guaranteed | Privacy tooling creates false confidence if it allows clear text through unsupported clients or non-rewritable hooks. | Medium | Default behavior should block or require explicit local-only routing when interception is incomplete. |
| Brazilian PII detection | The project is explicitly Brazil-first, not generic English PII-first. | High | CPF, CNPJ, CNH, titulo de eleitor, PIS/PASEP, SUS, RG, phone, CEP, vehicle plates, names, and bank/account-like patterns should be covered with synthetic tests. |
| Secret and environment detection | Developer agents commonly touch `.env`, tokens, API keys, database URLs, cloud credentials, and config dumps. | High | Detect both inline secrets and secret-bearing files/paths. `.env` content must never be read into docs, examples, logs, or test fixtures. |
| Sensitive path protection | Agent tools can leak data by reading, grepping, globbing, copying, archiving, or uploading local files. | High | Protect `.env`, `.env.*`, `data_sensivel/**`, dumps, credentials, secret-like names, and user-configured sensitive paths. Normalize paths where possible. |
| Claude Code prompt guard | Claude is the first practical integration because project hooks already exist. | Medium | Keep `UserPromptSubmit` support as the first productized integration. Use masking only if supported by the actual hook behavior; otherwise block with sanitized guidance. |
| Claude Code pre-tool guard | Tool calls are a major exfiltration route even when prompts are clean. | High | Guard `Read`, `Grep`, `Glob`, `Bash`, `Edit`, and `Write` inputs. Expand beyond simple reads to copy/archive/upload and indirect exfiltration patterns. |
| Safe output and logging | A privacy guard that prints matched values leaks the data it is protecting. | Medium | Hook stdout/stderr, exceptions, diagnostics, tests, and demos must show entity type/count/range only, not raw values or snippets. |
| Policy modes | Teams need different strictness levels without editing code. | Medium | Keep clear modes such as `block`, `warn`, and `mask`/`scrub`, but define exact semantics. `scrub` must not imply rewriting unless the original payload is actually replaced. |
| Synthetic regression tests | Privacy claims need executable proof, not print-driven demos. | High | Use pytest-style tests with synthetic CPF/CNPJ/secrets and path names. Assert exit codes, masked outputs, and absence of raw values in stdout/stderr/logs. |
| Dependency and setup manifest | A reusable package needs reproducible installation. | Medium | Package Presidio, spaCy, Portuguese model requirements, hook entry points, and optional local-only integrations in a documented install path. |
| Configuration for custom sensitive paths and patterns | Every project has local conventions beyond `.env` and `data_sensivel`. | Medium | Support project-level config for deny paths, allowed local endpoints, thresholds, and custom pattern labels. Do not require editing hook source. |
| Codex compatibility investigation | The user explicitly wants Codex/IDE-agent support as a target. | Medium | Treat as a discovery/compatibility feature in v1, not a guaranteed enforcement claim until the interception points are proven. |

## Differentiators

Features that set the package apart. Not all are required on day one, but they are valuable if built after the table stakes are solid.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Brazil-first recognizer quality suite | Most privacy scanners are US/global-first; validated Brazilian IDs reduce false positives and misses. | High | Build a fixture matrix for valid/invalid checksums, formatted/unformatted values, overlaps, and common false positives. |
| Local-only provider routing option | When data cannot be safely masked, routing to local Ollama-style endpoints can preserve workflow continuity. | Medium | v1 should present this as an optional safe fallback, not the default product boundary. Enforce localhost/allowlist checks. |
| Guard self-audit command | Users need to know whether hooks are installed and active before trusting the tool. | Medium | Add a CLI check that verifies Claude settings, hook executability, config, denied paths, and safe-output settings without reading sensitive files. |
| Dry-run explain mode with sanitized findings | Helps tune false positives without exposing raw data. | Medium | Report entity labels, counts, confidence, source field, and character ranges. Avoid matched text. |
| Shared detection contract across Presidio and hooks | Prevents drift between heavy Presidio detection and lightweight hook detection. | High | Define one tested contract for entity labels, confidence thresholds, and redaction tokens. Hook path can remain standard-library-only but should share fixtures and semantics. |
| CI-ready privacy test harness | Makes the package useful to teams that want a release gate against leakage regressions. | Medium | Provide sample tests and commands that assert secrets/PII are blocked or masked and never printed. |
| Per-provider policy profiles | External providers, local models, and internal endpoints may need different behavior. | Medium | Useful after basic enforcement works. For v1, keep profiles simple: external = mask/block, local = allow with safeguards. |
| IDE-agent compatibility matrix | Helps users understand where protection is enforceable versus advisory. | Medium | Include Claude Code as supported first, Codex as investigated/experimental until verified, and unsupported clients as block/advisory only. |

## Anti-Features

Features to explicitly not build for v1.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Hosted SaaS or cloud proxy | Violates the local privacy boundary and increases compliance/key-management burden. | Keep all analysis, masking, policy, and logs local. |
| Claiming universal LLM protection | Clients without hooks, wrappers, proxies, or equivalent interception cannot be guaranteed safe. | Publish explicit support levels and fail closed for unsupported surfaces. |
| Deanonymization after LLM responses | Adds mapping storage, key lifecycle, and accidental rehydration risk. The project says v1 only needs outbound masking. | Use irreversible placeholders for v1. Keep reversible demo separate from production behavior. |
| Reading real `.env` or `data_sensivel` contents for tests/docs | This would reproduce the exact exfiltration risk the product prevents. | Use synthetic fixtures and path-only tests. |
| Logging raw detections for debugging | Raw hook output can leak into terminals, transcripts, CI logs, and agent memory. | Log entity kind, count, confidence bucket, and range only. |
| Print-driven demo files as regression tests | Manual inspection will miss privacy regressions and stdout leaks. | Add assertion-based tests for detectors, hooks, masking, and log safety. |
| Full LangChain/LlamaIndex integration framework | Too broad for the terminal/IDE-agent v1 and distracts from the immediate risk. | Defer framework adapters until local agent boundaries are stable. |
| Broad network traffic interception | OS/proxy interception is complex, brittle, and can create overbroad security claims. | Start with explicit agent integration surfaces and local wrapper entry points. |
| Storing reversible token maps by default | Creates a new sensitive store that must be protected, rotated, and audited. | Use non-reversible masking unless a later phase defines key management and retention. |
| Allowing warn mode as the default | Warning-only privacy guards are easy to ignore and do not meet the core value. | Default to block or guaranteed mask for external-provider paths. |

## Feature Dependencies

```text
Package layout and config -> Shared detection contract -> Automatic masking and hook enforcement
Brazilian recognizer tests -> Brazilian PII detection quality -> Safe default policy modes
Safe output/logging rules -> Hook behavior tests -> Claude-first integration release
Sensitive path model -> Pre-tool guard expansion -> Exfiltration prevention tests
Interception-surface validation -> Codex compatibility investigation -> Codex support claim
Provider classification -> External fail-closed policy -> Optional local-only routing
```

## MVP Recommendation

Prioritize:

1. **Package foundation with shared detection contract** - Move reusable detection, redaction tokens, policy config, and safe-output helpers out of demos into importable modules.
2. **Brazilian PII, secret, env, and sensitive-path test suite** - Establish synthetic regression coverage before changing enforcement behavior.
3. **Claude-first fail-closed integration** - Productize prompt and tool guards with sanitized outputs, strict defaults, and clear behavior for block/warn/mask modes.
4. **Automatic masking where technically guaranteed** - Only ship this for surfaces that can replace the outbound payload before provider submission.
5. **Codex compatibility investigation** - Document enforceable interception points, gaps, and whether support is blocker/wrapper/config based.

Defer:

- **Deanonymization:** v1 does not need response restoration and should avoid token-map storage.
- **Hosted/cloud proxy:** conflicts with the local boundary.
- **Framework adapters:** terminal/IDE-agent workflows need to stabilize first.
- **Advanced local LLM routing:** keep as optional fallback after provider classification and localhost enforcement tests exist.

## Acceptance Signals for v1 Features

| Feature Area | Acceptance Signal |
|--------------|-------------------|
| Automatic masking | A test proves synthetic sensitive values are replaced before a mocked external provider receives the payload. |
| Fail-closed behavior | Unsupported or non-rewritable surfaces block by default and emit no raw sensitive values. |
| Brazilian PII detection | Valid synthetic Brazilian identifiers are detected; invalid checksum lookalikes are downgraded or ignored where appropriate. |
| Secret/env detection | Synthetic API keys, database URLs, `.env` references, and credential-like paths are blocked or masked. |
| Sensitive path protection | Reads, greps, globs, shell reads, copy/archive/upload attempts, and path traversal variants against protected paths are denied. |
| Safe logging | Tests assert raw fixture values do not appear in stdout, stderr, logs, or exception text. |
| Policy modes | Each mode has executable tests proving exact behavior. `warn` is non-default; `mask` only exists where replacement is real. |
| Claude integration | Hook JSON fixtures cover prompt submission, tool use, malformed input, exit codes, and sanitized messages. |
| Codex investigation | A written compatibility matrix states supported, experimental, and unsupported enforcement surfaces with evidence. |

## Sources

- `.planning/PROJECT.md` - Project goals, active requirements, constraints, out-of-scope boundaries, and key decisions.
- `.planning/codebase/ARCHITECTURE.md` - Existing script/demo structure, Presidio flow, Claude hook flow, and data boundaries.
- `.planning/codebase/CONCERNS.md` - Known bugs, security risks, missing critical features, and test gaps.
- `.planning/codebase/INTEGRATIONS.md` - Current Presidio, spaCy, Ollama, Claude hook, and local file integration state.
- `.planning/codebase/STACK.md` - Current Python/Presidio/spaCy stack and missing packaging/test manifest.
- `.planning/codebase/STRUCTURE.md` - File organization, sensitive path rules, and where future code belongs.
- `.planning/codebase/TESTING.md` - Current verification pattern and missing assertion-based test coverage.
