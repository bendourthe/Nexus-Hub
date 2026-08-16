"""Retire v3.17.0 provider overrides without stranding elevated config.

The removed autonomy controller stored a byte-for-byte backup beside every
project config it changed. This temporary SessionStart migration restores those
backups when an affected project is next opened. It also gives the installers a
stdlib-only way to remove the controller's stale hook registrations from an
existing Claude settings file.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any


STATE_VERSION = 1
STATE_RELATIVE_PATH = Path(".nexus-hub") / "autonomy-state.json"
LEGACY_HOOK_MARKERS = ("autonomy-expiry", "autonomy-guard")
MIGRATION_SCRIPT = "retire-provider-override.py"


def _atomic_write(path: Path, content: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            os.chmod(path, mode)
    finally:
        temporary.unlink(missing_ok=True)


def _git_root(project: Path) -> Path | None:
    candidate = project.expanduser().resolve()
    if candidate.is_file():
        candidate = candidate.parent
    result = subprocess.run(
        ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return Path(result.stdout.strip()).resolve()


def _project_path(root: Path, raw: Any, field: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"legacy {field} is missing or invalid")
    resolved = Path(raw).expanduser().resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"legacy {field} escapes the project") from exc
    return resolved


def _write_state(path: Path, state: Mapping[str, Any]) -> None:
    platforms = state.get("platforms")
    if isinstance(platforms, dict) and not platforms:
        path.unlink(missing_ok=True)
        return
    body = json.dumps(dict(state), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    _atomic_write(path, body.encode("utf-8"))


def restore_legacy_state(project: Path) -> int:
    """Restore every valid legacy entry and preserve failures for retry."""
    root = _git_root(project)
    if root is None:
        return 0
    state_path = root / STATE_RELATIVE_PATH
    if not state_path.is_file():
        return 0

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or state.get("version") != STATE_VERSION:
            raise ValueError("unsupported legacy state version")
        platforms = state.get("platforms")
        if not isinstance(platforms, dict):
            raise ValueError("legacy platforms value must be an object")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Nexus-Hub could not read retired provider state: {exc}", file=sys.stderr)
        return 1

    failed = False
    for platform, raw_entry in list(platforms.items()):
        try:
            if not isinstance(raw_entry, dict):
                raise ValueError("legacy platform entry must be an object")
            config_path = _project_path(root, raw_entry.get("config_path"), "config path")
            backup_path = _project_path(root, raw_entry.get("backup_path"), "backup path")
            if not backup_path.is_file():
                raise FileNotFoundError(f"recorded backup is missing at {backup_path}")

            if bool(raw_entry.get("original_exists")):
                _atomic_write(config_path, backup_path.read_bytes())
            else:
                config_path.unlink(missing_ok=True)

            del platforms[platform]
            _write_state(state_path, state)
            backup_path.unlink(missing_ok=True)
            print(
                f"Nexus-Hub restored {platform} configuration from the retired provider override."
            )
        except (OSError, ValueError) as exc:
            failed = True
            print(
                f"Nexus-Hub preserved retired provider state for {platform}: {exc}",
                file=sys.stderr,
            )
    return 1 if failed else 0


def _is_legacy_handler(handler: Any) -> bool:
    if not isinstance(handler, dict):
        return False
    command = handler.get("command")
    return isinstance(command, str) and any(
        marker in command for marker in LEGACY_HOOK_MARKERS
    )


def migrate_claude_settings(settings_path: Path, hook_command: str) -> int:
    """Remove stale controller handlers and register the retirement migration."""
    if not settings_path.exists():
        return 0
    try:
        original = settings_path.read_bytes()
        document = json.loads(original.decode("utf-8"))
        if not isinstance(document, dict):
            raise ValueError("settings root must be an object")
        hooks = document.get("hooks")
        if hooks is None:
            hooks = {}
            document["hooks"] = hooks
        if not isinstance(hooks, dict):
            raise ValueError("settings hooks value must be an object")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Nexus-Hub left malformed Claude settings untouched: {exc}", file=sys.stderr)
        return 1

    for event, raw_groups in list(hooks.items()):
        if not isinstance(raw_groups, list):
            continue
        groups: list[Any] = []
        for raw_group in raw_groups:
            if not isinstance(raw_group, dict) or not isinstance(raw_group.get("hooks"), list):
                groups.append(raw_group)
                continue
            group = dict(raw_group)
            group["hooks"] = [
                handler for handler in raw_group["hooks"] if not _is_legacy_handler(handler)
            ]
            if group["hooks"]:
                groups.append(group)
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]

    registered = any(
        isinstance(handler, dict)
        and MIGRATION_SCRIPT in str(handler.get("command", ""))
        for group in hooks.get("SessionStart", [])
        if isinstance(group, dict)
        for handler in group.get("hooks", [])
        if isinstance(group.get("hooks"), list)
    )
    if not registered:
        hooks.setdefault("SessionStart", []).append(
            {
                "matcher": "",
                "hooks": [{"type": "command", "command": hook_command}],
            }
        )

    updated = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    if updated == original:
        return 0
    backup_path = settings_path.with_name(settings_path.name + ".v3.17.2.bak")
    try:
        if not backup_path.exists():
            _atomic_write(backup_path, original)
        _atomic_write(settings_path, updated)
    except OSError as exc:
        print(f"Nexus-Hub could not migrate Claude settings: {exc}", file=sys.stderr)
        return 1
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Retire Nexus-Hub provider overrides safely")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--settings", type=Path)
    parser.add_argument("--hook-command")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    settings_result = 0
    if args.settings is not None:
        if not args.hook_command:
            print("--hook-command is required with --settings", file=sys.stderr)
            return 2
        settings_result = migrate_claude_settings(args.settings, args.hook_command)
    project_result = restore_legacy_state(args.project)
    return 1 if settings_result or project_result else 0


if __name__ == "__main__":
    raise SystemExit(main())
