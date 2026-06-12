---
phase: 09-milestone-v1-0-audit-cleanup
reviewed: 2026-06-11T00:00:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - privguard/cleanup.py
findings:
  critical: 0
  warning: 0
  info: 1
  total: 1
status: clean
---

# Phase 09: Code Review Report

**Reviewed:** 2026-06-11T00:00:00Z
**Depth:** standard
**Files Reviewed:** 1
**Status:** clean

## Summary

Reviewed `privguard/cleanup.py` (a fail-closed cleanup CLI that deletes repo-root
artifacts) focusing on the three phase-09 audit fixes: WR-01 (`_load_patterns`
pyproject.toml reopen guard), WR-02 (`_format_dry_run` parameterized with
`apply: bool`), and IN-01 (removal of an unreachable `return` in `_human_size`).

All three changes are correct and constitute robustness/clarity improvements with
no behavior regression in the relevant code paths.

- **WR-01:** The reopen is now wrapped in `try/except (OSError,
  tomllib.TOMLDecodeError)`, emitting a sanitized `_err("pyproject.toml
  unreadable", "pyproject_unreadable")` and `raise SystemExit(2)`. This mirrors
  the existing guard in `_verify_repo_root` (lines 55-60) exactly, so the two
  TOML reads are now consistent. The error string is static — no path or file
  contents leak. POL-04 (paths/reason-codes only) is upheld.
- **WR-02:** The fragile `.replace()` chain in main()'s `--apply` branch is
  replaced by a clean `apply=True` parameter. The new header
  (`f"{prefix} {verb} ..."` → `"[apply] deleting ..."`) and the
  `if not apply` trailer suppression reproduce the prior apply-mode output for
  the non-empty case. No sanitization regression — all interpolated values are
  either static (`prefix`, `verb`) or already-sanitized counts/basenames.
- **IN-01:** The removed post-loop `return f"{n} B"` was genuinely unreachable:
  the early `if n < 1024` handles small values, and the loop's
  `if n_float < 1024 or unit == "GB"` always returns on the final `"GB"`
  iteration. The function still returns on every path. No behavior change.

No new injection or information-disclosure surface was introduced. All
`_err`/`_warn` calls continue to emit only static messages, reason codes, and
basenames (`path.name` / `rel`) — never file contents. The TOCTOU symlink
re-check (lines 248-251) and hardcoded `_PROTECTED` list (D-09) remain intact.

One non-blocking Info item is noted below regarding an incidental behavior change
in the empty-result apply case — it is a latent-bug fix, not a regression.

## Info

### IN-01: Empty-result `--apply` header now correctly reads `[apply]`

**File:** `privguard/cleanup.py:194-195`
**Issue:** Before WR-02, the apply-mode output was produced by
`.replace("[dry-run] would delete", "[apply] deleting")`. That substring does
not occur in the empty branch (`"[dry-run] nothing to clean.\n"`), so under the
old code `privguard cleanup --apply` on a clean repo printed
`"[dry-run] nothing to clean."` — a stale `[dry-run]` label. The new
parameterized code emits `"[apply] nothing to clean.\n"`, which is the
intended/correct label. This is an improvement (latent display bug fixed), not a
regression. Flagged only so the changed empty-case output is documented for any
snapshot/CLI tests that assert on it.
**Fix:** No action required. If a test asserts the old `[dry-run] nothing to
clean.` string for `--apply`, update it to expect `[apply] nothing to clean.`.

---

_Reviewed: 2026-06-11T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
