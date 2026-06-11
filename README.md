<p align="center">
  <img src="privguard_thumb.png" alt="privguard" width="100%">
</p>

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

## What privguard catches

Everything below is **proven output**, not a wish list. This is the verbatim result of
piping a synthetic fixture file through `privguard mask` on the default (strict) settings —
reproducible with the test suite in `tests/test_detection.py` (85 passing detection/masking
tests):

```text
CPF 123.456.789-09                      →  CPF <BR_CPF>
CNPJ 12.345.678/0001-95                 →  CNPJ <BR_CNPJ>
CNH 12345678900                         →  CNH <BR_CNH>
PIS 123.45678.90-0                      →  PIS <BR_PIS_PASEP>
SUS 123 4567 8901 2348                  →  SUS <BR_CARTAO_SUS>
RG 12.345.678-9                         →  RG <BR_RG>
celular +55 (11) 91234-5678             →  celular <BR_PHONE>
CEP 01310-200                           →  CEP <BR_CEP>
placa ABC-1234 e BRA1A23                →  placa <BR_PLACA_OLD> e <BR_PLACA_MERCOSUL>
api_key=sk-test-abcdefghij...           →  api_key=<API_KEY>
token ghp_ABCDEFGHIJ...                 →  token <TOKEN>
DATABASE_URL=postgres://user:pass@...   →  DATABASE_URL=<DATABASE_URL>
email contato@exemplo.com.br            →  email <EMAIL>
```

Also detected by the same pattern engine and covered by `tests/test_detection.py`:
IBAN (`<IBAN>`, including space-separated), boleto barcodes (`<BR_BOLETO>`), bank agency and
account references (`<BR_BANK_AGENCY>`, `<BR_BANK_ACCOUNT>`), street addresses (`<BR_ADDRESS>`),
título de eleitor (`<BR_TITULO_ELEITOR>`), private/public IPs (`<IP_PRIVADO>`, `<IP_PUBLICO>`),
credit-card numbers that pass the Luhn check (`<CREDIT_CARD>`), AWS keys (`<AWS_KEY>`), JWTs
(`<JWT>`), and `KEY=`, `SECRET=`, `PASSWORD=` style assignments.

Brazilian identifiers (CPF, CNPJ, CNH, título, PIS/PASEP, cartão SUS) are validated by their
**checksum** before masking — a random 11-digit string is not treated as a CPF. This is what
keeps false positives low; it is also the source of the deliberate gaps below.

## What privguard does NOT catch (by default)

These are not bugs — they are documented, tested limits. The first two **pass through
untouched** unless you explicitly opt in:

| Input (synthetic) | Default strict mode | Opt-in |
|---|---|---|
| `Maria Silva` (a person's name) | `Maria Silva` — **not masked** | `PII_GUARD_DETECT_NAMES=true` → `<BR_NAME>` |
| `456.789.123-45` (CPF with an invalid checksum) | `456.789.123-45` — **not masked** | `PII_GUARD_LENIENT=true` → `<BR_CPF>` |
| `45678912345` (bare 11-digit, no dots/dash) | not masked as CPF | stays strict even in lenient mode (format guard) |

Why each gap exists:

- **Names are off by default** because free-text name matching produces too many false
  positives to enable globally. Turn it on with `PII_GUARD_DETECT_NAMES=true` when your
  payloads are name-heavy.
- **Invalid-checksum identifiers are off by default** because strict checksum validation is
  what keeps everyday numbers from being mis-masked. Synthetic or typo'd CPFs (common in test
  data) only mask under `PII_GUARD_LENIENT=true`, and even then only the **formatted**
  `DDD.DDD.DDD-DD` shape — never a bare run of 11 digits, which would shadow CNH and PIS/PASEP.
- **Codex masking is not provided at all** — Codex is `experimental block-only`. privguard can
  block sensitive Codex payloads but does not rewrite them. See [Capabilities matrix](#capabilities-matrix).

privguard targets Brazilian PII and secret-shaped strings. It is one layer of defense with
fail-closed blocking on supported surfaces — not a guarantee of 100% recall on arbitrary text.

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
