# Domain Pitfalls

**Domain:** Local privacy guard package for LLM/code-agent terminal and IDE workflows
**Researched:** 2026-05-01
**Scope:** Privacy/security failure modes for Brazilian PII, credentials, local sensitive files, hook/client integrations, and command/tool exfiltration boundaries.
**Overall confidence:** HIGH for project-specific risks from `.planning/PROJECT.md` and `.planning/codebase/*.md`; MEDIUM for cross-client IDE/agent behavior because exact Codex and other IDE-agent interception surfaces still need validation.

## Critical Pitfalls

Mistakes that can cause real data disclosure, false security claims, or major rewrites.

### Pitfall 1: Raw Values Leak Through Logs, Hook Output, Demo Output, or Error Messages

**What goes wrong:** Sensitive values are detected but then echoed back through `stdout`, `stderr`, JSON hook output, terminal transcripts, CI logs, model debug traces, or demo print statements.

**Why it happens:** The current codebase is demo-oriented and uses plain `print()`/`stderr`. Existing mapping documents identify hook messages that can include matched values, Presidio demos that print original snippets, and Ollama error paths that can expose prompts if not constrained.

**Consequences:** The guard becomes an exfiltration path. Even if remote LLM submission is blocked, raw CPF/CNPJ, names, credentials, `.env` values, dump excerpts, or command strings can end up in terminal history, agent transcripts, issue reports, screenshots, or CI artifacts.

**Prevention:**
- Treat all output channels as untrusted by default.
- Hook denial messages must include only entity type, count, policy name, and optionally character ranges; never include `h.value`, original snippets, prompt excerpts, command text, or file contents.
- Demos and examples must default to anonymized output and aggregate counts. Any raw-output teaching mode should require an explicit local-only opt-in such as `--show-original`.
- Provider/client adapters must redact request, response, exception, retry, and telemetry logs before formatting errors.
- Add regression tests that assert blocked prompts and commands do not echo sensitive substrings in either `stdout` or `stderr`.

**Detection:**
- Search source for `print(`, `stderr.write`, logger calls, exception formatting, `repr(payload)`, and JSON hook output paths.
- Run hook tests with synthetic sensitive values and assert those exact values are absent from every captured output stream.
- Review CI artifacts and local transcripts after failed tests for raw fixture values.

**Confidence:** HIGH. Directly supported by current codebase concerns and project requirements.

### Pitfall 2: False Confidence From Hooks That Cannot Rewrite the Submitted Prompt

**What goes wrong:** A mode named or documented as "scrub", "mask", or "sanitize" emits a redacted suggestion but the original clear-text prompt still proceeds to the LLM provider.

**Why it happens:** Some hook APIs can block or annotate but cannot replace the in-flight payload. Current Claude prompt guard `scrub` behavior is documented as not actually rewriting the submitted prompt.

**Consequences:** Users believe sensitive data was masked while the provider receives raw data. This is worse than a visible block because it creates a false assurance around the core value: no clear-text sensitive data leaves the machine.

**Prevention:**
- Classify each integration surface by capability: `rewrite-capable`, `block-only`, `observe-only`, or `unsupported`.
- Default to block mode unless a client surface has verified replacement semantics.
- Avoid product terms like "scrub" or "mask" for hook paths that cannot mutate the outgoing payload.
- For Claude Code, treat hook-based prompt masking as unproven until an integration test demonstrates the external submission receives the rewritten text.
- For Codex and IDE agents, validate interception semantics before claiming support.

**Detection:**
- Add integration tests or harnesses that submit synthetic PII and capture the exact payload sent to the provider/client boundary.
- Require a compatibility matrix for every supported client and mode.
- Fail roadmap phases that add "masking" without a verified rewrite or wrapper boundary.

**Confidence:** HIGH for current Claude hook risk; MEDIUM for other clients pending surface validation.

### Pitfall 3: Regex and Pattern Bypasses in Prompt, Path, and Command Scanning

**What goes wrong:** Sensitive data or protected file references bypass guards through alternate formatting, Unicode confusables, separators, casing, shell expansion, encoding, variable indirection, archives, or helper scripts.

**Why it happens:** Hook scanning is intentionally lightweight and regex-based. The pre-tool guard currently checks selected command/path shapes, not a fully parsed shell AST or resolved filesystem access graph.

