"""Build GitHub Copilot native hook files from the catalog registration."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ._hooks_common import script_basename, sourced_modules

COPILOT_COMPAT_EVENTS = frozenset(
    {
        "SessionStart",
        "SessionEnd",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "Stop",
        "PreCompact",
        "Notification",
    }
)

_COPILOT_PERMISSION_AUTHORITATIVE_SCRIPTS = frozenset({"rewrite-command.sh"})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bash_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _command_pair(
    script: str, base: str, event: str, src_hooks_dir: Path
) -> tuple[str, str]:
    bash_script = _bash_quote(f"{base}/{script}")
    powershell_script = _powershell_quote(f"{base}/{script}")
    if script.endswith(".py"):
        bash_child = f"python3 {bash_script}"
        powershell_child = f"python {powershell_script}"
    else:
        sibling = f"{Path(script).stem}.ps1"
        bash_child = f"bash {bash_script}"
        powershell_child = (
            "powershell -NoProfile -ExecutionPolicy Bypass "
            f"-File {_powershell_quote(f'{base}/{sibling}')}"
        )
    bash_authority = ""
    powershell_authority = ""
    if script in _COPILOT_PERMISSION_AUTHORITATIVE_SCRIPTS:
        bash_authority = f" --handler-sha256 {_sha256(src_hooks_dir / script)}"
        powershell_authority = (
            f" --handler-sha256 {_sha256(src_hooks_dir / sibling)}"
        )
    compat = f"{base}/copilot-hook-compat.py"
    return (
        (
            f"python3 {_bash_quote(compat)} copilot {event} --handler {script}"
            f"{bash_authority} -- {bash_child}"
        ),
        (
            f"python {_powershell_quote(compat)} copilot {event} --handler {script}"
            f"{powershell_authority} -- {powershell_child}"
        ),
    )


def build_copilot_hooks(
    settings: dict, src_hooks_dir: Path, command_base: str
) -> tuple[dict, set[str], list[str]]:
    """Return ``(versioned config, scripts, skipped reasons)`` for Copilot."""
    events: dict[str, list[dict[str, object]]] = {}
    scripts: set[str] = set()
    skipped: list[str] = []
    source_events = settings.get("hooks")
    if not isinstance(source_events, dict):
        return {"version": 1, "hooks": {}}, scripts, ["missing hooks object"]
    for event, groups in source_events.items():
        if event not in COPILOT_COMPAT_EVENTS:
            skipped.append(f"{event}: no Copilot compatibility event")
            continue
        if not isinstance(groups, list):
            skipped.append(f"{event}: event value is not an array")
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            matcher = group.get("matcher", "")
            for handler in group.get("hooks", []):
                if not isinstance(handler, dict):
                    continue
                script = script_basename(str(handler.get("command", "")))
                if script is None or not (src_hooks_dir / script).exists():
                    skipped.append(f"{event}: missing catalog script {script or '<none>'}")
                    continue
                bash, powershell = _command_pair(
                    script, command_base, event, src_hooks_dir
                )
                entry: dict[str, object] = {
                    "type": "command",
                    "bash": bash,
                    "powershell": powershell,
                    "timeoutSec": 30,
                }
                if isinstance(matcher, str) and matcher:
                    entry["matcher"] = matcher
                events.setdefault(event, []).append(entry)
                scripts.add(script)
                if script.endswith(".sh"):
                    sibling = f"{Path(script).stem}.ps1"
                    if (src_hooks_dir / sibling).exists():
                        scripts.add(sibling)
    scripts |= sourced_modules(scripts, src_hooks_dir)
    return {"version": 1, "hooks": events}, scripts, skipped


__all__ = ["COPILOT_COMPAT_EVENTS", "build_copilot_hooks"]
