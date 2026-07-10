---
phase: 11-fail-closed-hardening
plan: 03
subsystem: security-core
tags: [evasion-hardening, fragmentation, concatenation, checksum-gated, offset-safe, denoised-rescan]

requires:
  - phase: 11-fail-closed-hardening
    provides: offset-safe _normalize_for_detection() + orig-index map (11-02)
  - phase: 11-fail-closed-hardening
    provides: shared choke point detect() (11-01)
provides:
  - Checksum-gated denoised second pass in detect() (strip whitespace/quotes/plus, rescan checksum-bearing patterns, keep format-separated validator-passers)
  - Fragmentation (R5/R6) and string-concatenation (R10) formatted-CPF vectors closed
  - reason_code reassembled_checksum_valid for denoised-pass hits
affects: [evasion-hardening-thread]

tech-stack:
  added: []
  patterns:
    - "Denoised rescan composes the 11-02 orig-index map (denoised->normalized->original) so reassembled hits rebase onto the ORIGINAL span; masking contract intact"
    - "Checksum-bearing kinds only + validator-pass + format-separator requirement = FP bounded by checksum collision on FORMATTED values; bare-digit reassembly never emitted"
    - "True no-op when nothing is stripped (len(denoised) == len(norm)); dedup against primary hits by (kind, digits)"

key-files:
  created:
    - .planning/phases/11-fail-closed-hardening/11-03-SUMMARY.md
  modified:
    - privguard/detection.py
    - tests/test_evasion_adversarial.py

key-decisions:
  - "Denoised pass strips ONLY [whitespace, single/double quote, plus] — dots/hyphens/slashes survive so formatted patterns still match and their survival is the FP-limiting signal"
  - "A reassembled match is emitted only if it retains a format separator (dot/hyphen/slash): this uniformly excludes ALL bare-digit reassembly (whitespace-joined numbers, all of BR_CNH, the \\d{11}/\\d{12}/\\d{15} regex branches) which collide too readily once separators are stripped"
  - "Only checksum-bearing kinds (CANONICAL_VALIDATORS) run in the denoised pass; non-checksum kinds (EMAIL, secrets, phone, CEP, plates) are NOT emitted — no checksum to bound their FP"
  - "R11 (f-string) left as ACCEPTED LIMITATION: `{p}` interpolation reassembles at RUNTIME, not textually, so no static separator-strip can rebuild the value"
  - "Denoised hits deduplicated against primary-pass hits by (kind, digits) so a value already caught contiguously is not double-reported"

requirements-completed: [DET-07]

metrics:
  duration: 14min
  completed: 2026-07-10
  tasks: 2
  files_modified: 2

status: complete
---

# Phase 11 Plan 03: Checksum-Gated Denoised Rescan Summary

**detect() now runs a checksum-gated denoised second pass — it strips injectable separators (whitespace, quotes, plus) from the normalized text, rescans with the checksum-bearing patterns only, and emits a hit ONLY when the reassembled value keeps a format separator AND passes its validator — closing the formatted fragmentation (R5), whitespace-injection (R6) and string-concatenation (R10) CPF vectors while the FP corpus stays at 0.0; f-string reassembly (R11) is documented as an accepted limitation because it reassembles at runtime, not textually.**

## What Changed

### Task 1 — checksum-gated denoised rescan (`detection.py`) — commit `50a0d18`
Added `_DENOISE_STRIP` (the injectable-separator set), `_DENOISE_SEP_RE` (format-separator gate), `_DENOISED_PATTERNS` (checksum-bearing subset of `PATTERNS`), `_denoise(norm, orig_index)` and `_denoised_hits(...)`.

- `_denoise` walks the already-normalized text, drops any char that `isspace()` or is in `'"+`, and records the ORIGINAL offset (composed through the 11-02 `orig_index`) for each surviving char — yielding `(denoised, den_index)`.
- `_denoised_hits` rescans `denoised` with `_DENOISED_PATTERNS`. A match is emitted only if it (1) contains a `.`/`-`/`/` separator, (2) passes its validator, and (3) is not already present in the primary hits by `(kind, digits)`. Surviving hits rebase onto the original text via `den_index` with `reason_code="reassembled_checksum_valid"`.
- Wired into `detect()` AFTER the primary-pass offset remap (so all hits share ORIGINAL offsets), guarded by `len(denoised) < len(norm)` — a true no-op on separator-free text.

### Task 2 — flip R5/R6/R10, R11 limitation (`test_evasion_adversarial.py`) — commit `cee7bc4`
Renamed and re-asserted R5, R6, R10 to DETECTED with updated `# RISCO fixed in 11-03` comments; left R11 pinned as pass-through with an explicit `ACCEPTED LIMITATION` comment; added an "Update (11-03)" note to the module docstring snapshot.

## Kinds Covered vs. Excluded (denoised pass)

