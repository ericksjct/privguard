"""
Machine-readable Codex compatibility matrix.

Provides evidence-backed compatibility rows for OpenAI Codex CLI hook surfaces.
Every row maps to an existing SurfaceCapability value and documents support label,
evidence sources, privacy action, and remaining gaps.

No row claims automatic_masking=True in Phase 04 because outbound payload
replacement before provider submission has not been proven.

CDX-01: Documents current Codex interception options and block/rewrite status.
CDX-02: Compatibility matrix with conservative labels backed by evidence.
CDX-03: No automatic Codex masking claim until verified outbound replacement proven.
"""

from __future__ import annotations

from dataclasses import dataclass

from .policy import SurfaceCapability


@dataclass(frozen=True)
class CodexCompatibilityRow:
    """One row in the Codex compatibility matrix.

    Attributes:
        surface: Human-readable name of the Codex surface or event type.
        support_label: User-facing label (e.g. 'experimental block-only', 'unsupported').
        surface_capability: One of SurfaceCapability.ALL (maps to privguard policy).
        privacy_action: Short code describing what privguard does on this surface.
        evidence: Non-empty tuple of evidence sources justifying the label.
        tested_version_or_docs_date: Version string or docs check date for evidence.
        automatic_masking: True only if outbound payload replacement is proven before
            provider submission. Must never be True unless a synthetic E2E test proves
            payload == mask_text(payload).text before submission.
        gaps: Non-empty tuple of remaining gaps or uncertainties for this surface.
    """

    surface: str
    support_label: str
    surface_capability: str
    privacy_action: str
    evidence: tuple[str, ...]
    tested_version_or_docs_date: str
    automatic_masking: bool
    gaps: tuple[str, ...]


# ---------------------------------------------------------------------------
# Conservative support label vocabulary (user-facing)
# ---------------------------------------------------------------------------

class CodexSupportLabel:
    """User-facing support label vocabulary for Codex surfaces."""

    EXPERIMENTAL_BLOCK_ONLY = "experimental block-only"
    OBSERVE_ONLY = "observe-only"
    UNSUPPORTED = "unsupported"

    ALL = {
        EXPERIMENTAL_BLOCK_ONLY,
        OBSERVE_ONLY,
        UNSUPPORTED,
    }


# Backward-compatible alias
CODEX_SUPPORT_LABELS = CodexSupportLabel


# ---------------------------------------------------------------------------
# Phase 04 Codex compatibility matrix
#
# Evidence standard (D-01 through D-07):
#   - Positive block-capable labels require documented hook behavior AND local
#     codex-cli probe evidence.
#   - No surface uses automatic_masking=True because no synthetic E2E test has
#     proven that the outbound payload == mask_text(payload).text before any
#     external provider submission.
#   - All labels default to experimental until no-provider synthetic interception
#     proof is recorded.
# ---------------------------------------------------------------------------

