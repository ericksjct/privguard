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
- [x] **Phase 7: Project README + Repo Hygiene** - First-time user can read a bilingual (PT + EN) README and clean up repo cruft via a config-driven, fail-safe cleanup mechanism.
- [ ] **Phase 9: Milestone v1.0 Audit Cleanup** - All v1.0 audit tech-debt is swept: REQUIREMENTS/ROADMAP state matches the verified system, README documents the shipped block/warn/mask selector, and cleanup.py robustness fixes land (closes tech-debt items from the 2026-06-10 audit).
- [x] **Phase 10: Test Hardening (fail-closed first)** - Failure-path, evasion, and robustness coverage proves the fail-closed promise: injected detector failures always block, adversarial evasion vectors are documented or flagged RISCO, and a branch-coverage gate is enforced. (completed 2026-07-09)
- [ ] **Phase 11: Fail-Closed Hardening** - Close the phase-10 findings: the guard blocks on detector error and oversized input (fail-closed, not fail-open), the ReDoS-class regex is made backtracking-safe, and detection is hardened against common evasion (normalization, fragmentation/concatenation, encoded secrets) without regressing the false-positive rate.

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

  1. User can read a top-level README in Portuguese (`README.md`) and English (`README.en.md`) that covers install, CLI usage, Claude Code hook setup, the Claude/Codex capabilities matrix, what privguard does *not* do, and the synthetic-fixture-only policy.
  2. User can run a single cleanup command and remove pytest cache directories, build artifacts, and other declared temporary directories from the repo root without touching `.env`, `data_sensivel/`, `.planning/`, `.git/`, or any source directory.
  3. Maintainer can add a new cleanup pattern by editing one list in `pyproject.toml` (`[tool.privguard.cleanup]`), without modifying the cleanup script.
  4. Cleanup script runs as dry-run by default and requires an explicit `--apply` flag before deleting anything (matches privguard's fail-closed posture).
  5. `.gitignore` covers every pattern declared as cleanup-eligible, so transient artifacts never reach commits even when cleanup hasn't been run.

**Plans**: TBD plans

Plans:

- [ ] TBD (run `/gsd-plan-phase 7`)

### Phase 9: Milestone v1.0 Audit Cleanup

**Goal**: v1.0 documentation state and the cleanup utility accurately reflect the verified system at the 2026-06-10 audit close — checkboxes match VERIFICATION verdicts, the Progress table covers all 13 phases, the README documents the shipped block/warn/mask selector, and cleanup.py honors the D-14 exit-code contract.
**Depends on**: Phase 8
**Requirements**: DOC-01, MAINT-01 (checkbox/traceability sync — both verified SATISFIED by Phase 7 on 2026-05-10)
**Gap Closure**: Closes 9 tech-debt items across 5 sources from `.planning/v1.0-MILESTONE-AUDIT.md` (2026-06-10)
**Success Criteria** (what must be TRUE):

  1. REQUIREMENTS.md DOC-01 and MAINT-01 are `[x]` with traceability rows `Complete`; coverage note reflects the synced state.
  2. ROADMAP.md Phase 7 is `[x]` with its progress row corrected to `3/3 Complete 2026-05-10`; the Progress table includes Phase 8 and backlog 999.1–999.5 so it reflects the true 13-phase milestone.
  3. README.md (Portuguese default) and README.en.md (English) document the `PII_GUARD_MODE` selector (block default / warn opt-in non-protective / mask) instead of declaring warn-only "out of scope"; DOC-01 wording matches the shipped `README.md` + `README.en.md` layout (no stale `README.pt-BR.md` reference).
  4. cleanup.py: `_load_patterns()` reopen of `pyproject.toml` is guarded so a TOCTOU `OSError` surfaces as sanitized `[CLEANUP] error` (exit 2 per D-14), not unhandled exit 1; apply/dry-run headers are built explicitly (no fragile `.replace()` substitution); the unreachable `_human_size` return is removed.
  5. The synthetic regression gate still passes (252 passed / 1 skipped baseline) after the cleanup.py changes.

**Plans**: 3 plans

Plans:

- [x] 09-01-PLAN.md — Sync REQUIREMENTS.md + ROADMAP.md state (tick DOC-01/MAINT-01/Phase 7, add 13-phase Progress table, drop stale README.pt-BR.md refs)
- [x] 09-02-PLAN.md — Rewrite README.md (PT) + README.en.md (EN) warn-vs-block FAQ to document the PII_GUARD_MODE block/warn/mask selector
- [x] 09-03-PLAN.md — cleanup.py robustness fixes (WR-01 guarded read, WR-02 explicit headers, IN-01 dead-code) + BLOCKING full regression gate

### Phase 10: Test Hardening (fail-closed first)

**Goal**: The fail-closed promise is proven, not assumed: every injected detector failure results in a block, every adversarial evasion vector is tested and documented (pass-throughs flagged RISCO, never silenced), checksum validators survive mutation and property-based testing, and a branch-coverage gate is enforced from a measured baseline.
**Depends on**: Phase 9
**Requirements**: TEST-07
**Source**: Imported from `.planning/handoff_lacunas.md` (Tiers 1–2, the handoff's non-negotiable core; Tiers 3–4 remain in the handoff as follow-up candidates)
**Success Criteria** (what must be TRUE):

  1. Branch-coverage baseline is measured and recorded before any new test is written.
  2. Every injected detector failure (exception, missing Presidio, timeout, oversized input, invalid config) results in a block decision — zero exception-to-allow paths.
  3. Every evasion vector (homoglyphs, zero-width, fragmentation, encoding, concatenation, code fences) has a test documenting current behavior; pass-throughs are RISCO items.
  4. Mutation score over checksum/decision code is reported and surviving mutants become tests; hypothesis properties hold for validators and masking idempotence.
  5. `--cov-fail-under` (branch) is active from the measured baseline, and the pre-existing suite still passes.

**Plans**: 2/2 plans complete

Plans:

- [x] 10-01-PLAN.md — Baseline + dev-deps, then Tier 1: fail-closed injection (P1), adversarial evasion (P2), ReDoS/size guard (P3)
- [x] 10-02-PLAN.md — Tier 2: property-based validators (P5), checksum edges (P6), FP corpus/overlap (P7), mutation + coverage gate (P4)

### Phase 11: Fail-Closed Hardening

**Goal**: The phase-10 findings are closed so v1.0 delivers its fail-closed promise: an operational failure (detector exception or oversized input) blocks with exit code 2 instead of falling open, the ReDoS-class EMAIL regex is backtracking-safe, and detection resists common evasion (Unicode normalization, checksum-gated fragmentation/concatenation reassembly, single-layer encoded-secret decode-and-rescan) — all without regressing the measured false-positive rate (0.0 baseline from phase 10's P7 corpus).
**Depends on**: Phase 10
**Requirements**: DET-07
**Source**: Closes the RISCO/DECISAO findings recorded in `.planning/phases/10-test-hardening/10-VERIFICATION.md` (R1–R12, D1–D3).
**Scope honesty**: R1/D2/D3 are correctness guarantees (fail-closed on error, no ReDoS). R2–R11 are recall improvements gated hard on the false-positive corpus; a client-side scanner cannot be adversarially complete, and any evasion pass that would raise the FP rate is dropped and documented as a limitation rather than shipped as noise. D1 (detector-hang watchdog) stays out — it depends on Claude Code's external hook timeout and is a v2 concern.
**Success Criteria** (what must be TRUE):

  1. A detector exception on either hook (`UserPromptSubmit`, `PreToolUse`) blocks with exit code 2 and a sanitized reason — never exits 1 (fail-open). The phase-10 R1 tests now assert block.
  2. Oversized input (over the configured cap) blocks fail-closed with a sanitized reason instead of being scanned in full; the EMAIL regex scales linearly on hostile input (ReDoS closed). The phase-10 D2/D3 tests now assert the bound.
  3. `valida_cartao_sus` rejects unassigned CNS leading-digit ranges (R12); homoglyph/zero-width/combining evasion (R2–R4) is detected via an offset-safe normalization pass.
  4. Checksum-gated reassembly detects fragmented and concatenated Brazilian identifiers (R5, R6, R10, R11); single-layer base64/hex/URL-encoded secrets are caught by decode-and-rescan (R7, R8, R9) — each only where it holds the false-positive corpus at/near 0.0.
  5. The full synthetic suite stays green under the enforced branch-coverage gate, and every phase-10 RISCO test is flipped from "pass-through pinned" to "fixed" or explicitly re-documented as an accepted limitation.

**Plans**: 2/4 plans executed

Plans:

- [x] 11-01-PLAN.md — Fail-closed core: exception→block wrapper on both hooks (R1), input-size cap (D2), backtracking-safe EMAIL regex (D3), SUS leading-digit range check (R12)
- [x] 11-02-PLAN.md — Offset-safe normalization pass in detect() for homoglyph/zero-width/combining evasion (R2, R3, R4), FP-corpus gated
- [ ] 11-03-PLAN.md — Checksum-gated denoised rescan for fragmentation + concatenation (R5, R6, R10, R11), FP-corpus gated
- [ ] 11-04-PLAN.md — Decode-and-rescan for single-layer encoded secrets (R7, R8, R9), FP-corpus gated

## Backlog

### Phase 999.1: WebFetch Domain Allowlist (BACKLOG)

**Goal:** Permitir `WebFetch` apenas para domínios confiáveis (ex: github.com, docs.python.org) em vez de bloquear completamente. Implementar `check_webfetch()` em `privguard/hooks.py` com `_ALLOWED_FETCH_DOMAINS` e inspeção via `urlparse`. Atualmente `WebFetch` fica bloqueado e o fluxo recomendado é Bash+curl (opção de menor risco).
**Requirements:** WF-01
**Plans:** 2/2 plans complete

Plans:

- [x] 999.1-01-PLAN.md — Add _ALLOWED_FETCH_DOMAINS constant and check_webfetch() to hooks.py; wire WebFetch branch in main_pre_tool()
- [x] 999.1-02-PLAN.md — Add 6 WebFetch domain allowlist tests to test_claude_hooks.py

### Phase 999.2: Audit Log Mínimo Viável (BACKLOG)

**Goal:** Registrar em `~/.privguard/audit.log` cada evento de bloqueio/warn dos hooks como linha JSON (timestamp, reason_code, category). Fire-and-forget — nunca falha o hook se o log não puder ser escrito. Inclui 1-2 testes de contrato.
**Requirements:** TBD
**Plans:** 1 plan

Plans:

- [x] 999.2-01: _audit_log() + instrumentação + testes (complete 2026-05-21)

### Phase 999.3: Masking Gaps — CNPJ, Email, PIX celular (BACKLOG)

**Goal:** Fechar gaps de detecção encontrados no stress test (texto_com_pii.txt): (1) CNPJ não é detectado — o prefixo `XX.XXX.XXX` é confundido com RG; (2) emails são mascarados de forma inconsistente — a maioria passa sem máscara; (3) PIX chave celular (`+55169...`) não é mascarado. Falsos positivos relacionados: transaction IDs confundidos com placa (`<BR_PLACA_OLD>`), códigos de barras confundidos com PIS/PASEP e telefone.
**Requirements:** TBD
**Plans:** 1/1 plans complete

Plans:

- [ ] TBD (promote with /gsd-review-backlog when ready)

### Phase 999.4: CPF Leniency Mode — mascarar CPFs com checksum inválido (BACKLOG)

**Goal:** Atualmente só CPFs com dígito verificador válido são detectados/mascarados. CPFs sintéticos ou com erro de digitação (`456.789.123-45`, `111.222.333-44`, etc.) passam sem máscara. Implementar modo leniente opcional (`PII_GUARD_LENIENT=true`) que mascara qualquer padrão `DDD.DDD.DDD-DD` independente do checksum. Decisão: strict é o default seguro; lenient é opt-in para cenários de teste com dados sintéticos. CNH leniency (bare 11-digit) deferred to future phase due to high false-positive risk.
**Requirements:** DET-01
**Plans:** 2/2 plans complete

Plans:

- [x] 999.4-01-PLAN.md — Add _lenient_default(), _LENIENT_KINDS, _LENIENT_SCORES to detection.py; update detect() and analyze_text(); add lenient to mask_text()
- [x] 999.4-02-PLAN.md — Add --lenient CLI flag to scan/mask/policy-check; add 7 detection tests + 1 masking test

### Phase 999.5: Detection Hardening v2 — CEP variants, CNPJ leniency, IBAN FP fix, name detection opt-in (BACKLOG)

**Goal:** Fechar os gaps de detecção identificados via stress-test com `texto_com_pii.txt`:

1. **CEP variante com ponto** — `14.025-580` não é detectado; regex atual `\d{5}-?\d{3}` não cobre formato `NN.NNN-NNN`.
2. **CNPJ leniency** (opt-in via `PII_GUARD_LENIENT`) — CNPJs sintéticos/com checksum inválido (`11.222.333/0001-00`) passam sem máscara. Mesmo env var do CPF lenient.
3. **IBAN falso positivo** — `DE89 3704 0044 0532 0130 00` gera hit `BR_PHONE` no span interno. Corrigido com novo PatternEntry IBAN espaçado (score 0.90 supera BR_PHONE 0.76).
4. **Detecção de nomes brasileiros** (opt-in via `PII_GUARD_DETECT_NAMES=true` ou `--detect-names`) — frozenset IBGE 2010, scoring por tier: 0.58/0.65/0.72. Função separada `_find_name_hits()`.
5. **Falsos positivos de código de barras** — BR_BOLETO pattern (score 0.92) supera BR_PIS_PASEP (0.91) e BR_PHONE (0.76) via overlap logic.

**Requirements:** TBD
**Plans:** 4/4 plans complete

Plans:

- [x] 999.5-01-PLAN.md — Create privguard/data/ name files and pyproject.toml package-data wiring
- [x] 999.5-02-PLAN.md — Apply four regex/constant fixes to detection.py (CEP, IBAN, BR_BOLETO, CNPJ leniency)
- [x] 999.5-03-PLAN.md — Implement name detection (_find_name_hits, detect_names kwarg, --detect-names CLI flag)
- [x] 999.5-04-PLAN.md — Append 14 regression tests for all 5 detection gaps to tests/test_detection.py

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8, then backlog 999.1 -> 999.2 -> 999.3 -> 999.4 -> 999.5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Package Foundation | 4/4 | Complete | 2026-05-02 |
| 2. Privacy Core | 4/4 | Complete | 2026-05-03 |
| 3. Claude Enforcement | 4/4 | Complete | 2026-05-03 |
| 4. Codex Compatibility Evidence | 2/2 | Complete | 2026-05-04 |
| 5. Synthetic Regression Gate | 1/1 | Complete | 2026-05-05 |
| 6. Milestone Cleanup | 4/4 | Complete | 2026-05-08 |
| 7. Project README + Repo Hygiene | 3/3 | Complete | 2026-05-10 |
| 8. Hook Mode Selector | 2/2 | Complete | 2026-05-25 |
| 999.1 WebFetch Allowlist | 2/2 | Complete (no VERIFICATION.md) | 2026-05-27 |
| 999.2 Audit Log | 1/1 | Complete (no VERIFICATION.md) | 2026-05-21 |
| 999.3 Masking Gaps (RG/CNPJ/PIX) | 1/1 | Complete | 2026-05-21 |
| 999.4 CPF Leniency Mode | 2/2 | Complete | 2026-05-21 |
| 999.5 Detection Hardening v2 | 4/4 | Complete | 2026-05-24 |
| 10. Test Hardening | 2/2 | Complete   | 2026-07-09 |
| 11. Fail-Closed Hardening | 2/4 | In Progress|  |

### Phase 8: eu quero que o usuário possa escolher se ele quer rodar o hook no modo de mascaramento sem bloqueio ou com bloqueio na detecção de pii

**Goal:** User can set `PII_GUARD_MODE=mask` to receive a blocked prompt with a sanitized masked version shown in stderr (for manual resubmission), instead of a plain block. The `scrub` mode is removed and falls through to `block` with a one-line notice.
**Requirements**: TBD
**Depends on:** Phase 7
**Plans:** 2/2 plans complete

Plans:

- [x] 08-01-PLAN.md — Add mask branch to main_user_prompt() and mode-aware inline_pii check to main_pre_tool(); remove scrub branch
- [x] 08-02-PLAN.md — Update test_claude_hooks.py: drop scrub from parametrize, add 5 mask mode tests
