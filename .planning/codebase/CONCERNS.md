# Codebase Concerns

**Analysis Date:** 2026-05-01

## Tech Debt

**Demo scripts are the main application surface:**
- Issue: The repo is organized as standalone demo/test scripts rather than a packaged application with clear runtime boundaries.
- Files: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`
- Impact: Future production code can accidentally reuse demo behavior such as printing original sensitive text, using hard-coded samples, or relying on local environment state.
- Fix approach: Move reusable Presidio recognizers and anonymization operators into a dedicated package module, keep demos under an explicit examples directory, and make production entry points avoid raw PII output by default.

**Recognizer logic duplicated across hook and Presidio demo layers:**
- Issue: Brazilian document validators and detection patterns exist in both a lightweight regex hook module and a Presidio-based recognizer script.
- Files: `hooks/_pii_core.py`, `test_presidio_br.py`
- Impact: The hook and Presidio paths can drift, causing a prompt/tool guard to miss identifiers that the Presidio path detects, or vice versa.
- Fix approach: Define a single shared recognizer contract with tests for CPF, CNPJ, phone, CEP, PIS/PASEP, SUS, license plates, and token/secret patterns; have hook code import the lightweight subset from that module.

**No dependency manifest or lockfile:**
- Issue: The repo imports `presidio_analyzer`, `presidio_anonymizer`, and spaCy model `pt_core_news_lg`, but no `requirements.txt`, `pyproject.toml`, lockfile, or setup docs are present.
- Files: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`
- Impact: Reproducing the environment depends on machine-local packages; future runs may fail or behave differently after dependency updates.
- Fix approach: Add a minimal dependency manifest with pinned compatible versions for Presidio, spaCy, and required language models; document model installation separately from runtime code.

**Generated Python cache files are present in the working tree:**
- Issue: `__pycache__` artifacts are present alongside source files.
- Files: `__pycache__/test_presidio_br.cpython-314.pyc`, `hooks/__pycache__/_pii_core.cpython-314.pyc`
- Impact: Generated files add noise, can mask stale code during manual inspection, and should not be treated as source artifacts.
- Fix approach: Exclude `__pycache__/` through `.gitignore` when the project is placed under version control and keep generated caches out of documentation and packaging.

## Known Bugs

**PII guard scrub mode does not actually rewrite the submitted prompt:**
- Symptoms: `PII_GUARD_MODE=scrub` returns additional context containing a redacted suggestion, but the original prompt remains the submitted prompt from the caller's perspective.
- Files: `hooks/pii_guard.py`
- Trigger: Set `PII_GUARD_MODE=scrub` and submit a prompt containing detected PII.
- Workaround: Use default `block` mode for sensitive prompts until the hook integration can replace or prevent the original prompt at the source.

**Hook messages can echo sensitive values back to stderr/stdout:**
- Symptoms: Detection summaries include raw matched values and redacted prompt suggestions, which can leak sensitive content into terminal logs, transcripts, or tool output.
- Files: `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, `hooks/_pii_core.py`
- Trigger: Submit detected PII to the prompt hook, run a blocked command with inline PII, or execute `hooks/_pii_core.py` directly.
- Workaround: Keep hook outputs to entity type, count, and character ranges; never include `h.value` or original snippets in user-facing hook messages.

**Ollama response parsing assumes successful JSON responses:**
- Symptoms: `call_ollama()` reads and parses the response body without checking HTTP status, error shape, or malformed JSON.
- Files: `ollama_local_demo.py`
- Trigger: Local Ollama returns a non-200 status, an error payload, partial response, or non-JSON body.
- Workaround: Check `resp.status` before parsing, catch `json.JSONDecodeError`, and return a controlled failure message without echoing the prompt.

## Security Considerations

**Sensitive data files live inside the project tree:**
- Risk: Real or realistic sensitive files are colocated with source code and are easy to read, copy, archive, or accidentally commit when version control is initialized.
- Files: `data_sensivel/cooperados.csv`, `data_sensivel/dump_2025_05.txt`, `.env`
- Current mitigation: `.claude/settings.json` denies several Claude Code read/glob/grep patterns and `hooks/pre_tool_guard.py` blocks matching paths for supported tool payloads. This audit did not read `.env` or the sensitive data file contents.
- Recommendations: Move real sensitive data outside the repo, keep only synthetic fixtures under source control, add `.gitignore` entries for `.env`, `data_sensivel/`, dumps, credentials, caches, and local model artifacts, and add a pre-commit secret/PII scanner before any repository is initialized.

**Guard enforcement depends on Claude Code hook configuration:**
- Risk: The privacy controls are effective only in clients that load `.claude/settings.json` and execute the Python hook scripts.
- Files: `.claude/settings.json`, `.claude/settings.local.json`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`
- Current mitigation: User prompt and pre-tool hooks are configured for Claude Code, and local allow rules are kept in `.claude/settings.local.json`.
- Recommendations: Treat hooks as defense in depth, not a data boundary. Add OS/filesystem permissions for sensitive data, use repository ignore rules, and include CLI tests that invoke hook scripts directly with representative payloads.

