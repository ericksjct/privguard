from __future__ import annotations

import io
import json
import sys

import pytest

from privguard.cli import main as cli_main
from privguard.hooks import main_pre_tool, main_user_prompt


RAW_CPF = "123.456.789-09"
FAKE_SECRET = "sk-test-abcdefghijklmnopqrstuvwxyz"
PROTECTED_ENV = ".env"
PROTECTED_DATA_PATH = "data_sensivel/synthetic.csv"
PROMPT_SNIPPET = "analise o cadastro"
COMMAND_SNIPPETS = (
    "Get-Content",
    "Copy-Item",
    "Compress-Archive",
    "certutil",
    "Set-Clipboard",
    "curl",
)
PROMPT_TEXT = f"{PROMPT_SNIPPET}: CPF {RAW_CPF} token={FAKE_SECRET}"
COMMAND_TEXT = f"Get-Content {PROTECTED_DATA_PATH} | Set-Clipboard"


FORBIDDEN_OUTPUT = (
    RAW_CPF,
    FAKE_SECRET,
    PROTECTED_ENV,
    PROTECTED_DATA_PATH,
    "data_sensivel",
    PROMPT_SNIPPET,
    PROMPT_TEXT,
    COMMAND_TEXT,
    "CPF ",
    "sk-test-",
    "redacted=",
    "<BR_CPF>",
    "<TOKEN>",
    *COMMAND_SNIPPETS,
)


def _assert_forbidden_values_absent(output: str) -> None:
    for value in FORBIDDEN_OUTPUT:
        assert value not in output


def _run_user_prompt(monkeypatch: pytest.MonkeyPatch, payload: dict[str, object]) -> int:
    monkeypatch.delenv("PII_GUARD_MODE", raising=False)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    return main_user_prompt()


def _run_pre_tool(monkeypatch: pytest.MonkeyPatch, payload: dict[str, object]) -> int:
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    return main_pre_tool()


def test_phase_03_claude_surfaces_block_and_stay_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _run_user_prompt(monkeypatch, {"prompt": PROMPT_TEXT}) == 2
    captured = capsys.readouterr()
    prompt_output = captured.out + captured.err

    assert "UserPromptSubmit" in prompt_output
    assert "action=block" in prompt_output
    assert "BR_CPF" in prompt_output
    _assert_forbidden_values_absent(prompt_output)

    assert _run_pre_tool(
        monkeypatch,
        {"tool_name": "Read", "tool_input": {"file_path": PROTECTED_DATA_PATH}},
    ) == 2
    captured = capsys.readouterr()
    path_output = captured.out + captured.err

    assert "PreToolUse" in path_output
    assert "action=block" in path_output
    assert "protected_path" in path_output
    _assert_forbidden_values_absent(path_output)

    assert _run_pre_tool(
        monkeypatch,
        {"tool_name": "PowerShell", "tool_input": {"command": COMMAND_TEXT}},
    ) == 2
    captured = capsys.readouterr()
    command_output = captured.out + captured.err

    assert "PreToolUse" in command_output
    assert "action=block" in command_output
    assert "category=clipboard" in command_output
    _assert_forbidden_values_absent(command_output)


def test_phase_03_claude_doctor_reports_synthetic_safe_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert cli_main(["claude", "doctor", "--json"]) == 0

    captured = capsys.readouterr()
    output = captured.out + captured.err
    payload = json.loads(captured.out)

    assert captured.err == ""
    assert payload["command"] == "claude doctor"
    assert payload["synthetic_data"] is True

    checks = {check["name"]: check for check in payload["checks"]}
    assert {
        "hook_wiring",
        "effective_prompt_policy",
        "synthetic_prompt_block",
        "synthetic_protected_path_block",
        "synthetic_command_block",
    } <= set(checks)
    assert all(check["result"] == "pass" for check in checks.values())
    assert all(
        check["synthetic_data"] is True
        for check in checks.values()
        if check["name"].startswith("synthetic_")
    )
    _assert_forbidden_values_absent(output)
