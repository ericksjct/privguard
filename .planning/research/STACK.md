# Technology Stack

**Project:** Privacy Guard for LLM Code Agents
**Researched:** 2026-05-01
**Scope:** Stack dimension only: Python packaging, Microsoft Presidio/spaCy, lightweight hook runtime, dependency pinning, and local-only operation.
**Overall confidence:** MEDIUM-HIGH

## Recommendation

Package this as a local-first Python library and CLI with two deliberately separate runtime paths:

1. **Hook runtime:** standard-library-only Python scripts for Claude Code `UserPromptSubmit` and `PreToolUse` events. This path must stay fast, dependency-light, and fail closed. It should block unsafe prompt/tool processing or return redacted context, but it should not load Presidio or spaCy.
2. **Analysis/masking runtime:** importable package modules using Microsoft Presidio, Presidio Anonymizer, and spaCy Portuguese models for higher-quality Brazilian PII detection and masking. This path can pay the spaCy model load cost and should be used by explicit CLI commands, tests, and any longer-running masking process.

Do not build a server, SaaS proxy, or remote gateway in the first roadmap. The product value depends on raw sensitive data staying local before any external LLM submission.

## Recommended Stack

### Core Packaging

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | `>=3.10,<3.14` for package support; current local interpreter is 3.14.3 but should be treated as a dev-machine outlier | Runtime and package language | Official Presidio docs list support for Python 3.10, 3.11, 3.12, and 3.13. Avoid advertising Python 3.14 support until Presidio/spaCy wheels and tests prove it. |
| `pyproject.toml` | PEP 621 metadata | Build and dependency manifest | The repo has no manifest today. A package manifest is required for reproducible installs, console scripts, optional extras, and version constraints. |
| `hatchling` or `setuptools` | Current stable | Build backend | Use `hatchling` for a clean new package. Use `setuptools` only if compatibility with existing Python packaging habits matters more than simplicity. |
| `pip-tools` or `uv` lock workflow | Current stable | Dependency pinning | Keep broad package constraints in `pyproject.toml`, then generate a lock/constraints file for exact reproducible installs. For privacy/compliance demos, exact dependency versions matter. |
| `pytest` | Current stable | Regression tests | Required to prove hooks block, masking does not echo raw values, and Brazilian validators do not drift. No formal test runner exists today. |
| `ruff` | Current stable | Lint/format | Lightweight single-tool linting and formatting for a small Python package. |

### Package Layout

Use a `src/` package layout:

```text
src/privacy_guard/
  __init__.py
  cli.py
  policy.py
  masking.py
  recognizers/
    br.py
    validators.py
  hooks/
    pii_core.py
    claude_prompt.py
    claude_pre_tool.py
```

Keep root demo scripts only as examples after extraction:

```text
examples/
  presidio_br_demo.py
  reversible_demo.py
  ollama_local_demo.py
```

This removes the current ambiguity where files named `test_*.py` are runnable demos rather than assertion-based tests.

### Presidio and spaCy

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `presidio-analyzer` | Pin initially to the installed/recent line, preferably `==2.2.362` after compatibility check; otherwise keep current local `==2.2.359` until tests are green | PII detection engine | Presidio is the right base because it supports predefined and custom recognizers. The project already has Brazilian checksum recognizers built on it. |
| `presidio-anonymizer` | Pin with analyzer, preferably `==2.2.362` after compatibility check; current local anonymizer is `2.2.362` | Masking, replacement, encryption/decryption operators | The anonymizer already supports the replacement/mask/encrypt patterns demonstrated locally. |
| `spacy` | Pin to `~=3.8` initially | NLP engine used by Presidio | Local code already uses spaCy through Presidio `NlpEngineProvider`. spaCy is cross-platform and supports Portuguese trained pipelines. |
| `pt_core_news_lg` | Install as a model asset matching spaCy 3.8 | Portuguese NLP for Brazilian text | Current code requires `pt_core_news_lg`. Keep it for recall-oriented analysis; add a separate fast-mode investigation before switching to `pt_core_news_sm`. |
| `cryptography` | Transitive via `presidio-anonymizer`, lock exact version | Encryption/decryption operator dependency | Required if reversible anonymization demos remain. V1 product should mask before submission and avoid deanonymization by default, but tests should still pin this transitive dependency. |

