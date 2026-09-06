#!/usr/bin/env python3
"""Verify installer/integration CODE matches docs/policy/platform-read-contracts.md.

Deterministic, offline, stdlib-only. This is layer 3 of the three-layer platform
verification described in the contract doc:

  1. contract-vs-reality  -> the /update release web-search step (agent-driven)
  2. install-vs-reality   -> `nexus-hub verify` (runner.py cmd_verify)
  3. code-vs-contract     -> THIS script (run by `make validate`)

For each platform it asserts: (a) the integration's config declares the paths the
living contract states; (b) skills are flattened one level (via the config flag or
the integration's own install override); (c) the contract doc mentions the platform's
read-paths (so code and doc cannot drift apart silently); and (d) both installers
still reference the platform key (delivery not silently dropped).

Exit 0 when code and contract agree; exit 1 with a per-divergence report otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import get  # noqa: E402

CONTRACT_DOC = REPO_ROOT / "docs" / "policy" / "platform-read-contracts.md"
CONTRACT_JSON = REPO_ROOT / "docs" / "policy" / "platform-read-contracts.json"
INSTALLER_SH = REPO_ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = REPO_ROOT / "scripts" / "installer.ps1"

# Per-platform expectations, loaded from the machine-readable single source
# docs/policy/platform-read-contracts.json (its `contract_checks` block), so the
# expected paths live in ONE place shared with the runtime `[verify]` pass and
# the freshness guard. Each entry:
#   config       : key/value pairs the integration config MUST declare.
#   flatten      : "flag" (config sets flatten_skills_layout=True) or "override"
#                  (the integration flattens in its own install_* method).
#   doc_mentions : substrings that MUST appear in the prose contract doc.
def _load_expectations() -> dict:
    try:
        data = json.loads(CONTRACT_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    checks = data.get("contract_checks")
    return checks if isinstance(checks, dict) else {}


EXPECTATIONS: dict[str, dict] = _load_expectations()


def _installer_tokens(key: str) -> list[str]:
    """Tokens either installer might use for a platform key (bash lower-kebab,
    PowerShell UPPER_SNAKE)."""
    return [key, key.upper().replace("-", "_")]


def check(doc: str, installer_sh: str, installer_ps: str) -> list[str]:
    """Return a list of drift problems (empty when code and contract agree).

    Pure over its inputs (plus the live integration registry), so tests can inject
    a drifted doc / installer text.
    """
    problems: list[str] = []
    for key, exp in EXPECTATIONS.items():
        try:
            integ = get(key)
        except Exception as exc:  # noqa: BLE001
            problems.append(f"{key}: not resolvable in the integration registry ({exc})")
            continue
        cfg = integ.config
        for ck, cv in exp["config"].items():
            if cfg.get(ck) != cv:
                problems.append(
                    f"{key}: config[{ck!r}]={cfg.get(ck)!r}, contract expects {cv!r}"
                )
        if exp["flatten"] == "flag" and cfg.get("flatten_skills_layout") is not True:
            problems.append(
                f"{key}: expected flatten_skills_layout=True (skills read one level "
                f"deep), config has {cfg.get('flatten_skills_layout')!r}"
            )
        for token in exp["doc_mentions"]:
            if token not in doc:
                problems.append(
                    f"{key}: contract doc does not mention {token!r} (code/doc drift)"
                )
        if installer_sh and not any(t in installer_sh for t in _installer_tokens(key)):
            problems.append(f"{key}: not referenced in installer.sh (delivery dropped?)")
        if installer_ps and not any(t in installer_ps for t in _installer_tokens(key)):
            problems.append(f"{key}: not referenced in installer.ps1 (delivery dropped?)")
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    quiet = "--quiet" in argv
    if not CONTRACT_DOC.exists():
        print(f"[verify-contracts] MISSING contract doc: {CONTRACT_DOC}")
        return 1
    if not EXPECTATIONS:
        print(f"[verify-contracts] MISSING or empty contract JSON: {CONTRACT_JSON} (no contract_checks block)")
        return 1
    doc = CONTRACT_DOC.read_text(encoding="utf-8")
    installer_sh = INSTALLER_SH.read_text(encoding="utf-8") if INSTALLER_SH.exists() else ""
    installer_ps = INSTALLER_PS1.read_text(encoding="utf-8") if INSTALLER_PS1.exists() else ""

    problems = check(doc, installer_sh, installer_ps)
    if problems:
        print("[verify-contracts] DRIFT between code and docs/policy/platform-read-contracts.md:")
        for p in problems:
            print(f"  - {p}")
        return 1
    if not quiet:
        print(f"[verify-contracts] OK: {len(EXPECTATIONS)} platforms match the contract doc.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
