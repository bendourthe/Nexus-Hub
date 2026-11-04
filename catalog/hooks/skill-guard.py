#!/usr/bin/env python3
"""PreToolUse hook (Edit|MultiEdit|Write): deterministic skill-activation guard.

Reads skill-rules.json and, when the edited file path matches a rule's
fileTriggers, SUGGESTS the skill by default (advisory, exit 0). It blocks the
edit ONLY when NEXUS_SKILL_GUARD_BLOCK=1 AND the matched rule's enforcement is
"block" AND the rule's skipConditions are not met - inverting the fail-closed
default of the pattern it adapts to Nexus-Hub's fail-open, suggest-by-default
posture.

Fail-open: any parse error, a missing rules file, or any exception exits 0. It is
a no-op when the rules file is absent, honors NEXUS_DISABLED_HOOKS /
NEXUS_HOOK_PROFILE=minimal, makes no outbound call, and never logs the edited
content (only the file path and the rule message).

Part of Nexus-Hub. See catalog/style-guides/skill-activation-rules.md.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, TextIO

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
NEXUS_TAG = "[Nexus-Hub: skill-guard]"


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


_HOOK_NAME = "skill-guard"

# Defensive import: if the shared helper is missing, fail open (exit 0).
try:
    from _skill_rules import (
        hook_disabled,
        load_rules,
        path_matches,
        read_stdin_json,
        rule_skipped_by_env,
        rule_skipped_by_session,
        used_skills,
    )
except Exception:
    sys.exit(0)


def _block_mode() -> bool:
    """True only when NEXUS_SKILL_GUARD_BLOCK opts in explicitly."""
    return os.environ.get("NEXUS_SKILL_GUARD_BLOCK", "").strip() not in ("", "0", "false", "False")


def _edited_content(tool_input: dict[str, Any]) -> str:
    """Concatenate the new content across Write.content, Edit.new_string, MultiEdit.edits[]."""
    parts: list[str] = []
    if isinstance(tool_input.get("content"), str):
        parts.append(tool_input["content"])
    if isinstance(tool_input.get("new_string"), str):
        parts.append(tool_input["new_string"])
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict) and isinstance(edit.get("new_string"), str):
                parts.append(edit["new_string"])
    return "\n".join(parts)


def main() -> None:
    if hook_disabled(_HOOK_NAME):
        sys.exit(0)

    data = read_stdin_json()
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)
    file_path = str(tool_input.get("file_path") or tool_input.get("path") or "")
    if not file_path:
        sys.exit(0)

    rules = load_rules()
    if not rules:
        sys.exit(0)

    content = _edited_content(tool_input)
    used = used_skills(str(data.get("session_id", "")))

    matched: list[dict[str, Any]] = []
    for rule in rules:
        if not str(rule.get("skill", "")):
            continue
        if rule_skipped_by_env(rule) or rule_skipped_by_session(rule, used):
            continue
        if path_matches(rule, file_path, content):
            matched.append(rule)

    if not matched:
        sys.exit(0)

    # Block ONLY when explicitly opted in AND a matched rule is enforcement=block.
    if _block_mode():
        blockers = [r for r in matched if str(r.get("enforcement")) == "block"]
        if blockers:
            reasons = "; ".join(
                f"{r.get('skill')}: {r.get('message') or 'load this skill first'}" for r in blockers
            )
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": _nexus_tagged(f"blocked (NEXUS_SKILL_GUARD_BLOCK=1): {reasons}"),
                }
            }
            json.dump(output, sys.stdout)
            sys.exit(0)

    # Default path: advisory suggestion to stderr, never blocks.
    for rule in matched:
        message = rule.get("message") or "consider loading this skill"
        _nexus_msg(f"{_nexus_esc(str(rule.get('skill')))}: {_nexus_esc(str(message))}")
    sys.exit(0)


if __name__ == "__main__":
    main()
