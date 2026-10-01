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

`verify_push_route` answers whether a push would really reach the verified host
(v4.13.5 WN-2 and WN-3): any git transport override that can redirect the push
makes it `cannot-verify`, SSH hosts are resolved with the ssh git itself runs,
and a push remote other than the verified one for the source branch is `unmet`.

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
HTTPS_RE = re.compile(r"^https://(?:(?P<user>[^@/\s]+)@)?(?P<host>[^/:\s]+)(?::(?P<port>\d+))?/(?P<path>\S+)$", re.IGNORECASE)
SSH_URL_RE = re.compile(r"^ssh://(?:(?P<user>[^@/\s]+)@)?(?P<host>[^/:\s]+)(?::(?P<port>\d+))?/(?P<path>\S+)$", re.IGNORECASE)
SCP_RE = re.compile(r"^(?:(?P<user>[^@/:\s]+)@)?(?P<host>[^/:\s]+):(?P<path>[^/\s][^\s]*)$")
ALIAS_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class Budget(Protocol):
    def remaining(self) -> float:
        """Seconds left in the caller's shared time budget."""


# --------------------------------------------------------------------------- tools


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


# Windows batch files run through cmd.exe, which re-parses every argument: a branch
# named `feat/x&mkdir,pwned` becomes a second command. Tools must resolve to a real
# executable, so a `.cmd` or `.bat` on PATH is skipped (the search continues past it).
BATCH_EXTENSIONS = (".bat", ".cmd")


def _which_on_path(name: str) -> str | None:
    """Find `name` on PATH's absolute entries only, never in the current directory.

    `shutil.which` on Windows searches the current directory first even when given an
    explicit path, so a `git.bat` planted at a repository root would run before the
    inside-the-tree refusal could see it. Batch files are never returned.
    """
    exts = [""]
    if os.name == "nt":
        exts = [e.lower() for e in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if e]
        exts = [e for e in exts if e not in BATCH_EXTENSIONS]
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


def _match_remote(url: str) -> tuple[re.Match[str], bool] | None:
    url = url.strip()
    # `#`, `?`, and `\` end or confuse an authority, so a regex would read a host git never contacts.
    if not url or any(c.isspace() for c in url) or any(c in url for c in "#?\\"):
        return None
    # `<transport>::<address>` hands the push to a `git-remote-<transport>` helper,
    # which may connect anywhere, so no host in the address can be trusted.
    if "::" in url:
        return None
    for pattern, via_ssh in ((HTTPS_RE, False), (SSH_URL_RE, True)):
        match = pattern.match(url)
        if match:
            return match, via_ssh
    if "://" in url:
        return None
    match = SCP_RE.match(url)
    # git reads `C:owner/repo` as a drive-relative local path on Windows, never as ssh host `c`.
    if not match or len(match.group("host")) == 1:
        return None
    return match, True


def parse_remote(url: str) -> tuple[str, str, bool] | None:
    """(host, owner/repo, via_ssh) for a recognized remote URL, else None."""
    found = _match_remote(url)
    if found is None:
        return None
    match, via_ssh = found
    path = REPO_PATH_RE.match(match.group("path"))
    if not path:
        return None
    return match.group("host").lower(), path.group("repo"), via_ssh


def ssh_target(url: str) -> tuple[str | None, str | None] | None:
    """(user, port) git passes to ssh for an SSH remote, or None when not an SSH URL."""
    found = _match_remote(url)
    if found is None or not found[1]:
        return None
    groups = found[0].groupdict()
    return groups.get("user"), groups.get("port")


def _ssh_settings(host: str, ssh: str, run: Runner, user: str | None, port: str | None) -> dict[str, str] | None:
    """`ssh -G` settings for exactly the target git connects to: `[-p port] [user@]host`.

    A `Match user` or `Match host ... user` block applies only with the user git
    sends, so probing the bare host would read a different configuration.
    """
    if not ALIAS_RE.match(host) or host.startswith("-"):
        return None
    if user is not None and (not ALIAS_RE.match(user) or user.startswith("-")):
        return None
    if port is not None and not port.isdigit():
        return None
    argv = [ssh, "-G", *(["-p", port] if port else []), f"{user}@{host}" if user else host]
    rc, out = run(argv, None)
    if rc != 0:
        return None
    settings: dict[str, str] = {}
    for line in out.splitlines():
        key, _, value = line.strip().partition(" ")
        settings.setdefault(key.lower(), value.strip())
    return settings


