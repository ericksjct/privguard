# Phase 04: Codex Compatibility Evidence - Pattern Map

**Mapped:** 2026-05-03
**Files analyzed:** 8
**Analogs found:** 7 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `docs/codex-compatibility.md` | documentation | transform | `.planning/REQUIREMENTS.md` + `.planning/phases/04-codex-compatibility-evidence/04-RESEARCH.md` | partial |
| `privguard/codex.py` | config / utility | transform | `privguard/policy.py` | role-match |
| `tests/test_codex_compatibility.py` | test | transform | `tests/test_policy.py` | role-match |
| `tests/test_codex_claim_gate.py` | test | batch / transform | `tests/test_claude_phase_gate.py` | role-match |
| `privguard/diagnostics.py` | utility | request-response | `privguard/diagnostics.py` Claude doctor helpers | exact-if-needed |
| `privguard/cli.py` | controller / CLI | request-response | `privguard/cli.py` Claude subcommand wiring | exact-if-needed |
| `tests/test_codex_doctor.py` | test | request-response | `tests/test_claude_doctor.py` | exact-if-needed |
| `.codex/hooks.json.example` | config | event-driven | none in repo | no-analog |

## Pattern Assignments

### `docs/codex-compatibility.md` (documentation, transform)

**Analog:** `.planning/REQUIREMENTS.md` for auditable requirement rows; `04-RESEARCH.md` for matrix content.

**Requirements pattern** (`.planning/REQUIREMENTS.md` lines 48-52):
```markdown
### Codex

- [ ] **CDX-01**: Project documents the current Codex interception options and whether prompt/tool payloads can be blocked or rewritten before provider submission.
- [ ] **CDX-02**: Project includes a compatibility matrix that marks Codex support as supported, experimental, block-only, or unsupported with evidence.
- [ ] **CDX-03**: Guard does not claim automatic Codex masking until a tested integration proves raw payloads are replaced before submission.
```

**Roadmap success pattern** (`.planning/ROADMAP.md` lines 76-83):
```markdown
### Phase 4: Codex Compatibility Evidence
**Goal**: Codex support is represented honestly through tested interception evidence, capability labels, and no automatic masking claims until raw payload replacement is proven.
**Depends on**: Phase 2
**Requirements**: CDX-01, CDX-02, CDX-03
**Success Criteria** (what must be TRUE):
  1. Developer can read a current Codex compatibility assessment that states which prompt and tool interception options were verified.
  2. Developer can see each Codex surface labeled as supported, experimental, block-only, or unsupported with evidence.
  3. Developer cannot enable or encounter a claim of automatic Codex masking unless a tested integration proves raw outbound payloads are replaced before provider submission.
```

**Core documentation pattern:** make each row explicit: surface, user-facing label, `SurfaceCapability`, evidence source, tested version or docs date, privacy action, and gaps. Do not use a single broad "Codex supported" row.

---

### `privguard/codex.py` (config / utility, transform)

**Analog:** `privguard/policy.py`

**Imports pattern** (`privguard/policy.py` lines 3-12):
```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .masking import MaskResult
```

For `privguard/codex.py`, prefer:
```python
from __future__ import annotations

from dataclasses import dataclass

from .policy import SurfaceCapability
```

**Capability vocabulary pattern** (`privguard/policy.py` lines 40-55):
```python
class SurfaceCapability:
    REWRITE_CAPABLE = "rewrite-capable"
    BLOCK_ONLY = "block-only"
    OBSERVE_ONLY = "observe-only"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    EXTERNAL = "external"

    ALL = {
        REWRITE_CAPABLE,
        BLOCK_ONLY,
        OBSERVE_ONLY,
        UNSUPPORTED,
        UNKNOWN,
        EXTERNAL,
    }
```

**Decision semantics to preserve** (`privguard/policy.py` lines 261-288):
```python
if normalized_capability == SurfaceCapability.REWRITE_CAPABLE:
    if hit_count == 0:
        return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "no_sensitive_hits"), 0, protected_path)
    if mask_result and mask_result.verified:
        return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "mask_verified"), hit_count, protected_path)
    return _decision(PolicyAction.PAUSE, normalized_capability, (*reasons, "mask_required"), hit_count, protected_path)

if normalized_capability == SurfaceCapability.BLOCK_ONLY:
    if hit_count:
        return _decision(PolicyAction.BLOCK, normalized_capability, (*reasons, "sensitive_hits_block_only"), hit_count, protected_path)
    return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "no_sensitive_hits"), 0, protected_path)
```

