# Roadmap: privguard

## Overview

This roadmap turns the current Presidio demos and Claude hook scripts into a reusable local privacy guard for terminal and IDE code agents. The v1 path is deliberately local-first and fail-closed: package the tool, unify Brazilian PII and secret detection, enforce irreversible outbound masking only where rewrite is proven, block protected paths and non-rewritable external-provider surfaces, document Codex support honestly, and prove with synthetic tests that raw sensitive values are not echoed or passed through.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Package Foundation** - Developers can install and run a reusable local package/CLI without demo scripts becoming production behavior.
- [ ] **Phase 2: Privacy Core** - Detection, masking, path classification, policy decisions, and safe diagnostics share one fail-closed contract.
- [ ] **Phase 3: Claude Enforcement** - Claude Code prompt and tool hooks enforce strict outbound privacy and protected-path blocking with sanitized output.
- [ ] **Phase 4: Codex Compatibility Evidence** - Codex support claims are backed by documented interception evidence and explicit support-level labels.
- [ ] **Phase 5: Synthetic Regression Gate** - The full v1 surface is covered by synthetic tests proving no raw sensitive values leak through outputs, logs, hooks, masks, or failures.

## Phase Details

### Phase 1: Package Foundation
**Goal**: Developers can install and run the privacy guard as a local reusable Python tool while existing demos are separated from production-safe behavior.
**Depends on**: Nothing (first phase)
**Requirements**: PKG-01, PKG-02, PKG-03, PKG-04
**Success Criteria** (what must be TRUE):
  1. Developer can install the project locally with a reproducible dependency manifest and run the `privacy-guard` command.
  2. Developer can run CLI diagnostics and local masking checks without invoking root-level demo scripts.
  3. Reusable detection, masking, policy, and adapter code is importable from package modules.
  4. Existing demos are clearly separated from production code and do not print raw sensitive data by default.
**Plans**: TBD

Plans:
- [ ] 01-01: TBD

### Phase 2: Privacy Core
**Goal**: Supported clients and CLI commands share Brazil-first detection, irreversible masking, protected-path classification, fail-closed policy decisions, and sanitized diagnostics.
**Depends on**: Phase 1
**Requirements**: DET-01, DET-02, DET-03, DET-04, DET-05, DET-06, MASK-01, MASK-02, MASK-03, MASK-04, POL-01, POL-02, POL-03, POL-04
**Success Criteria** (what must be TRUE):
  1. User can scan synthetic Brazilian identifiers, fake secrets, and protected path strings and see only entity types, counts, offsets, and reason codes.
  2. User can mask detected sensitive text into typed placeholders, and the guard refuses output when original synthetic sensitive substrings remain.
  3. User can rely on strict mode as the default for external-provider workflows, including unknown providers and unclassified client targets.
  4. User can see whether a surface is rewrite-capable, block-only, observe-only, or unsupported before the guard allows external submission.
  5. Lightweight hook detection and Presidio-backed detection agree on validator semantics for shared synthetic fixtures.
**Plans**: TBD

Plans:
- [ ] 02-01: TBD

### Phase 3: Claude Enforcement
**Goal**: Claude Code is protected by production hook adapters that block sensitive prompts, protected file access, risky tool commands, and unsafe outputs when rewrite cannot be guaranteed.
**Depends on**: Phase 2
**Requirements**: CLD-01, CLD-02, CLD-03, CLD-04, CLD-05
**Success Criteria** (what must be TRUE):
  1. Developer can submit a Claude prompt containing synthetic sensitive data and the hook blocks it when safe rewrite is unavailable.
  2. Developer can attempt Claude reads, searches, edits, writes, or shell commands against protected paths and the hook blocks before file contents are read.
  3. Developer can attempt command exfiltration patterns involving protected paths and the hook denies them with sanitized reason codes.
  4. Developer can validate Claude hook installation and effective policy without reading `.env`, dumps, credentials, or `data_sensivel` contents.
  5. Claude hook stdout, stderr, and JSON responses never include raw matched values, prompt snippets, protected file contents, or secret-looking substrings.
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

### Phase 4: Codex Compatibility Evidence
**Goal**: Codex support is represented honestly through tested interception evidence, capability labels, and no automatic masking claims until raw payload replacement is proven.
**Depends on**: Phase 2
**Requirements**: CDX-01, CDX-02, CDX-03
**Success Criteria** (what must be TRUE):
  1. Developer can read a current Codex compatibility assessment that states which prompt and tool interception options were verified.
  2. Developer can see each Codex surface labeled as supported, experimental, block-only, or unsupported with evidence.
  3. Developer cannot enable or encounter a claim of automatic Codex masking unless a tested integration proves raw outbound payloads are replaced before provider submission.
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

### Phase 5: Synthetic Regression Gate
**Goal**: v1 privacy behavior is backed by synthetic-only automated tests that prove masking, blocking, path handling, output hygiene, and fail-closed behavior across the package and adapters.
**Depends on**: Phase 4
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06
**Success Criteria** (what must be TRUE):
  1. Developer can run the test suite and confirm it uses only synthetic Brazilian PII, fake secrets, and fake protected paths.
  2. Developer can verify raw synthetic sensitive values never appear in stdout, stderr, logs, hook JSON, masked payloads, or exception messages.
  3. Developer can see tests pass for valid and invalid Brazilian identifiers, overlap handling, false-positive lookalikes, and Windows path normalization cases.
  4. Developer can see Claude hook tests cover prompt/tool payloads, malformed input, exit codes, policy modes, and sanitized output.
  5. Developer can see fail-closed tests pass when detection, masking, configuration, or client capability validation fails.
**Plans**: TBD

Plans:
- [ ] 05-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Package Foundation | 0/TBD | Not started | - |
| 2. Privacy Core | 0/TBD | Not started | - |
| 3. Claude Enforcement | 0/TBD | Not started | - |
| 4. Codex Compatibility Evidence | 0/TBD | Not started | - |
| 5. Synthetic Regression Gate | 0/TBD | Not started | - |
