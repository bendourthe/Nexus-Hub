#!/usr/bin/env python3
"""user-command-shell-check: warn when a reply hands the user a command that
Windows PowerShell 5.1 cannot parse.

Part of Nexus-Hub. Registered on ``Stop`` in ``catalog/hooks/settings.json``.
The communication contract (``catalog/style-guides/agent-communication.md``,
section 3.3) says a command handed to a Windows user must run in Windows
PowerShell 5.1: no ``&&``, no ``||``, and no Bash-only syntax. This hook reads
the agent's final reply when a turn ends and, when a block meant for the user's
PowerShell terminal breaks that rule, shows the user one warning. It never
blocks the turn and never asks the agent to continue.

Behavior
--------
- The final reply is taken from the Stop payload's ``last_assistant_message``,
  which the Claude Code hooks reference recommends over reading the transcript.
  When that field is absent, the hook reads the tail of ``transcript_path`` and
  joins the text blocks of the last assistant message (one message can span
  several JSONL lines that share ``message.id``).
- A fenced block (``` or ~~~) is checked when its info string is ``powershell``,
  ``ps1``, ``pwsh``, or ``ps``, or when it has no info string and the host is
  Windows. Blocks labelled anything else (``bash``, ``sh``, ``text``, ...) are
  never checked. ``NEXUS_SHELL_CHECK_PLATFORM=windows|posix`` overrides the host.
- Per line, comments (``#``) are skipped and quoted strings are ignored, then
  ``&&``, ``||``, a heredoc ``<<``, a leading ``VAR=value command`` prefix, and a
  leading ``export`` are flagged. ``A; if ($?) { B }`` is the PowerShell form and
  is not flagged.
- Findings produce one JSON object on stdout with a ``systemMessage`` field,
  which Claude Code shows to the user as a warning. The message names only the
  flagged tokens and their block and line numbers, never the command text.
- Silent with exit 0 in every other case: ``stop_hook_active`` set, malformed
  stdin, no reply text, an unreadable transcript, any exception, and any
  payload that is not Claude Code's. The Stop chain is also delivered to Cursor,
  Codex, GitHub Copilot, Kimi, Gemini CLI, and Qwen Code; their advisory output
  channels differ, so the hook stays silent there rather than guess.

Runtime controls: ``NEXUS_DISABLED_HOOKS=user-command-shell-check`` or
``NEXUS_HOOK_PROFILE=minimal`` disables the hook. stdlib only; reads local files
only and makes no network call.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

HOOK_NAME = "user-command-shell-check"
MAX_STDIN_BYTES = 8 * 1024 * 1024
TRANSCRIPT_TAIL_BYTES = 512 * 1024
MAX_REPORTED = 5

POWERSHELL_LABELS = frozenset({"powershell", "ps1", "pwsh", "ps"})
# Keys only other platforms send; any of them means "not Claude Code".
FOREIGN_KEYS = ("timestamp", "turn_id", "cursor_version", "session_title", "client_type")

FENCE_RE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})\s*(?P<info>[^\s`]*)")
QUOTED_RE = re.compile(r"'[^']*'|\"(?:[^\"`]|`.)*\"")
ENV_PREFIX_RE = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*=\S*\s+\S")
EXPORT_RE = re.compile(r"^\s*export\s")

TOKEN_LABELS = {
    "&&": "`&&`",
    "||": "`||`",
    "<<": "a `<<` heredoc",
    "VAR=": "a leading `VAR=value` prefix",
    "export": "`export`",
}


# ----- switches and input ------------------------------------------------------


def hook_disabled() -> bool:
    """True when opted out via NEXUS_DISABLED_HOOKS or the minimal profile."""
    names = {n.strip() for n in os.environ.get("NEXUS_DISABLED_HOOKS", "").split(",")}
    if HOOK_NAME in names:
        return True
    return os.environ.get("NEXUS_HOOK_PROFILE", "").strip() == "minimal"


def is_windows() -> bool:
    """The platform the user's terminal runs on, with a test override."""
    override = os.environ.get("NEXUS_SHELL_CHECK_PLATFORM", "").strip().lower()
    if override in ("windows", "posix"):
        return override == "windows"
    return os.name == "nt"


