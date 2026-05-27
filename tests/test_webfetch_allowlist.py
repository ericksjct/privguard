"""Tests for WebFetch domain-allowlist gating (Plan 999.1-01)."""

from __future__ import annotations

import io
import json
import sys

import pytest

from privguard.hooks import check_webfetch, _ALLOWED_FETCH_DOMAINS, main_pre_tool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_pre_tool(monkeypatch: pytest.MonkeyPatch, payload: object) -> int:
    raw = json.dumps(payload)
    monkeypatch.setattr(sys, "stdin", io.StringIO(raw))
    return main_pre_tool()


# ---------------------------------------------------------------------------
# _ALLOWED_FETCH_DOMAINS constant
# ---------------------------------------------------------------------------

def test_allowed_domains_is_frozenset():
    assert isinstance(_ALLOWED_FETCH_DOMAINS, frozenset)


def test_allowed_domains_minimum_count():
    assert len(_ALLOWED_FETCH_DOMAINS) >= 7


def test_allowed_domains_contains_github():
    assert "github.com" in _ALLOWED_FETCH_DOMAINS


def test_allowed_domains_contains_docs_python_org():
    assert "docs.python.org" in _ALLOWED_FETCH_DOMAINS


def test_allowed_domains_contains_pypi_org():
    assert "pypi.org" in _ALLOWED_FETCH_DOMAINS


def test_allowed_domains_contains_docs_anthropic_com():
    assert "docs.anthropic.com" in _ALLOWED_FETCH_DOMAINS


def test_allowed_domains_contains_raw_githubusercontent_com():
    assert "raw.githubusercontent.com" in _ALLOWED_FETCH_DOMAINS


def test_allowed_domains_contains_docs_rs():
    assert "docs.rs" in _ALLOWED_FETCH_DOMAINS


def test_allowed_domains_contains_crates_io():
    assert "crates.io" in _ALLOWED_FETCH_DOMAINS


# ---------------------------------------------------------------------------
# check_webfetch() — allowed domains
# ---------------------------------------------------------------------------

def test_check_webfetch_github_allowed():
    ok, reason = check_webfetch({"url": "https://github.com/anthropics/privguard"})
    assert ok is True
    assert reason == ""


def test_check_webfetch_docs_python_allowed():
    ok, reason = check_webfetch({"url": "https://docs.python.org/3/library/urllib.parse.html"})
    assert ok is True
    assert reason == ""


def test_check_webfetch_pypi_allowed():
    ok, reason = check_webfetch({"url": "https://pypi.org/project/privguard/"})
    assert ok is True
    assert reason == ""


def test_check_webfetch_docs_anthropic_allowed():
    ok, reason = check_webfetch({"url": "https://docs.anthropic.com/en/api"})
    assert ok is True
    assert reason == ""


def test_check_webfetch_raw_githubusercontent_allowed():
    ok, reason = check_webfetch({"url": "https://raw.githubusercontent.com/owner/repo/main/file.py"})
    assert ok is True
    assert reason == ""


def test_check_webfetch_docs_rs_allowed():
    ok, reason = check_webfetch({"url": "https://docs.rs/serde/latest/serde/"})
    assert ok is True
    assert reason == ""


def test_check_webfetch_crates_io_allowed():
    ok, reason = check_webfetch({"url": "https://crates.io/crates/serde"})
    assert ok is True
    assert reason == ""


# ---------------------------------------------------------------------------
# check_webfetch() — subdomain matching
# ---------------------------------------------------------------------------

def test_check_webfetch_subdomain_of_github_allowed():
    ok, reason = check_webfetch({"url": "https://api.github.com/repos/foo/bar"})
    assert ok is True
    assert reason == ""


def test_check_webfetch_subdomain_of_pypi_allowed():
    ok, reason = check_webfetch({"url": "https://files.pythonhosted.org/"})
    # files.pythonhosted.org is NOT in the allowlist — this must be blocked
    assert ok is False
    assert reason == "webfetch_domain_not_allowed"


# ---------------------------------------------------------------------------
# check_webfetch() — blocked domains
# ---------------------------------------------------------------------------

def test_check_webfetch_evil_com_blocked():
    ok, reason = check_webfetch({"url": "https://evil.com/steal"})
    assert ok is False
    assert reason == "webfetch_domain_not_allowed"


def test_check_webfetch_pastebin_blocked():
    ok, reason = check_webfetch({"url": "https://pastebin.com/raw/abc123"})
    assert ok is False
    assert reason == "webfetch_domain_not_allowed"


def test_check_webfetch_notgithub_blocked():
    """'notgithub.com' must NOT match 'github.com'."""
    ok, reason = check_webfetch({"url": "https://notgithub.com/repo"})
    assert ok is False
    assert reason == "webfetch_domain_not_allowed"


def test_check_webfetch_path_bypass_blocked():
    """'evil.com/github.com' must NOT pass — naive substring check would allow it."""
    ok, reason = check_webfetch({"url": "https://evil.com/github.com/repo"})
    assert ok is False
    assert reason == "webfetch_domain_not_allowed"


# ---------------------------------------------------------------------------
# check_webfetch() — missing or empty URL
# ---------------------------------------------------------------------------

def test_check_webfetch_missing_url_key():
    ok, reason = check_webfetch({})
    assert ok is False
    assert reason == "webfetch_url_missing"


def test_check_webfetch_empty_string_url():
    ok, reason = check_webfetch({"url": ""})
    assert ok is False
    assert reason == "webfetch_url_missing"


def test_check_webfetch_none_url():
    ok, reason = check_webfetch({"url": None})
    assert ok is False
    assert reason == "webfetch_url_missing"


# ---------------------------------------------------------------------------
# check_webfetch() — malformed URL (no scheme)
# ---------------------------------------------------------------------------

def test_check_webfetch_no_scheme_blocked():
    """urlparse('evil.com/path').netloc == '' so netloc check catches it."""
    ok, reason = check_webfetch({"url": "evil.com/path"})
    assert ok is False
    assert reason == "webfetch_domain_not_allowed"


# ---------------------------------------------------------------------------
# main_pre_tool() — WebFetch integration
# ---------------------------------------------------------------------------

def test_main_pre_tool_webfetch_allowed_returns_zero(monkeypatch):
    payload = {
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://github.com/anthropics/privguard"},
    }
    assert run_pre_tool(monkeypatch, payload) == 0


def test_main_pre_tool_webfetch_blocked_returns_two(monkeypatch):
    payload = {
        "tool_name": "WebFetch",
        "tool_input": {"url": "https://evil.com/steal"},
    }
    assert run_pre_tool(monkeypatch, payload) == 2


def test_main_pre_tool_webfetch_missing_url_returns_two(monkeypatch):
    payload = {
        "tool_name": "WebFetch",
        "tool_input": {},
    }
    assert run_pre_tool(monkeypatch, payload) == 2


def test_main_pre_tool_webfetch_malformed_url_returns_two(monkeypatch):
    payload = {
        "tool_name": "WebFetch",
        "tool_input": {"url": "evil.com/no-scheme"},
    }
    assert run_pre_tool(monkeypatch, payload) == 2
