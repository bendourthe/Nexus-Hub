#!/usr/bin/env python3
"""Deterministic planner and writer for the per-model prompting profile layer.

The research half of `model-prompting-research` is agent work: search the web,
read primary sources, judge and refute claims. But the two ends of that pipeline
must NOT be agent work, because both are exactly the kind of mechanical step an
LLM does inconsistently:

  * `plan`  - decide WHICH models still need research (the fan-out work-list).
  * `write` - merge verified claims into the profile layer, schema-valid by
              construction, and regenerate the Markdown mirrors.

Keeping these deterministic buys three things. The work-list is reproducible, so
the same roster always fans out the same way. The written layer always satisfies
`scripts/verify_model_prompting_profiles.py`, so the research run cannot leave a
malformed index behind. And a run that stops early (a budget cap, a kill switch,
an offline stage) still writes a VALID partial layer, because each write is a
complete merge rather than a half-finished edit.

The workflow template (`assets/research-workflow.js`) has no filesystem access,
so the CALLER runs `plan` first and passes the work-list in as workflow args,
then runs `write` per model as claims survive verification. That is the
"scope-first" shape the agent-orchestration-primitives reference template
recommends.

This script makes NO network call. It never invents, edits, or re-scopes a
claim: it validates what it is given and refuses the whole write on anything
malformed, so a bad research result fails loudly instead of silently degrading
the layer.

Usage:
    python write_model_prompting_profile.py plan --roster claude-opus-5 claude-sonnet-5
    python write_model_prompting_profile.py plan --only claude-opus-5
    python write_model_prompting_profile.py write --input verified.json
    python write_model_prompting_profile.py write --input verified.json --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SKILL_NAME = "model-prompting-research"
INDEX_REL = Path("assets") / "profiles-index.json"
PROFILES_REL = Path("references") / "models"

SCHEMA_VERSION = "1.1.0"
ALLOWED_ROSTER_SOURCES = ("api", "picker", "config", "manual")
ALLOWED_CONFIDENCE = ("high", "medium", "low", "unverified")
ALLOWED_SCOPE = ("model-specific", "model-agnostic-candidate")
CLAIM_REQUIRED_KEYS = ("claim", "source_url", "confidence", "scope")
CLAIM_OPTIONAL_KEYS = ("note",)

# A claim that has not survived the adversarial-verify pass must never be
# presented as actionable guidance. The writer accepts it (so a partial or
# low-confidence research result is still recorded honestly) but the planner
# treats a model whose claims are ALL unverified as still needing research.
UNVERIFIED = "unverified"


class WriteError(Exception):
    """A malformed input that must abort the whole write."""


def roster_hash(roster: list[str]) -> str:
    """The canonical roster hash, identical to the repo-level validator's."""
    return hashlib.sha256("\n".join(sorted(roster)).encode("utf-8")).hexdigest()


def default_bundle() -> Path:
    """This script lives in the bundle's scripts/ dir, so the bundle is its parent."""
    return Path(__file__).resolve().parents[1]


