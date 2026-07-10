"""P3 ReDoS latency-bound + input-size behavior suite (Phase 10 / TEST-07).

Feeds backtracking-hostile inputs to detect() and bounds their latency. Phase
10 pinned the EMAIL regex as super-linear (DECISAO D3); 11-01 fixed it, so the
EMAIL tests here now assert LINEAR scaling. The hook-level input-size guard
(D2) is asserted in test_fail_closed_injection; detect() itself stays uncapped
for the CLI scan/mask path.

Key behavior (Python 3.14):
  - Pure digit runs (CNPJ/CPF/SUS/boleto numeric patterns) scan LINEARLY and
    fast (50k digits ~30 ms) — no catastrophic backtracking.
  - The EMAIL regex is now ``\\b(?>[\\w.+-]{1,64})@(?>[\\w-]{1,63})\\.(?>[\\w.-]{2,255})\\b``:
    atomic groups + RFC-5321 length bounds remove the phase-10 O(n^2) scan
    (72k hostile chars ~24 ms, linear).

All fixtures are synthetic; no realistic Brazilian PII literal is introduced.
Latency ceilings are deliberately generous to avoid CI flakiness while still
fencing against a regression back into super-linear backtracking.
"""

from __future__ import annotations

import time

import pytest

from privguard.detection import detect

from test_v1_regression_gate import SYNTH_CPF


def _elapsed_ms(text: str) -> float:
    t0 = time.perf_counter()
    detect(text)
    return (time.perf_counter() - t0) * 1000.0


# ---------------------------------------------------------------------------
# Numeric patterns: no catastrophic backtracking
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("label", "text"),
    [
        ("digit_run_50k", "1" * 50_000),
        ("spaced_digit_groups", "1234 5678 9012 " * 2000),
        ("cnpj_boleto_bait", "9" * 60_000),
    ],
    ids=["digit_run_50k", "spaced_digit_groups", "cnpj_boleto_bait"],
)
def test_numeric_hostile_inputs_scan_linearly_under_bound(label: str, text: str) -> None:
    # Numeric detection patterns (CPF/CNPJ/SUS/boleto/titulo) show no
    # catastrophic backtracking on long digit runs; each stays well under a
    # generous 1s ceiling. This fences against a regression into pathological
    # backtracking in the numeric patterns.
    assert _elapsed_ms(text) < 1000.0, f"{label} exceeded 1s latency bound"


# ---------------------------------------------------------------------------
# EMAIL regex: linear after atomic-group + length-bound fix (D3, 11-01)
# ---------------------------------------------------------------------------


def test_email_bait_completes_under_generous_bound() -> None:
    # D3 (fixed in 11-01): the EMAIL regex uses atomic groups, so a long
    # "[\w.+-]+ with no @" run can no longer catastrophically backtrack. A
    # ~13k-char hostile run completes well under a generous 1s ceiling.
    text = "a.b+c-" * 2200  # ~13k chars of email-body chars, never an '@'
    assert _elapsed_ms(text) < 1000.0


def test_email_bait_scales_linearly_after_atomic_fix() -> None:
    # D3 (fixed in 11-01): with the atomic-group EMAIL regex the scan is now
    # LINEAR — doubling the hostile input roughly doubles (not squares) the
    # time. This flips the phase-10 super-linear pin; a large hostile run must
    # stay well under a generous ceiling and NOT show quadratic blow-up.
    small = "a.b+c-" * 3000   # ~18k chars
    large = "a.b+c-" * 6000   # ~36k chars (2x)
    t_small = _elapsed_ms(small)
    t_large = _elapsed_ms(large)
    assert t_large < 1000.0, "atomic EMAIL regex should stay fast on hostile input"
    # Linear signature: 2x input costs roughly <=2x time (generous 4x slack for
    # timer noise / constant overhead). Quadratic behavior would blow past this.
    if t_small > 5.0:
        assert t_large < t_small * 4.0, (
            "EMAIL scan expected ~linear after the atomic-group fix; a >4x jump "
            "on 2x input signals a regression back to super-linear backtracking."
        )


# ---------------------------------------------------------------------------
# Oversized input: no size guard exists
# ---------------------------------------------------------------------------


def test_detect_has_no_size_cap_for_the_cli_path() -> None:
    # D2 (fixed in 11-01): the size guard lives at the HOOK boundary
    # (hooks.MAX_INPUT_CHARS), NOT inside detect() — the CLI scan/mask path must
    # still process large files without truncation. So detect() deliberately has
    # no size cap: a ~2 MB benign blob with a trailing synthetic CPF is scanned
    # in full and the CPF is still found. The oversized-input BLOCK is asserted
    # at the hook in test_fail_closed_injection (10 MB → input_too_large).
    blob = ("texto publico seguro " * (2 * 1024 * 1024 // 21)) + f" CPF {SYNTH_CPF}"
    hits = detect(blob, min_score=0.7)
    assert any(h.kind == "BR_CPF" for h in hits)
