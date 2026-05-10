---
phase: 01-package-foundation
plan: 01
subsystem: packaging
tags: [python, setuptools, cli, argparse]

requires: []
provides:
  - "Setuptools package metadata for editable local installation"
  - "Importable privguard package identity with version metadata"
  - "Sanitized privguard info CLI implemented with stdlib only"
affects: [package-foundation, privacy-core, claude-enforcement]

tech-stack:
  added: [setuptools, argparse, importlib.metadata]
  patterns:
    - "PEP 621 pyproject.toml metadata with empty default dependencies"
    - "Console script entry point mapped to privguard.cli:main"
    - "Sanitized CLI diagnostics with no optional detector imports"

key-files:
  created:
    - pyproject.toml
    - privguard/__init__.py
    - privguard/cli.py
  modified: []

key-decisions:
  - "Used only the locked privguard console script name; no privacy-guard alias was added."
  - "Kept default dependencies empty and placed Presidio/spaCy only under the optional full extra."
  - "Made privguard info stdlib-only so it does not import optional full detector dependencies."

patterns-established:
  - "Package identity lives in privguard/__init__.py with __version__ exported."
  - "CLI commands dispatch through argparse subcommands and return integer exit codes."

requirements-completed: [PKG-01, PKG-02, PKG-03]

duration: 2min
completed: 2026-05-01
---

# Phase 01 Plan 01: Package Foundation Summary

**Setuptools editable-install metadata with a stdlib-only `privguard info` diagnostics command**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-01T23:02:42Z
- **Completed:** 2026-05-01T23:04:38Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `pyproject.toml` with setuptools build metadata, package name `privguard`, empty default dependencies, optional `full` extras, and the `privguard` console script.
- Added `privguard/__init__.py` with package version identity.
- Added `privguard/cli.py` with an `info` subcommand that prints only package version, lightweight detector tier, and optional-extra availability.

## Task Commits

Each task commit was attempted atomically, but this tool session cannot create `.git/index.lock`.

1. **Task 1: Add setuptools package metadata** - commit failed before staging.
2. **Task 2: Add package identity and `privguard info`** - commit failed before staging.

## Files Created/Modified

- `pyproject.toml` - Setuptools build backend, project metadata, optional `full` extras, and console script mapping.
- `privguard/__init__.py` - Importable package version identity.
- `privguard/cli.py` - Sanitized `privguard info` CLI command.
- `.planning/phases/01-package-foundation/01-01-SUMMARY.md` - Execution summary.

## Decisions Made

- Followed D-01 and exposed only `privguard`, with no `privacy-guard` compatibility alias.
- Kept `dependencies = []` so default installation does not pull Presidio, spaCy, or Portuguese NLP models.
- Used `argparse` and `importlib.metadata` from the Python standard library for the CLI foundation.

## Deviations from Plan

### Auto-fixed Issues

None.

### Execution Deviations

**1. Git commit protocol could not complete**
- **Found during:** Task 1, Task 2, and final metadata commit steps.
- **Issue:** `git add` failed with `fatal: Unable to create 'C:/Users/Erick/Documents/projetos/privguard/.git/index.lock': Permission denied`.
- **Fix:** No repository metadata fix was possible in this session. Implementation continued per execution rule.
- **Files modified:** None beyond planned files.
- **Verification:** All three commit attempts failed before staging, so no partial commit was created.

**2. Editable install could not complete in this permission-constrained session**
- **Found during:** Task 2 verification.
- **Issue:** `python -m pip install -e .` failed with `[Errno 13] Permission denied` while creating pip build-tracker files. Retrying with workspace-local `TMP`/`TEMP` produced the same permission error under `.tmp-pip`.
- **Fix:** Verified package import and CLI dispatch directly with `python -m privguard.cli info` and `privguard.cli.main(['info'])`.
- **Files modified:** `.tmp-pip/` was created by the pip retry. Cleanup was attempted, but the local command policy blocked the `Remove-Item` cleanup command before execution.
- **Verification:** Direct CLI module execution and import-level CLI dispatch passed.

**Total deviations:** 0 auto-fixed; 2 execution-environment deviations.
**Impact on plan:** Source implementation is complete. Editable-install and git-commit gates remain blocked by local filesystem permissions, not by package code.

## Issues Encountered

- The generated `privguard` console command could not be verified because editable installation failed before wrapper generation.
- The direct fallback command `python -m privguard.cli info` printed:
  - `privguard 0.1.0`
  - `detectors: lightweight`
  - `optional_full: available via privguard[full]`

## User Setup Required

None for code behavior. A later session with writable `.git/index.lock` and pip build-tracker permissions should rerun `python -m pip install -e .`, `privguard info`, and the GSD commit protocol.

## Known Stubs

None.

## Threat Flags

None.

## Next Phase Readiness

Plan 01-02 can build on the `privguard` package boundary and add importable detection, masking, and policy modules without importing optional Presidio/spaCy dependencies by default.

## Self-Check: PASSED WITH DOCUMENTED COMMIT BLOCKER

- `pyproject.toml` exists.
- `privguard/__init__.py` exists.
- `privguard/cli.py` exists.
- `.planning/phases/01-package-foundation/01-01-SUMMARY.md` exists.
- No task commits exist because both commit attempts failed before staging with `.git/index.lock` permission denied.

---
*Phase: 01-package-foundation*
*Completed: 2026-05-01*