def load_index(bundle: Path) -> dict:
    """Load the existing index, or return an empty skeleton when absent."""
    path = bundle / INDEX_REL
    if not path.is_file():
        return {"schema_version": SCHEMA_VERSION, "meta": {}, "models": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise WriteError(f"existing index is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise WriteError("existing index does not contain a JSON object")
    data.setdefault("schema_version", SCHEMA_VERSION)
    data.setdefault("meta", {})
    data.setdefault("models", {})
    return data


# ---------------------------------------------------------------------------
# plan: which models still need research
# ---------------------------------------------------------------------------


def plan_targets(
    roster: list[str],
    models: dict,
    only: str | None = None,
    refresh_all: bool = False,
) -> dict:
    """Compute the research work-list. Pure; no I/O.

    A model needs research when it has no profile, when its profile carries no
    claims, or when every claim it carries is still `unverified` (a seed that no
    verify pass has confirmed). `--only` narrows to one model for the scope-first
    calibration run; `--refresh-all` re-researches the whole roster.
    """
    roster = sorted({m.strip() for m in roster if m and m.strip()})
    if only:
        only = only.strip()
        targets = [only] if only else []
        return {
            "targets": targets,
            "reason": "explicit --only (scope-first calibration)",
            "roster": roster,
            "in_roster": only in roster,
        }

    targets: list[str] = []
    for model_id in roster:
        entry = models.get(model_id)
        if not isinstance(entry, dict):
            targets.append(model_id)
            continue
        claims = entry.get("claims")
        if not isinstance(claims, list) or not claims:
            targets.append(model_id)
            continue
        if refresh_all or all(
            isinstance(c, dict) and c.get("confidence") == UNVERIFIED for c in claims
        ):
            targets.append(model_id)

    return {
        "targets": targets,
        "reason": "refresh-all" if refresh_all else "unprofiled or wholly-unverified",
        "roster": roster,
        "in_roster": True,
    }


# ---------------------------------------------------------------------------
# write: merge verified claims into the layer
# ---------------------------------------------------------------------------


def _validate_claim(model_id: str, position: int, claim: object) -> dict:
    """Validate and normalize one incoming claim. Raises WriteError."""
    where = f"models['{model_id}'].claims[{position}]"
    if not isinstance(claim, dict):
        raise WriteError(f"{where} must be an object")

    unknown = set(claim) - set(CLAIM_REQUIRED_KEYS) - set(CLAIM_OPTIONAL_KEYS)
    if unknown:
        raise WriteError(f"{where} has unknown key(s): {', '.join(sorted(unknown))}")
    for key in CLAIM_REQUIRED_KEYS:
        if key not in claim:
            raise WriteError(f"{where} is missing required key '{key}'")

    text = claim["claim"]
    if not isinstance(text, str) or not text.strip():
        raise WriteError(f"{where}.claim must be a non-empty string")
    url = claim["source_url"]
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        raise WriteError(
            f"{where}.source_url must be an http(s) URL to a primary source, got {url!r}"
        )
    if claim["confidence"] not in ALLOWED_CONFIDENCE:
        raise WriteError(
            f"{where}.confidence must be one of {list(ALLOWED_CONFIDENCE)}, "
            f"got {claim['confidence']!r}"
        )
    if claim["scope"] not in ALLOWED_SCOPE:
        raise WriteError(
            f"{where}.scope must be one of {list(ALLOWED_SCOPE)}, got {claim['scope']!r}"
        )

    normalized = {
        "claim": text.strip(),
        "source_url": url.strip(),
        "confidence": claim["confidence"],
        "scope": claim["scope"],
    }
    note = claim.get("note")
    if note is not None:
        if not isinstance(note, str):
            raise WriteError(f"{where}.note must be a string when present")
        normalized["note"] = note.strip()
    return normalized


def _render_mirror(model_id: str, entry: dict, roster_source: str) -> str:
    """Render the human-readable Markdown mirror for one model entry."""
    rows = []
    for claim in entry["claims"]:
        # Pipes would break the table; the source is a URL so it cannot contain one
        # unescaped, but claim text is free-form and must be escaped.
        text = claim["claim"].replace("|", "\\|")
        note = claim.get("note", "")
        suffix = f" {note.replace('|', chr(92) + '|')}" if note else ""
        rows.append(
            f"| {text}{suffix} | `{claim['confidence']}` | `{claim['scope']}` | "
            f"[source]({claim['source_url']}) |"
        )
    table = "\n".join(rows)

    return f"""# Prompting Profile: {model_id}

**Platform**: {entry["platform"]}
**Last verified**: {entry["last_verified"]}
**Roster provenance**: `{roster_source}`

This file mirrors the `models["{model_id}"]` entry in `assets/profiles-index.json`. The index is authoritative; if the two disagree, regenerate this file from the index with `scripts/write_model_prompting_profile.py`.

## Verified prompting guidance

| Claim | Confidence | Scope | Primary source |
|---|---|---|---|
{table}

## Does not apply to shared bodies

Every claim in this file is scoped to the model named in the H1. It must not be copied into a shared catalog body: a `SKILL.md`, a command file, or any of the five `base-*.md` instruction templates. Those artifacts are distributed verbatim to every supported platform, so a line naming one model is wrong for every reader running a different one, and `scripts/check_base_template_parity.py` fails the build when such a line diverges across the templates.

If a claim here turns out to be true of models generally rather than of this one, re-scope it to `model-agnostic-candidate` in `assets/profiles-index.json` and let the guard-gated auto-apply path propose the shared-body edit, so the change is branch-isolated, guard-checked, and reviewable.

## Schema

The field rules for this file and its index entry are documented in `references/schema.md`.
"""


def merge(index: dict, payload: dict) -> tuple[dict, list[str]]:
    """Merge a verified-research payload into the index. Pure; raises WriteError.

    Returns the updated index and the list of model ids that were written.
    """
    if not isinstance(payload, dict):
        raise WriteError("payload must be a JSON object")
    for key in ("platform", "verified_at", "models"):
        if key not in payload:
            raise WriteError(f"payload is missing required key '{key}'")

    platform = payload["platform"]
    if not isinstance(platform, str) or not platform.strip():
        raise WriteError("payload.platform must be a non-empty string")
    verified_at = payload["verified_at"]
    if not isinstance(verified_at, str) or len(verified_at) != 10:
        raise WriteError("payload.verified_at must be a YYYY-MM-DD string")

    roster_source = payload.get("roster_source", "manual")
    if roster_source not in ALLOWED_ROSTER_SOURCES:
        raise WriteError(
            f"payload.roster_source must be one of {list(ALLOWED_ROSTER_SOURCES)}, "
            f"got {roster_source!r}"
        )

    incoming = payload["models"]
    if not isinstance(incoming, dict) or not incoming:
        raise WriteError("payload.models must be a non-empty object")

    written: list[str] = []
    for model_id in sorted(incoming):
        claims = incoming[model_id]
        if not isinstance(claims, list) or not claims:
            raise WriteError(f"models['{model_id}'] must be a non-empty array of claims")
        normalized = [_validate_claim(model_id, i, c) for i, c in enumerate(claims)]
        index["models"][model_id] = {
            "platform": platform,
            "last_verified": verified_at,
            "claims": normalized,
        }
        written.append(model_id)

    # The roster is the LIVE roster when the payload carries one; otherwise keep
    # the recorded roster and widen it to cover anything just profiled, so the
    # index never claims a model it has no roster entry for.
    recorded = index["meta"].get("roster")
    recorded = list(recorded) if isinstance(recorded, list) else []
    roster = payload.get("roster")
    if isinstance(roster, list) and roster:
        merged_roster = [str(m).strip() for m in roster if str(m).strip()]
    else:
        merged_roster = recorded
    merged_roster = sorted(set(merged_roster) | set(index["models"]))

    index["schema_version"] = SCHEMA_VERSION
    legacy_platform = index["meta"].get("platform")
    if legacy_platform in (None, platform):
        # Single-platform layer, or a write for the layer's primary platform: the
        # legacy keys stay the source of truth (schema 1.0.0 behavior).
        index["meta"] = {
            **index["meta"],
            "last_verified": verified_at,
            "platform": platform,
            "roster_source": roster_source,
            "roster": merged_roster,
            "roster_hash": roster_hash(merged_roster),
        }
        return index, written

    # v4.7.0 (schema 1.1.0): a write for ANOTHER platform lands in the optional
    # meta.platforms array, so the primary platform's roster is never rewritten by
    # research on a different vendor's models.
    entries = [e for e in index["meta"].get("platforms", []) if isinstance(e, dict)]
    existing = next((e for e in entries if e.get("platform") == platform), None)
    prior = [str(m) for m in (existing or {}).get("roster", []) if str(m).strip()]
    if isinstance(roster, list) and roster:
        platform_roster = [str(m).strip() for m in roster if str(m).strip()]
    else:
        platform_roster = prior
    profiled_here = [m for m, e in index["models"].items() if e.get("platform") == platform]
    platform_roster = sorted(set(platform_roster) | set(profiled_here))
    entry = {
        "platform": platform,
        "roster_source": roster_source,
        "roster": platform_roster,
        "roster_hash": roster_hash(platform_roster),
        "last_verified": verified_at,
    }
    index["meta"]["platforms"] = [e for e in entries if e.get("platform") != platform] + [entry]
    return index, written


def platform_roster_source(index: dict, platform: str) -> str:
    """The roster provenance for a platform: its meta.platforms entry, else the legacy meta."""
    for entry in index.get("meta", {}).get("platforms", []) or []:
        if isinstance(entry, dict) and entry.get("platform") == platform:
            return str(entry.get("roster_source", "manual"))
    return str(index.get("meta", {}).get("roster_source", "manual"))


def write_layer(bundle: Path, index: dict, written: list[str]) -> list[Path]:
    """Persist the index and regenerate a Markdown mirror per written model."""
    paths: list[Path] = []
    index_path = bundle / INDEX_REL
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    paths.append(index_path)

    mirrors = bundle / PROFILES_REL
    mirrors.mkdir(parents=True, exist_ok=True)
    for model_id in written:
        entry = index["models"][model_id]
        roster_source = platform_roster_source(index, str(entry.get("platform", "")))
        mirror = mirrors / f"{model_id}.md"
        mirror.write_text(
            _render_mirror(model_id, entry, roster_source),
            encoding="utf-8",
            newline="\n",
        )
        paths.append(mirror)
    return paths


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="write-model-prompting-profile",
        description="Plan the research work-list, or merge verified claims into the layer.",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="Path to the skill bundle (defaults to this script's parent directory).",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_plan = sub.add_parser("plan", help="Print the models that still need research.")
    p_plan.add_argument("--roster", nargs="*", default=None, help="The LIVE model roster.")
    p_plan.add_argument(
        "--platform",
        help="Plan against the recorded roster of this platform (a meta.platforms entry); default is the legacy meta roster.",
    )
    p_plan.add_argument("--only", help="Narrow to one model (scope-first calibration).")
    p_plan.add_argument(
        "--refresh-all", action="store_true", help="Re-research every rostered model."
    )

    p_write = sub.add_parser("write", help="Merge a verified-research payload.")
    p_write.add_argument("--input", type=Path, required=True, help="Payload JSON file, or - for stdin.")
    p_write.add_argument("--dry-run", action="store_true", help="Validate without writing.")
    p_write.add_argument("--quiet", action="store_true")

    args = parser.parse_args(argv)
    bundle = args.bundle or default_bundle()

    try:
        index = load_index(bundle)
    except WriteError as exc:
        print(f"[profile-write] ERROR: {exc}", file=sys.stderr)
        return 1

    if args.mode == "plan":
        roster = args.roster if args.roster else index["meta"].get("roster", [])
        if not args.roster and args.platform:
            roster = next(
                (
                    e.get("roster", [])
                    for e in index["meta"].get("platforms", []) or []
                    if isinstance(e, dict) and e.get("platform") == args.platform
                ),
                [],
            )
        if not isinstance(roster, list):
            roster = []
        result = plan_targets(
            [str(m) for m in roster], index["models"], args.only, args.refresh_all
        )
        print(json.dumps(result, indent=2))
        return 0

    raw = sys.stdin.read() if str(args.input) == "-" else args.input.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except ValueError as exc:
        print(f"[profile-write] ERROR: payload is not valid JSON: {exc}", file=sys.stderr)
        return 1

    try:
        index, written = merge(index, payload)
    except WriteError as exc:
        print(f"[profile-write] ERROR: {exc}", file=sys.stderr)
        print("  Nothing was written; fix the payload and re-run.", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"[profile-write] DRY RUN: would write {len(written)} model(s): {', '.join(written)}")
        return 0

    paths = write_layer(bundle, index, written)
    if not args.quiet:
        print(f"[profile-write] wrote {len(written)} model(s): {', '.join(written)}")
        for path in paths:
            print(f"  {path}")
        unprofiled = [m for m in index["meta"]["roster"] if m not in index["models"]]
        if unprofiled:
            print(f"  UNVERIFIED (rostered, no profile): {', '.join(unprofiled)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
