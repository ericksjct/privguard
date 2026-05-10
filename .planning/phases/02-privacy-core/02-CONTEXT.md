# Phase 2: Privacy Core - Context

**Gathered:** 2026-05-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers the shared privacy core used by CLI commands and supported client integrations:
Brazil-first sensitive-data detection, irreversible masking, protected-path classification,
fail-closed policy decisions, and sanitized diagnostics.

The phase does not implement Claude-specific enforcement details or Codex support claims. Those are
Phase 3 and Phase 4. Phase 2 defines the core contract they must use.

</domain>

<decisions>
## Implementation Decisions

### Detection Contract
- **D-01:** The product should expose one complete detection experience, not user-facing "light"
  and "full" operating modes. The user wants comprehensive v1 coverage by default.
- **D-02:** Phase 2 should cover Brazilian identifiers, contact data, secret-like values, and
  protected path strings from the v1 requirements: CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS,
  RG-like values, phone numbers, CEP, vehicle plates, API keys, tokens, passwords, database URLs,
  environment variable assignments, `.env`, `data_sensivel/**`, dumps, credential-like files, and
  secret-like filenames.
- **D-03:** Internal implementation may still use multiple detector components when useful, such
  as lightweight regex validators and optional Presidio-backed recognizers, but this must not force
  the user to choose detection modes for normal v1 operation.

### Masking Guarantees
- **D-04:** Masking is irreversible for v1. The system replaces sensitive values with typed
  placeholders and does not require or persist deanonymization maps.
- **D-05:** After masking, the core must verify that original sensitive substrings or suspicious
  leftovers are not still present in the masked output.
- **D-06:** If incomplete masking is detected, the system must pause instead of allowing automatic
  continuation. The user should be told that masking may be incomplete and given a safe decision
  point: continue manually, retry masking, or block.
- **D-07:** For external-provider workflows, the safe default remains fail-closed. Manual override
  can exist as an explicit decision, but the system must not silently allow clear text or partially
  masked content onward.

### Policy Surface Model
- **D-08:** Unknown, unclassified, or external-provider surfaces are treated as unsafe by default.
  If the guard cannot prove that the payload was masked before leaving the local boundary, it
  blocks by default.
- **D-09:** Phase 2 should define capability labels that downstream integrations can use:
  rewrite-capable, block-only, observe-only, unsupported, unknown, and external.
- **D-10:** Rewrite-capable surfaces may allow masked content onward only after verification.
  Block-only surfaces must block when sensitive data is found. Observe-only surfaces and unsupported
  clients must not be represented as automatic protection.

### Diagnostics Shape
- **D-11:** Diagnostics should support both human-readable text and structured JSON.
- **D-12:** The default CLI output can be human-readable. JSON should be configurable for tools,
  tests, hooks, and future integrations.
- **D-13:** All diagnostic formats must be sanitized. They may include entity type, counts, offsets,
  confidence scores, reason codes, policy decision, and surface capability. They must not include
  raw matched values, original prompt snippets, protected file contents, secret-looking strings, or
  unmasked sensitive paths beyond safe reason categories.

### the agent's Discretion
- The planner may decide the exact Python API shape for detector results, masking verification
  results, policy decisions, and diagnostic serializers.
- The planner may decide whether Presidio-backed detection is implemented in this phase or exposed
  behind an internal adapter, as long as the user-facing behavior remains one complete detection
  contract.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/REQUIREMENTS.md` - DET-01 through DET-06, MASK-01 through MASK-04, and POL-01
  through POL-04 define the acceptance criteria for this phase.
- `.planning/ROADMAP.md` - Phase 2 goal, requirements mapping, and success criteria.
- `.planning/PROJECT.md` - Core value, v1 constraints, and privacy boundary.
- `.planning/STATE.md` - Recent decisions from Phase 1 and current blockers.

### Prior phase decisions
- `.planning/phases/01-package-foundation/01-CONTEXT.md` - Locks package identity, flat
  `privguard/` module layout, lightweight default package direction, hook adapter expectations,
  and demo separation.

### Existing package code
- `privguard/detection.py` - Current lightweight `Hit`, validators, pattern list, and overlap
  handling.
- `privguard/masking.py` - Current irreversible placeholder redaction helper.
- `privguard/policy.py` - Current protected-path patterns and sanitized hit summary helpers.
- `privguard/hooks.py` - Current package-backed Claude hook handlers using detection, masking,
  and policy helpers.
- `privguard/cli.py` - Current CLI entry point.

### Demo/reference implementations
- `demos/test_presidio_br.py` - Brazilian Presidio recognizers and checksum validators from the
  pre-package demo layer. Use as reference only; do not restore raw-output demo behavior.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `privguard.detection.Hit`, `detect()`, `valida_cpf()`, `valida_cnpj()`, and `valida_luhn()`:
  current lightweight detector foundation.
- `privguard.masking.redact()`: current irreversible typed-placeholder masking behavior.
- `privguard.policy.is_sensitive_path()`, `summarize_hits()`, and `format_hit_summary()`:
  current policy and diagnostic helpers.
- `privguard.hooks`: current adapter layer proving the package modules can back hook behavior.

### Established Patterns
- The package uses a flat `privguard/` module layout from Phase 1.
- Hook runtime should remain dependency-light and fast.
- Diagnostics should summarize kind, offsets, and scores instead of exposing `Hit.value`.
- Sensitive files such as `.env` and `data_sensivel/**` must be handled by path classification
  only; do not read their contents.

### Integration Points
- CLI behavior currently starts at `privguard.cli:main`.
- Claude hook files under `hooks/` should remain thin adapters over package code.
- Phase 3 will consume the Phase 2 core for Claude-specific blocking behavior.
- Phase 4 will consume the Phase 2 policy labels when documenting Codex compatibility.

</code_context>

<specifics>
## Specific Ideas

- The user is non-specialist and wants one comprehensive privacy behavior, not multiple detector
  modes to choose from.
- If masking looks incomplete, the user wants a warning and a choice: continue manually, retry
  masking, or block.
- For unknown or unproven surfaces, the confirmed rule is block by default.
- Human-readable and JSON diagnostics are both desired, with config deciding which format to use.

</specifics>

<deferred>
## Deferred Ideas

- Claude-specific enforcement details belong to Phase 3.
- Codex interception evidence and support labels belong to Phase 4.
- Additional IDE-agent, LangChain, LlamaIndex, local proxy, and enterprise policy distribution
  remain v2 work unless a later phase explicitly promotes them.

</deferred>

---

*Phase: 02-privacy-core*
*Context gathered: 2026-05-02*
