# Testing Patterns

**Analysis Date:** 2026-05-01

## Test Framework

**Runner:**
- Formal test runner: Not detected.
- There is no `pytest.ini`, `pyproject.toml`, `setup.cfg`, `tox.ini`, `requirements.txt`, or package manifest at the project root.
- Current verification is script-based through executable Python files: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, `hooks/_pii_core.py`, `hooks/pii_guard.py`, and `hooks/pre_tool_guard.py`.

**Assertion Library:**
- Not detected.
- Current scripts verify behavior by printing detected entities, anonymized output, hook JSON, or exit codes.

**Run Commands:**
```bash
python test_presidio.py              # Run English Presidio anonymization demo
python test_presidio_br.py           # Run Portuguese/Brazilian recognizer demo
python reversible_demo.py            # Run reversible encrypt/decrypt anonymization demo
python ollama_local_demo.py          # Check Ollama availability and run local LLM demo when available
python hooks/_pii_core.py            # Run standalone regex/validator smoke demo
```

## Test File Organization

**Location:**
- Test/demo scripts are root-level and named like tests: `test_presidio.py` and `test_presidio_br.py`.
- Hook smoke logic is embedded in hook modules under `hooks/`: `hooks/_pii_core.py`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`.
- Demo input files exist under `data_sensivel/`; treat this directory as sensitive test data and do not read or print its contents in planning docs or casual verification.

**Naming:**
- `test_*.py` currently means "runnable demo script", not pytest-style test module.
- `*_demo.py` scripts demonstrate integration scenarios: `reversible_demo.py` and `ollama_local_demo.py`.
- Hook modules use event/policy names: `pii_guard.py` for prompt scanning and `pre_tool_guard.py` for tool-use blocking.

**Structure:**
```text
project-root/
├── test_presidio.py          # English Presidio demo with fictional PII samples
├── test_presidio_br.py       # Brazilian recognizers, validators, samples, and demo runner
├── reversible_demo.py        # Presidio encrypt/decrypt round-trip demo
├── ollama_local_demo.py      # Local Ollama availability/integration demo
└── hooks/
    ├── _pii_core.py          # Shared regex validators with standalone smoke block
    ├── pii_guard.py          # UserPromptSubmit hook entry point
    └── pre_tool_guard.py     # PreToolUse hook entry point
```

## Test Structure

**Suite Organization:**
```python
SAMPLES = [
    "O cliente Carlos Alberto de Souza, portador do CPF 529.982.247-25, ...",
]

def build_analyzer() -> AnalyzerEngine:
    ...

def build_operators() -> dict:
    ...

def main() -> None:
    analyzer = build_analyzer()
    anonymizer = AnonymizerEngine()
    operators = build_operators()
    for n, text in enumerate(SAMPLES, 1):
        results = analyzer.analyze(text=text, language="pt", score_threshold=0.3)
        anon = anonymizer.anonymize(text=text, analyzer_results=kept, operators=operators)
        print(f"Anonim.  : {anon.text}")

if __name__ == "__main__":
    main()
```

**Patterns:**
- Setup pattern: construct dependencies inside `main()` or small builders, e.g. `build_analyzer()` and `build_operators()` in `test_presidio_br.py`.
- Teardown pattern: Not detected; scripts do not create persistent external resources.
- Assertion pattern: Not detected; behavior is checked by manual inspection of stdout/stderr and exit codes.
- Determinism pattern: `test_presidio.py` seeds randomness with `random.seed(42)` before sampling demo cases.
- Overlap handling pattern: `test_presidio_br.py` and `hooks/_pii_core.py` sort detections by score and start offset, then keep non-overlapping highest-score results.

## Mocking

**Framework:** Not detected.

**Patterns:**
```python
def has_ollama_server() -> bool:
    try:
        conn = http.client.HTTPConnection(OLLAMA_HOST, OLLAMA_PORT, timeout=2)
        conn.request("GET", "/api/tags")
        return conn.getresponse().status == 200
    except OSError:
        return False
