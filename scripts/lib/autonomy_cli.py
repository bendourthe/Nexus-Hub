"""Public command-line surface for time-bounded project autonomy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _eprint(message: str) -> None:
    print(message, file=sys.stderr)


def _load_autonomy_module():
    """Load the sibling policy engine without duplicating its decisions."""
    try:
        from . import autonomy
    except ImportError as exc:  # pragma: no cover - missing install artifact
        _eprint(
            "nexus-hub autonomy: scripts/lib/autonomy.py not found "
            f"({exc}). Re-run the installer."
        )
        return None
    return autonomy


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-hub autonomy",
        description="Manage project-scoped Nexus-Hub autonomy.",
    )
    parser.add_argument(
        "verb",
        nargs="?",
        choices=("status", "enable", "disable", "revert"),
        default="status",
    )
    parser.add_argument("--platform", help="Integration key to manage.")
    parser.add_argument(
        "--tier",
        choices=("edits", "full"),
        default="edits",
        help="Autonomy tier for enable (default: edits).",
    )
    parser.add_argument(
        "--ttl",
        type=int,
        default=60,
        help="Autonomy lifetime in minutes for enable (default: 60).",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print status as JSON for local integrations.",
    )
    return parser


def _public_tier(value: object) -> str:
    return "edits" if value == "edits_only" else str(value or "off")


def _format_remaining(seconds: object) -> str:
    if not isinstance(seconds, int) or seconds <= 0:
        return "-"
    minutes = max(1, (seconds + 59) // 60)
    hours, remainder = divmod(minutes, 60)
    return f"{hours}h {remainder}m" if hours else f"{remainder}m"


def _render_status(document: dict) -> None:
    project = document.get("project") or "not in a git repository"
    print(f"Project: {project}")
    note = document.get("note")
    if note:
        print(f"Note: {note}")
    print(f"{'Platform':<18} {'Support':<12} {'Status':<10} {'Tier':<8} TTL")
    for item in document.get("platforms", []):
        supported = "verified" if item.get("supported") else "unavailable"
        print(
            f"{item.get('platform', 'unknown')!s:<18} "
            f"{supported:<12} "
            f"{item.get('status', 'off')!s:<10} "
            f"{_public_tier(item.get('tier')):<8} "
            f"{_format_remaining(item.get('remaining_seconds'))}"
        )


def _resolve_platform(
    document: dict, requested: str | None, verb: str, tier: str
) -> str | None:
    if requested:
        return requested
    entries = list(document.get("platforms", []))
    if verb in {"disable", "revert"}:
        candidates = [item for item in entries if item.get("status") != "off"]
    else:
        engine_tier = "edits_only" if tier == "edits" else tier
        candidates = [
            item
            for item in entries
            if item.get("supported") and engine_tier in item.get("available_tiers", [])
        ]
    if len(candidates) == 1:
        return str(candidates[0]["platform"])
    _eprint(
        f"nexus-hub autonomy {verb}: choose a target with --platform <key>; "
        "the current project does not have one unambiguous target."
    )
    return None


def _operation_exit_code(result) -> int:
    print(result.message)
    if result.backup_path and result.changed:
        print(f"Backup: {result.backup_path}")
    return 0 if result.outcome not in {"error", "rejected"} else 2


def _confirm_edits_enable() -> bool:
    if not sys.stdin or not sys.stdin.isatty():
        _eprint("Edits autonomy requires an interactive confirmation.")
        return False
    try:
        answer = (
            input("Enable edits autonomy with this preview? [y/N] ").strip().lower()
        )
    except EOFError:
        return False
    return answer in {"y", "yes"}


def main(argv: list[str]) -> int:
    """Render and dispatch project-local autonomy operations to the core engine."""
    autonomy = _load_autonomy_module()
    if autonomy is None:
        return 2
    args = _build_parser().parse_args(argv)
    document = autonomy.status(project_dir=args.project)

    if args.verb == "status":
        if args.json:
            print(json.dumps(document, sort_keys=True))
        else:
            _render_status(document)
        return 0 if document.get("project") else 2

    platform = _resolve_platform(document, args.platform, args.verb, args.tier)
    if platform is None:
        return 2

    if args.verb == "disable":
        return _operation_exit_code(
            autonomy.disable(platform, project_dir=args.project)
        )
    if args.verb == "revert":
        return _operation_exit_code(autonomy.revert(platform, project_dir=args.project))

    if args.tier == "full" and (not sys.stdin or not sys.stdin.isatty()):
        _eprint(
            "Full autonomy requires an interactive terminal and typed project-name confirmation."
        )
        return 2

    engine_tier = "edits_only" if args.tier == "edits" else "full"
    preview = autonomy.enable(
        platform,
        engine_tier,
        args.ttl,
        project_dir=args.project,
        preview_only=True,
    )
    if preview.outcome != "preview":
        return _operation_exit_code(preview)
    print(preview.diff or "(No configuration diff.)")

    confirmation = None
    if args.tier == "full":
        project = Path(str(document["project"])).name
        try:
            confirmation = input(
                f"Type the project directory name '{project}' to enable full autonomy: "
            )
        except EOFError:
            return 2
    elif not _confirm_edits_enable():
        print("Autonomy enablement cancelled; no files were changed.")
        return 0

    result = autonomy.enable(
        platform,
        engine_tier,
        args.ttl,
        project_dir=args.project,
        confirmation=confirmation,
    )
    return _operation_exit_code(result)