def read_payload(stream: Any) -> dict[str, Any] | None:
    """Parse the hook's JSON object from ``stream``; None when it is not one."""
    raw = stream.read(MAX_STDIN_BYTES + 1)
    if not raw or len(raw) > MAX_STDIN_BYTES:
        return None
    try:
        # Bytes, not the locale code page; utf-8-sig drops the BOM that
        # Windows PowerShell 5.1 prefixes to piped stdin.
        payload = json.loads(raw.decode("utf-8-sig", "replace"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def is_claude_code(payload: dict[str, Any]) -> bool:
    """True unless the payload carries another platform's signature."""
    if any(key in payload for key in FOREIGN_KEYS):
        return False
    return not os.environ.get("QWEN_PROJECT_DIR")


# ----- final reply -------------------------------------------------------------


def _tail_lines(path: Path) -> list[str]:
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        start = max(0, size - TRANSCRIPT_TAIL_BYTES)
        handle.seek(start)
        data = handle.read()
    lines = data.decode("utf-8", "replace").splitlines()
    return lines[1:] if start > 0 else lines


def _text_blocks(message: dict[str, Any]) -> list[str]:
    content = message.get("content")
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    return [
        b["text"]
        for b in content
        if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
    ]


def reply_from_transcript(transcript_path: Any) -> str:
    """Text of the last main-thread assistant message in a Claude Code transcript."""
    if not isinstance(transcript_path, str) or not transcript_path:
        return ""
    path = Path(transcript_path)
    if not path.is_file():
        return ""
    target_id: Any = None
    parts: list[list[str]] = []
    for line in reversed(_tail_lines(path)):
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(entry, dict) or entry.get("isSidechain"):
            continue
        kind = entry.get("type")
        if kind == "user" and parts:
            break
        if kind != "assistant" or not isinstance(entry.get("message"), dict):
            continue
        message = entry["message"]
        if parts and message.get("id") != target_id:
            break
        target_id = message.get("id")
        parts.append(_text_blocks(message))
    return "\n".join(text for blocks in reversed(parts) for text in blocks)


def final_reply(payload: dict[str, Any]) -> str:
    """The final assistant text, from the payload or the transcript tail."""
    text = payload.get("last_assistant_message")
    if isinstance(text, str) and text:
        return text
    return reply_from_transcript(payload.get("transcript_path"))


# ----- checking ----------------------------------------------------------------


def fenced_blocks(text: str) -> list[tuple[str, list[str]]]:
    """(info string, lines) for every fenced block; an unclosed block runs to the end."""
    blocks: list[tuple[str, list[str]]] = []
    fence: str | None = None
    info = ""
    body: list[str] = []
    for line in text.splitlines():
        if fence is None:
            match = FENCE_RE.match(line)
            if match:
                fence, info, body = match.group("fence"), match.group("info"), []
            continue
        stripped = line.strip()
        if stripped and stripped[0] == fence[0] and set(stripped) == {fence[0]} and len(stripped) >= len(fence):
            blocks.append((info, body))
            fence = None
            continue
        body.append(line)
    if fence is not None:
        blocks.append((info, body))
    return blocks


def should_check(info: str, windows: bool) -> bool:
    label = info.strip().lower()
    if label:
        return label in POWERSHELL_LABELS
    return windows


def line_findings(line: str) -> list[str]:
    """The Bash-only tokens on one command line, in a stable order."""
    if line.lstrip().startswith("#"):
        return []
    bare = QUOTED_RE.sub("''", line)
    found = [token for token in ("&&", "||", "<<") if token in bare]
    if ENV_PREFIX_RE.match(bare):
        found.append("VAR=")
    if EXPORT_RE.match(bare):
        found.append("export")
    return found


def find_problems(text: str, windows: bool) -> list[tuple[int, int, str]]:
    """(block number, line number, token) for every flagged line, 1-based."""
    problems: list[tuple[int, int, str]] = []
    checked = 0
    for info, lines in fenced_blocks(text):
        if not should_check(info, windows):
            continue
        checked += 1
        for number, line in enumerate(lines, start=1):
            problems.extend((checked, number, token) for token in line_findings(line))
    return problems


def build_message(problems: list[tuple[int, int, str]]) -> str:
    multi_block = len({block for block, _, _ in problems}) > 1
    shown = []
    for block, number, token in problems[:MAX_REPORTED]:
        where = f"block {block}, line {number}" if multi_block else f"line {number}"
        shown.append(f"{TOKEN_LABELS[token]} ({where})")
    extra = len(problems) - len(shown)
    listing = ", ".join(shown) + (f", and {extra} more" if extra > 0 else "")
    return (
        f"Command check: a block meant for your PowerShell terminal uses {listing}, "
        "which Windows PowerShell 5.1 rejects. Ask the agent to rewrite it with one "
        "command per line."
    )


def evaluate(payload: dict[str, Any]) -> dict[str, str] | None:
    """The hook's stdout object, or None for silence."""
    if payload.get("stop_hook_active") is True or not is_claude_code(payload):
        return None
    text = final_reply(payload)
    if not text:
        return None
    problems = find_problems(text, is_windows())
    if not problems:
        return None
    return {"systemMessage": build_message(problems)}


def main() -> int:
    """Hook entry point. Always exits 0."""
    try:
        if hook_disabled():
            return 0
        payload = read_payload(sys.stdin.buffer)
        if payload is None:
            return 0
        output = evaluate(payload)
        if output is not None:
            sys.stdout.write(json.dumps(output) + "\n")
            sys.stdout.flush()
    except Exception:  # noqa: BLE001 - an advisory hook must never break the host's turn
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
