---
phase: 07
slug: readme-hygiene
status: verified
threats_open: 0
asvs_level: 1
created: 2026-05-10
---

# Phase 07 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| user shell → `privguard cleanup` argv | User-controlled flags (`--apply`); argparse rejects unknown flags with exit 2 (D-14) | `--apply` boolean; cleanup pattern strings via `pyproject.toml` (not argv) |
| `privguard cleanup` → filesystem (read) | Cleanup walks cwd via `os.walk(followlinks=False)`; D-13 refuses symlinks before any read enters matching | repo artifact filenames, directory tree structure; never file contents |
| `privguard cleanup` → filesystem (write/delete) | Write path gated: `--apply` explicit opt-in AND repo-root guard AND not in `_PROTECTED` AND no symlink in tree | repo artifact paths (counts and sizes only in output; never file contents per POL-04) |
| `privguard cleanup` → `pyproject.toml` parse | tomllib reads binary mode; schema validated per Pitfall 2; malformed TOML → exit 2 | cleanup pattern strings (`[tool.privguard.cleanup].patterns`) |
| repo source code → `_PROTECTED` constant | Hardcoded in `privguard/cleanup.py`; cannot be overridden by any `pyproject.toml` entry | one-way protection boundary; no data crossing |
| README reader → installed `privguard` CLI | User copies hook-setup JSON snippet; broken command form silently disables Claude Code prompt protection | CLI command strings (`privguard-user-prompt`, `privguard-pre-tool`) |
| README reader → privguard privacy posture | User reads capabilities matrix to decide whether to trust privguard with sensitive data | capability status strings (`block-supported`, `experimental block-only`) |
| README example code → user shell | User copies masking demo from Quickstart | synthetic fixture strings (never real Brazilian PII) |
| author → public repo | Documentation author writes content that will be publicly visible and indexed | translated prose + locked vocabulary strings |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-07-01 | Tampering | `pyproject.toml` `[tool.privguard.cleanup]` | mitigate | Hardcoded `_PROTECTED` list in `privguard/cleanup.py` (D-09) cannot be shrunk by a malicious PR touching `pyproject.toml`. Verified: `test_cleanup_apply_skips_protected_paths_with_warning` passes — `.env` survives `--apply` with `reason=protected` in stderr. | closed |
| T-07-02 | Tampering / Elevation | symlink in matched directory (e.g. `__pycache__/`) pointing to sibling file | mitigate | D-13: `_has_symlink_in_tree(root)` pre-validates before `shutil.rmtree`; TOCTOU re-check immediately before delete (Pitfall 3). `os.walk(followlinks=False)` guarantees walker never crosses into linked tree. Verified: `test_cleanup_apply_refuses_symlinks` passes (SKIPPED on Windows per admin requirement — by design). | closed |
| T-07-03 | Misuse | Running `privguard cleanup --apply` in an unrelated project | mitigate | D-11 repo-root guard requires both `.git/` directory AND `pyproject.toml` with `[project] name = "privguard"`. Both must hold or script exits 2 before any filesystem walk. Verified: `test_cleanup_exits_2_outside_privguard_repo_root` passes. | closed |
| T-07-04 | Information Disclosure | Cleanup output echoing file contents or sensitive path strings | mitigate | D-10 + Phase 2 POL-04: `_format_dry_run` outputs paths-and-counts only; `_err()` and `_warn()` emit `reason=<code>` sanitized stderr (mirrors `privguard/hooks.py:38`). Verified: `_assert_sanitized` corpus check passes in every test including `test_cleanup_dry_run_output_is_sanitized`. | closed |
| T-07-05 | Denial-of-service / Loss-of-availability | Accidental deletion via missing dry-run safeguard | mitigate | D-12: dry-run is the default action; `--apply` is the explicit opt-in. Verified: `test_cleanup_default_is_dry_run_no_deletion` — `__pycache__/` survives a bare `privguard cleanup` call with exit 0. | closed |
| T-07-06 | Tampering / Misuse | `tomli` shim missing on Python 3.10 → ImportError at runtime | mitigate | D-16: `tomli; python_version < '3.11'` declared in `[project.dependencies]` so pip installs it on 3.10. `try/except ModuleNotFoundError` shim in `privguard/cleanup.py` falls back gracefully. Verified: acceptance grep `grep -F "tomli; python_version < '3.11'" pyproject.toml` passes. | closed |
| T-07-07 | Tampering | Malformed `[tool.privguard.cleanup]` (e.g. `patterns = "string"` instead of list) | mitigate | Pitfall 2 schema validation in `_load_patterns()`: explicit `isinstance(table, dict)`, `"patterns" in table`, `isinstance(patterns, list)`, `all(isinstance(p, str) for p in patterns)` checks before any use. Returns exit 2 on mismatch. | closed |
| T-07-08 | Repudiation | Reduced auditability — cleanup deleted things but no external log | accept | Dry-run preview (D-10) lists every matched path before `--apply` runs; `--apply` echoes the same listing prefixed `[apply] deleting`. No external audit log: v1 is dev-machine tooling, not enterprise audit. Deferred to v2 / ENT-02 per CONTEXT.md "Deferred Ideas". | closed |
| T-07-09 | Elevation of Privilege via OS error | `shutil.rmtree` failure leaves repo in partial state | accept | D-14 returns exit 1 on `--apply` OS error; `[CLEANUP] error: failed to delete ... reason=delete_failed` names the failed path. Partial state is bounded (other matches continue; protected list honored throughout). Hard to test deterministically without simulated filesystem failures; documented constraint. | closed |
| T-07-02-T1 | Tampering / Information Disclosure | Hook-setup JSON snippet in README §4 documenting non-working command form | mitigate | Snippet uses `privguard-user-prompt` and `privguard-pre-tool` (D-15 console scripts), NOT `python -m privguard.hooks.main_user_prompt` (single-file module, not runnable submodule). Verified: positive grep for both console-script names passed; `! grep "python -m privguard.hooks" README.md` passed (07-02-SUMMARY). | closed |
| T-07-02-T2 | Misrepresentation (Spoofing of capability) | Capabilities matrix in README §5 mis-representing Codex status | mitigate | Matrix wording locked by D-06 — only `block-supported` (Claude rows ×2) and `experimental block-only` (Codex rows ×2) appear as status values. Verified: `grep -c "block-supported" >= 2`, `grep -c "experimental block-only" >= 2`, `! grep "rewrite-capable"`, `! grep "automatic masking"` all passed (07-02-SUMMARY). | closed |
| T-07-02-T3 | Information Disclosure (real PII in public docs) | Quickstart code block in README §2 | mitigate | Synthetic fixtures from `tests/test_v1_regression_gate.py:45-47` reused verbatim (TEST-01 / RESEARCH.md). No inline literal CPF/CNPJ in plan text. Acceptance criterion derives verification at runtime from test source. Verified: `SYNTH_CPF` and `SYNTH_CNPJ` from test file confirmed present in README (07-02-SUMMARY). | closed |
| T-07-02-T4 | Spoofing (capability matrix drift from `docs/codex-compatibility.md`) | README capabilities matrix vs. canonical Codex evidence doc | accept | README matrix is a 4-row condensed view; drift possible if `CODEX_COMPATIBILITY` (in `privguard/codex.py`) changes without README update. v1 enforcement is social (D-03 paired-update rule). CI drift check deferred to v2 per CONTEXT.md "Deferred Ideas — Drift-prevention regression test". README links to the canonical doc as authoritative reference. | closed |
| T-07-03-01 | Information Disclosure | `README.pt-BR.md` code examples containing real PII | mitigate | All code examples use the same synthetic fixtures as `README.md` (123.456.789-09 style CPFs, synthetic GHP tokens). Verified: 07-03-SUMMARY confirms `<BR_CPF>`, `<BR_CNPJ>`, `<TOKEN>` present; all acceptance checks passed. | closed |
| T-07-03-02 | Tampering | Locked vocabulary drift in `README.pt-BR.md` translation | mitigate | Action text provides full translated content verbatim. Acceptance criteria grep for all locked strings: `block-supported` ≥ 2, `experimental block-only` ≥ 2, `privguard-user-prompt`, `privguard-pre-tool`, `<BR_CPF>`, `<BR_CNPJ>`, `<TOKEN>`. Verified: all checks passed (07-03-SUMMARY). | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-07-01 | T-07-08 | v1 cleanup is dev-machine tooling; dry-run preview serves as the audit trail. External audit log deferred to v2/ENT-02. | gsd-secure-phase (automated audit) | 2026-05-10 |
| AR-07-02 | T-07-09 | Partial-state risk on OS error is bounded (other matches continue; protected list always honored). Deterministic simulation of filesystem failures excluded from v1 test scope. | gsd-secure-phase (automated audit) | 2026-05-10 |
| AR-07-03 | T-07-02-T4 | Matrix drift between README and `docs/codex-compatibility.md` enforced socially (D-03 paired-update rule). CI drift regression check deferred to v2. README links to the canonical doc. | gsd-secure-phase (automated audit) | 2026-05-10 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-05-10 | 15 | 15 | 0 | gsd-secure-phase (State B — from PLAN + SUMMARY artifacts) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-05-10