The first package milestone should preserve existing Brazilian validators for CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS, RG, phone, CEP, and vehicle plates, but move them into shared importable modules. The hook scanner and Presidio recognizers should reuse the same validator functions to prevent drift.

### Hook Runtime

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python standard library | Same interpreter as CLI | Low-latency hook execution | Hooks run in the agent loop. Loading spaCy on every prompt/tool event is too slow and too failure-prone. |
| Regex + checksum validators | Local package module | Fast detection of high-confidence identifiers and secrets | This is appropriate for prompt/tool blocking, especially CPF/CNPJ/Luhn/secret/token patterns. |
| JSON stdin/stdout contract | Claude Code hook protocol | Communicate block/allow decisions | Claude Code hooks pass event payloads through stdin and support exit-code and JSON decisions. |
| Exit code `2` and JSON `decision`/`permissionDecision` | Claude Code hook protocol | Fail closed on unsafe prompt/tool use | Official Claude Code docs state that `UserPromptSubmit` can block prompt processing and `PreToolUse` can block tool calls. |

Keep hook output sterile:

- Do not print raw matched values.
- Do not include original snippets in stderr/stdout.
- Use entity type, count, character range, and redacted suggestions only.
- Treat `scrub` mode as advisory unless the integration can prove the original prompt/tool input is replaced before model submission.

## Claude Code and Codex Integration Status

### Claude Code

Claude Code is the first concrete integration target.

Official Claude Code docs currently document:

- `UserPromptSubmit` runs when the user submits a prompt, before Claude processes it, and can validate or block prompts.
- `PreToolUse` runs after Claude creates tool parameters and before the tool call is processed.
- Exit code `2` blocks `PreToolUse` tool calls.
- Exit code `2` for `UserPromptSubmit` blocks prompt processing, erases the prompt, and shows stderr to the user.
- Structured JSON output can also block `UserPromptSubmit`, and `PreToolUse` can use `hookSpecificOutput.permissionDecision = "deny"`.

Roadmap implication: implement Claude support first and test it directly by piping synthetic JSON payloads into hook entry points. Default behavior should be block/fail-closed.

### OpenAI Codex

Treat Codex support as a compatibility investigation, not an assumed v1 surface.

Current OpenAI Codex public docs describe Codex CLI operation, approval modes, local execution, and sandbox/network behavior, but the official docs page checked during research did not document a Claude-equivalent hook contract. The open-source `openai/codex` repository and recent issues show hook work and discussion around `UserPromptSubmit`, `PreToolUse`, and `PostToolUse`, including reports that some tool paths may not emit pre/post tool hook events consistently. That means Codex hook coverage appears less settled than Claude Code.

Roadmap implication: do not promise automatic Codex masking/blocking until a phase verifies the exact installed Codex version, hook file format, supported events, Windows behavior, and tool coverage for shell, file reads, file writes, apply-patch-style edits, MCP tools, and IDE entry points.

## Dependency Pinning Strategy

Use three dependency layers:

1. `pyproject.toml` package requirements:
   - `python = ">=3.10,<3.14"`
   - `presidio-analyzer ~=2.2`
   - `presidio-anonymizer ~=2.2`
   - `spacy ~=3.8`
2. `requirements.lock` or equivalent generated lock:
   - Exact pins for production/test reproducibility.
   - Include transitive versions for `cryptography`, `phonenumbers`, `regex`, `pyyaml`, `tldextract`, and spaCy dependencies.
3. Model installation docs:
   - Keep spaCy model setup explicit, for example `python -m spacy download pt_core_news_lg`.
   - If installing the model as a wheel URL, pin the exact wheel compatible with the locked spaCy version.

Do not hide model downloads inside runtime code. Runtime should fail with a clear local setup error if the model is missing.

## Local-Only Operation

Required defaults:

- No remote service calls from the privacy guard package.
- No telemetry.
- No external LLM SDK dependency in the core package.
- No reading `.env`, `data_sensivel/`, dumps, credentials, or secret-like files during tests or docs generation.
- Synthetic fixtures only.
- Optional Ollama support must remain `127.0.0.1` only and should live behind an optional extra such as `privacy-guard[ollama]` or an examples-only path.

Recommended policy modes:

