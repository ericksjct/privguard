# Architecture Patterns

**Domain:** Local privacy guard package for LLM/code-agent terminal and IDE workflows
**Researched:** 2026-05-01
**Confidence:** MEDIUM-HIGH

## Recommended Architecture

Build the project as a local Python package with a small CLI and thin client adapters around a shared privacy core. The current repo already proves the two hard parts separately: Presidio-backed Brazilian detection/masking in root demo scripts and Claude Code prompt/tool hooks in `hooks/`. The roadmap should merge those into one package boundary so Claude, Codex-style wrappers, future IDE adapters, and diagnostics all use the same detector, masking, and policy contracts.

Recommended package shape:

```text
privacy_guard/
  detectors/          # shared lightweight + Presidio-backed detection
  masking/            # redaction, replacement, hashing, optional encryption operators
  policy/             # mode, threshold, protected paths, fail-closed decisions
  adapters/
    claude/           # UserPromptSubmit and PreToolUse command handlers
    codex/            # wrapper/proxy/hook-compatible handlers when validated
    ide/              # future IDE extension bridge, not v1 core
  cli/                # diagnostics, scan, mask, explain-policy
  testing/            # synthetic fixtures and adapter harness helpers
```

Keep the runtime boundary local: raw input enters a detector process on the user's machine, policy decides whether the content can be rewritten safely, masking transforms it when possible, and only masked text may continue to an external LLM provider. If an adapter cannot replace the outbound content with the masked version before provider submission, it must block and report a safe reason without echoing raw matches.

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| Shared detector library | Detect Brazilian PII, credentials, sensitive paths, and secret-like values through one stable `DetectionResult` contract. | Masking engine, policy engine, CLI diagnostics, adapter tests |
| Lightweight detector | Fast regex/checksum scanner for hook paths where startup latency and dependency footprint matter. | Hook adapters, policy engine, unit tests |
| Presidio detector | Higher-recall analyzer using Microsoft Presidio, spaCy Portuguese NLP, custom Brazilian recognizers, and checksum validation. | CLI diagnostics, batch/local scan commands, masking engine |
| Masking engine | Convert detection spans into safe outbound text using deterministic replacement/redaction/masking/hash operators. | Detector library, policy engine, adapters |
| Policy engine | Decide `allow`, `rewrite`, `block`, or `local_only` based on mode, confidence threshold, client rewrite capability, tool type, protected path rules, and provider trust. | All adapters, CLI, tests |
| Hook adapters | Translate client-specific JSON/stdin events into normalized requests and enforce policy decisions with client-native block/rewrite semantics. | Policy engine, masking engine, detector library |
| CLI diagnostics | Provide local commands to scan synthetic text/files, explain matches, print effective policy, validate hook config, and dry-run masking. | Detector library, policy engine, masking engine |
| Tests/fixtures | Prove that raw sensitive values are not emitted to stdout/stderr, logs, masked payloads, or hook contexts. Use synthetic data only. | Every package component |
| Packaging | Provide reproducible install, entry points, optional Presidio extras, and pinned dependency ranges. | CLI, adapters, test runner |

## Data Flow

### Prompt/Message Flow

```text
client event
  -> adapter parses event into GuardRequest
  -> policy identifies client capabilities and trust boundary
  -> detector scans prompt/tool payload
  -> masking engine produces masked text when required
  -> policy emits GuardDecision
  -> adapter applies native rewrite or blocks fail-closed
```

For Claude Code today, `UserPromptSubmit` can block before the prompt is processed, but the current `scrub` mode only adds redacted context; it does not replace the submitted prompt. Treat that as a block-only surface until a verified rewrite mechanism exists. `PreToolUse` can block reads/searches/commands before execution and should remain the primary guard for protected files and tool payloads.

### Tool/File Flow

```text
tool request
  -> adapter normalizes tool name and input fields
  -> policy checks protected paths before content access
  -> if content is already present, detector scans inline strings
  -> if content must be read to mask, adapter must prove local-only read and rewrite support
  -> otherwise block with safe diagnostic
```

Protected paths such as `.env`, `.env.*`, `data_sensivel/**`, dumps, credentials, and secret-like files should be blocked before file reads. Do not design a path where the guard reads protected raw files merely to generate better diagnostics for an external model workflow.

## Shared Detector Library

The detector API should be independent of Presidio-specific classes so adapters do not depend on `AnalyzerEngine`, spaCy startup, or Presidio result shapes.

