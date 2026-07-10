---
phase: 11-fail-closed-hardening
plan: 04
subsystem: security-core
tags: [evasion-hardening, encoded-secrets, decode-and-rescan, base64, hex, url-encoding, phase-close]

requires:
  - phase: 11-fail-closed-hardening
    provides: shared choke point detect() with normalization + denoised passes (11-01/02/03)
provides:
  - Single-layer decode-and-rescan stage in detect() (base64/hex/URL blobs → high-confidence secret rescan → hit on the encoded blob)
  - Encoded-secret evasion vectors R7 (base64), R8 (hex), R9 (URL) closed
  - reason_code encoded_secret_<enc> for decode-and-rescan hits
  - Phase-close: every phase-10 finding R1-R12 / D1-D4 carries a definitive disposition
affects: [evasion-hardening-thread]

tech-stack:
  added: []
  patterns:
    - "Decode-and-rescan scans the ORIGINAL text (encoded blobs are ASCII, unaffected by normalization) so the emitted hit spans the original encoded blob with no offset remap"
    - "Recovered content is rescanned with the high-confidence secret patterns ONLY (_ENCODED_SECRET_KINDS); numeric BR identifiers are excluded because a short digit run collides trivially after arbitrary decode"
    - "FP bounded by three gates in series: min blob length → decode-to-valid-UTF-8 → high-confidence secret match. Ordinary base64/hex (hashes, IDs, images, benign text) fails one of the three"

key-files:
  created:
    - .planning/phases/11-fail-closed-hardening/11-04-SUMMARY.md
  modified:
    - privguard/detection.py
    - tests/test_evasion_adversarial.py
    - tests/test_fail_closed_injection.py

key-decisions:
  - "Secret kinds selected by explicit name set (_ENCODED_SECRET_KINDS), not by score threshold — auditable, and JWT (0.90) is included because a JWT is unambiguously a secret regardless of its score"
  - "Scan the ORIGINAL text for encoded blobs, not the normalized string — encoded secrets are ASCII so normalization is irrelevant, and native offsets avoid the remap machinery"
  - "One hit per encoded blob (break after first secret match) — the goal is to block the outbound payload, not enumerate every pattern inside it"
  - "ValueError alone is caught for decode failures — binascii.Error and UnicodeDecodeError are both ValueError subclasses, so a bad blob or non-UTF-8 result is skipped silently"
  - "D1 (hang watchdog) re-documented as OUT OF SCOPE for v1 (external Claude Code hook-timeout dependency); its test comment was upgraded from a dangling 'candidate fix thread' to a definitive disposition"

requirements-completed: [DET-07]

metrics:
  duration: 9min
  completed: 2026-07-10
  tasks: 3
  files_modified: 3

status: complete
---

# Phase 11 Plan 04: Encoded-Secret Decode-and-Rescan + Phase Close Summary

**detect() now runs a single-layer decode-and-rescan stage — it finds base64/hex/URL-encoded blobs above a minimum length in the original text, reverses the encoding one layer, and rescans the recovered text with the high-confidence secret patterns only; on a match it emits one hit spanning the encoded blob, closing the encoded-secret vectors R7/R8/R9 while the FP corpus stays at 0.0 (a benign blob that decodes to non-secret text produces no hit). This is the last plan of the phase, so the SUMMARY carries the final phase-wide disposition table: every phase-10 finding R1-R12 / D1-D4 is now fixed-and-asserted, an accepted limitation, or explicitly out-of-scope.**

## What Changed

### Task 1 — decode-and-rescan stage (`detection.py`) — commit `e0fa936`
Added `_ENCODED_SECRET_KINDS` (the high-confidence secret kind set), `_ENCODED_SECRET_PATTERNS` (the matching subset of `PATTERNS`), the three blob regexes (`_B64_BLOB_RE`, `_HEX_BLOB_RE`, `_URLENC_BLOB_RE`), the three single-layer decoders, and `_scan_encoded_secrets(text)`.

