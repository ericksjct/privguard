---
phase: "03"
status: all_fixed
findings_in_scope: 3
fixed: 3
skipped: 0
iteration: 1
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-05-03T00:00:00Z
**Source review:** .planning/phases/03-claude-enforcement/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 3
- Fixed: 3
- Skipped: 0

## Fixed Issues

### WR-001 — status: fixed

**Files modified:** `privguard/policy.py`, `privguard/hooks.py`
**Commit:** 3d475ef
**Applied fix:** Added optional `min_score: float = 0.6` parameter to `classify_command` in `policy.py` and forwarded `detect(value, min_score=min_score)` inside the function. Updated both call sites in `hooks.py` — `check_bash` (line 142) and `main_pre_tool` (line 287) — to pass `min_score=_inline_threshold()`, ensuring `PII_GUARD_THRESHOLD` is respected on the command surface consistently with the prompt and LLM-orchestration surfaces.

### WR-002 — status: fixed

**Files modified:** `tests/test_policy_commands.py`
**Commit:** 3ea5631
**Applied fix:** Added module-level constant `_PROJECT_ROOT = pathlib.Path(__file__).parent.parent` and updated `test_command_classification_source_does_not_read_files` to resolve the policy source file as `(_PROJECT_ROOT / "privguard" / "policy.py").read_text(...)` instead of the bare relative `pathlib.Path("privguard/policy.py")`. The test now works correctly regardless of the working directory from which pytest is invoked.

### WR-003 — status: fixed

**Files modified:** `.claude/settings.json`
**Commit:** 9abf8ab
**Applied fix:** Changed both hook `command` values from `python "..."` to `python3 "..."` — the `UserPromptSubmit` hook (`pii_guard.py`) and the `PreToolUse` hook (`pre_tool_guard.py`). This prevents silent enforcement bypass on Linux and macOS systems where `python` is absent from PATH and only `python3` is available.

---

_Fixed: 2026-05-03T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
