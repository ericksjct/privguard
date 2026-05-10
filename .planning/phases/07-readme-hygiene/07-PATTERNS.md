# Phase 7: Project README + Repo Hygiene - Pattern Map

**Mapped:** 2026-05-08
**Files analyzed:** 7 (4 new, 3 modified)
**Analogs found:** 5 / 7 (2 README files have no in-repo analog by design — `<no-analog>`)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `README.md` (new) | documentation (top-level prose) | static | `<no-analog>` (see "No Analog Found"; mirror tone of `AGENTS.md` + `docs/install.md`) | n/a |
| `README.pt-BR.md` (new) | documentation (top-level prose, pt-BR) | static | `<no-analog>` (see "No Analog Found"; mirror EN twin) | n/a |
| `privguard/cleanup.py` (new) | service module (filesystem CLI logic, stdlib-only) | request-response (argv -> exit code) + file-I/O (read pyproject.toml, walk + delete tree) | `privguard/diagnostics.py` (module exposing pure helpers + a `_load_*` reader called from `cli.py`) — **role match**; structurally similar to `privguard/hooks.py` (single-file module exposing `main_*` callables consumed by an entry point) — **call-shape match** | role-match (best fit: hybrid — `diagnostics.py` for "stdlib-only readers + `_doctor_check`-style validators called by a `cmd_*` wrapper"; `hooks.py` for "module exposes `main()` that returns int and is wired from `pyproject.toml [project.scripts]` / `cli.py`") |
| `tests/test_cleanup.py` (new, recommended) | test (pytest, in-process CLI invocation with synthetic fixtures) | request-response | `tests/test_claude_doctor.py` — exact: subcommand-level test with sanitized-output assertions, exit-code assertions, and reuse of `_assert_sanitized` helper; complemented by `tests/test_cli.py` (per-subcommand `main([...])` call shape) | exact (claude-doctor) + role-match (test_cli) |
| `privguard/cli.py` (modified) | controller (argparse dispatcher) | request-response | itself — extend the existing `subparsers.add_parser(...)` block at lines 108-146 | exact (self-mirror) |
| `pyproject.toml` (modified) | config (PEP 621 + tool table) | static | itself — extend existing `[project.scripts]` (line 23-24) and `[project.optional-dependencies]` (line 16-21); the new `[tool.privguard.cleanup]` table has no in-repo analog (first `[tool.privguard.*]` table) | partial (self-mirror for `[project.scripts]` and dependency-marker syntax; new table is greenfield) |
| `.gitignore` (modified) | config (gitignore patterns) | static | itself — append-only delta of three lines (`dist/`, `build/`, `*.egg-info/`) | exact (self-mirror) |

## Pattern Assignments

### `privguard/cleanup.py` (new — service module, request-response + file-I/O)

**Primary analog:** `privguard/diagnostics.py` (lines 1-12, 105-144, 170-200) — best fit for the "stdlib-only readers + `_check_*` validators called by a `cmd_*` wrapper" pattern.
**Secondary analog:** `privguard/hooks.py` (lines 1-12, 149-190) — for the "module exposes a `main_*()` callable returning `int`" call shape.

**Imports / module header pattern** — copy from `privguard/diagnostics.py` lines 1-11:

```python
"""Sanitized diagnostic serializers for detection, masking, and policy metadata."""

from __future__ import annotations

import json
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any

from .detection import DetectionReport, Hit, detect
from .masking import MaskResult
```

For `cleanup.py` adapt to:
- `from __future__ import annotations` is mandatory (every privguard module uses it — `diagnostics.py:3`, `hooks.py:3`, `cli.py:3`, `policy.py:3`, `codex.py:16`).
- A one-line module docstring at the top (single sentence, lowercase tone matching `diagnostics.py:1`, `policy.py:1`, `hooks.py:1`).
- Stdlib-only imports: `import os`, `import shutil`, `import sys`, `from pathlib import Path`, `import fnmatch`, plus the `tomllib` shim.

**`tomllib` shim pattern (D-16)** — no in-repo analog (first `tomllib` use); RESEARCH.md §"Code Examples" lines 691-696 is the verbatim shim:

```python
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # 3.10 fallback per D-16
    import tomli as tomllib  # type: ignore[no-redef]
```

