---
phase: 09-milestone-v1-0-audit-cleanup
plan: 02
subsystem: docs
tags: [readme, documentation, pii-guard-mode, bilingual]

# Dependency graph
requires:
  - phase: 08-hook-mode-selector
    provides: PII_GUARD_MODE selector (block default / warn opt-in non-protective / mask) shipped in hooks.py
provides:
  - README.md (PT) warn-vs-block FAQ documenting the three-mode PII_GUARD_MODE selector
  - README.en.md (EN) warn-vs-block FAQ with content parity
affects: [milestone-audit, documentation-drift]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Bilingual README parity: identical three-mode PII_GUARD_MODE table in PT and EN"

key-files:
  created: []
  modified:
    - README.md
    - README.en.md

key-decisions:
  - "FAQ documents shipped PII_GUARD_MODE selector instead of false warn-only out-of-scope claim; default behavior unchanged (still fail-closed block)"
  - "Honesty constraints enforced: no warn-by-default claim, no automatic-masking claim; mask documented as block + show-masked-for-copy-paste (exit 2)"

patterns-established:
  - "Doc-only audit-drift fix: rewrite FAQ to match verified hooks.py behavior, grep-enforced acceptance criteria for absence of overclaim wording"

requirements-completed: [DOC-01]

# Metrics
duration: 1min
completed: 2026-06-12
---

# Phase 09 Plan 02: Warn-vs-Block FAQ PII_GUARD_MODE Documentation Summary

**Both README files now document the shipped three-mode PII_GUARD_MODE selector (block default / warn opt-in non-protective / mask), replacing the false "warn-only is out of scope" claim that drifted from Phase 8.**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-06-12T01:23:22Z
- **Completed:** 2026-06-12T01:24:27Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Rewrote the "Por que ele bloqueia em vez de avisar?" FAQ in README.md (PT) to document the `PII_GUARD_MODE` selector with a three-mode table (block / warn / mask).
- Rewrote the "Why does it block instead of warn?" FAQ in README.en.md (EN) with content parity — identical three-mode semantics, exit codes, and protective flags.
- Removed the now-false "está explicitamente fora do escopo" / "out of scope" warn-only claim from both files.
- Preserved honesty constraints: block stated as default fail-closed; warn labeled opt-in non-protective (`local_development_non_protective`); mask described as still blocking (exit 2) + show-masked-for-copy-paste; no auto-mask or warn-by-default overclaim.

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite the warn-vs-block FAQ in README.md (PT) and README.en.md (EN) with parity** - `15ba92d` (docs)

**Plan metadata:** committed separately with STATE.md/ROADMAP.md updates.

## Files Created/Modified
- `README.md` - PT warn-vs-block FAQ rewritten to document PII_GUARD_MODE three-mode selector
- `README.en.md` - EN warn-vs-block FAQ rewritten with content parity

## Decisions Made
None beyond the plan — followed the plan's verbatim OLD→NEW replacement text exactly. The default block behavior was not changed (doc-only edit).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. Both FAQ blocks matched the plan's OLD text exactly; both edits applied cleanly. The commit message was written to a temp file and applied via `git commit -F` per the project's PII-blocking pre-tool hook guidance (no PII in the message, applied as a precaution).

## Verification

Acceptance criteria grep results:
- `PII_GUARD_MODE` README.md: 2, README.en.md: 2 (selector documented in both)
- `fora do escopo` README.md: 0; `out of scope` README.en.md: 0 (warn-only out-of-scope claim removed)
- `local_development_non_protective` README.md: 1, README.en.md: 1 (warn labeled non-protective)
- No "warns by default" / "avisa por padrão" overclaim in either file
- No `.claude/worktrees/**` README copies touched (only canonical README.md and README.en.md modified)

## Threat Surface

No new threat surface. Per the plan's threat model (T-09-03 mitigated, T-09-04 accepted): doc-only edit, no runtime code touched, default stays fail-closed block. The grep-enforced absence of overclaim wording mitigates the false-assurance/repudiation risk.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ROADMAP Phase 9 success criterion 3 (README documents PII_GUARD_MODE selector) is met.
- Remaining Phase 9 plans (if any) can proceed; no blockers introduced.

## Self-Check: PASSED

- FOUND: `.planning/phases/09-milestone-v1-0-audit-cleanup/09-02-SUMMARY.md`
- FOUND: commit `15ba92d`

---
*Phase: 09-milestone-v1-0-audit-cleanup*
*Completed: 2026-06-12*
