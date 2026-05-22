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


def test_verify_mask_allows_placeholder_only_secret_assignment() -> None:
    text = "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

    result = mask_text(text)

    assert result.verified is True
    assert result.text == "token=<TOKEN>"
    assert "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890" not in result.text


def test_verify_mask_rejects_placeholder_assignment_with_secret_suffix() -> None:
    original = "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    hits = detection.detect(original)
    masked = "token=<TOKEN>ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

    verified, reason_codes = verify_mask(original, masked, hits)

    assert verified is False
    assert "original_value_remaining" in reason_codes


def test_mask_result_for_clean_text_is_verified_and_unchanged() -> None:
    result = mask_text("texto publico sem identificadores")

    assert result.changed is False
    assert result.verified is True
    assert result.verification_status == "verified"
    assert result.reason_codes == ("no_sensitive_hits",)


def test_mask_text_does_not_fail_open_when_caller_passes_empty_hits() -> None:
    text = "CPF 123.456.789-09"

    result = mask_text(text, hits=[])

    assert result.verified is False
    assert result.verification_status == "failed"
    assert "residual_detection" in result.reason_codes
    assert result.text == text


def test_verify_mask_runs_residual_detection_when_hits_empty() -> None:
    text = "CPF 123.456.789-09"

    verified, reason_codes = verify_mask(text, text, [])

    assert verified is False
    assert "residual_detection" in reason_codes


def test_verify_mask_returns_no_sensitive_hits_when_truly_clean() -> None:
    text = "texto publico sem identificadores"

    verified, reason_codes = verify_mask(text, text, [])

    assert verified is True
    assert reason_codes == ("no_sensitive_hits",)


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


# --- Phase 999.4: CPF leniency masking tests ---

def test_lenient_cpf_masks_correctly() -> None:
    """mask_text('456.789.123-45', lenient=True) returns verified=True with <BR_CPF>."""
    import os
    os.environ.pop("PII_GUARD_LENIENT", None)
    result = mask_text("456.789.123-45", lenient=True)
    assert result.verified is True, f"verified must be True, got {result.verified}"
    assert "<BR_CPF>" in result.text, f"<BR_CPF> not in masked text: {result.text}"
    assert "456.789.123-45" not in result.text, "raw CPF value must not remain after masking"


def test_lenient_mask_strict_default_leaves_invalid_cpf_unmasked() -> None:
    """mask_text('456.789.123-45') with no param leaves the invalid CPF unmasked."""
    import os
    os.environ.pop("PII_GUARD_LENIENT", None)
    result = mask_text("456.789.123-45")
    assert "456.789.123-45" in result.text, "strict default must leave invalid CPF unmasked"


def test_lenient_mask_backward_compat_valid_cpf() -> None:
    """Existing valid CPF masking still works with no lenient param."""
    import os
    os.environ.pop("PII_GUARD_LENIENT", None)
    result = mask_text("CPF 123.456.789-09")
    assert "<BR_CPF>" in result.text
    assert result.verified is True
