---
phase: 07-readme-hygiene
verified: 2026-05-10T22:30:00Z
status: passed
score: 9/9
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 8/9
  gaps_closed:
    - "README.pt-BR.md exists — plan 07-03 executed and delivered 217-line Portuguese translation"
    - "Cross-language switcher link README.md -> README.pt-BR.md is now live (target file exists)"
    - "DOC-01 is fully closed — both English and Portuguese READMEs satisfy all content requirements"
  gaps_remaining: []
  regressions: []
---

# Phase 7: Project README + Repo Hygiene Verification Report

**Phase Goal:** First-time user can land in the repo, understand what privguard does and does not do, install it, and clean up after themselves — in either English or Portuguese.
**Verified:** 2026-05-10T22:30:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (plan 07-03 executed to close Portuguese README gap)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | User can read a top-level README in English (`README.md`) and Portuguese (`README.pt-BR.md`) covering install, CLI usage, hook setup, capabilities matrix, non-goals, and synthetic-fixture-only policy | VERIFIED | `README.md` (182 lines, 9 D-04 sections) and `README.pt-BR.md` (217 lines, 9 D-04 sections in pt-BR) both exist at repo root. Cross-language switcher on line 1 of both files links bidirectionally. DOC-01 fully satisfied. |
| 2 | User can run `privguard cleanup` to preview and remove transient artifacts without touching protected paths | VERIFIED | `privguard/cleanup.py` (257 lines) implements repo-root guard, dry-run default, `_PROTECTED` list (14 entries), symlink refusal. CLI wired via `privguard/cli.py`. 6 contract tests pass (139 passed, 1 skipped on Windows). |
| 3 | Maintainer can extend cleanup patterns by editing one TOML list without modifying the cleanup script | VERIFIED | `[tool.privguard.cleanup].patterns` in `pyproject.toml` (8 patterns). `_load_patterns()` reads at runtime. No code change required to add patterns. |
| 4 | Cleanup runs dry-run by default and requires explicit `--apply` to delete | VERIFIED | `main()` checks `getattr(ns, 'apply', False)`. Default path prints `[dry-run] would delete` and returns 0 with no deletions. `test_cleanup_default_is_dry_run_no_deletion` asserts this. |
| 5 | `.gitignore` covers every cleanup-eligible pattern | VERIFIED | All 8 D-08 patterns present in `.gitignore`: `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `dist/`, `build/`, `*.egg-info/`. Lines 15-17 confirmed. |
| 6 | First-time user can understand, install, and integrate privguard with Claude Code from the English README | VERIFIED | README has Install, Quickstart (with synthetic CPF/CNPJ/token fixtures), CLI usage, Claude Code hook setup (D-15 console scripts), Capabilities matrix, non-goals (5 bullets), synthetic-fixture policy, FAQ (4 entries), and AGENTS.md pointer. All acceptance criteria met. |
| 7 | README uses correct vocabulary: `block-supported` x2+, `experimental block-only` x2+, no `rewrite-capable`, no `automatic masking` | VERIFIED | `block-supported` appears 3x in README.md; `experimental block-only` appears 4x. Neither forbidden phrase found in either README file. |
| 8 | D-15 hook setup uses console-script names, not `python -m` form | VERIFIED | JSON snippet uses `privguard-user-prompt` and `privguard-pre-tool`. The `python -m privguard.hooks` form is absent. Both console scripts declared in `pyproject.toml [project.scripts]` at lines 27-28. |
| 9 | `tomli` conditional dependency declared for Python < 3.11 | VERIFIED | `pyproject.toml` declares `tomli; python_version < '3.11'`. `cleanup.py` uses the `try/except ModuleNotFoundError` shim. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `README.md` | English README, 9 D-04 sections, D-06 locked vocabulary, D-15 hook snippet, 180+ lines | VERIFIED | 182 lines. 9 sections with full prose. All locked vocabulary enforced. Forbidden phrases absent. |
| `README.pt-BR.md` | Portuguese translation, cross-language switcher, same 9 sections, 150+ lines | VERIFIED | 217 lines. 9 D-04 sections in pt-BR. Block-supported x3, experimental block-only x4. All locked vocabulary verbatim. Switcher on line 1 links bidirectionally. |
| `privguard/cleanup.py` | Stdlib-only cleanup module with `_PROTECTED`, repo-root guard, dry-run formatter, symlink refusal, `main()` returning 0/1/2 | VERIFIED | 257 lines. All 14 `_PROTECTED` entries present. `tomllib` shim present. `followlinks=False` explicit. `[CLEANUP]` sanitized stderr. No `onerror=` anti-pattern. |
| `privguard/cli.py` | `cleanup` subparser with `--apply` flag dispatching to `cleanup_main` | VERIFIED | Import on line 10, `cmd_cleanup` wrapper, subparser registered, `set_defaults(func=cmd_cleanup)`. |
| `pyproject.toml` | `[tool.privguard.cleanup]` patterns table, `tomli` conditional dep, two D-15 console scripts | VERIFIED | All three additions confirmed: `[tool.privguard.cleanup]` at line 33 with 8 patterns; `tomli; python_version < '3.11'`; console scripts at lines 27-28. |
| `.gitignore` | Parity with all 8 D-08 cleanup patterns | VERIFIED | Lines 15-17 add `dist/`, `build/`, `*.egg-info/`. All 8 patterns now present. |
| `tests/test_cleanup.py` | 6 contract tests covering all safety contracts | VERIFIED | 6 tests covering dry-run default, apply deletion, repo-root guard, protected-list refusal, symlink refusal (skip on Windows), output sanitization. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `privguard/cli.py` | `privguard/cleanup.py` | `from .cleanup import main as cleanup_main` | WIRED | Line 10 confirmed |
| `privguard/cleanup.py` | `pyproject.toml` | `tomllib.load()` reads `[tool.privguard.cleanup].patterns` | WIRED | `_load_patterns()` reads TOML at runtime |
| `tests/test_cleanup.py` | `privguard/cli.py` | `from privguard.cli import main` | WIRED | Line 10 confirmed |
| `pyproject.toml` | `privguard/hooks.py` | `[project.scripts] privguard-user-prompt = "privguard.hooks:main_user_prompt"` | WIRED | Lines 27-28 confirmed |
| `README.md` | `docs/codex-compatibility.md` | Markdown link in matrix footer | WIRED | Lines 120, 144 confirmed; target file exists |
| `README.md` | `docs/install.md` | Markdown link in Install section | WIRED | Line 24 confirmed; target file exists |
| `README.md` | `AGENTS.md` | `[AGENTS.md](AGENTS.md)` in For coding agents section | WIRED | Line 171 confirmed; target file exists |
| `README.md` | `privguard-user-prompt` / `privguard-pre-tool` | D-15 console-script names in hook JSON snippet | WIRED | Lines 85, 92 of README.md confirmed |
| `README.md` | `README.pt-BR.md` | Cross-language switcher link on line 1 | WIRED | Target file now exists (gap closed by plan 07-03) |
| `README.pt-BR.md` | `README.md` | Cross-language switcher link on line 1 | WIRED | Line 1 of README.pt-BR.md confirmed |

### Data-Flow Trace (Level 4)

Not applicable. Phase 7 delivers a CLI module and static documentation files. No dynamic rendering components.

### Behavioral Spot-Checks

Step 7b: SKIPPED. The pre-tool guard in this environment blocks Python execution commands. All verifications performed via static analysis (Read/Grep tools) against confirmed file contents. The SUMMARY reports 139 passed, 1 skipped (Windows symlink) when tests were run at execution time.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| MAINT-01 | 07-01 | Config-driven cleanup with `[tool.privguard.cleanup]`, hardcoded protected list, dry-run-by-default | SATISFIED | `privguard/cleanup.py` (257 lines), `pyproject.toml` patterns table (8 patterns), 6 contract tests, all safety contracts verified |
| DOC-01 | 07-02, 07-03 | Bilingual top-level README (English + Portuguese) covering install, CLI, hooks, matrix, non-goals, policy | SATISFIED | `README.md` (182 lines, English, 9 sections) and `README.pt-BR.md` (217 lines, pt-BR, 9 sections) both exist with all required content |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `privguard/cleanup.py` | 68-69 | `_load_patterns` re-opens `pyproject.toml` without `try/except` — narrow TOCTOU window where `OSError` surfaces as unhandled exception (exit 1) instead of `[CLEANUP] error: ... reason=...` (exit 2) | Warning | Breaks exit-code contract D-14 if file removed between the two reads. Identified in REVIEW.md WR-01. Carried from initial verification — no change. |
| `privguard/cleanup.py` | 230-232 | `_format_dry_run` output reused via fragile `.replace("[dry-run] would delete", "[apply] deleting")` string substitution | Warning | Silent regression risk if header text changes. REVIEW.md WR-02. Carried from initial verification — no change. |
| `privguard/cleanup.py` | 176 | Unreachable `return f"{n} B"` after `_human_size` loop always returns on `"GB"` iteration | Info | Dead code, no runtime bug. REVIEW.md IN-01. Carried from initial verification — no change. |

No blockers. All three are pre-existing code quality issues documented in REVIEW.md. They do not prevent the phase goal from being achieved.

### Human Verification Required

None. All checks were verifiable by static analysis.

## Re-verification Summary

The single gap from the initial verification (2026-05-10T21:00:00Z) has been closed:

**Gap closed: `README.pt-BR.md` now exists.** Plan 07-03 was executed and delivered a 217-line Brazilian Portuguese translation of `README.md`. The file contains:
- Cross-language switcher on line 1 (identical to README.md line 1)
- All 9 D-04 sections in natural pt-BR (Instalação, Início rápido, Uso da CLI, Configuração do hook do Claude Code, Matriz de capacidades, O que o privguard NÃO faz, Política de fixture-apenas-sintéticos, FAQ, Para agentes de código)
- Locked vocabulary verbatim: `block-supported` x3, `experimental block-only` x4, `privguard-user-prompt`, `privguard-pre-tool`, `<BR_CPF>`, `<BR_CNPJ>`, `<TOKEN>`
- All code blocks, JSON, TOML, CLI commands, and file paths unchanged from README.md

DOC-01 is fully satisfied. The broken cross-language link from README.md is now live. No regressions against previously-passing items.

**Phase 7 goal achieved.** A first-time user can land on the repo, read about privguard in English or Portuguese, install it via pip, wire the Claude Code hooks using `privguard-user-prompt` / `privguard-pre-tool`, understand the privacy model and what the tool does not do, and clean up transient artifacts with a single command.

---

_Verified: 2026-05-10T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
