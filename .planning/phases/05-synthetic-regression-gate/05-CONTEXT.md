# Phase 5: Synthetic Regression Gate - Context

**Gathered:** 2026-05-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 delivers the v1 synthetic regression gate. It should prove, with automated tests, that the
package and supported adapters do not leak raw synthetic sensitive values through detection,
masking, policy decisions, CLI output, Claude hooks, Codex compatibility claims, failures, or
diagnostics.

The phase does not add new integrations, does not weaken Phase 4 Codex labels, does not introduce
real sensitive fixtures, and does not require reading `.env` or `data_sensivel/**`. It consolidates
and closes test coverage around the v1 surfaces already built in Phases 1-4.

Phase 5 depends on Phase 4 artifacts being verified before final execution. If Phase 4 verification
is still pending, planners should treat `docs/codex-compatibility.md`, `privguard/codex.py`, and
Codex claim-gate tests as expected upstream inputs and confirm their status before execution.

</domain>

<decisions>
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/REQUIREMENTS.md` - TEST-01 through TEST-06 define Phase 5 acceptance criteria.
- `.planning/ROADMAP.md` - Phase 5 goal, dependency on Phase 4, and success criteria.
- `.planning/PROJECT.md` - Core value, synthetic-only constraint, fail-closed default, and v1
  terminal/IDE-agent scope.
- `.planning/STATE.md` - Current phase progress and whether Phase 4 has been verified.

### Prior phase decisions
- `.planning/phases/02-privacy-core/02-CONTEXT.md` - Detection, masking, policy, diagnostics, and
  fail-closed decisions that the v1 gate must preserve.
- `.planning/phases/03-claude-enforcement/03-CONTEXT.md` - Claude hook behavior, output hygiene,
  malformed JSON behavior, and synthetic doctor validation requirements.
- `.planning/phases/04-codex-compatibility-evidence/04-CONTEXT.md` - Codex evidence standard,
  conservative labels, and no automatic masking claim without proof.

### Existing implementation
- `privguard/detection.py` - Brazil-first detection and validators.
- `privguard/masking.py` - Irreversible masking and verification behavior.
- `privguard/policy.py` - Protected path classification, command classification, and fail-closed
  policy decisions.
- `privguard/diagnostics.py` - Sanitized diagnostic serialization.
- `privguard/hooks.py` - Claude hook behavior used by tests without running Claude.
- `privguard/cli.py` - CLI commands and output behavior.
- `privguard/codex.py` - Codex compatibility matrix and support labels from Phase 4.
- `.claude/settings.json` - Claude hook wiring and deny rules, path only.
- `docs/codex-compatibility.md` - Human-readable Codex compatibility assessment from Phase 4.

### Existing tests to preserve and extend
- `tests/test_detection.py` - Brazilian identifiers, secrets, overlap, validator parity.
- `tests/test_masking.py` - Masking verification and sanitized diagnostics.
- `tests/test_policy.py` - Surface capability decisions and protected path policy.
- `tests/test_policy_commands.py` - Protected command classification.
- `tests/test_cli.py` - CLI scan/mask/policy-check output hygiene.
- `tests/test_claude_hooks.py` - Prompt/tool hook payloads, malformed JSON, exit codes, policy
  modes, sanitized output, orchestration payload PII.
- `tests/test_claude_doctor.py` - Safe Claude validation diagnostics.
- `tests/test_claude_phase_gate.py` - Existing cross-surface Claude output hygiene gate.
- `tests/test_codex_compatibility.py` - Codex matrix and conservative policy behavior.
- `tests/test_codex_claim_gate.py` - CDX-03 unsupported automatic masking claim prevention.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Existing tests already cover most of TEST-03, TEST-04, TEST-05, and pieces of TEST-01/TEST-02.
- `tests/test_claude_phase_gate.py` is the closest pattern for a phase-level aggregate hygiene
  gate.
- `tests/test_codex_claim_gate.py` is the closest pattern for repository text scanning while
  avoiding protected paths.
- `privguard.diagnostics.to_dict()` and `to_json()` are the right serialization boundaries for
  checking sanitized structured output.

### Established Patterns
- Tests invoke package functions directly and monkeypatch `sys.stdin`, environment variables, and
  CLI arguments; no external agent process is needed.
- Tests assert output absence by checking forbidden synthetic values are not present in captured
  stdout/stderr or serialized JSON.
- Path protection is validated through strings and classifiers, not file reads.

### Integration Points
- New Phase 5 tests should live under `tests/` and run under `python -m pytest tests -q`.
- Any repository scanner must exclude `.git`, `.planning`, `.env*`, `data_sensivel`, caches, and
  generated bytecode.
- If a helper module is introduced under `tests/`, claim scanners should avoid treating helper
  fixture strings as product claims.

</code_context>

<specifics>
## Specific Ideas

- The fallback discussion choice was the recommended full coverage path because interactive
  question selection was unavailable in this runtime.
- Phase 5 should be conservative and audit-oriented: make gaps visible rather than adding clever
  test infrastructure.
- The test suite should remain fast and local; current verification commands have been running in
  well under a second for the package tests.

</specifics>

<deferred>
## Deferred Ideas

- Real coverage tooling, CI configuration, signed releases, SBOMs, enterprise telemetry, local proxy
  mode, LangChain/LlamaIndex adapters, and additional IDE agents remain outside Phase 5 unless a
  later roadmap update promotes them.
- Phase 4 final verification and roadmap closure should be completed before executing Phase 5 if it
  remains pending.

</deferred>

---

*Phase: 05-synthetic-regression-gate*
*Context gathered: 2026-05-04*
