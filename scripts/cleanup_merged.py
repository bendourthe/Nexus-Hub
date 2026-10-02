#!/usr/bin/env python3
"""Remove branches and worktrees that are verifiably merged and idle; report the rest.

Installed at ~/.nexus-hub/scripts/cleanup_merged.py beside check_plan_completion.py.
Dry-run by default: nothing is removed without `--apply`.

    cleanup_merged.py [--dry-run | --apply] [--integration-branch develop]
                      [--idle-hours 24] [--json] [--repo PATH]
                      [--plan PLAN | --minor vX.Y] [--session ID] [--receipt]

One line per item: `REMOVE <item>` or `KEEP <item> <check>` (a failed removal is
`KEEP <item> removal-failed <reason>`), where `<item>` is `worktree:<path>`,
`branch:<name>`, or `remote:<remote>/<name>`. The check id is always the last token
(the last two for `removal-failed`); `--json` is the exact form.

The seven checks and why each exists are recorded in
docs/decisions/proposed/policy/2026-09-28-verified-merged-and-idle-cleanup.md. Every
check must pass, is evaluated per item, and is re-read immediately before that item
is removed. Removal never uses `branch -D`, a bare `--force`, or
`worktree remove --force`: a worktree goes through `git worktree remove` and
`git worktree prune`, a local branch through `git update-ref -d <ref> <sha>` (which
succeeds only while the ref still equals the merged head, so a squash merge is
handled without forcing), and a remote branch through
`git push --force-with-lease=<ref>:<sha> <remote> --delete <ref>`, which the server
refuses when the tip moved. A gitignored file outside ALLOWED_IGNORED keeps its
worktree, because `git worktree remove` deletes ignored files with the tree.

`--receipt` (with `--apply` and the run's `--plan` or `--minor`) writes the final-pass
receipt beside the run record, sealed under the runs secret; the completion
contract's `cleanup.merged` predicate reads it through `receipt_status`. The
receipt is written only when the record carries the `cleanup-merged` approval and is
bound to the caller's `--session`. Naming a `--plan` or `--minor` exempts its record
from the owned-by-run check only when that record is the calling session's own
verified record; another session's run keeps every item it owns.

Exit codes: 0 done (items may be kept), 1 at least one removal failed, 2 usage or
not a git repository, 3 blocked (another cleanup holds the lock, or the record does
not cover `--receipt`). Output never carries git or gh text: only item names and
fixed ids.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import hmac
import json
import math
import os
import re
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

# On Windows, a console program started by a process with no console of its own
# (a hook or agent launched without one, or a detached test) opens a visible
# window that takes keyboard focus. Every child here has its output captured and
# its prompts disabled, so it never needs a window.
NO_WINDOW: dict = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
from types import ModuleType

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import repo_host

EXIT_OK, EXIT_PARTIAL, EXIT_USAGE, EXIT_BLOCKED = 0, 1, 2, 3
CALL_TIMEOUT_SECONDS = 30.0
LOCK_STALE_SECONDS = 3600.0
PR_LIMIT = 1000
STATIC_PROTECTED = {"main", "master", "develop", "HEAD"}
MIN_IDLE_HOURS = 24.0
ALLOWED_IGNORED = ("node_modules", "__pycache__", ".venv", ".pytest_cache", "dist", "build")
# Inside an allowlisted directory these names keep the worktree: a safety net, not a guarantee.
SENSITIVE_NAMES = (".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "id_rsa*", "id_ed25519*",
                   "*.kdbx", "credentials*", "secrets*")
# A ref name carrying a shell metacharacter is never passed to any tool.
UNSAFE_NAME_CHARS = set('&|<>^%!"`;')
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
RECEIPT_KIND = "cleanup-merged-receipt"
RECEIPT_SUFFIX = ".cleanup-receipt.json"
_RECEIPT_DOMAIN = b"nexus-hub cleanup-merged receipt\n"
_REFLOG_TIME_RE = re.compile(r"@\{(\d+)\}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")

# Stable check ids, in evaluation order; the first that fails is reported.
CHECK_IDS = (
    "unsafe-name",         # the ref name holds one of & | < > ^ % ! " ` ; and is never passed to a tool
    "records-unreadable",  # a run record under ~/.nexus-hub/runs/ could not be read, so ownership is unknown
    "protected",           # main, master, develop, the integration or default branch, or GitHub-protected
    "gh-unavailable",      # gh missing, unauthenticated, offline, truncated, or no verified repository
    "remote-unreadable",   # `git ls-remote` on the verified remote failed
    "remote-mismatch",     # the remote is not the verified one, or its push route is not `met`
    "open-pr",             # an OPEN pull request uses the branch as head
    "no-merged-pr",        # no MERGED same-repository pull request has this head branch
    "merged-elsewhere",    # merged, but not into the integration branch or the default branch
    "detached",            # a worktree with no branch checked out
    "local-ahead",         # the local tip descends from the merged head
    "head-mismatch",       # a local or remote tip differs from every merged head
    "checked-out",         # the branch is checked out in a worktree that stays (local and remote items)
    "current-worktree",    # the worktree this command runs in, or the one holding the process's cwd
    "missing",             # the worktree directory is gone or prunable
    "locked",              # `git worktree lock` holds the worktree
    "status-unreadable",   # `git status`, `git ls-files`, or the directory walk failed in the worktree
    "dirty",               # tracked modifications in the worktree
    "hidden-changes",      # an assume-unchanged, skip-worktree, or unmerged index entry (`git ls-files -v`)
    "untracked",           # untracked files in the worktree
    "ignored-not-allowlisted",  # an ignored entry that is not an allowlisted directory
    "contains-worktree",   # another worktree, a nested `.git`, or a submodule checkout inside it
    "link-present",        # a symlink, junction, or other reparse point anywhere in the tree
    "sensitive-ignored",   # a secret-like file name inside an allowlisted directory
    "owned-by-run",        # a live run record or runner lock on this machine names it
    "recently-active",     # a reflog entry, file change, or push within the idle window
    "idle-unknown",        # a reflog or the remote push time could not be read
    "in-use",              # (removal only) the worktree directory could not be renamed, so a handle holds it
)
# A check that says nothing about the item, only that the pass could not see: no receipt.
GLOBAL_UNKNOWN = {"gh-unavailable", "remote-unreadable", "records-unreadable"}
REMOVAL_FAILED = "removal-failed"

Runner = Callable[[list[str], Path | None], tuple[int, str, str]]


def _exec(argv: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run one command; (rc, stdout, stderr). rc -1 means it did not run in time."""
    env = dict(os.environ, GH_PROMPT_DISABLED="1", GIT_TERMINAL_PROMPT="0", NO_COLOR="1",
               GH_NO_UPDATE_NOTIFIER="1", GIT_PAGER="cat")
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_EXEC_PATH",
                 "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT", "GIT_NAMESPACE"):
        env.pop(name, None)
    try:
        proc = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, check=False,
                              encoding="utf-8", errors="replace", timeout=CALL_TIMEOUT_SECONDS,
                              **NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return -1, "", ""
    return proc.returncode, proc.stdout, proc.stderr


