# Phase 7: Project README + Repo Hygiene - Research

**Researched:** 2026-05-08
**Domain:** Bilingual technical documentation (EN + pt-BR) + stdlib-only repo cleanup CLI
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**README structure**

- **D-01:** Two separate files at repo root: `README.md` (English, primary) and
  `README.pt-BR.md` (Portuguese). Each file contains the full content for its language.
  Single-file bilingual sections are rejected.
- **D-02:** Cross-language switcher is a badge-style row above the H1 in each README:
  `[🇺🇸 English](README.md) | [🇧🇷 Português](README.pt-BR.md)`. Plain markdown link
  syntax with country-flag emoji prefixes. No shields.io badges in v1.
- **D-03:** Both READMEs MUST update together in every PR. PRs touching `README.md` MUST
  also update `README.pt-BR.md` (or declare "translation pending" in the PR body).
  Enforced socially (no CI for v1).
- **D-04:** README scope = phase-criteria minimum + walkthrough + FAQ. Required sections
  in BOTH languages:
  1. Install (`pip install privguard`, `pip install privguard[full]` with Python 3.14
     gating note linking to `docs/install.md`).
  2. Quickstart "in 60 seconds" — synthetic CPF/CNPJ masking example via `privguard mask`.
  3. CLI usage (`privguard scan`, `privguard mask`, `privguard policy-check`,
     `privguard claude doctor`, `privguard cleanup`).
  4. Claude Code hook setup (`.claude/settings.json` snippet wiring `UserPromptSubmit`
     and `PreToolUse` to package-backed entry points using `python -m` form).
  5. Codex / Claude capabilities matrix (D-06 condensed table + footer link).
  6. What privguard does NOT do — explicit non-goals: hosted SaaS, deanonymization,
     LangChain/LlamaIndex adapters, unsupported clients, real-data fixtures.
  7. Synthetic-fixture-only policy statement.
  8. FAQ — required entries: "Does this work with Codex?", "What if a CPF is missed?",
     "Why does it block instead of warn?", "How do I extend the cleanup patterns?"
  9. "For coding agents working in this repo, see [AGENTS.md](AGENTS.md)" line.
- **D-05:** README and `AGENTS.md` stay independent. AGENTS.md is NOT modified by
  Phase 7. Single link, no anchor coupling, no content promotion.
- **D-06:** Capabilities matrix in README is a condensed 4-row table (rows: Claude
  `UserPromptSubmit` block-supported, Claude `PreToolUse` block-supported, Codex
  prompt experimental block-only, Codex tool experimental block-only). Footer link
  to `docs/codex-compatibility.md` for evidence. NO "rewrite-capable" or "automatic
  masking" claims.

**Cleanup command**

- **D-07:** Cleanup is a `privguard cleanup` subcommand (NOT a standalone script).
  Logic in `privguard/cleanup.py`; wiring in `privguard/cli.py` alongside the existing
  `scan`, `mask`, `policy-check`, `claude doctor` subparsers.
- **D-08:** Default patterns in `pyproject.toml` `[tool.privguard.cleanup]`:
  ```toml
  patterns = [
      "__pycache__/", "*.py[cod]", ".pytest_cache/", ".coverage",
      "htmlcov/", "dist/", "build/", "*.egg-info/",
  ]
  ```
  Maintainer adds new patterns by appending to this list.
- **D-09:** Protected list is HARDCODED in `privguard/cleanup.py` as a module-level
  constant (cannot be overridden, shrunk, or extended via `pyproject.toml`):
  ```python
  _PROTECTED = (
      ".env", ".env.*", "data_sensivel/", ".planning/", ".git/",
      "privguard/", "tests/", "hooks/", "demos/", "docs/",
      "pyproject.toml", "AGENTS.md", "README.md", "README.pt-BR.md",
  )
  ```
  Any path matching a protected entry (or under a protected directory) is skipped
  with a warning, regardless of whether it also matches a cleanup pattern.
- **D-10:** Dry-run output is grouped by pattern with byte sizes:
  ```
  [dry-run] would delete (3 paths, 1.4 MB total):
    __pycache__/        2 dirs / 47 files / 1.2 MB
    .pytest_cache/      1 dir  / 12 files / 180 KB
    *.pyc               3 files / 24 KB
  Run with --apply to delete.
  ```
  No `--json` mode in v1 (deferred). Output sanitized — paths only, never file
  contents (extends Phase 2 POL-04 to cleanup).
- **D-11:** Repo-root guard is MANDATORY. Before any scan, the script verifies BOTH:
  (1) `.git/` directory exists in cwd, AND (2) `pyproject.toml` exists in cwd and
  contains `name = "privguard"` under `[project]`. If either check fails, exit code 2.
- **D-12:** `--apply` alone deletes — no further interactive prompt. No `--yes` flag.
  Dry-run default + repo-root guard + protected list + symlink refusal are the
  safety net.
- **D-13:** Refuse to delete symlinks AND refuse to follow them. If a path matched
  by a cleanup pattern is a symlink, or contains a symlink in its tree during
  recursive deletion: skip it, emit warning, continue. Skipped symlinks do NOT
  count as failures (exit 0).
- **D-14:** Exit codes follow privguard's CLI convention:
  - `0` — Dry-run preview printed cleanly OR `--apply` deleted everything
    matched successfully.
  - `1` — `--apply` attempted to delete and failed (permissions, OS error).
  - `2` — Misuse: not in privguard repo root (D-11 failed), malformed `pyproject.toml`,
    `[tool.privguard.cleanup]` missing or invalid, conflicting/unknown flag.

### Claude's Discretion

