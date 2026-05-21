# Roadmap: privguard

## Overview

This roadmap turns the current Presidio demos and Claude hook scripts into a reusable local privacy guard for terminal and IDE code agents. The v1 path is deliberately local-first and fail-closed: package the tool, unify Brazilian PII and secret detection, enforce irreversible outbound masking only where rewrite is proven, block protected paths and non-rewritable external-provider surfaces, document Codex support honestly, and prove with synthetic tests that raw sensitive values are not echoed or passed through.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Package Foundation** - Developers can install and run a reusable local package/CLI without demo scripts becoming production behavior.
- [x] **Phase 2: Privacy Core** - Detection, masking, path classification, policy decisions, and safe diagnostics share one fail-closed contract.
- [x] **Phase 3: Claude Enforcement** - Claude Code prompt and tool hooks enforce strict outbound privacy and protected-path blocking with sanitized output.
- [x] **Phase 4: Codex Compatibility Evidence** - Codex support claims are backed by documented interception evidence and explicit support-level labels.
- [x] **Phase 5: Synthetic Regression Gate** - The full v1 surface is covered by synthetic tests proving no raw sensitive values leak through outputs, logs, hooks, masks, or failures.
- [x] **Phase 6: Milestone Cleanup** - v1 documentation, packaging, and public API surface accurately reflect the verified state of the system at audit close (closes tech-debt items from v1.0 milestone audit).
- [ ] **Phase 7: Project README + Repo Hygiene** - First-time user can read a bilingual (EN + PT-BR) README and clean up repo cruft via a config-driven, fail-safe cleanup mechanism.

## Phase Details

### Phase 1: Package Foundation
**Goal**: Developers can install and run the privacy guard as a local reusable Python tool while existing demos are separated from production-safe behavior.
**Depends on**: Nothing (first phase)
**Requirements**: PKG-01, PKG-02, PKG-03, PKG-04
**Success Criteria** (what must be TRUE):
  1. Developer can install the project locally with a reproducible dependency manifest and run the `privguard` command.
  2. Developer can run CLI diagnostics and local masking checks without invoking root-level demo scripts.
  3. Reusable detection, masking, policy, and adapter code is importable from package modules.
  4. Existing demos are clearly separated from production code and do not print raw sensitive data by default.
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — Add setuptools package metadata and `privguard info`.
- [x] 01-02-PLAN.md — Extract lightweight detection, masking, and policy modules.
- [x] 01-03-PLAN.md — Refactor Claude hook entry files into package-backed adapters.
- [x] 01-04-PLAN.md — Move demos into `demos/` and remove raw-value default demo printing.

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
**Plans**: 4 plans

Plans:
- [x] 02-01-PLAN.md — Build the shared Brazil-first detection contract and synthetic parity tests.
- [x] 02-02-PLAN.md — Add irreversible masking, verification, and sanitized diagnostics.
- [x] 02-03-PLAN.md — Implement protected-path classification and fail-closed policy decisions.
- [x] 02-04-PLAN.md — Wire Phase 2 core into CLI commands and package exports.

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
**Plans**: 4 plans

Plans:
- [x] 03-01-PLAN.md — Harden prompt hook output and default blocking.
- [x] 03-02-PLAN.md — Expand PreToolUse protected-path and command blocking.
- [x] 03-03-PLAN.md — Add safe `privguard claude doctor` diagnostics.
- [x] 03-04-PLAN.md — Add Phase 03 synthetic regression gate and collection hygiene. (completed 2026-05-03)

### Phase 4: Codex Compatibility Evidence
**Goal**: Codex support is represented honestly through tested interception evidence, capability labels, and no automatic masking claims until raw payload replacement is proven.
**Depends on**: Phase 2
**Requirements**: CDX-01, CDX-02, CDX-03
**Success Criteria** (what must be TRUE):
  1. Developer can read a current Codex compatibility assessment that states which prompt and tool interception options were verified.
  2. Developer can see each Codex surface labeled as supported, experimental, block-only, or unsupported with evidence.
  3. Developer cannot enable or encounter a claim of automatic Codex masking unless a tested integration proves raw outbound payloads are replaced before provider submission.
**Plans**: 2 plans

Plans:
- [x] 04-01-PLAN.md — Create the Codex compatibility matrix and human-readable assessment.
- [x] 04-02-PLAN.md — Add the CDX-03 claim-prevention gate for unsupported Codex masking claims.

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
**Plans**: 1 plans

Plans:
- [x] 05-01-PLAN.md — Create the pytest-native v1 synthetic regression gate for TEST-01 through TEST-06.