def _checker() -> ModuleType:
    import check_plan_completion  # a sibling; imported lazily because it imports this module

    return check_plan_completion


# --------------------------------------------------------------------------- model


@dataclass(frozen=True)
class Item:
    kind: str  # "worktree" | "branch" | "remote"
    name: str  # the branch name; for a worktree, its checked-out branch or ""
    remote: str = ""
    path: str = ""

    def label(self) -> str:
        if self.kind == "worktree":
            return "worktree:" + _CONTROL_RE.sub("?", self.path)
        if self.kind == "remote":
            return f"remote:{self.remote}/{self.name}"
        return "branch:" + self.name

    def as_dict(self) -> dict:
        return {"kind": self.kind, "name": self.name, "remote": self.remote, "path": self.path}


@dataclass
class Verdict:
    item: Item
    action: str  # "REMOVE" | "KEEP"
    check: str = ""
    sha: str = ""  # the merged head a REMOVE was verified against
    reason: str = ""
    partial: list[str] = field(default_factory=list)

    def line(self) -> str:
        if self.action == "REMOVE":
            return f"REMOVE {self.item.label()}"
        tail = f" {self.reason}" if self.reason else ""
        return f"KEEP {self.item.label()} {self.check}{tail}"

    def as_dict(self) -> dict:
        return {"item": self.item.label(), **self.item.as_dict(), "action": self.action,
                "check": self.check or None, "reason": self.reason or None, "partial": self.partial}


@dataclass
class Worktree:
    path: str
    head: str
    branch: str | None
    locked: bool
    prunable: bool


@dataclass
class State:
    """One read of every fact the checks use."""

    local: dict[str, str]
    worktrees: list[Worktree]
    remote_heads: dict[str, str] | None  # the verified remote's live heads; None when unreadable
    tracking: dict[str, dict[str, str]]  # other remotes' remote-tracking refs (listing only)
    prs: dict[str, list[dict]] | None
    protected: set[str] | None
    owned_branches: set[str]
    owned_paths: set[str]
    records_ok: bool = True


# --------------------------------------------------------------------------- host


