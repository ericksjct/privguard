# Phase 6: Milestone Cleanup - Context

**Gathered:** 2026-05-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 closes the 11 tech-debt items identified in `.planning/v1.0-MILESTONE-AUDIT.md` so the
v1 snapshot is internally consistent. The audit verdict was `tech_debt`, not `gaps_found`: 32/32
v1 requirements satisfied, 5/5 phases verified, 134 tests pass, 0 critical blockers. What remains
is documentation drift, packaging hygiene, public API surface alignment, and Python 3.14 install
behavior — items that must agree with the verified state before the milestone can close.

The phase does **not**:
- Add new product features or runtime behavior.
- Add a README (DOC-01) or repo-cleanup mechanism (MAINT-01) — those are scoped to Phase 7.
- Add CI / drift-prevention regression tests — out of scope for v1 close (candidate for v2 backlog).
- Touch detection, masking, policy, hook, or codex runtime code beyond `__init__.py` re-exports.

The phase does:
- Sync REQUIREMENTS.md checkboxes and traceability table with VERIFICATION.md verdicts.
- Sync ROADMAP.md Phase 5 status, progress row, and remove `privacy-guard` legacy-name drift.
- Decide the `privacy-guard` console-script alias question: drop it (D-01).
- Re-export the Phase 03/04 public surface from `privguard/__init__.py.__all__` (D-02).
- Document the Python 3.14 presidio/spacy extras gating (D-03).
- Rewrite REQUIREMENTS.md PKG-02 to canonical `privguard` (D-04).
- Backfill `requirements_completed:` frontmatter in 04-01-SUMMARY.md and 05-01-SUMMARY.md.

</domain>

<decisions>
## Implementation Decisions

### Console-Script Alias (audit item: pyproject.toml line 20)

- **D-01:** Drop the `privacy-guard = "privguard.cli:main"` line from `pyproject.toml`.
  Phase 1 D-01 locked the canonical name to `privguard`; the alias was declared but never
  installed in the active editable install. No code, hook adapter, or test references
  `privacy-guard` as the entry-point name. After D-01, `pyproject.toml [project.scripts]`
  must contain only the `privguard` line.

### Public API Re-exports (audit item: privguard/__init__.py)

- **D-02:** Extend `privguard/__init__.py.__all__` to re-export the **9** Phase 03/04 symbols
  below. The audit names 5; this decision adds 4 supporting types so the public API is
  type-coherent (e.g. `CODEX_COMPATIBILITY` is iterable but consumers also need the row
  dataclass and label vocabulary; `classify_command` returns `CommandClassification`).
  Imports stay regular (no submodule re-exports beyond name binding):
  - From `privguard.policy`: `classify_command`, `CommandClassification`
  - From `privguard.hooks`: `main_user_prompt`, `main_pre_tool`
  - From `privguard.diagnostics`: `build_claude_doctor_report`
  - From `privguard.codex`: `CODEX_COMPATIBILITY`, `CodexCompatibilityRow`,
    `CodexSupportLabel`, `get_codex_compatibility`

### Python 3.14 Extras Gating (audit item: environment / packaging)

- **D-03:** Document the existing presidio/spacy gating; do **not** change `requires-python`
  and do **not** drop the `python_version < '3.14'` markers. Action items:
  1. Add a comment block in `pyproject.toml` (above `[project.optional-dependencies]`)
     stating that presidio-analyzer / presidio-anonymizer / spacy do not yet support
     Python 3.14 upstream, so `pip install privguard[full]` installs zero of those packages
     on 3.14. The lightweight detection path remains fully functional.
  2. Add a short installation note. Preferred location is a new `docs/install.md`
     section "Python version support" (planner's discretion to fold it into an existing
     doc instead if cleaner). The note must call out:
     - `pip install privguard` works on Python ≥ 3.10 (lightweight detection only).
     - `pip install privguard[full]` only installs presidio/spacy on Python < 3.14.
     - DET-06 parity test (`tests/test_detection_presidio_parity.py` or equivalent) is
       skipped on 3.14 by environment marker, not by silent failure.
  3. No behavior change. Existing `requires-python = ">=3.10"` stays.

