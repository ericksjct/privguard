# Phase 7: Project README + Repo Hygiene - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-08
**Phase:** 07-readme-hygiene
**Areas discussed:** README structure, README scope & depth, Cleanup command shape & patterns, Cleanup safety surface

---

## Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| README structure | Two separate files vs single bilingual file vs primary-EN with pt-BR digest | ✓ |
| README scope & depth | Phase-criteria minimum vs +walkthrough vs +FAQ; relationship to AGENTS.md | ✓ |
| Cleanup command shape & patterns | Subcommand vs script; default patterns; protected list location | ✓ |
| Cleanup safety surface | Repo-root guard, confirmation, symlinks, JSON output | ✓ |

**User's choice:** All four areas selected (multi-select).

---

## README Structure

### Q1: How should the bilingual README be laid out?

| Option | Description | Selected |
|--------|-------------|----------|
| Two files, cross-linked | `README.md` (EN, primary) + `README.pt-BR.md` (PT), each with header link to the other. Standard OSS Brazilian-project pattern. | ✓ |
| Single file, two sections | One `README.md` with `# (English)` then `# (Português)` sections, anchor-linked at the top. | |
| EN canonical + pt-BR digest | Full EN README; pt-BR is a shorter Portuguese digest linking back to EN for deep sections. | |

**User's choice:** Two files, cross-linked
**Notes:** Matches phase success criterion #1 wording exactly. → captured as D-01.

### Q2: How prominent should the language switcher be at the top of each README?

| Option | Description | Selected |
|--------|-------------|----------|
| First line, plain link | `🇧🇷 [Leia em português](README.pt-BR.md)` as a single line, compact. | |
| Above title, badge style | A row of language badges (`[English] [Português]`) above the H1, visually distinct. | ✓ |
| Footer only | Cross-link sits at the bottom of each file. Minimalist top, weaker discoverability. | |

**User's choice:** Above title, badge style
**Notes:** Maximizes discoverability for Brazilian users landing on EN README. → captured as D-02.

### Q3: When the EN and pt-BR versions drift, what's the policy?

| Option | Description | Selected |
|--------|-------------|----------|
| Both must update together | Any PR touching one README must also update the other (or declare "translation pending"). | ✓ |
| EN canonical, pt-BR catches up | EN updates first; pt-BR is updated in same PR when feasible, or tracking issue is opened. | |
| No formal policy | Update whichever as needed; drift is accepted. | |

**User's choice:** Both must update together
**Notes:** Strongest parity, aligned with Brazil-first principle in PROJECT.md. → captured as D-03.

### Q4: Continue or move on?

**User's choice:** Next area

---

## README Scope & Depth

### Q5: What scope should the v1 README cover?

| Option | Description | Selected |
|--------|-------------|----------|
| Phase criteria minimum | Install, CLI usage, hook setup, capabilities matrix, non-goals, synthetic policy. | |
| Minimum + walkthrough | All of the above + "in 60 seconds" quickstart with synthetic masking + hook-config snippet. | |
| Minimum + walkthrough + FAQ | All of the above + FAQ entries. | ✓ |

**User's choice:** Minimum + walkthrough + FAQ
**Notes:** Most onboarding-friendly. Captured 4 required FAQ questions in CONTEXT.md D-04. → captured as D-04.

### Q6: How should README relate to the existing 22K `AGENTS.md`?

| Option | Description | Selected |
|--------|-------------|----------|
| Independent, both at root | README for humans, AGENTS.md for agents; README has short "For coding agents" link. | ✓ |
| README links into AGENTS.md sections | README defers deep technical sections to AGENTS.md anchors. | |
| Move AGENTS.md content into docs/ | Promote AGENTS.md content into `docs/architecture.md` etc.; AGENTS.md becomes a stub. | |

**User's choice:** Independent, both at root
**Notes:** AGENTS.md is GSD-generated and may regenerate; coupling human docs to it is risky. → captured as D-05.

### Q7: How should the capabilities matrix appear in README?

| Option | Description | Selected |
|--------|-------------|----------|
| Condensed table + link | 4-row table (UserPromptSubmit, PreToolUse, Codex prompt, Codex tools) with footer link to `docs/codex-compatibility.md`. | ✓ |
| Full matrix inline | Embed full `docs/codex-compatibility.md` matrix directly in README. | |
| Status badges only | Just shields.io-style badges with link to docs. | |

**User's choice:** Condensed table + link
**Notes:** Status visible at-a-glance, evidence stays in dedicated doc, drift risk minimized. → captured as D-06.

### Q8: Continue or move on?

**User's choice:** Next area

---

## Cleanup Command Shape & Patterns

### Q9: Where should the cleanup command live?

| Option | Description | Selected |
|--------|-------------|----------|
| Subcommand: `privguard cleanup` | Logic in `privguard/cleanup.py`, wired into `privguard/cli.py`. | ✓ |
| Standalone: `scripts/cleanup.py` | Lighter, no CLI plumbing, run as `python scripts/cleanup.py --apply`. | |
| Both | Logic in package + thin script wrapper. | |

**User's choice:** Subcommand: `privguard cleanup`
**Notes:** Matches Phase 1 package-based code decision; ships in installed package; testable. → captured as D-07.

### Q10: Which default patterns ship in `[tool.privguard.cleanup]`?

