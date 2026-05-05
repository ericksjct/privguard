# Phase 05: synthetic-regression-gate - Research

**Researched:** 2026-05-04 [VERIFIED: system date]
**Domain:** Python pytest privacy regression gate for synthetic-only PII masking/blocking behavior [VERIFIED: .planning/ROADMAP.md]
**Confidence:** HIGH [VERIFIED: codebase inspection + pytest run + official pytest docs]

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

## Implementation Decisions

### Gate Shape
- **D-01:** The v1 regression gate should be pytest-native, not a separate custom runner. The
  primary developer command remains `python -m pytest tests -q`.
- **D-02:** Add one or more Phase 5 regression tests that aggregate existing package, Claude, and
  Codex behaviors into an auditable v1 gate. Prefer a focused `tests/test_v1_regression_gate.py`
  style file over broad rewrites of existing tests.
- **D-03:** The gate should map directly to TEST-01 through TEST-06 so future reviewers can see
  which v1 requirement each check protects.

### Synthetic Fixture Policy
- **D-04:** All tests must use inline synthetic Brazilian PII, fake secrets, and fake protected
  paths. No test may read `.env`, `.env.*`, `data_sensivel/**`, real dumps, or real credentials.
- **D-05:** Existing constants in tests can remain if they are clear and synthetic. The planner may
  introduce a shared `tests` helper only if it reduces duplication without obscuring which fixture
  value is being checked.
- **D-06:** Synthetic fixture values should be intentionally fake and obvious, such as checksum-valid
  sample CPF/CNPJ values, fake `sk-test-...` tokens, `.env`, `data_sensivel/synthetic.csv`,
  `dump_*`, `*.cooperados.csv`, and `*.cpf.txt`.

### Leakage Surfaces
- **D-07:** TEST-02 must cover all relevant output surfaces already present in v1: CLI stdout/stderr,
  CLI JSON, Claude hook stdout/stderr, hook JSON/additionalContext, masked payload verification,
  diagnostic serialization, exception/failure paths where applicable, and documentation/claim text
  scanned by Codex gates.
- **D-08:** Output hygiene assertions should fail on raw synthetic sensitive values, secret-looking
  prefixes, protected path strings, original prompt snippets, command snippets where they would echo
  protected paths, and unsafe `redacted=` style prompt payload echoes.
- **D-09:** Sanitized metadata remains allowed: entity kind, offsets, counts, scores, reason codes,
  policy action, surface capability, support label, and synthetic-data markers.

### Coverage Priorities
- **D-10:** Phase 5 must preserve existing coverage for valid and invalid Brazilian identifiers,
  overlap handling, false-positive lookalikes, Windows/mixed/relative/quoted path normalization,
  malformed hook JSON, policy modes, and fail-closed capability decisions.
- **D-11:** Phase 5 should add missing tests rather than reorganizing the whole suite. Refactors are
  allowed only when they make the gate easier to audit and keep diffs small.
- **D-12:** The gate should include failure-mode coverage for invalid configuration or threshold
  values, incomplete masking, unverified masking, unknown/external/unsupported surfaces, and
  unsupported Codex automatic masking claims.

### Runtime Boundaries
- **D-13:** The v1 gate should not require network access, local Ollama, real Codex execution, real
  Claude execution, Presidio model downloads, or access to protected files. It should run locally
  from synthetic inputs using the package modules and existing hook entry points.
- **D-14:** Environment-specific warnings, such as pytest cache write warnings on this machine, are
  acceptable if tests pass and the warning does not indicate a privacy failure.

### the agent's Discretion
- The planner may decide whether the aggregate gate is one file or a small set of files.
- The planner may decide whether to use helper functions, fixtures, or plain test constants.
- The planner may decide whether to add a lightweight coverage/traceability table in a test
  docstring, comments, or a planning summary, as long as TEST-01..TEST-06 are visibly covered.

### Claude's Discretion

- The planner may decide whether the aggregate gate is one file or a small set of files.
- The planner may decide whether to use helper functions, fixtures, or plain test constants.
- The planner may decide whether to add a lightweight coverage/traceability table in a test
  docstring, comments, or a planning summary, as long as TEST-01..TEST-06 are visibly covered.

### Deferred Ideas (OUT OF SCOPE)

- Real coverage tooling, CI configuration, signed releases, SBOMs, enterprise telemetry, local proxy
  mode, LangChain/LlamaIndex adapters, and additional IDE agents remain outside Phase 5 unless a
  later roadmap update promotes them.
- Phase 4 final verification and roadmap closure should be completed before executing Phase 5 if it
  remains pending.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | Test suite uses only synthetic Brazilian PII, fake secrets, and fake protected paths. [VERIFIED: .planning/REQUIREMENTS.md] | Add a safe fixture-origin gate that scans test constants/source paths while excluding `.env*`, `data_sensivel/**`, `.git`, `.planning`, caches, and bytecode. [VERIFIED: tests/test_codex_claim_gate.py + 05-CONTEXT.md] |
