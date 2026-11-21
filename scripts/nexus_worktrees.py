#!/usr/bin/env python3
"""Centralized worktree policy helper behind `nexus-hub worktree` (v4.15.6).

One resolver decides where a linked worktree lives, one non-executing Git profile
inspects repositories, one resumable read-only scan inventories every linked
worktree on the machine, and one reviewed-manifest executor moves them.

Actions (this module owns the logic; `scripts/nexus_hub_cli.py` forwards to it):

    path     Resolve a worktree's canonical destination. Writes nothing.
    create   Create a worktree at that destination (serialized per repository).
    list     Report a repository's registered worktrees and canonical destinations.
    audit    Read-only machine discovery with an explicit coverage ledger.
    migrate  Dry-run a reviewed manifest, then apply exactly that manifest.

Layout: `<root>/<repository-identity>/<worktree-name>`. The root comes from the
`NEXUS_WORKTREE_ROOT` environment variable, then the user's own
`<nexus-hub home>/config/worktrees.json`, then `~/.worktrees`. Policy is never read
from a repository-controlled file, and there is no silent fallback to a sibling,
vendor, temporary, network, or synchronized folder.

Exit codes: 0 complete, 2 refused before any mutation, 3 partial or cannot-verify.
This is organizational enforcement inside supported Nexus-Hub surfaces, not an OS
security boundary. Stdlib only; no outbound call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import queue
import re
import shutil
import stat
import subprocess
import sys
import threading
import time
import unicodedata
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

import runpy as _process_runpy

_PROCESS_POLICY = _process_runpy.run_path(
    str(Path(__file__).resolve().parents[0] / "nexus_process.py")
)
_PROCESS_POLICY["install_no_window_default"]()

NO_WINDOW = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}

AUDIT_SCHEMA = "nexus-worktree-audit/1"
EXIT_OK = 0
EXIT_REFUSED = 2
EXIT_PARTIAL = 3

IS_NT = os.name == "nt"
REPARSE_ATTRIBUTE = 0x400
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
WINDOWS_RESERVED = frozenset(
    {
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(1, 10)),
        *(f"lpt{i}" for i in range(1, 10)),
    }
)
MAX_NAME_LENGTH = 40
MAX_DESTINATION_LENGTH = 240
GIT_TIMEOUT_SECONDS = 30
LIST_CAP = 500


class PolicyError(Exception):
    """A refusal (exit 2) or, with cannot_verify set, an unverifiable state (exit 3)."""

    def __init__(self, code: str, message: str, *, cannot_verify: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.cannot_verify = cannot_verify

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "cannot-verify" if self.cannot_verify else "refused",
            "code": self.code,
            "message": self.message,
        }


# --------------------------------------------------------------------------- paths


def canon(path: str | os.PathLike[str]) -> str:
    """Resolved absolute path with Windows long-path prefix removed."""
    resolved = os.path.realpath(os.fspath(path))
    if (
        IS_NT
        and resolved.startswith("\\\\?\\")
        and not resolved.startswith("\\\\?\\UNC")
    ):
        resolved = resolved[4:]
    return resolved


def key_of(path: str | os.PathLike[str]) -> str:
    """Comparison key: resolved and case-folded on Windows."""
    resolved = canon(path)
    return os.path.normcase(resolved) if IS_NT else resolved


def is_within(child: str | os.PathLike[str], parent: str | os.PathLike[str]) -> bool:
    c, p = key_of(child), key_of(parent)
    return c == p or c.startswith(p.rstrip("\\/") + os.sep)


def is_reparse(path: str | os.PathLike[str]) -> bool:
    """True for a symlink or Windows junction/reparse point, without following it."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    return stat.S_ISLNK(st.st_mode) or bool(
        getattr(st, "st_file_attributes", 0) & REPARSE_ATTRIBUTE
    )


def hub_home() -> Path:
    return Path(os.environ.get("NEXUS_HUB_HOME") or (Path.home() / ".nexus-hub"))


def state_dir() -> Path:
    """Local-only state: manifests, receipts, identity mapping. Never a removal target."""
    override = os.environ.get("NEXUS_WORKTREE_STATE")
    return Path(override) if override else hub_home() / "state" / "worktrees"


def atomic_write(path: Path, text: str, *, exclusive: bool = False) -> None:
    """Durable write: temp file, fsync, replace. `exclusive` refuses an existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and path.exists():
        raise PolicyError(
            "output-exists", f"refusing to overwrite an existing file: {path.name}"
        )
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex[:8]}.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


# --------------------------------------------------------------------------- names


def sanitize_component(
    raw: str, *, max_length: int = MAX_NAME_LENGTH
) -> tuple[str, bool]:
    """Return (safe component, lossless). Lossy results get a hash suffix from the caller."""
    text = unicodedata.normalize("NFKD", raw or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    lowered = text.lower()
    safe = re.sub(r"[^a-z0-9._-]+", "-", lowered).strip("-. ")
    safe = re.sub(r"-{2,}", "-", safe)
    lossless = safe == raw
    if len(safe) > max_length:
        safe, lossless = safe[:max_length].rstrip("-. "), False
    if not safe or safe in {".", ".."}:
        return "wt", False
    if safe.split(".", 1)[0] in WINDOWS_RESERVED:
        return f"wt-{safe}", False
    return safe, lossless


def worktree_name(raw: str) -> str:
    """Short readable name; lossy conversions and case changes get a collision-safe suffix."""
    safe, lossless = sanitize_component(raw)
    if lossless:
        return safe
    digest = hashlib.sha256((raw or "").encode("utf-8")).hexdigest()[:6]
    return f"{safe}-{digest}"


def repo_slug(display: str) -> str:
    name = display[:-4] if display.lower().endswith(".git") else display
    safe, _ = sanitize_component(name, max_length=32)
    return safe


# --------------------------------------------------------------------------- root policy


@dataclass
class RootInfo:
    path: Path
    provenance: str  # env | config | default

    def as_dict(self) -> dict[str, str]:
        return {"root": str(self.path), "provenance": self.provenance}


def _drive_type(path: str) -> int | None:
    if not IS_NT:
        return None
    try:
        import ctypes

        drive = os.path.splitdrive(path)[0]
        return int(ctypes.windll.kernel32.GetDriveTypeW(drive + "\\"))  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return None


def validate_root(value: str, provenance: str) -> Path:
    """Validate a root before any mutation; never falls back to another location."""
    if not value or not value.strip():
        raise PolicyError("root-empty", f"worktree root from {provenance} is empty")
    expanded = os.path.expanduser(value.strip())
    if expanded.startswith(("\\\\", "//")):
        raise PolicyError(
            "root-network", "a network or UNC path cannot be the worktree root"
        )
    if not os.path.isabs(expanded) or (IS_NT and not os.path.splitdrive(expanded)[0]):
        raise PolicyError(
            "root-not-absolute",
            f"worktree root from {provenance} must be an absolute local path",
        )
    if ".." in Path(expanded).parts:
        raise PolicyError("root-traversal", "worktree root must not contain '..'")
    if IS_NT:
        drive = os.path.splitdrive(expanded)[0] + "\\"
        if not os.path.exists(drive):
            raise PolicyError(
                "root-volume-unavailable",
                f"volume {drive} is not available",
                cannot_verify=True,
            )
        if _drive_type(expanded) == 4:
            raise PolicyError(
                "root-network", "a network drive cannot be the worktree root"
            )
    root = Path(os.path.abspath(expanded))
    lowered = [part.lower() for part in root.parts]
    if any(part in VENDOR_DIRS for part in lowered):
        raise PolicyError(
            "root-vendor-dir",
            "worktree root must not sit inside a tool or Nexus-Hub directory",
        )
    if is_within(root, hub_home()):
        raise PolicyError(
            "root-inside-nexus-hub",
            "worktree root must be separate from the Nexus-Hub home",
        )
    if any(part.startswith(SYNC_PREFIXES) for part in lowered):
        raise PolicyError(
            "root-synchronized", "worktree root must not sit in a synchronized folder"
        )
    if root.exists() and is_reparse(root):
        raise PolicyError(
            "root-reparse", "worktree root must not be a symlink or junction"
        )
    for ancestor in [root, *root.parents]:
        if (ancestor / ".git").exists():
            raise PolicyError(
                "root-inside-repository",
                "worktree root must not sit inside a Git repository",
            )
    return root


def resolve_root() -> RootInfo:
    """Environment, then the user's own config file, then the home default."""
    env_value = os.environ.get("NEXUS_WORKTREE_ROOT")
    if env_value and env_value.strip():
        return RootInfo(validate_root(env_value, "NEXUS_WORKTREE_ROOT"), "env")
    config = hub_home() / "config" / "worktrees.json"
    if config.is_file():
        try:
            data = json.loads(config.read_text(encoding="utf-8-sig"))
            value = data["root"] if isinstance(data, dict) else None
        except (OSError, ValueError, KeyError) as exc:
            raise PolicyError(
                "config-malformed",
                f"{config.name} is not valid worktree policy: {exc.__class__.__name__}",
            ) from exc
        if not isinstance(value, str):
            raise PolicyError(
                "config-malformed", f"{config.name} must hold a string 'root'"
            )
        return RootInfo(validate_root(value, "config"), "config")
    return RootInfo(
        validate_root(str(Path.home() / ".worktrees"), "default"), "default"
    )


