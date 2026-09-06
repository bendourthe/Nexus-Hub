#!/usr/bin/env python3
"""Structural validator for the per-model prompting profile layer (v3.15.5).

The `model-prompting-research` skill bundles a per-model prompting profile layer:
an authoritative machine index (`assets/profiles-index.json`) plus one
human-readable Markdown mirror per profiled model
(`references/models/<model-id>.md`). Every later stage of the feature reads that
layer programmatically (the research engine writes it, the staleness checker
compares its roster, the edit-routing classifier reads each claim's `scope` to
decide whether an edit may touch a shared catalog body), so a malformed layer
must fail the build rather than silently mis-route an edit.

This script is that gate. It is STRUCTURAL ONLY and deliberately makes no
freshness judgement: it never compares `meta.last_verified` against the clock and
never enumerates a live model roster. Roster staleness is the separate, ADVISORY
concern of `scripts/check_model_prompting_freshness.py`, kept out of every
blocking gate so a vendor shipping a new model can never wedge a release.

What it checks:

  * the index exists, parses, and carries exactly the three top-level keys;
  * `meta` is complete and well-typed, `meta.roster` is sorted + unique, and
    `meta.roster_hash` matches a recomputation from `meta.roster` in the same
    file (a self-consistency check that catches a hand-edited roster);
  * every model entry is well-typed and carries at least one claim;
  * every claim carries the four required keys, a plausible `source_url`, and a
    `confidence` / `scope` drawn from the allowed sets, with no unknown keys;
  * the index's model set and the `references/models/*.md` set match in BOTH
    directions.

What it deliberately does NOT check: that every model in `meta.roster` has a
profile. A rostered model with no entry is an UNVERIFIED model, a legitimate
state that the research run surfaces as a known-gaps item rather than a build
failure.

Deterministic, offline, stdlib-only. Exit 0 when the layer is valid, 1 otherwise.

Usage:
    python scripts/verify_model_prompting_profiles.py
    python scripts/verify_model_prompting_profiles.py --root /tmp/fixture
    python scripts/verify_model_prompting_profiles.py --bundle path/to/skill --quiet
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SKILL_NAME = "model-prompting-research"
# Candidate bundle locations, tried in order: the in-repo catalog path, then the
# FLATTENED `skills/<name>/` layout the installer writes to every platform target
# (so the copy under ~/.nexus-hub/scripts/ is usable against an installed tree).
BUNDLE_CANDIDATES = (
    Path("catalog") / "skills" / "ai-development" / SKILL_NAME,
    Path("skills") / SKILL_NAME,
)
INDEX_REL = Path("assets") / "profiles-index.json"
PROFILES_REL = Path("references") / "models"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")

TOP_LEVEL_KEYS = {"schema_version", "meta", "models"}
META_KEYS = {"last_verified", "platform", "roster_source", "roster", "roster_hash"}
# v4.7.0 (schema 1.1.0): an OPTIONAL per-platform roster array beside the legacy
# single-platform keys, so an OpenAI model can be profiled without rewriting the
# Claude roster. Each entry carries its own roster and hash, validated the same way.
META_OPTIONAL_KEYS = {"platforms"}
PLATFORM_ENTRY_KEYS = {"platform", "roster_source", "roster", "roster_hash", "last_verified"}
MODEL_KEYS = {"platform", "last_verified", "claims"}
CLAIM_REQUIRED_KEYS = {"claim", "source_url", "confidence", "scope"}
CLAIM_OPTIONAL_KEYS = {"note"}

ALLOWED_ROSTER_SOURCES = {"api", "picker", "config", "manual"}
ALLOWED_CONFIDENCE = {"high", "medium", "low", "unverified"}
ALLOWED_SCOPE = {"model-specific", "model-agnostic-candidate"}


def roster_hash(roster: list[str]) -> str:
    """The canonical roster hash: sha256 of the sorted ids joined by newlines.

    Shared with check_model_prompting_freshness.py by definition (both compute it
    the same way from a sorted list) so a roster recorded by one is comparable by
    the other.
    """
    return hashlib.sha256("\n".join(sorted(roster)).encode("utf-8")).hexdigest()


def find_bundle(root: Path, override: Path | None) -> Path | None:
    """Locate the skill bundle under `root`, or return the explicit override."""
    if override is not None:
        return override if override.is_dir() else None
    for candidate in BUNDLE_CANDIDATES:
        path = root / candidate
        if path.is_dir():
            return path
    return None


def _validate_meta(meta: object) -> list[str]:
    """Validate the `meta` block. Returns a list of error strings."""
    errors: list[str] = []
    if not isinstance(meta, dict):
        return [f"meta must be an object, got {type(meta).__name__}"]

    unknown = set(meta) - META_KEYS - META_OPTIONAL_KEYS
    if unknown:
        errors.append(f"meta has unknown key(s): {', '.join(sorted(unknown))}")
    for key in sorted(META_KEYS - set(meta)):
        errors.append(f"meta is missing required key '{key}'")
    if "platforms" in meta:
        errors.extend(_validate_platforms(meta["platforms"]))

    last_verified = meta.get("last_verified")
    if "last_verified" in meta and (
        not isinstance(last_verified, str) or not DATE_RE.match(last_verified)
    ):
        errors.append(f"meta.last_verified must be a YYYY-MM-DD string, got {last_verified!r}")

    platform = meta.get("platform")
    if "platform" in meta and (not isinstance(platform, str) or not platform.strip()):
        errors.append(f"meta.platform must be a non-empty string, got {platform!r}")

    source = meta.get("roster_source")
    if "roster_source" in meta and source not in ALLOWED_ROSTER_SOURCES:
        errors.append(
            f"meta.roster_source must be one of {sorted(ALLOWED_ROSTER_SOURCES)}, got {source!r}"
        )

    roster = meta.get("roster")
    roster_ok = False
    if "roster" in meta:
        if not isinstance(roster, list) or not roster:
            errors.append("meta.roster must be a non-empty array of model ids")
        elif not all(isinstance(entry, str) and entry.strip() for entry in roster):
            errors.append("meta.roster entries must all be non-empty strings")
        else:
            roster_ok = True
            if roster != sorted(roster):
                errors.append("meta.roster must be sorted ascending")
            if len(set(roster)) != len(roster):
                errors.append("meta.roster must not contain duplicate model ids")

    recorded_hash = meta.get("roster_hash")
    if "roster_hash" in meta:
        if not isinstance(recorded_hash, str) or not HASH_RE.match(recorded_hash):
            errors.append(
                f"meta.roster_hash must be 64 lowercase hex characters, got {recorded_hash!r}"
            )
        elif roster_ok:
            expected = roster_hash(roster)  # type: ignore[arg-type]
            if recorded_hash != expected:
                errors.append(
                    f"meta.roster_hash does not match meta.roster "
                    f"(recorded {recorded_hash}, expected {expected}); re-stamp it after "
                    f"editing the roster"
                )
    return errors


def _validate_roster_block(where: str, block: dict) -> list[str]:
    """Roster rules shared by the legacy meta block and each per-platform entry."""
    errors: list[str] = []
    roster = block.get("roster")
    roster_ok = False
    if "roster" in block:
        if not isinstance(roster, list) or not roster:
            errors.append(f"{where}.roster must be a non-empty array of model ids")
        elif not all(isinstance(entry, str) and entry.strip() for entry in roster):
            errors.append(f"{where}.roster entries must all be non-empty strings")
        else:
            roster_ok = True
            if roster != sorted(roster):
                errors.append(f"{where}.roster must be sorted ascending")
            if len(set(roster)) != len(roster):
                errors.append(f"{where}.roster must not contain duplicate model ids")
    recorded_hash = block.get("roster_hash")
    if "roster_hash" in block:
        if not isinstance(recorded_hash, str) or not HASH_RE.match(recorded_hash):
            errors.append(f"{where}.roster_hash must be 64 lowercase hex characters, got {recorded_hash!r}")
        elif roster_ok:
            expected = roster_hash(roster)  # type: ignore[arg-type]
            if recorded_hash != expected:
                errors.append(
                    f"{where}.roster_hash does not match {where}.roster "
                    f"(recorded {recorded_hash}, expected {expected}); re-stamp it after editing the roster"
                )
    return errors


def _validate_platforms(platforms: object) -> list[str]:
    """Validate the optional schema-1.1.0 `meta.platforms` array."""
    if not isinstance(platforms, list) or not platforms:
        return ["meta.platforms must be a non-empty array when present"]
    errors: list[str] = []
    seen: set[str] = set()
    for position, entry in enumerate(platforms):
        where = f"meta.platforms[{position}]"
        if not isinstance(entry, dict):
            errors.append(f"{where} must be an object, got {type(entry).__name__}")
            continue
        unknown = set(entry) - PLATFORM_ENTRY_KEYS
        if unknown:
            errors.append(f"{where} has unknown key(s): {', '.join(sorted(unknown))}")
        for key in sorted(PLATFORM_ENTRY_KEYS - set(entry)):
            errors.append(f"{where} is missing required key '{key}'")
        platform = entry.get("platform")
        if "platform" in entry:
            if not isinstance(platform, str) or not platform.strip():
                errors.append(f"{where}.platform must be a non-empty string, got {platform!r}")
            elif platform in seen:
                errors.append(f"{where}.platform {platform!r} appears more than once")
            else:
                seen.add(platform)
        if "roster_source" in entry and entry.get("roster_source") not in ALLOWED_ROSTER_SOURCES:
            errors.append(
                f"{where}.roster_source must be one of {sorted(ALLOWED_ROSTER_SOURCES)}, got {entry.get('roster_source')!r}"
            )
        last_verified = entry.get("last_verified")
        if "last_verified" in entry and (not isinstance(last_verified, str) or not DATE_RE.match(last_verified)):
            errors.append(f"{where}.last_verified must be a YYYY-MM-DD string, got {last_verified!r}")
        errors.extend(_validate_roster_block(where, entry))
    return errors


def _validate_claim(model_id: str, position: int, claim: object) -> list[str]:
    """Validate one claim object. Returns a list of error strings."""
    where = f"models['{model_id}'].claims[{position}]"
    if not isinstance(claim, dict):
        return [f"{where} must be an object, got {type(claim).__name__}"]

    errors: list[str] = []
    unknown = set(claim) - CLAIM_REQUIRED_KEYS - CLAIM_OPTIONAL_KEYS
    if unknown:
        errors.append(f"{where} has unknown key(s): {', '.join(sorted(unknown))}")
    for key in sorted(CLAIM_REQUIRED_KEYS - set(claim)):
        errors.append(f"{where} is missing required key '{key}'")

    text = claim.get("claim")
    if "claim" in claim and (not isinstance(text, str) or not text.strip()):
        errors.append(f"{where}.claim must be a non-empty string")

    url = claim.get("source_url")
    if "source_url" in claim:
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            errors.append(
                f"{where}.source_url must be an http(s) URL to a primary source, got {url!r}"
            )

    confidence = claim.get("confidence")
    if "confidence" in claim and confidence not in ALLOWED_CONFIDENCE:
        errors.append(
            f"{where}.confidence must be one of {sorted(ALLOWED_CONFIDENCE)}, got {confidence!r}"
        )

    scope = claim.get("scope")
    if "scope" in claim and scope not in ALLOWED_SCOPE:
        errors.append(f"{where}.scope must be one of {sorted(ALLOWED_SCOPE)}, got {scope!r}")

    note = claim.get("note")
    if "note" in claim and not isinstance(note, str):
        errors.append(f"{where}.note must be a string when present")

    return errors


def _validate_models(models: object) -> list[str]:
    """Validate the `models` map and every claim inside it."""
    errors: list[str] = []
    if not isinstance(models, dict):
        return [f"models must be an object, got {type(models).__name__}"]
    if not models:
        errors.append("models must carry at least one model entry")

    for model_id, entry in sorted(models.items()):
        if not isinstance(model_id, str) or not model_id.strip():
            errors.append(f"models has a non-empty-string key requirement, got {model_id!r}")
            continue
        if not isinstance(entry, dict):
            errors.append(f"models['{model_id}'] must be an object, got {type(entry).__name__}")
            continue

        unknown = set(entry) - MODEL_KEYS
        if unknown:
            errors.append(
                f"models['{model_id}'] has unknown key(s): {', '.join(sorted(unknown))}"
            )
        for key in sorted(MODEL_KEYS - set(entry)):
            errors.append(f"models['{model_id}'] is missing required key '{key}'")

        platform = entry.get("platform")
        if "platform" in entry and (not isinstance(platform, str) or not platform.strip()):
            errors.append(f"models['{model_id}'].platform must be a non-empty string")

        last_verified = entry.get("last_verified")
        if "last_verified" in entry and (
            not isinstance(last_verified, str) or not DATE_RE.match(last_verified)
        ):
            errors.append(
                f"models['{model_id}'].last_verified must be a YYYY-MM-DD string, "
                f"got {last_verified!r}"
            )

        claims = entry.get("claims")
        if "claims" in entry:
            if not isinstance(claims, list) or not claims:
                errors.append(
                    f"models['{model_id}'].claims must be a non-empty array of claim objects"
                )
            else:
                for position, claim in enumerate(claims):
                    errors.extend(_validate_claim(model_id, position, claim))

    return errors


def _validate_mirrors(models: object, profiles_dir: Path) -> list[str]:
    """Both-directions match between index model ids and references/models/*.md."""
    errors: list[str] = []
    if not isinstance(models, dict):
        return errors

    indexed = {str(model_id) for model_id in models}
    if profiles_dir.is_dir():
        mirrored = {path.stem for path in sorted(profiles_dir.glob("*.md"))}
    else:
        mirrored = set()
        if indexed:
            errors.append(
                f"missing profiles directory {profiles_dir} (every indexed model needs a "
                f"Markdown mirror)"
            )
            return errors

    for model_id in sorted(indexed - mirrored):
        errors.append(
            f"models['{model_id}'] has no Markdown mirror at "
            f"{(profiles_dir / (model_id + '.md')).as_posix()}"
        )
    for model_id in sorted(mirrored - indexed):
        errors.append(
            f"{(profiles_dir / (model_id + '.md')).as_posix()} has no matching entry in "
            f"the index's models map"
        )
    return errors


def validate_bundle(bundle: Path) -> list[str]:
    """Validate one profile-layer bundle. Returns a list of error strings."""
    index_path = bundle / INDEX_REL
    if not index_path.is_file():
        return [f"missing profile index: {index_path}"]
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"{index_path} is not valid JSON: {exc}"]
    if not isinstance(data, dict):
        return [f"{index_path} must contain a JSON object at the top level"]

    errors: list[str] = []
    unknown = set(data) - TOP_LEVEL_KEYS
    if unknown:
        errors.append(f"unknown top-level key(s): {', '.join(sorted(unknown))}")
    for key in sorted(TOP_LEVEL_KEYS - set(data)):
        errors.append(f"missing required top-level key '{key}'")

    schema_version = data.get("schema_version")
    if "schema_version" in data and (
        not isinstance(schema_version, str) or not schema_version.strip()
    ):
        errors.append(f"schema_version must be a non-empty string, got {schema_version!r}")

    if "meta" in data:
        errors.extend(_validate_meta(data["meta"]))
    if "models" in data:
        errors.extend(_validate_models(data["models"]))
        errors.extend(_validate_mirrors(data["models"], bundle / PROFILES_REL))

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="verify-model-prompting-profiles",
        description="Structural gate for the per-model prompting profile layer.",
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
    parser.add_argument("--quiet", action="store_true", help="Print nothing on success.")
    args = parser.parse_args(argv)

    bundle = find_bundle(args.root, args.bundle)
    if bundle is None:
        searched = args.bundle or ", ".join(
            (args.root / candidate).as_posix() for candidate in BUNDLE_CANDIDATES
        )
        print(f"[profile-schema] MISSING bundle for '{SKILL_NAME}'; searched: {searched}")
        return 1

    errors = validate_bundle(bundle)
    if errors:
        print(f"[profile-schema] INVALID: {len(errors)} structural error(s) in {bundle.as_posix()}")
        for error in errors:
            print(f"  ERROR: {error}")
        print("  See references/schema.md in the skill bundle for the field rules.")
        return 1

    if not args.quiet:
        index_path = bundle / INDEX_REL
        data = json.loads(index_path.read_text(encoding="utf-8"))
        models = data.get("models", {})
        roster = data.get("meta", {}).get("roster", [])
        unverified = [m for m in roster if m not in models]
        print(
            f"[profile-schema] OK: {len(models)} profiled model(s) of {len(roster)} rostered "
            f"(schema {data.get('schema_version')}, last verified "
            f"{data.get('meta', {}).get('last_verified')})."
        )
        if unverified:
            print(
                f"  Note: {len(unverified)} rostered model(s) not yet profiled "
                f"({', '.join(unverified)}); tracked as known gaps, not a gate failure."
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