**Consequences:** A command such as reading, copying, compressing, base64-encoding, or uploading sensitive data can avoid detection. Prompt PII can slip through when formatted differently from fixture patterns.

**Prevention:**
- Use regex hooks as a fast first line, not the only boundary.
- Normalize text before detection: Unicode normalization, separator normalization, case folding where applicable, and digit extraction for Brazilian identifiers.
- Use checksum validators for CPF, CNPJ, CNH, PIS/PASEP, voter title, SUS, and Luhn-like numbers where available.
- Add deny-by-path policy independent of command verb: any command string referencing protected paths should be denied unless explicitly safe.
- Add tests for bypass families: quoted Windows paths, mixed `/` and `\`, `..` traversal, wildcard expansion, PowerShell variables, environment variables, aliases, `Get-Content`, `type`, `more`, `python -c`, `tar/zip`, `curl`, `Invoke-WebRequest`, `scp`, `base64`, and clipboard commands.

**Detection:**
- Maintain a bypass test corpus with expected block decisions.
- Track false negatives by category, not only by individual example.
- Review every new supported shell or IDE tool for argument expansion semantics.

**Confidence:** HIGH for current hook design; MEDIUM for exact bypass coverage until a shell-aware parser strategy is chosen.

### Pitfall 4: Path Normalization Gaps Expose Protected Files

**What goes wrong:** `.env`, `data_sensivel/**`, dumps, credentials, or secret-like files are protected by apparent path string matches, but equivalent paths bypass the rule.

**Why it happens:** Raw string comparisons miss canonical path equivalence: relative traversal, symlinks/junctions, drive-letter casing, UNC paths, URL/file URI forms, short 8.3 Windows paths, mixed separators, encoded characters, and shell-expanded variables.

**Consequences:** The agent can read or search protected local data even though policy appears to deny it. This can leak raw values into prompts, tool outputs, or logs.

**Prevention:**
- Resolve paths against the project root before policy decisions when the tool payload exposes file paths.
- Compare canonical absolute paths and enforce that protected roots remain protected after normalization.
- Deny ambiguous paths that cannot be safely resolved in a hook context.
- Include both explicit protected roots and filename-sensitive rules such as `.env`, `.env.*`, `*credential*`, `*secret*`, `dump_*`, and common cloud credential locations.
- Avoid relying solely on `.claude/settings.json`; enforce the same policy in package code and tests.

**Detection:**
- Unit-test `is_sensitive_path()` and tool payload handling with Windows and POSIX-style variants.
- Add fixture-free tests that reference protected path names only and never read their contents.
- Test execution from alternate working directories because current scripts use path insertion and project-root assumptions.

**Confidence:** HIGH. Path matching fragility is explicitly identified in the codebase map.

### Pitfall 5: False Negatives and False Positives Undermine Trust in Opposite Ways

**What goes wrong:** The guard misses sensitive data that should be masked, or blocks safe content so often that users disable or bypass it.

**Why it happens:** Brazilian identifiers have overlapping numeric formats; names and account data are context-sensitive; generic regexes overmatch; thresholds can be changed through environment variables; Presidio and lightweight hook recognizers are duplicated and can drift.

**Consequences:** False negatives leak data. Excessive false positives push developers toward `warn` mode, local hook disablement, manual copy/paste around the guard, or broad allow rules.

**Prevention:**
- Define privacy modes with explicit recall/friction tradeoffs: strict, balanced, and permissive.
- Keep strict mode as the default for protected paths, credentials, `.env`, dumps, and high-confidence Brazilian identifiers.
- Use checksum validation and overlap tests for structured identifiers.
- Keep hook and Presidio recognizer behavior aligned through shared fixtures and a documented recognizer contract.
- Make allowlisting narrow, local, and auditable; never allowlist raw protected roots.

**Detection:**
- Build a synthetic fixture suite for valid/invalid CPF, CNPJ, CNH, voter title, PIS/PASEP, SUS, RG-like values, phones, CEP, plates, bank/account data, API keys, `.env`-style lines, and benign numeric strings.
- Track expected entity counts and blocked/allowed decisions in automated tests.
- Review user bypass requests as product signals, not just one-off exceptions.

**Confidence:** HIGH. Supported by duplicated recognizer concerns and missing assertion-based tests.

### Pitfall 6: Command Exfiltration Through Shell, Scripting, Network, Clipboard, or Archive Tools

**What goes wrong:** A command reads sensitive data and sends it elsewhere, or transforms it before sending so simple scanner rules do not see the payload.

**Why it happens:** Terminal agents can run broad shell commands. A pre-tool hook sees command text, not every file descriptor, subprocess, or network operation that the shell will perform after expansion.

**Consequences:** Sensitive files can be copied into logs, compressed into artifacts, uploaded to network endpoints, placed on the clipboard, embedded in generated code, or passed to external CLIs.

**Prevention:**
- Deny command references to protected paths regardless of command verb.
- Block or require explicit local approval for commands that combine protected paths with network, archive, clipboard, encoding, or process-substitution tools.
- Treat arbitrary script execution that can read protected paths as high risk unless the script is part of the package test suite and uses synthetic data.
- Separate "read project source" permission from "read sensitive local data" permission at the policy level.
- Add a future OS-level option for filesystem permissions or sandboxing; hooks alone are not a complete data boundary.

**Detection:**
- Test known exfiltration forms: `curl --data-binary @file`, `Invoke-WebRequest -InFile`, `scp`, `rclone`, `git add` of sensitive files, `tar/zip` including sensitive paths, `base64 file | curl`, `python -c open(...)`, PowerShell `Get-Content | Set-Clipboard`, and copy commands into public folders.
- Inspect generated artifacts and git status for sensitive path names before commits or packaging.

**Confidence:** HIGH for risk; MEDIUM for complete mitigation because full shell semantics are hard to model in lightweight hooks.

### Pitfall 7: Real Sensitive Data Enters Tests, Fixtures, Docs, Planning, or Commits

**What goes wrong:** Real `.env` values, company dumps, Brazilian personal data, or realistic customer files are copied into fixtures, docs, examples, screenshots, test snapshots, planning notes, or version control.

**Why it happens:** The repo currently contains protected local data paths inside the project tree. Demo culture encourages copying representative examples. Automated agents may read files unless guarded.

**Consequences:** The project intended to prevent leakage becomes a repository of sensitive data. This creates legal, compliance, and operational cleanup risk.

**Prevention:**
- Move real sensitive data outside the source tree where feasible.
- Add `.gitignore` entries before repository sharing: `.env`, `.env.*`, `data_sensivel/`, dumps, credentials, caches, local model artifacts, and generated transcripts.
- Use synthetic fixtures only, with clearly fake but validator-correct identifiers.
- Add a pre-commit or pre-package scanner for secrets, protected paths, and Brazilian PII.
- Planning and research docs may reference protected paths by name but must never quote contents.

**Detection:**
- Scan git status and staged files for protected paths before commits.
- Run secret/PII scanning over docs, tests, snapshots, and examples.
- Review generated artifacts after failed tests because failure output often captures raw inputs.

**Confidence:** HIGH. Directly aligned with project constraints and current `data_sensivel/` placement.

### Pitfall 8: Provider and Client Integration Assumptions Break the Privacy Boundary

**What goes wrong:** The package assumes a provider/client can be intercepted, rewritten, or configured locally, but the actual tool sends prompts, context, embeddings, telemetry, file snippets, or tool results through a separate path.

**Why it happens:** Claude Code hooks, Codex-style agents, IDE extensions, and LLM SDKs have different interception points. Some can block prompt submission, some can wrap provider calls, and some may collect context before user hooks run.

**Consequences:** Sensitive data can leave through context indexing, tool result summaries, chat history sync, crash telemetry, embeddings, or provider retries even if the visible prompt path is protected.

**Prevention:**
- Support clients only after mapping all outbound channels: prompts, tool calls, tool results, file context, embeddings, telemetry, logs, retries, and crash reports.
- Start with controlled local boundaries: wrapper CLI, local proxy with fail-closed behavior, or verified hook surfaces.
- For unsupported clients, say unsupported rather than implying protection.
- Add provider/client adapters with explicit privacy contracts and tests that assert remote endpoints never receive raw synthetic sensitive values.
- Keep local LLM routing pinned to loopback or explicitly approved local endpoints.

**Detection:**
- Build a compatibility matrix with capability, tested version/date, supported modes, and known gaps.
- Use fake provider endpoints in tests to capture exact outbound payloads.
- Check whether client updates changed hook payload schema or timing.

**Confidence:** MEDIUM. The risk is clear, but exact client behavior requires phase-specific validation.

### Pitfall 9: Dependency Drift Changes Detection, Anonymization, or Crypto Behavior

**What goes wrong:** Presidio, spaCy, language models, `cryptography`, or transitive dependencies change behavior after upgrades or machine-local installs.

**Why it happens:** The project has no dependency manifest or lockfile. Current installed versions are machine-local, and model availability is implicit.

**Consequences:** Entity recall/precision, recognizer results, anonymizer operators, encryption/decryption compatibility, performance, or error behavior can drift without code changes. Compliance claims become unreproducible.

**Prevention:**
- Add `pyproject.toml` or `requirements.txt` plus a lockfile before packaging.
- Pin Presidio analyzer/anonymizer, spaCy, language model, and cryptography-compatible versions.
- Record the required `pt_core_news_lg` model version and install step.
- Treat dependency upgrades as security-sensitive changes requiring regression tests for detection counts, masking output, and no-raw-output guarantees.

**Detection:**
- CI should print package versions without printing environment secrets.
- Add smoke tests that fail when expected synthetic entities are missed or output format changes in unsafe ways.
- Run compatibility tests before dependency bumps.

**Confidence:** HIGH. No manifest/lockfile is documented in the codebase map.

### Pitfall 10: Secret and Key Management Patterns Stay Demo-Grade

**What goes wrong:** Demo encryption/decryption patterns, local environment handling, or reversible maps become production defaults.

**Why it happens:** `reversible_demo.py` demonstrates in-memory AES key use and notes production keyring/HSM needs, but no production secret manager exists. `.env` exists but should not be read.

**Consequences:** Decryption keys, token maps, or provider credentials can leak through memory dumps, logs, local files, or bad defaults. Reversible masking can become a new sensitive data store.

**Prevention:**
- For v1, prefer irreversible masking before external submission unless reversible restoration is explicitly required.
- If reversible maps are introduced, store keys in OS keyring/HSM/local secret store, define retention, and separate decryption authority from scanning code.
- Never log encrypted tokens when they can be correlated with local maps.
- Provide `.env.example` with variable names only, not values.

**Detection:**
- Search for key material, token maps, and `.env` reads in source and tests.
- Add tests that production modes never print keys, encrypted maps, raw source text, or provider secrets.

**Confidence:** HIGH for current gap; MEDIUM for final key management recommendation until reversible requirements are confirmed.

## Moderate Pitfalls

### Pitfall 1: Hook Runtime Failures Fail Open in Unsafe Contexts

**What goes wrong:** Invalid JSON, missing Python, missing environment variables, import failures, or hook crashes allow the action to proceed.

**Prevention:** Define failure policy per event. Malformed hook payloads may fail open for compatibility, but missing guard executable, missing scanner imports, or invalid mode configuration should produce a visible fail-closed state in strict mode. Add startup diagnostics that do not include raw prompt content.

**Confidence:** MEDIUM. Current hook JSON parsing fails open by design; production policy needs explicit treatment.

### Pitfall 2: Threshold and Mode Configuration Can Weaken Protection Silently

**What goes wrong:** `PII_GUARD_THRESHOLD` or `PII_GUARD_MODE` is set to permissive values and users assume protection is unchanged.

**Prevention:** Validate env values, print privacy-safe startup status, make strict defaults explicit, and require deliberate local config for warn/permissive modes. Consider refusing unsafe modes for protected paths and credentials.

**Confidence:** HIGH.

### Pitfall 3: Overlap Resolution Suppresses More Specific Detections

**What goes wrong:** Broad numeric or generic secret patterns overlap with CPF/CNPJ/CNH/PIS/SUS/phone/CEP matches and the wrong entity wins.

**Prevention:** Add deterministic priority ordering, entity-specific tests, and expected overlap outcomes before adding recognizers.

**Confidence:** HIGH.

### Pitfall 4: Performance Pressure Encourages Unsafe Shortcuts

**What goes wrong:** Slow Presidio/spaCy startup or hook latency motivates disabling scans, raising thresholds, or skipping tool-result scanning.

**Prevention:** Keep hook scanning lightweight; cache heavy analyzers only in controlled long-running processes; benchmark worst-case regex input; expose fast strict checks for paths/secrets independent of NLP.

**Confidence:** MEDIUM.

### Pitfall 5: Local LLM Routing Is Mistaken for Universal Safety

**What goes wrong:** Ollama/local routing is treated as safe even when model endpoint, logs, plugins, or container/network boundaries are not verified.

**Prevention:** Enforce loopback/local allowlists, validate model endpoint before sending prompts, avoid logging prompts on errors, and document that local routing is a separate privacy mode, not a blanket guarantee.

**Confidence:** MEDIUM.

## Minor Pitfalls

### Pitfall 1: Demo/Test Naming Confuses Tooling

**What goes wrong:** Files named `test_*.py` are demo scripts, so future pytest adoption may collect them unexpectedly or preserve print-driven tests.

**Prevention:** Move demos under `examples/` or rename before adding formal tests. Put assertion tests under `tests/`.

**Confidence:** HIGH.

### Pitfall 2: Generated Caches and Local Config Add Packaging Noise

**What goes wrong:** `__pycache__`, local settings, and generated artifacts are included in packages or commits.

**Prevention:** Add ignore rules and package include/exclude configuration before distribution.

**Confidence:** HIGH.

### Pitfall 3: Import Path Mutation Breaks Alternate Working Directories

**What goes wrong:** Scripts using `sys.path.insert()` work from one invocation pattern but fail or import the wrong module elsewhere.

**Prevention:** Package shared modules and run hooks through stable module entry points.

**Confidence:** MEDIUM.

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| Package layout and CLI | Demo output and raw sample behavior become production defaults | Separate `src/` package from `examples/`; default CLI output to masked data/counts only |
| Claude Code integration | Hook "scrub" implies rewrite but cannot replace prompt | Default to block unless payload rewrite is proven; document hook capability matrix |
| Codex/IDE integration | Unsupported interception surfaces leak context outside guard | Research exact client lifecycle; use wrapper/proxy only where outbound payload can be captured |
| Prompt masking | False negatives from regex-only detection | Combine lightweight high-confidence hooks with Presidio-backed analysis where latency permits |
| Tool-use guard | Command exfiltration through shell expansion or helper scripts | Deny protected path references broadly; test shell bypass corpus |
| Path protection | Raw string path matching misses equivalent protected paths | Canonicalize paths, resolve project root, deny ambiguous paths |
| Logging and diagnostics | Denial/error messages echo raw values | Test captured `stdout`/`stderr` for absence of sensitive fixture values |
| Test suite | Real data enters fixtures or snapshots | Synthetic fixtures only; never read `.env` or `data_sensivel`; scan test artifacts |
| Dependency manifest | Presidio/spaCy behavior drifts | Pin versions and model; add regression tests before upgrades |
| Local LLM mode | Non-local endpoint or error logs expose prompts | Enforce loopback allowlist and privacy-safe error handling |
| Reversible anonymization | Key/map storage becomes a sensitive database | Defer reversible flows for v1 unless required; use keyring/HSM and retention policy if added |

## Validation Checklist for Roadmap Phases

- Does this phase prove raw sensitive values are absent from `stdout`, `stderr`, logs, exceptions, snapshots, and hook JSON?
- Does this phase distinguish block-only, rewrite-capable, observe-only, and unsupported client surfaces?
- Does this phase include path normalization tests for protected files without reading their contents?
- Does this phase include command exfiltration bypass tests for Windows PowerShell and common POSIX-like forms?
- Does this phase use only synthetic validator-correct sensitive data?
- Does this phase pin or record dependency versions if behavior depends on Presidio, spaCy, language models, or cryptography?
- Does this phase fail closed for protected files, credentials, and high-confidence Brazilian identifiers?
- Does this phase document any remaining false-negative or false-positive classes as explicit risk?

## Sources

- `.planning/PROJECT.md` - Project goal, constraints, active requirements, and safety defaults.
- `.planning/codebase/ARCHITECTURE.md` - Current script/hook layers, data flow, state management, and hook behavior.
- `.planning/codebase/CONCERNS.md` - Known bugs, security considerations, fragile areas, and test gaps.
- `.planning/codebase/CONVENTIONS.md` - Current output/error patterns and hook coding conventions.
- `.planning/codebase/INTEGRATIONS.md` - Presidio, spaCy, Ollama, Claude hook, and local secret handling boundaries.
- `.planning/codebase/STACK.md` - Current dependency versions, missing manifest/lockfile, and runtime assumptions.
- `.planning/codebase/STRUCTURE.md` - Protected path layout and where guard logic currently lives.
- `.planning/codebase/TESTING.md` - Existing verification style, missing automated tests, and fixture constraints.
