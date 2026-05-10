# Phase 03: Claude Enforcement - Pattern Map

**Mapped:** 2026-05-03
**Files analyzed:** 11
**Analogs found:** 11 / 11

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `privguard/hooks.py` | middleware | request-response | `privguard/hooks.py` | exact |
| `privguard/policy.py` | service | transform | `privguard/policy.py` | exact |
| `privguard/diagnostics.py` | utility | transform | `privguard/diagnostics.py` | exact |
| `privguard/cli.py` | controller | request-response | `privguard/cli.py` | exact |
| `hooks/pii_guard.py` | middleware | request-response | `hooks/pii_guard.py` | exact |
| `hooks/pre_tool_guard.py` | middleware | request-response | `hooks/pre_tool_guard.py` | exact |
| `.claude/settings.json` | config | event-driven | `.claude/settings.json` | exact |
| `tests/test_claude_hooks.py` | test | request-response | `tests/test_cli.py`, `tests/test_policy.py` | role-match |
| `tests/test_policy_commands.py` | test | transform | `tests/test_policy.py` | exact |
| `tests/test_claude_doctor.py` | test | request-response | `tests/test_cli.py` | exact |
| `pyproject.toml` or pytest config | config | batch | `pyproject.toml` | exact |

## Pattern Assignments

### `privguard/hooks.py` (middleware, request-response)

**Analog:** `privguard/hooks.py`

**Imports pattern** (lines 5-12):
```python
import json
import os
import re
import sys

from .detection import detect
from .masking import redact
from .policy import EXFIL_CMDS, READ_CMDS, SENSITIVE_GLOBS, format_hit_summary, is_sensitive_path
```

**Hook denial pattern** (lines 15-17):
```python
def deny(prefix: str, reason_code: str) -> int:
    sys.stderr.write(f"[{prefix} BLOQUEADO] reason={reason_code}\n")
    return 2
```

**Malformed JSON fail-open pattern** (lines 57-61 and 107-111):
```python
try:
    payload = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    return 0
```

**Prompt hook pattern to harden** (lines 63-75, 100-104):
```python
prompt = payload.get("prompt", "") or ""
if not prompt.strip():
    return 0

threshold = float(os.environ.get("PII_GUARD_THRESHOLD", "0.7"))
mode = os.environ.get("PII_GUARD_MODE", "block")
hits = list(detect(prompt, min_score=threshold))
if not hits:
    return 0

summary = format_hit_summary(hits)
redacted = redact(prompt, hits)
```

Planner note: keep `detect()` and threshold handling, but remove hook output of `redacted` or any prompt-derived text. Phase 3 output must be metadata only.

**Tool dispatch pattern** (lines 113-136):
```python
tool = payload.get("tool_name", "")
tool_input = payload.get("tool_input", {}) or {}
if not isinstance(tool_input, dict):
    tool_input = {}

if tool in ("Read", "Edit", "Write", "NotebookEdit"):
    ok, reason_code = check_path_tool(tool_input)
    if not ok:
        return deny("PRE-TOOL-GUARD", reason_code)
    return 0
```

Planner note: extend this dispatcher for `MultiEdit`, notebook read paths, broader shell-capable tool names, and unknown file-capable tools if `.claude/settings.json` moves to `*`.

### `privguard/policy.py` (service, transform)

**Analog:** `privguard/policy.py`

**Imports and dataclass pattern** (lines 5-12, 24-29):
```python
import re
from dataclasses import dataclass
from typing import Sequence

from .detection import DetectionReport, Hit
from .diagnostics import format_hit_summary as _format_hit_summary
from .diagnostics import summarize_hits as _summarize_hits
from .masking import MaskResult

@dataclass(frozen=True)
class PathClassification:
    is_protected: bool
    category: str
    reason_code: str
```

**Protected path pattern** (lines 83-116):
```python
def _normalize_path(path: str) -> str:
    value = str(path or "").strip().strip("\"'")
    value = value.replace("\\", "/")
    value = re.sub(r"/+", "/", value)
    parts: list[str] = []
    for part in value.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    prefix = "/" if value.startswith("/") else ""
    return (prefix + "/".join(parts)).lower()

def classify_path(path: str) -> PathClassification:
    p = _normalize_path(path)
    name = p.rsplit("/", 1)[-1] if p else ""
```

