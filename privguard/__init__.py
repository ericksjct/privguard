"""Local privacy guard package for code-agent workflows."""

from .detection import DetectionReport, Hit, analyze_text, detect
from .diagnostics import format_text, to_json
from .masking import MaskResult, mask_text, redact, verify_mask
from .policy import (
    PathClassification,
    PolicyAction,
    PolicyDecision,
    PolicyMode,
    SurfaceCapability,
    classify_path,
    decide_policy,
    is_sensitive_path,
)

__version__ = "0.1.0"

__all__ = [
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
    "classify_path",
    "decide_policy",
    "detect",
    "format_text",
    "is_sensitive_path",
    "mask_text",
    "redact",
    "to_json",
    "verify_mask",
]
