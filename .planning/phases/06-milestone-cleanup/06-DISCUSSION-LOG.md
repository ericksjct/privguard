# Phase 6: Milestone Cleanup - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-06
**Phase:** 06-milestone-cleanup
**Areas discussed:** Console-script alias, Public API re-exports, Python 3.14 extras gating, PKG-02 wording

---

## Gray Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Console-script alias | Drop, install+test, or rename canonical | ✓ |
| Public API re-exports | Audit-list, +types, or exclude hook entry points | ✓ |
| Python 3.14 extras gating | Document, tighten requires-python, drop, or add fallback extras | ✓ |
| PKG-02 wording | Rewrite direct, rewrite + historical note, or keep | ✓ |

**User's choice:** All four areas selected.

---

## Console-Script Alias

| Option | Description | Selected |
|--------|-------------|----------|
| Drop the alias (Recommended) | Remove `privacy-guard` from pyproject.toml; canonical = `privguard` | ✓ |
| Keep alias, install + smoke test | Reinstall and assert both entry points resolve | |
| Rename canonical to `privacy-guard` | Reopen Phase 1 D-01 — not recommended | |

**User's choice:** Drop the alias.
**Notes:** No code/tests reference `privacy-guard` as entry point. Alias was declared but never installed in active editable install. Phase 1 D-01 already locked canonical name.

---

## Public API Re-exports

| Option | Description | Selected |
|--------|-------------|----------|
| Audit list verbatim (Recommended) | 5 symbols: `classify_command`, `main_user_prompt`, `main_pre_tool`, `build_claude_doctor_report`, `CODEX_COMPATIBILITY` | |
| Audit list + Codex types + `CommandClassification` | 9 symbols including supporting types | ✓ |
| Data + classifiers only, exclude hook entry points | 4 symbols (drops the two `main_*` adapter entries) | |

**User's choice:** "decide para mim" — Claude decided Option 2 (audit list + types).
**Notes:** Decision rationale: shipping `CODEX_COMPATIBILITY` without `CodexCompatibilityRow` / `CodexSupportLabel` is a half-API; consumers iterating the tuple need the row dataclass for typed attribute access. Same for `classify_command` without its return type `CommandClassification`. Audit names 5 as gap-examples, not exhaustive whitelist; ROADMAP success criterion #5 still satisfied because `{5} ⊂ {9}`. Cost of the 4 extra names is trivial; benefit is a coherent type-complete public API at v1 close.

---

## Python 3.14 Extras Gating

| Option | Description | Selected |
|--------|-------------|----------|
| Document the gating (Recommended) | Comment in pyproject.toml + note in docs explaining presidio/spacy don't support 3.14 yet | ✓ |
| Tighten `requires-python` to `<3.14` | Make `pip install privguard` fail loudly on 3.14 | |
| Drop the gating, let presidio fail | Remove `python_version < '3.14'` markers; pip resolver fails with upstream error | |
| Add a 3.14-only fallback extras group | Keep `[full]` gated, add `[lightweight]` extras for documentation | |

**User's choice:** Document the gating.
**Notes:** User initially asked for a plain-language explanation in Portuguese before deciding. Explanation covered: what presidio is, what extras mean, why upstream lacks 3.14 support, and the silent-no-op UX bug on 3.14 (`pip install privguard[full]` reports success but installs zero packages). Lightweight detection still works on 3.14 (134 tests pass). Documenting is the lowest-risk path: keeps the existing behavior the lightweight users depend on, makes the silent gap visible. No README/install doc exists yet — preferred new location is `docs/install.md` with planner's discretion to fold elsewhere.

---

## PKG-02 Wording

| Option | Description | Selected |
|--------|-------------|----------|
| Rewrite direct (Recommended) | New text: "Developer can run a `privguard` CLI entry point..." | ✓ |
| Rewrite + historical note | Same text plus parenthesis on rename history | |
| Keep wording, add parenthesis | Leave `privacy-guard`, add note that canonical is `privguard` | |

**User's choice:** Rewrite direct, no historical note.
**Notes:** Rename trail lives in Phase 1 D-01 / 01-CONTEXT.md and (after this phase) in Phase 6's commit message and CONTEXT.md. Cleaner final state in REQUIREMENTS.md.

---

## Claude's Discretion

Items the user did not need to weigh in on; planner executes:
- Mechanical sync edits (M-01..M-07): REQUIREMENTS.md checkboxes, traceability table, ROADMAP.md Phase 5 status / progress row, ROADMAP.md `privacy-guard` legacy-name purge, SUMMARY frontmatter backfills for 04-01 and 05-01.
- Commit ordering (atomic single-commit vs per-artifact commits).
- Whether to create new `docs/install.md` or fold the Python 3.14 note into an existing doc.

## Deferred Ideas

- Drift-prevention regression test that locks REQUIREMENTS.md checkboxes against VERIFICATION.md verdicts — useful but out of scope for v1 close, candidate for v2 backlog.
- Re-installing presidio on a 3.10–3.13 venv to actually run DET-06 parity locally — environment work, not Phase 6.
- Renaming canonical command back to `privacy-guard` — explicitly rejected (would reopen Phase 1 D-01).
