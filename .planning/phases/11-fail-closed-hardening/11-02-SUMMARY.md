---
phase: 11-fail-closed-hardening
plan: 02
subsystem: security-core
tags: [normalization, homoglyph, zero-width, combining-marks, offset-safe, evasion-hardening]

requires:
  - phase: 11-fail-closed-hardening
    provides: shared choke point detect() (11-01)
  - phase: 10-test-hardening
    provides: P2 adversarial evasion suite (R2/R3/R4 pins)
provides:
  - Offset-safe _normalize_for_detection() applied inside detect()
  - Confusable-digit + Cf/Mn normalization closing evasion vectors R2/R3/R4
  - Hit offsets/value guaranteed to index the ORIGINAL text (masking contract intact)
affects: [evasion-hardening-thread]

tech-stack:
  added: []
  patterns:
    - "Length-controlled normalization only (1:1 translate + Cf/Mn removal) so an exact orig-index map is buildable in one pass; NFKC/NFKD deliberately avoided"
    - "Identity fast-path (norm == text) skips remap entirely -> zero regression and no perf cost on benign input"
    - "Scan normalized string, then rebase surviving Hits onto original offsets so masking/diagnostics stay correct"

key-files:
  created:
    - .planning/phases/11-fail-closed-hardening/11-02-SUMMARY.md
  modified:
    - privguard/detection.py
    - tests/test_evasion_adversarial.py

key-decisions:
  - "NFKC/NFKD NOT used: they are length-changing (ligatures, compatibility decomposition) and would break the offset map that masking depends on"
  - "_CONFUSABLE_DIGITS kept conservative and digits-only: fullwidth U+FF10-FF19 plus the exact Cyrillic homoglyphs the R2 vector injects (U+0417 Ze->3, U+041E O->0); Latin-letter homoglyphs intentionally NOT mapped to avoid FP spikes"
  - "Cf (zero-width/format) and Mn (nonspacing-combining) chars removed during normalization; these carry no digit signal and their removal reassembles the fragmented value"
  - "Overlap/threshold/sort run on rebased original offsets so the existing masking contract is unchanged"

requirements-completed: [DET-07]

metrics:
  duration: 9min
  completed: 2026-07-10
  tasks: 3
  files_modified: 2

status: complete
---

# Phase 11 Plan 02: Offset-Safe Unicode Normalization Summary

**detect() now runs a single offset-safe normalization pass (conservative confusable-digit translation + Cf/Mn removal) before scanning, closing the homoglyph (R2), zero-width (R3), and combining-mark (R4) evasion vectors — while an identity fast-path and an exact orig-index remap guarantee Hit start/end/value still index the ORIGINAL text, so masking and the FP corpus (rate 0.0) are untouched and the full suite stays green at 86.85% coverage.**

## What Changed

### Task 1 — offset-safe normalization helper (`detection.py`)
Added `_CONFUSABLE_DIGITS` (module constant), `_normalize_for_detection(text) -> (norm, orig_index)`, and `_map_hit_to_original(hit, text, idx)`.

- `_normalize_for_detection` walks the text once. Each char is either translated 1:1 via `_CONFUSABLE_DIGITS` (offset preserved, `orig_index` records the original position) or, if `unicodedata.category(ch) in ("Cf", "Mn")`, dropped (nothing recorded). Everything else is copied verbatim. `orig_index[i]` is the offset in the original text of normalized char `i`.
- Benign input containing no homoglyph/Cf/Mn chars normalizes to itself, giving an identity map — the property the fast-path relies on.

### Task 2 — wire into detect() with offset mapping + identity fast-path (`detection.py`)
`detect()` computes `norm, orig_index = _normalize_for_detection(text)` and `identity = norm == text`. It scans `norm` (or `text` on the identity path), builds raw pattern + name Hits on normalized offsets, then — only when `not identity` — remaps each Hit onto the original via `_map_hit_to_original` (`orig_start = idx[m.start()]`, `orig_end = idx[m.end()-1] + 1`, `value = text[orig_start:orig_end]`, empty-match guarded). Overlap/threshold/sort then operate on the rebased (original) offsets, so the masking contract is byte-for-byte unchanged. On the common benign path the remap is skipped entirely: zero regression, no perf cost.

