<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![CI][ci-shield]][ci-url]
[![Python][python-shield]][python-url]
[![License][license-shield]][license-url]

[🇧🇷 Português](README.md) | [🇺🇸 English](README.en.md)

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/ericksjct/privguard">
    <img src="privguard_thumb.png" alt="privguard" width="520">
  </a>

  <h3 align="center">privguard</h3>

  <p align="center">
    Local-first guard that stops Brazilian PII and secrets from leaking to external LLMs.
    <br />
    <a href="docs/install.md"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/ericksjct/privguard/issues/new?labels=bug">Report Bug</a>
    &middot;
    <a href="https://github.com/ericksjct/privguard/issues/new?labels=enhancement">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#quickstart">Quickstart</a></li>
        <li><a href="#cli">CLI</a></li>
        <li><a href="#claude-code-hook">Claude Code hook</a></li>
        <li><a href="#what-privguard-catches">What it catches</a></li>
        <li><a href="#what-privguard-does-not-catch-by-default">What it does not catch</a></li>
        <li><a href="#fail-closed-behavior">Fail-closed behavior</a></li>
        <li><a href="#capabilities-matrix">Capabilities matrix</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->
## About The Project

privguard is a local-first Python package that intercepts Brazilian personal data (PII) and
secrets before they reach external LLM providers such as Anthropic or OpenAI. It runs entirely
in your development environment — there is no hosted service component. When detection cannot
produce a verified safe payload, privguard fails closed and blocks the prompt rather than letting
sensitive data through.

The initial focus is Brazilian sensitive data: CPF, CNPJ, CNH, bank and account data, API keys,
environment variables, credentials, and local sensitive files. The package acts locally at the
agent boundary (Claude Code `UserPromptSubmit` + `PreToolUse`) to keep sensitive data on the machine.

Why it exists:

* **Zero clear-text leakage** to external providers is the core value — not a side effect.
* **Fail-closed by default** — when in doubt, block. A detector failure or hostile input blocks, never silently allows.
* **Synthetic fixtures only** — real PII never enters tests, examples, or commits.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

[![Python][python-badge]][python-url]
[![Presidio][presidio-badge]][presidio-url]
[![spaCy][spacy-badge]][spacy-url]

The base detection path is stdlib-only (no third-party runtime dependencies). The `[full]` extra
adds Microsoft Presidio + spaCy for richer detection.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

Python ≥ 3.10. For `[full]` extra compatibility notes on Python 3.14, see
[`docs/install.md`](docs/install.md).

### Installation

```bash
pip install privguard            # base install (no third-party runtime dependencies)
pip install "privguard[full]"    # adds the Presidio analyzer for richer detection
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->
## Usage

### Quickstart

After installing, pipe any text to `privguard mask` to replace detected sensitive values with
typed placeholders. privguard never modifies the original source — it prints the masked output
to stdout and exits:

```bash
$ echo "Customer CPF: 123.456.789-09" | privguard mask
Customer CPF: <BR_CPF>

$ echo "Company CNPJ: 12.345.678/0001-95" | privguard mask
Company CNPJ: <BR_CNPJ>