# --------------------------------------------------------------------------- git inspection


@dataclass
class GitResult:
    rc: int
    out: str
    err: str
    timed_out: bool = False


ALLOWED_INSPECTION = {
    "rev-parse",
    "worktree",
    "status",
    "for-each-ref",
    "rev-list",
    "merge-base",
    "ls-files",
    "cat-file",
    "config",
    "check-ref-format",
    "diff",
    "symbolic-ref",
    "show-ref",
}
EXECUTABLE_CONFIG = (
    re.compile(r"^filter\.(?P<name>.+)\.(clean|smudge|process)$", re.I),
    re.compile(r"^diff\.(?P<name>.+)\.(textconv|command)$", re.I),
    re.compile(r"^core\.(fsmonitor|hookspath|sshcommand|editor|askpass|pager)$", re.I),
    re.compile(r"^diff\.external$", re.I),
    re.compile(r"^merge\..+\.driver$", re.I),
    re.compile(r"^gpg\..*program$", re.I),
)


def trusted_git(inside: str | os.PathLike[str] | None = None) -> str:
    """One absolute Git executable, never one that resolves inside the inspected tree."""
    found = shutil.which("git")
    if not found:
        raise PolicyError(
            "git-missing", "git was not found on PATH", cannot_verify=True
        )
    resolved = canon(found)
    if inside is not None and is_within(resolved, inside):
        raise PolicyError(
            "git-untrusted",
            "the git executable resolves inside the inspected tree; refusing",
        )
    return resolved


def _inspection_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    env.update(
        GIT_TERMINAL_PROMPT="0",
        GIT_OPTIONAL_LOCKS="0",
        GIT_PAGER="cat",
        GCM_INTERACTIVE="never",
        NO_COLOR="1",
    )
    return env


def executable_config_entries(config_z: str) -> list[tuple[str, str]]:
    """(key, scope) for config keys that would make Git launch a program (never values)."""
    parts = config_z.split("\0")
    found: list[tuple[str, str]] = []
    for index in range(0, len(parts) - 1, 2):
        scope, name = parts[index], parts[index + 1].split("\n", 1)[0]
        if name and any(pattern.match(name) for pattern in EXECUTABLE_CONFIG):
            found.append((name, scope))
    return found


def executable_config_keys(config_z: str) -> list[str]:
    """Names only, deduplicated, from every scope."""
    names: list[str] = []
    for name, _ in executable_config_entries(config_z):
        if name not in names:
            names.append(name)
    return names


LOCAL_SCOPES = frozenset({"local", "worktree", "command"})


