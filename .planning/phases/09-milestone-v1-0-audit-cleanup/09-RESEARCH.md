# Phase 9: Milestone v1.0 Audit Cleanup - Research

**Researched:** 2026-06-11
**Domain:** Documentation-state sync + Python CLI robustness (gap-closure / tech-debt sweep)
**Confidence:** HIGH

## Summary

This is a gap-closure phase, not a feature phase. The source of truth is `.planning/v1.0-MILESTONE-AUDIT.md` (2026-06-10), which enumerates **9 tech-debt items across 5 sources**. There is no CONTEXT.md — the audit document and the ROADMAP Phase 9 success criteria ARE the locked decisions. My job was to confirm the EXACT current state of each target file (the audit's line numbers have drifted) and surface gaps between the audit and current code/docs so the planner can edit with unique string matches and zero re-investigation.

Two material drifts from the audit were found and are flagged below: (1) **`README.pt-BR.md` no longer exists** — the README was restructured AFTER the audit so Portuguese is now `README.md` (default) and English is `README.en.md`; every audit/ROADMAP/REQUIREMENTS reference to `README.pt-BR.md` is now stale and the DOC-01 requirement text itself must be updated to match the shipped layout. (2) **Line numbers drifted** in ROADMAP.md (Phase 9 was inserted into the file): the Phase 7 progress row is now line 229 (audit said 212) and Phase 8 is a trailing section starting line 231. I verified every anchor below by reading the current files.

The regression baseline is confirmed green on this host (`python -m pytest -q` → 252 passed; the 1 skip in the audit baseline is `test_cleanup_apply_refuses_symlinks`, which skips on Windows — see Validation Architecture). The three cleanup.py fixes (WR-01, WR-02, IN-01) are low-severity and self-contained; the existing 6 cleanup contract tests do NOT assert the exact `[apply] deleting` header text, giving the WR-02 refactor latitude as long as the `[dry-run]` / `[apply]` prefixes and the sanitized `[CLEANUP] error: ... reason=...` format are preserved.

**Primary recommendation:** Treat this as a pure string-edit + 3-function-patch phase. Use the verbatim anchors in this document for every edit. Fix the stale `README.pt-BR.md` → `README.md`/`README.en.md` references everywhere they appear in tracked planning docs (this is an extra, audit-missed item the planner MUST include). Keep `python -m pytest` green as the single gate.

## User Constraints

> No CONTEXT.md exists for this phase. The locked-decision source is `.planning/v1.0-MILESTONE-AUDIT.md` (2026-06-10) plus the Phase 9 entry in `.planning/ROADMAP.md` (lines 143-157). These are treated with locked-decision authority.

### Locked Decisions (from audit + ROADMAP Phase 9 success criteria)

1. **REQUIREMENTS.md** — tick `[x]` DOC-01 and MAINT-01; set both traceability rows to `Complete`; coverage note reflects synced state.
2. **ROADMAP.md** — tick `[x]` Phase 7; correct its progress row to `3/3 Complete 2026-05-10`; add Phase 8 + backlog 999.1–999.5 rows to the Progress table (true 13-phase milestone).
3. **README.md (PT) + README.en.md (EN)** — rewrite the warn-vs-block FAQ to document the `PII_GUARD_MODE` selector (block default / warn opt-in non-protective / mask) instead of declaring warn-only "out of scope". DOC-01 wording must match the shipped `README.md` + `README.en.md` layout (NO stale `README.pt-BR.md`).
4. **cleanup.py** — WR-01: guard `_load_patterns()` reopen so a TOCTOU `OSError` surfaces as sanitized `[CLEANUP] error` (exit 2 per D-14); WR-02: build apply/dry-run headers explicitly (no fragile `.replace()`); IN-01: remove the unreachable `return f"{n} B"`.
5. **Regression gate** — `python -m pytest` must stay green at the 252-passed / 1-skipped baseline after all changes.

### Claude's Discretion

- **Item 9 (process / OPTIONAL):** Backfill `999.1-VERIFICATION.md` + `999.2-VERIFICATION.md`, OR accept the SUMMARY self-checks as sufficient for backlog phases. This is a planner/user decision. **Researcher recommendation: ACCEPT the SUMMARY self-checks** (do not backfill). Rationale below in Open Questions.
- Exact wording/formatting of the rewritten FAQ sections (must be faithful to the code behavior documented in "PII_GUARD_MODE behavior" below).
- Whether to also fix the stale `README.pt-BR.md` references in tracked planning docs as part of this phase (researcher recommends YES — see Don't-Miss item).

### Deferred Ideas (OUT OF SCOPE)

- Any v2 requirement (INT-*, LOC-*, ENT-*).
- Any code behavior change beyond the 3 cleanup.py robustness fixes. The README rewrite is doc-only; default behavior stays fail-closed block.
- Touching the `.claude/worktrees/` copies of README files (git worktrees, not the canonical repo files).

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DOC-01 | Bilingual top-level README covering install, CLI usage, hook setup, capability matrix, "does not do", synthetic-only policy | Already SATISFIED by Phase 7 (VERIFICATION 2026-05-10). This phase only ticks the checkbox + traceability row AND updates the requirement text to drop the stale `README.pt-BR.md` reference (current text at REQUIREMENTS.md:65 still names `README.pt-BR.md`). |
| MAINT-01 | Config-driven cleanup with `[tool.privguard.cleanup]` patterns, hardcoded protected list, dry-run-by-default + `--apply` | Already SATISFIED by Phase 7. This phase ticks the checkbox + traceability row. The cleanup.py robustness fixes (WR-01/02, IN-01) harden the already-satisfied MAINT-01 implementation. |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Requirement/roadmap state accuracy | Planning docs (`.planning/*.md`) | — | Pure markdown checkbox/table edits; no runtime impact |
| User-facing mode documentation | Docs (`README.md`, `README.en.md`) | — | Doc-only; describes existing `hooks.py` behavior, changes no code |
| Cleanup CLI error contract (D-14) | CLI / utility code (`privguard/cleanup.py`) | Tests (`tests/test_cleanup.py`) | Exit-code contract lives in `cleanup.py`; contract tests guard it |
| Regression gate | Test suite (`tests/`) | — | `pytest` is the single verification surface; no new tests required |

## Standard Stack

No new dependencies. This phase edits existing files only.

### Core (already present, verified)
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| pytest | installed (collected 252 tests, plugin 9.0.2 per pyc cache name) | Regression gate | Existing project test runner; D-14 contract tests live here |
| tomllib / tomli | stdlib (3.11+) / fallback | Read `pyproject.toml` in cleanup.py | Already imported at cleanup.py:12-15 |

**Installation:** None. `python -m pytest` runs the existing suite.

**Version verification:** No package versions to verify — this phase adds zero dependencies. The cleanup.py tomllib import already has the 3.10 fallback (cleanup.py:12-15).

## Architecture Patterns

### Pattern 1: Match the existing guarded-read idiom for WR-01

The fix for WR-01 already has a canonical template **in the same file**. `_verify_repo_root()` (cleanup.py:55-60) ALREADY wraps a `tomllib.load` in exactly the right try/except with the D-14 contract. `_load_patterns()` (cleanup.py:66-78) does NOT. Make `_load_patterns` mirror the verified sibling.

**Existing guarded read (the template) — cleanup.py:55-60:**
```python
    try:
        with pyproject.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        _err("pyproject.toml unreadable", "pyproject_unreadable")
        raise SystemExit(2)
```

**Current UNGUARDED read in `_load_patterns` — cleanup.py:66-69 (the WR-01 target):**
```python
def _load_patterns(cwd: Path) -> list[str]:
    """Read [tool.privguard.cleanup].patterns. Schema-validate per Pitfall 2."""
    with (cwd / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
```

The fix: wrap lines 68-69 in `try/except (OSError, tomllib.TOMLDecodeError)` → `_err(...)` + `raise SystemExit(2)`, matching the sibling. Reuse a reason code consistent with the `_err` convention (e.g. `pyproject_unreadable` or a new code like `cleanup_pyproject_unreadable`). The planner should pick a reason code and the test (if any added) must match it exactly. **No test currently asserts this path** (see Validation), so the fix is purely additive robustness.

### Pattern 2: Explicit header construction for WR-02

**Current fragile substitution — cleanup.py:230-234 (the WR-02 target):**
```python
    apply_output = (
        _format_dry_run(matches, skips)
        .replace("[dry-run] would delete", "[apply] deleting")
        .replace("Run with --apply to delete.\n", "")
    )
```

`_format_dry_run` (cleanup.py:179-202) hardcodes two strings that the `.replace()` depends on: the header `"[dry-run] would delete (...)"` (line 186) and the trailer `"Run with --apply to delete."` (line 201). The brittle coupling is that any edit to those literals silently breaks `--apply`.

**Recommended refactor:** parameterize `_format_dry_run` with a `mode` (or `apply: bool`) argument so it emits the correct header/trailer directly, e.g. `[dry-run] would delete (...)` + `Run with --apply to delete.` vs `[apply] deleting (...)` + no trailer. Then the `--apply` branch calls `_format_dry_run(matches, skips, apply=True)` with no `.replace()`. This keeps a single formatter and removes the silent-regression risk.

**Constraint:** The output prefixes `[dry-run]` and `[apply]` and the empty-state line `[dry-run] nothing to clean.` (line 184) must be preserved — `tests/test_cleanup.py:64` asserts `"[dry-run]" in captured.out`. No test asserts the literal `[apply] deleting` text, but keeping it is required by the audit's intent and by the `main()` docstring contract.

### Pattern 3: Dead-code removal for IN-01

**Current unreachable return — cleanup.py:168-176 (the IN-01 target):**
```python
def _human_size(n: int) -> str:
    """Return a human-readable byte count (e.g. '12 B', '1.5 KB', '3.2 MB')."""
    if n < 1024:
        return f"{n} B"
    for unit in ("KB", "MB", "GB"):
        n_float = n / (1024 ** ("KB MB GB".split().index(unit) + 1))
        if n_float < 1024 or unit == "GB":
            return f"{n_float:.1f} {unit}"
    return f"{n} B"          # <-- IN-01: unreachable
```

**Confirmed unreachable:** the loop's last iteration has `unit == "GB"`, and the condition `if n_float < 1024 or unit == "GB"` is therefore always True on the GB pass, so the function always returns inside the loop. Line 176 (`return f"{n} B"`) can never execute. Remove it. (Optionally add a `# pragma: no cover` is unnecessary — just delete the line.) No behavior change, no test impact.

### Anti-Patterns to Avoid
- **Editing by line number.** The audit's line numbers are stale (see drift table). Use the verbatim string anchors in this document for unique matches.
- **Rewriting the README warn-mode FAQ as "we now warn by default."** The default is STILL fail-closed block. Warn is opt-in and **non-protective** (`mode_scope=local_development_non_protective`). The FAQ must say so explicitly.
- **Touching `.claude/worktrees/**/README*.md`.** Those are agent git-worktree copies, not the canonical files. Leave them.
- **Changing the 6 cleanup tests to chase the refactor.** The refactor must keep them green as-is; do not weaken assertions.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Guarded TOML read for WR-01 | A new error-handling style | Copy the exact `try/except (OSError, tomllib.TOMLDecodeError)` idiom already at cleanup.py:55-60 | Keeps one D-14 contract; reviewer/tests already understand it |
| Apply/dry-run header text | Two divergent formatter functions | One parameterized `_format_dry_run(..., apply=bool)` | Single source of header truth; removes the `.replace()` coupling entirely |

**Key insight:** Every fix in this phase has an in-repo precedent. WR-01's correct form is literally 10 lines above the bug. Do not invent new patterns.

## Verbatim Edit Anchors (CURRENT state — verified 2026-06-11)

> The planner MUST use these exact strings for unique-match edits. Line numbers are advisory; strings are authoritative.

### REQUIREMENTS.md

**Anchor 1 — DOC-01 checkbox (current line 65). NOTE the stale `README.pt-BR.md` in the text — must also be updated per ROADMAP success criterion 3:**
```
- [ ] **DOC-01**: Project includes a bilingual top-level README (English primary `README.md`, Portuguese secondary `README.pt-BR.md`) covering installation, CLI usage, Claude Code hook setup, the Claude/Codex capabilities matrix, what the guard does *not* do, and the synthetic-fixture-only policy.
```
Required edits: `[ ]` → `[x]` AND fix the layout description. Per the shipped reality, Portuguese is the DEFAULT (`README.md`) and English is `README.en.md`. Suggested new text: "bilingual top-level README (Portuguese default `README.md`, English `README.en.md`)".

**Anchor 2 — MAINT-01 checkbox (current line 69):**
```
- [ ] **MAINT-01**: Repo includes a config-driven cleanup mechanism with patterns declared in `pyproject.toml` (`[tool.privguard.cleanup]`), a hard-coded protected list (`.env`, `data_sensivel/`, `.planning/`, `.git/`, source directories) the script can never delete, and a dry-run-by-default contract that requires an explicit `--apply` flag before deletion.
```
Required edit: `[ ]` → `[x]`.

**Anchor 3 — DOC-01 traceability row (current line 143):**
```
| DOC-01 | Phase 7 | Pending |
```
Required edit: `Pending` → `Complete`.

**Anchor 4 — MAINT-01 traceability row (current line 144):**
```
| MAINT-01 | Phase 7 | Pending |
```
Required edit: `Pending` → `Complete`.

**Anchor 5 — coverage / last-updated footer (lines 146-154):** The Coverage block already reads "Mapped to phases: 34 / Unmapped: 0" (no change needed). Consider appending a new `*Last updated: 2026-06-11 after milestone v1.0 audit cleanup (Phase 9 — ticked DOC-01/MAINT-01, updated DOC-01 README layout text)*` line for provenance (matches the existing footer convention at lines 153-154).

### ROADMAP.md

**Anchor 6 — Phase 7 checkbox in the Phases list (current line 21):**
```
- [ ] **Phase 7: Project README + Repo Hygiene** - First-time user can read a bilingual (EN + PT-BR) README and clean up repo cruft via a config-driven, fail-safe cleanup mechanism.
```
Required edit: `[ ]` → `[x]`. (Optional: the "EN + PT-BR" label is now imprecise given the README restructure; the planner may align it, but this is cosmetic and not in the audit scope.)

**Anchor 7 — Phase 7 progress-table row (current line 229, audit said 212):**
```
| 7. Project README + Repo Hygiene | 0/TBD | Not started | - |
```
Required edit → `| 7. Project README + Repo Hygiene | 3/3 | Complete | 2026-05-10 |` (3 plans confirmed: 07-01/02/03 SUMMARYs exist; date from audit roll-up).

**Anchor 8 — Progress-table header + existing rows (current lines 221-229):** The table currently STOPS at Phase 7. Append rows for Phase 8 and backlog 999.1–999.5 immediately after the Phase 7 row. Verified completion data (from audit roll-up table, lines 64-76, and SUMMARY presence):

| Row to add | Plans | Status | Completed |
|------------|-------|--------|-----------|
| 8. Hook Mode Selector | 2/2 | Complete | 2026-05-25 |
| 999.1 WebFetch Allowlist | 2/2 | Complete (no VERIFICATION.md) | 2026-05-27* |
| 999.2 Audit Log | 1/1 | Complete (no VERIFICATION.md) | 2026-05-21 |
| 999.3 Masking Gaps (RG/CNPJ/PIX) | 1/1 | Complete | 2026-05-21 |
| 999.4 CPF Leniency Mode | 2/2 | Complete | 2026-05-21 |
| 999.5 Detection Hardening v2 | 4/4 | Complete | 2026-05-24 |

*999.1 has no VERIFICATION.md and no dated SUMMARY verified in this session; STATE.md last_activity (line 8) shows "2026-05-27 — Phase 999.1 execution started". The audit roll-up (line 72) lists it `complete` with no date. Planner: use 2026-05-27 or leave date as `complete` — flag as the one soft anchor. The exact phase title for the 999.x rows should match the audit roll-up labels (lines 72-76) for consistency.

**Anchor 9 — "Execution Order" line (current line 219):**
```
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7
```
This stops at 7. Optional consistency update to reflect 1→...→7→8 + backlog; not strictly in the audit's 9 items but improves table accuracy alongside Anchor 8.

**Anchor 10 — Phase 8 trailing section (current lines 231-241):** Phase 8 currently exists ONLY as an `### Phase 8:` section AFTER the Progress table. Adding it to the table (Anchor 8) resolves the audit complaint. The planner may leave the trailing detail section in place (it carries plan detail) or relocate it for tidiness — the audit only requires the table to include Phase 8.

### README.md (Portuguese — DEFAULT file)

**Anchor 11 — warn-vs-block FAQ (current lines 244-251):**
```
### Por que ele bloqueia em vez de avisar?

O modo somente-aviso está explicitamente fora do escopo (consulte
[O que o privguard NÃO faz](#o-que-o-privguard-não-faz)). O valor central do privguard é impedir
que dados sensíveis alcancem um provedor externo de LLM — um aviso que o usuário pode ignorar não
satisfaria esse objetivo. O comportamento fail-closed estrito é o padrão para fluxos de trabalho
com provedores externos; a reescrita é usada apenas em superfícies onde a substituição de payload
de saída é verificada.
```
Required edit: rewrite to document `PII_GUARD_MODE` (block default / warn opt-in non-protective / mask). The default-is-block message stays; "fora do escopo" claim is removed. Use the verified behavior in "PII_GUARD_MODE behavior" below.

### README.en.md (English)

**Anchor 12 — warn-vs-block FAQ (current lines 214-216):**
```
### Why does it block instead of warn?

Warning-only mode is explicitly out of scope (see [What privguard does NOT do](#what-privguard-does-not-do)). The core value of privguard is preventing sensitive data from reaching an external LLM provider — a warning that the user can ignore would not satisfy that goal. Strict fail-closed behavior is the default for external-provider workflows; rewrite is only used on surfaces where outbound payload replacement is verified.
```
Required edit: same rewrite as Anchor 11, in English. Keep parity between the two files.

### cleanup.py
- WR-01 anchor: lines 66-69 (see Pattern 1 verbatim).
- WR-02 anchor: lines 230-234 + the `_format_dry_run` literals at lines 184, 186, 201 (see Pattern 2).
- IN-01 anchor: line 176 `    return f"{n} B"` (see Pattern 3).

## PII_GUARD_MODE behavior (VERIFIED in code — basis for README rewrite)

Source: `privguard/hooks.py` lines 227-277 (UserPromptSubmit) and 360-378 (PreToolUse), read 2026-06-11.

| Mode | Env value | Behavior on PII detected | Exit code | Protective? |
|------|-----------|--------------------------|-----------|-------------|
| **block** (DEFAULT) | unset or `block` | Blocks prompt; sanitized `[PII-GUARD BLOQUEADO]` diagnostic to stderr | 2 | Yes (fail-closed) |
| **warn** | `warn` | Allows prompt through; emits JSON context / `action=warn`; tagged `mode_scope=local_development_non_protective` | 0 | **No** — opt-in, non-protective |
| **mask** | `mask` | Still BLOCKS (exit 2); shows masked version in stderr for manual resubmit. If mask cannot be verified → block with `mask_verification_failed` | 2 | Yes (block + show-masked) |
| **scrub** | `scrub` | Removed. Emits one-line notice and falls through to default block | 2 | Yes |

Key facts for the FAQ (all `[VERIFIED: privguard/hooks.py]`):
- Default is fail-closed block; nothing changed about the default.
- `warn` is explicitly **non-protective** and intended for local development only (`local_development_non_protective`, hooks.py:170,195).
- `mask` never forwards a sanitized payload automatically — Claude Code's UserPromptSubmit schema (v2.1.150) has no prompt-replacement field, so block+show-masked is the only safe path (STATE.md decision [Phase 08], line 94). Document mask as "blocks AND prints a masked version you can copy-paste."
- The README must NOT claim privguard "warns by default" or "automatically masks" — both would be overclaims contradicting the verified behavior.

## Runtime State Inventory

> This is a rename-adjacent / doc-sync phase. Inventory of runtime state that a file-only edit would miss:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no datastores reference any renamed string. Verified: no DB/collection keys involved. | None |
| Live service config | None — no external service config embeds the edited strings. | None |
| OS-registered state | None — no scheduled tasks / services reference these docs. | None |
| Secrets/env vars | `PII_GUARD_MODE` is read at runtime (hooks.py:227,360) but is being DOCUMENTED, not renamed. No env-var name change. | None |
| Build artifacts | `privguard/__pycache__/hooks.cpython-313.pyc` and `.cpython-314.pyc` are stale-but-harmless compiled caches (matched `PII_GUARD_MODE` grep). cleanup.py edits will leave a stale `cleanup` pyc until next run. | None required; `privguard cleanup` itself clears `__pycache__/` |
| **Stale doc references** | **`README.pt-BR.md` no longer exists** but is still NAMED in: REQUIREMENTS.md:65 (DOC-01 text), ROADMAP.md:133 (Phase 7 SC1) and ROADMAP.md:151 (Phase 9 SC3 — which itself instructs removing the stale ref). The audit (.planning/v1.0-MILESTONE-AUDIT.md) names it at lines 21,137,165 but the audit is a historical record — do NOT edit it. | Fix the live references in REQUIREMENTS.md and (optionally) ROADMAP.md:133. The `.claude/worktrees/**` copies are git worktrees — IGNORE. |

**The canonical question — after every file edit, what still references the old layout?** Only the audit document (historical, leave as-is) and `.claude/worktrees/` (worktree copies, not canonical). All LIVE planning/doc references to `README.pt-BR.md` must be corrected. This is an audit-MISSED item: the audit was written against the pre-restructure layout and still says "README.md / README.pt-BR.md". The phase goal (ROADMAP:151) explicitly requires "no stale `README.pt-BR.md` reference."

## Common Pitfalls

### Pitfall 1: Editing the audit document itself
**What goes wrong:** Treating `.planning/v1.0-MILESTONE-AUDIT.md` as a target to "fix."
**Why it happens:** It contains stale `README.pt-BR.md` and stale line numbers.
**How to avoid:** The audit is an immutable historical record (dated 2026-06-10). Fix the LIVE files it points to, not the audit.

### Pitfall 2: WR-02 refactor breaking the empty-state path
**What goes wrong:** Refactoring `_format_dry_run` and forgetting the `if not matches and not skips:` early return (line 184), which emits `[dry-run] nothing to clean.\n`.
**Why it happens:** The early return also needs an apply-mode equivalent or graceful handling.
**How to avoid:** Cover both branches when parameterizing; in apply mode with nothing to clean, emit an `[apply]`-prefixed or neutral message. No test currently exercises apply+empty, but keep it sane.

### Pitfall 3: Reason-code mismatch in WR-01
**What goes wrong:** Adding a try/except with a reason code that no test expects (harmless now) — but if the planner ALSO adds a test, the literal must match.
**How to avoid:** Pick the reason code first, use it in both `_err()` and any new test. `_err` format is fixed: `[CLEANUP] error: {message} reason={reason_code}` (cleanup.py:37-39).

### Pitfall 4: Breaking PT/EN README parity
**What goes wrong:** Rewriting only one language file, or letting the two FAQs diverge in substance.
**How to avoid:** Edit Anchor 11 (PT) and Anchor 12 (EN) together; same three-mode table content in both.

## Drift Table (audit 2026-06-10 → current 2026-06-11)

| Audit claim | Current reality | Impact |
|-------------|-----------------|--------|
| DOC-01 at line 65 | Confirmed line 65 | Anchor stable |
| MAINT-01 at line 69 | Confirmed line 69 | Anchor stable |
| Traceability DOC-01 line 143 / MAINT-01 line 144 | Confirmed 143/144 | Anchors stable |
| ROADMAP Phase 7 checkbox line 21 | Confirmed line 21 | Anchor stable |
| ROADMAP Phase 7 progress row line 212 | **Now line 229** (Phase 9 inserted into file) | Use string anchor, not line |
| Progress table ends at Phase 7 (lines 204-212) | **Now lines 221-229** | Append after line 229 |
| README FAQ at README.md:244-251 | Confirmed PT at 244-251; EN at README.en.md:214-216 | Both anchors stable |
| `README.pt-BR.md` exists | **Does NOT exist** — restructured to README.md (PT) + README.en.md (EN) | Extra fix: correct stale refs |
| Baseline 252 passed / 1 skipped | Confirmed: `pytest -q` → 252 passed (1 skip = Windows symlink skip) | Gate confirmed |
| 6 cleanup contract tests | Confirmed: 6 tests in test_cleanup.py (5 run + 1 Windows-skip) | Gate confirmed |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (plugin 9.0.2 per `tests/__pycache__/*pytest-9.0.2*` cache name) |
| Config file | none detected at repo root (no pytest.ini/pyproject `[tool.pytest]` verified); collection works via default discovery |
| Quick run command | `python -m pytest tests/test_cleanup.py -q` |
| Full suite command | `python -m pytest -q` |

### Phase Requirements → Test Map
| Req / Item | Behavior | Test Type | Automated Command | File Exists? |
|------------|----------|-----------|-------------------|-------------|
| DOC-01 / MAINT-01 sync | Markdown checkbox/table edits | manual review | (no automated test — doc state) | n/a |
| README FAQ rewrite | Doc-only | manual review | (no automated test) | n/a |
| WR-01 guarded read | TOCTOU OSError → exit 2 + `[CLEANUP] error` | unit (optional add) | `python -m pytest tests/test_cleanup.py -q` | ✅ test_cleanup.py (no test for this exact path yet) |
| WR-02 explicit headers | dry-run/apply prefixes preserved | unit (existing) | `python -m pytest tests/test_cleanup.py::test_cleanup_apply_deletes_pycache -q` | ✅ |
| IN-01 dead-code removal | no behavior change | unit (existing, regression) | `python -m pytest tests/test_cleanup.py -q` | ✅ |
| Regression gate | full suite green | suite | `python -m pytest -q` | ✅ |

### Sampling Rate
- **Per cleanup.py edit:** `python -m pytest tests/test_cleanup.py -q` (fast, 6 tests)
- **Per phase merge / gate:** `python -m pytest -q` (must show 252 passed / 1 skipped)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- None required. Existing test infrastructure covers all functional changes.
- **Optional (Claude's discretion):** add one WR-01 test asserting `[CLEANUP] error:` + `reason=<code>` + exit 2 when `pyproject.toml` is removed between `_verify_repo_root` and `_load_patterns`. Hard to trigger deterministically (TOCTOU); a monkeypatch of `_load_patterns`'s open to raise `OSError` is the practical approach. Not strictly required — the fix is additive robustness and the audit lists it low-severity.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python | All | ✓ | 3.13 + 3.14 caches present | — |
| pytest | Regression gate | ✓ | plugin 9.0.2 | — |
| tomllib | cleanup.py | ✓ | stdlib (3.11+); tomli fallback wired | tomli |

**Missing dependencies:** None. This phase has no new external dependencies.

## Security Domain

> `security_enforcement` is not set to `false` in config — included. This phase is low security-surface (doc edits + 3 robustness fixes), but the cleanup.py changes touch the sanitized-output contract.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | `_load_patterns` schema-validates the cleanup table (cleanup.py:71-77); WR-01 adds OSError guarding. Keep both. |
| V7 Error Handling & Logging | yes | D-14 exit-code contract + `_err`/`_warn` sanitized writers (cleanup.py:37-43). WR-01 must route the new error through `_err` (paths only, never contents — POL-04). |
| V6 Cryptography | no | n/a |
| V2/V3/V4 Auth/Session/Access | no | n/a (local CLI/doc phase) |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Sensitive value leaking via cleanup error message | Information Disclosure | `_err` emits paths + reason codes only, never file contents (POL-04); WR-01 fix must use `_err`, not a raw exception print. The 6 cleanup tests assert `_assert_sanitized` over forbidden synthetic values — keep green. |
| README overclaim ("we mask/warn automatically") | Repudiation / false assurance | FAQ rewrite must state default=block, warn=non-protective, mask=block+show. No automatic-masking claim (CDX-03 / claim-gate posture). |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | 999.1 completion date is ~2026-05-27 (from STATE.md last_activity); audit lists it `complete` with no date | Anchor 8 | Low — a progress-table date; planner can use "complete" if uncertain |
| A2 | No repo-root pytest config file exists (default discovery only) | Validation Architecture | Low — `pytest -q` works regardless; affects only "Config file" cell |
| A3 | The 1 skipped test in the 252/1 baseline is `test_cleanup_apply_refuses_symlinks` (Windows skip via `os.name == "nt"`) | Summary / Validation | Low — confirmed the skip guard exists at test_cleanup.py:133-134; on this host pytest summary reported 252 passed |

## Open Questions

1. **Backfill 999.1/999.2 VERIFICATION.md or accept SUMMARY self-checks? (Audit item 9, OPTIONAL)**
   - What we know: Both backlog phases are functionally complete; SUMMARY self-checks pass; backlog phases carry no v1 requirements; the audit explicitly says "flagged for process completeness only" (audit line 143).
   - What's unclear: Whether the user wants formal VERIFICATION.md for milestone-close tidiness.
   - **Recommendation: ACCEPT the SUMMARY self-checks; do NOT backfill.** Rationale: backlog phases introduce no orphan requirements, the green suite covers them, and the audit itself ranks this as process-only. Backfilling fabricates retroactive verification records dated after-the-fact, which is lower-integrity than honestly labeling them "complete (SUMMARY self-check)". If the planner/user disagrees, the progress-table rows already mark them "(no VERIFICATION.md)" transparently.

2. **Update the "EN + PT-BR" label at ROADMAP.md:21 and the SC1 wording at ROADMAP.md:133?**
   - These reference the pre-restructure layout. The audit's 9 items don't list them, but ROADMAP:133 names `README.pt-BR.md` which is now stale.
   - **Recommendation:** Fix ROADMAP:133's `README.pt-BR.md` → `README.en.md` as part of the stale-reference sweep (consistent with Phase 9 SC3 intent). The line-21 "EN + PT-BR" label is cosmetic — planner's discretion.

## Sources

### Primary (HIGH confidence — read this session)
- `.planning/v1.0-MILESTONE-AUDIT.md` — the 9 tech-debt items, roll-up table, recommendations
- `.planning/REQUIREMENTS.md` — DOC-01/MAINT-01 checkboxes (65,69) + traceability rows (143,144)
- `.planning/ROADMAP.md` — Phase 7 checkbox (21), progress table (221-229), Phase 8 trailing section (231-241), Phase 9 success criteria (143-157)
- `.planning/STATE.md` — phase progress, Phase 8 decisions (mask-mode exit-2 rationale)
- `README.md` (PT default) — FAQ lines 244-251
- `README.en.md` (EN) — FAQ lines 214-216
- `privguard/cleanup.py` — WR-01 (66-69), WR-02 (179-202, 230-234), IN-01 (168-176), _err/_warn contract (37-43), _verify_repo_root template (55-60)
- `privguard/hooks.py` — PII_GUARD_MODE behavior (170,195,227-277,360-378)
- `tests/test_cleanup.py` — 6 cleanup contract tests + sanitization assertions
- Live commands: `python -m pytest -q` (252 passed), `python -m pytest tests/test_cleanup.py -q` (cleanup tests)

### Secondary
- `.planning/config.json` — confirmed `nyquist_validation: false`, `commit_docs: true`

### Tertiary (LOW confidence — flagged)
- 999.1 completion date inferred from STATE.md last_activity (A1)

## Metadata

**Confidence breakdown:**
- Edit anchors (verbatim strings): HIGH — every anchor read from current files this session
- cleanup.py fixes: HIGH — in-repo precedent exists; unreachable code mathematically confirmed
- README mode behavior: HIGH — read directly from hooks.py
- Regression baseline: HIGH — ran the suite
- ROADMAP 999.1 date: LOW — inferred (A1)

**Research date:** 2026-06-11
**Valid until:** 2026-07-11 (stable; only invalidated if the target files are edited before planning)
