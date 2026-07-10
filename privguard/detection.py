"""Lightweight stdlib-only sensitive data detection."""

from __future__ import annotations

import functools
import os
import re
import unicodedata
from dataclasses import dataclass
from importlib.resources import files as _importlib_files
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
    # CNS leading digit must be an assigned range: 1,2 (definitive) or
    # 7,8,9 (provisional). Reject unassigned ranges (3-6, 0) even with a
    # valid checksum (R12, 11-01).
    if cartao[0] not in "12789":
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
    # D3 (11-01): atomic groups + RFC-5321 length bounds. The quadratic came
    # from O(n) `\b` start positions each scanning O(n) to end; bounding the
    # local part to 64 and domain labels to 63/255 makes every failed start
    # O(1), so a long "[\w.+-]+ with no @" run scans linearly. Atomic groups
    # additionally forbid internal backtracking. Legit emails are unaffected
    # (RFC 5321: local <=64, label <=63).
    PatternEntry("EMAIL", re.compile(r"\b(?>[\w.+-]{1,64})@(?>[\w-]{1,63})\.(?>[\w.-]{2,255})\b"), 0.95),
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


_NAMES_DATA = _importlib_files("privguard") / "data"

_TOKEN_RE = re.compile(r"[^\W\d_]+", re.UNICODE)


@functools.lru_cache(maxsize=1)
def _load_name_sets() -> tuple[frozenset[str], frozenset[str]]:
    first = frozenset(
        n.strip().lower()
        for n in (_NAMES_DATA / "names_first.txt").read_text(encoding="utf-8").splitlines()
        if n.strip() and not n.startswith("#")
    )
    surns = frozenset(
        n.strip().lower()
        for n in (_NAMES_DATA / "names_surnames.txt").read_text(encoding="utf-8").splitlines()
        if n.strip() and not n.startswith("#")
    )
    return first, surns


def _lenient_default() -> bool:
    return os.environ.get("PII_GUARD_LENIENT", "").lower() in ("1", "true", "yes")


def _detect_names_default() -> bool:
    return os.environ.get("PII_GUARD_DETECT_NAMES", "").lower() in ("1", "true", "yes")


def _find_name_hits(text: str) -> list[Hit]:
    first_names, surnames = _load_name_sets()
    tokens: list[tuple[str, int, int]] = [
        (m.group(0).lower(), m.start(), m.end())
        for m in _TOKEN_RE.finditer(text)
    ]
    hits: list[Hit] = []
    i = 0
    while i < len(tokens):
        tok, ts, te = tokens[i]
        is_first = tok in first_names
        is_surn = tok in surnames
        if is_first and i + 1 < len(tokens):
            ntok, nts, nte = tokens[i + 1]
            if ntok in surnames:
                hits.append(Hit("BR_NAME", ts, nte, text[ts:nte], 0.72, "name_fullname"))
                i += 2
                continue
        if is_surn and i + 1 < len(tokens):
            ntok, nts, nte = tokens[i + 1]
            if ntok in first_names:
                hits.append(Hit("BR_NAME", ts, nte, text[ts:nte], 0.72, "name_fullname"))
                i += 2
                continue
        if is_first:
            hits.append(Hit("BR_NAME", ts, te, text[ts:te], 0.58, "name_first"))
        elif is_surn:
            hits.append(Hit("BR_NAME", ts, te, text[ts:te], 0.65, "name_surname"))
        i += 1
    return hits


_LENIENT_KINDS: frozenset[str] = frozenset({"BR_CPF", "BR_CNPJ"})

_LENIENT_SCORES: dict[str, float] = {"BR_CPF": 0.75, "BR_CNPJ": 0.75}


# Confusable digit homoglyphs → ASCII digit. Length-preserving 1:1 map only, so
# the offset index built by _normalize_for_detection stays exact. CONSERVATIVE
# and digits-only: fullwidth ０-９ (U+FF10–FF19) plus the specific Cyrillic
# homoglyphs the adversarial suite injects (Ze→3, O→0). Full NFKC/NFKD is
# deliberately NOT used — it is length-changing (ligatures, compat decomposition)
# and would break the offset map for little threat-model gain. Latin-letter
# homoglyphs are intentionally NOT mapped (would mangle legit text, spike FP).
_CONFUSABLE_DIGITS: dict[int, str] = {
    **{0xFF10 + d: str(d) for d in range(10)},  # fullwidth ０-９
    0x0417: "3",  # CYRILLIC CAPITAL LETTER ZE (З) → 3
    0x041E: "0",  # CYRILLIC CAPITAL LETTER O  (О) → 0
}


def _normalize_for_detection(text: str) -> tuple[str, list[int]]:
    """Offset-safe normalization pass for detection scanning.

    Returns ``(normalized, orig_index)`` where ``orig_index[i]`` is the offset
    in the ORIGINAL ``text`` of normalized char ``i``. Two length-controlled
    transforms only, so the map is exact:

    - confusable digit homoglyphs translated 1:1 (offset preserved), and
    - zero-width/format (Cf) and nonspacing-combining (Mn) chars dropped
      (recorded as nothing).

    Benign input without homoglyphs/Cf/Mn normalizes to itself (identity),
    letting detect() take a fast path that behaves exactly as before.
    """
    out: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(text):
        repl = _CONFUSABLE_DIGITS.get(ord(ch))
        if repl is not None:
            out.append(repl)
            idx.append(i)
            continue
        if unicodedata.category(ch) in ("Cf", "Mn"):
            continue  # drop zero-width / combining marks
        out.append(ch)
        idx.append(i)
    return "".join(out), idx


def _map_hit_to_original(h: Hit, text: str, idx: list[int]) -> Hit:
    """Rebase a Hit's start/end/value from normalized offsets onto ``text``."""
    if h.end <= h.start:  # empty match guard (patterns here never match empty)
        pos = idx[h.start] if h.start < len(idx) else len(text)
        return Hit(h.kind, pos, pos, "", h.score, h.reason_code, h.source)
    orig_start = idx[h.start]
    orig_end = idx[h.end - 1] + 1
    return Hit(h.kind, orig_start, orig_end, text[orig_start:orig_end],
               h.score, h.reason_code, h.source)


def detect(
    text: str,
    min_score: float = 0.6,
    lenient: bool | None = None,
    detect_names: bool | None = None,
) -> list[Hit]:
    use_lenient = _lenient_default() if lenient is None else lenient
    use_detect_names = _detect_names_default() if detect_names is None else detect_names
    # Offset-safe normalization: scan the normalized string so homoglyph /
    # zero-width / combining evasions (R2/R3/R4) are caught, then rebase every
    # Hit onto the ORIGINAL text so masking/diagnostics offsets stay correct.
    # Identity fast-path: benign input normalizes to itself -> no remap, no
    # perf cost, byte-for-byte identical behavior to before.
    norm, orig_index = _normalize_for_detection(text)
    identity = norm == text
    scan = text if identity else norm
    raw: list[Hit] = []
    for entry in PATTERNS:
        for m in entry.regex.finditer(scan):
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

    if use_detect_names:
        raw.extend(_find_name_hits(scan))
    if not identity:
        raw = [_map_hit_to_original(h, text, orig_index) for h in raw]
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
    detect_names: bool | None = None,
) -> DetectionReport:
    hits = tuple(detect(text, min_score=min_score, lenient=lenient, detect_names=detect_names))
    counts: dict[str, int] = {}
    for hit in hits:
        counts[hit.kind] = counts.get(hit.kind, 0) + 1
    return DetectionReport(hits=hits, counts=counts)
