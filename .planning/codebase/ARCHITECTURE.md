# Architecture

**Analysis Date:** 2026-05-01

## Pattern Overview

**Overall:** Script-oriented privacy/PII demo workspace with a separate Claude Code guard hook layer.

**Key Characteristics:**
- Runtime behavior is organized around standalone Python entry-point scripts at the repository root: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, and `ollama_local_demo.py`.
- Microsoft Presidio demos and Claude hook enforcement are separate module boundaries: Presidio-based detection/anonymization lives in root demo scripts, while low-latency hook scanning lives in `hooks/`.
- Sensitive local inputs are isolated under `data_sensivel/` and protected by `.claude/settings.json` deny rules plus `hooks/pre_tool_guard.py`.
- There is no package layout, application server, or importable `src/` package. Additions should stay script-based unless a deliberate package refactor is planned.

## Layers

**Presidio English Demo Layer:**
- Purpose: Demonstrates default Microsoft Presidio analyzer/anonymizer behavior against fictitious English PII samples.
- Location: `test_presidio.py`
- Contains: `SAMPLES`, inline `OperatorConfig` mapping, and `main()`.
- Depends on: `presidio_analyzer.AnalyzerEngine`, `presidio_anonymizer.AnonymizerEngine`, `presidio_anonymizer.entities.OperatorConfig`, Python `random`.
- Used by: Direct CLI execution via `python test_presidio.py`.

**Presidio Brazilian Recognizer Layer:**
- Purpose: Defines Brazilian PII recognizers and checksum validators for CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS card, RG, phone, CEP, and vehicle plates.
- Location: `test_presidio_br.py`
- Contains: Validator functions, `ChecksumPatternRecognizer`, `build_br_recognizers()`, `build_analyzer()`, `build_operators()`, `SAMPLES`, and `main()`.
- Depends on: `presidio_analyzer`, `presidio_anonymizer`, `presidio_analyzer.nlp_engine.NlpEngineProvider`, `re`, and `typing`.
- Used by: Direct CLI execution via `python test_presidio_br.py`; imported by `reversible_demo.py` for `build_br_recognizers()`.

**Reversible Anonymization Demo Layer:**
- Purpose: Demonstrates local reversible anonymization using Presidio `encrypt` and `decrypt` operators so clear-text PII stays local.
- Location: `reversible_demo.py`
- Contains: Local AES key generation, local Portuguese analyzer construction, anonymization, simulated LLM response, deanonymization, and `main()`.
- Depends on: `test_presidio_br.build_br_recognizers`, `presidio_analyzer`, `presidio_anonymizer.AnonymizerEngine`, `presidio_anonymizer.DeanonymizeEngine`, `OperatorConfig`, `secrets`, `string`, `sys`, and `pathlib`.
- Used by: Direct CLI execution via `python reversible_demo.py`.

**Local LLM Demo Layer:**
- Purpose: Demonstrates routing PII-containing prompts to a local Ollama server instead of a remote model provider.
- Location: `ollama_local_demo.py`
- Contains: Ollama binary/server detection, setup instructions, localhost HTTP generation call, and `main()`.
- Depends on: Python standard library only: `http.client`, `json`, `shutil`, and `sys`.
- Used by: Direct CLI execution via `python ollama_local_demo.py`.

**Claude Hook Guard Layer:**
- Purpose: Blocks or warns on sensitive prompts, sensitive path access, sensitive file reads, obvious exfiltration commands, and inline PII in tool commands.
- Location: `hooks/`
- Contains: Shared scanner/redactor in `hooks/_pii_core.py`, prompt hook in `hooks/pii_guard.py`, and tool hook in `hooks/pre_tool_guard.py`.
- Depends on: Python standard library only: `re`, `json`, `os`, `sys`, `pathlib`, `dataclasses`, and `typing`.
- Used by: `.claude/settings.json` hook configuration for `UserPromptSubmit` and `PreToolUse`.

**Sensitive Data Boundary:**
- Purpose: Stores local sensitive sample/source data that must not be read by agents or sent to remote services.
- Location: `data_sensivel/`
- Contains: Sensitive CSV/text files such as `data_sensivel/cooperados.csv` and `data_sensivel/dump_2025_05.txt`.
- Depends on: Not applicable.
- Used by: Guard policy references in `.claude/settings.json` and path detection rules in `hooks/pre_tool_guard.py`.

## Data Flow

**Default Presidio Demo Flow (`test_presidio.py`):**