**Policy decision pattern** (lines 149-157, 164-173, 193-196):
```python
def decide_policy(
    capability: str = SurfaceCapability.UNKNOWN,
    hits: Sequence[Hit] | None = None,
    report: DetectionReport | None = None,
    mask_result: MaskResult | None = None,
    path_classification: PathClassification | None = None,
    mode: str = PolicyMode.STRICT,
    payload_text: str | None = None,
) -> PolicyDecision:
```

```python
if path_classification is not None:
    reasons.append(path_classification.reason_code)
    if path_classification.is_protected:
        return _decision(
            PolicyAction.BLOCK,
            normalized_capability,
            (*reasons, "protected_path"),
            hit_count,
            protected_path=True,
        )
```

```python
if normalized_capability == SurfaceCapability.BLOCK_ONLY:
    if hit_count:
        return _decision(PolicyAction.BLOCK, normalized_capability, (*reasons, "sensitive_hits_block_only"), hit_count, protected_path)
    return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "no_sensitive_hits"), 0, protected_path)
```

Planner note: put new command category regexes and command classification helpers here, beside `READ_CMDS` and `EXFIL_CMDS` (lines 69-80), so hooks stay orchestration-only.

### `privguard/diagnostics.py` (utility, transform)

**Analog:** `privguard/diagnostics.py`

**Sanitized serializer pattern** (lines 13-26, 34-42, 50-56):
```python
def summarize_hits(hits: Any) -> list[dict[str, object]]:
    return [to_dict(hit) for hit in tuple(hits)]

def to_dict(value: Any) -> Any:
    if isinstance(value, Hit):
        return {
            "kind": value.kind,
            "start": value.start,
            "end": value.end,
            "score": value.score,
            "reason_code": value.reason_code,
            "source": value.source,
        }
```

```python
if isinstance(value, MaskResult):
    return {
        "changed": value.changed,
        "verified": value.verified,
        "verification_status": value.verification_status,
        "reason_codes": list(value.reason_codes),
        "hit_count": len(value.hits),
        "hits": summarize_hits(value.hits),
    }
```

```python
if is_dataclass(value):
    result: dict[str, Any] = {}
    for name in getattr(value, "__dataclass_fields__", {}):
        if name in {"value", "text"}:
            continue
        result[name] = to_dict(getattr(value, name))
    return result
```

**JSON and compact text pattern** (lines 61-72, 75-88):
```python
def to_json(value: Any) -> str:
    return json.dumps(to_dict(value), ensure_ascii=False, sort_keys=True)

def format_hit_summary(hits: Any) -> str:
    return ", ".join(
        (
            f"{hit.kind}@{hit.start}:{hit.end} "
            f"score={hit.score:.2f} reason={hit.reason_code}"
        )
        for hit in tuple(hits)
    )
```

Planner note: new hook and doctor outputs should reuse `to_dict()`, `to_json()`, and `format_hit_summary()` or add metadata-only helpers here. Do not serialize `Hit.value`, `MaskResult.text`, original prompts, protected path strings, or redacted prompt text.

### `privguard/cli.py` (controller, request-response)

**Analog:** `privguard/cli.py`

**Imports pattern** (lines 5-13):
```python
import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

from . import __version__
from .detection import analyze_text, detect
from .diagnostics import format_text, to_dict, to_json
from .masking import mask_text
from .policy import SurfaceCapability, classify_path, decide_policy
```

**Subcommand handler pattern** (lines 34-40, 52-73):
```python
def cmd_scan(args: argparse.Namespace) -> int:
    report = analyze_text(_read_text(args))
    if args.json:
        print(to_json(report))
    else:
        print(format_text(report))
    return 0
```

```python
def cmd_policy_check(args: argparse.Namespace) -> int:
    text = _read_text(args)
    hits = detect(text)
    mask_result = mask_text(text, hits=hits) if args.masked else None
    path_classification = classify_path(args.path) if args.path else None
    decision = decide_policy(
        capability=args.capability,
        hits=hits,
        mask_result=mask_result,
        path_classification=path_classification,
        payload_text=mask_result.text if mask_result is not None else text,
    )
```

**Parser registration pattern** (lines 76-106):
```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="privguard")
    subparsers = parser.add_subparsers(required=True)

    info = subparsers.add_parser("info")
    info.set_defaults(func=cmd_info)
```

Planner note: add `claude` as a subparser with a `doctor` subparser or add `claude-doctor`; keep command handlers returning `0` for pass and non-zero for failed checks. Synthetic doctor output should include an audit-visible marker such as `synthetic_data: true`.

### `hooks/pii_guard.py` (middleware, request-response)

**Analog:** `hooks/pii_guard.py`

