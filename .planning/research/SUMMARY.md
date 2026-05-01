# Project Research Summary

**Project:** Privacy Guard for LLM Code Agents
**Domain:** Local privacy/security guard for terminal and IDE LLM code-agent workflows
**Researched:** 2026-05-01
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project should become a local-first Python package and CLI that prevents Brazilian PII, credentials, environment values, dumps, and protected local files from reaching external LLM providers in clear text. The right shape is not a hosted proxy or a general Presidio demo; it is a developer-workflow safety layer around prompts, tool calls, local file access, and agent integrations. Experts build this kind of tool by separating fast enforcement paths from heavier analysis paths, proving enforcement with synthetic regression tests, and making unsupported client surfaces visibly block-only instead of advisory.

The recommended approach is to package the existing Presidio Brazilian recognizers and Claude hook scripts behind shared detector, masking, policy, and adapter contracts. Hooks should stay lightweight and standard-library friendly, using regex/checksum detection and path policy for low-latency fail-closed enforcement. Presidio, spaCy Portuguese models, and richer anonymization should live in the analysis/masking runtime used by CLI diagnostics, tests, and controlled masking flows where startup cost is acceptable.

The main risk is false confidence: claiming that data was masked when the integration can only warn, annotate, or block. The roadmap must therefore validate rewrite capability before shipping automatic masking for any client, default to blocking when rewrite is unproven, and test that raw sensitive values never appear in outbound payloads, stdout, stderr, logs, exceptions, fixtures, docs, or commits. Codex and IDE-agent support should be treated as compatibility research until their exact interception and rewrite surfaces are proven.

## Key Findings

### Recommended Stack

Use Python packaging with a `src/privacy_guard/` layout, a `privacy-guard` console script, and optional dependency extras. Keep broad dependency ranges in `pyproject.toml`, but generate a lock/constraints file for reproducibility. Target Python `>=3.10,<3.14`; the local interpreter may be newer, but Presidio/spaCy support should be treated as proven only through Python 3.13 until tests say otherwise.

**Core technologies:**
- Python package plus CLI: reusable local tool and integration entry points.
- `hatchling` or `setuptools`: build backend, with `hatchling` preferred for a clean new package.
- Microsoft Presidio Analyzer/Anonymizer `~=2.2`: rich PII detection and masking operators.
- spaCy `~=3.8` plus `pt_core_news_lg`: Portuguese NLP for Brazil-first detection quality.
- Standard-library hook runtime: fast, dependency-light Claude hook enforcement.
- Regex plus checksum validators: high-confidence detection for CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS, RG-like values, phone, CEP, plates, credit cards, secrets, and env patterns.
- `pytest`: assertion-based proof for blocking, masking, path policy, and output hygiene.
- `ruff`: lightweight lint and formatting.

Critical version decision: do not advertise Python 3.14 compatibility, and do not hide spaCy model downloads inside runtime code. Runtime should fail with a safe setup error if Presidio/spaCy/model dependencies are missing.

### Expected Features

**Must have (table stakes):**
- Automatic masking before external provider submission, but only where replacement is technically guaranteed.
- Fail-closed blocking when masking/rewrite cannot be proven.
- Brazil-first PII detection for CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS, RG, phone, CEP, vehicle plates, names, contact data, and bank/account-like patterns.
- Secret, environment, credential, dump, and API-key detection.
- Sensitive path protection for `.env`, `.env.*`, `data_sensivel/**`, dumps, credentials, secret-like names, and configured protected paths.
- Claude Code prompt and pre-tool guards as the first production integration.
- Safe output and logging: entity type, count, range, and reason codes only; no raw matches or snippets.
- Clear policy modes with strict/block as the default for external-provider paths.
- Synthetic regression tests proving no raw values leak through outputs or pass-through behavior.
- Package manifest, CLI, config, and reproducible dependency setup.