- For each candidate blob: decode single-layer (`base64.b64decode(validate=True)`, `bytes.fromhex`, `urllib.parse.unquote(errors="strict")`), each wrapped so a `ValueError` (bad encoding OR non-UTF-8 result) is skipped silently.
- The recovered string is rescanned with `_ENCODED_SECRET_PATTERNS` only. On the first secret match, one `Hit` is emitted spanning the ENCODED blob in the original text with `reason_code="encoded_secret_<enc>"`; then it breaks to the next blob.
- Wired into `detect()` after the denoised pass and before the threshold/overlap/sort, scanning the ORIGINAL `text` directly (encoded secrets are ASCII, so normalization is irrelevant and native offsets need no remap). No-op cost on text with no qualifying blobs.

### Task 2 — flip R7/R8/R9 + benign FP guard (`test_evasion_adversarial.py`) — commit `82a7f4b`
Re-asserted R7 (base64), R8 (hex), R9 (URL) as DETECTED with `# RISCO fixed in 11-04` comments; added `test_base64_of_benign_text_produces_no_hit` (a blob decoding to non-secret UTF-8 must produce no hit — the decode-succeeds-but-no-secret path); added an "Update (11-04)" note to the module docstring recording the closed vectors and residual limitations.

### Task 3 — phase-close disposition (`test_fail_closed_injection.py`) — commit `33e3830`
Rewrote the slow-detector test comment into a definitive D1 disposition (OUT OF SCOPE for v1; internal watchdog is the v2 upgrade path) replacing the dangling "candidate fix thread" wording. Reconciliation only, no production code.

## Final Phase-Wide Disposition — R1-R12 / D1-D4

