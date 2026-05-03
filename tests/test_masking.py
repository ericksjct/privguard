from __future__ import annotations

import json

from privguard import detection
from privguard.diagnostics import format_text, to_dict, to_json
from privguard.masking import MaskResult, mask_text, redact, verify_mask


def test_mask_text_replaces_sensitive_spans_with_typed_placeholders() -> None:
    text = "CPF 123.456.789-09 e token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890."

    result = mask_text(text)

    assert isinstance(result, MaskResult)
    assert result.changed is True
    assert result.verified is True
    assert result.verification_status == "verified"
    assert "<BR_CPF>" in result.text
    assert "<TOKEN>" in result.text
    assert "123.456.789-09" not in result.text
    assert "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890" not in result.text
    assert not hasattr(result, "mapping")


def test_redact_remains_compatible_wrapper() -> None:
    text = "CPF 123.456.789-09"
    hits = detection.detect(text)

    assert redact(text, hits) == "CPF <BR_CPF>"


def test_mask_text_normalizes_caller_provided_hit_order() -> None:
    text = "CPF 123.456.789-09 CNPJ 12.345.678/0001-95"
    hits = list(reversed(detection.detect(text)))

    result = mask_text(text, hits=hits)

    assert result.verified is True
    assert "123.456.789-09" not in result.text
    assert "12.345.678/0001-95" not in result.text
    assert result.text == "CPF <BR_CPF> CNPJ <BR_CNPJ>"


def test_verify_mask_fails_when_original_value_remains() -> None:
    text = "CPF 123.456.789-09"
    hits = detection.detect(text)

    verified, reason_codes = verify_mask(text, text, hits)

    assert verified is False
    assert "original_value_remaining" in reason_codes


def test_verify_mask_fails_on_residual_detection() -> None:
    original = "CPF 123.456.789-09"
    hits = detection.detect(original)
    masked = "CPF <BR_CPF> e CNPJ 12.345.678/0001-95"

    verified, reason_codes = verify_mask(original, masked, hits)

    assert verified is False
    assert "residual_detection" in reason_codes


def test_mask_result_for_clean_text_is_verified_and_unchanged() -> None:
    result = mask_text("texto publico sem identificadores")

    assert result.changed is False
    assert result.verified is True
    assert result.verification_status == "verified"
    assert result.reason_codes == ("no_sensitive_hits",)


def test_diagnostics_do_not_expose_raw_values_or_masked_payload() -> None:
    raw_cpf = "123.456.789-09"
    text = f"CPF {raw_cpf}"
    report = detection.analyze_text(text)
    result = mask_text(text)

    rendered_report = to_json(report)
    rendered_mask = to_json(result)
    rendered_text = format_text(result)
    parsed = json.loads(rendered_mask)

    assert raw_cpf not in rendered_report
    assert raw_cpf not in rendered_mask
    assert "<BR_CPF>" not in rendered_mask
    assert "<BR_CPF>" not in rendered_text
    assert parsed["verified"] is True
    assert parsed["hit_count"] == 1


def test_to_dict_sanitizes_hits_and_nested_structures() -> None:
    raw_cpf = "123.456.789-09"
    hit = detection.detect(f"CPF {raw_cpf}")[0]

    data = to_dict({"hit": hit, "items": [hit]})

    assert data["hit"]["kind"] == "BR_CPF"
    assert "value" not in data["hit"]
    assert raw_cpf not in str(data)
