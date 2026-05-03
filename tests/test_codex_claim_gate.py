"""
CDX-03 claim gate: prevents unsupported Codex automatic masking claims.

Scans safe repository text (docs, source, tests, package config) for phrases
that imply Codex automatic masking or rewrite-capable surfaces.  A positive
automatic masking claim is only allowed if CODEX_COMPATIBILITY has at least one
row with:

    row.automatic_masking is True
    row.surface_capability == SurfaceCapability.REWRITE_CAPABLE
    "verified outbound payload replacement" in " ".join(row.evidence + row.gaps)

Because no such row exists in Phase 04, any unsupported positive masking claim
must fail.  Negated/disclaimer wording is explicitly allowed.

Requirements: CDX-03
"""

from __future__ import annotations

import pathlib
import re
import pytest

from privguard.codex import CODEX_COMPATIBILITY
from privguard.policy import SurfaceCapability

# ---------------------------------------------------------------------------
# Forbidden claim patterns (case-insensitive substring matches)
# ---------------------------------------------------------------------------

FORBIDDEN_CLAIM_PATTERNS: tuple[str, ...] = (
    "codex masks prompts automatically",
    "codex automatic masking",
    "automatic codex masking",
    "codex rewrite-capable",
    "codex rewrites prompts before submission",
)

# ---------------------------------------------------------------------------
# Allowed negated/disclaimer wording (exact lowercase sentence or prefix)
# ---------------------------------------------------------------------------

ALLOWED_NEGATED_CLAIMS: tuple[str, ...] = (
    # Full canonical disclaimer (may appear on one line or split across two lines)
    "automatic codex masking is unsupported until verified outbound payload replacement is proven",
    # Docstring/comment negation: "No automatic Codex masking claim"
    "no automatic codex masking claim",
)

# ---------------------------------------------------------------------------
# Allowed surface-name string literals in the machine-readable matrix source.
# These are data values in privguard/codex.py, not human-readable claims.
# ---------------------------------------------------------------------------

_ALLOWED_SURFACE_NAME_LITERALS: tuple[str, ...] = (
    # The matrix surface row for the unsupported automatic masking surface
    '"automatic codex masking rewrite"',
    "\"automatic codex masking rewrite\"",
    "'automatic codex masking rewrite'",
)

# ---------------------------------------------------------------------------
# Safe file targets to scan
# ---------------------------------------------------------------------------

_ROOT = pathlib.Path(".")

# Explicit excluded path component set
_EXCLUDED_PARTS = frozenset({
    ".git",
    ".planning",
    "data_sensivel",
    "__pycache__",
    ".pytest_cache",
})


def _is_excluded(path: pathlib.Path) -> bool:
    """Return True if this path should be excluded from the claim scan."""
    parts = path.parts
    # Exclude any path whose components include excluded set members
    for part in parts:
        if part in _EXCLUDED_PARTS:
            return True
        # Exclude pytest cache result files (e.g. pytest-cache-files-*)
        if part.startswith("pytest-cache-files-"):
            return True
    # Exclude .env and .env.* exactly
    name = path.name
    if name == ".env" or name.startswith(".env."):
        return True
    # Exclude Codex-specific test files that reference forbidden strings as
    # test fixtures or assertion strings (not real claims).
    if name in {"test_codex_claim_gate.py", "test_codex_compatibility.py"}:
        return True
    return False


def _safe_text_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Return the safe text file targets to scan for claim violations.

    Scans only explicit safe globs:
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
# Claim detection helpers
# ---------------------------------------------------------------------------

def _has_verified_codex_masking_proof() -> bool:
    """Return True only if CODEX_COMPATIBILITY has a proven automatic masking row.

    A row qualifies as verified proof when:
      - row.automatic_masking is True
      - row.surface_capability == SurfaceCapability.REWRITE_CAPABLE
      - "verified outbound payload replacement" appears in the combined
        evidence + gaps string
    """
    for row in CODEX_COMPATIBILITY:
        if (
            row.automatic_masking is True
            and row.surface_capability == SurfaceCapability.REWRITE_CAPABLE
            and "verified outbound payload replacement" in " ".join(row.evidence + row.gaps)
        ):
            return True
    return False


