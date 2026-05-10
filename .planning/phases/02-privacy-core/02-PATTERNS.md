# Phase 02: privacy-core - Pattern Map

**Mapped:** 2026-05-02
**Files analyzed:** 11 new/modified files
**Analogs found:** 11 / 11

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `privguard/detection.py` | service / model | transform | `privguard/detection.py` | exact |
| `privguard/masking.py` | service / utility | transform | `privguard/masking.py` | exact |
| `privguard/policy.py` | service / model | request-response | `privguard/policy.py` | exact |
| `privguard/diagnostics.py` | utility | transform | `privguard/policy.py` + `privguard/hooks.py` | role-match |
| `privguard/cli.py` | controller / CLI | request-response | `privguard/cli.py` | exact |
| `privguard/hooks.py` | controller / adapter | request-response | `privguard/hooks.py` | exact |
| `privguard/__init__.py` | config / package API | transform | `privguard/__init__.py` | exact |
| `pyproject.toml` | config | batch | `pyproject.toml` | exact |
| `tests/test_detection.py` | test | batch | `privguard/detection.py` + `demos/test_presidio_br.py` | role-match |
| `tests/test_masking.py` | test | batch | `privguard/masking.py` | role-match |
| `tests/test_policy.py` | test | batch | `privguard/policy.py` + `privguard/hooks.py` | role-match |

## Pattern Assignments

### `privguard/detection.py` (service / model, transform)

**Analog:** `privguard/detection.py`

**Imports pattern** (lines 3-7):
```python
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable
```

**Model pattern** (lines 10-16):
```python
@dataclass
class Hit:
    kind: str
    start: int
    end: int
    value: str
    score: float
```

**Validator pattern** (lines 19-33):
```python
def _digits(s: str) -> str:
    return re.sub(r"\D", "", s)


def valida_cpf(cpf: str) -> bool:
    cpf = _digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for i in (9, 10):
        s = sum(int(cpf[n]) * ((i + 1) - n) for n in range(i))
        d = (s * 10) % 11
        d = 0 if d == 10 else d
        if d != int(cpf[i]):
            return False
    return True
```

**Detector registry pattern** (lines 68-87):
```python
PatternEntry = tuple[str, re.Pattern[str], float, Callable[[str], bool] | None]

PATTERNS: list[PatternEntry] = [
    ("BR_CPF", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"), 0.95, valida_cpf),
    ("BR_CNPJ", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"), 0.95, valida_cnpj),
    ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), 0.85, valida_luhn),
]
```

**Core transform and overlap pattern** (lines 90-107):
```python
def detect(text: str, min_score: float = 0.6) -> list[Hit]:
    raw: list[Hit] = []
    for kind, rx, score, validator in PATTERNS:
        for m in rx.finditer(text):
            value = m.group(0)
            hit_score = score
            if validator and not validator(value):
                hit_score = 0.05
            raw.append(Hit(kind, m.start(), m.end(), value, hit_score))

    raw = [h for h in raw if h.score >= min_score]
    raw.sort(key=lambda h: (-h.score, h.start))
    kept: list[Hit] = []
    for h in raw:
        if not any(not (h.end <= k.start or h.start >= k.end) for k in kept):
            kept.append(h)
    kept.sort(key=lambda h: h.start)
    return kept
```

**BR validator reference:** port missing validators from `demos/test_presidio_br.py` lines 70-129 (`valida_cnh`, `valida_titulo_eleitor`, `valida_pis`, `valida_cartao_sus`) and recognizer coverage from lines 164-267. Keep formulas, but expose through stdlib package patterns.

---

### `privguard/masking.py` (service / utility, transform)

**Analog:** `privguard/masking.py`

**Imports pattern** (lines 3-5):
```python
from __future__ import annotations

from .detection import Hit
```

**Core replacement pattern** (lines 8-16):
```python
def redact(text: str, hits: list[Hit]) -> str:
    out = []
    cursor = 0
    for h in hits:
        out.append(text[cursor:h.start])
        out.append(f"<{h.kind}>")
        cursor = h.end
    out.append(text[cursor:])
    return "".join(out)
```

**Planner note:** evolve this exact cursor-based replacement into `MaskResult` / `mask_text()` and verification. Keep irreversible typed placeholders. Do not create deanonymization maps.

---

### `privguard/policy.py` (service / model, request-response)

**Analog:** `privguard/policy.py`

