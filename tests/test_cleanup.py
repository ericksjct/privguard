"""Cleanup CLI subcommand contract tests (Phase 7 / MAINT-01)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from privguard.cli import main


# Reuse the synthetic-fixture corpus from tests/test_claude_doctor.py:11-28.
# Cleanup operates on path strings; these values would only ever leak via a
# pathological pyproject.toml or filename — defense in depth via Phase 2 POL-04.
SYNTHETIC_CPF = "123.456.789-09"
SYNTHETIC_SECRET = "sk-test-abcdefghijklmnopqrstuvwxyz"
SYNTHETIC_PROTECTED_PATH = "data_sensivel/synthetic.csv"
SYNTHETIC_ENV_PATH = ".env"


FORBIDDEN_OUTPUT_VALUES = (
    SYNTHETIC_CPF,
    SYNTHETIC_SECRET,
    SYNTHETIC_PROTECTED_PATH,
    "<BR_CPF>",
    "<TOKEN>",
)


def _assert_sanitized(rendered: str) -> None:
    for value in FORBIDDEN_OUTPUT_VALUES:
        assert value not in rendered, f"forbidden value {value!r} leaked into output"


def _seed_repo(tmp_path: Path, *, patterns: list[str] | None = None,
               project_name: str = "privguard") -> None:
    """Create a synthetic privguard repo root: .git/ + pyproject.toml + cleanup table."""
    (tmp_path / ".git").mkdir()
    pyproject_text = f'[project]\nname = "{project_name}"\n\n'
    if patterns is not None:
        toml_list = ",\n    ".join(f'"{p}"' for p in patterns)
        pyproject_text += f"[tool.privguard.cleanup]\npatterns = [\n    {toml_list},\n]\n"
    (tmp_path / "pyproject.toml").write_text(pyproject_text, encoding="utf-8")


def test_cleanup_default_is_dry_run_no_deletion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_repo(tmp_path, patterns=["__pycache__/"])
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "x.pyc").write_bytes(b"compiled")

    monkeypatch.chdir(tmp_path)
    assert main(["cleanup"]) == 0  # default = dry-run
    assert pycache.exists(), "dry-run must NOT delete"
    assert (pycache / "x.pyc").exists()

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    assert "[dry-run]" in captured.out
    _assert_sanitized(rendered)


def test_cleanup_apply_deletes_pycache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_repo(tmp_path, patterns=["__pycache__/"])
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "x.pyc").write_bytes(b"compiled")

    monkeypatch.chdir(tmp_path)
    assert main(["cleanup", "--apply"]) == 0
    assert not pycache.exists(), "--apply must delete the matched directory"

    captured = capsys.readouterr()
    _assert_sanitized(captured.out + captured.err)


def test_cleanup_exits_2_outside_privguard_repo_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # tmp_path has neither .git/ nor pyproject.toml — repo-root guard must trip.
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        main(["cleanup", "--apply"])
    assert excinfo.value.code == 2

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    assert "[CLEANUP] error:" in captured.err
    # Either guard may trip first — both produce reason= prefixes.
    assert "reason=missing_git_dir" in captured.err or "reason=missing_pyproject" in captured.err
    _assert_sanitized(rendered)


def test_cleanup_apply_skips_protected_paths_with_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Seed a cleanup pattern (".env") that would match .env via fnmatch, then prove
    # the hardcoded _PROTECTED list refuses it regardless (both ".env" and ".env.*"
    # appear in _PROTECTED; using exact pattern here to ensure the pattern matches
    # so that the protection check fires).
    _seed_repo(tmp_path, patterns=[".env"])
    env_file = tmp_path / ".env"
    env_file.write_text("FAKE_KEY=synthetic", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    assert main(["cleanup", "--apply"]) == 0
    assert env_file.exists(), "_PROTECTED must shield .env from any cleanup pattern"

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    assert "reason=protected" in captured.err
    _assert_sanitized(rendered)


def test_cleanup_apply_refuses_symlinks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    if os.name == "nt":
        pytest.skip("symlink creation requires admin or DevMode on Windows")
    _seed_repo(tmp_path, patterns=["__pycache__/"])
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    sibling_target = tmp_path / "sibling_keep.txt"
    sibling_target.write_text("must survive", encoding="utf-8")
    (pycache / "link_to_sibling").symlink_to(sibling_target)

    monkeypatch.chdir(tmp_path)
    assert main(["cleanup", "--apply"]) == 0
    assert pycache.exists(), "directory containing a symlink must be skipped (D-13)"
    assert sibling_target.exists(), "symlink target must survive"

    captured = capsys.readouterr()
    rendered = captured.out + captured.err
    assert "reason=symlink" in captured.err
    _assert_sanitized(rendered)


def test_cleanup_dry_run_output_is_sanitized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_repo(tmp_path, patterns=["__pycache__/", "*.py[cod]"])
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "stale.pyc").write_bytes(b"stale")

    monkeypatch.chdir(tmp_path)
    assert main(["cleanup"]) == 0
    captured = capsys.readouterr()
    _assert_sanitized(captured.out + captured.err)