class GitInspector:
    """Bounded, non-executing Git command profile used for every inspection.

    Inherited GIT_* overrides are dropped, optional writes and prompts are off,
    fsmonitor and hooks are disabled, and any repository-configured filter,
    textconv, or external diff is overridden with an empty value before it can
    run. Safe-ownership checks are retained; no safe.directory wildcard is used.
    """

    def __init__(
        self,
        git: str | None = None,
        timeout: float = GIT_TIMEOUT_SECONDS,
        runner: Callable[..., Any] | None = None,
    ) -> None:
        self.git = git or trusted_git()
        self.timeout = timeout
        self._runner = runner or subprocess.run
        self._neutral: dict[str, list[str]] = {}
        self._config_cache: dict[str, tuple[list[str], list[str]]] = {}

    def _run(self, argv: list[str], cwd: str | None) -> GitResult:
        try:
            proc = self._runner(
                argv,
                cwd=cwd,
                env=_inspection_env(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                check=False,
                **NO_WINDOW,
            )
        except subprocess.TimeoutExpired:
            return GitResult(-1, "", "timeout", True)
        except OSError as exc:
            return GitResult(-1, "", exc.__class__.__name__)
        return GitResult(proc.returncode, proc.stdout, proc.stderr)

    def _scope(self, cwd: str | None, git_dir: str | None) -> list[str]:
        return ["--git-dir", git_dir] if git_dir else (["-C", cwd] if cwd else [])

    def _config_scan(
        self, cwd: str | None, git_dir: str | None
    ) -> tuple[list[str], list[str]]:
        scope = git_dir or cwd or ""
        if scope not in self._config_cache:
            result = self._run(
                [
                    self.git,
                    "--no-optional-locks",
                    *self._scope(cwd, git_dir),
                    "config",
                    "--list",
                    "--show-scope",
                    "-z",
                ],
                None,
            )
            entries = (
                executable_config_entries(result.out) if result.rc == 0 else []
            )
            everywhere = list(dict.fromkeys(name for name, _ in entries))
            local = list(
                dict.fromkeys(name for name, kind in entries if kind in LOCAL_SCOPES)
            )
            self._config_cache[scope] = (everywhere, local)
        return self._config_cache[scope]

    def config_keys(
        self, cwd: str | None = None, git_dir: str | None = None
    ) -> list[str]:
        """Every executable key, from any scope. Used to neutralize them."""
        return list(self._config_scan(cwd, git_dir)[0])

    def local_config_keys(
        self, cwd: str | None = None, git_dir: str | None = None
    ) -> list[str]:
        """Executable keys the repository itself sets. User-wide keys such as Git LFS are not findings."""
        return list(self._config_scan(cwd, git_dir)[1])

    def _neutralize(self, cwd: str | None, git_dir: str | None) -> list[str]:
        scope = git_dir or cwd or ""
        if scope not in self._neutral:
            flags: list[str] = []
            for name in self.config_keys(cwd, git_dir):
                lowered = name.lower()
                if (
                    lowered.startswith(("filter.", "diff."))
                    and lowered != "diff.external"
                ):
                    flags += ["-c", f"{name}="]
            self._neutral[scope] = flags
        return self._neutral[scope]

    def run(
        self, argv: list[str], *, cwd: str | None = None, git_dir: str | None = None
    ) -> GitResult:
        sub = argv[0] if argv else ""
        if sub not in ALLOWED_INSPECTION:
            raise PolicyError(
                "git-command-not-allowed",
                f"'{sub}' is not an allowed inspection command",
            )
        if sub == "worktree" and argv[1:2] != ["list"]:
            raise PolicyError(
                "git-command-not-allowed",
                "only 'worktree list' is an inspection command",
            )
        if sub == "config" and not set(argv[1:]) & {"--list", "--get", "-z"}:
            raise PolicyError(
                "git-command-not-allowed", "config inspection is read-only"
            )
        base = [
            self.git,
            "--no-optional-locks",
            "-c",
            "core.fsmonitor=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "-c",
            "core.pager=cat",
            "-c",
            "diff.external=",
            "-c",
            "protocol.ext.allow=never",
            *self._neutralize(cwd, git_dir),
            *self._scope(cwd, git_dir),
            *argv,
        ]
        return self._run(base, None)


@dataclass
class RegisteredWorktree:
    path: str
    head: str
    branch: str | None
    detached: bool
    bare: bool
    locked: bool
    lock_reason: str
    prunable: bool


def parse_worktree_list(text: str) -> list[RegisteredWorktree]:
    """Parse `git worktree list --porcelain -z` records."""
    found: list[RegisteredWorktree] = []
    for block in text.split("\0\0"):
        fields = [f for f in block.split("\0") if f]
        if not fields or not fields[0].startswith("worktree "):
            continue
        attrs: dict[str, str] = {}
        for field_text in fields[1:]:
            name, _, value = field_text.partition(" ")
            attrs[name] = value
        branch = attrs.get("branch", "")
        found.append(
            RegisteredWorktree(
                path=fields[0][len("worktree ") :],
                head=attrs.get("HEAD", ""),
                branch=branch.removeprefix("refs/heads/") if branch else None,
                detached="detached" in attrs,
                bare="bare" in attrs,
                locked="locked" in attrs,
                lock_reason=attrs.get("locked", ""),
                prunable="prunable" in attrs,
            )
        )
    return found


def list_registered(
    git: GitInspector, *, cwd: str | None = None, git_dir: str | None = None
) -> list[RegisteredWorktree]:
    result = git.run(
        ["worktree", "list", "--porcelain", "-z"], cwd=cwd, git_dir=git_dir
    )
    if result.timed_out:
        raise PolicyError(
            "git-timeout", "git worktree list timed out", cannot_verify=True
        )
    if result.rc != 0:
        raise PolicyError(
            "registry-unreadable",
            f"git worktree list failed: {result.err.strip()[:160]}",
            cannot_verify=True,
        )
    return parse_worktree_list(result.out)


def _sha(parts: Iterable[bytes]) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


def worktree_state(git: GitInspector, path: str) -> dict[str, Any]:
    """Fingerprint a worktree's HEAD, index, working changes, untracked and ignored names."""
    head = git.run(["rev-parse", "HEAD"], cwd=path)
    branch = git.run(["symbolic-ref", "-q", "--short", "HEAD"], cwd=path)
    status = git.run(
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=path
    )
    staged = git.run(["ls-files", "--stage", "-z"], cwd=path)
    ignored = git.run(
        ["ls-files", "--others", "--ignored", "--exclude-standard", "-z"], cwd=path
    )
    if any(r.timed_out for r in (head, status, staged, ignored)):
        raise PolicyError(
            "git-timeout", "git state inspection timed out", cannot_verify=True
        )
    if status.rc != 0 or staged.rc != 0 or ignored.rc != 0:
        raise PolicyError(
            "state-unreadable",
            f"git state inspection failed: {(status.err or staged.err or ignored.err).strip()[:160]}",
            cannot_verify=True,
        )
    submodules = [
        e.split("\t", 1)[1]
        for e in staged.out.split("\0")
        if e.startswith("160000 ") and "\t" in e
    ]
    return {
        "head": head.out.strip() if head.rc == 0 else "",
        "branch": branch.out.strip() if branch.rc == 0 else None,
        "status_digest": _sha(e.encode() for e in status.out.split("\0") if e),
        "index_digest": _sha(e.encode() for e in staged.out.split("\0") if e),
        "ignored_digest": _sha(
            e.encode() for e in sorted(ignored.out.split("\0")) if e
        ),
        "dirty": bool(status.out.strip("\0")),
        "ignored_count": len([e for e in ignored.out.split("\0") if e]),
        "submodules": submodules,
    }


# --------------------------------------------------------------------------- markers and identity


@dataclass
class Marker:
    path: str
    kind: str  # main | linked | bare | submodule | malformed | dangling
    gitdir: str | None = None
    common: str | None = None
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "common": self.common,
            "detail": self.detail or None,
        }


def _read_gitfile(path: Path) -> str | None:
    try:
        text = path.read_bytes()[:4096].decode("utf-8", errors="replace").strip()
    except OSError:
        return None
    return (
        text[len("gitdir:") :].strip()
        if text.startswith("gitdir:") and "\n" not in text
        else None
    )


def read_common_dir(gitdir: Path) -> Path | None:
    """The shared common directory recorded in a linked worktree's git directory."""
    try:
        text = (gitdir / "commondir").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return Path(os.path.normpath(gitdir / text)) if text else None


def classify_dir(directory: Path, names: set[str]) -> Marker | None:
    """Classify a directory by Git marker files only; never executes anything."""
    dot_git = directory / ".git"
    if ".git" in names:
        if dot_git.is_dir() and not is_reparse(dot_git):
            if (dot_git / "HEAD").is_file():
                return Marker(str(directory), "main", str(dot_git), canon(dot_git))
            return Marker(
                str(directory), "malformed", detail="'.git' directory has no HEAD"
            )
        raw = _read_gitfile(dot_git) if dot_git.is_file() else None
        if raw is None:
            return Marker(
                str(directory),
                "malformed",
                detail="'.git' is neither a directory nor a valid gitdir file",
            )
        gitdir = (
            Path(raw) if os.path.isabs(raw) else Path(os.path.normpath(directory / raw))
        )
        if not gitdir.is_dir():
            return Marker(
                str(directory),
                "dangling",
                str(gitdir),
                detail="gitdir target is missing",
            )
        common = read_common_dir(gitdir)
        if gitdir.parent.name == "worktrees" and common is not None:
            return Marker(str(directory), "linked", str(gitdir), canon(common))
        if "modules" in gitdir.parts:
            return Marker(str(directory), "submodule", str(gitdir), canon(gitdir))
        if (gitdir / "HEAD").is_file():
            return Marker(
                str(directory),
                "main",
                str(gitdir),
                canon(gitdir),
                "separate git directory",
            )
        return Marker(
            str(directory),
            "malformed",
            str(gitdir),
            detail="gitdir target is not a Git directory",
        )
    if {"HEAD", "objects", "refs"} <= names and (directory / "HEAD").is_file():
        return Marker(str(directory), "bare", str(directory), canon(directory))
    return None


