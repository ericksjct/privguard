# External Integrations

**Analysis Date:** 2026-05-01

## APIs & External Services

**Local LLM:**
- Ollama - Optional local-only LLM endpoint for prompts containing PII in `ollama_local_demo.py`.
  - SDK/Client: Python standard library `http.client`; no external Ollama SDK.
  - Endpoint: `http://127.0.0.1:11434`.
  - API paths used:
    - `GET /api/tags` for health/model availability detection.
    - `POST /api/generate` for prompt generation.
  - Auth: none detected.
  - Default model in code: `llama3.1:8b`.
  - Current availability: Ollama binary was not detected on PATH during mapping.

**Microsoft Presidio:**
- Presidio Analyzer - Local Python library integration for PII detection in `test_presidio.py`, `test_presidio_br.py`, and `reversible_demo.py`.
  - SDK/Client: `presidio_analyzer`.
  - Auth: none.
- Presidio Anonymizer - Local Python library integration for redaction, masking, encryption, and deanonymization in `test_presidio.py`, `test_presidio_br.py`, and `reversible_demo.py`.
  - SDK/Client: `presidio_anonymizer`.
  - Auth: none.

**spaCy NLP:**
- spaCy - Local NLP engine used by Presidio via `NlpEngineProvider` in `test_presidio_br.py` and `reversible_demo.py`.
  - SDK/Client: `spacy` through Presidio NLP engine provider.
  - Models: `pt_core_news_lg` required by Portuguese flows; installed locally.
  - Auth: none.

## Data Storage

**Databases:**
- Not detected.
  - Connection: not applicable.
  - Client: not applicable.

**File Storage:**
- Local filesystem only.
- Sensitive sample data folder exists at `data_sensivel/`.
- Sensitive data files detected by name only:
  - `data_sensivel/cooperados.csv`.
  - `data_sensivel/dump_2025_05.txt`.
- Project policies in `.claude/settings.json` and hook logic in `hooks/pre_tool_guard.py` treat `data_sensivel/`, `cooperados/`, `dump_*`, `.env`, and credential/secret-like paths as sensitive.

**Caching:**
- None detected.
- Python bytecode cache directories exist: `__pycache__/` and `hooks/__pycache__/`.

## Authentication & Identity

**Auth Provider:**
- Not detected.
  - Implementation: no app authentication flow exists.

**Local Secret Handling:**
- `.env` exists and is protected by `.claude/settings.json`; contents were not read.
- `reversible_demo.py` generates an in-memory 32-character AES key for Presidio `encrypt`/`decrypt` demonstration.
- `reversible_demo.py` notes that production key material should come from a local keyring or HSM; no keyring/HSM integration is implemented in visible code.

## Monitoring & Observability

**Error Tracking:**
- None detected.

**Logs:**
- Console/stdout printing is used by demo scripts: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, and `ollama_local_demo.py`.
- Hook blocks are reported through stderr in `hooks/pii_guard.py` and `hooks/pre_tool_guard.py`.
- Claude hook context is emitted as JSON to stdout for warn/scrub modes in `hooks/pii_guard.py`.

## CI/CD & Deployment

**Hosting:**
- None detected.

**CI Pipeline:**
- None detected.

## Environment Configuration

**Required env vars:**
- `CLAUDE_PROJECT_DIR` - Used by `.claude/settings.json` hook commands to locate project hook scripts.

**Optional env vars:**
- `PII_GUARD_THRESHOLD` - Controls minimum detection score for `hooks/pii_guard.py`; default is `0.7`.
- `PII_GUARD_MODE` - Controls `hooks/pii_guard.py` action; default is `block`, with `warn` and `scrub` supported.

**Secrets location:**
- `.env` is present at project root and must remain protected.
- No `.env.example` or documented safe environment template detected.
- No cloud credential files detected in the visible root listing.

## Hooks & Local Tooling

**Claude Code Hooks:**
- `.claude/settings.json` configures `UserPromptSubmit` to run `python "$CLAUDE_PROJECT_DIR/hooks/pii_guard.py"`.
- `.claude/settings.json` configures `PreToolUse` for `Read|Bash|Grep|Glob|Edit|Write` to run `python "$CLAUDE_PROJECT_DIR/hooks/pre_tool_guard.py"`.
- `hooks/pii_guard.py` scans submitted prompts for PII and can block, warn, or emit scrubbed context.
- `hooks/pre_tool_guard.py` blocks sensitive path access, sensitive reads through shell commands, network exfiltration references to sensitive paths, and inline PII in tool commands.
- `hooks/_pii_core.py` provides shared regex detection, CPF/CNPJ/Luhn validation, overlap filtering, and redaction.

**Local Data Protection Rules:**
- `.claude/settings.json` denies direct reads of `data_sensivel/**`, `cooperados/**`, `dump_*`, `.env`, `.env.*`, credential-like files, and secret-like files.
- `hooks/pre_tool_guard.py` reinforces the deny list for path tools and shell commands.

## Webhooks & Callbacks

**Incoming:**
- None detected.

**Outgoing:**
- Localhost-only HTTP calls to Ollama from `ollama_local_demo.py`.
- No external network API calls detected in visible source.

## Notable Gaps

- Ollama is optional and not installed/detected on PATH; `ollama_local_demo.py` falls back to setup instructions when unavailable.
- No dependency manifest captures Presidio, spaCy, spaCy model, or Ollama assumptions.
- No safe `.env.example` documents required/optional environment variable names.
- No production secret manager, keyring, or HSM integration is implemented for reversible anonymization keys.
- No CI job validates that hooks, Presidio demos, and required NLP models remain runnable.

---

*Integration audit: 2026-05-01*
