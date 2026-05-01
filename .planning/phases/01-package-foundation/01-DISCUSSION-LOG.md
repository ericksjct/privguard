# Phase 1: Package Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 01-package-foundation
**Areas discussed:** Package layout, Dependency manifest, Distribution model, CLI usage, Demo separation, Project name

---

## Package Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Flat structure | `privguard/` with one file per responsibility, no sub-folders | ✓ |
| Nested by responsibility | Sub-folders for detection/, masking/, hooks/adapters/ | |

**User's choice:** Flat structure
**Notes:** User prioritized portability and simplicity. Flat layout is easier to navigate and carry.

---

## Dependency Management

| Option | Description | Selected |
|--------|-------------|----------|
| Lightweight core + optional Presidio | Core uses regex only; Presidio as `[full]` extras | ✓ |
| Presidio as hard dependency | Always installs Presidio + spaCy | |

**User's choice:** Two-tier — lightweight default, Presidio optional
**Notes:** User explicitly wants the package to be "leve" (lightweight) and fast, without heavy model downloads on install.

---

## Distribution Model

| Option | Description | Selected |
|--------|-------------|----------|
| git clone + pip install -e . | Clone repo, install editable. Works offline after clone. | ✓ |
| .whl file copy | Build wheel on personal PC, copy to corporate machine | |
| Copy privacy_guard/ folder | Direct folder copy, no installation | |

**User's choice:** git clone + pip install -e .
**Notes:** User develops on personal PC and uses on corporate machine. Prefers git clone as the distribution mechanism — simpler, always up to date with git pull.

---

## CLI Usage Pattern

| Option | Description | Selected |
|--------|-------------|----------|
| Automatic via hooks | Claude Code hooks invoke the guard automatically | ✓ |
| Manual CLI invocation | User calls `privguard check "text"` manually | |

**User's choice:** Automatic via hooks
**Notes:** User does not want to call the CLI manually during normal work. A diagnostics command (`privguard info`) is still useful to verify installation.

---

## Demo Separation

| Option | Description | Selected |
|--------|-------------|----------|
| Move to demos/ | Separate folder, not part of package, not maintained | ✓ |
| Keep at root with warnings | Less work but mixes demo with production | |

**User's choice:** Move to demos/ (not maintained)
**Notes:** User confirmed existing demos do not need to be preserved or kept runnable.

---

## Project Name

| Option | Description | Selected |
|--------|-------------|----------|
| privguard | Short, clear, privacy + guard | ✓ |
| sentinela | Portuguese for sentinel | |
| escudo | Portuguese for shield | |
| privaguard | Longer variant | |

**User's choice:** `privguard`
**Notes:** User recognized the project needed its own identity separate from "microsoft-presidio" (the underlying library being used).

---

## Claude's Discretion

- Internal module imports and `__init__.py` public API surface
- Whether `hooks/_pii_core.py` is moved verbatim or refactored
