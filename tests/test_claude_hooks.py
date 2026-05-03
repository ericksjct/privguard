from __future__ import annotations

import io
import json
import sys

import pytest

from privguard.hooks import main_user_prompt


RAW_CPF = "123.456.789-09"
PROMPT_SNIPPET = "analise o cadastro"
SECRET_LOOKING = "sk-test-abcdefghijklmnopqrstuvwxyz"


def run_user_prompt(
    monkeypatch: pytest.MonkeyPatch,
    payload: object | str,
    *,
    mode: str | None = None,
) -> int:
    if mode is None:
        monkeypatch.delenv("PII_GUARD_MODE", raising=False)
    else:
        monkeypatch.setenv("PII_GUARD_MODE", mode)

    if isinstance(payload, str):
        raw_payload = payload
    else:
        raw_payload = json.dumps(payload)

    monkeypatch.setattr(sys, "stdin", io.StringIO(raw_payload))
    return main_user_prompt()


def assert_no_prompt_derived_text(output: str) -> None:
    forbidden = (
        RAW_CPF,
        PROMPT_SNIPPET,
        SECRET_LOOKING,
        "<BR_CPF>",
        "redacted=",
        "CPF ",
        "api_key",
        "sk-test-",
    )
    for value in forbidden:
        assert value not in output


def test_user_prompt_blocks_synthetic_cpf_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prompt = f"{PROMPT_SNIPPET}: CPF {RAW_CPF}"

    assert run_user_prompt(monkeypatch, {"prompt": prompt}) == 2

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert captured.out == ""
    assert "BLOQUEADO" in captured.err
    assert "reason=pii_detected" in output
    assert "action=block" in output
    assert "BR_CPF@24:38" in output
    assert "score=" in output
    assert "reason=checksum_valid" in output
    assert "remediation=" in output
    assert_no_prompt_derived_text(output)


def test_user_prompt_allows_clean_prompt_without_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run_user_prompt(monkeypatch, {"prompt": "texto publico sem dados sensiveis"}) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_user_prompt_malformed_json_fails_open_without_echo(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    malformed = f'{{"prompt": "{PROMPT_SNIPPET} CPF {RAW_CPF}"'

    assert run_user_prompt(monkeypatch, malformed) == 0

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert output == ""
    assert_no_prompt_derived_text(output)


@pytest.mark.parametrize("mode", ["warn", "scrub"])
def test_non_blocking_prompt_modes_are_labeled_non_protective_and_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mode: str,
) -> None:
    prompt = f"{PROMPT_SNIPPET}: CPF {RAW_CPF} api_key={SECRET_LOOKING}"

    exit_code = run_user_prompt(monkeypatch, {"prompt": prompt}, mode=mode)

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert exit_code in {0, 2}
    assert "local_development_non_protective" in output
    assert "UserPromptSubmit" in output or "BLOQUEADO" in output
    assert "BR_CPF" in output
    assert "API_KEY" in output
    assert_no_prompt_derived_text(output)