**Imports pattern** (lines 3-7):
```python
from __future__ import annotations

import re

from .detection import Hit
```

**Protected path pattern** (lines 9-16):
```python
SENSITIVE_GLOBS = [
    re.compile(r"(?:^|[\\/])data_sensivel(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])cooperados(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])dump_[\w\-]+\.[a-z]+$", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])\.env(?:\.[a-z]+)?$", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])credenciais[\w\-.]*", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])segredo[\w\-.]*", re.IGNORECASE),
]
```

**Path classification primitive** (lines 32-36):
```python
def is_sensitive_path(path: str) -> bool:
    if not path:
        return False
    p = path.replace("\\", "/").lower()
    return any(rx.search(p) for rx in SENSITIVE_GLOBS)
```

**Sanitized summary pattern** (lines 39-48):
```python
def summarize_hits(hits: list[Hit]) -> list[dict[str, object]]:
    return [
        {
            "kind": h.kind,
            "start": h.start,
            "end": h.end,
            "score": h.score,
        }
        for h in hits
    ]
```

**Decision analog:** `privguard/hooks.py` lines 15-17 centralizes block exit codes:
```python
def deny(prefix: str, reason_code: str) -> int:
    sys.stderr.write(f"[{prefix} BLOQUEADO] reason={reason_code}\n")
    return 2
```

**Planner note:** expand boolean path checks into `PathClassification` with reason codes. Add `SurfaceCapability` and `PolicyDecision` here or in a sibling module, preserving fail-closed defaults for `unknown` and `external`.

---

### `privguard/diagnostics.py` (utility, transform)

**Analog:** `privguard/policy.py` + `privguard/hooks.py`

**Sanitized data source pattern:** use only the metadata emitted by `summarize_hits()` in `privguard/policy.py` lines 39-48. Do not serialize `Hit.value`.

**JSON output pattern** (`privguard/hooks.py` lines 76-85):
```python
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": (
            f"[PII-GUARD aviso] reason=pii_detected detections={summary}; "
            f"redacted={redacted}"
        ),
    }
}))
```

**Text summary pattern** (`privguard/policy.py` lines 51-55):
```python
def format_hit_summary(hits: list[Hit]) -> str:
    return ", ".join(
        f"{h.kind}@{h.start}:{h.end} score={h.score:.2f}"
        for h in hits
    )
```

**Planner note:** copy JSON construction style, but do not copy `redacted={redacted}` into diagnostics. Phase 2 diagnostics should include reason codes, counts, offsets, scores, policy decision, and capability only.

---

### `privguard/cli.py` (controller / CLI, request-response)

**Analog:** `privguard/cli.py`

**Imports pattern** (lines 3-8):
```python
from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version

from . import __version__
```

**Subcommand pattern** (lines 23-31):
```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="privguard")
    subparsers = parser.add_subparsers(required=True)

    info = subparsers.add_parser("info")
    info.set_defaults(func=cmd_info)

    args = parser.parse_args(argv)
    return args.func(args)
```

**Entry-point pattern** (lines 34-35):
```python
if __name__ == "__main__":
    raise SystemExit(main())
```

**Planner note:** add `scan`, `mask`, and policy/diagnostic commands using this subparser pattern. Prefer explicit `--json` to choose structured output.

---

### `privguard/hooks.py` (controller / adapter, request-response)

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

**Fail-open malformed input pattern** (lines 57-61 and 107-111):
```python
try:
    payload = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    return 0
```

**Tool-policy pattern** (lines 118-134):
```python
if tool in ("Read", "Edit", "Write", "NotebookEdit"):
    ok, reason_code = check_path_tool(tool_input)
    if not ok:
        return deny("PRE-TOOL-GUARD", reason_code)
    return 0
```

**Planner note:** keep hook adapters thin. Move shared policy decision and diagnostics into package core so Phase 3 can consume them without duplicating behavior.

---

### `privguard/__init__.py` (config / package API, transform)

**Analog:** `privguard/__init__.py`

**Export pattern** (lines 1-8):
```python
"""Local privacy guard package for code-agent workflows."""

from .detection import Hit, detect
from .masking import redact

__version__ = "0.1.0"

__all__ = ["Hit", "detect", "redact", "__version__"]
```

**Planner note:** export stable result types and top-level core functions only after the Phase 2 API is settled. Keep raw-value-bearing internals out of diagnostics exports.

---

### `pyproject.toml` (config, batch)

**Analog:** `pyproject.toml`

