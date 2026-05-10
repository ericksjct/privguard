# Phase 1: Package Foundation - Research

**Researched:** 2026-05-01 [VERIFIED: local date/context]
**Domain:** Python packaging, CLI entry points, local privacy-tool module extraction [VERIFIED: .planning/phases/01-package-foundation/01-CONTEXT.md]
**Confidence:** HIGH for packaging structure, MEDIUM for optional Presidio extras because current latest `presidio-analyzer` excludes Python 3.14 [CITED: https://pypi.org/project/presidio-analyzer/]

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
## Deferred Ideas

- Presidio + spaCy full detection — available as `privguard[full]` extras, implemented in Phase 2.
- Additional CLI subcommands beyond diagnostics (e.g., `privguard check <text>`) — Phase 2+.
- Renaming the GitHub repository from `microsoft-presidio` to `privguard` — user action required
  (cannot be done from planning files). Suggested: do this before or during Phase 1 execution.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PKG-01 | Developer can install the project as a local Python package with a reproducible dependency manifest. [VERIFIED: .planning/REQUIREMENTS.md] | Use `pyproject.toml` with `[build-system]`, `[project]`, explicit package discovery, and editable-install verification. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/] |
| PKG-02 | Developer can run a `privacy-guard` CLI entry point for diagnostics and local masking checks. [VERIFIED: .planning/REQUIREMENTS.md] | Context supersedes the command name to `privguard`; implement `[project.scripts] privguard = "privguard.cli:main"` and at least `privguard info`. [VERIFIED: .planning/phases/01-package-foundation/01-CONTEXT.md] [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/] |
| PKG-03 | Reusable detection, masking, policy, and adapter code lives in importable package modules instead of root-level demo scripts. [VERIFIED: .planning/REQUIREMENTS.md] | Create flat `privguard/` modules and migrate lightweight hook behavior from `hooks/_pii_core.py`; keep hook scripts as thin adapters. [VERIFIED: rg/Get-Content hooks] |
| PKG-04 | Existing demos are separated from production code and do not print raw sensitive data by default. [VERIFIED: .planning/REQUIREMENTS.md] | Move root demo scripts to `demos/` and gate or redact raw-output paths before leaving them runnable. [VERIFIED: rg print/SAMPLES demo scripts] |
</phase_requirements>

## Summary

Phase 1 should be planned as a packaging and boundary extraction phase, not a detection-behavior rewrite. [VERIFIED: .planning/phases/01-package-foundation/01-CONTEXT.md] The default install should be a zero-runtime-dependency package using Python stdlib code moved from `hooks/_pii_core.py`, while Presidio, spaCy, and Portuguese NLP model work remain optional and largely deferred. [VERIFIED: hooks/_pii_core.py] [VERIFIED: .planning/phases/01-package-foundation/01-CONTEXT.md]

