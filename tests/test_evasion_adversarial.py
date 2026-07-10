"""P2 adversarial evasion suite (Phase 10 / TEST-07, handoff Tier 1).

One test per evasion vector, each pinning CURRENT detect() behavior with an
explicit assertion. Vectors that pass through undetected carry a ``# RISCO:``
comment and a matching entry in the plan SUMMARY RISCO list — never silenced,
never xfail-and-forget. No production code is changed here (handoff rule).

Fixtures are the canonical synthetic constants (RAW_CPF, SECRET_LOOKING) from
test_claude_hooks. Hostile/evasion variants are derived programmatically at
runtime (translate tables, join with zero-width chars, base64/hex/url encode);
no new realistic Brazilian PII literal is introduced.

Behavior snapshot at authoring time (min_score=0.7):
  DETECTED     : fullwidth_digits, code_fence, markdown_link, code_comment
  PASS-THROUGH : cyrillic_homoglyph, zero_width, combining_chars,
                 fragmented_lines, whitespace_injected, b64_secret,
                 hex_secret, urlenc_secret, code_concat, fstring_concat

Update (11-02): the offset-safe normalization pass in detect() now closes the
cyrillic_homoglyph (R2), zero_width (R3), and combining_chars (R4) vectors —
these are asserted DETECTED below.

Update (11-03): the checksum-gated denoised rescan closes the formatted
fragmentation/concatenation vectors — fragmented_lines (R5), whitespace_injected
(R6), and code_concat (R10) are now DETECTED. fstring_concat (R11) stays an
ACCEPTED LIMITATION (runtime f-string interpolation is not textual). The
encoding vectors (b64/hex/urlenc secrets) remain pinned as PASS-THROUGH.
"""

from __future__ import annotations

import base64

from privguard.detection import detect

from test_claude_hooks import RAW_CPF, SECRET_LOOKING

_THRESHOLD = 0.7

# Fullwidth digit translation table (ASCII 0-9 → U+FF10..U+FF19).
_FULLWIDTH = {ord(str(d)): chr(0xFF10 + d) for d in range(10)}
_ZERO_WIDTH = "​"  # zero-width space
_COMBINING_ACUTE = "́"


def _has_cpf(text: str) -> bool:
    return any(h.kind == "BR_CPF" for h in detect(text, min_score=_THRESHOLD))


def _any_hit(text: str) -> bool:
    return bool(detect(text, min_score=_THRESHOLD))


# ---------------------------------------------------------------------------
# Unicode obfuscation
# ---------------------------------------------------------------------------


def test_fullwidth_digit_cpf_is_detected() -> None:
    # Fullwidth digits: \d in the regex matches Unicode decimal digits, so a
    # fullwidth-digit CPF is still caught. Current behavior = DETECTED.
    text = RAW_CPF.translate(_FULLWIDTH)
    assert _has_cpf(text)


def test_cyrillic_homoglyph_cpf_is_detected() -> None:
    # RISCO fixed in 11-02: the offset-safe _CONFUSABLE_DIGITS map translates
    # the Cyrillic homoglyph digits (З→3, О→0) back to ASCII before scanning,
    # so the CPF is now DETECTED.
    text = RAW_CPF.replace("3", "З").replace("0", "О")
    assert _has_cpf(text)


def test_zero_width_chars_inside_cpf_is_detected() -> None:
    # RISCO fixed in 11-02: normalization drops zero-width/format (Cf) chars,
    # so the interleaved-ZWSP CPF is now DETECTED (offsets still index the
    # original, ZWSP-laden span).
    text = _ZERO_WIDTH.join(RAW_CPF)
    assert _has_cpf(text)


def test_combining_chars_on_cpf_digits_is_detected() -> None:
    # RISCO fixed in 11-02: normalization drops nonspacing-combining (Mn)
    # marks, so the accented-digit CPF is now DETECTED.
    text = "".join(c + _COMBINING_ACUTE if c.isdigit() else c for c in RAW_CPF)
    assert _has_cpf(text)