**Thin adapter pattern** (lines 1-11):
```python
"""Claude UserPromptSubmit hook adapter for privguard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from privguard.hooks import main_user_prompt

if __name__ == "__main__":
    raise SystemExit(main_user_prompt())
```

Planner note: keep this file tiny and stable for `.claude/settings.json`. Do not duplicate detection, masking, policy, or output formatting here.

### `hooks/pre_tool_guard.py` (middleware, request-response)

**Analog:** `hooks/pre_tool_guard.py`

**Thin adapter pattern** (lines 1-11):
```python
"""Claude PreToolUse hook adapter for privguard."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from privguard.hooks import main_pre_tool

if __name__ == "__main__":
    raise SystemExit(main_pre_tool())
```

Planner note: keep this file a stable adapter. Expand tool handling in `privguard.hooks` and command/path policy in `privguard.policy`.

### `.claude/settings.json` (config, event-driven)

**Analog:** `.claude/settings.json`

**Permission deny pattern** (lines 3-24):
```json
"permissions": {
  "deny": [
    "Read(./data_sensivel/**)",
    "Read(./cooperados/**)",
    "Read(./dump_*)",
    "Read(./.env)",
    "Read(./.env.*)"
  ]
}
```

**Hook wiring pattern** (lines 26-48):
```json
"hooks": {
  "UserPromptSubmit": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR/hooks/pii_guard.py\""
        }
      ]
    }
  ],
  "PreToolUse": [
    {
      "matcher": "Read|Bash|Grep|Glob|Edit|Write",
      "hooks": [
        {
          "type": "command",
          "command": "python \"$CLAUDE_PROJECT_DIR/hooks/pre_tool_guard.py\""
        }
      ]
    }
  ]
}
```

Planner note: Phase 3 should evaluate changing the `PreToolUse` matcher to `*` or adding `MultiEdit`, notebook, and other file-capable tool names. Preserve the `CLAUDE_PROJECT_DIR` path style.

### `tests/test_claude_hooks.py` (test, request-response)

**Analogs:** `tests/test_cli.py`, `tests/test_policy.py`

**Pytest capture pattern** (`tests/test_cli.py` lines 19-27):
```python
def test_scan_human_output_is_sanitized(capsys: pytest.CaptureFixture[str]) -> None:
    raw_cpf = "123.456.789-09"

    assert main(["scan", f"CPF {raw_cpf}"]) == 0

    out = capsys.readouterr().out
    assert "BR_CPF" in out
    assert raw_cpf not in out
```

**Synthetic path and no-file-I/O pattern** (`tests/test_policy.py` lines 21-36, 49-53):
```python
cases = {
    ".env": ("env_file", "protected_path_env"),
    ".env.local": ("env_file", "protected_path_env"),
    r"data_sensivel\synthetic.csv": ("protected_data", "protected_path_data"),
}

for path, expected in cases.items():
    classification = classify_path(path)
    assert classification.is_protected is True
```

```python
source = pathlib.Path("privguard/policy.py").read_text(encoding="utf-8")

assert ".read_text(" not in source
assert ".open(" not in source
```

Planner note: tests should monkeypatch `sys.stdin` for hook JSON payloads and capture `stderr`/`stdout`. Assert exit code `2` for blocked synthetic prompt/tool payloads, `0` for clean and malformed JSON, and no raw synthetic value or redacted placeholder output.

### `tests/test_policy_commands.py` (test, transform)

**Analog:** `tests/test_policy.py`

**Parameterized-style policy assertions to copy** (lines 21-47, 130-139):
```python
for path, expected in cases.items():
    classification = classify_path(path)
    assert classification.is_protected is True
    assert (classification.category, classification.reason_code) == expected
    assert is_sensitive_path(path) is True
```

```python
decision = decide_policy(
    SurfaceCapability.REWRITE_CAPABLE,
    hits=[],
    path_classification=classify_path(".env"),
)

assert decision.action == PolicyAction.BLOCK
assert decision.protected_path is True
assert "protected_path" in decision.reason_codes
```

Planner note: test command classification as pure string transforms. Use synthetic protected path strings such as `.env`, `data_sensivel/synthetic.csv`, and `exports/dump_synthetic.txt`; do not create or read those files.

### `tests/test_claude_doctor.py` (test, request-response)

**Analog:** `tests/test_cli.py`

**CLI command invocation pattern** (lines 10-17, 122-130):
```python
def test_info_command_returns_package_metadata(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["info"]) == 0

    out = capsys.readouterr().out

    assert "privguard" in out
    assert "detectors: lightweight" in out
```