Use `pyproject.toml` with setuptools, `[project.scripts]` for the `privguard` command, and explicit flat package discovery for the new root-level `privguard/` package. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/] [CITED: https://setuptools.pypa.io/en/stable/userguide/package_discovery.html] The planner must account for a requirements/context mismatch: the requirements still say `privacy-guard`, but locked decision D-01 says the CLI is `privguard`. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/phases/01-package-foundation/01-CONTEXT.md]

**Primary recommendation:** Plan one package-foundation wave that creates `pyproject.toml`, `privguard/`, a minimal stdlib `privguard info` CLI, thin hook adapters, and quarantined demos with no default raw-value printing. [VERIFIED: local code + CONTEXT.md]

## Project Constraints (from AGENTS.md)

- Raw sensitive data must stay local and must not be sent to external LLM providers. [VERIFIED: AGENTS.md]
- Do not read `.env` or files under `data_sensivel/`; use synthetic fixtures only. [VERIFIED: AGENTS.md]
- Brazilian sensitive data types are first-class: CPF, CNPJ, bank/account data, names, contact data, credentials, and environment variables. [VERIFIED: AGENTS.md]
- v1 is outbound masking/blocking only; deanonymization is deferred/out of scope. [VERIFIED: AGENTS.md]
- If a surface cannot be safely rewritten, block rather than silently allow clear text. [VERIFIED: AGENTS.md]
- Reuse Python, Microsoft Presidio, spaCy Portuguese models, and lightweight hook scripts unless a phase proves a better boundary. [VERIFIED: AGENTS.md]
- Hook entry points currently fail open on malformed JSON and use exit code `2` for blocking violations. [VERIFIED: hooks/pii_guard.py] [VERIFIED: hooks/pre_tool_guard.py]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Package installation metadata | Local Python packaging | Developer workstation | `pyproject.toml` owns build metadata, dependencies, extras, and console script generation. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/] |
| CLI diagnostics | Local CLI | Package modules | `privguard.cli` should call importable package APIs and emit sanitized installation/detector status. [VERIFIED: CONTEXT.md] |
| Lightweight detection core | Local package module | Hook adapters | `hooks/_pii_core.py` already has stdlib regex validators and should become `privguard.detection`. [VERIFIED: hooks/_pii_core.py] |
| Hook compatibility | Hook adapter scripts | Local package module | `.claude/settings.json` invokes files under `hooks/`, so those scripts should remain and import `privguard`. [VERIFIED: .claude/settings.json] |
| Demo behavior | `demos/` scripts | Package modules only if safe | Root demos print raw original sample text today, so they must be separated and gated/redacted. [VERIFIED: rg print demo scripts] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib | 3.14.3 local | Runtime for core detector, masking placeholders, policy structs, JSON hook adapters, and CLI. | Existing production hook code uses only stdlib modules, keeping default install small. [VERIFIED: python --version] [VERIFIED: hooks/_pii_core.py] |
| setuptools | 82.0.1 latest/local | PEP 517 build backend for `pyproject.toml`. | PyPA guide documents setuptools as a standard backend, and local pip has 82.0.1 installed. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/] [VERIFIED: pip show setuptools] [VERIFIED: PyPI setuptools] |
| argparse | Python 3.14 stdlib | Implement `privguard info` without third-party CLI dependencies. | Python docs support subcommands via `add_subparsers()` and `set_defaults()`. [CITED: https://docs.python.org/3.14/library/argparse.html] |
| importlib.metadata | Python 3.14 stdlib | Report installed package version in `privguard info`. | Python docs expose `version()` for installed distributions. [CITED: https://docs.python.org/3.14/library/importlib.metadata.html] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| presidio-analyzer | 2.2.362 latest | Optional `[full]` detector in Phase 2. | Declare only under `[project.optional-dependencies].full`; do not import in core modules. [CITED: https://pypi.org/project/presidio-analyzer/] |
| presidio-anonymizer | 2.2.362 latest/local | Optional Presidio anonymizer in future full mode. | Keep optional; v1 package foundation does not need it for core CLI info. [CITED: https://pypi.org/project/presidio-anonymizer/] [VERIFIED: pip show presidio-anonymizer] |
| spacy | 3.8.14 latest, 3.8.13 local | Optional NLP backend for Presidio demos/full mode. | Use only in `[full]` extras or demos; never default core install. [CITED: https://pypi.org/project/spacy/] [VERIFIED: pip show spacy] |
| pytest | 9.0.3 latest, 9.0.2 local | Focused packaging smoke tests if planner adds them. | Use for install/import/CLI smoke tests with synthetic-only fixtures. [CITED: https://pypi.org/project/pytest/] [VERIFIED: pip show pytest] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| setuptools | Hatchling or uv-build | Context locked setuptools, so alternatives are out of scope. [VERIFIED: CONTEXT.md] |
| argparse | Click/Typer | Extra dependency and unnecessary for `info`; keep core zero-dependency. [VERIFIED: hooks stdlib usage] [ASSUMED] |
| flat `privguard/` package | `src/privguard/` layout | Context locked flat package layout. [VERIFIED: CONTEXT.md] |

**Installation:**
```bash
python -m pip install -e .
privguard info
```

**Version verification:** Latest versions checked on 2026-05-01: `setuptools` 82.0.1 published 2026-03-09, `presidio-analyzer` 2.2.362 published 2026-03-15, `presidio-anonymizer` 2.2.362 published 2026-03-15, `spacy` 3.8.14 published 2026-03-29, `pytest` 9.0.3 published 2026-04-07. [CITED: PyPI pages in Sources]

**Critical compatibility note:** `presidio-analyzer` 2.2.362 declares `Requires-Python <3.14, >=3.10`, while this machine is Python 3.14.3; do not make `presidio-analyzer` a default dependency for Phase 1. [CITED: https://pypi.org/project/presidio-analyzer/] [VERIFIED: python --version]

## Architecture Patterns

### System Architecture Diagram

```text
pip install -e .
  -> pyproject.toml
  -> setuptools build backend
  -> editable package metadata + console script
  -> privguard CLI
      -> info command
          -> importlib.metadata.version("privguard")
          -> privguard.detection available detectors
          -> sanitized stdout only

Claude hook event
  -> existing hooks/pii_guard.py or hooks/pre_tool_guard.py
  -> thin adapter import from privguard.*
  -> package detection / policy / masking functions
  -> sanitized allow/block response

Developer opens demo manually
  -> demos/*.py
  -> default mode avoids raw original sensitive-looking output
  -> optional explicit demo flag can show synthetic raw data if planner chooses
```

### Recommended Project Structure

```text
privguard/
├── __init__.py       # version/API exports
├── detection.py      # Hit, validators, PATTERNS, detect()
├── masking.py        # redact()/mask helpers, no deanonymization state
├── policy.py         # policy modes/reason codes scaffolding
├── hooks.py          # hook payload helpers/adapters
└── cli.py            # argparse main(), info command
hooks/
├── pii_guard.py      # thin Claude UserPromptSubmit script
└── pre_tool_guard.py # thin Claude PreToolUse script
demos/
├── test_presidio.py
├── test_presidio_br.py
├── reversible_demo.py
└── ollama_local_demo.py
pyproject.toml
```

### Pattern 1: PEP 621 Metadata and Console Script
**What:** Put build backend, project metadata, dependencies, extras, and CLI command in `pyproject.toml`. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/]
**When to use:** Always for this phase because D-05 locks `pyproject.toml` and setuptools. [VERIFIED: CONTEXT.md]
**Example:**
```toml
# Source: Python Packaging User Guide
[build-system]
requires = ["setuptools >= 77.0.3"]
build-backend = "setuptools.build_meta"

[project]
name = "privguard"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
full = [
  "presidio-analyzer==2.2.362; python_version < '3.14'",
  "presidio-anonymizer==2.2.362",
  "spacy==3.8.14",
]

[project.scripts]
privguard = "privguard.cli:main"

[tool.setuptools.packages.find]
include = ["privguard"]
```

### Pattern 2: Thin Hook Adapter
**What:** Keep `hooks/*.py` as Claude-invoked scripts, but import production APIs from `privguard`. [VERIFIED: .claude/settings.json] [VERIFIED: hooks/pii_guard.py]
**When to use:** Required because `.claude/settings.json` currently invokes `python "$CLAUDE_PROJECT_DIR/hooks/pii_guard.py"` and `hooks/pre_tool_guard.py`. [VERIFIED: .claude/settings.json]
**Example:**
```python
# Source: existing hook pattern, refactored for package import
from privguard.hooks import main_user_prompt

if __name__ == "__main__":
    raise SystemExit(main_user_prompt())
```

### Pattern 3: CLI Subcommands Dispatch to Functions
**What:** Use `argparse` subparsers with `set_defaults(func=...)`. [CITED: https://docs.python.org/3.14/library/argparse.html]
**When to use:** `privguard info` now, later `check`/`mask` commands without adding dependencies. [VERIFIED: CONTEXT.md]
**Example:**
```python
# Source: Python argparse docs pattern
parser = argparse.ArgumentParser(prog="privguard")
subparsers = parser.add_subparsers(required=True)
info = subparsers.add_parser("info")
info.set_defaults(func=cmd_info)
args = parser.parse_args(argv)
return args.func(args)
```

### Anti-Patterns to Avoid
- **Importing Presidio in core package import path:** breaks D-03/D-04 and may fail on Python 3.14 due current `presidio-analyzer` metadata. [VERIFIED: CONTEXT.md] [CITED: https://pypi.org/project/presidio-analyzer/]
- **Leaving root demo scripts named `test_*.py`:** they look like tests but are executable demos and currently print original sample text. [VERIFIED: rg demo scripts]
- **Hand-editing `.claude/settings.json` to call package internals directly:** keep hook file paths stable in Phase 1 and make scripts thin adapters. [VERIFIED: .claude/settings.json]
- **Printing `Hit.value` in diagnostics:** existing hooks do this today; Phase 1 package CLI and adapters should establish sanitized-output boundaries. [VERIFIED: hooks/pii_guard.py] [VERIFIED: hooks/pre_tool_guard.py]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Editable install metadata | Custom `sys.path` scripts or copy instructions | `pyproject.toml` + setuptools | pip/build backends own editable installs and metadata. [CITED: https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml.html] |
| CLI wrapper generation | Manual `.bat`/shell launchers | `[project.scripts]` | Packaging tools generate platform wrappers, including Windows console behavior. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/] |
| CLI parsing | Manual `sys.argv` branching | `argparse` | stdlib supports subcommands, help, and dispatch. [CITED: https://docs.python.org/3.14/library/argparse.html] |
| Version reporting | Hard-coded CLI version string only | `importlib.metadata.version()` with fallback | Installed distribution metadata is discoverable through stdlib. [CITED: https://docs.python.org/3.14/library/importlib.metadata.html] |
| Raw-value diagnostics | Printing matched substrings | Entity types/counts/offsets/reason codes | Requirements prohibit raw sensitive outputs in diagnostics. [VERIFIED: .planning/REQUIREMENTS.md] |

**Key insight:** Phase 1’s hardest problem is not packaging syntax; it is preventing the package foundation from preserving demo-era raw-output behavior as production behavior. [VERIFIED: rg demo scripts] [VERIFIED: .planning/REQUIREMENTS.md]

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None found; repo has no database/cache/application state, and sensitive `data_sensivel/` was not read. [VERIFIED: rg --files excluding sensitive paths] | None for Phase 1. [VERIFIED: local file scan] |
| Live service config | `.claude/settings.json` references `hooks/pii_guard.py` and `hooks/pre_tool_guard.py` directly. [VERIFIED: .claude/settings.json] | Keep those files or update config in a later Claude enforcement phase; Phase 1 should keep thin adapters to avoid breaking local hooks. [VERIFIED: CONTEXT.md] |
| OS-registered state | None found in repo; no Task Scheduler/pm2/system service config files were present. [VERIFIED: rg --files excluding sensitive paths] | None unless user has out-of-repo registrations, which were not inspected. [ASSUMED] |
| Secrets/env vars | `PII_GUARD_THRESHOLD` and `PII_GUARD_MODE` are read by `hooks/pii_guard.py`; `.env` exists but was not read. [VERIFIED: hooks/pii_guard.py] [VERIFIED: AGENTS.md] | Preserve env var behavior in adapter or document that Phase 2/3 owns policy changes. [VERIFIED: CONTEXT.md] |
| Build artifacts | `__pycache__/` exists; no package metadata directory exists because package is not installed from this repo yet. [VERIFIED: Get-ChildItem] | Ignore or clean only if planner wants tidy packaging verification; do not rely on it. [VERIFIED: local file scan] |

## Common Pitfalls

### Pitfall 1: Default Install Accidentally Pulls Full NLP Stack
**What goes wrong:** `pip install -e .` downloads Presidio/spaCy or fails on Python 3.14. [CITED: https://pypi.org/project/presidio-analyzer/]  
**Why it happens:** Presidio dependencies are put in `[project.dependencies]` instead of `[project.optional-dependencies].full`. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/]  
**How to avoid:** Keep core `dependencies = []` for Phase 1 and put full dependencies behind extras with Python markers. [VERIFIED: CONTEXT.md]  
**Warning signs:** `pip install -e .` resolves `spacy`, `presidio-analyzer`, or model downloads. [VERIFIED: CONTEXT.md]

### Pitfall 2: Presidio Latest Does Not Support Local Python 3.14
**What goes wrong:** Installing `[full]` on this machine may fail because `presidio-analyzer` 2.2.362 declares Python `<3.14`. [CITED: https://pypi.org/project/presidio-analyzer/] [VERIFIED: python --version]  
**Why it happens:** Current demos have packages installed locally, but package metadata for latest analyzer excludes Python 3.14. [VERIFIED: pip show presidio-analyzer] [CITED: https://pypi.org/project/presidio-analyzer/]  
**How to avoid:** Do not test Phase 1 success through `[full]`; document `[full]` as future optional and guard it with markers or an open question for Phase 2. [VERIFIED: CONTEXT.md]  
**Warning signs:** Planner includes `presidio-analyzer` as required dependency or makes full-mode install part of Phase 1 gate. [VERIFIED: CONTEXT.md]

### Pitfall 3: Production CLI Leaks Raw Matches
**What goes wrong:** `info`, diagnostics, or hook output prints `Hit.value`, original prompts, or sample text. [VERIFIED: hooks/pii_guard.py]  
**Why it happens:** Existing demo-era code prints original strings and hook summaries include raw values. [VERIFIED: rg demo scripts/hooks]  
**How to avoid:** Package CLI should emit detector names, counts, offsets, and sanitized placeholders only. [VERIFIED: .planning/REQUIREMENTS.md]  
**Warning signs:** Any `print(... h.value ...)`, `Original :`, or unredacted prompt in package modules. [VERIFIED: rg output]

### Pitfall 4: Root Demo Scripts Stay in Test Discovery Path
**What goes wrong:** Future pytest discovery may collect executable demo scripts named `test_presidio*.py`. [VERIFIED: rg --files] [ASSUMED]  
**Why it happens:** Files are named like tests but have `main()` demos and raw-output prints. [VERIFIED: test_presidio.py] [VERIFIED: test_presidio_br.py]  
**How to avoid:** Move them to `demos/`, rename if needed, and avoid default raw-output behavior. [VERIFIED: CONTEXT.md]  
**Warning signs:** Root still contains `test_presidio.py` or `test_presidio_br.py` after Phase 1. [VERIFIED: rg --files]

## Code Examples

### Minimal `privguard info`
```python
# Source: Python argparse + importlib.metadata docs
from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version


def cmd_info(_args: argparse.Namespace) -> int:
    try:
        package_version = version("privguard")
    except PackageNotFoundError:
        package_version = "0.0.0+local"
    print(f"privguard {package_version}")
    print("detectors: lightweight")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="privguard")
    subparsers = parser.add_subparsers(required=True)
    info = subparsers.add_parser("info")
    info.set_defaults(func=cmd_info)
    args = parser.parse_args(argv)
    return args.func(args)
```

### Sanitized Detection Summary Shape
```python
# Source: project requirements for sanitized diagnostics
def summarize_hits(hits):
    return [
        {"kind": hit.kind, "start": hit.start, "end": hit.end, "score": hit.score}
        for hit in hits
    ]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `setup.py` as primary packaging interface | `pyproject.toml` with `[build-system]` and `[project]` | PEP 517/518/621 era; current PyPA docs recommend `pyproject.toml`. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/] | Planner should create `pyproject.toml`, not `setup.py`. |
| Script-only local imports via `sys.path.insert()` | Importable package modules | Phase 1 locked decision. [VERIFIED: CONTEXT.md] | Hook scripts become adapters; reusable code lives under `privguard/`. |
| Demo scripts printing original examples | Production CLI emits sanitized diagnostics | v1 requirements. [VERIFIED: .planning/REQUIREMENTS.md] | Move/gate demos and never use their raw-output style in `privguard/`. |

**Deprecated/outdated:**
- `privacy-guard` command name in requirements is superseded by locked decision `privguard`. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: CONTEXT.md]
- Root-level `test_presidio*.py` as runnable demos is incompatible with package/test hygiene. [VERIFIED: rg --files] [VERIFIED: CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Click/Typer are unnecessary for `privguard info`. | Standard Stack | If CLI scope expands in Phase 1, argparse may be less ergonomic but still sufficient. |
| A2 | No out-of-repo OS registrations reference current hook scripts. | Runtime State Inventory | User may need to update manual shortcuts/tasks outside the repo. |
| A3 | Future pytest discovery could collect root demo files. | Common Pitfalls | If pytest config excludes them later, impact is low; moving demos is still required by context. |

## Open Questions (RESOLVED)

1. **Should Phase 1 provide a `privacy-guard` compatibility alias?**
   - What we know: Requirements say `privacy-guard`, but locked context says CLI is `privguard`. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: CONTEXT.md]
   - RESOLVED: Phase 1 provides no `privacy-guard` compatibility alias. Use only `privguard` per D-01 unless the user later requests an alias explicitly. [VERIFIED: CONTEXT.md]

2. **How should `[full]` extras handle Python 3.14?**
   - What we know: `presidio-analyzer` latest excludes Python 3.14, while local Python is 3.14.3. [CITED: https://pypi.org/project/presidio-analyzer/] [VERIFIED: python --version]
   - RESOLVED: `[full]` is optional/documented only in Phase 1 and is not a Phase 1 success gate. Default install remains lightweight; full Presidio/spaCy behavior is deferred to Phase 2 per D-03 and D-04. [VERIFIED: CONTEXT.md]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Package runtime and CLI | yes | 3.14.3 | None. [VERIFIED: python --version] |
| pip | Editable install | yes | 26.0.1 | None. [VERIFIED: python -m pip --version] |
| git | `git clone` install flow | yes | 2.53.0.windows.2 | Existing checkout already present. [VERIFIED: git --version] |
| setuptools | Build backend | yes | 82.0.1 | Pin build backend in `pyproject.toml`. [VERIFIED: pip show setuptools] |
| pytest | Optional packaging smoke tests | yes | 9.0.2 local; 9.0.3 latest | Use `python -m pytest` if tests are added. [VERIFIED: pip show pytest] [CITED: https://pypi.org/project/pytest/] |
| presidio-analyzer | Future `[full]` extra | installed locally | 2.2.359 local; 2.2.362 latest | Keep optional; not Phase 1 gate. [VERIFIED: pip show presidio-analyzer] [CITED: https://pypi.org/project/presidio-analyzer/] |
| spacy | Future `[full]` extra | installed locally | 3.8.13 local; 3.8.14 latest | Keep optional; not Phase 1 gate. [VERIFIED: pip show spacy] [CITED: https://pypi.org/project/spacy/] |

**Missing dependencies with no fallback:** None for Phase 1 core packaging. [VERIFIED: local environment audit]

**Missing dependencies with fallback:** Presidio/spaCy latest compatibility with Python 3.14 is not suitable for a Phase 1 gate; use lightweight core only. [CITED: https://pypi.org/project/presidio-analyzer/] [VERIFIED: CONTEXT.md]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No authentication surface in Phase 1 package foundation. [VERIFIED: ROADMAP.md] |
| V3 Session Management | no | No session state in Phase 1. [VERIFIED: ROADMAP.md] |
| V4 Access Control | yes | Hook adapters must preserve protected-path blocking boundaries; deeper enforcement is Phase 3. [VERIFIED: .claude/settings.json] [VERIFIED: ROADMAP.md] |
| V5 Input Validation | yes | CLI/hook payloads should parse structured input and fail safely/sanitized; current hooks parse JSON and tolerate malformed payloads. [VERIFIED: hooks/pii_guard.py] [VERIFIED: hooks/pre_tool_guard.py] |
| V6 Cryptography | no for Phase 1 core | Reversible encryption demo is not production v1 behavior and should stay out of default package behavior. [VERIFIED: reversible_demo.py] [VERIFIED: REQUIREMENTS.md] |
| V14 Configuration | yes | `pyproject.toml`, extras, and hook adapter paths become security-sensitive config because wrong defaults can send raw values or install heavy/full dependencies. [VERIFIED: CONTEXT.md] |

### Known Threat Patterns for Local Privacy Package

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Raw PII echoed by CLI/demo output | Information Disclosure | Sanitize diagnostics to type/count/offset/reason; never print `Hit.value`. [VERIFIED: REQUIREMENTS.md] |
| Optional full stack imported in default path | Denial of Service / Availability | Keep Presidio/spaCy imports out of `privguard.__init__`, `detection`, and `cli info`. [VERIFIED: CONTEXT.md] |
| Hook adapter path broken after refactor | Tampering / Information Disclosure | Preserve `hooks/*.py` entry files as adapters until Phase 3 revisits Claude config. [VERIFIED: .claude/settings.json] |
| Demo scripts imply production-safe behavior | Spoofing / Information Disclosure | Move to `demos/` and make raw-output behavior opt-in or remove it. [VERIFIED: CONTEXT.md] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/01-package-foundation/01-CONTEXT.md` - locked decisions D-01 through D-08 and deferred scope. [VERIFIED: local file]
- `.planning/REQUIREMENTS.md` - PKG-01 through PKG-04 and sanitized-output/privacy requirements. [VERIFIED: local file]
- `.planning/ROADMAP.md` - Phase 1 scope and phase boundaries. [VERIFIED: local file]
- `AGENTS.md` - project privacy/data hygiene constraints. [VERIFIED: local file]
- `hooks/_pii_core.py`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, `.claude/settings.json` - current implementation boundaries. [VERIFIED: local files]
- Python Packaging User Guide - `pyproject.toml`, dependencies, optional dependencies, scripts. [CITED: https://packaging.python.org/en/latest/guides/writing-pyproject-toml/]
- pip docs - `pyproject.toml` builds and editable installs. [CITED: https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml.html]
- setuptools docs - flat-layout package discovery. [CITED: https://setuptools.pypa.io/en/stable/userguide/package_discovery.html]
- Python docs - `argparse` and `importlib.metadata`. [CITED: https://docs.python.org/3.14/library/argparse.html] [CITED: https://docs.python.org/3.14/library/importlib.metadata.html]

### Secondary (MEDIUM confidence)
- PyPI package pages for current versions and Python requirements: `presidio-analyzer`, `presidio-anonymizer`, `spacy`, `pytest`, `setuptools`. [CITED: https://pypi.org/]
- PyPI `privacy-guard` page showing the old command/package name is occupied by another project. [CITED: https://pypi.org/project/privacy-guard/]

### Tertiary (LOW confidence)
- Assumptions A1-A3 in the Assumptions Log. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH for core packaging because it is based on locked context and PyPA/Python docs. [VERIFIED: CONTEXT.md] [CITED: packaging.python.org]
- Architecture: HIGH because module layout is locked and current hook paths are verified locally. [VERIFIED: CONTEXT.md] [VERIFIED: .claude/settings.json]
- Pitfalls: MEDIUM-HIGH because raw-output and dependency pitfalls are verified, while future pytest behavior is partly assumed. [VERIFIED: rg output] [ASSUMED]

**Research date:** 2026-05-01 [VERIFIED: current_date]
**Valid until:** 2026-05-31 for packaging docs; recheck PyPI versions and Presidio Python support before implementing `[full]` extras. [ASSUMED]
