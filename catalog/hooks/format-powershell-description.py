#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code: formats PowerShell tool descriptions
into a fixed-header/footer comment block for commands that require
user approval, and passes through allowed read-only commands unchanged
so that the permission system can auto-approve them.

Install:
  1. Copy this file to ~/.claude/hooks/format-powershell-description.py
  2. Add the PreToolUse hook config to ~/.claude/settings.json with
     matcher "PowerShell"
  3. Add the CLAUDE.md instruction to write plain-text descriptions

Behavior:
  - Reads PowerShell allow patterns from all settings levels
  - Auto-approve is intentionally conservative for PowerShell because
    the language allows arbitrary code execution through several
    surfaces that look identical to read-only filtering at the regex
    level (script blocks, subexpressions, the call operator, etc.).
  - A command is auto-approved only when ALL of these hold:
      * single line (no newlines)
      * contains no script block characters ({ })
      * contains no statement separator (;)
      * contains no I/O redirection (> < or backtick line continuation)
      * contains no subexpression ($(...) or @(...)) or call operator (&)
      * each pipe-separated segment matches a configured allow pattern
  - If ANY check fails, the description is rendered as a comment box
    at the top of the command so it stays visible in the truncated
    approval-dialog preview, and the call is NOT auto-approved.

Part of DevAI-Hub.
"""

from __future__ import annotations

import fnmatch
import json
import pathlib
import re
import shutil
import sys
import textwrap

# Configuration
_BOX_HEADER = "# ===== Description ===== #"
_BOX_FOOTER = "# ======================= #"
_MIN_CONTENT_WIDTH = 30
_MAX_CONTENT_WIDTH = 77

_PERMISSION_PREFIX = "PowerShell("


# Description box formatting

def format_description_box(text: str, *, width: int | None = None) -> str:
    """Format description text between fixed header/footer rules.

    Header and footer are fixed-width so they fit any terminal. Content
    lines carry a '# ' prefix and wrap at *width* (defaults to terminal
    width clamped to [_MIN_CONTENT_WIDTH, _MAX_CONTENT_WIDTH]). Pass
    *width* explicitly to override terminal detection (useful in tests).
    """
    if width is None:
        cols = shutil.get_terminal_size(fallback=(_MAX_CONTENT_WIDTH + 2, 24)).columns
        width = max(_MIN_CONTENT_WIDTH, min(_MAX_CONTENT_WIDTH, cols - 2))

    wrapped = textwrap.wrap(text.strip(), width=width)
    if not wrapped:
        wrapped = ["(no description)"]

    content_lines = [f"# {line}" for line in wrapped]
    return "\n".join([_BOX_HEADER] + content_lines + [_BOX_FOOTER])


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


# Permission matching

def load_allow_patterns() -> list[str]:
    """Read PowerShell allow patterns from all applicable settings levels.

    Checks (in merge order):
      1. ~/.claude/settings.json
      2. ~/.claude/settings.local.json
      3. <project>/.claude/settings.json
      4. <project>/.claude/settings.local.json

    Returns the inner pattern strings (e.g. "Get-Process *" from
    "PowerShell(Get-Process *)"). Handles both current "Cmd *" and
    legacy "Cmd:*" syntax.
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
            # utf-8-sig strips a BOM written by PowerShell on Windows
            raw = path.read_text(encoding="utf-8-sig")
            data = json.loads(raw)
            for entry in data.get("permissions", {}).get("allow", []):
                if not isinstance(entry, str):
                    continue
                if entry.startswith(_PERMISSION_PREFIX) and entry.endswith(")"):
                    inner = entry[len(_PERMISSION_PREFIX):-1]
                    inner = re.sub(r"^([^:*\s]+):\*$", r"\1 *", inner)
                    patterns.append(inner)
        except (json.JSONDecodeError, OSError) as exc:
            print(
                f"[format-powershell-description] WARNING: failed to read {path}: {exc}",
                file=sys.stderr,
            )
            continue

    return patterns


# Quote-aware scanning

def _has_disallowed_syntax(cmd: str) -> bool:
    """Return True if *cmd* contains any character or operator that could
    enable arbitrary code execution outside the simple-pipeline shape we
    can reason about safely.

    Quote handling follows PowerShell semantics, not bash:

    * Single-quoted strings are fully literal -- nothing inside is scanned.
    * Double-quoted strings interpolate ``$var`` and ``$(...)`` and use
      backtick (`` ` ``) as the escape character. We therefore continue
      scanning inside double quotes for ``$(`` (executes a subexpression)
      and for any backtick (could escape parsing in obfuscated ways).
      ``;`` ``{`` ``>`` ``<`` ``&`` are all literal inside double quotes
      and are not flagged there.

    Outside any quoted string the scanner flags: ``;`` ``{`` ``}`` ``>``
    ``<`` `` ` ``, ``$(`` ``@(`` ``@{``, and bare ``&`` (the call
    operator). PS5.1 has no ``&&`` so a bare ``&`` is always the call
    operator.
    """
    in_single = False
    in_double = False
    i = 0
    n = len(cmd)
    while i < n:
        ch = cmd[i]

        if in_single:
            if ch == "'":
                in_single = False
            i += 1
            continue

        if in_double:
            if ch == '"':
                in_double = False
                i += 1
                continue
            # Backtick inside "" is the escape character. Any use of it is
            # treated as suspicious because it can obfuscate parsing.
            if ch == "`":
                return True
            # $(...) is a subexpression that executes inside double quotes
            if ch == "$" and i + 1 < n and cmd[i + 1] == "(":
                return True
            i += 1
            continue

        if ch == "'":
            in_single = True
            i += 1
            continue
        if ch == '"':
            in_double = True
            i += 1
            continue

        # Bare disallowed characters
        if ch in (";", "{", "}", ">", "<", "`"):
            return True

        # Subexpression: $( ... ) or @( ... ) or @{ ... }
        if ch in ("$", "@") and i + 1 < n and cmd[i + 1] in ("(", "{"):
            return True

        # Call operator: bare & not part of && (PS5.1 has no &&)
        if ch == "&":
            return True

        i += 1
    return False