class Host:
    """The repository and its tools, resolved once, outside the working tree."""

    def __init__(self, start: Path, integration: str, run: Runner | None = None) -> None:
        self.run = run or _exec
        self.notices: list[str] = []
        self.integration = integration
        git = repo_host.absolute_tool("git", None)
        if not git:
            raise RuntimeError("git not found")
        rc, out, _ = self.run([git, "-C", str(start), "rev-parse", "--show-toplevel"], None)
        if rc != 0:
            raise RuntimeError("not inside a git repository")
        self.current = Path(out.strip()).resolve()
        self.git = repo_host.absolute_tool("git", self.current)
        if not self.git:
            raise RuntimeError("git resolves inside the working tree; refusing")
        self.gh = repo_host.absolute_tool("gh", self.current)
        self.root = self._main_worktree() or self.current
        self.remote = "origin"
        self.repo, reason = repo_host.resolve_repo(
            self.root, git=self.git, gh=self.gh or "", run=self.run2, remote=self.remote
        )
        if self.repo is None:
            self.notices.append("repository-unverified: " + reason)
        self.default_branch: str | None = None

    def run2(self, argv: list[str], cwd: Path | None = None) -> tuple[int, str]:
        rc, out, _ = self.run(argv, cwd)
        return rc, out

    def g(self, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
        return self.run([self.git, "-C", str(cwd or self.root), *args], None)

    def _main_worktree(self) -> Path | None:
        rc, out, _ = self.run([self.git, "-C", str(self.current), "worktree", "list", "--porcelain", "-z"], None)
        first = out.split("\0", 1)[0] if rc == 0 else ""
        return Path(first[len("worktree "):]).resolve() if first.startswith("worktree ") else None

    def gh_json(self, *args: str) -> object | None:
        if not self.gh or not self.repo:
            return None
        rc, out, _ = self.run([self.gh, *args], self.root)
        if rc != 0:
            return None
        return _parse_json_stream(out)


def _parse_json_stream(text: str) -> object | None:
    """One JSON value, or the concatenated arrays `gh api --paginate` prints."""
    decoder = json.JSONDecoder()
    values: list[object] = []
    index, text = 0, text.strip()
    try:
        while index < len(text):
            value, index = decoder.raw_decode(text, index)
            values.append(value)
            while index < len(text) and text[index].isspace():
                index += 1
    except ValueError:
        return None
    if len(values) == 1:
        return values[0]
    if values and all(isinstance(v, list) for v in values):
        return [entry for v in values for entry in v]  # type: ignore[union-attr]
    return None


# --------------------------------------------------------------------------- reading state


def list_worktrees(host: Host) -> list[Worktree]:
    rc, out, _ = host.g("worktree", "list", "--porcelain", "-z")
    if rc != 0:
        raise RuntimeError("git worktree list failed")
    found: list[Worktree] = []
    for block in out.split("\0\0"):
        fields = [f for f in block.split("\0") if f]
        if not fields or not fields[0].startswith("worktree "):
            continue
        attrs = {f.split(" ", 1)[0]: (f.split(" ", 1)[1] if " " in f else "") for f in fields[1:]}
        branch = attrs.get("branch", "")
        found.append(Worktree(
            path=fields[0][len("worktree "):],
            head=attrs.get("HEAD", ""),
            branch=branch.removeprefix("refs/heads/") if branch.startswith("refs/heads/") else None,
            locked="locked" in attrs,
            prunable="prunable" in attrs,
        ))
    return found


def _refs(host: Host, prefix: str) -> dict[str, str]:
    rc, out, _ = host.g("for-each-ref", "--format=%(objectname) %(refname)", prefix)
    refs: dict[str, str] = {}
    for line in out.splitlines() if rc == 0 else []:
        sha, _, ref = line.partition(" ")
        if ref.startswith(prefix):
            refs[ref[len(prefix):]] = sha
    return refs


def _remote_heads(host: Host) -> dict[str, str] | None:
    rc, out, _ = host.g("ls-remote", "--heads", host.remote)
    if rc != 0:
        return None
    heads: dict[str, str] = {}
    for line in out.splitlines():
        sha, _, ref = line.partition("\t")
        if ref.startswith("refs/heads/"):
            heads[ref[len("refs/heads/"):]] = sha
    return heads


def _other_remotes(host: Host) -> dict[str, dict[str, str]]:
    rc, out, _ = host.g("remote")
    names = [n.strip() for n in out.splitlines() if n.strip()] if rc == 0 else []
    tracking: dict[str, dict[str, str]] = {}
    for name in names:
        if name == host.remote:
            continue
        refs = {k: v for k, v in _refs(host, f"refs/remotes/{name}/").items() if k != "HEAD"}
        if refs:
            tracking[name] = refs
    return tracking


def _pull_requests(host: Host, branch: str | None, names: Iterable[str] = ()) -> dict[str, list[dict]] | None:
    """Pull requests grouped by head branch; None when any answer is unknown or truncated.

    The bulk query (no `branch`) lists open and merged pull requests once. A
    repository with `PR_LIMIT` or more of either would truncate it, so a full
    page falls back to one `--head=<name>` query per candidate branch in
    `names`, the same query the pre-removal re-read uses, rather than leaving
    every item unknown for good.
    """
    fields = "number,headRefName,headRefOid,baseRefName,isCrossRepository,state"
    queries = [["--state", "all", "--head=" + branch]] if branch else [["--state", "open"], ["--state", "merged"]]
    grouped: dict[str, list[dict]] = {}
    for query in queries:
        data = host.gh_json("pr", "list", "--repo", str(host.repo), *query,
                            "--limit", str(PR_LIMIT), "--json", fields)
        if not isinstance(data, list):
            return None
        if len(data) >= PR_LIMIT:
            if branch:
                return None
            return _pull_requests_per_branch(host, names)
        for pr in data:
            if isinstance(pr, dict) and isinstance(pr.get("headRefName"), str):
                grouped.setdefault(pr["headRefName"], []).append(pr)
    return grouped


def _pull_requests_per_branch(host: Host, names: Iterable[str]) -> dict[str, list[dict]] | None:
    grouped: dict[str, list[dict]] = {}
    for name in sorted(set(names)):
        one = _pull_requests(host, name)
        if one is None:
            return None
        for head, prs in one.items():
            grouped.setdefault(head, []).extend(prs)
    return grouped


def _protected(host: Host) -> set[str] | None:
    meta = host.gh_json("api", f"repos/{host.repo}")
    branches = host.gh_json("api", "--paginate", "-X", "GET", f"repos/{host.repo}/branches",
                            "-f", "protected=true", "-f", "per_page=100")
    if not isinstance(meta, dict) or not isinstance(branches, list):
        return None
    names = {str(b.get("name")) for b in branches if isinstance(b, dict) and b.get("name")}
    default = meta.get("default_branch")
    if isinstance(default, str) and default:
        host.default_branch = default
        names.add(default)
    return names


def _norm(path: str | Path) -> str:
    resolved = str(Path(path).resolve())
    return resolved.casefold() if os.name == "nt" else resolved


def _collect_names(value: object, key: str, branches: set[str], paths: set[str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            _collect_names(v, k, branches, paths)
    elif isinstance(value, list):
        for v in value:
            _collect_names(v, key, branches, paths)
    elif isinstance(value, str) and value:
        if key in ("source_branch", "branches"):
            branches.add(value)
        elif key in ("worktree", "worktrees", "repo_root"):
            paths.add(_norm(value))


def _record_live(ck: ModuleType, record: dict, path: Path) -> bool:
    if ck.lock_live(path):
        return True
    # A run's record protects its branches until the run is stamped complete;
    # there is no expiry (completion contract, "Run record lifetime").
    return not record.get("completed")


def owned_names(host: Host, worktrees: list[Worktree], own: Path | None) -> tuple[set[str], set[str], bool]:
    """(branches, worktree paths, every record readable) for live run records of this repository.

    An unreadable record could name anything, so it makes ownership unknown for every item.
    """
    ck = _checker()
    runs = ck._runs_dir()
    ours = {_norm(host.root), *(_norm(w.path) for w in worktrees)}
    branches: set[str] = set()
    paths: set[str] = set()
    readable = True
    for path in sorted(runs.glob("*.json")) if runs.is_dir() else []:
        if path.name.endswith((".gate.json", RECEIPT_SUFFIX)):
            continue
        if own is not None and _norm(path) == _norm(own):
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            record = None
        if not isinstance(record, dict):
            host.notices.append("unreadable-run-record")
            readable = False
            continue
        root = record.get("repo_root")
        same_repo = bool(host.repo) and str(record.get("repo", "")).lower() == str(host.repo).lower()
        if not (same_repo or (isinstance(root, str) and _norm(root) in ours)):
            continue
        if _record_live(ck, record, path):
            _collect_names(record, "", branches, paths)
    return branches, paths, readable


def read_state(host: Host, own: Path | None, pr_branch: str | None = None) -> State:
    worktrees = list_worktrees(host)
    local = _refs(host, "refs/heads/")
    remote_heads = _remote_heads(host)
    tracking = _other_remotes(host)
    prs = protected = None
    if host.repo:
        names = {*local, *(remote_heads or {}), *(w.branch for w in worktrees if w.branch)}
        for refs in tracking.values():
            names.update(refs)
        prs = _pull_requests(host, pr_branch, names)
        protected = _protected(host)
    owned_b, owned_p, records_ok = owned_names(host, worktrees, own)
    return State(
        local=local,
        worktrees=worktrees,
        remote_heads=remote_heads,
        tracking=tracking,
        prs=prs,
        protected=protected,
        owned_branches=owned_b,
        owned_paths=owned_p,
        records_ok=records_ok,
    )


def enumerate_items(host: Host, st: State) -> list[Item]:
    """Worktrees first, then local branches, then remote branches: the removal order."""
    items = [Item("worktree", w.branch or "", path=w.path) for w in st.worktrees[1:]]
    items += [Item("branch", name) for name in sorted(st.local)]
    items += [Item("remote", name, remote=host.remote) for name in sorted(st.remote_heads or {})]
    for remote, refs in sorted(st.tracking.items()):
        items += [Item("remote", name, remote=remote) for name in sorted(refs)]
    return items


# --------------------------------------------------------------------------- checks


def _hosting_check(host: Host, st: State, item: Item, tips: list[str], local_tip: str | None) -> tuple[str, str]:
    """(first failed hosting check or "", the merged head every tip equals)."""
    name = item.name
    if name in STATIC_PROTECTED or name == host.integration:
        return "protected", ""
    if item.kind == "remote" and item.remote != host.remote:
        return "remote-mismatch", ""
    if st.prs is None or st.protected is None:
        return "gh-unavailable", ""
    if name in st.protected:
        return "protected", ""
    if st.remote_heads is None:
        return "remote-unreadable", ""
    prs = st.prs.get(name, [])
    if any(pr.get("state") == "OPEN" for pr in prs):
        return "open-pr", ""
    merged = [pr for pr in prs if pr.get("state") == "MERGED" and not pr.get("isCrossRepository")]
    if not merged:
        return "no-merged-pr", ""
    bases = {host.integration, host.default_branch} - {None, ""}
    merged = [pr for pr in merged if pr.get("baseRefName") in bases]
    if not merged:
        return "merged-elsewhere", ""
    heads = [str(pr.get("headRefOid") or "") for pr in merged]
    match = next((h for h in heads if h and all(t == h for t in tips)), "")
    if match:
        return "", match
    if local_tip and any(h and h != local_tip and _is_ancestor(host, h, local_tip) for h in heads):
        return "local-ahead", ""
    return "head-mismatch", ""


def _is_ancestor(host: Host, older: str, newer: str) -> bool:
    rc, _, _ = host.g("merge-base", "--is-ancestor", older, newer)
    return rc == 0


def _tips(host: Host, st: State, item: Item, wt: Worktree | None) -> tuple[list[str], str | None]:
    """(every tip the merged head must equal, the local tip): worktree HEAD, local, verified remote."""
    local_tip = st.local.get(item.name)
    remote_tip = (st.remote_heads or {}).get(item.name)
    if item.kind == "remote" and item.remote != host.remote:
        remote_tip = st.tracking.get(item.remote, {}).get(item.name)
    tips: list[str] = []
    if wt is not None:
        tips.append(wt.head)
    for tip in (local_tip, remote_tip):
        if tip:
            tips.append(tip)
    return tips, local_tip


def _inside(path: str, root: str) -> bool:
    child, parent = _norm(path), _norm(root)
    return child == parent or child.startswith(parent.rstrip(os.sep) + os.sep)


def _worktree_check(host: Host, st: State, wt: Worktree) -> tuple[str, float]:
    """(first failed worktree check or "", the newest mtime found in the tree)."""
    if _inside(os.getcwd(), wt.path) or _norm(wt.path) == _norm(host.current):
        return "current-worktree", 0.0
    if wt.prunable or not Path(wt.path).is_dir():
        return "missing", 0.0
    if wt.locked:
        return "locked", 0.0
    failed = _index_check(host, wt)
    if failed:
        return failed, 0.0
    if any(_inside(other.path, wt.path) for other in st.worktrees if _norm(other.path) != _norm(wt.path)):
        return "contains-worktree", 0.0
    scan = scan_tree(wt.path)
    for flag, check in ((scan.unreadable, "status-unreadable"), (scan.nested_git, "contains-worktree"),
                        (scan.link, "link-present"), (scan.sensitive, "sensitive-ignored")):
        if flag:
            return check, scan.newest
    return "", scan.newest


def _index_check(host: Host, wt: Worktree) -> str:
    rc, out, _ = host.run([host.git, "-C", wt.path, "status", "--porcelain=v1", "-z",
                           "--untracked-files=all", "--ignored=matching"], None)
    rc_v, listing, _ = host.run([host.git, "-C", wt.path, "ls-files", "-v", "-z"], None)
    if rc != 0 or rc_v != 0:
        return "status-unreadable"
    codes = [(e[:2], e[3:]) for e in out.split("\0") if len(e) > 3]
    if any(code not in ("??", "!!") for code, _ in codes):
        return "dirty"
    # `H` is an ordinary cached entry; lowercase is assume-unchanged, `S` skip-worktree,
    # `M` unmerged: each can hide a changed file from `git status`.
    if any(entry[:1] != "H" for entry in listing.split("\0") if entry):
        return "hidden-changes"
    if any(code == "??" for code, _ in codes):
        return "untracked"
    if any(code == "!!" and not _allowlisted(p) for code, p in codes):
        return "ignored-not-allowlisted"
    return ""


def _allowlisted(path: str) -> bool:
    """True only for an ignored DIRECTORY entry (trailing `/`) whose own name is allowlisted."""
    return path.endswith("/") and path.rstrip("/").rsplit("/", 1)[-1] in ALLOWED_IGNORED


def _sensitive(name: str) -> bool:
    lowered = name.lower()
    return any(fnmatch.fnmatchcase(lowered, pattern) for pattern in SENSITIVE_NAMES)


def _is_link(entry: os.DirEntry[str]) -> bool:
    """A symlink, a junction, or any other reparse point; an unreadable entry counts as one."""
    try:
        if entry.is_symlink() or (hasattr(entry, "is_junction") and entry.is_junction()):
            return True
        attrs = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)


@dataclass
class TreeScan:
    newest: float = 0.0
    link: bool = False
    nested_git: bool = False
    sensitive: bool = False
    unreadable: bool = False


def scan_tree(root: str) -> TreeScan:
    """Walk the whole worktree, allowlisted directories included, never following a link.

    `git worktree remove` deletes everything under the tree and follows junctions, so
    a link anywhere, a nested `.git` (another worktree or a submodule), or a
    secret-like name inside an allowlisted directory keeps the worktree.
    """
    scan = TreeScan()
    top = Path(root)
    if top.is_symlink() or (hasattr(os.path, "isjunction") and os.path.isjunction(top)):
        scan.link = True
        return scan
    stack: list[tuple[str, bool]] = [(root, False)]
    while stack:
        current, allowed = stack.pop()
        try:
            with os.scandir(current) as it:
                entries = list(it)
        except OSError:
            scan.unreadable = True
            continue
        for entry in entries:
            if entry.name == ".git":
                scan.nested_git |= _norm(current) != _norm(root)
                continue
            if _is_link(entry):
                scan.link = True
                continue
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                scan.unreadable = True
                continue
            scan.newest = max(scan.newest, info.st_mtime)
            if stat.S_ISDIR(info.st_mode):
                stack.append((entry.path, allowed or entry.name in ALLOWED_IGNORED))
            elif allowed and _sensitive(entry.name):
                scan.sensitive = True
    return scan


def _owned(st: State, item: Item, wt: Worktree | None) -> bool:
    if item.name and item.name in st.owned_branches:
        return True
    return wt is not None and _norm(wt.path) in st.owned_paths


def _reflog_newest(host: Host, ref: str, cwd: str | None = None) -> float | None:
    argv = [host.git, "-C", cwd or str(host.root), "reflog", "show", "--date=unix", "--format=%gd", ref, "--"]
    rc, out, _ = host.run(argv, None)
    times = [int(m.group(1)) for m in map(_REFLOG_TIME_RE.search, out.split()) if m] if rc == 0 else []
    return float(max(times)) if times else None


def last_push(host: Host, branch: str) -> float | None:
    """The newest GitHub repository-activity timestamp for the branch ref, or None when unknown.

    `GET /repos/{owner}/{repo}/activity?ref=refs/heads/<branch>` lists pushes, force
    pushes, branch creation and deletion, newest first. Any activity counts. An
    empty list, an error, or an unparseable time is unknown, never idle.
    """
    # Fields rather than a query string, so gh encodes the ref and no `&` reaches a shell.
    data = host.gh_json("api", "-X", "GET", f"repos/{host.repo}/activity",
                        "-f", "ref=refs/heads/" + branch, "-f", "per_page=30")
    if not isinstance(data, list):
        return None
    times: list[float] = []
    for entry in data:
        stamp = entry.get("timestamp") if isinstance(entry, dict) else None
        try:
            times.append(dt.datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).timestamp())
        except ValueError:
            continue
    return max(times) if times else None


def _idle_check(host: Host, st: State, item: Item, wt: Worktree | None, idle_hours: float,
                tree_mtime: float) -> str:
    since = time.time() - idle_hours * 3600
    known: list[float] = []
    unknown = False
    if item.name in st.local:
        newest = _reflog_newest(host, "refs/heads/" + item.name)
        unknown |= newest is None
        known += [newest] if newest is not None else []
    if wt is not None:
        head_log = _reflog_newest(host, "HEAD", cwd=wt.path)
        unknown |= head_log is None
        known += [head_log] if head_log is not None else []
        known.append(tree_mtime)
    if item.name:
        pushed = last_push(host, item.name)
        unknown |= pushed is None
        known += [pushed] if pushed is not None else []
    if any(t >= since for t in known):
        return "recently-active"
    return "idle-unknown" if unknown or not item.name else ""


def evaluate(host: Host, st: State, item: Item, idle_hours: float, leaving: set[str] | None = None) -> Verdict:
    """Every check for one item, in CHECK_IDS order; the first failure is the verdict.

    `leaving` holds the worktree paths this pass will remove first, so a branch checked
    out only there is not reported `checked-out` in the dry run.
    """
    if UNSAFE_NAME_CHARS & set(item.name):
        return Verdict(item, "KEEP", "unsafe-name")
    if not st.records_ok:
        return Verdict(item, "KEEP", "records-unreadable")
    wt = next((w for w in st.worktrees if _norm(w.path) == _norm(item.path)), None) if item.kind == "worktree" else None
    if item.kind == "worktree" and wt is None:
        return Verdict(item, "KEEP", "missing")
    if wt is not None and wt.branch is None:
        return Verdict(item, "KEEP", "detached")
    tips, local_tip = _tips(host, st, item, wt)
    failed, sha = _hosting_check(host, st, item, tips, local_tip)
    if failed:
        return Verdict(item, "KEEP", failed)
    if item.kind == "remote" and not _push_route_met(host, item):
        return Verdict(item, "KEEP", "remote-mismatch")
    if item.kind in ("branch", "remote"):
        # A branch checked out in a worktree that stays is in use, locally and on the remote.
        staying = [w for w in st.worktrees if _norm(w.path) not in (leaving or set())]
        if any(w.branch == item.name for w in staying):
            return Verdict(item, "KEEP", "checked-out")
    newest = 0.0
    if wt is not None:
        failed, newest = _worktree_check(host, st, wt)
        if failed:
            return Verdict(item, "KEEP", failed)
    if _owned(st, item, wt):
        return Verdict(item, "KEEP", "owned-by-run")
    failed = _idle_check(host, st, item, wt, idle_hours, newest)
    if failed:
        return Verdict(item, "KEEP", failed)
    return Verdict(item, "REMOVE", sha=sha)


def _push_route_met(host: Host, item: Item) -> bool:
    rc, url, _ = host.g("remote", "get-url", "--push", item.remote)
    if rc != 0 or not url.strip():
        return False
    status, repo, reason = repo_host.verify_push_route(
        host.root, url.strip(), git=host.git, run=host.run2, branch=item.name, expected_remote=item.remote
    )
    if status != "met":
        host.notices.append(f"push-route {status}: {reason}")
        return False
    return bool(repo) and repo.lower() == str(host.repo).lower()


# --------------------------------------------------------------------------- removal


def remove(host: Host, verdict: Verdict) -> Verdict:
    """Remove one re-verified item; a failure becomes `KEEP removal-failed <reason>`."""
    item = verdict.item
    if item.kind == "worktree":
        held = _held_open(Path(item.path))
        if held is not None:
            return Verdict(item, "KEEP", "in-use", partial=held)
        rc, _, _ = host.g("worktree", "remove", item.path)
        if rc != 0:
            partial = [p for p, present in (("directory-present", Path(item.path).exists()),
                                            ("still-listed", _still_listed(host, item.path))) if present]
            return Verdict(item, "KEEP", REMOVAL_FAILED, reason="worktree-remove-refused", partial=partial)
        rc, _, _ = host.g("worktree", "prune")
        if rc != 0:
            return Verdict(item, "REMOVE", sha=verdict.sha, partial=["prune-failed"])
        return verdict
    ref = "refs/heads/" + item.name
    if item.kind == "branch":
        rc, _, _ = host.g("update-ref", "-d", ref, verdict.sha)
        reason = "ref-changed"
    else:
        rc, _, _ = host.g("push", f"--force-with-lease={ref}:{verdict.sha}", item.remote, "--delete", ref)
        reason = "push-refused"
    if rc != 0:
        return Verdict(item, "KEEP", REMOVAL_FAILED, reason=reason)
    return verdict


def _held_open(path: Path) -> list[str] | None:
    """On Windows, None when the directory can be renamed away and back; else the partial state.

    An open handle anywhere in the tree makes the rename fail, and a remove would then
    stop halfway. POSIX lets a directory with open files be removed, so no probe runs.
    """
    if os.name != "nt":
        return None
    probe = path.with_name(f"{path.name}.cleanup-probe-{os.getpid()}")
    try:
        os.rename(path, probe)
    except OSError:
        return []
    for _attempt in range(10):
        try:
            os.rename(probe, path)
            return None
        except OSError:
            time.sleep(0.2)
    return ["renamed-to:" + probe.name]


def _still_listed(host: Host, path: str) -> bool:
    try:
        return any(_norm(w.path) == _norm(path) for w in list_worktrees(host))
    except RuntimeError:
        return True


# --------------------------------------------------------------------------- lock and receipt


def _lock_path(host: Host) -> Path:
    digest = hashlib.sha256(str(host.root).encode("utf-8")).hexdigest()[:16]
    return _checker()._runs_dir() / f"cleanup-{digest}.lock"


def acquire_lock(host: Host) -> Path | None:
    """Create the exclusive lock beside the run records; None when another live run holds it."""
    ck = _checker()
    path = _lock_path(host)
    path.parent.mkdir(parents=True, exist_ok=True)
    ck._restrict(path.parent, directory=True)
    for _attempt in range(2):
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            try:
                if time.time() - path.stat().st_mtime <= LOCK_STALE_SECONDS:
                    return None
                path.unlink()
            except OSError:
                return None
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "at": time.time()}))
        return path
    return None


