# Phase 5: Synthetic Regression Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-04
**Phase:** 05-synthetic-regression-gate
**Areas discussed:** Gate shape, Synthetic fixture policy, Leakage surfaces, Coverage priorities, Runtime boundaries

---

## Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Todas | Cobre escopo do gate v1, fixtures sintéticos e varredura de vazamentos antes do planejamento. | yes |
| Só essenciais | Discute apenas decisões que podem mudar a arquitetura dos testes. | |
| Você decide | O agente escolhe defaults conservadores com base nas fases anteriores e escreve o contexto direto. | |

**User's choice:** Fallback selected the recommended full-coverage path because structured question
selection was unavailable in this runtime.
**Notes:** The workflow fallback allows presenting options and using the recommended default. The
decisions were grounded in Phases 2-4 and the Phase 5 roadmap scope.

---

## Gate Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Pytest-native aggregate gate | Keep `python -m pytest tests -q` as the primary v1 verification path. | yes |
| Custom runner | Add a separate command or script to orchestrate checks. | |
| Agent discretion | Let planner choose later. | |

**User's choice:** Pytest-native aggregate gate.
**Notes:** This aligns with the existing test suite and avoids a new execution surface.

---

## Synthetic Fixture Policy

| Option | Description | Selected |
|--------|-------------|----------|
| Inline synthetic fixtures with optional helper | Preserve clear local constants; add helpers only if they reduce duplication. | yes |
| Central registry required | Force all tests to import shared fixtures. | |
| Leave fully decentralized | Avoid any helper even if duplication grows. | |

**User's choice:** Inline synthetic fixtures with optional helper.
**Notes:** The key requirement is auditability and no real sensitive data, not a specific fixture
architecture.

---

## Leakage Surfaces

| Option | Description | Selected |
|--------|-------------|----------|
| Broad v1 surface scan | Cover CLI, JSON, hooks, masking, diagnostics, failures, and Codex docs/claims. | yes |
| Only runtime outputs | Focus on stdout/stderr/JSON and skip docs/claim text. | |
| Existing coverage only | Rely on prior phase tests. | |

**User's choice:** Broad v1 surface scan.
**Notes:** TEST-02 explicitly mentions stdout, stderr, logs, hook JSON, masked payloads, and
exception messages, and Phase 4 added repository claim scanning.

---

## Coverage Priorities

| Option | Description | Selected |
|--------|-------------|----------|
| Fill gaps, avoid rewrites | Add missing tests around TEST-01..TEST-06 without reorganizing the suite. | yes |
| Refactor tests first | Consolidate test structure before adding coverage. | |
| Minimal smoke gate | Add only a small smoke test that invokes existing tests indirectly. | |

**User's choice:** Fill gaps, avoid rewrites.
**Notes:** This keeps Phase 5 focused and low-risk.

---

## Runtime Boundaries

| Option | Description | Selected |
|--------|-------------|----------|
| Local-only, no external services | No network, real Claude/Codex/Ollama, Presidio downloads, or protected-file reads. | yes |
| Include optional integrations if present | Probe local tools opportunistically. | |
| Require full external E2E | Run real clients/services. | |

**User's choice:** Local-only, no external services.
**Notes:** This preserves the privacy boundary and keeps the suite deterministic.

---

## the agent's Discretion

- Exact file split for Phase 5 tests.
- Whether to add a small test helper module.
- Whether requirement traceability appears in test docstrings, comments, or a summary artifact.

## Deferred Ideas

- CI configuration and formal coverage tooling.
- Real external-agent E2E tests.
- v2 integration adapters and enterprise release gates.
