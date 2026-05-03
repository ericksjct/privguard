---
phase: 02-privacy-core
verified: 2026-05-03T15:40:33Z
status: passed
score: 18/18 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 15/18
  gaps_closed:
    - "Token/API-key assignment masking now verifies safe when output is placeholder-only assignment."
    - "CLI mask exits 0 for token=... and api_key=... fake-secret assignment payloads without leaking raw values."
    - "CLI policy-check --masked --capability external allows verified masked fake-secret assignment payloads."
  gaps_remaining: []
  regressions: []
human_verification: []
---

# Phase 2: Privacy Core Verification Report

**Phase Goal:** Supported clients and CLI commands share Brazil-first detection, irreversible masking, protected-path classification, fail-closed policy decisions, and sanitized diagnostics.
**Verified:** 2026-05-03T15:40:33Z
**Status:** passed
**Re-verification:** Yes - after masking verification gap closure

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can scan synthetic Brazilian identifiers, fake secrets, and protected path strings and see only entity types, counts, offsets, and reason codes. | VERIFIED | `detect()`/`analyze_text()` are exercised by `tests/test_detection.py`; CLI scan JSON remains metadata-only. |
| 2 | User can mask detected sensitive text into typed placeholders, and the guard refuses output when original synthetic sensitive substrings remain. | VERIFIED | `verify_mask()` still fails original remnants and residual real detections; placeholder-only assignments are explicitly allowed only when the original value is absent. |
| 3 | User can rely on strict mode as the default for external-provider workflows, including unknown providers and unclassified client targets. | VERIFIED | `decide_policy()` defaults to strict and unknown/external block unless payload equals a verified `MaskResult.text`. |
| 4 | User can see whether a surface is rewrite-capable, block-only, observe-only, or unsupported before the guard allows external submission. | VERIFIED | `SurfaceCapability` labels are defined and exposed as CLI `--capability` choices. |
| 5 | Lightweight hook detection and Presidio-backed detection agree on validator semantics for shared synthetic fixtures. | VERIFIED | Canonical validator helpers and tests remain present in `privguard/detection.py` and `tests/test_detection.py`. |
| 6 | User can run one complete detection behavior for Brazilian identifiers, contact data, and secret-like values without choosing light/full modes. | VERIFIED | One `detect()` path; no user-facing detector mode selector. |
| 7 | Valid structured Brazilian identifiers are accepted by checksum validators, while invalid lookalikes are rejected or downgraded below the reporting threshold. | VERIFIED | Validator tests cover valid/invalid CPF, CNPJ, CNH, voter title, PIS/PASEP, and SUS fixtures. |
| 8 | Detection results can be summarized without exposing raw matched values. | VERIFIED | `diagnostics.to_dict()` omits `Hit.value`; tests assert raw fixtures do not appear in rendered diagnostics. |
| 9 | User can mask detected sensitive text into typed placeholders before external-provider submission paths. | VERIFIED | Direct spot-checks confirm token/API-key assignment masks verify and external policy allows the masked payload. |
| 10 | The core verifies masked output before it can be treated as safe. | VERIFIED | `verify_mask()` gates `MaskResult.verified`; `decide_policy()` requires verified mask plus payload match for external/unknown allow. |
| 11 | Diagnostics can be rendered as human-readable text or JSON without raw values or prompt snippets. | VERIFIED | `to_json()` and `format_text()` serialize metadata only; tests cover leak resistance. |
| 12 | User can classify protected path strings without reading protected file contents. | VERIFIED | `classify_path()` normalizes strings only; anti-pattern scan found no runtime file reads in `privguard/policy.py`. |
| 13 | Unknown, unclassified, external, unsupported, and unverified surfaces fail closed by default. | VERIFIED | Policy tests and CLI spot-checks confirm fail-closed defaults and pause/block for unverified masks. |
| 14 | Rewrite-capable surfaces allow masked content only after verification. | VERIFIED | `decide_policy()` allows rewrite-capable sensitive payloads only with verified mask results. |
| 15 | Policy decisions expose sanitized reason codes, capability labels, and decision status. | VERIFIED | `PolicyDecision` plus diagnostics serialization expose action/capability/reason metadata only. |
| 16 | User can run CLI scan, mask, and policy checks against synthetic input and receive sanitized output. | VERIFIED | Full CLI tests pass; direct `mask` and `policy-check --masked --capability external` assignment checks pass without raw-value leakage. |
| 17 | JSON output is available for tool consumers while human-readable output remains the default. | VERIFIED | CLI `scan`, `mask`, and `policy-check` implement `--json`; defaults remain human-readable. |
| 18 | The package exports stable core APIs for later Claude and Codex phases without implementing those integration details here. | VERIFIED | Public exports remain in `privguard/__init__.py`; no Phase 3/4 support claims were introduced. |

