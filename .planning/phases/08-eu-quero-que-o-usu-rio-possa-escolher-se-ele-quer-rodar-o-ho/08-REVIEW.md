---
phase: 08-mask-mode
reviewed: 2026-05-25T00:00:00Z
depth: standard
files_reviewed: 2
files_reviewed_list:
  - privguard/hooks.py
  - tests/test_claude_hooks.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-05-25T00:00:00Z
**Depth:** standard
**Files Reviewed:** 2
**Status:** issues_found

## Summary

Reviewed the Phase 8 `mask` mode implementation in `privguard/hooks.py` and its test coverage in
`tests/test_claude_hooks.py`. The review focused on the five security-critical constraints stated
in the phase context.

**All five security-critical constraints pass:**

1. `mask_result.verified` gate is checked before `mask_result.text` is ever written to stderr
   (hooks.py lines 212 vs 235). The unverified path exits at line 227 without touching `text`.
2. Both paths in the mask branch return 2 (lines 227, 237). There is no exit-0 path when PII is
   detected and `mode == "mask"`.
3. Neither `_prompt_diagnostic` call in the mask branch passes `mode=` (lines 221-225, 229-233).
   The `mode_scope=local_development_non_protective` label is correctly confined to the warn path.
4. The `scrub` branch (lines 206-208) has no `return` statement and falls through to the default
   block at line 239.
5. The LLM orchestration mask check always calls `_deny_pre_tool` (lines 333, 342) — there is no
   pass-through path, consistent with the fact that `updatedInput` is unavailable for Agent/Task.

Two warnings and three info items were found. None are security vulnerabilities. The warnings are
a log-format inconsistency and a test-helper asymmetry that could cause future maintenance issues.

---

## Warnings

### WR-01: `scrub` notice uses non-standard log prefix

**File:** `privguard/hooks.py:207`
**Issue:** The scrub deprecation notice is emitted as `[PII-GUARD] modo scrub removido, usando block`
— note the prefix is `[PII-GUARD]` rather than the `[PII-GUARD BLOQUEADO]` token used by every
other blocking path. Any log parser or monitoring system keying on `BLOQUEADO` will miss this
stderr line, creating a gap in observability for the scrub → block fallthrough.

**Fix:** Align the prefix with the standard blocking format, or add the standard notice as a
second write immediately after:
```python
if mode == "scrub":
    sys.stderr.write("[PII-GUARD BLOQUEADO] reason=scrub_removed action=block\n")
    # falls through to default block below
```
Alternatively, keep the informational notice but also ensure the fallthrough block path emits the
standard token (it does, at line 241) — so this is low risk if log parsers scan all stderr, not
just the first matching line per request.

---

### WR-02: `run_pre_tool` test helper lacks `mode` parameter, asymmetric with `run_user_prompt`

**File:** `tests/test_claude_hooks.py:42-49`
**Issue:** `run_user_prompt` accepts a `mode` parameter and handles env-var setup internally
(lines 22-39). `run_pre_tool` has no `mode` parameter. The Phase 8 pre-tool tests
(`test_pre_tool_mask_mode_*`) work around this by calling `monkeypatch.setenv("PII_GUARD_MODE",
"mask")` directly before calling `run_pre_tool` (e.g., line 428). This asymmetry increases the
risk of a future test writer forgetting to set the mode env var manually when testing pre-tool
mode-aware behaviour, silently testing the wrong mode.

**Fix:** Add a `mode` parameter to `run_pre_tool` mirroring `run_user_prompt`:
```python
def run_pre_tool(
    monkeypatch: pytest.MonkeyPatch,
    payload: object | str,
    *,
    mode: str | None = None,
) -> int:
    if mode is None:
        monkeypatch.delenv("PII_GUARD_MODE", raising=False)
    else:
        monkeypatch.setenv("PII_GUARD_MODE", mode)

    if isinstance(payload, str):
        raw_payload = payload
    else:
        raw_payload = json.dumps(payload)

    monkeypatch.setattr(sys, "stdin", io.StringIO(raw_payload))
    return main_pre_tool()
```
Then update `test_pre_tool_mask_mode_llm_orchestration_blocks_pii` and
`test_pre_tool_mask_mode_clean_llm_orchestration_payload_allows` to pass `mode="mask"` to the
helper instead of calling `monkeypatch.setenv` directly.

---

## Info

### IN-01: No test for `scrub` mode fallthrough in `test_claude_hooks.py`

**File:** `tests/test_claude_hooks.py` (no specific line — missing test)
**Issue:** The `scrub` fallthrough path (hooks.py lines 206-208) is not covered by any test in
the file. A regression that accidentally added `return 0` or `return 2` before the fallthrough
could go undetected.
**Fix:** Add a test:
```python
def test_user_prompt_scrub_mode_falls_through_to_block(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prompt = f"{PROMPT_SNIPPET}: CPF {RAW_CPF}"
    assert run_user_prompt(monkeypatch, {"prompt": prompt}, mode="scrub") == 2
    captured = capsys.readouterr()
    assert "BLOQUEADO" in captured.err
    assert "reason=pii_detected" in captured.err
```

---

### IN-02: `test_non_blocking_prompt_modes_are_labeled_non_protective_and_sanitized` is parametrized on only one mode

**File:** `tests/test_claude_hooks.py:305`
**Issue:** The parametrize decorator lists only `"warn"` (line 305: `@pytest.mark.parametrize("mode", ["warn"])`).
Using `parametrize` with a single value is a code-smell; it offers no combinatorial benefit and
may signal the intent to add more values (e.g., `"scrub"` or a future `"log"` mode) that was
never followed through.
**Fix:** Either inline it as a non-parametrized test, or add the `scrub` mode as a second
parameter entry now that coverage for that path is desired:
```python
@pytest.mark.parametrize("mode", ["warn"])
```
→ replace with a plain function, or extend to `["warn", "scrub"]` if the scrub notice is also
expected to show non-protective labelling (it is not — scrub falls through to block, so the test
body would need separate assertions for that case).

---

### IN-03: Magic string `"mask"` repeated across multiple call sites without a shared constant

**File:** `privguard/hooks.py:210, 327, 330` and `tests/test_claude_hooks.py:367, 428, 448`
**Issue:** The mode strings `"block"`, `"warn"`, `"mask"`, `"scrub"` appear as bare string
literals throughout. A typo in any comparison (e.g., `"masked"` vs `"mask"`) would silently fall
through to the default block. There is no centralised definition (enum or module constant) that
would catch such a typo at parse time or via IDE analysis.
**Fix:** Define a small set of constants or a `StrEnum` (Python 3.11+) in a shared location:
```python
# privguard/modes.py or top of hooks.py
class GuardMode:
    BLOCK = "block"
    WARN  = "warn"
    MASK  = "mask"
    SCRUB = "scrub"
```
Use `GuardMode.MASK` in comparisons and in tests. The fallthrough behaviour is safe (unknown modes
default to block), but the constants improve auditing and IDE navigation.

---

_Reviewed: 2026-05-25T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