| TEST-02 | Tests assert raw sensitive fixture values never appear in stdout, stderr, logs, hook JSON, masked payloads, or exception messages. [VERIFIED: .planning/REQUIREMENTS.md] | Use `capsys`, JSON parsing, `to_json()`, `format_text()`, hook entry points, and selected failure-path tests to assert forbidden synthetic values are absent. [VERIFIED: tests/test_cli.py + tests/test_claude_hooks.py + tests/test_masking.py] |
| TEST-03 | Tests cover valid and invalid Brazilian identifier examples, overlap handling, and false-positive lookalikes. [VERIFIED: .planning/REQUIREMENTS.md] | Existing detection tests already cover valid/invalid checksum IDs, overlap ordering, and secret lookalikes; aggregate gate should reference or exercise representative cases. [VERIFIED: tests/test_detection.py] |
| TEST-04 | Tests cover protected path normalization for Windows paths, mixed separators, relative traversal, quoted paths, and project-root-relative paths. [VERIFIED: .planning/REQUIREMENTS.md] | Existing path and command tests cover Windows, relative, quoted, globs, dump patterns, and protected path command classification; add project-root-relative case if not already explicit. [VERIFIED: tests/test_policy.py + tests/test_policy_commands.py] |
| TEST-05 | Tests cover Claude prompt and tool hook JSON payloads, malformed input, exit codes, policy modes, and sanitized output. [VERIFIED: .planning/REQUIREMENTS.md] | Existing Claude tests cover prompt/tool payloads, malformed JSON, exit codes, warn/scrub/block modes, orchestration payloads, and doctor output; aggregate gate should include these surfaces in one auditable v1 test path. [VERIFIED: tests/test_claude_hooks.py + tests/test_claude_doctor.py + tests/test_claude_phase_gate.py] |
| TEST-06 | Tests cover fail-closed behavior when detection, masking, configuration, or client capability validation fails. [VERIFIED: .planning/REQUIREMENTS.md] | Existing masking/policy/Codex tests cover residual detection, empty hits on sensitive text, unverified masks, unknown/external/unsupported surfaces, invalid thresholds, and unsupported Codex masking claims; add explicit exception/failure output hygiene if planner finds no current assertion. [VERIFIED: tests/test_masking.py + tests/test_policy.py + tests/test_claude_hooks.py + tests/test_codex_claim_gate.py] |
</phase_requirements>

## Summary

Phase 5 should be planned as a small pytest-native regression gate over the existing v1 package and adapter surfaces, not as a new runner, CI system, or integration expansion. [VERIFIED: 05-CONTEXT.md] The current suite already has 116 passing tests with one known pytest cache warning on this Windows machine, and the full command `python -m pytest tests -q` completes successfully. [VERIFIED: pytest run]

The strongest local pattern is the Phase 3 aggregate hygiene gate in `tests/test_claude_phase_gate.py`, plus the safe repository scanner in `tests/test_codex_claim_gate.py`. [VERIFIED: codebase inspection] Phase 5 should add `tests/test_v1_regression_gate.py` or a similarly focused file that maps TEST-01..TEST-06 directly in test names, docstrings, constants, or a compact traceability table. [VERIFIED: 05-CONTEXT.md]

**Primary recommendation:** Add a focused `tests/test_v1_regression_gate.py` that reuses package APIs and hook entry points, asserts one shared forbidden-output corpus across CLI/hook/diagnostic/failure surfaces, and leaves existing detailed tests in place. [VERIFIED: 05-CONTEXT.md + tests/test_claude_phase_gate.py]

## Project Constraints (from AGENTS.md)