- Section ordering within each README (D-04 lists sections; order, depth, TOC
  placement, intra-section flow are planner's choice as long as all sections appear).
- FAQ wording — D-04 fixes the four required questions; answers drafted from
  PROJECT.md, REQUIREMENTS.md, and prior phase verifications.
- Synthetic CPF/CNPJ values used in masking demo — must be obviously synthetic
  AND checksum-valid. Reuse existing `tests/` fixtures rather than inventing new ones.
- Quickstart code-block style (single block vs. multi-step prose).
- `docs/install.md` consolidation — README install section may either summarize and
  link to `docs/install.md`, OR fold the install.md content into README and slim
  `docs/install.md` to a stub. Pick whichever keeps drift risk lowest.
- Cleanup CLI flag names beyond `--apply` — `--verbose` / `-v`, `--dry-run` (explicit
  alias), `--quiet` are at planner's discretion. ONLY mandatory flag is `--apply`.
- Implementation language for the cleanup module — pure stdlib Python, no new deps.
  Use `pathlib`, `fnmatch`, `tomllib`, `os.walk`. Planner picks safest stdlib pattern;
  no `shutil.rmtree(..., onerror=)` fragility.

### Deferred Ideas (OUT OF SCOPE)

- Linter cache patterns in cleanup defaults (`.mypy_cache/`, `.ruff_cache/`, `.tox/`,
  `.nox/`) — add when those tools enter `pyproject.toml`.
- `--json` output mode for cleanup — v2 candidate (ENT-02 audit-safe telemetry).
- `--yes` / interactive `y/N` confirmation — explicitly rejected (D-12).
- Drift-prevention regression test for EN/pt-BR README parity — out of scope for v1.
- README badges (CI status, license, PyPI version) — no CI / no PyPI / no license
  decision yet.
- LICENSE file and CHANGELOG.md — not in Phase 7 scope; should land before any
  public PyPI publication.
- Promoting AGENTS.md content into structured `docs/` files (e.g.
  `docs/architecture.md`, `docs/threat-model.md`) — explicitly deferred (D-05).
- Status badges on capabilities matrix (shields.io style) — explicitly rejected.
- Cleanup-output forbidden-value gate (assert no synthetic CPF leaks even if one
  appears in a path string) — defensible-extension idea; defer to v2 unless trivially
  cheap.
- Internationalization beyond pt-BR (Spanish, etc.) — out of scope per PROJECT.md
  Brazil-first focus.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOC-01 | Project includes a bilingual top-level README (English primary `README.md`, Portuguese secondary `README.pt-BR.md`) covering installation, CLI usage, Claude Code hook setup, the Claude/Codex capabilities matrix, what the guard does *not* do, and the synthetic-fixture-only policy. | D-01..D-06 lock structure, scope, switcher, paired-update rule, AGENTS.md independence, and capabilities-matrix shape. Research provides verified placeholder vocabulary, existing synthetic CPF/CNPJ values, current `docs/install.md` and `docs/codex-compatibility.md` shape, the actual `.claude/settings.json` hook wiring pattern to translate to a `python -m` form, and Brazilian Portuguese translation conventions. |
| MAINT-01 | Repo includes a config-driven cleanup mechanism with patterns declared in `pyproject.toml` (`[tool.privguard.cleanup]`), a hard-coded protected list (`.env`, `data_sensivel/`, `.planning/`, `.git/`, source directories) the script can never delete, and a dry-run-by-default contract that requires an explicit `--apply` flag before deletion. | D-07..D-14 lock command shape, default patterns, protected list, dry-run format, repo-root guard, no-prompt-on-apply, symlink refusal, and exit codes. Research provides the existing argparse subparser registration pattern in `privguard/cli.py` to mirror, the current `.gitignore` contents and exact deltas needed for parity, the stdlib API surface (`tomllib`, `pathlib`, `fnmatch`, `os.walk` with `followlinks=False`, `os.path.islink`), and a flagged Python 3.10 / `tomllib` mismatch the planner must address. |
</phase_requirements>

## Summary

Phase 7 is documentation + tooling, not new product behavior. CONTEXT.md locks 14
decisions across the README structure and the `privguard cleanup` command, leaving
research to fill in implementation gaps the planner needs to write tasks.

The implementation gaps fall into three buckets:

1. **README content scaffolding** — exact synthetic CPF/CNPJ values and placeholder
   tokens to reuse (so the masking demo doesn't invent strings that look real or use
   tokens that don't match Phase 2's vocabulary), the current `docs/install.md` and
   `docs/codex-compatibility.md` shape (so the README either summarizes-and-links or
   absorbs-and-stubs without drift), and the actual `.claude/settings.json` shape
   (so the README hook-setup snippet matches what users will actually paste).

2. **Cleanup module implementation** — current `privguard/cli.py` argparse pattern
   (so `cleanup` is wired identically to `scan`/`mask`/`policy-check`/`claude doctor`),
   the current `.gitignore` contents and exact missing patterns (so the parity edit
   is a precise three-line addition rather than a rewrite), stdlib reference patterns
   for safe directory deletion that refuses symlinks (so the planner doesn't reach
   for `shutil.rmtree(onerror=)` and miss the symlink-refusal contract), and the
   repo-root guard pattern using `tomllib`.

3. **A flagged Python compatibility risk** — `tomllib` is stdlib in Python 3.11+,
   but `pyproject.toml` declares `requires-python = ">=3.10"`. The planner must
   choose a fallback strategy (vendored `tomli`, raise floor to 3.11, or bare-minimum
   regex parse for `[project] name = "privguard"`); see Common Pitfalls.

**Primary recommendation:** Plan five edits — `README.md`, `README.pt-BR.md`,
`pyproject.toml` (add `[tool.privguard.cleanup]`), `.gitignore` (add three lines),
`privguard/cleanup.py` (new), `privguard/cli.py` (one subparser), and
`tests/test_cleanup.py` (recommended but not strictly required by success criteria).
Resolve the `tomllib` Python-version mismatch up front rather than discover it at
verification time.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Bilingual README authoring (EN/pt-BR) | Repo-root documentation | — | Top-level READMEs are by convention at repo root; GitHub renders `README.md` automatically. |
| Cross-language switcher | Repo-root documentation | — | Two static markdown files cross-linking each other. |
| Capabilities matrix (condensed) in README | Repo-root documentation | `docs/codex-compatibility.md` (evidence source) | README is the human entry point; `docs/` holds verifiable evidence. README condensed table mirrors but does not duplicate. |
| Cleanup configuration declaration | `pyproject.toml` (project metadata) | — | Standard PEP 621 / tool-table location for project-scoped config. |
| Cleanup pattern matching + safe deletion | Python package (`privguard/cleanup.py`) | — | Phase 1 D-01 locked package-based code; subcommand follows Phase 6 PKG-02 canonical CLI surface. |
| Cleanup CLI dispatch | Python package (`privguard/cli.py`) | `privguard/cleanup.py` (logic) | Existing argparse pattern used by `scan`, `mask`, `policy-check`, `claude doctor`. |
| Protected-list enforcement | Python package (hardcoded module constant) | — | D-09 requires hardcoded list; not pyproject-overridable to prevent malicious / careless PR shrinkage. |
| `.gitignore` parity | Repo-root configuration | `pyproject.toml [tool.privguard.cleanup]` (source of truth for patterns) | `.gitignore` is consumed by `git`; no shared source-of-truth tool exists in v1. Manual parity per D-08 success criterion #5. |

## Project Constraints (from PROJECT.md and prior phases)

These constrain Phase 7 the same way locked decisions do; the planner must verify
compliance with each.

- **Brazil-first locale priority** [CITED: `.planning/PROJECT.md` Constraints] — pt-BR
  is a first-class deliverable, not a translation afterthought. D-03 paired-update
  rule reinforces this.
- **Fail-closed safety default** [CITED: `.planning/PROJECT.md` Constraints] — the
  cleanup command's dry-run default and `--apply` opt-in directly mirror this.
- **Synthetic-fixtures-only data hygiene** [CITED: `.planning/PROJECT.md` Constraints]
  — README's masking demo MUST use synthetic CPF/CNPJ values that are checksum-valid
  but obviously fake. Reuse existing `tests/test_v1_regression_gate.py:46-47` values.
- **Package-based code organization** [CITED: Phase 1 D-01 + `.planning/PROJECT.md`]
  — cleanup logic lives in `privguard/cleanup.py`, not in `scripts/`.
- **Sanitized diagnostics** [CITED: Phase 2 POL-04, extended in CONTEXT.md D-10] —
  cleanup output prints paths and counts only, never file contents.
- **No "automatic masking" claim for any surface without proof** [CITED: Phase 4
  CDX-03, `docs/codex-compatibility.md`] — README capabilities matrix uses only the
  vocabulary in `privguard/codex.py CODEX_COMPATIBILITY` (block-supported,
  experimental block-only, observe-only, unsupported). No "rewrite-capable" or
  "automatic masking" labels appear in the README.
- **Canonical CLI name is `privguard`** [CITED: Phase 6 D-04, `pyproject.toml:24`] —
  no occurrences of `privacy-guard` anywhere in either README.

## Standard Stack

### Core (no new dependencies — stdlib only per CONTEXT.md "Claude's Discretion")

| Module | Version | Purpose | Why Standard |
|--------|---------|---------|--------------|
| `argparse` | stdlib | Subcommand registration in `privguard/cli.py` | Already used for `scan`, `mask`, `policy-check`, `claude doctor`. [VERIFIED: read `privguard/cli.py:108-146`] |
| `pathlib` | stdlib | Path manipulation, repo-root guard | Standard cross-platform path API. [CITED: docs.python.org/3/library/pathlib.html] |
| `fnmatch` | stdlib | Glob-style pattern matching for `*.py[cod]`, `*.egg-info/`, `.env.*` | Filename-glob matching that mirrors shell glob semantics. [CITED: docs.python.org/3/library/fnmatch.html] |
| `tomllib` | stdlib (Python 3.11+) | Read `[tool.privguard.cleanup]` from `pyproject.toml` | Official PEP 680 stdlib TOML reader. [CITED: docs.python.org/3/library/tomllib.html] **NOTE: project floor is 3.10 — see Common Pitfalls Pitfall 1.** |
| `os.walk` | stdlib | Recursive directory traversal with `followlinks=False` | Standard recursive walker; `followlinks=False` is the default and enforces D-13 behavior. [CITED: docs.python.org/3/library/os.html#os.walk] |
| `os.path.islink` / `pathlib.Path.is_symlink()` | stdlib | Per-path symlink detection for D-13 | Standard symlink check (does not follow). [CITED: docs.python.org/3/library/os.path.html#os.path.islink] |
| `shutil.rmtree` | stdlib | Directory deletion when `--apply` and not a symlink | Standard recursive directory removal. [CITED: docs.python.org/3/library/shutil.html#shutil.rmtree] |
| `pytest` | already configured | Testing the cleanup subcommand (recommended) | Phase 5 regression gate is pytest-native; reuse. [VERIFIED: `tests/test_v1_regression_gate.py` runs under `pytest`] |

### Supporting

| Module | Purpose | When to Use |
|--------|---------|-------------|
| `dataclasses.dataclass` | Group dry-run preview entries (path, kind, size, file_count, dir_count, symlink-skip) | If the planner wants typed in-memory rows for the dry-run formatter; existing modules use this style (`Hit`, `MaskResult`, `PolicyDecision`). [VERIFIED: `privguard/detection.py:11`, `privguard/masking.py:13`] |
| `re` | Repo-root guard parsing of `[project] name = "privguard"` IF planner chooses regex over `tomllib` for the guard step | Only relevant if planner picks the regex fallback for Python 3.10 compat (Pitfall 1, Option C). |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `tomllib` (stdlib 3.11+) | `tomli` (PyPI) backport for Python 3.10 | New runtime dependency contradicts "no new deps" CONTEXT.md note. Workable but adds first-ever runtime dep — currently `pyproject.toml:9` lists `dependencies = []`. |
| `tomllib` | Bump `requires-python` to `>=3.11` | Drops Python 3.10 support; needs explicit user/maintainer call (project currently advertises 3.10 in `pyproject.toml:8` and `docs/install.md:11`). |
| `tomllib` | Hand-rolled minimal TOML parser | Don't hand-roll TOML — see "Don't Hand-Roll" section. |
| `shutil.rmtree(onerror=...)` | Pre-walk with `os.walk`, refuse symlinks, then `shutil.rmtree(non-symlink)` | CONTEXT.md "Claude's Discretion" explicitly calls out "no `shutil.rmtree(..., onerror=)` fragility" — picks the safer pre-validate-then-delete pattern. |
| `glob.glob` | `fnmatch.fnmatch` per path entry | `fnmatch` matches a single name against a pattern; `glob` walks the filesystem. The cleanup walker traverses with `os.walk` and uses `fnmatch` per name — cleaner than running `glob.glob` per pattern (which would re-walk). [CITED: docs.python.org/3/library/fnmatch.html] |

**Installation:**

No new dependencies. The cleanup module imports only stdlib. The `[tool.privguard.cleanup]`
table is read by privguard itself, NOT by `pip` (this is a privguard-private convention,
not PEP 621 metadata).

**Version verification:** Not applicable (no new packages installed).

## Architecture Patterns

### System Architecture Diagram

```
                         ┌────────────────────────────────────┐
                         │ User runs `privguard cleanup`      │
                         │ (or `privguard cleanup --apply`)   │
                         └────────────────┬───────────────────┘
                                          │
                                          ▼
                    ┌──────────────────────────────────────────┐
                    │ privguard/cli.py                         │
                    │ argparse dispatcher → cmd_cleanup(args)  │
                    └────────────────┬─────────────────────────┘
                                     │
                                     ▼
            ┌──────────────────────────────────────────────────────┐
            │ privguard/cleanup.py — main(args)                    │
            │                                                      │
            │  1. Repo-root guard (D-11)                           │
            │     ├─ cwd has .git/ ? ──── no ─→ exit 2             │
            │     └─ cwd/pyproject.toml has                        │
            │        [project] name="privguard" ?  no ─→ exit 2    │
            │                                                      │
            │  2. Read [tool.privguard.cleanup].patterns           │
            │     from pyproject.toml via tomllib (D-08)           │
            │     │                                                │
            │     └─ missing/invalid ─→ exit 2                     │
            │                                                      │
            │  3. Build candidate set                              │
            │     ├─ os.walk(., followlinks=False)                 │
            │     ├─ for each entry, classify against patterns     │
            │     │   • trailing "/" → directory tree match        │
            │     │   • no trailing "/" → fnmatch on basename      │
            │     ├─ filter out anything matching _PROTECTED       │
            │     │   (or under a protected directory) (D-09)      │
            │     └─ flag symlinks as "skipped: symlink" (D-13)    │
            │                                                      │
            │  4. Mode branch                                      │
            │     ├─ default (dry-run) ─→ format grouped preview   │
            │     │                       with sizes (D-10) → exit 0 │
            │     └─ --apply ─→ for each non-symlink candidate:    │
            │                    • re-check symlink at delete time │
            │                    • shutil.rmtree(dir) or .unlink()│
            │                    • on OS error → exit 1            │
            │                   on success → exit 0                │
            └──────────────────────────────────────────────────────┘

   External: pyproject.toml [tool.privguard.cleanup].patterns (config)
             .gitignore (parity, NOT consumed by cleanup at runtime)
```

### Recommended Project Structure

```
.
├── README.md                  # NEW — English-primary, full content (D-01)
├── README.pt-BR.md            # NEW — pt-BR translation, full content (D-01)
├── AGENTS.md                  # UNCHANGED — referenced via single link (D-05)
├── .gitignore                 # MODIFIED — add dist/, build/, *.egg-info/ (success #5)
├── pyproject.toml             # MODIFIED — add [tool.privguard.cleanup] (D-08)
├── privguard/
│   ├── cli.py                 # MODIFIED — register cleanup subparser (D-07)
│   ├── cleanup.py             # NEW — logic, _PROTECTED constant, dry-run formatter
│   └── ... (unchanged: detection.py, masking.py, policy.py, ...)
├── tests/
│   └── test_cleanup.py        # NEW (recommended, Claude's Discretion)
└── docs/
    ├── install.md             # REFERENCED — planner picks summarize-and-link
    │                            vs. absorb-and-slim (D-04 / Discretion)
    └── codex-compatibility.md # UNCHANGED — README links from D-06 footer
```

### Pattern 1: argparse subparser registration (mirror existing `cli.py`)

**What:** Add a `cleanup` subparser inside the existing `add_subparsers()` block.
**When to use:** New top-level subcommand (D-07).
**Example (mirrors existing `scan`/`mask`/`policy-check` pattern):**

```python
# Source: privguard/cli.py:108-146 [VERIFIED: read 2026-05-08]
# Add inside main() alongside existing subparsers:
cleanup = subparsers.add_parser("cleanup")
cleanup.add_argument(
    "--apply",
    action="store_true",
    help="Actually delete (default is dry-run preview).",
)
# Optional flags at planner's discretion (Claude's Discretion):
cleanup.add_argument("--verbose", "-v", action="store_true")
cleanup.add_argument("--dry-run", action="store_true",
                     help="Explicit alias for default behavior.")
cleanup.set_defaults(func=cmd_cleanup)
```

The dispatcher already calls `args.func(args)` at line 146; nothing else is needed
in `cli.py` besides the import of `cmd_cleanup` (or in-line definition that
delegates to `privguard.cleanup.main`).

### Pattern 2: Repo-root guard via `tomllib`

**What:** Verify cwd is the privguard repo root before doing anything destructive.
**When to use:** First action in `cleanup.main()` per D-11.
**Example:**

```python
# Source: derived from D-11; uses tomllib API [CITED: docs.python.org/3/library/tomllib.html]
from pathlib import Path
import sys
import tomllib  # 3.11+ — see Common Pitfalls Pitfall 1

def _verify_repo_root(cwd: Path) -> None:
    if not (cwd / ".git").is_dir():
        print("error: not in a git repository", file=sys.stderr)
        raise SystemExit(2)
    pyproject = cwd / "pyproject.toml"
    if not pyproject.is_file():
        print("error: pyproject.toml not found in cwd", file=sys.stderr)
        raise SystemExit(2)
    with pyproject.open("rb") as f:
        data = tomllib.load(f)
    if data.get("project", {}).get("name") != "privguard":
        print("error: pyproject.toml does not declare name = \"privguard\"",
              file=sys.stderr)
        raise SystemExit(2)
```

### Pattern 3: Pattern matching with directory-vs-file semantics

**What:** Trailing `/` means "match directory tree (recursive)"; no trailing `/`
means "fnmatch basename" (CONTEXT.md "Specifics" + D-08 examples).
**When to use:** Classifying each candidate against `[tool.privguard.cleanup].patterns`.
**Example:**

```python
# Source: derived from CONTEXT.md "Specifics" + fnmatch docs
# [CITED: docs.python.org/3/library/fnmatch.html]
import fnmatch
from pathlib import Path

def _matches(path: Path, pattern: str) -> bool:
    is_dir_pattern = pattern.endswith("/")
    bare = pattern.rstrip("/")
    if is_dir_pattern:
        # Directory tree match — only match directories with this name
        return path.is_dir() and fnmatch.fnmatch(path.name, bare)
    # File glob match — match basename against pattern (e.g. *.py[cod])
    return path.is_file() and fnmatch.fnmatch(path.name, bare)
```

Note: `fnmatch.fnmatch` honors POSIX glob syntax including character classes
(`[cod]` works directly). [CITED: docs.python.org/3/library/fnmatch.html]

### Pattern 4: Symlink-refusing recursive delete (D-13)

**What:** Pre-validate that no path in the deletion tree is a symlink before calling
`shutil.rmtree`. CONTEXT.md "Claude's Discretion" explicitly forbids
`shutil.rmtree(onerror=...)` fragility.
**When to use:** Before deleting any directory matched by a directory-pattern.
**Example:**

```python
# Source: derived from D-13 + os.walk(followlinks=False) docs
# [CITED: docs.python.org/3/library/os.html#os.walk]
import os
import shutil
from pathlib import Path

def _has_symlink_in_tree(root: Path) -> bool:
    if root.is_symlink():
        return True
    # followlinks=False ensures os.walk does NOT recurse into symlinked dirs
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames + filenames:
            if (Path(dirpath) / name).is_symlink():
                return True
    return False

def _safe_delete_directory(root: Path) -> None:
    if _has_symlink_in_tree(root):
        # Skipped per D-13 — emit warning, exit 0 still allowed
        return
    shutil.rmtree(root)
```

### Anti-Patterns to Avoid

- **`shutil.rmtree(path, onerror=callback)`:** Explicitly rejected in CONTEXT.md
  "Claude's Discretion" ("no `shutil.rmtree(..., onerror=)` fragility"). The
  recommended pattern is pre-validate-then-delete.
- **`os.walk(path, followlinks=True)`:** Default is `followlinks=False`; setting
  `True` would let a symlink in `__pycache__/` reach a sibling project's source
  (the exact failure mode D-13 prevents). [CITED: docs.python.org/3/library/os.html#os.walk]
- **`pathlib.Path.glob("**/*")`:** Follows symlinks in some CPython versions; not
  the safe default for cleanup. Use `os.walk(followlinks=False)` instead.
  [VERIFIED: Python 3.13+ added `Path.walk()` with `follow_symlinks=False` default,
  but for 3.10 floor compatibility prefer `os.walk`.]
- **Reading `pyproject.toml` with hand-rolled regex for the cleanup `patterns`
  array:** Don't — TOML arrays support comments, multi-line, and trailing commas.
  Use `tomllib`. (The repo-root-guard `name = "privguard"` check is single-key and
  COULD use a regex as a 3.10 fallback; the patterns array CANNOT.)
- **Single-file bilingual README with collapsed `<details>` sections:** Rejected
  by D-01 — must be two separate top-level files.
- **Inventing new synthetic CPF/CNPJ values for the README demo:** Rejected by
  Claude's Discretion — reuse existing `tests/test_v1_regression_gate.py` constants.
- **Promoting AGENTS.md content into the README:** Rejected by D-05 — README has
  ONE link to AGENTS.md; nothing more.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TOML parsing | A regex / `str.split` parser for `[tool.privguard.cleanup]` | `tomllib` (3.11+) or `tomli` backport on 3.10 | TOML supports inline tables, multi-line arrays, trailing commas, escaped strings, and comments. A regex parser fails the moment a maintainer adds a comment to the patterns list. [CITED: PEP 680, docs.python.org/3/library/tomllib.html] |
| Glob-style pattern matching | A custom `*` / `?` / `[...]` regex compiler | `fnmatch.fnmatch` | `fnmatch` honors POSIX glob syntax including character classes (`[cod]`) which D-08 patterns rely on. [CITED: docs.python.org/3/library/fnmatch.html] |
| Symlink detection | A custom "is this a symlink" walker | `os.path.islink` / `Path.is_symlink()` + `os.walk(followlinks=False)` | `os.walk(followlinks=False)` is the safe default; per-entry `is_symlink()` covers the leaf case D-13 demands. [CITED: docs.python.org/3/library/os.html#os.walk] |
| Recursive directory deletion | A custom `os.walk` + `os.unlink` + `os.rmdir` loop | `shutil.rmtree` (after symlink pre-validation) | `shutil.rmtree` handles platform quirks (Windows file-handle locking, read-only attribute on Windows, `EBUSY` on Linux). The pre-validation + `rmtree` split is safer than embedding error handling in the walk. [CITED: docs.python.org/3/library/shutil.html#shutil.rmtree] |
| Cross-language link badge in README | A custom HTML / shields.io image | Plain markdown link with country-flag emoji | D-02 explicitly picks plain markdown; shields.io would add a deferred dependency on a third-party CDN. |
| EN/pt-BR drift detection | A custom Python parity check | Social enforcement (D-03) for v1 | CI drift check is explicitly deferred (CONTEXT.md "Deferred Ideas"). |

**Key insight:** Phase 7 is a stdlib-only, no-new-deps phase by design (CONTEXT.md
"Claude's Discretion"). Every "don't hand-roll" entry above maps to a stdlib API
that already exists. The one wrinkle is `tomllib` vs. Python 3.10 floor; see Pitfall 1.

## Runtime State Inventory

> Phase 7 is a documentation + new-tooling phase, not a rename/refactor/migration.
> However, two state categories are still worth checking explicitly because the new
> `privguard cleanup` command interacts with on-disk state at runtime.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastores, no Mem0, no SQLite, no ChromaDB. [VERIFIED: `ls` of repo root + `privguard/` shows pure-Python package, zero database files] | none |
| Live service config | None — no n8n / Datadog / Tailscale / Cloudflare. [VERIFIED: `.claude/settings.json` is the only external-service config and it is in git] | none |
| OS-registered state | None — no Windows Task Scheduler, pm2, launchd, or systemd integrations. The Claude hooks run via `claude` itself, not OS scheduler. | none |
| Secrets/env vars | `.env` and `.env.*` exist as protected paths (D-09 includes them in `_PROTECTED`); cleanup must NEVER touch them. No env vars have new names. [VERIFIED: `.gitignore:1-2` lists `.env` and `.env.*`; D-09 hardcodes both] | none for code edit; cleanup module's tests must include a `.env` fixture proving protection |
| Build artifacts / installed packages | **`privguard.egg-info/` exists at repo root today** (visible in repo-root listing) — and is the EXACT category D-08's `*.egg-info/` pattern targets. After Phase 7 ships, `privguard cleanup --apply` will remove it; running `pip install -e .` again will recreate it. | The Phase 7 cleanup will delete `privguard.egg-info/` on first `--apply`; the planner should note this in the Phase 7 verification step (run `pip install -e .` to recreate before running the test suite). Also: 10 `pytest-cache-files-*/` directories exist at repo root [VERIFIED: `ls` 2026-05-08]; they are NOT covered by D-08 patterns (different naming) — these are pre-existing test artifacts and should be cleaned manually before Phase 7 verification, or the planner should explicitly note they are out of scope (D-08 does NOT include `pytest-cache-files-*`). |

**Canonical question** (post-Phase-7-launch state): After cleanup runs `--apply`,
what runtime state is gone that needs regeneration?

- `privguard.egg-info/` → regenerated by `pip install -e .`
- `__pycache__/` → regenerated by next `python` invocation
- `.pytest_cache/` → regenerated by next `pytest` run
- `.coverage` / `htmlcov/` → regenerated by next `pytest --cov` run
- `dist/` / `build/` → regenerated by next `python -m build` (only relevant if a
  release flow exists; v1 has none)

None of this is data loss; all are reproducible artifacts.

## Common Pitfalls

### Pitfall 1: `tomllib` vs. `requires-python = ">=3.10"` mismatch [HIGH severity]

**What goes wrong:** `pyproject.toml:8` declares `requires-python = ">=3.10"`
[VERIFIED: read 2026-05-08]. `docs/install.md:11` documents Python ≥ 3.10. CONTEXT.md
"Claude's Discretion" recommends `tomllib`. But **`tomllib` was added to the Python
standard library in 3.11** [CITED: PEP 680 / docs.python.org/3/library/tomllib.html].
Importing `tomllib` on Python 3.10 raises `ModuleNotFoundError`.

**Why it happens:** `tomllib` feels like it has been stdlib forever (PEP 680, Python
3.11, October 2022 — over three years ago) but the project floor predates it.
CONTEXT.md was written assuming current Python; it doesn't address the 3.10 case.

**How to avoid:** The planner picks one of three options up front (NOT during execution):

- **Option A (recommended):** Add a try/except import shim and add `tomli` as a
  conditional dependency:
  ```python
  try:
      import tomllib  # 3.11+
  except ModuleNotFoundError:
      import tomli as tomllib  # 3.10 fallback
  ```
  In `pyproject.toml`:
  ```toml
  dependencies = ["tomli; python_version < '3.11'"]
  ```
  Cost: introduces the project's first runtime dependency (currently
  `dependencies = []`). `tomli` is the canonical 3.10 backport; `tomllib` itself
  was vendored from `tomli` into stdlib. [CITED: PEP 680 history]

- **Option B:** Bump `requires-python` to `>=3.11`. Cost: drops Python 3.10 support
  and requires updates to `pyproject.toml:8` AND `docs/install.md:11` AND the
  `docs/install.md` Python version table at lines 31-35. Phase 6 D-03 deliberately
  documented 3.14 nuance; bumping the floor is a real policy change.

- **Option C:** Use `tomllib` only AS-NEEDED and fall back for the repo-root guard
  only. Cost: the `[tool.privguard.cleanup].patterns` array CANNOT be regex-parsed
  safely (TOML arrays support comments, multi-line, trailing commas, escaped strings).
  Option C only works if you also pick Option A or B for the patterns read.
  → **Reject Option C.**

**Warning signs:** A test running on Python 3.10 fails at `import tomllib` with
`ModuleNotFoundError`. The verification step that runs `python -m pytest tests` on
3.10 will catch this if 3.10 is in the test matrix; if not, it ships broken on 3.10
silently.

### Pitfall 2: `[tool.privguard.cleanup]` schema validation gap [MEDIUM severity]

**What goes wrong:** D-08 specifies `patterns = [list of strings]`. D-14 says
"missing or invalid `[tool.privguard.cleanup]` → exit 2". A naive read like
`data["tool"]["privguard"]["cleanup"]["patterns"]` raises `KeyError` on missing
keys, not a clean exit-2 message. A `patterns = "not a list"` is even worse:
it iterates a string character-by-character and silently treats every character
as a pattern.

**Why it happens:** TOML doesn't enforce schemas; `tomllib.load()` returns whatever
shape the file declares.

**How to avoid:** Validate explicitly after `tomllib.load`:

```python
table = data.get("tool", {}).get("privguard", {}).get("cleanup")
if not isinstance(table, dict) or "patterns" not in table:
    print("error: [tool.privguard.cleanup] missing or invalid", file=sys.stderr)
    raise SystemExit(2)
patterns = table["patterns"]
if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
    print("error: [tool.privguard.cleanup].patterns must be a list of strings",
          file=sys.stderr)
    raise SystemExit(2)
```

**Warning signs:** A malformed `pyproject.toml` produces a Python traceback instead
of an exit-2 message. Cover this in `tests/test_cleanup.py` with a synthetic
malformed pyproject fixture (no real values needed).

### Pitfall 3: TOCTOU on symlink check [MEDIUM severity]

**What goes wrong:** Pattern 4 above checks for symlinks at scan time. If an
attacker (or a parallel build) replaces a directory with a symlink between scan
and `shutil.rmtree`, the rmtree could follow it and delete a sibling project.

**Why it happens:** Time-of-check-to-time-of-use race between
`_has_symlink_in_tree(root)` returning False and `shutil.rmtree(root)` running.

**How to avoid:** Re-check symlink status immediately before each `shutil.rmtree`
or `unlink` call in the apply loop. This is "belt and suspenders" — `os.walk` with
`followlinks=False` already prevents the most common case, but the explicit re-check
is what makes D-13 ("refuse to delete symlinks") robust under concurrent
filesystem changes.

```python
def _safe_delete_directory(root: Path) -> None:
    if root.is_symlink():        # leaf check
        return
    if _has_symlink_in_tree(root):  # tree check
        return
    # TOCTOU window minimized; rmtree itself does NOT follow symlinks
    # in the deletion path on Linux/macOS, but Windows behavior varies.
    shutil.rmtree(root)
```

**Warning signs:** Cleanup deletes content outside the repo root in a CI
environment with concurrent processes. Hard to test deterministically; document
the constraint and rely on the dry-run preview as the primary safety net.

### Pitfall 4: `.gitignore` parity drift [LOW severity, HIGH visibility]

**What goes wrong:** Success criterion #5 requires `.gitignore` to cover every
pattern in `[tool.privguard.cleanup]`. If a maintainer adds a pattern to
`pyproject.toml` but forgets to update `.gitignore`, transient artifacts can get
committed. CONTEXT.md "Specifics" notes a verification step:
`for p in <patterns>; grep -F "$p" .gitignore || echo "missing: $p"`.

**Why it happens:** Two source-of-truth files with no automated drift check
(automation deferred to v2).

**How to avoid:**

1. The Phase 7 verification gate must run the parity check manually (CONTEXT.md
   "Specifics" specifies this).
2. The README "How do I extend the cleanup patterns?" FAQ (D-04 §8) MUST instruct
   the maintainer: "add to `pyproject.toml [tool.privguard.cleanup].patterns` AND
   to `.gitignore`."
3. **Current `.gitignore` delta** [VERIFIED: read `.gitignore` 2026-05-08]:
   - Already present: `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.coverage`,
     `htmlcov/`, plus Brazil-specific protected patterns (`.env`, `.env.*`,
     `data_sensivel/`, `cooperados/`, `dump_*`, `*.cooperados.csv`, `*.cpf.txt`,
     `credenciais*`, `segredo*`).
   - **MISSING and required by D-08:** `dist/`, `build/`, `*.egg-info/`.
   - The Phase 7 `.gitignore` edit is exactly: append three lines.

**Warning signs:** A future PR adds a pattern to `pyproject.toml` but `.gitignore`
isn't touched. The manual parity grep catches this.

### Pitfall 5: Translation tone inconsistency [MEDIUM severity for credibility]

**What goes wrong:** Mechanical translation of EN code-comment phrasing into pt-BR
produces awkward, non-native-sounding text that undermines the Brazil-first
positioning. Examples to avoid: literal "antes que possa enviar" for "before any
external-provider submission path" (correct: "antes do envio para provedores
externos"), or "fail-closed" rendered as "falha-fechado" (use "falha segura"
or keep the term in English with parenthetical: "fail-closed (falha segura)").

**Why it happens:** Translators (or AI translators) default to literal phrasing.
CONTEXT.md "Specifics" explicitly notes "Translation tone for pt-BR: Use Brazilian
Portuguese conventions (não pt-PT). No literal English-style code-comment translations;
rephrase naturally where it reads awkwardly."

**How to avoid:**

- Brazilian Portuguese (pt-BR), NOT European Portuguese (pt-PT). Differences include:
  pt-BR uses "arquivo" (file) where pt-PT uses "ficheiro"; pt-BR "tela" vs pt-PT
  "ecrã"; pt-BR "celular" vs pt-PT "telemóvel". The README must use the pt-BR forms.
- Keep technical terms that are universally English in the Brazilian dev community:
  "hook", "CLI", "log", "commit", "push", "pull request", "checksum", "regex",
  "stdlib", "subcommand". Don't force translations like "gancho" for "hook".
- For privguard-specific concepts, prefer English term + parenthetical pt-BR
  on first mention, then English alone afterwards: "fail-closed (falha segura)".
- Section headings should be naturally idiomatic, not word-for-word: EN "What
  privguard does NOT do" → pt-BR "O que o privguard NÃO faz" (natural) NOT
  "O que privguard faz não" (literal English-order).
- Voice/tone: pt-BR README uses "você" (informal-but-professional), matching
  Brazilian software documentation conventions. Avoid "tu" (regional) and
  "vós" (archaic). [ASSUMED: Brazilian software documentation convention based on
  general knowledge — not verified against a specific style guide in this session.]

**Warning signs:** A native pt-BR reader pauses or backtracks at a phrase, or
laughs at a literal translation. The planner should plan for a pt-BR proofread
pass after first draft, not skip it.

## Code Examples

Verified patterns from official sources and the existing privguard codebase.

### Reading `[tool.privguard.cleanup].patterns` with `tomllib`

```python
# Source: tomllib official docs [CITED: docs.python.org/3/library/tomllib.html]
# Adapted for privguard schema (D-08).
import sys
from pathlib import Path
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # see Common Pitfalls Pitfall 1, Option A
    import tomli as tomllib  # type: ignore[no-redef]

def load_patterns(pyproject: Path) -> list[str]:
    with pyproject.open("rb") as f:  # tomllib REQUIRES binary mode
        data = tomllib.load(f)
    table = data.get("tool", {}).get("privguard", {}).get("cleanup")
    if not isinstance(table, dict) or "patterns" not in table:
        print("error: [tool.privguard.cleanup] missing", file=sys.stderr)
        raise SystemExit(2)
    patterns = table["patterns"]
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        print("error: patterns must be list[str]", file=sys.stderr)
        raise SystemExit(2)
    return patterns
```

### Existing argparse subparser pattern (mirror for `cleanup`)

```python
# Source: privguard/cli.py:108-146 [VERIFIED: read 2026-05-08]
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="privguard")
    subparsers = parser.add_subparsers(required=True)

    info = subparsers.add_parser("info")
    info.set_defaults(func=cmd_info)

    scan = subparsers.add_parser("scan")
    scan.add_argument("text", nargs="?")
    scan.add_argument("--json", action="store_true")
    scan.set_defaults(func=cmd_scan)

    # ... mask, policy-check, claude doctor follow same shape ...

    args = parser.parse_args(argv)
    return args.func(args)
```

The cleanup subparser registration mirrors this exactly (Pattern 1 above).

### Quickstart synthetic-CPF/CNPJ masking demo (drop-in for README)

```bash
# Source: tests/test_v1_regression_gate.py:46-47 (synthetic CPF/CNPJ values)
# [VERIFIED: read 2026-05-08]
# Source: tests/test_masking.py:11-22 (placeholder vocabulary <BR_CPF>, <TOKEN>)
# [VERIFIED: read 2026-05-08]
$ echo "CPF 123.456.789-09 e token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890" \
    | privguard mask
CPF <BR_CPF> e token <TOKEN>
```

For the dual-CPF-CNPJ demo (matches `tests/test_masking.py:36-42`):

```bash
$ echo "CPF 123.456.789-09 CNPJ 12.345.678/0001-95" | privguard mask
CPF <BR_CPF> CNPJ <BR_CNPJ>
```

**Verified placeholder vocabulary** [VERIFIED: `privguard/detection.py:167-192`
+ masking format `<{kind}>` at `privguard/masking.py:32`]:

| Detector kind | Placeholder | Use in README demo? |
|---------------|-------------|---------------------|
| `BR_CPF` | `<BR_CPF>` | YES — the CPF demo case |
| `BR_CNPJ` | `<BR_CNPJ>` | YES — the CNPJ demo case |
| `TOKEN` | `<TOKEN>` | YES — for the GitHub PAT (`ghp_…`) demo case |
| `API_KEY` | `<API_KEY>` | YES — for an `sk-…` demo case if the planner picks one |
| `EMAIL` | `<EMAIL>` | optional |
| `BR_PHONE`, `BR_CEP`, `BR_RG`, `BR_CNH`, etc. | `<BR_*>` | optional |

**The masking format is mechanical: `<{kind}>` with the detector's `kind` string
verbatim.** [VERIFIED: `privguard/masking.py:32` — `out.append(f"<{h.kind}>")`].
Do NOT invent placeholder names like `<CPF>` (no `BR_` prefix); the actual output
has the `BR_` prefix because that's the detector's kind.

### Claude Code hook setup snippet (for README §4)

```jsonc
// Source: derived from .claude/settings.json [VERIFIED: read 2026-05-08]
// + CONTEXT.md "Specifics" requirement to use `python -m` form
// (current settings.json uses script paths via $CLAUDE_PROJECT_DIR; CONTEXT.md
//  mandates the python -m form for the README so install path doesn't leak).
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python -m privguard.hooks.main_user_prompt"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python -m privguard.hooks.main_pre_tool"
          }
        ]
      }
    ]
  }
}
```

**Caveat (planner should verify):** `privguard.hooks` exposes `main_user_prompt`
and `main_pre_tool` as functions [VERIFIED: `privguard/__init__.py:11`], NOT as
runnable submodules. `python -m privguard.hooks.main_user_prompt` will fail unless
`privguard/hooks/main_user_prompt.py` exists OR `privguard/hooks.py` is converted
to a package OR the README documents an alternative invocation. **This is a real
gap.** The current `.claude/settings.json` uses `python3 "$CLAUDE_PROJECT_DIR/hooks/pii_guard.py"`
which is a script-path invocation, not a `python -m` invocation.

**Two resolution paths the planner can pick from (Claude's Discretion):**

- **Path A:** Add tiny console-entry-point scripts `privguard-pre-tool` and
  `privguard-user-prompt` to `[project.scripts]` in `pyproject.toml`, and have
  the README snippet use those: `"command": "privguard-pre-tool"`. Cleanest user
  experience; consistent with the canonical `privguard` CLI from PKG-02.
- **Path B:** Add `__main__.py`-style modules (`privguard/hooks/__init__.py` +
  `privguard/hooks/main_user_prompt.py` etc.) so the literal `python -m
  privguard.hooks.main_user_prompt` from CONTEXT.md works. Larger refactor.

**Recommendation:** Path A. It is one line in `pyproject.toml` per entry point
and avoids restructuring `privguard/hooks.py` (which is a single-file module
today). The README would document `privguard-pre-tool` and `privguard-user-prompt`
as the hook commands. Surface this trade-off to the user during plan review if
strict adherence to the literal `python -m privguard.hooks.main_user_prompt`
phrasing in CONTEXT.md is required.

### Capabilities matrix (drop-in for README §5)

```markdown
<!-- Source: privguard/codex.py CODEX_COMPATIBILITY [VERIFIED: read 2026-05-08]
     + docs/codex-compatibility.md [VERIFIED: read 2026-05-08]
     + CONTEXT.md D-06 -->

| Surface | Status | Notes |
|---|---|---|
| Claude Code `UserPromptSubmit` | block-supported | Phase 3 verified |
| Claude Code `PreToolUse` | block-supported | Phase 3 verified |
| Codex prompt hook | experimental block-only | Phase 4 evidence |
| Codex tool hook | experimental block-only | Phase 4 evidence |

For full evidence and remaining gaps, see [`docs/codex-compatibility.md`](docs/codex-compatibility.md).
```

The vocabulary is locked: NO row is "rewrite-capable", "automatic masking", or
"supported" without "experimental block-only" or "block-supported" qualifier.
[VERIFIED: `docs/codex-compatibility.md:52-65`, no row is `rewrite-capable`]

### Existing synthetic fixtures to reuse (do NOT invent new ones)

```python
# Source: tests/test_v1_regression_gate.py:45-66 [VERIFIED: read 2026-05-08]
SYNTH_CPF = "123.456.789-09"           # checksum-valid synthetic CPF
SYNTH_CNPJ = "12.345.678/0001-95"      # checksum-valid synthetic CNPJ
SYNTH_CNH = "12345678900"              # checksum-valid synthetic CNH
INVALID_CPF = "123.456.789-00"         # SAME format, wrong check digit
INVALID_CNPJ = "12.345.678/0001-00"    # SAME format, wrong check digit
FAKE_SECRET_SK = "sk-test-abcdefghijklmnopqrstuvwxyz"
FAKE_SECRET_GHP = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
```

CONTEXT.md "Claude's Discretion" suggested values like `000.000.001-91`. The values
above are what the test suite already uses. They are checksum-valid, obviously
synthetic, and have FORBIDDEN_OUTPUT coverage (the regression gate asserts they
never appear in any v1 surface output). **Reuse them.** Inventing new values
fragments the synthetic-fixture surface and risks the new value happening to
match a real Brazilian record (the exact failure mode TEST-01 prevents).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tomli` external dependency | `tomllib` stdlib | Python 3.11 (PEP 680, Oct 2022) | Newer Python projects use `tomllib`; older floors need a fallback shim. Affects Pitfall 1. |
| `pathlib.Path.glob("**/*")` walking with implicit symlink follow | `os.walk(path, followlinks=False)` (default) OR `pathlib.Path.walk(follow_symlinks=False)` (3.12+) | Python 3.12 added `Path.walk` | For 3.10 floor, `os.walk(followlinks=False)` is the safe default. [CITED: docs.python.org/3/library/pathlib.html#pathlib.Path.walk] |
| `shutil.rmtree(path, onerror=callback)` | `shutil.rmtree(path, onexc=callback)` | Python 3.12 (`onerror` deprecated in favor of `onexc`) | Irrelevant for Phase 7 because CONTEXT.md rejects `onerror=`/`onexc=` patterns entirely; we pre-validate. [CITED: docs.python.org/3/library/shutil.html] |
| Single-file bilingual READMEs with HTML `<details>` | Two separate top-level files | GitHub convention (no specific date — established practice for 5+ years) | D-01 picks two files; aligns with GitHub's automatic README rendering and SEO discoverability per language. |

**Deprecated/outdated:**
- `shutil.rmtree(path, onerror=)` is deprecated in Python 3.12+ in favor of `onexc=`.
  Phase 7 rejects both patterns (CONTEXT.md "Claude's Discretion") so this is moot.
- `pathlib.Path.glob("**/*")` follows symlinks in some CPython releases; not used
  in Phase 7.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Brazilian Portuguese software-doc convention favors "você" over "tu", and uses arquivo/tela/celular instead of pt-PT ficheiro/ecrã/telemóvel | Pitfall 5 | Low — these are well-established pt-BR conventions, but I have not verified against a specific Brazilian developer style guide in this session. A native pt-BR reviewer should confirm during plan review. |
| A2 | `python -m privguard.hooks.main_user_prompt` will not work as written in CONTEXT.md "Specifics" because `privguard/hooks.py` is a single-file module exposing `main_user_prompt` and `main_pre_tool` as functions, not as runnable submodules | Code Examples §"Claude Code hook setup snippet" | HIGH — CONTEXT.md "Specifics" explicitly mandates the `python -m` form. If the planner does not pick a resolution (Path A or Path B) up front, the README hook snippet will be copy-paste-broken. The planner MUST surface this in the plan-check step. |
| A3 | The 10 `pytest-cache-files-*/` directories at repo root are pre-existing test artifacts not covered by D-08 | Runtime State Inventory | Low — visible in `ls`, but I have not traced their origin. Could be left from a flaky pytest plugin or a CI artifact. Out of scope for Phase 7 either way; only matters for the verification step. |
| A4 | Adding `dist/`, `build/`, `*.egg-info/` to `.gitignore` is the complete delta needed for D-08 parity | Pitfall 4, .gitignore section | Low — verified by line-by-line comparison [VERIFIED: read `.gitignore` 2026-05-08 + read D-08 patterns]. |

**If this table has 4 rows, three of which are LOW risk:** Only A2 needs resolution
in the plan-check or discuss-confirmation step. The other three are documented
caveats the planner can proceed past.

## Open Questions

1. **Hook command form: `python -m` vs. console-script vs. script-path** (per A2 above)
   - What we know: CONTEXT.md "Specifics" mandates `python -m
     privguard.hooks.main_user_prompt`. Current `.claude/settings.json` uses script
     paths. `privguard/hooks.py` is a single-file module.
   - What's unclear: Whether CONTEXT.md "Specifics" intended literal `python -m`
     phrasing or whether `privguard-pre-tool` console-script entries (Path A) are
     acceptable.
   - Recommendation: Plan-check or discuss-confirmation should ask the user to
     confirm Path A (add console scripts) is acceptable, since it satisfies the
     intent (install-path-independent invocation) without requiring a refactor of
     `privguard/hooks.py`.

2. **`docs/install.md` strategy: summarize-and-link vs. absorb-and-slim**
   - What we know: CONTEXT.md "Claude's Discretion" leaves this to the planner.
     `docs/install.md` is 2.8 KB / 54 lines and covers Python version support, the
     `[full]` extra, and 3.14 gating in detail.
   - What's unclear: Whether the user wants `docs/install.md` preserved as the
     long-form reference (READMEs link to it) or merged into the READMEs (and
     `docs/install.md` reduced to a stub or removed).
   - Recommendation: Default to summarize-and-link. The detailed Python 3.14 gating
     content was Phase 6 D-03's primary deliverable; absorbing it into both READMEs
     would duplicate ~30 lines into both languages. Summarize-and-link keeps the
     README install section short (5-10 lines per language) and concentrates the
     drift surface in one English-only file.

3. **Should `tests/test_cleanup.py` be added in this phase?**
   - What we know: Success criteria do NOT strictly require it. CONTEXT.md
     "Integration Points" notes "planner decides; success criteria do not strictly
     require new tests but Phase 5 fail-closed pattern strongly implies it".
   - What's unclear: Effort budget for the phase.
   - Recommendation: YES, add `tests/test_cleanup.py`. The cleanup module has
     four irreducible safety contracts (repo-root guard, protected-list refusal,
     symlink refusal, dry-run-by-default) that MUST be regression-tested or they
     will silently regress. Phase 5 set the precedent that every safety-critical
     module has a synthetic fixture-based test. Skipping the test would be the
     Phase 7 equivalent of removing TEST-06.

4. **Python version floor decision for `tomllib` (per Pitfall 1)**
   - What we know: Three options (A: shim + `tomli` dep, B: bump floor to 3.11,
     C: regex fallback — rejected).
   - What's unclear: Whether the project will tolerate its first runtime
     dependency or prefer to drop 3.10 support.
   - Recommendation: Surface to the user during plan-check. Default to Option A
     (`tomli` shim) because:
     - Python 3.10 EOL is October 2026 — five months away — but still active.
     - `tomli` is the canonical backport (vendored into stdlib as `tomllib`).
     - Adding one conditional dep is reversible; bumping the floor is more visible.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | ✓ | 3.14.3 [VERIFIED: `python --version` 2026-05-08] | — |
| `tomllib` | Cleanup module | ✓ on 3.11+ | stdlib | `tomli` PyPI on 3.10 (Pitfall 1) |
| `pytest` | `tests/test_cleanup.py` (recommended) | ✓ | already configured | — |
| `git` | Repo-root guard (`.git/` exists check) | ✓ | repo is a git repo | — |
| `pip` (editable install) | Re-creating `privguard.egg-info/` after cleanup | ✓ | required by Phase 1 | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** `tomllib` on Python 3.10 (Pitfall 1).

## Validation Architecture

> SKIPPED. `.planning/config.json` sets `workflow.nyquist_validation: false`
> [VERIFIED: read 2026-05-08]. Test infrastructure remains the Phase 5 pytest gate;
> the planner can add `tests/test_cleanup.py` for the cleanup module per
> Open Question #3, but no Nyquist mapping is required.

## Security Domain

> Reduced scope. Phase 7 has minimal security surface (documentation + a stdlib
> deletion CLI), but the deletion CLI does have one threat vector worth noting.
> `.planning/config.json` does not set `security_enforcement` explicitly; defaulting
> to enabled.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — no auth surface |
| V3 Session Management | no | N/A — no sessions |
| V4 Access Control | yes | Filesystem access — `_PROTECTED` constant + repo-root guard (D-09 + D-11) |
| V5 Input Validation | yes | `pyproject.toml` schema validation (Pitfall 2) and pattern-string validation |
| V6 Cryptography | no | N/A — no crypto |
| V12 Files and Resources | yes | Symlink handling (D-13 + Pitfall 3 TOCTOU) |

### Known Threat Patterns for stdlib filesystem-deletion CLI

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Symlink directed at sibling project's source | Tampering / Denial of Service | `os.walk(followlinks=False)` + per-path `is_symlink()` check + TOCTOU re-check at delete time (Pitfall 3) |
| `[tool.privguard.cleanup].patterns` injecting `*` or `/` to wipe arbitrary paths | Tampering | Pattern matching is BASENAME-only via `fnmatch` (not path-component); plus protected list filter; plus repo-root guard rejects mismatched cwd |
| Malicious PR shrinks the protected list | Tampering | D-09 hardcodes `_PROTECTED` as a module constant; cannot be overridden via `pyproject.toml`. PR review still required to catch a code edit that shrinks it. |
| Cleanup output echoing file contents (sensitive paths) | Information Disclosure | D-10 mandates paths-only output (extends Phase 2 POL-04 sanitized-diagnostics rule) |
| `pyproject.toml` schema-broken, raising Python traceback that leaks paths | Information Disclosure | Pitfall 2 validation — clean exit-2 message with no traceback |
| Running `privguard cleanup --apply` in an unrelated project | Tampering / Denial of Service | D-11 repo-root guard requires BOTH `.git/` AND `pyproject.toml` with `name = "privguard"` |

The deletion CLI does not introduce new authentication, network, or
cryptographic surfaces. The dominant threat is "deletes the wrong thing", and
D-09 + D-11 + D-13 + dry-run default form a four-layer defense.

## Sources

### Primary (HIGH confidence)

- `privguard/cli.py:108-146` [VERIFIED: read 2026-05-08] — argparse subparser registration pattern.
- `privguard/masking.py:22-35, 81-105` [VERIFIED: read 2026-05-08] — `<{kind}>` placeholder format.
- `privguard/detection.py:167-192` [VERIFIED: read 2026-05-08] — placeholder vocabulary (kind names).
- `privguard/__init__.py:1-57` [VERIFIED: read 2026-05-08] — public API surface, `main_user_prompt`/`main_pre_tool` exposure.
- `tests/test_v1_regression_gate.py:45-99` [VERIFIED: read 2026-05-08] — synthetic CPF/CNPJ values + FORBIDDEN_OUTPUT corpus.
- `tests/test_masking.py:11-22, 33-42` [VERIFIED: read 2026-05-08] — confirmed masking output `<BR_CPF>`, `<BR_CNPJ>`, `<TOKEN>`.
- `pyproject.toml:1-27` [VERIFIED: read 2026-05-08] — Python floor 3.10, `dependencies = []`, console scripts.
- `.gitignore:1-15` [VERIFIED: read 2026-05-08] — current 15 lines, missing `dist/`, `build/`, `*.egg-info/`.
- `.claude/settings.json:1-50` [VERIFIED: read 2026-05-08] — current hook wiring uses script paths, not `python -m`.
- `docs/install.md:1-54` [VERIFIED: read 2026-05-08] — Python 3.14 gating, baseline + `[full]` install.
- `docs/codex-compatibility.md:52-65` [VERIFIED: read 2026-05-08] — capability vocabulary verified for D-06 matrix.
- `.planning/phases/06-milestone-cleanup/06-VERIFICATION.md` [VERIFIED: read 2026-05-08] — Phase 6 verification approach (134 tests + targeted greps).
- PEP 680 / Python 3.11 release [CITED: docs.python.org/3/library/tomllib.html] — `tomllib` stdlib introduction.

### Secondary (MEDIUM confidence)

- Python stdlib documentation [CITED: docs.python.org/3/library/{tomllib,fnmatch,pathlib,shutil,os}.html] — semantics referenced from training but well-established in the language reference. Direct fetch was blocked by privguard's own hooks during this session.
- Brazilian Portuguese software documentation conventions [ASSUMED: see A1 in Assumptions Log].

### Tertiary (LOW confidence)

- None. All claims used in the plan recommendations have at least MEDIUM-confidence backing.

## Metadata

**Confidence breakdown:**

- README structure (D-01..D-06 implementation): **HIGH** — CONTEXT.md is exhaustive;
  research filled in only the synthetic-fixture references and the hook-snippet caveat.
- Cleanup module implementation (D-07..D-14): **HIGH** — every API needed is stdlib
  with verified semantics; one Python-version pitfall flagged with three resolution
  paths.
- pt-BR translation tone: **MEDIUM** — A1 documents the assumption; native review
  recommended.
- Hook setup snippet correctness: **MEDIUM** — A2 documents the gap between
  CONTEXT.md's literal phrasing and the actual `privguard/hooks.py` shape; planner
  must pick a resolution (recommended Path A: console scripts).

**Research date:** 2026-05-08
**Valid until:** 2026-06-07 (30 days; Phase 7 has no fast-moving external deps)