def receipt_path(record_path: Path) -> Path:
    return record_path.with_name(record_path.stem + RECEIPT_SUFFIX)


def _seal(body: dict, key: bytes) -> str:
    ck = _checker()
    return hmac.new(key, _RECEIPT_DOMAIN + ck._canonical(body), hashlib.sha256).hexdigest()


def write_receipt(host: Host, record_path: Path, record: dict, scope: str, verdicts: list[Verdict],
                  idle_hours: float) -> bool:
    """Write the sealed final-pass receipt beside the record; False when it cannot be sealed."""
    ck = _checker()
    key = ck._secret(create=False)
    if key is None:
        return False
    ref = "refs/heads/" + host.integration
    rc, out, _ = host.g("ls-remote", host.remote, ref)
    tip = next((line.split("\t")[0] for line in out.splitlines() if line.endswith("\t" + ref)), "") if rc == 0 else ""
    if not tip:
        return False
    host.g("fetch", "--quiet", "--no-tags", host.remote, ref)  # so the tip's history is local for the predicate
    body = {
        "kind": RECEIPT_KIND,
        "receipt_schema": 1,
        "scope": scope,
        "record_nonce": record.get("nonce"),
        "created": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "integration_branch": host.integration,
        "integration_tip": tip,
        "idle_hours": idle_hours,
        "removed": [v.item.as_dict() for v in verdicts if v.action == "REMOVE"],
        "kept": [{"item": v.item.label(), "check": v.check, "reason": v.reason or None}
                 for v in verdicts if v.action == "KEEP"],
    }
    body["seal"] = _seal(body, key)
    ck._write_record(receipt_path(record_path), body)
    return True


