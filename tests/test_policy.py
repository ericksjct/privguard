from __future__ import annotations

import json
import pathlib

from privguard.detection import detect
from privguard.diagnostics import to_dict, to_json
from privguard.masking import mask_text
from privguard.policy import (
    PathClassification,
    PolicyAction,
    PolicyDecision,
    PolicyMode,
    SurfaceCapability,
    classify_path,
    decide_policy,
    is_sensitive_path,
)


def test_classify_path_detects_protected_strings_without_file_io() -> None:
    cases = {
        ".env": ("env_file", "protected_path_env"),
        ".env.local": ("env_file", "protected_path_env"),
        r"data_sensivel\synthetic.csv": ("protected_data", "protected_path_data"),
        "../cooperados/lista.csv": ("protected_data", "protected_path_data"),
        "exports/dump_2025_05.txt": ("dump_file", "protected_path_dump"),
        "config/credenciais_fake.json": ("credentials_file", "protected_path_credentials"),
        "tmp/segredo-local.txt": ("secret_filename", "protected_path_secret_name"),
    }

    for path, expected in cases.items():
        classification = classify_path(path)
        assert classification.is_protected is True
        assert (classification.category, classification.reason_code) == expected
        assert is_sensitive_path(path) is True


def test_classify_path_normalizes_quotes_windows_and_relative_segments() -> None:
    env_path = classify_path(r'"C:\repo\safe\..\data_sensivel\synthetic.csv"')
    safe_path = classify_path("safe/example.txt")

    assert env_path.is_protected is True
    assert env_path.reason_code == "protected_path_data"
    assert safe_path == PathClassification(False, "unprotected", "path_unprotected")
    assert is_sensitive_path("safe/example.txt") is False


def test_classify_path_source_does_not_read_files() -> None:
    source = pathlib.Path("privguard/policy.py").read_text(encoding="utf-8")

    assert ".read_text(" not in source
    assert ".open(" not in source


def test_rewrite_capable_allows_only_clean_or_verified_masked_content() -> None:
    raw_text = "CPF 123.456.789-09"
    hits = detect(raw_text)

    clean = decide_policy(SurfaceCapability.REWRITE_CAPABLE, hits=[])
    needs_mask = decide_policy(SurfaceCapability.REWRITE_CAPABLE, hits=hits)
    masked = decide_policy(
        SurfaceCapability.REWRITE_CAPABLE,
        hits=hits,
        mask_result=mask_text(raw_text, hits=hits),
    )

    assert clean.action == PolicyAction.ALLOW
    assert needs_mask.action == PolicyAction.PAUSE
    assert "mask_required" in needs_mask.reason_codes
    assert masked.allow is True
    assert masked.action == PolicyAction.ALLOW


def test_incomplete_mask_never_allows() -> None:
    raw_text = "CPF 123.456.789-09"
    hits = detect(raw_text)
    result = mask_text(raw_text, hits=hits)
    failed = type(result)(
        text=raw_text,
        changed=False,
        verified=False,
        verification_status="failed",
        reason_codes=("original_value_remaining",),
        hits=tuple(hits),
    )

    decision = decide_policy(SurfaceCapability.REWRITE_CAPABLE, hits=hits, mask_result=failed)

    assert decision.action == PolicyAction.PAUSE
    assert decision.allow is False
    assert "mask_unverified" in decision.reason_codes


def test_block_only_unknown_external_and_unsupported_fail_closed() -> None:
    hits = detect("CPF 123.456.789-09")

    assert decide_policy(SurfaceCapability.BLOCK_ONLY, hits=hits).action == PolicyAction.BLOCK
    assert decide_policy(SurfaceCapability.UNKNOWN, hits=[]).action == PolicyAction.BLOCK
    assert decide_policy(SurfaceCapability.EXTERNAL, hits=[]).action == PolicyAction.BLOCK
    assert decide_policy(SurfaceCapability.UNSUPPORTED, hits=hits).action == PolicyAction.BLOCK
    assert decide_policy(SurfaceCapability.OBSERVE_ONLY, hits=hits).action == PolicyAction.BLOCK


def test_unknown_external_allow_verified_masked_output_only() -> None:
    raw_text = "CPF 123.456.789-09"
    hits = detect(raw_text)
    result = mask_text(raw_text, hits=hits)

    decision = decide_policy(SurfaceCapability.EXTERNAL, hits=hits, mask_result=result)

    assert decision.allow is True
    assert decision.action == PolicyAction.ALLOW
    assert "mask_verified" in decision.reason_codes


def test_protected_path_blocks_before_surface_policy() -> None:
    decision = decide_policy(
        SurfaceCapability.REWRITE_CAPABLE,
        hits=[],
        path_classification=classify_path(".env"),
    )

    assert decision.action == PolicyAction.BLOCK
    assert decision.protected_path is True
    assert "protected_path" in decision.reason_codes


def test_policy_diagnostics_are_sanitized() -> None:
    raw_cpf = "123.456.789-09"
    decision = decide_policy(SurfaceCapability.BLOCK_ONLY, hits=detect(f"CPF {raw_cpf}"))
    path = classify_path(".env")
    rendered = to_json({"decision": to_dict(decision), "path": to_dict(path)})
    parsed = json.loads(rendered)

    assert isinstance(decision, PolicyDecision)
    assert parsed["decision"]["action"] == "block"
    assert parsed["path"]["category"] == "env_file"
    assert raw_cpf not in rendered
    assert ".env" not in rendered


def test_permissive_mode_can_allow_unknown_clean_text() -> None:
    decision = decide_policy(
        SurfaceCapability.UNKNOWN,
        hits=[],
        mode=PolicyMode.PERMISSIVE,
    )

    assert decision.action == PolicyAction.ALLOW
    assert "permissive_no_sensitive_hits" in decision.reason_codes
