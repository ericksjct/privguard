# Phase 7: Project README + Repo Hygiene - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 delivers two artifacts that close out v1.0 milestone scope:

1. **Bilingual top-level README** (`README.md` English primary + `README.pt-BR.md` Portuguese)
   covering install, CLI usage, Claude Code hook setup, Codex/Claude capabilities matrix,
   non-goals, and the synthetic-fixture-only policy. Closes **DOC-01**.
2. **Config-driven repo cleanup mechanism** — a `privguard cleanup` CLI subcommand backed by
   `privguard/cleanup.py`, with default patterns in `pyproject.toml [tool.privguard.cleanup]`,
   a hardcoded protected list the script can never delete, dry-run by default, and `--apply`
   required to delete. `.gitignore` must reach parity with the cleanup patterns. Closes
   **MAINT-01**.

The phase does **not**:
- Add new product runtime behavior (detection, masking, policy, hooks unchanged).
- Promote `AGENTS.md` content into `docs/` — agent companion stays as-is.
- Add CI / drift-prevention tests for README parity — candidate for v2.
- Add badges, CHANGELOG, license-file changes, or `.editorconfig` — not in roadmap scope.
- Introduce linter cache patterns (`.mypy_cache/`, `.ruff_cache/`, `.tox/`) — those tools
  are not in `pyproject.toml`; defaults match what the project actually generates today.
- Add a JSON output mode for cleanup — deferred until CI integration is requested.

</domain>

<decisions>
## Implementation Decisions

### README Structure

- **D-01:** Two separate files at repo root: `README.md` (English, primary per success
  criterion #1) and `README.pt-BR.md` (Portuguese). Each contains the full content for its
  language. Single-file bilingual sections are rejected because criterion #1 explicitly
  names `README.pt-BR.md` as a separate file.
- **D-02:** Cross-language switcher is a **badge-style row above the H1** in each README
  (e.g. `[🇺🇸 English](README.md) | [🇧🇷 Português](README.pt-BR.md)`). Rejected: footer-only
  (Brazilian users may not discover pt-BR exists), plain first-line link (less prominent).
- **D-03:** **Both READMEs must update together in every PR.** Any PR touching `README.md`
  must also update `README.pt-BR.md` (or explicitly declare "translation pending" in the
  PR body). Enforced socially, not via CI for v1. Rejected: EN-canonical-pt-BR-catches-up
  (creates a second-class Brazilian experience that conflicts with the Brazil-first
  PROJECT.md principle).

### README Scope & Depth

- **D-04:** README scope = **phase-criteria minimum + walkthrough + FAQ**. Required sections
  in both languages:
  1. Install (`pip install privguard`, `pip install privguard[full]` with Python 3.14
     gating note linking to `docs/install.md`).
  2. Quickstart "in 60 seconds" — synthetic CPF/CNPJ masking example via `privguard mask`.
  3. CLI usage (`privguard scan`, `privguard mask`, `privguard policy-check`,
     `privguard claude doctor`, `privguard cleanup`).
  4. Claude Code hook setup (snippet for `.claude/settings.json` wiring `UserPromptSubmit`
     and `PreToolUse` to package-backed entry points `privguard.hooks.main_user_prompt`
     and `privguard.hooks.main_pre_tool`).
  5. Codex / Claude capabilities matrix (see D-06).
  6. **What privguard does NOT do** — explicit non-goals: hosted SaaS, deanonymization,
     LangChain/LlamaIndex adapters, unsupported clients, real-data fixtures.
  7. **Synthetic-fixture-only policy** statement — never use real CPF/CNPJ/`.env` data
     in examples, tests, or commits.
  8. FAQ — required entries: "Does this work with Codex?", "What if a CPF is missed?",
     "Why does it block instead of warn?", "How do I extend the cleanup patterns?"
  9. "For coding agents" pointer line linking to `AGENTS.md`.

- **D-05:** **README and `AGENTS.md` stay independent.** `AGENTS.md` is not modified by
  Phase 7. README links to it via a single "For coding agents working in this repo, see
  [AGENTS.md](AGENTS.md)" line. Rejected: linking into specific AGENTS.md anchors (couples
  human docs to a regenerated artifact); promoting AGENTS.md content into `docs/` (expands
  scope significantly).

