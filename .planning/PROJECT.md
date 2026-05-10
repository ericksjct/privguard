# privguard

## What This Is

privguard is a privacy package for LLM and code-agent workflows in terminal/IDE environments. It started as Microsoft Presidio experiments, but the product direction is now to automatically mask sensitive data before prompts, tool calls, or local context can be sent to external providers such as Anthropic or OpenAI.

The initial focus is Brazilian sensitive data: CPF, CNPJ, names, bank/account data, API keys, environment variables, credentials, dumps, and local sensitive files. The package should act locally at the agent boundary and prevent sensitive company data from leaving the machine or corporate environment.

## Core Value

No sensitive Brazilian or company data should be sent to external LLM providers in clear text.

## Requirements

### Validated

- ✓ Brazilian PII detection can be built on Microsoft Presidio with custom recognizers and checksum validators for CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS, RG, phone, CEP, and vehicle plates — existing demo code
- ✓ Prompt and tool-use guard hooks exist for Claude Code and can block or warn on detected sensitive data — existing hook code
- ✓ Sensitive local paths such as `.env` and `data_sensivel/**` are protected by Claude Code deny rules and pre-tool guard checks — existing configuration
- ✓ Local-only reversible anonymization has been demonstrated, proving that sensitive text can be transformed before an LLM-facing step — existing demo code
- ✓ Local LLM routing with Ollama has been demonstrated as an alternative to remote providers — existing demo code
- ✓ Phase 1 validated package foundation: `pyproject.toml`, importable `privguard` modules, `privguard info`, package-backed hook adapters, and demos separated under `demos/` — Phase 1 Package Foundation; editable-install wrapper has a pending environment UAT due local pip temp-permission errors
- ✓ Phase 2 validated privacy core: Brazil-first detection, irreversible masking, protected-path classification, fail-closed policy decisions, sanitized diagnostics, CLI scan/mask/policy-check, and synthetic regression coverage — Phase 2 Privacy Core
- ✓ Phase 3 validated Claude enforcement: Claude Code hook adapters block sensitive prompts, protected reads/searches/edits/writes, risky shell commands, LLM orchestration payload PII, protected wildcard path patterns, and unsafe unsupported surfaces with sanitized metadata-only output — Phase 3 Claude Enforcement
- ✓ Phase 4 validated Codex compatibility evidence: Codex support is evidence-labeled and no automatic Codex masking claim exists without tested interception/rewrite proof — Phase 4 Codex Compatibility Evidence
- ✓ Phase 5 validated synthetic regression gate: the v1 surface has synthetic tests proving raw sensitive values do not leak through outputs, logs, hooks, masks, or failures — Phase 5 Synthetic Regression Gate
- ✓ Phase 6 validated milestone cleanup: requirements, roadmap, summary traceability, canonical `privguard` package metadata, top-level public API exports, and Python 3.14 install guidance match the verified v1 state — Phase 6 Milestone Cleanup
- ✓ Phase 7 validated bilingual README hygiene: `README.md` (English) and `README.pt-BR.md` (Brazilian Portuguese) both exist with all 9 D-04 sections, locked vocabulary verbatim, cross-language switcher, and `privguard cleanup` subcommand documented — Phase 7 README Hygiene

### Active



### Out of Scope

- Building a hosted SaaS or cloud proxy — the protection boundary must stay local for now
- Desmascaramento after LLM responses — v1 only needs masking before external submission
- Full application integration framework support such as LangChain or LlamaIndex — terminal/IDE code-agent use comes first
- Guaranteeing protection in clients that do not support hooks, wrappers, proxies, or equivalent interception points — unsupported clients need a separate integration design
- Using real sensitive files as fixtures or committed examples — tests should use synthetic data only

## Context

The user wants this project to enforce privacy for LLM-assisted development and code-agent usage. The risk being addressed is accidental exfiltration of Brazilian personal data, credentials, environment variables, account information, dumps, or other sensitive company data to remote LLM servers.

