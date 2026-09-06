"""Translate host hook protocols for Nexus-Hub's Claude-shaped hook scripts.

This file is copied beside installed hook scripts and executed by Antigravity,
GitHub Copilot, or Devin Desktop Cascade. It uses only the Python standard
library and never makes network calls.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

_EVENT_NAMES = {
    "pre_run_command": "PreToolUse",
    "post_run_command": "PostToolUse",
    "pre_write_code": "PreToolUse",
    "post_write_code": "PostToolUse",
    "pre_user_prompt": "UserPromptSubmit",
    "post_cascade_response": "Stop",
}

# Only handlers that validate the host's explicit permission rules may grant a
# Copilot tool call. Every other catalog handler is deny-only at this bridge:
# it may still rewrite arguments, ask, or deny, but an `allow` is omitted so
# Copilot retains its normal permission flow.
COPILOT_PERMISSION_AUTHORITATIVE_HANDLERS = frozenset(
    {
        "rewrite-command.sh",
    }
)

_COPILOT_AUTHORITY_CHILDREN = {
    "rewrite-command.sh": ("rewrite-command.sh", "bash"),
    "rewrite-command.ps1": ("rewrite-command.sh", "powershell"),
}


def _windows_host() -> bool:
    """Whether this host is Windows.

    Indirected so a test can exercise the Windows branch on any platform.
    Patching ``os.name`` directly is not viable: ``pathlib.Path()`` selects
    ``WindowsPath`` from ``os.name`` AT CALL TIME, so faking it on POSIX makes
    every later ``Path(...)`` raise ``NotImplementedError`` instead of taking
    the branch under test.
    """
    return os.name == "nt"


_WINDOWS_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
)


def _resolve_bash_command(command: Sequence[str]) -> list[str]:
    """Return ``command`` with a bare ``bash`` resolved to an interpreter that runs.

    On Windows, ``bash`` on PATH is commonly the WSL launcher stub in System32.
    With no distribution installed it prints its notice to STDOUT and exits
    non-zero without writing to stderr, so the bridge sees a non-zero child with
    no diagnostic and denies. The guard then refuses every tool call it was meant
    to police, which reads to the user as a broken agent rather than a missing
    interpreter. `tests/conftest.py` documents the same hazard for the suite.

    Only a BARE ``bash`` is rewritten, and only to a verified absolute Git Bash.
    An absolute interpreter the caller chose is never second-guessed, and a host
    with no Git Bash keeps the original command so PATH resolution still applies.
    The rewrite happens at the execution site only: the permission-authority
    check still inspects the ORIGINAL command, so its binding is unchanged.
    """
    resolved = list(command)
    if not _windows_host() or not resolved or resolved[0] != "bash":
        return resolved
    for candidate in _WINDOWS_BASH_CANDIDATES:
        if Path(candidate).is_file():
            resolved[0] = candidate
            break
    return resolved


def _link_like(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(callable(is_junction) and is_junction())


def _copilot_permission_authoritative(
    handler_name: str,
    command: Sequence[str],
    expected_sha256: str,
    *,
    compat_path: str | Path | None = None,
) -> bool:
    """Return whether one generated Copilot child may grant permission."""
    if re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None:
        return False
    child_path_text = ""
    interpreter = ""
    if len(command) == 2 and command[0] == "bash":
        interpreter = "bash"
        child_path_text = command[1]
    elif len(command) == 6 and tuple(command[:5]) == (
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
    ):
        interpreter = "powershell"
        child_path_text = command[5]
    else:
        return False

    child_path = Path(child_path_text).expanduser()
    if ".." in child_path.parts:
        return False
    binding = _COPILOT_AUTHORITY_CHILDREN.get(child_path.name)
    if binding is None:
        return False
    expected_handler, expected_interpreter = binding
    if handler_name != expected_handler or interpreter != expected_interpreter:
        return False

    wrapper_path = Path(compat_path or __file__).expanduser()
    if wrapper_path.name != "copilot-hook-compat.py":
        return False
    try:
        if any(_link_like(path) for path in (wrapper_path, wrapper_path.parent, child_path)):
            return False
        wrapper = wrapper_path.resolve(strict=True)
        child = child_path.resolve(strict=True)
        expected_child = (wrapper.parent / child_path.name).resolve(strict=True)
        if wrapper.stat().st_nlink != 1 or child.stat().st_nlink != 1:
            return False
        actual_sha256 = hashlib.sha256(child.read_bytes()).hexdigest()
    except OSError:
        return False
    return (
        child.is_file()
        and child == expected_child
        and child.parent == wrapper.parent
        and hmac.compare_digest(actual_sha256, expected_sha256)
    )


def translate_payload(payload: dict[str, Any], event: str, tool_name: str) -> dict[str, Any]:
    """Return the Claude-compatible subset consumed by catalog hook scripts."""
    info = payload.get("tool_info")
    tool_info = info if isinstance(info, dict) else {}
    translated: dict[str, Any] = {
        "hook_event_name": _EVENT_NAMES.get(event, event),
        "tool_name": tool_name,
    }
    trajectory_id = payload.get("trajectory_id")
    if trajectory_id is not None:
        translated["session_id"] = trajectory_id

    if event in {"pre_run_command", "post_run_command"}:
        translated["tool_input"] = {
            "command": tool_info.get("command_line", ""),
            "cwd": tool_info.get("cwd", ""),
        }
    elif event in {"pre_write_code", "post_write_code"}:
        edits = tool_info.get("edits")
        edit_rows = [row for row in edits if isinstance(row, dict)] if isinstance(edits, list) else []
        old_text = "\n".join(str(row.get("old_string", "")) for row in edit_rows)
        new_text = "\n".join(str(row.get("new_string", "")) for row in edit_rows)
        translated["tool_input"] = {
            "file_path": tool_info.get("file_path", ""),
            "path": tool_info.get("file_path", ""),
            "old_string": old_text,
            "new_string": new_text,
            "content": new_text,
        }
    elif event == "pre_user_prompt":
        translated["prompt"] = tool_info.get("user_prompt", "")
    elif event == "post_cascade_response":
        translated["last_assistant_message"] = tool_info.get("response", "")
    return translated


_ANTIGRAVITY_ARG_ALIASES = {
    "command_line": "command",
    "target_file": "file_path",
    "file_path": "file_path",
    "absolute_path": "file_path",
    "code_content": "content",
    "new_content": "content",
}


def _snake_case(name: str) -> str:
    first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first).lower()


def _antigravity_tool_input(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    translated: dict[str, Any] = dict(value)
    for key, item in value.items():
        snake = _snake_case(str(key))
        translated.setdefault(snake, item)
        alias = _ANTIGRAVITY_ARG_ALIASES.get(snake)
        if alias is not None:
            translated.setdefault(alias, item)
    file_path = translated.get("file_path") or translated.get("path")
    if file_path is not None:
        translated.setdefault("file_path", file_path)
        translated.setdefault("path", file_path)

    replacement = translated.get("replacement_content")
    if isinstance(replacement, str):
        translated.setdefault("new_string", replacement)
        translated.setdefault("content", replacement)

    chunks = translated.get("replacement_chunks")
    if isinstance(chunks, list):
        edits: list[dict[str, Any]] = []
        replacement_texts: list[str] = []
        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue
            edit: dict[str, Any] = dict(chunk)
            for key, item in chunk.items():
                edit.setdefault(_snake_case(str(key)), item)
            edit_replacement = edit.get("replacement_content")
            if isinstance(edit_replacement, str):
                edit.setdefault("new_string", edit_replacement)
                replacement_texts.append(edit_replacement)
            edits.append(edit)
        translated.setdefault("edits", edits)
        if replacement_texts:
            combined = "\n".join(replacement_texts)
            translated.setdefault("new_string", combined)
            translated.setdefault("content", combined)
    return translated


def translate_antigravity_payload(
    payload: dict[str, Any], event: str
) -> dict[str, Any]:
    """Convert Antigravity camelCase/PascalCase input to the catalog contract."""
    tool_call = payload.get("toolCall")
    call = tool_call if isinstance(tool_call, dict) else {}
    translated: dict[str, Any] = {
        "hook_event_name": event,
        "tool_name": str(call.get("name", "")),
        "tool_input": _antigravity_tool_input(call.get("args")),
    }
    for source, target in {
        "conversationId": "session_id",
        "transcriptPath": "transcript_path",
        "artifactDirectoryPath": "artifact_directory_path",
        "modelName": "model_name",
        "stepIdx": "step_index",
    }.items():
        if source in payload:
            translated[target] = payload[source]
    return translated


def _copilot_tool_args(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def translate_copilot_payload(payload: dict[str, Any], event: str) -> dict[str, Any]:
    """Convert either native camelCase or compatible snake_case Copilot input."""
    native = "toolName" in payload or "toolArgs" in payload
    tool_name = payload.get("toolName") if native else payload.get("tool_name")
    raw_args = payload.get("toolArgs") if native else payload.get("tool_input")
    translated: dict[str, Any] = {
        "hook_event_name": event,
        "tool_name": str(tool_name or ""),
        "tool_input": _copilot_tool_args(raw_args),
    }
    for source, target in (
        ("sessionId", "session_id"),
        ("session_id", "session_id"),
        ("cwd", "cwd"),
        ("transcriptPath", "transcript_path"),
        ("transcript_path", "transcript_path"),
    ):
        if source in payload and target not in translated:
            translated[target] = payload[source]
    return translated


def _json_object(text: str) -> dict[str, Any]:
    if not text.strip():
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _reason(stderr: str, payload: dict[str, Any], fallback: str) -> str:
    specific = payload.get("hookSpecificOutput")
    hook_output = specific if isinstance(specific, dict) else payload
    candidate = hook_output.get("permissionDecisionReason") or hook_output.get("reason")
    if isinstance(candidate, str) and candidate.strip():
        return candidate.strip()
    if stderr.strip():
        return stderr.strip()
    return fallback


def translate_child_result(
    host: str,
    event: str,
    *,
    permission_authoritative: bool = False,
    stdout: str,
    stderr: str,
    returncode: int,
) -> tuple[dict[str, Any], int]:
    """Translate a catalog hook result into one documented host output object."""
    payload = _json_object(stdout)
    specific = payload.get("hookSpecificOutput")
    child = specific if isinstance(specific, dict) else payload

    if host == "antigravity":
        if returncode == 2:
            return {
                "decision": "deny",
                "reason": _reason(stderr, payload, "Nexus-Hub guard denied the tool call."),
            }, 0
        if returncode != 0:
            return {
                "decision": "ask",
                "reason": _reason(stderr, payload, "Nexus-Hub guard failed; review the tool call."),
            }, 0
        updated = child.get("updatedInput")
        if isinstance(updated, dict):
            return {
                "decision": "ask",
                "reason": "Nexus-Hub requested a tool-input rewrite that Antigravity hooks cannot apply.",
            }, 0
        decision = child.get("permissionDecision") or child.get("decision")
        if decision in {"allow", "deny", "ask", "force_ask", "deny_unless_prior_grant"}:
            output: dict[str, Any] = {"decision": decision}
            reason = _reason("", payload, "")
            if reason:
                output["reason"] = reason
            return output, 0
        # Empty output from a Claude guard means "no objection", not automatic
        # approval. Antigravity requires a decision, so retain human policy flow.
        return {"decision": "ask"}, 0

    if host == "copilot":
        if event == "PreToolUse" and returncode != 0:
            return {
                "permissionDecision": "deny",
                "permissionDecisionReason": _reason(
                    stderr, payload, "Nexus-Hub guard denied the tool call."
                ),
            }, 0
        if returncode != 0:
            return {}, returncode
        output = {}
        decision = child.get("permissionDecision")
        if decision in {"deny", "ask"} or (
            decision == "allow" and permission_authoritative is True
        ):
            output["permissionDecision"] = decision
        if decision == "deny":
            output["permissionDecisionReason"] = _reason(
                "", payload, "Nexus-Hub guard denied the tool call."
            )
        elif decision != "allow" or permission_authoritative is True:
            reason = child.get("permissionDecisionReason")
            if isinstance(reason, str) and reason:
                output["permissionDecisionReason"] = reason
        updated = child.get("updatedInput")
        if isinstance(updated, dict):
            output["modifiedArgs"] = updated
        context = child.get("additionalContext")
        if isinstance(context, str) and context:
            output["additionalContext"] = context
        return output, 0

    return payload, returncode


def _read_payload() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    host = "cascade"
    if args and args[0] in {"antigravity", "copilot", "cascade"}:
        host = args.pop(0)
    handler_name = ""
    handler_sha256 = ""
    if host == "cascade":
        valid = len(args) >= 4 and args[2] == "--"
    elif (
        host == "copilot"
        and len(args) >= 7
        and args[1] == "--handler"
        and args[3] == "--handler-sha256"
    ):
        valid = bool(args[2]) and bool(args[4]) and args[5] == "--"
    elif host == "copilot" and len(args) >= 5 and args[1] == "--handler":
        valid = bool(args[2]) and args[3] == "--"
    else:
        valid = len(args) >= 3 and args[1] == "--"
    if not valid:
        print(
            "hook-compat: expected [HOST] EVENT [TOOL] -- COMMAND [ARG ...]",
            file=sys.stderr,
        )
        return 0
    if host == "cascade":
        event, tool_name = args[0], args[1]
        command = args[3:]
    elif (
        host == "copilot"
        and len(args) >= 7
        and args[1] == "--handler"
        and args[3] == "--handler-sha256"
    ):
        event = args[0]
        handler_name = args[2]
        handler_sha256 = args[4]
        tool_name = ""
        command = args[6:]
    elif host == "copilot" and len(args) >= 5 and args[1] == "--handler":
        event = args[0]
        handler_name = args[2]
        tool_name = ""
        command = args[4:]
    else:
        event = args[0]
        tool_name = ""
        command = args[2:]
    if not command:
        return 0
    permission_authoritative = host == "copilot" and _copilot_permission_authoritative(
        handler_name, command, handler_sha256
    )
    payload = _read_payload()
    if host == "antigravity":
        translated = translate_antigravity_payload(payload, event)
    elif host == "copilot":
        translated = translate_copilot_payload(payload, event)
    else:
        translated = translate_payload(payload, event, tool_name)
    try:
        completed = subprocess.run(
            _resolve_bash_command(command),
            input=json.dumps(translated),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        message = f"hook-compat: {exc}"
        if host != "cascade":
            output, exit_code = translate_child_result(
                host,
                event,
                permission_authoritative=permission_authoritative,
                stdout="",
                stderr=message,
                returncode=1,
            )
            sys.stdout.write(json.dumps(output))
            print(message, file=sys.stderr)
            return exit_code
        print(message, file=sys.stderr)
        return 0
    if host == "cascade":
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        if completed.stderr:
            sys.stderr.write(completed.stderr)
        return completed.returncode
    output, exit_code = translate_child_result(
        host,
        event,
        permission_authoritative=(
            permission_authoritative
            and _copilot_permission_authoritative(
                handler_name, command, handler_sha256
            )
        ),
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )
    sys.stdout.write(json.dumps(output))
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "COPILOT_PERMISSION_AUTHORITATIVE_HANDLERS",
    "main",
    "translate_antigravity_payload",
    "translate_child_result",
    "translate_copilot_payload",
    "translate_payload",
]
