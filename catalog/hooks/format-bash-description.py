#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code: formats Bash tool descriptions
into a single-line `# Description:` prefix for commands that require user
approval, and passes through allowed commands unchanged so that the
permission system can auto-approve them.

Install:
  1. Copy this file to ~/.claude/hooks/format-bash-description.py
  2. Add the PreToolUse hook config to ~/.claude/settings.json
  3. Add the CLAUDE.md instruction to write plain-text descriptions

Behavior:
  - Reads allow patterns from all settings levels
  - For compound commands (&&, ||, ;), checks each subcommand
  - If ALL subcommands match an allow pattern: returns the clean
    command without the description prefix, so the permission matcher
    sees the real command and auto-approves it
  - If ANY subcommand is not in the allow list: prepends a single-line
    `# Description: <text>` so the description stays readable across every
    approval-dialog surface (Claude Desktop, VS Code extension, terminal).
    The same text is mirrored to `updatedInput.description` so surfaces
    that render the description field as a dialog subtitle always have
    a clean copy, regardless of how they render the command body.

Part of DevAI-Hub.
"""

from __future__ import annotations

import fnmatch
import json
import pathlib
import re
import sys

# ── Configuration ──────────────────────────────────────────────────────────
_PREFIX_MAX_LEN = 120   # max chars in the inline `# Description:` prefix
# ──────────────────────────────────────────────────────────────────────────


# ── Description prefix formatting ─────────────────────────────────────────

def _collapse_to_single_line(text: str) -> str:
    """Collapse newlines, tabs, and runs of whitespace into single spaces."""
    return re.sub(r"\s+", " ", text).strip()


def format_description_prefix(text: str) -> str:
    """Format description text into a single-line `# Description:` comment.

    The prefix is one line so it renders cleanly on every approval-dialog
    surface, including those that show the tool input as raw JSON (where
    embedded ``\\n`` characters would otherwise appear as literal escape
    sequences). Input newlines, tabs, and whitespace runs collapse to
    single spaces; the result is truncated to ``_PREFIX_MAX_LEN`` with a
    trailing ``...`` when it exceeds that length.
    """
    cleaned = _collapse_to_single_line(text)
    if not cleaned:
        return "# Description: (none provided)"
    if len(cleaned) > _PREFIX_MAX_LEN:
        cleaned = cleaned[: _PREFIX_MAX_LEN - 3].rstrip() + "..."
    return f"# Description: {cleaned}"


# One-release-cycle alias for any external caller that imported the
# previous name. Removed in the next minor release.
format_description_box = format_description_prefix


# ── Command cleaning ──────────────────────────────────────────────────────

def strip_description_box(command: str) -> str:
    """Remove description comment lines from the top of a command.

    Drops every leading ``#``-prefixed line, every leading underscore-only
    separator line (e.g. ``___``), and any blank lines between them. This
    absorbs every shape the hook has shipped so far: the legacy four-line
    ``# ===== Description =====`` box, the intermediate ``# desc: <text>``
    prefix, the ``# Description: <text>\\n___\\n<command>`` shape, and
    the current ``# Description: <text>\\n# ___\\n<command>`` shape with
    the divider commented out. A hook running mid-conversation on a
    command formatted with any prior shape still strips cleanly so the
    new prefix can be re-applied without doubling up.
    """
    lines = command.split("\n")
    cleaned_lines = []
    past_box = False
    for line in lines:
        if past_box:
            cleaned_lines.append(line)
            continue
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if stripped == "":
            continue
        if set(stripped) == {"_"}:
            # Underscore-only separator line (the ``___`` divider)
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


# ── Output-redirect detection ─────────────────────────────────────────────

# Agent-internal directories where writes are safe to auto-approve.
# These are the agent's own workspace, not user source code.
# Patterns use forward slashes and match as substrings, covering all platforms:
#   Linux:       /home/user/.claude/plans/file.md
#   macOS:       /Users/user/.claude/plans/file.md
#   Windows:     /c/Users/user/.claude/plans/file.md
#   Relative:    .claude/plans/file.md
_AGENT_INTERNAL_DIRS = (
    # Claude Code
    "/.claude/plans/",
    "/.claude/memory/",
    "/.claude/projects/",
    # Gemini CLI
    "/.gemini/memory/",
    "/.gemini/projects/",
    # OpenAI Codex
    "/.codex/memory/",
    "/.codex/projects/",
)


def _is_agent_internal_write(cmd: str) -> bool:
    """Return True if the redirect target is inside an agent-internal directory.

    Handles all platform path variants by normalizing backslashes to forward
    slashes and checking for known agent directory substrings.  Also handles
    relative paths like ``.claude/plans/file.md``.
    """
    tokens = _tokenize_shell(cmd)
    words = [v for t, v in tokens if t == "word"]

    for i, word in enumerate(words):
        if not word.startswith(">"):
            continue
        # Redirect found — extract the target path.
        # Forms: ">file", "> file" (next word), ">>file", ">> file"
        target = word.lstrip(">").strip()
        if not target and i + 1 < len(words):
            target = words[i + 1]
        if not target:
            continue

        # Normalize: backslashes to forward slashes, strip quotes
        normalized = target.replace("\\", "/").strip("'\"")

        # Check absolute agent-internal dirs
        for agent_dir in _AGENT_INTERNAL_DIRS:
            if agent_dir in normalized:
                return True

        # Check relative .claude/, .gemini/, .codex/ project-level dirs
        if normalized.startswith(".claude/") or normalized.startswith(".gemini/") or normalized.startswith(".codex/"):
            # Only allow writes to plans/, memory/, projects/ subdirs
            for agent_dir in _AGENT_INTERNAL_DIRS:
                # Extract the relative portion: ".claude/plans/" from "/.claude/plans/"
                rel_dir = agent_dir.lstrip("/")
                if normalized.startswith(rel_dir):
                    return True

    return False


def _has_output_redirect(cmd: str) -> bool:
    """Return True if *cmd* contains a top-level unquoted output redirect.

    Detects ``>``, ``>>``, and ``>file`` (no-space) token forms so that
    commands like ``cat > out.txt`` or ``echo text >> log`` are not
    auto-approved.  Input redirects (``<``, ``<<``) are intentionally
    ignored because they do not write to the filesystem.
    """
    tokens = _tokenize_shell(cmd)
    for tok_type, tok_value in tokens:
        if tok_type == "word" and tok_value.startswith(">"):
            return True
    return False


# ── bash/sh -c script extraction ─────────────────────────────────────────

def _find_bash_c_script(cmd: str) -> str | None:
    """Detect ``bash -c SCRIPT`` or ``sh -c SCRIPT`` anywhere in *cmd*.

    Handles invocations like ``xargs -I {} bash -c '...'`` where ``bash``
    is not the first word.  Returns the inner script string with outer
    single- or double-quotes stripped, or ``None`` if no match.
    """
    tokens = _tokenize_shell(cmd)
    words = [v for t, v in tokens if t == "word"]
    for i, word in enumerate(words):
        if word not in ("bash", "sh"):
            continue
        if i + 1 >= len(words) or words[i + 1] != "-c":
            continue
        if i + 2 >= len(words):
            continue
        arg = words[i + 2]
        if len(arg) >= 2 and arg[0] == arg[-1] and arg[0] in ("'", '"'):
            return arg[1:-1]
        return arg  # unquoted argument (rare but valid)
    return None


# ── Command normalization helpers ────────────────────────────────────────

# Git global options that consume one following argument
_GIT_GLOBAL_ARG_OPTS = frozenset({"-C", "-c", "--git-dir", "--work-tree",
                                   "--namespace", "--config-env"})
# Git global flags (no following argument consumed)
_GIT_GLOBAL_FLAGS = frozenset({"--no-pager", "--no-replace-objects", "--bare",
                                "--literal-pathspecs", "--glob-pathspecs",
                                "--noglob-pathspecs", "--icase-pathspecs",
                                "--no-optional-locks", "--no-lazy-fetch",
                                "--paginate", "-p"})


def _normalize_git_command(sub: str) -> str | None:
    """Strip git global options so pattern matching sees the subcommand.

    ``git -C /repo --no-pager log -5`` becomes ``git log -5`` for
    matching purposes.  Returns ``None`` if the command does not start
    with ``git`` or no global options were found (no normalization needed).
    """
    tokens = _tokenize_shell(sub)
    words = [(i, v) for i, (t, v) in enumerate(tokens) if t == "word"]
    if not words or words[0][1] != "git":
        return None

    drop_indices: set[int] = set()
    j = 1  # start after "git"
    while j < len(words):
        _, word = words[j]
        bare = word.split("=", 1)[0]  # handle --git-dir=/path

        if bare in _GIT_GLOBAL_ARG_OPTS:
            drop_indices.add(words[j][0])
            if "=" not in word and j + 1 < len(words):
                # Consumes the next word as argument
                drop_indices.add(words[j + 1][0])
                j += 2
            else:
                j += 1
        elif word in _GIT_GLOBAL_FLAGS:
            drop_indices.add(words[j][0])
            j += 1
        else:
            break  # reached the actual subcommand
        j = min(j, len(words))

    if not drop_indices:
        return None

    # Rebuild, skipping dropped tokens and collapsing adjacent whitespace.
    # Critically, dropping a token must NOT reset the whitespace tracker,
    # otherwise ``git [ws] -C [ws] /repo [ws] log`` collapses to
    # ``git   log`` instead of ``git log``.
    parts: list[str] = []
    prev_was_ws = False
    for idx, (tok_type, tok_value) in enumerate(tokens):
        if idx in drop_indices:
            continue  # keep prev_was_ws unchanged
        if tok_type == "ws":
            if prev_was_ws:
                continue
            prev_was_ws = True
        else:
            prev_was_ws = False
        parts.append(tok_value)
    return "".join(parts).strip()


def _strip_binary_path(sub: str) -> str | None:
    """Strip an absolute directory prefix from the command binary.

    ``/usr/bin/head -20 file.txt`` becomes ``head -20 file.txt``.
    Returns ``None`` if no absolute path prefix was found.
    """
    if not sub.startswith("/"):
        return None
    # Split on first whitespace to get the binary path
    parts = sub.split(None, 1)
    binary = parts[0]
    # Verify it looks like a path to a binary (not just "/")
    if "/" not in binary[1:]:
        return None
    basename = binary.rsplit("/", 1)[-1]
    if not basename:
        return None
    rest = parts[1] if len(parts) > 1 else ""
    return f"{basename} {rest}".strip() if rest else basename


# Known read-only prefix commands that don't change the safety profile
_PREFIX_COMMANDS = frozenset({"time", "command", "builtin", "exec"})
# Prefix commands that consume optional flags before the inner command
_PREFIX_WITH_FLAGS = {
    "nice": {"-n"},     # nice -n 19 cmd
    "timeout": set(),   # timeout 30 cmd  (first arg is always the duration)
}


def _unwrap_prefix_command(sub: str) -> str | None:
    """Strip known read-only prefix commands.

    ``env TERM=dumb git diff`` becomes ``git diff``.
    ``time git log`` becomes ``git log``.
    ``nice -n 19 find .`` becomes ``find .``.
    Returns ``None`` if no prefix was stripped.
    """
    tokens = _tokenize_shell(sub)
    words = [(i, v) for i, (t, v) in enumerate(tokens) if t == "word"]
    if not words:
        return None

    first = words[0][1]

    # env [VAR=val...] [flags...] command
    if first == "env":
        j = 1
        while j < len(words):
            w = words[j][1]
            # Skip env flags like -i, -u, -0, --
            if w.startswith("-"):
                j += 1
                # -u requires an argument
                if w == "-u" and j < len(words):
                    j += 1
                continue
            # Skip VAR=value assignments
            if "=" in w and not w.startswith("="):
                j += 1
                continue
            break
        if j >= len(words):
            return None
        # Rebuild from the inner command onward
        start_tok_idx = words[j][0]
        return "".join(v for _, v in tokens[start_tok_idx:]).strip() or None

    # Simple prefix commands: time, command, builtin, exec
    if first in _PREFIX_COMMANDS:
        if len(words) < 2:
            return None
        start_tok_idx = words[1][0]
        return "".join(v for _, v in tokens[start_tok_idx:]).strip() or None

    # nice -n N command
    if first == "nice":
        j = 1
        while j < len(words) and words[j][1].startswith("-"):
            w = words[j][1]
            j += 1
            if w == "-n" and j < len(words):
                j += 1  # skip the priority number
        if j >= len(words):
            return None
        start_tok_idx = words[j][0]
        return "".join(v for _, v in tokens[start_tok_idx:]).strip() or None

    return None


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

    The matching pipeline applies these steps in order for each subcommand:

    1. **Shell constructs** (``for...done``, ``if...fi``) and
       **subshells** ``(...)`` / **brace groups** ``{ ...; }``: body
       commands are extracted and checked recursively.
    2. **Output redirects** (``>``, ``>>``): always blocked.
    3. **Variable assignments** (``VAR=$(cmd)``): inner commands checked.
    4. **Direct pattern match** via ``fnmatch``.
    5. **Git global option normalization**: ``git -C /repo log`` is
       matched as ``git log``.
    6. **Absolute binary path stripping**: ``/usr/bin/head`` is matched
       as ``head``.
    7. **Prefix command unwrapping**: ``env``, ``time``, ``command``,
       ``nice`` wrappers are stripped and the inner command is checked.
    8. **bash/sh -c extraction**: inner script is checked recursively.
    """
    if not patterns:
        return False

    # Subshells (...) and brace groups { ...; } must be detected before
    # splitting because the tokenizer doesn't treat ( ) as block
    # delimiters, so split_compound_command would break them apart.
    trimmed = cmd.strip()
    if trimmed.startswith("(") and trimmed.endswith(")"):
        return command_is_allowed(trimmed[1:-1].strip(), patterns)
    if trimmed.startswith("{") and trimmed.endswith("}"):
        inner = trimmed[1:-1].strip().rstrip(";").strip()
        return command_is_allowed(inner, patterns) if inner else True

    subcommands = split_compound_command(cmd)
    if not subcommands:
        return False

    for sub in subcommands:
        if _is_shell_construct(sub):
            body_cmds = _extract_body_commands(sub)
            if body_cmds is None:
                return False
            for body_cmd in body_cmds:
                if not command_is_allowed(body_cmd, patterns):
                    return False
            continue

        # Output redirects (>, >>) are never safe to auto-approve,
        # UNLESS the target is an agent-internal directory (plan files,
        # memory, session state) where the agent writes as part of
        # normal operation.
        if _has_output_redirect(sub) and not _is_agent_internal_write(sub):
            return False

        unwrapped = _unwrap_var_assignment(sub)
        if unwrapped is not None:
            for inner_cmd in unwrapped:
                if not command_is_allowed(inner_cmd, patterns):
                    return False
            continue

        # Direct pattern match
        if any(fnmatch.fnmatchcase(sub, pat) for pat in patterns):
            continue

        # Normalization fallbacks — try each in turn.
        # A1: Git global options (git -C /repo log → git log)
        normalized = _normalize_git_command(sub)
        if normalized is not None and any(
            fnmatch.fnmatchcase(normalized, pat) for pat in patterns
        ):
            continue

        # A2: Absolute binary paths (/usr/bin/head → head)
        stripped_bin = _strip_binary_path(sub)
        if stripped_bin is not None and any(
            fnmatch.fnmatchcase(stripped_bin, pat) for pat in patterns
        ):
            continue

        # A3: Prefix commands (env, time, nice, command)
        unwrapped_prefix = _unwrap_prefix_command(sub)
        if unwrapped_prefix is not None:
            if command_is_allowed(unwrapped_prefix, patterns):
                continue

        # bash/sh -c inner script extraction
        inner = _find_bash_c_script(sub)
        if inner is not None:
            if not command_is_allowed(inner, patterns):
                return False
            continue

        # Nothing matched — this subcommand is not allowed
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

    # ── Allowed commands: return clean command (no prefix) and tell
    #    Claude Code to auto-approve via permissionDecision. We set
    #    this explicitly because Claude Code's own pattern matcher
    #    may mis-parse shell metacharacters inside quoted strings
    #    (e.g. grep "foo\|bar" looks like a pipe to the matcher). ──
    if is_allowed:
        description_text = _collapse_to_single_line(description or "")
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "All subcommands match configured allow patterns",
                "updatedInput": {
                    "command": cleaned_command,
                    "description": description_text or "(auto-approved)",
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
        # Description already looks like a comment line; don't double-format
        sys.exit(0)

    if not stripped:
        # No description - let require-description.sh block it
        sys.exit(0)

    # Normalize the description once: collapse any embedded newlines /
    # tabs so the field-level description and the inline prefix are both
    # single-line. The prefix additionally truncates to _PREFIX_MAX_LEN.
    description_text = _collapse_to_single_line(stripped)
    prefix = format_description_prefix(description_text)
    # `\n# ___\n` between the prefix and the command is a bash comment so
    # it does not execute when the command runs, while the underscores
    # still read as a divider on plain-text surfaces. Two newlines added;
    # the `# ___` line is dropped on retry by strip_description_box.
    updated_command = prefix + "\n# ___\n" + cleaned_command

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "updatedInput": {
                "command": updated_command,
                "description": description_text,
            },
        }
    }

    json.dump(output, sys.stdout)
    sys.exit(0)


if __name__ == "__main__":
    main()