**Pre-tool guard is regex-based and bypassable:**
- Risk: `pre_tool_guard.py` tokenizes commands with a simple path regex and only detects selected command/path shapes; encoded paths, variable expansion, aliases, archive tools, copy commands, or scripts that read sensitive files indirectly may bypass it.
- Files: `hooks/pre_tool_guard.py`
- Current mitigation: It checks common read commands, network commands, path tools, glob/grep paths, and inline PII.
- Recommendations: Normalize resolved paths where possible, deny any command referencing sensitive directories regardless of command verb, add copy/archive/upload command detection, and test bypass cases such as quoted Windows paths, environment variables, wildcard expansion, and Python scripts.

**Raw PII is printed by demos before anonymization:**
- Risk: Demo execution writes original sensitive-looking text and detected snippets to terminal output.
- Files: `test_presidio.py`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py`
- Current mitigation: The Presidio test scripts label embedded samples as fictitious.
- Recommendations: Keep raw-output demos clearly separated from any production workflow, add a `--show-original` opt-in flag for demonstrations, and default examples to printing only anonymized output and aggregate detection counts.

**Reversible encryption key lifecycle is demo-only:**
- Risk: The reversible demo generates an in-memory AES key and notes production should use keyring/HSM, but there is no real key management or rotation boundary.
- Files: `reversible_demo.py`
- Current mitigation: The generated key is local and not printed.
- Recommendations: Do not reuse the demo key pattern for production. Use a managed key store, define retention and rotation rules, avoid logging encrypted tokens when they can be linked back through local maps, and separate deanonymization authority from analysis code.

## Performance Bottlenecks

**spaCy large Portuguese model is loaded per run:**
- Problem: Each invocation builds a new Presidio analyzer and loads `pt_core_news_lg`.
- Files: `test_presidio_br.py`, `reversible_demo.py`
- Cause: `build_analyzer()` constructs the NLP engine on every script execution.
- Improvement path: Cache analyzer construction in long-running processes, expose a reusable factory, and allow a smaller model for fast local validation where recall requirements permit it.

**Hook scanning can process full command/prompt text synchronously:**
- Problem: User prompt and tool command hooks scan text inline before the action proceeds.
- Files: `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, `hooks/_pii_core.py`
- Cause: Regex scanning and overlap filtering run synchronously on every guarded event.
- Improvement path: Keep hook patterns lightweight, cap scan length for command strings, benchmark worst-case regex inputs, and add tests for pathological inputs that could cause latency spikes.

## Fragile Areas

**Overlap resolution is implemented manually in multiple places:**
- Files: `hooks/_pii_core.py`, `test_presidio_br.py`
- Why fragile: The code sorts by score and start position, then drops overlapping hits. Equal-score behavior and broad patterns can suppress more specific recognizers depending on ordering.
- Safe modification: Add unit tests for overlapping CPF/CNH/PIS numeric patterns, phone versus CEP-like numbers, and credit-card versus generic numeric identifiers before changing recognizer scores.
- Test coverage: No automated test runner or assertion-based tests are present; existing `test_*.py` files behave as print-driven demos.

**Hook path matching is string-based:**
- Files: `hooks/pre_tool_guard.py`, `.claude/settings.json`
- Why fragile: Rules compare raw path strings and command tokens instead of canonical paths, so relative traversal, mixed separators, and quoted Windows paths need explicit coverage.
- Safe modification: Add path normalization tests for `data_sensivel`, `.env`, dump files, credential names, and nested sensitive directories before expanding allow/deny behavior.
- Test coverage: No assertion-based tests verify hook JSON inputs, exit codes, or stderr behavior.