- Raw sensitive data must stay local and must not be sent to Anthropic, OpenAI, or other external LLM providers. [VERIFIED: AGENTS.md]
- v1 targets terminal/IDE code-agent workflows, especially Claude Code and Codex-style usage. [VERIFIED: AGENTS.md]
- Brazilian sensitive data types are first-class: CPF, CNPJ, bank/account data, names, contact data, credentials, and environment variables. [VERIFIED: AGENTS.md]
- v1 uses masking before submission, not deanonymization after the response. [VERIFIED: AGENTS.md]
- If a client surface cannot be safely rewritten, the tool should block rather than silently allow clear-text submission. [VERIFIED: AGENTS.md]
- Real sensitive datasets and `.env` values must not be read into planning docs, tests, generated examples, or commits. [VERIFIED: AGENTS.md]
- Reuse Python, Microsoft Presidio, spaCy Portuguese models, and lightweight hook scripts unless a phase proves a better boundary is needed. [VERIFIED: AGENTS.md]
- Hook entry points must fail open on malformed JSON input, while blocking violations use exit code `2` and sanitized `stderr`. [VERIFIED: AGENTS.md + privguard/hooks.py]
- New hook/detection tests should use synthetic-only fixtures and must not read `.env` or `data_sensivel/**`. [VERIFIED: AGENTS.md + 05-CONTEXT.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Synthetic fixture policy | Tests | Package modules | The gate owns fixture selection and scan exclusions; package modules only classify synthetic strings supplied by tests. [VERIFIED: 05-CONTEXT.md + tests/test_codex_claim_gate.py] |
| Detection correctness | Package core | Tests | `privguard.detection` owns validators and overlap semantics; tests prove valid/invalid/overlap behavior with synthetic values. [VERIFIED: privguard/detection.py + tests/test_detection.py] |
| Masking and verification | Package core | CLI/tests | `privguard.masking` owns typed placeholder replacement and verification; CLI/tests assert sanitized outputs. [VERIFIED: privguard/masking.py + tests/test_masking.py + tests/test_cli.py] |
| Protected path and command blocking | Package policy | Claude hook adapter | `privguard.policy` classifies paths/commands; `privguard.hooks` maps hook payloads to blocked exit code and sanitized messages. [VERIFIED: privguard/policy.py + privguard/hooks.py] |
| Claude hook behavior | Adapter layer | Tests | `main_user_prompt()` and `main_pre_tool()` are callable hook entry points; tests feed JSON through `sys.stdin` without running Claude. [VERIFIED: privguard/hooks.py + tests/test_claude_hooks.py] |
| Codex support claim gate | Package docs/tests | Policy | `privguard.codex` owns compatibility rows, while tests scan safe docs/source text for unsupported automatic masking claims. [VERIFIED: privguard/codex.py + tests/test_codex_claim_gate.py] |
| Output hygiene | Tests | Diagnostics/CLI/hooks | Tests should assert forbidden synthetic values are absent from stdout, stderr, JSON, diagnostics, masked metadata, and selected failure messages. [VERIFIED: 05-CONTEXT.md + tests/test_cli.py + tests/test_claude_phase_gate.py] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.14.3 | Runtime for package modules, CLI, hooks, and tests. | Existing local interpreter and installed editable package use this runtime. [VERIFIED: `python --version` + `python -m pip show privguard`] |
| pytest | 9.0.2 | Test runner and fixtures for capture, monkeypatching, parametrization, and assertions. | The phase decision locks a pytest-native gate and local version is installed. [VERIFIED: `python -m pytest --version` + 05-CONTEXT.md] |
| privguard | 0.1.0 editable | Package under test: detection, masking, policy, diagnostics, hooks, CLI, Codex matrix. | Installed editable from this workspace and current tests import package modules directly. [VERIFIED: `python -m pip show privguard` + tests/*.py] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `io`, `json`, `sys` | Python 3.14.3 stdlib | Feed synthetic hook JSON through stdin and parse hook/CLI JSON output. | Use for hook and CLI tests; no subprocess or real agent needed. [VERIFIED: tests/test_claude_hooks.py + tests/test_cli.py] |
| Python stdlib `pathlib`, `re` | Python 3.14.3 stdlib | Safe repository scans and forbidden pattern matching. | Use for source/claim scans while excluding protected paths. [VERIFIED: tests/test_codex_claim_gate.py] |
| pytest `capsys` | pytest 9.0.2 fixture | Capture stdout/stderr for hygiene assertions. | Use for CLI and hook output checks. [CITED: https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html] |
| pytest `monkeypatch` | pytest 9.0.2 fixture | Patch stdin and environment variables safely per test. | Use for hook JSON payloads and `PII_GUARD_MODE` / `PII_GUARD_THRESHOLD`. [CITED: https://docs.pytest.org/en/stable/how-to/monkeypatch.html] |
| pytest `@pytest.mark.parametrize` | pytest 9.0.2 feature | Compact coverage over identifiers, paths, commands, and modes. | Use for matrix-like synthetic cases without hand-built loops that hide failure IDs. [CITED: https://docs.pytest.org/en/stable/how-to/parametrize.html] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest-native gate | Custom runner script | Rejected by locked decision D-01 and would duplicate pytest capture/fixtures. [VERIFIED: 05-CONTEXT.md] |
| Direct package/hook function calls | Real Claude/Codex execution | Rejected by runtime boundary D-13; real agents are unnecessary and would make the gate environment-dependent. [VERIFIED: 05-CONTEXT.md] |
| Inline synthetic constants | Shared fixture module | Allowed only if it reduces duplication without hiding checked values; start inline for auditability. [VERIFIED: 05-CONTEXT.md] |
| `pytest-cov` coverage gate | Coverage tooling | Deferred because real coverage tooling and CI configuration are out of scope. [VERIFIED: 05-CONTEXT.md] |

**Installation:**

```bash
python -m pip install -e .
python -m pytest tests -q
```

Version verification performed with:

```bash
python --version
python -m pytest --version
python -m pip show pytest privguard presidio-analyzer presidio-anonymizer spacy
```

Observed versions: Python 3.14.3, pytest 9.0.2, privguard 0.1.0 editable, presidio-analyzer 2.2.359, presidio-anonymizer 2.2.362, spaCy 3.8.13. [VERIFIED: local commands]

## Architecture Patterns

### System Architecture Diagram

```text
Synthetic inline fixtures
  |
  v
pytest test functions
  |
  +--> privguard.detection.detect/analyze_text
  |       -> Hit metadata only -> diagnostics assertions
  |
  +--> privguard.masking.mask_text/verify_mask
  |       -> typed placeholders + verification -> forbidden-value assertions
  |
  +--> privguard.policy.classify_path/classify_command/decide_policy
  |       -> allow/block/pause decision -> fail-closed assertions
  |
  +--> privguard.cli.main(argv)
  |       -> stdout/stderr/JSON -> capsys + json.loads hygiene assertions
  |
  +--> privguard.hooks.main_user_prompt/main_pre_tool
  |       -> stdin JSON + env vars -> exit code + stdout/stderr/JSON hygiene assertions
  |
  +--> safe repo text scanner
          -> docs/source/test text excluding protected paths
          -> Codex claim and synthetic-only policy assertions
```

This data flow keeps all test input local, synthetic, and in process; no network, real Claude, real Codex, Ollama, Presidio model download, `.env`, or `data_sensivel/**` content is required. [VERIFIED: 05-CONTEXT.md + tests/*.py]

### Recommended Project Structure

```text
tests/
├── test_v1_regression_gate.py      # New Phase 5 aggregate TEST-01..TEST-06 gate
├── test_detection.py               # Existing detailed DET/TEST-03 coverage
├── test_masking.py                 # Existing masking, verification, diagnostics coverage
├── test_policy.py                  # Existing path and surface policy coverage
├── test_policy_commands.py         # Existing shell command protected-path coverage
├── test_cli.py                     # Existing CLI stdout/JSON coverage
├── test_claude_hooks.py            # Existing Claude hook payload/mode coverage
├── test_claude_doctor.py           # Existing safe doctor coverage
├── test_claude_phase_gate.py       # Existing Phase 3 aggregate hygiene pattern
├── test_codex_compatibility.py     # Existing Codex matrix coverage
└── test_codex_claim_gate.py        # Existing safe repo claim scanner pattern
```

The planner should add one focused file and only touch existing tests where a concrete TEST-01..TEST-06 gap is found. [VERIFIED: 05-CONTEXT.md]

### Pattern 1: Shared Forbidden Corpus Per Surface

**What:** Define synthetic raw values, raw prefixes, prompt snippets, command snippets, protected path strings, and unsafe redaction markers once per gate file, then assert they are absent from every rendered output surface. [VERIFIED: tests/test_claude_phase_gate.py]

**When to use:** Use for TEST-02 across CLI stdout/stderr, CLI JSON, hook stdout/stderr, hook JSON/additionalContext, diagnostics, masked metadata, and failure messages. [VERIFIED: 05-CONTEXT.md]

**Example:**

```python
FORBIDDEN_OUTPUT = (
    RAW_CPF,
    FAKE_SECRET,
    PROTECTED_DATA_PATH,
    PROMPT_SNIPPET,
    COMMAND_TEXT,
    "sk-test-",
    "redacted=",
)

def assert_forbidden_absent(rendered: str) -> None:
    for value in FORBIDDEN_OUTPUT:
        assert value not in rendered
```

Source: `tests/test_claude_phase_gate.py` [VERIFIED: codebase inspection]

### Pattern 2: In-Process Hook Invocation

**What:** Feed JSON into `sys.stdin` with `io.StringIO`, set or delete hook environment variables with `monkeypatch`, and call `main_user_prompt()` / `main_pre_tool()` directly. [VERIFIED: tests/test_claude_hooks.py]

**When to use:** Use for TEST-05 and fail-closed hook behavior; avoid launching Claude or shelling out. [VERIFIED: 05-CONTEXT.md]

**Example:**

```python
def run_user_prompt(monkeypatch, payload, mode=None):
    if mode is None:
        monkeypatch.delenv("PII_GUARD_MODE", raising=False)
    else:
        monkeypatch.setenv("PII_GUARD_MODE", mode)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    return main_user_prompt()
```

Source: `tests/test_claude_hooks.py`; pytest monkeypatch docs confirm env/attribute changes are undone after the test. [VERIFIED: codebase inspection] [CITED: https://docs.pytest.org/en/stable/how-to/monkeypatch.html]

### Pattern 3: Safe Repository Scanner

**What:** Scan only explicit safe globs and exclude `.git`, `.planning`, `.env*`, `data_sensivel`, caches, bytecode, and test files that contain claim fixture strings. [VERIFIED: tests/test_codex_claim_gate.py]

**When to use:** Use for TEST-01 synthetic-only checks and TEST-02/TEST-06 claim text hygiene; never recursively scan arbitrary workspace paths. [VERIFIED: 05-CONTEXT.md]

**Example:**

```python
_EXCLUDED_PARTS = frozenset({
    ".git",
    ".planning",
    "data_sensivel",
    "__pycache__",
    ".pytest_cache",
})

def _is_excluded(path: pathlib.Path) -> bool:
    return any(part in _EXCLUDED_PARTS for part in path.parts)
```

Source: `tests/test_codex_claim_gate.py` [VERIFIED: codebase inspection]

### Anti-Patterns to Avoid

- **Reading protected files to prove they are protected:** TEST-01 requires synthetic-only tests and project instructions forbid reading `.env` or `data_sensivel/**`. [VERIFIED: AGENTS.md + 05-CONTEXT.md]
- **Shelling out to real Claude/Codex/Ollama:** Phase 5 must not depend on real agent execution, local Ollama, network access, or model downloads. [VERIFIED: 05-CONTEXT.md]
- **Asserting exact full human messages:** Prefer reason codes, actions, counts, kinds, and absence of forbidden values; exact messages are brittle and can encourage echoing raw text. [VERIFIED: 05-CONTEXT.md + privguard/hooks.py]
- **Putting synthetic forbidden values in pytest parameter IDs:** pytest failure output can include parameter values, so prefer neutral IDs or test-local constants when the value itself is forbidden output. [CITED: https://docs.pytest.org/en/stable/how-to/parametrize.html]
- **Repository scanning with `Path.rglob("*")` over the whole workspace:** The workspace contains denied cache/temp paths and protected data directories, so scans must use allowlisted globs and exclusions. [VERIFIED: `rg --files` warnings + tests/test_codex_claim_gate.py]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test execution | Custom Python runner | `python -m pytest tests -q` | Locked by D-01 and pytest already handles collection, fixtures, capture, and exit status. [VERIFIED: 05-CONTEXT.md] [CITED: https://docs.pytest.org/en/stable/how-to/usage.html] |
| stdout/stderr capture | Manual `sys.stdout` / `sys.stderr` redirection | pytest `capsys` / `capfd` | pytest fixtures provide per-test capture and restore streams after each test. [CITED: https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html] |
| env/stdin patching | Global setup/teardown code | pytest `monkeypatch` + `io.StringIO` | Existing tests use this pattern and pytest restores patched state after tests. [VERIFIED: tests/test_claude_hooks.py] [CITED: https://docs.pytest.org/en/stable/how-to/monkeypatch.html] |
| PII validation | New CPF/CNPJ/CNH checksum logic in tests | `privguard.detection` validators and existing synthetic fixtures | Package validators are the implementation contract; duplicating algorithms in tests creates drift. [VERIFIED: privguard/detection.py + tests/test_detection.py] |
| Mask verification | String replacement assertions only | `mask_text()` + `verify_mask()` + forbidden-value assertions | `verify_mask()` detects original-value residuals and residual detections; string checks alone miss failure modes. [VERIFIED: privguard/masking.py + tests/test_masking.py] |
| Safe diagnostics | Ad hoc dict serialization | `privguard.diagnostics.to_dict()` / `to_json()` / `format_text()` | Existing serializers intentionally omit `Hit.value` and `MaskResult.text`. [VERIFIED: privguard/diagnostics.py + tests/test_masking.py] |
| Protected path parsing | File existence checks or reads | `classify_path()` / `classify_command()` | Policy classification works on strings and avoids file I/O. [VERIFIED: privguard/policy.py + tests/test_policy.py] |

**Key insight:** The gate should prove the existing privacy contract from the package boundary outward; rebuilding detection, masking, path parsing, or runners inside tests would create a second untrusted implementation. [VERIFIED: codebase inspection]

## Common Pitfalls

### Pitfall 1: Output Assertions Miss Failure Paths

**What goes wrong:** Tests prove successful masking is sanitized but forget unverified masks, invalid thresholds, malformed payloads, unsupported surfaces, or exception messages. [VERIFIED: 05-CONTEXT.md]
**Why it happens:** Success-path output is easier to capture than paths returning `2`, raising `ValueError`, or emitting sanitized stderr. [VERIFIED: tests/test_masking.py + tests/test_claude_hooks.py]
**How to avoid:** Include failure-path cases for `verify_mask()`, `redact()` failure, invalid `PII_GUARD_THRESHOLD`, unknown/external/unsupported policy, and unsupported Codex automatic masking claims. [VERIFIED: tests/test_masking.py + tests/test_policy.py + tests/test_codex_claim_gate.py]
**Warning signs:** TEST-02 checks only `main(["mask", ...]) == 0` and never inspects stderr or exception text. [VERIFIED: tests/test_cli.py]

### Pitfall 2: Synthetic Fixture Values Leak Through Pytest Failure Reports

**What goes wrong:** Parameter values, assertion messages, or failure summaries can display forbidden synthetic raw values even when application output is clean. [CITED: https://docs.pytest.org/en/stable/how-to/parametrize.html]
**Why it happens:** pytest reports parameter values and assertion introspection on failures. [CITED: https://docs.pytest.org/en/stable/how-to/parametrize.html]
**How to avoid:** Use neutral parameter IDs for forbidden values, avoid custom failure messages that include raw fixture text, and keep failure messages to sanitized labels/pattern names. [VERIFIED: tests/test_codex_claim_gate.py]
**Warning signs:** `pytest.mark.parametrize` uses raw CPF/path strings directly with no `ids=` where the failure output itself is part of the privacy surface. [ASSUMED]

### Pitfall 3: Safe Scans Accidentally Touch Protected or Denied Paths

**What goes wrong:** A repo-wide scan enters `.env`, `data_sensivel/**`, `.planning`, `.git`, pytest cache temp directories, or permission-denied temp paths. [VERIFIED: AGENTS.md + `rg --files` warnings]
**Why it happens:** Broad filesystem traversal is convenient but violates the phase boundary and can also fail on Windows denied directories. [VERIFIED: `rg --files` warnings]
**How to avoid:** Use explicit allowlisted globs for `docs/**/*.md`, `privguard/**/*.py`, `tests/**/*.py`, `pyproject.toml`, and `AGENTS.md`, then exclude known protected/cached paths. [VERIFIED: tests/test_codex_claim_gate.py]
**Warning signs:** Use of `Path(".").rglob("*")` without `_is_excluded()`-style filtering. [VERIFIED: tests/test_codex_claim_gate.py]

### Pitfall 4: Aggregate Gate Becomes a Duplicate Suite

**What goes wrong:** The new Phase 5 file reimplements every detailed test and becomes harder to maintain than the underlying suite. [VERIFIED: 05-CONTEXT.md]
**Why it happens:** Traceability pressure can lead to broad rewrites instead of representative cross-surface assertions. [VERIFIED: 05-CONTEXT.md]
**How to avoid:** Keep detailed coverage in existing files; the new gate should sample each requirement and document which existing files provide depth. [VERIFIED: 05-CONTEXT.md + tests/*.py]
**Warning signs:** Large refactors to existing tests without a direct TEST-01..TEST-06 gap. [VERIFIED: 05-CONTEXT.md]

### Pitfall 5: Allowing Masked Payload Echo in JSON Diagnostics

**What goes wrong:** Human masking output may safely contain `<BR_CPF>`, but JSON diagnostics and hook additionalContext should not echo masked prompt payloads or `redacted=` style strings. [VERIFIED: 05-CONTEXT.md + tests/test_masking.py]
**Why it happens:** Developers may treat placeholders as universally safe, while the phase decision distinguishes allowed metadata from payload echo. [VERIFIED: 05-CONTEXT.md]
**How to avoid:** Assert raw values and placeholders are absent from JSON diagnostics where payload text is not needed; allow placeholders only in explicitly safe human masked payload output. [VERIFIED: tests/test_cli.py + tests/test_masking.py]
**Warning signs:** `"<BR_CPF>" in rendered_json` or `redacted=` in hook output. [VERIFIED: 05-CONTEXT.md]

## Code Examples

### Gate Skeleton With Requirement Traceability

```python
"""V1 synthetic regression gate.

Requirements covered:
- TEST-01: synthetic-only fixture and safe scanner policy
- TEST-02: forbidden output corpus across v1 surfaces
- TEST-03: identifier validity/overlap representative cases
- TEST-04: protected path normalization representative cases
- TEST-05: Claude hook JSON/mode/malformed representative cases
- TEST-06: fail-closed masking/policy/Codex representative cases
"""
```

Source: Phase 5 context requires direct TEST-01..TEST-06 mapping. [VERIFIED: 05-CONTEXT.md]

### Capturing CLI Output

```python
def test_cli_json_is_sanitized(capsys):
    raw_cpf = "123.456.789-09"
    assert main(["scan", "--json", f"CPF {raw_cpf}"]) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["counts"]["BR_CPF"] == 1
    assert raw_cpf not in captured.out
    assert captured.err == ""
```

Source: `tests/test_cli.py`; pytest `capsys` exposes `out` and `err` via `readouterr()`. [VERIFIED: codebase inspection] [CITED: https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html]

### Capturing Hook JSON Additional Context

```python
def test_warn_mode_additional_context_is_sanitized(monkeypatch, capsys):
    monkeypatch.setenv("PII_GUARD_MODE", "warn")
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"prompt": PROMPT_TEXT})))

    assert main_user_prompt() == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert "BR_CPF" in captured.out
    assert RAW_CPF not in captured.out + captured.err
