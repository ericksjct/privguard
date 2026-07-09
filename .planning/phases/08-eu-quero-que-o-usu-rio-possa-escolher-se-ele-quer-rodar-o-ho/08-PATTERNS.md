# Phase 8: Hook Mode Selector - Pattern Map

**Mapped:** 2026-05-24
**Files analyzed:** 2 (1 modified, 1 extended)
**Analogs found:** 2 / 2

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `privguard/hooks.py` | middleware / adapter | request-response (stdin JSON → exit code) | `privguard/hooks.py` itself (existing branches) | exact — extending existing dispatch chain |
| `tests/test_claude_hooks.py` | test | request-response (hook invocation via monkeypatch) | `tests/test_claude_hooks.py` itself (existing mode tests) | exact — extending existing parametrized tests |

---

## Pattern Assignments

### `privguard/hooks.py` — mask branch in `main_user_prompt()` (lines 180-228)

**Analog:** `privguard/hooks.py` — existing `scrub` branch (lines 205-220) and default block branch (lines 222-228).

The new `mask` branch must be inserted **between the existing `warn` branch (line 200) and the `scrub` branch (line 205)**. The `scrub` branch is removed.

**Imports pattern** (lines 1-14) — no new imports needed; `mask_text` and `verify_mask` from `privguard.masking` must be added:

```python
# Add to existing import block at the top of hooks.py:
from .masking import mask_text, verify_mask
# Existing imports remain unchanged:
from .detection import detect
from .diagnostics import format_hit_summary, summarize_hits, to_json
from .policy import classify_command, classify_path
```

**Mode dispatch context** (lines 194-228) — the full shape of the dispatch chain to understand insertion point:

```python
# Line 194
mode = os.environ.get("PII_GUARD_MODE", "block")
hits = list(detect(prompt, min_score=threshold))
if not hits:
    _audit_log(event="UserPromptSubmit", action="allow", reason_code="no_pii")
    return 0

if mode == "warn":                          # line 200 — warn branch (unchanged)
    _audit_log(event="UserPromptSubmit", action="warn", reason_code="pii_detected")
    print(_prompt_json_context(reason_code="pii_detected", hits=hits, mode=mode))
    return 0

if mode == "scrub":                         # lines 205-220 — REMOVE THIS BRANCH
    ...
    return 2

# default block                             # lines 222-228
_audit_log(event="UserPromptSubmit", action="block", reason_code="pii_detected")
sys.stderr.write(
    "[PII-GUARD BLOQUEADO] "
    + _prompt_diagnostic(action="block", reason_code="pii_detected", hits=hits)
    + "\n"
)
return 2
```

**Core mask branch pattern** — insert after `warn`, before default block (scrub branch removed):

```python
if mode == "mask":
    mask_result = mask_text(prompt, hits=hits)
    if not mask_result.verified:
        _audit_log(
            event="UserPromptSubmit",
            action="block",
            reason_code="mask_verification_failed",
        )
        sys.stderr.write(
            "[PII-GUARD BLOQUEADO] "
            + _prompt_diagnostic(
                action="block",
                reason_code="mask_verification_failed",
                hits=hits,
            )
            + "\n"
        )
        return 2
    _audit_log(event="UserPromptSubmit", action="block", reason_code="pii_masked")
    sys.stderr.write(
        "[PII-GUARD BLOQUEADO] "
        + _prompt_diagnostic(action="block", reason_code="pii_masked", hits=hits)
        + "\n"
    )
    sys.stderr.write("[PII-GUARD VERSAO MASCARADA]\n")
    sys.stderr.write(mask_result.text + "\n")
    sys.stderr.write("[Reenvie o prompt acima com os valores mascarados]\n")
    return 2
```

**scrub removal pattern** — replace the `if mode == "scrub":` block with an optional one-line notice that falls through to default block:

```python
if mode == "scrub":
    sys.stderr.write("[PII-GUARD] modo scrub removido, usando block\n")
    # falls through to default block below
```

**Error handling pattern** — matches existing pattern throughout hooks.py; `_audit_log` never raises (lines 17-41), `mask_text` and `verify_mask` do not raise on normal inputs. The mask branch must check `mask_result.verified` before writing `mask_result.text` to stderr (to avoid emitting unverified/PII-containing text — see Pitfall 3 in RESEARCH.md).

---

### `privguard/hooks.py` — mode-aware `inline_pii` check in `main_pre_tool()` (lines 303-312)

**Analog:** `privguard/hooks.py` — existing `_LLM_ORCHESTRATION_TOOLS` branch (lines 303-312).

**Current state** (lines 303-312):

```python
if tool in _LLM_ORCHESTRATION_TOOLS:
    threshold = _inline_threshold()
    for text in _iter_text_values(tool_input):
        if detect(text, min_score=threshold):
            return _deny_pre_tool(
                reason_code="inline_pii",
                category="llm_orchestration",
                command_count=1,
            )
    return 0
```

**Mode-aware replacement pattern** — read `PII_GUARD_MODE` inside the branch; `warn` is non-protective pass-through; `mask` blocks with verified-mask reason; default blocks:

