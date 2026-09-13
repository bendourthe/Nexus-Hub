#!/usr/bin/env python3
"""Resolve presentation intake without reading sources or generating content."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

CHOICES = {
    "presentation": ("yes", "no"),
    "presentation_theme": ("light", "dark", "mixed"),
    "presentation_depth": ("concise", "balanced", "deep-dive"),
}
QUESTIONS = {
    "presentation": "Include Presentation Mode on the title page and global top menu?",
    "presentation_theme": "Which theme should presentation mode use?",
    "presentation_depth": "How much of the main page should presentation mode cover?",
}
DEFAULTS = {
    "presentation": "yes",
    "presentation_theme": "mixed",
    "presentation_depth": "balanced",
}


def resolve(
    explicit: dict[str, Any],
    *,
    session: dict[str, Any] | None = None,
    project: dict[str, Any] | None = None,
    interactive: bool = True,
) -> dict[str, Any]:
    """Current explicit values precede session answers and approved project policy."""
    values: dict[str, Any] = {}
    origins: dict[str, str] = {}
    notes: list[str] = []
    layers = [
        (explicit, "explicit"),
        (session or {}, "session"),
        (project or {}, "project"),
    ]
    for source, origin in layers:
        for key, value in source.items():
            if key in values:
                continue
            if key == "complete_source" and type(value) is not bool:
                raise TypeError("complete_source requires an explicit boolean")
            if key in CHOICES and value not in CHOICES[key]:
                notes.append(f"Invalid {key}: {value}; use {'|'.join(CHOICES[key])}.")
                continue
            values[key], origins[key] = value, origin
    nav = explicit.get("nav")
    if nav is not None:
        if nav not in {"scroll", "slides"}:
            notes.append(
                "Invalid --nav; use scroll|slides. Reading starts in scroll mode."
            )
        else:
            notes.append(
                "Legacy --nav is a compatibility alias; the reading page remains the entry view."
            )
    if explicit.get("presentation") not in CHOICES["presentation"] and (
        nav == "slides"
        or any(
            key in explicit and explicit[key] in CHOICES[key]
            for key in ("presentation_theme", "presentation_depth")
        )
    ):
        values["presentation"], origins["presentation"] = "yes", "explicit-alias"
    if values.get("complete_source"):
        for key, required in (
            ("verbosity", "comprehensive"),
            ("presentation_depth", "deep-dive"),
        ):
            if key in explicit and explicit[key] != required:
                if origins["complete_source"] != "explicit":
                    continue
                return {
                    "status": "conflict",
                    "conflict": f"Complete-source intent contradicts explicit {key}={explicit[key]}",
                    "values": values,
                    "provenance": origins,
                    "questions": [],
                    "notes": notes,
                }
            values[key], origins[key] = required, origins["complete_source"]
    if not interactive:
        for key, value in DEFAULTS.items():
            if key not in values:
                values[key], origins[key] = value, "default"
    if values.get("presentation") == "no":
        if (
            any(key in explicit for key in ("presentation_theme", "presentation_depth"))
            or nav == "slides"
        ):
            notes.append(
                "Presentation is No; theme, depth and legacy slides options are inapplicable."
            )
        questions: list[str] = []
        presentation = {"enabled": False}
    else:
        pending = (
            ["presentation"]
            if "presentation" not in values
            else [
                key
                for key in ("presentation_theme", "presentation_depth")
                if key not in values
            ]
        )
        questions = pending
        presentation = {
            "enabled": True,
            "theme": values.get("presentation_theme"),
            "depth": values.get("presentation_depth"),
        }
    return {
        "status": "pending" if questions else "resolved",
        "values": values,
        "provenance": origins,
        "presentation": presentation,
        "questions": [
            {"axis": key, "title": QUESTIONS[key], "choices": CHOICES[key]}
            for key in questions
        ],
        "notes": notes,
    }


def save_themes(
    slide_ids: list[str], policy: str, seed: str, previous: dict[str, str] | None = None
) -> dict[str, str]:
    """Resolve themes once during authoring; unchanged IDs retain their assignment."""
    if (
        not slide_ids
        or len(set(slide_ids)) != len(slide_ids)
        or policy not in {"light", "dark", "mixed"}
    ):
        raise ValueError("Unique slide IDs and valid theme policy required")
    if policy != "mixed":
        return dict.fromkeys(slide_ids, policy)
    previous = previous or {}
    if any(value not in {"light", "dark"} for value in previous.values()):
        raise ValueError("Invalid saved theme")
    result = {
        key: previous.get(
            key, random.Random(seed + ":" + key).choice(("light", "dark"))
        )
        for key in slide_ids
    }
    if len(slide_ids) > 1 and len(set(result.values())) == 1:
        fresh = [key for key in slide_ids if key not in previous]
        if not fresh:
            raise ValueError(
                "Saved mixed policy lacks both themes; author must resolve it"
            )
        result[fresh[-1]] = (
            "dark" if next(iter(result.values())) == "light" else "light"
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="JSON with explicit/session/project option objects",
    )
    parser.add_argument("--non-interactive", action="store_true")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or any(
            not isinstance(data.get(key, {}), dict)
            for key in ("explicit", "session", "project")
        ):
            raise TypeError("Intake input must contain option objects")
        result = resolve(
            data.get("explicit", {}),
            session=data.get("session"),
            project=data.get("project"),
            interactive=not args.non_interactive,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if result["status"] == "conflict" else 0
    except (ValueError, TypeError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
