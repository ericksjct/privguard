"""Claude hook handlers backed by package detection and policy helpers."""

from __future__ import annotations

import json
import os
import re
import sys

from .detection import detect
from .diagnostics import format_hit_summary, summarize_hits, to_json
from .policy import EXFIL_CMDS, READ_CMDS, SENSITIVE_GLOBS, is_sensitive_path


def deny(prefix: str, reason_code: str) -> int:
    sys.stderr.write(f"[{prefix} BLOQUEADO] reason={reason_code}\n")
    return 2


def check_path_tool(tool_input: dict) -> tuple[bool, str]:
    for key in ("file_path", "path", "notebook_path"):
        value = tool_input.get(key)
        if value and is_sensitive_path(str(value)):
            return False, "sensitive_path"
    return True, ""


def check_glob_grep(tool_input: dict) -> tuple[bool, str]:
    pattern = tool_input.get("pattern", "")
    path = tool_input.get("path", "")
    for value in (pattern, path):
        if value and is_sensitive_path(str(value)):
            return False, "sensitive_glob_or_grep"
    return True, ""


def _inline_threshold() -> float:
    """Return the PII detection threshold, shared by prompt and tool surfaces."""
    return float(os.environ.get("PII_GUARD_THRESHOLD", "0.7"))


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

    if READ_CMDS.search(command):
        for match in re.finditer(r"[\"']?([\w\-./\\:]{3,})[\"']?", command):
            if is_sensitive_path(match.group(1)):
                return False, "sensitive_read_command"

    if EXFIL_CMDS.search(command):
        if any(rx.search(command) for rx in SENSITIVE_GLOBS):
            return False, "sensitive_network_command"

    if detect(command, min_score=_inline_threshold()):
        return False, "inline_pii"

    return True, ""


def main_user_prompt() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return 0

    prompt = payload.get("prompt", "") or ""
    if not prompt.strip():
        return 0

    threshold = float(os.environ.get("PII_GUARD_THRESHOLD", "0.7"))
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
    "Read", "Edit", "Write", "NotebookEdit",
    "Glob", "Grep",
    "Bash", "PowerShell",
})


def main_pre_tool() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.stderr.write("[PRE-TOOL-GUARD BLOQUEADO] reason=malformed_payload\n")
        return 2

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    # Fail closed: only explicitly known local tools are allowed to pass
    # through unblocked.  WebFetch, WebSearch, MCP-bridged tools, and any
    # future Anthropic-added tools are denied until explicitly allow-listed.
    if tool not in _KNOWN_LOCAL_TOOLS:
        return deny("PRE-TOOL-GUARD", "unknown_tool")

    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        ok, reason_code = check_path_tool(tool_input)
        if not ok:
            return deny("PRE-TOOL-GUARD", reason_code)
        return 0

    if tool in ("Glob", "Grep"):
        ok, reason_code = check_glob_grep(tool_input)
        if not ok:
            return deny("PRE-TOOL-GUARD", reason_code)
        return 0

    if tool in ("Bash", "PowerShell"):
        ok, reason_code = check_bash(tool_input)
        if not ok:
            return deny("PRE-TOOL-GUARD", reason_code)
        return 0

    return 0
