# Phase 1: Package Foundation - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Convert the current script-oriented codebase into an installable Python package named `privguard`.
The phase delivers: a `pyproject.toml`, a flat `privguard/` module structure, a `privguard` CLI entry
point, and existing demo scripts separated from production code.

Scope anchor: packaging and structure only — detection logic, masking behavior, and hook enforcement
are Phase 2 and Phase 3 work.

</domain>

<decisions>
## Implementation Decisions

### Package identity
- **D-01:** Package name is `privguard` (Python import: `import privguard`, CLI: `privguard`).
  Replaces the previous working name "microsoft-presidio" / "privacy-guard".

### Package layout
- **D-02:** Flat module structure inside `privguard/` — one file per responsibility, no sub-folders.
  Files: `__init__.py`, `detection.py`, `masking.py`, `policy.py`, `hooks.py`, `cli.py`.
  Rationale: simpler to navigate, easier to copy or distribute if needed.

### Detection architecture
- **D-03:** Two-tier detection — lightweight regex core (no Presidio, based on existing
  `hooks/_pii_core.py`) as the default install; Presidio + spaCy Portuguese model as an optional
  `[full]` extras group. Default install stays small and fast.
- **D-04:** `pip install privguard` (core) must not download spaCy models or Presidio. Those are
  only pulled in with `pip install privguard[full]`.

### Dependency manifest
- **D-05:** Use `pyproject.toml` (PEP 517/518, setuptools backend). This is the file that makes
  `git clone` + `pip install -e .` work correctly on any machine.

### Distribution model
- **D-06:** The intended install flow on any machine (including the corporate machine) is:
  `git clone <repo>` → `pip install -e .`. No file copying, no internet access to PyPI after clone.
  The editable install keeps the package in sync with `git pull` updates.

### CLI usage pattern
- **D-07:** The `privguard` CLI is invoked automatically by Claude Code hooks — the user does not
  call it manually during normal coding. Phase 1 should expose at minimum a `privguard info`
  diagnostics command (shows version and active detectors) so the user can verify installation.

### Demo separation
- **D-08:** Existing demo scripts (`test_presidio_br.py`, `test_presidio.py`, `reversible_demo.py`,
  `ollama_local_demo.py`) do NOT need to be preserved or maintained. Move them to a `demos/`
  folder (or archive) so they are clearly separated from production `privguard/` code.
  They must not print raw sensitive values by default if left runnable.

### Claude's Discretion
- Internal module imports and `__init__.py` public API surface — planner decides what to expose.
- Whether `hooks/_pii_core.py` is moved into `privguard/detection.py` verbatim or refactored
  into a cleaner module boundary — planner decides based on what fits Phase 2 detection work.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` §Packaging — PKG-01 through PKG-04 define the acceptance criteria
  for this phase exactly.

### Existing production code to migrate
- `hooks/_pii_core.py` — standalone regex+validator (no Presidio). This is the core detection
  logic that becomes `privguard/detection.py` (lightweight tier).
- `hooks/pii_guard.py` — Claude Code UserPromptSubmit hook. Becomes `privguard/hooks.py` or
  stays in `hooks/` as a thin adapter that imports from `privguard`.
- `hooks/pre_tool_guard.py` — Claude Code PreToolUse hook. Same treatment as above.

### Demo scripts (separate, do not migrate to package)
- `test_presidio_br.py`, `test_presidio.py`, `reversible_demo.py`, `ollama_local_demo.py` —
  move to `demos/` folder. Not imported by the package.

No external ADRs or specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `hooks/_pii_core.py`: Production-quality standalone detector with `Hit` dataclass, `detect()`,
  and `redact()` functions. CPF/CNPJ validators with checksum. This becomes the lightweight
  detection core with minimal or zero changes.
- `hooks/pii_guard.py` / `pre_tool_guard.py`: Working Claude Code hooks that import `_pii_core`.
  Will become thin adapters that import from `privguard` after packaging.

### Established Patterns
- Detection returns typed `Hit` objects (kind, start, end, value, score) — preserve this API.
- Hook scripts are standalone Python files invoked by Claude Code directly — they do not need
  to become package entry points, just importers of `privguard`.

### Integration Points
- `hooks/` directory and `.claude/settings.json` hook config reference `hooks/*.py` directly.
  After packaging, hooks should still live at `hooks/*.py` but import from `privguard` instead
  of `_pii_core` directly.

</code_context>

<specifics>
## Specific Ideas

- User will use this package across two machines: personal PC (development) and corporate machine
  (usage). The distribution flow is `git clone` + `pip install -e .` — no manual file transfer.
- The corporate machine usage is primarily through Claude Code hooks running automatically —
  not manual CLI calls.
- Package must stay lightweight by default so the install on the corporate machine is fast and
  does not require downloading large NLP models unless explicitly requested.

</specifics>

<deferred>
## Deferred Ideas

- Presidio + spaCy full detection — available as `privguard[full]` extras, implemented in Phase 2.
- Additional CLI subcommands beyond diagnostics (e.g., `privguard check <text>`) — Phase 2+.
- Renaming the GitHub repository from `microsoft-presidio` to `privguard` — user action required
  (cannot be done from planning files). Suggested: do this before or during Phase 1 execution.

</deferred>

---

*Phase: 01-package-foundation*
*Context gathered: 2026-05-01*
