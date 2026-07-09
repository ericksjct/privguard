"""P1 fail-closed failure-injection suite (Phase 10 / TEST-07, handoff Tier 1).

Proves — or documents the absence of — the fail-closed promise under injected
detector failure. Tests pin CURRENT behavior only; where current behavior is
not a block, the test carries a ``# RISCO:`` comment and the plan SUMMARY
carries the matching RISCO/DECISAO entry. No production code is fixed here
(handoff rule: bugs go to a separate Fixer thread).

Scenarios (from 10-01-PLAN Task 1):
  (a) detect() raises → what happens to the hook decision
  (b) Presidio/[full] absent → stdlib detection path still blocks
  (c) slow detector (no internal timeout) → still blocks, latency documented
  (d) 10 MB input → processed without crash/OOM, no size rejection exists
  (e) malformed [tool.privguard] config → sanitized fail-closed error

All fixtures are the canonical synthetic constants from test_claude_hooks /
test_v1_regression_gate — no new realistic Brazilian PII is invented.
"""

from __future__ import annotations

import io
import json
import sys
import time

import pytest

from privguard import hooks
from privguard.cli import main as cli_main
from privguard.detection import detect as real_detect

from test_claude_hooks import (
    PROMPT_SNIPPET,
    RAW_CPF,
    assert_no_prompt_derived_text,
    run_pre_tool,
    run_user_prompt,
)

PII_PROMPT = f"{PROMPT_SNIPPET}: CPF {RAW_CPF}"


# ---------------------------------------------------------------------------
# (a) detector raises an exception
# ---------------------------------------------------------------------------


def _boom(*_a, **_kw):
    raise RuntimeError("injected detector failure")


def test_user_prompt_detector_exception_escapes_unhandled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # RISCO: an exception raised inside detect() escapes main_user_prompt()
    # unhandled. As a console script this becomes a traceback + process exit
    # code 1. Claude Code treats any exit code other than 2 as NON-blocking,
    # so a crashing detector is FAIL-OPEN today — the prompt proceeds with the
    # raw PII. Expected fail-closed behavior would be: catch, sanitize, exit 2.
    monkeypatch.delenv("PII_GUARD_MODE", raising=False)
    monkeypatch.setattr(hooks, "detect", _boom)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({"prompt": PII_PROMPT})))

    with pytest.raises(RuntimeError):
        hooks.main_user_prompt()

    captured = capsys.readouterr()
    # Nothing prompt-derived may leak before the crash surfaces.
    assert_no_prompt_derived_text(captured.out + captured.err)


def test_pre_tool_detector_exception_escapes_unhandled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # RISCO: same fail-open shape on the PreToolUse surface — detect() raising
    # inside the LLM-orchestration payload scan escapes main_pre_tool()
    # unhandled (traceback + exit 1 → non-blocking in Claude Code).
    monkeypatch.delenv("PII_GUARD_MODE", raising=False)
    monkeypatch.setattr(hooks, "detect", _boom)
    payload = {"tool_name": "Task", "tool_input": {"prompt": PII_PROMPT}}
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    with pytest.raises(RuntimeError):
        hooks.main_pre_tool()

    captured = capsys.readouterr()
    assert_no_prompt_derived_text(captured.out + captured.err)


# ---------------------------------------------------------------------------
# (b) Presidio / [full] extra absent
# ---------------------------------------------------------------------------


class _BlockOptionalExtras:
    """meta_path finder that makes presidio/spacy imports fail as if uninstalled."""

    PREFIXES = ("presidio_analyzer", "presidio_anonymizer", "spacy")

    def find_spec(self, fullname, path=None, target=None):  # noqa: ANN001
        if fullname.split(".")[0] in self.PREFIXES:
            raise ModuleNotFoundError(f"No module named {fullname!r} (injected)")
        return None


def test_missing_presidio_extra_still_blocks_via_stdlib_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # privguard's hook runtime is stdlib-only: no module in the block decision
    # path imports presidio or spacy. Simulate a machine without the [full]
    # extra and prove the block decision still fires — absence of the extra
    # cannot degrade to allow.
    blocker = _BlockOptionalExtras()
    monkeypatch.setattr(sys, "meta_path", [blocker, *sys.meta_path])
    for mod in list(sys.modules):
        if mod.split(".")[0] in _BlockOptionalExtras.PREFIXES:
            monkeypatch.delitem(sys.modules, mod)

    assert run_user_prompt(monkeypatch, {"prompt": PII_PROMPT}) == 2

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "BLOQUEADO" in captured.err
    assert "reason=pii_detected" in output
    assert_no_prompt_derived_text(output)


