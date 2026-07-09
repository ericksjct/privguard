"""P5 property-based validator + masking tests (Phase 10 / TEST-07, handoff Tier 2).

Hypothesis properties over the CPF/CNPJ validators and the masking pipeline.
Tests pin CURRENT behavior; no production code is changed here. Synthetic
CPF/CNPJ values are GENERATED with correct check digits inside the strategies
(the handoff explicitly allows computing checksums programmatically) — no new
Brazilian PII literal is invented.

Properties (from 10-02-PLAN Task 0):
  (a) generated checksum-valid CPF/CNPJ are always detected in strict mode
  (b) random 11-digit strings with invalid checksums are never detected as CPF
  (c) mask_text idempotence: masking already-masked text changes nothing
  (d) lenient detection is a superset of strict (never masks fewer positions)

A fixed, derandomized Hypothesis profile keeps CI stable and fast.
"""

from __future__ import annotations

from hypothesis import assume, given, settings, strategies as st

from privguard.detection import detect, valida_cnpj, valida_cpf
from privguard.masking import mask_text

# ---------------------------------------------------------------------------
# Deterministic, fast Hypothesis profile (registered + used explicitly)
# ---------------------------------------------------------------------------

FAST = settings(max_examples=150, deadline=None, derandomize=True)


# ---------------------------------------------------------------------------
# Synthetic-value generators (compute the check digits — never hardcode PII)
# ---------------------------------------------------------------------------


def _cpf_check_digits(base9: list[int]) -> tuple[int, int]:
    s = sum(base9[i] * (10 - i) for i in range(9))
    d1 = (s * 10) % 11
    d1 = 0 if d1 == 10 else d1
    base10 = base9 + [d1]
    s = sum(base10[i] * (11 - i) for i in range(10))
    d2 = (s * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return d1, d2


_CNPJ_W1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
_CNPJ_W2 = [6] + _CNPJ_W1


def _cnpj_check_digits(base12: list[int]) -> tuple[int, int]:
    s = sum(base12[i] * _CNPJ_W1[i] for i in range(12))
    d1 = s % 11
    d1 = 0 if d1 < 2 else 11 - d1
    base13 = base12 + [d1]
    s = sum(base13[i] * _CNPJ_W2[i] for i in range(13))
    d2 = s % 11
    d2 = 0 if d2 < 2 else 11 - d2
    return d1, d2


def _format_cpf(d: list[int]) -> str:
    s = "".join(map(str, d))
    return f"{s[0:3]}.{s[3:6]}.{s[6:9]}-{s[9:11]}"


def _format_cnpj(d: list[int]) -> str:
    s = "".join(map(str, d))
    return f"{s[0:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:14]}"


_digit9 = st.lists(st.integers(0, 9), min_size=9, max_size=9)
_digit12 = st.lists(st.integers(0, 9), min_size=12, max_size=12)
_digit11 = st.lists(st.integers(0, 9), min_size=11, max_size=11)


# ---------------------------------------------------------------------------
# (a) valid CPF/CNPJ are always detected in strict mode
# ---------------------------------------------------------------------------


@given(base9=_digit9)
@FAST
def test_valid_cpf_always_detected_strict(base9: list[int]) -> None:
    # Repeated-digit sequences are rejected by design (see test_checksum_edges);
    # exclude them so this property is about genuine checksum-valid documents.
    assume(len(set(base9)) > 1)
    d1, d2 = _cpf_check_digits(base9)
    full = base9 + [d1, d2]
    assume(len(set(full)) > 1)
    text = f"meu documento e {_format_cpf(full)} obrigado"
    hits = detect(text, lenient=False)
    assert any(h.kind == "BR_CPF" for h in hits), full


@given(base12=_digit12)
@FAST
def test_valid_cnpj_always_detected_strict(base12: list[int]) -> None:
    assume(len(set(base12)) > 1)
    d1, d2 = _cnpj_check_digits(base12)
    full = base12 + [d1, d2]
    assume(len(set(full)) > 1)
    text = f"empresa {_format_cnpj(full)} registrada"
    hits = detect(text, lenient=False)
    assert any(h.kind == "BR_CNPJ" for h in hits), full


# ---------------------------------------------------------------------------
# (b) invalid-checksum 11-digit strings are never detected as CPF (strict)
# ---------------------------------------------------------------------------


@given(digits=_digit11)
@FAST
def test_invalid_cpf_never_detected_strict(digits: list[int]) -> None:
    formatted = _format_cpf(digits)
    assume(not valida_cpf(formatted))
    hits = detect(formatted, lenient=False)
    assert not any(h.kind == "BR_CPF" for h in hits), formatted


# ---------------------------------------------------------------------------
# (c) mask_text idempotence
# ---------------------------------------------------------------------------

_valid_cpf_text = st.builds(lambda b: _format_cpf(b + list(_cpf_check_digits(b))), _digit9)
_valid_cnpj_text = st.builds(lambda b: _format_cnpj(b + list(_cnpj_check_digits(b))), _digit12)
_benign = st.sampled_from([
    "relatorio mensal", "codigo revisado", "versao 1.2.3", "issue ABC-123",
    "data 2024-01-15", "texto publico", "sem dados", "obrigado equipe",
])
_email = st.sampled_from(["dev@example.com", "qa@example.org", "ops@example.net"])

_token = st.one_of(_valid_cpf_text, _valid_cnpj_text, _benign, _email)


@given(tokens=st.lists(_token, min_size=1, max_size=8))
@FAST
def test_mask_text_is_idempotent(tokens: list[str]) -> None:
    text = " ".join(tokens)
    once = mask_text(text).text
    twice = mask_text(once).text
    assert twice == once


# ---------------------------------------------------------------------------
# (d) lenient detection is a superset of strict (never masks fewer positions)
# ---------------------------------------------------------------------------


def _covered(text: str, lenient: bool) -> set[int]:
    covered: set[int] = set()
    for h in detect(text, lenient=lenient):
        covered.update(range(h.start, h.end))
    return covered


@given(tokens=st.lists(_token, min_size=1, max_size=8))
@FAST
def test_lenient_is_superset_of_strict(tokens: list[str]) -> None:
    text = " ".join(tokens)
    strict = _covered(text, lenient=False)
    lenient = _covered(text, lenient=True)
    assert strict <= lenient
