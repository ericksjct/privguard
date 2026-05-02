"""Sanitized diagnostic serializers for detection, masking, and policy metadata."""

from __future__ import annotations

import json
from dataclasses import is_dataclass
from typing import Any

from .detection import DetectionReport, Hit
from .masking import MaskResult


def summarize_hits(hits: Any) -> list[dict[str, object]]:
    return [to_dict(hit) for hit in tuple(hits)]


def to_dict(value: Any) -> Any:
    if isinstance(value, Hit):
        return {
            "kind": value.kind,
            "start": value.start,
            "end": value.end,
            "score": value.score,
            "reason_code": value.reason_code,
            "source": value.source,
        }

    if isinstance(value, DetectionReport):
        return {
            "counts": dict(value.counts),
            "hits": summarize_hits(value.hits),
        }

    if isinstance(value, MaskResult):
        return {
            "changed": value.changed,
            "verified": value.verified,
            "verification_status": value.verification_status,
            "reason_codes": list(value.reason_codes),
            "hit_count": len(value.hits),
            "hits": summarize_hits(value.hits),
        }

    if isinstance(value, dict):
        return {str(k): to_dict(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [to_dict(item) for item in value]

    if is_dataclass(value):
        result: dict[str, Any] = {}
        for name in getattr(value, "__dataclass_fields__", {}):
            if name in {"value", "text"}:
                continue
            result[name] = to_dict(getattr(value, name))
        return result

    return value


def to_json(value: Any) -> str:
    return json.dumps(to_dict(value), ensure_ascii=False, sort_keys=True)


def format_hit_summary(hits: Any) -> str:
    return ", ".join(
        (
            f"{hit.kind}@{hit.start}:{hit.end} "
            f"score={hit.score:.2f} reason={hit.reason_code}"
        )
        for hit in tuple(hits)
    )


def format_text(value: Any) -> str:
    data = to_dict(value)

    if isinstance(data, dict) and "counts" in data:
        counts = data.get("counts") or {}
        total = sum(int(count) for count in counts.values())
        return f"detections={total} counts={counts}"

    if isinstance(data, dict) and "verification_status" in data:
        return (
            f"mask verified={data.get('verified')} "
            f"status={data.get('verification_status')} "
            f"reasons={data.get('reason_codes')}"
        )

    if isinstance(data, list):
        return ", ".join(str(item) for item in data)

    return str(data)
