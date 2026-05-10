# Coding Conventions

**Analysis Date:** 2026-05-01

## Naming Patterns

**Files:**
- Use root-level runnable demo/test scripts with descriptive snake_case names: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`.
- Use hook modules under `hooks/` for Claude hook entry points and shared low-latency PII detection: `hooks/_pii_core.py`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`.
- Prefix internal shared modules with an underscore when they are not intended as user-facing scripts: `hooks/_pii_core.py`.

**Functions:**
- Use snake_case for Python functions: `build_analyzer()` in `test_presidio_br.py`, `build_br_recognizers()` in `test_presidio_br.py`, `has_ollama_server()` in `ollama_local_demo.py`.
- Use Portuguese domain verbs for Brazilian validator functions: `valida_cpf()`, `valida_cnpj()`, `valida_cnh()`, `valida_titulo_eleitor()`, `valida_pis()`, `valida_cartao_sus()` in `test_presidio_br.py`.
- Use `main()` as the CLI/script entry function, guarded by `if __name__ == "__main__":` in all runnable scripts: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, `hooks/_pii_core.py`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`.

**Variables:**
- Use uppercase constants for static configuration and samples: `SAMPLES` in `test_presidio.py` and `test_presidio_br.py`, `THRESHOLD` and `MODE` in `hooks/pii_guard.py`, `SENSITIVE_GLOBS`, `READ_CMDS`, and `EXFIL_CMDS` in `hooks/pre_tool_guard.py`.
- Use short local variables in validator/math-heavy code where the algorithm is compact: `s`, `d`, `dv1`, `dv2`, `pesos1`, `pesos2` in `test_presidio_br.py` and `hooks/_pii_core.py`.
- Prefer explicit domain names for recognizer instances: `cpf`, `cnpj`, `cnh`, `telefone`, `cep`, `placa`, `titulo`, `pis`, `sus` in `test_presidio_br.py`.

**Types:**
- Use dataclasses for simple structured records: `Hit` in `hooks/_pii_core.py`.
- Use type hints on reusable helpers and hook functions: `detect(text: str, min_score: float = 0.6) -> List[Hit]` in `hooks/_pii_core.py`, `check_bash(tool_input: dict) -> tuple[bool, str]` in `hooks/pre_tool_guard.py`, `main() -> int` in `hooks/pii_guard.py`.
- Use Presidio classes directly for integration boundaries: `AnalyzerEngine`, `PatternRecognizer`, `RecognizerRegistry`, `RecognizerResult`, `OperatorConfig` in `test_presidio_br.py` and `reversible_demo.py`.

## Code Style

**Formatting:**
- Formatting tool: Not detected. There is no `pyproject.toml`, `setup.cfg`, `.flake8`, `ruff.toml`, `pytest.ini`, or other root quality config.
- Style follows readable PEP 8 conventions: 4-space indentation, snake_case functions, uppercase constants, blank lines between top-level definitions, and line wrapping for long dictionaries/lists.
- Keep runnable scripts readable for demos: use section banners and print separators consistently, as in `test_presidio_br.py` and `reversible_demo.py`.
- Use ASCII in new code unless the surrounding file already contains Portuguese text or domain labels with accents. Existing Portuguese files contain non-ASCII sample text and comments in `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, and hooks.

