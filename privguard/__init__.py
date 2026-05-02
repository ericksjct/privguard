"""Local privacy guard package for code-agent workflows."""

from .detection import DetectionReport, Hit, analyze_text, detect
from .diagnostics import format_text, to_json
from .masking import MaskResult, mask_text, redact, verify_mask

__version__ = "0.1.0"

__all__ = [
    "DetectionReport",
    "Hit",
    "MaskResult",
    "__version__",
    "analyze_text",
    "detect",
    "format_text",
    "mask_text",
    "redact",
    "to_json",
    "verify_mask",
]
