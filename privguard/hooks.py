"""Claude hook handlers backed by package detection and policy helpers."""

from __future__ import annotations

import json
import math
import os
import sys

from .detection import detect
from .diagnostics import format_hit_summary, summarize_hits, to_json
from .policy import classify_command, classify_path


def deny(prefix: str, reason_code: str) -> int:
    sys.stderr.write(f"[{prefix} BLOQUEADO] reason={reason_code}\n")
    return 2


def _deny_pre_tool(
    *,
    reason_code: str,
    category: str,
    path_count: int = 0,
    command_count: int = 0,
) -> int:
    details = [
        f"reason={reason_code}",
        "action=block",
        "event=PreToolUse",
        f"category={category}",
    ]
    if path_count:
        details.append(f"path_count={path_count}")
    if command_count:
        details.append(f"command_count={command_count}")
    details.append("remediation=remove_protected_path_or_use_synthetic_fixture")
    sys.stderr.write("[PRE-TOOL-GUARD BLOQUEADO] " + " ".join(details) + "\n")
    return 2


def _iter_path_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            if any(name in str(key).lower() for name in ("path", "pattern")):
                paths.extend(_iter_path_values(item))
        return paths
    if isinstance(value, list):
        paths = []
        for item in value:
            paths.extend(_iter_path_values(item))
        return paths
    return []


def check_path_tool(tool_input: dict) -> tuple[bool, str]:
    for key in ("file_path", "path", "notebook_path"):
        for value in _iter_path_values(tool_input.get(key)):
            classification = classify_path(value)
            if classification.is_protected:
                return False, classification.reason_code
    return True, ""


def check_glob_grep(tool_input: dict) -> tuple[bool, str]:
    pattern = tool_input.get("pattern", "")
    path = tool_input.get("path", "")
    for value in (pattern, path):
        if value:
            classification = classify_path(str(value))
            if classification.is_protected:
                return False, classification.reason_code
    return True, ""


def _inline_threshold() -> float:
    """Return the PII detection threshold, shared by prompt and tool surfaces."""
    try:
        threshold = float(os.environ.get("PII_GUARD_THRESHOLD", "0.7"))
    except ValueError:
        return 0.7
    if not math.isfinite(threshold) or threshold < 0 or threshold > 1:
        return 0.7
    return threshold


def _prompt_diagnostic(
    *,
    action: str,
    reason_code: str,
    hits: list,
    mode: str | None = None,
) -> str:
    details = [
        f"reason={reason_code}",
        f"action={action}",
        "event=UserPromptSubmit",
        f"detections={format_hit_summary(hits)}",
        f"hit_count={len(hits)}",
    ]
    if mode is not None:
        details.append(f"mode={mode}")
        details.append("mode_scope=local_development_non_protective")
    details.append("remediation=remove_sensitive_values_or_use_synthetic_data")
    return " ".join(details)


def _prompt_json_context(*, reason_code: str, hits: list, mode: str) -> str:
    return to_json({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                "[PII-GUARD aviso] "
                + _prompt_diagnostic(
                    action="allow",
                    reason_code=reason_code,
                    hits=hits,
                    mode=mode,
                )
            ),
        },
        "diagnostics": {
            "action": "allow",
            "event": "UserPromptSubmit",
            "hit_count": len(hits),
            "hits": summarize_hits(hits),
            "mode": mode,
            "mode_scope": "local_development_non_protective",
            "reason_codes": [reason_code],
        },
    })


def check_bash(tool_input: dict) -> tuple[bool, str]:
    command = tool_input.get("command", "") or ""
    if not command:
        return True, ""

    classification = classify_command(command)
    if classification.is_blocked:
        return False, classification.reason_code

    return True, ""


