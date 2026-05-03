# Phase 4: Codex Compatibility Evidence - Context

**Gathered:** 2026-05-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers evidence-backed Codex compatibility claims. It must document current Codex
interception and rewrite options, classify each relevant prompt/tool surface with explicit support
labels, and prevent any automatic Codex masking claim unless raw outbound payload replacement is
proven with strict evidence.

The phase does not build a broad IDE-agent ecosystem, local proxy, LangChain/LlamaIndex adapter, or
enterprise policy distribution. It also does not relax the privacy standard established by the core
policy and Claude phases.

</domain>

<decisions>
## Implementation Decisions

### Evidence Standard
- **D-01:** Codex compatibility uses a strict proof bar. A positive support claim needs current
  official/documented Codex behavior, local installed-Codex probing where feasible, and synthetic
  end-to-end evidence for the specific surface being labeled.
- **D-02:** Documentation-only or repo-issue-only signals may inform the assessment, but they are
  not enough for a positive supported masking claim.
- **D-03:** If a Codex surface cannot be exercised locally or cannot prove pre-provider payload
  replacement, the matrix must label it conservatively and explain the missing evidence.

### Codex Policy Parity
- **D-04:** All prior criteria used for the shared privacy core and Claude enforcement apply to
  Codex too: fail closed by default, synthetic-only validation, sanitized diagnostics, protected
  path handling without file reads, and no raw matched values in outputs.
- **D-05:** If Codex can block a surface but cannot prove rewrite before provider submission, the
  correct label is block-only or experimental block-only, not automatic masking.
- **D-06:** If hook/event coverage, Windows behavior, tool coverage, or version behavior is
  uncertain, the label must remain experimental or unsupported with the uncertainty stated plainly.
- **D-07:** Automatic Codex masking can be claimed only for a surface where tests prove the outbound
  payload equals the verified masked payload before any external-provider submission.

### Deliverable Shape
- **D-08:** Phase 4 should deliver documentation, a compatibility matrix, and automated tests or
  checks that prevent overstated Codex masking claims.
- **D-09:** A Codex doctor-style CLI command is optional, not required. Add one only if the planner
  finds a stable local Codex surface that can be validated safely with synthetic probes.
- **D-10:** The compatibility artifact should be auditable: each row should list the surface, support
  label, evidence source, tested version or docs date where available, privacy action, and remaining
  gaps.

### the agent's Discretion
- The planner may choose the exact file name/location for the Codex compatibility assessment, as
  long as it is easy to find from project docs and included in tests or claim checks.
- The planner may decide whether claim-prevention checks scan Markdown docs, package metadata, CLI
  help text, or all of these.
- The planner may decide whether local Codex probing is a script, pytest fixture, CLI subcommand, or
  manual evidence appendix, provided positive labels still require strict proof.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements and roadmap
- `.planning/REQUIREMENTS.md` - CDX-01 through CDX-03 define the Codex acceptance criteria.
- `.planning/ROADMAP.md` - Phase 4 goal and success criteria.
- `.planning/PROJECT.md` - Core privacy boundary, Codex compatibility target, fail-closed default,
  and no false support claims for unsupported clients.
- `.planning/STATE.md` - Current blocker that Codex interception and rewrite capability are
  unproven.

### Prior phase decisions
- `.planning/phases/02-privacy-core/02-CONTEXT.md` - Locks `SurfaceCapability` labels,
  fail-closed policy, verified masking requirements, and sanitized diagnostics.
- `.planning/phases/03-claude-enforcement/03-CONTEXT.md` - Locks the enforcement standard that
  non-rewriting prompt surfaces block rather than claiming scrub/masking protection.

### Existing implementation
- `privguard/policy.py` - `SurfaceCapability`, `PolicyAction`, and `decide_policy()` provide the
  capability vocabulary and fail-closed decision model Codex labels should reuse.
- `privguard/masking.py` - Verified irreversible masking contract that any rewrite-capable Codex
  claim must satisfy.
- `privguard/diagnostics.py` - Sanitized diagnostic serialization helpers.
- `privguard/cli.py` - Existing CLI structure where an optional Codex diagnostic could be added.
- `tests/test_policy.py` - Existing policy tests covering rewrite-capable, block-only, unknown,
  external, observe-only, and unsupported surfaces.
- `tests/test_claude_phase_gate.py` - Useful pattern for phase-level synthetic gates that protect
  integration claims and output hygiene.

### Prior research
- `.planning/research/STACK.md` - Existing Codex research notes and external reference list. Treat
  these as starting points only; Phase 4 must refresh current official Codex evidence before making
  claims.
- `.planning/research/SUMMARY.md` - Project-level risk framing around false confidence from
  unsupported or non-rewriting client surfaces.
- `.planning/research/PITFALLS.md` - Risks around unsupported interception surfaces, stale
  dependency/client behavior, and overbroad privacy claims.

### External refs to refresh
- `https://developers.openai.com/codex/` - Current official OpenAI Codex documentation entry point.
- `https://developers.openai.com/codex/cli` - Current official Codex CLI documentation if available.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SurfaceCapability` already includes `rewrite-capable`, `block-only`, `observe-only`,
  `unsupported`, `unknown`, and `external`; Phase 4 should not invent new support vocabulary unless
  it maps cleanly back to these policy labels.
- `decide_policy()` already enforces the key rule: unknown/external surfaces fail closed unless the
  payload exactly matches a verified masked payload.
- `mask_text()` and `verify_mask()` already provide the masking verification contract a Codex
  rewrite-capable claim would need.
- Existing pytest files show how to assert sanitized output and fail-closed behavior with synthetic
  fixtures.

### Established Patterns
- Integration claims are tied to explicit surface capabilities, not vague support language.
- Tests and docs must use synthetic CPF/CNPJ/secrets and fake protected paths only.
- Protected files such as `.env` and `data_sensivel/**` must be handled by path classification; do
  not read their contents.
- Hook/adapter diagnostics expose reason codes, kinds, counts, offsets, and decisions, never raw
  prompt text or matched values.

### Integration Points
- A Codex assessment document can live under project docs or Phase 4 artifacts, but the planner
  should ensure future users can find it from `README`/CLI/docs if product docs are introduced.
- A claim-prevention test can scan repository text for phrases that imply Codex automatic masking
  and require nearby evidence or approved labels.
- Optional Codex probing should use local synthetic payloads and should not depend on real project
  secrets, `.env`, or `data_sensivel` contents.

</code_context>

<specifics>
## Specific Ideas

- User selected the strictest evidence option: official/current evidence plus local probing plus
  synthetic proof before any positive Codex support claim.
- User explicitly stated that all criteria used previously should apply to Codex too. This carries
  forward the Phase 2/3 standard rather than creating a weaker Codex-specific standard.
- User selected docs + matrix + tests as the expected deliverable shape.

</specifics>

<deferred>
## Deferred Ideas

- `privguard codex doctor` is deferred to planner discretion; add it only if a stable local Codex
  validation surface exists.
- Broad IDE-agent support, local proxy mode, LangChain/LlamaIndex adapters, and enterprise policy
  distribution remain v2 work.

</deferred>

---

*Phase: 04-codex-compatibility-evidence*
*Context gathered: 2026-05-03*