**Dependency-light package pattern** (lines 5-16):
```toml
[project]
name = "privguard"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
full = [
    "presidio-analyzer==2.2.362; python_version < '3.14'",
    "presidio-anonymizer==2.2.362",
    "spacy==3.8.14",
]
```

**CLI entry pattern** (lines 18-19):
```toml
[project.scripts]
privguard = "privguard.cli:main"
```

**Planner note:** if adding the `privacy-guard` command alias, copy this console script pattern and point it at the same `privguard.cli:main`.

---

### `tests/test_detection.py` (test, batch)

**Analog:** `privguard/detection.py` + `demos/test_presidio_br.py`

**Core behavior to test:** validator checksum downgrade from `privguard/detection.py` lines 90-100 and overlap selection lines 101-107.

**Fixture source pattern:** use only synthetic values like the demo docstring states in `demos/test_presidio_br.py` lines 17-18:
```python
Todos os dados abaixo são FICTÍCIOS, gerados apenas para teste.
```

**BR coverage reference:** validators from `demos/test_presidio_br.py` lines 70-129 and recognizer entities from lines 164-267.

**Planner note:** no existing pytest files exist. Create pytest tests with fake fixtures only; never read `.env` or `data_sensivel/**`.

---

### `tests/test_masking.py` (test, batch)

**Analog:** `privguard/masking.py`

**Core behavior to test:** cursor replacement from `privguard/masking.py` lines 8-16.

**Expected assertions:** typed placeholders are present, original synthetic hit values are absent, and no deanonymization map or reversible state is returned.

**Planner note:** tests should validate verification failure paths by constructing a synthetic missed/remaining value case without printing that raw value in failure messages.

---

### `tests/test_policy.py` (test, batch)

**Analog:** `privguard/policy.py` + `privguard/hooks.py`

**Path policy behavior to test:** normalized string matching from `privguard/policy.py` lines 32-36 and protected categories from lines 9-16.

**Fail-closed behavior to test:** denial pattern from `privguard/hooks.py` lines 15-17 and tool check branching from lines 118-134.

**Diagnostic leak behavior to test:** summary output from `privguard/policy.py` lines 39-55 must not include `Hit.value`.

**Planner note:** include Windows and POSIX separators, relative paths, `.env.*`, dumps, credential-like names, and `data_sensivel/**` by path string only.

## Shared Patterns

### Dependency-Light Core

**Source:** `pyproject.toml` lines 5-16 and `privguard/detection.py` lines 3-7  
**Apply to:** `privguard/detection.py`, `privguard/masking.py`, `privguard/policy.py`, `privguard/diagnostics.py`, hook hot paths

Keep the default package stdlib-only. Presidio remains optional/reference.

### Internal Raw Values, External Sanitized Summaries

**Source:** `privguard/detection.py` lines 10-16, `privguard/policy.py` lines 39-55  
**Apply to:** diagnostics, policy decisions, CLI output, hook output, tests

Raw `Hit.value` exists for masking and verification only. Serializers must consume metadata fields only.

### Fail-Closed Policy

**Source:** `privguard/hooks.py` lines 15-17, 118-134  
**Apply to:** policy decisions and downstream hook integrations

Use explicit reason codes and return structured decisions. Unknown, external, unsupported, and unverified masking paths must block or pause by default.

### Thin Adapter Boundary

**Source:** `hooks/pii_guard.py` lines 1-11 and `hooks/pre_tool_guard.py` lines 1-11  
**Apply to:** future Claude/Codex client adapters

Adapters insert the repo root into `sys.path`, import package entry points, and exit through `raise SystemExit(...)`. Shared behavior belongs in `privguard/`.

### Protected Path Hygiene

**Source:** `privguard/policy.py` lines 9-36  
**Apply to:** path classifiers, tests, CLI, hooks

Classify protected paths by string normalization and regex/category matching. Do not open protected paths.

## No Analog Found

All inferred Phase 2 files have at least a role-match analog. There is no existing pytest suite, so test files should copy behavior from package modules and use standard pytest conventions.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| None | - | - | All files have exact or role-match analogs. |

## Metadata

**Analog search scope:** `privguard/`, `hooks/`, `demos/`, `pyproject.toml`, `.planning/REQUIREMENTS.md`  
**Files scanned:** 17 source/config/planning files, excluding `.env` and `data_sensivel/**` contents  
**Pattern extraction date:** 2026-05-02