def receipt_status(
    root: Path,
    git: str,
    run: Callable[[list[str], Path | None], tuple[int, str]],
    record_path: Path,
    nonce: object,
    merge_commit: str | None,
    target_branch: str,
) -> str:
    """The `cleanup.merged` predicate (completion contract): met, unmet, or cannot-verify.

    Met when the receipt beside the record verifies under the runs secret, names the
    record's nonce and target branch, used an idle window of at least MIN_IDLE_HOURS,
    was taken with the integration tip containing `merge_commit` (the last merge), and
    every item it removed is still gone. Items that became eligible
    after the receipt never reopen the verdict.
    """
    ck = _checker()
    path = receipt_path(record_path)
    key = ck._secret(create=False)
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return "unmet"
    if not isinstance(body, dict) or key is None or body.get("kind") != RECEIPT_KIND:
        return "unmet"
    seal = str(body.pop("seal", ""))
    if not hmac.compare_digest(seal, _seal(body, key)) or body.get("record_nonce") != nonce:
        return "unmet"
    idle = body.get("idle_hours")
    if body.get("integration_branch") != target_branch or not isinstance(idle, (int, float)) or not (
        math.isfinite(idle) and idle >= MIN_IDLE_HOURS
    ):
        return "unmet"
    if not merge_commit:
        return "cannot-verify"
    rc, _ = run([git, "-C", str(root), "merge-base", "--is-ancestor", merge_commit, str(body.get("integration_tip"))], None)
    if rc != 0:
        return "unmet" if rc == 1 else "cannot-verify"
    return _removed_still_gone(root, git, run, body.get("removed") or [])


