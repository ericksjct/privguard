"""Compatibility shim for legacy imports from hooks._pii_core."""

from privguard.detection import Hit, detect, valida_cpf, valida_cnpj, valida_luhn
from privguard.masking import redact

__all__ = [
    "Hit",
    "detect",
    "valida_cpf",
    "valida_cnpj",
    "valida_luhn",
    "redact",
]
