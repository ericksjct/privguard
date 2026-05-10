# Technology Stack

**Analysis Date:** 2026-05-01

## Languages

**Primary:**
- Python 3.14.3 - All visible source files and hooks: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`, `hooks/_pii_core.py`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`.

**Secondary:**
- JSON - Claude Code project configuration in `.claude/settings.json` and `.claude/settings.local.json`.
- CSV/text data - Sensitive local sample data exists under `data_sensivel/cooperados.csv` and `data_sensivel/dump_2025_05.txt`; treat these as protected data inputs.

## Runtime

**Environment:**
- Local Python interpreter: Python 3.14.3.
- Installed package location observed from `python -m pip show`: `C:\Users\Erick\AppData\Roaming\Python\Python314\site-packages`.
- Scripts are intended to run directly with `python <script>.py`; no application server entry point is present.

**Package Manager:**
- pip is implied by installed package metadata.
- Lockfile: missing.
- Dependency manifest: missing. No `requirements.txt`, `pyproject.toml`, `Pipfile`, `poetry.lock`, or `uv.lock` is present at the project root.

## Frameworks

**Core:**
- Microsoft Presidio Analyzer 2.2.359 - PII detection in `test_presidio.py`, `test_presidio_br.py`, and `reversible_demo.py`.
- Microsoft Presidio Anonymizer 2.2.362 - PII masking, replacement, encryption, and deanonymization in `test_presidio.py`, `test_presidio_br.py`, and `reversible_demo.py`.
- spaCy 3.8.13 - NLP engine used by Presidio in `test_presidio_br.py` and `reversible_demo.py`.
- spaCy language models:
  - `pt_core_news_lg` is installed and required by `test_presidio_br.py` and `reversible_demo.py`.
  - `en_core_web_lg` is installed but not directly referenced by visible source.
  - `en_core_web_sm` is not installed.

**Testing:**
- No test framework is configured. Files named `test_presidio.py` and `test_presidio_br.py` are executable demo scripts with `main()` functions, not pytest-style test suites.

**Build/Dev:**
- No build system detected.
- Claude Code hook configuration is project-local in `.claude/settings.json`.
- `hooks/_pii_core.py` is a standalone low-latency regex/validator module with no Presidio dependency.

## Key Dependencies

**Critical:**
- `presidio-analyzer` 2.2.359 - Core PII entity detection for generic and Brazilian Portuguese demos.
- `presidio-anonymizer` 2.2.362 - Redaction, masking, encryption, and decryption operations.
- `spacy` 3.8.13 - NLP backend for Portuguese analysis through `NlpEngineProvider`.
- `pt_core_news_lg` - Required spaCy model for Portuguese Presidio flows in `test_presidio_br.py` and `reversible_demo.py`.

**Infrastructure:**
- Python standard library modules used across scripts: `json`, `http.client`, `os`, `pathlib`, `random`, `re`, `secrets`, `shutil`, `string`, `sys`, `dataclasses`, and `typing`.
- Presidio transitive dependencies observed from installed metadata:
  - `phonenumbers`, `pyyaml`, `regex`, `tldextract` for `presidio-analyzer`.
  - `cryptography` for `presidio-anonymizer` encryption/decryption operators.
- Optional local binary: `ollama` is referenced by `ollama_local_demo.py` but was not detected on PATH.

## Configuration

**Environment:**
- `.env` exists at project root and is explicitly protected by project Claude permissions; do not read or quote its contents.
- Hook environment variables used by `hooks/pii_guard.py`:
  - `PII_GUARD_THRESHOLD` - Detection threshold, default `0.7`.
  - `PII_GUARD_MODE` - Hook behavior, default `block`; supported values are `block`, `warn`, and `scrub`.
- Claude hook commands in `.claude/settings.json` rely on `CLAUDE_PROJECT_DIR` to locate `hooks/pii_guard.py` and `hooks/pre_tool_guard.py`.

**Build:**
- No build config detected.
- No linting, formatting, or packaging config detected.
- `.claude/settings.json` configures deny rules and hooks.
- `.claude/settings.local.json` configures local command allowances for commands such as `python hooks\\_pii_core.py`, `python reversible_demo.py`, and Ollama/Python discovery commands.

## Platform Requirements

**Development:**
- Windows/PowerShell environment is implied by local paths and `.claude/settings.local.json` command allowances.
- Python 3.14.3 with user-site packages installed.
- Required Python packages must be installed manually because no manifest exists.
- Required spaCy model for Portuguese flows: `pt_core_news_lg`.
- Optional English spaCy model `en_core_web_lg` is present locally for generic Presidio NLP behavior.
- Optional Ollama setup for local LLM demo:
  - Ollama binary/service.
  - Local server at `127.0.0.1:11434`.
  - A pulled model such as `llama3.1:8b`, `qwen2.5:7b`, or `phi4:14b`.

**Production:**
- No production deployment target detected.
- Current code is demo/script-oriented and local-hook-oriented.
- Sensitive data handling assumes local execution and local-only processing for PII.

## Notable Gaps

- Add a dependency manifest such as `requirements.txt` or `pyproject.toml` before expecting reproducible setup on another machine.
- Add a lockfile if exact Presidio/spaCy/cryptography versions matter for compliance demonstrations.
- Document expected `.env` variable names in a safe `.env.example`; `.env` itself must remain unread and uncommitted.
- Add automated test configuration if these demos become enforced regression checks.

---

*Stack analysis: 2026-05-01*
