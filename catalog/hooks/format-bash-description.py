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
BORDER_CHAR = "="  # Plain ASCII - maximum compatibility across all terminals
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


# ── Shell-aware tokenizer and splitter ────────────────────────────────────

# Keywords that open/close shell block constructs
_SHELL_OPENERS = frozenset({"for", "while", "until", "if", "case", "select"})
_SHELL_CLOSERS = frozenset({"done", "fi", "esac"})
# Keywords that start the body inside a block (used by _extract_body_commands)
_BODY_STARTERS = frozenset({"do", "then"})
# Keywords that are clause separators inside if/elif/else bodies.
# They may appear as the first word of a split fragment and must be stripped
# before the remainder is treated as a command.
_CLAUSE_KEYWORDS = frozenset({"else", "elif", "then"})


def _bare_keyword(token_value: str) -> str:
    """Return the bare word if *token_value* is a simple shell keyword.

    Ignores tokens that contain path separators, variable expansions,
    or other characters that prove it is not a standalone keyword.
    """
    stripped = token_value.strip()
    if not stripped or not stripped.isalpha():
        return ""
    return stripped


def _tokenize_shell(cmd: str) -> list[tuple[str, str]]:
    """Tokenize a shell command string into (type, value) pairs.

    Token types:
      - ``'word'``  - a shell word (may include internal quotes/escapes)
      - ``'op'``    - an operator: ``&&``, ``||``, ``;;``, ``|``, ``;``
      - ``'ws'``    - whitespace (spaces, tabs, newlines)
    """
    tokens: list[tuple[str, str]] = []
    i = 0
    length = len(cmd)

    while i < length:
        ch = cmd[i]

        # ── Whitespace ──
        if ch in (" ", "\t", "\n"):
            start = i
            while i < length and cmd[i] in (" ", "\t", "\n"):
                i += 1
            tokens.append(("ws", cmd[start:i]))
            continue

        # ── Two-character operators ──
        if i + 1 < length and cmd[i : i + 2] in ("&&", "||", ";;"):
            tokens.append(("op", cmd[i : i + 2]))
            i += 2
            continue

        # ── Single-character operators ──
        if ch in ("|", ";"):
            tokens.append(("op", ch))
            i += 1
            continue

        # ── Word (may contain quotes, escapes, $(), backticks, etc.) ──
        start = i
        subshell_depth = 0  # nesting depth inside $(…) or $((…))
        in_backtick = False  # inside `…` command substitution
        while i < length:
            ch = cmd[i]
            # Only treat operators as word-boundaries when not inside a
            # command substitution - $(...) and `...` create nested shells
            # whose internal &&, ||, ; must not be treated as splits.
            if subshell_depth == 0 and not in_backtick:
                if ch in (" ", "\t", "\n", ";", "|"):
                    break
                if i + 1 < length and cmd[i : i + 2] in ("&&", "||", ";;"):
                    break
            # $( → open a command-substitution subshell
            if ch == "$" and i + 1 < length and cmd[i + 1] == "(":
                subshell_depth += 1
                i += 2
                continue
            # ( inside an existing $() deepens the nesting
            if ch == "(" and subshell_depth > 0:
                subshell_depth += 1
                i += 1
                continue
            # ) closes one level of $(…) nesting
            if ch == ")" and subshell_depth > 0:
                subshell_depth -= 1
                i += 1
                continue
            # Backtick command substitution
            if ch == "`":
                in_backtick = not in_backtick
                i += 1
                continue
            # Consume single-quoted strings
            if ch == "'":
                i += 1
                while i < length and cmd[i] != "'":
                    i += 1
                if i < length:
                    i += 1
            # Consume double-quoted strings
            elif ch == '"':
                i += 1
                while i < length:
                    if cmd[i] == "\\" and i + 1 < length:
                        i += 2
                    elif cmd[i] == '"':
                        i += 1
                        break
                    else:
                        i += 1
            elif ch == "\\" and i + 1 < length:
                i += 2
            else:
                i += 1
        tokens.append(("word", cmd[start:i]))

    return tokens


