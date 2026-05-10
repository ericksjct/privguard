# Phase 02: Privacy Core - Research

**Researched:** 2026-05-02 [VERIFIED: system date]  
**Domain:** Local privacy detection, irreversible masking, policy decisions, and sanitized diagnostics for Python CLI/hook consumers. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]  
**Confidence:** HIGH for existing-code direction, MEDIUM for SafeSend reuse because source inspection was partial. [VERIFIED: local file audit] [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/]

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
Phase 2 delivers the shared privacy core used by CLI commands and supported client integrations:
Brazil-first sensitive-data detection, irreversible masking, protected-path classification,
fail-closed policy decisions, and sanitized diagnostics. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]

- The product should expose one complete detection experience, not user-facing "light" and "full" operating modes. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Phase 2 should cover Brazilian identifiers, contact data, secret-like values, and protected path strings from the v1 requirements. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Internal implementation may use multiple detector components, but normal v1 operation must not require user detection-mode choices. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Masking is irreversible for v1 and must not require or persist deanonymization maps. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Masked output must be verified so original sensitive substrings or suspicious leftovers are not still present. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- If incomplete masking is detected, the system must pause and offer continue manually, retry masking, or block. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- External-provider workflows default to fail-closed. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Unknown, unclassified, or external-provider surfaces are unsafe by default. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Phase 2 should define capability labels: rewrite-capable, block-only, observe-only, unsupported, unknown, and external. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Rewrite-capable surfaces may allow masked content only after verification; block-only surfaces block on sensitive data; observe-only and unsupported clients must not be represented as automatic protection. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Diagnostics must support human-readable and JSON formats and must be sanitized. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Diagnostics may include entity type, counts, offsets, confidence scores, reason codes, policy decision, and surface capability. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Diagnostics must not include raw matched values, original prompt snippets, protected file contents, secret-looking strings, or unmasked sensitive paths beyond safe reason categories. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]

### Claude's Discretion
- The planner may decide the exact Python API shape for detector results, masking verification results, policy decisions, and diagnostic serializers. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- The planner may decide whether Presidio-backed detection is implemented in this phase or exposed behind an internal adapter, as long as the user-facing behavior remains one complete detection contract. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]

### Deferred Ideas (OUT OF SCOPE)
- Claude-specific enforcement details belong to Phase 3. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Codex interception evidence and support labels belong to Phase 4. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Additional IDE-agent, LangChain, LlamaIndex, local proxy, and enterprise policy distribution remain v2 work unless a later phase explicitly promotes them. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DET-01 | Detect synthetic CPF values with checksum validation. [VERIFIED: .planning/REQUIREMENTS.md] | Reuse `valida_cpf()` and add numeric/format parity fixtures. [VERIFIED: privguard/detection.py] |
| DET-02 | Detect synthetic CNPJ values with checksum validation. [VERIFIED: .planning/REQUIREMENTS.md] | Reuse `valida_cnpj()` and add numeric/format parity fixtures. [VERIFIED: privguard/detection.py] |
| DET-03 | Detect CNH, voter title, PIS/PASEP, SUS, RG-like values, phones, CEP, and plates. [VERIFIED: .planning/REQUIREMENTS.md] | Port missing validators from `demos/test_presidio_br.py` into package code and keep demo raw-output behavior out. [VERIFIED: demos/test_presidio_br.py] |
| DET-04 | Detect API keys, tokens, passwords, database URLs, and env assignments. [VERIFIED: .planning/REQUIREMENTS.md] | Extend `PATTERNS` with secret categories and classify by type/reason, not value. [VERIFIED: privguard/detection.py] |
| DET-05 | Classify protected paths without reading file contents. [VERIFIED: .planning/REQUIREMENTS.md] | Expand `is_sensitive_path()` into normalized protected-path classification with reason codes. [VERIFIED: privguard/policy.py] |
| DET-06 | Lightweight and Presidio-backed detection share validator semantics and synthetic fixtures. [VERIFIED: .planning/REQUIREMENTS.md] | Make package validators canonical; Presidio recognizers should call the same validators if added. [VERIFIED: demos/test_presidio_br.py] |
| MASK-01 | Replace detected values with typed placeholders before external-provider submission. [VERIFIED: .planning/REQUIREMENTS.md] | Evolve `redact()` into a masking result API that carries placeholder output and sanitized metadata. [VERIFIED: privguard/masking.py] |
| MASK-02 | Verify masked output does not contain original synthetic sensitive substrings. [VERIFIED: .planning/REQUIREMENTS.md] | Add post-mask verification over original hit values plus residual detection. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |
| MASK-03 | Use irreversible masking and no deanonymization maps. [VERIFIED: .planning/REQUIREMENTS.md] | Use typed placeholders like `<BR_CPF>` and do not persist mapping state. [VERIFIED: privguard/masking.py] |
| MASK-04 | Block when a client surface cannot prove outbound payload replacement. [VERIFIED: .planning/REQUIREMENTS.md] | Policy should combine surface capability, detection result, masking status, and verification status. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |
| POL-01 | Expose explicit policy modes with strict/fail-closed default. [VERIFIED: .planning/REQUIREMENTS.md] | Define strict default decisions in package policy, not hook-only env parsing. [VERIFIED: privguard/hooks.py] |
| POL-02 | Distinguish rewrite-capable, block-only, observe-only, and unsupported surfaces. [VERIFIED: .planning/REQUIREMENTS.md] | Add surface capability enum/labels consumed later by Claude and Codex phases. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |
| POL-03 | Treat unknown/unclassified provider targets as external and require masking or blocking. [VERIFIED: .planning/REQUIREMENTS.md] | Make `unknown` and `external` fail-closed unless verified masked output exists. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |
| POL-04 | Emit only sanitized decisions and diagnostics. [VERIFIED: .planning/REQUIREMENTS.md] | Add JSON and text serializers from sanitized summary records only. [VERIFIED: privguard/policy.py] |
</phase_requirements>

