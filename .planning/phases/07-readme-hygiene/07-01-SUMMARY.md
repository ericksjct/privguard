---
phase: 07-readme-hygiene
plan: "01"
subsystem: cli
tags: [cleanup, cli, packaging, maintenance, pyproject, gitignore, testing, tomli]

requires:
  - phase: 06-milestone-cleanup
    provides: "canonical privguard package metadata, pyproject.toml base, confirmed hook entrypoints"

provides:
  - "privguard/cleanup.py: stdlib-only config-driven cleanup module with hardcoded _PROTECTED list (D-09), repo-root guard (D-11), dry-run default (D-12), symlink refusal (D-13), sanitized [CLEANUP] stderr, tomllib/tomli shim"
  - "privguard/cli.py: cleanup subparser wired to cmd_cleanup, dispatching to cleanup_main"
  - "pyproject.toml: [tool.privguard.cleanup] patterns table (D-08), tomli conditional dep (D-16), two console scripts privguard-user-prompt / privguard-pre-tool (D-15)"
  - ".gitignore: dist/, build/, *.egg-info/ added — parity with D-08 cleanup patterns"
  - "tests/test_cleanup.py: six contract tests covering all four safety contracts"
  - "conftest.py: worktree meta-path fix ensuring local privguard takes precedence over editable install"

affects:
  - "07-02 (README.en plan — will document cleanup, console scripts, install)"
  - "07-03 (README.pt-BR — bilingual mirror of 07-02)"

tech-stack:
  added:
    - "tomli (conditional dep for Python < 3.11 — falls back to stdlib tomllib on 3.11+)"
  patterns:
    - "config-driven cleanup: [tool.privguard.cleanup].patterns in pyproject.toml with hardcoded _PROTECTED override"
    - "fail-closed guard sequence: _verify_repo_root → _load_patterns → _collect_candidates (each exits 2 on misuse)"
    - "sanitized [CLEANUP] stderr format: paths and reason codes only, never file contents (extends POL-04)"
    - "TOCTOU re-check before shutil.rmtree: pre-validate + re-check inside apply loop"
    - "worktree conftest.py: removes editable-install MetaPathFinder so pytest uses local package copy"

key-files:
  created:
    - privguard/cleanup.py
    - tests/test_cleanup.py
    - conftest.py
  modified:
    - privguard/cli.py
    - pyproject.toml
    - .gitignore

key-decisions:
  - "Changed test_cleanup_apply_skips_protected_paths_with_warning pattern from '.env.*' to '.env': fnmatch cannot match '.env' against '.env.*' (requires a dot+suffix), so the protection check never fired with the original pattern."
  - "Added conftest.py to remove the setuptools editable-install MetaPathFinder during pytest: the system-wide __editable__.privguard-0.1.0.pth redirects 'import privguard' to the main repo, making worktree changes invisible to pytest without the fix."

patterns-established:
  - "Cleanup dry-run is the default; --apply is the explicit opt-in (D-12 contract)."
  - "_PROTECTED constant in cleanup.py is hardcoded and cannot be overridden by pyproject.toml (D-09 contract)."

requirements-completed: [MAINT-01]

duration: 12min
completed: "2026-05-10"
---

# Phase 7 Plan 01: Cleanup CLI + Console Scripts + gitignore Summary