| Kind | In denoised pass? | Emitted when reassembled? | Why |
|------|-------------------|---------------------------|-----|
| BR_CPF | yes | yes — formatted `NNN.NNN.NNN-NN` | dots+hyphen survive stripping, strong FP signal |
| BR_CNPJ | yes | yes — formatted `NN.NNN.NNN/NNNN-NN` | dots/slash/hyphen survive |
| BR_PIS_PASEP | yes | yes — formatted `NNN.NNNNN.NN-N` | dots+hyphen survive |
| BR_TITULO_ELEITOR | yes | no in practice | formatted form uses SPACES (stripped) → bare digits → excluded by format-sep gate |
| BR_CARTAO_SUS | yes | no in practice | formatted form uses SPACES → bare digits → excluded |
| CREDIT_CARD | yes | no in practice | groups are space/dash separated → reassembles to bare 16 digits → excluded (space-separated cards are already caught by the PRIMARY pattern) |
| BR_CNH | yes | never | pure `\b\d{11}\b`, no format separator → always excluded (most collision-prone) |
| EMAIL, secrets, phone, CEP, plates | NO | — | no checksum to bound FP |

**Net effect:** the denoised pass fires only for DOT/HYPHEN-formatted checksum identifiers (CPF, CNPJ, dotted PIS). Every bare-digit reassembly is excluded by design.

## Vectors: Fixed vs. Accepted Limitation

| Vector | Input shape | Outcome |
|--------|-------------|---------|
| R5 fragmented across lines | `123.456.\n789-09` | **FIXED** — strip `\n`, reassembles formatted CPF |
| R6 whitespace between digits | `1 2 3 . 4 5 6 . 7 8 9 - 0 9` | **FIXED** — strip spaces, dots/hyphen survive |
| R10 string concatenation | `"123.456" + ".789-09"` | **FIXED** — strip quotes+plus, reassembles formatted CPF |
| R11 f-string interpolation | `f"{p}.789-09"` | **ACCEPTED LIMITATION** — `{p}` reassembles at RUNTIME; static strip leaves the literal `{p}` between fragments, so the value never rebuilds in text. Fixing needs code evaluation, out of scope for a static scanner. Test stays pinned as pass-through, documented here. |

Honest scope note (from the plan): a client-side static scanner cannot be adversarially complete. This raises the cost of accidental/low-effort evasion for FORMATTED Brazilian identifiers; it is not a guarantee against deliberate obfuscation. Bare-digit fragmentation and non-checksum kinds (concatenated EMAIL/secret) remain out of reach and are accepted limitations.

## Measured FP-corpus rate

`tests/test_false_positive_corpus.py`: **docs_with_hits = 0, FP rate 0.0** (ceiling 0.05) — UNCHANGED by this plan. The ceiling was never loosened. The format-separator gate plus checksum validation means no benign whitespace-joined number in the corpus produces a hit.

## reason_code

Denoised-pass hits carry `reason_code = "reassembled_checksum_valid"`. Primary-pass behavior and its reason_codes are unchanged. When the exact original span is ambiguous the hit still spans the contributing chars (start of first → end of last), forcing a block decision — never a silent allow (verified: R5 hit spans the whole `\n`-laden original, offsets 0–15).

## Verification

- `python -m pytest`: **327 passed, 1 skipped**, coverage **87.11%** (≥ `--cov-fail-under=84`). Baseline entering: 327 passed / 1 skipped. Net 0 test-count change (three pins flipped in place, one relabeled).
- `tests/test_detection.py` + `tests/test_masking.py` + `tests/test_v1_regression_gate.py`: green — masking offsets/values on benign PII unchanged (no-op path).
- `tests/test_evasion_adversarial.py` + `tests/test_false_positive_corpus.py`: green — R5/R6/R10 detected, R11 pinned, FP rate 0.0.

## Deviations from Plan

**1. [Rule 2 - Missing critical FP bound] Added a format-separator requirement to the denoised pass.**
- **Found during:** Task 1.
- **Issue:** The plan's default (all checksum-bearing kinds) keeps the 20-doc corpus at 0.0, but bare-11-digit matching (BR_CNH entirely, plus the `\d{11}` branches of CPF/PIS) on separator-stripped text is a real-world collision surface the small corpus does not exercise — e.g. a phone written `11 987654321` reassembles to an 11-digit run that a checksum passes ~1/100.
- **Fix:** Emit a denoised hit only when the reassembled value retains a `.`/`-`/`/` separator. This uniformly excludes every bare-digit reassembly (the plan's suggested tightening, generalized) while still catching all target vectors (all formatted CPF). Documented as covered-vs-excluded above.
- **Files modified:** `privguard/detection.py`.
- **Commit:** `50a0d18`.

## Known Stubs

None.

## Task Commits

1. **Task 1: checksum-gated denoised rescan** — `50a0d18` (feat)
2. **Task 2: flip R5/R6/R10 + R11 limitation** — `cee7bc4` (test)

---
*Phase: 11-fail-closed-hardening*
*Completed: 2026-07-10*

## Self-Check: PASSED

SUMMARY.md + both modified source files present on disk; both task commits (50a0d18, cee7bc4) present in git history.