| Option | Description | Selected |
|--------|-------------|----------|
| Standard Python set | `__pycache__/`, `*.py[cod]`, `.pytest_cache/`, `.coverage`, `htmlcov/`, `dist/`, `build/`, `*.egg-info/`. | ✓ |
| Standard + linter caches | Above + `.mypy_cache/`, `.ruff_cache/`, `.tox/`, `.nox/`. | |
| Conservative | Just `__pycache__/`, `.pytest_cache/`, `.coverage`. | |

**User's choice:** Standard Python set
**Notes:** Linter caches deferred until those tools are added to pyproject.toml. → captured as D-08.

### Q11: Where does the protected list live?

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded in `privguard/cleanup.py` | Cannot be overridden by config; maintainer must edit code. | ✓ |
| In `pyproject.toml` `[tool.privguard.cleanup]` | Alongside cleanup patterns, easier to inspect in one place. | |
| Hardcoded + extendable via config | Hardcoded baseline cannot be removed; pyproject can ADD. | |

**User's choice:** Hardcoded in `privguard/cleanup.py`
**Notes:** Strongest fail-closed posture; matches success criterion #2 "hard-coded protected list" wording. → captured as D-09.

### Q12: On dry-run, what should the cleanup output look like?

| Option | Description | Selected |
|--------|-------------|----------|
| Grouped by pattern, with sizes | `__pycache__/  2 dirs / 47 files / 1.2 MB` style, total at top. | ✓ |
| Flat path list only | One path per line. Simplest, machine-readable. | |
| Two-mode: text default + `--json` | Default human-readable; `--json` flag for CI. | |

**User's choice:** Grouped by pattern, with sizes
**Notes:** `--json` mode deferred to v2 (CI integration not requested for v1). → captured as D-10.

### Q13: Continue or move on?

**User's choice:** Next area

---

## Cleanup Safety Surface

### Q14: Should the script enforce running inside the privguard repo root?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — require `.git/` + `pyproject.toml` with `name = "privguard"` | Refuses elsewhere. | ✓ |
| Yes — require `.git/` only | Lighter check; doesn't verify it's privguard specifically. | |
| No root guard | Relies on dry-run + protected list as the only safety. | |

**User's choice:** Yes — require `.git/` + `pyproject.toml` with `name = "privguard"`
**Notes:** Strongest accidental-cwd guard; matches fail-closed posture. → captured as D-11.

### Q15: How should `--apply` confirm before deleting?

| Option | Description | Selected |
|--------|-------------|----------|
| `--apply` alone — no further prompt | If you typed `--apply`, you meant it. | ✓ |
| `--apply` shows summary + interactive `y/N`; `--yes` skips | Belt-and-suspenders. | |
| `--apply` requires typing the count of files | Most paranoid; high friction. | |

**User's choice:** `--apply` alone — no further prompt
**Notes:** Dry-run + repo-root guard + protected list + symlink refusal already form the safety net. → captured as D-12.

### Q16: How should the cleanup handle symlinks?

| Option | Description | Selected |
|--------|-------------|----------|
| Refuse to delete symlinks | Skip and warn. Avoids following symlinks out of repo root. | ✓ |
| Delete the symlink, never follow it | Standard rm behavior. | |
| Follow and delete contents | Risky; not recommended. | |

**User's choice:** Refuse to delete symlinks
**Notes:** Maximally conservative; aligns with fail-closed defaults across the project. → captured as D-13.

### Q17: What exit codes should `privguard cleanup` use?

| Option | Description | Selected |
|--------|-------------|----------|
| 0 success / 2 misuse / 1 fail | Matches privguard's existing CLI convention. | ✓ |
| 0 / 1 only | Simpler, less granular. | |
| 0 / 3 partial / 1 fail | Adds exit 3 for partial success. | |

**User's choice:** 0 success / 2 misuse / 1 fail
**Notes:** Matches Phase 2 / 3 CLI conventions. → captured as D-14.

### Q18: Done or explore more?

**User's choice:** I'm ready for context

---

## Claude's Discretion

The planner / executor handles these without further user input:

- Section ordering within each README (sections required, order at planner discretion).
- Exact FAQ wording (questions fixed, answers drafted from PROJECT.md / verifications).
- Synthetic CPF/CNPJ values used in masking demo (reuse existing `tests/` fixtures).
- Quickstart code-block style (single block vs. multi-step prose).
- `docs/install.md` consolidation policy (link-out vs. absorb-and-slim).
- Cleanup CLI flag names beyond `--apply` (e.g. `--verbose`, `--quiet`).
- Implementation detail of `privguard/cleanup.py` (stdlib-only, planner picks safest pattern).

## Deferred Ideas

Captured in CONTEXT.md `<deferred>` section. Highlights:

- Linter cache patterns in cleanup defaults (when tools are introduced).
- `--json` output mode for cleanup (v2 enterprise audit).
- `--yes` / interactive `y/N` confirmation (rejected for v1).
- EN/pt-BR README drift-prevention regression test (out of scope for v1).
- README badges (CI / license / PyPI) — when CI / publication exist.
- License file and `CHANGELOG.md` — pre-publication concern.
- Promoting `AGENTS.md` content into structured `docs/` (would expand scope).
- Internationalization beyond pt-BR — out of scope per Brazil-first principle.
