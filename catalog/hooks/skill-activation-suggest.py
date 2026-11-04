#!/usr/bin/env python3
"""UserPromptSubmit hook: deterministic skill-activation backstop.

Reads skill-rules.json and, when the submitted prompt matches a rule's
promptTriggers, prints a one-line suggestion naming the skill(s) to load. This is
a DETERMINISTIC BACKSTOP to the model-judgment description triggering, aimed at
the under-triggering the AGENTS.md description-style section acknowledges - not a
replacement for it.

Advisory and non-blocking: it always exits 0, is a no-op when the rules file is
absent, and honors NEXUS_DISABLED_HOOKS / NEXUS_HOOK_PROFILE=minimal. It never
blocks a prompt, makes no outbound call, and never reads or logs secrets.

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
NEXUS_TAG = "[Nexus-Hub: skill-activation-suggest]"


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


_HOOK_NAME = "skill-activation-suggest"

# Defensive import: if the shared helper is missing, fail open (exit 0) rather
# than crash, preserving the advisory-only guarantee.
try:
    from _skill_rules import (
        hook_disabled,
        load_rules,
        prompt_matches,
        read_stdin_json,
        rule_skipped_by_env,
        rule_skipped_by_session,
        used_skills,
    )
except Exception:
    sys.exit(0)


def main() -> None:
    if hook_disabled(_HOOK_NAME):
        sys.exit(0)

    data = read_stdin_json()
    prompt = str(data.get("prompt", "") or "")
    if not prompt.strip():
        sys.exit(0)

    rules = load_rules()
    if not rules:
        sys.exit(0)

    used = used_skills(str(data.get("session_id", "")))
    suggestions: list[str] = []
    seen: set[str] = set()
    for rule in rules:
        skill = str(rule.get("skill", ""))
        if not skill or skill in seen:
            continue
        if rule_skipped_by_env(rule) or rule_skipped_by_session(rule, used):
            continue
        if prompt_matches(rule, prompt):
            message = str(rule.get("message") or f"Consider loading the {skill} skill.")
            suggestions.append(f"- {skill}: {message}")
            seen.add(skill)

    if suggestions:
        # For UserPromptSubmit, stdout is added to the agent's context, so this
        # nudges the agent to load the matched skill(s). Non-blocking, exit 0.
        _nexus_msg(
            "Relevant Nexus-Hub skills for this prompt:",
            *(_nexus_esc(line) for line in suggestions),
            stream=sys.stdout,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
