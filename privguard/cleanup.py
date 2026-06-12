"""Config-driven repo cleanup with hardcoded protected list and fail-closed posture."""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # 3.10 fallback per D-16
    import tomli as tomllib  # type: ignore[no-redef]


# D-09: hardcoded protected list — cannot be overridden by pyproject.toml.
_PROTECTED: tuple[str, ...] = (
    ".env",
    ".env.*",
    "data_sensivel/",
    ".planning/",
    ".git/",
    "privguard/",
    "tests/",
    "hooks/",
    "demos/",
    "docs/",
    "pyproject.toml",
    "AGENTS.md",
    "README.md",
    "README.en.md",
)


def _err(message: str, reason_code: str) -> None:
    """Sanitized stderr writer — paths only, never file contents (Phase 2 POL-04)."""
    sys.stderr.write(f"[CLEANUP] error: {message} reason={reason_code}\n")


def _warn(path: str, reason_code: str) -> None:
    sys.stderr.write(f"[CLEANUP] skipped path={path} reason={reason_code}\n")


def _verify_repo_root(cwd: Path) -> None:
    """D-11: cwd must have .git/ AND pyproject.toml with [project] name='privguard'."""
    if not (cwd / ".git").is_dir():
        _err("not in privguard repo root", "missing_git_dir")
        raise SystemExit(2)
    pyproject = cwd / "pyproject.toml"
    if not pyproject.is_file():
        _err("not in privguard repo root", "missing_pyproject")
        raise SystemExit(2)
    try:
        with pyproject.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        _err("pyproject.toml unreadable", "pyproject_unreadable")
        raise SystemExit(2)
    if not isinstance(data, dict) or data.get("project", {}).get("name") != "privguard":
        _err("pyproject.toml does not declare name=\"privguard\"", "wrong_project_name")
        raise SystemExit(2)


def _load_patterns(cwd: Path) -> list[str]:
    """Read [tool.privguard.cleanup].patterns. Schema-validate per Pitfall 2."""
    try:
        with (cwd / "pyproject.toml").open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        _err("pyproject.toml unreadable", "pyproject_unreadable")
        raise SystemExit(2)
    table = data.get("tool", {}).get("privguard", {}).get("cleanup")
    if not isinstance(table, dict) or "patterns" not in table:
        _err("[tool.privguard.cleanup] missing or invalid", "cleanup_table_missing")
        raise SystemExit(2)
    patterns = table["patterns"]
    if not isinstance(patterns, list) or not all(isinstance(p, str) for p in patterns):
        _err("[tool.privguard.cleanup].patterns must be list[str]", "cleanup_patterns_invalid")
        raise SystemExit(2)
    return patterns


def _matches_protected(rel_path: str, is_dir: bool) -> bool:
    """True if rel_path equals or is under any _PROTECTED entry. fnmatch handles `.env.*`."""
    parts = rel_path.replace(os.sep, "/").split("/")
    head = parts[0]
    for protected in _PROTECTED:
        bare = protected.rstrip("/")
        # Directory-prefix protect: anything under a protected dir
        if protected.endswith("/") and head == bare:
            return True
        # File / glob protect: top-level basename match
        if not protected.endswith("/") and len(parts) == 1 and fnmatch.fnmatch(head, bare):
            return True
    return False


def _matches_pattern(rel_path: str, pattern: str, is_dir: bool, is_file: bool) -> bool:
    """D-08 semantics: trailing '/' = directory-tree match by name; no slash = fnmatch basename."""
    bare = pattern.rstrip("/")
    name = Path(rel_path).name
    if pattern.endswith("/"):
        return is_dir and fnmatch.fnmatch(name, bare)
    return is_file and fnmatch.fnmatch(name, bare)


def _has_symlink_in_tree(root: Path) -> bool:
    """D-13: refuse to delete trees that contain any symlink. Pre-validate before rmtree."""
    if root.is_symlink():
        return True
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames + filenames:
            if (Path(dirpath) / name).is_symlink():
                return True
    return False


