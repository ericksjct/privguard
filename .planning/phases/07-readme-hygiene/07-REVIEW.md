---
phase: 07-readme-hygiene
reviewed: 2026-05-10T19:33:16Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - .gitignore
  - README.md
  - conftest.py
  - privguard/cleanup.py
  - privguard/cli.py
  - pyproject.toml
  - tests/test_cleanup.py
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-05-10T19:33:16Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Seven files changed in the phase-07 (readme-hygiene) diff were reviewed:
`.gitignore`, `README.md`, `conftest.py`, `privguard/cleanup.py`,
`privguard/cli.py`, `pyproject.toml`, and `tests/test_cleanup.py`.

`README.md`, `pyproject.toml`, `.gitignore`, and `tests/test_cleanup.py` are
clean. `conftest.py` and `privguard/cli.py` are clean. `privguard/cleanup.py`
contains two warnings and two info-level findings.

No security vulnerabilities, hardcoded secrets, or authentication bypasses were
found. All synthetic-fixture rules are respected throughout the test file.

---

## Warnings

### WR-01: `_load_patterns` does not handle `OSError` / `TOMLDecodeError` on re-read

**File:** `privguard/cleanup.py:68-69`

**Issue:** `_load_patterns` opens `pyproject.toml` a second time (after
`_verify_repo_root` already read it). The second open has no `try/except`.
If the file is removed or corrupted between the two reads — a narrow but
real TOCTOU window — Python will propagate a raw `OSError` or
`tomllib.TOMLDecodeError` traceback to the user instead of the project's
standard `[CLEANUP] error: ... reason=...` exit path.

The symptom would be an unhandled exception exiting with code 1 rather than
the documented code 2, breaking any caller that checks exit codes.

**Fix:**
```python
def _load_patterns(cwd: Path) -> list[str]:
    """Read [tool.privguard.cleanup].patterns. Schema-validate per Pitfall 2."""
    try:
        with (cwd / "pyproject.toml").open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        _err("pyproject.toml unreadable on second read", "pyproject_unreadable")
        raise SystemExit(2)
    table = data.get("tool", {}).get("privguard", {}).get("cleanup")
    # ... rest unchanged
```

---

### WR-02: `_format_dry_run` apply-output rewrite uses fragile string replace

**File:** `privguard/cleanup.py:230-232`

**Issue:** The `--apply` branch generates its output header by calling
`_format_dry_run(matches, skips)` and then replacing the literal string
`"[dry-run] would delete"` with `"[apply] deleting"`. This creates a hidden
coupling: any edit to `_format_dry_run`'s header text that does not also
update the `replace()` call will silently produce an apply output that still
says `[dry-run]`, making it impossible for the user to distinguish a dry run
from a real deletion in the output.

The `test_cleanup_apply_deletes_pycache` test does not assert on the apply
output text, so this regression would not be caught by the test suite.

**Fix:** Parameterise `_format_dry_run` so callers pass the prefix:
```python
def _format_dry_run(
    matches: list[tuple[str, Path, int, int, int]],
    skips: list[tuple[str, str]],
    *,
    label: str = "dry-run",
    verb: str = "would delete",
) -> str:
    if not matches and not skips:
        return f"[{label}] nothing to clean.\n"
    total_bytes = sum(m[4] for m in matches)
    lines = [
        f"[{label}] {verb} ({len(matches)} paths, {_human_size(total_bytes)} total):"
    ]
    # ... rest unchanged
```

Then call it in the `--apply` branch as:
```python
apply_output = _format_dry_run(matches, skips, label="apply", verb="deleting")
```

---

## Info

### IN-01: Unreachable `return` at the end of `_human_size`

**File:** `privguard/cleanup.py:176`

**Issue:** The `for` loop in `_human_size` iterates over `("KB", "MB", "GB")`.
The loop body always returns on the `"GB"` iteration because the condition
`if n_float < 1024 or unit == "GB"` is unconditionally true when
`unit == "GB"`. The final `return f"{n} B"` on line 176 is therefore dead
code and will never execute for inputs `n >= 1024`.

This does not cause a runtime bug (the function is always correct), but it
confuses static analysis and indicates incomplete cleanup of the iterative
refactor.

**Fix:** Remove the dead return, or restructure to make the intent explicit:
```python
def _human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    n_float = float(n)
    for unit in ("KB", "MB", "GB"):
        n_float /= 1024.0
        if n_float < 1024 or unit == "GB":
            return f"{n_float:.1f} {unit}"
    return f"{n} B"  # unreachable; remove entirely
```

---

### IN-02: `_format_dry_run` per-pattern size column sums `r[3]` (byte_size) but label says "dirs"

**File:** `privguard/cleanup.py:192-197`

**Issue:** Within `_format_dry_run`, each row in `by_pattern` is the tuple
`(path, file_count, dir_count, byte_size)` (indices 0–3). The variable
assignments on lines 192-194 are:

```python
total_files = sum(r[1] for r in rows)   # r[1] = file_count  ✓
total_dirs  = sum(r[2] for r in rows)   # r[2] = dir_count   ✓
total_size  = sum(r[3] for r in rows)   # r[3] = byte_size   ✓
```

The format string on lines 196-197 then prints:
```
{path_count} paths / {total_dirs} dirs / {total_files} files / {_human_size(total_size)}
```

This is correct — `total_dirs` is emitted before `total_files`. However,
note that `total_size` actually accumulates `r[3]` which is `byte_size`, but
the header line (line 185) uses `m[4]` for the global total:
```python
total_bytes = sum(m[4] for m in matches)   # m[4] = byte_size (from full 5-tuple)
```

The per-pattern sub-rows are 4-tuples `(p, fc, dc, bs)`, so `r[3]` is
indeed byte_size — matching `m[4]` of the 5-tuple. The arithmetic is
consistent. This finding is purely a readability note: the dual tuple widths
(5 for `matches`, 4 for `by_pattern` rows) make the index arithmetic harder
to verify at a glance. Introducing named tuples or dataclasses would
eliminate this ambiguity.

**Fix (optional):** Replace the anonymous tuples with `dataclasses.dataclass`
or `typing.NamedTuple` to make field access self-documenting.

---

_Reviewed: 2026-05-10T19:33:16Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
