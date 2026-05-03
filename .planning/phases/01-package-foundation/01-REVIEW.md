---
phase: 01-package-foundation
reviewed: 2026-05-03T00:00:00Z
depth: standard
files_reviewed: 14
files_reviewed_list:
  - demos/ollama_local_demo.py
  - demos/reversible_demo.py
  - demos/test_presidio.py
  - demos/test_presidio_br.py
  - hooks/_pii_core.py
  - hooks/pii_guard.py
  - hooks/pre_tool_guard.py
  - privguard/__init__.py
  - privguard/cli.py
  - privguard/detection.py
  - privguard/hooks.py
  - privguard/masking.py
  - privguard/policy.py
  - pyproject.toml
findings:
  critical: 2
  warning: 5
  info: 4
  total: 11
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-05-03T00:00:00Z
**Depth:** standard
**Files Reviewed:** 14
**Status:** issues_found

## Summary

Fresh review against current state, superseding the stale 2026-05-01 report. Phase 02 work has resolved CR-02 (unformatted CPF/CNPJ are now matched in `privguard/detection.py:168-174`) — CONFIRMED RESOLVED. CR-01 (scrub fail-open in `privguard/hooks.py`) and WR-01 (inline-PII threshold drift in `privguard/hooks.py`) remain ACTIVE and are re-stated below as CR-01 and WR-01 with current line numbers. Phase 02 added `privguard/diagnostics.py` and refactored `policy.py` and `masking.py`; those modules are out of the Phase 01 focus and were already covered by the Phase 02 review (DET/MASK series).

New findings concentrate on the privacy boundary that Phase 01 owns: the hook adapters' fail-open behavior on unknown tools and malformed JSON (CR-02 NEW), the Phase 01 scope being mostly UNCOMMITTED (WR-02), policy classifier substring matching that over-flags benign filenames (WR-03), CLI mask command emitting unverified text on stdout (WR-04), and packaging metadata gaps (multiple Info items). No raw PII leaks were found in `demos/*` — they print only `len(text)` and entity-type markers, never the raw values.

## Critical Issues

### CR-01: Scrub mode does not actually replace the submitted prompt (CONFIRMED, RE-STATED)

**File:** `privguard/hooks.py:88-98`
**Issue:** `PII_GUARD_MODE=scrub` returns exit code `0` after writing the redacted copy into `hookSpecificOutput.additionalContext`. In Claude Code's UserPromptSubmit hook contract, `additionalContext` is APPENDED to the prompt — it does NOT replace the original prompt that the user submitted. The clear-text original therefore still leaves the local boundary, while the redacted copy is also appended (effectively duplicating the leak surface). This violates the project's stated safety default ("block rather than silently allow clear-text submission") and the Phase 01 privacy-boundary requirement. Same root cause flagged by the prior REVIEW.md and not yet remediated.
**Fix:**
```python
    if mode == "scrub":
        sys.stderr.write(
            "[PII-GUARD BLOQUEADO] reason=scrub_unsupported "
            f"detections={summary}; redacted={redacted}\n"
        )
        return 2
```
Until Claude exposes a documented mechanism to replace (not append to) a submitted prompt, treat `scrub` as an alias for `block` — return exit code 2 and write to stderr. If/when prompt replacement is supported, route the redacted text through that mechanism and only then return 0. Document this in `pii_guard.py` or environment docs.

### CR-02: Hook adapters fail-open on malformed JSON and unknown tools

**File:** `privguard/hooks.py:57-61, 107-111, 118-136`
**Issue:** Both `main_user_prompt()` and `main_pre_tool()` catch `json.JSONDecodeError`/`ValueError` and `return 0` — i.e., allow the prompt or tool call to proceed unscanned. Worse, `main_pre_tool()` only checks four explicit tool buckets (`Read/Edit/Write/NotebookEdit`, `Glob/Grep`, `Bash/PowerShell`); anything else (`WebFetch`, `WebSearch`, MCP-bridged tools, future Anthropic-added tools) falls through to `return 0` at line 136. A malformed payload or an unrecognized network-egress tool therefore silently bypasses every privacy check. This is the inverse of the project's stated "Safety default: block rather than silently allow."
**Fix:**
```python
def main_user_prompt() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.stderr.write("[PII-GUARD BLOQUEADO] reason=malformed_payload\n")
        return 2
    # ...

def main_pre_tool() -> int:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.stderr.write("[PRE-TOOL-GUARD BLOQUEADO] reason=malformed_payload\n")
        return 2

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    KNOWN_LOCAL_TOOLS = {"Read", "Edit", "Write", "NotebookEdit",
                        "Glob", "Grep", "Bash", "PowerShell"}
    if tool not in KNOWN_LOCAL_TOOLS:
        # Fail closed: WebFetch/WebSearch/MCP/future tools must be explicitly allow-listed.
        return deny("PRE-TOOL-GUARD", "unknown_tool")

    # ... existing dispatch
```
The allow-list approach matches the requirement that any client surface that cannot be safely rewritten must block.

