# Phase 1: Package Foundation - Pattern Map

**Mapped:** 2026-05-01
**Files analyzed:** 14
**Analogs found:** 13 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pyproject.toml` | config | batch | none in repo | no-local-analog |
| `privguard/__init__.py` | config | transform | `hooks/_pii_core.py` | partial |
| `privguard/detection.py` | utility | transform | `hooks/_pii_core.py` | exact |
| `privguard/masking.py` | utility | transform | `hooks/_pii_core.py` | exact |
| `privguard/policy.py` | config | request-response | `hooks/pre_tool_guard.py` | role-match |
| `privguard/hooks.py` | service | request-response | `hooks/pii_guard.py`, `hooks/pre_tool_guard.py` | exact |
| `privguard/cli.py` | controller | request-response | `ollama_local_demo.py` | role-match |
| `hooks/_pii_core.py` | adapter | transform | `hooks/_pii_core.py` | exact |
| `hooks/pii_guard.py` | adapter | request-response | `hooks/pii_guard.py` | exact |
| `hooks/pre_tool_guard.py` | adapter | request-response + file-I/O policy | `hooks/pre_tool_guard.py` | exact |
| `demos/test_presidio.py` | demo | batch transform | `test_presidio.py` | exact |
| `demos/test_presidio_br.py` | demo | batch transform | `test_presidio_br.py` | exact |
| `demos/reversible_demo.py` | demo | batch transform | `reversible_demo.py` | exact |
| `demos/ollama_local_demo.py` | demo | request-response | `ollama_local_demo.py` | exact |

## Pattern Assignments

### `pyproject.toml` (config, batch)

**Analog:** none in repo

No local packaging file exists. Use the researched PyPA/setuptools pattern from `01-RESEARCH.md`: PEP 517/518 build system, PEP 621 project metadata, `[project.scripts] privguard = "privguard.cli:main"`, flat package discovery, and optional `[full]` extras only. Do not put Presidio/spaCy in default dependencies.

**Required shape from research:**
```toml
[build-system]
requires = ["setuptools >= 77.0.3"]
build-backend = "setuptools.build_meta"

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

[project.scripts]
privguard = "privguard.cli:main"

[tool.setuptools.packages.find]
include = ["privguard"]
```

---

### `privguard/detection.py` (utility, transform)

**Analog:** `hooks/_pii_core.py`

**Imports pattern** (`hooks/_pii_core.py` lines 5-7):
```python
import re
from dataclasses import dataclass
from typing import List, Callable, Optional
```

**Data model pattern** (`hooks/_pii_core.py` lines 10-16):
```python
@dataclass
class Hit:
    kind: str
    start: int
    end: int
    value: str
    score: float
```

**Brazilian validator pattern** (`hooks/_pii_core.py` lines 19-33):
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

**Core detection pattern** (`hooks/_pii_core.py` lines 68-86, 89-110):
```python
PATTERNS: List[tuple] = [
    ("BR_CPF", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"), 0.95, valida_cpf),
    ("BR_CNPJ", re.compile(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b"), 0.95, valida_cnpj),
    ("CREDIT_CARD", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), 0.85, valida_luhn),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b"), 0.95, None),
    ("API_KEY", re.compile(r"\b(?:sk-(?:ant-)?[\w-]{20,}|sk_(?:live|test)_[\w]+)\b"), 0.99, None),
]


def detect(text: str, min_score: float = 0.6) -> List[Hit]:
    raw: List[Hit] = []
    for kind, rx, score, validator in PATTERNS:
        for m in rx.finditer(text):
            v = m.group(0)
            s = score
            if validator:
                if not validator(v):
                    s = 0.05
            raw.append(Hit(kind, m.start(), m.end(), v, s))

    raw = [h for h in raw if h.score >= min_score]
    raw.sort(key=lambda h: (-h.score, h.start))
    kept: List[Hit] = []
    for h in raw:
        if not any(not (h.end <= k.start or h.start >= k.end) for k in kept):
            kept.append(h)
    kept.sort(key=lambda h: h.start)
    return kept
```

**Important adjustment for package code:** keep `Hit.value` for internal masking, but diagnostics and CLI output must summarize hits without printing `value`.

---

### `privguard/masking.py` (utility, transform)

**Analog:** `hooks/_pii_core.py`

**Masking pattern** (`hooks/_pii_core.py` lines 113-121):
```python
def redact(text: str, hits: List[Hit]) -> str:
    out = []
    cursor = 0
    for h in hits:
        out.append(text[cursor:h.start])
        out.append(f"<{h.kind}>")
        cursor = h.end
    out.append(text[cursor:])
    return "".join(out)
```

**Apply to:** `privguard.masking.redact()` or equivalent. Import `Hit` from `privguard.detection`; do not duplicate the dataclass.

---

### `privguard/policy.py` (config, request-response)

**Analog:** `hooks/pre_tool_guard.py`

**Sensitive path policy pattern** (`hooks/pre_tool_guard.py` lines 22-30, 48-52):
```python
SENSITIVE_GLOBS = [
    re.compile(r"(?:^|[\\/])data_sensivel(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])cooperados(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])dump_[\w\-]+\.[a-z]+$", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])\.env(?:\.[a-z]+)?$", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])credenciais[\w\-.]*", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])segredo[\w\-.]*", re.IGNORECASE),
]


