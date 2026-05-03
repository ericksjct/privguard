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
# Allowed negated/disclaimer wording (exact lowercase sentence)
# ---------------------------------------------------------------------------

ALLOWED_NEGATED_CLAIMS: tuple[str, ...] = (
    "automatic codex masking is unsupported until verified outbound payload replacement is proven",
)

# ---------------------------------------------------------------------------
# Safe file targets to scan
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
    """Return True if this path should be excluded from the claim scan."""
    for part in path.parts:
        if part in _EXCLUDED_PARTS:
            return True
        if part.startswith("pytest-cache-files-"):
            return True
    name = path.name
    if name == ".env" or name.startswith(".env."):
        return True
    return False


def _safe_text_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Return the safe text file targets to scan for claim violations."""
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


def _has_verified_codex_masking_proof() -> bool:
    """Return True only if CODEX_COMPATIBILITY has a proven automatic masking row."""
    for row in CODEX_COMPATIBILITY:
        if (
            row.automatic_masking is True
            and row.surface_capability == SurfaceCapability.REWRITE_CAPABLE
            and "verified outbound payload replacement" in " ".join(row.evidence + row.gaps)
        ):
            return True
    return False


def _find_unsupported_claims(text: str) -> list[str]:
    """Return a list of forbidden claim patterns found in *text* (naive line-only check)."""
    text_lower = text.lower()
    violations: list[str] = []

    for pattern in FORBIDDEN_CLAIM_PATTERNS:
        start = 0
        while True:
            idx = text_lower.find(pattern, start)
            if idx == -1:
                break
            line_start = text_lower.rfind("\n", 0, idx) + 1
            line_end_idx = text_lower.find("\n", idx)
            if line_end_idx == -1:
                line_end_idx = len(text_lower)
            single_line = text_lower[line_start:line_end_idx]
            allowed = any(disclaimer in single_line for disclaimer in ALLOWED_NEGATED_CLAIMS)
            if not allowed:
                violations.append(pattern)
            start = idx + 1

    return violations


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_codex_automatic_masking_claims_require_verified_matrix_proof() -> None:
    """CDX-03: Unsupported Codex masking claims must not appear in safe repo text."""
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
        pass
    else:
        if found_violations:
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
    assert violations == [], f"Allowed negated claim was incorrectly flagged: {violations}"


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
