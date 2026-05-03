"""Policy helpers for protected paths and sanitized diagnostics."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from .detection import DetectionReport, Hit
from .diagnostics import format_hit_summary as _format_hit_summary
from .diagnostics import summarize_hits as _summarize_hits
from .masking import MaskResult

SENSITIVE_GLOBS = [
    re.compile(r"(?:^|[\\/])data_sensivel(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])cooperados(?:[\\/]|$)", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])dump_[\w\-]+\.[a-z]+$", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])\.env(?:\.[\w\-]+)?$", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])(?:credentials?|credenciais?)[\w\-.]*", re.IGNORECASE),
    re.compile(r"(?:^|[\\/])(?:secret|segredo|token|key)[\w\-.]*", re.IGNORECASE),
]


@dataclass(frozen=True)
class PathClassification:
    is_protected: bool
    category: str
    reason_code: str


class SurfaceCapability:
    REWRITE_CAPABLE = "rewrite-capable"
    BLOCK_ONLY = "block-only"
    OBSERVE_ONLY = "observe-only"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    EXTERNAL = "external"

    ALL = {
        REWRITE_CAPABLE,
        BLOCK_ONLY,
        OBSERVE_ONLY,
        UNSUPPORTED,
        UNKNOWN,
        EXTERNAL,
    }


class PolicyMode:
    STRICT = "strict"
    PERMISSIVE = "permissive"


class PolicyAction:
    ALLOW = "allow"
    BLOCK = "block"
    PAUSE = "pause"


@dataclass(frozen=True)
class PolicyDecision:
    action: str
    allow: bool
    reason_codes: tuple[str, ...]
    capability: str
    hit_count: int = 0
    protected_path: bool = False

READ_CMDS = re.compile(
    r"\b(?:cat|type|less|more|head|tail|"
    r"Get-Content|gc|Select-String|sls|findstr|"
    r"python(?:3)?(?:\s+-c)?|node\s+-e)\b",
    re.IGNORECASE,
)

EXFIL_CMDS = re.compile(
    r"\b(?:curl|wget|Invoke-WebRequest|iwr|Invoke-RestMethod|irm|"
    r"nc|ncat|netcat)\b",
    re.IGNORECASE,
)


def _normalize_path(path: str) -> str:
    value = str(path or "").strip().strip("\"'")
    value = value.replace("\\", "/")
    value = re.sub(r"/+", "/", value)
    parts: list[str] = []
    for part in value.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    prefix = "/" if value.startswith("/") else ""
    return (prefix + "/".join(parts)).lower()


def classify_path(path: str) -> PathClassification:
    p = _normalize_path(path)
    name = p.rsplit("/", 1)[-1] if p else ""

    if not p:
        return PathClassification(False, "empty", "path_empty")
    if name == ".env" or name.startswith(".env."):
        return PathClassification(True, "env_file", "protected_path_env")
    if re.search(r"(?:^|/)data_sensivel(?:/|$)", p) or re.search(r"(?:^|/)cooperados(?:/|$)", p):
        return PathClassification(True, "protected_data", "protected_path_data")
    if re.match(r"dump_[\w\-]+\.[a-z0-9]+$", name):
        return PathClassification(True, "dump_file", "protected_path_dump")
    # Word-boundary patterns: tokens must appear as a discrete word in the
    # filename (separated by ., _, -, or at start/end of stem) to avoid
    # false-positives on names like tokenizer.py, keychain.md, secretary.txt.
    if re.search(r"(?:^|[._-])(?:credentials?|credenciais?)(?:[._-]|$)", name):
        return PathClassification(True, "credentials_file", "protected_path_credentials")
    if re.search(r"(?:^|[._-])(?:secret|segredo|token|key|api[._-]?key)(?:[._-]|$)", name):
        return PathClassification(True, "secret_filename", "protected_path_secret_name")
    return PathClassification(False, "unprotected", "path_unprotected")


def is_sensitive_path(path: str) -> bool:
    return classify_path(path).is_protected


def _hits_from(
    hits: Sequence[Hit] | None = None,
    report: DetectionReport | None = None,
) -> tuple[Hit, ...]:
    if report is not None:
        return tuple(report.hits)
    return tuple(hits or ())


def _decision(
    action: str,
    capability: str,
    reason_codes: Sequence[str],
    hit_count: int,
    protected_path: bool = False,
) -> PolicyDecision:
    return PolicyDecision(
        action=action,
        allow=action == PolicyAction.ALLOW,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        capability=capability,
        hit_count=hit_count,
        protected_path=protected_path,
    )


def decide_policy(
    capability: str = SurfaceCapability.UNKNOWN,
    hits: Sequence[Hit] | None = None,
    report: DetectionReport | None = None,
    mask_result: MaskResult | None = None,
    path_classification: PathClassification | None = None,
    mode: str = PolicyMode.STRICT,
    payload_text: str | None = None,
) -> PolicyDecision:
    normalized_capability = capability if capability in SurfaceCapability.ALL else SurfaceCapability.UNKNOWN
    selected_hits = _hits_from(hits=hits, report=report)
    hit_count = len(selected_hits)
    protected_path = bool(path_classification and path_classification.is_protected)
    reasons: list[str] = []

    if path_classification is not None:
        reasons.append(path_classification.reason_code)
        if path_classification.is_protected:
            return _decision(
                PolicyAction.BLOCK,
                normalized_capability,
                (*reasons, "protected_path"),
                hit_count,
                protected_path=True,
            )

    if mask_result is not None:
        reasons.extend(mask_result.reason_codes)
        if not mask_result.verified:
            return _decision(
                PolicyAction.PAUSE,
                normalized_capability,
                (*reasons, "mask_unverified"),
                hit_count or len(mask_result.hits),
                protected_path,
            )

    if normalized_capability == SurfaceCapability.REWRITE_CAPABLE:
        if hit_count == 0:
            return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "no_sensitive_hits"), 0, protected_path)
        if mask_result and mask_result.verified:
            return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "mask_verified"), hit_count, protected_path)
        return _decision(PolicyAction.PAUSE, normalized_capability, (*reasons, "mask_required"), hit_count, protected_path)

    if normalized_capability == SurfaceCapability.BLOCK_ONLY:
        if hit_count:
            return _decision(PolicyAction.BLOCK, normalized_capability, (*reasons, "sensitive_hits_block_only"), hit_count, protected_path)
        return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "no_sensitive_hits"), 0, protected_path)

    if normalized_capability in {SurfaceCapability.UNKNOWN, SurfaceCapability.EXTERNAL}:
        payload_matches_mask = (
            mask_result is not None
            and payload_text is not None
            and payload_text == mask_result.text
        )
        if mask_result and mask_result.verified and payload_matches_mask:
            return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "mask_verified", "payload_masked"), hit_count, protected_path)
        if mode == PolicyMode.PERMISSIVE and hit_count == 0:
            return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "permissive_no_sensitive_hits"), 0, protected_path)
        return _decision(PolicyAction.BLOCK, normalized_capability, (*reasons, "fail_closed_surface"), hit_count, protected_path)

    if normalized_capability in {SurfaceCapability.OBSERVE_ONLY, SurfaceCapability.UNSUPPORTED}:
        if hit_count:
            return _decision(PolicyAction.BLOCK, normalized_capability, (*reasons, "cannot_protect_sensitive_hits"), hit_count, protected_path)
        return _decision(PolicyAction.ALLOW, normalized_capability, (*reasons, "no_sensitive_hits"), 0, protected_path)

    return _decision(PolicyAction.BLOCK, SurfaceCapability.UNKNOWN, (*reasons, "fail_closed_surface"), hit_count, protected_path)


def summarize_hits(hits: list[Hit]) -> list[dict[str, object]]:
    return _summarize_hits(hits)


def format_hit_summary(hits: list[Hit]) -> str:
    return _format_hit_summary(hits)
