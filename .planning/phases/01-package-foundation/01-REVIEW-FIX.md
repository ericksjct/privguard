---
phase: 01-package-foundation
fixed_at: 2026-05-03T00:00:00Z
review_path: .planning/phases/01-package-foundation/01-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 7
skipped: 0
status: all_fixed
---

# Phase 1: Code Review Fix Report

**Fixed at:** 2026-05-03T00:00:00Z
**Source review:** .planning/phases/01-package-foundation/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7
- Fixed: 7
- Skipped: 0

## Fixed Issues

### CR-01: Scrub mode does not actually replace the submitted prompt

**Files modified:** `privguard/hooks.py`
**Commit:** e0a0d83
**Applied fix:** Replaced the `scrub` branch in `main_user_prompt()` — removed the `print(json.dumps(...))` + `return 0` that wrote the redacted copy into `additionalContext` (which only appended, never replaced the original). Now writes a `[PII-GUARD BLOQUEADO] reason=scrub_unsupported` message to stderr and returns exit code 2, treating `scrub` as an alias for `block` until Claude exposes a documented prompt-replacement mechanism.

---

### CR-02: Hook adapters fail-open on malformed JSON and unknown tools

**Files modified:** `privguard/hooks.py`
**Commit:** 749cd1a
**Applied fix:** Two changes in one commit:
1. `main_user_prompt()` `except` clause now writes `[PII-GUARD BLOQUEADO] reason=malformed_payload` to stderr and returns 2 instead of 0.
2. `main_pre_tool()` `except` clause similarly returns 2 on malformed JSON. Added module-level `_KNOWN_LOCAL_TOOLS` frozenset (`Read`, `Edit`, `Write`, `NotebookEdit`, `Glob`, `Grep`, `Bash`, `PowerShell`) and a guard at the top of `main_pre_tool()` that calls `deny("PRE-TOOL-GUARD", "unknown_tool")` for any tool not in the set — blocking `WebFetch`, `WebSearch`, MCP-bridged tools, and future unknown tools.

---

### WR-01: PreTool inline-PII threshold drifts from prompt threshold

**Files modified:** `privguard/hooks.py`
**Commit:** 1ff70a9
**Applied fix:** Extracted a `_inline_threshold()` helper that reads `float(os.environ.get("PII_GUARD_THRESHOLD", "0.7"))`. Changed `check_bash()` to call `detect(command, min_score=_inline_threshold())` instead of the hardcoded `0.85`. Both prompt and tool surfaces now read from the same env-var configuration source.

---

### WR-02: Hook adapters and `privguard/hooks.py` are not under version control

**Files modified:** `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, `hooks/_pii_core.py`, `demos/ollama_local_demo.py`, `demos/reversible_demo.py`, `demos/test_presidio.py`, `demos/test_presidio_br.py`
**Commit:** dcec6c2
**Applied fix:** Staged and committed all previously untracked runtime boundary files. `privguard/hooks.py` was already picked up by the CR-01/CR-02/WR-01 commits above. All seven listed paths are now tracked in git history.

---

### WR-03: Path classifier substring match over-flags benign filenames

**Files modified:** `privguard/policy.py`
**Commit:** 2181fd4
**Applied fix:** Replaced bare `re.search(r"(?:credentials?|credenciais?)", name)` and `re.search(r"(?:secret|segredo|token|key)", name)` with word-boundary patterns using `(?:^|[._-])` prefix and `(?:[._-]|$)` suffix. The credentials branch now matches only when the token is a discrete word; the secret/token/key branch additionally matches `api[._-]?key`. Benign filenames such as `tokenizer.py`, `keychain.md`, `monkey.json`, `secretary_notes.txt` no longer trigger a block. Legitimate filenames such as `api-key.txt`, `secret_token.json`, and `.token` still match correctly. A comment explains the rationale.

---

### WR-04: `privguard mask` writes unverified output to stdout

**Files modified:** `privguard/cli.py`
**Commit:** acf67b6
**Applied fix:** Rewrote `cmd_mask()` to check `result.verified` first. On failure, output (plain text or JSON) goes to `sys.stderr` and the function returns 2 immediately — nothing reaches stdout. On success, output goes to stdout and returns 0. Added a docstring documenting the exit-code contract so callers understand `0` means "safe to forward."

---

### WR-05: Overlapping 11-digit detectors silently shadow each other

**Files modified:** `privguard/detection.py`
**Commit:** 8ba500d
**Applied fix:** In `detect()`, replaced the "downgrade to score 0.05 on checksum failure" pattern with a `continue` — failed-checksum hits are simply not emitted. This means a 11-digit value that fails the CPF checksum will not occupy the span in the dedup loop, allowing `BR_CNH` and `BR_PIS_PASEP` validators to be tested against the same span independently. The dedup logic (keep highest-score non-overlapping hit) is now safe because it only sees hits whose checksums have already passed.

---

_Fixed: 2026-05-03T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
