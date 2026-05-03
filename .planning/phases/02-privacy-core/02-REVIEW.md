---
phase: 02-privacy-core
reviewed: 2026-05-03T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - privguard/__init__.py
  - privguard/cli.py
  - privguard/detection.py
  - privguard/diagnostics.py
  - privguard/masking.py
  - privguard/policy.py
  - pyproject.toml
  - tests/test_cli.py
  - tests/test_detection.py
  - tests/test_masking.py
  - tests/test_policy.py
findings:
  critical: 0
  warning: 1
  info: 6
  total: 7
status: has_issues
---

# Phase 02: Code Review Report

**Reviewed:** 2026-05-03T00:00:00Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** has_issues

## Summary

Re-review of the Phase 02 privacy core (detection, irreversible masking, protected-path classification, fail-closed policy decisions, sanitized diagnostics, CLI wiring). The prior REVIEW.md marked this phase clean; this pass re-examines the same surface and surfaces one Warning and several Info-level concerns that the previous review missed.

The implementation is solid in its core security posture: the diagnostics serializer skips `value`/`text` fields, masking runs a re-detect verification on the masked output, the policy ladder treats UNKNOWN/EXTERNAL/UNSUPPORTED/OBSERVE_ONLY as fail-closed when hits are present, and the CLI wires the masked payload (not the raw text) into the policy authorization check. Test scope hygiene is good — only synthetic identifiers (the canonical test CPF `123.456.789-09`, fake-format tokens, fake `.env`/`data_sensivel` paths) are used, with no real PII or secrets.

The Warning addresses a genuine fail-open path in the public masking API: `mask_text(text, hits=[])` short-circuits `verify_mask` to a "verified" status even when the underlying text contains unmasked sensitive data. This is reachable through the public API surface (not the CLI, which always sources hits from `detect`), and contradicts the irreversible masking guarantee. The Info items cover dead policy code (`READ_CMDS`, `EXFIL_CMDS`, `SENSITIVE_GLOBS`), an over-broad path-classification regex that flags benign filenames like `monkey.py`, and minor diagnostics/CLI ergonomics.

## Warnings

### WR-01: `verify_mask` short-circuits to verified when caller passes empty hits, allowing the public masking API to fail-open

**File:** `privguard/masking.py:62-63` (and indirectly `privguard/masking.py:87-94`)

**Issue:** `verify_mask` has an early return on empty hits:

```python
if not hits:
    return True, ("no_sensitive_hits",)
```

`mask_text(text, hits=[])` therefore returns `MaskResult(verified=True, verification_status="verified", reason_codes=("no_sensitive_hits",), text=<original text unchanged>)` even when `text` contains sensitive data. The masking layer's own re-detect verification is skipped entirely on the empty-hits path, so a caller that supplies `hits=[]` (intentionally or by mistake) gets a "verified" mask result on raw sensitive content. Downstream `decide_policy` for REWRITE_CAPABLE will then ALLOW that payload (`mask_result.verified` is True, so the policy hits the `mask_verified` branch).

The CLI is not affected today (it sources hits from `detect`), but `mask_text`/`verify_mask` are exported in `privguard/__init__.py` and documented as the public API for irreversible masking. Any future caller (hooks, integrations, tests) that constructs hits lazily and passes an empty list will silently bypass the irreversibility guarantee. This contradicts MASK-02 (re-detect verification) for the empty-hits path.

**Fix:** Always run a residual re-detect on the masked text, regardless of whether the caller supplied hits. Treat `not hits` as "trust nothing" rather than "trust everything":

```python
def verify_mask(
    original_text: str,
    masked_text: str,
    hits: Sequence[Hit],
    min_score: float = 0.6,
) -> tuple[bool, tuple[str, ...]]:
    reason_codes: list[str] = []

    for hit in hits:
        if hit.value and hit.value in masked_text:
            reason_codes.append("original_value_remaining")

    residual_hits = [
        hit for hit in detect(masked_text, min_score=min_score)
        if not _is_safe_placeholder_residual(hit.value)
    ]
    if residual_hits:
        reason_codes.append("residual_detection")

    if reason_codes:
        return False, tuple(dict.fromkeys(reason_codes))

    if not hits:
        return True, ("no_sensitive_hits",)
    return True, ("mask_verified",)
```

Add a regression test in `tests/test_masking.py`:

```python
def test_mask_text_does_not_fail_open_when_caller_passes_empty_hits() -> None:
    text = "CPF 123.456.789-09"
    result = mask_text(text, hits=[])
    assert result.verified is False
    assert "residual_detection" in result.reason_codes
```

## Info

### IN-01: `READ_CMDS` and `EXFIL_CMDS` regex constants in `policy.py` are dead code

**File:** `privguard/policy.py:69-80`

**Issue:** `READ_CMDS` (line 69) and `EXFIL_CMDS` (line 76) are compiled regexes intended for command-pattern classification, but no function in the module references them, and no caller imports them. They are not exported in `privguard/__init__.py`. This appears to be partially-implemented surface-classification logic from an earlier design pass.

**Fix:** Either wire these into `decide_policy` (e.g., as a heuristic for surface inference when `capability=UNKNOWN` and `payload_text` matches an exfil command) and add tests, or remove them. Leaving compiled-but-unused regex at module scope is a code-quality smell that suggests incomplete logic.

