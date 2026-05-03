---
phase: 02-privacy-core
fixed_at: 2026-05-03T00:00:00Z
review_path: .planning/phases/02-privacy-core/02-REVIEW.md
iteration: 1
findings_in_scope: 1
fixed: 1
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-05-03T00:00:00Z
**Source review:** `.planning/phases/02-privacy-core/02-REVIEW.md`
**Iteration:** 1

**Summary:**
- Findings in scope (critical + warning): 1
- Fixed: 1
- Skipped: 0
- Out-of-scope (Info, deferred): 6

The configured `fix_scope` is `critical_warning`, so only the single Warning (WR-01) was addressed in this pass. The six Info-level findings (IN-01 through IN-06) are intentionally deferred and listed under "Out of Scope" for traceability.

## Fixed Issues

### WR-01: `verify_mask` short-circuits to verified when caller passes empty hits

**Files modified:** `privguard/masking.py`, `tests/test_masking.py`
**Commit:** `a6b6604`
**Applied fix:**
- Reordered `verify_mask` (privguard/masking.py:54-78) so the empty-hits early-return is evaluated AFTER residual re-detection rather than before it. The function now always:
  1. checks each provided hit's raw `value` against `masked_text` (`original_value_remaining`),
  2. runs `detect(masked_text, ...)` filtered by `_is_safe_placeholder_residual` (`residual_detection`),
  3. returns `False` if either reason fired,
  4. only then collapses to `(True, ("no_sensitive_hits",))` when `hits` is empty AND no residual was found, or `(True, ("mask_verified",))` otherwise.

  Net effect: `mask_text(text, hits=[])` on text containing sensitive data now returns `verified=False`, `verification_status="failed"`, `reason_codes` containing `"residual_detection"`, and the original (unchanged) text — closing the public-API fail-open that contradicted MASK-02.

- Added three regression tests in `tests/test_masking.py`:
  - `test_mask_text_does_not_fail_open_when_caller_passes_empty_hits` — exact case from REVIEW.md.
  - `test_verify_mask_runs_residual_detection_when_hits_empty` — pins the residual-detection branch on raw input via the `verify_mask` API directly.
  - `test_verify_mask_returns_no_sensitive_hits_when_truly_clean` — pins the still-good positive case (clean text, empty hits => verified with `no_sensitive_hits`).

**Verification:**
- Tier 1: re-read masking.py:54-78 and tests/test_masking.py:96-122 — fix text present, surrounding code intact.
- Tier 2: `python -c "import ast; ast.parse(...)"` on both files — OK.
- Additional: `python -m pytest tests/test_masking.py -q` — 13 passed (10 pre-existing + 3 new), confirming the existing `test_mask_result_for_clean_text_is_verified_and_unchanged` still passes (clean text + empty hits still yields `("no_sensitive_hits",)`).

## Skipped Issues

None — the only in-scope finding was applied successfully.

## Out of Scope (deferred Info findings)

The following findings are Info severity and outside this run's `critical_warning` scope. They remain documented in `02-REVIEW.md` for a future pass:

- **IN-01:** `READ_CMDS` / `EXFIL_CMDS` dead regex constants in `privguard/policy.py:69-80`.
- **IN-02:** `SENSITIVE_GLOBS` dead and divergent from inline classifier in `privguard/policy.py:14-21`.
- **IN-03:** Substring-based filename heuristic in `privguard/policy.py:114` over-matches benign names (`monkey.py`, `tokenizer.py`, etc.).
- **IN-04:** `to_dict` denylist in `privguard/diagnostics.py:50-56` skips only `value`/`text`; future raw-bearing fields would silently leak.
- **IN-05:** `cmd_policy_check` collapses BLOCK and PAUSE into exit code `2` (`privguard/cli.py:73`).
- **IN-06:** `format_text` falls through to `str(dict)` for policy-decision payloads (`privguard/cli.py:72` -> `privguard/diagnostics.py:75-93`).

---

_Fixed: 2026-05-03T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
