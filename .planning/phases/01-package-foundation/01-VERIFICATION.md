---
phase: 01-package-foundation
verified: 2026-05-01T23:28:41Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
human_verification_resolved:
  - test: "Editable install and generated console script"
    expected: "`python -m pip install -e .` succeeds from repo root and `privguard info` runs through the generated console wrapper."
    result: "pass"
    evidence: "Resolved in 01-HUMAN-UAT.md; editable install and generated console wrapper passed in local PowerShell."
---

# Phase 1: Package Foundation Verification Report

**Phase Goal:** Developers can install and run the privacy guard as a local reusable Python tool while existing demos are separated from production-safe behavior.
**Verified:** 2026-05-01T23:28:41Z
**Status:** passed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Developer can install the project locally with a reproducible dependency manifest and run the package CLI. | VERIFIED | `pyproject.toml` has setuptools metadata, `dependencies = []`, optional `full`, and `privguard = "privguard.cli:main"` at lines 1-19. The previous environment blocker was resolved by human UAT: `01-HUMAN-UAT.md` records `python -m pip install -e .` and generated `privguard info` console wrapper verification as pass. |
| 2 | Developer can run CLI diagnostics without invoking root-level demo scripts. | VERIFIED | `python -m privguard.cli info` printed `privguard 0.1.0`, `detectors: lightweight`, and `optional_full: available via privguard[full]`. `privguard/cli.py` uses `importlib.metadata.version("privguard")` at line 13. |
| 3 | Reusable detection, masking, policy, and adapter code is importable from package modules. | VERIFIED | Import smoke checks passed for `detect`, `redact`, `Hit`, `is_sensitive_path`, `summarize_hits`, and `format_hit_summary`. Core files define `Hit`, `detect`, `redact`, and policy helpers in `privguard/detection.py`, `privguard/masking.py`, and `privguard/policy.py`. |
| 4 | Core package imports do not require Presidio, spaCy, or demo scripts. | VERIFIED | `rg -n "presidio|spacy|test_presidio|reversible_demo|ollama_local_demo" privguard` returned no matches. |
| 5 | Sanitized hit summaries omit raw `Hit.value` while preserving kind, offsets, and score. | VERIFIED | `summarize_hits([Hit(...)])` returned only `kind`, `start`, `end`, and `score`; `format_hit_summary()` did not contain the synthetic CPF. |
| 6 | Hook entry files still exist and are thin adapters over `privguard`. | VERIFIED | `hooks/pii_guard.py` imports `main_user_prompt` at line 7; `hooks/pre_tool_guard.py` imports `main_pre_tool` at line 7; `_pii_core.py` is a compatibility shim importing from package modules. |
| 7 | Hook malformed JSON exits 0; blocking violations exit 2 without raw matched values or protected paths. | VERIFIED | Synthetic CPF prompt returned exit code 2 with no raw CPF in captured output. Malformed JSON returned 0. Synthetic `.env` Read payload returned 2 with no `.env` in captured output. |
| 8 | Existing demos are separated from production code and do not print raw sensitive data by default. | VERIFIED | Root demo files are absent; four demos exist under `demos/`. `py_compile` passed. Grep for known raw literals and `Original : {text}` returned no matches. Demo output code uses hidden-content or masked-prompt messages. |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `pyproject.toml` | Setuptools metadata, editable-install support, console script | VERIFIED | gsd artifact check passed; metadata assertions passed; editable install and generated console wrapper passed in `01-HUMAN-UAT.md`. |
| `privguard/__init__.py` | Importable package identity and public exports | VERIFIED | Exports `Hit`, `detect`, `redact`, and `__version__`. |
| `privguard/cli.py` | `privguard info` command | VERIFIED | Direct module CLI works and stays stdlib-only. |
| `privguard/detection.py` | Lightweight `Hit`, validators, patterns, and `detect()` | VERIFIED | Synthetic valid CPF detected; invalid CPF rejected. |
| `privguard/masking.py` | `redact()` masking helper | VERIFIED | Synthetic CPF redacted to `CPF <BR_CPF>`. |
| `privguard/policy.py` | Protected path and sanitized summary helpers | VERIFIED | `.env` and `data_sensivel/cooperados.csv` path literals classify sensitive without reading files. |
| `privguard/hooks.py` | Package-level hook handlers | VERIFIED | Prompt/tool hook behavior spot-checks passed. |
| `hooks/*.py` | Stable Claude entry adapters and compatibility shim | VERIFIED | Adapters import package handlers; `_pii_core.py` imports package detection/masking. |
| `demos/*.py` | Separated runnable demos | VERIFIED | All four expected demos exist and compile. |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `pyproject.toml` | `privguard.cli:main` | `[project.scripts]` | VERIFIED | `privguard = "privguard.cli:main"` present. |
| `privguard/cli.py` | installed metadata | `importlib.metadata.version` | VERIFIED | `version("privguard")` present with local fallback. |
| `privguard/masking.py` | `privguard.detection.Hit` | type import | VERIFIED | `from .detection import Hit` present. |
| `privguard/__init__.py` | detection and masking APIs | public exports | VERIFIED | Imports and `__all__` present. |
| `hooks/pii_guard.py` | `privguard.hooks.main_user_prompt` | direct import | VERIFIED | Thin adapter with repo-root path setup. |
| `hooks/pre_tool_guard.py` | `privguard.hooks.main_pre_tool` | direct import | VERIFIED | Thin adapter with repo-root path setup. |
| repo root | `demos/` | file move | VERIFIED | Root demo files absent; moved files exist under `demos/`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `privguard/cli.py` | `package_version` | `importlib.metadata.version("privguard")`, fallback to `__version__` | Yes | VERIFIED |
| `privguard/hooks.py` | `hits` | `detect(prompt, min_score=threshold)` | Yes | VERIFIED |
| `privguard/hooks.py` | `redacted` | `redact(prompt, hits)` | Yes | VERIFIED |
| `privguard/policy.py` | hit summaries | `Hit` objects passed from detection | Yes, sanitized | VERIFIED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|---|---|---|---|
| CLI diagnostics | `python -m privguard.cli info` | Printed package/version, lightweight detector tier, optional full extra | PASS |
| Core detect/mask | `python -c "from privguard import detect, redact; ..."` | Valid CPF detected and redacted; invalid CPF rejected | PASS |
| Policy summaries | `python -c "from privguard.policy import ..."` | Sensitive path literals classified; summary omitted raw value | PASS |
| Hook prompt block | Synthetic CPF piped to `python hooks\pii_guard.py` | Exit 2; no raw CPF in output | PASS |
| Hook malformed JSON | `not-json` piped to hook adapters | Exit 0 | PASS |
| Hook protected path block | Synthetic `.env` Read payload piped to `python hooks\pre_tool_guard.py` | Exit 2; no raw `.env` in output | PASS |
| Demo/source syntax | `python -m py_compile ...` | All package, hook, and demo files compiled | PASS |
| Editable install wrapper | `python -m pip install -e .`; `privguard info` | Human UAT passed generated console wrapper verification | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| PKG-01 | 01-01 | Install as local Python package with reproducible dependency manifest | VERIFIED | Source metadata verified; editable install and generated console wrapper passed in `01-HUMAN-UAT.md`. |
| PKG-02 | 01-01 | CLI entry point for diagnostics and local checks | VERIFIED WITH NOTE | Context D-01 supersedes requirement wording from `privacy-guard` to locked command `privguard`; `privguard info` works via direct module and console script metadata exists. No `privacy-guard` alias is intentionally provided. |
| PKG-03 | 01-01, 01-02, 01-03 | Reusable detection, masking, policy, and adapter code in importable package modules | VERIFIED | Imports, behavior checks, hook adapters, and no optional dependency imports verified. |
| PKG-04 | 01-04 | Demos separated from production code and no raw sensitive default output | VERIFIED | Demos moved under `demos/`; root demos absent; raw literal grep passed; demos compile. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---:|---|---|---|
| `privguard/hooks.py` | 82 | `PII_GUARD_MODE=scrub` returns 0 with redacted text in context, not proven prompt replacement | Deferred | Code review CR-01 is a real privacy concern for Phase 3 Claude enforcement. Default mode blocks, and Phase 1 goal is package foundation, so this is not a Phase 1 blocker. |
| `privguard/detection.py` | 71 | Formatted-only CPF/CNPJ lightweight patterns | Deferred | Code review CR-02 belongs to Phase 2 detection depth; Phase 1 only needed reusable lightweight extraction and demo separation. |
| `privguard/hooks.py` | 51 | Inline tool PII threshold drift | Deferred | Code review WR-01 belongs to Phase 2 policy/Phase 3 Claude enforcement. |