# ---------------------------------------------------------------------------
# Fragmentation
# ---------------------------------------------------------------------------


def test_cpf_fragmented_across_lines_is_detected() -> None:
    # RISCO fixed in 11-03: the checksum-gated denoised pass strips the injected
    # newline, reassembles the formatted CPF, and the checksum passes — DETECTED
    # (reason_code reassembled_checksum_valid).
    text = RAW_CPF[:8] + "\n" + RAW_CPF[8:]
    assert _has_cpf(text)


def test_whitespace_injected_between_digits_is_detected() -> None:
    # RISCO fixed in 11-03: the denoised pass strips the injected spaces; the
    # formatted CPF (dots/hyphen survive) reassembles and passes checksum —
    # DETECTED.
    text = " ".join(RAW_CPF)
    assert _has_cpf(text)


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------


def test_base64_encoded_secret_passes_through() -> None:
    # RISCO: a base64-encoded secret is opaque to the plaintext token regexes;
    # passes through. Documented, not fixed (no decode-and-rescan stage exists).
    text = "payload=" + base64.b64encode(SECRET_LOOKING.encode()).decode()
    assert not _any_hit(text)


def test_hex_encoded_secret_passes_through() -> None:
    # RISCO: hex-encoded secret passes through undetected. Documented, not fixed.
    text = "payload=" + SECRET_LOOKING.encode().hex()
    assert not _any_hit(text)


def test_url_encoded_secret_passes_through() -> None:
    # RISCO: percent-encoded secret passes through undetected. Documented, not fixed.
    text = "payload=" + "".join(f"%{b:02X}" for b in SECRET_LOOKING.encode())
    assert not _any_hit(text)


# ---------------------------------------------------------------------------
# Code concatenation
# ---------------------------------------------------------------------------


def test_string_concatenation_cpf_is_detected() -> None:
    # RISCO fixed in 11-03: the denoised pass strips quotes and the plus sign,
    # reassembling `"123.456" + ".789-09"` into the formatted CPF, which passes
    # checksum — DETECTED.
    text = 'cpf = "' + RAW_CPF[:7] + '" + "' + RAW_CPF[7:] + '"'
    assert _has_cpf(text)


def test_fstring_concatenation_cpf_passes_through() -> None:
    # RISCO ACCEPTED LIMITATION (11-03): the f-string reassembles the CPF at
    # RUNTIME via `{p}` interpolation, not textually. Stripping separators
    # leaves the literal `{p}` between the fragments, so the value never
    # reassembles in static text. Fixing this would require evaluating code, out
    # of scope for a static scanner; left pinned as pass-through, documented in
    # the 11-03 SUMMARY.
    text = 'p = "' + RAW_CPF[:7] + '"\ncpf = f"{p}' + RAW_CPF[7:] + '"'
    assert not _has_cpf(text)


# ---------------------------------------------------------------------------
# PII embedded in markup — these ARE detected (regex is context-blind)
# ---------------------------------------------------------------------------


def test_cpf_inside_code_fence_is_detected() -> None:
    # A well-formed CPF inside a markdown code fence is still matched; the
    # regex does not honor fence boundaries. Current behavior = DETECTED.
    text = "```python\ncpf = \"" + RAW_CPF + "\"\n```"
    assert _has_cpf(text)


def test_cpf_inside_markdown_link_is_detected() -> None:
    # A CPF embedded in a markdown link target is still matched. DETECTED.
    text = "[cadastro](https://example.invalid/lookup?cpf=" + RAW_CPF + ")"
    assert _has_cpf(text)


def test_cpf_inside_code_comment_is_detected() -> None:
    # A CPF in a code comment is still matched (context-blind regex). DETECTED.
    text = "# valor de teste: " + RAW_CPF
    assert _has_cpf(text)