def _ssh_hostname(
    alias: str, ssh: str, run: Runner, user: str | None = None, port: str | None = None
) -> str | None:
    settings = _ssh_settings(alias, ssh, run, user, port)
    if settings is None:
        return None
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
    git: str | None = None,
) -> tuple[str | None, str]:
    """(owner/repo or None, reason) from one remote URL, with the host verified.

    With `git`, an SSH alias is resolved with the ssh that git itself runs
    (`git_ssh`); without it, with the explicit `ssh` or the one on PATH. The probe
    carries the URL's user and port, as git's own ssh command line does.
    """
    parsed = parse_remote(url)
    if parsed is None:
        return None, "unparseable"
    host, repo, via_ssh = parsed
    accepted = accepted_hosts()
    if host in accepted:
        return repo, "remote"
    if not via_ssh:
        return None, "unverified-host"
    runner = run or _default_runner(budget)
    if not ssh and git and repo_root is not None:
        ssh = git_ssh(repo_root, git=git, run=runner)
        if not ssh:
            return None, "ssh-undetermined"
    ssh = ssh or absolute_tool("ssh", repo_root)
    if not ssh:
        return None, "ssh-unavailable"
    user, port = ssh_target(url) or (None, None)
    real = _ssh_hostname(host, ssh, runner, user, port)
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


# --------------------------------------------------------------------------- push route

# Environment variables that change where or how git connects (v4.13.5 WN-2).
SSH_ENV = ("GIT_SSH", "GIT_SSH_COMMAND")
# Weaken or replace TLS verification for an HTTPS push. A proxy alone is not listed:
# with verification intact, a CONNECT proxy cannot present github.com's certificate,
# so it can refuse or delay the push but cannot send it to another host.
TLS_ENV = ("GIT_SSL_NO_VERIFY", "GIT_SSL_CAINFO", "GIT_SSL_CAPATH", "SSL_CERT_FILE", "SSL_CERT_DIR", "CURL_CA_BUNDLE")
# Config injected through the environment reaches the push, though the checker's
# own git calls strip it; GIT_EXEC_PATH replaces the transport programs themselves.
CONFIG_ENV = ("GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT")
EXEC_ENV = ("GIT_EXEC_PATH",)
# Scopes a user-level process can write. System config needs administrator rights,
# and Git for Windows' installer sets `http.sslcainfo` there by default.
WRITABLE_SCOPES = {"global", "local", "worktree", "command"}
FALSE_VALUES = {"false", "no", "off", "0"}
# Every config key that can redirect a push, matched on the lowercased key. The
# filter runs here, not in `git config --get-regexp`: a `git.cmd` wrapper passes its
# arguments through cmd.exe, which reads `|` and `^` in a pattern as shell syntax.
_ROUTE_KEY_RE = re.compile(
    r"^(core\.sshcommand|https?\..*curloptresolve|https?\..*sslverify|https?\..*sslcainfo"
    r"|https?\..*sslcapath|url\..*\.(push)?insteadof|remote\..*\.vcs)$"
)
# Print the `ssh` git's own shell resolves: git spawns ssh with the same PATH it
# gives an alias, so this is the ssh a push runs. Neither alias carries a shell
# metacharacter, for the same cmd.exe reason; `cygpath` turns an MSYS answer into
# a Windows path in a second call.
_WHICH_SSH_ALIAS = "alias.nexus-which-ssh=!command -v ssh"
_WIN_PATH_ALIAS = "alias.nexus-win-path=!cygpath -w"