# ---------------------------------------------------------------------------
# (c) slow detector — no internal timeout exists
# ---------------------------------------------------------------------------


def test_slow_detector_still_blocks_no_internal_timeout(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # DECISAO: privguard has no internal detector timeout. A slow detector
    # simply delays the decision; the eventual decision is still block. A HUNG
    # detector, however, relies on Claude Code's external hook timeout, which
    # is treated as a non-blocking error (fail-open on their side). Candidate
    # fix thread: internal watchdog that converts timeout → block.
    calls: list[float] = []

    def slow_detect(text, *a, **kw):  # noqa: ANN001
        calls.append(time.perf_counter())
        time.sleep(0.3)
        return real_detect(text, *a, **kw)

    monkeypatch.setattr(hooks, "detect", slow_detect)

    start = time.perf_counter()
    assert run_user_prompt(monkeypatch, {"prompt": PII_PROMPT}) == 2
    elapsed = time.perf_counter() - start

    assert calls, "injected slow detector was not invoked"
    assert elapsed >= 0.3

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "reason=pii_detected" in output
    assert_no_prompt_derived_text(output)


# ---------------------------------------------------------------------------
# (d) 10 MB synthetic input
# ---------------------------------------------------------------------------

_MB = 1024 * 1024


def _big_text(mb: int) -> str:
    chunk = "texto publico seguro sem dados sensiveis aqui "
    target = mb * _MB
    return (chunk * (target // len(chunk) + 1))[:target]


def test_10mb_prompt_with_pii_blocks_without_crash(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # 10 MB of benign filler with one synthetic CPF appended: the hook must
    # reach the block decision without crashing or OOM. Measured locally at
    # roughly 8.5s per detect() call — latency documented in the SUMMARY.
    prompt = _big_text(10) + f" CPF {RAW_CPF}"

    assert run_user_prompt(monkeypatch, {"prompt": prompt}) == 2

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "BLOQUEADO" in captured.err
    assert "reason=pii_detected" in output
    assert_no_prompt_derived_text(output)


def test_10mb_clean_prompt_currently_allowed_no_size_guard(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # DECISAO: no input-size guard exists — a clean 10 MB prompt is fully
    # scanned (~8.5s) and allowed. There is no explicit rejection of oversized
    # inputs; a size cap before regex is a candidate fix thread (see also
    # test_redos_size_guard.py). This test pins the current allow behavior.
    assert run_user_prompt(monkeypatch, {"prompt": _big_text(10)}) == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


# ---------------------------------------------------------------------------
# (e) malformed [tool.privguard] config in a tmp pyproject
# ---------------------------------------------------------------------------


def _seed_repo(tmp_path, pyproject_text: str) -> None:  # noqa: ANN001
    (tmp_path / ".git").mkdir()
    (tmp_path / "pyproject.toml").write_text(pyproject_text, encoding="utf-8")


@pytest.mark.parametrize(
    ("pyproject_text", "reason"),
    [
        # [tool.privguard] present but cleanup is not a table
        ('[project]\nname = "privguard"\n\n[tool.privguard]\ncleanup = 123\n',
         "cleanup_table_missing"),
        # cleanup table missing entirely
        ('[project]\nname = "privguard"\n',
         "cleanup_table_missing"),
        # patterns is not a list
        ('[project]\nname = "privguard"\n\n[tool.privguard.cleanup]\npatterns = "notalist"\n',
         "cleanup_patterns_invalid"),
        # patterns is a list of non-strings
        ('[project]\nname = "privguard"\n\n[tool.privguard.cleanup]\npatterns = [1, 2]\n',
         "cleanup_patterns_invalid"),
        # syntactically invalid TOML — repo-root guard trips first
        ('[project\nname = privguard\n',
         "pyproject_unreadable"),
    ],
)
def test_cleanup_malformed_privguard_config_fails_closed_sanitized(
    tmp_path,  # noqa: ANN001
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    pyproject_text: str,
    reason: str,
) -> None:
    _seed_repo(tmp_path, pyproject_text)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(SystemExit) as excinfo:
        cli_main(["cleanup"])
    assert excinfo.value.code == 2

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert f"reason={reason}" in captured.err
    assert "Traceback" not in output
    assert_no_prompt_derived_text(output)