def _collect_candidates(
    cwd: Path, patterns: list[str]
) -> tuple[list[tuple[str, Path, int, int, int]], list[tuple[str, str]]]:
    """Return (matches, skips).

    Each match: (pattern, abs_path, file_count, dir_count, byte_size).
    Each skip: (rel_path, reason_code) where reason_code in {'protected', 'symlink'}.
    """
    matches: list[tuple[str, Path, int, int, int]] = []
    skips: list[tuple[str, str]] = []
    # Top-level walk only — patterns target repo-root artifacts (D-08 examples).
    # os.walk with followlinks=False is the safe default per Pitfall 3 / D-13.
    for entry in cwd.iterdir():
        rel = entry.name
        is_dir = entry.is_dir() and not entry.is_symlink()
        is_file = entry.is_file() and not entry.is_symlink()
        is_link = entry.is_symlink()
        for pattern in patterns:
            if not _matches_pattern(
                rel, pattern, is_dir=is_dir or is_link, is_file=is_file or is_link
            ):
                continue
            if _matches_protected(rel, is_dir=is_dir):
                skips.append((rel, "protected"))
                break
            if is_link or _has_symlink_in_tree(entry):
                skips.append((rel, "symlink"))
                break
            file_count = 0
            dir_count = 1 if is_dir else 0
            byte_size = 0
            if is_dir:
                for dirpath, dirnames, filenames in os.walk(entry, followlinks=False):
                    dir_count += len(dirnames)
                    for fname in filenames:
                        fpath = Path(dirpath) / fname
                        try:
                            byte_size += fpath.stat().st_size
                            file_count += 1
                        except OSError:
                            pass
            else:
                try:
                    byte_size = entry.stat().st_size
                    file_count = 1
                except OSError:
                    pass
            matches.append((pattern, entry, file_count, dir_count, byte_size))
            break  # one match per top-level entry; do not double-count across patterns
    return matches, skips


def _human_size(n: int) -> str:
    """Return a human-readable byte count (e.g. '12 B', '1.5 KB', '3.2 MB')."""
    if n < 1024:
        return f"{n} B"
    for unit in ("KB", "MB", "GB"):
        n_float = n / (1024 ** ("KB MB GB".split().index(unit) + 1))
        if n_float < 1024 or unit == "GB":
            return f"{n_float:.1f} {unit}"


def _format_dry_run(
    matches: list[tuple[str, Path, int, int, int]],
    skips: list[tuple[str, str]],
    apply: bool = False,
) -> str:
    """D-10: grouped-by-pattern preview with byte sizes. Paths-and-counts only, no contents.

    apply=False emits the [dry-run] header + 'Run with --apply to delete.' trailer;
    apply=True emits the [apply] header and no trailer.
    """
    prefix = "[apply]" if apply else "[dry-run]"
    verb = "deleting" if apply else "would delete"
    if not matches and not skips:
        return f"{prefix} nothing to clean.\n"
    total_bytes = sum(m[4] for m in matches)
    lines = [f"{prefix} {verb} ({len(matches)} paths, {_human_size(total_bytes)} total):"]
    by_pattern: dict[str, list[tuple[Path, int, int, int]]] = {}
    for pattern, p, fc, dc, bs in matches:
        by_pattern.setdefault(pattern, []).append((p, fc, dc, bs))
    for pattern, rows in by_pattern.items():
        path_count = len(rows)
        total_files = sum(r[1] for r in rows)
        total_dirs = sum(r[2] for r in rows)
        total_size = sum(r[3] for r in rows)
        lines.append(
            f"  {pattern:<20} {path_count} paths / {total_dirs} dirs / "
            f"{total_files} files / {_human_size(total_size)}"
        )
    for rel, reason in skips:
        lines.append(f"  (skipped: {reason}) {rel}")
    if not apply:
        lines.append("Run with --apply to delete.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | argparse.Namespace | None = None) -> int:
    """Entry: 0=clean dry-run or successful apply, 1=apply OS error, 2=misuse (D-14)."""
    if isinstance(argv, argparse.Namespace):
        ns = argv
    else:
        parser = argparse.ArgumentParser(prog="privguard cleanup")
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually delete (default is dry-run preview).",
        )
        ns = parser.parse_args(argv)

    cwd = Path.cwd()
    _verify_repo_root(cwd)
    patterns = _load_patterns(cwd)
    matches, skips = _collect_candidates(cwd, patterns)

    if not getattr(ns, "apply", False):
        sys.stdout.write(_format_dry_run(matches, skips))
        for rel, reason in skips:
            _warn(rel, reason)
        return 0

    # --apply branch
    apply_output = _format_dry_run(matches, skips, apply=True)
    sys.stdout.write(apply_output)
    for rel, reason in skips:
        _warn(rel, reason)
    failed = False
    for _pattern, path, _fc, _dc, _bs in matches:
        # TOCTOU re-check per Pitfall 3
        if path.is_symlink() or _has_symlink_in_tree(path):
            _warn(path.name, "symlink")
            continue
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except OSError as exc:
            failed = True
            _err(
                f"failed to delete {path.name}: {exc.__class__.__name__}",
                "delete_failed",
            )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