def checkout_common_dir(git: GitInspector, repo: str) -> tuple[Path, Path]:
    """(common dir, checkout top-level or bare dir) for an existing checkout."""
    start = Path(repo)
    if not start.exists():
        raise PolicyError("repo-missing", "the repository path does not exist")
    names = {p.name for p in start.iterdir()} if start.is_dir() else set()
    marker = classify_dir(start, names)
    if marker is None or marker.kind in ("malformed", "dangling", "submodule"):
        top = git.run(["rev-parse", "--show-toplevel"], cwd=str(start))
        if top.rc != 0 or not top.out.strip():
            raise PolicyError(
                "not-a-repository", "the path is not inside a Git checkout"
            )
        start = Path(top.out.strip())
        names = {p.name for p in start.iterdir()}
        marker = classify_dir(start, names)
    if (
        marker is None
        or not marker.common
        or marker.kind in ("malformed", "dangling", "submodule")
    ):
        raise PolicyError("not-a-repository", "the path is not a usable Git checkout")
    return Path(marker.common), start


@dataclass
class RepoIdentity:
    id: str
    slug: str
    common_dir: str
    main_path: str
    adopted: str = (
        ""  # "relocation" when an existing identity was carried to a moved repository
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slug": self.slug,
            "common_dir": self.common_dir,
            "adopted": self.adopted or None,
        }


def _identity_map_path() -> Path:
    return state_dir() / "identities.json"


def _read_identity_map() -> dict[str, dict[str, Any]]:
    path = _identity_map_path()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        repos = data["repos"]
    except (OSError, ValueError, KeyError) as exc:
        raise PolicyError(
            "identity-map-malformed",
            "the identity mapping is unreadable; refusing to guess",
        ) from exc
    if not isinstance(repos, dict):
        raise PolicyError(
            "identity-map-malformed",
            "the identity mapping is malformed; refusing to guess",
        )
    return repos


def _pointer_owner_ok(worktree_path: str, common: Path) -> bool:
    """True when a registered worktree's own '.git' pointer resolves into this common directory."""
    raw = _read_gitfile(Path(worktree_path) / ".git")
    if raw is None:
        return False
    gitdir = (
        Path(raw)
        if os.path.isabs(raw)
        else Path(os.path.normpath(Path(worktree_path) / raw))
    )
    resolved = read_common_dir(gitdir) if gitdir.is_dir() else None
    return resolved is not None and key_of(resolved) == key_of(common)


IDENTITY_DIR = re.compile(r"^[a-z0-9._-]+-[0-9a-f]{8}$")


def resolve_identity(
    common: Path,
    main_path: str,
    registered: list[RegisteredWorktree],
    root: Path,
    *,
    write: bool,
) -> RepoIdentity:
    """Stable identity rooted in Git's canonical common directory.

    Two clones with one basename or remote differ because the suffix hashes the
    common directory. A main repository that moved keeps its identity only when
    its own linked worktrees, under this root, prove it through their pointers
    and the previously recorded location is gone; anything else that conflicts
    refuses rather than guessing.
    """
    common_key = key_of(common)
    slug = repo_slug(Path(main_path).name or common.name)
    mapping = _read_identity_map()
    for entry_id, entry in mapping.items():
        if isinstance(entry, dict) and entry.get("common_key") == common_key:
            return RepoIdentity(entry_id, slug, str(common), main_path)
    candidates = {
        Path(w.path).parent.name
        for w in registered
        if not w.bare
        and IDENTITY_DIR.match(Path(w.path).parent.name)
        and is_within(w.path, root)
        and Path(w.path).parent.parent == Path(root)
        and key_of(Path(w.path).parent.parent) == key_of(root)
        and _pointer_owner_ok(w.path, common)
    }
    adopted = ""
    if len(candidates) > 1:
        raise PolicyError(
            "identity-conflict",
            "this repository's worktrees sit under more than one identity directory",
        )
    if candidates:
        identity_id = next(iter(candidates))
        previous = mapping.get(identity_id)
        if isinstance(previous, dict) and previous.get("common_key") != common_key:
            if os.path.isdir(previous.get("common_dir", "")):
                raise PolicyError(
                    "identity-conflict",
                    "another live repository already holds this identity",
                )
        base_id = (
            f"{slug}-{hashlib.sha256(common_key.encode('utf-8')).hexdigest()[:8]}"
        )
        adopted = "relocation" if identity_id != base_id else ""
    else:
        identity_id = (
            f"{slug}-{hashlib.sha256(common_key.encode('utf-8')).hexdigest()[:8]}"
        )
        other = mapping.get(identity_id)
        if isinstance(other, dict) and other.get("common_key") != common_key:
            raise PolicyError(
                "identity-conflict",
                "an identity with this suffix is recorded for another repository",
            )
    identity = RepoIdentity(identity_id, slug, str(common), main_path, adopted)
    if write:
        mapping[identity_id] = {
            "common_key": common_key,
            "common_dir": str(common),
            "main_path": main_path,
        }
        atomic_write(
            _identity_map_path(),
            json.dumps({"version": 1, "repos": mapping}, indent=2, sort_keys=True)
            + "\n",
        )
    return identity


def repo_context(
    git: GitInspector, repo: str, root: Path, *, write: bool
) -> tuple[RepoIdentity, list[RegisteredWorktree]]:
    common, top = checkout_common_dir(git, repo)
    scope = (
        {"git_dir": str(common)}
        if (common / "HEAD").is_file() and common == top
        else {"cwd": str(top)}
    )
    registered = list_registered(git, **scope)
    main = next((w for w in registered), None)
    main_path = main.path if main else str(top)
    return (
        resolve_identity(common, main_path, registered, root, write=write),
        registered,
    )


# --------------------------------------------------------------------------- destination


@dataclass
class Destination:
    path: Path
    identity: RepoIdentity
    name: str
    root: RootInfo
    state: str  # new | registered
    lossless: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "path": str(self.path),
            "identity": self.identity.id,
            "name": self.name,
            "name_lossless": self.lossless,
            "root": str(self.root.path),
            "root_provenance": self.root.provenance,
            "state": self.state,
            "identity_adopted": self.identity.adopted or None,
        }


def resolve_destination(
    identity: RepoIdentity,
    raw_name: str,
    root: RootInfo,
    registered: list[RegisteredWorktree],
) -> Destination:
    """Canonical destination with ownership, collision, reparse and length checks."""
    if not raw_name or not raw_name.strip():
        raise PolicyError("name-empty", "a worktree name is required")
    name = worktree_name(raw_name)
    lossless = sanitize_component(raw_name)[1]
    base = root.path / identity.id
    dest = base / name
    if IS_NT and len(str(dest)) > MAX_DESTINATION_LENGTH:
        raise PolicyError(
            "path-too-long",
            f"the destination is longer than {MAX_DESTINATION_LENGTH} characters",
        )
    if not is_within(dest, root.path) or key_of(dest.parent) != key_of(base):
        raise PolicyError(
            "destination-escape", "the destination resolves outside the worktree root"
        )
    for existing in (root.path, base):
        if existing.exists() and is_reparse(existing):
            raise PolicyError(
                "destination-reparse",
                "a symlink or junction sits in the destination path",
            )
    if base.is_dir():
        for sibling in base.iterdir():
            if sibling.name != name and sibling.name.casefold() == name.casefold():
                raise PolicyError(
                    "case-collision",
                    f"'{sibling.name}' already exists and differs only by letter case",
                )
    state = "new"
    if os.path.lexists(dest):
        if is_reparse(dest):
            raise PolicyError(
                "destination-reparse", "the destination is a symlink or junction"
            )
        if any(key_of(w.path) == key_of(dest) for w in registered):
            state = "registered"
        elif (dest / ".git").exists():
            raise PolicyError(
                "destination-owned-by-other",
                "the destination holds a checkout that this repository does not register",
            )
        else:
            raise PolicyError(
                "destination-exists",
                "the destination already exists and is not a registered worktree",
            )
    return Destination(dest, identity, name, root, state, lossless)


