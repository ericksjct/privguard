from __future__ import annotations

import importlib

import pytest

from privguard import detection


def _kinds(text: str) -> set[str]:
    return {hit.kind for hit in detection.detect(text)}


def test_detects_valid_brazilian_identifiers_and_contact_data() -> None:
    text = (
        "CPF 123.456.789-09; CNPJ 12.345.678/0001-95; "
        "CNH 12345678900; titulo 1234 5678 0191; "
        "PIS 123.45678.90-0; SUS 123 4567 8901 2348; "
        "RG 12.345.678-9; celular +55 (11) 91234-5678; "
        "CEP 01310-200; placas ABC-1234 e BRA1A23."
    )

    assert _kinds(text) >= {
        "BR_CPF",
        "BR_CNPJ",
        "BR_CNH",
        "BR_TITULO_ELEITOR",
        "BR_PIS_PASEP",
        "BR_CARTAO_SUS",
        "BR_RG",
        "BR_PHONE",
        "BR_CEP",
        "BR_PLACA_OLD",
        "BR_PLACA_MERCOSUL",
    }


def test_invalid_checksum_lookalikes_are_below_default_threshold() -> None:
    text = (
        "CPF 123.456.789-00; CNPJ 12.345.678/0001-00; "
        "CNH 12345678999; titulo 1234 5678 0199; "
        "PIS 123.45678.90-9; SUS 123 4567 8901 2340."
    )

    assert _kinds(text).isdisjoint(
        {
            "BR_CPF",
            "BR_CNPJ",
            "BR_CNH",
            "BR_TITULO_ELEITOR",
            "BR_PIS_PASEP",
            "BR_CARTAO_SUS",
        }
    )


def test_detects_secret_like_values_without_exposing_report_values() -> None:
    text = (
        "api_key=sk-test-abcdefghijklmnopqrstuvwxyz; "
        "token = ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890; "
        "password='fake-password-value'; "
        "DATABASE_URL=postgres://user:pass@localhost:5432/app; "
        "FEATURE_FLAG=true"
    )

    report = detection.analyze_text(text)

    assert report.counts["API_KEY"] == 1
    assert report.counts["TOKEN"] == 1
    assert report.counts["PASSWORD_ASSIGNMENT"] == 1
    assert report.counts["DATABASE_URL"] == 1
    assert "FEATURE_FLAG" not in report.counts
    assert all(hit.reason_code for hit in report.hits)
    assert all(hit.source == "stdlib" for hit in report.hits)

    sanitized = str(report.counts)
    for hit in report.hits:
        assert hit.value not in sanitized


def test_detect_import_contract_and_report_counts_are_stable() -> None:
    hit = detection.detect("CPF 123.456.789-09")[0]
    report = detection.analyze_text("CPF 123.456.789-09")

    assert hit.reason_code == "checksum_valid"
    assert hit.source == "stdlib"
    assert isinstance(report.hits, tuple)
    assert report.counts == {"BR_CPF": 1}


def test_default_core_does_not_import_presidio() -> None:
    importlib.import_module("privguard.detection")

    assert "presidio" not in detection.__dict__


def test_overlap_prefers_higher_confidence_then_longer_then_earlier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        detection,
        "PATTERNS",
        [
            detection.PatternEntry("LOW_LONG", detection.re.compile(r"ABCDE"), 0.70),
            detection.PatternEntry("HIGH_SHORT", detection.re.compile(r"BCD"), 0.90),
            detection.PatternEntry("EQUAL_SHORT", detection.re.compile(r"123"), 0.80),
            detection.PatternEntry("EQUAL_LONG", detection.re.compile(r"1234"), 0.80),
            detection.PatternEntry("EARLY", detection.re.compile(r"XYZ"), 0.75),
            detection.PatternEntry("LATE", detection.re.compile(r"YZA"), 0.75),
        ],
    )

    hits = detection.detect("ABCDE 1234 XYZA")

    assert [hit.kind for hit in hits] == ["HIGH_SHORT", "EQUAL_LONG", "EARLY"]


def test_optional_recognizer_paths_can_use_package_validators() -> None:
    validator = detection.canonical_validator_for("BR_CPF")

    assert validator is detection.valida_cpf
    assert detection.validate_with_canonical("BR_CNPJ", "12.345.678/0001-95") is True
    assert detection.validate_with_canonical("BR_CNPJ", "12.345.678/0001-00") is False


@pytest.mark.parametrize(
    ("validator", "valid_value", "invalid_value"),
    [
        (detection.valida_cpf, "123.456.789-09", "123.456.789-00"),
        (detection.valida_cnpj, "12.345.678/0001-95", "12.345.678/0001-00"),
        (detection.valida_cnh, "12345678900", "12345678999"),
        (detection.valida_titulo_eleitor, "1234 5678 0191", "1234 5678 0199"),
        (detection.valida_pis, "123.45678.90-0", "123.45678.90-9"),
        (detection.valida_cartao_sus, "123 4567 8901 2348", "123 4567 8901 2340"),
    ],
)
def test_package_validators_are_canonical(
    validator: object,
    valid_value: str,
    invalid_value: str,
) -> None:
    assert validator(valid_value) is True
    assert validator(invalid_value) is False
