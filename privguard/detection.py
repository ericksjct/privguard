"""Lightweight stdlib-only sensitive data detection."""

from __future__ import annotations

import base64
import functools
import os
import re
import unicodedata
import urllib.parse
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


# Separators an attacker can inject between an identifier's characters without
# changing how a human reads the value: whitespace/newlines, single/double
# quotes, and plus signs (source-level string concatenation). Stripping them
# reassembles a CPF fragmented across lines (R5), spaced between digits (R6),
# or concatenated in code (R10). Dots/hyphens/slashes are deliberately NOT
# stripped — the formatted regexes depend on them, and their survival is the
# signal that keeps the denoised pass from firing on benign whitespace-joined
# numbers.
_DENOISE_STRIP = frozenset("'\"+")

# A reassembled match is only emitted if it still carries one of these format
# separators. Bare all-digit runs (whitespace-joined phone digits, all of
# BR_CNH, the \d{11}/\d{12}/\d{15} regex branches) are too collision-prone once
# separators are stripped, so they are NOT emitted from the denoised pass.
_DENOISE_SEP_RE = re.compile(r"[.\-/]")

# Denoised-pass patterns: only checksum-bearing kinds, so a reassembled false
# match is bounded by checksum collision (~1/100 for CPF) rather than a loose
# regex. Reused from PATTERNS so the regexes live in exactly one place.
_DENOISED_PATTERNS: list[PatternEntry] = [
    p for p in PATTERNS if p.validator is not None and p.kind in CANONICAL_VALIDATORS
]


def _denoise(norm: str, orig_index: list[int]) -> tuple[str, list[int]]:
    """Strip injectable separators from ``norm``, composing the original map.

    Returns ``(denoised, den_index)`` where ``den_index[j]`` is the offset in the
    ORIGINAL text of denoised char ``j`` (composed through ``orig_index`` from
    the normalization pass). Reassembles fragmented / concatenated identifiers
    so a checksum-gated rescan can catch them, while the map lets surviving hits
    be rebased onto the original span.
    """
    out: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(norm):
        if ch.isspace() or ch in _DENOISE_STRIP:
            continue
        out.append(ch)
        idx.append(orig_index[i])
    return "".join(out), idx


def _denoised_hits(
    denoised: str, den_index: list[int], text: str, existing: list[Hit]
) -> list[Hit]:
    """Checksum-gated hits reassembled from separator-stripped text.

    Only checksum-bearing patterns run; a match is kept only if it still carries
    a format separator AND passes its validator, so false positives stay bounded
    by checksum collision on formatted values (bare-digit reassembly is skipped
    as too collision-prone). Hits are rebased onto the ORIGINAL ``text`` via
    ``den_index`` and deduplicated against ``existing`` primary hits by
    (kind, digits) so a value already caught normally is not double-reported.
    reason_code ``reassembled_checksum_valid`` marks their provenance. When the
    original span cannot be mapped exactly it still spans the contributing
    chars, forcing a block (never a silent allow).
    """
    seen = {(h.kind, _digits(h.value)) for h in existing}
    out: list[Hit] = []
    for entry in _DENOISED_PATTERNS:
        for m in entry.regex.finditer(denoised):
            value = m.group(0)
            if not _DENOISE_SEP_RE.search(value):
                continue  # bare-digit run — collision-prone, not emitted
            if not entry.validator(value):  # type: ignore[misc]  # filtered non-None
                continue
            key = (entry.kind, _digits(value))
            if key in seen:
                continue
            seen.add(key)
            o_start, o_end = den_index[m.start()], den_index[m.end() - 1] + 1
            out.append(Hit(entry.kind, o_start, o_end, text[o_start:o_end],
                           entry.score, "reassembled_checksum_valid"))
    return out


# Encoded-secret pass: only HIGH-confidence recognizable secret kinds are
# rescanned in decoded content. Numeric Brazilian identifiers are deliberately
# EXCLUDED — a short digit run false-positives trivially after decoding an
# arbitrary byte blob, so we never rescan for them. Selected by kind (not by
# score) so the set is explicit and auditable; JWT (0.90) is included because a
# JWT is unambiguously a secret regardless of its score.
_ENCODED_SECRET_KINDS: frozenset[str] = frozenset({
    "API_KEY", "AWS_KEY", "TOKEN", "JWT", "DATABASE_URL",
    "PASSWORD_ASSIGNMENT", "SECRET_ASSIGNMENT", "ENV_VAR_ASSIGNMENT",
})
_ENCODED_SECRET_PATTERNS: list[PatternEntry] = [
    p for p in PATTERNS if p.kind in _ENCODED_SECRET_KINDS
]

