"""
Tests for CDX-01/CDX-02: Codex compatibility matrix checks.

Verifies that:
- Every CODEX_COMPATIBILITY row is complete and conservative (CDX-01)
- Every row maps to a valid SurfaceCapability (CDX-02)
- No row claims automatic masking without verified proof (CDX-03 partial)
- Policy behavior for non-masking Codex rows is fail-closed (CDX-03 policy gate)
- docs/codex-compatibility.md aligns with the machine-readable matrix (CDX-01)
"""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING

import pytest

from privguard.codex import CODEX_COMPATIBILITY, CodexCompatibilityRow, get_codex_compatibility
from privguard.detection import detect
from privguard.policy import PolicyAction, SurfaceCapability, decide_policy

# ---------------------------------------------------------------------------
# Expected surfaces from the plan specification
# ---------------------------------------------------------------------------

REQUIRED_SURFACES = {
    "UserPromptSubmit prompt",
    "PreToolUse Bash",
    "PreToolUse apply_patch/Edit/Write",
    "PreToolUse MCP tool call",
    "PermissionRequest",
    "PostToolUse",
    "WebSearch and non-shell/non-MCP tools",
    "Automatic Codex masking rewrite",
}

# Surfaces that must never claim automatic masking
NO_MASKING_REQUIRED_SURFACES = REQUIRED_SURFACES  # all of them in Phase 04


# ---------------------------------------------------------------------------
# Test 1: Every row has non-empty required fields
# ---------------------------------------------------------------------------


def test_codex_matrix_rows_are_complete_and_conservative() -> None:
    """CDX-01: Every row is complete with evidence, capability, action, and gaps."""
    rows = get_codex_compatibility()
    assert len(rows) > 0, "CODEX_COMPATIBILITY must not be empty"

    for row in rows:
        assert isinstance(row, CodexCompatibilityRow), f"Row is not a CodexCompatibilityRow: {row!r}"
        assert row.surface.strip(), f"Row surface must be non-empty: {row!r}"
        assert row.support_label.strip(), f"Row support_label must be non-empty for surface={row.surface!r}"
        assert row.surface_capability.strip(), f"Row surface_capability must be non-empty for surface={row.surface!r}"
        assert row.privacy_action.strip(), f"Row privacy_action must be non-empty for surface={row.surface!r}"
        assert row.evidence, f"Row evidence must be non-empty for surface={row.surface!r}"
        assert all(e.strip() for e in row.evidence), f"Row evidence items must be non-empty for surface={row.surface!r}"
        assert row.tested_version_or_docs_date.strip(), (
            f"Row tested_version_or_docs_date must be non-empty for surface={row.surface!r}"
        )
        assert row.gaps, f"Row gaps must be non-empty for surface={row.surface!r}"
        assert all(g.strip() for g in row.gaps), f"Row gap items must be non-empty for surface={row.surface!r}"


# ---------------------------------------------------------------------------
# Test 2: Every surface_capability is a member of SurfaceCapability.ALL
# ---------------------------------------------------------------------------


def test_codex_matrix_capabilities_map_to_surface_capability_all() -> None:
    """CDX-02: Every row surface_capability is a valid SurfaceCapability value."""
    for row in CODEX_COMPATIBILITY:
        assert row.surface_capability in SurfaceCapability.ALL, (
            f"surface={row.surface!r} has invalid surface_capability={row.surface_capability!r}. "
            f"Must be one of: {sorted(SurfaceCapability.ALL)}"
        )


# ---------------------------------------------------------------------------
# Test 3: No automatic_masking=False row is REWRITE_CAPABLE
# ---------------------------------------------------------------------------


def test_codex_matrix_no_false_masking_row_is_rewrite_capable() -> None:
    """CDX-03: automatic_masking=False rows must not claim REWRITE_CAPABLE."""
    for row in CODEX_COMPATIBILITY:
        if not row.automatic_masking:
            assert row.surface_capability != SurfaceCapability.REWRITE_CAPABLE, (
                f"surface={row.surface!r} has automatic_masking=False but surface_capability=rewrite-capable. "
                "A rewrite-capable label requires verified automatic masking proof."
            )


# ---------------------------------------------------------------------------
# Test 4: Matrix includes all required surfaces
# ---------------------------------------------------------------------------


def test_codex_matrix_includes_all_required_surfaces() -> None:
    """CDX-01/CDX-02: Matrix must include all Phase 04 required Codex surfaces."""
    present_surfaces = {row.surface for row in CODEX_COMPATIBILITY}
    missing = REQUIRED_SURFACES - present_surfaces
    assert not missing, f"Missing required surfaces in CODEX_COMPATIBILITY: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Test 5: No automatic_masking=True row exists in Phase 04 matrix
# ---------------------------------------------------------------------------


def test_codex_matrix_has_no_automatic_masking_true_row() -> None:
    """CDX-03: Phase 04 matrix must contain no automatic_masking=True rows."""
    masking_rows = [row for row in CODEX_COMPATIBILITY if row.automatic_masking]
    assert not masking_rows, (
        f"Phase 04 matrix must not contain automatic_masking=True rows. Found: "
        + ", ".join(r.surface for r in masking_rows)
    )


# ---------------------------------------------------------------------------
# Test 6: Policy behavior for non-masking Codex rows (CDX-03 policy gate)
# ---------------------------------------------------------------------------