**Should have (differentiators):**
- Brazil-first recognizer quality suite with valid/invalid checksum matrices and overlap tests.
- Guard self-audit command for hook installation, config, protected paths, and safe-output status.
- Dry-run explain mode with sanitized findings.
- Shared detection contract across lightweight hooks and Presidio recognizers.
- CI-ready privacy test harness.
- Per-provider policy profiles and optional local-only routing once loopback restrictions are tested.
- IDE-agent compatibility matrix that distinguishes supported, experimental, and unsupported surfaces.

**Defer (v2+):**
- Hosted SaaS/cloud proxy.
- Universal LLM protection claims.
- Deanonymization and reversible token-map storage by default.
- Full LangChain/LlamaIndex-style framework adapters.
- Broad OS/network traffic interception.
- Advanced local LLM routing beyond a constrained optional fallback.

### Architecture Approach

Use a local package with a small CLI and thin adapters around shared privacy core modules. Every client event should become a normalized `GuardRequest`; every outcome should be a `GuardDecision` from a central policy engine. Detection and masking should be independent of client-specific hooks so Claude, future Codex/wrapper work, CLI diagnostics, and tests all use the same policy and fixture contract.

**Major components:**
1. Shared detector library: normalized detection results for PII, secrets, and sensitive paths.
2. Lightweight detector: standard-library regex/checksum scanner for hook paths.
3. Presidio detector: higher-recall Presidio/spaCy analyzer with custom Brazilian recognizers.
4. Masking engine: span resolution, typed replacements, full redaction for secrets, and post-mask verification.
5. Policy engine: `allow`, `rewrite`, `block`, `local_only`, and `diagnose` decisions based on mode, provider, client capability, tool intent, detection results, and path classification.
6. Hook adapters: Claude first; Codex/IDE later only after capability validation.
7. CLI diagnostics: scan, mask, explain policy, validate hooks, and doctor commands with safe output.
8. Tests/fixtures: synthetic-only proof for detectors, masking, policy, hooks, CLI, path normalization, failures, and output hygiene.

Key patterns: path policy before content policy; detect, mask, then verify; fail closed on unproven rewrite; keep hook adapters thin; never read protected files just to decide whether they are sensitive.

### Critical Pitfalls

1. **Raw values leak through logs, hook output, demos, or errors** — sanitize all output channels and test captured stdout/stderr/logs against exact synthetic values.
2. **False confidence from non-rewriting hooks** — classify client surfaces as rewrite-capable, block-only, observe-only, or unsupported; never call advisory output "masking".
3. **Regex/path/command bypasses** — normalize inputs, use checksum validators, deny protected path references broadly, and maintain a bypass corpus for PowerShell and common POSIX-like forms.
4. **Path normalization gaps expose protected files** — resolve canonical paths where safe, block ambiguous paths, and test Windows/POSIX separators, traversal, casing, quoted paths, and protected filename patterns.
5. **Real sensitive data enters tests, docs, planning, or commits** — synthetic fixtures only; never read `.env` or `data_sensivel` contents; add ignore and scanning gates.
6. **Dependency drift changes detection behavior** — add manifest, lockfile, model versioning, and regression tests before upgrades.
7. **Codex/IDE assumptions break the boundary** — validate actual outbound channels, hook lifecycle, rewrite semantics, telemetry/log behavior, and version-specific behavior before support claims.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Package Foundation and Safe Defaults
**Rationale:** Everything else depends on importable modules, reproducible installs, CLI entry points, and a clean split between examples and production code.
**Delivers:** `pyproject.toml`, `src/privacy_guard/`, console script skeleton, config defaults, optional extras, lock workflow, demos moved to `examples/`, initial `.gitignore`/package exclusions.
**Addresses:** dependency manifest, reusable local tool, safe default policy shape.
**Avoids:** dependency drift, demo/test naming confusion, import path mutation, generated cache/package noise.
**Research flag:** Standard pattern; skip deeper research unless packaging constraints emerge.