```python
@dataclass(frozen=True)
class DetectionResult:
    kind: str
    start: int
    end: int
    score: float
    source: str
    validator: str | None = None

class Detector(Protocol):
    def detect(self, text: str, *, min_score: float) -> list[DetectionResult]:
        ...
```

Use the existing `hooks/_pii_core.py` approach as the lightweight detector seed, but move it into the package and share validators with the Presidio recognizer layer. Preserve the Brazilian checksum validators as pure functions with direct tests for valid and invalid CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS, RG-like identifiers, phone, CEP, vehicle plates, credit cards, API keys, environment variable assignments, and credential tokens.

Use Presidio as the richer detector behind a separate adapter. Official Presidio docs confirm that `AnalyzerEngine` coordinates recognizers through a `RecognizerRegistry`, supports custom recognizers, and that `PatternRecognizer` covers regex, deny-list, validation, invalidation, and context logic. This matches the current `ChecksumPatternRecognizer` direction and should be the production path for Portuguese/Brazilian detection quality.

## Masking Engine

The masking engine owns span application, overlap resolution, and output guarantees. It should accept normalized detection results and return a structured result:

```python
@dataclass(frozen=True)
class MaskingResult:
    masked_text: str
    replacements: list[Replacement]
    raw_value_count: int
    safe_for_external: bool
```

Recommended defaults:

| Entity class | Default operator | Rationale |
|--------------|------------------|-----------|
| CPF/CNPJ/CNH/PIS/SUS/voter title/RG | Stable typed replacement, e.g. `<CPF>` | Keeps meaning without leaking identifiers |
| API keys/tokens/passwords/env values | Full redact, e.g. `<SECRET>` | Partial masks can preserve exploitable material |
| Names/contact/bank/account data | Typed replacement or partial mask by strict policy | Maintains task context while minimizing disclosure |
| File paths under protected roots | Path category replacement, e.g. `<SENSITIVE_PATH>` | Avoids revealing local data layout |

Presidio anonymizer supports replace, redact, hash, mask, and encrypt operators, but v1 should default to irreversible masking before external submission. Reversible encryption is useful for local-only demos and later workflows, but it adds key lifecycle, retention, and deanonymization authority that the project explicitly does not need in v1.

## Policy Engine

Policy is the central safety boundary. Do not bury decisions in adapters or detector thresholds.

Policy inputs:

| Input | Examples |
|-------|----------|
| Privacy mode | `strict`, `balanced`, `diagnostic`, `local_only` |
| Provider trust | external Anthropic/OpenAI, local Ollama, unknown |
| Client capability | can block, can rewrite prompt, can rewrite tool args, can only warn |
| Detection results | entity kinds, score, span count, source detector |
| Tool intent | prompt, read, grep, glob, shell, write, edit, network |
| Path classification | protected, sensitive-name, normal, unknown |

Policy outputs:

| Decision | Meaning | Adapter behavior |
|----------|---------|------------------|
| `allow` | No policy-relevant risk detected. | Continue silently. |
| `rewrite` | Sensitive content detected and adapter can safely substitute masked content. | Submit only masked content. |
| `block` | Sensitive content detected and rewrite is unavailable, unverified, or failed. | Stop client action. |
| `local_only` | Raw content may be used only with local model/tool target. | Route to local adapter or block external path. |
| `diagnose` | Safe summary for humans/tests. | Print entity counts/ranges only, no raw values. |

Fail-closed rule: if the policy cannot prove that raw content was replaced before external submission, the decision is `block`. Warning-only modes are acceptable for diagnostics, but they must be visibly non-enforcing and must not be the default.

## Hook Adapters

Adapters should be thin translators from client events to `GuardRequest` and from `GuardDecision` to client-native behavior.

### Claude Adapter

Current Claude Code docs state that hooks receive JSON on stdin, `UserPromptSubmit` fires before prompt processing, `PreToolUse` fires before tool execution, and blocking surfaces can stop with exit code `2` or structured JSON decisions. Use that official contract as the first production integration.

Implement:

| Adapter command | Event | Behavior |
|-----------------|-------|----------|
| `privacy-guard claude prompt` | `UserPromptSubmit` | Detect prompt PII; block unless verified rewrite is supported. |
| `privacy-guard claude tool` | `PreToolUse` | Block protected paths, risky shell reads, exfiltration commands, and inline sensitive values. |
| `privacy-guard claude validate-config` | CLI diagnostic | Confirm hook commands, project root, mode, and protected path rules. |

Avoid printing raw matches to stderr/stdout. Current hook code can echo values in summaries; the package version should emit entity kind, count, score bucket, and safe remediation text only.

### Codex and IDE Adapters

