[🇺🇸 English](README.md) | [🇧🇷 Português](README.pt-BR.md)

# privguard

privguard is a local-first Python package that intercepts Brazilian PII and secrets before
they reach external LLM providers such as Anthropic or OpenAI. It runs entirely in your
developer environment — there is no hosted service component. When detection cannot produce
a verified safe payload, privguard fails closed and blocks the prompt rather than letting
sensitive data through.

The initial focus is Brazilian sensitive data: CPF, CNPJ, CNH, bank/account data, API keys,
environment variables, credentials, and local sensitive files. The package acts locally at
the agent boundary (Claude Code `UserPromptSubmit` + `PreToolUse`) to prevent sensitive data
from leaving the machine.

## Install

```bash
pip install privguard            # baseline (no third-party runtime deps)
pip install "privguard[full]"    # adds Presidio analyzer for richer detection
```

Requires Python ≥ 3.10. For the `[full]` extra's Python 3.14 gating notes, see
[`docs/install.md`](docs/install.md).

## Quickstart

After installing, pipe any text through `privguard mask` to replace detected sensitive
values with typed placeholders. privguard never modifies the original source — it prints
the masked output to stdout and exits:

```bash
$ echo "CPF do cliente: 123.456.789-09" | privguard mask
CPF do cliente: <BR_CPF>

$ echo "CNPJ da empresa: 12.345.678/0001-95" | privguard mask
CNPJ da empresa: <BR_CNPJ>

$ echo "token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890" | privguard mask
token: <TOKEN>
```

The placeholders follow the Phase 2 vocabulary: `<BR_CPF>` for Brazilian CPF,
`<BR_CNPJ>` for CNPJ, `<TOKEN>` for GitHub personal access tokens and similar
secret-shaped strings. The masking is irreversible — v1 does not persist a
deanonymization map.

