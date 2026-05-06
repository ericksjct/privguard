# Requirements: privguard

**Defined:** 2026-05-01
**Core Value:** No sensitive Brazilian or company data should be sent to external LLM providers in clear text.

## v1 Requirements

Requirements for the initial release. Each maps to roadmap phases.

### Packaging

- [x] **PKG-01**: Developer can install the project as a local Python package with a reproducible dependency manifest.
- [x] **PKG-02**: Developer can run a `privacy-guard` CLI entry point for diagnostics and local masking checks.
- [x] **PKG-03**: Reusable detection, masking, policy, and adapter code lives in importable package modules instead of root-level demo scripts.
- [x] **PKG-04**: Existing demos are separated from production code and do not print raw sensitive data by default.

### Detection

- [x] **DET-01**: Guard can detect synthetic Brazilian CPF values with checksum validation.
- [x] **DET-02**: Guard can detect synthetic Brazilian CNPJ values with checksum validation.
- [x] **DET-03**: Guard can detect additional Brazilian identifiers including CNH, voter title, PIS/PASEP, SUS, RG-like values, phone numbers, CEP, and vehicle plates.
- [x] **DET-04**: Guard can detect secret-like values including API keys, tokens, passwords, database URLs, and environment variable assignments.
- [x] **DET-05**: Guard can classify protected paths including `.env`, `.env.*`, `data_sensivel/**`, dumps, credential-like files, and secret-like filenames without reading file contents.
- [x] **DET-06**: Lightweight hook detection and Presidio-backed detection share validator semantics and synthetic fixtures to prevent drift.

### Masking

- [x] **MASK-01**: Guard can replace detected sensitive values with typed placeholders before any external-provider submission path.
- [x] **MASK-02**: Guard verifies masked output does not contain the original synthetic sensitive substrings before allowing it onward.
- [x] **MASK-03**: Guard uses irreversible masking for v1 and does not require or persist deanonymization maps.
- [x] **MASK-04**: Guard blocks instead of allowing clear text when a client surface cannot prove that masking replaced the outbound payload.

### Policy

- [x] **POL-01**: Guard exposes explicit policy modes with strict/fail-closed behavior as the default for external-provider workflows.
- [x] **POL-02**: Guard distinguishes supported rewrite-capable surfaces, block-only surfaces, observe-only surfaces, and unsupported clients.
- [x] **POL-03**: Guard treats unknown or unclassified provider targets as external and requires masking or blocking.
- [x] **POL-04**: Guard emits only sanitized decisions and diagnostics containing entity types, counts, offsets, and reason codes.

### Claude

- [x] **CLD-01**: Claude Code `UserPromptSubmit` integration blocks sensitive prompts when safe rewrite is unavailable.
- [x] **CLD-02**: Claude Code `PreToolUse` integration blocks reads, searches, edits, writes, and shell commands that reference protected paths.
- [x] **CLD-03**: Claude Code `PreToolUse` integration blocks command exfiltration patterns involving protected paths, network tools, archive tools, encoding tools, or clipboard commands.
- [x] **CLD-04**: Claude hook outputs never include raw matched values, original prompt snippets, protected file contents, or secret-looking substrings.
- [x] **CLD-05**: Developer can validate Claude hook installation and effective policy without reading protected files.

### Codex

- [ ] **CDX-01**: Project documents the current Codex interception options and whether prompt/tool payloads can be blocked or rewritten before provider submission.
- [ ] **CDX-02**: Project includes a compatibility matrix that marks Codex support as supported, experimental, block-only, or unsupported with evidence.
- [ ] **CDX-03**: Guard does not claim automatic Codex masking until a tested integration proves raw payloads are replaced before submission.

### Testing

- [ ] **TEST-01**: Test suite uses only synthetic Brazilian PII, fake secrets, and fake protected paths.
- [ ] **TEST-02**: Tests assert raw sensitive fixture values never appear in stdout, stderr, logs, hook JSON, masked payloads, or exception messages.
- [ ] **TEST-03**: Tests cover valid and invalid Brazilian identifier examples, overlap handling, and false-positive lookalikes.
- [ ] **TEST-04**: Tests cover protected path normalization for Windows paths, mixed separators, relative traversal, quoted paths, and project-root-relative paths.
- [ ] **TEST-05**: Tests cover Claude prompt and tool hook JSON payloads, malformed input, exit codes, policy modes, and sanitized output.
- [ ] **TEST-06**: Tests cover fail-closed behavior when detection, masking, configuration, or client capability validation fails.

