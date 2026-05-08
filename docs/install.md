# Installation

privguard is a local-first Python package. There is no hosted service component — everything runs in your developer environment.

## Baseline install

```bash
pip install privguard
```

Requirements: Python >= 3.10. The baseline install brings in zero third-party runtime dependencies and provides:

- The `privguard` CLI (`privguard --help` / `privguard info` / `privguard scan` / `privguard mask` / `privguard policy-check` / `privguard claude doctor`).
- The lightweight Brazil-first detection path (`privguard.detection`).
- Masking, policy classification, and the Claude Code hook adapters.

## Extras: `privguard[full]`

```bash
pip install "privguard[full]"
```

The `full` extra adds Presidio-backed detection (`presidio-analyzer`, `presidio-anonymizer`, `spacy`).

## Python version support

privguard targets Python 3.10 and above (`requires-python = ">=3.10"` in `pyproject.toml`). All v1 functionality except the optional Presidio parity path is supported across all targeted Python versions.

Some optional dependencies carry upstream constraints:

| Python version | `pip install privguard` | `pip install privguard[full]` |
|----------------|-------------------------|-------------------------------|
| 3.10, 3.11, 3.12, 3.13 | Lightweight detection works. | Presidio analyzer, Presidio anonymizer, and spaCy are installed. |
| 3.14 | Lightweight detection works. | Presidio analyzer-backed detection is unavailable; dependencies with Python 3.14 support are not blocked by privguard. |

This is enforced in `pyproject.toml` with package-specific markers. `presidio-analyzer` remains gated by `python_version < '3.14'`; `presidio-anonymizer` is not gated out by privguard because its current package metadata supports Python 3.14.

### Implications on Python 3.14

- `pip install privguard[full]` succeeds, but analyzer-backed detection remains unavailable because `presidio-analyzer` is gated out.
- `privguard.detection` still imports and runs cleanly using the lightweight detector — there is no silent failure.
- The DET-06 lightweight-vs-Presidio parity check (the test that compares lightweight detector output with Presidio detector output for shared synthetic fixtures) is **skipped** on Python 3.14 by environment marker, not by silent failure. The `requires-python` floor still allows Python 3.14, so privguard remains installable; only the parity test is short-circuited.

This is the current state, not a long-term policy. The remaining extras gating will be relaxed on a per-package basis once the blocking upstream package metadata supports Python 3.14.

## Verifying the install

```bash
privguard --version
privguard info
python -c "from privguard import classify_command, CODEX_COMPATIBILITY; print('OK')"
```

The third line proves the v1 public API surface is bound at the top-level package — see `privguard/__init__.py` for the full `__all__` list.