def main_user_prompt() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return 0

    prompt = payload.get("prompt", "") or ""
    if not prompt.strip():
        return 0

    threshold = _inline_threshold()
    mode = os.environ.get("PII_GUARD_MODE", "block")
    hits = list(detect(prompt, min_score=threshold))
    if not hits:
        return 0

    if mode == "warn":
        print(_prompt_json_context(reason_code="pii_detected", hits=hits, mode=mode))
        return 0

    if mode == "scrub":
        # scrub cannot replace the original prompt via additionalContext (it only
        # appends, leaking clear-text).  Treat scrub as block until Claude exposes
        # a documented prompt-replacement mechanism.
        sys.stderr.write(
            "[PII-GUARD BLOQUEADO] "
            + _prompt_diagnostic(
                action="block",
                reason_code="scrub_unsupported",
                hits=hits,
                mode=mode,
            )
            + "\n"
        )
        return 2

    sys.stderr.write(
        "[PII-GUARD BLOQUEADO] "
        + _prompt_diagnostic(action="block", reason_code="pii_detected", hits=hits)
        + "\n"
    )
    return 2


_KNOWN_LOCAL_TOOLS = frozenset({
    # File / notebook tools
    "Read", "Edit", "Write", "MultiEdit", "NotebookEdit", "NotebookRead",
    "Glob", "Grep",
    # Shell
    "Bash", "PowerShell",
    # Claude Code orchestration / meta tools (no external data egress)
    "Agent", "Task",
    "TaskCreate", "TaskGet", "TaskList", "TaskOutput", "TaskStop", "TaskUpdate",
    "ToolSearch",
    "AskUserQuestion",
    "ExitPlanMode", "EnterPlanMode",
    "ExitWorktree", "EnterWorktree",
    "Monitor",
    "PushNotification", "RemoteTrigger", "ScheduleWakeup",
    "CronCreate", "CronDelete", "CronList",
    "Skill",
})

_LLM_ORCHESTRATION_TOOLS = frozenset({
    "Agent", "Task", "TaskCreate", "TaskUpdate",
})

# MCP plugin prefixes whose tools are trusted (local memory, no external egress).
# WebFetch / WebSearch remain blocked — they are network-egress surfaces.
_ALLOWED_MCP_PREFIXES = (
    "mcp__plugin_mempalace_mempalace__",
    "mcp__ide__",
)


def _is_allowed_tool(tool: str) -> bool:
    if tool in _KNOWN_LOCAL_TOOLS:
        return True
    return any(tool.startswith(prefix) for prefix in _ALLOWED_MCP_PREFIXES)


def _iter_text_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(_iter_text_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(_iter_text_values(item))
        return values
    return []


def main_pre_tool() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return 0

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Fail closed: WebFetch, WebSearch, and unknown MCP tools are blocked.
    # Add entries to _KNOWN_LOCAL_TOOLS or _ALLOWED_MCP_PREFIXES to allow more.
    if not _is_allowed_tool(tool):
        return _deny_pre_tool(reason_code="unknown_tool", category="unknown_tool")

    if tool in _LLM_ORCHESTRATION_TOOLS:
        threshold = _inline_threshold()
        for text in _iter_text_values(tool_input):
            if detect(text, min_score=threshold):
                return _deny_pre_tool(
                    reason_code="inline_pii",
                    category="llm_orchestration",
                    command_count=1,
                )
        return 0

    if tool in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit", "NotebookRead"):
        ok, reason_code = check_path_tool(tool_input)
        if not ok:
            return _deny_pre_tool(reason_code=reason_code, category="protected_path", path_count=1)
        return 0

    if tool in ("Glob", "Grep"):
        ok, reason_code = check_glob_grep(tool_input)
        if not ok:
            return _deny_pre_tool(reason_code=reason_code, category="protected_path", path_count=1)
        return 0

    if tool in ("Bash", "PowerShell"):
        command = str(tool_input.get("command", "") or "")
        classification = classify_command(command)
        if classification.is_blocked:
            return _deny_pre_tool(
                reason_code=classification.reason_code,
                category=classification.category,
                command_count=1,
            )
        return 0

    return 0