def canonical_name_for(wt: RegisteredWorktree) -> str:
    """Name an existing worktree would keep: its own folder name when already valid, else its branch."""
    folder = Path(wt.path).name
    if sanitize_component(folder)[1]:
        return folder
    return wt.branch or folder or f"detached-{wt.head[:7]}"


# --------------------------------------------------------------------------- machine discovery

EXCLUDED_NAMES = frozenset(
    {
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "site-packages",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        ".gradle",
        ".m2",
        "$recycle.bin",
        "system volume information",
        ".git",
    }
)
VOLUME_ROOT_EXCLUDED = frozenset(
    {
        "windows",
        "program files",
        "program files (x86)",
        "programdata",
        "$windows.~bt",
        "recovery",
    }
)
DRIVE_KINDS = {
    0: "unknown",
    1: "no-root",
    2: "removable",
    3: "fixed",
    4: "network",
    5: "optical",
    6: "ram-disk",
}


def fixed_volumes() -> tuple[list[str], list[dict[str, str]]]:
    """(fixed local volume roots, other storage with the reason it is not scanned)."""
    if not IS_NT:
        return ["/"], []
    try:
        import ctypes

        mask = ctypes.windll.kernel32.GetLogicalDrives()  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return [], [{"root": "?", "reason": "drive enumeration unavailable"}]
    fixed: list[str] = []
    other: list[dict[str, str]] = []
    for index in range(26):
        if not mask & (1 << index):
            continue
        root = f"{chr(65 + index)}:\\"
        kind = int(ctypes.windll.kernel32.GetDriveTypeW(root))  # type: ignore[attr-defined]
        if kind == 3:
            fixed.append(root)
        else:
            other.append(
                {
                    "root": root,
                    "reason": f"excluded-storage:{DRIVE_KINDS.get(kind, 'unknown')}",
                }
            )
    return fixed, other


@dataclass
class Ledger:
    regions: list[dict[str, Any]] = field(default_factory=list)
    excluded: list[dict[str, str]] = field(default_factory=list)
    excluded_count: int = 0
    reparse: list[str] = field(default_factory=list)
    reparse_count: int = 0
    failures: list[dict[str, str]] = field(default_factory=list)
    failure_count: int = 0
    dirs: int = 0

    def add_excluded(self, path: str, reason: str) -> None:
        self.excluded_count += 1
        if len(self.excluded) < LIST_CAP:
            self.excluded.append({"path": path, "reason": reason})

    def add_reparse(self, path: str) -> None:
        self.reparse_count += 1
        if len(self.reparse) < LIST_CAP:
            self.reparse.append(path)

    def add_failure(self, path: str, reason: str) -> None:
        self.failure_count += 1
        if len(self.failures) < LIST_CAP:
            self.failures.append({"path": path, "reason": reason})

    def as_dict(self) -> dict[str, Any]:
        return {
            "regions": self.regions,
            "directories_scanned": self.dirs,
            "excluded": {"count": self.excluded_count, "sample": self.excluded},
            "reparse_points": {"count": self.reparse_count, "sample": self.reparse},
            "access_failures": {"count": self.failure_count, "sample": self.failures},
        }


@dataclass
class ScanOptions:
    roots: list[str]
    use_exclusions: bool = True
    max_seconds: float | None = None
    max_dirs: int | None = None
    checkpoint: Path | None = None
    resume: bool = False
    progress: Callable[[str], None] | None = None
    dir_timeout: float = 60.0


class _TimedLister:
    """Lists directories on a daemon worker so a stalled volume cannot hang the scan.

    Cloud-backed and virtual drives can report as fixed storage and block a
    directory read indefinitely. A read that exceeds the timeout is abandoned (its
    daemon thread stays blocked), recorded as a failure, and a fresh worker takes
    over, so the time budget and the progress line keep working.
    """

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        self.abandoned = 0
        self._start()

    def _start(self) -> None:
        self._requests: queue.Queue[str] = queue.Queue()
        self._results: queue.Queue[tuple[str, Any]] = queue.Queue()

        def work(requests: queue.Queue, results: queue.Queue) -> None:
            while True:
                directory = requests.get()
                try:
                    results.put(("ok", list(os.scandir(directory))))
                except OSError as exc:
                    results.put(("error", exc))

        threading.Thread(target=work, args=(self._requests, self._results), daemon=True).start()

    def list(self, directory: str) -> list[os.DirEntry[str]]:
        self._requests.put(directory)
        try:
            kind, value = self._results.get(timeout=self.timeout)
        except queue.Empty:
            self.abandoned += 1
            self._start()
            raise TimeoutError(directory) from None
        if kind == "error":
            raise value
        return value


def _scan_options_digest(options: ScanOptions) -> str:
    return hashlib.sha256(
        json.dumps([sorted(options.roots), options.use_exclusions]).encode()
    ).hexdigest()[:16]