```

Source: `privguard/hooks.py` and `tests/test_claude_hooks.py` [VERIFIED: codebase inspection]

### Fail-Closed Masking Failure

```python
def test_unverified_mask_is_never_allowed():
    raw_text = "CPF 123.456.789-09"
    hits = detect(raw_text)
    result = mask_text(raw_text, hits=hits)
    failed = type(result)(
        text=raw_text,
        changed=False,
        verified=False,
        verification_status="failed",
        reason_codes=("original_value_remaining",),
        hits=tuple(hits),
    )

    decision = decide_policy(SurfaceCapability.REWRITE_CAPABLE, hits=hits, mask_result=failed)
    assert decision.allow is False
    assert "mask_unverified" in decision.reason_codes
```

Source: `tests/test_policy.py` [VERIFIED: codebase inspection]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Root demo scripts as behavior proof | Importable `privguard` package with pytest tests | Phase 1 completed before Phase 5 [VERIFIED: ROADMAP.md + pyproject.toml] | Phase 5 should test package APIs and adapters, not demos. [VERIFIED: tests/*.py] |
| Presidio/spaCy dependency for hook/runtime tests | Stdlib lightweight detection in `privguard.detection` and hook entry points | Phase 2 package core [VERIFIED: privguard/detection.py + AGENTS.md] | Gate can run without Presidio model downloads. [VERIFIED: 05-CONTEXT.md] |
| Claude-only hygiene gate | v1 cross-surface gate including CLI, package core, Claude, Codex docs/matrix | Phase 5 goal [VERIFIED: ROADMAP.md] | Aggregate test should extend the Phase 3 pattern across all v1 surfaces. [VERIFIED: tests/test_claude_phase_gate.py] |
| Positive Codex masking claims | Conservative unsupported/block-only labels until outbound replacement is proven | Phase 4 artifacts [VERIFIED: privguard/codex.py + docs/codex-compatibility.md] | Phase 5 must preserve the no-unsupported-claim gate. [VERIFIED: tests/test_codex_claim_gate.py] |

**Deprecated/outdated:**
- A custom regression runner is out of scope because D-01 locks pytest-native execution. [VERIFIED: 05-CONTEXT.md]
- Real sensitive fixtures are prohibited by project constraints and TEST-01. [VERIFIED: AGENTS.md + REQUIREMENTS.md]
- Real Claude/Codex/Ollama execution is out of scope for Phase 5. [VERIFIED: 05-CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Use neutral pytest parameter IDs for forbidden raw fixture values when failure output itself is considered a privacy surface. [ASSUMED] | Common Pitfalls | If over-applied, tests become slightly less self-documenting; if under-applied, a failing test may display synthetic raw values in pytest failure output. |

## Open Questions (RESOLVED)

1. **Should the planner add explicit sanitized exception-message tests for `redact()` failure?** [VERIFIED: tests/test_masking.py]
   - What we know: `redact()` raises `ValueError("mask verification failed")` when verification fails, and current tests cover `verify_mask()` failures. [VERIFIED: privguard/masking.py + tests/test_masking.py]
  - What's unclear: Existing tests do not appear to assert exception-message hygiene for `redact()` specifically. [VERIFIED: codebase inspection]
  - Recommendation: Add one small TEST-02/TEST-06 case using `pytest.raises(ValueError)` and assert the message contains no raw synthetic value. [VERIFIED: 05-CONTEXT.md]
  - RESOLVED: `05-01-PLAN.md` incorporates this as explicit failure/exception hygiene coverage in the v1 synthetic regression gate.

2. **Does TEST-04 require an explicit project-root-relative protected path case beyond current Windows/relative/quoted coverage?** [VERIFIED: .planning/REQUIREMENTS.md]
   - What we know: Current tests cover `.env`, `.env.local`, `data_sensivel\synthetic.csv`, `../cooperados/lista.csv`, quoted Windows traversal, dumps, and sensitive globs. [VERIFIED: tests/test_policy.py + tests/test_policy_commands.py]
  - What's unclear: The exact string "project-root-relative" is not represented as a named test case. [VERIFIED: codebase inspection]
  - Recommendation: Add an explicit case such as `./data_sensivel/synthetic.csv` or `privguard/../data_sensivel/synthetic.csv` if the planner wants unambiguous TEST-04 traceability. [VERIFIED: REQUIREMENTS.md]
  - RESOLVED: `05-01-PLAN.md` includes explicit TEST-04 traceability for project-root-relative protected path normalization.

3. **Should TEST-01 scan product docs for real-looking fixture policy violations, or only tests?** [VERIFIED: 05-CONTEXT.md]
   - What we know: Phase 5 must prevent raw sensitive values in tests, generated examples, commits, outputs, and docs/claim text surfaces already scanned by Codex gates. [VERIFIED: AGENTS.md + 05-CONTEXT.md]
  - What's unclear: A strict docs scan can flag allowed synthetic fixtures in planning docs if `.planning` is included, so it must be scoped carefully. [VERIFIED: tests/test_codex_claim_gate.py]
  - Recommendation: Scan `tests/`, `privguard/`, `docs/`, `pyproject.toml`, and `AGENTS.md` with explicit exclusions; do not scan `.planning`, `.env*`, `data_sensivel`, or caches. [VERIFIED: tests/test_codex_claim_gate.py]
  - RESOLVED: `05-01-PLAN.md` scopes TEST-01 source scanning to safe repository surfaces and excludes `.planning`, `.env*`, `data_sensivel`, caches, and bytecode.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Running package and tests | yes | 3.14.3 | None needed. [VERIFIED: `python --version`] |
| pytest | Phase 5 regression gate | yes | 9.0.2 | None; D-01 locks pytest-native gate. [VERIFIED: `python -m pytest --version` + 05-CONTEXT.md] |
| privguard editable package | Importable package tests | yes | 0.1.0 editable from workspace | Reinstall editable with `python -m pip install -e .` if imports fail. [VERIFIED: `python -m pip show privguard`] |
| Presidio/spaCy | Optional full extras and demos | installed but not required for Phase 5 gate | presidio-analyzer 2.2.359, presidio-anonymizer 2.2.362, spaCy 3.8.13 | Do not require model downloads in Phase 5. [VERIFIED: `python -m pip show ...` + 05-CONTEXT.md] |
| Network access | Not required | not needed | — | Keep tests local and synthetic. [VERIFIED: 05-CONTEXT.md] |
| Real Claude/Codex/Ollama | Not required | not needed | — | Call package hook functions directly. [VERIFIED: 05-CONTEXT.md + tests/test_claude_hooks.py] |

**Missing dependencies with no fallback:**
- None for the researched Phase 5 approach. [VERIFIED: pytest run]

**Missing dependencies with fallback:**
- None required; optional Presidio/spaCy/Ollama dependencies must not become phase gate requirements. [VERIFIED: 05-CONTEXT.md]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No authentication surface exists in Phase 5 tests. [VERIFIED: codebase inspection] |
| V3 Session Management | no | No session management surface exists in this package. [VERIFIED: codebase inspection] |
| V4 Access Control | yes | Block protected path access and unsupported/unknown external surfaces before content leaves local boundary. [VERIFIED: privguard/policy.py + privguard/hooks.py] |
| V5 Input Validation / File Handling | yes | Validate/sanitize path strings with `classify_path()` and command strings with `classify_command()`; ASVS file handling guidance includes strict validation/sanitization for user-submitted path data. [VERIFIED: privguard/policy.py] [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/05-file-handling/03-file-storage] |
| V6 Cryptography | no for Phase 5 gate | v1 gate tests irreversible masking only and does not add cryptographic key handling. [VERIFIED: 05-CONTEXT.md] |
| V14 Data Protection | yes | Assert raw synthetic sensitive values do not appear in outputs, diagnostics, logs, hooks, masks, or failures. [VERIFIED: REQUIREMENTS.md + 05-CONTEXT.md] |
| V16 Security Logging and Error Handling | yes | Sanitized diagnostics and failure output should avoid sensitive data; ASVS logging/error handling guidance includes avoiding sensitive data in logs and generic handling for security-sensitive errors. [VERIFIED: privguard/diagnostics.py] [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/16-security-logging-and-error-handling/02-general-logging] [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/16-security-logging-and-error-handling/05-error-handling] |

### Known Threat Patterns for privguard pytest gate

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Synthetic raw PII echoed in stdout/stderr/JSON | Information Disclosure | Shared forbidden-output assertions with `capsys`, JSON parsing, and diagnostics serialization checks. [VERIFIED: tests/test_cli.py + tests/test_claude_phase_gate.py] |
| Protected file path read during tests | Information Disclosure | Safe scanner allowlists and path-string classification only; no `.env` or `data_sensivel/**` reads. [VERIFIED: AGENTS.md + tests/test_codex_claim_gate.py] |
| Unsupported client surface allowed by default | Information Disclosure | `decide_policy()` fails closed for unknown/external/unsupported surfaces unless verified masked payload is proven. [VERIFIED: privguard/policy.py + tests/test_policy.py] |
| Unverified mask treated as safe | Tampering / Information Disclosure | `verify_mask()` residual checks and policy `mask_unverified` pause behavior. [VERIFIED: privguard/masking.py + privguard/policy.py] |
| Unsupported Codex masking claim creates false assurance | Spoofing / Information Disclosure | Codex matrix and claim scanner require verified outbound payload replacement before positive automatic masking claims. [VERIFIED: privguard/codex.py + tests/test_codex_claim_gate.py] |

## Sources

### Primary (HIGH confidence)

- `.planning/phases/05-synthetic-regression-gate/05-CONTEXT.md` - locked Phase 5 decisions, runtime boundaries, coverage priorities, and deferred scope. [VERIFIED: file read]
- `.planning/REQUIREMENTS.md` - TEST-01 through TEST-06 acceptance criteria. [VERIFIED: file read]
- `.planning/ROADMAP.md` - Phase 5 goal, dependency, and success criteria. [VERIFIED: file read]
- `.planning/STATE.md` - prior decisions and current phase state. [VERIFIED: file read]
- `AGENTS.md` - privacy, synthetic-only, fail-closed, and project workflow constraints. [VERIFIED: file read]
- `privguard/*.py` and `tests/*.py` - implementation and existing test patterns. [VERIFIED: codebase inspection]
- Local commands: `python --version`, `python -m pytest --version`, `python -m pip show ...`, `python -m pytest tests -q`. [VERIFIED: command output]
- pytest official docs: capture stdout/stderr, monkeypatch, parametrization, invocation. [CITED: https://docs.pytest.org/en/stable/how-to/capture-stdout-stderr.html] [CITED: https://docs.pytest.org/en/stable/how-to/monkeypatch.html] [CITED: https://docs.pytest.org/en/stable/how-to/parametrize.html] [CITED: https://docs.pytest.org/en/stable/how-to/usage.html]
- OWASP ASVS 5.0 taxonomy pages for file handling and logging/error handling. [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/05-file-handling/03-file-storage] [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/16-security-logging-and-error-handling/02-general-logging] [CITED: https://cornucopia.owasp.org/taxonomy/asvs-5.0/16-security-logging-and-error-handling/05-error-handling]

### Secondary (MEDIUM confidence)

- None used. [VERIFIED: research log]

### Tertiary (LOW confidence)

- Assumption A1 about neutral pytest parameter IDs for forbidden raw fixture values. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions verified locally and phase locks pytest. [VERIFIED: local commands + 05-CONTEXT.md]
- Architecture: HIGH - implementation and tests were inspected directly. [VERIFIED: codebase inspection]
- Pitfalls: HIGH for existing surfaces, MEDIUM for pytest failure-output parameter ID risk because it is derived from pytest behavior and privacy policy rather than an existing failing case. [VERIFIED: codebase inspection] [ASSUMED]

**Research date:** 2026-05-04 [VERIFIED: system date]
**Valid until:** 2026-06-03 for local project architecture; re-check pytest version and Phase 4 status before planning if dependencies or Codex docs changed. [ASSUMED]
