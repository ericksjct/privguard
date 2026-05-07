"""Local privacy guard package for code-agent workflows."""

from .codex import (
    CODEX_COMPATIBILITY,
    CodexCompatibilityRow,
    CodexSupportLabel,
    get_codex_compatibility,
)
from .detection import DetectionReport, Hit, analyze_text, detect
from .diagnostics import build_claude_doctor_report, format_text, to_json
from .hooks import main_pre_tool, main_user_prompt
from .masking import MaskResult, mask_text, redact, verify_mask
from .policy import (
    CommandClassification,
    PathClassification,
    PolicyAction,
    PolicyDecision,
    PolicyMode,
    SurfaceCapability,
    classify_command,
    classify_path,
    decide_policy,
    is_sensitive_path,
)

__version__ = "0.1.0"

__all__ = [
    "CODEX_COMPATIBILITY",
    "CodexCompatibilityRow",
    "CodexSupportLabel",
    "CommandClassification",
    "DetectionReport",
    "Hit",
    "MaskResult",
    "PathClassification",
    "PolicyAction",
    "PolicyDecision",
    "PolicyMode",
    "SurfaceCapability",
    "__version__",
    "analyze_text",
    "build_claude_doctor_report",
    "classify_command",
    "classify_path",
    "decide_policy",
    "detect",
    "format_text",
    "get_codex_compatibility",
    "is_sensitive_path",
    "main_pre_tool",
    "main_user_prompt",
    "mask_text",
    "redact",
    "to_json",
    "verify_mask",
]