| Finding | Vector | Disposition | Plan | Asserted in |
|---------|--------|-------------|------|-------------|
| R1 | detector exception → exit 1 → fail-open | **FIXED** — exit 2 `detector_error` wrapper on both hooks | 11-01 | `test_fail_closed_injection.py` |
| R2 | Cyrillic homoglyph digits (З→3, О→0) | **FIXED** — `_CONFUSABLE_DIGITS` 1:1 map | 11-02 | `test_evasion_adversarial.py` |
| R3 | zero-width / format (Cf) chars in CPF | **FIXED** — normalization drops Cf | 11-02 | `test_evasion_adversarial.py` |
| R4 | combining (Mn) marks on digits | **FIXED** — normalization drops Mn | 11-02 | `test_evasion_adversarial.py` |
| R5 | CPF fragmented across lines | **FIXED** — checksum-gated denoised pass | 11-03 | `test_evasion_adversarial.py` |
| R6 | whitespace injected between digits | **FIXED** — denoised pass | 11-03 | `test_evasion_adversarial.py` |
| R7 | base64-encoded secret | **FIXED** — decode-and-rescan | 11-04 | `test_evasion_adversarial.py` |
| R8 | hex-encoded secret | **FIXED** — decode-and-rescan | 11-04 | `test_evasion_adversarial.py` |
| R9 | URL/percent-encoded secret | **FIXED** — decode-and-rescan | 11-04 | `test_evasion_adversarial.py` |
| R10 | source string concatenation CPF | **FIXED** — denoised pass strips quotes/plus | 11-03 | `test_evasion_adversarial.py` |
| R11 | f-string interpolation CPF | **ACCEPTED LIMITATION** — reassembles at runtime, not textually | 11-03 | `test_evasion_adversarial.py` |
| R12 | SUS accepts unassigned CNS leading-digit range (3-6) | **FIXED** — leading-digit range enforcement | 11-01 | `test_checksum_edges.py` |
| D1 | no internal hang/timeout watchdog | **OUT OF SCOPE (v1)** — depends on Claude Code's external hook timeout (their runtime fail-opens on it); internal watchdog is the v2 upgrade path | — | `test_fail_closed_injection.py` |
| D2 | no input-size guard (clean oversized allowed) | **FIXED** — `MAX_INPUT_CHARS` hook-boundary guard (`input_too_large`) | 11-01 | `test_fail_closed_injection.py` |
| D3 | EMAIL regex super-linear (ReDoS-class) | **FIXED** — atomic groups + RFC-5321 length bounds → linear | 11-01 | `test_redos_size_guard.py` |
| D4 | mutation score not produced (mutmut on win32) | **OUT OF SCOPE (v1)** — mutmut refuses to start on win32 (boxed/mutmut#397); scoped `[tool.mutmut]` staged for WSL/CI | — | `pyproject.toml` (config staged) |

**Net:** every R1-R10, R12, D2, D3 is fixed-and-asserted; R11 is an accepted limitation; D1 and D4 are explicitly out-of-scope for v1 with a named upgrade path. No stale "pass-through pinned" comment remains implying an unaddressed gap.

## Residual Limitations (honest scope)

A client-side static scanner cannot be adversarially complete. What remains out of reach after this phase:

- **Double / multi-layer encoding** — the stage decodes ONE layer. base64(base64(secret)) recovers a still-encoded inner blob; the inner layer is not decoded again (bounded work, avoids a decode bomb). Documented, not fixed.
- **Encoded numeric Brazilian identifiers** — decoded content is NOT rescanned for CPF/CNPJ/etc. A short digit run false-positives trivially after arbitrary decode, so numeric kinds are deliberately excluded. An encoded CPF passes through.
- **R11 f-string interpolation** — runtime reassembly, not textual; a static strip cannot rebuild the value.
- **D1 hang** — external hook-timeout dependency (v2).
- **Novel secret formats** — the rescan only knows the patterns in `_ENCODED_SECRET_KINDS`; an unrecognized token shape encoded is not caught.

This raises the cost of low-effort accidental encoding (copy-pasted encoded config, a token in a data URI); it is not a guarantee against deliberate obfuscation.

## Measured FP-corpus rate

`tests/test_false_positive_corpus.py`: **docs_with_hits = 0, FP rate 0.0** (ceiling 0.05) — UNCHANGED by this plan. The three FP gates in series (min blob length → decode-to-valid-UTF-8 → high-confidence-secret match) mean no benign base64/hex blob in the corpus produces a hit, and `test_base64_of_benign_text_produces_no_hit` pins the decode-succeeds-but-no-secret path explicitly. The ceiling was never loosened.

## reason_code

Decode-and-rescan hits carry `reason_code = "encoded_secret_base64" | "encoded_secret_hex" | "encoded_secret_url"`. The hit spans the whole ENCODED blob (start/end of the blob match) so masking blocks the outbound encoded payload. Prior-pass behavior and reason_codes are unchanged.

## Verification

- `python -m pytest -q`: **328 passed, 1 skipped**, coverage **87.39%** (≥ `--cov-fail-under=84`). Baseline entering: 327 passed / 1 skipped; +1 is the new benign FP-guard test.
- `tests/test_detection.py` + `tests/test_v1_regression_gate.py`: green — no regression, no-op path on ordinary text.
- `tests/test_evasion_adversarial.py` + `tests/test_false_positive_corpus.py`: green — R7/R8/R9 detected, benign encoded blob no-hit, FP rate 0.0.

## Deviations from Plan

None — plan executed as written. Task 3's D1 comment upgrade (dangling "candidate fix thread" → definitive out-of-scope disposition) is the reconciliation the task called for, not a scope change.

## Known Stubs

None.

## Task Commits

1. **Task 1: decode-and-rescan stage** — `e0fa936` (feat)
2. **Task 2: flip R7/R8/R9 + benign FP guard** — `82a7f4b` (test)
3. **Task 3: phase-close D1 disposition** — `33e3830` (test)

---
*Phase: 11-fail-closed-hardening*
*Completed: 2026-07-10*

## Self-Check: PASSED

SUMMARY.md + all three modified source files present on disk; all three task commits (e0fa936, 82a7f4b, 33e3830) present in git history.
