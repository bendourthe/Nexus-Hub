#!/usr/bin/env python3
"""Detection helper for the action-restatement-guard Stop hook (Part of Nexus-Hub).

The communication contract says that when anything waits on the user, the message
carries a ``## Action needed`` heading and restates every step or the full decision
under it, and never refers the user back to earlier text. This helper reads the Stop
payload on stdin and, when the last assistant message asks the user to act AND points
back to earlier text, prints one JSON object that blocks the stop:

    {"decision": "block", "reason": "[Nexus-Hub: action-restatement-guard] ..."}

Detection (both must hold, matched case-insensitively):

- Ask signals: "waiting on you", "waiting for you", "reply", "run these", "please run",
  "your turn", "paste", "approve", "approval", "action needed", "choose", "when you have",
  or a lettered option list (a line starting "A." or "A)" and another starting "B.").
- Back-references: "from earlier", "earlier message", "previous message", "as above",
  "listed above", "given above", "steps above", "see above", "scroll up", "as before",
  "the steps I gave", "the steps I listed", "I posted earlier", "mentioned earlier",
  "see my earlier".

Precision choices (the false-positive policy):

- Fenced code blocks and inline code spans are ignored, so a message that quotes or
  discusses a phrase (for example this rule) does not trip the guard.
- When the message already has an ``Action needed`` heading, only the text from that
  heading onward is checked for back-references, so narrative above it ("as mentioned
  earlier, the build passed") is not blocked.
- A message that asks for action but has no heading and no back-reference is allowed.
  The ask signals ("reply", "choose", "approve") are common in messages that need no
  restatement, so a missing heading alone would block too many correct messages.

The hook fails open: ``stop_hook_active`` set, malformed or oversized stdin, a payload
from another platform, a missing or unreadable transcript, and any exception all exit 0
with no output. Only the tail of a large transcript is read.

Runtime controls: ``NEXUS_DISABLED_HOOKS=action-restatement-guard`` or
``NEXUS_HOOK_PROFILE=minimal``. Standard library only; no network.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
NEXUS_TAG = "[Nexus-Hub: action-restatement-guard]"
HOOK_NAME = "action-restatement-guard"
MAX_STDIN_BYTES = 8 * 1024 * 1024
TRANSCRIPT_TAIL_BYTES = 512 * 1024
# Keys only other platforms send; any of them means "not Claude Code".
FOREIGN_KEYS = (
    "timestamp",
    "turn_id",
    "cursor_version",
    "session_title",
    "client_type",
)

ASK_RE = re.compile(
    r"waiting\s+(?:on|for)\s+you|\breply\b|run\s+these|please\s+run|your\s+turn|\bpaste\b"
    r"|\bapprove\b|\bapproval\b|action\s+needed|\bchoose\b|when\s+you\s+have",
    re.IGNORECASE,
)
LETTERED_A_RE = re.compile(r"^\s*(?:[-*]\s*)?\(?\*{0,2}A\*{0,2}[.)]\s", re.MULTILINE)
LETTERED_B_RE = re.compile(r"^\s*(?:[-*]\s*)?\(?\*{0,2}B\*{0,2}[.)]\s", re.MULTILINE)
BACKREF_RE = re.compile(
    r"\bfrom\s+earlier\b|\bearlier\s+message\b|\bprevious\s+message\b|\bas\s+above\b"
    r"|\blisted\s+above\b|\bgiven\s+above\b|\bsteps\s+above\b|\bsee\s+above\b"
    r"|\bscroll\s+up\b|\bas\s+before\b|\bthe\s+steps\s+i\s+(?:gave|listed)\b"
    r"|\bi\s+posted\s+earlier\b|\bmentioned\s+earlier\b|\bsee\s+my\s+earlier\b",
    re.IGNORECASE,
)
HEADING_RE = re.compile(
    r"^\s{0,3}#{1,6}\s*action\s+needed\b", re.IGNORECASE | re.MULTILINE
)
FENCE_RE = re.compile(
    r"^ {0,3}(`{3,}|~{3,}).*?^ {0,3}\1[`~]*[ \t]*$", re.DOTALL | re.MULTILINE
)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

REASON = (
    "Your final message asks the user to act and points back to earlier text ({phrase!r}). "
    "The user must not have to scroll a long session to find what to do. Rewrite the final "
    "message with a `## Action needed` heading that restates every step in full (where to "
    "run it, the exact command, the expected output) or the full decision with its lettered "
    "options and your recommendation, and do not refer to earlier messages."
)


def hook_disabled() -> bool:
    """True when opted out via NEXUS_DISABLED_HOOKS or the minimal profile."""
    names = {n.strip() for n in os.environ.get("NEXUS_DISABLED_HOOKS", "").split(",")}
    if HOOK_NAME in names:
        return True
    return os.environ.get("NEXUS_HOOK_PROFILE", "").strip() == "minimal"


def read_payload(stream: Any) -> dict[str, Any] | None:
    """Parse the hook's JSON object from ``stream``; None when it is not one."""
    raw = stream.read(MAX_STDIN_BYTES + 1)
    if not raw or len(raw) > MAX_STDIN_BYTES:
        return None
    try:
        # utf-8-sig drops the BOM that Windows PowerShell 5.1 can prefix to piped stdin.
        payload = json.loads(raw.decode("utf-8-sig", "replace"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def is_claude_code(payload: dict[str, Any]) -> bool:
    """True unless the payload carries another platform's signature."""
    if any(key in payload for key in FOREIGN_KEYS):
        return False
    return not os.environ.get("QWEN_PROJECT_DIR")


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
        if isinstance(b, dict)
        and b.get("type") == "text"
        and isinstance(b.get("text"), str)
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


def _strip_code(text: str) -> str:
    return INLINE_CODE_RE.sub(" ", FENCE_RE.sub(" ", text))


def asks_user_to_act(text: str) -> bool:
    """True when the text carries an ask signal or a lettered A/B option list."""
    if ASK_RE.search(text):
        return True
    return bool(LETTERED_A_RE.search(text) and LETTERED_B_RE.search(text))


def find_backreference(text: str) -> str | None:
    """The first back-reference phrase that counts, or None.

    With an ``Action needed`` heading present, only the text from the heading on counts.
    """
    prose = _strip_code(text)
    heading = HEADING_RE.search(prose)
    scope = prose[heading.start() :] if heading else prose
    match = BACKREF_RE.search(scope)
    return match.group(0).lower() if match else None


def evaluate(payload: dict[str, Any]) -> str | None:
    """The block reason for this Stop payload, or None to allow."""
    if payload.get("stop_hook_active") or not is_claude_code(payload):
        return None
    reply = final_reply(payload)
    if not reply:
        return None
    prose = _strip_code(reply)
    if not asks_user_to_act(prose):
        return None
    phrase = find_backreference(reply)
    if phrase is None:
        return None
    return f"{NEXUS_TAG} {REASON.format(phrase=phrase)}"


def main() -> int:
    try:
        if hook_disabled():
            return 0
        payload = read_payload(sys.stdin.buffer)
        reason = evaluate(payload) if payload is not None else None
        if reason:
            sys.stdout.write(json.dumps({"decision": "block", "reason": reason}) + "\n")
    except Exception:  # noqa: BLE001 - a Stop guard must never fail the turn
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