class Scanner:
    """Resumable read-only walk that records every skip, failure and exclusion."""

    def __init__(
        self, options: ScanOptions, other_storage: list[dict[str, str]] | None = None
    ) -> None:
        self.options = options
        self.ledger = Ledger()
        self.markers: list[Marker] = []
        self.pending: list[tuple[str, str]] = []  # (root, directory)
        self.completed_roots: list[str] = []
        self.interrupted: str | None = None
        self._lister = _TimedLister(options.dir_timeout)
        self.other_storage = other_storage or []
        self._last_progress = time.monotonic()
        self._last_checkpoint = time.monotonic()
        self._started = time.monotonic()

    # ---- checkpoint

    def _snapshot(self) -> dict[str, Any]:
        return {
            "version": 1,
            "options": _scan_options_digest(self.options),
            "completed_roots": self.completed_roots,
            "pending": self.pending,
            "markers": [m.__dict__ for m in self.markers],
            "ledger": self.ledger.__dict__,
            "elapsed": time.monotonic() - self._started,
        }

    def save_checkpoint(self) -> None:
        if self.options.checkpoint is not None:
            atomic_write(self.options.checkpoint, json.dumps(self._snapshot()))
        self._last_checkpoint = time.monotonic()

    def load_checkpoint(self) -> None:
        path = self.options.checkpoint
        if path is None or not path.is_file():
            raise PolicyError("checkpoint-missing", "no checkpoint to resume from")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise PolicyError(
                "checkpoint-malformed", "the checkpoint is unreadable"
            ) from exc
        if not isinstance(data, dict) or data.get("options") != _scan_options_digest(
            self.options
        ):
            raise PolicyError(
                "checkpoint-mismatch",
                "the checkpoint was made with different roots or options",
            )
        self.completed_roots = list(data["completed_roots"])
        self.pending = [tuple(item) for item in data["pending"]]  # type: ignore[misc]
        self.markers = [Marker(**m) for m in data["markers"]]
        self.ledger = Ledger(**data["ledger"])

    # ---- walk

    def _budget_hit(self) -> bool:
        opts = self.options
        if (
            opts.max_seconds is not None
            and time.monotonic() - self._started >= opts.max_seconds
        ):
            self.interrupted = "time-budget"
        elif opts.max_dirs is not None and self.ledger.dirs >= opts.max_dirs:
            self.interrupted = "directory-budget"
        return self.interrupted is not None

    def _tick(self, root: str) -> None:
        now = time.monotonic()
        if self.options.progress and now - self._last_progress >= 5:
            self.options.progress(
                f"audit: {self.ledger.dirs} directories scanned, {len(self.markers)} Git markers, in {root}"
            )
            self._last_progress = now
        if now - self._last_checkpoint >= 10:
            self.save_checkpoint()

    def _excluded(self, name: str, directory: str, root: str) -> str | None:
        lowered = name.lower()
        if lowered in EXCLUDED_NAMES:
            return f"hint:{lowered}"
        if key_of(directory) == key_of(root) and lowered in VOLUME_ROOT_EXCLUDED:
            return f"hint:{lowered}"
        return None

    def _visit(self, root: str, directory: str) -> None:
        try:
            entries = self._lister.list(directory)
        except (OSError, TimeoutError) as exc:
            self.ledger.add_failure(directory, exc.__class__.__name__)
            if self._lister.abandoned >= 3:
                self.interrupted = "storage-unresponsive"
            return
        self.ledger.dirs += 1
        names = {e.name for e in entries}
        marker = classify_dir(Path(directory), names)
        if marker is not None:
            self.markers.append(marker)
            if marker.kind == "bare":
                return
        for entry in entries:
            try:
                st = entry.stat(follow_symlinks=False)
            except OSError as exc:
                self.ledger.add_failure(entry.path, exc.__class__.__name__)
                continue
            if (
                not stat.S_ISDIR(st.st_mode)
                and not stat.S_ISLNK(st.st_mode)
                and not getattr(st, "st_file_attributes", 0) & REPARSE_ATTRIBUTE
            ):
                continue
            if (
                stat.S_ISLNK(st.st_mode)
                or getattr(st, "st_file_attributes", 0) & REPARSE_ATTRIBUTE
            ):
                self.ledger.add_reparse(entry.path)
                continue
            reason = (
                self._excluded(entry.name, directory, root)
                if self.options.use_exclusions
                else None
            )
            if reason is None and entry.name.lower() == ".git":
                reason = "hint:.git"
            if reason is not None:
                if reason != "hint:.git":
                    self.ledger.add_excluded(entry.path, reason)
                continue
            self.pending.append((root, entry.path))

    def run(self) -> None:
        if self.options.resume:
            self.load_checkpoint()
        else:
            for root in self.options.roots:
                if not os.path.isdir(root):
                    self.ledger.regions.append(
                        {
                            "root": root,
                            "status": "unmounted",
                            "reason": "path or volume is not available",
                        }
                    )
                elif root not in self.completed_roots:
                    self.pending.insert(0, (root, root))
            for item in self.other_storage:
                self.ledger.regions.append(
                    {
                        "root": item["root"],
                        "status": "excluded-storage",
                        "reason": item["reason"],
                    }
                )
        while self.pending:
            if self._budget_hit():
                break
            root, directory = self.pending.pop()
            self._visit(root, directory)
            self._tick(root)
        # Scanned and partial rows are recomputed every run so a resumed scan
        # never keeps a stale "partial" row for a root it has since finished.
        self.ledger.regions = [
            r for r in self.ledger.regions if r["status"] not in ("scanned", "partial")
        ]
        for root in self.options.roots:
            if not os.path.isdir(root):
                continue
            unfinished = any(r == root for r, _ in self.pending)
            self.ledger.regions.append(
                {
                    "root": root,
                    "status": "partial" if unfinished else "scanned",
                    "reason": self.interrupted if unfinished else None,
                }
            )
        self.save_checkpoint()


def _git_scope_for(common: str, markers: list[Marker]) -> dict[str, str]:
    main = next(
        (
            m
            for m in markers
            if m.kind == "main" and m.common == common and not m.detail
        ),
        None,
    )
    return {"cwd": main.path} if main else {"git_dir": common}


def _inspect_registries(
    git: GitInspector,
    by_common: dict[str, list[Marker]],
    progress: Callable[[str], None] | None,
) -> dict[str, tuple[list[str], Any]]:
    """Read every repository's config keys and worktree registry on a small thread pool."""
    from concurrent.futures import ThreadPoolExecutor

    def inspect(item: tuple[str, list[Marker]]) -> tuple[str, list[str], Any]:
        common_key, markers = item
        common = next(m.common for m in markers if m.common)
        scope = _git_scope_for(common, markers)
        keys = git.local_config_keys(scope.get("cwd"), scope.get("git_dir"))
        try:
            return common_key, keys, list_registered(git, **scope)
        except PolicyError as exc:
            return common_key, keys, exc

    items = sorted(by_common.items())
    inspected: dict[str, tuple[list[str], Any]] = {}
    last = time.monotonic()
    with ThreadPoolExecutor(max_workers=8) as pool:
        for done, (common_key, keys, result) in enumerate(pool.map(inspect, items), 1):
            inspected[common_key] = (keys, result)
            if progress and time.monotonic() - last >= 5:
                progress(f"audit: inspected {done} of {len(items)} repositories")
                last = time.monotonic()
    return inspected


