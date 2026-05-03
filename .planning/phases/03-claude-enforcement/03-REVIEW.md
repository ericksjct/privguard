---
phase: "03"
reviewed: 2026-05-03T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - tests/test_claude_hooks.py
  - privguard/hooks.py
  - tests/test_policy_commands.py
  - privguard/policy.py
  - .claude/settings.json
  - tests/test_claude_doctor.py
  - tests/fixtures/claude_missing_hooks_settings.json
  - privguard/diagnostics.py
  - privguard/cli.py
  - tests/test_claude_phase_gate.py
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: findings
---

# Phase 03: Code Review Report

**Reviewed:** 2026-05-03T00:00:00Z
**Depth:** standard
**Files Reviewed:** 10
**Status:** issues_found

## Summary

Phase 03 implements Claude Code hook enforcement for PII detection and path/command policy. The core security posture is sound: fail-closed for unknown tools, sanitized diagnostics that never echo raw PII back to the model, and a layered detection pipeline (prompt surface -> path surface -> command surface). No critical vulnerabilities were found.

Three warnings were identified: the command-text PII threshold ignores the user-configurable `PII_GUARD_THRESHOLD` environment variable (inconsistent with the prompt and tool surfaces), a test uses a fragile relative path that breaks outside the project root, and bare `python` in `.claude/settings.json` creates a silent enforcement gap on Linux/macOS systems where only `python3` is in PATH.

Four info items cover a non-dict `tool_input` being silently coerced to empty dict (reducing fail-closed coverage for malformed payloads), a broad MCP IDE prefix allowance that skips path guards, a stream asymmetry between `warn` and `scrub` modes that lacks a locking test, and synthetic PII constants in a production module that will trigger secret-scanner false positives.

---

## Warnings

### WR-001: `classify_command` PII check ignores the configurable threshold

**File:** `privguard/policy.py:192`

**Issue:** `detect(value)` is called with the default `min_score=0.6` to detect inline PII in command strings. Every other PII check in the system resolves the threshold via `_inline_threshold()` in `hooks.py`, which reads `PII_GUARD_THRESHOLD` from the environment. The mismatch means a user who raises the threshold to `0.9` will still have commands blocked at `0.6`, and lowering it below `0.6` has no effect on command-text PII. The divergence is invisible to the test suite because `test_policy_commands.py` exercises `classify_command` directly without any env-var setup.

**Fix:**
```python
# policy.py — add optional threshold parameter
def classify_command(command: str, min_score: float = 0.6) -> CommandClassification:
    value = str(command or "")
    if not value.strip():
        return CommandClassification(False, "empty", "command_empty")
    if _command_has_protected_path(value):
        ...
    if detect(value, min_score=min_score):   # <-- forward threshold
        return CommandClassification(True, "inline_pii", "inline_pii")
    ...

# hooks.py — forward resolved threshold in PreToolUse handler
classification = classify_command(command, min_score=_inline_threshold())
```

---

### WR-002: Test uses hard-coded relative path that breaks outside project root

**File:** `tests/test_policy_commands.py:79`

**Issue:** `pathlib.Path("privguard/policy.py").read_text(encoding="utf-8")` resolves relative to the process working directory at runtime. If pytest is invoked from a subdirectory (e.g., `tests/`) or by a CI runner that sets `cwd` to a different location, the call raises `FileNotFoundError` and the test fails with a confusing traceback rather than a meaningful assertion failure.

**Fix:**
```python
import pathlib

_PROJECT_ROOT = pathlib.Path(__file__).parent.parent

def test_command_classification_source_does_not_read_files() -> None:
    source = (_PROJECT_ROOT / "privguard" / "policy.py").read_text(encoding="utf-8")
    assert ".read_text(" not in source
    assert ".open(" not in source
```

---

### WR-003: Bare `python` in hook commands silently disables enforcement on many systems

**File:** `.claude/settings.json:30` and `.claude/settings.json:41`

**Issue:** Both hook commands are spelled `python "..."`. On Linux and macOS, `python` is commonly absent (only `python3` is in PATH since PEP 394). When Claude Code spawns the hook and the binary cannot be found, the hook process fails to start — Claude Code receives an execution error and continues without enforcing any guard. For a security-critical tool this is a silent bypass, not a graceful degradation. The `claude doctor` check verifies wiring by parsing the settings JSON strings but does not attempt to execute the hook binary, so the gap goes undetected.

