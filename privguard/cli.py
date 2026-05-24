"""Command-line interface for privguard diagnostics."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

from . import __version__
from .cleanup import main as cleanup_main
from .detection import analyze_text, detect
from .diagnostics import (
    build_claude_doctor_report,
    claude_doctor_passed,
    format_claude_doctor_text,
    format_text,
    to_dict,
    to_json,
)
from .masking import mask_text
from .policy import SurfaceCapability, classify_path, decide_policy


def cmd_info(_args: argparse.Namespace) -> int:
    try:
        package_version = version("privguard")
    except PackageNotFoundError:
        package_version = __version__

    print(f"privguard {package_version}")
    print("detectors: lightweight")
    print("optional_full: available via privguard[full]")
    return 0


def _read_text(args: argparse.Namespace) -> str:
    text = getattr(args, "text", None)
    if text is None:
        return sys.stdin.read()
    import os
    if os.path.isfile(text):
        with open(text, encoding="utf-8") as fh:
            return fh.read()
    return text


def cmd_scan(args: argparse.Namespace) -> int:
    lenient = True if args.lenient else None
    detect_names = True if args.detect_names else None
    report = analyze_text(_read_text(args), lenient=lenient, detect_names=detect_names)
    if args.json:
        print(to_json(report))
    else:
        print(format_text(report))
    return 0


def cmd_mask(args: argparse.Namespace) -> int:
    """Mask PII in text.

    Exit codes:
      0 — masking verified; output on stdout is safe to forward.
      2 — masking unverified; output goes to stderr only; do NOT forward.
    """
    lenient = True if args.lenient else None
    detect_names = True if args.detect_names else None
    result = mask_text(_read_text(args), lenient=lenient, detect_names=detect_names)
    if not result.verified:
        if args.json:
            print(to_json(result), file=sys.stderr)
        else:
            print(
                f"mask verification failed: {result.verification_status} "
                f"reasons={list(result.reason_codes)}",
                file=sys.stderr,
            )
        return 2
    if args.json:
        print(to_json(result))
    else:
        print(result.text)
    return 0


def cmd_policy_check(args: argparse.Namespace) -> int:
    text = _read_text(args)
    lenient = True if args.lenient else None
    detect_names = True if args.detect_names else None
    hits = detect(text, lenient=lenient, detect_names=detect_names)
    mask_result = mask_text(text, hits=hits) if args.masked else None
    path_classification = classify_path(args.path) if args.path else None
    decision = decide_policy(
        capability=args.capability,
        hits=hits,
        mask_result=mask_result,
        path_classification=path_classification,
        payload_text=mask_result.text if mask_result is not None else text,
    )
    payload = {
        "decision": to_dict(decision),
        "path": to_dict(path_classification) if path_classification else None,
    }

    if args.json:
        print(to_json(payload))
    else:
        print(format_text(payload))
    return 0 if decision.allow else 2


def cmd_claude_doctor(args: argparse.Namespace) -> int:
    report = build_claude_doctor_report(args.settings)
    if args.json:
        print(to_json(report))
    else:
        print(format_claude_doctor_text(report))
    return 0 if claude_doctor_passed(report) else 2


def cmd_cleanup(args: argparse.Namespace) -> int:
    return cleanup_main(args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="privguard")
    subparsers = parser.add_subparsers(required=True)

    info = subparsers.add_parser("info")
    info.set_defaults(func=cmd_info)

    scan = subparsers.add_parser("scan")
    scan.add_argument("text", nargs="?")
    scan.add_argument("--json", action="store_true")
    scan.add_argument(
        "--lenient",
        action="store_true",
        default=False,
        help="Mask DDD.DDD.DDD-DD CPF patterns regardless of checksum (opt-in).",
    )
    scan.add_argument(
        "--detect-names",
        action="store_true",
        default=False,
        help="Detect Brazilian person names using IBGE 2010 census data (opt-in).",
    )
    scan.set_defaults(func=cmd_scan)

    mask = subparsers.add_parser("mask")
    mask.add_argument("text", nargs="?")
    mask.add_argument("--json", action="store_true")
    mask.add_argument(
        "--lenient",
        action="store_true",
        default=False,
        help="Mask DDD.DDD.DDD-DD CPF patterns regardless of checksum (opt-in).",
    )
    mask.add_argument(
        "--detect-names",
        action="store_true",
        default=False,
        help="Detect Brazilian person names using IBGE 2010 census data (opt-in).",
    )
    mask.set_defaults(func=cmd_mask)

    policy = subparsers.add_parser("policy-check")
    policy.add_argument("text", nargs="?")
    policy.add_argument("--json", action="store_true")
    policy.add_argument("--path")
    policy.add_argument("--masked", action="store_true")
    policy.add_argument(
        "--capability",
        choices=sorted(SurfaceCapability.ALL),
        default=SurfaceCapability.UNKNOWN,
    )
    policy.add_argument(
        "--lenient",
        action="store_true",
        default=False,
        help="Mask DDD.DDD.DDD-DD CPF patterns regardless of checksum (opt-in).",
    )
    policy.add_argument(
        "--detect-names",
        action="store_true",
        default=False,
        help="Detect Brazilian person names using IBGE 2010 census data (opt-in).",
    )
    policy.set_defaults(func=cmd_policy_check)

    cleanup = subparsers.add_parser("cleanup")
    cleanup.add_argument(
        "--apply",
        action="store_true",
        help="Actually delete (default is dry-run preview).",
    )
    cleanup.set_defaults(func=cmd_cleanup)

    claude = subparsers.add_parser("claude")
    claude_subparsers = claude.add_subparsers(required=True)

    doctor = claude_subparsers.add_parser("doctor")
    doctor.add_argument("--json", action="store_true")
    doctor.add_argument("--settings", default=".claude/settings.json")
    doctor.set_defaults(func=cmd_claude_doctor)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