def build_report(
    scanner: Scanner,
    git: GitInspector,
    root: RootInfo | None,
    *,
    with_state: bool = False,
    progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Merge Git-marker discovery with every common repository's own worktree registry."""
    findings: list[dict[str, Any]] = []
    by_common: dict[str, list[Marker]] = {}
    nested: list[Marker] = []
    for marker in scanner.markers:
        if marker.kind in ("malformed", "dangling"):
            findings.append(
                {
                    "kind": f"{marker.kind}-marker",
                    "path": marker.path,
                    "detail": marker.detail,
                }
            )
        elif marker.kind == "submodule":
            nested.append(marker)
        elif marker.common:
            by_common.setdefault(key_of(marker.common), []).append(marker)
    repositories: list[dict[str, Any]] = []
    seen_ids: dict[str, str] = {}
    identity_root = root.path if root else Path(os.devnull)
    inspected = _inspect_registries(git, by_common, progress)
    for common_key, markers in sorted(by_common.items()):
        common = next(m.common for m in markers if m.common)
        config_keys, registered_or_error = inspected[common_key]
        entry: dict[str, Any] = {
            "common_dir": common,
            "kind": "bare" if any(m.kind == "bare" for m in markers) else "main",
            "worktrees": [],
            "config_executable_keys": config_keys,
        }
        if isinstance(registered_or_error, PolicyError):
            exc = registered_or_error
            entry["registry_error"] = exc.code
            findings.append(
                {"kind": "registry-unreadable", "path": common, "detail": exc.code}
            )
            repositories.append(entry)
            continue
        registered = registered_or_error
        main_path = registered[0].path if registered else common
        try:
            identity = resolve_identity(
                Path(common), main_path, registered, identity_root, write=False
            )
        except PolicyError as exc:
            findings.append(
                {"kind": "identity-ambiguous", "path": common, "detail": exc.code}
            )
            repositories.append(entry)
            continue
        if identity.id in seen_ids and seen_ids[identity.id] != common_key:
            findings.append(
                {"kind": "duplicate-identity", "path": common, "detail": identity.id}
            )
        seen_ids[identity.id] = common_key
        entry.update(identity=identity.id, main_path=main_path)
        if entry["config_executable_keys"]:
            findings.append(
                {
                    "kind": "executable-config",
                    "path": common,
                    "detail": ",".join(entry["config_executable_keys"]),
                }
            )
        scanned_paths = {key_of(m.path) for m in markers if m.kind == "linked"}
        registered_keys = {key_of(w.path) for w in registered}
        for wt in registered:
            is_main = wt is registered[0]
            exists = os.path.isdir(wt.path)
            row: dict[str, Any] = {
                "path": wt.path,
                "main": is_main,
                "bare": wt.bare,
                "exists": exists,
                "head": wt.head,
                "branch": wt.branch,
                "detached": wt.detached,
                "locked": wt.locked,
                "lock_reason": wt.lock_reason or None,
                "prunable": wt.prunable,
                "found_by_scan": key_of(wt.path) in scanned_paths or is_main,
            }
            if not is_main and not wt.bare:
                row["has_gitmodules"] = os.path.isfile(
                    os.path.join(wt.path, ".gitmodules")
                )
                row["in_policy"] = (
                    bool(root)
                    and Path(wt.path).parent.name == identity.id
                    and key_of(Path(wt.path).parent.parent) == key_of(identity_root)
                )
                row["vendor_directory"] = any(
                    part.lower() in VENDOR_DIRS for part in Path(wt.path).parts
                )
                row["canonical_name"] = canonical_name_for(wt)
                row["canonical_destination"] = (
                    str(
                        identity_root
                        / identity.id
                        / worktree_name(row["canonical_name"])
                    )
                    if root
                    else None
                )
                row["pointer_ok"] = exists and _pointer_owner_ok(wt.path, Path(common))
                if with_state and exists:
                    try:
                        row["state"] = worktree_state(git, wt.path)
                    except PolicyError as exc:
                        row["state_error"] = exc.code
            if not exists and not wt.prunable:
                findings.append(
                    {
                        "kind": "registered-missing",
                        "path": wt.path,
                        "detail": "registered path is absent",
                    }
                )
            elif wt.prunable:
                findings.append(
                    {
                        "kind": "registered-prunable",
                        "path": wt.path,
                        "detail": "git marks this registration prunable",
                    }
                )
            entry["worktrees"].append(row)
        for marker in markers:
            if marker.kind == "linked" and key_of(marker.path) not in registered_keys:
                findings.append(
                    {
                        "kind": "unregistered-marker",
                        "path": marker.path,
                        "detail": "a linked-worktree marker the repository does not register",
                    }
                )
        repositories.append(entry)
    ledger = scanner.ledger.as_dict()
    partial = bool(
        scanner.interrupted
        or scanner.ledger.failure_count
        or any(r["status"] != "scanned" for r in scanner.ledger.regions)
        or any(r.get("registry_error") for r in repositories)
    )
    exclusions = scanner.ledger.excluded_count + len(
        [r for r in scanner.ledger.regions if r["status"] == "excluded-storage"]
    )
    ambiguous = any(
        f["kind"]
        in (
            "identity-ambiguous",
            "duplicate-identity",
            "malformed-marker",
            "dangling-marker",
            "registry-unreadable",
        )
        for f in findings
    )
    worktree_total = sum(
        1
        for r in repositories
        for w in r["worktrees"]
        if not w["main"] and not w["bare"]
    )
    return {
        "schema": AUDIT_SCHEMA,
        "status": "partial" if partial else "complete",
        "resumable": bool(scanner.interrupted),
        "interrupted_by": scanner.interrupted,
        "worktree_root": root.as_dict() if root else None,
        "coverage": ledger,
        "repositories": repositories,
        "submodule_checkouts": len(nested),
        "findings": findings,
        "summary": {
            "repositories": len(repositories),
            "linked_worktrees": worktree_total,
            "findings": len(findings),
            "exclusions": exclusions,
            "access_failures": scanner.ledger.failure_count,
        },
        "full_machine_claim_allowed": (not partial)
        and exclusions == 0
        and not ambiguous,
    }


def run_audit(args: argparse.Namespace) -> int:
    git = GitInspector()
    try:
        root: RootInfo | None = resolve_root()
    except PolicyError as exc:
        root = None
        notice = exc.as_dict()
    else:
        notice = None
    other: list[dict[str, str]] = []
    roots = [os.path.abspath(r) for r in (args.root or [])]
    if not roots:
        roots, other = fixed_volumes()
    checkpoint = (
        Path(args.checkpoint)
        if args.checkpoint
        else state_dir()
        / f"audit-{_scan_options_digest(ScanOptions(roots, not args.deep))}.checkpoint.json"
    )
    options = ScanOptions(
        roots=roots,
        use_exclusions=not args.deep,
        max_seconds=args.max_seconds,
        max_dirs=args.max_dirs,
        dir_timeout=args.dir_timeout,
        checkpoint=checkpoint,
        resume=args.resume,
        progress=lambda text: print(text, file=sys.stderr, flush=True),
    )
    scanner = Scanner(options, other)
    scanner.run()
    report = build_report(
        scanner,
        git,
        root,
        with_state=args.with_state,
        progress=options.progress,
    )
    if notice:
        report["worktree_root_error"] = notice
        report["full_machine_claim_allowed"] = False
    if report["status"] == "complete" and checkpoint.exists():
        checkpoint.unlink()
    elif report["status"] == "partial":
        report["checkpoint"] = str(checkpoint)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        atomic_write(Path(args.output), text, exclusive=True)
    if args.json or not args.output:
        sys.stdout.write(text)
    return EXIT_OK if report["status"] == "complete" else EXIT_PARTIAL


# --------------------------------------------------------------------------- actions


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(
            "\n".join(f"{k}: {v}" for k, v in payload.items() if v is not None) + "\n"
        )


def run_path(args: argparse.Namespace) -> int:
    git = GitInspector()
    root = resolve_root()
    identity, registered = repo_context(git, args.repo, root.path, write=False)
    dest = resolve_destination(identity, args.name, root, registered)
    _emit(dest.as_dict(), args.json)
    return EXIT_OK


LOCK_WAIT_SECONDS = 15.0
STALE_LOCK_SECONDS = 600
CREATE_TIMEOUT_SECONDS = 180


class RepoLock:
    """One create or migrate operation per repository identity at a time."""

    def __init__(self, identity_id: str, wait: float = LOCK_WAIT_SECONDS) -> None:
        self.path = state_dir() / "locks" / f"{identity_id}.lock"
        self.wait = wait

    def __enter__(self) -> "RepoLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.wait
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if time.monotonic() >= deadline:
                    try:
                        age = time.time() - self.path.stat().st_mtime
                    except OSError:
                        age = 0
                    hint = (
                        f" The lock is {int(age)} seconds old; after confirming no create or migrate is running, remove {self.path.name} from the Nexus-Hub state directory."
                        if age > STALE_LOCK_SECONDS
                        else ""
                    )
                    raise PolicyError(
                        "repository-locked",
                        "another worktree operation holds this repository." + hint,
                    ) from None
                time.sleep(0.1)
                continue
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps({"pid": os.getpid(), "started": time.time()}))
            return self

    def __exit__(self, *exc: object) -> None:
        try:
            self.path.unlink()
        except OSError:
            pass


