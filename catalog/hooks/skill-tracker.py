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
    if skill:
        record_skill(str(data.get("session_id", "")), skill)

    sys.exit(0)


if __name__ == "__main__":
    main()
