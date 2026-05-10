[🇺🇸 English](README.md) | [🇧🇷 Português](README.pt-BR.md)

# privguard

privguard is a local-first Python package that intercepts Brazilian PII and secrets before
they reach external LLM providers such as Anthropic or OpenAI. It runs entirely in your
developer environment — there is no hosted service component. When detection cannot produce
a verified safe payload, privguard fails closed and blocks the prompt rather than letting
sensitive data through.

## Install

```bash
pip install privguard            # baseline (no third-party runtime deps)
pip install "privguard[full]"    # adds Presidio analyzer for richer detection
```

Requires Python ≥ 3.10. For the `[full]` extra's Python 3.14 gating notes, see
[`docs/install.md`](docs/install.md).

## Quickstart

```bash
$ echo "CPF do cliente: 123.456.789-09" | privguard mask
CPF do cliente: <BR_CPF>

$ echo "CNPJ da empresa: 12.345.678/0001-95" | privguard mask
CNPJ da empresa: <BR_CNPJ>

$ echo "token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890" | privguard mask
token: <TOKEN>
```

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

<!-- TODO: filled by Task 2 -->

## Synthetic-fixture-only policy

<!-- TODO: filled by Task 2 -->

## FAQ

<!-- TODO: filled by Task 2 -->

## For coding agents

<!-- TODO: filled by Task 2 -->