```python
assert main(["policy-check", "--json", "--path", ".env", "texto publico"]) == 2

out = capsys.readouterr().out
payload = json.loads(out)
assert payload["path"]["category"] == "env_file"
assert ".env" not in out
```

Planner note: `claude doctor` tests should load CLI output as JSON when `--json` is passed, assert `synthetic_data is True`, and assert synthetic raw prompt/secret values and protected path strings are absent from rendered output.

### `pyproject.toml` or pytest config (config, batch)

**Analog:** `pyproject.toml`

**Current package config pattern** (lines 1-23):
```toml
[build-system]
requires = ["setuptools >= 77.0.3"]
build-backend = "setuptools.build_meta"

[project]
name = "privguard"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[project.scripts]
privguard = "privguard.cli:main"
privacy-guard = "privguard.cli:main"

[tool.setuptools.packages.find]
include = ["privguard"]
```

Planner note: if pytest collection hygiene is needed, add config in this file rather than introducing an unrelated config style. Keep runtime dependencies empty for Phase 3 unless a hard requirement appears.

## Shared Patterns

### Stable Hook Adapters

**Source:** `hooks/pii_guard.py` lines 1-11 and `hooks/pre_tool_guard.py` lines 1-11  
**Apply to:** `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, `.claude/settings.json`

Keep hook entry files as compatibility shims and route all behavior through package functions:
```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from privguard.hooks import main_pre_tool

if __name__ == "__main__":
    raise SystemExit(main_pre_tool())
```

### Fail-Closed Policy

**Source:** `privguard/policy.py` lines 149-215  
**Apply to:** hook prompt decisions, tool decisions, doctor synthetic probes

Use `decide_policy()` and `SurfaceCapability.BLOCK_ONLY` for Claude prompt surfaces. Unknown/external surfaces block unless the payload is verified masked and exactly matches the masked output.

### Protected Path Classification Without File I/O

**Source:** `privguard/policy.py` lines 83-120; `tests/test_policy.py` lines 49-53  
**Apply to:** `privguard/policy.py`, `privguard/hooks.py`, `privguard/cli.py`, all Claude tests

Protected files are classified from strings only:
```python
def is_sensitive_path(path: str) -> bool:
    return classify_path(path).is_protected
```

Lock the invariant with the existing source inspection test:
```python
assert ".read_text(" not in source
assert ".open(" not in source
```

### Metadata-Only Diagnostics

**Source:** `privguard/diagnostics.py` lines 17-26, 34-42, 50-56; `tests/test_masking.py` lines 125-141  
**Apply to:** hook stderr/stdout, doctor JSON, CLI output, tests

Use serializers that omit raw values and masked payloads:
```python
if isinstance(value, Hit):
    return {
        "kind": value.kind,
        "start": value.start,
        "end": value.end,
        "score": value.score,
        "reason_code": value.reason_code,
        "source": value.source,
    }
```

Existing test expectation:
```python
assert raw_cpf not in rendered_report
assert raw_cpf not in rendered_mask
assert "<BR_CPF>" not in rendered_mask
assert "<BR_CPF>" not in rendered_text
```

### Synthetic Fixtures Only

**Source:** `tests/test_detection.py` lines 14-21 and `tests/test_policy.py` lines 21-30  
**Apply to:** all new tests and `privguard claude doctor`

Use fictional values already present in tests, such as `CPF 123.456.789-09`, `CNPJ 12.345.678/0001-95`, synthetic token strings, `.env`, and `data_sensivel/synthetic.csv`. Never read `.env` or `data_sensivel/**`.

### CLI Subcommand Shape

**Source:** `privguard/cli.py` lines 76-106  
**Apply to:** `privguard claude doctor`

Register new commands through `argparse` subparsers and dispatch through `set_defaults(func=...)`. Return `0` for success and non-zero for failed validation checks.

## No Analog Found

All expected Phase 3 files have at least a role-match analog in the current codebase. The closest gap is `privguard claude doctor`: no existing nested CLI group exists, but `privguard/cli.py` provides the direct subcommand pattern and `tests/test_cli.py` provides CLI test style.

## Metadata

**Analog search scope:** `privguard/**`, `hooks/**`, `tests/**`, `.claude/settings.json`, `pyproject.toml`; excluded `.env` and `data_sensivel/**`.
**Files scanned:** 19
**Pattern extraction date:** 2026-05-03
