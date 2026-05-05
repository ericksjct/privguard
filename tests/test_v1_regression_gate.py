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
    # Exclude test files that contain claim/fixture strings as test data
    # (not real claims) — same exclusion policy as test_codex_claim_gate.py
    if name in {
        "test_codex_claim_gate.py",
        "test_codex_compatibility.py",
        "test_v1_regression_gate.py",
    }:
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


# ===========================================================================
# TEST-02: Cross-surface forbidden-output hygiene
# ===========================================================================


def test_TEST_02_cli_scan_json_output_is_sanitized(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TEST-02: CLI scan --json output must not echo raw sensitive fixture values."""
    assert cli_main(["scan", "--json", f"CPF {SYNTH_CPF}"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["counts"]["BR_CPF"] == 1
    _assert_forbidden_values_absent(captured.out + captured.err)


def test_TEST_02_cli_mask_text_output_sanitized_in_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TEST-02: CLI mask output must not echo raw CPF in JSON surfaces."""
    assert cli_main(["mask", "--json", f"CPF {SYNTH_CPF}"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    # JSON diagnostics must not contain raw value or masked payload text
    json_str = json.dumps(payload)
    assert SYNTH_CPF not in json_str
    # Placeholders are allowed only in human mask output, not JSON diagnostics
    assert "<BR_CPF>" not in json_str


def test_TEST_02_diagnostics_serialization_excludes_raw_values() -> None:
    """TEST-02: diagnostics to_json/format_text must not expose raw sensitive values."""
    text = f"CPF {SYNTH_CPF} CNPJ {SYNTH_CNPJ}"
    report = analyze_text(text)
    result = mask_text(text)

    rendered_report = to_json(report)
    rendered_mask = to_json(result)
    rendered_text = format_text(result)

    # Raw values must not appear in any serialized form
    assert SYNTH_CPF not in rendered_report
    assert SYNTH_CPF not in rendered_mask
    assert SYNTH_CNPJ not in rendered_report
    assert SYNTH_CNPJ not in rendered_mask
    # Masked placeholders must not appear in JSON diagnostics either
    assert "<BR_CPF>" not in rendered_mask
    assert "<BR_CNPJ>" not in rendered_mask
    assert "<BR_CPF>" not in rendered_text

    # Metadata is still present
    parsed = json.loads(rendered_mask)
    assert parsed["verified"] is True
    assert parsed["hit_count"] >= 1


def test_TEST_02_masked_metadata_excludes_payload_text() -> None:
    """TEST-02: MaskResult metadata serialization must not echo masked payload text."""
    text = f"token api_key={FAKE_SECRET_SK}"
    result = mask_text(text)
    assert result.verified is True

    serialized = to_json(result)
    # Raw secret must not appear
    assert FAKE_SECRET_SK not in serialized
    # Masked placeholder must not appear in JSON diagnostics
    assert "<TOKEN>" not in serialized
    assert "sk-test-" not in serialized


# ===========================================================================
# TEST-05: Claude hook JSON/mode/malformed/exit-code representative cases
# ===========================================================================


def test_TEST_05_user_prompt_hook_blocks_pii_with_sanitized_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TEST-05: Prompt hook blocks synthetic PII (exit 2), output is sanitized."""
    assert _run_user_prompt(monkeypatch, {"prompt": PROMPT_TEXT}) == 2
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "UserPromptSubmit" in output or "BLOQUEADO" in output
    assert "action=block" in output
    assert "BR_CPF" in output
    _assert_forbidden_values_absent(output)


def test_TEST_05_pre_tool_hook_blocks_protected_path_with_sanitized_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TEST-05: PreToolUse hook blocks a protected-path Read call (exit 2), output is sanitized."""
    payload = {"tool_name": "Read", "tool_input": {"file_path": PROT_DATA}}
    assert _run_pre_tool(monkeypatch, payload) == 2
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "PreToolUse" in output or "action=block" in output
    assert "protected_path" in output
    _assert_forbidden_values_absent(output)


def test_TEST_05_malformed_json_hook_fails_open_with_no_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TEST-05: Malformed JSON input to both hooks fails open (exit 0) with no output."""
    malformed = '{"prompt": "CPF incomplete'
    assert _run_user_prompt(monkeypatch, malformed) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    malformed_tool = '{"tool_name": "Read", "tool_input": {"file_path": '
    assert _run_pre_tool(monkeypatch, malformed_tool) == 0
    captured = capsys.readouterr()
    assert captured.out + captured.err == ""


def test_TEST_05_non_blocking_prompt_modes_are_labeled_non_protective(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TEST-05: warn and scrub modes are labeled non-protective and output is sanitized."""
    for mode in ("warn", "scrub"):
        exit_code = _run_user_prompt(monkeypatch, {"prompt": PROMPT_TEXT}, mode=mode)
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert exit_code in {0, 2}
        assert "local_development_non_protective" in output
        assert "BR_CPF" in output
        _assert_forbidden_values_absent(output)


def test_TEST_05_invalid_threshold_uses_default_without_echo(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """TEST-05: Invalid threshold values fall back to default without echoing prompt text."""
    for threshold in ("nan", "inf", "-1", "2", "not-a-number"):
        exit_code = _run_user_prompt(
            monkeypatch,
            {"prompt": PROMPT_TEXT},
            threshold=threshold,
        )
        captured = capsys.readouterr()
        output = captured.out + captured.err
        assert exit_code == 2, (
            f"Expected exit 2 (PII blocked) with threshold={threshold!r}; got {exit_code}"
        )
        assert "reason=pii_detected" in output
        _assert_forbidden_values_absent(output)


# ===========================================================================
# TEST-06: Fail-closed failure paths
# ===========================================================================


def test_TEST_06_unverified_mask_never_allows_external_submission() -> None:
    """TEST-06: A MaskResult with verified=False must never allow external submission."""
    raw_text = f"CPF {SYNTH_CPF}"
    hits = detect(raw_text)
    result = mask_text(raw_text, hits=hits)

    # Construct a failed mask result (verified=False) using the same dataclass type
    failed = type(result)(
        text=raw_text,
        changed=False,
        verified=False,
        verification_status="failed",
        reason_codes=("original_value_remaining",),
        hits=tuple(hits),
    )

    decision = decide_policy(SurfaceCapability.REWRITE_CAPABLE, hits=hits, mask_result=failed)
    assert decision.allow is False
    assert decision.action != PolicyAction.ALLOW
    assert "mask_unverified" in decision.reason_codes


def test_TEST_06_fail_closed_for_all_non_rewrite_capable_surfaces() -> None:
    """TEST-06: UNKNOWN/EXTERNAL/UNSUPPORTED/OBSERVE_ONLY/BLOCK_ONLY fail closed with sensitive hits."""
    hits = detect(f"CPF {SYNTH_CPF}")
    assert hits, "Synthetic CPF must produce detection hits"

    for capability in (
        SurfaceCapability.UNKNOWN,
        SurfaceCapability.EXTERNAL,
        SurfaceCapability.UNSUPPORTED,
        SurfaceCapability.OBSERVE_ONLY,
        SurfaceCapability.BLOCK_ONLY,
    ):
        decision = decide_policy(capability, hits=list(hits))
        assert decision.allow is False, (
            f"Surface {capability!r} must not allow sensitive hits; got action={decision.action!r}"
        )
        assert decision.action in {PolicyAction.BLOCK, PolicyAction.PAUSE}, (
            f"Surface {capability!r} must block or pause; got {decision.action!r}"
        )


def test_TEST_06_redact_failure_raises_sanitized_exception() -> None:
    """TEST-02/TEST-06: redact() with empty hits raises ValueError with sanitized message."""
    raw_text = f"CPF {SYNTH_CPF}"
    # Passing empty hits list on sensitive text causes mask_text to produce an
    # unverified result (residual_detection), which redact() must raise as ValueError.
    with pytest.raises(ValueError) as exc_info:
        redact(raw_text, hits=[])

    exc_message = str(exc_info.value)
    # Exception message must not contain the raw sensitive value
    assert SYNTH_CPF not in exc_message, (
        "Exception message must not echo the raw CPF value"
    )
    assert "sk-test-" not in exc_message
    # Should contain a generic/sanitized reason, not a raw fixture
    assert exc_message  # non-empty sanitized message


def test_TEST_06_empty_mask_with_sensitive_text_fails_closed() -> None:
    """TEST-06: mask_text() with explicitly empty hits on sensitive text is unverified."""
    raw_text = f"CPF {SYNTH_CPF}"
    result = mask_text(raw_text, hits=[])
    # Must not be verified — passing no hits on PII-containing text is a failure mode
    assert result.verified is False
    assert result.verification_status == "failed"
    assert "residual_detection" in result.reason_codes


def test_TEST_06_codex_has_no_automatic_masking_rows() -> None:
    """TEST-06: CODEX_COMPATIBILITY must not contain automatic_masking=True rows."""
    masking_rows = [row for row in CODEX_COMPATIBILITY if row.automatic_masking]
    assert not masking_rows, (
        "Phase 04/05 matrix must not contain automatic_masking=True rows. Found: "
        + ", ".join(r.surface for r in masking_rows)
    )


def test_TEST_06_codex_claim_scan_reports_only_file_path_and_pattern() -> None:
    """TEST-06: Unsupported Codex masking claims must not appear in safe repo text.

    Failure message reports only file path and pattern name — no raw line content
    is included to avoid leaking synthetic fixture values.
    """
    import re as _re

    forbidden_phrases = (
        "codex masks prompts automatically",
        "codex automatic masking",
        "automatic codex masking",
    )
    allowed_negations = (
        "automatic codex masking is unsupported until verified outbound payload replacement is proven",
        "no automatic codex masking claim",
    )

    files = _safe_text_files()
    assert files, (
        "Safe file scan returned no files — check working directory and glob patterns"
    )
    violations: list[tuple[pathlib.Path, str]] = []

    for target in files:
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        content_lower = content.lower()
        lines_list = content_lower.splitlines()

        for phrase in forbidden_phrases:
            start = 0
            while True:
                idx = content_lower.find(phrase, start)
                if idx == -1:
                    break

                # Find the line number for this match
                line_num = content_lower.count("\n", 0, idx)

                # Build single-line context (whitespace collapsed)
                line_start = content_lower.rfind("\n", 0, idx) + 1
                line_end = content_lower.find("\n", idx)
                if line_end == -1:
                    line_end = len(content_lower)
                single_line = _re.sub(r"\s+", " ", content_lower[line_start:line_end])

                # Build two-line window (current + next line, whitespace collapsed)
                # Handles disclaimers split across two lines like:
                #   "**automatic Codex masking\nis unsupported until..."
                if line_num + 1 < len(lines_list):
                    raw_window = lines_list[line_num] + " " + lines_list[line_num + 1]
                    two_line = _re.sub(r"\s+", " ", raw_window)
                else:
                    two_line = single_line

                # Allow if either window contains a negation
                allowed_single = any(neg in single_line for neg in allowed_negations)
                allowed_two = any(neg in two_line for neg in allowed_negations)

                # Allow surface-name table rows labeled unsupported
                is_surface_row = (
                    "automatic codex masking rewrite" in single_line
                    and (
                        "unsupported" in single_line
                        or single_line.strip().startswith("#")
                        or '"automatic codex masking rewrite"' in single_line
                        or "'automatic codex masking rewrite'" in single_line
                    )
                )

                if not (allowed_single or allowed_two or is_surface_row):
                    violations.append((target, phrase))

                start = idx + 1

    if violations:
        # Failure message: file path + pattern name only (no raw line content)
        msg_lines = ["Unsupported Codex masking claims found:"]
        for path, pattern in violations:
            msg_lines.append(f"  {path}: matched pattern {pattern!r}")
        pytest.fail("\n".join(msg_lines))