Treat Codex/IDE support as compatibility targets until their interception and rewrite surfaces are validated. The architecture should support them through the same adapter contract, but the policy engine must classify unverified clients as block-only for sensitive content.

Do not promise automatic masking for a client until tests prove:

1. The adapter sees the full outbound prompt/tool payload before provider submission.
2. The adapter can replace that payload atomically.
3. The original payload is not kept in transcript, logs, telemetry, debug output, or tool context.
4. Failure during detection/masking/rewrite blocks submission.

## CLI Diagnostics

The CLI is for local verification, not a bypass around hooks.

Recommended commands:

```text
privacy-guard scan --text "..."
privacy-guard scan --file path --synthetic-ok
privacy-guard mask --text "..."
privacy-guard explain-policy --client claude --event UserPromptSubmit
privacy-guard validate-hooks --client claude
privacy-guard doctor
```

Diagnostics should default to safe output:

- Print entity types, counts, offsets, confidence buckets, and detector source.
- Print masked text only when explicitly requested.
- Never print raw detected values unless an explicit local-only debug flag is set, and keep that flag out of hook paths.
- Refuse to scan `.env` and `data_sensivel/**` unless the command is a purely local policy test that does not read file contents.

## Tests and Fixtures

Tests are a first-class architecture boundary because the product promise is negative: sensitive values must not leak.

Recommended test layout:

```text
tests/
  unit/
    test_br_validators.py
    test_lightweight_detector.py
    test_masking_engine.py
    test_policy_engine.py
  integration/
    test_claude_prompt_adapter.py
    test_claude_tool_adapter.py
    test_cli_diagnostics.py
  fixtures/
    synthetic_br.py
    synthetic_secrets.py
```

Required assertions:

| Test area | Must prove |
|-----------|------------|
| Detector parity | Lightweight and Presidio detectors share validator truth for key Brazilian identifiers. |
| Masking safety | Masked text contains no original sensitive substrings. |
| Overlap handling | More specific/high-confidence spans win deterministically. |
| Hook block behavior | Sensitive prompt/tool input exits blocked when rewrite is not guaranteed. |
| Output hygiene | stdout/stderr/log output never contains raw matched values. |
| Path policy | `.env`, `data_sensivel/**`, dumps, credentials, mixed separators, traversal, and quoted Windows paths block before reads. |
| Failure behavior | Detector exceptions, Presidio startup failures, malformed payloads, and masking errors block external submissions in enforcing paths. |

Use only synthetic Brazilian identities, fake credentials, and fake file paths in fixtures. Real `.env` values and `data_sensivel` contents must never become fixtures, snapshots, planning text, or test logs.

## Packaging

Move from demo scripts to installable package before adding more integrations.

Recommended packaging decisions:

| Concern | Recommendation |
|---------|----------------|
| Build metadata | Use `pyproject.toml` with package entry points. |
| Runtime entry point | Expose `privacy-guard` console script. |
| Hook startup | Keep hook adapter dependencies minimal; lazy-load Presidio only for commands that need it. |
| Optional dependencies | Use extras such as `privacy-guard[presidio]`, `privacy-guard[dev]`, and later `privacy-guard[ide]`. |
| spaCy model | Document and validate model installation separately; fail with a safe setup error. |
| Demo scripts | Move existing scripts under `examples/` and make raw output opt-in. |

Do not make Presidio/spaCy startup required for every hook invocation if the lightweight detector can enforce the common prompt/tool cases. Use the richer Presidio detector in CLI scans, batch validation, and any long-running daemon/wrapper mode where model load cost is acceptable.

## Patterns to Follow

### Pattern 1: Normalized Guard Contracts

**What:** Convert every client event into a `GuardRequest` and every policy result into a `GuardDecision`.
**When:** All adapters and CLI commands.

```python
@dataclass(frozen=True)
class GuardRequest:
    surface: str
    client: str
    payload: str
    provider: str | None
    can_rewrite: bool
    tool_name: str | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

@dataclass(frozen=True)
class GuardDecision:
    action: Literal["allow", "rewrite", "block", "local_only", "diagnose"]
    safe_text: str | None
    reason_code: str
    diagnostics: Mapping[str, int | str]
```

### Pattern 2: Detect Then Mask Then Verify

**What:** After masking, run a lightweight verification pass that checks the masked text does not contain detected raw substrings.
**When:** Every `rewrite` decision headed toward an external provider.

```python
masked = masking_engine.mask(text, detections, policy)
if not masked.safe_for_external:
    return GuardDecision(action="block", safe_text=None, reason_code="mask_verify_failed", diagnostics={})
```

