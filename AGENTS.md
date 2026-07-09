<!-- GSD:project-start source:PROJECT.md -->
## Project

**Privacy Guard for LLM Code Agents**

This project is becoming a privacy package for LLM and code-agent workflows in terminal/IDE environments. It started as Microsoft Presidio experiments, but the product direction is now to automatically mask sensitive data before prompts, tool calls, or local context can be sent to external providers such as Anthropic or OpenAI.

The initial focus is Brazilian sensitive data: CPF, CNPJ, names, bank/account data, API keys, environment variables, credentials, dumps, and local sensitive files. The package should act locally at the agent boundary and prevent sensitive company data from leaving the machine or corporate environment.

**Core Value:** No sensitive Brazilian or company data should be sent to external LLM providers in clear text.

### Constraints

- **Privacy boundary**: Raw sensitive data must stay local and must not be sent to Anthropic, OpenAI, or other external LLM providers — this is the purpose of the project.
- **Initial environment**: v1 targets terminal/IDE code-agent workflows, especially Claude Code and Codex-style usage — broader app/framework integrations are deferred.
- **Locale priority**: Brazilian sensitive data types must be first-class, not an afterthought — CPF, CNPJ, bank/account data, names, contact data, credentials, and environment variables are central.
- **Masking behavior**: v1 needs masking before submission, not deanonymization after the response — simpler privacy model and less key-management risk.
- **Safety default**: If a client surface cannot be safely rewritten, the tool should block rather than silently allow clear-text submission — avoids false confidence.
- **Data hygiene**: Real sensitive datasets and `.env` values must not be read into planning docs, tests, generated examples, or commits — synthetic fixtures only.
- **Current stack**: Python, Microsoft Presidio, spaCy Portuguese models, and lightweight hook scripts are already present — reuse them unless a phase proves a better boundary is needed.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.14.3 - All visible source files and hooks: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, `hooks/_pii_core.py`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`.
- JSON - Claude Code project configuration in `.claude/settings.json` and `.claude/settings.local.json`.
- CSV/text data - Sensitive local sample data exists under `data_sensivel/cooperados.csv` and `data_sensivel/dump_2025_05.txt`; treat these as protected data inputs.
## Runtime
- Local Python interpreter: Python 3.14.3.
- Installed package location observed from `python -m pip show`: `C:\Users\Erick\AppData\Roaming\Python\Python314\site-packages`.
- Scripts are intended to run directly with `python <script>.py`; no application server entry point is present.
- pip is implied by installed package metadata.
- Lockfile: missing.
- Dependency manifest: missing. No `requirements.txt`, `pyproject.toml`, `Pipfile`, `poetry.lock`, or `uv.lock` is present at the project root.
## Frameworks
- Microsoft Presidio Analyzer 2.2.359 - PII detection in `test_presidio.py`, `test_presidio_br.py`, and `reversible_demo.py`.
- Microsoft Presidio Anonymizer 2.2.362 - PII masking, replacement, encryption, and deanonymization in `test_presidio.py`, `test_presidio_br.py`, and `reversible_demo.py`.
- spaCy 3.8.13 - NLP engine used by Presidio in `test_presidio_br.py` and `reversible_demo.py`.
- spaCy language models:
- No test framework is configured. Files named `test_presidio.py` and `test_presidio_br.py` are executable demo scripts with `main()` functions, not pytest-style test suites.
- No build system detected.
- Claude Code hook configuration is project-local in `.claude/settings.json`.
- `hooks/_pii_core.py` is a standalone low-latency regex/validator module with no Presidio dependency.
## Key Dependencies
- `presidio-analyzer` 2.2.359 - Core PII entity detection for generic and Brazilian Portuguese demos.
- `presidio-anonymizer` 2.2.362 - Redaction, masking, encryption, and decryption operations.
- `spacy` 3.8.13 - NLP backend for Portuguese analysis through `NlpEngineProvider`.
- `pt_core_news_lg` - Required spaCy model for Portuguese Presidio flows in `test_presidio_br.py` and `reversible_demo.py`.
- Python standard library modules used across scripts: `json`, `http.client`, `os`, `pathlib`, `random`, `re`, `secrets`, `shutil`, `string`, `sys`, `dataclasses`, and `typing`.
- Presidio transitive dependencies observed from installed metadata:
- Optional local binary: `ollama` is referenced by `ollama_local_demo.py` but was not detected on PATH.
## Configuration
- `.env` exists at project root and is explicitly protected by project Claude permissions; do not read or quote its contents.
- Hook environment variables used by `hooks/pii_guard.py`:
- Claude hook commands in `.claude/settings.json` rely on `CLAUDE_PROJECT_DIR` to locate `hooks/pii_guard.py` and `hooks/pre_tool_guard.py`.
- No build config detected.
- No linting, formatting, or packaging config detected.
- `.claude/settings.json` configures deny rules and hooks.
- `.claude/settings.local.json` configures local command allowances for commands such as `python hooks\\_pii_core.py`, `python reversible_demo.py`, and Ollama/Python discovery commands.
## Platform Requirements
- Windows/PowerShell environment is implied by local paths and `.claude/settings.local.json` command allowances.
- Python 3.14.3 with user-site packages installed.
- Required Python packages must be installed manually because no manifest exists.
- Required spaCy model for Portuguese flows: `pt_core_news_lg`.
- Optional English spaCy model `en_core_web_lg` is present locally for generic Presidio NLP behavior.
- Optional Ollama setup for local LLM demo:
- No production deployment target detected.
- Current code is demo/script-oriented and local-hook-oriented.
- Sensitive data handling assumes local execution and local-only processing for PII.
## Notable Gaps
- Add a dependency manifest such as `requirements.txt` or `pyproject.toml` before expecting reproducible setup on another machine.
- Add a lockfile if exact Presidio/spaCy/cryptography versions matter for compliance demonstrations.
- Document expected `.env` variable names in a safe `.env.example`; `.env` itself must remain unread and uncommitted.
- Add automated test configuration if these demos become enforced regression checks.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Use root-level runnable demo/test scripts with descriptive snake_case names: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`.
- Use hook modules under `hooks/` for Claude hook entry points and shared low-latency PII detection: `hooks/_pii_core.py`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`.
- Prefix internal shared modules with an underscore when they are not intended as user-facing scripts: `hooks/_pii_core.py`.
- Use snake_case for Python functions: `build_analyzer()` in `test_presidio_br.py`, `build_br_recognizers()` in `test_presidio_br.py`, `has_ollama_server()` in `ollama_local_demo.py`.
- Use Portuguese domain verbs for Brazilian validator functions: `valida_cpf()`, `valida_cnpj()`, `valida_cnh()`, `valida_titulo_eleitor()`, `valida_pis()`, `valida_cartao_sus()` in `test_presidio_br.py`.
- Use `main()` as the CLI/script entry function, guarded by `if __name__ == "__main__":` in all runnable scripts: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, `hooks/_pii_core.py`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`.
- Use uppercase constants for static configuration and samples: `SAMPLES` in `test_presidio.py` and `test_presidio_br.py`, `THRESHOLD` and `MODE` in `hooks/pii_guard.py`, `SENSITIVE_GLOBS`, `READ_CMDS`, and `EXFIL_CMDS` in `hooks/pre_tool_guard.py`.
- Use short local variables in validator/math-heavy code where the algorithm is compact: `s`, `d`, `dv1`, `dv2`, `pesos1`, `pesos2` in `test_presidio_br.py` and `hooks/_pii_core.py`.
- Prefer explicit domain names for recognizer instances: `cpf`, `cnpj`, `cnh`, `telefone`, `cep`, `placa`, `titulo`, `pis`, `sus` in `test_presidio_br.py`.
- Use dataclasses for simple structured records: `Hit` in `hooks/_pii_core.py`.
- Use type hints on reusable helpers and hook functions: `detect(text: str, min_score: float = 0.6) -> List[Hit]` in `hooks/_pii_core.py`, `check_bash(tool_input: dict) -> tuple[bool, str]` in `hooks/pre_tool_guard.py`, `main() -> int` in `hooks/pii_guard.py`.
- Use Presidio classes directly for integration boundaries: `AnalyzerEngine`, `PatternRecognizer`, `RecognizerRegistry`, `RecognizerResult`, `OperatorConfig` in `test_presidio_br.py` and `reversible_demo.py`.
## Code Style
- Formatting tool: Not detected. There is no `pyproject.toml`, `setup.cfg`, `.flake8`, `ruff.toml`, `pytest.ini`, or other root quality config.
- Style follows readable PEP 8 conventions: 4-space indentation, snake_case functions, uppercase constants, blank lines between top-level definitions, and line wrapping for long dictionaries/lists.
- Keep runnable scripts readable for demos: use section banners and print separators consistently, as in `test_presidio_br.py` and `reversible_demo.py`.
- Use ASCII in new code unless the surrounding file already contains Portuguese text or domain labels with accents. Existing Portuguese files contain non-ASCII sample text and comments in `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, and hooks.
- Linting tool: Not detected.
- Existing code has one explicit lint suppression for local path import ordering: `# noqa: E402` in `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, and `reversible_demo.py`.
- New code should avoid adding broad suppressions. If local hook imports require path manipulation, keep the suppression scoped to that import line.
## Import Organization
- No package-level import aliases or configured path aliases are detected.
- For scripts importing sibling modules, the project inserts the script directory into `sys.path`: `sys.path.insert(0, str(Path(__file__).parent))` in hook scripts and `sys.path.insert(0, str(pathlib.Path(__file__).parent))` in `reversible_demo.py`.
- Prefer extracting shared code into a package before adding more `sys.path` manipulation. If keeping the current script layout, keep path insertion local and immediately followed by the local import.
## Error Handling
- Hook entry points must fail open on malformed JSON input: `hooks/pii_guard.py` and `hooks/pre_tool_guard.py` catch `json.JSONDecodeError` and `ValueError`, then return `0`.
- Blocking hook violations use exit code `2` and write the reason to `stderr`: `deny()` in `hooks/pre_tool_guard.py`, block mode in `hooks/pii_guard.py`.
- Optional/local service checks should catch expected OS/network errors and return booleans instead of raising: `has_ollama_server()` in `ollama_local_demo.py` catches `OSError`.
- Demo scripts generally rely on Presidio/Ollama dependency exceptions surfacing naturally. Do not hide integration failures in reusable code unless the script can provide actionable setup output, as `ollama_local_demo.py` does.
## Logging
- Use `print()` for user-facing demo output in runnable scripts: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, and the standalone sample block in `hooks/_pii_core.py`.
- Use `sys.stderr.write()` for blocking hook messages that Claude hook runners should treat as denials: `hooks/pii_guard.py` and `hooks/pre_tool_guard.py`.
- Use JSON output for non-blocking hook context returned to Claude: `hooks/pii_guard.py` emits `hookSpecificOutput` for `warn` and `scrub` modes.
## Comments
- Use comments to mark major demo or algorithm sections: section banners in `test_presidio_br.py` separate validators, recognizer definitions, samples, and engine setup.
- Use comments to clarify policy-sensitive behavior: `hooks/pre_tool_guard.py` documents sensitive path patterns, read commands, exfiltration commands, and inline PII checks.
- Use short comments for important security assumptions: `reversible_demo.py` states the AES key stays local and explains production key storage expectations.
- Not applicable. This is a Python codebase.
- Python module docstrings are used heavily to describe script purpose and threat model: `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, `hooks/pii_guard.py`, and `hooks/pre_tool_guard.py`.
## Function Design
## Module Design
- Put new low-latency hook detection logic in `hooks/_pii_core.py`.
- Put new hook policy checks in `hooks/pre_tool_guard.py` or `hooks/pii_guard.py` depending on event type.
- Put Presidio recognizer experiments in `test_presidio_br.py` only if they remain demo-oriented; extract to a package before relying on them as library code.
- Keep demo data fictional and clearly labeled in module docstrings, as in `test_presidio.py` and `test_presidio_br.py`.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Runtime behavior is organized around standalone Python entry-point scripts at the repository root: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, and `ollama_local_demo.py`.
- Microsoft Presidio demos and Claude hook enforcement are separate module boundaries: Presidio-based detection/anonymization lives in root demo scripts, while low-latency hook scanning lives in `hooks/`.
- Sensitive local inputs are isolated under `data_sensivel/` and protected by `.claude/settings.json` deny rules plus `hooks/pre_tool_guard.py`.
- There is no package layout, application server, or importable `src/` package. Additions should stay script-based unless a deliberate package refactor is planned.
## Layers
- Purpose: Demonstrates default Microsoft Presidio analyzer/anonymizer behavior against fictitious English PII samples.
- Location: `test_presidio.py`
- Contains: `SAMPLES`, inline `OperatorConfig` mapping, and `main()`.
- Depends on: `presidio_analyzer.AnalyzerEngine`, `presidio_anonymizer.AnonymizerEngine`, `presidio_anonymizer.entities.OperatorConfig`, Python `random`.
- Used by: Direct CLI execution via `python test_presidio.py`.
- Purpose: Defines Brazilian PII recognizers and checksum validators for CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS card, RG, phone, CEP, and vehicle plates.
- Location: `test_presidio_br.py`
- Contains: Validator functions, `ChecksumPatternRecognizer`, `build_br_recognizers()`, `build_analyzer()`, `build_operators()`, `SAMPLES`, and `main()`.
- Depends on: `presidio_analyzer`, `presidio_anonymizer`, `presidio_analyzer.nlp_engine.NlpEngineProvider`, `re`, and `typing`.
- Used by: Direct CLI execution via `python test_presidio_br.py`; imported by `reversible_demo.py` for `build_br_recognizers()`.
- Purpose: Demonstrates local reversible anonymization using Presidio `encrypt` and `decrypt` operators so clear-text PII stays local.
- Location: `reversible_demo.py`
- Contains: Local AES key generation, local Portuguese analyzer construction, anonymization, simulated LLM response, deanonymization, and `main()`.
- Depends on: `test_presidio_br.build_br_recognizers`, `presidio_analyzer`, `presidio_anonymizer.AnonymizerEngine`, `presidio_anonymizer.DeanonymizeEngine`, `OperatorConfig`, `secrets`, `string`, `sys`, and `pathlib`.
- Used by: Direct CLI execution via `python reversible_demo.py`.
- Purpose: Demonstrates routing PII-containing prompts to a local Ollama server instead of a remote model provider.
- Location: `ollama_local_demo.py`
- Contains: Ollama binary/server detection, setup instructions, localhost HTTP generation call, and `main()`.
- Depends on: Python standard library only: `http.client`, `json`, `shutil`, and `sys`.
- Used by: Direct CLI execution via `python ollama_local_demo.py`.
- Purpose: Blocks or warns on sensitive prompts, sensitive path access, sensitive file reads, obvious exfiltration commands, and inline PII in tool commands.
- Location: `hooks/`
- Contains: Shared scanner/redactor in `hooks/_pii_core.py`, prompt hook in `hooks/pii_guard.py`, and tool hook in `hooks/pre_tool_guard.py`.
- Depends on: Python standard library only: `re`, `json`, `os`, `sys`, `pathlib`, `dataclasses`, and `typing`.
- Used by: `.claude/settings.json` hook configuration for `UserPromptSubmit` and `PreToolUse`.
- Purpose: Stores local sensitive sample/source data that must not be read by agents or sent to remote services.
- Location: `data_sensivel/`
- Contains: Sensitive CSV/text files such as `data_sensivel/cooperados.csv` and `data_sensivel/dump_2025_05.txt`.
- Depends on: Not applicable.
- Used by: Guard policy references in `.claude/settings.json` and path detection rules in `hooks/pre_tool_guard.py`.
## Data Flow
- The demo scripts are stateless across runs. Presidio analyzers, anonymizers, and encryption keys are constructed inside each process.
- `reversible_demo.py` keeps the encryption key in process memory only.
- Hook behavior is controlled through environment variables `PII_GUARD_THRESHOLD` and `PII_GUARD_MODE`.
- No database, cache, or persistent application state is detected.
## Key Abstractions
- Purpose: Reduce false positives for structured Brazilian identifiers.
- Examples: `test_presidio_br.py`
- Pattern: Pure validation functions normalize with `_digits()` and return `bool`; examples include `valida_cpf()`, `valida_cnpj()`, `valida_cnh()`, `valida_titulo_eleitor()`, `valida_pis()`, and `valida_cartao_sus()`.
- Purpose: Extend Presidio `PatternRecognizer` with post-match checksum validation.
- Examples: `test_presidio_br.py`
- Pattern: Override `analyze()`, inspect matched text spans, raise score to `valid_score` for valid identifiers, and downgrade invalid identifiers to `invalid_score`.
- Purpose: Centralize the list of custom Brazilian recognizers.
- Examples: `test_presidio_br.py`, imported by `reversible_demo.py`
- Pattern: `build_br_recognizers()` returns a list of configured Presidio recognizer instances. Reuse this factory rather than duplicating BR recognizer definitions.
- Purpose: Build a Portuguese Presidio analyzer with spaCy and custom BR recognizers.
- Examples: `test_presidio_br.py`, `reversible_demo.py`
- Pattern: `build_analyzer()` constructs `NlpEngineProvider`, `RecognizerRegistry`, loads predefined recognizers, registers custom recognizers, and returns `AnalyzerEngine`.
- Purpose: Define anonymization behavior by entity type.
- Examples: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`
- Pattern: Use `OperatorConfig` dictionaries keyed by Presidio entity name, with `"DEFAULT"` as fallback.
- Purpose: Represent lightweight regex detections without depending on Presidio at hook runtime.
- Examples: `hooks/_pii_core.py`
- Pattern: `@dataclass Hit` with `kind`, `start`, `end`, `value`, and `score`.
- Purpose: Provide fast PII and secret detection for prompt/tool guard hooks.
- Examples: `hooks/_pii_core.py`
- Pattern: `PATTERNS` stores `(kind, compiled_regex, score, optional_validator)` tuples; `detect()` filters by threshold and removes overlaps; `redact()` replaces spans with `<KIND>` markers.
## Entry Points
- Location: `test_presidio.py`
- Triggers: `python test_presidio.py`
- Responsibilities: Run default Presidio analysis/anonymization over fictitious English sample strings.
- Location: `test_presidio_br.py`
- Triggers: `python test_presidio_br.py`
- Responsibilities: Build Portuguese Presidio analyzer with custom Brazilian recognizers, display detections, and anonymize fictitious Portuguese samples.
- Location: `reversible_demo.py`
- Triggers: `python reversible_demo.py`
- Responsibilities: Encrypt detected PII locally, simulate LLM handling of encrypted tokens, and restore original text locally.
- Location: `ollama_local_demo.py`
- Triggers: `python ollama_local_demo.py`
- Responsibilities: Detect local Ollama availability, print setup guidance, or call localhost model generation.
- Location: `hooks/pii_guard.py`
- Triggers: `.claude/settings.json` `UserPromptSubmit` command `python "$CLAUDE_PROJECT_DIR/hooks/pii_guard.py"`
- Responsibilities: Inspect submitted prompts for PII and block/warn/scrub based on environment configuration.
- Location: `hooks/pre_tool_guard.py`
- Triggers: `.claude/settings.json` `PreToolUse` matcher `Read|Bash|Grep|Glob|Edit|Write`
- Responsibilities: Prevent agent reads/writes/searches against sensitive paths and block risky shell commands.
- Location: `hooks/_pii_core.py`
- Triggers: `python hooks/_pii_core.py`
- Responsibilities: Run a built-in scanner/redactor smoke demo for the lightweight hook detection core.
## Error Handling
- `hooks/pii_guard.py` and `hooks/pre_tool_guard.py` tolerate invalid JSON stdin by returning `0`, avoiding hook crashes on malformed payloads.
- `hooks/pre_tool_guard.py` centralizes blocked policy outcomes through `deny(reason)`.
- `ollama_local_demo.py` catches `OSError` when probing localhost and returns setup guidance with process status `1` if Ollama is unavailable.
- Presidio demo scripts do not wrap analyzer/model initialization failures; missing dependencies or missing `pt_core_news_lg` fail at process startup.
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