def git_ssh(root: Path, *, git: str, run: Runner) -> str | None:
    """The ssh executable git itself would run for a push from `root`, or None.

    None when it cannot be determined or lives inside the working tree. A
    GIT_SSH / GIT_SSH_COMMAND / core.sshCommand override is reported separately
    by `transport_overrides`. On Windows an extensionless answer (a POSIX script
    beside a `.cmd` or `.exe` launcher) maps to its runnable sibling.
    """
    rc, out = run([git, "-C", str(root), "-c", _WHICH_SSH_ALIAS, "nexus-which-ssh"], None)
    lines = [line.strip() for line in out.splitlines() if line.strip()] if rc == 0 else []
    if not lines:
        return None
    answer = lines[-1]
    if os.name == "nt" and answer.startswith("/"):
        rc, out = run([git, "-C", str(root), "-c", _WIN_PATH_ALIAS, "nexus-win-path", answer], None)
        lines = [line.strip() for line in out.splitlines() if line.strip()] if rc == 0 else []
        if not lines:
            return None
        answer = lines[-1]
    found = Path(answer)
    if not found.is_absolute():
        return None
    if os.name == "nt" and not found.suffix:
        exts = [e.lower() for e in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if e]
        runnable = [found.with_name(found.name + ext) for ext in exts]
        found = next((c for c in runnable if c.is_file()), found)
        if not found.suffix:
            return None
    if not found.is_file() or _is_inside(found, root):
        return None
    return str(found)


def effective_push_remote(root: Path, branch: str, *, git: str, run: Runner) -> str | None:
    """The remote a plain `git push` from `branch` uses, or None when unreadable.

    git's order: `branch.<b>.pushRemote`, `remote.pushDefault`, `branch.<b>.remote`,
    then `origin` (v4.13.5 WN-3).
    """
    for key in (f"branch.{branch}.pushRemote", "remote.pushDefault", f"branch.{branch}.remote"):
        rc, out = run([git, "-C", str(root), "config", "--get", key], None)
        if rc == 0 and out.strip():
            return out.strip()
        if rc != 1:
            return None
    return "origin"


def _config_entries(root: Path, *, git: str, run: Runner) -> list[tuple[str, str, str]] | None:
    """[(scope, lowercased key, value)] for every config entry, or None when unreadable.

    `--show-scope --null` prints `scope NUL key LF value NUL` per entry. A git too old
    for `--show-scope` falls back to `--null --list` with every entry treated as
    user-writable, which only ever reports more overrides.
    """
    rc, out = run([git, "-C", str(root), "config", "--show-scope", "--null", "--list"], None)
    scoped = rc == 0
    if not scoped:
        rc, out = run([git, "-C", str(root), "config", "--null", "--list"], None)
        if rc != 0:
            return None
    tokens = out.split("\0")
    entries: list[tuple[str, str, str]] = []
    step = 2 if scoped else 1
    for index in range(0, len(tokens) - step + 1, step):
        scope = tokens[index] if scoped else "local"
        key, _, value = tokens[index + step - 1].strip("\n").partition("\n")
        if key.strip():
            entries.append((scope.strip(), key.strip().lower(), value.strip()))
    return entries


