#!/usr/bin/env python3
"""Pure worktree-placement check shared by worktree-policy.sh and worktree-policy.ps1.

Reads one hook payload on stdin and looks only at `tool_input.command`. It never
runs the proposed command, never calls Git, and never starts a process, so it
cannot hang an unrelated command. Exit 0 allows; exit 42 (the wrappers turn it into 2) denies a recognized
`git worktree add` or `git worktree move` whose destination is not
`<root>/<identity>/<name>`, or one whose destination or wrapper cannot be
certified. Everything else is allowed.

The root is the NEXUS_WORKTREE_ROOT variable, then the user's own
`<nexus-hub home>/config/worktrees.json`, then `~/.worktrees`. A repository file
is never consulted. A malformed or invalid override is a denial for a worktree
mutation, never a silent fallback. The only override is changing that root; there
is no bypass switch, and NEXUS_HOOK_PROFILE and NEXUS_DISABLED_HOOKS do not apply.

This is organizational enforcement for hosts that run Nexus-Hub hooks. Aliases,
scripts and nested shells it cannot parse are listed as uncovered in
docs/runbooks/worktree-organization.md. The root rules duplicate
`scripts/nexus_worktrees.validate_root`; a drift test keeps the two in step,
because a delivered hook must not depend on a path back to the source tree.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

TAG = "[Nexus-Hub: worktree-policy]"
DENIED_EXIT = 42
VENDOR_DIRS = frozenset(
    {
        ".claude",
        ".cursor",
        ".vscode",
        ".idea",
        ".codex",
        ".gemini",
        ".windsurf",
        ".agents",
        ".nexus-hub",
    }
)
SYNC_PREFIXES = (
    "onedrive",
    "dropbox",
    "icloud",
    "google drive",
    "googledrive",
    "box sync",
    "my drive",
)
SEPARATORS = {";", "&&", "||", "|", "&", "\n"}
WRAPPERS = frozenset(
    {
        "bash",
        "sh",
        "zsh",
        "dash",
        "pwsh",
        "powershell",
        "cmd",
        "eval",
        "iex",
        "invoke-expression",
        "xargs",
        "start-process",
        "wsl",
    }
)
OPTION_WITH_ARGUMENT = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--config-env",
}
ADD_OPTIONS_WITH_ARGUMENT = {"-b", "-B", "--reason"}
MUTATION_TEXT = re.compile(r"\bworktree\s+(add|move)\b", re.IGNORECASE)
CD_COMMANDS = frozenset({"cd", "pushd", "popd", "set-location", "sl", "chdir"})
APPROVE_TARGETS = frozenset(
    {"nexus-hub", "nexus-hub.cmd", "nexus_worktrees.py", "nexus_hub_cli.py"}
)
APPROVE_TEXT = re.compile(r"migrate\b[^\n]*--approve", re.IGNORECASE)
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
HERE_STRING = re.compile(r"@(['\"])\r?\n.*?\r?\n\1@", re.DOTALL)
APPROVE_HINT = (
    "Approval is a human step: the person who owns the decision runs "
    "`nexus-hub worktree migrate --approve ...` in their own terminal, never an agent tool call."
)
UNRESOLVABLE = re.compile(r"[$%*?`]|\$\(")
HINT = (
    "Create it with: nexus-hub worktree create --repo <checkout> --branch <branch> "
    "--base <commit> --name <name>. Resolve the path first with: "
    "nexus-hub worktree path --repo <checkout> --name <name> --json."
)


class Denied(Exception):
    pass


def visible(text: str) -> str:
    """Make control characters visible so an echoed value cannot forge a tagged line."""
    out = []
    for char in text:
        code = ord(char)
        if char == "\n":
            out.append("\\n")
        elif char == "\r":
            out.append("\\r")
        elif char == "\t":
            out.append("\\t")
        elif code < 32 or code == 127:
            out.append(f"\\x{code:02x}")
        else:
            out.append(char)
    return "".join(out)


def deny(message: str) -> int:
    sys.stderr.write(f"{TAG} BLOCKED: {message} {HINT}\n")
    return 2


def hub_home() -> Path:
    return Path(os.environ.get("NEXUS_HUB_HOME") or (Path.home() / ".nexus-hub"))


def is_within(child: Path, parent: Path) -> bool:
    c = os.path.normcase(os.path.realpath(child))
    p = os.path.normcase(os.path.realpath(parent)).rstrip("\\/")
    return c == p or c.startswith(p + os.sep)


def validate_root(value: str, origin: str) -> Path:
    if not value or not value.strip():
        raise Denied(f"the worktree root from {origin} is empty")
    expanded = os.path.expanduser(value.strip())
    if expanded.startswith(("\\\\", "//")):
        raise Denied("a network or UNC path cannot be the worktree root")
    if not os.path.isabs(expanded) or (
        os.name == "nt" and not os.path.splitdrive(expanded)[0]
    ):
        raise Denied(f"the worktree root from {origin} must be an absolute local path")
    if ".." in Path(expanded).parts:
        raise Denied("the worktree root must not contain '..'")
    root = Path(os.path.abspath(expanded))
    lowered = [part.lower() for part in root.parts]
    if any(part in VENDOR_DIRS for part in lowered) or is_within(root, hub_home()):
        raise Denied(
            "the worktree root must not sit inside a tool or Nexus-Hub directory"
        )
    if any(part.startswith(SYNC_PREFIXES) for part in lowered):
        raise Denied("the worktree root must not sit in a synchronized folder")
    for ancestor in [root, *root.parents]:
        if (ancestor / ".git").exists():
            raise Denied("the worktree root must not sit inside a Git repository")
    return root


def resolve_root() -> Path:
    env_value = os.environ.get("NEXUS_WORKTREE_ROOT")
    if env_value and env_value.strip():
        return validate_root(env_value, "NEXUS_WORKTREE_ROOT")
    config = hub_home() / "config" / "worktrees.json"
    if config.is_file():
        try:
            value = json.loads(config.read_text(encoding="utf-8-sig"))["root"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise Denied(
                "the worktree policy file is not valid JSON with a 'root'"
            ) from exc
        if not isinstance(value, str):
            raise Denied("the worktree policy file must hold a string 'root'")
        return validate_root(value, "config")
    return validate_root(str(Path.home() / ".worktrees"), "default")


def tokenize(command: str) -> list[str]:
    """Split on quotes and shell separators. Backslashes stay literal so Windows paths survive."""
    tokens: list[str] = []
    current: list[str] = []
    started = False
    quote = ""
    i, n = 0, len(command)

    def flush() -> None:
        nonlocal started
        if started:
            tokens.append("".join(current))
            current.clear()
            started = False

    while i < n:
        char = command[i]
        if quote:
            if char == quote:
                quote = ""
            elif (
                char in ("\\", "`")
                and quote == '"'
                and i + 1 < n
                and command[i + 1] == '"'
            ):
                current.append('"')
                i += 1
            else:
                current.append(char)
        elif char in ("'", '"'):
            quote, started = char, True
        elif char in " \t\r":
            flush()
        elif char == "\n":
            flush()
            tokens.append("\n")
        elif char in ";|&":
            flush()
            pair = command[i : i + 2]
            if pair in ("&&", "||"):
                tokens.append(pair)
                i += 1
            else:
                tokens.append(char)
        else:
            current.append(char)
            started = True
        i += 1
    flush()
    return tokens


def segments(tokens: list[str]) -> list[list[str]]:
    result: list[list[str]] = [[]]
    for token in tokens:
        if token in SEPARATORS:
            result.append([])
        else:
            result[-1].append(token)
    return [s for s in result if s]


def program_name(token: str) -> str:
    base = re.split(r"[\\/]", token)[-1].lower()
    return base[:-4] if base.endswith(".exe") else base


def git_worktree_action(segment: list[str]) -> tuple[list[str], list[str], str] | None:
    """(-C chain, arguments after the action, action) for a `git ... worktree <action>` segment."""
    index = 0
    while index < len(segment) and (
        re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", segment[index])
        or program_name(segment[index]) in {"sudo", "command", "env", "call"}
        or segment[index] == "&"
    ):
        index += 1
    if index >= len(segment) or program_name(segment[index]) != "git":
        return None
    index += 1
    chain: list[str] = []
    while index < len(segment) and segment[index].startswith("-"):
        option = segment[index]
        if option in OPTION_WITH_ARGUMENT and index + 1 < len(segment):
            if option == "-C":
                chain.append(segment[index + 1])
            index += 2
        else:
            index += 1
    if index + 1 >= len(segment) or segment[index].lower() != "worktree":
        return None
    return chain, segment[index + 2 :], segment[index + 1].lower()


def positionals(arguments: list[str], with_value: set[str]) -> list[str]:
    found: list[str] = []
    skip = False
    for token in arguments:
        if skip:
            skip = False
        elif token == "--":
            continue
        elif token in with_value:
            skip = True
        elif not token.startswith("-"):
            found.append(token)
    return found


def effective_cwd(base: str, chain: list[str]) -> str:
    cwd = base
    for step in chain:
        cwd = os.path.abspath(os.path.join(cwd, os.path.expanduser(step)))
    return cwd


def is_absolute(raw: str) -> bool:
    expanded = os.path.expanduser(raw)
    return os.path.isabs(expanded) and (
        os.name != "nt" or bool(os.path.splitdrive(expanded)[0])
    )


def check_destination(
    raw: str, cwd: str, root: Path, verb: str, after_cd: bool = False
) -> None:
    if UNRESOLVABLE.search(raw) or not raw.strip():
        raise Denied(
            f"the destination of `git worktree {verb}` cannot be determined "
            f"({visible(raw)}) so it cannot be checked against the worktree root."
        )
    if after_cd and not is_absolute(raw):
        raise Denied(
            f"`git worktree {verb}` uses a relative destination ({visible(raw)}) after a "
            "directory change in the same command, so its location cannot be certified."
        )
    destination = os.path.abspath(os.path.join(cwd, os.path.expanduser(raw)))
    if any(part.lower() in VENDOR_DIRS for part in Path(destination).parts):
        raise Denied(
            f"`git worktree {verb}` targets a tool or Nexus-Hub directory ({visible(raw)})."
        )
    dest = Path(destination)
    if os.path.normcase(os.path.realpath(dest.parent.parent)) != os.path.normcase(
        os.path.realpath(root)
    ):
        raise Denied(
            f"`git worktree {verb}` destination {visible(raw)} is outside "
            f"{visible(str(root))}/<identity>/<name>."
        )


def command_word(segment: list[str]) -> str:
    """First command word of a segment, past environment assignments and common prefixes."""
    index = 0
    while index < len(segment) and (
        re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", segment[index])
        or program_name(segment[index].lstrip("({")) in {"sudo", "command", "env", "call"}
        or segment[index] == "&"
    ):
        index += 1
    return segment[index].lstrip("({") if index < len(segment) else ""


def strip_heredoc_bodies(command: str) -> str:
    """Drop heredoc and PowerShell here-string bodies, which are text (a commit message), not commands.

    A body fed to a shell wrapper (`bash <<EOF`) is kept so what it runs is still checked.
    An unquoted bash heredoc can run substitutions; that case is not certified.
    """

    def feeds_wrapper(line: str) -> bool:
        tokens = segments(tokenize(line.split("<<", 1)[0]))
        return any(program_name(command_word(t)) in WRAPPERS for t in tokens if t)

    out: list[str] = []
    skipping = ""
    for line in command.split("\n"):
        if skipping:
            if line.strip() == skipping:
                skipping = ""
            continue
        match = HEREDOC.search(line)
        if match and not feeds_wrapper(line):
            skipping = match.group(2)
        out.append(line)
    text = "\n".join(out)
    return HERE_STRING.sub(
        lambda m: "''" if not feeds_wrapper(text[: m.start()].rsplit("\n", 1)[-1]) else m.group(0),
        text,
    )


def without_single_quotes(command: str) -> str:
    return re.sub(r"'[^']*'", "''", command)


def substitution_runs_mutation(command: str, shell: str) -> bool:
    """True when a command substitution outside single quotes contains a worktree add or move."""
    text = without_single_quotes(command)
    starts = [m.start() for m in re.finditer(r"\$\(", text)]
    if shell != "powershell":
        starts += [m.start() for m in re.finditer("`", text)]
    return any(MUTATION_TEXT.search(text[start:]) for start in starts)


def approval_attempt(segment: list[str]) -> bool:
    names = {program_name(t.lstrip("({")) for t in segment}
    flags = any(t == "--approve" or t.startswith("--approve=") for t in segment)
    return bool(names & APPROVE_TARGETS) and "migrate" in segment and flags


def evaluate(command: str, cwd: str, shell: str = "bash") -> int:
    command = strip_heredoc_bodies(command)
    segs = segments(tokenize(command))
    recognized = False
    changed_dir = False
    root: Path | None = None
    try:
        for segment in segs:
            word = program_name(command_word(segment))
            if word in CD_COMMANDS:
                changed_dir = True
                continue
            if approval_attempt(segment):
                return deny_approval("an agent tool call cannot approve a migration manifest.")
            hit = git_worktree_action(segment)
            if hit is None or hit[2] not in ("add", "move"):
                continue
            recognized = True
            chain, arguments, action = hit
            root = root or resolve_root()
            where = effective_cwd(cwd, chain)
            if action == "add":
                found = positionals(arguments, ADD_OPTIONS_WITH_ARGUMENT)
                if not found:
                    raise Denied("`git worktree add` has no destination path")
                check_destination(found[0], where, root, "add", changed_dir)
            else:
                found = positionals(arguments, set())
                if len(found) < 2:
                    raise Denied("`git worktree move` needs a source and a destination")
                check_destination(found[1], where, root, "move", changed_dir)
    except Denied as exc:
        return deny(str(exc))
    wrapped = any(program_name(command_word(s)) in WRAPPERS for s in segs if s)
    if wrapped and APPROVE_TEXT.search(command) and re.search(
        r"nexus-hub|nexus_worktrees|nexus_hub_cli", command, re.IGNORECASE
    ):
        return deny_approval("an approval inside a nested shell cannot be certified.")
    if recognized:
        return 0
    if MUTATION_TEXT.search(command) and (
        wrapped or substitution_runs_mutation(command, shell)
    ):
        return deny(
            "a worktree add or move sits inside a wrapper, substitution or nested "
            "shell that cannot be certified."
        )
    return 0


def deny_approval(message: str) -> int:
    sys.stderr.write(f"{TAG} BLOCKED: {message} {APPROVE_HINT}\n")
    return 2


def main() -> int:
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except ValueError:
        payload = None
    if not isinstance(payload, dict):
        if MUTATION_TEXT.search(raw):
            return deny(
                "the hook payload is malformed but mentions a worktree add or move."
            )
        return 0
    tool_input = payload.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command:
        return 0
    cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else os.getcwd()
    shell = "powershell" if str(payload.get("tool_name", "")).lower() == "powershell" else "bash"
    return evaluate(command, cwd or os.getcwd(), shell)


if __name__ == "__main__":
    # Python itself exits 2 when it cannot open a script, so a denial is reported as 42
    # and the wrappers translate it. Any other code means this helper did not run.
    result = main()
    sys.exit(DENIED_EXIT if result == 2 else result)