```

**What to Mock:**
- Mock HTTP calls to `127.0.0.1:11434` when adding automated tests for `ollama_local_demo.py`.
- Mock `sys.stdin`, `sys.stderr`, and environment variables for `hooks/pii_guard.py` and `hooks/pre_tool_guard.py`.
- Mock or isolate Presidio engine construction for fast unit tests around validator and recognizer construction in `test_presidio_br.py`.

**What NOT to Mock:**
- Do not mock checksum validators such as `valida_cpf()`, `valida_cnpj()`, `valida_cnh()`, `valida_pis()`, and `valida_luhn()`; test them directly with valid/invalid examples.
- Do not mock `_pii_core.detect()` in hook integration tests unless the test targets hook routing only. The security value is in end-to-end detection and blocking behavior.

## Fixtures and Factories

**Test Data:**
```python
SAMPLES = [
    "Patient John Doe, SSN 123-45-6789, born on 03/14/1985, ...",
    "O cliente Carlos Alberto de Souza, portador do CPF 529.982.247-25, ...",
]
```

**Location:**
- Fictional inline samples live in `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, and the smoke block in `hooks/_pii_core.py`.
- Sensitive demo files live under `data_sensivel/`; use path-based policy tests without reading contents.
- Environment-controlled hook behavior is configured through `PII_GUARD_THRESHOLD` and `PII_GUARD_MODE` in `hooks/pii_guard.py`.

## Coverage

**Requirements:** None enforced.

**View Coverage:**
```bash
# Not available: no coverage tool or config detected.
```

## Test Types

**Unit Tests:**
- Not formalized. Natural unit-test candidates are pure validators and helpers in `test_presidio_br.py` and `hooks/_pii_core.py`: `_digits()`, `valida_cpf()`, `valida_cnpj()`, `valida_cnh()`, `valida_titulo_eleitor()`, `valida_pis()`, `valida_cartao_sus()`, `valida_luhn()`, `is_sensitive_path()`, `detect()`, and `redact()`.

**Integration Tests:**
- Script-based integration checks exist through Presidio analyzer/anonymizer flows in `test_presidio.py`, `test_presidio_br.py`, and `reversible_demo.py`.
- Hook behavior can be tested by piping JSON into `hooks/pii_guard.py` and `hooks/pre_tool_guard.py` and checking exit codes and stderr/stdout.
- Ollama integration in `ollama_local_demo.py` is environment-dependent and exits `1` with setup instructions when the local server is unavailable.

**E2E Tests:**
- Not used.
- Closest current E2E flow is `reversible_demo.py`, which detects PII, encrypts it, simulates an LLM response, decrypts locally, and prints whether the round trip matched the original text.

## Common Patterns

**Async Testing:**
```python
# Not applicable. The codebase uses synchronous scripts and standard-library HTTP calls.
```

**Error Testing:**
```python
try:
    payload = json.loads(sys.stdin.read())
except (json.JSONDecodeError, ValueError):
    return 0
```

**Hook Verification Commands:**
```bash
printf '{"prompt":"CPF 529.982.247-25"}' | python hooks/pii_guard.py
printf '{"tool_name":"Read","tool_input":{"file_path":"data_sensivel/cooperados.csv"}}' | python hooks/pre_tool_guard.py
printf '{"tool_name":"Bash","tool_input":{"command":"cat data_sensivel/cooperados.csv"}}' | python hooks/pre_tool_guard.py
```

**Manual Quality Checks:**
```bash
python -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('.').glob('*.py')]; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('hooks').glob('*.py')]"
python test_presidio.py
python test_presidio_br.py
python reversible_demo.py
python hooks/_pii_core.py
```

**Observed Verification Result:**
- Syntax verification with `python -m py_compile` completed successfully for `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, `hooks/_pii_core.py`, `hooks/pii_guard.py`, and `hooks/pre_tool_guard.py`.
- Generated `.pyc` files from that syntax check were removed so mapped documentation remains the only intended workspace change.

---

*Testing analysis: 2026-05-01*