## Warnings

### WR-01: PreTool inline-PII threshold drifts from prompt threshold (CONFIRMED, RE-STATED)

**File:** `privguard/hooks.py:51`
**Issue:** `check_bash()` blocks inline PII at `min_score=0.85` (hardcoded), while `main_user_prompt()` uses `PII_GUARD_THRESHOLD` defaulting to `0.7`. Several configured detector kinds score below 0.85 — `BR_PHONE` 0.76, `BR_CEP` 0.72, `IP_PRIVADO` 0.70, `BR_RG` 0.78, `BR_PLACA_OLD` 0.80 (see `detection.py:177-181, 190`) — so a Bash/PowerShell command containing those raw values is allowed even though the same value pasted into a prompt would be blocked. Two enforcement surfaces drift apart silently. Same finding as prior REVIEW.md, still not remediated.
**Fix:**
```python
def _inline_threshold() -> float:
    return float(os.environ.get("PII_GUARD_THRESHOLD", "0.7"))

def check_bash(tool_input: dict) -> tuple[bool, str]:
    # ...
    if detect(command, min_score=_inline_threshold()):
        return False, "inline_pii"
    return True, ""
```
Or hoist a module-level `INLINE_TOOL_THRESHOLD` constant read once at import. Either way, prompt and tool surfaces must read the same configuration source.

### WR-02: Hook adapters and `privguard/hooks.py` are not under version control

**File:** `privguard/hooks.py` (entire file), `hooks/pii_guard.py`, `hooks/pre_tool_guard.py`, `hooks/_pii_core.py`
**Issue:** `git ls-files` shows the only Phase 01 source files tracked in git are `privguard/__init__.py`, `privguard/cli.py`, `privguard/detection.py`, `privguard/diagnostics.py`, `privguard/masking.py`, `privguard/policy.py`, and `pyproject.toml`. Every file that actually mediates the privacy boundary at runtime — the Claude hook entry points (`hooks/pii_guard.py`, `hooks/pre_tool_guard.py`), the legacy compatibility shim (`hooks/_pii_core.py`), and the package-level hook handlers (`privguard/hooks.py`) — is currently untracked. This means: (a) no review history on the file that hosts CR-01 and WR-01; (b) `pip install privguard` would NOT ship `privguard/hooks.py` because `[tool.setuptools.packages.find]` only includes the `privguard` directory but build metadata won't pick up files git doesn't see during sdist creation in some workflows; (c) any rollback or audit cannot restore the boundary code. This itself is a security-posture finding for a privacy-tooling repo.
**Fix:** Stage and commit these files with a clear message before the next phase closes. Verify with:
```powershell
git add privguard/hooks.py hooks/pii_guard.py hooks/pre_tool_guard.py hooks/_pii_core.py demos/*.py
git status   # confirm clean
git ls-files privguard/ hooks/ demos/   # confirm all listed
```
If any file is intentionally local-only (e.g., a developer scratch demo), add it to `.gitignore` with an explicit comment instead of leaving it ambiguous.

### WR-03: Path classifier substring match over-flags benign filenames