### REQUIREMENTS.md PKG-02 Wording (audit item: REQUIREMENTS.md PKG-02)

- **D-04:** Rewrite PKG-02 directly to use the canonical name. New text:
  `**PKG-02**: Developer can run a `privguard` CLI entry point for diagnostics and local
  masking checks.` No historical note in the requirement itself; the rename trail lives in
  Phase 1 D-01 / 01-CONTEXT.md and (after D-01 here) in Phase 6's commit message and
  CONTEXT.md.

### Mechanical Items (Claude's Discretion — planner executes without further input)

These items have no design choice; they're sync operations between artifacts that already
have an authoritative source:

- **M-01:** REQUIREMENTS.md — tick `[x]` on CDX-01, CDX-02, CDX-03, TEST-01, TEST-02,
  TEST-03, TEST-04, TEST-05, TEST-06. Authoritative source: 04-VERIFICATION.md and
  05-VERIFICATION.md (both report SATISFIED).
- **M-02:** REQUIREMENTS.md traceability table — change CDX-01..03 and TEST-01..06 rows
  from `Pending` to `Complete`.
- **M-03:** ROADMAP.md — tick `[x]` on Phase 5 (line 19). Authoritative source: Phase 5
  VERIFICATION.md PASSED 2026-05-05 + 05-01-PLAN.md `[x]`.
- **M-04:** ROADMAP.md progress table — change Phase 5 row from `0/TBD ... Not started` to
  `1/1 ... Complete 2026-05-05`.
- **M-05:** ROADMAP.md Overview line 28 and Phase 1 success criterion #1 — replace
  `privacy-guard` with `privguard` (legacy name drift). Same edit anywhere else in
  ROADMAP.md if a rg pass finds further occurrences.
- **M-06:** `.planning/phases/04-codex-compatibility-evidence/04-01-SUMMARY.md` frontmatter —
  add `requirements_completed: [CDX-01, CDX-02]`. CDX-03 is in 04-02-SUMMARY.md already.
- **M-07:** `.planning/phases/05-synthetic-regression-gate/05-01-SUMMARY.md` frontmatter —
  add `requirements_completed: [TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06]`.

### Verification Bar

The phase verification gate is purely textual and structural — no new runtime tests required:

- `rg "privacy-guard" -n .planning/ pyproject.toml privguard/ docs/` returns either zero
  hits or only acceptable historical references (e.g. CHANGELOG-style notes if they exist).
- `pytest tests -q` still reports 134 passed (no test code changed; `__all__` change must
  not break existing imports — `tests/test_v1_regression_gate.py` and friends import via
  submodules so unaffected, but a smoke import line can be added).
