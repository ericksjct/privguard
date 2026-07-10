---
phase: 11-fail-closed-hardening
verified: 2026-07-09T00:00:00Z
status: passed
score: 5/5 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification: # No previous VERIFICATION.md — initial verification
  previous_status: none
requirements: [DET-07]
---

# Phase 11: Fail-Closed Hardening Verification Report

**Phase Goal:** Close the phase-10 findings — the guard blocks on detector error and oversized input (fail-closed, not fail-open), the ReDoS-class EMAIL regex is made backtracking-safe, and detection is hardened against common evasion (normalization, fragmentation/concatenation, encoded secrets) without regressing the false-positive rate. (DET-07)
**Verified:** 2026-07-09
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth (SC) | Status | Evidence |
|---|-----------|--------|----------|
| SC1 | Detector exception on either hook blocks with exit 2 + sanitized reason, never exit 1 (R1) | ✓ VERIFIED | `_run_fail_closed` (hooks.py:231-246) wraps both `main_user_prompt` (249) and `main_pre_tool` (376); catches `Exception`, emits `reason=detector_error action=block`, returns 2. `BaseException` deliberately not caught. Tests assert exit 2 on both hooks + BaseException propagation (`test_fail_closed_injection.py:53,76,92`). |
| SC2 | Oversized input blocks fail-closed (not scanned in full); EMAIL regex scales linearly (D2, D3) | ✓ VERIFIED | `_too_large`/`_max_input_chars` (hooks.py:143-158) gate the prompt path (266→exit 2 `input_too_large`), LLM-orchestration (409-414) and Bash (460-465). EMAIL regex uses atomic groups + RFC-5321 length bounds (detection.py:205). Tests: `test_10mb_prompt_with_pii_blocks`, `test_10mb_clean_prompt_blocked` (exit 2), `test_email_bait_scales_linearly_after_atomic_fix` (<4x time on 2x input). |
| SC3 | SUS leading-digit range check (R12) + offset-safe Unicode-normalization evasion detected (R2/R3/R4) | ✓ VERIFIED | `valida_cartao_sus` rejects `cartao[0] not in "12789"` BEFORE checksum (detection.py:143). `_normalize_for_detection` maps `_CONFUSABLE_DIGITS` 1:1 and drops Cf/Mn (313-339), rebased via `_map_hit_to_original`. Tests: `test_sus_out_of_range_leading_digit_rejected` builds a checksum-VALID card with leading 3-6 and asserts rejection; cyrillic/zero-width/combining CPF asserted DETECTED. Offset correctness confirmed empirically (see below). |
| SC4 | Fragmentation/concatenation reassembly (R5/R6/R10/R11) + encoded-secret decode-and-rescan (R7/R8/R9), FP-gated | ✓ VERIFIED | Checksum-gated denoised pass (`_denoise`/`_denoised_hits`, detection.py:377-427, reason_code `reassembled_checksum_valid`); single-layer `_scan_encoded_secrets` (476-501, reason_code `encoded_secret_<enc>`). Tests assert R5/R6/R10 DETECTED, R7/R8/R9 DETECTED, benign base64 no-hit. R11 f-string is an HONEST accepted limitation (asserted pass-through). FP corpus held at 0.0 by hard assertion (not loosened). |
| SC5 | Full suite green under coverage gate; every phase-10 R#/D# has a definitive disposition | ✓ VERIFIED | `python -m pytest -q` → **328 passed, 1 skipped**, coverage **87.39% ≥ --cov-fail-under=84** (pyproject.toml:46). SUMMARY disposition table covers R1-R12 + D1-D4; no stale "pass-through pinned" comment implying an unaddressed gap remains. |

**Score:** 5/5 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `privguard/detection.py` | Normalization, denoised rescan, encoded-secret scan, backtracking-safe EMAIL, SUS range check | ✓ VERIFIED | All symbols present, substantive, and wired into `detect()` (517-563). Reused `PATTERNS` regexes (single source). |
| `privguard/hooks.py` | Detector-exception wrapper (exit 2 detector_error), input-size guard (input_too_large) | ✓ VERIFIED | `_run_fail_closed`, `_too_large` wired into both hook entry points. |
| `tests/test_evasion_adversarial.py` | R2-R10 assert DETECTION; R11 pinned | ✓ VERIFIED | Genuine `detect()` calls, real synthetic values; RISCO→fixed comments match asserts. |
| `tests/test_fail_closed_injection.py` | Phase-10 pins flipped to exit-2 block | ✓ VERIFIED | Asserts `== 2` + `reason=detector_error`/`input_too_large` on both hooks. |
| `tests/test_redos_size_guard.py` | EMAIL linear-scaling assertions | ✓ VERIFIED | Time-bound + <4x linear-signature asserts. |
| `tests/test_checksum_edges.py` | SUS R12 leading-digit range | ✓ VERIFIED | Constructs checksum-valid 3-6 cards, asserts rejection. |
| `tests/test_false_positive_corpus.py` | FP rate ~0.0, ceiling not loosened | ✓ VERIFIED | Ceiling 0.05 UNCHANGED; hard `docs_with_hits == 0` assertion; non-trivial-corpus guard. |
| `pyproject.toml` | `--cov-fail-under=84` present | ✓ VERIFIED | Line 46; `[tool.mutmut]` staged for WSL/CI (D4). |

