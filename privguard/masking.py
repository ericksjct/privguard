"""Irreversible masking helpers for detected sensitive spans."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Sequence

from .detection import Hit, detect


@dataclass(frozen=True)
class MaskResult:
    text: str
    changed: bool
    verified: bool
    verification_status: str
    reason_codes: tuple[str, ...]
    hits: tuple[Hit, ...]


PLACEHOLDER_ASSIGNMENT = re.compile(
    r"^\s*[A-Za-z_][\w-]*\s*[:=]\s*<[A-Z][A-Z0-9_]*>\s*$"
)


def _replace_spans(text: str, hits: Sequence[Hit]) -> str:
    out = []
    cursor = 0
    for h in hits:
        out.append(text[cursor:h.start])
        out.append(f"<{h.kind}>")
        cursor = h.end
    out.append(text[cursor:])
    return "".join(out)


def _normalize_hits(hits: Sequence[Hit]) -> tuple[Hit, ...]:
    ordered = sorted(hits, key=lambda h: (h.start, -(h.end - h.start)))
    kept: list[Hit] = []
    cursor = -1
    for hit in ordered:
        if hit.start < cursor:
            continue
        kept.append(hit)
        cursor = hit.end
    return tuple(kept)


def _is_safe_placeholder_residual(value: str) -> bool:
    return bool(PLACEHOLDER_ASSIGNMENT.fullmatch(value))


def verify_mask(
    original_text: str,
    masked_text: str,
    hits: Sequence[Hit],
    min_score: float = 0.6,
    detect_names: bool | None = None,
) -> tuple[bool, tuple[str, ...]]:
    reason_codes: list[str] = []

    for hit in hits:
        if hit.value and hit.value in masked_text:
            reason_codes.append("original_value_remaining")

    residual_hits = [
        hit for hit in detect(masked_text, min_score=min_score, detect_names=detect_names)
        if not _is_safe_placeholder_residual(hit.value)
    ]
    if residual_hits:
        reason_codes.append("residual_detection")

    if reason_codes:
        return False, tuple(dict.fromkeys(reason_codes))

    if not hits:
        return True, ("no_sensitive_hits",)
    return True, ("mask_verified",)


def mask_text(
    text: str,
    hits: Sequence[Hit] | None = None,
    min_score: float = 0.6,
    lenient: bool | None = None,
    detect_names: bool | None = None,
) -> MaskResult:
    selected_hits = _normalize_hits(
        hits if hits is not None else detect(
            text, min_score=min_score, lenient=lenient, detect_names=detect_names
        )
    )
    masked_text = _replace_spans(text, selected_hits)
    verified, verification_reasons = verify_mask(
        text,
        masked_text,
        selected_hits,
        min_score=min_score,
        detect_names=detect_names,
    )
    hit_reasons = tuple(hit.reason_code for hit in selected_hits if hit.reason_code)
    reason_codes = tuple(dict.fromkeys((*hit_reasons, *verification_reasons)))
    status = "verified" if verified else "failed"

    return MaskResult(
        text=masked_text,
        changed=masked_text != text,
        verified=verified,
        verification_status=status,
        reason_codes=reason_codes,
        hits=selected_hits,
    )


def redact(text: str, hits: list[Hit]) -> str:
    result = mask_text(text, hits=hits)
    if not result.verified:
        raise ValueError("mask verification failed")
    return result.text
