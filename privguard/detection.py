"""Lightweight stdlib-only sensitive data detection."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Hit:
    kind: str
    start: int
    end: int
    value: str
    score: float
    reason_code: str = "pattern_match"
    source: str = "stdlib"


@dataclass(frozen=True)
class DetectionReport:
    hits: tuple[Hit, ...]
    counts: dict[str, int]


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def valida_cpf(cpf: str) -> bool:
    cpf = _digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        s = sum(int(cpf[n]) * ((i + 1) - n) for n in range(i))
        d = (s * 10) % 11
        d = 0 if d == 10 else d
        if d != int(cpf[i]):
            return False
    return True


def valida_cnpj(cnpj: str) -> bool:
    cnpj = _digits(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, pos in ((pesos1, 12), (pesos2, 13)):
        s = sum(int(cnpj[i]) * pesos[i] for i in range(len(pesos)))
        d = s % 11
        d = 0 if d < 2 else 11 - d
        if d != int(cnpj[pos]):
            return False
    return True


def valida_luhn(num: str) -> bool:
    n = _digits(num)
    if len(n) < 13 or len(n) > 19:
        return False
    s = 0
    par = False
    for d in reversed(n):
        x = int(d)
        if par:
            x *= 2
            if x > 9:
                x -= 9
        s += x
        par = not par
    return s % 10 == 0


def valida_cnh(cnh: str) -> bool:
    cnh = _digits(cnh)
    if len(cnh) != 11 or cnh == cnh[0] * 11:
        return False
    dsc = 0
    s = 0
    for i, peso in enumerate(range(9, 0, -1)):
        s += int(cnh[i]) * peso
    dv1 = s % 11
    if dv1 >= 10:
        dv1 = 0
        dsc = 2
    s = 0
    for i, peso in enumerate(range(1, 10)):
        s += int(cnh[i]) * peso
    dv2 = (s % 11) - dsc
    if dv2 < 0:
        dv2 += 11
    if dv2 >= 10:
        dv2 = 0
    return dv1 == int(cnh[9]) and dv2 == int(cnh[10])


def valida_titulo_eleitor(titulo: str) -> bool:
    titulo = _digits(titulo)
    if len(titulo) < 10 or len(titulo) > 12:
        return False
    titulo = titulo.zfill(12)
    uf = int(titulo[8:10])
    if uf < 1 or uf > 28:
        return False
    s1 = sum(int(titulo[i]) * (i + 2) for i in range(8))
    dv1 = s1 % 11
    if dv1 == 10:
        dv1 = 0
    s2 = int(titulo[8]) * 7 + int(titulo[9]) * 8 + dv1 * 9
    dv2 = s2 % 11
    if dv2 == 10:
        dv2 = 0
    return dv1 == int(titulo[10]) and dv2 == int(titulo[11])


def valida_pis(pis: str) -> bool:
    pis = _digits(pis)
    if len(pis) != 11 or pis == pis[0] * 11:
        return False
    pesos = [3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s = sum(int(pis[i]) * pesos[i] for i in range(10))
    d = 11 - (s % 11)
    if d >= 10:
        d = 0
    return d == int(pis[10])


def valida_cartao_sus(cartao: str) -> bool:
    cartao = _digits(cartao)
    if len(cartao) != 15:
        return False
    s = sum(int(cartao[i]) * (15 - i) for i in range(15))
    return s % 11 == 0


CANONICAL_VALIDATORS: dict[str, Callable[[str], bool]] = {
    "BR_CPF": valida_cpf,
    "BR_CNPJ": valida_cnpj,
    "BR_CNH": valida_cnh,
    "BR_TITULO_ELEITOR": valida_titulo_eleitor,
    "BR_PIS_PASEP": valida_pis,
    "BR_CARTAO_SUS": valida_cartao_sus,
    "CREDIT_CARD": valida_luhn,
}


def canonical_validator_for(kind: str) -> Callable[[str], bool] | None:
    return CANONICAL_VALIDATORS.get(kind)


def validate_with_canonical(kind: str, value: str) -> bool:
    validator = canonical_validator_for(kind)
    return validator(value) if validator else True


@dataclass(frozen=True)
class PatternEntry:
    kind: str
    regex: re.Pattern[str]
    score: float
    validator: Callable[[str], bool] | None = None
    reason_code: str = "pattern_match"


PATTERNS: list[PatternEntry] = [
    PatternEntry("BR_CNPJ", re.compile(r"\b(?:\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14})\b"), 0.95, valida_cnpj, "checksum_valid"),
    PatternEntry("BR_CPF", re.compile(r"\b(?:\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})\b"), 0.95, valida_cpf, "checksum_valid"),
    PatternEntry("BR_CNH", re.compile(r"\b\d{11}\b"), 0.93, valida_cnh, "checksum_valid"),
    PatternEntry("BR_TITULO_ELEITOR", re.compile(r"\b(?:\d{4}\s\d{4}\s\d{4}|\d{12})\b"), 0.92, valida_titulo_eleitor, "checksum_valid"),
    PatternEntry("BR_PIS_PASEP", re.compile(r"\b(?:\d{3}\.\d{5}\.\d{2}-\d|\d{11})\b"), 0.91, valida_pis, "checksum_valid"),
    PatternEntry(
        "BR_BOLETO",
        re.compile(
            r"(?:"
            r"\b\d{44,50}\b"
            r"|\b\d{5}\.\d{5}\s\d{5}\.\d{6}\s\d{5}\.\d{6}\s\d\s\d{14}\b"
            r"|\b\d{11}-\d(?:\s\d{11}-\d){3}\b"
            r")"
        ),
        0.92,
        None,
        "barcode_boleto",
    ),
    PatternEntry("BR_CARTAO_SUS", re.compile(r"\b(?:\d{3}\s\d{4}\s\d{4}\s\d{4}|\d{15})\b"), 0.94, valida_cartao_sus, "checksum_valid"),
    PatternEntry("CREDIT_CARD", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), 0.85, valida_luhn, "checksum_valid"),
    PatternEntry("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b"), 0.95),
    PatternEntry("IBAN", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{12,30}\b"), 0.90),
    PatternEntry("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:\s[A-Z0-9]{4}){3,}(?:\s[A-Z0-9]{1,4})?\b"), 0.90),
    PatternEntry("BR_RG", re.compile(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dXx]\b"), 0.78),
    PatternEntry("BR_PHONE", re.compile(r"(?<!\d)(?:\+55\s?)?\(?\d{2}\)?\s?(?:9[\s-]?\d{4}|[2-5]\d{3})[\s-]?\d{4}\b"), 0.76),
    PatternEntry("BR_CEP", re.compile(r"\b(?:\d{2}\.\d{3}|\d{5})-?\d{3}\b"), 0.72),
    PatternEntry("BR_PLACA_MERCOSUL", re.compile(r"\b[A-Z]{3}\d[A-Z]\d{2}\b"), 0.85),
    PatternEntry("BR_PLACA_OLD", re.compile(r"\b[A-Z]{3}-?\d{4}(?![-\d])\b"), 0.80),
    PatternEntry("DATABASE_URL", re.compile(r"\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis)://[^\s'\"<>]+", re.IGNORECASE), 0.99, None, "database_url"),
    PatternEntry("PASSWORD_ASSIGNMENT", re.compile(r"\b(?:password|passwd|pwd|senha)\s*=\s*['\"]?[^'\"\s;]+", re.IGNORECASE), 0.99, None, "secret_assignment"),
    PatternEntry("API_KEY", re.compile(r"\b(?:sk-(?:ant-)?[\w-]{20,}|sk_(?:live|test)_[\w-]+)\b"), 0.99, None, "secret_token"),
    PatternEntry("AWS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), 0.99, None, "secret_token"),
    PatternEntry("TOKEN", re.compile(r"\b(?:(?:ghp|github_pat|glpat)_[A-Za-z0-9_=-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,})\b"), 0.99, None, "secret_token"),
    PatternEntry("SECRET_ASSIGNMENT", re.compile(r"\b(?:api[_-]?key|secret|token|password|passwd|pwd|senha)\s*[:=]\s*['\"]?[^'\"\s;]+", re.IGNORECASE), 0.98, None, "secret_assignment"),
    PatternEntry("ENV_VAR_ASSIGNMENT", re.compile(r"\b[A-Z][A-Z0-9_]*(?:SECRET|TOKEN|KEY|PASSWORD|PASS|PWD)[A-Z0-9_]*\s*=\s*['\"]?[^'\"\s;]+"), 0.96, None, "secret_assignment"),
    PatternEntry("JWT", re.compile(r"\beyJ[\w-]+\.[\w-]+\.[\w-]+\b"), 0.90, None, "secret_token"),
    PatternEntry("BR_BANK_AGENCY", re.compile(r"(?:Ag[eê]ncia|Ag\.?)\s*(?:n[oºª°]\.?\s*)?\d{4,5}(?:-\d)?\b", re.IGNORECASE), 0.80),
    PatternEntry("BR_BANK_ACCOUNT", re.compile(r"(?:Conta\s+(?:Corrente|Poupan[çc]a)|C(?:\.?\s*/?\s*\.?C|C))\s*(?:n[oºª°]\.?\s*)?\d{4,7}-?\d?\b", re.IGNORECASE), 0.80),
    PatternEntry("BR_ADDRESS", re.compile(
        r"(?:Rua|R\.|Avenida|Av\.?|Alameda|Al\.|Travessa|Trav\.|Estrada|Est\.|"
        r"Rodovia|Rod\.|Pra[çc]a|Pç\.|Largo|Vila|Vl\.)"
        r"\s+(?:[A-Za-zÀ-ÿ'][A-Za-zÀ-ÿ'\.\s]{1,45}?)(?:\s*,\s*|\s+)(?:n[oº°]\.?\s*)?\d[\d\.]*",
        re.IGNORECASE,
    ), 0.62),
    PatternEntry("IP_PRIVADO", re.compile(r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b"), 0.70),
    PatternEntry("IP_PUBLICO", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), 0.65),
]


def _lenient_default() -> bool:
    return os.environ.get("PII_GUARD_LENIENT", "").lower() in ("1", "true", "yes")


_LENIENT_KINDS: frozenset[str] = frozenset({"BR_CPF", "BR_CNPJ"})

_LENIENT_SCORES: dict[str, float] = {"BR_CPF": 0.75, "BR_CNPJ": 0.75}


def detect(
    text: str,
    min_score: float = 0.6,
    lenient: bool | None = None,
) -> list[Hit]:
    use_lenient = _lenient_default() if lenient is None else lenient
    raw: list[Hit] = []
    for entry in PATTERNS:
        for m in entry.regex.finditer(text):
            value = m.group(0)
            # Skip hits whose checksum fails entirely — do NOT emit a
            # downgraded score that would shadow other kinds covering the
            # same span (e.g. BR_CPF failing checksum would block BR_CNH
            # and BR_PIS_PASEP from the same 11-digit value).
            if entry.validator and not entry.validator(value):
                if use_lenient and entry.kind in _LENIENT_KINDS:
                    # Formatted-only guard: bare 11-digit CPF must stay strict
                    # to avoid shadowing BR_CNH and BR_PIS_PASEP on same span.
                    if "." in value and "-" in value:
                        raw.append(Hit(
                            entry.kind, m.start(), m.end(), value,
                            _LENIENT_SCORES[entry.kind],
                            "lenient_pattern",
                        ))
                continue
            raw.append(Hit(entry.kind, m.start(), m.end(), value,
                           entry.score, entry.reason_code))

    raw = [h for h in raw if h.score >= min_score]
    raw.sort(key=lambda h: (-h.score, -(h.end - h.start), h.start))
    kept: list[Hit] = []
    for h in raw:
        if not any(not (h.end <= k.start or h.start >= k.end) for k in kept):
            kept.append(h)
    kept.sort(key=lambda h: h.start)
    return kept


def analyze_text(
    text: str,
    min_score: float = 0.6,
    lenient: bool | None = None,
) -> DetectionReport:
    hits = tuple(detect(text, min_score=min_score, lenient=lenient))
    counts: dict[str, int] = {}
    for hit in hits:
        counts[hit.kind] = counts.get(hit.kind, 0) + 1
    return DetectionReport(hits=hits, counts=counts)