def transport_overrides(
    root: Path,
    url: str,
    *,
    git: str,
    run: Runner,
    environ: dict[str, str] | None = None,
    remote: str = "origin",
) -> tuple[list[str], list[str]] | None:
    """(fixed override ids, raw remote URLs an insteadOf rule rewrites); None when unreadable.

    ids: `ssh-command`, `tls-verification`, `curlopt-resolve`, `remote-helper`,
    `config-env`, `exec-path`. Transport-specific ids apply only to their transport:
    an ssh push ignores TLS settings, an https push ignores an ssh command. A
    rewritten raw URL is an override only when it names a different verified
    repository from the effective push URL, which `verify_push_route` decides.
    """
    parsed = parse_remote(url)
    if parsed is None or not re.match(r"^[A-Za-z0-9_.-]+$", remote):
        return None
    via_ssh = parsed[2]
    env = os.environ if environ is None else environ
    found: set[str] = set()
    if any(env.get(name) for name in CONFIG_ENV):
        found.add("config-env")
    if any(env.get(name) for name in EXEC_ENV):
        found.add("exec-path")
    if via_ssh and any(env.get(name) for name in SSH_ENV):
        found.add("ssh-command")
    if not via_ssh and any(env.get(name) for name in TLS_ENV):
        found.add("tls-verification")
    entries = _config_entries(root, git=git, run=run)
    if entries is None:
        return None
    raw_urls = {url}
    rewrites: list[str] = []
    for scope, key, value in entries:
        if key in (f"remote.{remote.lower()}.url", f"remote.{remote.lower()}.pushurl"):
            raw_urls.add(value)
            continue
        if not _ROUTE_KEY_RE.match(key):
            continue
        if key.startswith("url.") and key.endswith("insteadof"):
            if value:
                rewrites.append(value)
        elif key.endswith(".vcs"):
            # git pushes through `git-remote-<vcs>`, a helper that may connect anywhere.
            if key == f"remote.{remote.lower()}.vcs" and value:
                found.add("remote-helper")
        elif not value:
            continue  # an empty value disables the setting
        elif key == "core.sshcommand" and via_ssh:
            found.add("ssh-command")
        elif via_ssh:
            continue  # the remaining keys configure the HTTP transport only
        elif key.endswith("curloptresolve"):
            found.add("curlopt-resolve")
        elif key.endswith("sslverify"):
            if value.lower() in FALSE_VALUES:
                found.add("tls-verification")
        elif key.endswith(("sslcainfo", "sslcapath")) and scope in WRITABLE_SCOPES:
            found.add("tls-verification")
    rewritten = sorted(raw for raw in raw_urls if any(raw.startswith(p) for p in rewrites))
    return sorted(found), rewritten


def _ssh_route_ok(host: str, ssh: str, run: Runner, user: str | None = None, port: str | None = None) -> bool:
    """True when ssh config sends a literal accepted host to itself, with no proxy."""
    settings = _ssh_settings(host, ssh, run, user, port)
    if settings is None:
        return False
    if any(settings.get(key, "none").lower() != "none" for key in ("proxycommand", "proxyjump")):
        return False
    return settings.get("hostname", "").lower() == host


def verify_push_route(
    root: Path,
    url: str,
    *,
    git: str,
    run: Runner,
    branch: str,
    expected_remote: str = "origin",
    environ: dict[str, str] | None = None,
) -> tuple[str, str | None, str]:
    """(status, owner/repo or None, fixed reason id) for a push of `branch` to `url`.

    `url` is the effective push URL (`git remote get-url --push`, rewrites applied).
    `met` only when the effective push remote is `expected_remote`, no transport
    override applies, and the host is verified with git's own ssh, probed with the
    URL's user and port. `unmet` for another push remote or an unverified host.
    `cannot-verify` for an override or anything that cannot be determined.
    """
    remote = effective_push_remote(root, branch, git=git, run=run)
    if remote is None:
        return "cannot-verify", None, "push-remote-unreadable"
    if remote != expected_remote:
        return "unmet", None, "push-remote-not-verified-remote"
    scanned = transport_overrides(root, url, git=git, run=run, environ=environ, remote=expected_remote)
    if scanned is None:
        return "cannot-verify", None, "transport-unreadable"
    overrides, rewritten = scanned
    if overrides:
        return "cannot-verify", None, "transport-override-" + overrides[0]
    parsed = parse_remote(url)
    if parsed is None:
        return "unmet", None, "unparseable"
    host, _repo, via_ssh = parsed
    ssh = None
    if via_ssh:
        ssh = git_ssh(root, git=git, run=run)
        if not ssh:
            return "cannot-verify", None, "ssh-undetermined"
        user, port = ssh_target(url) or (None, None)
        if host in accepted_hosts() and not _ssh_route_ok(host, ssh, run, user, port):
            return "cannot-verify", None, "transport-override-ssh-config-host"
    repo, reason = repo_from_url(url, repo_root=root, run=run, ssh=ssh)
    if repo is None:
        return "unmet", None, reason
    for raw in rewritten:
        # git already applied the rewrite to `url`; it only matters when the configured
        # URL names another repository, so an approval of one would push to the other.
        raw_repo, _raw_reason = repo_from_url(raw, repo_root=root, run=run, git=git)
        if raw_repo and raw_repo.lower() != repo.lower():
            return "cannot-verify", None, "transport-override-url-rewrite"
    return "met", repo, reason
