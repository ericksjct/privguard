---
phase: 02-privacy-core
plan: 04
subsystem: cli-package-api
tags: [python, cli, exports, diagnostics, pytest]

requires:
  - phase: 02-privacy-core
    plan: 01
    provides: Detection core
  - phase: 02-privacy-core
    plan: 02
    provides: Masking and diagnostics core
  - phase: 02-privacy-core
    plan: 03
    provides: Policy core
provides:
  - CLI scan, mask, and policy-check commands
  - Human-readable and JSON sanitized CLI output
  - Stable Phase 2 package exports
affects: [02-privacy-core, claude-enforcement, codex-evidence, synthetic-regression]

tech-stack:
  added: []
  patterns:
    - argparse subcommands
    - JSON output via sanitized diagnostics
    - CLI exit codes aligned with policy allow/block

key-files:
  created: [tests/test_cli.py]
  modified: [privguard/cli.py, privguard/__init__.py, pyproject.toml]

key-decisions:
  - "Added privacy-guard as a console-script alias while preserving privguard."
  - "Kept scan diagnostics sanitized; mask prints masked payload only for the explicit mask command."
  - "Did not add Claude-specific enforcement or Codex support claims in Phase 2 CLI."

patterns-established:
  - "CLI reads text from an explicit argument or stdin for scan, mask, and policy-check."
  - "CLI JSON output is generated from diagnostics.to_json() to avoid raw value leaks."

requirements-completed: [DET-01, DET-02, DET-03, DET-04, DET-05, DET-06, MASK-01, MASK-02, MASK-03, MASK-04, POL-01, POL-02, POL-03, POL-04]

duration: 5min
completed: 2026-05-02
---

# Phase 02 Plan 04: CLI and Package API Summary

**Phase 2 core wired into CLI commands and public exports**

## Performance

- **Duration:** 5 min
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `privguard scan` with human-readable and `--json` sanitized diagnostics.
- Added `privguard mask` with explicit masked payload output and metadata-only `--json`.
- Added `privguard policy-check` with capability labels, optional path classification, optional verified masking, and allow/block exit codes.
- Added `privacy-guard = "privguard.cli:main"` alias while preserving `privguard`.
- Exported Phase 2 detection, masking, policy, and diagnostics APIs from `privguard.__init__`.
- Added synthetic-only CLI tests for output hygiene, JSON shape, stdin, masking, protected paths, and fail-closed policy behavior.

## Task Commits

Commit is pending manual execution because the Codex sandbox cannot write `.git/index.lock` in this workspace.

1. **Task 1: Add CLI scan and mask commands with sanitized output** - pending manual commit
2. **Task 2: Add CLI policy-check and package exports** - pending manual commit

## Files Created/Modified

- `privguard/cli.py` - `scan`, `mask`, and `policy-check` subcommands.
- `privguard/__init__.py` - Stable public exports for Phase 2 core APIs.
- `pyproject.toml` - `privacy-guard` console-script alias.
- `tests/test_cli.py` - CLI behavior and output hygiene tests.

## Decisions Made

- `policy-check` returns exit code `0` when allowed and `2` for block/pause outcomes.
- `mask --json` intentionally excludes masked payload text; normal `mask` output is the explicit masked payload.
- Unknown surfaces remain fail-closed by default in CLI policy checks.

## Deviations from Plan

### Auto-fixed Issues

None.

---

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope expansion.

## Issues Encountered

- Codex still cannot create `.git/index.lock`; commit must be created from the user's PowerShell.
- Pytest emitted a cache warning due local cache directory permissions; tests passed.

## Verification

- `python -m pytest tests/test_cli.py tests/test_policy.py tests/test_masking.py tests/test_detection.py -q` - PASS (`39 passed`)
- `python -m compileall privguard` - PASS
- `python -c "from privguard.cli import main; assert main(['info']) == 0"` - PASS
- `python -c "from privguard import detect, mask_text; assert callable(detect); assert callable(mask_text)"` - PASS
- `python -c "import tomllib, pathlib; data=tomllib.loads(pathlib.Path('pyproject.toml').read_text(encoding='utf-8')); scripts=data['project']['scripts']; assert scripts['privguard']=='privguard.cli:main'; assert scripts.get('privacy-guard')=='privguard.cli:main'"` - PASS

## Known Stubs

None.

## Threat Flags

None.

## User Setup Required

Run `commit-02-04.ps1` from a PowerShell session that can write to `.git`.

## Next Phase Readiness

Phase 2 implementation is ready for phase-level review and verification after the manual commit is created.

## Self-Check: PASSED

- **Files:** All planned source and test files exist.
- **Tests:** Planned verification commands passed.
- **Commits:** Pending manual commit due sandbox `.git` permissions.

---
*Phase: 02-privacy-core*
*Completed: 2026-05-02*