def _find_unsupported_claims(text: str) -> list[str]:
    """Return a list of forbidden claim patterns found in *text*.

    A pattern match is not reported as a violation when any of these hold:

    1. The line containing the match also contains an allowed negated claim from
       ALLOWED_NEGATED_CLAIMS (single-line case).
    2. The two-line window (current + next line, whitespace-collapsed) contains
       an allowed negated claim (multi-line disclaimer split across lines).
    3. The match appears inside a quoted string literal that is an allowed matrix
       surface name (e.g. ``surface="Automatic Codex masking rewrite"`` in the
       machine-readable codex.py source file — a data value, not a claim).
    4. The line contains the surface-name-as-table-row pattern from the Markdown
       matrix (``automatic codex masking rewrite`` + ``unsupported`` on same line).
    """
    text_lower = text.lower()
    lines = text_lower.splitlines()
    violations: list[str] = []

    for pattern in FORBIDDEN_CLAIM_PATTERNS:
        start = 0
        while True:
            idx = text_lower.find(pattern, start)
            if idx == -1:
                break

            # Find the 0-based line number for this match position
            line_num = text_lower.count("\n", 0, idx)

            # Build the single-line context
            line_start = text_lower.rfind("\n", 0, idx) + 1
            line_end_idx = text_lower.find("\n", idx)
            if line_end_idx == -1:
                line_end_idx = len(text_lower)
            single_line = text_lower[line_start:line_end_idx]

            # Build two-line window (current + next line) with internal whitespace
            # collapsed to single spaces so that indented continuation lines
            # (e.g. "    is unsupported until...") join cleanly.
            import re as _re
            if line_num + 1 < len(lines):
                raw_window = lines[line_num] + " " + lines[line_num + 1]
                two_line_window = _re.sub(r"\s+", " ", raw_window)
            else:
                two_line_window = lines[line_num] if line_num < len(lines) else single_line

            # Also build a whitespace-collapsed version of the single line
            single_line_norm = _re.sub(r"\s+", " ", single_line)

            # Check 1: allowed negated claim on the same line (after whitespace collapse)
            allowed_single = any(disclaimer in single_line_norm for disclaimer in ALLOWED_NEGATED_CLAIMS)

            # Check 2: allowed negated claim spanning current + next line (whitespace-collapsed)
            allowed_two_line = any(disclaimer in two_line_window for disclaimer in ALLOWED_NEGATED_CLAIMS)

            # Check 3: match is inside an allowed surface-name string literal
            #   (e.g. surface="Automatic Codex masking rewrite" in codex.py)
            is_surface_name_literal = any(
                literal in single_line for literal in _ALLOWED_SURFACE_NAME_LITERALS
            )

            # Check 4: surface name in Markdown matrix table row labeled "unsupported"
            is_surface_name_labeled_unsupported = (
                "automatic codex masking rewrite" in single_line
                and "unsupported" in single_line
            )

            # Check 5: surface name reference in a Python section-divider comment
            #   (e.g. "# automatic codex masking rewrite" in codex.py — not a claim)
            is_section_divider_comment = (
                "automatic codex masking rewrite" in single_line
                and single_line.strip().startswith("#")
            )

            allowed = (
                allowed_single
                or allowed_two_line
                or is_surface_name_literal
                or is_surface_name_labeled_unsupported
                or is_section_divider_comment
            )
            if not allowed:
                violations.append(pattern)
            start = idx + 1

    return violations


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_codex_automatic_masking_claims_require_verified_matrix_proof() -> None:
    """CDX-03: Unsupported Codex masking claims must not appear in safe repo text.

    Scans docs/**/*.md, privguard/**/*.py, tests/**/*.py, pyproject.toml, and
    AGENTS.md for forbidden automatic masking claim patterns.  Passes only when
    either:
      (a) No forbidden claim patterns are found in safe repo files, OR
      (b) _has_verified_codex_masking_proof() returns True (a matrix row exists
          with automatic_masking=True and rewrite-capable capability and verified
          outbound replacement in evidence).

    Failure message reports only file paths and offending pattern — no raw line
    content is included to avoid leaking synthetic fixture values.
    """
    files = _safe_text_files(_ROOT)
    assert files, "Safe file scan returned no files — check glob patterns and repo structure"

    masking_proof_exists = _has_verified_codex_masking_proof()

    found_violations: list[tuple[pathlib.Path, str]] = []

    for target in files:
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        violations = _find_unsupported_claims(content)
        for pattern in violations:
            found_violations.append((target, pattern))

    if masking_proof_exists:
        # A verified masking row exists — positive claims are allowed
        pass
    else:
        # No matrix proof exists — any positive claim is a violation
        if found_violations:
            # Build sanitized failure message (path + pattern only, no raw content)
            lines = ["Unsupported Codex masking claims found (no verified matrix proof exists):"]
            for path, pattern in found_violations:
                lines.append(f"  {path}: matched forbidden pattern {pattern!r}")
            pytest.fail("\n".join(lines))


def test_allowed_negated_claim_is_not_flagged() -> None:
    """CDX-03: The canonical 'unsupported' disclaimer wording must not trigger a violation."""
    safe_text = (
        "automatic Codex masking is unsupported until verified outbound payload replacement is proven"
    )
    violations = _find_unsupported_claims(safe_text)
    assert violations == [], (
        f"Allowed negated claim was incorrectly flagged: {violations}"
    )


def test_positive_claim_without_matrix_proof_is_flagged() -> None:
    """CDX-03: A synthetic positive claim produces a violation when no matrix proof exists."""
    synthetic_text = "Codex masks prompts automatically for all users"
    violations = _find_unsupported_claims(synthetic_text)
    assert len(violations) >= 1, (
        "Expected at least one violation for synthetic positive masking claim, got none"
    )


def test_safe_file_scan_excludes_protected_paths() -> None:
    """CDX-03/hygiene: Safe file scanner excludes .env, data_sensivel, .planning, .git, caches."""
    files = _safe_text_files(_ROOT)
    for f in files:
        parts = f.parts
        assert ".env" not in parts and not f.name.startswith(".env"), (
            f"Excluded .env path appeared in scan: {f}"
        )
        assert "data_sensivel" not in parts, (
            f"Protected path data_sensivel appeared in scan: {f}"
        )
        assert ".planning" not in parts, (
            f"Planning directory appeared in scan: {f}"
        )
        assert ".git" not in parts, (
            f".git directory appeared in scan: {f}"
        )
        assert "__pycache__" not in parts, (
            f"__pycache__ appeared in scan: {f}"
        )
        for part in parts:
            assert not part.startswith("pytest-cache-files-"), (
                f"pytest-cache-files- path appeared in scan: {f}"
            )