**Fix option 1 — use `python3` explicitly:**
```json
"command": "python3 \"$CLAUDE_PROJECT_DIR/hooks/pii_guard.py\""
```

**Fix option 2 — use the installed package entry-point (most portable):**
```json
"command": "privguard-hook-user-prompt"
```

**Fix option 3 — add a `claude doctor` probe:** Extend `_check_hook_wiring` to attempt a `shutil.which("python")` or dry-run invocation so the check fails visibly when the binary is missing.

---

## Info

### IN-001: Non-dict `tool_input` silently coerced to empty dict, reducing fail-closed coverage

**File:** `privguard/hooks.py:254-255`

**Issue:** If `tool_input` is a non-dict value (e.g., a JSON array or string — both valid in Claude's hook payloads), it is replaced with `{}`. All subsequent path and command checks operate on the empty dict, find nothing to block, and return `True`. The fail-closed posture applied elsewhere (unknown tool -> block) is not applied here. A malformed or adversarially crafted payload for a file-access tool would slip through.

**Fix:**
```python
if not isinstance(tool_input, dict):
    return _deny_pre_tool(reason_code="malformed_tool_input", category="unknown_tool")
```

---

### IN-002: `mcp__ide__` prefix allowance bypasses path guards for IDE file tools

**File:** `privguard/hooks.py:218-221`

**Issue:** Any tool whose name starts with `mcp__ide__` is treated as a trusted local tool with no further argument inspection. IDE MCP plugins commonly expose `readFile`, `writeFile`, or `listDirectory` variants. An IDE plugin naming its file-read tool `mcp__ide__readFile` could access `data_sensivel/` paths unchecked because `_is_allowed_tool` returns `True` and `main_pre_tool` falls through to `return 0` without calling `check_path_tool`.

**Fix:** After the `_is_allowed_tool` gate, apply `check_path_tool` (or equivalent path inspection) to any `mcp__ide__` tool that carries a `file_path`, `path`, or `notebook_path` argument:
```python
if tool.startswith("mcp__ide__"):
    ok, reason_code = check_path_tool(tool_input)
    if not ok:
        return _deny_pre_tool(reason_code=reason_code, category="protected_path", path_count=1)
    return 0
```

---

### IN-003: `warn` vs `scrub` mode output stream asymmetry lacks a locking test

**File:** `privguard/hooks.py:166` and `privguard/hooks.py:172-183`

**Issue:** In `warn` mode the JSON diagnostic is written to stdout (`print(...)`). In `scrub` mode the block diagnostic is written to stderr (`sys.stderr.write(...)`). This is intentional (documented in the comment at lines 170-173), but the stream contract is not tested. The existing parametrized test at `test_claude_hooks.py:302-319` asserts the exit codes and content but does not assert which stream carries each value. A future refactor could swap streams and no test would catch it.

**Suggestion:** Add stream assertions to the parametrized non-blocking mode test:
```python
if mode == "warn":
    assert captured.out != ""   # JSON goes to stdout for warn
    assert "local_development_non_protective" in captured.out
elif mode == "scrub":
    assert captured.err != ""   # block message goes to stderr for scrub
    assert "local_development_non_protective" in captured.err
```

---

### IN-004: Synthetic PII constants in production module will trigger secret scanners

**File:** `privguard/diagnostics.py:14-19`

**Issue:** `SYNTHETIC_DOCTOR_PROMPT` embeds a checksum-valid CPF (`123.456.789-09`) and an API-key-shaped string (`sk-test-abcdefghijklmnopqrstuvwxyz`). These are intentionally synthetic and safe, but static analysis tools (`detect-secrets`, `truffleHog`, `gitleaks`) and future code reviewers may flag them as real credentials, causing CI false-positive alerts or PR rejections.

**Suggestion:** Add a suppression comment and clarify intent:
```python
# Synthetic values used exclusively for self-test in `claude doctor`.
# The CPF passes the checksum algorithm; the token matches the API_KEY pattern.
# Neither value is real. Secret-scanner suppressions are intentional.
SYNTHETIC_DOCTOR_PROMPT = (
    "Validacao sintetica CPF 123.456.789-09 "          # noqa: S105
    "token=sk-test-abcdefghijklmnopqrstuvwxyz"          # noqa: S105
)
```

---

_Reviewed: 2026-05-03T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
