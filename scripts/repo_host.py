#!/usr/bin/env python3
"""Resolve and verify the GitHub `owner/repo` behind a git remote.

Shared by `check_plan_completion.py` and any other caller that must pin a hosting
call to one repository. The installed layout is flat (`~/.nexus-hub/scripts/`), so
callers import this module as a sibling.

The resolution refuses to guess. A path is accepted only when its host is verified
as `github.com` or the configured `GH_HOST`:

- `https://host/owner/repo(.git)` takes the host literally.
- `ssh://git@host[:port]/owner/repo(.git)` and the scp-like `git@host:owner/repo(.git)`
  go through ssh, which applies `~/.ssh/config`, so a host that is not itself
  accepted is treated as an alias and replaced by the `hostname` line of
  `ssh -G <host>`. No ssh, a slow ssh, or an unaccepted real host yields no repository.

`resolve_repo` also cross-checks the URL's answer with `gh repo view` when no frozen
record repository exists, because `gh repo set-default` lives in `.git/config`, which
an agent can write; a disagreement yields no repository rather than a pick.

Only the standard library is used.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Callable, List, Optional, Protocol, Tuple

Runner = Callable[[List[str], Optional[Path]], Tuple[int, str]]

DEFAULT_TIMEOUT_SECONDS = 10.0
REPO_PATH_RE = re.compile(r"^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?$")
HTTPS_RE = re.compile(r"^https://(?:[^@/\s]+@)?(?P<host>[^/:\s]+)(?::\d+)?/(?P<path>\S+)$", re.IGNORECASE)
SSH_URL_RE = re.compile(r"^ssh://(?:[^@/\s]+@)?(?P<host>[^/:\s]+)(?::\d+)?/(?P<path>\S+)$", re.IGNORECASE)
SCP_RE = re.compile(r"^(?:[^@/:\s]+@)?(?P<host>[^/:\s]+):(?P<path>[^/\s][^\s]*)$")
ALIAS_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class Budget(Protocol):
    def remaining(self) -> float: ...


# --------------------------------------------------------------------------- tools


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _which_on_path(name: str) -> str | None:
    """Find `name` on PATH's absolute entries only, never in the current directory.

    `shutil.which` on Windows searches the current directory first even when given an
    explicit path, so a `git.bat` planted at a repository root would run before the
    inside-the-tree refusal could see it.
    """
    exts = [""]
    if os.name == "nt":
        exts = [e.lower() for e in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if e]
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        base = Path(entry)
        if not entry or not base.is_absolute():
            continue
        for ext in exts:
            candidate = base / (name + ext)
            if candidate.is_file() and (os.name == "nt" or os.access(candidate, os.X_OK)):
                return str(candidate)
    return None


def absolute_tool(name: str, repo_root: Path | None) -> str | None:
    """Resolve an executable once, refusing one that lives inside the working tree."""
    found = _which_on_path(name)
    if not found:
        return None
    if repo_root is not None and _is_inside(Path(found), repo_root):
        return None
    return found


def _default_runner(budget: Budget | None) -> Runner:
    def run(argv: list[str], cwd: Path | None = None) -> tuple[int, str]:
        timeout = budget.remaining() if budget is not None else DEFAULT_TIMEOUT_SECONDS
        if timeout <= 0:
            return -1, ""
        env = dict(os.environ, GH_PROMPT_DISABLED="1", GIT_TERMINAL_PROMPT="0", NO_COLOR="1")
        try:
            proc = subprocess.run(
                argv, cwd=cwd, env=env, capture_output=True, text=True, check=False,
                encoding="utf-8", errors="replace", timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired):
            return -1, ""
        return proc.returncode, proc.stdout

    return run


# --------------------------------------------------------------------------- hosts


def accepted_hosts() -> set[str]:
    """The one host `gh --repo owner/repo` queries: `GH_HOST` when set, else `github.com`.

    Accepting any other host would pin hosting calls to a same-named repository on a
    different server from the one the remote pushes to.
    """
    configured = os.environ.get("GH_HOST", "").strip().lower()
    configured = re.sub(r"^https?://", "", configured).split("/", 1)[0].split(":", 1)[0]
    return {configured} if configured else {"github.com"}


def parse_remote(url: str) -> tuple[str, str, bool] | None:
    """(host, owner/repo, via_ssh) for a recognized remote URL, else None."""
    url = url.strip()
    # `#`, `?`, and `\` end or confuse an authority, so a regex would read a host git never contacts.
    if not url or any(c.isspace() for c in url) or any(c in url for c in "#?\\"):
        return None
    for pattern, via_ssh in ((HTTPS_RE, False), (SSH_URL_RE, True)):
        match = pattern.match(url)
        if match:
            break
    else:
        if "://" in url:
            return None
        match, via_ssh = SCP_RE.match(url), True
        # git reads `C:owner/repo` as a drive-relative local path on Windows, never as ssh host `c`.
        if not match or len(match.group("host")) == 1:
            return None
    path = REPO_PATH_RE.match(match.group("path"))
    if not path:
        return None
    return match.group("host").lower(), path.group("repo"), via_ssh


def _ssh_hostname(alias: str, ssh: str, run: Runner) -> str | None:
    if not ALIAS_RE.match(alias) or alias.startswith("-"):
        return None
    rc, out = run([ssh, "-G", alias], None)
    if rc != 0:
        return None
    settings: dict[str, str] = {}
    for line in out.splitlines():
        key, _, value = line.strip().partition(" ")
        settings.setdefault(key.lower(), value.strip())
    # A proxy decides where the connection really goes, whatever `hostname` says.
    if any(settings.get(key, "none").lower() != "none" for key in ("proxycommand", "proxyjump")):
        return None
    return settings.get("hostname", "").lower() or None


def repo_from_url(
    url: str,
    *,
    repo_root: Path | None = None,
    budget: Budget | None = None,
    run: Runner | None = None,
    ssh: str | None = None,
) -> tuple[str | None, str]:
    """(owner/repo or None, reason) from one remote URL, with the host verified."""
    parsed = parse_remote(url)
    if parsed is None:
        return None, "unparseable"
    host, repo, via_ssh = parsed
    accepted = accepted_hosts()
    if host in accepted:
        return repo, "remote"
    if not via_ssh:
        return None, "unverified-host"
    ssh = ssh or absolute_tool("ssh", repo_root)
    if not ssh:
        return None, "ssh-unavailable"
    real = _ssh_hostname(host, ssh, run or _default_runner(budget))
    if real is None:
        return None, "ssh-unavailable"
    if real not in accepted:
        return None, "unverified-host"
    return repo, "remote-alias"


def resolve_repo(
    root: Path,
    record_repo: str | None = None,
    budget: Budget | None = None,
    *,
    git: str | None = None,
    gh: str | None = None,
    run: Runner | None = None,
    remote: str = "origin",
) -> tuple[str | None, str]:
    """(owner/repo or None, reason) for the repository at `root`.

    Order: a frozen `record_repo`; else the verified `origin` URL, cross-checked with
    `gh repo view` when `gh` answers. Callers treat None as `cannot-verify`.
    """
    if record_repo:
        return (record_repo, "record") if REPO_PATH_RE.match(record_repo) else (None, "unparseable")
    run = run or _default_runner(budget)
    git = git or absolute_tool("git", root)
    if not git:
        return None, "git-unavailable"
    rc, url = run([git, "-C", str(root), "remote", "get-url", remote], None)
    if rc != 0 or not url.strip():
        return None, "no-remote"
    repo, reason = repo_from_url(url.strip(), repo_root=root, run=run)
    if repo is None:
        return None, reason
    gh = gh if gh is not None else absolute_tool("gh", root)
    if not gh:
        return repo, reason
    rc, answer = run([gh, "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], root)
    answer = answer.strip()
    if rc != 0 or not answer:
        return repo, reason
    if answer.lower() != repo.lower():
        return None, "gh-disagrees"
    return repo, reason + "+gh"