All values shown above are synthetic test fixtures — see
[Synthetic-fixture-only policy](#synthetic-fixture-only-policy).

## CLI usage

```bash
privguard info             # version + module surface
privguard scan <text>      # detection only — entity types, counts, offsets, reason codes
privguard mask <text>      # detection + irreversible placeholder substitution
privguard policy-check     # decide whether a payload may leave (fail-closed default)
privguard claude doctor    # Claude hook installation + effective-policy diagnostics
privguard cleanup          # dry-run preview of cleanable artifacts (use --apply to delete)
```

Run any subcommand with `--help` to see all flags.

Key behaviors:

- `privguard scan` and `privguard mask` read from stdin when no positional argument is given.
- `privguard policy-check` is fail-closed by default: unknown or unclassified provider targets
  are treated as external and require verified masking.
- `privguard cleanup` is dry-run by default. Pass `--apply` to actually delete. The
  hardcoded protected list (`.env`, `data_sensivel/`, `.git/`, source directories) is always
  respected, regardless of which patterns appear in `pyproject.toml`.
- `privguard claude doctor` does not read any protected file — it inspects hook metadata only.

## Claude Code hook setup

After installing privguard, wire two hooks into your Claude Code project's
`.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "privguard-user-prompt" }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          { "type": "command", "command": "privguard-pre-tool" }
        ]
      }
    ]
  }
}
```

These two console scripts ship with `pip install privguard` (declared in
`pyproject.toml [project.scripts]`). They are install-path-independent — Claude Code finds
them on `PATH` after install.

Verify your installation with `privguard claude doctor` — it reports whether the hooks are
wired without reading any protected file.

## Capabilities matrix

Privacy interception status by surface (Phase 3 + Phase 4 evidence):

| Surface | Status | Notes |
|---|---|---|
| Claude Code `UserPromptSubmit` | block-supported | Phase 3 verified |
| Claude Code `PreToolUse` | block-supported | Phase 3 verified |
| Codex prompt hook | experimental block-only | Phase 4 evidence |
| Codex tool hook | experimental block-only | Phase 4 evidence |

For full evidence and remaining gaps, see
[`docs/codex-compatibility.md`](docs/codex-compatibility.md).

## What privguard does NOT do

privguard is a focused, local-first tool. It deliberately does NOT:

- **Run as a hosted SaaS or cloud proxy.** The privacy boundary stays on your machine; raw data never leaves it via privguard.
- **Deanonymize masked output (no deanonymization surface).** v1 uses irreversible masking — there is no key-management or retention surface to reverse a `<BR_CPF>` placeholder back to the original.
- **Adapt to LangChain, LlamaIndex, or generic SDK pipelines.** The supported integration is Claude Code (`block-supported`); Codex is `experimental block-only`. See [Capabilities matrix](#capabilities-matrix).
- **Protect unsupported clients.** Clients without tested interception (no documented hook event, no synthetic interception proof) are not labeled as protected — they are labeled `unsupported`.
- **Use real Brazilian PII or production secrets in tests, fixtures, examples, or commits.** Every value in this repository's tests is synthetic. See [Synthetic-fixture-only policy](#synthetic-fixture-only-policy).

## Synthetic-fixture-only policy

privguard's test suite, code examples, and documentation use only synthetic Brazilian identifiers and synthetic secret-shaped strings. The synthetic CPF, CNPJ, and CNH values shown in [Quickstart](#quickstart) come from `tests/test_v1_regression_gate.py` and are checksum-valid but obviously fabricated.

We do this because real PII in a public repo would reproduce the exfiltration risk privguard is built to prevent. The repository's `.gitignore` and the cleanup tool's hardcoded `_PROTECTED` list (in `privguard/cleanup.py`) treat `.env`, `data_sensivel/`, and the Brazilian-flagged paths as untouchable.

If you contribute a test, fixture, or example, use the existing constants in `tests/test_v1_regression_gate.py` rather than inventing new values — that file is the single source of truth for synthetic fixtures.

## FAQ

### Does this work with Codex?

Codex hooks are labeled `experimental block-only` in the [Capabilities matrix](#capabilities-matrix) — privguard can block sensitive prompts and tool payloads, but does not claim Codex masking — only blocking. The supporting evidence and remaining gaps are documented in [`docs/codex-compatibility.md`](docs/codex-compatibility.md). Treat Codex protection as best-effort blocking until outbound payload replacement is proven.

### What if a CPF is missed?

privguard's detection is fail-closed by design — when a CPF (or any PII) cannot be confidently masked, the hook blocks the prompt rather than letting it through. If you suspect a missed CPF, run `privguard claude doctor` to verify hook installation and effective policy, and `privguard scan "<text>"` to see what the detector sees. privguard is one layer of defense, not a guarantee of 100% recall.

### Why does it block instead of warn?

Warning-only mode is explicitly out of scope (see [What privguard does NOT do](#what-privguard-does-not-do)). The core value of privguard is preventing sensitive data from reaching an external LLM provider — a warning that the user can ignore would not satisfy that goal. Strict fail-closed behavior is the default for external-provider workflows; rewrite is only used on surfaces where outbound payload replacement is verified.

### How do I extend the cleanup patterns?

Add the new pattern to `[tool.privguard.cleanup]` in `pyproject.toml`, AND add the same pattern to `.gitignore` so transient artifacts cannot be committed before the next cleanup run. The trailing-slash convention matters: `__pycache__/` matches a directory tree recursively; `*.py[cod]` matches files by basename glob.

```toml
[tool.privguard.cleanup]
patterns = [
    "__pycache__/",
    "*.py[cod]",
    # ...your new pattern here...
]
```

The cleanup tool reads this list at runtime; the hardcoded protected list (`.env`, `data_sensivel/`, source dirs) cannot be overridden.

## For coding agents

For coding agents working in this repo, see [AGENTS.md](AGENTS.md).

`AGENTS.md` documents the project structure, coding conventions, protected paths, and
safety contracts that apply when an AI agent modifies this codebase. Key rules agents
must observe:

- Never read or write `.env`, `data_sensivel/`, or any path in the hardcoded `_PROTECTED`
  list in `privguard/cleanup.py`.
- Use only synthetic fixtures from `tests/test_v1_regression_gate.py` in tests, examples,
  and documentation — never invent new Brazilian PII values.
- Follow the fail-closed pattern: when in doubt about a surface capability, block rather
  than allow.
