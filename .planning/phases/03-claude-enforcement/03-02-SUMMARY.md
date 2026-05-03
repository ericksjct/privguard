---
phase: 03-claude-enforcement
plan: 02
subsystem: hooks
tags: [claude, privacy, pre-tool, commands, pytest]
requires:
  - phase: 03-claude-enforcement
    plan: 01
    provides: metadata-only prompt hook diagnostics
provides:
  - Claude PreToolUse blocks protected path reads, searches, edits, writes, notebooks, and shell commands
  - Protected command category classification for read, copy, archive, encoding, clipboard, network, and inline PII commands
  - Metadata-only PreToolUse denial output with no protected path or command snippets
affects: [claude-enforcement, protected-path-policy, synthetic-regression-gate]
tech-stack:
  added: []
  patterns:
    - string-only command classification
    - fail-closed PreToolUse dispatch
    - metadata-only hook denials
key-files:
  created:
    - tests/test_policy_commands.py
  modified:
    - privguard/policy.py
    - privguard/hooks.py
    - .claude/settings.json
    - tests/test_claude_hooks.py
key-decisions:
  - "PreToolUse matcher now uses `*` so current and future Claude tool events are routed through the local guard."
  - "Command classification lives in `privguard.policy` and remains string-only; it does not read protected files."
  - "Unknown PreToolUse tools fail closed with sanitized metadata."
requirements-completed: [CLD-02, CLD-03, CLD-04]
duration: 3min
completed: 2026-05-03
---

# Phase 03 Plan 02: Expand PreToolUse Protected-Path and Command Blocking Summary

**Claude PreToolUse now blocks protected paths and exfiltration-style commands before execution, with sanitized diagnostics only.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-05-03T16:59:18Z
- **Completed:** 2026-05-03T17:02:12Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Added `CommandClassification` and `classify_command()` to classify protected-path command patterns without file reads.
- Covered read, copy, archive, encoding/decoding, clipboard, network, and inline PII command categories with synthetic tests.
- Expanded `main_pre_tool()` for `MultiEdit`, `NotebookRead`, `NotebookEdit`, shell-capable tools, and conservative unknown-tool blocking.
- Replaced raw tool denials with metadata-only diagnostics containing action, event, category, counts, reason code, and remediation.
- Broadened `.claude/settings.json` PreToolUse matcher to `"*"` while preserving the `hooks/pre_tool_guard.py` adapter path.

## Task Commits

Task commits could not be created because Git cannot create `.git/index.lock` in this environment:

1. **Task 1: Add command category and PreToolUse tests** - not committed
2. **Task 2: Implement protected command classification and PreToolUse dispatch** - not committed
3. **Task 3: Broaden Claude PreToolUse matcher safely** - not committed

Expected commit messages once Git index writes are available:

- `test(03-02): add PreToolUse command blocking tests`
- `feat(03-02): enforce protected command blocking`
- `chore(03-02): broaden Claude PreToolUse matcher`
- `docs(03-02): complete PreToolUse enforcement plan`

## Files Created/Modified

- `tests/test_policy_commands.py` - Synthetic command category regression tests for pure `classify_command()` behavior.
- `tests/test_claude_hooks.py` - Synthetic PreToolUse payload tests for path tools, shell commands, unknown tools, and sanitized output.
- `privguard/policy.py` - String-only command classification contract and command category regexes.
- `privguard/hooks.py` - PreToolUse orchestration through policy helpers and sanitized denial metadata.
- `.claude/settings.json` - PreToolUse matcher broadened to `"*"`.

## Decisions Made

- Prefer match-all PreToolUse coverage because strict privacy should not rely on a stale explicit Claude tool list.
- Keep hook adapter paths stable and route behavior through package modules.
- Fail closed for unknown tools instead of allowing unclassified tool surfaces.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test Bug] Fixed capture handling in new unknown-tool test**
- **Found during:** Task 2
- **Issue:** The new test read `capsys` twice, which could drop part of the captured denial output.
- **Fix:** Capture stdout/stderr once and concatenate the captured values.
- **Files modified:** `tests/test_claude_hooks.py`
- **Verification:** `python -m pytest tests/test_policy_commands.py tests/test_claude_hooks.py tests/test_policy.py -q` passed.
- **Commit:** not committed; Git index writes are denied.

**Total deviations:** 1 auto-fixed. **Impact:** Test reliability only; no production behavior impact.

## Issues Encountered

- Git commit operations are blocked by `fatal: Unable to create 'C:/Users/Erick/Documents/projetos/privguard/.git/index.lock': Permission denied`.
- `python -m pytest` reports a non-blocking pytest cache warning because `.pytest_cache` cannot create one cache file; tests still pass.

## Verification

- `python -m pytest tests/test_policy_commands.py tests/test_claude_hooks.py tests/test_policy.py -q` - PASSED, 35 passed.
- `python -m pytest tests/test_claude_hooks.py -q` - PASSED, 20 passed.
- `Select-String -Path privguard/policy.py -Pattern "classify_command|\\.read_text\\(|\\.open\\("` - PASSED, `classify_command` present and no file-read patterns found.
- `Select-String -Path .claude/settings.json -Pattern '"matcher": "\\*"|pre_tool_guard.py'` - PASSED.

## Known Stubs

None.

## Threat Flags

None.

## User Setup Required

None.

## Next Phase Readiness

Implementation and verification are complete for CLD-02, CLD-03, and CLD-04, but the GSD commit and state-update gates are blocked until Git can create `.git/index.lock`.

## Self-Check: FAILED

- **Files exist:** PASSED
  - `tests/test_policy_commands.py`
  - `tests/test_claude_hooks.py`
  - `privguard/policy.py`
  - `privguard/hooks.py`
  - `.claude/settings.json`
  - `.planning/phases/03-claude-enforcement/03-02-SUMMARY.md`
- **Verification commands:** PASSED
  - `python -m pytest tests/test_policy_commands.py tests/test_claude_hooks.py tests/test_policy.py -q`
  - `python -m pytest tests/test_claude_hooks.py -q`
- **Commits exist:** FAILED
  - Task 1 commit missing because Git index writes are denied.
  - Task 2 commit missing because Git index writes are denied.
  - Task 3 commit missing because Git index writes are denied.
  - Metadata commit missing because Git index writes are denied.

---
*Phase: 03-claude-enforcement*
*Completed: 2026-05-03*