### Phase 2: Shared Detection Contract and Brazilian Validator Suite
**Rationale:** Hook and Presidio behavior must not drift. The core Brazil-first detection quality must be proven before enforcement grows.
**Delivers:** `DetectionResult` contract, shared validators, lightweight detector, synthetic fixture matrix, entity labels, overlap priority rules.
**Addresses:** Brazilian PII detection, secret/env pattern detection baseline, detector parity foundation.
**Avoids:** false negatives/positives, overlap suppression bugs, adapter-specific detector forks.
**Research flag:** Standard implementation, but include focused research only if checksum rules for a document type are uncertain.

### Phase 3: Policy, Path Protection, and Masking Engine
**Rationale:** Enforcement decisions belong in a central policy layer before adapters hard-code behavior. Path blocking must happen before content reads.
**Delivers:** policy modes, provider/client capability model, protected path classifier, masking engine, post-mask verification, safe diagnostics model.
**Addresses:** fail-closed blocking, sensitive path protection, automatic masking where guaranteed, safe output rules.
**Avoids:** reading sensitive files, raw diagnostics, unsafe permissive modes, mask verification failures.
**Research flag:** Standard pattern; no broad research needed, but test Windows path edge cases carefully.

### Phase 4: Claude Code Production Adapter
**Rationale:** Claude is the first concrete integration because hooks already exist and official hook blocking behavior is documented.
**Delivers:** `privacy-guard claude prompt`, `privacy-guard claude tool`, `validate-hooks`, JSON fixture harness, exit-code/structured-output tests, sanitized denial messages.
**Addresses:** Claude prompt guard, Claude pre-tool guard, protected file/tool blocking, output hygiene.
**Avoids:** "scrub" that does not rewrite, hook failures leaking raw values, command exfiltration through tools.
**Research flag:** Light research only to re-check current Claude hook rewrite/block semantics before implementing any rewrite claim.

### Phase 5: Presidio Runtime and CLI Diagnostics
**Rationale:** Rich analysis and masking can be added after the lightweight enforcement/policy contract exists, without burdening every hook invocation.
**Delivers:** Presidio detector adapter, custom Brazilian recognizers, anonymizer/masking CLI, `scan`, `mask`, `explain-policy`, `doctor`, spaCy model validation, safe setup errors.
**Addresses:** higher-recall Brazilian detection, local diagnostics, controlled masking flows, dependency/model validation.
**Avoids:** spaCy hook latency, runtime model-download surprises, raw demo output.
**Research flag:** Standard Presidio patterns are documented; use phase research only for specific recognizer/operator behavior or spaCy model tradeoffs.

### Phase 6: Codex and IDE Compatibility Investigation
**Rationale:** Codex/IDE support cannot be promised until actual interception, rewrite, logging, telemetry, and tool coverage are verified for the installed versions.
**Delivers:** compatibility matrix, fake-provider capture tests if feasible, support-level labels, decision on hooks vs wrapper vs unsupported/advisory mode.
**Addresses:** Codex compatibility target and future IDE-agent support without false claims.
**Avoids:** provider/client integration assumptions, unsupported surfaces leaking context, universal protection claims.
**Research flag:** Needs deeper `/gsd-research-phase`; public and implementation behavior may change.

### Phase 7: Local-Only Routing and Optional Advanced Controls
**Rationale:** Local routing is useful only after provider classification and fail-closed policy are reliable.
**Delivers:** optional loopback-only provider profile, local endpoint allowlist, privacy-safe errors, future CI/self-audit improvements.
**Addresses:** workflow continuity when external submission is blocked.
**Avoids:** treating local LLM routing as universal safety, prompt leakage through endpoint logs or non-local services.
**Research flag:** Needs targeted research if any non-loopback endpoint, daemon, enterprise policy distribution, or reversible workflow is considered.