## Summary

Phase 2 should convert the Phase 1 package modules from helper functions into a small core contract: `detect` returns sanitized-capable spans, `mask` returns irreversible placeholder text plus verification status, `classify_path` returns protected-path categories without reading files, and `decide_policy` applies fail-closed surface rules. [VERIFIED: privguard/detection.py] [VERIFIED: privguard/masking.py] [VERIFIED: privguard/policy.py] [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]

The production hot path should remain stdlib-only because `pyproject.toml` has no required runtime dependencies and marks Presidio/spaCy as optional `full` dependencies, while the installed environment currently has Python 3.14.3 and package versions that do not exactly match the optional pins. [VERIFIED: pyproject.toml] [VERIFIED: `python --version`] [VERIFIED: `python -m pip show presidio-analyzer presidio-anonymizer spacy`] Presidio remains useful as an optional parity/reference adapter because its official docs describe extensible recognizers, `PatternRecognizer`, `AnalyzerEngine`, and anonymizer replace/redact/mask operators. [CITED: https://microsoft.github.io/presidio/analyzer/] [CITED: https://microsoft.github.io/presidio/anonymizer/]

**Primary recommendation:** Plan Phase 2 around a dependency-light package core with canonical Brazilian validators, typed immutable-ish result objects, post-mask verification, strict policy decisions, and sanitized serializers; treat SafeSend and Presidio as pattern references, not copied production code. [VERIFIED: local code audit] [CITED: https://microsoft.github.io/presidio/analyzer/developing_recognizers/] [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Text/entity detection | Local Python package core | Optional Presidio adapter | CLI and hooks need the same local detector contract; Presidio can validate parity when installed. [VERIFIED: privguard/detection.py] [VERIFIED: pyproject.toml] |
| Irreversible masking | Local Python package core | CLI/hook adapters | Masking must happen locally before any external-provider boundary. [VERIFIED: .planning/REQUIREMENTS.md] |
| Protected-path classification | Local Python package core | Hook adapters | Path classification must avoid reading protected files and should be reusable by CLI, Claude, and future compatibility docs. [VERIFIED: privguard/policy.py] |
| Policy decisions | Local Python package core | Client adapters | Fail-closed behavior depends on surface capability and verification status, so it belongs below specific integrations. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |
| Diagnostics serialization | Local Python package core | CLI/hook format selection | Text and JSON outputs must be sanitized consistently across consumers. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |

## Implementation Approach

Use `privguard.detection` as the canonical detector module and expand it rather than creating separate "light" and "full" public modes. [VERIFIED: privguard/detection.py] [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] Keep `Hit.value` internal for masking, but never expose it through diagnostics. [VERIFIED: .planning/STATE.md] [VERIFIED: privguard/policy.py]

Recommended package API shape for planning: [ASSUMED]

| Function/Object | Purpose | Planning Notes |
|-----------------|---------|----------------|
| `DetectionHit` or evolved `Hit` | Internal span with `kind`, `start`, `end`, `value`, `score`, `reason_code`, `source`. [VERIFIED: privguard/detection.py] [ASSUMED] | Keep `value` available only inside masking/verification. [VERIFIED: .planning/STATE.md] |
| `DetectionReport` | Aggregate hits, counts, and sanitized summaries. [ASSUMED] | Prevent serializers from touching raw values. [VERIFIED: .planning/REQUIREMENTS.md] |
| `MaskResult` | `text`, `changed`, `verified`, `verification_status`, `reason_codes`, sanitized hit summaries. [ASSUMED] | Needed for MASK-02 and policy decisions. [VERIFIED: .planning/REQUIREMENTS.md] |
| `PathClassification` | `is_protected`, `category`, `reason_code`, sanitized display label. [ASSUMED] | Needed for DET-05 without reading contents. [VERIFIED: privguard/policy.py] |
| `SurfaceCapability` | `rewrite_capable`, `block_only`, `observe_only`, `unsupported`, `unknown`, `external`. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] | Use enum-like constants to avoid string drift. [ASSUMED] |
| `PolicyDecision` | `allow`, `block`, `pause`, `retry_suggested`, plus sanitized reason codes. [ASSUMED] | Encodes fail-closed and incomplete-mask pause behavior. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |

Detection should run deterministic regex/checksum recognizers first and should not depend on network, external services, `.env`, or `data_sensivel` contents. [VERIFIED: privguard/detection.py] [VERIFIED: AGENTS.md] [VERIFIED: .planning/REQUIREMENTS.md] Port `valida_cnh`, `valida_titulo_eleitor`, `valida_pis`, and `valida_cartao_sus` from `demos/test_presidio_br.py` into the package so lightweight and optional Presidio recognizers can call one validator source. [VERIFIED: demos/test_presidio_br.py] [VERIFIED: .planning/REQUIREMENTS.md]

Masking should sort accepted, non-overlapping hits by span and replace each with typed placeholders. [VERIFIED: privguard/masking.py] [VERIFIED: privguard/detection.py] Verification should check that no original hit value remains in masked output and should re-run detection on the masked output to catch suspicious leftovers; failures should return a pause/block-oriented result instead of silently allowing continuation. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] [ASSUMED]