**Score:** 18/18 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `privguard/detection.py` | Canonical validators, detection hits/reports, one public detect contract | VERIFIED | gsd artifact check passed; tests exercise detection and reports. |
| `privguard/masking.py` | `MaskResult`, irreversible placeholder masking, post-mask verification | VERIFIED | Placeholder assignment handling exists via `PLACEHOLDER_ASSIGNMENT` and residual filtering; tests cover token assignment pass and suffix rejection. |
| `privguard/diagnostics.py` | Sanitized text and JSON serializers | VERIFIED | Serializers omit raw hit values and masked payload text. |
| `privguard/policy.py` | Path classification, capabilities, fail-closed decisions | VERIFIED | External allow is tied to verified mask and payload match. |
| `privguard/cli.py` | scan, mask, policy-check subcommands | VERIFIED | CLI commands are wired to detection, masking, policy, and diagnostics. |
| `privguard/__init__.py` | Stable public exports | VERIFIED | gsd artifact check passed. |
| `pyproject.toml` | CLI script aliases | VERIFIED | gsd artifact check passed. |
| `tests/test_detection.py` | Detection regression tests | VERIFIED | Included in passing suite. |
| `tests/test_masking.py` | Masking/diagnostic leak tests | VERIFIED | Includes placeholder-only secret assignment regression coverage. |
| `tests/test_policy.py` | Policy/path tests | VERIFIED | Includes external verified-mask payload matching. |
| `tests/test_cli.py` | CLI behavior and output hygiene tests | VERIFIED | Includes mask and external policy fake-secret assignment regressions. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `privguard/detection.py` | `tests/test_detection.py` | synthetic fixture expectations | VERIFIED | gsd plan regex is invalid, but manual grep found `detect()` and `analyze_text()` exercised throughout tests. |
| `privguard/masking.py` | `privguard/detection.py` | `Hit` spans and residual checks | VERIFIED | Imports `Hit` and `detect`; `verify_mask()` calls `detect(masked_text)`. |
| `privguard/diagnostics.py` | `privguard/masking.py` | `MaskResult` metadata only | VERIFIED | Imports and serializes `MaskResult` without `text`. |
| `privguard/policy.py` | `privguard/masking.py` | mask verification status | VERIFIED | Uses `MaskResult.verified`, reason codes, and payload matching. |
| `privguard/policy.py` | `privguard/diagnostics.py` | sanitized decision metadata | VERIFIED | Compatibility wrappers delegate to diagnostics. |
| `privguard/cli.py` | detection/masking/policy | scan, mask, policy-check | VERIFIED | gsd key-link check passed for all three CLI links. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `privguard/cli.py` scan | `report` | `_read_text()` -> `analyze_text()` | Yes | FLOWING |
| `privguard/cli.py` mask | `result` | `_read_text()` -> `mask_text()` -> `verify_mask()` | Yes | FLOWING |
| `privguard/cli.py` policy-check | `decision` | `_read_text()`/`detect()`/`mask_text()`/`classify_path()` -> `decide_policy()` | Yes | FLOWING |
| `privguard/diagnostics.py` | serialized metadata | `to_dict()` over dataclasses/results | Yes | FLOWING and sanitized |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full phase test suite | `python -m pytest tests/test_detection.py tests/test_masking.py tests/test_policy.py tests/test_cli.py -q` | `45 passed`, one pytest cache warning | PASS |
| Compile package | `python -m compileall privguard` | Package compiled | PASS |
| CLI mask token assignment | `python -m privguard.cli mask "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"` | exit 0, `token=<TOKEN>` | PASS |
| CLI mask API-key assignment | `python -m privguard.cli mask "api_key=sk-test-abcdefghijklmnopqrstuvwxyz"` | exit 0, `api_key=<API_KEY>` | PASS |
| External policy masked API-key assignment | `python -m privguard.cli policy-check --json --masked --capability external "api_key=sk-test-abcdefghijklmnopqrstuvwxyz"` | exit 0, `allow=true`, `payload_masked`; raw value absent | PASS |
| External policy masked token assignment | `python -m privguard.cli policy-check --json --masked --capability external "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"` | exit 0, `allow=true`, `payload_masked`; raw value absent | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DET-01 | 02-01, 02-04 | CPF checksum detection | SATISFIED | Detection tests and scan behavior. |
| DET-02 | 02-01, 02-04 | CNPJ checksum detection | SATISFIED | Detection tests and scan behavior. |
| DET-03 | 02-01, 02-04 | Additional Brazilian identifiers/contact data | SATISFIED | Detection tests cover CNH, voter title, PIS/PASEP, SUS, RG, phone, CEP, plates. |
| DET-04 | 02-01, 02-04 | Secret-like values | SATISFIED | API key, token, password, database URL, and assignment tests pass. |
| DET-05 | 02-03, 02-04 | Protected path classification without contents | SATISFIED | `classify_path()` is string-only and tests cover path normalization. |
| DET-06 | 02-01, 02-04 | Validator parity semantics | SATISFIED | Canonical validator lookup and tests. |
| MASK-01 | 02-02, 02-04 | Typed placeholders before external submission | SATISFIED | Assignment masking and external policy spot-checks pass. |
| MASK-02 | 02-02, 02-04 | Verify masked output excludes originals | SATISFIED | Tests reject original remnants and direct CLI output omitted raw fake secrets. |
| MASK-03 | 02-02, 02-04 | Irreversible masking, no maps | SATISFIED | `MaskResult` has no mapping/deanonymization state. |
| MASK-04 | 02-03, 02-04 | Block when masking cannot prove replacement | SATISFIED | Unverified mask paths pause/block; verified external payloads require payload match. |
| POL-01 | 02-03, 02-04 | Strict/fail-closed default | SATISFIED | Unknown/external strict default blocks unless verified masked payload is supplied. |
| POL-02 | 02-03, 02-04 | Surface capability distinctions | SATISFIED | Capability constants and CLI choices exist. |
| POL-03 | 02-03, 02-04 | Unknown/unclassified external requires masking/blocking | SATISFIED | External `policy-check --masked` allows only verified masked payloads. |
| POL-04 | 02-02, 02-03, 02-04 | Sanitized decisions/diagnostics | SATISFIED | Diagnostics and CLI tests assert raw values and path strings are omitted. |

No orphaned Phase 2 requirements were found in `.planning/REQUIREMENTS.md`.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_policy.py` | 50 | `.read_text()` | Info | Test inspects `privguard/policy.py` source to prove runtime path classification does not read files; not product behavior. |
| `privguard/masking.py` | 22 | `PLACEHOLDER_ASSIGNMENT` | Info | Security-relevant exception is bounded to full placeholder-only assignments and paired with original-remnant checks. |

### Human Verification Required

None. The re-verified behaviors are package and CLI behaviors with deterministic automated checks.

### Gaps Summary

No gaps remain. The prior masking verification gap is closed by bounded placeholder-assignment residual handling, regression tests, and passing CLI spot-checks for `token=...` and `api_key=...` assignment payloads.

---

_Verified: 2026-05-03T15:40:33Z_
_Verifier: Claude (gsd-verifier)_
