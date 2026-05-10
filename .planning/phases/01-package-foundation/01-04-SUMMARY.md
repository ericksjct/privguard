---
phase: 01-package-foundation
plan: 04
subsystem: demos
tags: [python, presidio, ollama, privacy, demos]

requires:
  - phase: 01-package-foundation
    provides: "Package foundation context and demo separation decision D-08"
provides:
  - "Root Presidio and Ollama demos moved under demos/"
  - "Default demo stdout no longer prints raw original samples or detected snippets"
  - "Known root-era sensitive-looking literals removed from moved demo sources"
affects: [package-foundation, privacy-core, synthetic-regression]

tech-stack:
  added: []
  patterns:
    - "Demo scripts remain direct Python entry points under demos/"
    - "Default demo display uses sample metadata, entity kinds, spans, scores, and output lengths"

key-files:
  created:
    - demos/test_presidio.py
    - demos/test_presidio_br.py
    - demos/reversible_demo.py
    - demos/ollama_local_demo.py
  modified:
    - test_presidio.py
    - test_presidio_br.py
    - reversible_demo.py
    - ollama_local_demo.py

key-decisions:
  - "Kept demos runnable but changed default stdout to metadata instead of raw sample text."
  - "Used the GSD-standard summary path 01-04-SUMMARY.md per execution instructions."

patterns-established:
  - "Separated demos live under demos/ and are not root production-surface scripts."
  - "Demo detection output reports entity type, score, and span instead of matched value."

requirements-completed: [PKG-04]

duration: 3min
completed: 2026-05-01
---

# Phase 01 Plan 04: Demo Separation Summary

**Presidio and Ollama demos moved under `demos/` with default raw-value printing removed**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-01T23:07:40Z
- **Completed:** 2026-05-01T23:10:46Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Moved the four root-level demo scripts into `demos/`.
- Removed default `Original : {text}` and raw snippet printing from Presidio demo output.
- Removed the known root-era CPF/CNPJ literals from moved demo source and changed the Ollama prompt to use masked synthetic placeholders.
- Preserved direct script entry guards for all moved demos.

## Task Commits

Task commits were attempted, but this session cannot create `.git/index.lock`.

1. **Task 1: Move root demos into `demos/`** - commit blocked before staging.
2. **Task 2: Remove raw-value default demo printing** - commit blocked before staging.

## Files Created/Modified

- `demos/test_presidio.py` - Moved generic Presidio demo; default output now hides original text and detected snippets.
- `demos/test_presidio_br.py` - Moved Brazilian Presidio demo; default output now hides original text and detected snippets.
- `demos/reversible_demo.py` - Moved reversible anonymization demo; default output hides source, encrypted token text, and restored text.
- `demos/ollama_local_demo.py` - Moved local Ollama demo; default prompt uses masked synthetic placeholders.
- `test_presidio.py` - Removed from root by move.
- `test_presidio_br.py` - Removed from root by move.
- `reversible_demo.py` - Removed from root by move.
- `ollama_local_demo.py` - Removed from root by move.

## Decisions Made

- Followed D-08 by separating demos from the root package surface rather than turning them into package modules.
- Kept demo behavior minimal and safe; preserving full illustrative raw-output behavior is intentionally not part of PKG-04.

## Deviations from Plan

### Auto-fixed Issues

None.

### Execution Deviations

**1. Git commit protocol could not complete**
- **Found during:** Task 1, Task 2, and final metadata commit steps.
- **Issue:** `git add` failed with `fatal: Unable to create 'C:/Users/Erick/Documents/projetos/privguard/.git/index.lock': Permission denied`.
- **Fix:** No repository metadata fix was possible in this session. Implementation continued per execution rule.
- **Files modified:** None beyond planned files and this summary.
- **Verification:** Both commit attempts failed before staging, so no partial commit was created.

**Total deviations:** 0 auto-fixed; 1 execution-environment deviation.
**Impact on plan:** Source implementation and verification are complete. Atomic task commits remain blocked by local git index permissions.

## Issues Encountered

- Git staging/commit is blocked by `.git/index.lock` permission denial in this session.
- Existing `.tmp-pip/` permission warnings still appear in broad git status from previous work; this plan did not read or modify that directory.

## User Setup Required

None.

## Known Stubs

None. Stub-pattern scan only matched local list initialization and optional default arguments in demo implementation code.

## Threat Flags

None. `demos/ollama_local_demo.py` still contains the pre-existing localhost-only Ollama call pattern; this plan changed its default prompt to masked synthetic placeholders and did not add a new external network surface.

## Verification

- `python -m py_compile demos\test_presidio.py demos\test_presidio_br.py demos\reversible_demo.py demos\ollama_local_demo.py` passed.
- Root demo absence and moved demo presence assertions passed.
- `rg -n 'Original : \{text\}|529\.982\.247-25|11\.222\.333/0001-81|sk-ant-fake|AKIAIOSFODNN7EXAMPLE' demos` returned no matches.
- `rg -n 'if __name__ == "__main__"' demos\test_presidio.py demos\test_presidio_br.py demos\reversible_demo.py demos\ollama_local_demo.py` found all four entry guards.
- GSD metadata updates were applied to `STATE.md`, `ROADMAP.md`, and `REQUIREMENTS.md`; final metadata commit was blocked by `.git/index.lock`.

## Next Phase Readiness

PKG-04 is ready for downstream validation: demos are outside the production root surface and default demo output avoids the known raw sensitive-looking sample values.

## Self-Check: PASSED WITH DOCUMENTED COMMIT BLOCKER

- `demos/test_presidio.py` exists.
- `demos/test_presidio_br.py` exists.
- `demos/reversible_demo.py` exists.
- `demos/ollama_local_demo.py` exists.
- Root `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, and `ollama_local_demo.py` are absent.
- `.planning/phases/01-package-foundation/01-04-SUMMARY.md` exists.
- No task or metadata commits exist because commit attempts failed before staging with `.git/index.lock` permission denied.

---
*Phase: 01-package-foundation*
*Completed: 2026-05-01*
