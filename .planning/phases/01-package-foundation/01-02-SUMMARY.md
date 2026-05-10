---
phase: 01-package-foundation
plan: 02
subsystem: package-core
tags: [python, detection, masking, policy, stdlib]

requires:
  - "01-01 package identity and CLI foundation"
provides:
  - "Importable lightweight detection module"
  - "Importable irreversible masking helper"
  - "Protected path policy and sanitized hit diagnostics"
affects: [package-foundation, privacy-core, claude-enforcement]

tech-stack:
  added: [dataclasses, re]
  patterns:
    - "Stdlib-only detection and validators extracted into privguard.detection"
    - "Masking separated into privguard.masking"
    - "Diagnostics omit Hit.value by construction"

key-files:
  created:
    - privguard/detection.py
    - privguard/masking.py
    - privguard/policy.py
  modified:
    - privguard/__init__.py

key-decisions:
  - "Kept Hit.value internal for masking, while policy summaries expose only kind, offsets, and score."
  - "Preserved the hook-era sensitive path regex categories without reading protected files."
  - "Kept all Plan 01-02 modules free of Presidio, spaCy, and demo imports."

metrics:
  duration: 2min
  completed: 2026-05-01
  tasks: 2
  files: 5

requirements-completed: [PKG-03]
---

# Phase 01 Plan 02: Core Module Extraction Summary

**Stdlib-only detection, masking, and policy helpers are now importable from `privguard`.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-01T20:07:31Z
- **Completed:** 2026-05-01T20:09:15Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `privguard/detection.py` with `Hit`, CPF/CNPJ/Luhn validators, lightweight regex patterns, and `detect()`.
- Added `privguard/masking.py` with irreversible typed placeholder redaction.
- Added `privguard/policy.py` with protected path classification plus raw-value-free hit summaries.
- Updated `privguard/__init__.py` to export `Hit`, `detect`, `redact`, and `__version__`.

## Task Commits

Each task commit was attempted atomically, but this session cannot create `.git/index.lock`.

1. **Task 1: Extract lightweight detection and masking modules** - commit failed before staging.
2. **Task 2: Add policy helpers with sanitized diagnostics** - commit failed before staging.

## Files Created/Modified

- `privguard/detection.py` - Lightweight stdlib detector, validators, pattern table, and overlap handling.
- `privguard/masking.py` - `redact()` helper using `<KIND>` markers.
- `privguard/policy.py` - Sensitive path regexes, command regex constants, `is_sensitive_path()`, `summarize_hits()`, and `format_hit_summary()`.
- `privguard/__init__.py` - Public low-level API exports.
- `.planning/phases/01-package-foundation/01-02-SUMMARY.md` - Execution summary.

## Verification

Passed:

```powershell
python -c "from privguard import detect, redact; hits=detect('CPF 529.982.247-25', min_score=0.7); assert len(hits)==1 and hits[0].kind=='BR_CPF'; assert redact('CPF 529.982.247-25', hits)=='CPF <BR_CPF>'; assert detect('CPF 111.111.111-11', min_score=0.7)==[]"
python -c "from privguard.detection import Hit; from privguard.policy import is_sensitive_path, summarize_hits, format_hit_summary; h=Hit('BR_CPF',4,18,'529.982.247-25',0.95); assert is_sensitive_path('.env'); assert is_sensitive_path('data_sensivel/cooperados.csv'); assert summarize_hits([h]) == [{'kind':'BR_CPF','start':4,'end':18,'score':0.95}]; assert '529.982.247-25' not in format_hit_summary([h])"
python -c "from privguard import detect, redact; hits=detect('CPF 529.982.247-25', min_score=0.7); assert redact('CPF 529.982.247-25', hits)=='CPF <BR_CPF>'"
python -c "from privguard.detection import Hit; from privguard.policy import summarize_hits; assert 'value' not in summarize_hits([Hit('X',0,1,'secret',1.0)])[0]"
python -m compileall privguard
```

Also passed:

- `rg -n "presidio|spacy|test_presidio|reversible_demo|ollama_local_demo" privguard` returned no matches.
- Stub scan over Plan 01-02 package files returned no matches.

## Decisions Made

- Used only synthetic strings and path literals for verification.
- Did not read `.env` or any file under `data_sensivel/`.
- Did not modify root demo files or `hooks/*.py`, preserving the Plan 01-02 ownership boundary.

## Deviations from Plan

### Auto-fixed Issues

None.

### Execution Deviations

**1. Git commit protocol could not complete**
- **Found during:** Task 1 and Task 2 commit attempts.
- **Issue:** `git add` failed with `fatal: Unable to create 'C:/Users/Erick/Documents/projetos/privguard/.git/index.lock': Permission denied`.
- **Fix:** No repository metadata fix was possible in this session. Implementation continued per execution rule.
- **Files modified:** None beyond planned files and this summary.
- **Verification:** Both commit attempts failed before staging, so no partial task commits were created.

**2. TDD gate commits could not be recorded**
- **Found during:** Task 1 and Task 2.
- **Issue:** RED checks failed as expected before implementation, but the known git index lock blocker prevented recording TDD RED/GREEN commits.
- **Fix:** Executed inline RED and GREEN checks, then documented the missing commits here.
- **Impact:** Behavior was verified, but git history does not contain the expected TDD gate commits.

## TDD Gate Compliance

Warning: RED and GREEN behavior gates were executed, but `test(...)` and `feat(...)` commits are missing because `.git/index.lock` is not writable in this session.

## Known Stubs

None.

## Threat Flags

None.

## Self-Check: PASSED WITH DOCUMENTED COMMIT BLOCKER

- `privguard/detection.py` exists.
- `privguard/masking.py` exists.
- `privguard/policy.py` exists.
- `privguard/__init__.py` exports `Hit`, `detect`, `redact`, and `__version__`.
- `.planning/phases/01-package-foundation/01-02-SUMMARY.md` exists.
- No task commits exist because both commit attempts failed before staging with `.git/index.lock` permission denied.

---
*Phase: 01-package-foundation*
*Completed: 2026-05-01*