# Candidate encoded-blob regexes, conservative min lengths to avoid noise:
# base64 (>=24 body chars), hex (>=16 byte-pairs = 32 chars), and percent/URL
# runs. Short blobs are skipped — the min length is the first FP bound before
# the decode-and-secret-match gate.
_B64_BLOB_RE = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}")
_HEX_BLOB_RE = re.compile(r"(?:[0-9a-fA-F]{2}){16,}")
_URLENC_BLOB_RE = re.compile(r"(?:%[0-9A-Fa-f]{2})+")


def _decode_b64(blob: str) -> str:
    return base64.b64decode(blob, validate=True).decode("utf-8")


def _decode_hex(blob: str) -> str:
    return bytes.fromhex(blob).decode("utf-8")


def _decode_url(blob: str) -> str:
    return urllib.parse.unquote(blob, errors="strict")


# (encoding-name, blob-regex, single-layer decoder). ValueError covers every
# failure mode: binascii.Error (bad base64/hex) and UnicodeDecodeError (non-UTF-8
# result) are both ValueError subclasses, so a failed or non-text decode is
# skipped silently.
_ENCODED_CANDIDATES = (
    ("base64", _B64_BLOB_RE, _decode_b64),
    ("hex", _HEX_BLOB_RE, _decode_hex),
    ("url", _URLENC_BLOB_RE, _decode_url),
)


def _scan_encoded_secrets(text: str) -> list[Hit]:
    """Single-layer decode-and-rescan for secrets hidden in encoding (R7/R8/R9).

    Finds candidate base64/hex/URL-encoded blobs above a minimum length, decodes
    each single-layer, and rescans the decoded text with ONLY the high-confidence
    secret patterns. On a match it emits ONE Hit spanning the ENCODED blob in the
    original text (the point is to block the outbound encoded payload; the exact
    sub-span inside the blob is irrelevant). Ordinary blobs (hashes, IDs, images)
    either fail to decode to UTF-8 or contain no secret, so they produce no hit.
    Decode failures and non-UTF-8 results are skipped silently.
    """
    hits: list[Hit] = []
    for enc, regex, decoder in _ENCODED_CANDIDATES:
        for m in regex.finditer(text):
            try:
                decoded = decoder(m.group(0))
            except ValueError:
                continue  # bad encoding or non-UTF-8 result
            for entry in _ENCODED_SECRET_PATTERNS:
                if entry.regex.search(decoded):
                    hits.append(Hit(
                        entry.kind, m.start(), m.end(), m.group(0),
                        entry.score, f"encoded_secret_{enc}",
                    ))
                    break  # one hit per encoded blob
    return hits


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
    # raw is now on ORIGINAL offsets. Denoised second pass: strip injectable
    # separators and rescan with checksum-bearing patterns only, keeping
    # validator-passers whose value retains a format separator. This reassembles
    # fragmented (R5/R6) and concatenated (R10) formatted identifiers; the
    # checksum + format-separator gate keeps the FP corpus at 0.0. It is a true
    # no-op when nothing was stripped, so benign separator-free text is
    # unaffected. f-string interpolation (R11) reassembles at runtime, not
    # textually, so it stays an accepted limitation.
    denoised, den_index = _denoise(norm, orig_index)
    if len(denoised) < len(norm):
        raw.extend(_denoised_hits(denoised, den_index, text, raw))
    # Encoded-secret pass (R7/R8/R9): decode single-layer base64/hex/URL blobs in
    # the ORIGINAL text and rescan for high-confidence secrets only. Scans the
    # original directly (encoded secrets are ASCII, unaffected by normalization)
    # so the emitted hit spans the original encoded blob. A true no-op cost on
    # text with no qualifying blobs. Merged before the threshold/overlap/sort so
    # a plaintext hit covering the same span wins deterministically.
    raw.extend(_scan_encoded_secrets(text))
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