def split_compound_command(cmd: str) -> list[str]:
    """Split a command on shell operators (&&, ||, |, ;) at the top level.

    Respects single quotes, double quotes, backslash escapes, **and**
    shell control structures (``for/while/until…done``,
    ``if…then…fi``, ``case…esac``).  Operators that appear inside
    these constructs are kept as part of the enclosing block rather
    than causing a split.
    """
    tokens = _tokenize_shell(cmd)

    parts: list[str] = []
    current: list[str] = []
    depth = 0

    for tok_type, tok_value in tokens:
        if tok_type == "word":
            bare = _bare_keyword(tok_value)
            if bare in _SHELL_OPENERS:
                depth += 1
            elif bare in _SHELL_CLOSERS and depth > 0:
                depth -= 1
            current.append(tok_value)
        elif tok_type == "op" and depth == 0:
            # Top-level operator → split here
            parts.append("".join(current))
            current = []
        else:
            # Operator inside a construct, or whitespace → keep
            current.append(tok_value)

    if current:
        parts.append("".join(current))

    return [p.strip() for p in parts if p.strip()]


# ── Shell-construct body extraction ───────────────────────────────────────

def _is_shell_construct(cmd: str) -> bool:
    """Return True if *cmd* starts with a shell control keyword."""
    first = cmd.split(None, 1)[0] if cmd.strip() else ""
    return first in _SHELL_OPENERS


def _extract_body_commands(construct: str) -> list[str] | None:
    """Extract the body commands from a shell control structure.

    Supported forms:
      - ``for/while/until/select … do BODY done``
      - ``if … then BODY [elif … then BODY] [else BODY] fi``

    ``else``, ``elif``, and ``then`` may appear as the leading word of a
    split fragment because the semicolon-based splitter doesn't know about
    shell clause structure.  For example:
      ``if …; then echo yes; else echo no; fi``
    produces body fragments ``["echo yes", "else echo no"]``.
    The ``else`` prefix is stripped so the actual command ``echo no`` is
    what gets checked.  All branches (then/elif/else) are checked together.

    Returns a list of body subcommands (split at the top level within
    the body), or ``None`` if the construct cannot be parsed.
    """
    tokens = _tokenize_shell(construct)

    depth = 0
    body_start_idx: int | None = None
    body_end_idx: int | None = None

    for idx, (tok_type, tok_value) in enumerate(tokens):
        if tok_type != "word":
            continue
        bare = _bare_keyword(tok_value)
        if bare in _SHELL_OPENERS:
            depth += 1
        elif bare in _SHELL_CLOSERS:
            depth -= 1
            if depth == 0:
                body_end_idx = idx
                break
        elif bare in _BODY_STARTERS and depth == 1 and body_start_idx is None:
            body_start_idx = idx

    if body_start_idx is None or body_end_idx is None:
        return None

    # Collect everything between the body-starter and the closer
    body_text = "".join(
        v for _, v in tokens[body_start_idx + 1 : body_end_idx]
    ).strip()

    if not body_text:
        return []

    raw_cmds = split_compound_command(body_text)

    # Strip leading clause keywords (``else``, ``elif``, ``then``) from each
    # fragment.  These appear because the semicolon splitter treats them as
    # the start of a new fragment.  We strip the keyword and keep the rest
    # as the actual command to check.  Empty remainders are dropped.
    result: list[str] = []
    for c in raw_cmds:
        parts = c.split(None, 1)
        if parts and _bare_keyword(parts[0]) in _CLAUSE_KEYWORDS:
            if len(parts) == 2 and parts[1].strip():
                result.append(parts[1].strip())
            # else: bare "else" / "then" with no body -- skip
        else:
            result.append(c)
    return result


