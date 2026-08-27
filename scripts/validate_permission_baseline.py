#!/usr/bin/env python3
"""Validate that Nexus-Hub's shipped read-only permission baselines are actually read-only.

Nexus-Hub ships auto-approve allowlists in ``configs/permissions/``. Every entry in
those files is auto-approved by the target platform's *native* matcher with no
Nexus-Hub logic applied, so an entry that permits a write, a deletion, a process
spawn, or a remote mutation is a silent privilege grant on every installed host.

This validator exists because the v3.17.0 Phase 1.1 audit found several such
entries that looked read-only *by command name*: ``Bash(gh api *)`` admits
``--method DELETE``, ``Bash(find *)`` admits ``-fprintf``, ``Bash(git branch *)``
admits ``-D``, and ``Bash(xcrun *)`` executes an arbitrary named tool. Classifying
by name is what let them through, so the checks below classify by *invocation
shape* instead. This is the ``I6`` invariant recorded in
``docs/releases/v3/v3.15/comparisons/v3.15.6-comparison-sandbox-escapes.md``.

Detected shapes:

1. A literal shell redirection operator inside a pattern.
2. A literal mutating flag or subcommand for a known dual-mode tool.
3. A bare trailing wildcard directly after a dual-mode tool name, which admits any
   flag that tool accepts (the ``Bash(git *)`` versus ``Bash(git log *)`` distinction).
3b. The same one level deeper: a wildcard after a dual-mode *subcommand*, where pinning
   the first argument rescues nothing (``Bash(gh repo *)`` admits ``gh repo delete``),
   plus subcommands no amount of pinning rescues (``gh api`` takes ``--method`` at any
   depth). Rule 3 alone let ``Bash(gh api *)`` -- this validator's own motivating
   example -- pass; the Phase 1.4 tests caught that.
4. A PowerShell cmdlet that mutates outright, resolved through its aliases.
5. A PowerShell dual-mode cmdlet carrying an unpinned wildcard, which admits
   ``-CimSession`` or ``-ComputerName`` and converts a local read into a remote one.
6. PowerShell syntax classes that ``catalog/hooks/format-powershell-description.py``
   already rejects on the hook path, so the native-path and hook-path definitions of
   "read-only" cannot drift apart.

Matcher semantics this validator relies on are recorded, with sources, in
``docs/releases/v3/v3.17/development/permission-matcher-findings.md``.

Usage::

    python scripts/validate_permission_baseline.py                 # shipped configs
    python scripts/validate_permission_baseline.py FILE [FILE ...] # explicit files

Exit codes: ``0`` clean, ``1`` violations found, ``2`` usage or parse error.

Standard library only, by design: this runs inside ``make validate`` and CI on hosts
with no third-party packages installed.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Default targets. Each entry pairs a config path with how that platform's matcher
# resolves a pattern, because the two differ in a way that changes the verdict:
#   "glob"   - Claude Code. A pattern without a wildcard is an EXACT match, so a bare
#              tool name such as Bash(git tag) is safe (it lists tags and nothing more).
#   "prefix" - Gemini CLI. Every entry is a prefix, so run_shell_command(find) matches
#              "find . -delete" and a bare tool name is NOT safe.
DEFAULT_TARGETS: tuple[tuple[str, str], ...] = (
    ("configs/permissions/claude-permissions.json", "glob"),
    ("configs/permissions/gemini-permissions.json", "prefix"),
)

# --------------------------------------------------------------------------------------
# Data lists. Each is one line to extend; add a tool or cmdlet here rather than adding
# a code branch below.
# --------------------------------------------------------------------------------------

# Shell redirection operators. `> file` truncates its target regardless of what the
# command itself emits, so a redirect inside a pattern is a write primitive even when
# the command is a pure printer.
REDIRECT_PATTERN = re.compile(r"(?<![0-9\w])[12]?>>?|&>|>\|")

# Dual-mode tools: read-only in their common form, mutating under some flag or
# subcommand. Criterion for adding one: the tool has at least one documented flag or
# subcommand that writes a file, deletes state, spawns a process, or reaches a remote
# target. A pattern may name one of these ONLY when the first argument token is a
# literal that pins the subcommand (Bash(git log *) is fine, Bash(git *) is not).
DUAL_MODE_TOOLS: frozenset[str] = frozenset({
    "apt", "apt-get", "bash", "cargo", "defaults", "dmesg", "dnf", "docker", "dotnet",
    "dpkg", "env", "find", "gh", "git", "go", "gradle", "ip", "journalctl", "kubectl",
    "mvn", "node", "npm", "nmcli", "perl", "pip", "pip3", "pnpm", "plutil", "podman",
    "python", "python3", "rpm", "ruby", "sed", "sh", "sort", "ss", "sysctl",
    "systemctl", "tar", "xcode-select", "xcrun", "yarn", "yum", "zsh",
})

# Tools whose FIRST argument is itself an arbitrary program, so pinning cannot rescue
# them and no wildcard form is ever safe. Interpreters are deliberately NOT here: they
# take a program only behind an explicit flag (`-c`, `-e`, `-m`), which the
# MUTATING_TOKENS rule catches, leaving genuinely inert forms such as
# `Bash(python --version)` correctly allowed.
ALWAYS_UNSAFE_TOOLS: frozenset[str] = frozenset({
    "awk", "gawk", "mawk",  # BEGIN{print > "/path"} writes; the program IS the argument
})

# Tool+subcommand pairs where NO wildcard form is safe, because the mutating switch is
# a flag that can appear at any depth rather than a subcommand that pinning excludes.
# `gh api --method DELETE repos/o/r` is the canonical case and is why v3.17.0 Phase 1.1
# deleted the `gh api` entries outright instead of rescoping them: pinning the endpoint
# (`gh api repos/o/r *`) leaves `--method` just as reachable.
UNSAFE_SUBCOMMANDS: frozenset[str] = frozenset({
    "gh api",
})

# Dual-mode SUBCOMMANDS: pinning the first argument normally rescues a dual-mode tool
# (`Bash(git log *)` is safe), but these subcommands are themselves dual-mode, so
# pinning only to them rescues nothing -- `gh repo *` admits `gh repo delete` and
# `git branch *` admits `git branch -D`. One more level of pinning is required, which
# every entry in the shipped baseline already has (`gh pr view *`, `git branch --list *`).
# Criterion for adding a pair: the subcommand has its own mutating verb or flag.
DUAL_MODE_SUBCOMMANDS: frozenset[str] = frozenset({
    "gh auth", "gh cache", "gh config", "gh gist", "gh issue", "gh label", "gh pr",
    "gh release", "gh repo", "gh run", "gh secret", "gh ssh-key", "gh variable",
    "gh workflow",
    "git branch", "git config", "git notes", "git remote", "git stash",
    "git submodule", "git tag", "git worktree",
    "docker builder", "docker compose", "docker container", "docker image",
    "docker network", "docker system", "docker volume",
    "kubectl config",
})

# Literal mutating tokens, checked per tool. A token here appearing anywhere in the
# pattern is a violation regardless of position.
MUTATING_TOKENS: dict[str, tuple[str, ...]] = {
    "gh": ("--method post", "--method put", "--method patch", "--method delete",
           "-x post", "-x put", "-x patch", "-x delete", "delete", "create", "close",
           "merge", "edit", "set"),
    "find": ("-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf",
             "-fls"),
    "sort": ("-o", "--output"),
    "sed": ("-i", "--in-place"),
    "tar": ("-x", "--extract", "-c", "--create", "--delete"),
    "git": ("-d", "push", "commit", "add", "rm", "reset", "checkout", "switch",
            "merge", "rebase", "clean", "restore", "stash push", "stash pop",
            "stash drop", "stash clear", "set-url", "prune", "gc", "fetch", "pull",
            "apply", "cherry-pick", "revert", "worktree add", "worktree remove"),
    "ip": ("add", "del", "set", "flush", "change", "replace"),
    "sysctl": ("-w", "--write"),
    "ss": ("-k", "--kill"),
    "journalctl": ("--vacuum-size", "--vacuum-time", "--vacuum-files", "--rotate",
                   "--flush", "--sync"),
    "dmesg": ("-c", "-C", "--clear", "--read-clear"),
    "systemctl": ("start", "stop", "restart", "reload", "enable", "disable", "mask",
                  "unmask", "kill", "set-property"),
    "docker": ("run", "rm", "rmi", "exec", "stop", "kill", "build", "push", "pull",
               "create", "commit", "cp", "-h", "--context", "--url", "--connection"),
    "podman": ("run", "rm", "rmi", "exec", "stop", "kill", "build", "push", "--url",
               "--connection"),
    "npm": ("install", "uninstall", "publish", "link", "update", "exec", "run"),
    "yarn": ("add", "remove", "publish", "install", "run"),
    "pnpm": ("add", "remove", "publish", "install", "run", "exec"),
    "pip": ("install", "uninstall", "download"),
    "pip3": ("install", "uninstall", "download"),
    "go": ("build", "install", "run", "get", "generate", "clean"),
    "cargo": ("build", "install", "run", "publish", "clean"),
    "dotnet": ("build", "run", "publish", "clean", "add", "remove"),
    "mvn": ("install", "deploy", "clean"),
    "gradle": ("build", "publish", "clean"),
    "apt": ("install", "remove", "purge", "upgrade"),
    "apt-get": ("install", "remove", "purge", "upgrade"),
    "dnf": ("install", "remove", "upgrade"),
    "yum": ("install", "remove", "upgrade"),
    "dpkg": ("-i", "--install", "-r", "--remove", "-P", "--purge"),
    "rpm": ("-i", "--install", "-e", "--erase", "-U", "--upgrade"),
    "defaults": ("write", "delete", "import"),
    "plutil": ("-convert", "-insert", "-replace", "-remove"),
    "xcode-select": ("--switch", "-s", "--install", "--reset"),
    # Interpreters and shells: inert for `--version`, arbitrary execution behind these.
    "python": ("-c", "-m", "--command"),
    "python3": ("-c", "-m", "--command"),
    "node": ("-e", "-p", "--eval", "--print", "--require"),
    "perl": ("-e", "-E", "-i"),
    "ruby": ("-e", "-r"),
    "sh": ("-c",),
    "bash": ("-c",),
    "zsh": ("-c",),
    "xcrun": ("--run", "-r"),  # `xcrun <tool>` and `--run` execute; --find/--show-* query
    "env": ("-i", "--ignore-environment", "-u", "--unset"),
    "kubectl": ("apply", "delete", "create", "patch", "edit", "scale", "exec"),
    "nmcli": ("add", "modify", "delete", "up", "down"),
}

# PowerShell cmdlets that mutate outright. These must never appear in a read-only
# baseline in any form, pinned or not.
PS_MUTATING_CMDLETS: frozenset[str] = frozenset({
    "set-content", "add-content", "out-file", "new-item", "remove-item", "copy-item",
    "move-item", "rename-item", "clear-content", "set-item", "set-itemproperty",
    "new-itemproperty", "remove-itemproperty", "clear-itemproperty", "start-process",
    "stop-process", "invoke-expression", "invoke-command", "invoke-webrequest",
    "invoke-restmethod", "invoke-cimmethod", "invoke-wmimethod", "invoke-item",
    "set-executionpolicy", "register-scheduledtask", "unregister-scheduledtask",
    "start-service", "stop-service", "restart-service", "set-service", "new-service",
    "remove-psdrive", "new-psdrive", "set-variable", "remove-variable", "export-csv",
    "export-clixml", "set-acl", "new-symlink", "remove-module", "import-module",
    "set-date", "clear-host", "stop-computer", "restart-computer", "enable-psremoting",
})

# PowerShell alias -> canonical cmdlet. Claude Code canonicalizes aliases BEFORE
# matching, so a cmdlet-name-only denylist would let PowerShell(sc *) and
# PowerShell(iex *) straight through. Note that `sl` is Set-Location (harmless, and
# present in the shipped baseline), NOT Set-Content; getting that wrong produces a
# false positive on a legitimate entry.
PS_ALIASES: dict[str, str] = {
    "ac": "add-content", "cpi": "copy-item", "copy": "copy-item", "cp": "copy-item",
    "del": "remove-item", "erase": "remove-item", "rd": "remove-item",
    "rm": "remove-item", "rmdir": "remove-item", "ri": "remove-item",
    "icm": "invoke-command", "iex": "invoke-expression", "ii": "invoke-item",
    "irm": "invoke-restmethod", "iwr": "invoke-webrequest", "curl": "invoke-webrequest",
    "wget": "invoke-webrequest", "md": "new-item", "mkdir": "new-item", "ni": "new-item",
    "mi": "move-item", "move": "move-item", "mv": "move-item", "rni": "rename-item",
    "ren": "rename-item", "sc": "set-content", "si": "set-item",
    "sp": "set-itemproperty", "saps": "start-process", "start": "start-process",
    "spps": "stop-process", "kill": "stop-process", "sasv": "start-service",
    "spsv": "stop-service", "epcsv": "export-csv", "epal": "export-alias",
    "sv": "set-variable", "set": "set-variable", "clc": "clear-content",
    "cli": "clear-item", "rp": "remove-itemproperty", "sal": "set-alias",
}

# PowerShell dual-mode cmdlets: genuine getters whose returned objects expose mutating
# methods, and whose trailing wildcard admits a remote-target parameter. Allowed only
# when the pattern pins its arguments rather than trailing a bare wildcard.
PS_DUAL_MODE_CMDLETS: frozenset[str] = frozenset({
    "get-ciminstance", "get-wmiobject", "get-cimclass", "get-ciminstanceproperty",
})

# Parameters that retarget a local read at a remote host.
PS_REMOTE_PARAMS: tuple[str, ...] = ("-cimsession", "-computername", "-session",
                                     "-connectionuri", "-vmname")

# Syntax classes rejected by catalog/hooks/format-powershell-description.py. Kept in
# sync deliberately: tests/validators/test_validate_permission_baseline.py asserts this
# set matches the hook's, so the two layers cannot disagree about what "read-only" means.
PS_DISALLOWED_SYNTAX: tuple[str, ...] = (";", "&", "`", "$(", "@(", "@{", "{", "}",
                                         ">", "<")

# Rule prefixes this validator understands, mapped to the shell family they belong to.
RULE_PREFIXES: dict[str, str] = {
    "Bash": "posix",
    "PowerShell": "powershell",
    "run_shell_command": "posix",
}

_RULE_RE = re.compile(r"^(?P<tool>[A-Za-z_][A-Za-z0-9_]*)\((?P<body>.*)\)$", re.DOTALL)


class Violation:
    """One offending entry, with the rule that caught it."""

    __slots__ = ("source", "entry", "rule", "detail")

    def __init__(self, source: str, entry: str, rule: str, detail: str) -> None:
        self.source = source
        self.entry = entry
        self.rule = rule
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.source}: {self.entry}\n    [{self.rule}] {self.detail}"


def _normalize_wildcard_suffix(body: str) -> str:
    """Rewrite the ``:*`` trailing-wildcard form into the space-separated form.

    Claude Code treats ``Bash(ls:*)`` and ``Bash(ls *)`` as equivalent, and the ``:*``
    form is recognized only at the end of a pattern.
    """
    if body.endswith(":*"):
        return body[:-2] + " *"
    return body


def _tokenize(body: str) -> list[str]:
    """Split a pattern body into whitespace-separated tokens, quotes preserved."""
    return [tok for tok in body.strip().split() if tok]


def _canonical_cmdlet(token: str) -> str:
    """Resolve a PowerShell token to its canonical lowercase cmdlet name."""
    name = token.strip().lower()
    # Strip a call-operator or path prefix so `.\Set-Content` still resolves.
    name = name.lstrip("&.\\/ ")
    return PS_ALIASES.get(name, name)


def _check_posix_entry(source: str, entry: str, body: str, match_mode: str) -> list[Violation]:
    """Apply the POSIX-shell rules to one pattern body."""
    found: list[Violation] = []
    body = _normalize_wildcard_suffix(body)
    lowered = body.lower()
    tokens = _tokenize(body)

    if REDIRECT_PATTERN.search(body):
        found.append(Violation(
            source, entry, "redirect",
            "Pattern contains a shell redirection operator. `> file` truncates its "
            "target regardless of what the command emits, so this is a write primitive.",
        ))

    if not tokens:
        return found

    tool = tokens[0].lower().rsplit("/", 1)[-1]
    args = tokens[1:]

    if tool in ALWAYS_UNSAFE_TOOLS:
        # A bare exact-match entry with no arguments is still inert in glob mode.
        if match_mode == "prefix" or args or "*" in body:
            found.append(Violation(
                source, entry, "always-unsafe-tool",
                f"`{tool}` executes an arbitrary program or inner command, so no "
                f"wildcard form of it is safe to auto-approve.",
            ))
            return found

    for token in MUTATING_TOKENS.get(tool, ()):  # rule 2: literal mutating token
        if re.search(rf"(?<![\w-]){re.escape(token)}(?![\w-])", lowered):
            found.append(Violation(
                source, entry, "mutating-token",
                f"`{tool}` pattern contains the mutating token `{token}`.",
            ))
            break

    # Rule 3: an unpinned wildcard directly after a dual-mode tool name. In prefix
    # mode a bare tool name behaves identically to a trailing wildcard.
    if tool in DUAL_MODE_TOOLS:
        first_arg = args[0] if args else None
        unpinned = first_arg is None or first_arg.startswith("*")
        if unpinned and (match_mode == "prefix" or "*" in body or not args):
            if match_mode == "glob" and "*" not in body and args:
                pass  # exact-match pattern with pinned args: safe
            elif match_mode == "glob" and "*" not in body and not args:
                pass  # bare exact-match tool name (e.g. Bash(git tag)): safe
            else:
                found.append(Violation(
                    source, entry, "unpinned-dual-mode-tool",
                    f"`{tool}` is a dual-mode tool and this pattern does not pin its "
                    f"first argument to a literal subcommand, so the wildcard admits "
                    f"any flag `{tool}` accepts. Pin it (e.g. `{tool} <subcommand> *`).",
                ))

    # Rule 3b: the same reasoning one level deeper. Pinning the first argument is not
    # sufficient when the pinned subcommand is itself dual-mode. Without this, the very
    # entry that motivated this validator -- `Bash(gh api *)`, which admits
    # `--method DELETE` -- passes, because `api` satisfies rule 3.
    if args:
        pair = f"{tool} {args[0].lower()}"
        # In prefix mode every entry is a prefix, so a pattern with no wildcard behaves
        # exactly like one with a trailing wildcard.
        wildcard_reachable = match_mode == "prefix" or "*" in body
        next_token = args[1] if len(args) > 1 else None
        unpinned_next = next_token is None or next_token.startswith("*")

        if pair in UNSAFE_SUBCOMMANDS and wildcard_reachable:
            found.append(Violation(
                source, entry, "unsafe-subcommand",
                f"`{pair}` takes its mutating switch as a flag that can appear at any "
                f"depth, so no wildcard form is safe however far the pattern is pinned. "
                f"Drop it or replace it with a fully-literal read-only invocation.",
            ))
        elif pair in DUAL_MODE_SUBCOMMANDS and unpinned_next and wildcard_reachable:
            found.append(Violation(
                source, entry, "unpinned-dual-mode-subcommand",
                f"`{pair}` is itself dual-mode, so pinning only to `{args[0]}` leaves "
                f"the wildcard admitting its mutating verbs and flags. Pin one level "
                f"deeper (e.g. `{pair} <read-only-verb> *`).",
            ))

    return found


def _check_powershell_entry(source: str, entry: str, body: str) -> list[Violation]:
    """Apply the PowerShell rules to one pattern body."""
    found: list[Violation] = []
    body = _normalize_wildcard_suffix(body)
    lowered = body.lower()
    tokens = _tokenize(body)

    for syntax in PS_DISALLOWED_SYNTAX:
        if syntax in body:
            found.append(Violation(
                source, entry, "powershell-syntax",
                f"Pattern contains `{syntax}`, a syntax class that "
                f"catalog/hooks/format-powershell-description.py rejects on the hook "
                f"path. The native path and the hook path must agree.",
            ))
            break

    if not tokens:
        return found

    # A pattern may open with a subexpression such as ((Get-Location).Path); look at
    # every token so an embedded mutating cmdlet is still caught.
    for token in tokens:
        canonical = _canonical_cmdlet(token.strip("()$"))
        if canonical in PS_MUTATING_CMDLETS:
            found.append(Violation(
                source, entry, "powershell-mutating-cmdlet",
                f"`{token}` resolves to `{canonical}`, which mutates state and must "
                f"never appear in a read-only baseline.",
            ))
            return found

    head = _canonical_cmdlet(tokens[0].strip("()$"))
    args = tokens[1:]

    if head in PS_DUAL_MODE_CMDLETS:
        first_arg = args[0] if args else None
        if first_arg is None or first_arg.startswith("*"):
            found.append(Violation(
                source, entry, "powershell-unpinned-dual-mode",
                f"`{head}` returns objects whose methods mutate, and an unpinned "
                f"wildcard admits a remote-target parameter such as -CimSession, "
                f"converting a local read into a remote one. Pin the class instead.",
            ))

    for param in PS_REMOTE_PARAMS:
        if param in lowered:
            found.append(Violation(
                source, entry, "powershell-remote-target",
                f"Pattern names the remote-target parameter `{param}`.",
            ))
            break

    return found


def _iter_entries(payload: object) -> list[str]:
    """Collect every allowlist string from a permission document.

    Handles both shapes Nexus-Hub ships: Claude's ``permissions.allow`` array and
    Gemini's ``tools.allowed`` array. Metadata keys prefixed with ``_`` are skipped so
    the ``_hardening`` documentation block is never mistaken for a rule.
    """
    entries: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(key, str) and key.startswith("_"):
                    continue
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            entries.append(node)

    walk(payload)
    return entries


def check_file(path: Path, match_mode: str) -> list[Violation]:
    """Validate one permission config. Raises ValueError on an unreadable document."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc

    source = path.as_posix()
    found: list[Violation] = []

    for entry in _iter_entries(payload):
        match = _RULE_RE.match(entry.strip())
        if match is None:
            continue  # bare tool names such as "Read" or "WebSearch" carry no pattern
        prefix = match.group("tool")
        family = RULE_PREFIXES.get(prefix)
        if family is None:
            continue  # WebFetch(domain:...) and MCP rules are out of scope
        body = match.group("body")
        if family == "powershell":
            found.extend(_check_powershell_entry(source, entry, body))
        else:
            found.extend(_check_posix_entry(source, entry, body, match_mode))

    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate that shipped permission baselines are read-only at the "
                    "side-effect level.",
    )
    parser.add_argument(
        "files", nargs="*", type=Path,
        help="Permission config(s) to check. Defaults to the shipped configs.",
    )
    parser.add_argument(
        "--match-mode", choices=("glob", "prefix"), default=None,
        help="Matcher semantics for explicitly-passed files. Defaults to 'glob' "
             "(Claude Code). Use 'prefix' for Gemini-shaped configs.",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Print violations only; suppress the per-file OK lines.",
    )
    args = parser.parse_args(argv)

    if args.files:
        targets = [(path, args.match_mode or "glob") for path in args.files]
    else:
        targets = [(REPO_ROOT / rel, mode) for rel, mode in DEFAULT_TARGETS]

    all_violations: list[Violation] = []
    for path, mode in targets:
        if not path.exists():
            print(f"ERROR: {path} does not exist", file=sys.stderr)
            return 2
        try:
            violations = check_file(path, mode)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        all_violations.extend(violations)
        if not violations and not args.quiet:
            print(f"  {path.name} OK ({mode} matcher)")

    if all_violations:
        print(
            f"\nFAIL: {len(all_violations)} mutation-capable "
            f"{'entry' if len(all_violations) == 1 else 'entries'} in the read-only "
            f"baseline:\n",
            file=sys.stderr,
        )
        for violation in all_violations:
            print(f"  {violation}", file=sys.stderr)
        print(
            "\nSee docs/releases/v3/v3.17/development/permission-matcher-findings.md for the "
            "matcher semantics behind these rules.",
            file=sys.stderr,
        )
        return 1

    if not args.quiet:
        print("Permission baseline is read-only at the side-effect level.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
