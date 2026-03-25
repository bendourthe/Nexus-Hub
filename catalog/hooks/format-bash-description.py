#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code: formats Bash tool descriptions
into a 79-character bordered box.

Install:
  1. Copy this file to ~/.claude/hooks/format-bash-description.py
  2. Add the PreToolUse hook config to ~/.claude/settings.json
  3. Add the CLAUDE.md instruction to write plain-text descriptions

The model writes a plain description like:
  "Show git status and diff summary for the commit"

This hook transforms the command to start with:
  # ═══════════════════════════════ Description ═══════════════════════════════ #
  # Show git status and diff summary for the commit                           #
  # ═════════════════════════════════════════════════════════════════════════════ #

Part of DevAI-Hub.
"""

from __future__ import annotations

import json
import sys
import textwrap

# ── Configuration ──────────────────────────────────────────────────────────
BOX_WIDTH = 79
BORDER_CHAR = "="  # Plain ASCII — maximum compatibility across all terminals
# Alternatives (may cause mojibake on Windows):
#   BORDER_CHAR = "\u2550"  # ═ (Box Drawings Double Horizontal)
#   BORDER_CHAR = "\u2500"  # ─ (Box Drawings Light Horizontal)
# ──────────────────────────────────────────────────────────────────────────


def format_description_box(text: str) -> str:
    """Wrap plain text into a bordered box, 79 chars wide."""
    content_width = BOX_WIDTH - 4  # subtract "# " prefix and " #" suffix

    # ── Border line ──
    border = f"# {BORDER_CHAR * content_width} #"

    # ── Title line with centered " Description " ──
    title = " Description "
    padding = content_width - len(title)
    left_pad = padding // 2
    right_pad = padding - left_pad
    title_line = (
        f"# {BORDER_CHAR * left_pad}{title}{BORDER_CHAR * right_pad} #"
    )

    # ── Word-wrap the description text ──
    wrapped = textwrap.wrap(text.strip(), width=content_width)
    if not wrapped:
        wrapped = ["(no description)"]

    # ── Pad each content line to the full content width ──
    content_lines = [f"# {line:<{content_width}} #" for line in wrapped]

    # ── Assemble ──
    return "\n".join([title_line] + content_lines + [border])


def main() -> None:
    # ── Read hook input from stdin ──
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # let the tool call proceed unchanged

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    description = tool_input.get("description", "")

    # ── Skip if no description or already formatted ──
    if not description or not description.strip():
        sys.exit(0)

    stripped = description.strip()
    if stripped.startswith("#"):
        # Description already looks like a box; don't double-format
        sys.exit(0)

    # ── Format the box ──
    box = format_description_box(stripped)

    # ── Strip any model-generated box from the command ──
    # The model may have prepended its own # comment lines; remove them
    # so we don't end up with a double box.
    lines = command.split("\n")
    cleaned_lines = []
    past_box = False
    for line in lines:
        if not past_box and line.strip().startswith("#"):
            continue  # skip model-generated box lines
        if not past_box and line.strip() == "":
            continue  # skip blank lines between box and command
        past_box = True
        cleaned_lines.append(line)
    cleaned_command = "\n".join(cleaned_lines)

    # ── Prepend the deterministic box to the cleaned command ──
    updated_command = box + "\n\n" + cleaned_command

    # ── Return updated input so Claude Code uses the formatted version ──
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {
                "command": updated_command,
                "description": stripped,
            },
        }
    }

    json.dump(output, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