$ echo "token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890" | privguard mask
token: <TOKEN>
```

Placeholders follow the Phase 2 vocabulary: `<BR_CPF>` for Brazilian CPF, `<BR_CNPJ>` for CNPJ,
`<TOKEN>` for GitHub personal access tokens and similar secret-shaped strings. Masking is
irreversible — v1 does not persist a deanonymization map. Every value above is a synthetic test fixture.

### CLI

```bash
privguard info             # version + module surface
privguard scan <text>      # detection only — entity types, counts, offsets, reason codes
privguard mask <text>      # detection + irreversible placeholder replacement
privguard policy-check     # decides whether a payload may leave (fail-closed default)
privguard claude doctor    # Claude hook installation + effective policy diagnostic
privguard cleanup          # dry-run preview of cleanable artifacts (use --apply to delete)
```

Run any subcommand with `--help` for all flags. Key behaviors:

* `privguard scan` and `privguard mask` read from stdin when no positional argument is given.
* `privguard policy-check` is fail-closed by default: unknown or unclassified provider targets are
  treated as external and require verified masking.
* `privguard cleanup` is dry-run by default. Pass `--apply` to actually delete. The hardcoded
  protected list (`.env`, `data_sensivel/`, `.git/`, source directories) is always respected,
  regardless of the patterns in `pyproject.toml`.
* `privguard claude doctor` reads no protected file — it inspects only hook metadata.

### Claude Code hook

After installing privguard, configure two hooks in your Claude Code project's
`.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "privguard-user-prompt" } ] }
    ],
    "PreToolUse": [
      { "matcher": ".*", "hooks": [ { "type": "command", "command": "privguard-pre-tool" } ] }
    ]
  }
}
```

These two console scripts are installed by `pip install privguard` (declared in
`pyproject.toml [project.scripts]`) and are install-path independent — Claude Code finds them on
`PATH`. Verify with `privguard claude doctor`, which reports whether the hooks are configured
without reading any protected file.

### What privguard catches

Everything below is **proven output**, not a wishlist. It is the literal result of piping a
synthetic-fixture file through `privguard mask` at default settings (strict mode), reproducible
with the test suite in `tests/test_detection.py`:

```text
CPF 123.456.789-09                      →  CPF <BR_CPF>
CNPJ 12.345.678/0001-95                 →  CNPJ <BR_CNPJ>
CNH 12345678900                         →  CNH <BR_CNH>
PIS 123.45678.90-0                      →  PIS <BR_PIS_PASEP>
SUS 123 4567 8901 2348                  →  SUS <BR_CARTAO_SUS>
RG 12.345.678-9                         →  RG <BR_RG>
mobile +55 (11) 91234-5678              →  mobile <BR_PHONE>
CEP 01310-200                           →  CEP <BR_CEP>
plate ABC-1234 and BRA1A23              →  plate <BR_PLACA_OLD> and <BR_PLACA_MERCOSUL>
api_key=sk-test-abcdefghij...           →  api_key=<API_KEY>
token ghp_ABCDEFGHIJ...                 →  token <TOKEN>
DATABASE_URL=postgres://user:pass@...   →  DATABASE_URL=<DATABASE_URL>
email contact@example.com.br            →  email <EMAIL>
```

Also detected by the same engine and covered by `tests/test_detection.py`: IBAN (including
space-separated), boleto barcodes (`<BR_BOLETO>`), bank agency and account, addresses, voter
title, private/public IPs, Luhn-valid credit cards, AWS keys, JWTs, and `KEY=`/`SECRET=`/`PASSWORD=`
assignments.

Brazilian identifiers are validated by their **checksum** before masking — a random 11-digit
string is not treated as a CPF. That is what keeps false positives low; it is also the source of
the deliberate gaps below.

### What privguard does NOT catch (by default)

These are not bugs — they are documented, tested limits. The first two **pass through** unless you
explicitly opt in:

| Input (synthetic) | Strict mode (default) | Opt-in |
|---|---|---|
| `Maria Silva` (a person's name) | `Maria Silva` — **not masked** | `PII_GUARD_DETECT_NAMES=true` → `<BR_NAME>` |
| `456.789.123-45` (CPF with invalid checksum) | `456.789.123-45` — **not masked** | `PII_GUARD_LENIENT=true` → `<BR_CPF>` |
| `45678912345` (raw 11 digits, no dots/dash) | not masked as CPF | stays strict even in lenient mode (format guard) |

* **Names are off by default** because free-text name matching produces too many false positives to
  enable globally. Turn it on with `PII_GUARD_DETECT_NAMES=true`.
* **Invalid-checksum identifiers are off by default** because strict validation is what keeps
  everyday numbers from being masked by mistake. They only mask under `PII_GUARD_LENIENT=true`, and
  even then only the **punctuated** form `DDD.DDD.DDD-DD`.
* **Codex masking is not offered** — Codex is `experimental block-only`. privguard blocks sensitive
  Codex payloads but does not rewrite them.

privguard **does not guarantee detection against a deliberate obfuscator**. It is a local scanner
that raises the cost of accidental and low-effort evasion. Detection resists homoglyphs,
zero-width/combining characters, fragmentation and concatenation of checksum-bearing identifiers,
and single-layer encoded secrets (base64/hex/URL). It does **not** cover, by design: runtime
interpolation (`f"{cpf}"` only assembles at execution, not in the text), multi-layer encoding, and
numeric identifiers hidden inside encoded content.

### Fail-closed behavior

Fail-closed is the default even when something goes wrong inside the guard itself:

* **Detector error:** if detection raises an exception, the hook blocks (exit code 2) with
  `reason=detector_error` — never a silent allow.
* **Oversized input:** prompts and commands above a character limit are blocked with
  `reason=input_too_large` before being scanned. The default limit is 1,000,000 characters (~1 MB),
  tunable via `PII_GUARD_MAX_INPUT_CHARS`. The cap applies only at the hook boundary; the
  `scan`/`mask` CLI still processes large files normally.

Blocking is the default; the mode is configurable via `PII_GUARD_MODE`:

| Mode | `PII_GUARD_MODE` | Behavior on PII detected | Exit | Protective? |
|------|------------------|--------------------------|------|-------------|
| `block` (default) | unset or `block` | Blocks; sanitized diagnostic to stderr | 2 | Yes (fail-closed) |
| `warn` | `warn` | Lets through; tags `mode_scope=local_development_non_protective` | 0 | **No** — opt-in |
| `mask` | `mask` | Blocks (exit 2) and shows a masked version in stderr for manual resubmission | 2 | Yes |

The `warn` mode is **explicitly non-protective** (local dev). The `mask` mode never auto-forwards a
sanitized payload — Claude Code's `UserPromptSubmit` schema has no prompt-replacement field, so
blocking and printing the masked version is the only safe path.

### Capabilities matrix

Privacy interception status per surface (Phase 3 + Phase 4 evidence):

| Surface | Status | Notes |
|---|---|---|
| Claude Code `UserPromptSubmit` | block-supported | Verified in Phase 3 |
| Claude Code `PreToolUse` | block-supported | Verified in Phase 3 |
| Codex prompt hook | experimental block-only | Phase 4 evidence |
| Codex tool hook | experimental block-only | Phase 4 evidence |

For full evidence and remaining gaps, see [`docs/codex-compatibility.md`](docs/codex-compatibility.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ROADMAP -->
## Roadmap

Milestone v1.0 — all phases delivered and verified:

- [x] Package foundation + CLI (`privguard`)
- [x] Privacy core (BR-first detection, irreversible masking, fail-closed policy)
- [x] Claude Code enforcement (`UserPromptSubmit` + `PreToolUse`)
- [x] Codex compatibility evidence (honestly labeled)
- [x] Synthetic regression gate + detection hardening
- [x] Fail-closed hardening (detector error, oversized input, ReDoS, evasion) — verified
- [ ] Automatic masking via `updatedInput` on `PreToolUse` (rewrite surface)
- [ ] Hook E2E, legacy encoding (cp1252), config precedence (v1.1 backlog)

See [open issues](https://github.com/ericksjct/privguard/issues) for the full backlog.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open-source community such an amazing place to learn and create.
Any contributions you make are **greatly appreciated**.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-thing`)
3. Run the suite with the coverage gate (`python -m pytest`)
4. Commit (`git commit -m 'feat: add amazing thing'`)
5. Push to the branch (`git push origin feature/amazing-thing`)
6. Open a Pull Request

