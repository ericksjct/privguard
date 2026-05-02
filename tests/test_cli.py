from __future__ import annotations

import json

import pytest

from privguard.cli import main


def test_info_command_returns_package_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["info"]) == 0

    out = capsys.readouterr().out

    assert "privguard" in out
    assert "detectors: lightweight" in out


def test_scan_human_output_is_sanitized(capsys: pytest.CaptureFixture[str]) -> None:
    raw_cpf = "123.456.789-09"

    assert main(["scan", f"CPF {raw_cpf}"]) == 0

    out = capsys.readouterr().out
    assert "BR_CPF" in out
    assert raw_cpf not in out


def test_scan_json_output_is_sanitized(capsys: pytest.CaptureFixture[str]) -> None:
    raw_cpf = "123.456.789-09"

    assert main(["scan", "--json", f"CPF {raw_cpf}"]) == 0

    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["counts"]["BR_CPF"] == 1
    assert "value" not in payload["hits"][0]
    assert raw_cpf not in out


def test_mask_outputs_masked_payload_explicitly(capsys: pytest.CaptureFixture[str]) -> None:
    raw_cpf = "123.456.789-09"

    assert main(["mask", f"CPF {raw_cpf}"]) == 0

    out = capsys.readouterr().out
    assert "<BR_CPF>" in out
    assert raw_cpf not in out


def test_mask_json_outputs_metadata_not_payload(capsys: pytest.CaptureFixture[str]) -> None:
    raw_cpf = "123.456.789-09"

    assert main(["mask", "--json", f"CPF {raw_cpf}"]) == 0

    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["verified"] is True
    assert "<BR_CPF>" not in out
    assert raw_cpf not in out


def test_policy_check_blocks_unknown_by_default(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["policy-check", "texto publico"]) == 2

    out = capsys.readouterr().out
    assert "fail_closed_surface" in out


def test_policy_check_allows_verified_masked_external_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    raw_cpf = "123.456.789-09"

    assert main([
        "policy-check",
        "--json",
        "--masked",
        "--capability",
        "external",
        f"CPF {raw_cpf}",
    ]) == 0

    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["decision"]["allow"] is True
    assert raw_cpf not in out


def test_policy_check_blocks_protected_path_without_echoing_path(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["policy-check", "--json", "--path", ".env", "texto publico"]) == 2

    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["path"]["category"] == "env_file"
    assert ".env" not in out


def test_cli_can_read_text_from_stdin(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    raw_cpf = "123.456.789-09"
    monkeypatch.setattr("sys.stdin", type("FakeStdin", (), {"read": lambda self: f"CPF {raw_cpf}"})())

    assert main(["scan"]) == 0

    out = capsys.readouterr().out
    assert "BR_CPF" in out
    assert raw_cpf not in out
