"""Verification script for Task 2 of phase 999.4-01 (mask_text lenient parameter)."""
from __future__ import annotations

import os

from privguard.masking import mask_text

INVALID_CPF = "456.789.123-45"
VALID_CPF_TEXT = "CPF 123.456.789-09"

os.environ.pop("PII_GUARD_LENIENT", None)

# 1. Lenient mask of invalid-checksum CPF
result = mask_text(INVALID_CPF, lenient=True)
assert result.verified is True, f"FAIL: verified must be True, got {result.verified}"
assert "<BR_CPF>" in result.text, f"FAIL: <BR_CPF> not in masked text: {result.text}"
assert INVALID_CPF not in result.text, "FAIL: raw value must not remain"

# 2. Strict default: invalid CPF passes through unchanged (not masked)
result = mask_text(INVALID_CPF)
assert INVALID_CPF in result.text, "FAIL: strict default must leave invalid CPF unmasked"

# 3. Backward compat: existing valid CPF still masked when no lenient param
result = mask_text(VALID_CPF_TEXT)
assert "<BR_CPF>" in result.text
assert result.verified is True

print("ALL CHECKS PASSED")