```python
if tool in _LLM_ORCHESTRATION_TOOLS:
    threshold = _inline_threshold()
    mode = os.environ.get("PII_GUARD_MODE", "block")
    for text in _iter_text_values(tool_input):
        hits = list(detect(text, min_score=threshold))
        if not hits:
            continue
        if mode == "warn":
            # Non-protective pass-through for local development (existing behavior).
            continue
        if mode == "mask":
            mask_result = mask_text(text, hits=hits)
            if not mask_result.verified:
                return _deny_pre_tool(
                    reason_code="mask_verification_failed",
                    category="llm_orchestration",
                    command_count=1,
                )
            # Verified mask — block with pii_masked reason.
            # True replacement via updatedInput is not available for LLM orchestration
            # tools (only PreToolUse file tools support updatedInput).
            return _deny_pre_tool(
                reason_code="pii_masked",
                category="llm_orchestration",
                command_count=1,
            )
        # Default: block
        return _deny_pre_tool(
            reason_code="inline_pii",
            category="llm_orchestration",
            command_count=1,
        )
    return 0
```

**Key constraint:** Protected-path blocking (`check_path_tool`, `check_glob_grep`) and Bash/PowerShell `classify_command` branches (lines 314-336) are NOT touched — they remain mode-agnostic per D-02.

---

### `tests/test_claude_hooks.py` — new mask mode tests

**Analog:** `tests/test_claude_hooks.py` — existing parametrized mode test `test_non_blocking_prompt_modes_are_labeled_non_protective_and_sanitized` (lines 305-322) and `test_user_prompt_blocks_synthetic_cpf_by_default` (lines 84-102).

**Test helper pattern** (lines 22-39) — `run_user_prompt` already accepts `mode=` kwarg:

```python
def run_user_prompt(
    monkeypatch: pytest.MonkeyPatch,
    payload: object | str,
    *,
    mode: str | None = None,
) -> int:
    if mode is None:
        monkeypatch.delenv("PII_GUARD_MODE", raising=False)
    else:
        monkeypatch.setenv("PII_GUARD_MODE", mode)
    ...
    return main_user_prompt()
```

**Forbidden-output guard pattern** (lines 52-63) — `assert_no_prompt_derived_text` checks for raw CPF, prompt snippets, placeholders (`<BR_CPF>`), and other leak vectors. New mask mode tests MUST call this function:

```python
def assert_no_prompt_derived_text(output: str) -> None:
    forbidden = (
        RAW_CPF,          # "123.456.789-09"
        PROMPT_SNIPPET,   # "analise o cadastro"
        SECRET_LOOKING,   # "sk-test-abcdefghijklmnopqrstuvwxyz"
        "<BR_CPF>",       # masked placeholder must not leak via _prompt_diagnostic
        "redacted=",
        "CPF ",
        "api_key",
        "sk-test-",
    )
    for value in forbidden:
        assert value not in output
```

NOTE: `mask_result.text` (the masked version shown to user) WILL contain `<BR_CPF>` as a placeholder. This means the `<BR_CPF>` forbidden check in `assert_no_prompt_derived_text` will fire if the masked text is emitted. New mask-mode tests must either (a) use a custom forbidden list that removes `<BR_CPF>` (since showing `<BR_CPF>` in the masked version is intentional), or (b) assert only the raw CPF is absent. The key invariant is that `RAW_CPF` never appears in output.

**Parametrize update pattern** (line 305) — after scrub removal, update the parametrize list:

```python
# Before (line 305):
@pytest.mark.parametrize("mode", ["warn", "scrub"])

# After:
@pytest.mark.parametrize("mode", ["warn"])
```

**New test structure patterns** — modeled on `test_user_prompt_blocks_synthetic_cpf_by_default` (lines 84-102):

```python
def test_user_prompt_mask_mode_blocks_and_shows_masked_version(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prompt = f"{PROMPT_SNIPPET}: CPF {RAW_CPF}"

    assert run_user_prompt(monkeypatch, {"prompt": prompt}, mode="mask") == 2

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert captured.out == ""
    assert "BLOQUEADO" in captured.err
    assert "reason=pii_masked" in output
    assert "VERSAO MASCARADA" in captured.err
    assert "<BR_CPF>" in captured.err          # masked placeholder is intentional output
    assert RAW_CPF not in output               # raw CPF must never appear
    assert PROMPT_SNIPPET not in output        # prompt snippet must not leak
```

```python
def test_user_prompt_mask_mode_verification_failure_blocks_without_masked_text(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Force verify_mask to return False by monkeypatching
    # OR use a prompt that mask_text will fail to verify (if such case is constructible
    # with synthetic data). The safer approach is monkeypatching mask_text to return
    # a MaskResult with verified=False.
    from privguard.masking import MaskResult
    from privguard import hooks

    fake_result = MaskResult(
        text=f"CPF {RAW_CPF}",   # still contains PII — verification intentionally failed
        changed=False,
        verified=False,
        verification_status="failed",
        reason_codes=("original_value_remaining",),
        hits=(),
    )
    monkeypatch.setattr(hooks, "mask_text", lambda *a, **kw: fake_result)

    prompt = f"{PROMPT_SNIPPET}: CPF {RAW_CPF}"
    assert run_user_prompt(monkeypatch, {"prompt": prompt}, mode="mask") == 2

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "BLOQUEADO" in captured.err
    assert "reason=mask_verification_failed" in output
    assert "VERSAO MASCARADA" not in output    # must NOT show unverified masked text
    assert RAW_CPF not in output              # raw PII must not appear even in failure path
```