1. `main()` constructs `AnalyzerEngine()` and `AnonymizerEngine()`.
2. `random.sample()` chooses all records from `SAMPLES` in deterministic seed order.
3. `AnalyzerEngine.analyze(text=..., language="en")` returns Presidio recognizer results.
4. Results are printed with entity type, score, and snippet.
5. `AnonymizerEngine.anonymize()` applies the inline operator map and prints anonymized text.

**Brazilian Presidio Demo Flow (`test_presidio_br.py`):**

1. `build_analyzer()` creates a spaCy Portuguese NLP engine using model `pt_core_news_lg`.
2. `RecognizerRegistry(supported_languages=["pt"])` loads predefined Portuguese recognizers.
3. `build_br_recognizers()` returns custom recognizers; checksum-backed recognizers use `ChecksumPatternRecognizer.analyze()` to raise valid matches and downgrade invalid matches.
4. `main()` analyzes each `SAMPLES` entry using `score_threshold = 0.3`.
5. Overlapping results are removed by keeping the highest score.
6. `AnonymizerEngine.anonymize()` applies `build_operators()` replacements/masks and prints anonymized output.

**Reversible Local Encryption Flow (`reversible_demo.py`):**

1. `main()` generates a 32-character local AES key with `secrets`.
2. `build_analyzer()` builds the same Portuguese Presidio analyzer pattern used by `test_presidio_br.py`.
3. Presidio analyzes the local source text with `score_threshold=0.5`.
4. `AnonymizerEngine.anonymize()` uses `OperatorConfig("encrypt", {"key": key})`.
5. A simulated remote response references one encrypted token.
6. `DeanonymizeEngine.deanonymize()` decrypts the encrypted items locally using the same key.

**Local Ollama Flow (`ollama_local_demo.py`):**

1. `main()` checks for an `ollama` binary with `shutil.which()`.
2. `has_ollama_server()` probes `GET http://127.0.0.1:11434/api/tags`.
3. If unavailable, `setup_instructions()` prints setup guidance and exits with status `1`.
4. If available, `call_ollama()` posts JSON to `/api/generate` on localhost.
5. The response body is parsed and printed from the `response` field.

**Claude Prompt Guard Flow (`hooks/pii_guard.py`):**

1. Claude Code invokes the command configured in `.claude/settings.json` for `UserPromptSubmit`.
2. `main()` reads JSON from stdin and extracts `payload["prompt"]`.
3. `hooks/_pii_core.py detect()` scans the prompt using regex patterns and optional validators.
4. If no hit meets `PII_GUARD_THRESHOLD`, the hook exits `0`.
5. In `warn` or `scrub` mode, the hook emits JSON `hookSpecificOutput` with redacted context and exits `0`.
6. In default `block` mode, the hook writes a redacted suggestion to stderr and exits `2`.

**Claude Tool Guard Flow (`hooks/pre_tool_guard.py`):**

1. Claude Code invokes the command configured in `.claude/settings.json` for matched `PreToolUse` tools.
2. `main()` reads JSON from stdin and dispatches by `tool_name`.
3. File path tools are checked by `check_path_tool()`.
4. `Glob` and `Grep` inputs are checked by `check_glob_grep()`.
5. Bash/PowerShell commands are checked by `check_bash()` for sensitive reads, network exfiltration references, and inline PII.
6. Violations call `deny()`, write a reason to stderr, and exit `2`; allowed operations exit `0`.

**State Management:**
- The demo scripts are stateless across runs. Presidio analyzers, anonymizers, and encryption keys are constructed inside each process.
- `reversible_demo.py` keeps the encryption key in process memory only.
- Hook behavior is controlled through environment variables `PII_GUARD_THRESHOLD` and `PII_GUARD_MODE`.
- No database, cache, or persistent application state is detected.

## Key Abstractions

**Brazilian Checksum Validators:**
- Purpose: Reduce false positives for structured Brazilian identifiers.
- Examples: `test_presidio_br.py`
- Pattern: Pure validation functions normalize with `_digits()` and return `bool`; examples include `valida_cpf()`, `valida_cnpj()`, `valida_cnh()`, `valida_titulo_eleitor()`, `valida_pis()`, and `valida_cartao_sus()`.

**ChecksumPatternRecognizer:**
- Purpose: Extend Presidio `PatternRecognizer` with post-match checksum validation.
- Examples: `test_presidio_br.py`
- Pattern: Override `analyze()`, inspect matched text spans, raise score to `valid_score` for valid identifiers, and downgrade invalid identifiers to `invalid_score`.

**Recognizer Factory:**
- Purpose: Centralize the list of custom Brazilian recognizers.
- Examples: `test_presidio_br.py`, imported by `reversible_demo.py`
- Pattern: `build_br_recognizers()` returns a list of configured Presidio recognizer instances. Reuse this factory rather than duplicating BR recognizer definitions.

