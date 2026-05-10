---
phase: 01-package-foundation
audit-type: gsd-secure-phase
asvs-level: 2
block-on: open
threats-total: 17
threats-closed: 17
threats-open: 0
unregistered-flags: 0
date: 2026-05-02
---

# Phase 01 Security Audit

Verification of mitigations declared in the four plan threat models against the working-tree implementation. Implementation files were not modified during this audit. No `.env` or `data_sensivel/**` reads were performed; all checks are grep / file-read of source under the `privguard/`, `hooks/`, and `demos/` boundaries.

## Scope

- `pyproject.toml`
- `privguard/__init__.py`, `privguard/cli.py`, `privguard/detection.py`, `privguard/masking.py`, `privguard/policy.py`, `privguard/hooks.py`
- `hooks/_pii_core.py`, `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`
- `demos/test_presidio.py`, `demos/test_presidio_br.py`, `demos/reversible_demo.py`, `demos/ollama_local_demo.py`
- `.claude/settings.json`

## Threat Verification

### Plan 01-01 (package metadata)

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-01-01-01 | InfoDisclosure | mitigate | CLOSED | `privguard/cli.py:11-21` `cmd_info` prints exactly three sanitized lines (version, `detectors: lightweight`, `optional_full: available via privguard[full]`); no scanning, no value printing. |
| T-01-01-02 | DoS | mitigate | CLOSED | `pyproject.toml:9` `dependencies = []`; lines 11-16 place Presidio/spaCy under `[project.optional-dependencies].full` with `python_version < '3.14'` marker on `presidio-analyzer`. |
| T-01-01-03 | Spoofing | mitigate | CLOSED | `pyproject.toml:18-19` only `[project.scripts] privguard = "privguard.cli:main"`. Grep for `privacy-guard` in `pyproject.toml` returned no matches. |
| T-01-01-04 | InfoDisclosure | mitigate | CLOSED | `privguard/cli.py` and `privguard/__init__.py` contain no file-read calls; sources contain no `.env` or `data_sensivel` references. Audit performed via grep/Read against source only. |

### Plan 01-02 (core modules)

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-01-02-01 | InfoDisclosure | mitigate | CLOSED | `privguard/policy.py:39-48` `summarize_hits` returns dicts with only `kind`, `start`, `end`, `score`. Grep for `"value":` in `policy.py` returned no matches. `format_hit_summary` (lines 51-55) emits `kind@start:end score=...` only. |
| T-01-02-02 | InfoDisclosure | mitigate | CLOSED | Plan summary 01-02 lines 95-99 attest synthetic strings only; verification scripts in plan use synthetic CPF `529.982.247-25` and path strings, not file reads. |
| T-01-02-03 | DoS | mitigate | CLOSED | Grep for `presidio\|spacy\|test_presidio\|reversible_demo\|ollama_local_demo` across `privguard/` returned no matches. `detection.py`, `masking.py`, `policy.py`, `__init__.py` import only stdlib (`re`, `dataclasses`, `typing`). |
| T-01-02-04 | Tampering | mitigate | CLOSED | `privguard/policy.py:9-16` `SENSITIVE_GLOBS` preserves all six categories: `data_sensivel`, `cooperados`, `dump_*`, `.env`/`.env.*`, `credenciais*`, `segredo*` with case-insensitive matching. |

### Plan 01-03 (hook adapters)

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-01-03-01 | InfoDisclosure | mitigate | CLOSED | `privguard/hooks.py:73-74,100-103` use `format_hit_summary(hits)` and `redact(prompt, hits)`; grep for `h.value` in `privguard/` returned no matches. |
| T-01-03-02 | InfoDisclosure | mitigate | CLOSED | `privguard/hooks.py:15-17` `deny()` writes only `reason={reason_code}` to stderr. `check_path_tool`, `check_glob_grep`, `check_bash` (lines 20-54) return reason codes only (`sensitive_path`, `sensitive_glob_or_grep`, `sensitive_read_command`, `sensitive_network_command`, `inline_pii`); raw paths/commands/PII never reach output. |
| T-01-03-03 | Tampering | mitigate | CLOSED | `hooks/pii_guard.py:7,11` and `hooks/pre_tool_guard.py:7,11` import package handlers and `raise SystemExit(main_*())`. `.claude/settings.json:33,43` still references `hooks/pii_guard.py` and `hooks/pre_tool_guard.py` paths. |
| T-01-03-04 | DoS | mitigate | CLOSED | `privguard/hooks.py:60,110` both have `except (json.JSONDecodeError, ValueError): return 0`. |
| T-01-03-05 | EoP | mitigate | CLOSED | `privguard/hooks.py:17,104` `return 2` for blocked deny path and blocked prompt; `deny()` always returns 2. |

### Plan 01-04 (demo separation)

| Threat ID | Category | Disposition | Status | Evidence |
|-----------|----------|-------------|--------|----------|
| T-01-04-01 | InfoDisclosure | mitigate | CLOSED | Grep across `demos/` for `529\.982\.247-25\|11\.222\.333/0001-81\|sk-ant-fake\|AKIAIOSFODNN7EXAMPLE` returned no matches. Moved demos use sanitized synthetic literals (e.g. `168.995.350-09`, `<BR_CPF>` placeholder in Ollama prompt). |
| T-01-04-02 | InfoDisclosure | mitigate | CLOSED | Grep across `demos/` for `Original : \{text\}` returned no matches. `demos/test_presidio.py:89` and `demos/test_presidio_br.py:388` print `len(text)` plus `(conteudo original oculto)`; `demos/reversible_demo.py:58,73,93` print only character counts; `demos/ollama_local_demo.py:88-91` prompt uses `<BR_CPF>` and `<TEXTO_RECLAMACAO>` placeholders. |
| T-01-04-03 | Spoofing | mitigate | CLOSED | `Path('test_presidio.py').exists()`, `test_presidio_br.py`, `reversible_demo.py`, `ollama_local_demo.py` at repo root all return `False`. All four files exist under `demos/`. |
| T-01-04-04 | InfoDisclosure | mitigate | CLOSED | Audit verification used Glob, Grep over source, Bash `Path.exists()` only. No `.env` or `data_sensivel/**` reads were performed. |

## Unregistered Flags

None. SUMMARY.md `## Threat Flags` sections for plans 01-01 through 01-04 each declare `None`. The 01-04 summary notes `demos/ollama_local_demo.py` retains a localhost-only Ollama HTTP call that is pre-existing and not new attack surface; the default prompt now uses masked synthetic placeholders.

## Audit Notes

- Live hook enforcement was incidentally observed: Grep attempts that included `.env`, `data_sensivel`, etc. were blocked by `hooks/pre_tool_guard.py` with `reason=sensitive_glob_or_grep`, providing live evidence that T-01-03-02, T-01-03-03, T-01-03-05, and T-01-02-04 mitigations are also active in execution. Direct file Read of `privguard/policy.py` was used to inspect the regex categories without triggering the path policy.
- Phase 01 implementation is committed only at the plan level (planning artifacts); source files were placed on disk during prior sessions where `.git/index.lock` was not writable. This audit verified the working tree, per the explicit instruction in the prompt.
- The `.claude/settings.json` permission `deny` list (lines 4-24) is an additional defense-in-depth control on top of the hook reason-code policy and was not in scope for the phase 01 threat register but is observed intact.

## Accepted Risks Log

None for phase 01.

## Result

All 17 threats with disposition `mitigate` have verified mitigation evidence in the working tree. No threats remain open.