**Config-driven `privguard cleanup` subcommand with hardcoded protected list, repo-root guard, dry-run default, symlink refusal, and .gitignore parity; plus D-15 console scripts and D-16 tomli conditional dep**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-10T19:07:30Z
- **Completed:** 2026-05-10T19:19:40Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Created `privguard/cleanup.py` with all four safety contracts from MAINT-01: repo-root guard (D-11), dry-run default (D-12), symlink refusal with TOCTOU re-check (D-13), hardcoded `_PROTECTED` override (D-09), sanitized `[CLEANUP]` stderr (POL-04 extension), tomllib/tomli conditional shim (D-16)
- Wired `privguard cleanup [--apply]` into the CLI dispatcher (`privguard/cli.py`), added `[tool.privguard.cleanup]` patterns table to `pyproject.toml`, added the two console scripts `privguard-user-prompt` / `privguard-pre-tool` (D-15), and added `tomli; python_version < '3.11'` conditional dep (D-16)
- Appended `dist/`, `build/`, `*.egg-info/` to `.gitignore`, achieving full parity with the eight D-08 cleanup patterns (success criterion #5)
- Created six contract tests in `tests/test_cleanup.py`; full suite (139 passed, 1 skipped on Windows due to symlink admin requirement) passes with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement privguard/cleanup.py with all four safety contracts** - `984570d` (feat)
2. **Task 2: Wire cleanup into CLI + pyproject + .gitignore + write tests** - `624a192` (feat)

## Files Created/Modified

- `privguard/cleanup.py` - Stdlib-only cleanup module: `_PROTECTED` constant, repo-root guard, pattern matcher, symlink-refusing deleter, dry-run formatter, `main()` returning 0/1/2
- `privguard/cli.py` - Added `cleanup_main` import, `cmd_cleanup` wrapper, `cleanup` subparser with `--apply` flag
- `pyproject.toml` - Added `tomli` dep, two console scripts, `[tool.privguard.cleanup]` patterns table
- `.gitignore` - Added `dist/`, `build/`, `*.egg-info/` (three missing D-08 patterns)
- `tests/test_cleanup.py` - Six contract tests: dry-run default, apply deletion, repo-root guard, protected-list refusal, symlink refusal (skipped on Windows), output sanitization
- `conftest.py` - Worktree pytest import fix: removes editable-install MetaPathFinder so local package takes precedence

## Decisions Made

- Changed `test_cleanup_apply_skips_protected_paths_with_warning` pattern from `'.env.*'` to `'.env'`: fnmatch cannot match `'.env'` against `'.env.*'` (requires at least one character after the dot-star), so the protection check would never fire with the original pattern from the plan spec.
- Added `conftest.py` (not in the plan) to fix pytest import resolution in the worktree: the system-wide `__editable__.privguard-0.1.0.pth` installs a MetaPathFinder redirecting `import privguard` to the main repo, which does not yet have `cleanup.py`. Without the fix, all cleanup tests would fail silently using the pre-cleanup CLI.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed unfireable protected-path test assertion**
- **Found during:** Task 2 (test_cleanup_apply_skips_protected_paths_with_warning)
- **Issue:** Plan spec used cleanup pattern `'.env.*'` to test that `.env` is protected. `fnmatch.fnmatch('.env', '.env.*')` returns False (the glob requires at least one character after the dot), so the file was never added to matches or skips — protection check could never fire.
- **Fix:** Changed seed pattern to `'.env'` (exact match), which correctly triggers the match → protected-skip path.
- **Files modified:** `tests/test_cleanup.py`
- **Verification:** `test_cleanup_apply_skips_protected_paths_with_warning` passes; `.env` survives `--apply` with `reason=protected` in stderr.
- **Committed in:** `624a192` (Task 2 commit)

**2. [Rule 3 - Blocking] Added conftest.py to fix pytest editable-install import shadowing**
- **Found during:** Task 2 test execution
- **Issue:** The system-wide `__editable__.privguard-0.1.0.pth` installs a setuptools MetaPathFinder that redirects `import privguard` to the original installed repo (`C:\Users\Erick\Documents\projetos\privguard`), not the worktree. Setting `PYTHONPATH` is insufficient because MetaPathFinders outrank sys.path entries. Tests imported the old CLI without the cleanup subparser, causing "invalid choice: cleanup" errors.
- **Fix:** Added `conftest.py` at worktree root that removes the redirecting MetaPathFinder and inserts the worktree root at the front of `sys.path`, then invalidates already-cached privguard modules.
- **Files modified:** `conftest.py` (new)
- **Verification:** `python -m pytest tests/test_cleanup.py -v` → 5 passed, 1 skipped (Windows symlink); full suite → 139 passed, 1 skipped.
- **Committed in:** `624a192` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug in test spec, 1 blocking environment issue)
**Impact on plan:** Both fixes were necessary for correctness and test executability. No scope creep — conftest.py is a worktree-local pytest config artifact.

## Issues Encountered

- RTK (Rust Token Killer) proxy intercepts and filters pytest stdout, making test result diagnosis from the Bash tool difficult. Workaround: used `rtk proxy "python -m pytest ..."` to bypass filtering for diagnostic output.
- Windows symlink creation requires admin or DevMode; symlink test correctly auto-skips on Windows (as the plan anticipated).
- editable install MetaPathFinder blocked pytest from seeing worktree changes — resolved with `conftest.py` (Deviation #2 above).

## Threat Surface Scan

No new network endpoints, auth paths, or trust-boundary schema changes introduced. The `privguard cleanup` surface is filesystem-local and hardcoded-protected. Threats T-07-01 through T-07-09 from the plan's threat model are all mitigated or accepted as documented — no unmodeled surface found.

## Next Phase Readiness

- `privguard cleanup`, `privguard-user-prompt`, and `privguard-pre-tool` console scripts are declared in `pyproject.toml` and ready to document in the bilingual READMEs (07-02/07-03)
- All eight D-08 patterns appear in both `[tool.privguard.cleanup]` and `.gitignore`
- MAINT-01 requirement is closed

---

*Phase: 07-readme-hygiene*
*Completed: 2026-05-10*

## Self-Check: PASSED

Files verified:
- `privguard/cleanup.py` — EXISTS (257 lines)
- `privguard/cli.py` — MODIFIED (cleanup wiring confirmed)
- `pyproject.toml` — MODIFIED (all three additions confirmed)
- `.gitignore` — MODIFIED (three entries added)
- `tests/test_cleanup.py` — EXISTS (6 tests)
- `conftest.py` — EXISTS

Commits verified:
- `984570d` — EXISTS (feat: implement cleanup.py)
- `624a192` — EXISTS (feat: wire cleanup into CLI et al.)

Test suite: 139 passed, 1 skipped, 0 failed.