```python
def test_user_prompt_mask_mode_clean_prompt_allows(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run_user_prompt(
        monkeypatch, {"prompt": "texto publico sem dados sensiveis"}, mode="mask"
    ) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
```

```python
@pytest.mark.parametrize("tool_name", ["Agent", "Task", "TaskCreate", "TaskUpdate"])
def test_pre_tool_mask_mode_llm_orchestration_blocks_pii(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tool_name: str,
) -> None:
    monkeypatch.setenv("PII_GUARD_MODE", "mask")
    payload = {
        "tool_name": tool_name,
        "tool_input": {"prompt": f"{PROMPT_SNIPPET}: CPF {RAW_CPF}"},
    }

    assert run_pre_tool(monkeypatch, payload) == 2

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "category=llm_orchestration" in output
    assert "reason=pii_masked" in output or "reason=mask_verification_failed" in output
    assert_no_prompt_derived_text(output)
```

---

## Shared Patterns

### `_audit_log()` call signature
**Source:** `privguard/hooks.py` lines 17-41 (definition), lines 45-46, 68 (call sites)
**Apply to:** Both new mask branches (`main_user_prompt` and `main_pre_tool`)

```python
_audit_log(
    event="UserPromptSubmit",   # or "PreToolUse"
    action="block",
    reason_code="pii_masked",   # or "mask_verification_failed"
    category="",                # leave empty for UserPromptSubmit; "llm_orchestration" for PreToolUse
)
```

New reason codes for Phase 8:
- `pii_masked` — mask verified, prompt blocked with masked version shown to user
- `mask_verification_failed` — `verify_mask()` returned `False`, prompt blocked without showing masked text

### `_prompt_diagnostic()` call signature
**Source:** `privguard/hooks.py` lines 121-139 (definition), lines 224-226 (call site)
**Apply to:** New mask branch in `main_user_prompt()`

```python
_prompt_diagnostic(
    action="block",
    reason_code="pii_masked",       # or "mask_verification_failed"
    hits=hits,
    # NOTE: do NOT pass mode= here — that parameter adds "mode_scope=local_development_non_protective"
    # which only applies to warn mode (non-protective). Mask mode IS protective (exits 2).
)
```

### `_deny_pre_tool()` call signature
**Source:** `privguard/hooks.py` lines 50-70 (definition), lines 307-311 (call site)
**Apply to:** New mask branch in `main_pre_tool()` LLM orchestration section

```python
_deny_pre_tool(
    reason_code="pii_masked",           # or "mask_verification_failed"
    category="llm_orchestration",
    command_count=1,
)
```

### Sanitized output invariant
**Source:** `tests/test_claude_hooks.py` lines 52-63 (`assert_no_prompt_derived_text`)
**Apply to:** All new test cases

`RAW_CPF`, `PROMPT_SNIPPET`, and `SECRET_LOOKING` must never appear in stderr or stdout output. When the masked version (`mask_result.text`) is written to stderr, it will contain `<BR_CPF>` placeholders — this is intentional. The `<BR_CPF>` entry in `forbidden` is meant to prevent placeholder leakage through `_prompt_diagnostic`, not through the deliberate masked-version display. New mask-mode tests that assert the masked version is shown should NOT include `<BR_CPF>` in their forbidden list, but MUST include `RAW_CPF`.

### Synthetic-only fixture rule
**Source:** `.planning/PROJECT.md` (canonical), `tests/test_masking.py` lines 11-12 (example)
**Apply to:** All new test cases

All test fixtures must use fake/synthetic Brazilian IDs and secrets. `RAW_CPF = "123.456.789-09"` (line 16 of test_claude_hooks.py) is the canonical synthetic CPF. Do not introduce real PII in test data.

---

## No Analog Found

None — both modified files are existing files with directly reusable patterns.

---

## Metadata

**Analog search scope:** `privguard/` (all modules), `tests/` (all test files)
**Files scanned:** 10 source files, 12 test files
**Pattern extraction date:** 2026-05-24

### Critical Constraints Carried Forward

1. **Exit code 2 = block, exit 0 = allow** — never changed. Mask mode exits 2.
2. **`mask_result.verified` must be checked before writing `mask_result.text` to stderr** — Pitfall 3 from RESEARCH.md.
3. **`additionalContext` + exit 0 is explicitly rejected** — PII reaches Claude. Any code path that sets additionalContext to masked text and returns 0 is wrong.
4. **Protected-path and Bash classification branches in `main_pre_tool()` are mode-agnostic** — do not add `mode` reads there.
5. **`_prompt_diagnostic()` called without `mode=` in mask branch** — the `mode=` kwarg adds `mode_scope=local_development_non_protective` which must not appear on protective (exit 2) paths.