**Module-level constants pattern** — copy shape from `privguard/diagnostics.py` lines 14-19 (uppercase tuple/string constants at module top, before any function defs):

```python
# Source: privguard/diagnostics.py:14-19
SYNTHETIC_DOCTOR_PROMPT = (
    "Validacao sintetica CPF 123.456.789-09 "
    "token=sk-test-abcdefghijklmnopqrstuvwxyz"
)
SYNTHETIC_DOCTOR_PATH = "data_sensivel/synthetic.csv"
SYNTHETIC_DOCTOR_COMMAND = f"Get-Content {SYNTHETIC_DOCTOR_PATH} | Set-Clipboard"
```

For `cleanup.py` (D-09 hardcoded protected list — module-level tuple constant, single-leading-underscore for "module-private but discoverable"):

```python
_PROTECTED: tuple[str, ...] = (
    ".env", ".env.*", "data_sensivel/", ".planning/", ".git/",
    "privguard/", "tests/", "hooks/", "demos/", "docs/",
    "pyproject.toml", "AGENTS.md", "README.md", "README.pt-BR.md",
)
```

The leading-underscore + frozen-tuple convention matches `privguard/hooks.py:193-210` (`_KNOWN_LOCAL_TOOLS`, `_LLM_ORCHESTRATION_TOOLS`, `_ALLOWED_MCP_PREFIXES`):

```python
# Source: privguard/hooks.py:193-218
_KNOWN_LOCAL_TOOLS = frozenset({...})
_LLM_ORCHESTRATION_TOOLS = frozenset({...})
_ALLOWED_MCP_PREFIXES = (
    "mcp__plugin_mempalace_mempalace__",
    "mcp__ide__",
)
```

**`main(argv)` callable pattern** — copy call shape from `privguard/hooks.py:149-190` (`main_user_prompt`) and `privguard/cli.py:108-146`:

```python
# Source: privguard/hooks.py:149-153 (entry shape) + privguard/cli.py:108-110 (argparse)
# Cleanup is invoked via cli.py's cmd_cleanup wrapper, but exposes
# a public main(argv) so it can also be run as a console script if needed.

def main(argv: list[str] | None = None) -> int:
    # ... 1. repo-root guard (D-11) -> raise SystemExit(2) on failure ...
    # ... 2. read [tool.privguard.cleanup].patterns via tomllib shim ...
    # ... 3. build candidate set via os.walk(followlinks=False) ...
    # ... 4. dry-run preview OR --apply branch ...
    return 0  # or 1 (delete failure) or 2 (misuse)
```

The function-returns-`int` exit-code convention is consistent across `cli.py:23` (`cmd_info`), `cli.py:41` (`cmd_scan`), `cli.py:75` (`cmd_policy_check`), `cli.py:99` (`cmd_claude_doctor`), `hooks.py:149` (`main_user_prompt`), `hooks.py:246` (`main_pre_tool`).

**Repo-root guard via `tomllib`** (D-11) — no in-repo analog (first `tomllib` call); RESEARCH.md §"Pattern 2" lines 366-385 is the verified pattern. Copy verbatim, exit code 2 with `sys.stderr.write` matching the `hooks.py:16` and `hooks.py:38` sanitized-error style:

```python
# Source: privguard/hooks.py:14-17 (sys.stderr error format)
def deny(prefix: str, reason_code: str) -> int:
    sys.stderr.write(f"[{prefix} BLOQUEADO] reason={reason_code}\n")
    return 2
```

For `cleanup.py` repo-root-guard error messages, mirror this format (paths-only, no contents, no traceback) — example: `sys.stderr.write("[CLEANUP] error: not in privguard repo root reason=missing_git_dir\n")`.

**Sanitized output pattern (D-10 + Phase 2 POL-04)** — copy the "paths and counts only, never contents" rule already implemented in `privguard/diagnostics.py:84-102` (`format_text`):

```python
# Source: privguard/diagnostics.py:84-102
def format_text(value: Any) -> str:
    data = to_dict(value)
    if isinstance(data, dict) and "counts" in data:
        counts = data.get("counts") or {}
        total = sum(int(count) for count in counts.values())
        return f"detections={total} counts={counts}"
    # ...
    return str(data)
```

The dry-run formatter for `cleanup.py` follows the same shape: build a dict of `(pattern, [paths], total_bytes)` rows, render to a single multi-line string, never echo file contents. RESEARCH.md §"D-10" lines 71-78 fixes the exact dry-run format.

