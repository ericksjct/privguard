# Phase 2: Privacy Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-02
**Phase:** 2-Privacy Core
**Areas discussed:** Detection Contract, Masking Guarantees, Policy Surface Model, Diagnostics Shape

---

## Detection Contract

| Option | Description | Selected |
|--------|-------------|----------|
| One complete detection behavior | User-facing product exposes comprehensive v1 detection by default. | yes |
| Two operating modes | User chooses between lightweight and full detection modes. | |
| Let planner decide | Planner decides whether modes are exposed. | |

**User's choice:** One complete detection behavior.
**Notes:** User asked whether the idea was to have two modes and clarified: "eu quero um modo só com abrangência completa."

---

## Masking Guarantees

| Option | Description | Selected |
|--------|-------------|----------|
| Block automatically on incomplete masking | Strictest behavior when leftovers remain. | |
| Warn and ask user | Pause so user can continue, retry masking, or block. | yes |
| Let planner decide | Planner picks the safety behavior. | |

**User's choice:** Warn and ask user.
**Notes:** User wants to be notified if any piece remains after masking so they can decide whether to continue or retry masking.

---

## Policy Surface Model

| Option | Description | Selected |
|--------|-------------|----------|
| Block by default | Unknown or unproven surfaces are blocked unless masking is proven. | yes |
| Warn by default | Unknown or unproven surfaces are allowed with warning. | |
| Let planner decide | Planner picks the default policy. | |

**User's choice:** Block by default.
**Notes:** After clarification, user confirmed that unknown surfaces or surfaces without guaranteed masking should block by default.

---

## Diagnostics Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Human-readable text | Terminal-friendly summaries. | yes |
| Structured JSON | Machine-readable summaries for tools/tests/hooks. | yes |
| Configurable formats | Format can be changed later through configuration. | yes |

**User's choice:** Keep both human-readable and JSON formats, configurable later.
**Notes:** User accepted both formats and wants the ability to alter the display format through config.

---

## the agent's Discretion

- Exact internal API shape for detector results, masking verification, policy decisions, and diagnostics.
- Exact internal composition of lightweight and Presidio-backed components, as long as the user sees one complete detection behavior.

## Deferred Ideas

- Claude enforcement details remain Phase 3.
- Codex compatibility evidence remains Phase 4.