def _removed_still_gone(root: Path, git: str, run: Callable[[list[str], Path | None], tuple[int, str]],
                        removed: list[dict]) -> str:
    rc, listing = run([git, "-C", str(root), "worktree", "list", "--porcelain"], None)
    if rc != 0:
        return "cannot-verify"
    listed = {_norm(line[len("worktree "):]) for line in listing.splitlines() if line.startswith("worktree ")}
    for entry in removed:
        kind, name = entry.get("kind"), str(entry.get("name") or "")
        if kind == "worktree" and _norm(str(entry.get("path"))) in listed:
            return "unmet"
        if kind == "branch":
            rc, out = run([git, "-C", str(root), "for-each-ref", "--format=%(refname)", "refs/heads/" + name], None)
            if rc != 0:
                return "cannot-verify"
            if "refs/heads/" + name in out.split():
                return "unmet"
        if kind == "remote":
            rc, out = run([git, "-C", str(root), "ls-remote", "--heads", str(entry.get("remote")), "refs/heads/" + name], None)
            if rc != 0:
                return "cannot-verify"
            if any(line.endswith("\trefs/heads/" + name) for line in out.splitlines()):
                return "unmet"
    return "met"


# --------------------------------------------------------------------------- run


def run_pass(host: Host, idle_hours: float, apply: bool, own: Path | None) -> list[Verdict]:
    """Evaluate every item; with `apply`, re-read and remove each REMOVE item in order."""
    first = read_state(host, own)
    items = enumerate_items(host, first)
    leaving: set[str] = set()
    planned: list[Verdict] = []
    for item in items:
        verdict = evaluate(host, first, item, idle_hours, leaving)
        if verdict.action == "REMOVE" and item.kind == "worktree":
            leaving.add(_norm(item.path))
        planned.append(verdict)
    if not apply:
        return planned
    final: list[Verdict] = []
    for verdict in planned:
        if verdict.action != "REMOVE":
            final.append(verdict)
            continue
        # Re-read every fact immediately before this removal; the lease covers the rest.
        fresh = read_state(host, own, pr_branch=verdict.item.name or None)
        again = evaluate(host, fresh, verdict.item, idle_hours)
        final.append(remove(host, again) if again.action == "REMOVE" else again)
    return final