### Phase 6: Milestone Cleanup
**Goal**: v1 documentation, packaging, and public API surface accurately reflect the verified state of the system at audit close (2026-05-06).
**Depends on**: Phase 5
**Requirements**: PKG-02 (wording), CDX-01, CDX-02, CDX-03 (status sync), TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06 (status sync)
**Gap Closure**: Closes 11 tech-debt items from `.planning/v1.0-MILESTONE-AUDIT.md`
**Success Criteria** (what must be TRUE):
  1. REQUIREMENTS.md checkboxes and traceability table match VERIFICATION.md verdicts for every v1 requirement (CDX-01..03 and TEST-01..06 ticked `[x]` and `Complete`).
  2. ROADMAP.md Phase 5 status, progress row, and Phase 1 success criteria use the canonical command name `privguard` with no legacy drift.
  3. Plan summary frontmatter exposes `requirements_completed:` for every plan that satisfied a v1 requirement (04-01 and 05-01 backfilled).
  4. The legacy console-script alias is removed (Phase 1 D-01 locked the canonical name to `privguard`); `pyproject.toml` and REQUIREMENTS.md PKG-02 text agree on the canonical name.
  5. `privguard/__init__.py.__all__` re-exports the public Phase 03/04 surface (`classify_command`, `main_user_prompt`, `main_pre_tool`, `build_claude_doctor_report`, `CODEX_COMPATIBILITY`).
  6. Python 3.14 presidio-extras gating is either documented in `pyproject.toml` or relaxed so `pip install privguard[full]` behavior on 3.14 is intentional rather than incidental.
**Plans**: 4 plans

Plans:
- [x] 06-01-PLAN.md — Sync REQUIREMENTS.md checkboxes/traceability and rewrite PKG-02 to canonical `privguard`.
- [x] 06-02-PLAN.md — Sync ROADMAP.md Phase 5 status/progress and remove legacy CLI-name references (canonical: `privguard`).
- [x] 06-03-PLAN.md — Backfill `requirements_completed:` frontmatter in 04-01 and 05-01 SUMMARYs (and normalize 04-02).
- [x] 06-04-PLAN.md — Drop legacy console-script alias, extend `privguard.__all__`, document Python 3.14 extras gating, run verification bar.

### Phase 7: Project README + Repo Hygiene
**Goal**: First-time user can land in the repo, understand what privguard does and does not do, install it, and clean up after themselves — in either English or Portuguese.
**Depends on**: Phase 6
**Requirements**: DOC-01, MAINT-01
**Success Criteria** (what must be TRUE):
  1. User can read a top-level README in English (`README.md`) and Portuguese (`README.pt-BR.md`) that covers install, CLI usage, Claude Code hook setup, the Claude/Codex capabilities matrix, what privguard does *not* do, and the synthetic-fixture-only policy.
  2. User can run a single cleanup command and remove pytest cache directories, build artifacts, and other declared temporary directories from the repo root without touching `.env`, `data_sensivel/`, `.planning/`, `.git/`, or any source directory.
  3. Maintainer can add a new cleanup pattern by editing one list in `pyproject.toml` (`[tool.privguard.cleanup]`), without modifying the cleanup script.
  4. Cleanup script runs as dry-run by default and requires an explicit `--apply` flag before deleting anything (matches privguard's fail-closed posture).
  5. `.gitignore` covers every pattern declared as cleanup-eligible, so transient artifacts never reach commits even when cleanup hasn't been run.
**Plans**: TBD plans

Plans:
- [ ] TBD (run `/gsd-plan-phase 7`)

## Backlog

### Phase 999.1: WebFetch Domain Allowlist (BACKLOG)

**Goal:** Permitir `WebFetch` apenas para domínios confiáveis (ex: github.com, docs.python.org) em vez de bloquear completamente. Implementar `check_webfetch()` em `privguard/hooks.py` com `_ALLOWED_FETCH_DOMAINS` e inspeção via `urlparse`. Atualmente `WebFetch` fica bloqueado e o fluxo recomendado é Bash+curl (opção de menor risco).
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd-review-backlog when ready)

### Phase 999.2: Audit Log Mínimo Viável (BACKLOG)

**Goal:** Registrar em `~/.privguard/audit.log` cada evento de bloqueio/warn dos hooks como linha JSON (timestamp, reason_code, category). Fire-and-forget — nunca falha o hook se o log não puder ser escrito. Inclui 1-2 testes de contrato.
**Requirements:** TBD
**Plans:** 0 plans

Plans:
- [ ] TBD (promote with /gsd-review-backlog when ready)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Package Foundation | 4/4 | Complete | 2026-05-02 |
| 2. Privacy Core | 4/4 | Complete | 2026-05-03 |
| 3. Claude Enforcement | 4/4 | Complete | 2026-05-03 |
| 4. Codex Compatibility Evidence | 2/2 | Complete | 2026-05-04 |
| 5. Synthetic Regression Gate | 1/1 | Complete | 2026-05-05 |
| 6. Milestone Cleanup | 4/4 | Complete | 2026-05-08 |
| 7. Project README + Repo Hygiene | 0/TBD | Not started | - |
