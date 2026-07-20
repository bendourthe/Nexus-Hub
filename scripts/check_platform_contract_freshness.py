#!/usr/bin/env python3
"""Release freshness gate for the platform read-contract.

The platform read-contract (docs/policy/platform-read-contracts.json, with the
human-readable table in the sibling .md) must be re-verified against each
platform's CURRENT discovery format at every release, because those formats
change without notice. This guard makes that mandatory: it fails `make validate`
/ CI whenever the contract was not re-verified for the release being cut - i.e.
when the JSON's `meta.verified_for_version` does not match the canonical project
version in .claude-plugin/plugin.json.

Why version-match (not a date window): during development both values are the
last-released version, so the gate is GREEN and adds no friction. At release,
`/update release` bumps the project version; the gate then FAILS until the
`platform-contract-verification` skill (governance step 4) re-verifies each
platform and re-stamps `meta.verified_for_version` (+ `last_verified`) to the new
version. So a release literally cannot pass validation with a stale contract.

Deterministic, offline, stdlib-only. Exit 0 when fresh; exit 1 when stale.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_JSON = REPO_ROOT / "docs" / "policy" / "platform-read-contracts.json"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"


def _canonical_version(override: str | None) -> str | None:
    """The release being cut: an explicit --version, else the plugin.json version."""
    if override:
        return override.strip()
    try:
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    version = data.get("version")
    return str(version).strip() if version is not None else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check-platform-contract-freshness")
    parser.add_argument(
        "--version",
        help="Release version to check against (defaults to .claude-plugin/plugin.json).",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    if not CONTRACT_JSON.exists():
        print(f"[contract-freshness] MISSING contract JSON: {CONTRACT_JSON}")
        return 1
    try:
        meta = json.loads(CONTRACT_JSON.read_text(encoding="utf-8")).get("meta", {})
    except ValueError as exc:
        print(f"[contract-freshness] contract JSON is not valid JSON: {exc}")
        return 1

    stamped = str(meta.get("verified_for_version", "")).strip()
    canonical = _canonical_version(args.version)
    if not canonical:
        print("[contract-freshness] could not resolve the canonical version (.claude-plugin/plugin.json).")
        return 1
    if not stamped:
        print(f"[contract-freshness] {CONTRACT_JSON.name} meta.verified_for_version is missing.")
        return 1

    if stamped != canonical:
        print(
            f"[contract-freshness] STALE: the platform read-contract was last verified for "
            f"v{stamped}, but the release being cut is v{canonical}."
        )
        print(
            f"  Re-verify each platform's current discovery format and re-stamp "
            f"meta.verified_for_version (+ last_verified) in {CONTRACT_JSON.name}."
        )
        print(
            "  This is /update release governance step 4 (the platform-contract-verification skill)."
        )
        return 1

    if not args.quiet:
        print(
            f"[contract-freshness] OK: contract verified for v{canonical} "
            f"(last_verified {meta.get('last_verified', 'unknown')})."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
