"""P6 checksum boundary + blacklist edge tests (Phase 10 / TEST-07, handoff Tier 2).

Pins CURRENT behavior of the checksum validators at their boundaries. No
production code is changed; where a validation gap exists it is pinned by a
test carrying a ``# RISCO:`` comment and a matching SUMMARY entry.

Edges (from 10-02-PLAN Task 1):
  - repeated-sequence CPFs/CNPJs (already blacklisted by the validators)
  - DV=0 boundary (the ``d == 10 -> 0`` normalization branch)
  - SUS card definitive (1,2) vs provisional (7,8,9) leading-digit ranges
  - old plate vs Mercosul format ambiguity/overlap

All identifier literals are canonical invalid/synthetic sequences kept inside
this test file; valid values are computed from the checksum algorithm.
"""

from __future__ import annotations

import pytest

from privguard.detection import (
    detect,
    valida_cartao_sus,
    valida_cnpj,
    valida_cpf,
)


# ---------------------------------------------------------------------------
# Repeated-sequence blacklist — already enforced by the validators
# ---------------------------------------------------------------------------

_REPEATED_CPFS = [f"{d}{d}{d}.{d}{d}{d}.{d}{d}{d}-{d}{d}" for d in "0123456789"]
_REPEATED_CNPJS = [f"{d}{d}.{d}{d}{d}.{d}{d}{d}/{d}{d}{d}{d}-{d}{d}" for d in "0123456789"]


@pytest.mark.parametrize("cpf", _REPEATED_CPFS)
def test_repeated_sequence_cpf_rejected(cpf: str) -> None:
    # No blacklist gap: valida_cpf guards ``cpf == cpf[0] * 11`` up front, so
    # repeated-digit sequences that would otherwise satisfy the classic DV
    # algorithm are rejected. Pin that they are neither valid nor detected.
    assert valida_cpf(cpf) is False
    assert not any(h.kind == "BR_CPF" for h in detect(cpf, lenient=False))


@pytest.mark.parametrize("cnpj", _REPEATED_CNPJS)
def test_repeated_sequence_cnpj_rejected(cnpj: str) -> None:
    # CNPJ analog: valida_cnpj guards ``cnpj == cnpj[0] * 14``.
    assert valida_cnpj(cnpj) is False
    assert not any(h.kind == "BR_CNPJ" for h in detect(cnpj, lenient=False))


# ---------------------------------------------------------------------------
# DV=0 boundary — the ``d == 10 -> 0`` normalization branch
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


def _first_cpf_with_check_digit_zero() -> tuple[str, int, int]:
    # Deterministically search the base space for a valid CPF whose check
    # digits exercise the DV=0 branch (dv1 == 0 or dv2 == 0).
    for n in range(1, 1_000_000):
        base9 = [int(c) for c in f"{n:09d}"]
        if len(set(base9)) == 1:
            continue
        d1, d2 = _cpf_check_digits(base9)
        if d1 == 0 or d2 == 0:
            s = "".join(map(str, base9 + [d1, d2]))
            formatted = f"{s[0:3]}.{s[3:6]}.{s[6:9]}-{s[9:11]}"
            return formatted, d1, d2
    raise AssertionError("no DV=0 CPF found in search space")


def test_cpf_dv_zero_boundary_valid_and_detected() -> None:
    formatted, d1, d2 = _first_cpf_with_check_digit_zero()
    assert d1 == 0 or d2 == 0
    assert valida_cpf(formatted) is True
    assert any(h.kind == "BR_CPF" for h in detect(formatted, lenient=False))


# ---------------------------------------------------------------------------
# SUS card leading-digit ranges — enforced (R12 fixed in 11-01)
# ---------------------------------------------------------------------------


def _valid_sus_with_first(first: int) -> str:
    base = [first] + [0] * 12
    for d13 in range(10):
        for d14 in range(10):
            digits = base + [d13, d14]
            if sum(digits[i] * (15 - i) for i in range(15)) % 11 == 0:
                return "".join(map(str, digits))
    raise AssertionError(f"no valid SUS with leading digit {first}")


@pytest.mark.parametrize("first", [1, 2, 7, 8, 9])
def test_sus_valid_leading_digit_ranges_accepted(first: int) -> None:
    # Definitive (1,2) and provisional (7,8,9) leading digits are the assigned
    # CNS ranges; a checksum-valid card in these ranges validates.
    assert valida_cartao_sus(_valid_sus_with_first(first)) is True


@pytest.mark.parametrize("first", [3, 4, 5, 6])
def test_sus_out_of_range_leading_digit_rejected(first: int) -> None:
    # R12 (fixed in 11-01): valida_cartao_sus now enforces the CNS leading-digit
    # ranges. An unassigned range (3-6) is rejected even when the weighted-sum
    # checksum is valid — the leading-digit guard runs before the checksum.
    assert valida_cartao_sus(_valid_sus_with_first(first)) is False


# ---------------------------------------------------------------------------
# Old plate vs Mercosul — deterministic, non-overlapping formats
# ---------------------------------------------------------------------------

_MERCOSUL_PLATE = "ABC1D23"
_OLD_PLATE = "ABC1234"


def test_mercosul_plate_detected_as_mercosul_only() -> None:
    kinds = {h.kind for h in detect(_MERCOSUL_PLATE, lenient=False)}
    assert "BR_PLACA_MERCOSUL" in kinds
    assert "BR_PLACA_OLD" not in kinds


def test_old_plate_detected_as_old_only() -> None:
    kinds = {h.kind for h in detect(_OLD_PLATE, lenient=False)}
    assert "BR_PLACA_OLD" in kinds
    assert "BR_PLACA_MERCOSUL" not in kinds


def test_plate_format_resolution_is_deterministic() -> None:
    # The Mercosul letter-in-position-5 vs old four-trailing-digits formats do
    # not overlap; resolution is stable across repeated runs.
    text = f"placas {_MERCOSUL_PLATE} e {_OLD_PLATE}"
    runs = [tuple((h.kind, h.start, h.end) for h in detect(text, lenient=False)) for _ in range(5)]
    assert len(set(runs)) == 1
