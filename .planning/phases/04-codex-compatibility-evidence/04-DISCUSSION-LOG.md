# Phase 4: Codex Compatibility Evidence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-03
**Phase:** 4-Codex Compatibility Evidence
**Areas discussed:** Evidence bar, Support labels, Deliverable shape

---

## Gray Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| All areas | Cover evidence standard, support labels, and artifact shape before writing context. | ✓ |
| Evidence bar | Focus on what tests/docs/probes count as enough Codex compatibility evidence. | |
| Support labels | Focus on how strict Codex supported/experimental/block-only/unsupported labels should be. | |

**User's choice:** Interactive selection UI was unavailable, so the workflow fallback defaulted to
all key areas.
**Notes:** The discussion stayed within the Phase 4 boundary.

---

## Evidence Bar

| Option | Description | Selected |
|--------|-------------|----------|
| Strict proof | Official docs plus local installed-Codex probes plus synthetic end-to-end evidence. No positive support label without executable proof. | ✓ |
| Docs + manual evidence | Official docs/repo/issues plus documented manual testing notes are enough for an experimental label. | |
| Documentation only | Phase 4 mainly produces a compatibility assessment and avoids building probes/tests yet. | |

**User's choice:** Strict proof.
**Notes:** Positive Codex support requires current documented behavior, local probing where feasible,
and synthetic evidence for the specific surface.

---

## Support Labels

| Option | Description | Selected |
|--------|-------------|----------|
| Block-only | Safe to say Codex can block a surface, but explicitly no automatic masking. | ✓ |
| Experimental | Use when blocking works locally but hook coverage or version behavior is still unsettled. | ✓ |
| Unsupported | Anything without proven rewrite stays unsupported for v1 Codex claims. | ✓ |

**User's choice:** "Todos os critérios que usamos anteriormente deve ser aplicado aqui para o
codex também."
**Notes:** The decision is policy parity: apply the same Phase 2/3 criteria to Codex. That means
block-only when only blocking is proven, experimental when coverage is uncertain, unsupported when
protection cannot be proven, and no automatic masking claim without verified rewrite.

---

## Deliverable Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Docs + matrix + tests | Assessment in Markdown, compatibility matrix, and tests that prevent improper Codex masking claims. | ✓ |
| Docs + matrix only | Phase focused on documentation/evidence, without automated tests. | |
| CLI also | Add a command such as `privguard codex doctor` if there is enough local surface to validate. | |

**User's choice:** Docs + matrix + tests.
**Notes:** A Codex doctor command remains optional and should only be added if a stable local
validation surface exists.

---

## the agent's Discretion

- Exact document path/name for the compatibility assessment.
- Exact implementation of claim-prevention checks.
- Whether local Codex probing is implemented as pytest, script, CLI, or evidence appendix.
- Whether `privguard codex doctor` is worth adding in Phase 4.

## Deferred Ideas

- Broad IDE-agent support, local proxy mode, LangChain/LlamaIndex adapters, and enterprise policy
  distribution remain future work.