def split_powershell_pipeline(cmd: str) -> list[str]:
    """Split *cmd* on top-level ``|`` operators, respecting quotes.

    PowerShell 7's ``||`` pipeline-chain operator is also treated as a
    split boundary so a script using ``cmd1 || cmd2`` is checked as two
    separate subcommands. Empty fragments are dropped.
    """
    parts: list[str] = []
    current: list[str] = []
    in_single = False
    in_double = False
    i = 0
    n = len(cmd)
    while i < n:
        ch = cmd[i]

        if in_single:
            current.append(ch)
            if ch == "'":
                in_single = False
            i += 1
            continue

        if in_double:
            current.append(ch)
            if ch == "`" and i + 1 < n:
                current.append(cmd[i + 1])
                i += 2
                continue
            if ch == '"':
                in_double = False
            i += 1
            continue

        if ch == "'":
            in_single = True
            current.append(ch)
            i += 1
            continue
        if ch == '"':
            in_double = True
            current.append(ch)
            i += 1
            continue

        if ch == "|":
            parts.append("".join(current).strip())
            current = []
            i += 1
            # Coalesce a second | (PS7 ||) into the same split point
            if i < n and cmd[i] == "|":
                i += 1
            continue

        current.append(ch)
        i += 1

    if current:
        parts.append("".join(current).strip())

    return [p for p in parts if p]


def command_is_allowed(cmd: str, patterns: list[str]) -> bool:
    """Return True if every pipeline segment of *cmd* matches at least
    one allow pattern, AND *cmd* is structurally simple enough to
    auto-approve (single line, no script blocks, no redirection, no
    subexpressions, no call operator).
    """
    if not patterns:
        return False
    if "\n" in cmd:
        return False
    if _has_disallowed_syntax(cmd):
        return False

    subcommands = split_powershell_pipeline(cmd)
    if not subcommands:
        return False

    for sub in subcommands:
        if not any(fnmatch.fnmatchcase(sub, pat) for pat in patterns):
            return False
    return True


# Main hook logic

def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    description = tool_input.get("description", "")

    cleaned_command = strip_description_box(command)

    try:
        allow_patterns = load_allow_patterns()
        is_allowed = command_is_allowed(cleaned_command, allow_patterns)
    except Exception as exc:
        print(
            f"[format-powershell-description] WARNING: pattern check failed: {exc}",
            file=sys.stderr,
        )
        is_allowed = False

    # Allowed: ask Claude Code to auto-approve and pass the clean
    # command (without a comment box) so the permission matcher sees
    # the real command.
    if is_allowed:
        stripped = (description or "").strip()
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "All pipeline segments match configured allow patterns",
                "updatedInput": {
                    "command": cleaned_command,
                    "description": stripped if stripped else "(auto-approved)",
                },
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    # Not allowed: render description as a comment box on top of the
    # command AND surface it in permissionDecisionReason so it shows
    # directly under the dialog header instead of being hidden in
    # the collapsible "Details" panel.
    #
    # Why "ask" is required for the PowerShell tool: Claude Code's
    # PowerShell tool defaults to running a tool_use as soon as a
    # PreToolUse hook returns success without an explicit
    # permissionDecision. Bash falls through to a default-ask path
    # when no hook or rule grants permission, but PowerShell does not
    # (verified empirically against Claude Code 2.1.x by replaying
    # session transcripts). If we omit "ask" here, every PowerShell
    # tool_use that this hook does not auto-approve would still execute
    # silently because the absence of a decision is treated as approval.
    #
    # Why permissionDecisionReason carries the description: Claude
    # Code's PowerShell approval dialog hides the body of updatedInput
    # behind a collapsed "Details" panel, unlike the Bash dialog which
    # renders the comment-box prepend visibly. Putting the description
    # into permissionDecisionReason surfaces it under the dialog header
    # so the user sees it without expanding Details.
    stripped = (description or "").strip()
    if stripped.startswith("#"):
        # Description already looks like a box; pass through unchanged
        # but still force user approval.
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": stripped.lstrip("#").strip()
                or "PowerShell command not in auto-approve allow-list",
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    if not stripped:
        # No description provided. require-powershell-description.sh
        # (which runs after this hook) will block with exit 2 and
        # surface a clear error to the model. Exit silently here so we
        # don't double-emit user-visible output.
        sys.exit(0)

    box = format_description_box(stripped)
    updated_command = box + "\n\n" + cleaned_command

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": stripped,
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
