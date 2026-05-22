"""Verification script for Task 1 of phase 999.4-01 (CPF leniency mode)."""
from __future__ import annotations

import os

from privguard.detection import (
    _LENIENT_KINDS,
    _LENIENT_SCORES,
    _lenient_default,
    analyze_text,
    detect,
)

# Use a synthetic invalid CPF (wrong checksum: last two digits changed to -45)
INVALID_CPF = "456.789.123-45"
VALID_CPF = "123.456.789-09"
BARE_DIGITS = "45678912345"

os.environ.pop("PII_GUARD_LENIENT", None)

# 1. Strict default (no env var) — must NOT detect invalid CPF
hits = detect(INVALID_CPF)
assert not any(h.kind == "BR_CPF" for h in hits), "FAIL: strict default must block invalid CPF"

# 2. lenient=True — must detect invalid formatted CPF
hits = detect(INVALID_CPF, lenient=True)
assert any(h.kind == "BR_CPF" for h in hits), "FAIL: lenient=True must detect invalid CPF"
cpf = next(h for h in hits if h.kind == "BR_CPF")
assert cpf.score == 0.75, f"FAIL: score must be 0.75, got {cpf.score}"
assert cpf.reason_code == "lenient_pattern", f"FAIL: reason_code must be lenient_pattern, got {cpf.reason_code!r}"

# 3. Bare 11-digit stays strict (format guard)
hits = detect(BARE_DIGITS, lenient=True)
assert not any(h.kind == "BR_CPF" for h in hits), "FAIL: bare 11-digit must stay strict"

# 4. Valid CPF with lenient=True: strict hit wins
hits = detect(VALID_CPF, lenient=True)
cpf = next((h for h in hits if h.kind == "BR_CPF"), None)
assert cpf is not None, "FAIL: valid CPF must still be detected with lenient=True"
assert cpf.score == 0.95, f"FAIL: valid CPF must have score 0.95, got {cpf.score}"
assert cpf.reason_code == "checksum_valid"

# 5. Env var activates leniency
os.environ["PII_GUARD_LENIENT"] = "true"
try:
    hits = detect(INVALID_CPF)
    assert any(h.kind == "BR_CPF" for h in hits), "FAIL: env var must activate leniency"
finally:
    os.environ.pop("PII_GUARD_LENIENT", None)

# 6. analyze_text with lenient=True
report = analyze_text(INVALID_CPF, lenient=True)
assert report.counts == {"BR_CPF": 1}, f"FAIL: expected {{'BR_CPF': 1}}, got {report.counts}"

# 7. Module-level constants exist and have correct types/values
assert isinstance(_LENIENT_KINDS, frozenset)
assert "BR_CPF" in _LENIENT_KINDS
assert _LENIENT_SCORES["BR_CPF"] == 0.75
assert callable(_lenient_default)

print("ALL CHECKS PASSED")