- `python -c "from privguard import classify_command, CODEX_COMPATIBILITY"` succeeds
  (proves D-02 actually works).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Audit + roadmap (the source of truth for this phase's scope)
- `.planning/v1.0-MILESTONE-AUDIT.md` — 11 tech-debt items, organized by source file. The
  Recommendation section (lines 164-175) lists the suggested cleanup phase scope.
- `.planning/ROADMAP.md` §"Phase 6: Milestone Cleanup" — phase goal and 6 success criteria.
- `.planning/REQUIREMENTS.md` — current `[ ]` checkbox state (CDX/TEST rows) and PKG-02
  wording that needs to change.
- `.planning/PROJECT.md` — Core value, Phase 1 D-01 (canonical name `privguard`).
- `.planning/STATE.md` — current progress snapshot.

### Prior phase decisions (locked context)
- `.planning/phases/01-package-foundation/01-01-PLAN.md` / SUMMARY — Phase 1 D-01 canonical
  name decision.
- `.planning/phases/04-codex-compatibility-evidence/04-VERIFICATION.md` — CDX-01/02/03
  SATISFIED with evidence (drives M-01, M-02).
- `.planning/phases/05-synthetic-regression-gate/05-VERIFICATION.md` — TEST-01..06
  SATISFIED with evidence (drives M-01, M-02).
- `.planning/phases/04-codex-compatibility-evidence/04-01-SUMMARY.md` — frontmatter to
  backfill (M-06).
- `.planning/phases/05-synthetic-regression-gate/05-01-SUMMARY.md` — frontmatter to
  backfill (M-07).

### Code touched in this phase
- `pyproject.toml` — drop alias (D-01), add Python 3.14 gating comment (D-03).
- `privguard/__init__.py` — extend `__all__` (D-02).
- `docs/install.md` (new) or existing doc — add Python version support note (D-03).

### Code referenced but not modified
- `privguard/policy.py` — `classify_command`, `CommandClassification` (re-exported by D-02).
- `privguard/hooks.py` — `main_user_prompt`, `main_pre_tool` (re-exported by D-02).
- `privguard/diagnostics.py` — `build_claude_doctor_report` (re-exported by D-02).
- `privguard/codex.py` — `CODEX_COMPATIBILITY`, `CodexCompatibilityRow`, `CodexSupportLabel`,
  `get_codex_compatibility` (re-exported by D-02).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- All 5 modules referenced by `__all__` (D-02) already exist and have stable public symbols.
  No new public functions need to be authored — D-02 is a name-binding change only.
- `pyproject.toml` already has `[project]` and `[project.optional-dependencies]` sections;
  D-03 adds a comment block, not a new section.

### Established Patterns
- `privguard/__init__.py` already follows the pattern of importing concrete symbols from
  submodules and listing them alphabetically in `__all__`. D-02 just extends that list.
- The audit + Phase 5 SUMMARY pattern is to record `requirements_completed:` as a YAML list
  in the frontmatter (see 04-02-SUMMARY.md for an existing example). M-06/M-07 mirror that.
- Pre-existing tests do `from privguard.policy import ...` / `from privguard.hooks import ...`
  via submodule paths, so D-02's flat re-export does not collide with existing imports.

### Integration Points
- `pyproject.toml` change (D-01) does not affect the running editable install on this machine
  because the alias was never installed. Devs whose env predates v0.1.0 alpha installs are
  unaffected. Devs who happen to have the alias installed will lose the alias on next
  `pip install -e .` — acceptable per the alias's "uninstalled in active env" status.
- `docs/install.md` is a new file (no docs/install.md exists today); planner can either
  create it or fold the note into `docs/codex-compatibility.md` if a separate file feels
  premature for v1.

</code_context>

<specifics>
## Specific Ideas

- The 4 mechanical sweeps in REQUIREMENTS.md and ROADMAP.md are pure text edits. They
  should land in dedicated commits per artifact (one for REQUIREMENTS.md, one for
  ROADMAP.md, one for the SUMMARY frontmatter pair) so the audit trail is readable.
- The `__all__` change should not import any new module — only rebind names that already
  exist. After the change, `python -c "from privguard import <name>"` must succeed for
  every name in `__all__`.
- Planner has discretion on commit ordering (alias drop before or after PKG-02 wording
  edit; both end up consistent — pick whichever makes the diff easier to review).
- The Python 3.14 doc note (D-03) should not promise any future support timeline. State
  the current behavior, not a roadmap.

</specifics>

<deferred>
## Deferred Ideas

- **Drift-prevention regression test** — A test that asserts REQUIREMENTS.md checkboxes
  match the matching VERIFICATION.md verdicts so this audit drift cannot recur. Useful but
  out of scope for v1 close (this phase is a sweep, not infra). Candidate for v2 backlog.
- **Atomic single-commit close vs per-area commits** — Planner's discretion. Not gated by
  this phase.
- **`docs/install.md` vs folding into existing doc** — Planner's discretion (D-03 above).
- **README work and bilingual docs (DOC-01)** — Phase 7 scope; not Phase 6.
- **Repo cleanup mechanism (MAINT-01)** — Phase 7 scope; not Phase 6.
- **Re-installing presidio on a 3.10–3.13 venv to actually run DET-06 parity locally** — out
  of scope; this phase only documents the gating, doesn't change interpreter targets.
- **Renaming canonical command back to `privacy-guard`** — explicitly rejected (would
  reopen Phase 1 D-01 and invalidate Phase 1/3/5 verification).

</deferred>

---

*Phase: 06-milestone-cleanup*
*Context gathered: 2026-05-06*
