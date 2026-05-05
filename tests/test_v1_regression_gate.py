"""V1 synthetic regression gate.

Requirements covered:
- TEST-01: synthetic-only fixture and safe scanner policy (Tasks 1-2)
- TEST-02: forbidden output corpus across v1 surfaces (Task 2)
- TEST-03: identifier validity/overlap representative cases (Task 1)
- TEST-04: protected path normalization representative cases (Task 1)
- TEST-05: Claude hook JSON/mode/malformed representative cases (Task 2)
- TEST-06: fail-closed masking/policy/Codex representative cases (Task 3)

All tests use inline synthetic Brazilian PII, fake secrets, and fake protected
paths only. No test reads .env, .env.*, data_sensivel/**, or any protected file.
"""

from __future__ import annotations

import io
import json
import pathlib
import sys

import pytest

from privguard.cli import main as cli_main
from privguard.codex import CODEX_COMPATIBILITY
from privguard.detection import analyze_text, detect
from privguard.diagnostics import format_text, to_dict, to_json
from privguard.hooks import main_pre_tool, main_user_prompt
from privguard.masking import MaskResult, mask_text, redact, verify_mask
from privguard.policy import (
    PolicyAction,
    PolicyMode,
    SurfaceCapability,
    classify_command,
    classify_path,
    decide_policy,
)

# ---------------------------------------------------------------------------
# Synthetic fixture constants (D-04/D-06)
# None of these reference real sensitive data or protected files.
# ---------------------------------------------------------------------------

# Valid checksum Brazilian identifiers (synthetic/standard test values)
SYNTH_CPF = "123.456.789-09"
SYNTH_CNPJ = "12.345.678/0001-95"
SYNTH_CNH = "12345678900"

# Invalid checksum lookalikes (same format, wrong check digit)
INVALID_CPF = "123.456.789-00"
INVALID_CNPJ = "12.345.678/0001-00"

# Secret lookalike values (fake tokens that should be detected as secrets, not BR identifiers)
FAKE_SECRET_SK = "sk-test-abcdefghijklmnopqrstuvwxyz"
FAKE_SECRET_GHP = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

# Synthetic protected paths (string-only, never opened/read)
PROT_ENV = ".env"
PROT_DATA = "data_sensivel/synthetic.csv"
PROT_ROOT_RELATIVE = "./data_sensivel/synthetic.csv"
PROT_TRAVERSAL = "privguard/../data_sensivel/synthetic.csv"
PROT_WINDOWS = r"C:\repo\safe\..\data_sensivel\synthetic.csv"

# Synthetic prompt and command snippets (forbidden in outputs)
PROMPT_SNIPPET = "analise o cadastro"
PROMPT_TEXT = f"{PROMPT_SNIPPET}: CPF {SYNTH_CPF} token={FAKE_SECRET_SK}"
COMMAND_TEXT = f"Get-Content {PROT_DATA} | Set-Clipboard"

# ---------------------------------------------------------------------------
# Shared forbidden-output corpus
# Raw fixture strings that must never appear in any output surface.
# ---------------------------------------------------------------------------

FORBIDDEN_OUTPUT: tuple[str, ...] = (
    SYNTH_CPF,
    SYNTH_CNPJ,
    FAKE_SECRET_SK,
    FAKE_SECRET_GHP,
    PROT_ENV,
    PROT_DATA,
    "data_sensivel",
    PROMPT_SNIPPET,
    PROMPT_TEXT,
    COMMAND_TEXT,
    "sk-test-",
    "redacted=",
    "<BR_CPF>",
    "<TOKEN>",
    "<BR_CNPJ>",
    "Get-Content",
    "Set-Clipboard",
)


def _assert_forbidden_values_absent(output: str) -> None:
    """Assert that no forbidden synthetic value appears in the rendered output."""
    for value in FORBIDDEN_OUTPUT:
        assert value not in output, (
            "Forbidden value appeared in output: " + repr(value[:20]) + "..."
        )


# ---------------------------------------------------------------------------
# Safe file scanner helpers (TEST-01)
# ---------------------------------------------------------------------------

_ROOT = pathlib.Path(".")

_EXCLUDED_PARTS = frozenset({
    ".git",
    ".planning",
    "data_sensivel",
    "__pycache__",
    ".pytest_cache",
})


def _is_excluded(path: pathlib.Path) -> bool:
    """Return True if this path should be excluded from any safe scan."""
    parts = path.parts
    for part in parts:
        if part in _EXCLUDED_PARTS:
            return True
        if part.startswith("pytest-cache-files-"):
            return True
    name = path.name
    if name == ".env" or name.startswith(".env."):
        return True
    return False


def _safe_text_files(root: pathlib.Path = _ROOT) -> list[pathlib.Path]:
    """Return safe text file targets to scan.

    Only scans explicit safe globs:
      - docs/**/*.md
      - privguard/**/*.py
      - tests/**/*.py
      - pyproject.toml
      - AGENTS.md (if present)

    Excludes any path matching _is_excluded().
    """
    globs = [
        list(root.glob("docs/**/*.md")),
        list(root.glob("privguard/**/*.py")),
        list(root.glob("tests/**/*.py")),
        [root / "pyproject.toml"] if (root / "pyproject.toml").exists() else [],
        [root / "AGENTS.md"] if (root / "AGENTS.md").exists() else [],
    ]
    results: list[pathlib.Path] = []
    for group in globs:
        for p in group:
            if p.exists() and p.is_file() and not _is_excluded(p):
                results.append(p)
    return results


# ---------------------------------------------------------------------------
# Hook runner helpers (TEST-05 pattern)
# ---------------------------------------------------------------------------