**Core pattern to copy:** define frozen dataclass rows with explicit fields and a tuple/list constant. Each Codex row should map user labels back to `SurfaceCapability`; `automatic_masking` must default to `False` unless proof fields demonstrate verified outbound replacement.

---

### `tests/test_codex_compatibility.py` (test, transform)

**Analog:** `tests/test_policy.py`

**Imports pattern** (`tests/test_policy.py` lines 1-18):
```python
from __future__ import annotations

import json
import pathlib

from privguard.detection import detect
from privguard.diagnostics import to_dict, to_json
from privguard.masking import mask_text
from privguard.policy import (
    PathClassification,
    PolicyAction,
    PolicyDecision,
    PolicyMode,
    SurfaceCapability,
    classify_path,
    decide_policy,
    is_sensitive_path,
)
```

For Codex compatibility tests, import `CODEX_COMPATIBILITY` from `privguard.codex` and `SurfaceCapability` from `privguard.policy`.

**Capability/fail-closed test pattern** (`tests/test_policy.py` lines 99-106):
```python
def test_block_only_unknown_external_and_unsupported_fail_closed() -> None:
    hits = detect("CPF 123.456.789-09")

    assert decide_policy(SurfaceCapability.BLOCK_ONLY, hits=hits).action == PolicyAction.BLOCK
    assert decide_policy(SurfaceCapability.UNKNOWN, hits=[]).action == PolicyAction.BLOCK
    assert decide_policy(SurfaceCapability.EXTERNAL, hits=[]).action == PolicyAction.BLOCK
    assert decide_policy(SurfaceCapability.UNSUPPORTED, hits=hits).action == PolicyAction.BLOCK
    assert decide_policy(SurfaceCapability.OBSERVE_ONLY, hits=hits).action == PolicyAction.BLOCK
```

**Verified-payload-only pattern** (`tests/test_policy.py` lines 109-131):
```python
raw_decision = decide_policy(
    SurfaceCapability.EXTERNAL,
    hits=hits,
    mask_result=result,
    payload_text=raw_text,
)
decision = decide_policy(
    SurfaceCapability.EXTERNAL,
    hits=hits,
    mask_result=result,
    payload_text=result.text,
)

assert raw_decision.action == PolicyAction.BLOCK
assert decision.allow is True
assert "payload_masked" in decision.reason_codes
```

**Validation pattern:** assert every Codex matrix row has `surface`, `support_label`, `surface_capability`, `evidence`, `tested_version_or_docs_date`, `privacy_action`, `gaps`, and `automatic_masking`; assert `surface_capability in SurfaceCapability.ALL`; assert rows with `automatic_masking is False` are not `rewrite-capable`.

---

### `tests/test_codex_claim_gate.py` (test, batch / transform)

**Analog:** `tests/test_claude_phase_gate.py`

**Fixture and forbidden-output pattern** (`tests/test_claude_phase_gate.py` lines 13-50):
```python
RAW_CPF = "123.456.789-09"
FAKE_SECRET = "sk-test-abcdefghijklmnopqrstuvwxyz"
PROTECTED_ENV = ".env"
PROTECTED_DATA_PATH = "data_sensivel/synthetic.csv"
PROMPT_SNIPPET = "analise o cadastro"

FORBIDDEN_OUTPUT = (
    RAW_CPF,
    FAKE_SECRET,
    PROTECTED_ENV,
    PROTECTED_DATA_PATH,
    "data_sensivel",
    PROMPT_SNIPPET,
    "CPF ",
    "sk-test-",
    "<BR_CPF>",
    "<TOKEN>",
)

def _assert_forbidden_values_absent(output: str) -> None:
    for value in FORBIDDEN_OUTPUT:
        assert value not in output
```

**Phase gate assertion pattern** (`tests/test_claude_phase_gate.py` lines 102-129):
```python
assert cli_main(["claude", "doctor", "--json"]) == 0

captured = capsys.readouterr()
output = captured.out + captured.err
payload = json.loads(captured.out)

assert captured.err == ""
assert payload["command"] == "claude doctor"
assert payload["synthetic_data"] is True

checks = {check["name"]: check for check in payload["checks"]}
assert all(check["result"] == "pass" for check in checks.values())
_assert_forbidden_values_absent(output)
```

**Claim gate pattern:** scan safe repo text targets only, excluding `.env`, `data_sensivel/**`, `.git/**`, cache directories, and planning artifacts if desired. Fail on phrases such as "automatic Codex masking", "Codex rewrite-capable", or "Codex masks prompts automatically" unless the matrix contains an `automatic_masking=True` row with proof fields.

