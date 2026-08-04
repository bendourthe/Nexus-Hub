#!/usr/bin/env python3
"""Score generic routing intent and validate or render provider model maps."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

TIERS = ("frontier", "strong", "standard", "fast")
PROVIDERS = ("Anthropic", "OpenAI", "Google", "Cursor")
SIGNAL_LEVELS = ("low", "medium", "high")
ASSESS_LATER = "assess at implementation time"
DEFAULT_SNAPSHOT = (
    Path(__file__).resolve().parent.parent / "references" / "last-known-model-map.json"
)
URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


class MapValidationError(ValueError):
    """Raised when a model-map document violates the routing contract."""


def score_signals(signals: list[str], *, uncertain: bool = False) -> dict[str, str]:
    """Map five rubric signals to a generic tier and effort level."""
    if len(signals) != 5 or any(signal not in SIGNAL_LEVELS for signal in signals):
        raise ValueError("exactly five low|medium|high signals are required")

    high_count = signals.count("high")
    medium_count = signals.count("medium")
    if uncertain or high_count >= 2:
        return {"tier": "frontier", "effort": "max"}
    if high_count == 1:
        return {"tier": "frontier", "effort": "high"}
    if medium_count >= 3:
        return {"tier": "strong", "effort": "high"}
    if medium_count:
        return {"tier": "standard", "effort": "medium"}
    return {"tier": "fast", "effort": "low"}


def _require_date(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise MapValidationError(f"{field} must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise MapValidationError(f"{field} must be an ISO date") from exc
    return value


def validate_map(data: Any) -> dict[str, Any]:
    """Validate the dated 4x4 provider-map JSON schema."""
    if not isinstance(data, dict):
        raise MapValidationError("model map must be a JSON object")
    if data.get("schema_version") != 1:
        raise MapValidationError("schema_version must be 1")

    verified_as_of = _require_date(data.get("verified_as_of"), "verified_as_of")
    tiers = data.get("tiers")
    if not isinstance(tiers, dict):
        raise MapValidationError("tiers must be an object")

    normalized_tiers: dict[str, dict[str, str]] = {}
    for tier in TIERS:
        row = tiers.get(tier)
        if not isinstance(row, dict):
            raise MapValidationError(f"missing tier row: {tier}")
        normalized_row: dict[str, str] = {}
        for provider in PROVIDERS:
            model = row.get(provider)
            if not isinstance(model, str) or not model.strip():
                raise MapValidationError(f"empty model cell: {tier}/{provider}")
            if model.strip() == ASSESS_LATER:
                raise MapValidationError(
                    f"dated maps cannot defer a model cell: {tier}/{provider}"
                )
            normalized_row[provider] = model.strip()
        normalized_tiers[tier] = normalized_row

    sources = data.get("sources")
    if not isinstance(sources, dict):
        raise MapValidationError("sources must be an object")
    normalized_sources: dict[str, list[str]] = {}
    for provider in PROVIDERS:
        urls = sources.get(provider)
        has_valid_sources = (
            isinstance(urls, list)
            and bool(urls)
            and all(isinstance(url, str) and URL_PATTERN.match(url) for url in urls)
        )
        if not has_valid_sources:
            raise MapValidationError(
                f"sources for {provider} must contain at least one HTTP(S) URL"
            )
        normalized_sources[provider] = urls

    return {
        "schema_version": 1,
        "verified_as_of": verified_as_of,
        "tiers": normalized_tiers,
        "sources": normalized_sources,
    }


def load_map(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise MapValidationError(f"cannot read model map: {path}") from exc
    except json.JSONDecodeError as exc:
        raise MapValidationError(f"invalid JSON in model map: {path}") from exc
    return validate_map(data)


def render_map(data: dict[str, Any], *, status: str, as_of: str | None) -> str:
    """Render a validated map using the plan-contract Markdown grammar."""
    if status == "fresh":
        rendered_date = _require_date(as_of, "as_of")
        status_line = (
            f"**Model map status**: fresh as of {rendered_date}; sources cited below."
        )
    else:
        rendered_date = data["verified_as_of"]
        status_line = (
            f"**Model map status**: offline fallback; stale as of {rendered_date}."
        )

    lines = [
        "## Current model map",
        "",
        status_line,
        "",
        "| Tier | Anthropic | OpenAI | Google | Cursor |",
        "|---|---|---|---|---|",
    ]
    for tier in TIERS:
        row = data["tiers"][tier]
        cells = " | ".join(f"`{row[provider]}`" for provider in PROVIDERS)
        lines.append(f"| {tier} | {cells} |")

    lines.extend(["", "### Model map sources", ""])
    for provider in PROVIDERS:
        lines.append(f"- {provider}: {', '.join(data['sources'][provider])}")
    return "\n".join(lines) + "\n"


def render_unavailable() -> str:
    lines = [
        "## Current model map",
        "",
        "**Model map status**: unavailable; assess at implementation time.",
        "",
        "| Tier | Anthropic | OpenAI | Google | Cursor |",
        "|---|---|---|---|---|",
    ]
    deferred = " | ".join(f"`{ASSESS_LATER}`" for _ in PROVIDERS)
    lines.extend(f"| {tier} | {deferred} |" for tier in TIERS)
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    score_parser = subparsers.add_parser("score", help="score five rubric signals")
    score_parser.add_argument("signals", nargs=5, choices=SIGNAL_LEVELS)
    score_parser.add_argument("--uncertain", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="validate a map JSON")
    validate_parser.add_argument("path", type=Path)

    render_parser = subparsers.add_parser("render", help="render a validated map")
    render_parser.add_argument("path", type=Path)
    render_parser.add_argument("--status", choices=("fresh", "offline"), required=True)
    render_parser.add_argument("--as-of")

    subparsers.add_parser("fallback", help="render the bundled dated snapshot")
    subparsers.add_parser("unavailable", help="render the no-snapshot fallback")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "score":
            print(json.dumps(score_signals(args.signals, uncertain=args.uncertain)))
        elif args.command == "validate":
            data = load_map(args.path)
            print(
                json.dumps(
                    {
                        "valid": True,
                        "verified_as_of": data["verified_as_of"],
                        "tiers": len(data["tiers"]),
                        "providers": len(PROVIDERS),
                    }
                )
            )
        elif args.command == "render":
            print(
                render_map(load_map(args.path), status=args.status, as_of=args.as_of),
                end="",
            )
        elif args.command == "fallback":
            print(
                render_map(load_map(DEFAULT_SNAPSHOT), status="offline", as_of=None),
                end="",
            )
        else:
            print(render_unavailable(), end="")
    except (MapValidationError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