def is_sensitive_path(path: str) -> bool:
    if not path:
        return False
    p = path.replace("\\", "/").lower()
    return any(rx.search(p) for rx in SENSITIVE_GLOBS)
```

**Tool policy pattern** (`hooks/pre_tool_guard.py` lines 60-74):
```python
def check_path_tool(tool_input: dict) -> tuple[bool, str]:
    for key in ("file_path", "path", "notebook_path"):
        v = tool_input.get(key)
        if v and is_sensitive_path(str(v)):
            return False, f"Acesso a caminho sensivel '{v}' bloqueado pela politica."
    return True, ""


def check_glob_grep(tool_input: dict) -> tuple[bool, str]:
    pattern = tool_input.get("pattern", "")
    path = tool_input.get("path", "")
    for v in (pattern, path):
        if v and is_sensitive_path(str(v)):
            return False, f"Pattern/path sensivel '{v}' bloqueado."
    return True, ""
```

**Apply to:** preserve the allow/block tuple shape for adapters, but sanitize reasons before surfacing them if they contain raw paths or inline PII.

---

### `privguard/hooks.py` (service, request-response)

**Analog:** `hooks/pii_guard.py` and `hooks/pre_tool_guard.py`

**Hook JSON parse/fail-open pattern** (`hooks/pii_guard.py` lines 19-31):
```python
def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return 0

    prompt = payload.get("prompt", "") or ""
    if not prompt.strip():
        return 0

    hits = list(detect(prompt, min_score=THRESHOLD))
    if not hits:
        return 0
```

**Mode dispatch pattern** (`hooks/pii_guard.py` lines 36-68):
```python
if MODE == "warn":
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "...",
        }
    }))
    return 0

if MODE == "scrub":
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "...",
        }
    }))
    return 0

sys.stderr.write("[PII-GUARD BLOQUEADO] ...\n")
return 2
```

**PreToolUse dispatcher pattern** (`hooks/pre_tool_guard.py` lines 110-137):
```python
def main() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return 0

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}

    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        ok, why = check_path_tool(tool_input)
        if not ok:
            return deny(why)
        return 0

    if tool in ("Glob", "Grep"):
        ok, why = check_glob_grep(tool_input)
        if not ok:
            return deny(why)
        return 0

    if tool in ("Bash", "PowerShell"):
        ok, why = check_bash(tool_input)
        if not ok:
            return deny(why)
        return 0

    return 0
```

**Required package adjustment:** replace raw summaries like `f"{h.kind}('{h.value}')"` with sanitized summaries containing kind, start, end, and score only.

---

### `privguard/cli.py` (controller, request-response)

**Analog:** `ollama_local_demo.py`

**CLI entrypoint pattern** (`ollama_local_demo.py` lines 77-100):
```python
def main() -> int:
    print(f"Ollama binario no PATH: {has_ollama_binary()}")
    server_up = has_ollama_server()
    print(f"Servidor Ollama em {OLLAMA_HOST}:{OLLAMA_PORT}: {server_up}")

    if not server_up:
        print()
        setup_instructions()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Apply to:** keep `main() -> int` plus `sys.exit(main())` when runnable as a module. For package console scripts, use `argparse` as researched and keep output sanitized:

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="privguard")
    subparsers = parser.add_subparsers(required=True)
    info = subparsers.add_parser("info")
    info.set_defaults(func=cmd_info)
    args = parser.parse_args(argv)
    return args.func(args)