### Human Verification Completed

### 1. Editable Install And Console Wrapper

**Test:** On a machine/session where pip can create temp build-tracker files, run `python -m pip install -e .`, then `privguard info`.
**Expected:** Install succeeds; generated `privguard` console command prints the same three sanitized lines as `python -m privguard.cli info`.
**Result:** Pass.
**Evidence:** `01-HUMAN-UAT.md` records the editable install and generated console wrapper test as passed with `pending: 0`, `blocked: 0`, and `issues: 0`.

### Deferred Items

| # | Item | Addressed In | Evidence |
|---|---|---|---|
| 1 | Scrub mode/rewrite-capable hook semantics | Phase 3 | Phase 3 goal and success criteria require Claude hooks to block when rewrite cannot be guaranteed. |
| 2 | Unformatted CPF/CNPJ and broader detection coverage | Phase 2 | Phase 2 goal and DET-01 through DET-06 cover Brazil-first detection depth and validator consistency. |
| 3 | Inline tool threshold/policy consistency | Phase 2/3 | Phase 2 policy success criteria and Phase 3 Claude enforcement success criteria cover strict fail-closed behavior. |

### Gaps Summary

No source-code product gap blocks the Phase 1 package foundation. The previous environmental uncertainty around editable install and the generated console script wrapper is resolved by `01-HUMAN-UAT.md`. The locked command name is `privguard`; the older `privacy-guard` wording in REQUIREMENTS/ROADMAP is superseded by Phase 1 context D-01.

---

_Verified: 2026-05-01T23:28:41Z_
_Verifier: Claude (gsd-verifier)_