**Non-negotiable rule — synthetic fixtures only:** never use real Brazilian PII or production
secrets in tests, examples, or commits. Use the existing constants in
`tests/test_v1_regression_gate.py` — that file is the single source of truth for synthetic
fixtures. The `.gitignore` and the cleanup tool's `_PROTECTED` list treat `.env`, `data_sensivel/`,
and Brazilian-flagged paths as untouchable.

See [AGENTS.md](AGENTS.md) for project structure, conventions, and the security contracts that
apply when an AI agent modifies this codebase.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->
## License

Distributed under the Apache License 2.0. See [`LICENSE`](LICENSE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->
## Contact

ericksjct — via [GitHub issues](https://github.com/ericksjct/privguard/issues)

Project link: [https://github.com/ericksjct/privguard](https://github.com/ericksjct/privguard)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Microsoft Presidio](https://github.com/microsoft/presidio) — PII detection on the `[full]` path
* [spaCy](https://spacy.io) — Portuguese language models
* [Best-README-Template](https://github.com/othneildrew/Best-README-Template) — structure of this README
* [Shields.io](https://shields.io) — badges

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
[ci-shield]: https://img.shields.io/github/actions/workflow/status/ericksjct/privguard/ci.yml?style=for-the-badge
[ci-url]: https://github.com/ericksjct/privguard/actions/workflows/ci.yml
[python-shield]: https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white
[python-url]: https://www.python.org/
[license-shield]: https://img.shields.io/badge/license-Apache%202.0-green?style=for-the-badge
[license-url]: LICENSE
[python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[presidio-badge]: https://img.shields.io/badge/Microsoft%20Presidio-0078D4?style=for-the-badge&logo=microsoft&logoColor=white
[presidio-url]: https://github.com/microsoft/presidio
[spacy-badge]: https://img.shields.io/badge/spaCy-09A3D5?style=for-the-badge&logo=spacy&logoColor=white
[spacy-url]: https://spacy.io