### Phase Ordering Rationale

- Package and tests come first because current code is demo-oriented and cannot support reliable privacy claims without importable modules and automated assertions.
- Detection/validator work precedes masking/enforcement so all adapters share one Brazil-first contract.
- Policy/path/masking precedes Claude adapter hardening so enforcement decisions are centralized and testable.
- Claude ships before Codex because Claude hook blocking is already concrete; Codex remains an evidence-gathering phase.
- Presidio analysis is separated from hook enforcement to avoid spaCy startup latency and hook fragility.
- Local-only routing and reversible workflows stay late because they introduce extra boundary and key-management risk.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4:** only for current Claude rewrite semantics if masking, not just blocking, is proposed.
- **Phase 6:** Codex/IDE compatibility, because hook coverage and rewrite guarantees are not yet stable enough to assume.
- **Phase 7:** local routing or reversible/key-management work, if it expands beyond loopback-only optional behavior.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Python packaging, CLI entry points, extras, and test/lint setup.
- **Phase 2:** shared contracts, validators, synthetic fixtures, and unit tests.
- **Phase 3:** central policy engine, path classifier, masking result objects, and output-safety tests.
- **Phase 5:** Presidio recognizers and anonymizer integration, unless a specific operator/model decision is unresolved.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Python/Presidio/spaCy/Claude hook direction is well supported, but exact dependency pins and Python 3.14 compatibility need tests. |
| Features | HIGH | Table stakes align strongly across project goals, codebase maps, and privacy failure modes. Codex support remains medium confidence. |
| Architecture | MEDIUM-HIGH | Shared detector/masking/policy/adapter shape is coherent and matches current code boundaries; exact rewrite-capable adapters need validation. |
| Pitfalls | HIGH | Raw-output leaks, path bypasses, command exfiltration, fixture hygiene, and dependency drift are directly supported by project context and codebase concerns. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Claude rewrite capability:** verify whether any prompt/tool payload can be atomically replaced before provider submission; otherwise ship block-only for sensitive content.
- **Codex interception surface:** validate installed Codex version, hook/event support, Windows behavior, tool coverage, MCP/IDE paths, logs, and telemetry before support claims.
- **Exact dependency pins:** run compatibility tests for Presidio analyzer/anonymizer, spaCy, model version, and `cryptography` before locking.
- **False-positive policy balance:** define strict/balanced/diagnostic semantics early and keep strict defaults for credentials, protected paths, and high-confidence Brazilian identifiers.
- **Path normalization depth:** decide how far v1 resolves symlinks/junctions/UNC/short paths from hook contexts; deny ambiguous paths until proven safe.
- **Reversible workflows:** keep out of v1 unless a later phase defines key storage, retention, authority, and no-raw-output guarantees.

## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md` — project goals, constraints, active requirements, out-of-scope boundaries, and key decisions.
- `.planning/research/STACK.md` — recommended Python/Presidio/spaCy/hook stack, packaging, dependency strategy, and integration status.
- `.planning/research/FEATURES.md` — table stakes, differentiators, anti-features, dependencies, and v1 acceptance signals.
- `.planning/research/ARCHITECTURE.md` — component boundaries, data flow, adapter contract, policy model, and test architecture.
- `.planning/research/PITFALLS.md` — critical/moderate/minor pitfalls and phase-specific warnings.
- Microsoft Presidio docs — analyzer, recognizer, anonymizer, operators, and installation behavior.
- Claude Code hooks reference — prompt/tool hook timing and block behavior.

### Secondary (MEDIUM confidence)
- OpenAI Codex CLI docs and repository/issues — useful signals for Codex compatibility, but not yet enough for v1 enforcement claims.
- Existing codebase maps under `.planning/codebase/` — current architecture, stack, integrations, concerns, structure, and testing gaps.

---
*Research completed: 2026-05-01*
*Ready for roadmap: yes*
