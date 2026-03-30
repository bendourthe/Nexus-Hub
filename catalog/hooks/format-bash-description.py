#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code: formats Bash tool descriptions
into a 79-character bordered box for commands that require user
approval, and passes through allowed commands unchanged so that
the permission system can auto-approve them.

Install:
  1. Copy this file to ~/.claude/hooks/format-bash-description.py
  2. Add the PreToolUse hook config to ~/.claude/settings.json
  3. Add the CLAUDE.md instruction to write plain-text descriptions

Behavior:
  - Reads allow patterns from all settings levels
  - For compound commands (&&, ||, ;), checks each subcommand
  - If ALL subcommands match an allow pattern: returns the clean
    command without the description box, so the permission matcher
    sees the real command and auto-approves it
  - If ANY subcommand is not in the allow list: prepends the
    description box so it is visible in the approval dialog

Part of DevAI-Hub.
"""

from __future__ import annotations

import fnmatch
import json
import pathlib
import re
import sys
import textwrap

# ── Configuration ──────────────────────────────────────────────────────────
BOX_WIDTH = 79
BORDER_CHAR = "="  # Plain ASCII — maximum compatibility across all terminals
# ──────────────────────────────────────────────────────────────────────────


# ── Description box formatting ─────────────────────────────────────────────

def format_description_box(text: str) -> str:
    """Wrap plain text into a bordered box, 79 chars wide."""
    content_width = BOX_WIDTH - 4  # subtract "# " prefix and " #" suffix

    border = f"# {BORDER_CHAR * content_width} #"

    title = " Description "
    padding = content_width - len(title)
    left_pad = padding // 2
    right_pad = padding - left_pad
    title_line = (
        f"# {BORDER_CHAR * left_pad}{title}{BORDER_CHAR * right_pad} #"
    )

    wrapped = textwrap.wrap(text.strip(), width=content_width)
    if not wrapped:
        wrapped = ["(no description)"]

    content_lines = [f"# {line:<{content_width}} #" for line in wrapped]

    return "\n".join([title_line] + content_lines + [border])


# ── Command cleaning ──────────────────────────────────────────────────────

def strip_description_box(command: str) -> str:
    """Remove any description-box comment lines from the top of a command."""
    lines = command.split("\n")
    cleaned_lines = []
    past_box = False
    for line in lines:
        if not past_box and line.strip().startswith("#"):
            continue
        if not past_box and line.strip() == "":
            continue
        past_box = True
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


# ── Permission matching ───────────────────────────────────────────────────

def load_allow_patterns() -> list[str]:
    """Read Bash allow patterns from all applicable settings levels.

    Checks (in merge order):
      1. ~/.claude/settings.json          (user-global)
      2. ~/.claude/settings.local.json    (user-local)
      3. <project>/.claude/settings.json  (project-shared)
      4. <project>/.claude/settings.local.json (project-local)

    Returns the inner pattern strings (e.g. "git log *" from "Bash(git log *)").
    Handles both current "Bash(cmd *)" and legacy "Bash(cmd:*)" syntax.
    """
    patterns: list[str] = []
    home = pathlib.Path.home()
    cwd = pathlib.Path.cwd()

    settings_paths: list[pathlib.Path] = [
        home / ".claude" / "settings.json",
        home / ".claude" / "settings.local.json",
    ]

    for parent in [cwd, *cwd.parents]:
        project_claude = parent / ".claude"
        if project_claude.is_dir() and parent != home:
            settings_paths.append(project_claude / "settings.json")
            settings_paths.append(project_claude / "settings.local.json")
            break

    for path in settings_paths:
        if not path.is_file():
            continue
        try:
            # Use utf-8-sig to handle BOM written by PowerShell on Windows
            raw = path.read_text(encoding="utf-8-sig")
            data = json.loads(raw)
            for entry in data.get("permissions", {}).get("allow", []):
                if not isinstance(entry, str):
                    continue
                if entry.startswith("Bash(") and entry.endswith(")"):
                    inner = entry[5:-1]
                    # Normalise legacy colon syntax: "cd:*" → "cd *"
                    inner = re.sub(r"^([^:*\s]+):\*$", r"\1 *", inner)
                    patterns.append(inner)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[format-bash-description] WARNING: failed to read {path}: {exc}", file=sys.stderr)
            continue

    return patterns


def split_compound_command(cmd: str) -> list[str]:
    """Split a command on shell operators (&&, ||, |, ;) outside quotes.

    Respects single quotes, double quotes, and backslash escapes so
    that operators inside quoted strings (e.g. grep "foo\\|bar") are
    not treated as pipe operators.
    """
    parts: list[str] = []
    current: list[str] = []
    i = 0
    in_single = False
    in_double = False

    while i < len(cmd):
        ch = cmd[i]

        if ch == "'" and not in_double:
            in_single = not in_single
            current.append(ch)
            i += 1
        elif ch == '"' and not in_single:
            in_double = not in_double
            current.append(ch)
            i += 1
        elif ch == "\\" and not in_single and i + 1 < len(cmd):
            current.append(ch)
            current.append(cmd[i + 1])
            i += 2
        elif not in_single and not in_double:
            two = cmd[i : i + 2]
            if two in ("&&", "||"):
                parts.append("".join(current))
                current = []
                i += 2
            elif ch in ("|", ";"):
                parts.append("".join(current))
                current = []
                i += 1
            else:
                current.append(ch)
                i += 1
        else:
            current.append(ch)
            i += 1

    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def command_is_allowed(cmd: str, patterns: list[str]) -> bool:
    """Return True if every subcommand matches at least one allow pattern."""
    if not patterns:
        return False

    subcommands = split_compound_command(cmd)
    if not subcommands:
        return False

    for sub in subcommands:
        if not any(fnmatch.fnmatchcase(sub, pat) for pat in patterns):
            return False
    return True


# ── Main hook logic ───────────────────────────────────────────────────────

def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    description = tool_input.get("description", "")

    # ── Strip any model-generated box to get the clean command ──
    cleaned_command = strip_description_box(command)

    # ── Check if the clean command matches configured allow patterns ──
    try:
        allow_patterns = load_allow_patterns()
        is_allowed = command_is_allowed(cleaned_command, allow_patterns)
    except Exception as exc:
        print(f"[format-bash-description] WARNING: pattern check failed: {exc}", file=sys.stderr)
        is_allowed = False

    # ── Allowed commands: return clean command (no box) and tell
    #    Claude Code to auto-approve via permissionDecision. We set
    #    this explicitly because Claude Code's own pattern matcher
    #    may mis-parse shell metacharacters inside quoted strings
    #    (e.g. grep "foo\|bar" looks like a pipe to the matcher). ──
    if is_allowed:
        stripped = (description or "").strip()
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "All subcommands match configured allow patterns",
                "updatedInput": {
                    "command": cleaned_command,
                    "description": stripped if stripped else "(auto-approved)",
                },
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    # ── Non-allowed commands: always add a description box so the
    #    user can see context in the approval dialog. ──
    stripped = (description or "").strip()
    if stripped.startswith("#"):
        # Description already looks like a box; don't double-format
        sys.exit(0)

    # Use a placeholder when the model omits a description
    display_text = stripped if stripped else "(no description provided)"

    box = format_description_box(display_text)
    updated_command = box + "\n\n" + cleaned_command

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {
                "command": updated_command,
                "description": stripped if stripped else display_text,
            },
        }
    }

    json.dump(output, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