---

### `privguard/diagnostics.py` (utility, request-response, optional)

**Analog:** existing Claude doctor helpers in `privguard/diagnostics.py`

**Synthetic constants pattern** (`privguard/diagnostics.py` lines 14-19):
```python
SYNTHETIC_DOCTOR_PROMPT = (
    "Validacao sintetica CPF 123.456.789-09 "
    "token=sk-test-abcdefghijklmnopqrstuvwxyz"
)
SYNTHETIC_DOCTOR_PATH = "data_sensivel/synthetic.csv"
SYNTHETIC_DOCTOR_COMMAND = f"Get-Content {SYNTHETIC_DOCTOR_PATH} | Set-Clipboard"
```

**Sanitized serialization pattern** (`privguard/diagnostics.py` lines 26-71):
```python
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
    ...
    if is_dataclass(value):
        result: dict[str, Any] = {}
        for name in getattr(value, "__dataclass_fields__", {}):
            if name in {"value", "text"}:
                continue
            result[name] = to_dict(getattr(value, name))
        return result

def to_json(value: Any) -> str:
    return json.dumps(to_dict(value), ensure_ascii=False, sort_keys=True)
```

**Doctor check pattern** (`privguard/diagnostics.py` lines 109-126):
```python
def _doctor_check(
    name: str,
    passed: bool,
    reason_codes: list[str] | None = None,
    *,
    synthetic_data: bool | None = None,
    metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    check: dict[str, object] = {
        "name": name,
        "result": _check_result(passed),
        "reason_codes": list(reason_codes or []),
    }
    if synthetic_data is not None:
        check["synthetic_data"] = synthetic_data
    if metadata:
        check["metadata"] = metadata
    return check
```

**Protected config path pattern** (`privguard/diagnostics.py` lines 129-144):
```python
def _load_claude_settings(settings_path: str | Path) -> tuple[dict[str, Any], list[str]]:
    from .policy import classify_path

    if classify_path(str(settings_path)).is_protected:
        return {}, ["settings_path_protected"]

    try:
        with Path(settings_path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return {}, ["settings_missing"]
    except (OSError, json.JSONDecodeError, ValueError):
        return {}, ["settings_unreadable"]
```

**Use if planner adds a Codex doctor:** copy the doctor report shape, but name it `codex doctor`, keep `synthetic_data=True`, and do not read protected paths or require provider submission.

---

### `privguard/cli.py` (controller / CLI, request-response, optional)

**Analog:** existing CLI command handlers in `privguard/cli.py`

**Imports pattern** (`privguard/cli.py` lines 5-20):
```python
import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

from . import __version__
from .detection import analyze_text, detect
from .diagnostics import (
    build_claude_doctor_report,
    claude_doctor_passed,
    format_claude_doctor_text,
    format_text,
    to_dict,
    to_json,
)
from .masking import mask_text
from .policy import SurfaceCapability, classify_path, decide_policy
```

**Command handler pattern** (`privguard/cli.py` lines 99-105):
```python
def cmd_claude_doctor(args: argparse.Namespace) -> int:
    report = build_claude_doctor_report(args.settings)
    if args.json:
        print(to_json(report))
    else:
        print(format_claude_doctor_text(report))
    return 0 if claude_doctor_passed(report) else 2
```

**Subcommand wiring pattern** (`privguard/cli.py` lines 137-143):
```python
claude = subparsers.add_parser("claude")
claude_subparsers = claude.add_subparsers(required=True)

doctor = claude_subparsers.add_parser("doctor")
doctor.add_argument("--json", action="store_true")
doctor.add_argument("--settings", default=".claude/settings.json")
doctor.set_defaults(func=cmd_claude_doctor)
```

**Use if planner adds a Codex doctor:** add a sibling `codex` parser with `doctor`; keep exit code `2` for failed checks and JSON/human output parity. Do not add this unless local Codex probing can stay synthetic and no-provider.

---

### `tests/test_codex_doctor.py` (test, request-response, optional)

**Analog:** `tests/test_claude_doctor.py`