The current codebase has a package foundation, a validated privacy core, validated Claude enforcement, evidence-labeled Codex compatibility, a synthetic regression gate, and milestone-cleanup traceability. The shared core now includes synthetic-only Brazilian identifier and secret detection, irreversible typed masking with verification, protected-path classification without file reads, fail-closed surface policy decisions, sanitized diagnostics, public package exports, and CLI `scan`, `mask`, `policy-check`, and `claude doctor` commands. Editable-install console-wrapper verification remains pending in UAT because local pip temp directory permissions blocked `python -m pip install -e .`.

The current Claude integration is now production-hook oriented for the controlled local surfaces: `UserPromptSubmit` blocks sensitive prompt submission by default when safe rewrite is unavailable, `PreToolUse` blocks protected paths, exfiltration-style commands, sensitive glob patterns, unknown/network surfaces, and LLM orchestration payloads containing PII, and all diagnostics are metadata-only. Future v1 product behavior may still move toward automatic masking before external submission where the client provides a proven rewrite surface.

The user is not yet sure which exact integrations beyond Claude/Codex should be supported or how strict the balance should be between false positives and developer friction. The roadmap should therefore make privacy policy defaults explicit and validate them early.

## Constraints

- **Privacy boundary**: Raw sensitive data must stay local and must not be sent to Anthropic, OpenAI, or other external LLM providers — this is the purpose of the project.
- **Initial environment**: v1 targets terminal/IDE code-agent workflows, especially Claude Code and Codex-style usage — broader app/framework integrations are deferred.
- **Locale priority**: Brazilian sensitive data types must be first-class, not an afterthought — CPF, CNPJ, bank/account data, names, contact data, credentials, and environment variables are central.
- **Masking behavior**: v1 needs masking before submission, not deanonymization after the response — simpler privacy model and less key-management risk.
- **Safety default**: If a client surface cannot be safely rewritten, the tool should block rather than silently allow clear-text submission — avoids false confidence.
- **Data hygiene**: Real sensitive datasets and `.env` values must not be read into planning docs, tests, generated examples, or commits — synthetic fixtures only.
- **Current stack**: Python, Microsoft Presidio, spaCy Portuguese models, and lightweight hook scripts are already present — reuse them unless a phase proves a better boundary is needed.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Target terminal/IDE code-agent workflows first | The immediate risk is Claude/Codex-style agent usage, not arbitrary application traffic | Phase 3 validated Claude Code; Codex evidence remains active |
| Mask before external submission | The user wants safe outbound prompts rather than post-response restoration | — Pending |
| Do not require desmascaramento in v1 | Reduces key-management complexity and avoids storing reversible maps unnecessarily | — Pending |
| Treat Claude Code as the first concrete integration | The repo already has Claude hook configuration and guard scripts | Phase 3 validated strict Claude hook enforcement |
| Keep Codex/other IDE agents as compatibility targets | The user wants Claude/Codex coverage but the exact Codex interception surface still needs validation | — Pending |
| Favor fail-closed behavior where automatic masking cannot be guaranteed | The core value is zero clear-text leakage to external providers | Phase 3 blocks unsupported/unknown Claude surfaces and unsafe scrub mode |
| Bind external allow decisions to verified masked payloads | A local mask check alone is insufficient unless the authorized payload equals the verified masked text | Phase 2 policy core requires `payload_text == mask_result.text` for unknown/external allow |
| Keep the canonical CLI/package command name as `privguard` | Phase 1 locked the product name and Phase 6 removed legacy-name drift | Phase 6 removed the legacy console-script alias and synced PKG-02/ROADMAP wording |
| Gate optional Presidio extras per package on Python 3.14 | Current upstream metadata differs per dependency, so broad gating would make docs and installs stale | Phase 6 keeps analyzer-backed detection gated where needed while leaving supported dependencies installable |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-10 after Phase 7 completion*
