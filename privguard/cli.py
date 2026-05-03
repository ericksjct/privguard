"""Command-line interface for privguard diagnostics."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version

from . import __version__
from .detection import analyze_text, detect
from .diagnostics import format_text, to_dict, to_json
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
    if getattr(args, "text", None) is not None:
        return args.text
    return sys.stdin.read()


def cmd_scan(args: argparse.Namespace) -> int:
    report = analyze_text(_read_text(args))
    if args.json:
        print(to_json(report))
    else:
        print(format_text(report))
    return 0


def cmd_mask(args: argparse.Namespace) -> int:
    result = mask_text(_read_text(args))
    if args.json:
        print(to_json(result))
    else:
        print(result.text)
    return 0 if result.verified else 2


def cmd_policy_check(args: argparse.Namespace) -> int:
    text = _read_text(args)
    hits = detect(text)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="privguard")
    subparsers = parser.add_subparsers(required=True)

    info = subparsers.add_parser("info")
    info.set_defaults(func=cmd_info)

    scan = subparsers.add_parser("scan")
    scan.add_argument("text", nargs="?")
    scan.add_argument("--json", action="store_true")
    scan.set_defaults(func=cmd_scan)

    mask = subparsers.add_parser("mask")
    mask.add_argument("text", nargs="?")
    mask.add_argument("--json", action="store_true")
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
    policy.set_defaults(func=cmd_policy_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
