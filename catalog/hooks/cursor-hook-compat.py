"""Run one Nexus-Hub hook with Claude Code and Cursor compatible I/O.

Claude Code accepts a successful hook that writes nothing to stdout. Cursor
imports Claude hook registrations but requires stdout to contain one JSON object.
This launcher preserves Claude behavior byte-for-byte and normalizes only payloads
that carry Cursor's ``cursor_version`` marker.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, TextIO

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
NEXUS_TAG = "[Nexus-Hub: cursor-hook-compat]"


def _nexus_esc(value: str) -> str:
    """Make CR, LF, ESC and the other C0 control characters visible.

    An echoed value (a command, a file name) can then never start a forged
    tagged line.
    """
    out: list[str] = []
    for ch in value:
        code = ord(ch)
        if code == 9:
            out.append("\\t")
        elif code == 10:
            out.append("\\n")
        elif code == 13:
            out.append("\\r")
        elif code < 32 or code == 127:
            out.append(f"\\x{code:02x}")
        else:
            out.append(ch)
    return "".join(out)


def _nexus_tagged(message: str) -> str:
    """The tagged form of a message, for a JSON message field."""
    return f"{NEXUS_TAG} {message}"


def _nexus_msg(message: str, *more: str, stream: TextIO | None = None) -> None:
    """Print the tag and the message (stderr by default); further arguments are continuation lines."""
    out = stream or sys.stderr
    out.write(_nexus_tagged(message) + "\n")
    for line in more:
        out.write(line + "\n")


_CURSOR_DESCRIPTION_HOOKS = {
    "format-bash-description.py",
    "format-powershell-description.py",
    "require-description.sh",
    "require-description.ps1",
    "require-powershell-description.sh",
    "require-powershell-description.ps1",
}


def _load_payload(raw: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None


def _is_cursor(payload: dict[str, Any] | None) -> bool:
    return payload is not None and "cursor_version" in payload


def _cursor_allow(payload: dict[str, Any]) -> dict[str, str]:
    event = str(payload.get("hook_event_name") or "").lower()
    if event in {"pretooluse", "beforeshellexecution", "beforemcpexecution"}:
        return {"permission": "allow"}
    return {}


def _cursor_payload_for_hook(payload: dict[str, Any]) -> str:
    """Add Claude's tool_input.command shape for Cursor's dedicated shell event."""
    command = payload.get("command")
    if not isinstance(command, str):
        return json.dumps(payload)
    translated = dict(payload)
    tool_input = translated.get("tool_input")
    translated_input = dict(tool_input) if isinstance(tool_input, dict) else {}
    translated_input.setdefault("command", command)
    translated["tool_input"] = translated_input
    return json.dumps(translated)


def _valid_json_object(value: str) -> bool:
    try:
        return isinstance(json.loads(value), dict)
    except (json.JSONDecodeError, TypeError):
        return False


def _write_stderr(value: str) -> None:
    if value:
        sys.stderr.write(value)  # nexus: hook-msg-exempt relays the child hook's output
        if not value.endswith("\n"):
            sys.stderr.write("\n")  # nexus: hook-msg-exempt relays the child hook's output


def _catalog_hook_names(catalog_hooks_dir: Path) -> set[str]:
    return {
        path.name
        for path in catalog_hooks_dir.iterdir()
        if path.is_file() and path.suffix in {".sh", ".ps1", ".py"}
    }


def _rewrite_hook_command(
    command: str,
    *,
    windows: bool,
    catalog_names: set[str],
    scope: str,
    global_hooks_dir: str,
) -> str:
    """Return a host-native, compatibility-wrapped Nexus-Hub hook command."""
    matches = list(
        re.finditer(
            r'(?:(?:"(?P<quoted>[^"]+\.(?:sh|ps1|py))")|(?P<plain>[^\s"]+\.(?:sh|ps1|py)))\s*$',
            command,
            re.IGNORECASE,
        )
    )
    if not matches:
        return command
    raw_path = matches[-1].group("quoted") or matches[-1].group("plain")
    normalized_path = raw_path.replace("\\", "/")
    if not re.search(r"(^|/)\.claude/hooks/", normalized_path):
        return command
    script_name = re.split(r"[\\/]", raw_path)[-1]
    if script_name not in catalog_names:
        return command

    stem = Path(script_name).stem
    target_name = script_name if script_name.endswith(".py") else f"{stem}.{'ps1' if windows else 'sh'}"
    if target_name not in catalog_names:
        return command
    separator_index = max(raw_path.rfind("/"), raw_path.rfind("\\"))
    if separator_index < 0:
        return command
    base = raw_path[:separator_index]
    if scope == "global":
        base = global_hooks_dir
    target = f"{base}/{target_name}"
    compat = f"{base}/cursor-hook-compat.py"
    python_runner = "python" if windows else "python3"
    if target_name.endswith(".py"):
        hook_command = f'{python_runner} "{target}"'
    elif windows:
        hook_command = f'powershell -NoProfile -ExecutionPolicy Bypass -File "{target}"'
    else:
        hook_command = f'bash "{target}"'
    return f'{python_runner} "{compat}" {hook_command}'


def _rewrite_settings_object(
    value: Any,
    *,
    windows: bool,
    catalog_names: set[str],
    scope: str,
    global_hooks_dir: str,
) -> Any:
    if isinstance(value, list):
        return [
            _rewrite_settings_object(
                item,
                windows=windows,
                catalog_names=catalog_names,
                scope=scope,
                global_hooks_dir=global_hooks_dir,
            )
            for item in value
        ]
    if not isinstance(value, dict):
        return value
    rewritten = {
        key: _rewrite_settings_object(
            item,
            windows=windows,
            catalog_names=catalog_names,
            scope=scope,
            global_hooks_dir=global_hooks_dir,
        )
        for key, item in value.items()
    }
    command = rewritten.get("command")
    if rewritten.get("type") == "command" and isinstance(command, str):
        rewritten["command"] = _rewrite_hook_command(
            command,
            windows=windows,
            catalog_names=catalog_names,
            scope=scope,
            global_hooks_dir=global_hooks_dir,
        )
    return rewritten


def rewrite_settings(
    settings_file: Path, catalog_hooks_dir: Path, host: str, scope: str
) -> int:
    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8-sig"))
        catalog_names = _catalog_hook_names(catalog_hooks_dir)
        rewritten = _rewrite_settings_object(
            settings,
            windows=host == "windows",
            catalog_names=catalog_names,
            scope=scope,
            global_hooks_dir=(settings_file.resolve().parent / "hooks").as_posix(),
        )
        settings_file.write_text(
            json.dumps(rewritten, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    except (OSError, json.JSONDecodeError) as exc:
        _nexus_msg(f"could not rewrite {_nexus_esc(str(settings_file))}: {_nexus_esc(str(exc))}")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    command = list(sys.argv[1:] if argv is None else argv)
    if command[:1] == ["--rewrite-settings"]:
        if (
            len(command) != 8
            or command[2] != "--catalog-hooks-dir"
            or command[4] != "--host"
            or command[5] not in {
                "windows",
                "posix",
            }
            or command[6] != "--scope"
            or command[7] not in {"global", "workspace"}
        ):
            _nexus_msg(
                "usage: cursor-hook-compat.py --rewrite-settings <settings.json> --catalog-hooks-dir <dir> --host <windows|posix> --scope <global|workspace>"
            )
            return 2
        return rewrite_settings(
            Path(command[1]), Path(command[3]), command[5], command[7]
        )
    if not command:
        _nexus_msg("missing hook command")
        return 2

    raw = sys.stdin.read()
    payload = _load_payload(raw)
    cursor = _is_cursor(payload)
    hook_name = Path(command[-1]).name

    # Cursor's Shell payload has no Claude-specific description parameter. The
    # formatter/gate pair therefore cannot make a meaningful decision there.
    if cursor and hook_name in _CURSOR_DESCRIPTION_HOOKS:
        json.dump(_cursor_allow(payload), sys.stdout, separators=(",", ":"))
        sys.stdout.write("\n")
        return 0

    hook_input = _cursor_payload_for_hook(payload) if cursor else raw
    try:
        result = subprocess.run(
            command, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            input=hook_input,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        _nexus_msg(f"could not start {_nexus_esc(hook_name)}: {_nexus_esc(str(exc))}")
        return 2

    if not cursor:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)  # nexus: hook-msg-exempt relays the child hook's output
        return result.returncode

    _write_stderr(result.stderr)  # nexus: hook-msg-exempt relays the child hook's output
    if result.returncode != 0:
        # Cursor treats a non-zero hook exit as a block. Keep prose away from
        # stdout because its parser still expects that stream to be JSON.
        _write_stderr(result.stdout)  # nexus: hook-msg-exempt relays the child hook's output
        return result.returncode

    stripped = result.stdout.strip()
    if stripped and _valid_json_object(stripped):
        sys.stdout.write(stripped + "\n")
        return 0

    # Advisory hooks historically wrote prose to stdout. Preserve it in the
    # Hooks output channel without corrupting Cursor's JSON decision stream.
    _write_stderr(result.stdout)  # nexus: hook-msg-exempt relays the child hook's output
    json.dump(_cursor_allow(payload), sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
