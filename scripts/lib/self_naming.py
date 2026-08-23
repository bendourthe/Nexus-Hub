"""Build PATH-independent command strings for a script to print about itself.

A Nexus-Hub script that tells an agent "run this next" must print a command
that works even when the script is not on PATH. Resolve the script (and the
interpreter) from their real locations at runtime, then fold a home-directory
prefix to ``~/...`` so the printed form stays readable.

This is a command-construction helper, not a shell. It never executes the
string it returns.
"""

from __future__ import annotations

import sys
from pathlib import Path
from collections.abc import Sequence


def fold_user_path(path: Path) -> str:
    """Return ``~/relative`` when *path* sits under the user's home directory.

    Uses POSIX separators so the same printed command is readable on every
    host. Paths outside the home directory are returned as an absolute
    POSIX-style path. The leading ``~`` is left unquoted by
    :func:`quote_for_shell` so a POSIX shell or PowerShell can expand it.
    """
    resolved = Path(path).resolve()
    try:
        home = Path.home().resolve()
        relative = resolved.relative_to(home)
    except (OSError, ValueError):
        return resolved.as_posix()
    return "~/" + relative.as_posix()


def quote_for_shell(token: str) -> str:
    """Quote *token* only when it contains whitespace or shell metacharacters.

    A token that starts with ``~/`` is left unquoted so ``~`` still expands.
    Double quotes are used on every platform because they are accepted by
    POSIX shells and by PowerShell.
    """
    if token.startswith("~/") and not any(ch.isspace() for ch in token):
        if any(ch in token for ch in ('"', "'", "$", "`", "&", "|", ";", "<", ">")):
            return '"' + token.replace('"', '\\"') + '"'
        return token
    if not token or any(ch.isspace() or ch in ('"', "'", "$", "`", "&", "|", ";", "<", ">") for ch in token):
        return '"' + token.replace('"', '\\"') + '"'
    return token


def expand_printed_path(printed: str) -> Path:
    """Resolve a path as printed by :func:`fold_user_path` back to a real file.

    Used by tests (and by callers that want to assert the printed command
    still names an existing file) so ``~/...`` is expanded without a shell.
    """
    if printed.startswith("~/"):
        return (Path.home() / printed[2:]).resolve()
    return Path(printed).resolve()


def runnable_self_command(
    extra_args: Sequence[str] | None = None,
    *,
    script_path: Path | None = None,
    interpreter: Path | None = None,
) -> str:
    """Return a command that re-invokes this script with *extra_args*.

    The interpreter and the script are both resolved, home-folded, and
    quoted. *extra_args* are quoted individually and appended as-is; the
    caller is responsible for supplying a replayable argument list (for
    example ``["--root", str(root), "--part", "2"]``).
    """
    script = Path(script_path) if script_path is not None else Path(sys.argv[0])
    python = Path(interpreter) if interpreter is not None else Path(sys.executable)
    tokens = [
        quote_for_shell(fold_user_path(python)),
        quote_for_shell(fold_user_path(script)),
    ]
    if extra_args:
        tokens.extend(quote_for_shell(str(arg)) for arg in extra_args)
    return " ".join(tokens)


def first_existing_path_in_command(command: str) -> Path | None:
    """Return the script path named by a ``python script.py ...`` command.

    The usual printed form is ``<interpreter> <script> [args...]``. Both
    tokens exist as files; the script is the one an agent must be able to
    re-invoke, so this skips the interpreter when a later token also
    resolves to a file. Falls back to the first existing token when the
    command names only one file.
    """
    tokens = _split_quoted(command)
    existing = [
        expand_printed_path(token)
        for token in tokens
        if expand_printed_path(token).is_file()
    ]
    if len(existing) >= 2:
        return existing[1]
    if existing:
        return existing[0]
    return None


def _split_quoted(command: str) -> list[str]:
    """Split a command produced by this module back into tokens."""
    tokens: list[str] = []
    buf: list[str] = []
    in_quote = False
    i = 0
    while i < len(command):
        ch = command[i]
        if in_quote:
            if ch == "\\" and i + 1 < len(command) and command[i + 1] == '"':
                buf.append('"')
                i += 2
                continue
            if ch == '"':
                in_quote = False
                i += 1
                continue
            buf.append(ch)
            i += 1
            continue
        if ch == '"':
            in_quote = True
            i += 1
            continue
        if ch.isspace():
            if buf:
                tokens.append("".join(buf))
                buf.clear()
            i += 1
            continue
        buf.append(ch)
        i += 1
    if buf:
        tokens.append("".join(buf))
    return tokens