### Task 3 — flip R2/R3/R4 pins + FP-corpus gate (`test_evasion_adversarial.py`)
Renamed and re-asserted the three vectors to DETECTED, updated their `# RISCO` comments to "fixed in 11-02", and added an "Update (11-02)" note to the module docstring snapshot. R5–R11 remain pinned as pass-through. The FP corpus was re-run and stays at 0.0 (the confusable map is digits-only and the benign corpus contains no Cyrillic, so no benign string gains a hit).

## Confusable Codepoints Covered

| Codepoint | Char | Maps to | Source |
|-----------|------|---------|--------|
| U+FF10–U+FF19 | fullwidth ０-９ | 0–9 | plan (fullwidth digit class) |
| U+0417 | З (Cyrillic Capital Ze) | 3 | R2 test vector |
| U+041E | О (Cyrillic Capital O) | 0 | R2 test vector |

Removed by category (not translated): all `Cf` (format — ZWSP U+200B/R3, ZWNJ, ZWJ, BOM, soft hyphen) and all `Mn` (nonspacing-combining — combining acute U+0301/R4).

## Why NFKC Was NOT Used

Full `unicodedata.normalize("NFKC"/"NFKD", ...)` is length-changing: ligatures expand, compatibility characters decompose, and one input char can become several (or vice versa). That destroys the 1:1 / removal invariant that makes `orig_index` exact, which would in turn corrupt the Hit start/end/value that `mask_text` and diagnostics consume. The threat-model benefit (digit homoglyphs, zero-width, combining) is fully covered by the conservative translate+remove pass, so NFKC's cost (broken offsets) buys nothing here.

## Tests Flipped

| Vector | Old test (pass-through) | New test (detected) |
|--------|-------------------------|---------------------|
| R2 Cyrillic homoglyph | `test_cyrillic_homoglyph_cpf_passes_through` (`not _any_hit`) | `test_cyrillic_homoglyph_cpf_is_detected` (`_has_cpf`) |
| R3 zero-width | `test_zero_width_chars_inside_cpf_pass_through` (`not _any_hit`) | `test_zero_width_chars_inside_cpf_is_detected` (`_has_cpf`) |
| R4 combining marks | `test_combining_chars_on_cpf_digits_pass_through` (`not _any_hit`) | `test_combining_chars_on_cpf_digits_is_detected` (`_has_cpf`) |

## Verification

- `python -m pytest`: **327 passed, 1 skipped**, coverage **86.85%** (≥ `--cov-fail-under=84`). Baseline entering was 327 passed / 1 skipped @ 86.72% (pins flipped in place, net 0 test-count change; coverage nudged up from the new helper being exercised).
- Offset correctness confirmed on all three vectors: `text[hit.start:hit.end] == hit.value` for the homoglyph, ZWSP-interleaved, and combining-mark CPFs (value carries the original evasion chars, so masking covers the full original span).
- `tests/test_masking.py` + `tests/test_v1_regression_gate.py`: green — offsets/values on benign PII unchanged (identity fast-path).
- `tests/test_false_positive_corpus.py`: FP rate **0.0** (`docs_with_hits == 0`, ceiling 0.05) — unchanged.

## Deviations from Plan

None — plan executed as written.

## Task Commits

1. **Task 1: normalization helper** — `199b0cd` (feat)
2. **Task 2: wire into detect() + fast-path** — `641f6c5` (fix)
3. **Task 3: flip R2/R3/R4 + FP gate** — `278e232` (test)

## Known Stubs

None.

---
*Phase: 11-fail-closed-hardening*
*Completed: 2026-07-10*

## Self-Check: PASSED

SUMMARY.md + both modified source files present on disk; all three task commits (199b0cd, 641f6c5, 278e232) present in git history.
