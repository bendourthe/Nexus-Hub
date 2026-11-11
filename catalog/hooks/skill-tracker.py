#!/usr/bin/env python3
"""PostToolUse hook (Skill matcher): record which skills ran this session.

Writes the invoked skill name to a small per-session state file so that
skipConditions.skillAlreadyUsed in skill-rules.json works and the activation /
guard hooks do not re-suggest a skill that is already loaded.

Advisory and fail-open: any error exits 0, it makes no outbound call, and it
records only the skill name (never the skill arguments or any secret).

Part of Nexus-Hub. See catalog/style-guides/skill-activation-rules.md.
"""

from __future__ import annotations

import sys
from typing import TextIO

# --- Nexus-Hub source label (v4.14.8) ---
# Every message this hook prints starts with the tag, so a reader can tell a
# Nexus-Hub message from a harness message. The hook name in the tag is the
# NEXUS_DISABLED_HOOKS value. Decision record:
# docs/decisions/implemented/tooling/2026-10-30-hook-messages-name-nexus-hub.md
NEXUS_TAG = "[Nexus-Hub: skill-tracker]"


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


_HOOK_NAME = "skill-tracker"

# Defensive import: if the shared helper is missing, fail open (exit 0).
try:
    from _skill_rules import hook_disabled, read_stdin_json, record_skill
except Exception:
    sys.exit(0)


def main() -> None:
    if hook_disabled(_HOOK_NAME):
        sys.exit(0)

    data = read_stdin_json()
    tool_input = data.get("tool_input") or {}
    skill = ""
    if isinstance(tool_input, dict):
        skill = str(tool_input.get("skill") or tool_input.get("name") or "")
    # Skill names are identities under the catalog's 64-character contract.
    # Refuse oversized names; truncation would make distinct skills collide.
    if len(skill) > 64:
        _nexus_msg("skill identity exceeds 64 characters; skipping.")
        sys.exit(0)
    if skill:
        record_skill(str(data.get("session_id", "")), skill)

    sys.exit(0)


if __name__ == "__main__":
    main()