def _load_scope_record(args: argparse.Namespace, host: Host, budget: float) -> tuple[Path, object, str]:
    """(record path, loaded state, scope) for the `--plan` or `--minor` the caller named,
    verified and bound to the caller's `--session` (a record of another session loads as
    no record)."""
    ck = _checker()
    if args.minor:
        minor = ck._minor_module()
        rctx = ck.RepoContext(host.current, ck.Budget(budget))
        state = minor.load_minor(ck, rctx, args.minor, args.session)
        return minor.record_file(ck, rctx, args.minor), state, "minor:" + args.minor
    ctx = ck.Context(args.plan, ck.Budget(budget))
    return ctx.record_path(), ck.load_record(ctx, args.session), "plan:" + ctx.rel


def _is_own(state: object, session: str | None) -> bool:
    record = getattr(state, "record", None)
    return bool(session) and isinstance(record, dict) and record.get("session_id") == session


def _record_for_receipt(args: argparse.Namespace, host: Host) -> tuple[Path, dict, str] | int:
    if not args.session:
        print("BLOCKED: approval-not-covered")
        print("reason: session-required")
        return EXIT_BLOCKED
    path, state, scope = _load_scope_record(args, host, 120.0)
    if state.forced is not None:
        print(state.forced[0])
        return EXIT_BLOCKED
    record = state.record
    if record is None and path.is_file():
        print("BLOCKED: approval-not-covered")
        print("reason: record-bound-to-another-session")
        return EXIT_BLOCKED
    classes = {c.get("class") for c in ((record or {}).get("approvals") or {}).get("classes") or [] if isinstance(c, dict)}
    if record is None or "cleanup-merged" not in classes:
        print("BLOCKED: approval-not-covered")
        print("reason: no-cleanup-merged-approval")
        return EXIT_BLOCKED
    return path, record, scope