**Schema validation on `[tool.privguard.cleanup]`** (Pitfall 2) — no exact in-repo analog; closest pattern is the defensive `isinstance` checks in `privguard/diagnostics.py:142-144` (`_load_claude_settings`):

```python
# Source: privguard/diagnostics.py:135-144
try:
    with Path(settings_path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
except FileNotFoundError:
    return {}, ["settings_missing"]
except (OSError, json.JSONDecodeError, ValueError):
    return {}, ["settings_unreadable"]
if not isinstance(data, dict):
    return {}, ["settings_invalid"]
return data, []
```

Mirror this for `pyproject.toml` reading (binary-mode open per tomllib API, isinstance-check the result, exit 2 on schema mismatch — RESEARCH.md §"Pitfall 2" lines 569-581 has the exact check sequence).

**Symlink-refusing delete pattern (D-13)** — no in-repo analog (no existing privguard module deletes files); RESEARCH.md §"Pattern 4" lines 421-443 is the verified pattern. The convention to mirror from privguard idioms: use `os.walk(root, followlinks=False)` (default) and re-check `is_symlink()` immediately before `shutil.rmtree` to close the TOCTOU window (Pitfall 3, RESEARCH.md lines 588-611).

---

### `privguard/cli.py` (modified — controller, request-response)

**Analog:** `privguard/cli.py` itself, lines 108-146 — extend the same `subparsers.add_parser(...)` block.

**Existing `cmd_*` wrapper pattern** (lines 41-47, 50-72, 75-96, 99-105):

```python
# Source: privguard/cli.py:99-105 (closest exit-code pattern to cleanup)
def cmd_claude_doctor(args: argparse.Namespace) -> int:
    report = build_claude_doctor_report(args.settings)
    if args.json:
        print(to_json(report))
    else:
        print(format_claude_doctor_text(report))
    return 0 if claude_doctor_passed(report) else 2
```

For `cmd_cleanup`, copy this shape — thin wrapper that delegates to `privguard.cleanup.main(args)` and returns its int. Suggested form:

```python
# New in privguard/cli.py — mirrors cmd_claude_doctor:99-105
from .cleanup import main as cleanup_main  # add to existing imports at top

def cmd_cleanup(args: argparse.Namespace) -> int:
    return cleanup_main(args)
```

**Subparser registration** (lines 115-143 — copy the `mask` / `policy` shape):

```python
# Source: privguard/cli.py:115-118 (closest single-flag-no-positional pattern)
mask = subparsers.add_parser("mask")
mask.add_argument("text", nargs="?")
mask.add_argument("--json", action="store_true")
mask.set_defaults(func=cmd_mask)
```

For `cleanup` (D-07, D-12, RESEARCH.md §"Pattern 1" lines 339-353):

```python
# New — register inside main() alongside scan/mask/policy/claude
cleanup = subparsers.add_parser("cleanup")
cleanup.add_argument(
    "--apply",
    action="store_true",
    help="Actually delete (default is dry-run preview).",
)
cleanup.set_defaults(func=cmd_cleanup)
```