### Data-Flow / Offset Trace (Level 4)

Empirically exercised `detect()` across all four passes with a synthetic checksum-valid CPF and a synthetic API-key secret; for every returned Hit confirmed `0 <= start <= end <= len(text)` and `text[start:end] == value` on the ORIGINAL string:

| Pass | reason_code | Offsets index ORIGINAL | Notes |
|------|-------------|------------------------|-------|
| Normalization (zero-width, Cf drop) | checksum_valid | ✓ | span covers ZWSP-laden original |
| Normalization (fullwidth homoglyph 1:1) | checksum_valid | ✓ | length-preserving map, exact |
| Denoised reassembly (fragmented across newline) | reassembled_checksum_valid | ✓ | span covers the injected newline; digits reconstruct the CPF |
| Encoded-secret decode-and-rescan | encoded_secret_base64 | ✓ | Hit spans the ENCODED blob in the original |

Catch (d) — offset-mapping bugs in `_map_hit_to_original`/`_denoised_hits` — investigated and cleared: every returned Hit indexes the original text, so masking blocks the correct span.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full suite green under coverage gate | `python -m pytest -q` | 328 passed, 1 skipped, 87.39% | ✓ PASS |
| Offset correctness across all 4 passes | scripted `detect()` probe | all spans index original | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DET-07 | 11-01..04 | Guard fails closed on operational failure (detector exception / oversized input) and resists common evasion without regressing FP rate | ✓ SATISFIED | All 5 SC verified; REQUIREMENTS.md line 146 marks DET-07 Complete. |

### Anti-Patterns Found

None. No unreferenced TBD/FIXME/XXX in the phase-modified files. `except ValueError: continue` (decode failures) and `except Exception: pass` (audit log fire-and-forget) are intentional, documented fail-safe paths — not silent stubs.

### Accepted Limitations (honest scope — DET-07 is a client-side scanner)

These are legitimate, honestly documented dispositions, NOT failures:

- **R11 f-string interpolation** — reassembles at RUNTIME, not textually; a static strip cannot rebuild it. Test pins pass-through.
- **Encoded numeric BR identifiers** — decoded content is deliberately NOT rescanned for CPF/CNPJ (short digit runs false-positive after arbitrary decode).
- **Double/multi-layer encoding** — decode-and-rescan reverses ONE layer (bounded work; avoids a decode bomb).
- **D1 hang watchdog** — OUT OF SCOPE v1; depends on Claude Code's external hook timeout. v2 upgrade path named.
- **D4 mutation score** — mutmut refuses to start on win32 (boxed/mutmut#397); `[tool.mutmut]` config staged for WSL/CI.

### Human Verification Required

None. All behavior-dependent truths (exception→block, oversize→block, offset correctness across normalization/denoise/encoded passes) are exercised by passing tests and the scripted offset probe.

### Gaps Summary

No gaps. All five success criteria are observably true in the codebase:
- Both hooks fail closed (exit 2) on detector exception and oversized input — no reachable fail-open path (BaseException intentionally propagates; verified by test).
- EMAIL regex is atomic-group + length-bounded and asserted linear.
- SUS R12 range check runs before checksum (proven with checksum-valid out-of-range cards).
- Normalization/denoise/encoded passes detect the evasion vectors AND emit offsets that index the original text (masking-safe), with the FP corpus held at a hard 0.0 — the FP assertion was NOT loosened to fake a fix.
- Full suite green (328 passed / 1 skipped, 87.39% ≥ 84%); every R1-R12 / D1-D4 carries a definitive disposition.

Adversarial catches (a) unasserted/unreachable fix, (b) FP loosened instead of real gate, (c) reachable fail-open, (d) offset-mapping bug — all investigated and cleared.

---

_Verified: 2026-07-09_
_Verifier: Claude (gsd-verifier)_