### IN-02: `SENSITIVE_GLOBS` is dead code and out of sync with the live classifier

**File:** `privguard/policy.py:14-21`

**Issue:** `SENSITIVE_GLOBS` is defined but never iterated by `classify_path` or any other function. The live classifier at `policy.py:104-116` re-implements equivalent rules inline, and the two implementations have diverged: `SENSITIVE_GLOBS` matches `dump_*.<a-z>+` (line 17) while the inline classifier matches `dump_*.<a-z0-9>+` (line 110). This dual definition risks future drift — a contributor updating one set will likely miss the other.

**Fix:** Remove `SENSITIVE_GLOBS` and rely on the inline `classify_path` implementation, or refactor `classify_path` to iterate `SENSITIVE_GLOBS` (using `(category, reason_code)` tuples alongside each pattern) so there is a single source of truth for protected-path rules.

### IN-03: `classify_path` filename heuristic flags benign names containing `key`/`secret`/`token`

**File:** `privguard/policy.py:114`

**Issue:** The regex `re.search(r"(?:secret|segredo|token|key)", name)` matches the substring anywhere inside the filename, so files like `monkey.py`, `donkey.json`, `tokenizer.py`, `keystore_helpers.py`, `secretary.csv`, or `gtoken_parser.go` are classified as `secret_filename` and unconditionally BLOCKED in `decide_policy`. The same applies to `re.search(r"(?:credentials?|credenciais?)", name)` at line 112 (less prone to false positives but still substring-based).

The fail-closed posture is correct in spirit, but over-blocking common dev filenames will erode trust and push integrators toward whitelisting/escape-hatches that weaken the overall guarantee.

**Fix:** Anchor the filename heuristic to whole tokens or boundary-delimited components. For example:

```python
# Match "secret" as a whole word/token within the filename, not as a substring.
if re.search(r"(?:^|[._\-])(?:secret|segredo|token|key|api[_\-]?key)(?:[._\-]|$)", name):
    return PathClassification(True, "secret_filename", "protected_path_secret_name")
```

This still flags `tmp/segredo-local.txt` and `secrets.json` while excluding `monkey.py` and `tokenizer.py`. Update `tests/test_policy.py::test_classify_path_detects_protected_strings_without_file_io` to add at least one negative case (e.g., `assert classify_path("tools/tokenizer.py").is_protected is False`).

### IN-04: `to_dict` allowlist is fragile — only fields named `value`/`text` are skipped

**File:** `privguard/diagnostics.py:50-56`

**Issue:** The generic dataclass branch in `to_dict` excludes only the two field names `{"value", "text"}`. Any future dataclass added to the package that stores raw sensitive data under a differently-named field (e.g., `raw`, `payload`, `secret`, `original`, `data`) would be silently serialized through `to_json`, bypassing the no-raw-values diagnostic guarantee. The current code is correct because no such field exists today, but the design relies on every future contributor knowing this allowlist.

**Fix:** Invert the policy from a denylist to a per-dataclass opt-in. Either (a) require dataclasses to declare a `__diagnostic_fields__` class attribute listing fields safe to serialize, falling back to the current allowlist for dataclasses without it; or (b) keep the current behavior but extend the skip set to include `{"value", "text", "raw", "payload", "secret", "original", "data"}` and add a unit test that fails when a new dataclass is introduced without explicit diagnostic coverage.

### IN-05: `cmd_policy_check` collapses BLOCK and PAUSE into a single non-zero exit code

**File:** `privguard/cli.py:73`

**Issue:** `return 0 if decision.allow else 2` — both `PolicyAction.BLOCK` and `PolicyAction.PAUSE` produce exit code `2`. A shell caller (or hook) cannot distinguish "denied, do not retry" (BLOCK) from "deferred, mask and retry" (PAUSE) without parsing JSON output. The PAUSE outcome semantically maps to a different remediation flow (mask the payload, re-invoke) than BLOCK (refuse the operation entirely).

**Fix:** Use distinct exit codes per action, e.g.:

```python
if decision.action == PolicyAction.ALLOW:
    return 0
if decision.action == PolicyAction.PAUSE:
    return 3
return 2  # BLOCK and any unknown action
```

Document the exit code contract in the CLI help and add a CLI test asserting each action maps to its expected code.

### IN-06: `format_text` non-JSON branch for `policy-check` falls through to `str(dict)`

**File:** `privguard/cli.py:72` (calls `format_text(payload)` from `privguard/diagnostics.py:75-93`)

**Issue:** `cmd_policy_check` non-JSON path calls `format_text({"decision": ..., "path": ...})`. The `format_text` function in `diagnostics.py` only has formatting branches for dicts containing `counts` (DetectionReport) or `verification_status` (MaskResult). The policy payload has neither, so the function falls through to `return str(data)`, producing Python's default dict repr — readable but not designed for human consumption (single line, includes Python quoting). The test `test_policy_check_blocks_unknown_by_default` only asserts that `fail_closed_surface` appears in the output, which it does, so the gap is silent.

**Fix:** Add a branch in `format_text` for policy decision payloads (e.g., when `data` is a dict containing a `decision` key with an `action` subfield), rendering action, allow flag, capability, and reason codes in a stable single-line format. Also add a CLI test asserting the human output includes the action verbatim (e.g., `assert "action=block" in out`) so future drift is caught.

---

_Reviewed: 2026-05-03T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