Optional flags (`--verbose`, `--dry-run` alias, `--quiet`) are at planner discretion (D-04 / Claude's Discretion); use the `action="store_true"` shape verbatim. The dispatcher at `cli.py:145-146` (`args.func(args)`) requires no change.

**Import block** — extend the existing import block at lines 9-20 by adding one line:

```python
# Source: privguard/cli.py:9-20 — add the cleanup import in the same style
from .cleanup import main as cleanup_main  # OR: from . import cleanup
```

Match the existing relative-import-with-`from .module import ...` style (every other CLI import is relative).

---

### `tests/test_cleanup.py` (new — test, request-response)

**Primary analog:** `tests/test_claude_doctor.py` (lines 1-80) — exact match for "subcommand-level test with sanitized-output assertions, exit-code assertions, JSON-vs-text mode coverage, FORBIDDEN_OUTPUT helper".

**Secondary analog:** `tests/test_cli.py` (lines 1-145) — for the "per-subcommand `main(["..."])` call-and-assert" minimal shape.

**Imports + synthetic constants pattern** — copy from `tests/test_claude_doctor.py:1-28`:

```python
# Source: tests/test_claude_doctor.py:1-28
from __future__ import annotations

import json
from pathlib import Path

import pytest

from privguard.cli import main


SYNTHETIC_CPF = "123.456.789-09"
SYNTHETIC_SECRET = "sk-test-abcdefghijklmnopqrstuvwxyz"
SYNTHETIC_PROTECTED_PATH = "data_sensivel/synthetic.csv"
SYNTHETIC_ENV_PATH = ".env"
SYNTHETIC_PROMPT = f"CPF {SYNTHETIC_CPF} token={SYNTHETIC_SECRET}"
SYNTHETIC_COMMAND = f"Get-Content {SYNTHETIC_PROTECTED_PATH} | Set-Clipboard"


FORBIDDEN_OUTPUT_VALUES = (
    SYNTHETIC_CPF,
    SYNTHETIC_SECRET,
    SYNTHETIC_PROTECTED_PATH,
    SYNTHETIC_ENV_PATH,
    SYNTHETIC_PROMPT,
    SYNTHETIC_COMMAND,
    "<BR_CPF>",
    "<TOKEN>",
)


def _assert_sanitized(rendered: str) -> None:
    for value in FORBIDDEN_OUTPUT_VALUES:
        assert value not in rendered
```

For `test_cleanup.py`, mirror this header but reuse the same fixtures (synthetic CPF / paths) — DO NOT invent new ones (Phase 5 TEST-01 + RESEARCH.md §"Existing synthetic fixtures to reuse" lines 853-870). The cleanup tests don't need any synthetic CPF/CNPJ values to exercise the cleanup CLI (cleanup operates on path strings), but reusing the FORBIDDEN-OUTPUT corpus inoculates against future leakage if a path ever contained one.

**Test function pattern** — copy from `tests/test_claude_doctor.py:36-62` (JSON mode + sanitized assertion + exit-code assertion):

```python
# Source: tests/test_claude_doctor.py:36-62
def test_claude_doctor_json_passes_with_synthetic_checks(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["claude", "doctor", "--json"]) == 0

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    payload = json.loads(captured.out)

    assert payload["command"] == "claude doctor"
    assert payload["synthetic_data"] is True
    assert captured.err == ""
    # ... per-check assertions ...
    _assert_sanitized(rendered)
```

For `test_cleanup.py`, the four irreducible safety contracts from RESEARCH.md Open Question #3 each need a test mirroring this shape (`assert main([...]) == EXPECTED_EXIT_CODE` + `_assert_sanitized(out + err)`):

| Contract | Test name (suggested) | Expected exit code | Setup |
|----------|----------------------|---------------------|-------|
| Repo-root guard (D-11) | `test_cleanup_exits_2_outside_privguard_repo_root` | 2 | `monkeypatch.chdir(tmp_path)` (planner introduces the tmp_path pattern; no current test uses it — see "Note on tmp_path" below) |
| Dry-run is default (D-12) | `test_cleanup_default_is_dry_run_no_deletion` | 0 | seed tmp repo with `__pycache__/` + `.git/` + `pyproject.toml`, assert files still exist after `main(["cleanup"])` |
| Protected list refusal (D-09) | `test_cleanup_apply_skips_protected_paths_with_warning` | 0 | seed tmp repo with `.env`, assert it survives `main(["cleanup", "--apply"])` and stderr names it as skipped |
| Symlink refusal (D-13) | `test_cleanup_apply_refuses_symlinks` | 0 | seed tmp repo with a symlink inside `__pycache__/`, assert symlink target survives, exit 0, warning emitted |

**Note on `tmp_path`** — `tests/test_cleanup.py` is the **first** test in the suite that needs filesystem fixtures (`tmp_path`, `monkeypatch.chdir`). [VERIFIED via Grep: no other test file in `tests/` uses `tmp_path` or `monkeypatch.chdir`.] The planner introduces this pattern; pytest's built-in `tmp_path` fixture is the right primitive. There is no in-repo precedent to copy from for this specific aspect — reach for the standard pytest idiom:

```python
def test_cleanup_default_is_dry_run_no_deletion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Seed a fake privguard repo: .git/, pyproject.toml with name="privguard",
    # and a __pycache__/ directory the cleanup pattern matches.
    (tmp_path / ".git").mkdir()
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "privguard"\n[tool.privguard.cleanup]\npatterns = ["__pycache__/"]\n',
        encoding="utf-8",
    )
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "x.pyc").write_bytes(b"")

    monkeypatch.chdir(tmp_path)
    assert main(["cleanup"]) == 0  # dry-run default
    assert pycache.exists()  # NOT deleted

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    assert "[dry-run]" in captured.out
    _assert_sanitized(rendered)
```

This follows pytest's own conventions; surface to the user during plan-check that this is the first `tmp_path` use in the suite (planner discretion, not a project-style break — Phase 5 fixtures are content-only, not filesystem-state, hence no prior need).

---

### `pyproject.toml` (modified — config)

**Analog:** `pyproject.toml` itself, lines 1-27 — extend three blocks.

**`[project.scripts]` extension (D-15)** — copy syntax from line 23-24:

```toml
# Source: pyproject.toml:23-24
[project.scripts]
privguard = "privguard.cli:main"
```

For Phase 7 (D-15), append two entries in the same `module:function` style:

```toml
[project.scripts]
privguard = "privguard.cli:main"
privguard-user-prompt = "privguard.hooks:main_user_prompt"
privguard-pre-tool    = "privguard.hooks:main_pre_tool"
```

The `module:function` form is verified against the existing entry — these are the exact functions exposed at `privguard/__init__.py:11` and `privguard/hooks.py:149` / `:246`.

**`[project.dependencies]` conditional-marker pattern (D-16)** — no current `dependencies = [...]` entry (line 9 is `dependencies = []`), but the conditional-marker syntax is verified in the same file at lines 17-21:

```toml
# Source: pyproject.toml:16-21 (verified marker syntax)
[project.optional-dependencies]
full = [
    "presidio-analyzer==2.2.362; python_version < '3.14'",
    "presidio-anonymizer==2.2.362",
    "spacy==3.8.14; python_version < '3.14'",
]
```

For Phase 7 (D-16), change line 9 from `dependencies = []` to:

```toml
dependencies = [
    "tomli; python_version < '3.11'",
]
```

**`[tool.privguard.cleanup]` table (D-08)** — no in-repo analog (first `[tool.privguard.*]` table). The TOML syntax is standard PEP 518; the verbatim table from RESEARCH.md §"D-08" lines 53-57 (with comment per CONTEXT.md "Specifics" line 395 — "trailing `/` means directory tree, no trailing `/` means glob basename"):

```toml
# Source: D-08 verbatim + CONTEXT.md "Specifics" comment requirement
[tool.privguard.cleanup]
# A trailing "/" means "directory tree, recursive".
# No trailing "/" means glob-style basename match (fnmatch syntax).
patterns = [
    "__pycache__/",
    "*.py[cod]",
    ".pytest_cache/",
    ".coverage",
    "htmlcov/",
    "dist/",
    "build/",
    "*.egg-info/",
]
```

Place this table **after** `[tool.setuptools.packages.find]` (line 26-27) — `[tool.*]` tables are conventionally grouped at the bottom of `pyproject.toml`.

---

### `.gitignore` (modified — config)

**Analog:** `.gitignore` itself, lines 1-15 — append-only delta.

**Existing structure** (lines 1-15):

```
.env
.env.*
data_sensivel/
cooperados/
dump_*
*.cooperados.csv
*.cpf.txt
credenciais*
segredo*
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
```

**Phase 7 delta** (RESEARCH.md §"Pitfall 4" lines 635-641 — verified the only missing patterns are the three packaging-artifact entries):

```
dist/
build/
*.egg-info/
```

Append these three lines verbatim after line 14 (`htmlcov/`). No reordering, no comments needed (existing `.gitignore` has no comments — match the style).

---

## Shared Patterns

### `from __future__ import annotations` (mandatory)

**Source:** every existing `.py` in `privguard/` (`cli.py:3`, `diagnostics.py:3`, `hooks.py:3`, `policy.py:3`, `codex.py:16`, `masking.py`, `detection.py`).
**Apply to:** `privguard/cleanup.py` (new), `tests/test_cleanup.py` (new).

```python
# Source: privguard/cli.py:1-3 (canonical module header)
"""Command-line interface for privguard diagnostics."""

from __future__ import annotations
```

### Sanitized error / diagnostic output (Phase 2 POL-04 + D-10)

**Source:** `privguard/hooks.py:14-17` (deny prefix), `privguard/diagnostics.py:84-102` (paths-and-counts-only formatter).
**Apply to:** all stderr writes in `privguard/cleanup.py`, all `print()` calls in `privguard/cleanup.py` dry-run formatter and `--apply` warnings.

```python
# Source: privguard/hooks.py:15-17
def deny(prefix: str, reason_code: str) -> int:
    sys.stderr.write(f"[{prefix} BLOQUEADO] reason={reason_code}\n")
    return 2
```

For cleanup, the prefix becomes `[CLEANUP]` (English, since cleanup is dev-machine tooling not user-facing protective-block messaging — `BLOQUEADO` is a Portuguese block-event signal, not a generic error tag). Mirror only the format shape: `[<TAG>] <key>=<value> <key>=<value>` — never echo file contents, only paths and counts.

### Exit-code convention `0 / 1 / 2`

**Source:** `privguard/cli.py:23` (`cmd_info` returns 0), `cli.py:67` (`cmd_mask` returns 2 on verification failure), `cli.py:96` (`cmd_policy_check` returns 2 on block), `cli.py:105` (`cmd_claude_doctor` returns 0 or 2), `hooks.py:39` (`_deny_pre_tool` returns 2), `hooks.py:190` (`main_user_prompt` returns 2 on block).
**Apply to:** `privguard/cleanup.py` (D-14):
- `0` — clean dry-run OR successful `--apply`.
- `1` — `--apply` deletion failure (OS error, permissions).
- `2` — misuse (D-11 fail, schema fail, unknown flag — argparse returns 2 itself for unknown flags).

### Frozen-tuple module-level constants

**Source:** `privguard/hooks.py:193-218` (`_KNOWN_LOCAL_TOOLS`, `_LLM_ORCHESTRATION_TOOLS`, `_ALLOWED_MCP_PREFIXES`), `privguard/diagnostics.py:14-19` (`SYNTHETIC_DOCTOR_*`).
**Apply to:** `privguard/cleanup.py` `_PROTECTED` constant (D-09).

```python
# Source: privguard/hooks.py:217-221
_ALLOWED_MCP_PREFIXES = (
    "mcp__plugin_mempalace_mempalace__",
    "mcp__ide__",
)
```

The single-leading-underscore "module-private but importable" + tuple-of-strings + trailing-comma-on-last-element conventions are uniform in privguard.

### `capsys` + `_assert_sanitized` test pattern

**Source:** `tests/test_claude_doctor.py:31-33` (`_assert_sanitized` helper + `FORBIDDEN_OUTPUT_VALUES`), `tests/test_cli.py:19-26` (raw-CPF-not-in-output assertion).
**Apply to:** `tests/test_cleanup.py` — every test function asserts `_assert_sanitized(captured.out + captured.err)` to enforce Phase 2 POL-04 / Phase 7 D-10 paths-only output rule.

```python
# Source: tests/test_claude_doctor.py:31-33
def _assert_sanitized(rendered: str) -> None:
    for value in FORBIDDEN_OUTPUT_VALUES:
        assert value not in rendered
```

### `assert main(["subcommand", ...]) == EXIT_CODE` invocation

**Source:** `tests/test_cli.py:11, 22, 32, 44, 54, 64, 75, 95, 107, 125, 140`, `tests/test_claude_doctor.py:39, 68`.
**Apply to:** `tests/test_cleanup.py` — all four contract tests use this shape (call `privguard.cli.main(["cleanup", ...])`, NOT `privguard.cleanup.main(...)` directly, to exercise the full argparse path including subparser registration).

```python
# Source: tests/test_cli.py:22 (canonical shape)
assert main(["scan", f"CPF {raw_cpf}"]) == 0
```

---

## No Analog Found

| File | Role | Data Flow | Reason | Planner action |
|------|------|-----------|--------|----------------|
| `README.md` | top-level documentation prose | static | The repo has no prior top-level README. Closest in-repo prose-style markdown is `AGENTS.md` (22K, GSD-generated) and `docs/install.md` (2.8K, hand-written). Mirror tone (terse, technical, English, lowercase headings where appropriate) and structural conventions (one-line code-block quickstarts, fenced ` ```bash ` blocks, inline-code for CLI invocations) from `docs/install.md`. Do NOT mirror AGENTS.md's GSD-block structure (`<!-- GSD:project-start -->`) — that is auto-generated and not human-authored prose convention. | Use RESEARCH.md §"Code Examples" (lines 736-803) drop-in snippets for the masking demo, hook-setup snippet, and capabilities matrix; mirror `docs/install.md:1-54` for tone and code-block density. |
| `README.pt-BR.md` | top-level documentation prose, pt-BR | static | No pt-BR prose exists in the repo today. Tone reference is the existing pt-BR error messages in `privguard/hooks.py` (`BLOQUEADO`, `aviso`, `remediation`) and the synthetic test fixture comments — these are the only pt-BR strings in-repo and confirm the project uses Brazilian Portuguese conventions (`BLOQUEADO` not pt-PT `BLOQUEADO`/`bloqueado` distinctions are minimal here, but `aviso` is pt-BR over pt-PT `aviso/advertência`). | Use RESEARCH.md §"Pitfall 5" lines 660-676 for translation-tone guidance (você, arquivo/tela/celular, keep "hook"/"CLI"/"commit" in English, fail-closed → "fail-closed (falha segura)" parenthetical pattern). EN twin is the structural source of truth; pt-BR copies structure section-for-section. |
| `[tool.privguard.cleanup]` table in `pyproject.toml` | config table | static | No prior `[tool.privguard.*]` table exists. Closest is `[tool.setuptools.packages.find]` at lines 26-27 (single-key table, comment-free). | Match its terseness; add a single comment line above `patterns = [...]` documenting the trailing-slash semantic (CONTEXT.md "Specifics" line 395). |

## Metadata

**Analog search scope:**
- `privguard/*.py` (8 modules: `__init__.py`, `cli.py`, `codex.py`, `detection.py`, `diagnostics.py`, `hooks.py`, `masking.py`, `policy.py`)
- `tests/*.py` (11 test files)
- `docs/*.md` (`install.md`, `codex-compatibility.md`)
- `pyproject.toml`, `.gitignore`, `.claude/settings.json`, `AGENTS.md`

**Files scanned:** 8 package modules + 11 test files + 2 doc markdowns + 4 config/meta files = 25 files.

**Key in-repo conventions confirmed:**
- Every `.py` in `privguard/` opens with a one-line docstring + `from __future__ import annotations`.
- Every `cmd_*` and `main_*` callable returns `int` (0/2 dominant; 1 reserved for "operation attempted and OS-failed" — Phase 7 introduces the first 1-exit case).
- Module-private constants use `_LEADING_UNDERSCORE` + frozen tuple/frozenset.
- Sanitized output writes via `sys.stderr.write(f"[<TAG> ...] key=value\n")` — no `logging` module, no `print()` to stderr, no f-string interpolation of raw payload values into output.
- All tests use `from privguard.cli import main` + `main([...])` + `capsys.readouterr()` — no `subprocess`, no test-fixture files on disk (until Phase 7).
- Synthetic fixtures live at `tests/test_v1_regression_gate.py:45-99` and `tests/test_claude_doctor.py:11-28`; reused, never reinvented.

**Pattern extraction date:** 2026-05-08

**Critical planner notes:**
1. **`tmp_path` is new.** Phase 7 introduces the first test that needs filesystem-state fixtures. No in-repo analog exists; pytest's standard `tmp_path` + `monkeypatch.chdir` is the right primitive. Surface this in plan-check so the planner doesn't get blocked looking for an analog that doesn't exist.
2. **`tomllib` shim is new.** D-16 mandates the try/except shim; no in-repo precedent. Verbatim shim is in RESEARCH.md §"Pitfall 1 Option A" lines 526-535.
3. **Exit code 1 is new.** `cleanup --apply` OS-failure case is the first `return 1` in privguard. All existing CLI exits are 0 or 2. The convention extension is locked by D-14.
4. **Two console scripts are new.** D-15 adds `privguard-user-prompt` and `privguard-pre-tool` to `[project.scripts]`. The `module:function` form is already established by `privguard = "privguard.cli:main"` at `pyproject.toml:24`; the new entries follow it exactly.
5. **README files have no in-repo prose analog by design.** Use `docs/install.md` for tone/density and the verbatim drop-in snippets from RESEARCH.md §"Code Examples". Do NOT copy structural conventions from `AGENTS.md` (GSD-generated, not hand-authored).