```

---

### `privguard/__init__.py` (config, transform)

**Analog:** `hooks/_pii_core.py`

Use the package boundary to expose stable, low-level API only. Best candidates from `hooks/_pii_core.py` are `Hit`, `detect`, and `redact` (`hooks/_pii_core.py` lines 10-16, 89-121). Avoid importing Presidio/spaCy or demo modules from `__init__.py`.

**Recommended export shape:**
```python
from .detection import Hit, detect
from .masking import redact

__all__ = ["Hit", "detect", "redact"]
```

---

### `hooks/_pii_core.py` (adapter, transform)

**Analog:** `hooks/_pii_core.py`

If retained for compatibility, make it a thin import shim from `privguard.detection` and `privguard.masking`. Current callers import `detect` and `redact` from this module (`hooks/pii_guard.py` lines 12-13; `hooks/pre_tool_guard.py` lines 19-20). Planner should decide whether to keep this file to avoid breaking any out-of-repo script references.

---

### `hooks/pii_guard.py` (adapter, request-response)

**Analog:** `hooks/pii_guard.py`

**Current local import pattern** (`hooks/pii_guard.py` lines 7-16):
```python
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _pii_core import detect, redact  # noqa: E402

THRESHOLD = float(os.environ.get("PII_GUARD_THRESHOLD", "0.7"))
MODE = os.environ.get("PII_GUARD_MODE", "block")  # block | warn | scrub
```

**Adapter target pattern:** replace local path import with package import or delegate completely:
```python
from privguard.hooks import main_user_prompt


if __name__ == "__main__":
    raise SystemExit(main_user_prompt())
```

**Error handling to preserve** (`hooks/pii_guard.py` lines 20-23):
```python
try:
    payload = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    return 0
```

---

### `hooks/pre_tool_guard.py` (adapter, request-response + file-I/O policy)

**Analog:** `hooks/pre_tool_guard.py`

**Current local import pattern** (`hooks/pre_tool_guard.py` lines 13-20):
```python
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _pii_core import detect  # noqa: E402
```

**Deny pattern** (`hooks/pre_tool_guard.py` lines 55-57):
```python
def deny(reason: str) -> int:
    sys.stderr.write(f"[PRE-TOOL-GUARD BLOQUEADO] {reason}\n")
    return 2
```

**Adapter target pattern:** delegate to package hook entrypoint:
```python
from privguard.hooks import main_pre_tool


if __name__ == "__main__":
    raise SystemExit(main_pre_tool())
```

---

### `demos/test_presidio.py` (demo, batch transform)

**Analog:** `test_presidio.py`

**Demo structure pattern** (`test_presidio.py` lines 46-54, 75-90):
```python
def main():
    print("=" * 80)
    print("Microsoft Presidio - Teste com PII sensíveis fictícias")
    print("=" * 80)

    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    for idx, (n, text) in enumerate(chosen, 1):
        print(f"\n--- Amostra #{idx} (id original {n}) ---")
        print(f"Original : {text}")
        results = analyzer.analyze(text=text, language="en")
        anon = anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)
        print(f"Anonim.  : {anon.text}")
```

**Required adjustment:** demos can remain runnable, but default output should not print `Original : {text}` or raw snippets. Prefer redacted output or an explicit opt-in flag for raw synthetic values.

---

### `demos/test_presidio_br.py` (demo, batch transform)

**Analog:** `test_presidio_br.py`

**Optional full recognizer pattern** (`test_presidio_br.py` lines 164-185):
```python
def build_br_recognizers() -> List[EntityRecognizer]:
    cpf = ChecksumPatternRecognizer(
        supported_entity="BR_CPF",
        supported_language="pt",
        patterns=[
            Pattern("cpf_formatado", r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b", 0.6),
            Pattern("cpf_numerico",  r"\b\d{11}\b", 0.3),
        ],
        context=["cpf", "documento", "rg/cpf", "cadastro de pessoa"],
        validator=valida_cpf,
    )

    cnpj = ChecksumPatternRecognizer(
        supported_entity="BR_CNPJ",
        supported_language="pt",
        patterns=[
            Pattern("cnpj_formatado", r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", 0.7),
            Pattern("cnpj_numerico",  r"\b\d{14}\b", 0.3),
        ],
        context=["cnpj", "empresa", "razão social", "pessoa jurídica"],
        validator=valida_cnpj,
    )
```

**Analyzer construction pattern** (`test_presidio_br.py` lines 320-336):
```python
def build_analyzer() -> AnalyzerEngine:
    nlp_conf = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}],
    }
    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_conf).create_engine()

    registry = RecognizerRegistry(supported_languages=["pt"])
    registry.load_predefined_recognizers(languages=["pt"])
    for r in build_br_recognizers():
        registry.add_recognizer(r)

    return AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["pt"],
    )