**Linting:**
- Linting tool: Not detected.
- Existing code has one explicit lint suppression for local path import ordering: `# noqa: E402` in `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, and `reversible_demo.py`.
- New code should avoid adding broad suppressions. If local hook imports require path manipulation, keep the suppression scoped to that import line.

## Import Organization

**Order:**
1. Standard library imports first: `json`, `os`, `re`, `sys`, `pathlib`, `http.client`, `shutil`, `secrets`, `string`.
2. Third-party Presidio imports next: `presidio_analyzer`, `presidio_anonymizer`, and `presidio_analyzer.nlp_engine`.
3. Local imports last, after path setup when needed: `from _pii_core import detect, redact` in `hooks/pii_guard.py`, `from test_presidio_br import build_br_recognizers` in `reversible_demo.py`.

**Path Aliases:**
- No package-level import aliases or configured path aliases are detected.
- For scripts importing sibling modules, the project inserts the script directory into `sys.path`: `sys.path.insert(0, str(Path(__file__).parent))` in hook scripts and `sys.path.insert(0, str(pathlib.Path(__file__).parent))` in `reversible_demo.py`.
- Prefer extracting shared code into a package before adding more `sys.path` manipulation. If keeping the current script layout, keep path insertion local and immediately followed by the local import.

## Error Handling

**Patterns:**
- Hook entry points must fail open on malformed JSON input: `hooks/pii_guard.py` and `hooks/pre_tool_guard.py` catch `json.JSONDecodeError` and `ValueError`, then return `0`.
- Blocking hook violations use exit code `2` and write the reason to `stderr`: `deny()` in `hooks/pre_tool_guard.py`, block mode in `hooks/pii_guard.py`.
- Optional/local service checks should catch expected OS/network errors and return booleans instead of raising: `has_ollama_server()` in `ollama_local_demo.py` catches `OSError`.
- Demo scripts generally rely on Presidio/Ollama dependency exceptions surfacing naturally. Do not hide integration failures in reusable code unless the script can provide actionable setup output, as `ollama_local_demo.py` does.

## Logging

**Framework:** `print` and `sys.stderr`

**Patterns:**
- Use `print()` for user-facing demo output in runnable scripts: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, and the standalone sample block in `hooks/_pii_core.py`.
- Use `sys.stderr.write()` for blocking hook messages that Claude hook runners should treat as denials: `hooks/pii_guard.py` and `hooks/pre_tool_guard.py`.
- Use JSON output for non-blocking hook context returned to Claude: `hooks/pii_guard.py` emits `hookSpecificOutput` for `warn` and `scrub` modes.

## Comments

**When to Comment:**
- Use comments to mark major demo or algorithm sections: section banners in `test_presidio_br.py` separate validators, recognizer definitions, samples, and engine setup.
- Use comments to clarify policy-sensitive behavior: `hooks/pre_tool_guard.py` documents sensitive path patterns, read commands, exfiltration commands, and inline PII checks.
- Use short comments for important security assumptions: `reversible_demo.py` states the AES key stays local and explains production key storage expectations.

**JSDoc/TSDoc:**
- Not applicable. This is a Python codebase.
- Python module docstrings are used heavily to describe script purpose and threat model: `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, `hooks/pii_guard.py`, and `hooks/pre_tool_guard.py`.

## Function Design

**Size:** Keep pure validators and detection helpers small and directly testable. `valida_cpf()`, `valida_cnpj()`, and `valida_luhn()` are compact deterministic functions in `test_presidio_br.py` and `hooks/_pii_core.py`. Larger demo orchestration should stay inside `main()` in runnable scripts.

**Parameters:** Prefer simple typed parameters for reusable functions: `is_sensitive_path(path: str)`, `detect(text: str, min_score: float = 0.6)`, and `redact(text: str, hits: List[Hit])`.

**Return Values:** Return booleans for validation/check helpers, typed tuples for hook checks, structured `Hit` records for detection, and integer process codes from hook/demo entry points where the caller needs exit semantics.

## Module Design

**Exports:** There are no explicit `__all__` exports. Reusable functions are imported by name from script modules: `build_br_recognizers()` from `test_presidio_br.py`, `detect()` and `redact()` from `hooks/_pii_core.py`.

**Barrel Files:** Not used. There is no package `__init__.py` or barrel module.

**Prescriptive Guidance:**
- Put new low-latency hook detection logic in `hooks/_pii_core.py`.
- Put new hook policy checks in `hooks/pre_tool_guard.py` or `hooks/pii_guard.py` depending on event type.
- Put Presidio recognizer experiments in `test_presidio_br.py` only if they remain demo-oriented; extract to a package before relying on them as library code.
- Keep demo data fictional and clearly labeled in module docstrings, as in `test_presidio.py` and `test_presidio_br.py`.

---

*Convention analysis: 2026-05-01*
