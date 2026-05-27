"""Claude hook handlers backed by package detection and policy helpers."""

from __future__ import annotations

import datetime
import json
import math
import os
import pathlib
import sys
from urllib.parse import urlparse

from .detection import detect
from .diagnostics import format_hit_summary, summarize_hits, to_json
from .masking import mask_text
from .policy import classify_command, classify_path


_ALLOWED_FETCH_DOMAINS: frozenset[str] = frozenset({
    "github.com",
    "raw.githubusercontent.com",
    "docs.python.org",
    "pypi.org",
    "docs.anthropic.com",
    "docs.rs",
    "crates.io",
})


def check_webfetch(tool_input: dict) -> tuple[bool, str]:
    """Allow WebFetch only to domains in _ALLOWED_FETCH_DOMAINS.

    Subdomain matching: a netloc of "api.github.com" is allowed because it
    ends with ".github.com" (i.e. the parent domain "github.com" is allowed).
    """
    url = tool_input.get("url") or ""
    if not url or not isinstance(url, str):
        return False, "webfetch_url_missing"
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if not netloc:
        return False, "webfetch_domain_not_allowed"
    # Exact match or subdomain match (netloc ends with ".<allowed_domain>")
    for domain in _ALLOWED_FETCH_DOMAINS:
        if netloc == domain or netloc.endswith("." + domain):
            return True, ""
    return False, "webfetch_domain_not_allowed"


def _audit_log(
    *,
    event: str,
    action: str,
    reason_code: str,
    category: str = "",
    log_path: "pathlib.Path | None" = None,
) -> None:
    """Append one JSON line to ~/.privguard/audit.log. Never raises."""
    try:
        if log_path is None:
            log_dir = pathlib.Path.home() / ".privguard"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "audit.log"
        entry = {
            "ts": datetime.datetime.now(datetime.UTC).isoformat().replace("+00:00", "Z"),
            "event": event,
            "action": action,
            "reason_code": reason_code,
            "category": category,
        }
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def deny(prefix: str, reason_code: str) -> int:
    _audit_log(event="UserPromptSubmit", action="block", reason_code=reason_code)
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
    _audit_log(event="PreToolUse", action="block", reason_code=reason_code, category=category)
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

    classification = classify_command(command, min_score=_inline_threshold())
    if classification.is_blocked:
        return False, classification.reason_code

    return True, ""


def main_user_prompt() -> int:
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("privguard-user-prompt: PreToolUse hook for Claude Code. Reads JSON from stdin.")
        return 0
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
        _audit_log(event="UserPromptSubmit", action="allow", reason_code="no_pii")
        return 0

    if mode == "warn":
        _audit_log(event="UserPromptSubmit", action="warn", reason_code="pii_detected")
        print(_prompt_json_context(reason_code="pii_detected", hits=hits, mode=mode))
        return 0

    if mode == "scrub":
        sys.stderr.write("[PII-GUARD] modo scrub removido, usando block\n")
        # falls through to default block below

    if mode == "mask":
        mask_result = mask_text(prompt, hits=hits)
        if not mask_result.verified:
            _audit_log(
                event="UserPromptSubmit",
                action="block",
                reason_code="mask_verification_failed",
            )
            sys.stderr.write(
                "[PII-GUARD BLOQUEADO] "
                + _prompt_diagnostic(
                    action="block",
                    reason_code="mask_verification_failed",
                    hits=hits,
                )
                + "\n"
            )
            return 2
        _audit_log(event="UserPromptSubmit", action="block", reason_code="pii_masked")
        sys.stderr.write(
            "[PII-GUARD BLOQUEADO] "
            + _prompt_diagnostic(action="block", reason_code="pii_masked", hits=hits)
            + "\n"
        )
        sys.stderr.write("[PII-GUARD VERSAO MASCARADA]\n")
        sys.stderr.write(mask_result.text + "\n")
        sys.stderr.write("[Reenvie o prompt acima com os valores mascarados]\n")
        return 2

    _audit_log(event="UserPromptSubmit", action="block", reason_code="pii_detected")
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
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("privguard-pre-tool: PreToolUse hook for Claude Code. Reads JSON from stdin.")
        return 0
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return 0

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    if tool == "WebFetch":
        ok, reason_code = check_webfetch(tool_input)
        if not ok:
            return _deny_pre_tool(reason_code=reason_code, category="webfetch")
        return 0

    # Fail closed: WebSearch and unknown MCP tools are blocked.
    # Add entries to _KNOWN_LOCAL_TOOLS or _ALLOWED_MCP_PREFIXES to allow more.
    if not _is_allowed_tool(tool):
        return _deny_pre_tool(reason_code="unknown_tool", category="unknown_tool")

    if tool in _LLM_ORCHESTRATION_TOOLS:
        threshold = _inline_threshold()
        mode = os.environ.get("PII_GUARD_MODE", "block")
        for text in _iter_text_values(tool_input):
            hits = list(detect(text, min_score=threshold))
            if not hits:
                continue
            if mode == "warn":
                # Non-protective pass-through for local development.
                continue
            if mode == "mask":
                mask_result = mask_text(text, hits=hits)
                if not mask_result.verified:
                    return _deny_pre_tool(
                        reason_code="mask_verification_failed",
                        category="llm_orchestration",
                        command_count=1,
                    )
                # Verified mask — block with pii_masked reason.
                # updatedInput is not available for LLM orchestration tools (Agent/Task),
                # so mask mode cannot forward a sanitized payload. Block is the only safe
                # option (consistent with D-01 / D-02 decisions).
                return _deny_pre_tool(
                    reason_code="pii_masked",
                    category="llm_orchestration",
                    command_count=1,
                )
            # Default: block
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
        classification = classify_command(command, min_score=_inline_threshold())
        if classification.is_blocked:
            return _deny_pre_tool(
                reason_code=classification.reason_code,
                category=classification.category,
                command_count=1,
            )
        return 0

    return 0