```

**Required adjustment:** keep Presidio/spaCy imports out of default `privguard` modules. This file belongs under `demos/` and may fail if optional full dependencies are unavailable.

---

### `demos/reversible_demo.py` (demo, batch transform)

**Analog:** `reversible_demo.py`

**Local import reuse pattern** (`reversible_demo.py` lines 21-24):
```python
# Reuso dos recognizers BR ja construidos no test_presidio_br.py
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from test_presidio_br import build_br_recognizers
```

**Encryption demo pattern** (`reversible_demo.py` lines 67-73):
```python
encrypted = anonymizer.anonymize(
    text=text,
    analyzer_results=results,
    operators={"DEFAULT": OperatorConfig("encrypt", {"key": key})},
)
print("\n[3] Texto CIFRADO (e este que voce mandaria ao Claude):")
print(f"    {encrypted.text}")
```

**Required adjustment:** reversible deanonymization is explicitly out of Phase 1 production scope. Keep as demo only, and avoid printing original raw text by default (`reversible_demo.py` lines 57-58 currently do).

---

### `demos/ollama_local_demo.py` (demo, request-response)

**Analog:** `ollama_local_demo.py`

**Optional service probe pattern** (`ollama_local_demo.py` lines 31-41):
```python
def has_ollama_binary() -> bool:
    return shutil.which("ollama") is not None


def has_ollama_server() -> bool:
    try:
        conn = http.client.HTTPConnection(OLLAMA_HOST, OLLAMA_PORT, timeout=2)
        conn.request("GET", "/api/tags")
        return conn.getresponse().status == 200
    except OSError:
        return False
```

**Setup-output pattern** (`ollama_local_demo.py` lines 44-65):
```python
def setup_instructions() -> None:
    print("=" * 80)
    print("Ollama nao detectado. Instalacao minima (Windows):")
    print("=" * 80)
    print("  1) winget install Ollama.Ollama")
    print("     ou: https://ollama.com/download")
    print("=" * 80)
```

**Required adjustment:** this demo currently constructs a prompt containing CPF-like data (`ollama_local_demo.py` lines 87-93). Keep any such example synthetic and do not print raw sensitive-looking prompts by default.

## Shared Patterns

### Hook Entry Points
**Source:** `.claude/settings.json` lines 26-44
**Apply to:** `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`
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

Keep these file paths stable in Phase 1. Make the hook files import/delegate to `privguard` rather than changing `.claude/settings.json`.

### Fail-Open JSON Handling
**Source:** `hooks/pii_guard.py` lines 20-23 and `hooks/pre_tool_guard.py` lines 111-114
**Apply to:** all hook request handlers
```python
try:
    payload = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    return 0
```

### Blocking Exit Code
**Source:** `hooks/pre_tool_guard.py` lines 55-57 and `hooks/pii_guard.py` lines 60-68
**Apply to:** hook denial paths
```python
def deny(reason: str) -> int:
    sys.stderr.write(f"[PRE-TOOL-GUARD BLOQUEADO] {reason}\n")
    return 2
```

### Environment Configuration
**Source:** `hooks/pii_guard.py` lines 15-16
**Apply to:** prompt hook handling in `privguard.hooks`
```python
THRESHOLD = float(os.environ.get("PII_GUARD_THRESHOLD", "0.7"))
MODE = os.environ.get("PII_GUARD_MODE", "block")  # block | warn | scrub
```

### Sanitized Output Boundary
**Source:** negative pattern in `hooks/pii_guard.py` line 33 and `hooks/pre_tool_guard.py` lines 102-105
**Apply to:** `privguard.cli`, `privguard.hooks`, demo defaults
```python
# Avoid this production pattern because it prints raw matched values:
summary = ", ".join(f"{h.kind}('{h.value}')" for h in hits)

# Prefer sanitized summaries:
summary = [
    {"kind": h.kind, "start": h.start, "end": h.end, "score": h.score}
    for h in hits
]
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `pyproject.toml` | config | batch | No packaging/build metadata file exists in the repo. Use `01-RESEARCH.md` PyPA/setuptools pattern. |

## Metadata

**Analog search scope:** root Python scripts, `hooks/`, `.claude/settings.json`, excluding `.env` and `data_sensivel/`.
**Files scanned:** 8 safe local files plus planning context.
**Pattern extraction date:** 2026-05-01
