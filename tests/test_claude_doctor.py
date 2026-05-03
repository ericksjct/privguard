from __future__ import annotations

import json
from pathlib import Path

import pytest

from privguard.cli import main


SYNTHETIC_CPF = "123.456.789-09"
SYNTHETIC_SECRET = "sk-test-abcdefghijklmnopqrstuvwxyz"
SYNTHETIC_PROTECTED_PATH = "data_sensivel/synthetic.csv"
SYNTHETIC_ENV_PATH = ".env"
SYNTHETIC_PROMPT = f"CPF {SYNTHETIC_CPF} token={SYNTHETIC_SECRET}"
SYNTHETIC_COMMAND = f"Get-Content {SYNTHETIC_PROTECTED_PATH} | Set-Clipboard"


FORBIDDEN_OUTPUT_VALUES = (
    SYNTHETIC_CPF,
    SYNTHETIC_SECRET,
    SYNTHETIC_PROTECTED_PATH,
    SYNTHETIC_ENV_PATH,
    SYNTHETIC_PROMPT,
    SYNTHETIC_COMMAND,
    "<BR_CPF>",
    "<TOKEN>",
)


def _assert_sanitized(rendered: str) -> None:
    for value in FORBIDDEN_OUTPUT_VALUES:
        assert value not in rendered


def test_claude_doctor_json_passes_with_synthetic_checks(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["claude", "doctor", "--json"]) == 0

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    payload = json.loads(captured.out)

    assert payload["command"] == "claude doctor"
    assert payload["synthetic_data"] is True
    assert captured.err == ""

    checks = {check["name"]: check for check in payload["checks"]}
    assert set(checks) == {
        "hook_wiring",
        "effective_prompt_policy",
        "synthetic_prompt_block",
        "synthetic_protected_path_block",
        "synthetic_command_block",
    }
    assert all(check["result"] == "pass" for check in checks.values())
    assert checks["synthetic_prompt_block"]["synthetic_data"] is True
    assert checks["synthetic_protected_path_block"]["synthetic_data"] is True
    assert checks["synthetic_command_block"]["synthetic_data"] is True

    _assert_sanitized(rendered)


def test_claude_doctor_human_output_is_synthetic_and_sanitized(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["claude", "doctor"]) == 0

    captured = capsys.readouterr()
    rendered = captured.out + captured.err

    assert "claude doctor" in captured.out
    assert "synthetic_data=true" in captured.out
    assert "hook_wiring: pass" in captured.out
    assert "effective_prompt_policy: pass" in captured.out
    assert "synthetic_prompt_block: pass" in captured.out
    assert "synthetic_protected_path_block: pass" in captured.out
    assert "synthetic_command_block: pass" in captured.out
    assert captured.err == ""

    _assert_sanitized(rendered)


def test_claude_doctor_json_returns_nonzero_for_missing_wiring(
    capsys: pytest.CaptureFixture[str],
) -> None:
    settings_path = Path("tests/fixtures/claude_missing_hooks_settings.json")

    assert main(["claude", "doctor", "--json", "--settings", str(settings_path)]) == 2

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    payload = json.loads(captured.out)
    checks = {check["name"]: check for check in payload["checks"]}

    assert payload["synthetic_data"] is True
    assert checks["hook_wiring"]["result"] == "fail"
    assert "hook_wiring_missing" in checks["hook_wiring"]["reason_codes"]
    assert captured.err == ""

    _assert_sanitized(rendered)


def test_claude_doctor_rejects_protected_settings_path_without_reading(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["claude", "doctor", "--json", "--settings", SYNTHETIC_ENV_PATH]) == 2

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    payload = json.loads(captured.out)
    checks = {check["name"]: check for check in payload["checks"]}

    assert checks["hook_wiring"]["result"] == "fail"
    assert "settings_path_protected" in checks["hook_wiring"]["reason_codes"]
    assert captured.err == ""

    _assert_sanitized(rendered)
