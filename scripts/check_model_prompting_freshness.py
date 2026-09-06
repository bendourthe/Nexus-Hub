#!/usr/bin/env python3
"""ADVISORY staleness check for the per-model prompting profile layer (v3.15.5).

New models ship on the vendor's clock, not on Nexus-Hub's release clock. When one
does, the per-model prompting profile layer bundled in the
`model-prompting-research` skill is stale until a research run refreshes it. This
script detects that drift and says so, and does NOT stop anything.

That is a deliberate contrast with `scripts/check_platform_contract_freshness.py`,
which DOES hard-gate `make validate` and CI. The platform read-contract must be
re-verified for the release being cut, so gating it is correct. Profile freshness
is different: gating it would mean a vendor shipping a model on a Tuesday wedges
every Nexus-Hub release until someone runs a research swarm. So this checker is
advisory by default and must NEVER be wired into `make validate` or CI as a
blocking step. `--strict` exists only for a local operator who wants a non-zero
exit to drive their own tooling.

The script makes NO network call. The caller enumerates the live roster (via the
`model-routing` skill's `enumerate-models` helper) and passes the model ids on
argv, which keeps the only outbound dependency in the agent's own web/API surface
rather than in a repo script.

Verdicts:

  IN SYNC   the recorded roster matches the roster passed on argv exactly.
  DRIFTED   models were added, removed, or the recorded hash was not re-stamped.
  UNKNOWN   no live roster was supplied, so no comparison is possible (this is
            the normal offline / model-picker-only outcome, not an error).

Deterministic, offline, stdlib-only.

Usage:
    python scripts/check_model_prompting_freshness.py claude-opus-5 claude-sonnet-5
    python scripts/check_model_prompting_freshness.py --strict claude-opus-5
    python scripts/check_model_prompting_freshness.py --root /tmp/fixture claude-opus-5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Reuse the bundle discovery and the canonical roster-hash definition from the
# structural validator so the two scripts can never disagree about where the
# layer lives or how a roster hashes.
try:
    from verify_model_prompting_profiles import (  # type: ignore[import-not-found]
        INDEX_REL,
        SKILL_NAME,
        find_bundle,
        roster_hash,
    )
except ImportError:  # pragma: no cover - direct execution from another cwd.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from verify_model_prompting_profiles import (  # type: ignore[import-not-found]
        INDEX_REL,
        SKILL_NAME,
        find_bundle,
        roster_hash,
    )

REPO_ROOT = Path(__file__).resolve().parents[1]


def compare_rosters(recorded: list[str], recorded_hash: str, live: list[str]) -> dict[str, object]:
    """Compare a recorded roster against a live one. Pure; no I/O.

    Returns a dict with `verdict` ("in_sync" or "drifted") plus the `added`,
    `removed`, and `hash_restamp_needed` details that explain a drift verdict.
    """
    recorded_set = set(recorded)
    live_set = set(live)
    added = sorted(live_set - recorded_set)
    removed = sorted(recorded_set - live_set)
    # A stale hash with an identical id set means the roster list was hand-edited
    # without re-stamping the hash. Report it rather than silently calling it fresh.
    hash_restamp_needed = not added and not removed and recorded_hash != roster_hash(live)
    drifted = bool(added or removed or hash_restamp_needed)
    return {
        "verdict": "drifted" if drifted else "in_sync",
        "added": added,
        "removed": removed,
        "hash_restamp_needed": hash_restamp_needed,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check-model-prompting-freshness",
        description=(
            "Advisory roster-drift check for the per-model prompting profile layer. "
            "Never a blocking gate; see the module docstring."
        ),
    )
    parser.add_argument(
        "models",
        nargs="*",
        help=(
            "The LIVE model roster, one id per argument, as enumerated by the caller "
            "(model-routing). Omit to get an UNKNOWN verdict."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="Tree to search for the skill bundle (default: the repo root).",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        help="Explicit path to the skill bundle, bypassing the --root search.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--advisory",
        action="store_true",
        help="Always exit 0 regardless of verdict (the default, and what the release step uses).",
    )
    mode.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on DRIFTED or UNKNOWN. For local operator tooling only, never CI.",
    )
    parser.add_argument(
        "--platform",
        help=(
            "Compare against the recorded roster of this platform (a schema-1.1.0 meta.platforms "
            "entry) instead of the legacy meta roster."
        ),
    )
    parser.add_argument("--quiet", action="store_true", help="Print only the verdict line.")
    args = parser.parse_args(argv)

    def finish(drifted_or_unknown: bool) -> int:
        """Advisory mode always succeeds; only --strict propagates a failure."""
        return 1 if (args.strict and drifted_or_unknown) else 0

    bundle = find_bundle(args.root, args.bundle)
    if bundle is None:
        print(f"[profile-freshness] UNKNOWN: no '{SKILL_NAME}' bundle found under {args.root}.")
        return finish(True)

    index_path = bundle / INDEX_REL
    if not index_path.is_file():
        print(f"[profile-freshness] UNKNOWN: missing profile index at {index_path}.")
        return finish(True)
    try:
        meta = json.loads(index_path.read_text(encoding="utf-8")).get("meta", {})
    except ValueError as exc:
        print(f"[profile-freshness] UNKNOWN: {index_path.name} is not valid JSON ({exc}).")
        return finish(True)
    if not isinstance(meta, dict):
        print(f"[profile-freshness] UNKNOWN: {index_path.name} has no usable meta block.")
        return finish(True)

    block = meta
    if args.platform:
        block = next(
            (
                e
                for e in (meta.get("platforms") or [])
                if isinstance(e, dict) and e.get("platform") == args.platform
            ),
            None,
        )
        if block is None:
            print(
                f"[profile-freshness] UNKNOWN: {index_path.name} has no meta.platforms entry for "
                f"{args.platform!r}."
            )
            return finish(True)
    label = f"meta.platforms[{args.platform}]" if args.platform else "meta"
    recorded = block.get("roster")
    if not isinstance(recorded, list) or not all(isinstance(entry, str) for entry in recorded):
        print(f"[profile-freshness] UNKNOWN: {index_path.name} {label}.roster is missing or malformed.")
        return finish(True)
    recorded_hash = str(block.get("roster_hash", ""))
    last_verified = block.get("last_verified", "unknown")

    live = sorted({model.strip() for model in args.models if model.strip()})
    if not live:
        print(
            "[profile-freshness] UNKNOWN: no live roster supplied, so drift cannot be "
            "determined."
        )
        if not args.quiet:
            print(
                "  Enumerate the roster first (the model-routing skill's enumerate-models "
                "helper) and pass the ids as arguments."
            )
            print(f"  Recorded roster ({len(recorded)}, last verified {last_verified}): "
                  f"{', '.join(recorded) if recorded else '(empty)'}")
        return finish(True)

    result = compare_rosters(recorded, recorded_hash, live)
    if result["verdict"] == "in_sync":
        print(
            f"[profile-freshness] IN SYNC: {len(recorded)} model(s) match the live roster "
            f"(last verified {last_verified})."
        )
        return finish(False)

    added = result["added"]
    removed = result["removed"]
    print(
        f"[profile-freshness] DRIFTED: the profile layer was last verified {last_verified} "
        f"against a roster that no longer matches the live one."
    )
    if added:
        print(f"  added (live but unprofiled): {', '.join(added)}")  # type: ignore[arg-type]
    if removed:
        print(f"  removed (recorded but no longer live): {', '.join(removed)}")  # type: ignore[arg-type]
    if result["hash_restamp_needed"]:
        print(
            "  roster ids match but meta.roster_hash was not re-stamped after the last edit."
        )
    if not args.quiet:
        print("  Run /tune-prompting to refresh the profile layer. This is ADVISORY:")
        print("  it never blocks a release and is not a CI gate.")
    return finish(True)


if __name__ == "__main__":
    raise SystemExit(main())