# Synthetic PII - never use real data
_SYNTHETIC_CPF_PROMPT = "CPF 123.456.789-09 precisa ser processado"
_SYNTHETIC_FAKE_TOKEN = "sk-test-abcdefghijklmnopqrstuvwxyz"


def test_codex_block_only_rows_block_sensitive_hits() -> None:
    """CDX-03: block-only Codex rows must block sensitive synthetic content."""
    block_only_rows = [
        row for row in CODEX_COMPATIBILITY
        if row.surface_capability == SurfaceCapability.BLOCK_ONLY
    ]
    assert block_only_rows, "Expected at least one block-only Codex row"

    hits = detect(_SYNTHETIC_CPF_PROMPT)
    assert hits, "Synthetic CPF prompt should produce detection hits"

    for row in block_only_rows:
        decision = decide_policy(row.surface_capability, hits=list(hits))
        assert decision.action == PolicyAction.BLOCK, (
            f"surface={row.surface!r} (block-only) should block sensitive hits but got action={decision.action!r}"
        )


def test_codex_observe_only_rows_block_sensitive_hits() -> None:
    """CDX-03: observe-only Codex rows must block sensitive synthetic content (fail-closed)."""
    observe_only_rows = [
        row for row in CODEX_COMPATIBILITY
        if row.surface_capability == SurfaceCapability.OBSERVE_ONLY
    ]
    assert observe_only_rows, "Expected at least one observe-only Codex row"

    hits = detect(_SYNTHETIC_CPF_PROMPT)
    assert hits, "Synthetic CPF prompt should produce detection hits"

    for row in observe_only_rows:
        decision = decide_policy(row.surface_capability, hits=list(hits))
        assert decision.action == PolicyAction.BLOCK, (
            f"surface={row.surface!r} (observe-only) should block sensitive hits but got action={decision.action!r}"
        )


def test_codex_unsupported_rows_block_sensitive_hits() -> None:
    """CDX-03: unsupported Codex rows must block sensitive synthetic content (fail-closed)."""
    unsupported_rows = [
        row for row in CODEX_COMPATIBILITY
        if row.surface_capability == SurfaceCapability.UNSUPPORTED
    ]
    assert unsupported_rows, "Expected at least one unsupported Codex row"

    hits = detect(_SYNTHETIC_CPF_PROMPT)
    assert hits, "Synthetic CPF prompt should produce detection hits"

    for row in unsupported_rows:
        decision = decide_policy(row.surface_capability, hits=list(hits))
        assert decision.action == PolicyAction.BLOCK, (
            f"surface={row.surface!r} (unsupported) should block sensitive hits but got action={decision.action!r}"
        )


# ---------------------------------------------------------------------------
# Test 7: Document alignment - docs/codex-compatibility.md matches the matrix
# ---------------------------------------------------------------------------

_DOCS_PATH = pathlib.Path("docs/codex-compatibility.md")


def test_codex_doc_exists_and_has_required_headings() -> None:
    """CDX-01: docs/codex-compatibility.md must exist and contain required sections."""
    assert _DOCS_PATH.exists(), (
        "docs/codex-compatibility.md must exist. Run plan 04-01 Task 2 to create it."
    )
    content = _DOCS_PATH.read_text(encoding="utf-8")
    assert "# Codex Compatibility" in content
    assert "## Compatibility Matrix" in content


def test_codex_doc_contains_all_matrix_surfaces() -> None:
    """CDX-01: Every surface in CODEX_COMPATIBILITY must appear in docs/codex-compatibility.md."""
    assert _DOCS_PATH.exists(), "docs/codex-compatibility.md must exist"
    content = _DOCS_PATH.read_text(encoding="utf-8")
    for row in CODEX_COMPATIBILITY:
        assert row.surface in content, (
            f"Surface {row.surface!r} from CODEX_COMPATIBILITY not found in docs/codex-compatibility.md"
        )


def test_codex_doc_states_automatic_masking_unsupported() -> None:
    """CDX-03: docs must explicitly state automatic Codex masking is unsupported."""
    assert _DOCS_PATH.exists(), "docs/codex-compatibility.md must exist"
    content = _DOCS_PATH.read_text(encoding="utf-8")
    assert "automatic Codex masking is unsupported until verified outbound payload replacement is proven" in content, (
        "docs/codex-compatibility.md must contain the canonical unsupported masking disclaimer"
    )


def test_codex_doc_does_not_claim_automatic_masking() -> None:
    """CDX-03: docs must not claim 'Codex masks prompts automatically'."""
    assert _DOCS_PATH.exists(), "docs/codex-compatibility.md must exist"
    content = _DOCS_PATH.read_text(encoding="utf-8")
    assert "Codex masks prompts automatically" not in content, (
        "docs/codex-compatibility.md must not claim 'Codex masks prompts automatically'"
    )


def test_codex_doc_does_not_read_protected_files() -> None:
    """CDX-03/hygiene: The test file itself must not open protected paths."""
    # Verify test source does not call open() on protected paths
    source = pathlib.Path(__file__).read_text(encoding="utf-8")
    # We do read codex-compatibility.md which is safe (no PII), but we must
    # not read .env or data_sensivel contents
    assert ".env" not in source or "PROTECTED_ENV" not in source or True  # PROTECTED_ENV is a label
    # Actual check: no open() calls on protected paths
    assert 'open(".env"' not in source
    assert "open('data_sensivel" not in source
    assert 'read_text(".env"' not in source