**Synthetic fixture pattern** (`tests/test_claude_doctor.py` lines 11-28):
```python
SYNTHETIC_CPF = "123.456.789-09"
SYNTHETIC_SECRET = "sk-test-abcdefghijklmnopqrstuvwxyz"
SYNTHETIC_PROTECTED_PATH = "data_sensivel/synthetic.csv"
SYNTHETIC_ENV_PATH = ".env"
SYNTHETIC_PROMPT = f"CPF {SYNTHETIC_CPF} token={SYNTHETIC_SECRET}"
SYNTHETIC_COMMAND = f"Get-Content {SYNTHETIC_PROTECTED_PATH} | Set-Clipboard"

FORBIDDEN_OUTPUT_VALUES = (
    SYNTHETIC_CPF,
    SYNTHETIC_SECRET,
    SYNTHETIC_PROTECTED_PATH,
    SYNTHETIC_ENV_PATH,
    SYNTHETIC_PROMPT,
    SYNTHETIC_COMMAND,
    "<BR_CPF>",
    "<TOKEN>",
)
```

**JSON doctor test pattern** (`tests/test_claude_doctor.py` lines 36-62):
```python
assert main(["claude", "doctor", "--json"]) == 0

captured = capsys.readouterr()
rendered = captured.out + captured.err
payload = json.loads(captured.out)

assert payload["command"] == "claude doctor"
assert payload["synthetic_data"] is True
assert captured.err == ""

checks = {check["name"]: check for check in payload["checks"]}
assert all(check["result"] == "pass" for check in checks.values())
_assert_sanitized(rendered)
```

**Protected settings path test pattern** (`tests/test_claude_doctor.py` lines 105-119):
```python
assert main(["claude", "doctor", "--json", "--settings", SYNTHETIC_ENV_PATH]) == 2

captured = capsys.readouterr()
rendered = captured.out + captured.err
payload = json.loads(captured.out)
checks = {check["name"]: check for check in payload["checks"]}

assert checks["hook_wiring"]["result"] == "fail"
assert "settings_path_protected" in checks["hook_wiring"]["reason_codes"]
assert captured.err == ""

_assert_sanitized(rendered)
```

**Use if planner adds a Codex doctor:** update command names and expected check names, but keep synthetic-only fixtures and sanitized assertions.

## Shared Patterns

### Surface Capability Mapping
**Source:** `privguard/policy.py` lines 40-55 and 261-288  
**Apply to:** `privguard/codex.py`, `tests/test_codex_compatibility.py`, `docs/codex-compatibility.md`

Use `SurfaceCapability` as the machine vocabulary. User-facing labels should map conservatively:

| User label | Internal capability |
|------------|---------------------|
| supported masking | `rewrite-capable` only with verified outbound replacement proof |
| block-only | `block-only` |
| experimental block-only | `block-only` plus explicit gaps |
| observe-only | `observe-only` |
| unsupported | `unsupported` |
| unknown / unproven | `unknown` |

### Verified Masking Proof
**Source:** `tests/test_policy.py` lines 109-131  
**Apply to:** any Codex row or test that considers `automatic_masking=True`

Positive masking requires `payload_text == mask_result.text`; raw payload plus verified mask is still blocked.

### Sanitized Diagnostics
**Source:** `privguard/diagnostics.py` lines 26-71  
**Apply to:** docs examples, optional doctor output, all tests

Serializers must omit dataclass fields named `value` and `text`; JSON output should include counts, kinds, offsets, reason codes, evidence labels, and pass/fail results only.

### Synthetic-Only Evidence
**Source:** `tests/test_claude_phase_gate.py` lines 13-50 and `tests/test_claude_doctor.py` lines 11-28  
**Apply to:** all Phase 04 tests and optional probes

Use synthetic CPF/token/path fixtures. Do not read `.env` or `data_sensivel/**`; protected paths are validated by string classification only.

### Protected Path Handling
**Source:** `privguard/policy.py` lines 134-155 and `tests/test_policy.py` lines 21-57  
**Apply to:** optional Codex probe/doctor and claim gate exclusion logic

Protected paths should be detected by normalization and regex/string classification. Tests may read source files to prove policy code does not call `.read_text()` or `.open()`, but must not read protected paths.

### Optional CLI Shape
**Source:** `privguard/cli.py` lines 99-143  
**Apply to:** optional `privguard codex doctor`

CLI commands return `0` on pass, `2` on failed checks, support `--json`, and route output through `to_json()` or a safe human formatter.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.codex/hooks.json.example` | config | event-driven | No project-local `.codex/` config exists. If added, derive content from current official Codex docs and keep it clearly marked as an example, not active protection. |

## Metadata

**Analog search scope:** `privguard/`, `tests/`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, phase context/research docs.  
**Excluded:** `.env`, `data_sensivel/**`, cache directories with access denied.  
**Files scanned:** 18 safe source/planning files plus repo file listing.  
**Pattern extraction date:** 2026-05-03