**File:** `privguard/policy.py:114`
**Issue:** `classify_path()` matches `re.search(r"(?:secret|segredo|token|key)", name)` against the basename (lowercased). With no word boundaries, this flags legitimate filenames as `protected_path_secret_name` and forces a `BLOCK` decision via `decide_policy()`. Examples that get false-positively blocked: `tokenizer.py`, `monkey.json`, `keychain.md`, `keyboard_layout.cfg`, `keystone.yaml`, `secretary_notes.txt`. In a code-agent workflow that routinely opens tokenizer/keystore files, this turns the policy into noise and conditions users to ignore blocks (alarm fatigue). Combined with CR-02's fail-open on unknown tools, the threat model has both false-positives on benign names and false-negatives on novel egress surfaces.
**Fix:**
```python
# Match only when these tokens appear as a discrete word in the filename,
# either as the whole stem or separated by ., _, or - boundaries.
_SECRET_NAME = re.compile(
    r"(?:^|[._-])(?:secret|segredo|token|key|api[._-]?key)(?:[._-]|$)"
)
# ...
    if _SECRET_NAME.search(name):
        return PathClassification(True, "secret_filename", "protected_path_secret_name")
```
Add unit cases for `tokenizer.py` (must NOT match), `keystore.cfg` (must NOT match), `api-key.txt` (MUST match), `secret_token.json` (MUST match), `.env.production` (MUST match — already handled by the `.env` branch above). Apply the same word-boundary tightening to the `credentials?|credenciais?` branch on line 113.

### WR-04: `privguard mask` writes unverified output to stdout

**File:** `privguard/cli.py:43-49`
**Issue:** `cmd_mask()` calls `mask_text()`, then prints `result.text` unconditionally and only differentiates the exit code (`0 if result.verified else 2`). When verification fails (`residual_detection` or `original_value_remaining`), the masked-but-unverified text is still written to stdout. A pipeline like `privguard mask < input.txt | curl ... ` will happily forward that unverified output regardless of exit code, because most shells don't gate stdout on `$?`. This contradicts the masking module's own contract (`redact()` raises `ValueError` on unverified results — see `masking.py:110-112`). The CLI should match the library invariant.
**Fix:**
```python
def cmd_mask(args: argparse.Namespace) -> int:
    result = mask_text(_read_text(args))
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
```
Document the exit-code contract in `--help` so callers know `0` means "safe to forward, `2` means "do NOT forward."

### WR-05: Overlapping 11-digit detectors silently shadow each other

**File:** `privguard/detection.py:167-174, 207-213`
**Issue:** `BR_CPF` (`\d{11}`, score 0.95), `BR_CNH` (`\d{11}`, score 0.93), and `BR_PIS_PASEP` (`\d{11}`, score 0.91) all match the same 11-digit numeric span. The dedup loop in `detect()` keeps only the highest-score hit per overlapping span. Because all three checksums are independent algorithms, a string that is a valid CNH but not a valid CPF will be tested against CPF first (highest score), fail the checksum, get its score downgraded to 0.05, be filtered out by `min_score=0.6`, and then NEVER reach the CNH/PIS validators because the dedup keeps the (downgraded) CPF entry. Net effect: numeric-only CNH and PIS-PASEP values can pass undetected through the prompt and tool guard. The same shadowing affects `BR_CNPJ` (14 digits) vs `BR_CARTAO_SUS` (15 digits) — non-overlapping there, but `BR_CNPJ` (14) vs `\d{15}` SUS doesn't overlap at byte level, so this specific pair is safe; the 11-digit cluster is the real bug.
**Fix:** Run all checksum validators per-span and keep the FIRST one whose checksum passes, instead of using static score ordering. Sketch:
```python
def detect(text: str, min_score: float = 0.6) -> list[Hit]:
    raw: list[Hit] = []
    for entry in PATTERNS:
        for m in entry.regex.finditer(text):
            value = m.group(0)
            if entry.validator and not entry.validator(value):
                continue  # do NOT emit a downgraded hit that will shadow other kinds
            raw.append(Hit(entry.kind, m.start(), m.end(), value,
                           entry.score, entry.reason_code))
    # ... existing overlap dedup is now safe
```
This drops the "keep for inspection at score 0.05" debugging artifact; if observability is needed, gate it behind a debug flag rather than emitting hits that pollute the dedup logic. Add a regression test with a 11-digit value that is a valid CNH but not a valid CPF to lock the behavior.

## Info

### IN-01: `pyproject.toml` is missing standard project metadata

**File:** `pyproject.toml:5-9`
**Issue:** `[project]` declares only `name`, `version`, `requires-python`, `dependencies`. Standard fields used by PyPI and `pip show` are absent: `description`, `readme`, `license`, `authors`, `keywords`, `classifiers`, `urls`. With setuptools 77+ and no `license` field, PyPI uploads will warn/reject; users running `pip show privguard` see no description; downstream tooling (Sigstore, SBOM) cannot infer license. PKG-01 metadata target is incomplete.
**Fix:**
```toml
[project]
name = "privguard"
version = "0.1.0"
description = "Local privacy guard for LLM code-agent workflows (Brazilian PII first-class)."
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"  # or whichever the project chooses
authors = [{ name = "Erick", email = "erick.sjct@gmail.com" }]
keywords = ["privacy", "pii", "lgpd", "llm", "claude-code", "presidio"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Security",
]
dependencies = []
```
Confirm the chosen license matches any reuse from Microsoft Presidio examples (Presidio is MIT, so MIT is compatible).