# Regex: matches a shell variable assignment prefix, e.g. "count=" or "FOO="
_VAR_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=(.*)", re.DOTALL)


def _unwrap_var_assignment(sub: str) -> list[str] | None:
    """If *sub* is a shell variable assignment, return the commands inside it.

    Returns:
      - ``None``  if *sub* is not a variable assignment.
      - ``[]``    if the assignment RHS is a plain literal (nothing to check).
      - A list of command strings to check when the RHS contains ``$(cmd)``
        and/or a trailing command (e.g. ``VAR=$(subcmd) actual_cmd``).

    Examples::

        "count=$(ls -d */)"      → ["ls -d */"]
        "FOO=bar"                → []
        "FOO=bar echo hello"     → ["echo hello"]
        "X=$(cmd) extra args"    → ["cmd", "extra args"]
    """
    m = _VAR_ASSIGN_RE.match(sub)
    if not m:
        return None

    rhs = m.group(1)

    if not rhs.startswith("$("):
        # Plain assignment: VAR=literal [trailing_cmd]
        # Anything after whitespace is a prefix-assigned command.
        parts = rhs.split(None, 1)
        if len(parts) == 2:
            # e.g. "bar echo hello" → trailing command is "echo hello"
            return [parts[1]]
        return []

    # RHS is $(inner_cmd) [trailing]
    # Walk character by character to find the matching closing paren.
    depth = 0
    close_idx = len(rhs) - 1
    for i, ch in enumerate(rhs):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                close_idx = i
                break

    inner = rhs[2:close_idx]          # strip leading $( and closing )
    trailing = rhs[close_idx + 1:].strip()

    cmds: list[str] = []
    if inner.strip():
        cmds.append(inner.strip())
    if trailing:
        cmds.append(trailing)
    return cmds


def command_is_allowed(cmd: str, patterns: list[str]) -> bool:
    """Return True if every subcommand matches at least one allow pattern.

    Shell control structures (``for…done``, ``if…fi``, etc.) are kept
    as single units by the splitter.  Their *body* commands are
    extracted and checked recursively so that, for example,
    ``for f in *.py; do wc -l "$f"; done`` is allowed when ``wc *``
    is in the allow list.

    Variable assignments of the form ``VAR=$(cmd)`` or ``VAR=val cmd`` are
    unwrapped so that the embedded command is checked rather than the raw
    assignment string.

    Note: output redirections (``cmd > file``) are not stripped before
    pattern matching, so ``ls > /tmp/out`` will match ``ls *`` and be
    auto-approved.  This is acceptable for the current threat model --
    ``git-guardrails.sh`` blocks genuinely destructive patterns.
    """
    if not patterns:
        return False

    subcommands = split_compound_command(cmd)
    if not subcommands:
        return False

    for sub in subcommands:
        if _is_shell_construct(sub):
            body_cmds = _extract_body_commands(sub)
            if body_cmds is None:
                # Cannot parse the construct → treat as not allowed
                return False
            for body_cmd in body_cmds:
                if not command_is_allowed(body_cmd, patterns):
                    return False
        else:
            unwrapped = _unwrap_var_assignment(sub)
            if unwrapped is not None:
                # Variable assignment: check any embedded commands recursively
                for inner_cmd in unwrapped:
                    if not command_is_allowed(inner_cmd, patterns):
                        return False
            elif not any(fnmatch.fnmatchcase(sub, pat) for pat in patterns):
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

    # ── Non-allowed commands: require a real description.
    #    If none is provided, exit silently so that require-description.sh
    #    sees an empty description field and blocks the call, forcing
    #    Claude to retry with a description.  Never add a placeholder. ──
    stripped = (description or "").strip()
    if stripped.startswith("#"):
        # Description already looks like a box; don't double-format
        sys.exit(0)

    if not stripped:
        # No description - let require-description.sh block it
        sys.exit(0)

    box = format_description_box(stripped)
    updated_command = box + "\n\n" + cleaned_command

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