def git_write(
    git: GitInspector,
    argv: list[str],
    cwd: str,
    timeout: float = CREATE_TIMEOUT_SECONDS,
) -> GitResult:
    """Authorized Git write (worktree creation). Inherited GIT_* overrides are dropped."""
    try:
        proc = subprocess.run(
            [git.git, *argv],
            cwd=cwd,
            env=_inspection_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            **NO_WINDOW,
        )
    except subprocess.TimeoutExpired:
        return GitResult(-1, "", "timeout", True)
    except OSError as exc:
        return GitResult(-1, "", exc.__class__.__name__)
    return GitResult(proc.returncode, proc.stdout, proc.stderr)


def _checked_argument(label: str, value: str | None) -> str:
    if (
        not value
        or not value.strip()
        or value.startswith("-")
        or any(c in value for c in "\0\r\n")
    ):
        raise PolicyError(
            f"invalid-{label}", f"the {label} is empty or starts with a dash"
        )
    return value


def run_create(args: argparse.Namespace) -> int:
    git = GitInspector()
    branch, base = _checked_argument("branch", args.branch), _checked_argument(
        "base", args.base
    )
    if branch.startswith("@") or "@{" in branch:
        raise PolicyError(
            "invalid-branch", "the branch name is not a plain branch name"
        )
    root = resolve_root()
    first, _ = repo_context(git, args.repo, root.path, write=False)
    with RepoLock(first.id):
        identity, registered = repo_context(git, args.repo, root.path, write=True)
        common, top = checkout_common_dir(git, args.repo)
        dest = resolve_destination(identity, args.name, root, registered)
        scope = {"cwd": str(top)}
        if git.run(["check-ref-format", "--branch", branch], **scope).rc != 0:
            raise PolicyError("invalid-branch", "Git does not accept this branch name")
        if dest.state == "registered":
            held = next(w for w in registered if key_of(w.path) == key_of(dest.path))
            if held.branch == branch:
                payload = dest.as_dict()
                payload.update(status="exists", branch=branch, head=held.head)
                _emit(payload, args.json)
                return EXIT_OK
            raise PolicyError(
                "destination-registered-other-branch",
                "the destination already holds a different branch",
            )
        if (
            git.run(
                ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], **scope
            ).rc
            == 0
        ):
            raise PolicyError(
                "branch-exists", "the branch already exists; create a new branch name"
            )
        sha = git.run(
            ["rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"], **scope
        )
        if sha.rc != 0 or not sha.out.strip():
            raise PolicyError(
                "base-unresolved", "the base does not resolve to a commit"
            )
        dest.path.parent.mkdir(parents=True, exist_ok=True)
        made = git_write(
            git,
            [
                "-C",
                str(top),
                "worktree",
                "add",
                "-b",
                branch,
                str(dest.path),
                sha.out.strip(),
            ],
            str(top),
        )
        if made.timed_out:
            raise PolicyError(
                "git-timeout",
                "git worktree add timed out; inspect the destination before retrying",
                cannot_verify=True,
            )
        if made.rc != 0:
            raise PolicyError(
                "git-failed", f"git worktree add failed: {made.err.strip()[:200]}"
            )
        after = list_registered(git, cwd=str(top))
        landed = next((w for w in after if key_of(w.path) == key_of(dest.path)), None)
        if (
            landed is None
            or landed.branch != branch
            or not _pointer_owner_ok(str(dest.path), common)
        ):
            raise PolicyError(
                "postcondition-failed",
                "git reported success but the worktree is not registered as expected",
                cannot_verify=True,
            )
    payload = dest.as_dict()
    payload.update(status="created", branch=branch, head=landed.head)
    _emit(payload, args.json)
    return EXIT_OK


def run_list(args: argparse.Namespace) -> int:
    git = GitInspector()
    root = resolve_root()
    identity, registered = repo_context(git, args.repo, root.path, write=False)
    rows = []
    for index, wt in enumerate(registered):
        row: dict[str, Any] = {
            "path": wt.path,
            "main": index == 0,
            "branch": wt.branch,
            "detached": wt.detached,
            "head": wt.head,
            "locked": wt.locked,
            "prunable": wt.prunable,
        }
        if index and not wt.bare:
            canonical = root.path / identity.id / worktree_name(canonical_name_for(wt))
            row["canonical_destination"] = str(canonical)
            row["in_policy"] = key_of(canonical) == key_of(wt.path)
        rows.append(row)
    payload = {
        "status": "ok",
        "identity": identity.id,
        "root": str(root.path),
        "root_provenance": root.provenance,
        "worktrees": rows,
    }
    if args.json:
        _emit(payload, True)
    else:
        for row in rows:
            flag = (
                ""
                if row.get("in_policy", True)
                else f"  -> {row['canonical_destination']}"
            )
            sys.stdout.write(f"{row['path']}  [{row['branch'] or 'detached'}]{flag}\n")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-hub worktree", description="Centralized worktree policy."
    )
    sub = parser.add_subparsers(dest="action", required=True)
    path = sub.add_parser(
        "path", help="Resolve a worktree destination without writing."
    )
    path.add_argument("--repo", required=True)
    path.add_argument("--name", required=True)
    path.add_argument("--json", action="store_true")
    create = sub.add_parser(
        "create", help="Create a worktree at its canonical destination."
    )
    create.add_argument("--repo", required=True)
    create.add_argument("--branch", required=True, help="New branch to create.")
    create.add_argument("--base", required=True, help="Commit or ref to branch from.")
    create.add_argument("--name", required=True)
    create.add_argument("--json", action="store_true")
    listing = sub.add_parser(
        "list", help="Registered worktrees with canonical destinations."
    )
    listing.add_argument("--repo", required=True)
    listing.add_argument("--json", action="store_true")
    audit = sub.add_parser(
        "audit",
        help="Read-only discovery of every linked worktree with explicit coverage.",
    )
    audit.add_argument(
        "--machine",
        action="store_true",
        help="Scan every fixed local volume (default scope).",
    )
    audit.add_argument(
        "--root",
        action="append",
        help="Limit discovery to this directory (repeatable).",
    )
    audit.add_argument(
        "--deep",
        action="store_true",
        help="Disable the dependency-folder exclusion hints.",
    )
    audit.add_argument(
        "--with-state",
        action="store_true",
        help="Also fingerprint each linked worktree's state.",
    )
    audit.add_argument("--max-seconds", type=float)
    audit.add_argument("--max-dirs", type=int)
    audit.add_argument(
        "--dir-timeout",
        type=float,
        default=60.0,
        help="Seconds one directory read may take before it is abandoned and recorded.",
    )
    audit.add_argument("--checkpoint")
    audit.add_argument("--resume", action="store_true")
    audit.add_argument("--json", action="store_true")
    audit.add_argument("--output", help="Write the coverage report to this new file.")
    return parser


HANDLERS: dict[str, Callable[[argparse.Namespace], int]] = {
    "path": run_path,
    "create": run_create,
    "list": run_list,
    "audit": run_audit,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return HANDLERS[args.action](args)
    except PolicyError as exc:
        sys.stdout.write(json.dumps(exc.as_dict(), indent=2) + "\n")
        return EXIT_PARTIAL if exc.cannot_verify else EXIT_REFUSED


if __name__ == "__main__":
    sys.exit(main())