### IN-02: `[full]` extras gated on `python_version < '3.14'` while target runtime is 3.14.3

**File:** `pyproject.toml:13-15`
**Issue:** `01-PATTERNS.md` records the project runtime as Python 3.14.3, but the `[full]` extras (`presidio-analyzer`, `presidio-anonymizer`, `spacy`) are pinned with marker `python_version < '3.14'`. On the actual target interpreter, `pip install privguard[full]` resolves all three extras to "no candidate" and silently installs nothing — the user gets the same surface as the default install, but believes the heavy detector path is available. This is a footgun for the demo flows in `demos/reversible_demo.py` and `demos/test_presidio_br.py` which import Presidio at module load.
**Fix:** Drop the markers (and accept the install will fail on 3.14 if upstream wheels are missing — fail loudly, not silently), or invert: install on >=3.10,<3.14 and document that 3.14 needs a manual Presidio install once upstream ships wheels. Also drop the marker from `presidio-anonymizer` (it has the marker on `presidio-analyzer` and `spacy` only — already fixed in current `pyproject.toml`, line 14: anonymizer has marker, spacy has marker, analyzer has marker — re-confirm consistent).

### IN-03: Unreachable `IP_PUBLICO` pattern under default threshold

**File:** `privguard/detection.py:191`
**Issue:** `IP_PUBLICO` is registered with score `0.50`, but `detect()` defaults `min_score=0.6` (and hooks raise it to 0.7+). The pattern can never produce a hit with the documented thresholds. Either the score is too low or the pattern is dead. The same is borderline-true for `BR_PHONE` (0.76 vs `min_score=0.85` in `check_bash` — covered by WR-01) but `IP_PUBLICO` is fully unreachable in all current call sites.
**Fix:** Either bump the score to 0.65 (with the understanding that bare `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` is noisy and produces false positives like `1.2.3.4` in version strings), or remove the pattern entirely. If kept for future use, document that it requires an explicit `min_score` override:
```python
# Scored deliberately below default threshold; opt-in only via min_score=0.5.
PatternEntry("IP_PUBLICO", re.compile(...), 0.50),
```

### IN-04: `demos/test_presidio.py` defines `sanitize_text` but never calls it

**File:** `demos/test_presidio.py:11-20, 87-104`
**Issue:** `sanitize_text(text, results)` is defined and exported from the module's top level but `main()` only prints `len(text)` and entity types — `sanitize_text` is dead in this file. Either it's a leftover from a refactor or it was intended to be called when displaying samples. Sister file `demos/test_presidio_br.py` has the equivalent helper named `sanitized_display` and likewise does not call it from `main()`. Not a leak (the demos already avoid raw output), but indicates incomplete refactor. Recommendation: either delete the helpers or wire them in for parity with the BR demo's intent.
**Fix:** Remove unused helpers, or replace the `len(text)` line with the sanitized-marker view to demonstrate exactly what would be sent forward:
```python
print(f"Entrada  : {sanitize_text(text, results)}")
```
Since the existing pattern is to print only lengths to be extra-safe with synthetic-but-PII-shaped data, deleting the unused functions is the cleaner option.

---

## Re-evaluation of prior REVIEW.md findings

| Prior ID | Prior Location | Status | Notes |
|----------|----------------|--------|-------|
| CR-01 | `privguard/hooks.py:88` (scrub fail-open) | ACTIVE | Re-stated as CR-01 above with current line range 88-98. |
| CR-02 | `privguard/detection.py:71` (unformatted CPF/CNPJ) | RESOLVED in Phase 02 | Current `PATTERNS` at `detection.py:168-169` includes both formatted and `\d{11}`/`\d{14}` numeric variants with checksum validators. Verified by reading the file. |
| WR-01 | `privguard/hooks.py:51` (inline threshold drift) | ACTIVE | Re-stated as WR-01 above; same `min_score=0.85` hardcoded literal at `hooks.py:51`. |

---

_Reviewed: 2026-05-03T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