- **D-06:** **Capabilities matrix in README is a condensed 4-row table** with footer link
  to `docs/codex-compatibility.md` for evidence:

  | Surface | Status | Notes |
  |---|---|---|
  | Claude Code `UserPromptSubmit` | block-supported | Phase 3 verified |
  | Claude Code `PreToolUse` | block-supported | Phase 3 verified |
  | Codex prompt hook | experimental block-only | Phase 4 evidence |
  | Codex tool hook | experimental block-only | Phase 4 evidence |

  No "rewrite-capable" or "automatic masking" claim for any surface. Rejected: full
  inline matrix (drift risk vs. `docs/codex-compatibility.md`); badges-only (insufficient
  for a privacy tool's primary trust signal).

### Cleanup Command Shape & Patterns

- **D-07:** **Cleanup is a `privguard cleanup` subcommand**, not a standalone script.
  Logic in `privguard/cleanup.py`; wiring in `privguard/cli.py` alongside `scan`, `mask`,
  `policy-check`, and `claude doctor`. Discoverable via `privguard --help`, ships with the
  installed package, testable through the existing pytest path. Rejected: standalone
  `scripts/cleanup.py` (breaks Phase 1 "package-based code" decision and is not installed).

- **D-08:** **Default patterns in `[tool.privguard.cleanup]` (Standard Python set):**
  ```toml
  [tool.privguard.cleanup]
  patterns = [
      "__pycache__/",
      "*.py[cod]",
      ".pytest_cache/",
      ".coverage",
      "htmlcov/",
      "dist/",
      "build/",
      "*.egg-info/",
  ]
  ```
  Maintainer adds new patterns by appending to this list (success criterion #3).
  `.gitignore` must include each pattern (success criterion #5).

- **D-09:** **Protected list is hardcoded in `privguard/cleanup.py`** as a module-level
  constant. Cannot be overridden, shrunk, or extended by `pyproject.toml`. Mandatory entries:
  ```python
  _PROTECTED = (
      ".env",
      ".env.*",
      "data_sensivel/",
      ".planning/",
      ".git/",
      "privguard/",
      "tests/",
      "hooks/",
      "demos/",
      "docs/",
      "pyproject.toml",
      "AGENTS.md",
      "README.md",
      "README.pt-BR.md",
  )
  ```
  Any path matching a protected entry (or under a protected directory) is skipped with a
  warning, regardless of whether it also matches a cleanup pattern. Rejected: pyproject
  override (a malicious or careless PR could shrink the list); hardcoded-plus-extendable
  (over-engineered for v1; maintainer can edit code if needed).

- **D-10:** **Dry-run output is grouped by pattern with byte sizes.** Default format:
  ```
  [dry-run] would delete (3 paths, 1.4 MB total):
    __pycache__/        2 dirs / 47 files / 1.2 MB
    .pytest_cache/      1 dir  / 12 files / 180 KB
    *.pyc               3 files / 24 KB
  Run with --apply to delete.
  ```
  No `--json` mode in v1 (deferred). Output is sanitized — paths only, never file contents
  (extends Phase 2 POL-04 sanitized-diagnostics rule to cleanup).

### Cleanup Safety Surface

- **D-11:** **Repo-root guard is mandatory.** Before any scan, the script must verify it
  is running in the privguard repo root by requiring **both**:
  1. `.git/` directory exists in cwd, and
  2. `pyproject.toml` exists in cwd and contains `name = "privguard"` under `[project]`.

  If either check fails, the script exits with code 2 (misuse) and a clear message. This
  prevents accidental `privguard cleanup --apply` in unrelated projects with similarly-named
  artifacts. Strongest guard available without installing the package per-repo.

- **D-12:** **`--apply` alone deletes — no further interactive prompt.** If you typed
  `--apply`, you meant it. The dry-run default + repo-root guard + protected list +
  symlink refusal are the safety net. No `--yes` flag (nothing to skip). Rejected:
  interactive `y/N` (clutters automation, doesn't add safety beyond dry-run);
  type-the-count confirmation (theatrical friction for a script run on dev machines).

- **D-13:** **Refuse to delete symlinks (and refuse to follow them).** If a path matched
  by a cleanup pattern is a symlink, or contains a symlink anywhere in its tree during
  recursive deletion, the script:
  1. Skips the symlink and any path beneath it.
  2. Emits a warning naming the skipped path.
  3. Continues with other matches.
  4. Returns exit 0 (skips are not failures) but the dry-run preview will have shown
     the symlink as `(skipped: symlink)`.

  Prevents a symlink in `__pycache__/` from pointing at a sibling project's source and
  taking real code with it.

- **D-14:** **Exit codes follow privguard's existing CLI convention:**
  - `0` — Dry-run preview printed cleanly, OR `--apply` deleted everything matched
    successfully (skipped symlinks/protected paths do not count as failures).
  - `1` — `--apply` attempted to delete a path and failed (permissions, OS error, etc.).
  - `2` — Misuse: not in privguard repo root (D-11 failed), malformed `pyproject.toml`,
    `[tool.privguard.cleanup]` missing or invalid, conflicting flags, unknown flag.

### Claude's Discretion

The planner / executor handles these without further user input:

- **Section ordering within each README** — D-04 lists sections, but exact order, heading
  level depths, table-of-contents placement, and intra-section flow are at the planner's
  discretion as long as all listed sections appear.
- **FAQ wording** — D-04 fixes the four required questions; the answers themselves are
  drafted from PROJECT.md, REQUIREMENTS.md, and prior phase verifications.
- **Synthetic CPF/CNPJ values used in masking demo** — Must be obviously synthetic
  (e.g. `000.000.001-91`, `00.000.000/0001-91` style with checksum-valid but obviously-fake
  patterns). Reuse existing test fixtures from `tests/` rather than inventing new ones.
- **Quickstart code-block style** (single block vs. multi-step prose) — planner choice.
- **`docs/install.md` consolidation** — README install section may either summarize and
  link to `docs/install.md`, or fold the install.md content into README and slim
  `docs/install.md` to a stub. Planner picks whichever keeps drift risk lowest.
- **Cleanup CLI flag names beyond `--apply`** — `--verbose` / `-v`, `--dry-run` (explicit
  alias), `--quiet` are at the planner's discretion. The mandatory flag is `--apply`.
- **Implementation language for the cleanup module** — pure stdlib Python, no new deps.
  Use `pathlib`, `fnmatch`, `tomllib`, `os.walk`. No `shutil.rmtree(..., onerror=)`
  fragility; planner picks the safest stdlib pattern.

### Resolutions from Research Review (2026-05-08)

Two open questions surfaced by `07-RESEARCH.md` were resolved by the user
before planning. They are locked decisions and supersede any conflicting
phrasing earlier in this document.

- **D-15:** **Hook command form is console scripts, not `python -m`.** The
  CONTEXT.md "Specifics" section originally said `python -m privguard.hooks.main_user_prompt`
  / `python -m privguard.hooks.main_pre_tool`, but `privguard/hooks.py` is a
  single-file module that exposes `main_user_prompt` and `main_pre_tool` as
  functions, not as runnable submodules. Resolution: **add two console scripts
  to `pyproject.toml [project.scripts]`** —
  ```toml
  [project.scripts]
  # ... existing entries ...
  privguard-user-prompt = "privguard.hooks:main_user_prompt"
  privguard-pre-tool    = "privguard.hooks:main_pre_tool"
  ```
  Both READMEs' Claude Code hook setup section MUST use the console-script
  names (`privguard-user-prompt`, `privguard-pre-tool`) in the
  `.claude/settings.json` snippet. The literal `python -m …` phrasing in the
  earlier "Specifics" subsection is overridden by this decision. Rejected:
  refactoring `privguard/hooks.py` into a package (expands scope); `python -c
  '...'` form (ugly).

- **D-16:** **`tomllib` reader uses a conditional `tomli` shim.** `pyproject.toml`
  declares `requires-python = ">=3.10"`, but `tomllib` is stdlib only in
  Python 3.11+. Resolution: **add a conditional dependency** to
  `[project.dependencies]`:
  ```toml
  dependencies = [
      # ... existing entries ...
      "tomli; python_version < '3.11'",
  ]
  ```
  `privguard/cleanup.py` imports the parser via:
  ```python
  try:
      import tomllib  # Python 3.11+
  except ModuleNotFoundError:
      import tomli as tomllib  # Python 3.10
  ```
  Preserves the 3.10 floor without bumping it. Rejected: bumping
  `requires-python` to `>=3.11` (drops 3.10 support unnecessarily for a
  config-reading utility).

### Folded Todos

None. The cross-phase todo match returned zero relevant items.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 7 scope sources
- `.planning/ROADMAP.md` §"Phase 7: Project README + Repo Hygiene" — phase goal, 5 success
  criteria, requirement mapping (DOC-01, MAINT-01).
- `.planning/REQUIREMENTS.md` §Documentation (DOC-01) and §Maintenance (MAINT-01) — the
  exact requirement wording that must be satisfied to tick `[x]`.
- `.planning/PROJECT.md` — Core value, constraints (Brazil-first locale priority,
  fail-closed safety default, synthetic-fixtures-only data hygiene), Key Decisions table.

### Locked prior decisions (carry forward, do not revisit)
- `.planning/phases/01-package-foundation/01-CONTEXT.md` — D-01 canonical name `privguard`,
  package-based code pattern.
- `.planning/phases/02-privacy-core/02-CONTEXT.md` — POL-04 sanitized diagnostics
  (extends to cleanup output: paths only, never contents).
- `.planning/phases/03-claude-enforcement/03-CONTEXT.md` — Claude hook block semantics and
  output hygiene gate (informs README hook-setup section).
- `.planning/phases/04-codex-compatibility-evidence/04-CONTEXT.md` — Codex evidence
  standard (no "rewrite-capable" / "automatic masking" claims; informs D-06 matrix).
- `.planning/phases/05-synthetic-regression-gate/05-CONTEXT.md` — TEST-01 synthetic-only
  fixture policy (informs README masking-demo synthetic-CPF requirement).
- `.planning/phases/06-milestone-cleanup/06-CONTEXT.md` — D-04 PKG-02 canonical wording,
  D-03 Python 3.14 gating in `docs/install.md` (README install section links here).

### Code touched in this phase
- `README.md` (new) — English-primary top-level README, all sections from D-04.
- `README.pt-BR.md` (new) — Portuguese full translation, paired updates per D-03.
- `pyproject.toml` — add `[tool.privguard.cleanup]` table (D-08).
- `.gitignore` — extend to include every pattern from D-08 (success criterion #5).
- `privguard/cleanup.py` (new) — cleanup logic, hardcoded protected list (D-09),
  pattern matching, symlink handling (D-13), repo-root guard (D-11), dry-run formatter
  (D-10).
- `privguard/cli.py` — add `cleanup` subcommand wiring (D-07).

### Code referenced but not modified
- `privguard/__init__.py` — `__all__` may need `cleanup` re-export if planner decides
  cleanup should be in the public API surface (planner discretion; not required by
  success criteria).
- `AGENTS.md` — referenced from README, not modified (D-05).
- `docs/codex-compatibility.md` — referenced from README capabilities matrix (D-06),
  not modified.
- `docs/install.md` — referenced or partly absorbed by README install section
  (planner discretion per D-04 / Claude's Discretion).
- `tests/` — synthetic CPF/CNPJ fixtures reused for README masking demo.

### External evidence
- Phase 4 verification of Codex labels — `.planning/phases/04-codex-compatibility-evidence/04-VERIFICATION.md`
  (drives D-06 status column values).
- Phase 3 verification of Claude hook block semantics — `.planning/phases/03-claude-enforcement/03-VERIFICATION.md`
  (drives D-06 status column for Claude rows; informs README hook-setup section).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`privguard/cli.py` already implements an argparse-based subcommand dispatcher** for
  `scan`, `mask`, `policy-check`, and `claude doctor`. Adding `cleanup` follows the same
  pattern — no new CLI framework needed. Inspect existing subcommand registration before
  adding.
- **`tests/` already contains synthetic CPF/CNPJ fixtures** validated through Phase 5.
  README masking demo should reuse these (planner decides which exact fixture file —
  `tests/test_detection_*.py` or fixture modules — is most stable).
- **`docs/install.md` already covers `pip install` + Python 3.14 gating** (Phase 6 D-03).
  README install section can summarize and link, or absorb and slim. No need to re-derive.
- **`AGENTS.md` (22K)** is GSD-generated and contains project context, stack, structure,
  and conventions for coding agents. Useful as a single canonical link target rather than
  duplicated content.
- **`docs/codex-compatibility.md` (7.5K)** is the authoritative Codex evidence document.
  README condensed matrix (D-06) links here; do NOT duplicate.
- **Existing `.gitignore` (15 lines)** already covers `.env`, `data_sensivel/`,
  `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.coverage`, `htmlcov/`, plus
  Brazil-specific protected patterns. Phase 7 must ADD `dist/`, `build/`, `*.egg-info/`
  (the new D-08 patterns it does not yet cover).

### Established Patterns

- **Sanitized diagnostics** (Phase 2 POL-04 / Phase 3) — extends to cleanup output. Print
  paths and counts; never file contents. The dry-run formatter (D-10) follows this rule.
- **Fail-closed default** (PROJECT.md constraint) — extends to cleanup. Dry-run is the
  default action; `--apply` is the explicit opt-in. Repo-root guard refuses ambiguous
  invocations.
- **Synthetic-only fixtures** (Phase 5 TEST-01) — README masking demo must use existing
  synthetic test fixtures, not invented values that could resemble real Brazilian IDs.
- **Package-first code organization** (Phase 1) — new logic lives under `privguard/`,
  not as a root-level script. Already validated in Phase 6 (`privguard/codex.py`).
- **Sub-command CLI pattern** (Phase 1 / Phase 2) — new functionality is exposed as a
  `privguard <verb>` subcommand, not as a flag on existing subcommands.

### Integration Points

- `privguard/cli.py` — add `cleanup` to the subparser registry; register `--apply` flag.
- `privguard/cleanup.py` (new) — exports a `main(argv)` callable that `cli.py` invokes;
  imports stdlib only (`pathlib`, `fnmatch`, `tomllib`, `os.walk`, `os.path.islink`).
- `pyproject.toml [tool.privguard.cleanup]` — new table the cleanup module reads via
  `tomllib.load()`. Schema: `patterns: list[str]`. No other keys for v1.
- `.gitignore` — extended to mirror `[tool.privguard.cleanup].patterns`. Each cleanup
  pattern must have a corresponding gitignore entry (success criterion #5). The cleanup
  patterns themselves come from D-08; the protected list (D-09) does NOT need gitignore
  entries (those paths are intentionally tracked or already gitignored).
- `tests/` — new `tests/test_cleanup.py` recommended (planner decides; success criteria
  do not strictly require new tests but Phase 5 fail-closed pattern strongly implies it).
- `docs/install.md` — referenced from both READMEs' install sections.

</code_context>

<specifics>
## Specific Ideas

- **README badge row format** (D-02): Use plain markdown link syntax with country flag
  emoji prefixes — `[🇺🇸 English](README.md) | [🇧🇷 Português](README.pt-BR.md)` — and
  place it on the line immediately above the H1, with a blank line before the H1. No
  shields.io badges in v1 (deferred).
- **Quickstart synthetic example** (D-04 §2): Show one CPF (`000.000.001-91`-style),
  one CNPJ, and one fake API key being masked via `privguard mask`. Output should show
  typed placeholders (`<CPF>`, `<CNPJ>`, `<API_KEY>` or whatever the Phase 2 vocabulary
  is). Reuse Phase 2's existing placeholder vocabulary verbatim — do not invent new
  tokens for the README.
- **Hook setup snippet** (D-04 §4): Show the JSON for `.claude/settings.json` wiring
  both `UserPromptSubmit` → `python -m privguard.hooks.main_user_prompt` and `PreToolUse`
  → `python -m privguard.hooks.main_pre_tool`. Use `python -m` form (not direct script
  paths) so the install path doesn't need documentation.
- **FAQ "What if a CPF is missed?"**: Answer must reference the fail-closed posture and
  the `privguard claude doctor` diagnostic command. Do NOT promise 100% recall.
- **FAQ "Does this work with Codex?"**: Answer must match the D-06 matrix language —
  "experimental block-only", with link to `docs/codex-compatibility.md`. Do NOT claim
  automatic masking.
- **Cleanup pattern matching semantics**: A trailing `/` (e.g. `__pycache__/`) means
  "directory tree, recursive". No trailing `/` (e.g. `*.py[cod]`) means glob-style file
  match. Document this in the README and as a `#`-comment in `pyproject.toml`.
- **`.gitignore` parity check**: Phase 7 verification gate should include
  `for p in <patterns>; grep -F "$p" .gitignore || echo "missing: $p"` to enforce
  success criterion #5 manually. (No automated drift test in v1 per "deferred ideas".)
- **Translation tone for pt-BR**: Use Brazilian Portuguese conventions (não pt-PT). No
  literal English-style code-comment translations; rephrase naturally where it reads
  awkwardly.

</specifics>

<deferred>
## Deferred Ideas

These came up during discussion or are obvious near-neighbors of phase scope. Captured
so they aren't lost; not acted on in Phase 7.

- **Linter cache patterns in cleanup defaults** (`.mypy_cache/`, `.ruff_cache/`, `.tox/`,
  `.nox/`) — add when those tools are introduced to `pyproject.toml`. Until then, defaults
  reflect what the project actually generates.
- **`--json` output mode for cleanup** — useful for CI pipelines that want a machine-readable
  audit. Not needed for v1 dev-machine usage. Candidate for v2 enterprise track (ENT-02
  audit-safe telemetry).
- **`--yes` / interactive `y/N` confirmation** — explicitly rejected for v1 (D-12). Could
  be reconsidered if enterprise / shared-machine usage emerges.
- **Drift-prevention regression test for EN/pt-BR README parity** — a CI check that flags
  one-language-only README diffs. Useful but out of scope for v1 (Phase 6 deferred a
  similar audit-drift regression test for the same reason).
- **README badges (CI status, license, PyPI version)** — deferred; v1 has no CI, no
  published PyPI release, no license file decision. Add when those exist.
- **License file (`LICENSE`) and `CHANGELOG.md`** — not in Phase 7 scope. Should land
  before any public PyPI publication.
- **Promoting `AGENTS.md` content into structured `docs/` files** (e.g.
  `docs/architecture.md`, `docs/threat-model.md`) — explicitly deferred (D-05). Would
  significantly expand Phase 7 scope.
- **Status badges on capabilities matrix** (shields.io style) — explicitly rejected in
  favor of the condensed table (D-06). Could revisit if README becomes a primary
  marketing surface.
- **Cleanup tool extending Phase 2 sanitized-diagnostics tests to its own output** —
  i.e. a forbidden-output gate that asserts cleanup output never echoes a synthetic CPF
  even if one were somehow in a path string. Defensible-extension idea; planner may include
  if low-effort, otherwise defer to v2.
- **Internationalization beyond pt-BR** (Spanish, etc.) — explicitly out of scope per
  PROJECT.md Brazil-first focus.

</deferred>

---

*Phase: 07-readme-hygiene*
*Context gathered: 2026-05-08*