### Pattern 3: Path Policy Before Content Policy

**What:** Classify protected paths before opening files or letting client tools read them.
**When:** Read, grep, glob, shell, edit, write, and file-context ingestion events.

```python
if policy.is_protected_path(path):
    return GuardDecision(action="block", safe_text=None, reason_code="protected_path", diagnostics={})
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Adapter-Specific Detector Forks

**What:** Claude hooks, CLI, and future IDE adapters each maintain separate regexes and validators.
**Why bad:** Detection drift means one surface can miss identifiers another surface catches.
**Instead:** One detector package with lightweight and Presidio implementations behind the same contract.

### Anti-Pattern 2: "Scrub" That Only Adds Context

**What:** Returning a redacted suggestion while the original prompt still proceeds.
**Why bad:** It creates false confidence and still leaks clear text.
**Instead:** Use verified rewrite only; otherwise block.

### Anti-Pattern 3: Raw Diagnostics in Security Paths

**What:** Printing matched values, snippets, original prompts, or commands to stderr/stdout.
**Why bad:** Hook output and terminal transcripts become secondary leak channels.
**Instead:** Print safe reason codes, entity types, counts, and offsets.

### Anti-Pattern 4: Reading Sensitive Files to Decide Whether They Are Sensitive

**What:** Opening `.env`, dumps, or `data_sensivel/**` to scan contents before deciding.
**Why bad:** The guard itself becomes a raw-data exfiltration path through logs, exceptions, or model context.
**Instead:** Block protected paths by path policy first; scan only synthetic or explicitly allowed local files.

## Fail-Closed Behavior

The fail-closed behavior must be explicit and testable:

| Failure condition | Required decision |
|------------------|-------------------|
| Client cannot rewrite prompt/tool payload | Block sensitive content. |
| Client rewrite semantics are undocumented or untested | Block sensitive content. |
| Detector raises exception in enforcing path | Block external submission with safe setup/error reason. |
| Masking engine fails or verification finds raw substrings | Block external submission. |
| Policy cannot classify provider as local/trusted | Treat as external and enforce masking/blocking. |
| Hook receives malformed payload | For non-sensitive unknown payloads, current hooks fail open; production enforcing adapters should fail closed when the action is external or contains accessible payload text. |
| Diagnostic output would include raw values | Omit values or block diagnostic output. |

This is stricter than the current script behavior and should be a roadmap requirement. The project value is privacy assurance, so a blocked workflow is preferable to silent clear-text leakage.

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| Hook latency | Lightweight detector per event is enough. | Add benchmarks and optional long-running local daemon for Presidio-heavy checks. | Enterprise policy service may distribute signed configs, but raw scanning stays local. |
| Policy management | Local config file and CLI doctor. | Versioned policy profiles, org defaults, CI checks. | Central policy distribution with local enforcement and audit-safe telemetry. |
| Detector quality | Synthetic unit fixtures for Brazilian identifiers. | Golden corpus of synthetic prompts and adapter regressions. | Formal evaluation suite by locale/domain, still synthetic or approved de-identified data. |
| Packaging | `pip install -e .` and console script. | Published internal package with extras and lockfile. | Signed releases, SBOM, reproducible builds, extension marketplace packages. |
| Client coverage | Claude hooks first. | Add validated Codex/wrapper and one IDE integration. | Adapter SDK and certification tests for third-party clients. |

## Sources

- Project context: `.planning/PROJECT.md` (read 2026-05-01).
- Codebase maps: `.planning/codebase/ARCHITECTURE.md`, `CONCERNS.md`, `CONVENTIONS.md`, `INTEGRATIONS.md`, `STACK.md`, `STRUCTURE.md`, `TESTING.md` (read 2026-05-01).
- Microsoft Presidio Analyzer docs: https://microsoft.github.io/presidio/analyzer/ (HIGH confidence for analyzer/recognizer boundaries).
- Microsoft Presidio recognizer development docs: https://microsoft.github.io/presidio/analyzer/adding_recognizers/ and https://microsoft.github.io/presidio/analyzer/developing_recognizers/ (HIGH confidence for custom recognizer approach).
- Microsoft Presidio Anonymizer docs: https://microsoft.github.io/presidio/anonymizer/ and https://microsoft.github.io/presidio/anonymizer/adding_operators/ (HIGH confidence for masking/operator capabilities).
- Claude Code hooks reference: https://code.claude.com/docs/en/hooks (HIGH confidence for Claude hook event/blocking behavior as of 2026-05-01 crawl).