def _run_user_prompt(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
    *,
    mode: str | None = None,
    threshold: str | None = None,
) -> int:
    if mode is None:
        monkeypatch.delenv("PII_GUARD_MODE", raising=False)
    else:
        monkeypatch.setenv("PII_GUARD_MODE", mode)
    if threshold is None:
        monkeypatch.delenv("PII_GUARD_THRESHOLD", raising=False)
    else:
        monkeypatch.setenv("PII_GUARD_THRESHOLD", threshold)
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    monkeypatch.setattr(sys, "stdin", io.StringIO(raw))
    return main_user_prompt()


def _run_pre_tool(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
) -> int:
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    monkeypatch.setattr(sys, "stdin", io.StringIO(raw))
    return main_pre_tool()


# ===========================================================================
# TEST-01: Synthetic fixture policy and safe source scanner
# ===========================================================================


def test_TEST_01_safe_source_scan_excludes_protected_paths_and_uses_synthetic_policy() -> None:
    """TEST-01: Safe file scanner uses only allowlisted globs and excludes protected paths."""
    files = _safe_text_files()
    assert files, "Safe file scan returned no files — check glob patterns"

    for f in files:
        parts = f.parts
        # Must not include protected paths
        assert "data_sensivel" not in parts, f"data_sensivel appeared in scan: {f}"
        assert ".planning" not in parts, f".planning appeared in scan: {f}"
        assert ".git" not in parts, f".git appeared in scan: {f}"
        assert "__pycache__" not in parts, f"__pycache__ appeared in scan: {f}"
        assert ".pytest_cache" not in parts, f".pytest_cache appeared in scan: {f}"
        # Must not include .env files
        assert not (f.name == ".env" or f.name.startswith(".env.")), (
            f"Protected .env path appeared in scan: {f}"
        )
        # Must not include pytest-cache-files- paths
        for part in parts:
            assert not part.startswith("pytest-cache-files-"), (
                f"pytest-cache-files- path appeared in scan: {f}"
            )


# ===========================================================================
# TEST-03: Brazilian identifier validity, overlap, and lookalikes
# ===========================================================================


def test_TEST_03_identifier_validity_overlap_and_lookalikes_are_represented() -> None:
    """TEST-03: Valid/invalid identifiers, overlap selection, and secret lookalikes."""
    # Valid CPF and CNPJ are detected
    hits = detect(f"CPF {SYNTH_CPF} CNPJ {SYNTH_CNPJ}")
    kinds = {h.kind for h in hits}
    assert "BR_CPF" in kinds
    assert "BR_CNPJ" in kinds

    # Invalid checksum lookalikes are not detected above threshold
    invalid_text = f"CPF {INVALID_CPF} CNPJ {INVALID_CNPJ}"
    invalid_hits = detect(invalid_text)
    invalid_kinds = {h.kind for h in invalid_hits}
    assert "BR_CPF" not in invalid_kinds
    assert "BR_CNPJ" not in invalid_kinds

    # Secret lookalike (sk-test-...) is detected as a secret, NOT as a Brazilian identifier
    secret_hits = detect(f"api_key={FAKE_SECRET_SK}")
    secret_kinds = {h.kind for h in secret_hits}
    assert "BR_CPF" not in secret_kinds
    assert "BR_CNPJ" not in secret_kinds
    assert any("API_KEY" in k or "TOKEN" in k or "SECRET" in k for k in secret_kinds), (
        f"Fake secret should produce a secret-type hit; got kinds={secret_kinds!r}"
    )

    # At least one additional Brazilian identifier beyond CPF/CNPJ is covered
    multi_text = (
        f"CNH {SYNTH_CNH}; "
        "PIS 123.45678.90-0; SUS 123 4567 8901 2348"
    )
    multi_hits = detect(multi_text)
    multi_kinds = {h.kind for h in multi_hits}
    assert len(multi_kinds) >= 2, (
        f"Expected at least 2 identifier kinds from multi_text; got {multi_kinds!r}"
    )


# ===========================================================================
# TEST-04: Protected path normalization
# ===========================================================================


def test_TEST_04_protected_path_normalization_is_project_root_traceable() -> None:
    """TEST-04: Windows paths, mixed separators, relative traversal, quoted, and project-root-relative paths."""
    cases = [
        # (path_string, description, expected_reason_code)
        (PROT_DATA, "posix protected data path", "protected_path_data"),
        (PROT_ROOT_RELATIVE, "project-root-relative ./data_sensivel/...", "protected_path_data"),
        (PROT_TRAVERSAL, "traversal privguard/../data_sensivel/...", "protected_path_data"),
        (PROT_WINDOWS, "Windows mixed-separator traversal path", "protected_path_data"),
        (r"data_sensivel\synthetic.csv", "Windows backslash path", "protected_path_data"),
        (r'"C:\repo\data_sensivel\file.csv"', "quoted Windows path", "protected_path_data"),
        (".env", "env file", "protected_path_env"),
        (".env.local", "env variant", "protected_path_env"),
    ]
    for path_str, description, expected_reason_code in cases:
        c = classify_path(path_str)
        assert c.is_protected is True, (
            f"Path not classified as protected ({description}): {path_str!r}"
        )
        assert c.reason_code == expected_reason_code, (
            f"Wrong reason_code for {description}: expected {expected_reason_code!r} got {c.reason_code!r}"
        )

    # Explicit project-root-relative protected path asserts protected_path_data
    proj_root_path = "./data_sensivel/synthetic.csv"
    proj_result = classify_path(proj_root_path)
    assert proj_result.is_protected is True
    assert proj_result.reason_code == "protected_path_data"
