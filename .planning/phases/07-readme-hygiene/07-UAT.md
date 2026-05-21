---
status: resolved
phase: 07-readme-hygiene
source: [07-01-SUMMARY.md, 07-02-SUMMARY.md, 07-03-SUMMARY.md]
started: 2026-05-10T20:00:00Z
updated: 2026-05-21T19:55:00Z
---

## Current Test

[testing complete]

## Tests

### 1. privguard cleanup dry-run (default)
expected: Run `privguard cleanup` (no flags) from repo root. Lists files matching cleanup patterns from pyproject.toml but deletes nothing. Shows a dry-run notice. Exit code 0.
result: pass

### 2. privguard cleanup protected file never deleted
expected: With `privguard cleanup --apply`, a file like `.env` is never deleted even if it matches a pattern. The stderr output shows `[CLEANUP] .env reason=protected`. No protected file is removed.
result: issue
reported: "Footer 'Run with --apply to delete.' appears in --apply output — it should only show in dry-run mode."
severity: minor

### 3. privguard cleanup repo-root guard
expected: Running `privguard cleanup` from inside a subdirectory (e.g., `cd src; privguard cleanup`) exits with code 2 and prints an error indicating it must be run from repo root.
result: pass

### 4. Console scripts available
expected: After `pip install -e .`, both `privguard-user-prompt` and `privguard-pre-tool` are available as runnable commands (e.g., `privguard-user-prompt --help` works without "command not found" error).
result: issue
reported: "privguard-user-prompt --help produces no output. Command exists (no 'command not found') but --help flag is not implemented."
severity: minor

### 5. README.md structure and content
expected: Open `README.md` at repo root. Line 1 is the cross-language switcher (`[🇺🇸 English](README.md) | [🇧🇷 Português](README.pt-BR.md)`). The file contains all 9 required sections: Install, Quickstart (with `<BR_CPF>`/`<BR_CNPJ>`/`<TOKEN>` placeholders), CLI usage (6 subcommands), Claude Code hook setup (with `privguard-user-prompt`/`privguard-pre-tool` snippet), Capabilities matrix (block-supported / experimental block-only rows), What privguard does NOT do, Synthetic-fixture-only policy, FAQ (4 Q&A entries), For coding agents (AGENTS.md link).
result: pass

### 6. README.pt-BR.md Portuguese translation
expected: Open `README.pt-BR.md` at repo root. Line 1 is the same cross-language switcher. All 9 sections from README.md appear translated in Brazilian Portuguese (e.g., "Instalação", "Início rápido", "Uso da CLI", "Configuração do hook", "Matriz de capacidades", etc.). The same `<BR_CPF>`, `<BR_CNPJ>`, `<TOKEN>` placeholders and `privguard-user-prompt`/`privguard-pre-tool` snippets appear unchanged.
result: pass

### 7. Test suite still passes
expected: Running `uv run pytest` from repo root passes with no regressions. Expected: 139 passed, 1 skipped (Windows symlink test), 0 failed.
result: pass

## Summary

total: 7
passed: 5
issues: 2
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "privguard cleanup --apply should not print 'Run with --apply to delete.' footer"
  status: resolved
  reason: "Fixed in abc3c72 — strip footer from apply output via .replace()"
  severity: minor
  test: 2
  artifacts: [privguard/cleanup.py]
  missing: []

- truth: "privguard-user-prompt and privguard-pre-tool should respond to --help"
  status: resolved
  reason: "Fixed in abc3c72 — added --help/-h handler before stdin.read() in both main functions"
  severity: minor
  test: 4
  artifacts: [privguard/hooks.py]
  missing: []