def _own_record(args: argparse.Namespace, host: Host) -> Path | None:
    """The named scope's record path, exempt from owned-by-run only when it is the
    calling session's own verified record. Naming another session's plan or minor
    never lifts that run's protection: its record stays in the ownership scan."""
    if not (args.plan or args.minor):
        return None
    path, state, _scope = _load_scope_record(args, host, 60.0)
    if _is_own(state, args.session):
        return path
    host.notices.append("scope-record-not-own")
    return None


def _idle_hours(text: str) -> float:
    try:
        value = float(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("not a number") from exc
    if not math.isfinite(value) or value < MIN_IDLE_HOURS:
        raise argparse.ArgumentTypeError(f"must be a finite number of at least {MIN_IDLE_HOURS:g}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Remove verifiably merged and idle branches and worktrees.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="report only (the default)")
    mode.add_argument("--apply", action="store_true", help="remove every item whose checks all pass")
    parser.add_argument("--integration-branch", default="develop")
    parser.add_argument("--idle-hours", type=_idle_hours, default=MIN_IDLE_HOURS,
                        help=f"idle window in hours (at least {MIN_IDLE_HOURS:g})")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--repo", default=".")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--plan", help="the calling run's plan (its own record is not 'another run')")
    scope.add_argument("--minor", help="the calling run's minor token vX.Y")
    parser.add_argument("--receipt", action="store_true", help="write the final-pass receipt (needs --apply)")
    parser.add_argument("--session", help="the calling session's id: only its own verified run record "
                        "is exempt from the owned-by-run check, and a receipt needs it")
    return parser


def report(repo: Path, integration_branch: str = "develop", idle_hours: float = 24.0) -> tuple[list[Verdict], list[str]]:
    """The dry-run verdicts and notices, for callers that only report (check_release_preconditions)."""
    host = Host(repo, integration_branch)
    return run_pass(host, idle_hours, apply=False, own=None), host.notices


def _emit(verdicts: list[Verdict], notices: list[str], args: argparse.Namespace) -> None:
    if args.json:
        print(json.dumps({"mode": "apply" if args.apply else "dry-run",
                          "items": [v.as_dict() for v in verdicts], "notices": sorted(set(notices))}, indent=2))
    else:
        for verdict in verdicts:
            print(verdict.line())
            for part in verdict.partial:
                print(f"  partial: {part}")
    for notice in sorted(set(notices)):
        print(f"notice: {notice}", file=sys.stderr)
    removed = sum(v.action == "REMOVE" for v in verdicts)
    mode = "removed" if args.apply else "would remove (dry-run, nothing removed)"
    print(f"summary: {removed} {mode}, {len(verdicts) - removed} kept", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.receipt and not (args.apply and (args.plan or args.minor)):
        print("--receipt needs --apply and the run's --plan or --minor", file=sys.stderr)
        return EXIT_USAGE
    try:
        host = Host(Path(args.repo).resolve(), args.integration_branch)
        target = _record_for_receipt(args, host) if args.receipt else None
        if isinstance(target, int):
            return target
        own = target[0] if target else _own_record(args, host)
    except (RuntimeError, _checker().Malformed) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    lock = acquire_lock(host) if args.apply else None
    if args.apply and lock is None:
        print("BLOCKED: cleanup-running")
        return EXIT_BLOCKED
    try:
        verdicts = run_pass(host, args.idle_hours, args.apply, own)
    finally:
        if lock is not None:
            lock.unlink(missing_ok=True)
    blocked = None
    if args.apply and any(v.check == "records-unreadable" for v in verdicts):
        blocked = "BLOCKED: records-unreadable"
    elif target and any(v.check in GLOBAL_UNKNOWN for v in verdicts):
        blocked = "BLOCKED: cannot-verify"  # a pass that could not see is not a final pass
    elif target and not write_receipt(host, target[0], target[1], target[2], verdicts, args.idle_hours):
        blocked = "BLOCKED: receipt-not-written"
    if blocked:
        print(blocked)
    _emit(verdicts, host.notices, args)
    if blocked:
        return EXIT_BLOCKED
    return EXIT_PARTIAL if any(v.check == REMOVAL_FAILED for v in verdicts) else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
