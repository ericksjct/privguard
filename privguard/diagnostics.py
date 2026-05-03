"""Sanitized diagnostic serializers for detection, masking, and policy metadata."""

from __future__ import annotations

import json
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any

from .detection import DetectionReport, Hit, detect
from .masking import MaskResult


SYNTHETIC_DOCTOR_PROMPT = (
    "Validacao sintetica CPF 123.456.789-09 "
    "token=sk-test-abcdefghijklmnopqrstuvwxyz"
)
SYNTHETIC_DOCTOR_PATH = "data_sensivel/synthetic.csv"
SYNTHETIC_DOCTOR_COMMAND = f"Get-Content {SYNTHETIC_DOCTOR_PATH} | Set-Clipboard"


def summarize_hits(hits: Any) -> list[dict[str, object]]:
    return [to_dict(hit) for hit in tuple(hits)]


def to_dict(value: Any) -> Any:
    if isinstance(value, Hit):
        return {
            "kind": value.kind,
            "start": value.start,
            "end": value.end,
            "score": value.score,
            "reason_code": value.reason_code,
            "source": value.source,
        }

    if isinstance(value, DetectionReport):
        return {
            "counts": dict(value.counts),
            "hits": summarize_hits(value.hits),
        }

    if isinstance(value, MaskResult):
        return {
            "changed": value.changed,
            "verified": value.verified,
            "verification_status": value.verification_status,
            "reason_codes": list(value.reason_codes),
            "hit_count": len(value.hits),
            "hits": summarize_hits(value.hits),
        }

    if isinstance(value, dict):
        return {str(k): to_dict(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [to_dict(item) for item in value]

    if is_dataclass(value):
        result: dict[str, Any] = {}
        for name in getattr(value, "__dataclass_fields__", {}):
            if name in {"value", "text"}:
                continue
            result[name] = to_dict(getattr(value, name))
        return result

    return value


def to_json(value: Any) -> str:
    return json.dumps(to_dict(value), ensure_ascii=False, sort_keys=True)


def format_hit_summary(hits: Any) -> str:
    return ", ".join(
        (
            f"{hit.kind}@{hit.start}:{hit.end} "
            f"score={hit.score:.2f} reason={hit.reason_code}"
        )
        for hit in tuple(hits)
    )


def format_text(value: Any) -> str:
    data = to_dict(value)

    if isinstance(data, dict) and "counts" in data:
        counts = data.get("counts") or {}
        total = sum(int(count) for count in counts.values())
        return f"detections={total} counts={counts}"

    if isinstance(data, dict) and "verification_status" in data:
        return (
            f"mask verified={data.get('verified')} "
            f"status={data.get('verification_status')} "
            f"reasons={data.get('reason_codes')}"
        )

    if isinstance(data, list):
        return ", ".join(str(item) for item in data)

    return str(data)


def _check_result(passed: bool) -> str:
    return "pass" if passed else "fail"


def _doctor_check(
    name: str,
    passed: bool,
    reason_codes: list[str] | None = None,
    *,
    synthetic_data: bool | None = None,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    check: dict[str, object] = {
        "name": name,
        "result": _check_result(passed),
        "reason_codes": list(reason_codes or []),
    }
    if synthetic_data is not None:
        check["synthetic_data"] = synthetic_data
    if metadata:
        check["metadata"] = metadata
    return check


def _load_claude_settings(settings_path: str | Path) -> tuple[dict[str, Any], list[str]]:
    from .policy import classify_path

    if classify_path(str(settings_path)).is_protected:
        return {}, ["settings_path_protected"]

    try:
        with Path(settings_path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return {}, ["settings_missing"]
    except (OSError, json.JSONDecodeError, ValueError):
        return {}, ["settings_unreadable"]
    if not isinstance(data, dict):
        return {}, ["settings_invalid"]
    return data, []


def _hook_commands(entries: Any) -> list[str]:
    commands: list[str] = []
    if not isinstance(entries, list):
        return commands
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        for hook in entry.get("hooks", []) or []:
            if isinstance(hook, dict) and isinstance(hook.get("command"), str):
                commands.append(hook["command"])
    return commands


def _hook_matchers(entries: Any) -> list[str]:
    matchers: list[str] = []
    if not isinstance(entries, list):
        return matchers
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("matcher"), str):
            matchers.append(entry["matcher"])
    return matchers


def _check_hook_wiring(settings_path: str | Path) -> dict[str, object]:
    settings, errors = _load_claude_settings(settings_path)
    hooks = settings.get("hooks", {}) if isinstance(settings, dict) else {}
    if not isinstance(hooks, dict):
        hooks = {}

    prompt_commands = _hook_commands(hooks.get("UserPromptSubmit"))
    pre_tool_commands = _hook_commands(hooks.get("PreToolUse"))
    pre_tool_matchers = _hook_matchers(hooks.get("PreToolUse"))

    prompt_wired = any(
        "hooks/pii_guard.py" in command.replace("\\", "/")
        for command in prompt_commands
    )
    pre_tool_wired = any(
        "hooks/pre_tool_guard.py" in command.replace("\\", "/")
        for command in pre_tool_commands
    )
    matcher_strict = "*" in pre_tool_matchers

    reason_codes = list(errors)
    if not prompt_wired or not pre_tool_wired:
        reason_codes.append("hook_wiring_missing")
    if pre_tool_wired and not matcher_strict:
        reason_codes.append("pre_tool_matcher_not_strict")

    passed = prompt_wired and pre_tool_wired and matcher_strict and not errors
    return _doctor_check(
        "hook_wiring",
        passed,
        reason_codes,
        metadata={
            "user_prompt_hook": prompt_wired,
            "pre_tool_hook": pre_tool_wired,
            "pre_tool_match_all": matcher_strict,
        },
    )


def _check_effective_prompt_policy() -> dict[str, object]:
    from .policy import PolicyAction, SurfaceCapability, decide_policy

    hits = list(detect(SYNTHETIC_DOCTOR_PROMPT))
    decision = decide_policy(SurfaceCapability.BLOCK_ONLY, hits=hits)
    passed = decision.action == PolicyAction.BLOCK and bool(hits)
    reason_codes = list(decision.reason_codes)
    if not passed:
        reason_codes.append("prompt_policy_not_blocking")
    return _doctor_check(
        "effective_prompt_policy",
        passed,
        reason_codes,
        synthetic_data=True,
        metadata={
            "action": decision.action,
            "hit_count": len(hits),
            "kinds": sorted({hit.kind for hit in hits}),
        },
    )


def _check_synthetic_prompt_block() -> dict[str, object]:
    hits = list(detect(SYNTHETIC_DOCTOR_PROMPT))
    passed = bool(hits)
    reason_codes = ["pii_detected"] if passed else ["synthetic_prompt_not_detected"]
    return _doctor_check(
        "synthetic_prompt_block",
        passed,
        reason_codes,
        synthetic_data=True,
        metadata={
            "hit_count": len(hits),
            "hits": summarize_hits(hits),
        },
    )


def _check_synthetic_protected_path_block() -> dict[str, object]:
    from .policy import classify_path

    classification = classify_path(SYNTHETIC_DOCTOR_PATH)
    passed = classification.is_protected
    return _doctor_check(
        "synthetic_protected_path_block",
        passed,
        [classification.reason_code],
        synthetic_data=True,
        metadata={
            "category": classification.category,
            "protected_path": classification.is_protected,
        },
    )


def _check_synthetic_command_block() -> dict[str, object]:
    from .policy import classify_command

    classification = classify_command(SYNTHETIC_DOCTOR_COMMAND)
    passed = classification.is_blocked
    return _doctor_check(
        "synthetic_command_block",
        passed,
        [classification.reason_code],
        synthetic_data=True,
        metadata={
            "category": classification.category,
            "blocked": classification.is_blocked,
        },
    )


def build_claude_doctor_report(settings_path: str | Path = ".claude/settings.json") -> dict[str, object]:
    checks = [
        _check_hook_wiring(settings_path),
        _check_effective_prompt_policy(),
        _check_synthetic_prompt_block(),
        _check_synthetic_protected_path_block(),
        _check_synthetic_command_block(),
    ]
    return {
        "command": "claude doctor",
        "synthetic_data": True,
        "checks": checks,
    }


def claude_doctor_passed(report: dict[str, object]) -> bool:
    checks = report.get("checks", [])
    return isinstance(checks, list) and all(
        isinstance(check, dict) and check.get("result") == "pass"
        for check in checks
    )


def format_claude_doctor_text(report: dict[str, object]) -> str:
    lines = [
        "claude doctor",
        f"synthetic_data={str(report.get('synthetic_data') is True).lower()}",
    ]
    checks = report.get("checks", [])
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, dict):
                continue
            reason_codes = check.get("reason_codes") or []
            suffix = ""
            if reason_codes:
                suffix = f" reason_codes={reason_codes}"
            lines.append(f"{check.get('name')}: {check.get('result')}{suffix}")
    return "\n".join(lines)