### Documentation

- [ ] **DOC-01**: Project includes a bilingual top-level README (English primary `README.md`, Portuguese secondary `README.pt-BR.md`) covering installation, CLI usage, Claude Code hook setup, the Claude/Codex capabilities matrix, what the guard does *not* do, and the synthetic-fixture-only policy.

### Maintenance

- [ ] **MAINT-01**: Repo includes a config-driven cleanup mechanism with patterns declared in `pyproject.toml` (`[tool.privguard.cleanup]`), a hard-coded protected list (`.env`, `data_sensivel/`, `.planning/`, `.git/`, source directories) the script can never delete, and a dry-run-by-default contract that requires an explicit `--apply` flag before deletion.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Integrations

- **INT-01**: Guard supports additional IDE-agent integrations after their interception and rewrite surfaces are validated.
- **INT-02**: Guard supports LangChain, LlamaIndex, or application-level SDK adapters.
- **INT-03**: Guard supports a local proxy or wrapper mode for clients that do not expose hooks.

### Local Models

- **LOC-01**: Guard can route eligible sensitive workflows to explicitly approved local-only model endpoints.
- **LOC-02**: Guard validates local model endpoints, timeout behavior, and safe error handling before sending prompts.

### Enterprise

- **ENT-01**: Guard supports centrally distributed policy profiles while keeping raw scanning local.
- **ENT-02**: Guard emits audit-safe telemetry that never contains raw sensitive values.
- **ENT-03**: Guard supports signed releases, SBOM generation, and enterprise package distribution.

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Hosted SaaS or cloud proxy | The privacy boundary must stay local and raw data must not be sent to a new external service. |
| Deanonymization after LLM responses | v1 only needs outbound masking; reversible maps create key-management and retention risk. |
| Universal protection for unsupported clients | Clients without tested interception cannot be guaranteed safe. |
| Real sensitive data in tests, docs, examples, or commits | This would reproduce the exfiltration risk the project exists to prevent. |
| Warning-only default mode | The core value requires blocking or verified masking for external-provider paths. |
| Full framework adapter ecosystem in v1 | Terminal/IDE code-agent protection comes first. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PKG-01 | Phase 1 | Complete |
| PKG-02 | Phase 1 | Complete |
| PKG-03 | Phase 1 | Complete |
| PKG-04 | Phase 1 | Complete |
| DET-01 | Phase 2 | Complete |
| DET-02 | Phase 2 | Complete |
| DET-03 | Phase 2 | Complete |
| DET-04 | Phase 2 | Complete |
| DET-05 | Phase 2 | Complete |
| DET-06 | Phase 2 | Complete |
| MASK-01 | Phase 2 | Complete |
| MASK-02 | Phase 2 | Complete |
| MASK-03 | Phase 2 | Complete |
| MASK-04 | Phase 2 | Complete |
| POL-01 | Phase 2 | Complete |
| POL-02 | Phase 2 | Complete |
| POL-03 | Phase 2 | Complete |
| POL-04 | Phase 2 | Complete |
| CLD-01 | Phase 3 | Complete |
| CLD-02 | Phase 3 | Complete |
| CLD-03 | Phase 3 | Complete |
| CLD-04 | Phase 3 | Complete |
| CLD-05 | Phase 3 | Complete |
| CDX-01 | Phase 4 | Pending |
| CDX-02 | Phase 4 | Pending |
| CDX-03 | Phase 4 | Pending |
| TEST-01 | Phase 5 | Pending |
| TEST-02 | Phase 5 | Pending |
| TEST-03 | Phase 5 | Pending |
| TEST-04 | Phase 5 | Pending |
| TEST-05 | Phase 5 | Pending |
| TEST-06 | Phase 5 | Pending |
| DOC-01 | Phase 7 | Pending |
| MAINT-01 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 34 total
- Mapped to phases: 34
- Unmapped: 0

---
*Requirements defined: 2026-05-01*
*Last updated: 2026-05-06 after v1.0 milestone audit (added Phase 6 cleanup + Phase 7 README/hygiene scope, added DOC-01 and MAINT-01)*