CODEX_COMPATIBILITY: tuple[CodexCompatibilityRow, ...] = (
    # ------------------------------------------------------------------
    # UserPromptSubmit prompt
    # Codex hooks docs show `decision: "block"` and exit code 2 blocking.
    # Local codex-cli 0.128.0 observed. No no-provider synthetic proof yet.
    # ------------------------------------------------------------------
    CodexCompatibilityRow(
        surface="UserPromptSubmit prompt",
        support_label=CodexSupportLabel.EXPERIMENTAL_BLOCK_ONLY,
        surface_capability=SurfaceCapability.BLOCK_ONLY,
        privacy_action="block_sensitive_prompt_when_hook_observed",
        evidence=(
            "OpenAI Codex hooks docs 2026-05-03",
            "local codex-cli 0.128.0 version observed",
        ),
        tested_version_or_docs_date="codex-cli 0.128.0 / docs 2026-05-03",
        automatic_masking=False,
        gaps=(
            "no verified outbound payload rewrite",
            "no no-provider synthetic interception proof recorded",
        ),
    ),

    # ------------------------------------------------------------------
    # PreToolUse Bash
    # Docs show matcher support for Bash and tool_input.command.
    # Official docs note incomplete shell interception for unified_exec.
    # ------------------------------------------------------------------
    CodexCompatibilityRow(
        surface="PreToolUse Bash",
        support_label=CodexSupportLabel.EXPERIMENTAL_BLOCK_ONLY,
        surface_capability=SurfaceCapability.BLOCK_ONLY,
        privacy_action="block_protected_path_or_inline_pii_in_bash_command",
        evidence=(
            "OpenAI Codex hooks docs 2026-05-03",
            "local codex-cli 0.128.0 version observed",
        ),
        tested_version_or_docs_date="codex-cli 0.128.0 / docs 2026-05-03",
        automatic_masking=False,
        gaps=(
            "incomplete shell coverage for newer unified_exec path",
            "no verified outbound payload rewrite",
            "Windows shell behavior not confirmed via local probe",
        ),
    ),

    # ------------------------------------------------------------------
    # PreToolUse apply_patch/Edit/Write
    # Docs say apply_patch can match Edit and Write aliases.
    # Payload shape for file contents needs local fixture confirmation.
    # ------------------------------------------------------------------
    CodexCompatibilityRow(
        surface="PreToolUse apply_patch/Edit/Write",
        support_label=CodexSupportLabel.EXPERIMENTAL_BLOCK_ONLY,
        surface_capability=SurfaceCapability.BLOCK_ONLY,
        privacy_action="block_protected_path_edit_when_event_payload_exposes_path",
        evidence=(
            "OpenAI Codex hooks docs 2026-05-03",
            "local codex-cli 0.128.0 version observed",
        ),
        tested_version_or_docs_date="codex-cli 0.128.0 / docs 2026-05-03",
        automatic_masking=False,
        gaps=(
            "payload shape for file contents not confirmed via local fixture",
            "no verified outbound payload rewrite",
            "apply_patch alias coverage for Edit/Write not locally verified",
        ),
    ),

    # ------------------------------------------------------------------
    # PreToolUse MCP tool call
    # Docs list MCP tool names as matchable with tool_input args.
    # MCP schemas vary by server; conservative blocking only.
    # ------------------------------------------------------------------
    CodexCompatibilityRow(
        surface="PreToolUse MCP tool call",
        support_label=CodexSupportLabel.EXPERIMENTAL_BLOCK_ONLY,
        surface_capability=SurfaceCapability.BLOCK_ONLY,
        privacy_action="block_known_payload_schemas_or_conservative_string_scan",
        evidence=(
            "OpenAI Codex hooks docs 2026-05-03",
            "local codex-cli 0.128.0 version observed",
        ),
        tested_version_or_docs_date="codex-cli 0.128.0 / docs 2026-05-03",
        automatic_masking=False,
        gaps=(
            "MCP schemas vary by server; false-negative risk for opaque args",
            "variable MCP payload shapes not locally verified",
            "no verified outbound payload rewrite",
        ),
    ),

    # ------------------------------------------------------------------
    # PermissionRequest
    # Docs allow deny decisions for approval requests. Runs only when Codex
    # is about to ask for approval; commands that skip approval bypass this.
    # ------------------------------------------------------------------
    CodexCompatibilityRow(
        surface="PermissionRequest",
        support_label=CodexSupportLabel.OBSERVE_ONLY,
        surface_capability=SurfaceCapability.OBSERVE_ONLY,
        privacy_action="secondary_deny_signal_not_primary_privacy_boundary",
        evidence=(
            "OpenAI Codex hooks docs 2026-05-03",
            "local codex-cli 0.128.0 version observed",
        ),
        tested_version_or_docs_date="codex-cli 0.128.0 / docs 2026-05-03",
        automatic_masking=False,
        gaps=(
            "commands not requiring approval do not hit PermissionRequest",
            "cannot substitute for PreToolUse as primary privacy boundary",
        ),
    ),

    # ------------------------------------------------------------------
    # PostToolUse
    # Docs say it runs after supported tools and cannot undo side effects.
    # Not a pre-exfiltration control.
    # ------------------------------------------------------------------
    CodexCompatibilityRow(
        surface="PostToolUse",
        support_label=CodexSupportLabel.OBSERVE_ONLY,
        surface_capability=SurfaceCapability.OBSERVE_ONLY,
        privacy_action="observe_only_cannot_undo_prior_tool_side_effects",
        evidence=(
            "OpenAI Codex hooks docs 2026-05-03",
            "local codex-cli 0.128.0 version observed",
        ),
        tested_version_or_docs_date="codex-cli 0.128.0 / docs 2026-05-03",
        automatic_masking=False,
        gaps=(
            "cannot protect data already exfiltrated by prior tool execution",
            "not a pre-exfiltration control",
        ),
    ),

    # ------------------------------------------------------------------
    # WebSearch and non-shell/non-MCP tools
    # Official docs state these are not intercepted by current hook coverage.
    # ------------------------------------------------------------------
    CodexCompatibilityRow(
        surface="WebSearch and non-shell/non-MCP tools",
        support_label=CodexSupportLabel.UNSUPPORTED,
        surface_capability=SurfaceCapability.UNSUPPORTED,
        privacy_action="do_not_claim_protection_unsupported_surface",
        evidence=(
            "OpenAI Codex hooks docs 2026-05-03: incomplete non-shell/non-MCP coverage documented",
            "local codex-cli 0.128.0 version observed",
        ),
        tested_version_or_docs_date="codex-cli 0.128.0 / docs 2026-05-03",
        automatic_masking=False,
        gaps=(
            "no hook interception documented for WebSearch or other non-shell/non-MCP paths",
            "requires future official support before any privacy protection label upgrade",
        ),
    ),

    # ------------------------------------------------------------------
    # Automatic Codex masking rewrite
    # Docs show blocking and context addition; cited tool rewrite fields
    # are reserved/unsupported. No proof that outbound payload equals
    # mask_text(payload).text before provider submission.
    # ------------------------------------------------------------------
    CodexCompatibilityRow(
        surface="Automatic Codex masking rewrite",
        support_label=CodexSupportLabel.UNSUPPORTED,
        surface_capability=SurfaceCapability.UNSUPPORTED,
        privacy_action="do_not_claim_masking",
        evidence=(
            "OpenAI Codex hooks docs 2026-05-03: updatedInput and rewrite fields reserved/unsupported",
            "local codex-cli 0.128.0 version observed",
        ),
        tested_version_or_docs_date="codex-cli 0.128.0 / docs 2026-05-03",
        automatic_masking=False,
        gaps=(
            "requires proof outbound payload equals verified masked payload before provider submission",
            "no synthetic E2E test proves payload == mask_text(payload).text pre-submission",
        ),
    ),
)


def get_codex_compatibility() -> tuple[CodexCompatibilityRow, ...]:
    """Return the full Codex compatibility matrix.

    Returns a tuple of CodexCompatibilityRow instances representing the current
    Phase 04 evidence-backed compatibility assessment for Codex CLI surfaces.

    No row in this matrix claims automatic_masking=True. Automatic Codex masking
    is unsupported until verified outbound payload replacement is proven.
    """
    return CODEX_COMPATIBILITY