| Mode | Behavior | Use |
|------|----------|-----|
| `strict` | Block on any high-confidence sensitive data or protected path | Default for Claude hooks and CI-style checks |
| `mask` | Return or write masked text only when the integration can guarantee replacement before model submission | CLI and controlled integrations |
| `warn` | Report counts/types without blocking | Local tuning and false-positive analysis only |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Runtime boundary | Local package + hooks | Cloud proxy/SaaS | Violates current local-only privacy boundary and creates a new exfiltration surface. |
| Hook implementation | Standard-library scanner | Presidio/spaCy inside hooks | spaCy model startup is too heavy for prompt/tool hook latency and makes hooks fragile when dependencies are missing. |
| PII engine | Presidio + custom BR recognizers | Hand-rolled regex only | Regex-only detection is useful for hooks but insufficient for higher-quality name/context detection and anonymization workflows. |
| Python version target | `>=3.10,<3.14` | Require Python 3.14 | Local machine has 3.14.3, but official Presidio docs list support only through 3.13. |
| Codex integration | Investigate compatibility phase | Assume Claude-style parity | Official OpenAI Codex docs do not currently provide the same stable hook reference found in Claude docs; GitHub issues indicate active evolution. |
| Dependency management | `pyproject.toml` + lock | Ad hoc installed packages | Current repo is not reproducible without local machine state. |

## Installation Sketch

```bash
python -m venv .venv
python -m pip install -U pip
python -m pip install -e ".[presidio,dev]"
python -m spacy download pt_core_news_lg
```

Suggested extras:

```toml
[project.optional-dependencies]
presidio = [
  "presidio-analyzer~=2.2",
  "presidio-anonymizer~=2.2",
  "spacy~=3.8",
]
dev = [
  "pytest",
  "ruff",
]
ollama = []
```

Keep the hook entry points usable without installing the `presidio` extra.

## Roadmap Implications

1. **Packaging foundation first**
   - Add `pyproject.toml`, `src/privacy_guard/`, CLI entry point, lint/test tooling, and lock workflow.
   - Move duplicated validators into shared modules.
   - Keep hooks dependency-light.

2. **Claude hook hardening second**
   - Port current `hooks/` into package-backed scripts or thin wrappers.
   - Add tests for `UserPromptSubmit` and `PreToolUse` JSON payloads, exit codes, stderr safety, and protected paths.
   - Make default mode strict/block.

3. **Presidio masking engine third**
   - Extract Brazilian recognizers and operator maps.
   - Add synthetic fixtures for entity detection and masking.
   - Benchmark model loading and decide whether a long-running local process is necessary later.

4. **Codex compatibility investigation later**
   - Verify actual installed Codex hook behavior.
   - Check whether prompt, shell, read, write, patch, MCP, and IDE tool paths are interceptable.
   - Only then decide whether to support Codex through hooks, wrappers, sandbox policy, or documented unsupported mode.

## Sources

- Project context: `.planning/PROJECT.md`
- Codebase context: `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONCERNS.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/INTEGRATIONS.md`, `.planning/codebase/STACK.md`, `.planning/codebase/STRUCTURE.md`, `.planning/codebase/TESTING.md`
- Microsoft Presidio installation docs: https://microsoft.github.io/presidio/installation/
- spaCy installation docs: https://spacy.io/usage
- Claude Code hooks reference: https://docs.anthropic.com/en/docs/claude-code/hooks
- OpenAI Codex CLI docs: https://developers.openai.com/codex/cli
- OpenAI Codex repository: https://github.com/openai/codex
- Codex hook compatibility signals from open GitHub issues: https://github.com/openai/codex/issues/14754, https://github.com/openai/codex/issues/16226, https://github.com/openai/codex/issues/16732

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Python packaging recommendation | HIGH | Based on current repo gaps and standard Python packaging practice. |
| Presidio/spaCy recommendation | HIGH | Existing code already works around this stack; official Presidio docs confirm package/model installation pattern and supported Python versions. |
| Lightweight hook runtime | HIGH | Existing repo already uses this shape; Claude docs confirm hook blocking semantics. |
| Dependency versions | MEDIUM | Local installed versions differ slightly from latest PyPI snippets. Pin after running package tests. |
| Codex hook support | LOW-MEDIUM | Public OpenAI docs are not as explicit as Claude docs, and GitHub issues indicate active hook evolution. Requires phase-specific validation. |