**Demo imports mutate `sys.path`:**
- Files: `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, `reversible_demo.py`
- Why fragile: Direct `sys.path.insert()` makes imports depend on invocation location and local file names.
- Safe modification: Package reusable modules or use explicit module execution from a known project root; keep hook startup fast and dependency-light.
- Test coverage: No tests cover execution from alternate working directories.

## Scaling Limits

**Local-file sensitive data model has no governance boundary:**
- Current capacity: Current sensitive data files are small, with `data_sensivel/cooperados.csv` and `data_sensivel/dump_2025_05.txt` under 1 KB each.
- Limit: The current layout does not scale to larger datasets, multiple operators, access audits, retention policies, or controlled exports.
- Scaling path: Store sensitive datasets outside the source tree, use encrypted storage or governed data platforms, add access logging, and use synthetic fixtures in the project.

**Ollama demo assumes a single local model endpoint:**
- Current capacity: One local HTTP endpoint at `127.0.0.1:11434` and a default model string in `ollama_local_demo.py`.
- Limit: No model availability check beyond `/api/tags`, no model selection policy, no timeout/retry strategy, and no concurrency handling.
- Scaling path: Add an adapter layer for local LLM calls, validate allowed model names, set explicit privacy policies per task, and handle unavailable model/server states without exposing prompts.

## Dependencies at Risk

**Presidio and spaCy versions are implicit:**
- Risk: Detection behavior, entity types, NLP models, and anonymizer operators can change across versions.
- Impact: PII recall/precision, reversible anonymization behavior, and test outputs can drift without code changes.
- Migration plan: Pin versions in a manifest, record required spaCy model names, add smoke tests for expected entity counts, and run compatibility tests before dependency upgrades.

**Ollama model names are advisory and not verified:**
- Risk: `ollama_local_demo.py` suggests specific model names but does not confirm that the requested model exists before `/api/generate`.
- Impact: Demo failures are discovered only at generation time and may produce unclear errors.
- Migration plan: Query `/api/tags`, validate the selected model, and make model selection configurable through a non-secret environment variable or CLI argument.

## Missing Critical Features

**No automated regression test suite:**
- Problem: Existing files named `test_presidio.py` and `test_presidio_br.py` print demonstrations instead of making assertions.
- Blocks: Safe refactoring of recognizers, hook behavior, anonymization operators, and privacy guarantees.

**No source-control hygiene files:**
- Problem: There is no `.gitignore`, and this directory is not currently a Git repository.
- Blocks: Safe project sharing, review, or publication without first filtering `.env`, `data_sensivel/`, `__pycache__/`, generated dumps, and local configuration files.

**No documented data classification boundary:**
- Problem: The repo mixes demo code, hook code, local configuration, and sensitive-looking data in one directory.
- Blocks: Clear decisions about what can be sent to external LLMs, what must stay local, and what can be committed or shared.

## Test Coverage Gaps

**Hook behavior is untested:**
- What's not tested: JSON parsing failures, `block`/`warn`/`scrub` modes, threshold handling, redaction output, exit codes, and stderr/stdout safety.
- Files: `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, `hooks/_pii_core.py`
- Risk: A future hook edit can silently stop blocking sensitive prompts or can start leaking raw values in hook output.
- Priority: High

**Brazilian recognizers lack assertion-based fixtures:**
- What's not tested: Valid and invalid CPF/CNPJ/CNH/titulo/PIS/SUS checks, false positives from overlapping numeric patterns, and expected anonymization operator output.
- Files: `test_presidio_br.py`
- Risk: Recognizer changes can reduce recall or create excessive false positives without failing a test.
- Priority: High

**Local LLM privacy path is not verified:**
- What's not tested: That prompts containing sensitive data are only sent to `127.0.0.1`, that non-local endpoints are rejected, and that error handling does not print sensitive prompt content.
- Files: `ollama_local_demo.py`
- Risk: Future integration work can turn a local-only demonstration into an external request path.
- Priority: High

**Reversible anonymization round-trip has no automated check:**
- What's not tested: Encryption/decryption round-trip, behavior when no entities are detected, entity-token ordering, and failures with wrong keys.
- Files: `reversible_demo.py`
- Risk: Reversible anonymization can fail or restore incorrect text without automated detection.
- Priority: Medium

---

*Concerns audit: 2026-05-01*