**Analyzer Factory:**
- Purpose: Build a Portuguese Presidio analyzer with spaCy and custom BR recognizers.
- Examples: `test_presidio_br.py`, `reversible_demo.py`
- Pattern: `build_analyzer()` constructs `NlpEngineProvider`, `RecognizerRegistry`, loads predefined recognizers, registers custom recognizers, and returns `AnalyzerEngine`.

**Operator Maps:**
- Purpose: Define anonymization behavior by entity type.
- Examples: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`
- Pattern: Use `OperatorConfig` dictionaries keyed by Presidio entity name, with `"DEFAULT"` as fallback.

**Hook Hit Model:**
- Purpose: Represent lightweight regex detections without depending on Presidio at hook runtime.
- Examples: `hooks/_pii_core.py`
- Pattern: `@dataclass Hit` with `kind`, `start`, `end`, `value`, and `score`.

**Hook Detection Pipeline:**
- Purpose: Provide fast PII and secret detection for prompt/tool guard hooks.
- Examples: `hooks/_pii_core.py`
- Pattern: `PATTERNS` stores `(kind, compiled_regex, score, optional_validator)` tuples; `detect()` filters by threshold and removes overlaps; `redact()` replaces spans with `<KIND>` markers.

## Entry Points

**English Presidio Demo:**
- Location: `test_presidio.py`
- Triggers: `python test_presidio.py`
- Responsibilities: Run default Presidio analysis/anonymization over fictitious English sample strings.

**Brazilian Presidio Demo:**
- Location: `test_presidio_br.py`
- Triggers: `python test_presidio_br.py`
- Responsibilities: Build Portuguese Presidio analyzer with custom Brazilian recognizers, display detections, and anonymize fictitious Portuguese samples.

**Reversible Encryption Demo:**
- Location: `reversible_demo.py`
- Triggers: `python reversible_demo.py`
- Responsibilities: Encrypt detected PII locally, simulate LLM handling of encrypted tokens, and restore original text locally.

**Local Ollama Demo:**
- Location: `ollama_local_demo.py`
- Triggers: `python ollama_local_demo.py`
- Responsibilities: Detect local Ollama availability, print setup guidance, or call localhost model generation.

**Prompt Guard Hook:**
- Location: `hooks/pii_guard.py`
- Triggers: `.claude/settings.json` `UserPromptSubmit` command `python "$CLAUDE_PROJECT_DIR/hooks/pii_guard.py"`
- Responsibilities: Inspect submitted prompts for PII and block/warn/scrub based on environment configuration.

**Pre-Tool Guard Hook:**
- Location: `hooks/pre_tool_guard.py`
- Triggers: `.claude/settings.json` `PreToolUse` matcher `Read|Bash|Grep|Glob|Edit|Write`
- Responsibilities: Prevent agent reads/writes/searches against sensitive paths and block risky shell commands.

**Hook Scanner Diagnostic:**
- Location: `hooks/_pii_core.py`
- Triggers: `python hooks/_pii_core.py`
- Responsibilities: Run a built-in scanner/redactor smoke demo for the lightweight hook detection core.

## Error Handling

**Strategy:** Demo scripts generally print status and continue through samples; hooks fail closed for policy violations with exit code `2`.

**Patterns:**
- `hooks/pii_guard.py` and `hooks/pre_tool_guard.py` tolerate invalid JSON stdin by returning `0`, avoiding hook crashes on malformed payloads.
- `hooks/pre_tool_guard.py` centralizes blocked policy outcomes through `deny(reason)`.
- `ollama_local_demo.py` catches `OSError` when probing localhost and returns setup guidance with process status `1` if Ollama is unavailable.
- Presidio demo scripts do not wrap analyzer/model initialization failures; missing dependencies or missing `pt_core_news_lg` fail at process startup.

## Cross-Cutting Concerns

**Logging:** Plain `print()` and `stderr` output only. There is no logging framework.

**Validation:** Brazilian document validation is implemented in `test_presidio_br.py`; hook-level validation is implemented in `hooks/_pii_core.py`. The two validation implementations are duplicated rather than shared.

**Authentication:** Not applicable. No application auth layer exists.

**Security Boundaries:** `.claude/settings.json` denies reads of `.env`, `.env.*`, `data_sensivel/**`, and credential-like files. `hooks/pre_tool_guard.py` enforces similar path rules and command scanning at runtime.

**External Runtime Boundaries:** `ollama_local_demo.py` sends traffic only to `127.0.0.1:11434`; Presidio demos run locally; Claude hook scripts are invoked by Claude Code through `.claude/settings.json`.

---

*Architecture analysis: 2026-05-01*