Policy should be package-owned rather than hook-owned because Phase 3 and Phase 4 depend on shared semantics. [VERIFIED: .planning/ROADMAP.md] Current `privguard.hooks` contains policy-like mode parsing and redacted output construction, so Phase 2 should move decision and diagnostics construction into reusable package functions and leave hooks as thin adapters later. [VERIFIED: privguard/hooks.py]

## SafeSend Lessons / Reuse Assessment

Direct source inspection of `https://github.com/abdulrmanfz0-glitch/safesend` and raw GitHub files was not available in this environment; earlier local shell fetches reportedly failed with SSL errors, and web/raw fetches here returned no inspectable source. [VERIFIED: web open attempts] Therefore, SafeSend code reuse is **partial/LOW confidence** and should be limited to product patterns unless a planner/executor can inspect the repository locally. [VERIFIED: web open attempts]

Reusable lessons from public SafeSend descriptions: [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/] [CITED: https://www.reddit.com/r/vibecoding/comments/1syszto/i_built_a_small_tool_in_2_hours_a_contributor/]

| SafeSend Pattern | Reuse for privguard? | Assessment |
|------------------|----------------------|------------|
| Browser/local-only processing with zero servers/accounts/telemetry claim. [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/] | Yes, as product principle. | Matches privguard's local privacy boundary. [VERIFIED: AGENTS.md] |
| Typed placeholders such as `[NAME_1]` and `[PHONE_1]`. [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/] | Yes, adapted as irreversible `<ENTITY>` or counted placeholders. | Privguard v1 should not restore originals, so do not copy round-trip mapping behavior. [VERIFIED: .planning/REQUIREMENTS.md] |
| Round-trip restoration. [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/] | No for v1. | Deanonymization is explicitly out of scope. [VERIFIED: .planning/REQUIREMENTS.md] |
| Locally learned custom terms. [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/] | Defer. | Project-specific learned terms imply persistence and policy distribution, which are v2/enterprise-adjacent. [VERIFIED: .planning/REQUIREMENTS.md] |
| Large-file performance improvements and security feedback from contributors. [CITED: https://www.reddit.com/r/vibecoding/comments/1syszto/i_built_a_small_tool_in_2_hours_a_contributor/] | Yes, as a planning warning. | Phase 2 should test bounded text sizes and avoid catastrophic regex behavior. [ASSUMED] |
| Broad multilingual detection. [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/] | Not for Phase 2. | Privguard v1 prioritizes Brazilian identifiers and terminal/IDE workflows. [VERIFIED: AGENTS.md] |

Do not copy SafeSend code into privguard until the MIT license, repository contents, tests, and implementation quality are directly inspected. [ASSUMED] The safer reuse path is to borrow the UX idea of clear placeholders, local-only execution, and explicit user decision points after incomplete masking. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/]

## Existing Code Reuse

| Existing Code | Reuse | Gap to Plan |
|---------------|-------|-------------|
| `privguard.detection.Hit`, `_digits`, `valida_cpf`, `valida_cnpj`, `valida_luhn`, `detect`. [VERIFIED: privguard/detection.py] | Keep and evolve. | Add missing Brazilian validators, reason codes, numeric-format coverage, secret/env/database URL patterns, and fixture parity. [VERIFIED: .planning/REQUIREMENTS.md] |
| `privguard.detection.PATTERNS`. [VERIFIED: privguard/detection.py] | Keep as initial detector registry. | Consider richer `PatternEntry` dataclass for readability and source metadata. [ASSUMED] |
| Overlap handling in `detect`. [VERIFIED: privguard/detection.py] | Keep core behavior. | Add tests for equal scores, nested spans, and invalid checksum candidates. [VERIFIED: .planning/REQUIREMENTS.md] |
| `privguard.masking.redact`. [VERIFIED: privguard/masking.py] | Keep as primitive. | Wrap with `mask_text()` returning `MaskResult` and `verify_mask()`. [ASSUMED] |
| `privguard.policy.is_sensitive_path`. [VERIFIED: privguard/policy.py] | Keep concept. | Expand normalization and return categories/reason codes for `.env`, dumps, credentials, and secret-like filenames. [VERIFIED: .planning/REQUIREMENTS.md] |
| `summarize_hits` and `format_hit_summary`. [VERIFIED: privguard/policy.py] | Keep sanitized summary pattern. | Move/extend into diagnostics serializers for JSON and text. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |
| `privguard.hooks`. [VERIFIED: privguard/hooks.py] | Use as adapter proof only. | Current hook output includes redacted text in diagnostics; Phase 2 must decide whether redacted payload belongs in diagnostics or only in explicit mask output. [VERIFIED: privguard/hooks.py] [ASSUMED] |
| `demos/test_presidio_br.py`. [VERIFIED: demos/test_presidio_br.py] | Use validators/recognizer semantics as reference. | Do not restore raw demo input/output behavior. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | Python 3.14.3 installed; package supports `>=3.10`. [VERIFIED: `python --version`] [VERIFIED: pyproject.toml] | Regex, dataclasses, argparse, JSON, pathlib-style path classification. [VERIFIED: privguard/detection.py] [VERIFIED: privguard/policy.py] | Keeps hook/CLI privacy core local, fast, and dependency-light. [VERIFIED: pyproject.toml] |
| `privguard` package modules | 0.1.0. [VERIFIED: pyproject.toml] | Detection, masking, policy, CLI, hook adapters. [VERIFIED: pyproject.toml] [VERIFIED: privguard/*.py] | Existing Phase 1 package foundation already extracted these modules. [VERIFIED: .planning/STATE.md] |

### Optional / Reference

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `presidio-analyzer` | Optional pin 2.2.362 for Python `<3.14`; locally installed 2.2.359. [VERIFIED: pyproject.toml] [VERIFIED: `python -m pip show presidio-analyzer`] | Optional Presidio-backed recognizer parity. [CITED: https://microsoft.github.io/presidio/analyzer/] | Use only when installed and compatible; do not make it required for hooks. [VERIFIED: pyproject.toml] |
| `presidio-anonymizer` | Optional pin 2.2.362; locally installed 2.2.362. [VERIFIED: pyproject.toml] [VERIFIED: `python -m pip show presidio-anonymizer`] | Reference anonymization operators. [CITED: https://microsoft.github.io/presidio/anonymizer/] | Phase 2 can avoid it for production masking because simple irreversible replacement is already implemented. [VERIFIED: privguard/masking.py] |
| `spacy` | Optional pin 3.8.14; locally installed 3.8.13. [VERIFIED: pyproject.toml] [VERIFIED: `python -m pip show spacy`] | Presidio NLP backend for Portuguese models. [CITED: https://microsoft.github.io/presidio/analyzer/] | Use only in optional full/parity tests, not strict hot path. [VERIFIED: pyproject.toml] |
| `pytest` | Locally installed 9.0.2. [VERIFIED: `python -m pytest --version`] | Synthetic regression tests. [VERIFIED: local command] | Add tests in Phase 2 even though Nyquist validation is disabled. [VERIFIED: .planning/config.json] |

**Installation:** no new required runtime packages are needed for the Phase 2 core. [VERIFIED: pyproject.toml] Optional parity remains `pip install -e .[full]` on compatible Python versions. [VERIFIED: pyproject.toml]

## Architecture Patterns

### System Architecture Diagram

```text
Input text/path/surface metadata
        |
        v
Local detection and path classification
        |
        +--> no findings ----------------------+
        |                                      |
        v                                      v
Findings with internal raw spans       Surface policy evaluation
        |                                      |
        v                                      v
Irreversible local masking             Allow/block decision
        |
        v
Post-mask verification
        |
        +--> verified + rewrite-capable surface --> allow masked payload
        |
        +--> incomplete/unknown/block-only/external --> pause or block
        |
        v
Sanitized diagnostics (text or JSON)
```

This data flow keeps raw sensitive values local and only allows sanitized diagnostics across user-visible outputs. [VERIFIED: AGENTS.md] [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]

### Recommended Project Structure

```text
privguard/
├── detection.py      # canonical regex/checksum detection and shared validators
├── masking.py        # irreversible placeholders plus verification result
├── policy.py         # protected paths, surface capabilities, fail-closed decisions
├── diagnostics.py    # sanitized JSON/text serializers if policy.py gets too broad
├── hooks.py          # thin adapter, later Phase 3 hardening
└── cli.py            # scan/mask/policy diagnostics commands
tests/
├── test_detection.py
├── test_masking.py
├── test_policy.py
└── test_diagnostics.py
```

Adding `diagnostics.py` is optional, but it will likely keep `policy.py` from mixing classification and serialization. [ASSUMED]

### Pattern 1: Canonical Validators Shared by All Detectors

**What:** Keep checksum validators in package code and call them from regex detection and any optional Presidio recognizers. [VERIFIED: privguard/detection.py] [VERIFIED: demos/test_presidio_br.py]  
**When to use:** CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS, credit cards, and any structured identifier where checksum validation reduces false positives. [VERIFIED: demos/test_presidio_br.py]  
**Why:** Presidio docs state recognizers can combine regex, context, validation, and custom logic; using package validators avoids drift. [CITED: https://microsoft.github.io/presidio/analyzer/] [CITED: https://microsoft.github.io/presidio/analyzer/developing_recognizers/]

### Pattern 2: Internal Raw Values, External Sanitized Summaries

**What:** Keep raw `value` only on internal hit objects used by masking and verification; serializers consume summaries with kind/start/end/score/reason only. [VERIFIED: privguard/detection.py] [VERIFIED: privguard/policy.py]  
**When to use:** All CLI diagnostics, hook messages, JSON outputs, exceptions, and test failure messages. [VERIFIED: .planning/REQUIREMENTS.md]  
**Why:** The project explicitly forbids raw matched values and prompt snippets in diagnostics. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]

### Pattern 3: Fail-Closed Decision Function

**What:** Compute policy from `(surface_capability, detection_report, mask_result, target_kind)` and return a structured decision. [ASSUMED]  
**When to use:** Before any client adapter allows outbound content to an external or unknown provider. [VERIFIED: .planning/REQUIREMENTS.md]  
**Why:** Unknown and external targets must require verified masking or blocking. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]

### Anti-Patterns to Avoid

- **User-facing detector modes:** conflicts with the locked one-complete-detection decision. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- **Diagnostics built from original text:** violates POL-04 and makes tests harder to keep leak-free. [VERIFIED: .planning/REQUIREMENTS.md]
- **Reading protected paths to classify them:** DET-05 requires path classification without file reads. [VERIFIED: .planning/REQUIREMENTS.md]
- **Using Presidio as mandatory hook runtime:** optional dependency pins and local Python 3.14 compatibility make this risky for core enforcement. [VERIFIED: pyproject.toml] [VERIFIED: `python --version`]
- **Reversible maps or SafeSend-style restoration:** v1 explicitly excludes deanonymization after LLM responses. [VERIFIED: .planning/REQUIREMENTS.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Brazilian checksum algorithms already present in demos | New unverified formulas | Port existing `demos/test_presidio_br.py` validators into package and test them. [VERIFIED: demos/test_presidio_br.py] | Prevent validator drift. [VERIFIED: .planning/REQUIREMENTS.md] |
| Optional NLP/NER recognizer architecture | Custom ML/NER framework | Presidio optional adapter if needed. [CITED: https://microsoft.github.io/presidio/analyzer/] | Presidio already supports custom recognizers and NLP engines. [CITED: https://microsoft.github.io/presidio/analyzer/] |
| Text anonymization operators beyond simple replacement | New encryption/decryption/pseudonymization layer | Existing `redact()` plus typed placeholders for v1. [VERIFIED: privguard/masking.py] | Reversible behavior is out of scope. [VERIFIED: .planning/REQUIREMENTS.md] |
| CLI JSON serialization by string concatenation | Ad hoc JSON text | Python `json` on sanitized dicts. [VERIFIED: privguard/hooks.py] | Prevent accidental raw snippets and malformed output. [VERIFIED: .planning/REQUIREMENTS.md] |
| Path classification by file IO | Opening `.env`, dumps, or `data_sensivel` | Normalize path strings and match configured protected categories. [VERIFIED: privguard/policy.py] | Project forbids reading protected contents in planning/tests/examples. [VERIFIED: AGENTS.md] |

## Common Pitfalls

### Pitfall 1: Sanitized Diagnostics Still Leak Masked Payloads
**What goes wrong:** Hook or CLI output includes `redacted=<masked text>`, which may still reveal surrounding proprietary context. [VERIFIED: privguard/hooks.py]  
**How to avoid:** Separate "mask output" commands from "diagnostic output"; diagnostics default to counts, spans, types, and reason codes only. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] [ASSUMED]

### Pitfall 2: Regex-Only Identifiers Inflate False Positives
**What goes wrong:** CNH, voter title, PIS/PASEP, SUS, cards, and CPF/CNPJ-like numbers are detected without checksum validation. [VERIFIED: demos/test_presidio_br.py]  
**How to avoid:** Use validators for structured IDs and tests for invalid lookalikes. [VERIFIED: .planning/REQUIREMENTS.md]

### Pitfall 3: Optional Full Stack Becomes Required Accidentally
**What goes wrong:** A hook path imports Presidio/spaCy and fails on Python/version/model availability. [VERIFIED: pyproject.toml] [VERIFIED: `python -m pip show presidio-analyzer spacy`]  
**How to avoid:** Keep imports lazy and optional; the default `privguard` package core should work with stdlib only. [VERIFIED: pyproject.toml] [ASSUMED]

### Pitfall 4: Incomplete Masking Allows External Submission
**What goes wrong:** Masking returns text but no verifier checks original substrings or residual detections. [VERIFIED: privguard/masking.py]  
**How to avoid:** Add verification status and make policy pause/block on failure. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]

### Pitfall 5: Protected Paths Are Treated as Text PII Only
**What goes wrong:** `.env` or sensitive dataset paths are missed unless their contents are scanned. [VERIFIED: privguard/policy.py]  
**How to avoid:** Classify path strings as protected independently of text PII detection. [VERIFIED: .planning/REQUIREMENTS.md]

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Secret regexes miss common key formats. [ASSUMED] | HIGH | Add fixtures for API keys, tokens, password/env assignments, and database URLs using fake values only. [VERIFIED: .planning/REQUIREMENTS.md] |
| Overlap handling masks a lower-risk span and leaves a higher-risk span. [ASSUMED] | HIGH | Test nested/equal/partial overlaps and prefer higher confidence, then longer span. [CITED: https://microsoft.github.io/presidio/anonymizer/] |
| CLI command name mismatch: requirements mention `privacy-guard`, while `pyproject.toml` exposes `privguard`. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: pyproject.toml] | MEDIUM | Planner should decide whether Phase 2 adds aliases or leaves packaging naming to a follow-up. [ASSUMED] |
| Presidio optional versions differ from local install and current latest release. [VERIFIED: pyproject.toml] [VERIFIED: `python -m pip show presidio-analyzer`] [CITED: https://github.com/microsoft/presidio] | MEDIUM | Keep Presidio optional; use package validators as source of truth. [ASSUMED] |
| SafeSend implementation may contain useful code but was not inspectable. [VERIFIED: web open attempts] | LOW | Revisit source in execution only if fetch succeeds; do not depend on it for Phase 2. [ASSUMED] |

## Validation Architecture / Test Strategy

Nyquist validation is explicitly disabled in `.planning/config.json`, so the formal GSD validation section is skipped. [VERIFIED: .planning/config.json] Phase 2 still needs automated tests because its requirements are privacy-sensitive and Phase 5 depends on synthetic regression coverage. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/ROADMAP.md]

| Property | Value |
|----------|-------|
| Test framework | `pytest` 9.0.2 is installed locally. [VERIFIED: `python -m pytest --version`] |
| Existing test files | No `tests/` directory; only demo files named `demos/test_presidio*.py` were found. [VERIFIED: `rg --files -g "*test*" ...`] |
| Quick run command | `python -m pytest tests/test_detection.py tests/test_masking.py tests/test_policy.py -q` [ASSUMED] |
| Full phase command | `python -m pytest -q` after adding tests. [ASSUMED] |

Required test groups:

| Requirement Area | Tests to Add |
|------------------|--------------|
| DET-01/DET-02 | Valid and invalid synthetic CPF/CNPJ, formatted and numeric if supported. [VERIFIED: .planning/REQUIREMENTS.md] |
| DET-03 | CNH, voter title, PIS/PASEP, SUS, RG-like, phone, CEP, old/Mercosul plates, plus invalid lookalikes. [VERIFIED: .planning/REQUIREMENTS.md] |
| DET-04 | Fake API key, token, password assignment, database URL, env var assignment, and non-secret lookalikes. [VERIFIED: .planning/REQUIREMENTS.md] |
| DET-05 | Windows paths, mixed separators, relative traversal, quoted paths, `.env.*`, dumps, credential-like filenames, `data_sensivel/**`; never read file contents. [VERIFIED: .planning/REQUIREMENTS.md] |
| DET-06 | Same synthetic fixtures pass package validators and optional Presidio recognizers when full dependencies are available. [VERIFIED: .planning/REQUIREMENTS.md] |
| MASK-01/MASK-03 | Typed placeholders replace spans and no deanonymization map is returned or persisted. [VERIFIED: .planning/REQUIREMENTS.md] |
| MASK-02/MASK-04 | Verification fails if any original synthetic hit value remains; policy blocks or pauses on verification failure. [VERIFIED: .planning/REQUIREMENTS.md] |
| POL-01/POL-03 | Strict default blocks unknown/external/unmasked sensitive payloads. [VERIFIED: .planning/REQUIREMENTS.md] |
| POL-02 | Capability labels produce expected allow/block/pause decisions. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |
| POL-04 | JSON/text diagnostics contain only type/count/span/score/reason/capability/decision fields. [VERIFIED: .planning/REQUIREMENTS.md] |

Add a leak assertion helper that fails if any raw synthetic fixture appears in stdout, stderr, diagnostic JSON, exception text, or masked output. [VERIFIED: .planning/REQUIREMENTS.md] Keep all fixtures synthetic and never read `.env` or `data_sensivel`. [VERIFIED: AGENTS.md]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Package core and CLI | Yes [VERIFIED: `python --version`] | 3.14.3 [VERIFIED: `python --version`] | None needed |
| pytest | Phase 2 tests | Yes [VERIFIED: `python -m pytest --version`] | 9.0.2 [VERIFIED: `python -m pytest --version`] | Add test dependency if packaging requires reproducibility. [ASSUMED] |
| Presidio Analyzer | Optional parity adapter | Yes locally, optional by package [VERIFIED: `python -m pip show presidio-analyzer`] [VERIFIED: pyproject.toml] | 2.2.359 local; 2.2.362 latest release cited. [VERIFIED: local pip] [CITED: https://github.com/microsoft/presidio] | Skip optional parity on incompatible env. [ASSUMED] |
| Presidio Anonymizer | Optional reference | Yes locally [VERIFIED: `python -m pip show presidio-anonymizer`] | 2.2.362 [VERIFIED: local pip] | Use stdlib `redact()` for v1. [VERIFIED: privguard/masking.py] |
| spaCy | Optional Presidio NLP | Yes locally [VERIFIED: `python -m pip show spacy`] | 3.8.13 [VERIFIED: local pip] | Keep optional; do not import on default path. [ASSUMED] |

**Missing dependencies with no fallback:** none for the stdlib Phase 2 core. [VERIFIED: pyproject.toml]  
**Missing dependencies with fallback:** exact optional `full` versions are not all matched locally; fallback is the stdlib detector/masker. [VERIFIED: pyproject.toml] [VERIFIED: local pip]

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | No for Phase 2 core. [VERIFIED: .planning/ROADMAP.md] | No user auth surface in this phase. [VERIFIED: .planning/ROADMAP.md] |
| V3 Session Management | No for Phase 2 core. [VERIFIED: .planning/ROADMAP.md] | No sessions in package core. [VERIFIED: local code audit] |
| V4 Access Control | Yes for local protected-path policy. [VERIFIED: .planning/REQUIREMENTS.md] | Fail-closed protected-path classification and surface capability decisions. [VERIFIED: .planning/REQUIREMENTS.md] |
| V5 Input Validation | Yes. [VERIFIED: .planning/REQUIREMENTS.md] | Regex plus checksum validators and sanitized serializers. [VERIFIED: privguard/detection.py] |
| V6 Cryptography | No for v1 masking. [VERIFIED: .planning/REQUIREMENTS.md] | Do not add encryption/decryption maps in Phase 2. [VERIFIED: .planning/REQUIREMENTS.md] |

Known threat patterns:

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Clear-text sensitive value in outbound prompt/tool payload. [VERIFIED: AGENTS.md] | Information Disclosure | Local detection, masking, verification, fail-closed policy. [VERIFIED: .planning/REQUIREMENTS.md] |
| Diagnostic leak through logs/JSON/errors. [VERIFIED: .planning/REQUIREMENTS.md] | Information Disclosure | Serialize sanitized summaries only. [VERIFIED: privguard/policy.py] |
| Protected-file exfiltration by path reference. [VERIFIED: .planning/REQUIREMENTS.md] | Information Disclosure | Classify protected path strings and block without reading contents. [VERIFIED: privguard/policy.py] |
| False assurance on unsupported clients. [VERIFIED: .planning/REQUIREMENTS.md] | Spoofing / Information Disclosure | Label unsupported/unknown/external surfaces and block by default. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] |

## Planning Recommendations

1. Plan separate tasks for canonical detection expansion, masking result/verification, protected-path classification, policy decisions, diagnostics serializers, CLI commands, and tests. [ASSUMED]
2. Implement detection before masking and policy, because masking verification and decisions depend on stable hit semantics. [ASSUMED]
3. Add tests in the same phase rather than waiting for Phase 5, because Phase 5 should harden the full v1 surface rather than discover core contract bugs. [VERIFIED: .planning/ROADMAP.md] [ASSUMED]
4. Keep Presidio parity behind optional imports and skip tests when dependencies/models are unavailable. [VERIFIED: pyproject.toml] [ASSUMED]
5. Treat SafeSend as UX/product inspiration only until source inspection succeeds. [VERIFIED: web open attempts]
6. Make the CLI expose `scan`, `mask`, and possibly `policy-check` commands with `--json`; default output should be human-readable and sanitized. [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md] [ASSUMED]
7. Ensure exceptions and assertion messages in tests do not print fixture raw values. [VERIFIED: .planning/REQUIREMENTS.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Use richer result objects such as `DetectionReport`, `MaskResult`, `PathClassification`, and `PolicyDecision`. | Implementation Approach | Planner may choose a simpler API, but must still support the same behavior. |
| A2 | Re-run detection on masked output as part of verification. | Implementation Approach | Could create false failures if placeholders match patterns; tests must confirm placeholders are inert. |
| A3 | Add `diagnostics.py` if `policy.py` gets too broad. | Architecture Patterns | Planner may keep serializers in `policy.py`; risk is module sprawl, not behavior. |
| A4 | SafeSend source should not be copied until inspected directly. | SafeSend Lessons | Could miss reusable MIT code, but avoids adopting unverified browser code. |
| A5 | CLI should add `scan`, `mask`, and `policy-check`. | Planning Recommendations | Command names may change, but planner still needs diagnostics and masking entry points. |

## Open Questions (RESOLVED)

1. **Should Phase 2 resolve the `privacy-guard` vs `privguard` command-name mismatch?** [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: pyproject.toml]  
   What we know: requirements mention `privacy-guard`; package metadata exposes `privguard`. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: pyproject.toml]  
   RESOLVED: Plan 02-04 adds a `privacy-guard` console alias while preserving `privguard`, so requirements and existing package identity both remain valid. [VERIFIED: .planning/phases/02-privacy-core/02-04-PLAN.md]

2. **Should masked payload text be included in hook-style diagnostics?** [VERIFIED: privguard/hooks.py]  
   What we know: current hook code includes redacted text in messages; Phase 2 requires diagnostics to be sanitized but allows masking output as a product feature. [VERIFIED: privguard/hooks.py] [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]  
   RESOLVED: Plans keep diagnostics metadata-only and expose masked text only from explicit mask APIs/commands, never from hook-style diagnostics. [VERIFIED: .planning/phases/02-privacy-core/02-02-PLAN.md] [VERIFIED: .planning/phases/02-privacy-core/02-03-PLAN.md] [VERIFIED: .planning/phases/02-privacy-core/02-04-PLAN.md]

3. **How much Presidio parity is required in Phase 2?** [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]  
   What we know: DET-06 requires shared validator semantics and fixtures; implementation discretion allows optional adapter. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]  
   RESOLVED: Plan 02-01 makes package validators canonical and keeps Presidio parity optional/canonical-validator based; stdlib core completion is not blocked on spaCy model availability. [VERIFIED: .planning/phases/02-privacy-core/02-01-PLAN.md]

## Sources

### Primary (HIGH confidence)
- `.planning/phases/02-privacy-core/02-CONTEXT.md` - locked implementation decisions and phase boundary. [VERIFIED: local read]
- `.planning/REQUIREMENTS.md` - DET/MASK/POL acceptance criteria. [VERIFIED: local read]
- `.planning/ROADMAP.md` - Phase 2 goal and success criteria. [VERIFIED: local read]
- `.planning/STATE.md` - prior decisions and blockers. [VERIFIED: local read]
- `pyproject.toml` - package metadata and optional dependency pins. [VERIFIED: local read]
- `privguard/detection.py`, `privguard/masking.py`, `privguard/policy.py`, `privguard/hooks.py`, `privguard/cli.py` - current implementation. [VERIFIED: local read]
- `demos/test_presidio_br.py` - Brazilian validators and Presidio recognizer reference. [VERIFIED: local read]
- `AGENTS.md` - project privacy and data-hygiene constraints. [VERIFIED: local read]

### Official / External (HIGH-MEDIUM confidence)
- Microsoft Presidio Analyzer docs - recognizer architecture, custom recognizers, `PatternRecognizer`, `AnalyzerEngine`. [CITED: https://microsoft.github.io/presidio/analyzer/]
- Microsoft Presidio Anonymizer docs - replace/redact/mask/encrypt/decrypt operators and overlap handling. [CITED: https://microsoft.github.io/presidio/anonymizer/]
- Microsoft Presidio recognizer best practices - accuracy/performance/environment guidance. [CITED: https://microsoft.github.io/presidio/analyzer/developing_recognizers/]
- Microsoft Presidio GitHub - project description and latest release 2.2.362 dated Mar 18, 2026. [CITED: https://github.com/microsoft/presidio]

### Tertiary / Partial (LOW confidence)
- SafeSend public Reddit description - browser-only, placeholders, restoration, local learned terms, MIT/open-source/test claims. [CITED: https://www.reddit.com/r/SideProject/comments/1sx26s8/safesend_mask_sensitive_data_before_pasting_into/]
- SafeSend public Reddit update - contributor changes, large-file/security feedback. [CITED: https://www.reddit.com/r/vibecoding/comments/1syszto/i_built_a_small_tool_in_2_hours_a_contributor/]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified from local package metadata, local environment, and official Presidio docs. [VERIFIED: pyproject.toml] [CITED: https://microsoft.github.io/presidio/analyzer/]
- Architecture: HIGH - follows existing package modules and locked Phase 2 decisions. [VERIFIED: privguard/*.py] [VERIFIED: .planning/phases/02-privacy-core/02-CONTEXT.md]
- Pitfalls: MEDIUM - based on current code gaps, requirements, Presidio docs, and partial SafeSend public reports. [VERIFIED: local code audit] [CITED: https://microsoft.github.io/presidio/analyzer/developing_recognizers/] [CITED: https://www.reddit.com/r/vibecoding/comments/1syszto/i_built_a_small_tool_in_2_hours_a_contributor/]

**Research date:** 2026-05-02 [VERIFIED: system date]  
**Valid until:** 2026-06-01 for local architecture; re-check Presidio/SafeSend sources before using external code. [ASSUMED]
