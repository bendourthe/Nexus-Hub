#!/usr/bin/env python3
"""Decide whether a full /implement run is complete, incomplete, blocked, or paused.

Implements catalog/skills/workflow/implement-phase/references/completion-contract.md,
which owns the predicate list, the verdicts, and the run-record rules. Read the
contract before changing this file; this module does not restate the rules, it
executes them.

Subcommands:
    check <plan> [--json] [--session ID]   verdict line first, then one line per predicate
    score <plan> [--session ID]            "<met-count> <head> <latest-ci-run-id|->"
    record render <plan> --session ID [--approvals F | --action A]
                                           open an approval round; print the exact paste line
    record create|answer|pause|resume|block <plan> ...
                                           write the run record (approval-origin enforced)
    record retire <plan>                   move a per-plan record aside (never deletes it)
    members <vX.Y>                         a minor's member plans, in version order
    record render|create|answer|pause|resume|block|path --minor <vX.Y> ...
                                           the schema-2 minor record (completion_minor.py)
    record member-start --minor <vX.Y> --member <vX.Y.Z> --session ID --head SHA
                                           pass the member gate; record the member's start_head
    record add-class --minor <vX.Y> --session ID --class archive-member [--text LINE]
                                           add one class to a running minor record from the
                                           user's pasted `record render --action add-class` line
    check-minor <vX.Y> [--json] [--session ID]
                                           the minor verdict, then per-member and minor lines
    score-minor <vX.Y> [--session ID]      the minor's progress score

Exit codes: 0 PLAN COMPLETE (or MINOR COMPLETE), 1 INCOMPLETE, 3 BLOCKED, 4 PAUSED, 2 malformed input.

Output never carries free text from the plan, the gaps file, git, or gh: only
fixed predicate ids and statuses, so a gate can hand it to a model safely.
"""

from __future__ import annotations

import argparse
import tempfile
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
import datetime as dt
import hashlib
import hmac
import importlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from types import MappingProxyType, ModuleType, SimpleNamespace

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import approval_binding
import approval_page
import repo_host

EXIT_COMPLETE, EXIT_INCOMPLETE, EXIT_MALFORMED, EXIT_BLOCKED, EXIT_PAUSED = (
    0,
    1,
    2,
    3,
    4,
)
SCHEMA = 1
SCHEMA_MINOR = 2
BUDGET_SECONDS = 20.0

BLOCKER_CATEGORIES = (
    "approval-not-covered",
    "unreproducible-red-check",
    "user-edit-guard",
    "destructive-outside-approval",
    "ci-security-change",
    "no-progress",
    "record-tampered",
    "platform-unavailable",
)
APPROVAL_CLASSES = {
    "push-merge",
    "release",
    "repush",
    "release-notes",
    "refactor-moves",
    "spend",
    "defer-gaps",
    "unattended-with-bypass",
    # Minor-level classes (schema 2). `cleanup-merged` is also offered to a one-plan run.
    "cleanup-merged",
    "carry-gaps",
    "gap-migration",
    "archive-minor",
    "minor-close-pr",
    # Optional, unbound, and valid only beside `archive-minor`: archive each member as it
    # is released (completion contract, "Member archive").
    "archive-member",
}
MINOR_ONLY_CLASSES = {"gap-migration", "archive-minor", "minor-close-pr", "archive-member"}
# A one-plan run that is the last of its minor archives it through the same two
# classes; `carry-gaps` records the gaps a one-plan run leaves open in the next
# version (completion contract, "Single-plan carry and archive").
PLAN_CLOSE_CLASSES = {"archive-minor", "minor-close-pr"}
PLAN_ONLY_CLASSES = {"carry-gaps"}

# On Windows, a console program started by a process with no console of its own
# (a hook or agent launched without one, or a detached test) opens a visible
# window that takes keyboard focus. Every child here has its output captured and
# its prompts disabled, so it never needs a window.
NO_WINDOW: dict = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
GAP_TYPES = {"NI", "DF", "BG", "MT", "WN", "QG"}
REQUIRED_SECTIONS = (
    "Architecture refactor",
    "Known-gaps reconciliation",
    "Living docs architecture",
    "Git-tree hygiene",
    "CI/CD coverage",
    "Tier 3 deep pass",
    "Goal-vs-codebase review",
    "Human/manual testing suggestions",
    "Full-suite testing and stabilization",
    "Publication and integration",
)

PLAN_REL_RE = re.compile(r"^docs/(?:[^/]+/)*plans/[^/]+\.md$")
TASK_RE = re.compile(r"^- \[([ xX])\]\s+(T\d{3,})\b(.*)$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^(\s*- )\[[ xX]\]", re.MULTILINE)
STATUS_LINE_RE = re.compile(r"^\*\*Status\*\*:[^\n]*$", re.MULTILINE)
STATUS_VALUE_RE = re.compile(
    r"^\*\*Status\*\*:[ \t]*(`?)(queued|in-progress|complete|superseded|shipped|blocked)\1[ \t]*\r?$"
)
FIRST_SECTION_RE = re.compile(r"^## ", re.MULTILINE)
VERSION_RE = re.compile(r"^\*\*Version\*\*:\s*(v?\d+\.\d+\.\d+)", re.MULTILINE)
SLUG_RE = re.compile(r"^\*\*Slug\*\*:\s*(\S+)", re.MULTILINE)
GAP_ITEM_RE = re.compile(r"^#### (?P<type>[A-Z]{2})-\d+\b(?P<title>.*)$", re.MULTILINE)


import runpy as _process_runpy
from pathlib import Path as _ProcessPath

_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[0] / "nexus_process.py"))
_PROCESS_POLICY["install_no_window_default"]()


class Malformed(Exception):
    """Input the contract says must exit 2."""


class Budget:
    def __init__(self, seconds: float) -> None:
        self.deadline = time.monotonic() + seconds

    def remaining(self) -> float:
        return max(0.0, self.deadline - time.monotonic())


# --------------------------------------------------------------------------- tools


def _runs_dir() -> Path:
    override = os.environ.get("NEXUS_HUB_RUNS_DIR")
    return Path(override) if override else Path.home() / ".nexus-hub" / "runs"


def _env() -> dict[str, str]:
    env = dict(os.environ)
    # WN-13: inherited Git repository selectors must not redirect record checks.
    for name in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES", "GIT_PREFIX", "GIT_NAMESPACE", "GIT_EXEC_PATH",
        "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS",
    ):
        env.pop(name, None)
    for name in tuple(env):
        if name.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")):
            env.pop(name)
    env.update(
        GH_PROMPT_DISABLED="1",
        GIT_TERMINAL_PROMPT="0",
        NO_COLOR="1",
        GH_NO_UPDATE_NOTIFIER="1",
    )
    return env


def _run(argv: list[str], budget: Budget, cwd: Path | None = None) -> tuple[int, str]:
    """Run a command inside the shared budget; (rc, stdout). rc -1 means it did not run."""
    rc, out, _err = _run_with_stderr(argv, budget, cwd)
    return rc, out


def _run_with_stderr(
    argv: list[str], budget: Budget, cwd: Path | None = None
) -> tuple[int, str, str]:
    """Like `_run`, also returning stderr; (rc, stdout, stderr)."""
    timeout = budget.remaining()
    if timeout <= 0:
        return -1, "", ""
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            env=_env(),
            capture_output=True,
            text=True,
            check=False,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            **NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return -1, "", ""
    return proc.returncode, proc.stdout, proc.stderr


# --------------------------------------------------------------------------- plan


def plan_hash_text(text: str) -> str:
    """sha256 of a plan with every checkbox and the header Status value normalized.

    Ticks and the Status value change as the run progresses, so neither counts as an
    edit. Only the FIRST `**Status**:` line above the first `## ` heading is
    normalized, and only when its whole value is one known token (optionally in
    backticks); any other text on it, and every other Status line, is hashed, so an
    instruction appended there is an edit like any other.
    """
    text = CHECKBOX_RE.sub(r"\1[ ]", text)
    section = FIRST_SECTION_RE.search(text)
    header_end = section.start() if section else len(text)
    status = STATUS_LINE_RE.search(text, 0, header_end)
    if status and STATUS_VALUE_RE.match(status.group(0)):
        text = text[: status.start()] + "**Status**:" + text[status.end() :]
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def legacy_plan_hash_text(text: str) -> str:
    """The pre-v4.13.6 hash (checkboxes only), still accepted for older records."""
    return hashlib.sha256(CHECKBOX_RE.sub(r"\1[ ]", text).encode("utf-8")).hexdigest()


def record_key(root: Path, repo: str, scope: str) -> str:
    """sha256 of the repository root, the resolved owner/repo, and `plan:<path>` or `minor:vX.Y`."""
    return hashlib.sha256("\n".join((str(root), repo, scope)).encode("utf-8")).hexdigest()


class RepoContext:
    """The repository a check runs in: absolute tools, remotes, and the record key repo."""

    def __init__(self, start: Path, budget: Budget) -> None:
        self.budget = budget
        self.notices: list[str] = []
        self.git = repo_host.absolute_tool("git", None)
        if not self.git:
            raise Malformed("git not found")
        rc, out = _run([self.git, "-C", str(start), "rev-parse", "--show-toplevel"], budget)
        if rc == -1:
            raise _minor_module().ObservationUnavailable("repository")
        if rc != 0:
            raise Malformed("plan is not inside a git repository")
        self.root = Path(out.strip()).resolve()
        # Re-resolve git outside the tree now that the tree is known.
        self.git = repo_host.absolute_tool("git", self.root)
        if not self.git:
            raise Malformed("git resolves inside the working tree; refusing")
        self.gh = repo_host.absolute_tool("gh", self.root)
        self.remote_url = self._git_out("remote", "get-url", "origin")
        self.push_remote_url = self._git_out("remote", "get-url", "--push", "--all", "origin")
        self._default_repo: str | None = None
        self._key_repo: str | None = None

    def run(self, argv: list[str], cwd: Path | None = None) -> tuple[int, str]:
        return _run(argv, self.budget, cwd)

    @property
    def default_repo(self) -> str:
        """The verified origin repository, resolved only when no frozen repo exists."""
        if self._default_repo is None:
            repo, _reason = repo_host.resolve_repo(
                self.root, git=self.git, gh=self.gh or "", run=self.run
            )
            self._default_repo = repo or ""
        return self._default_repo

    @property
    def key_repo(self) -> str:
        """The owner/repo a record key names: the verified push URL's, else the fetch URL's.

        No `gh` call, so the key does not depend on the network; an unresolvable
        remote keys on the empty string.
        """
        if self._key_repo is None:
            self._key_repo = (
                self.url_repo(self.push_remote_url) or self.url_repo(self.remote_url) or ""
            ).lower()
        return self._key_repo

    def url_repo(self, url: str) -> str | None:
        """The verified repository one remote URL names, or None.

        An SSH alias is resolved with the ssh git itself runs (v4.13.5 WN-2).
        """
        repo, _reason = repo_host.repo_from_url(
            url, repo_root=self.root, run=self.run, git=self.git
        )
        return repo

    def _git_out(self, *args: str) -> str:
        rc, out = _run([self.git, "-C", str(self.root), *args], self.budget)
        return out.strip() if rc == 0 else ""

    def scoped_record_path(self, scope: str) -> Path:
        return _runs_dir() / f"{record_key(self.root, self.key_repo, scope)}.json"


class Context(RepoContext):
    def __init__(self, plan_arg: str, budget: Budget) -> None:
        plan = Path(plan_arg).expanduser()
        if not plan.is_file():
            raise Malformed(f"plan not found: {plan_arg}")
        self.plan = plan.resolve()
        super().__init__(self.plan.parent, budget)
        self.rel = self.plan.relative_to(self.root).as_posix()
        if not PLAN_REL_RE.match(self.rel):
            raise Malformed("plan path must match docs/**/plans/*.md")
        try:
            self.text = self.plan.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise Malformed(f"plan unreadable: {exc.__class__.__name__}") from exc
        self.tasks = [
            (tid, mark.lower() == "x", _task_path(rest))
            for mark, tid, rest in TASK_RE.findall(self.text)
        ]
        if not self.tasks:
            raise Malformed("plan has no T### task lines")
        found = VERSION_RE.search(self.text)
        if not found:
            raise Malformed("plan has no **Version** line")
        self.version = (
            found.group(1) if found.group(1).startswith("v") else "v" + found.group(1)
        )
        slug = SLUG_RE.search(self.text)
        self.slug = slug.group(1) if slug else self.plan.stem
        self.version_dir = self.plan.parent.parent

    def plan_hash(self) -> str:
        """The plan hash a new record freezes (see `plan_hash_text`)."""
        return plan_hash_text(self.text)

    def plan_hash_matches(self, frozen: object) -> bool:
        """True when a frozen hash equals the current plan under either hash rule."""
        return frozen in (plan_hash_text(self.text), legacy_plan_hash_text(self.text))

    def record_paths(self) -> list[Path]:
        """[the `plan:<path>` key, the pre-v4.13.6 key], in lookup order."""
        return plan_record_paths(self.root, self.key_repo, self.remote_url, self.rel)

    def record_path(self) -> Path:
        """The existing record for this plan, else where a new one is written."""
        paths = self.record_paths()
        found = next((p for p in paths if p.is_file()), None)
        if found is None:
            found = find_record_by_content(
                self.root, lambda r: r.get("schema") == SCHEMA and r.get("plan") == self.rel
            )
        return found or paths[0]


def find_records_by_content(root: Path, match: Callable[[dict], bool]) -> list[Path]:
    """Every record for this repository root that `match` accepts, wherever its key points.

    The key names the resolved owner/repo, which a remote-URL change moves. Without
    this lookup a changed remote would hide the record, and the run would read as
    having none instead of reporting `approval.remote unmet`; and a per-plan record
    off its key would be invisible to the one-authority rule.
    """
    runs = _runs_dir()
    if not runs.is_dir():
        return []
    found: list[Path] = []
    for path in sorted(runs.glob("*.json")):
        if path.name.endswith(".gate.json"):
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeDecodeError):
            continue
        if isinstance(record, dict) and record.get("repo_root") == str(root) and match(record):
            found.append(path)
    return found


def find_record_by_content(root: Path, match: Callable[[dict], bool]) -> Path | None:
    """The first record `find_records_by_content` returns, or None."""
    return next(iter(find_records_by_content(root, match)), None)


def plan_record_files(root: Path, key_repo: str, remote_url: str, rel: str) -> list[Path]:
    """Every existing per-plan record for `rel`: its keys, then any found by content."""
    found = [p for p in plan_record_paths(root, key_repo, remote_url, rel) if p.is_file()]
    for path in find_records_by_content(
        root, lambda r: r.get("schema") == SCHEMA and r.get("plan") == rel
    ):
        if path not in found:
            found.append(path)
    return found


def plan_record_paths(root: Path, key_repo: str, remote_url: str, rel: str) -> list[Path]:
    """Where a per-plan record lives: the v4.13.6 key first, then the legacy key.

    The legacy key hashed the root, the raw fetch URL, and the path; it is still read
    so a run recorded before the upgrade keeps its authority.
    """
    legacy = hashlib.sha256("\n".join((str(root), remote_url, rel)).encode("utf-8")).hexdigest()
    return [
        _runs_dir() / f"{record_key(root, key_repo, 'plan:' + rel)}.json",
        _runs_dir() / f"{legacy}.json",
    ]


def _task_path(rest: str) -> str:
    tokens = rest.split()
    return tokens[-1] if tokens else ""


# --------------------------------------------------------------------------- record


def _secret(create: bool) -> bytes | None:
    path = _runs_dir() / ".secret"
    if path.is_file():
        return path.read_bytes()
    if not create:
        return None
    _runs_dir().mkdir(parents=True, exist_ok=True)
    _restrict(_runs_dir(), directory=True)
    path.write_bytes(secrets.token_bytes(32))
    _restrict(path, directory=False)
    return path.read_bytes()


# One owner-only helper for records and pending approval rounds alike.
_restrict = approval_binding.restrict


def _canonical(obj: object) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


_SIGNED_FIELDS = (
    "approvals",
    "plan_sha256",
    "session_id",
    "repo",
    "deferrable_gap_types",
    # Fixed at `record create` and never rewritten: deleting `start_head` turned
    # every ticked task `met` with no commit check.
    "start_head",
    "nonce",
    "created",
)
# A schema-2 record also signs what makes it a minor record, so removing `scope`,
# `minor`, or a member, or relabelling it schema 1, fails verification. `excluded`
# is signed because it decides which late plans count as approved exclusions, and
# `completed` because it ends the record's authority (a forged one would silence it).
_SIGNED_MINOR_FIELDS = ("schema", "scope", "minor", "members", "excluded", "completed")


def _hmac_payload(record: dict) -> dict:
    fields = _SIGNED_FIELDS
    if record.get("schema") == SCHEMA and "completed" in record:
        # The completion stamp ends a one-plan record's liveness, so it is signed once
        # present; a record without it signs exactly as before and still verifies.
        fields = _SIGNED_FIELDS + ("completed",)
    if record.get("schema") != SCHEMA:
        # Anything that is not a schema-1 record signs the minor fields too; a schema-1
        # payload stays exactly as it was, so existing records still verify.
        fields = _SIGNED_FIELDS + _SIGNED_MINOR_FIELDS
    if record.get("schema") != SCHEMA and "implementation_controller" in record:
        fields += ("implementation_controller",)
    return {k: record.get(k) for k in fields}


def _sign(record: dict, key: bytes) -> str:
    return hmac.new(key, _canonical(_hmac_payload(record)), hashlib.sha256).hexdigest()



# Schema-2 mutation snapshots remain outside the signed JSON payload.
class MinorConflict(Malformed):
    """A stale or foreign controller must retry from a fresh verified snapshot."""


class MinorSnapshot(dict):
    def __init__(self, record: dict, path: Path, raw: bytes, ctx: RepoContext) -> None:
        super().__init__(record)
        self.record_path = path.resolve()
        self.loaded_sha256 = hashlib.sha256(raw).hexdigest()
        self.context = ctx


_MINOR_LEASE = ContextVar('minor_record_lease', default=None)


@contextmanager
def _minor_os_lock(lock_path: Path, budget):
    """One bounded stdlib OS lease; persistent sidecar is never stolen or deleted."""
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    _restrict(lock_path.parent, directory=True)
    handle = lock_path.open('a+b')
    locked = False
    try:
        _restrict(lock_path, directory=False)
        if lock_path.stat().st_size == 0:
            handle.write(b'0')
            handle.flush()
        deadline = time.monotonic() + min(3.0, budget.remaining())
        while True:
            handle.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
                break
            except OSError as exc:
                if time.monotonic() >= deadline:
                    raise MinorConflict('minor-record-busy') from exc
                time.sleep(0.025)
        yield
    finally:
        try:
            if locked:
                handle.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


@contextmanager
def minor_creation_lease(ctx: RepoContext, token: str):
    """All linked roots serialize first discovery and creation for this minor."""
    cm = _minor_module()
    cm.parse_minor(sys.modules[__name__], token)
    common = cm._common_dir(ctx, ctx.root)
    if not common or not Path(common).is_absolute() or str(Path(common).resolve()) != common:
        raise MinorConflict('creation-common-directory-unavailable')
    identity = hashlib.sha256(_canonical([os.path.normcase(common), 'minor:' + token])).hexdigest()
    lock_path = _runs_dir() / 'creation-locks' / (identity + '.lock')
    with _minor_os_lock(lock_path, ctx.budget):
        yield


@contextmanager
def minor_lease(path: Path, expected: str | None, ctx: RepoContext):
    """Full-byte CAS under the unchanged original-record-adjacent lease."""
    path = path.resolve()
    active = _MINOR_LEASE.get()
    if active is not None:
        if active['path'] != path:
            raise MinorConflict('nested-minor-record-conflict')
        yield active
        return
    with _minor_os_lock(path.with_name(path.stem + '.mutation.lock'), ctx.budget):
        raw = path.read_bytes() if path.exists() else None
        actual = hashlib.sha256(raw).hexdigest() if raw is not None else None
        if actual != expected:
            raise MinorConflict('minor-record-changed')
        current = json.loads(raw) if raw is not None else None
        if current is not None:
            _minor_module().require_controller(sys.modules[__name__], ctx, current, path)
        active = {'path': path, 'expected': expected, 'ctx': ctx}
        token = _MINOR_LEASE.set(active)
        try:
            yield active
            latest = path.read_bytes() if path.exists() else None
            latest_digest = hashlib.sha256(latest).hexdigest() if latest is not None else None
            if latest_digest != active['expected']:
                raise MinorConflict('minor-record-changed')
        finally:
            _MINOR_LEASE.reset(token)


@contextmanager
def minor_transaction(record: MinorSnapshot):
    if not isinstance(record, MinorSnapshot):
        raise MinorConflict('minor-snapshot-required')
    with minor_lease(record.record_path, record.loaded_sha256, record.context) as lease:
        yield lease


def minor_operation(function):
    """Serialize native minor entry points before consuming genuine input."""
    @wraps(function)
    def wrapped(args):
        if not _scoped(args):
            return function(args)
        cm = _minor_module()
        ctx = cm.repo_context(sys.modules[__name__], args)
        path = cm.record_file(sys.modules[__name__], ctx, args.minor)
        raw = path.read_bytes() if path.exists() else None
        expected = hashlib.sha256(raw).hexdigest() if raw is not None else None
        with minor_lease(path, expected, ctx):
            return function(args)
    return wrapped


def resolve_minor_controller(path: Path, session: str, *, budget_seconds: float = BUDGET_SECONDS) -> tuple[RepoContext, MinorSnapshot]:
    """Trusted siblings resolve execution identity; raw JSON is only a lookup hint."""
    raw = path.read_bytes()
    record = json.loads(raw)
    key = _secret(create=False)
    if (not isinstance(record, dict) or key is None
            or not hmac.compare_digest(str(record.get('approvals_hmac', '')), _sign(record, key))
            or record.get('session_id') != session):
        raise MinorConflict('record-tampered-or-session-mismatch')
    binding = record.get('implementation_controller') or {}
    root = Path(str(binding.get('repo_root') or record.get('repo_root', '')))
    ctx = RepoContext(root, Budget(min(BUDGET_SECONDS, budget_seconds)))
    cm = _minor_module()
    snapshot = MinorSnapshot(record, path, raw, ctx)
    cm.require_controller(sys.modules[__name__], ctx, snapshot, snapshot.record_path)
    if not cm._verified(sys.modules[__name__], ctx, snapshot.get('minor'), snapshot):
        raise MinorConflict('minor-authority-unverified')
    return ctx, snapshot


def historical_host_cwds(record: dict) -> set[str]:
    """Caller supplies only an authenticated record; no unsigned redirect confers authority."""
    binding = record.get('implementation_controller') or {}
    origin = binding.get('origin_root')
    return {str(Path(origin).resolve())} if isinstance(origin, str) else set()


def _write_record(path: Path, record: dict) -> None:
    minor = record.get('schema') == SCHEMA_MINOR and record.get('scope') == 'minor'
    if not minor:
        path.parent.mkdir(parents=True, exist_ok=True)
        _restrict(path.parent, directory=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        _restrict(tmp, directory=False)
        os.replace(tmp, path)

        return
    active = _MINOR_LEASE.get()
    if minor and active is None:
        with minor_transaction(record):
            _write_record(path, record)
        return
    if minor:
        path = path.resolve()
        if active['path'] != path:
            raise MinorConflict('minor-record-path-changed')
        if isinstance(record, MinorSnapshot) and record.loaded_sha256 != active['expected']:
            raise MinorConflict('minor-snapshot-changed')
        raw = path.read_bytes() if path.exists() else None
        actual = hashlib.sha256(raw).hexdigest() if raw is not None else None
        if actual != active['expected']:
            raise MinorConflict('minor-record-changed')
        key = _secret(create=False)
        if key is None or not hmac.compare_digest(str(record.get('approvals_hmac', '')), _sign(record, key)):
            raise MinorConflict('unsigned-minor-write')
        previous = json.loads(raw) if raw is not None else {}
        _minor_module().check_historical_scope_write(sys.modules[__name__], active['ctx'], previous, record)
        _minor_module().check_manifest_permission_write(sys.modules[__name__], active['ctx'], previous, record)
        _minor_module().check_v415_compatibility_write(sys.modules[__name__], active['ctx'], previous, record)
    path.parent.mkdir(parents=True, exist_ok=True)
    _restrict(path.parent, directory=True)
    descriptor, name = tempfile.mkstemp(prefix=path.stem + '.', suffix='.tmp', dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write('\n')
        _restrict(tmp, directory=False)
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)
    if minor:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        active['expected'] = digest
        if isinstance(record, MinorSnapshot):
            record.loaded_sha256 = digest


class RecordState:
    """The loaded record plus the verdict its state forces, if any."""

    def __init__(self) -> None:
        self.record: dict | None = None
        self.forced: tuple[str, int] | None = None  # (verdict line, exit code)
        self.notices: list[str] = []


TAMPERED = ("BLOCKED: record-tampered", EXIT_BLOCKED)


def read_record(ctx: RepoContext, path: Path) -> dict | None:
    """The raw record at `path`, or None when it sits in a working tree or is unreadable.

    Callers treat None for an existing file as `record-tampered`. Unavailable
    Git provenance raises ObservationUnavailable instead of asserting integrity.
    """
    rc, out = _run(
        [ctx.git, "-C", str(path.parent), "rev-parse", "--is-inside-work-tree"],
        ctx.budget,
    )
    if rc == -1:
        raise _minor_module().ObservationUnavailable("record.provenance")
    if rc == 0 and out.strip() == "true":
        tracked_rc, _ = _run(
            [ctx.git, "-C", str(path.parent), "ls-files", "--error-unmatch", "--", path.name],
            ctx.budget,
        )
        if tracked_rc == -1:
            raise _minor_module().ObservationUnavailable("record.provenance")
        if tracked_rc != 1:
            return None
    try:
        raw = path.read_bytes()
        record = json.loads(raw)
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    if not isinstance(record, dict):
        return None
    return MinorSnapshot(record, path, raw, ctx) if record.get("schema") == SCHEMA_MINOR else record


def load_record(ctx: Context, session: str | None) -> RecordState:
    """Load this plan's record, dispatching on `schema`.

    Schema 1 is the per-plan record, unchanged. A schema-2 (minor) record lives
    under a `minor:vX.Y` key and is loaded by `completion_minor.load_minor`; one
    found under a plan key is tampered, as is any unknown schema.
    """
    state = RecordState()
    path = ctx.record_path()
    if not path.is_file():
        return state
    record = read_record(ctx, path)
    if record is None or record.get("schema") != SCHEMA:
        state.forced = TAMPERED
        return state
    return _load_schema1(ctx, record, session, state)


def _load_schema1(
    ctx: Context, record: dict, session: str | None, state: RecordState
) -> RecordState:
    tampered = TAMPERED
    if session and record.get("session_id") != session:
        state.notices.append("run record bound to another session ignored")
        return state
    key = _secret(create=False)
    if (
        record.get("schema") != SCHEMA
        or key is None
        or not ctx.plan_hash_matches(record.get("plan_sha256"))
        or not hmac.compare_digest(
            str(record.get("approvals_hmac", "")), _sign(record, key)
        )
    ):
        state.forced = tampered
        return state
    # No expiry: an approval holds until its run completes or the user retires it
    # (completion contract, "Run record lifetime"), however long the run takes.
    state.record = record
    if record.get("pause"):
        state.forced = ("PAUSED", EXIT_PAUSED)
        return state
    open_blockers = [b for b in record.get("blockers", []) if b.get("open")]
    if open_blockers:
        state.forced = (f"BLOCKED: {open_blockers[0]['category']}", EXIT_BLOCKED)
    return state


def project(record: dict, version: str) -> dict | None:
    """The per-plan view of a record, so `evaluate`, the gates, and the runner keep one path.

    A schema-1 record is its own view. A schema-2 record yields the member whose
    `version` matches (members are identified by version, never by path), with the
    record's frozen remote and repository and the member's own branches, tag,
    cleanup, and classes plus the minor-level classes. Returns None when no member
    has that version.
    """
    if record.get("schema") == SCHEMA:
        return record
    member = next(
        (m for m in record.get("members") or [] if isinstance(m, dict) and m.get("version") == version),
        None,
    )
    if member is None:
        return None
    minor = record.get("approvals") or {}
    own = member.get("approvals") or {}
    cleanup = own.get("cleanup") or {"branches": [], "worktrees": []}
    archives = [{"version": m.get("version"), "archived": m["archived"]} for m in record.get("members") or []
                if isinstance(m, dict) and isinstance(m.get("archived"), dict)]
    approvals = {
        "plan": member.get("plan_path"),
        "remote_url": minor.get("remote_url"),
        "push_remote_url": minor.get("push_remote_url"),
        "repo": record.get("repo"),
        "source_branch": member.get("source_branch"),
        "target_branch": member.get("target_branch") or "develop",
        "release_version": member.get("release_version") or version,
        "tag": member.get("tag") or version,
        "cleanup": cleanup,
        "classes": [*(own.get("classes") or []), *(minor.get("classes") or [])],
        "authorization_context": minor.get('authorization_context'),
        "autonomy_policy": minor.get('autonomy_policy'),
        "page_sha256": minor.get("page_sha256"),
    }
    return {
        "schema": record.get("schema"),
        "scope": "member",
        "version": member["version"],
        "plan_path": member.get("plan_path"),
        "member_start_head": member.get("start_head"),
        "minor": record.get("minor"),
        "plan": member.get("plan_path"),
        "plan_sha256": member.get("plan_sha256"),
        "repo_root": record.get("repo_root"),
        "remote_url": record.get("remote_url"),
        "repo": record.get("repo"),
        "session_id": record.get("session_id"),
        "worktree": (member.get("implementation") or {}).get("worktree") or member.get("worktree") or record.get("worktree"),
        "start_head": member.get("start_head") or (member.get("implementation") or {}).get("base_head") or record.get("start_head"),
        # Ordinary new gaps never migrate; exact frozen recording tasks have a separate disposition.
        "minor_start_head": record.get("start_head"),
        "nonce": record.get("nonce"),
        "created": record.get("created"),
        "approvals": approvals,
        # Minor runs have no deferrable state: a gap is fixed or migrated.
        "deferrable_gap_types": [],
        "cleanup": cleanup,
        "blockers": record.get("blockers") or [],
        "pause": record.get("pause"),
        # A member archived on release carries its signed archived identity, and the view
        # carries every member's, so no archive commit counts as this member's task work;
        # a record where no member has one projects exactly as before.
        **({"archived": member["archived"]} if "archived" in member else {}),
        **({"member_archives": archives} if archives else {}),
    }


def _parse_time(value: object) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- predicates


def evaluate(ctx: Context, record: dict | None, *, task_authority: V415TaskAuthority | None = None) -> tuple[list[tuple[str, str]], int]:
    """Return ([(predicate id, status)], deferred item count)."""
    results: list[tuple[str, str]] = []
    approvals = (record or {}).get("approvals", {})
    start = (record or {}).get("start_head")
    for tid, checked, path in ctx.tasks:
        results.append((f"task.{tid}", _task_status(ctx, checked, path, start, record,
                                                 task_id=tid, task_authority=task_authority)))
    gaps_status, deferred = _gaps_status(ctx, record)
    results.append(("gaps.version", gaps_status))
    evidence = _evidence_file(ctx, record)
    results.append(
        ("evidence.file", "met" if evidence and _has_sections(evidence) else "unmet")
    )
    results.append(("tests.evidence", _tests_status(ctx, evidence, start)))
    results.append(("approval.remote", _approved_remote_status(ctx, record)))
    repo = approvals.get("repo") or ctx.default_repo
    branch = approvals.get("source_branch") or f"feat/{ctx.version}-{ctx.slug}"
    target = approvals.get("target_branch") or "develop"
    results.append(("integration.merged", _pr_merged(ctx, repo, branch)))
    results.append(("integration.checks", _pr_checks(ctx, repo, branch, target, start)))
    tag = approvals.get("tag") or ctx.version
    results.append(("release.tag", _tag_status(ctx, tag)))
    results.append(("release.changelog", _changelog_status(ctx)))
    results.append(("release.version-sync", _version_sync(ctx, start)))
    results.append(("release.github", _release_status(ctx, repo, tag)))
    results.append(("release.main", _main_contains(ctx, tag)))
    cleanup = approvals.get("cleanup") or {}
    results.append(
        ("cleanup.branches", _branches_gone(ctx, cleanup.get("branches") or [branch]))
    )
    results.append(
        ("cleanup.worktree", _worktrees_gone(ctx, cleanup.get("worktrees"), branch))
    )
    classes = {c.get("class") for c in approvals.get("classes") or [] if isinstance(c, dict)}
    # A minor member's projection never carries it: the minor verdict owns the final pass.
    if record is not None and record.get("schema") == SCHEMA and "cleanup-merged" in classes:
        results.append(("cleanup.merged", _cleanup_merged_status(ctx, record, repo, branch)))
    if record is None or record.get("schema") == SCHEMA:
        results += _plan_close_results(ctx, record, repo)
    return results, deferred


def _plan_close_results(ctx: Context, record: dict | None, repo: str) -> list[tuple[str, str]]:
    """`gaps.carried`, `archive.minor`, and `archive.empty-dirs` for a one-plan run.

    A minor member's projection never reaches here: the minor close owns its gaps
    and its archive (completion contract, "Single-plan carry and archive").
    """
    cm, me = _minor_module(), sys.modules[__name__]
    last = cm.last_plan_status(me, ctx, ctx.version, repo)
    results = [("gaps.carried", cm.gaps_carried_status(me, ctx, ctx.version, record, last))]
    if last == "unmet":
        return results + [("archive.minor", "n/a"), ("archive.empty-dirs", "n/a")]
    if last == "cannot-verify":
        return results + [("archive.minor", "cannot-verify"), ("archive.empty-dirs", "cannot-verify")]
    token = "v{}.{}".format(*cm.minor_of(ctx.version))
    return results + [
        ("archive.minor", cm.archive_minor_status(me, ctx, token, record)),
        ("archive.empty-dirs", cm.empty_dirs_status(ctx)),
    ]


def _approved_remote_status(ctx: RepoContext, record: dict | None) -> str:
    if record is None:
        return "cannot-verify"
    if record.get("schema") == SCHEMA_MINOR and record.get("scope") == "minor":
        # An authenticated parent has no single branch: verify every frozen member route.
        members = record.get("members")
        if not isinstance(members, list) or not members:
            return "cannot-verify"
        views, versions = [], set()
        for member in members:
            if (not isinstance(member, dict)
                    or not re.fullmatch(r"v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", str(member.get("version", "")))
                    or not isinstance(member.get("approvals"), dict)):
                return "cannot-verify"
            version = member["version"]
            if version in versions:
                return "cannot-verify"
            versions.add(version)
            view = project(record, version)
            branch = (view or {}).get("approvals", {}).get("source_branch")
            if not isinstance(branch, str) or not branch.strip():
                return "cannot-verify"
            views.append(view)
        statuses = [_approved_remote_status(ctx, view) for view in views]
        if all(status == "met" for status in statuses):
            return "met"
        return "unmet" if all(status in {"met", "unmet"} for status in statuses) else "cannot-verify"
    approvals = record.get("approvals", {})
    expected_url = approvals.get("push_remote_url")
    if not expected_url or ctx.push_remote_url != expected_url:
        return "unmet"
    branch = str(approvals.get("source_branch") or f"feat/{ctx.version}-{ctx.slug}")
    # v4.13.5 WN-2 and WN-3: the push must go to origin, over a route no override
    # can redirect, to a host resolved with the ssh git itself runs.
    status, pushed_repo, reason = repo_host.verify_push_route(
        ctx.root, ctx.push_remote_url, git=ctx.git, run=ctx.run, branch=branch
    )
    if status != "met":
        ctx.notices.append(f"approval.remote {status}: {reason}")
        return status
    approved_repo = str(approvals.get("repo") or "")
    return "met" if pushed_repo and pushed_repo.lower() == approved_repo.lower() else "unmet"


# A plan can name a dated record it creates (a decision record) by its template, for
# example `docs/decisions/proposed/policy/YYYY-MM-DD-slug.md`, because the date is not
# known when the plan is frozen. No file can carry that literal name.
DATE_PLACEHOLDER = "YYYY-MM-DD"


_V415_ORIGINAL_HASHES = MappingProxyType({
    "v4.15.0": "9a60e8e3d6d608306b431ff13d5dd5355d38c463bbcab16e0bd99b7118330dc8",
    "v4.15.1": "5a2fc4e94d87d3f7863b16224c80dee5973cade81172fcd0823a358f3532f451",
    "v4.15.2": "bd1c0f917b1844cf47e903d7c9b40b7f4f5edf31a9c99591ef7a6215aa0ab835",
    "v4.15.3": "97a8f0a291eb844deaa2daf679dd3b8176936f476cc98af662eb1c44931d2cbe",
    "v4.15.4": "40abcad912dc8ee9b72866832103ae3f896bc597898ae63508bcdd002a85da2c",
})
# These are individually reviewed literals, never a release-prefix substitution.
_V415_TASK_TARGETS = MappingProxyType({
    **{("v4.15.1", tid, old): new for tids, old, new in (
        (("T101", "T105"), "docs/releases/v4/v4.16/development/detection-evidence.md", "docs/releases/v4/v4.15/development/detection-evidence.md"),
        (("T102", "T103"), "docs/releases/v4/v4.16/development/injection-prototype.md", "docs/releases/v4/v4.15/development/injection-prototype.md"),
        (("T104",), "docs/releases/v4/v4.16/development/profile-layer-trust-audit.md", "docs/releases/v4/v4.15/development/profile-layer-trust-audit.md"),
        (("T106", "T109", "T110", "T112", "T113", "T115", "T116", "T117", "T118", "T119"), "docs/releases/v4/v4.16/development/last-phase-evidence.md", "docs/releases/v4/v4.15/development/v4.15.1-last-phase-evidence.md"),
        (("T111",), "docs/releases/v4/v4.16/known-gaps.md", "docs/releases/v4/v4.15/known-gaps.md"),
        (("T107",), "docs/decisions/implemented/policy/2026-09-14-model-adaptive-runtime-platform-scope.md", "docs/decisions/proposed/policy/2026-10-31-model-adaptive-runtime-platform-scope.md"),
        (("T108",), "docs/decisions/implemented/policy/2026-09-14-model-adaptive-runtime-platform-scope.md", "docs/decisions/rejected/policy/2026-10-31-model-adaptive-runtime-platform-scope.md"),
    ) for tid in tids},
    **{("v4.15.2", tid, old): new for tids, old, new in (
        (("T001", "T006"), "docs/releases/v4/v4.17/development/phase-1-evidence.md", "docs/releases/v4/v4.15/development/v4.15.2-phase1-evidence.md"),
        (("T014",), "docs/releases/v4/v4.17/development/phase-2-evidence.md", "docs/releases/v4/v4.15/development/v4.15.2-phase2-evidence.md"),
        (("T024",), "docs/releases/v4/v4.17/development/phase-3-evidence.md", "docs/releases/v4/v4.15/development/v4.15.2-phase3-evidence.md"),
        (("T027",), "docs/releases/v4/v4.17/development/shared-agents-inventory.md", "docs/releases/v4/v4.15/development/v4.15.2-shared-agents-inventory.md"),
        (("T041", "T055"), "docs/releases/v4/v4.17/development/claude-agents-evaluation.md", "docs/releases/v4/v4.15/development/v4.15.2-claude-agents-evaluation.md"),
        (("T042",), "docs/releases/v4/v4.17/development/phase-4-evidence.md", "docs/releases/v4/v4.15/development/v4.15.2-phase4-evidence.md"),
        (("T043", "T046", "T047", "T048", "T049", "T050", "T051", "T052"), "docs/releases/v4/v4.17/development/last-phase-evidence.md", "docs/releases/v4/v4.15/development/v4.15.2-last-phase-evidence.md"),
        (("T044",), "docs/releases/v4/v4.17/known-gaps.md", "docs/releases/v4/v4.15/known-gaps.md"),
        (("T039",), "tests/integrations/test_org_materialization.py", "tests/installer/test_org_materialization.py"),
    ) for tid in tids},
})
_V415_TASK_ISSUER = object()


@dataclass(frozen=True, slots=True)
class V415TaskAuthority:
    """An in-process capability issued only after the native full-parent checks.

    This is an explicit trusted-code interface, not a serialized record marker or
    a security boundary against arbitrary Python executing in this process.
    """

    root: Path
    repo: str
    minor: str
    member: str
    original_sha256: str
    plan_rel: str
    plan_sha256: str
    _issuer: object = field(repr=False, compare=False)
    record_nonce: str | None = None
    member_start_head: str | None = None
    implementation_sha256: str | None = None
    source_branch: str | None = None
    target_branch: str | None = None
    historical_merge: str | None = None
    historical_tree: str | None = None


def _v415_task_authority(*, root: Path, repo: str, minor: str, member: str,
                         original_sha256: str, plan_rel: str, plan_sha256: str,
                         record_nonce: str | None = None, member_start_head: str | None = None,
                         implementation_sha256: str | None = None, source_branch: str | None = None,
                         target_branch: str | None = None, historical_merge: str | None = None,
                         historical_tree: str | None = None) -> V415TaskAuthority | None:
    """Mint after completion_minor's full-parent factory verifies original identity."""
    if (repo != "bendourthe/Nexus-Hub" or minor != "v4.15"
            or _V415_ORIGINAL_HASHES.get(member) != original_sha256
            or not isinstance(plan_rel, str) or not PLAN_REL_RE.fullmatch(plan_rel)
            or not isinstance(plan_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", plan_sha256)):
        return None
    return V415TaskAuthority(Path(root).resolve(), repo, minor, member, original_sha256,
                             plan_rel, plan_sha256, _V415_TASK_ISSUER, record_nonce, member_start_head,
                             implementation_sha256, source_branch, target_branch, historical_merge, historical_tree)


_V415_NO_CHANGE = MappingProxyType({
    ("v4.15.0", "T215"): ".github/workflows/ci.yml",
    ("v4.15.1", "T114"): ".github/workflows/ci.yml",
    ("v4.15.4", "T018"): "scripts/ci/profiles.py",
    ("v4.15.4", "T016"): "docs/handbooks/handbooks.json",
})
_V415_EVIDENCE = MappingProxyType({
    "v4.15.0": ("docs/releases/v4/v4.15/development/last-phase-evidence.md",
                 "docs/releases/v4/v4.15/development/v4.15.0-last-phase-evidence.md"),
    "v4.15.1": ("docs/releases/v4/v4.15/development/v4.15.1-last-phase-evidence.md",),
    "v4.15.4": ("docs/releases/v4/v4.15/development/v4.15.4-last-phase-evidence.md",),
})
_V415_FROZEN_PLANS = frozenset("docs/releases/v4/v4.15/plans/" + name for name in (
    "v4.15.0-instruction-necessity-review.md", "v4.15.1-adoption-model-adaptive-harness.md",
    "v4.15.2-adoption-harness-economics-and-portable-engineering-system.md",
    "v4.15.3-adoption-behavioral-harness-and-security-review-evidence.md", "v4.15.4-checker-evidence-and-diagnostics.md"))
_V415_COMPARISON_CONTRACT = "catalog/skills/infrastructure/cicd-architect/references/repository-native-profiles.md"
_V415_PROOF_DOMAIN = b"nexus-v415-unchanged-task-v1\0"
_V415_GATE_TIMEOUT = 300
_V415_LOG_CAP = 8 * 1024 * 1024


def _v415_fs(path: Path) -> Path:
    """Reuse the published installed sibling; only validated internal file operations use it."""
    try:
        return _sibling("validate_unicode_safety").filesystem_path(path)
    except (ImportError, AttributeError):
        raise Malformed("qualification-filesystem-helper-unavailable") from None


@contextmanager
def _v415_private_snapshot():
    root = Path(tempfile.mkdtemp(prefix="nq-")).resolve()
    try:
        yield root
    finally:
        # This exact freshly created directory is the only recursive cleanup target.
        if root.parent != Path(tempfile.gettempdir()).resolve() or not root.name.startswith("nq-"):
            raise Malformed("qualification-cleanup-containment")
        _v415_plain(root)
        def readonly(function, path, _error):
            os.chmod(_v415_fs(Path(path)), 0o700)
            function(_v415_fs(Path(path)))
        shutil.rmtree(_v415_fs(root), onerror=readonly)


def _v415_plain(path: Path) -> None:
    path = _v415_fs(path)
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise Malformed("qualification-unsafe-path")


def _v415_read(path: Path, cap: int = _V415_LOG_CAP) -> bytes:
    path = _v415_fs(path)
    _v415_plain(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > cap:
        raise Malformed("qualification-input-cap")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        data = stream.read(cap + 1)
        after = os.fstat(stream.fileno())
    _v415_plain(path)
    def identity(value):
        return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns
    if len(data) > cap or any(identity(value) != identity(before) for value in (opened, after, path.stat())):
        raise Malformed("qualification-input-changed")
    return data


def _v415_git(ctx: Context, *args: str, raw_text: bool = False) -> str:
    rc, out = ctx.run([ctx.git, "-c", "core.longpaths=true", "-C", str(ctx.root), *args])
    if rc:
        raise Malformed("qualification-git-unavailable")
    return out if raw_text or "-z" in args else out.strip()


def _v415_inputs(ctx: Context, ref: str, member: str, *, working: bool = False) -> dict:
    """All tracked modes/blobs; only exact final outputs and known plan marks normalize."""
    raw = _v415_git(ctx, "ls-tree", "-r", "-l", "-z", ref)
    rows, entries, total = [], {}, 0
    for entry in raw.split("\0"):
        if not entry:
            continue
        meta, path = entry.split("\t", 1)
        mode, kind, blob, size = meta.split()
        parts = path.split("/")
        if (mode not in {"100644", "100755"} or kind != "blob" or len(entries) >= 30000
                or path.startswith("/") or "\\" in path or "\ufffd" in path
                or any(p in {"", ".", ".."} or p.casefold() == ".git" or ":" in p or p.endswith((".", " ")) for p in parts)):
            raise Malformed("qualification-unsafe-tree")
        total += int(size)
        if total > 512 * 1024 * 1024:
            raise Malformed("qualification-tree-cap")
        entries[path] = (mode, blob)
        if path in _V415_EVIDENCE.get(member, ()):
            continue
        value = blob
        if path in _V415_FROZEN_PLANS:
            text = _v415_git(ctx, "show", f"{ref}:{path}", raw_text=True)
            if "\ufffd" in text:
                raise Malformed("qualification-invalid-plan-text")
            value = "plan:" + plan_hash_text(text)
        rows.append([path, mode, value])
    if working:
        if not _minor_module().v415_index_flags_visible(ctx):
            raise Malformed("qualification-hidden-index-flags")
        changed = _v415_git(ctx, "status", "--porcelain=v1", "--untracked-files=all", "-z")
        for line in changed.split("\0"):
            if not line:
                continue
            path = line[3:]
            if line[:2] not in {" M", "M ", "MM"} or path not in entries:
                raise Malformed("qualification-dirty-candidate")
            if path in _V415_EVIDENCE.get(member, ()):
                continue
            if (path not in _V415_FROZEN_PLANS
                    or plan_hash_text(_v415_read(ctx.root / path).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n"))
                    != plan_hash_text(_v415_git(ctx, "show", f"{ref}:{path}", raw_text=True))):
                raise Malformed("qualification-dirty-candidate")
            if line[0] == "M":
                staged = _v415_git(ctx, "ls-files", "--stage", "--", path).split()
                if (not staged or staged[0] != entries[path][0]
                        or plan_hash_text(_v415_git(ctx, "show", ":" + path, raw_text=True))
                        != plan_hash_text(_v415_git(ctx, "show", f"{ref}:{path}", raw_text=True))):
                    raise Malformed("qualification-dirty-candidate")
            if os.name != "nt" and bool((ctx.root / path).stat().st_mode & 0o111) != (entries[path][0] == "100755"):
                raise Malformed("qualification-dirty-candidate")
    return {"fingerprint": hashlib.sha256(_canonical(rows)).hexdigest(), "entries": entries,
            "tree": _v415_git(ctx, "rev-parse", f"{ref}^{{tree}}"), "count": len(entries)}


def _v415_sha(data: bytes) -> str:
    return hashlib.sha256(data if b"\0" in data else data.replace(b"\r\n", b"\n")).hexdigest()


def _v415_producer_sha() -> str:
    return _v415_sha(Path(__file__).read_bytes())


def _v415_json(data: str | bytes):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise Malformed("qualification-json-duplicate-key")
            result[key] = value
        return result
    def finite(_value):
        raise Malformed("qualification-json-nonfinite")
    try:
        return json.loads(data, object_pairs_hook=unique, parse_constant=finite)
    except RecursionError:
        raise Malformed("qualification-json-depth") from None


def _v415_blob_bytes(ctx: Context, ref: str, path: str, *, working: bool = False) -> bytes:
    if working:
        return _v415_read(ctx.root / path)
    # Exact Git blob output, including binary evidence, never passes a text decoder.
    rc, out = ctx.run([ctx.git, "-C", str(ctx.root), "rev-parse", f"{ref}:{path}"])
    if rc or not re.fullmatch(r"[0-9a-f]{40,64}", out.strip()):
        raise Malformed("qualification-reference-unavailable")
    if int(_v415_git(ctx, "cat-file", "-s", out.strip())) > _V415_LOG_CAP:
        raise Malformed("qualification-reference-cap")
    proc = subprocess.run([ctx.git, "-C", str(ctx.root), "cat-file", "blob", out.strip()],
                          capture_output=True, timeout=max(0.01, ctx.budget.remaining()), env=_env(), check=False, **NO_WINDOW)
    if proc.returncode or len(proc.stdout) > _V415_LOG_CAP:
        raise Malformed("qualification-reference-cap")
    return proc.stdout


def _v415_semantic(ctx: Context, ref: str, member: str, inputs: dict, *, working: bool = False) -> dict:
    sections, markers = [], 0
    for path in _V415_EVIDENCE[member]:
        if path not in inputs["entries"]:
            continue
        text = _v415_blob_bytes(ctx, ref, path, working=working).decode("utf-8").replace("\r\n", "\n")
        markers += len(re.findall(r"^```v415-ci-comparison$", text, re.MULTILINE))
        if len(re.findall(r"^## CI/CD coverage\s*$", text, re.MULTILINE)) > 1:
            raise Malformed("qualification-comparison-shape")
        match = re.search(r"^## CI/CD coverage\s*\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
        if match and "```v415-ci-comparison\n" in match.group(1):
            sections.append((path, match.group(1)))
    if len(sections) != 1 or markers != 1:
        raise Malformed("qualification-comparison-missing")
    evidence, section = sections[0]
    blocks = re.findall(r"^```v415-ci-comparison\n(.*?)\n```", section, re.MULTILINE | re.DOTALL)
    if len(blocks) != 1:
        raise Malformed("qualification-comparison-shape")
    data = _v415_json(blocks[0])
    if (not isinstance(data, dict) or set(data) != {"source_fingerprint", "contract", "steps", "fields", "required_proof"}
            or data["source_fingerprint"] != inputs["fingerprint"]):
        raise Malformed("qualification-comparison-binding")
    references = {}
    def bind(reference):
        if (not isinstance(reference, dict) or set(reference) != {"path", "sha256"}
                or reference["path"] not in inputs["entries"] or reference["path"] in _V415_EVIDENCE[member]):
            raise Malformed("qualification-reference-shape")
        if reference["path"] in references:
            if reference != references[reference["path"]]:
                raise Malformed("qualification-reference-binding")
            return
        digest = _v415_sha(_v415_blob_bytes(ctx, ref, reference["path"], working=working))
        if digest != reference["sha256"]:
            raise Malformed("qualification-reference-binding")
        references[reference["path"]] = reference
    if data["contract"].get("path") != _V415_COMPARISON_CONTRACT:
        raise Malformed("qualification-contract-binding")
    bind(data["contract"])
    for key, number, count in (("steps", "step", 6), ("fields", "field", 23)):
        rows = data[key]
        if not isinstance(rows, list) or len(rows) != count:
            raise Malformed("qualification-comparison-incomplete")
        for index, row in enumerate(rows, 1):
            if (not isinstance(row, dict) or set(row) != {number, "observation", "references"}
                    or type(row[number]) is not int or row[number] != index
                    or not isinstance(row["observation"], str) or len(row["observation"].strip()) < 16
                    or re.search(r"\b(?:TBD|TODO|UNEVALUATED|unverified|unavailable|partial|not run)\b", row["observation"], re.IGNORECASE)
                    or not isinstance(row["references"], list) or not 1 <= len(row["references"]) <= 8):
                raise Malformed("qualification-comparison-incomplete")
            for reference in row["references"]:
                bind(reference)
    if not isinstance(data["required_proof"], dict) or set(data["required_proof"]) != {"real_installer", "target_os"}:
        raise Malformed("qualification-required-proof")
    for category in data["required_proof"].values():
        if not isinstance(category, list) or not 1 <= len(category) <= 16:
            raise Malformed("qualification-required-proof")
        for reference in category:
            bind(reference)
    return {"evidence": evidence, "section_sha256": hashlib.sha256(section.encode()).hexdigest(),
            "references": sorted(references.values(), key=lambda r: r["path"]),
            "review": "coordinator-authored; structure-and-binding-only"}


def _v415_gates(member: str, tid: str) -> list[list[str]]:
    if (member, tid) == ("v4.15.4", "T016"):
        return [["catalog/skills/documentation/technical-documentation/scripts/check_handbooks.py", "--root", "."]]
    gates = [["-m", "pytest", "-q", "tests/validators/test_ci_workflow_contract.py"],
             ["scripts/validate_workflow_security.py"], ["scripts/check_required_check_coverage.py"],
             ["scripts/check_installer_parity.py"]]
    if member == "v4.15.0":
        gates.append(["scripts/check_base_template_parity.py"])
    return gates


def _v415_case(ctx: Context, tid: str, authority: V415TaskAuthority | None) -> str:
    if (type(authority) is not V415TaskAuthority or authority._issuer is not _V415_TASK_ISSUER
            or str(ctx.root).startswith(("\\\\?\\", "\\\\.\\"))
            or authority.root != ctx.root.resolve() or authority.member != ctx.version
            or authority.repo != "bendourthe/Nexus-Hub" or authority.minor != "v4.15"
            or _V415_ORIGINAL_HASHES.get(ctx.version) != authority.original_sha256
            or authority.plan_rel != ctx.rel or authority.plan_sha256 != ctx.plan_hash()
            or any(not isinstance(value, str) or not value for value in (authority.record_nonce, authority.source_branch, authority.target_branch))
            or not isinstance(authority.member_start_head, str) or not re.fullmatch(r"[0-9a-f]{40,64}", authority.member_start_head)
            or not isinstance(authority.implementation_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", authority.implementation_sha256)):
        raise Malformed("qualification-authority-unavailable")
    if (authority.historical_merge is None) != (authority.historical_tree is None) or any(
            value is not None and (not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40,64}", value))
            for value in (authority.historical_merge, authority.historical_tree)):
        raise Malformed("qualification-authority-unavailable")
    target = _V415_NO_CHANGE.get((authority.member, tid))
    if target is None or (tid, True, target) not in ctx.tasks:
        raise Malformed("qualification-task-unavailable")
    return target


def _v415_proof_path(authority: V415TaskAuthority, tid: str) -> Path:
    key = hashlib.sha256(_canonical([authority.repo, authority.minor, authority.record_nonce, authority.member, tid])).hexdigest()
    return _v415_fs(_runs_dir() / "v415-qualification" / key / "latest.json")


def _v415_proof_identity(authority: V415TaskAuthority, tid: str, target: str) -> dict:
    return {"repo": authority.repo, "minor": authority.minor, "member": authority.member,
            "original_sha256": authority.original_sha256, "record_nonce": authority.record_nonce,
            "start_head": authority.member_start_head, "implementation_sha256": authority.implementation_sha256,
            "source_branch": authority.source_branch, "target_branch": authority.target_branch,
            "task_id": tid, "literal": target}


@contextmanager
def _v415_windows_gate(command: list[str], snapshot: Path, env: dict, output):
    """Atomically create a hidden process inside a private kill-on-close Windows job."""
    import ctypes
    import ctypes.wintypes as w
    import msvcrt

    size_t = ctypes.c_size_t
    class BasicLimits(ctypes.Structure):
        _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong), ("flags", w.DWORD),
                    ("minimum", size_t), ("maximum", size_t), ("active", w.DWORD), ("affinity", size_t),
                    ("priority", w.DWORD), ("scheduling", w.DWORD)]
    class ExtendedLimits(ctypes.Structure):
        _fields_ = [("basic", BasicLimits), ("io", ctypes.c_ulonglong * 6), ("process_memory", size_t),
                    ("job_memory", size_t), ("peak_process", size_t), ("peak_job", size_t)]
    class Accounting(ctypes.Structure):
        _fields_ = [("times", ctypes.c_longlong * 4), ("faults", w.DWORD), ("total", w.DWORD),
                    ("active", w.DWORD), ("terminated", w.DWORD)]
    class Startup(ctypes.Structure):
        _fields_ = [("cb", w.DWORD), ("reserved", w.LPWSTR), ("desktop", w.LPWSTR), ("title", w.LPWSTR),
                    *[(name, w.DWORD) for name in ("x", "y", "width", "height", "columns", "rows", "fill", "flags")],
                    ("show", w.WORD), ("reserved_size", w.WORD), ("reserved_bytes", w.LPVOID),
                    ("stdin", w.HANDLE), ("stdout", w.HANDLE), ("stderr", w.HANDLE)]
    class StartupEx(ctypes.Structure):
        _fields_ = [("startup", Startup), ("attributes", w.LPVOID)]
    class ProcessInfo(ctypes.Structure):
        _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE), ("pid", w.DWORD), ("tid", w.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    signatures = (
        ("CreateJobObjectW", [w.LPVOID, w.LPCWSTR], w.HANDLE),
        ("SetInformationJobObject", [w.HANDLE, ctypes.c_int, w.LPVOID, w.DWORD], w.BOOL),
        ("QueryInformationJobObject", [w.HANDLE, ctypes.c_int, w.LPVOID, w.DWORD, w.LPVOID], w.BOOL),
        ("InitializeProcThreadAttributeList", [w.LPVOID, w.DWORD, w.DWORD, ctypes.POINTER(size_t)], w.BOOL),
        ("UpdateProcThreadAttribute", [w.LPVOID, w.DWORD, size_t, w.LPVOID, size_t, w.LPVOID, w.LPVOID], w.BOOL),
        ("DeleteProcThreadAttributeList", [w.LPVOID], None),
        ("CreateProcessW", [w.LPCWSTR, w.LPWSTR, w.LPVOID, w.LPVOID, w.BOOL, w.DWORD,
                            w.LPVOID, w.LPCWSTR, w.LPVOID, ctypes.POINTER(ProcessInfo)], w.BOOL),
        ("GetExitCodeProcess", [w.HANDLE, ctypes.POINTER(w.DWORD)], w.BOOL),
        ("WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD),
        ("TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL),
        ("CloseHandle", [w.HANDLE], w.BOOL),
    )
    for name, arguments, result in signatures:
        function = getattr(kernel, name)
        function.argtypes, function.restype = arguments, result
    def checked(result):
        if not result:
            raise ctypes.WinError(ctypes.get_last_error())
    job = kernel.CreateJobObjectW(None, None)
    checked(job)
    process, attributes = ProcessInfo(), None
    try:
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway permissions.
        checked(kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
        size = size_t()
        kernel.InitializeProcThreadAttributeList(None, 2, 0, ctypes.byref(size))
        if not size.value:
            raise OSError("qualification-atomic-job-unavailable")
        buffer = ctypes.create_string_buffer(size.value)
        checked(kernel.InitializeProcThreadAttributeList(buffer, 2, 0, ctypes.byref(size)))
        attributes = buffer
        jobs = (w.HANDLE * 1)(job)
        checked(kernel.UpdateProcThreadAttribute(attributes, 0, 0x2000D, ctypes.byref(jobs), ctypes.sizeof(jobs), None, None))
        with open(os.devnull, "rb") as input_stream:
            inherited = [msvcrt.get_osfhandle(input_stream.fileno()), msvcrt.get_osfhandle(output.fileno())]
            old_flags = [os.get_handle_inheritable(handle) for handle in inherited]
            try:
                for handle in inherited:
                    os.set_handle_inheritable(handle, True)
                handles = (w.HANDLE * 2)(*inherited)
                checked(kernel.UpdateProcThreadAttribute(attributes, 0, 0x20002, ctypes.byref(handles), ctypes.sizeof(handles), None, None))
                startup = StartupEx()
                startup.startup.cb, startup.startup.flags = ctypes.sizeof(startup), 0x100
                startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = inherited[0], inherited[1], inherited[1]
                startup.attributes = ctypes.addressof(attributes)
                environment = ctypes.create_unicode_buffer("\0".join(f"{k}={v}" for k, v in sorted(env.items(), key=lambda item: item[0].upper())) + "\0\0")
                line = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
                checked(kernel.CreateProcessW(command[0], line, None, None, True,
                        subprocess.CREATE_NO_WINDOW | 0x80000 | 0x400, environment, str(snapshot), ctypes.byref(startup), ctypes.byref(process)))
            finally:
                for handle, original in zip(inherited, old_flags):
                    os.set_handle_inheritable(handle, original)
        checked(kernel.CloseHandle(process.thread))
        process.thread = None
        def poll():
            state = kernel.WaitForSingleObject(process.process, 0)
            if state == 258:
                return None
            if state != 0:
                raise OSError("qualification-process-observation-unavailable")
            code = w.DWORD()
            checked(kernel.GetExitCodeProcess(process.process, ctypes.byref(code)))
            return code.value
        yield poll
    finally:
        try:
            checked(kernel.TerminateJobObject(job, 1))
            deadline = time.monotonic() + 5
            while True:
                accounting = Accounting()
                checked(kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None))
                if not accounting.active:
                    break
                if time.monotonic() >= deadline:
                    raise OSError("qualification-process-tree-not-drained")
                time.sleep(0.01)
        finally:
            for handle in (process.thread, process.process, job):
                if handle:
                    kernel.CloseHandle(handle)
            if attributes is not None:
                kernel.DeleteProcThreadAttributeList(attributes)


@contextmanager
def _v415_gate_process(command: list[str], snapshot: Path, env: dict, output):
    if os.name == "nt":
        with _v415_windows_gate(command, snapshot, env, output) as poll:
            yield poll
        return
    import signal
    if not all(hasattr(os, name) for name in ("waitid", "WNOWAIT", "P_PID")):
        raise OSError("qualification-owned-process-observation-unavailable")
    process = subprocess.Popen(command, cwd=snapshot, env=env, stdin=subprocess.DEVNULL,
                               stdout=output, stderr=subprocess.STDOUT, start_new_session=True, **NO_WINDOW)
    def poll():
        result = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        if result is None:
            return None
        return result.si_status if result.si_code == os.CLD_EXITED else -result.si_status
    try:
        yield poll
    finally:
        # WNOWAIT retains our leader's identity until the private process group is stopped.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            # The owned leader/group already exited; the mandatory leader reap still runs below.
            pass
        finally:
            process.wait(timeout=5)


def _v415_run_gate(snapshot: Path, argv: list[str], report: Path, env: dict) -> dict:
    """Only called with the compiled gate argv and a private materialized snapshot."""
    command = [sys.executable, *[(str(snapshot / p) if p.endswith(".py") else p) for p in argv]]
    _v415_plain(report)
    with report.open("xb") as output:
        try:
            with _v415_gate_process(command, snapshot, env, output) as poll:
                deadline = time.monotonic() + _V415_GATE_TIMEOUT
                code = poll()
                while code is None:
                    if time.monotonic() >= deadline or os.fstat(output.fileno()).st_size > _V415_LOG_CAP:
                        code = -1
                        break
                    time.sleep(0.025)
                    code = poll()
        except (OSError, subprocess.SubprocessError):
            code = -1
    _restrict(report, directory=False)
    data = _v415_read(report)
    if len(data) > _V415_LOG_CAP:
        raise Malformed("qualification-report-cap")
    return {"argv": argv, "exit_code": code, "report": report.name, "sha256": hashlib.sha256(data).hexdigest()}


def _v415_publish_proof(path: Path, attempt: Path, body: dict, key: bytes, filename: str) -> None:
    sealed = {**body, "seal": hmac.new(key, _V415_PROOF_DOMAIN + _canonical(body), hashlib.sha256).hexdigest()}
    _v415_plain(attempt)
    retained = attempt / filename
    with retained.open("xb") as handle:
        handle.write(_canonical(sealed))
        handle.flush()
        os.fsync(handle.fileno())
    _restrict(retained, directory=False)
    temporary = attempt / ("sealed-" + secrets.token_hex(12) + ".json")
    with temporary.open("xb") as handle:
        handle.write(_canonical(sealed))
        handle.flush()
        os.fsync(handle.fileno())
    _restrict(temporary, directory=False)
    _v415_plain(path)
    os.replace(temporary, path)


def _qualify_v415_task(ctx: Context, tid: str, authority: V415TaskAuthority) -> Path:
    """Execute fixed gates on a clean committed copy; no approvals or run records change."""
    target = _v415_case(ctx, tid, authority)
    if not _minor_module().v415_index_flags_visible(ctx):
        raise Malformed("qualification-hidden-index-flags")
    if authority.historical_merge is not None or _v415_git(ctx, "status", "--porcelain=v1", "--untracked-files=all"):
        raise Malformed("qualification-clean-active-candidate-required")
    commit = _v415_git(ctx, "rev-parse", "HEAD")
    if ctx.run([ctx.git, "-C", str(ctx.root), "merge-base", "--is-ancestor", authority.member_start_head, commit])[0]:
        raise Malformed("qualification-baseline-not-in-candidate")
    inputs = _v415_inputs(ctx, commit, ctx.version)
    baseline = _v415_inputs(ctx, authority.member_start_head, ctx.version)
    if target not in inputs["entries"] or baseline["entries"].get(target) != inputs["entries"][target]:
        raise Malformed("qualification-target-changed")
    gates = _v415_gates(ctx.version, tid)
    if any((p not in inputs["entries"]) for gate in gates for p in gate if p.endswith(".py")):
        raise Malformed("qualification-gate-missing")
    semantic = None if tid == "T016" else _v415_semantic(ctx, commit, ctx.version, inputs)
    path = _v415_proof_path(authority, tid)
    _v415_plain(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    _restrict(path.parent, directory=True)
    attempt = path.parent / ("attempt-" + secrets.token_hex(12))
    attempt.mkdir()
    _restrict(attempt, directory=True)
    body = {"kind": "v415-unchanged-task", "receipt_schema": 1,
            **_v415_proof_identity(authority, tid, target), "created": _now(), "candidate": commit,
            "tree": inputs["tree"], "fingerprint": inputs["fingerprint"], "tracked_count": inputs["count"],
            "exclusions": list(_V415_EVIDENCE[ctx.version]), "target_blob": list(inputs["entries"][target]),
            "semantic": semantic, "gate_definitions": gates, "gates": [], "outcome": "fail",
            "gate_sources": {p: inputs["entries"][p][1] for gate in gates for p in gate if p.endswith(".py")},
            "runtime": {"python": sys.version.split()[0], "implementation": sys.implementation.name},
            "producer_sha256": _v415_producer_sha()}
    key = _secret(create=False)
    if key is None:
        raise Malformed("qualification-secret-unavailable")
    _v415_publish_proof(path, attempt, body, key, "incomplete.json")
    try:
        with _v415_private_snapshot() as private_root:
            _restrict(private_root, directory=True)
            snapshot, home = private_root / "s", private_root / "h"
            home.mkdir()
            env = _env()
            for name in list(env):
                if (name.startswith(("PYTHON", "PYTEST")) or name in {"BASH_ENV", "ENV", "NODE_OPTIONS"}
                        or any(word in name.upper() for word in ("TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "KEY"))):
                    env.pop(name, None)
            tool_paths = [str(Path(sys.executable).parent), str(Path(ctx.git).parent)]
            for entry in env.get("PATH", "").split(os.pathsep):
                if not Path(entry).is_absolute() or Path(entry).resolve().is_relative_to(ctx.root):
                    continue
                tool_paths.append(entry)
            env["PATH"] = os.pathsep.join(tool_paths)
            env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home / "a"), LOCALAPPDATA=str(home / "l"),
                       NEXUS_HUB_HOME=str(home / "n"), NEXUS_HUB_RUNS_DIR=str(home / "r"),
                       NEXUS_EDIT_GUARD_DIR=str(home / "g"), NEXUS_EDIT_GUARD_SESSION="v415-qualification",
                       PYTHONNOUSERSITE="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
            for args in ([ctx.git, "-c", "core.longpaths=true", "init", "-q", "--template=", str(snapshot)],
                         [ctx.git, "-C", str(snapshot), "config", "core.longpaths", "true"],
                         [ctx.git, "-C", str(snapshot), "-c", "core.hooksPath=" + str(home / "hooks"), "fetch", "-q", "--no-tags", "--depth=1", str(ctx.root), commit],
                         [ctx.git, "-C", str(snapshot), "-c", "core.autocrlf=false", "-c", "core.hooksPath=" + str(home / "hooks"), "checkout", "-q", "--detach", "FETCH_HEAD"]):
                process = subprocess.run(args, env=env, capture_output=True, timeout=120, check=False, **NO_WINDOW)
                if process.returncode:
                    raise Malformed("qualification-snapshot-unavailable")
            # Checkout object identity, not the source workspace, defines every executed input.
            for rel in inputs["entries"]:
                _v415_plain(snapshot / rel)
                os.chmod(_v415_fs(snapshot / rel), 0o500 if inputs["entries"][rel][0] == "100755" else 0o400)
            for index, argv in enumerate(gates):
                report = attempt / f"gate-{index}.log"
                result = _v415_run_gate(snapshot, argv, report, env)
                result["report"] = attempt.name + "/" + report.name
                body["gates"].append(result)
                if result["exit_code"] != 0:
                    raise Malformed("qualification-gate-failed")
                output = _v415_read(report).decode("utf-8", errors="replace")
                if argv[:2] == ["-m", "pytest"] and not re.search(r"\b[1-9]\d* passed\b", output):
                    raise Malformed("qualification-gate-incomplete")
                if tid == "T016":
                    result_data = _v415_json(output)
                    if (result_data.get("status") != "pass" or result_data.get("scope") != "full"
                            or result_data.get("errors") != [] or not result_data.get("documents")
                            or result_data.get("candidate") != {"revision": commit, "working_tree": "clean"}
                            or not any(row.get("id") == "completion" for row in result_data["documents"])
                            or any(row.get("status") not in {"verified", "verified-opt-out"} for row in result_data["documents"])):
                        raise Malformed("qualification-handbook-incomplete")
            clean = subprocess.run([ctx.git, "-C", str(snapshot), "status", "--porcelain=v1", "--untracked-files=all"],
                                   env=env, capture_output=True, timeout=30, check=False, **NO_WINDOW)
            if (clean.returncode or clean.stdout.strip()
                    or not _minor_module().v415_index_flags_visible(SimpleNamespace(root=snapshot, git=ctx.git, run=ctx.run))):
                raise Malformed("qualification-snapshot-changed")
        if (_v415_git(ctx, "rev-parse", "HEAD") != commit
                or _v415_git(ctx, "status", "--porcelain=v1", "--untracked-files=all")
                or not _minor_module().v415_index_flags_visible(ctx)
                or _v415_inputs(ctx, commit, ctx.version)["fingerprint"] != inputs["fingerprint"]
                or _v415_producer_sha() != body["producer_sha256"]):
            raise Malformed("qualification-candidate-changed")
        body["outcome"] = "pass"
    finally:
        _v415_publish_proof(path, attempt, body, key, "receipt.json")
    return path


def qualify_v415_task(ctx: Context, tid: str, authority: V415TaskAuthority) -> Path:
    try:
        return _qualify_v415_task(ctx, tid, authority)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError):
        raise Malformed("qualification-input-or-execution-unavailable") from None


def v415_no_change_status(ctx: Context, tid: str, path: str, start: str | None,
                           authority: V415TaskAuthority | None) -> str:
    """Bounded read-only proof verification; never executes a gate."""
    try:
        target = _v415_case(ctx, tid, authority)
        if target != path or start != authority.member_start_head:
            return "unmet"
        location = _v415_proof_path(authority, tid)
        if not location.exists():
            return "unmet"
        body = _v415_json(_v415_read(location, 512 * 1024))
        seal = body.pop("seal")
        key = _secret(create=False)
        expected = {"kind", "receipt_schema", "created", "candidate", "tree", "fingerprint", "tracked_count", "exclusions", "target_blob",
                    "semantic", "gate_definitions", "gate_sources", "runtime", "gates", "outcome", "producer_sha256", *_v415_proof_identity(authority, tid, target)}
        if (set(body) != expected or key is None or not isinstance(seal, str)
                or not hmac.compare_digest(seal, hmac.new(key, _V415_PROOF_DOMAIN + _canonical(body), hashlib.sha256).hexdigest())
                or any(body.get(k) != v for k, v in _v415_proof_identity(authority, tid, target).items())
                or body["kind"] != "v415-unchanged-task" or body["receipt_schema"] != 1 or body["outcome"] != "pass"
                or type(body["receipt_schema"]) is not int or type(body["tracked_count"]) is not int
                or not 1 <= body["tracked_count"] <= 30000
                or any(not isinstance(body[k], str) or not re.fullmatch(r"[0-9a-f]{64}", body[k]) for k in ("fingerprint", "producer_sha256"))
                or not isinstance(body["tree"], str) or not re.fullmatch(r"[0-9a-f]{40,64}", body["tree"])
                or body["exclusions"] != list(_V415_EVIDENCE[ctx.version]) or body["gate_definitions"] != _v415_gates(ctx.version, tid)):
            return "unmet"
        if not isinstance(body["created"], str) or dt.datetime.fromisoformat(body["created"]).tzinfo is None:
            return "unmet"
        candidate = body["candidate"]
        if not isinstance(candidate, str) or not re.fullmatch(r"[0-9a-f]{40,64}", candidate):
            return "unmet"
        if ctx.run([ctx.git, "-C", str(ctx.root), "merge-base", "--is-ancestor", start, candidate])[0]:
            return "unmet"
        reference = candidate
        if authority.historical_merge is not None:
            if (_v415_git(ctx, "rev-parse", f"{authority.historical_merge}^{{tree}}") != authority.historical_tree
                    or ctx.run([ctx.git, "-C", str(ctx.root), "merge-base", "--is-ancestor", candidate, authority.historical_merge])[0]):
                return "unmet"
            reference = authority.historical_merge
        else:
            if ctx.run([ctx.git, "-C", str(ctx.root), "merge-base", "--is-ancestor", candidate, "HEAD"])[0]:
                return "unmet"
            if body["producer_sha256"] != _v415_producer_sha():
                return "unmet"
            current = _v415_inputs(ctx, "HEAD", ctx.version, working=True)
            if current["fingerprint"] != body["fingerprint"]:
                return "unmet"
        inputs = _v415_inputs(ctx, candidate, ctx.version)
        publication = inputs if reference == candidate else _v415_inputs(ctx, reference, ctx.version)
        baseline = _v415_inputs(ctx, start, ctx.version)
        if (inputs["fingerprint"] != body["fingerprint"] or publication["fingerprint"] != body["fingerprint"]
                or inputs["tree"] != body["tree"] or inputs["count"] != body["tracked_count"]
                or list(inputs["entries"].get(target, ())) != body["target_blob"]
                or baseline["entries"].get(target) != inputs["entries"].get(target)
                or body["gate_sources"] != {p: inputs["entries"][p][1] for gate in body["gate_definitions"] for p in gate if p.endswith(".py")}
                or not isinstance(body["runtime"], dict) or set(body["runtime"]) != {"python", "implementation"}
                or any(not isinstance(value, str) or not value for value in body["runtime"].values())):
            return "unmet"
        if tid != "T016" and (body["semantic"] != _v415_semantic(ctx, candidate, ctx.version, inputs)
                    or body["semantic"] != _v415_semantic(ctx, reference, ctx.version, publication)
                    or (authority.historical_merge is None and body["semantic"] != _v415_semantic(ctx, "HEAD", ctx.version, current, working=True))):
            return "unmet"
        gates = _v415_gates(ctx.version, tid)
        if not isinstance(body["gates"], list) or len(body["gates"]) != len(gates):
            return "unmet"
        for expected_argv, gate in zip(gates, body["gates"]):
            if (set(gate) != {"argv", "exit_code", "report", "sha256"} or gate["argv"] != expected_argv
                    or type(gate["exit_code"]) is not int or gate["exit_code"] != 0
                    or not re.fullmatch(r"attempt-[0-9a-f]{24}/gate-[0-9]+\.log", gate["report"])
                    or hashlib.sha256(_v415_read(location.parent / gate["report"])).hexdigest() != gate["sha256"]):
                return "unmet"
        return "met"
    except (Malformed, OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError):
        return "unmet"


def _v415_task_target(ctx: Context, path: str, task_id: str | None,
                      authority: V415TaskAuthority | None, record: dict | None) -> str:
    if (type(authority) is not V415TaskAuthority or authority._issuer is not _V415_TASK_ISSUER
            or authority.repo != "bendourthe/Nexus-Hub" or authority.minor != "v4.15"
            or authority.member != ctx.version or authority.root != ctx.root.resolve()
            or authority.plan_rel != ctx.rel or authority.plan_sha256 != ctx.plan_hash()
            or _V415_ORIGINAL_HASHES.get(authority.member) != authority.original_sha256):
        return path
    corrected = _V415_TASK_TARGETS.get((authority.member, task_id, path))
    if corrected is None:
        return path
    # A verified archive's existing predicate searches both the archive and its
    # original active location and excludes archive-only/uncertain changes.
    archived = (record or {}).get("archived")
    if isinstance(archived, dict):
        source, destination = archived.get("from"), archived.get("plan_path")
        if isinstance(source, str) and isinstance(destination, str) and "/plans/" in source and "/plans/" in destination:
            active_root = source.rsplit("/plans/", 1)[0]
            if corrected.startswith(active_root + "/"):
                candidate = destination.rsplit("/plans/", 1)[0] + corrected[len(active_root):]
                if _minor_module().task_origin(ctx.version, candidate, archived) == corrected:
                    return candidate
    return corrected


def _task_status(ctx: Context, checked: bool, path: str, start: str | None, record: dict | None = None,
                 *, task_id: str | None = None, task_authority: V415TaskAuthority | None = None) -> str:
    if not checked or not path:
        return "unmet"
    if not start:
        return "met"
    path = _v415_task_target(ctx, path, task_id, task_authority, record)
    # Once any member of the minor carries a signed archived identity, an archive commit
    # (any member's, or the close's) never counts as task work (contract, "Member archive").
    archives = record if _minor_module().archive_active(record) else None
    if path.count(DATE_PLACEHOLDER) == 1:
        return _dated_task_status(ctx, path, start, archives)
    if archives is not None:
        status = _minor_module().archive_task_status(ctx, ctx.version, path, start, archives)
        return v415_no_change_status(ctx, task_id, path, start, task_authority) if status == "unmet" else status
    rc, out = _run(
        [
            ctx.git,
            "-C",
            str(ctx.root),
            "log",
            "--full-history",
            "--format=%H",
            f"{start}..HEAD",
            "--",
            path,
        ],
        ctx.budget,
    )
    if rc != 0:
        return "cannot-verify"
    return "met" if out.strip() else v415_no_change_status(ctx, task_id, path, start, task_authority)


def _dated_task_status(ctx: Context, path: str, start: str, archives: dict | None = None) -> str:
    """Met only when exactly one file with a real date in the placeholder's place changed.

    The placeholder must appear once; zero or several dated matches are unmet, so a
    second dated file cannot make a stale task pass and nothing is guessed when none matches.
    With `archives` (a minor where an archive happened), archive commits are skipped and
    the path's original location is searched too, as for any other task line.
    """
    head, tail = path.split(DATE_PLACEHOLDER)
    pattern = re.compile(re.escape(head) + r"\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])" + re.escape(tail) + r"\Z")
    folder = head.rsplit("/", 1)[0] if "/" in head else "."
    if archives is not None:
        return _dated_archive_status(ctx, path, start, archives, pattern, folder)
    rc, out = _run(
        [ctx.git, "-C", str(ctx.root), "log", "--full-history", "--format=", "--name-only", "--no-renames",
         f"{start}..HEAD", "--", folder],
        ctx.budget,
    )
    if rc != 0:
        return "cannot-verify"
    matches = {line.strip() for line in out.splitlines() if pattern.match(line.strip())}
    return "met" if len(matches) == 1 else "unmet"


def _dated_archive_status(ctx: Context, path: str, start: str, archives: dict, pattern: re.Pattern[str], folder: str) -> str:
    """`_dated_task_status` once an archive happened: archive commits never count.

    The path's original location (before a member archive or the close re-pointed it)
    is searched too, and a match there is read in its archived form, so one dated file
    found at both places counts once.
    """
    cm = _minor_module()
    landing = cm.archive_landing(ctx, archives)
    if landing is None:
        return "cannot-verify"
    excluded = landing.excluded
    origin = cm.task_origin(ctx.version, path, archives.get("archived"))
    folders, old_tree, new_tree = [folder], "", ""
    if origin is not None:
        rest = len(path) - len(cm.ARCHIVE_TREE.format(M=cm.minor_of(ctx.version)[0], m=cm.minor_of(ctx.version)[1]))
        old_tree, new_tree = origin[: len(origin) - rest], path[: len(path) - rest]
        head = origin.split(DATE_PLACEHOLDER)[0]
        folders.append(head.rsplit("/", 1)[0] if "/" in head else ".")
    rc, out = _run(
        [ctx.git, "-c", "core.quotePath=false", "-C", str(ctx.root), "log", "--full-history", "--format=@@%H", "--name-only",
         "-z", "--no-renames", f"{start}..HEAD", "--", *folders],
        ctx.budget,
    )
    if rc != 0:
        return "cannot-verify"
    matches: set[str] = set()
    shas: set[str] = set()
    current = ""
    for token in out.split("\0"):
        name = token.lstrip("\n")
        if name.startswith("@@"):
            current = name[2:].strip()
            shas.add(current)
            continue
        if not name or current in excluded:
            continue
        if old_tree and name.startswith(old_tree + "/"):
            name = new_tree + name[len(old_tree):]
        if pattern.match(name):
            matches.add(name)
    if cm.uncertain_for(landing, folders, shas):
        return "cannot-verify"
    return "met" if len(matches) == 1 else "unmet"


def _in_archive_tree(ctx: Context) -> bool:
    """True when the plan sits in its minor's archive tree (a member archived on release)."""
    cm = _minor_module()
    try:
        major, minor = cm.minor_of(ctx.version)
    except (ValueError, IndexError):
        return False
    return ctx.version_dir.resolve() == (ctx.root / cm.ARCHIVE_TREE.format(M=major, m=minor)).resolve()


def _gaps_ledger(ctx: Context, record: dict | None = None) -> Path | None:
    """The minor's known-gaps ledger for `gaps.version`; None when two layouts both hold one.

    A plan in an active tree reads `<version dir>/known-gaps.md`, as always. A member
    archived on release sits in the archive tree while its minor's ledger stays active
    until the close, so its ledger is resolved across every layout: reading only the
    archive folder would find no ledger and read every open gap as met. Only a member
    whose record carries its signed `archived` identity is read this way.
    """
    gaps = ctx.version_dir / "known-gaps.md"
    if not (_in_archive_tree(ctx) and isinstance((record or {}).get("archived"), dict)):
        return gaps
    cm = _minor_module()
    found = [ctx.root / rel for rel in cm.ledger_rels(*cm.minor_of(ctx.version)) if (ctx.root / rel).is_file()]
    if len(found) > 1:
        return None
    return found[0] if found else gaps


def _gaps_status(ctx: Context, record: dict | None) -> tuple[str, int]:
    gaps = _gaps_ledger(ctx, record)
    if gaps is None:
        return "cannot-verify", 0
    if not gaps.exists():
        return "met", 0
    try:
        text = gaps.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "cannot-verify", 0
    # A version heading may carry a title (`## v4.3.0 - agentic-verification`); an exact
    # match alone missed it and read every open gap as met.
    section = _section(text, f"## {ctx.version}", level="## ", titled=True)
    if section is None:
        return "met", 0
    open_block = _section(section, "### Open Items", level="### ")
    if open_block is None:
        return "met", 0
    deferrable = set((record or {}).get("deferrable_gap_types") or [])
    own_tasks = {tid for tid, _, _ in ctx.tasks}
    unmet = deferred = 0
    items = list(GAP_ITEM_RE.finditer(open_block))
    for index, item in enumerate(items):
        end = items[index + 1].start() if index + 1 < len(items) else len(open_block)
        body = open_block[item.start() : end]
        # Only the ledger's resolution marker counts ("- RESOLVED ..." or "-- RESOLVED ..."),
        # never the word inside a title such as "Unresolved flake".
        if RESOLVED_MARKER_RE.search(item.group("title")):
            continue
        # A minor member's gap migrated at the minor close is closed only when the
        # migration verifies (completion contract, "Minor gaps and archive"); a
        # per-plan run has no migration, so the marker alone stays unmet.
        if MIGRATED_MARKER_RE.search(item.group("title")) and (
            _migration_met(ctx, record, gaps, item.group(0)) or _plan_migration_met(ctx, record, gaps, item.group(0))
        ):
            continue
        # A minor member's open item whose id is in the frozen migratable list waits for
        # the minor close, where `gaps.minor` decides it; the member gate must not wait on it.
        if _pending_migration(ctx, record, text, item.group(0)):
            deferred += 1
            continue
        source = re.search(r"\*\*Source phase\*\*:([^\n]*)", body)
        from_own_task = bool(
            source and set(re.findall(r"T\d{3,}", source.group(1))) & own_tasks
        )
        if item.group("type") in deferrable and not from_own_task:
            deferred += 1
        else:
            unmet += 1
    if unmet:
        return "unmet", 0
    return ("deferred" if deferred else "met"), deferred


RESOLVED_MARKER_RE = re.compile(r"\s-{1,2}\s*RESOLVED\b")
MIGRATED_MARKER_RE = re.compile(r"\s-{1,2}\s*MIGRATED to v\d+\.\d+\.\d+\s*$")


def _plan_migration_met(ctx: Context, record: dict | None, gaps: Path, heading: str) -> bool:
    """True when a one-plan run carrying `carry-gaps` moved this item to the next minor."""
    if not record or record.get("schema") != SCHEMA or not _has_class(record, "carry-gaps"):
        return False
    cm = _minor_module()
    ledgers, _unreadable = cm.load_ledgers(ctx.root)
    ledger = next((l for l in ledgers if l.path.resolve() == gaps.resolve()), None)
    found = cm.LEDGER_ITEM_RE.match(heading.lstrip("#").strip())
    if ledger is None or found is None:
        return False
    # Ids repeat across version sections, so only this plan's own section counts.
    item = next((i for i in ledger.items if i.gid == found.group("id") and i.state == "migrated"
                 and cm.section_version(i.section) == ctx.version), None)
    return item is not None and cm.plan_migration_met(ledgers, ledger, item)


def _has_class(record: dict | None, name: str) -> bool:
    classes = ((record or {}).get("approvals") or {}).get("classes") or []
    return any(isinstance(c, dict) and c.get("class") == name for c in classes)


def _migration_met(ctx: Context, record: dict | None, gaps: Path, heading: str) -> bool:
    """True when this migrated item of a minor member verifies against the minor record."""
    if not record or record.get("scope") != "member" or not record.get("minor"):
        return False
    cm = _minor_module()
    ledgers, _unreadable = cm.load_ledgers(ctx.root)
    ledger = next((l for l in ledgers if l.path.resolve() == gaps.resolve()), None)
    found = cm.LEDGER_ITEM_RE.match(heading.lstrip("#").strip())
    if ledger is None or found is None:
        return False
    item = next((i for i in ledger.items if i.gid == found.group("id") and i.state == "migrated"), None)
    if item is None:
        return False
    status, _reason = cm.verify_migration(ctx, record, str(record["minor"]), ledgers, ledger, item)
    return status == "met"


def _pending_migration(ctx: Context, record: dict | None, text: str, heading: str) -> bool:
    """True for a frozen inherited item or exact predeclared recording-only opportunity.

    A security or high-severity item is deferred only when the approval also names it
    individually; otherwise it blocks the member's `gaps.version`, since it could never
    migrate at the close.
    """
    if not record or record.get("scope") != "member" or not record.get("minor"):
        return False
    found = re.match(r"^#### ([A-Z]{2}-\d+)\b", heading)
    if found is None:
        return False
    cm = _minor_module()
    items = [i for i in cm.parse_ledger(text) if i.gid == found.group(1)]
    if len(items) != 1:
        return False
    item = items[0]
    # The same gate the close uses, so an item that could never migrate there (created
    # during the run, or sensitive at the record's start) is never deferred here either.
    status, _reason = cm.migration_gate(ctx, record, cm.minor_of(str(record["minor"])), item.gid, item)
    return status == "met"


def _section(text: str, heading: str, level: str, titled: bool = False) -> str | None:
    lines = text.splitlines(keepends=True)
    start = None
    for index, line in enumerate(lines):
        stripped = line.rstrip()
        if start is None and (stripped == heading or (titled and stripped.startswith(heading + " "))):
            start = index + 1
        elif (
            start is not None
            and line.startswith(level)
            and not line.startswith(level + "#")
        ):
            return "".join(lines[start:index])
    return "".join(lines[start:]) if start is not None else None


def _evidence_file(ctx: Context, record: dict | None = None) -> str | None:
    folders = [ctx.version_dir / "development"]
    if _in_archive_tree(ctx) and isinstance((record or {}).get("archived"), dict):
        # A member archived on release: its own evidence moved with it, while a shared
        # unprefixed evidence file stays in the active tree until the minor close.
        cm = _minor_module()
        major, minor = cm.minor_of(ctx.version)
        folders += [ctx.root / tree.format(M=major, m=minor) / "development" for tree in cm.ACTIVE_TREES]
    candidates = [(folder / f"{ctx.version}-last-phase-evidence.md", False) for folder in folders]
    candidates += [(folder / "last-phase-evidence.md", True) for folder in folders]
    for candidate, needs_name in candidates:
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8", errors="replace")
            if not needs_name or ctx.plan.name in text:
                return text
    return None


def _has_sections(text: str) -> bool:
    return all(
        re.search(rf"^## {re.escape(name)}\s*$", text, re.MULTILINE)
        for name in REQUIRED_SECTIONS
    )


def _tests_status(ctx: Context, evidence: str | None, start: str | None) -> str:
    if evidence is None:
        return "unmet"
    section = _section(evidence, "## Full-suite testing and stabilization", level="## ")
    if (
        not section
        or not re.search(r"\b(passed|PASS)\b", section)
        # A quoted run that reports failures is not passing evidence ("3 failed, 0 passed").
        or re.search(r"\b[1-9]\d* (failed|errors?)\b", section)
        or "`" not in section
    ):
        return "unmet"
    if start:
        rc, out = _run(
            [ctx.git, "-C", str(ctx.root), "diff", "--name-only", f"{start}..HEAD"],
            ctx.budget,
        )
        if rc != 0:
            return "cannot-verify"
        changed = [p for p in out.split() if "test" in p.lower()]
    else:
        changed = [
            p
            for p in re.findall(r"[\w./-]*tests?[\w./-]*\.\w+", section)
            if (ctx.root / p).exists()
        ]
    return "met" if any(p in section for p in changed) else "unmet"


# `gh` exits 1 both when GitHub answers "that does not exist" and when it cannot be
# asked at all (HTTP 401, network), so only the whole stderr line tells them apart.
# A not-found answer is definitive evidence that the work is not done yet (unmet), and
# must never read as an unreachable platform: that verdict is terminal and would stop a
# run whose next step is simply to open the pull request or publish the release.
GH_NOT_FOUND = object()
_GH_NOT_FOUND_LINES = (
    re.compile(r'no pull requests found for branch ".*"'),
    # WN-13: a just-opened PR can exist before its first check is reported.
    re.compile(r"no checks reported on the '[^'\r\n]+' branch"),
    re.compile(r"release not found"),
)


def _gh_json(ctx: Context, repo: str, *args: str) -> object | None:
    if not ctx.gh or not repo:
        return None
    rc, out, err = _run_with_stderr([ctx.gh, *args, "--repo", repo], ctx.budget, cwd=ctx.root)
    if rc == 1 and any(p.fullmatch(err.strip()) for p in _GH_NOT_FOUND_LINES):
        return GH_NOT_FOUND
    if rc != 0:
        return None
    try:
        return json.loads(out)
    except ValueError:
        return None


def _pr_merged(ctx: Context, repo: str, branch: str) -> str:
    data = _gh_json(ctx, repo, "pr", "view", branch, "--json", "state")
    if data is GH_NOT_FOUND:
        return "unmet"
    if not isinstance(data, dict):
        return "cannot-verify"
    return "met" if data.get("state") == "MERGED" else "unmet"


REQUIRED_CHECKS_PATH = "docs/policy/required-checks.json"


def _committed_blob(ctx: Context, *revs: str | None, path: str) -> tuple[str, str] | None:
    """(rev, text) of `path` at the first rev that has it, or None.

    Gates read committed content only (v4.13.2 WN-12): an edit to the working tree
    must not change what "required" means or what runs at a turn end.
    """
    for rev in revs:
        if not rev:
            continue
        rc, out = _run([ctx.git, "-C", str(ctx.root), "show", f"{rev}:{path}"], ctx.budget)
        if rc == 0:
            return rev, out
    return None


def _required_contexts(ctx: Context, target: str, start: str | None = None) -> list[str] | None:
    """The target branch's required contexts from the manifest on `origin/<target>`,
    falling back to the run's `start_head`; None defers to `gh pr checks --required`."""
    found = _committed_blob(ctx, f"origin/{target}", start, path=REQUIRED_CHECKS_PATH)
    if found is None:
        return None
    try:
        branches = json.loads(found[1]).get("branches", {})
    except (ValueError, AttributeError):
        return None
    contexts = branches.get(target, {}).get("contexts") if isinstance(branches, dict) else None
    return list(contexts) if isinstance(contexts, list) else None


def _pr_checks(ctx: Context, repo: str, branch: str, target: str, start: str | None = None) -> str:
    required = _required_contexts(ctx, target, start)
    args = ["pr", "checks", branch, "--json", "name,bucket"]
    if required is None:
        args.append("--required")
    data = _gh_json(ctx, repo, *args)
    if data is GH_NOT_FOUND:
        return "unmet"
    if not isinstance(data, list):
        return "cannot-verify"
    buckets = {str(c.get("name")): c.get("bucket") for c in data if isinstance(c, dict)}
    names = required if required is not None else list(buckets)
    if not names:
        return "cannot-verify"
    return (
        "met" if all(buckets.get(n) in ("pass", "skipping") for n in names) else "unmet"
    )


def _tag_status(ctx: Context, tag: str) -> str:
    rc, out = _run([ctx.git, "-C", str(ctx.root), "tag", "-l", tag], ctx.budget)
    if rc != 0:
        return "cannot-verify"
    if out.strip() != tag:
        return "unmet"
    rc, out = _run(
        [
            ctx.git,
            "-C",
            str(ctx.root),
            "ls-remote",
            "--tags",
            "origin",
            f"refs/tags/{tag}",
        ],
        ctx.budget,
    )
    if rc != 0:
        return "cannot-verify"
    return "met" if out.strip() else "unmet"


def _changelog_status(ctx: Context) -> str:
    changelog = ctx.root / "CHANGELOG.md"
    if not changelog.is_file():
        return "unmet"
    bare = ctx.version.lstrip("v")
    text = changelog.read_text(encoding="utf-8", errors="replace")
    return (
        "met"
        if re.search(rf"^## \[{re.escape(bare)}\]", text, re.MULTILINE)
        else "unmet"
    )


VERSION_SYNC_PATH = "scripts/check_version_sync.py"
# Runs a script's committed source as if it were the working-tree file: `__file__`
# and sys.path[0] name the real location, so the script's own root discovery and
# sibling imports behave as before, but its code is the committed blob.
_RUN_BLOB = (
    "import sys\n"
    "source, real = sys.argv[1], sys.argv[2]\n"
    "sys.argv = [real]\n"
    "sys.path.insert(0, real.rsplit('/', 1)[0])\n"
    "code = compile(open(source, encoding='utf-8').read(), real, 'exec')\n"
    "exec(code, {'__name__': '__main__', '__file__': real})\n"
)


def _version_sync(ctx: Context, start: str | None = None) -> str:
    """Run the project's version-sync script from the run's `start_head` tree (or
    HEAD without a record), so a working-tree edit to the script cannot change the gate."""
    found = _committed_blob(ctx, start or "HEAD", path=VERSION_SYNC_PATH)
    if found is None:
        return "n/a"
    # Outside the runs directory and the repository: neither may gain a stray file.
    blob = Path(tempfile.gettempdir()) / f"nexus-version-sync-{os.getpid()}-{secrets.token_hex(4)}.py"
    try:
        blob.write_text(found[1], encoding="utf-8")
        real = (ctx.root / VERSION_SYNC_PATH).as_posix()
        rc, _ = _run([sys.executable, "-c", _RUN_BLOB, str(blob), real], ctx.budget, cwd=ctx.root)
    except OSError:
        return "cannot-verify"
    finally:
        blob.unlink(missing_ok=True)
    if rc == -1:
        return "cannot-verify"
    return "met" if rc == 0 else "unmet"


def _release_status(ctx: Context, repo: str, tag: str) -> str:
    data = _gh_json(ctx, repo, "release", "view", tag, "--json", "isDraft")
    if data is GH_NOT_FOUND:
        return "unmet"
    if not isinstance(data, dict):
        return "cannot-verify"
    return "met" if data.get("isDraft") is False else "unmet"


def _main_contains(ctx: Context, tag: str) -> str:
    rc, out = _run(
        [ctx.git, "-C", str(ctx.root), "ls-remote", "origin", "refs/heads/main"],
        ctx.budget,
    )
    if rc != 0 or not out.strip():
        return "cannot-verify"
    main_sha = out.split()[0]
    rc, _ = _run(
        [ctx.git, "-C", str(ctx.root), "merge-base", "--is-ancestor", tag, main_sha],
        ctx.budget,
    )
    if rc == 0:
        return "met"
    return "unmet" if rc == 1 else "cannot-verify"


def _branches_gone(ctx: Context, branches: list[str]) -> str:
    for branch in branches:
        rc, out = _run(
            [ctx.git, "-C", str(ctx.root), "branch", "--list", branch], ctx.budget
        )
        if rc != 0:
            return "cannot-verify"
        if out.strip():
            return "unmet"
    rc, out = _run(
        [ctx.git, "-C", str(ctx.root), "ls-remote", "--heads", "origin", *branches],
        ctx.budget,
    )
    if rc != 0:
        return "cannot-verify"
    return "unmet" if out.strip() else "met"


def _worktrees_gone(ctx: Context, worktrees: list[str] | None, branch: str) -> str:
    rc, out = _run(
        [ctx.git, "-C", str(ctx.root), "worktree", "list", "--porcelain"], ctx.budget
    )
    if rc != 0:
        return "cannot-verify"
    listed = {
        line[len("worktree ") :].strip()
        for line in out.splitlines()
        if line.startswith("worktree ")
    }
    if worktrees:
        wanted = {str(Path(w).resolve()) for w in worktrees}
        return (
            "unmet" if any(str(Path(w).resolve()) in wanted for w in listed) else "met"
        )
    return "unmet" if f"branch refs/heads/{branch}" in out else "met"


def _cleanup_merged_status(ctx: Context, record: dict, repo: str, branch: str) -> str:
    """`cleanup.merged`: the sealed final-pass receipt postdates the plan's merge (contract)."""
    data = _gh_json(ctx, repo, "pr", "view", branch, "--json", "state,mergeCommit")
    if data is GH_NOT_FOUND:
        return "unmet"
    if not isinstance(data, dict):
        return "cannot-verify"
    if data.get("state") != "MERGED":
        return "unmet"
    merge = (data.get("mergeCommit") or {}).get("oid") if isinstance(data.get("mergeCommit"), dict) else None
    try:
        cleanup_merged = _sibling("cleanup_merged")  # call-time only: it imports this module
    except ImportError:
        return "cannot-verify"
    target = str((record.get("approvals") or {}).get("target_branch") or "develop")
    return cleanup_merged.receipt_status(
        ctx.root, ctx.git, ctx.run, ctx.record_path(), record.get("nonce"), merge, target
    )


# --------------------------------------------------------------------------- verdict


def verdict(
    ctx: Context, session: str | None
) -> tuple[str, int, list[tuple[str, str]], RecordState]:
    state = load_record(ctx, session)
    if state.forced and state.record is None and state.forced[1] == EXIT_BLOCKED:
        return state.forced[0], state.forced[1], [], state
    results, deferred = evaluate(ctx, state.record)
    if state.forced:
        return state.forced[0], state.forced[1], results, state
    unmet = [pid for pid, status in results if status in ("unmet", "cannot-verify")]
    if unmet:
        return "INCOMPLETE: " + " ".join(unmet), EXIT_INCOMPLETE, results, state
    head = ctx._git_out("rev-parse", "HEAD") or "-"
    nonce = (state.record or {}).get("nonce", "-")
    line = f"PLAN COMPLETE {ctx.rel} {head} {nonce}"
    if deferred:
        line += f" ({deferred} deferred)"
    return line, EXIT_COMPLETE, results, state


def cmd_check(args: argparse.Namespace) -> int:
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
    line, code, results, state = verdict(ctx, args.session)
    record = state.record
    if code == EXIT_COMPLETE and record is not None and record.get("schema") == SCHEMA:
        mark_completed(ctx, record, line.split()[3] if len(line.split()) > 3 else "-")
    for notice in [*state.notices, *ctx.notices]:
        print(f"notice: {notice}", file=sys.stderr)
    print(line)
    if args.json:
        print(
            json.dumps(
                {"verdict": line, "exit": code, "predicates": dict(results)},
                sort_keys=True,
            )
        )
    else:
        for pid, status in results:
            print(f"{pid} {status}")
    return code


def cmd_score(args: argparse.Namespace) -> int:
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
    state = load_record(ctx, args.session)
    results, _ = evaluate(ctx, state.record)
    met = sum(1 for _, status in results if status in ("met", "deferred", "n/a"))
    head = ctx._git_out("rev-parse", "HEAD") or "-"
    approvals = (state.record or {}).get("approvals", {})
    repo = approvals.get("repo") or ctx.default_repo
    branch = approvals.get("source_branch") or f"feat/{ctx.version}-{ctx.slug}"
    runs = _gh_json(
        ctx,
        repo,
        "run",
        "list",
        "--branch",
        branch,
        "--limit",
        "1",
        "--json",
        "databaseId",
    )
    run_id = (
        str(runs[0]["databaseId"])
        if isinstance(runs, list) and runs and "databaseId" in runs[0]
        else "-"
    )
    print(f"{met} {head} {run_id}")
    return 0


# --------------------------------------------------------------------------- record commands


def normalize(text: str) -> str:
    return approval_binding.normalize(text)


def _digest(text: str) -> str:
    return approval_binding.digest(text)


def _approvals_from_file(path: str, minor: bool = False) -> dict:
    try:
        spec = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Malformed(f"approvals file unreadable: {exc.__class__.__name__}") from exc
    if not isinstance(spec, dict):
        raise Malformed("approvals file must hold a JSON object")
    classes = spec.get("classes")
    if not isinstance(classes, list) or not classes or not all(isinstance(c, dict) for c in classes):
        raise Malformed("approvals file needs a non-empty 'classes' list")
    for entry in classes:
        name = str(entry.get("class", ""))
        if not (name in APPROVAL_CLASSES or name.startswith("ask-first:")):
            raise Malformed(f"approval class not approvable in advance: {name}")
        if name in PLAN_ONLY_CLASSES and minor:
            raise Malformed(f"approval class {name} belongs to a one-plan run; a minor run migrates gaps")
        if name in MINOR_ONLY_CLASSES - PLAN_CLOSE_CLASSES and not minor:
            raise Malformed(f"approval class {name} belongs to a minor run (record ... --minor vX.Y)")
    defer = next((c.get("bound") for c in classes if c["class"] == "defer-gaps"), []) or []
    if not set(defer) <= GAP_TYPES:
        raise Malformed("defer-gaps bound must list gap types from NI DF BG MT WN QG")
    try:
        if 'autonomy' in spec:
            approval_binding.validate_policy(spec['autonomy'])
    except ValueError as exc:
        raise Malformed(str(exc)) from exc
    return spec


def _blocked(category: str) -> int:
    print(f"BLOCKED: {category}")
    return EXIT_BLOCKED


def _refused(reason: str) -> int:
    """An approval that was not recorded: the blocker line first, then the fixed reason id."""
    print("BLOCKED: approval-not-covered")
    print(f"reason: {reason}")
    return EXIT_BLOCKED


def _create_page(ctx: Context, spec: dict) -> dict:
    try:
        _validate_policy_paths(ctx.root, spec.get('autonomy') or {})
    except ValueError as exc:
        raise Malformed(str(exc)) from exc
    return approval_binding.create_page(
        rel=ctx.rel,
        version=ctx.version,
        plan_sha256=ctx.plan_hash(),
        repo=str(spec.get("repo") or ctx.default_repo),
        head=ctx._git_out("rev-parse", "HEAD"),
        spec=spec,
    )


def _action_page(ctx: Context, record: dict, action: str, blocker: int | None) -> dict:
    category = None
    if action == "answer":
        blockers = record.get("blockers", [])
        if blocker is None or not 0 <= blocker < len(blockers) or not blockers[blocker].get("open"):
            raise Malformed("no open blocker at that index")
        category = blockers[blocker].get("category")
    page = approval_binding.action_page(
        action,
        rel=ctx.rel,
        version=ctx.version,
        record_nonce=str(record.get("nonce", "")),
        blocker=blocker,
        category=category,
        fingerprint=approval_binding.blocker_fingerprint(blockers[blocker]) if action == 'answer' else None,
    )
    if action == 'answer':
        page['blocker'].update(request=blockers[blocker].get('request') or {}, purpose=blockers[blocker].get('purpose'), why=blockers[blocker].get('why'))
    return page


def _round_key(ctx: Context) -> str:
    """One approval round per record: a newer render replaces the older one."""
    return ctx.record_path().stem


def _consume(
    ctx: Context,
    action: str,
    page: dict,
    session: str,
    text: str | None,
    required_session: str | None = None,
) -> tuple[dict, str] | int:
    try:
        pending, bound = approval_binding.consume(
            _runs_dir(),
            _round_key(ctx),
            _secret(create=False),
            action=action,
            live_page=page,
            session=session,
            required_session=required_session,
        )
    except approval_binding.Refusal as refusal:
        return _refused(refusal.reason)
    if text is not None and normalize(text) not in {normalize(x) for x in [*pending["paste_lines"], approval_binding.pasted(pending)]}:
        # The round is spent either way: a claimed text that is not the pasted line is not an approval.
        return _refused("approval-not-captured")
    return pending, bound


def _sibling(name: str) -> ModuleType:
    """Import sibling script `name` at call time.

    Layering is one-way: siblings such as `completion_minor` and `cleanup_merged`
    import this module, so this module never imports them statically (that would be
    an import cycle). Both layouts resolve the plain name, because this file puts its
    own directory on `sys.path`: the flat `~/.nexus-hub/scripts/` install and the
    repository's `scripts/` directory alike.
    """
    return importlib.import_module(name)


def _minor_module() -> ModuleType:
    """The minor-scope sibling, imported only when a minor scope is named."""
    return _sibling("completion_minor")


def _scoped(args: argparse.Namespace) -> bool:
    """True for a `--minor vX.Y` invocation; exactly one of plan and --minor is required."""
    minor = getattr(args, "minor", None)
    if bool(minor) == bool(getattr(args, "plan", None)):
        raise Malformed("name one plan, or one minor with --minor vX.Y")
    return bool(minor)


def cmd_members(args: argparse.Namespace) -> int:
    return _minor_module().cmd_members(sys.modules[__name__], args)


def cmd_check_minor(args: argparse.Namespace) -> int:
    return _minor_module().cmd_check_minor(sys.modules[__name__], args)


def cmd_score_minor(args: argparse.Namespace) -> int:
    return _minor_module().cmd_score_minor(sys.modules[__name__], args)


def cmd_check_member(args: argparse.Namespace) -> int:
    return _minor_module().cmd_check_member(sys.modules[__name__], args)


def cmd_qualify_task(args: argparse.Namespace) -> int:
    """Only an authenticated active native parent can execute the compiled gates."""
    cm, me = _minor_module(), sys.modules[__name__]
    rctx = cm.repo_context(me, args)
    rctx.budget = Budget(1800)
    state = cm.load_minor(me, rctx, args.minor, args.session)
    if state.forced:
        print(state.forced[0])
        return state.forced[1]
    if state.record is None:
        raise MinorConflict("qualification-parent-unavailable")
    record = state.record
    member = next((m for m in record["members"] if m["version"] == args.member), None)
    plan = next((p for p in cm.scan_plans(rctx.root, *cm.parse_minor(me, args.minor)) if p.version == args.member), None)
    if member is None or plan is None:
        raise MinorConflict("qualification-member-unavailable")
    with minor_transaction(record):
        authority = cm.v415_task_authority(me, rctx, record, member, plan)
        if authority is None:
            raise MinorConflict("qualification-authority-unavailable")
        ctx = Context(str(authority.root / authority.plan_rel), Budget(1800))
        qualify_v415_task(ctx, args.task, authority)
    print(f"QUALIFIED {args.member} {args.task}")
    return 0


def cmd_record_member_implement_start(args: argparse.Namespace) -> int:
    return _minor_module().cmd_record_member_implement_start(sys.modules[__name__], args)


def cmd_record_member_start(args: argparse.Namespace) -> int:
    return _minor_module().cmd_record_member_start(sys.modules[__name__], args)


def _covering_minor(ctx: Context) -> int | None:
    """The refusal when a valid, uncompleted minor record covers this plan's version."""
    token = _minor_module().covering_minor(sys.modules[__name__], ctx, ctx.version)
    if token is None:
        return None
    print(f"BLOCKED: approval-not-covered (minor record {token} covers {ctx.version})")
    return EXIT_BLOCKED


def cmd_record_render(args: argparse.Namespace) -> int:
    mode = render_mode(args)  # a flag conflict is refused before any round opens
    if _scoped(args):
        return _minor_module().cmd_record_render(sys.modules[__name__], args)
    if args.action == "correct-ci-read":
        raise Malformed("--action correct-ci-read requires --minor")
    if getattr(args, "member", None) is not None:
        raise Malformed("--member requires --minor with --action answer, supplement-scope or permit-manifest")
    if (args.action in ("add-class", "supplement-scope", "permit-manifest", "permit-outputs")
            or getattr(args, "added_class", None) is not None or getattr(args, "outputs", None) is not None):
        raise Malformed("--action add-class, supplement-scope, permit-manifest, permit-outputs, --outputs and --class require --minor")
    if getattr(args, "merge", None) is not None:
        raise Malformed("--merge requires --minor with --action supplement-scope")
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
    display: dict | None = None
    if args.action == "create":
        if not args.approvals:
            raise Malformed("record render --action create needs --approvals")
        covered = _covering_minor(ctx)
        if covered is not None:
            return covered
        page = _create_page(ctx, _approvals_from_file(args.approvals))
        minor = _minor_module()
        display = minor.page_display(
            ctx.root, ctx.version, [(ctx.version, ctx.rel, ctx.text)], earlier=False,
            summary=minor.summary_input(sys.modules[__name__], ctx.root, args.summary),
        )
    elif args.action == "retire":
        page = _retire_page(ctx)
        if page is None:
            print("no live run record to retire for this plan", file=sys.stderr)
            return EXIT_MALFORMED
    else:
        loaded = _load_for_update(args, allow_other_session=args.action == "resume")
        if isinstance(loaded, int):
            return loaded
        page = _action_page(ctx, loaded[1], args.action, args.blocker)
    session = None if args.session == "auto" else args.session
    blocker = args.blocker if args.action == "answer" else None

    def data_of(pending: dict) -> dict:
        return approval_page.render_data(pending, scope=ctx.version, blocker=blocker, display=display)

    try:
        pending = approval_binding.render(
            _runs_dir(),
            _round_key(ctx),
            _secret(create=True) or b"",
            action=args.action,
            scope=ctx.version,
            page=page,
            session=session,
            blocker=blocker,
            platform=args.platform,
            allow_short_reply=mode == "question",
            check=lambda pending: approval_page.render_page(data_of(pending)),
        )
    except approval_binding.Refusal as refusal:
        return _refused(refusal.reason)
    except approval_page.PageError as exc:
        print(f"approval page not rendered: {exc}", file=sys.stderr)
        return EXIT_MALFORMED
    return approval_page.emit(data_of(pending), mode)


def render_mode(args: argparse.Namespace) -> str:
    if getattr(args, "question", False):
        if args.json or args.page:
            raise Malformed("--question cannot be combined with --json or --page")
        if args.session == "auto":
            raise Malformed("--question needs an explicit bound session")
        return "question"
    """`record render` prints JSON, the plain-language page, or the bare paste line(s)."""
    if args.json and args.page:
        raise Malformed("choose one of --json and --page")
    return "json" if args.json else "page" if args.page else "lines"


def cmd_record_create(args: argparse.Namespace) -> int:
    if _scoped(args):
        return _minor_module().cmd_record_create(sys.modules[__name__], args)
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
    covered = _covering_minor(ctx)
    if covered is not None:
        return covered
    spec = _approvals_from_file(args.approvals)
    page = _create_page(ctx, spec)
    consumed = _consume(ctx, "create", page, args.session, None)
    if isinstance(consumed, int):
        return consumed
    pending, session = consumed
    approved_repo = str(page["repo"])
    pushed_repo = ctx.url_repo(ctx.push_remote_url)
    if not pushed_repo or pushed_repo.lower() != approved_repo.lower():
        return _refused("push-remote-outside-approval")
    paste = approval_binding.pasted(pending)
    defer = next(
        (c.get("bound") for c in spec["classes"] if c["class"] == "defer-gaps"), []
    ) or []
    approvals = {
        "plan": ctx.rel,
        "remote_url": ctx.remote_url,
        "push_remote_url": ctx.push_remote_url,
        "repo": approved_repo,
        "source_branch": spec.get("source_branch"),
        "target_branch": spec.get("target_branch") or "develop",
        "release_version": spec.get("release_version") or ctx.version,
        "tag": spec.get("tag") or ctx.version,
        "cleanup": spec.get("cleanup") or {"branches": [], "worktrees": []},
        # The user approved the page, and the pasted line is their verbatim text.
        "classes": [{**c, "text": paste} for c in spec["classes"]],
        "page_sha256": hashlib.sha256(approval_binding.canonical(page)).hexdigest(),
        "authorization_context": pending.get('capture'),
        "autonomy_policy": page.get('autonomy'),
    }
    record = {
        "schema": SCHEMA,
        "plan": ctx.rel,
        "plan_sha256": ctx.plan_hash(),
        "repo_root": str(ctx.root),
        "remote_url": ctx.remote_url,
        "repo": approvals["repo"],
        "session_id": session,
        "worktree": str(ctx.root),
        "start_head": page["head"],
        # The round nonce the approval was bound to becomes the run's nonce.
        "nonce": pending["nonce"],
        "created": _now(),
        "approvals": approvals,
        "deferrable_gap_types": sorted(defer),
        "cleanup": approvals["cleanup"],
        "blockers": [],
        "pause": None,
    }
    record["approvals_hmac"] = _sign(record, _secret(create=True) or b"")
    new_path, legacy_path = ctx.record_paths()
    _write_record(new_path, record)
    if legacy_path.is_file():
        # A new record replaces a pre-v4.13.6 one, which would otherwise still be read.
        _retire(legacy_path)
    print(f"RECORDED {ctx.rel} nonce={record['nonce']}")
    return 0


def _retire(path: Path) -> Path:
    """Move a record aside to `runs/retired/`, never deleting it."""
    retired = _runs_dir() / "retired" / f"{path.stem}.{int(time.time())}.json"
    retired.parent.mkdir(parents=True, exist_ok=True)
    _restrict(retired.parent, directory=True)
    os.replace(path, retired)
    return retired


def lock_live(record_path: Path) -> bool:
    """True when a runner holds the lock beside this record (run_plan.py's naming)."""
    lock = record_path.with_name(record_path.stem + ".runner.lock")
    try:
        age = time.time() - lock.stat().st_mtime
    except OSError:
        return False
    try:
        import run_plan  # a sibling, imported only when a lock exists

        stale = float(run_plan.LOCK_STALE_SECONDS)
    except ImportError:
        stale = 6 * 3600.0
    return age <= stale


def record_live(ctx: RepoContext, path: Path) -> tuple[bool, dict | None]:
    """(live, record): not yet stamped complete, or unreadable (counted as someone's)."""
    record = read_record(ctx, path)
    if record is None:
        return True, record
    return not record.get("completed"), record


def mark_completed(ctx: Context, record: dict, head: str) -> None:
    """Stamp a one-plan record complete once its check reports PLAN COMPLETE, and re-sign it.

    The stamp ends the record's liveness, so another run may take the plan and
    cleanup no longer protects its branches; the record still verifies, so the same
    check keeps reporting PLAN COMPLETE.
    """
    key = _secret(create=False)
    if key is None or record.get("completed"):
        return
    record["completed"] = {"at": _now(), "head": head}
    record["approvals_hmac"] = _sign(record, key)
    _write_record(ctx.record_path(), record)


def _retire_page(ctx: Context) -> dict | None:
    """The page a retire paste approves: the nonces of the live records it moves aside."""
    live = []
    for path in plan_record_files(ctx.root, ctx.key_repo, ctx.remote_url, ctx.rel):
        is_live, record = record_live(ctx, path)
        if is_live:
            live.append(str((record or {}).get("nonce") or path.stem))
    if not live:
        return None
    return approval_binding.action_page(
        "retire", rel=ctx.rel, version=ctx.version, record_nonce=",".join(sorted(live))
    )


def cmd_record_retire(args: argparse.Namespace) -> int:
    """Move this plan's per-plan records aside, so a minor run can hold the only authority.

    A completed record or one bound to the caller's own `--session` moves at once. Another session's live record moves only after the user pastes
    the line `record render <plan> --action retire` printed, because retiring it
    removes that run's authority, pause, and blockers.
    """
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
    found = plan_record_files(ctx.root, ctx.key_repo, ctx.remote_url, ctx.rel)
    if not found:
        print("no run record for this plan", file=sys.stderr)
        return 1
    if any(lock_live(p) for p in found):
        return _blocked("owned-by-another-run (a runner holds this record)")
    session = getattr(args, "session", None)
    foreign = []
    for path in found:
        is_live, record = record_live(ctx, path)
        own = bool(session) and session != "auto" and (record or {}).get("session_id") == session
        if is_live and not own:
            foreign.append(path)
    if foreign:
        page = _retire_page(ctx)
        if not session or page is None:
            return _refused("not-rendered")
        consumed = _consume(ctx, "retire", page, session, getattr(args, "text", None))
        if isinstance(consumed, int):
            return consumed
    for path in found:
        _retire(path)
    print(f"RETIRED {ctx.rel}")
    return 0


def _load_for_update(
    args: argparse.Namespace, *, allow_other_session: bool = False
) -> tuple[Context, dict] | int:
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
    session = None if allow_other_session or getattr(args, "session", None) == "auto" else args.session
    state = load_record(ctx, session)
    if state.record is None:
        if state.forced:
            return (
                _blocked(state.forced[0].removeprefix("BLOCKED: "))
                if state.forced[1] == EXIT_BLOCKED
                else EXIT_MALFORMED
            )
        print("no run record for this plan and session", file=sys.stderr)
        return EXIT_MALFORMED
    return ctx, state.record


def _consume_action(
    args: argparse.Namespace, action: str
) -> tuple[Context, dict, dict, str] | int:
    loaded = _load_for_update(args, allow_other_session=action == "resume")
    if isinstance(loaded, int):
        return loaded
    ctx, record = loaded
    page = _action_page(ctx, record, action, getattr(args, "blocker", None))
    # Only a genuine resume capture may carry the record into another session.
    # Pause and blocker answers still require the existing owner's session.
    required = None if action == "resume" else str(record.get("session_id") or "")
    consumed = _consume(
        ctx, action, page, args.session, args.text, required
    )
    if isinstance(consumed, int):
        return consumed
    return ctx, record, consumed[0], consumed[1]


def cmd_record_answer(args: argparse.Namespace) -> int:
    if _scoped(args):
        return _minor_module().cmd_record_answer(sys.modules[__name__], args)
    if getattr(args, "member", None) is not None:
        raise Malformed("--member requires --minor")
    consumed = _consume_action(args, "answer")
    if isinstance(consumed, int):
        return consumed
    ctx, record, pending, _session = consumed
    record["blockers"][args.blocker].update(open=False, answered=_now())
    record["approvals"]["classes"].append(
        {"class": "answer", "blocker": args.blocker, "text": approval_binding.pasted(pending)}
    )
    record["approvals_hmac"] = _sign(record, _secret(create=False) or b"")
    _write_record(ctx.record_path(), record)
    print(f"ANSWERED blocker {args.blocker}")
    return 0


def cmd_record_pause(args: argparse.Namespace) -> int:
    if _scoped(args):
        return _minor_module().cmd_record_action(sys.modules[__name__], args, "pause")
    consumed = _consume_action(args, "pause")
    if isinstance(consumed, int):
        return consumed
    ctx, record, pending, _session = consumed
    record["pause"] = {"at": _now(), "text_sha256": pending["paste_digests"][0]}
    _write_record(ctx.record_path(), record)
    print("PAUSED")
    return 0


def cmd_record_resume(args: argparse.Namespace) -> int:
    if _scoped(args):
        return _minor_module().cmd_record_action(sys.modules[__name__], args, "resume")
    consumed = _consume_action(args, "resume")
    if isinstance(consumed, int):
        return consumed
    ctx, record, _pending, session = consumed
    record["pause"] = None
    record["session_id"] = session
    record["approvals_hmac"] = _sign(record, _secret(create=False) or b"")
    _write_record(ctx.record_path(), record)
    print("RESUMED")
    return 0


def cmd_record_block(args: argparse.Namespace) -> int:
    if _scoped(args):
        return _minor_module().cmd_record_block(sys.modules[__name__], args)
    if args.member:
        raise Malformed("--member applies only with --minor")
    if args.category not in BLOCKER_CATEGORIES:
        raise Malformed(f"unknown blocker category: {args.category}")
    loaded = _load_for_update(args)
    if isinstance(loaded, int):
        return loaded
    ctx, record = loaded
    approved = {c.get("class") for c in record["approvals"].get("classes", [])}
    remote_mismatch = (
        args.category == "approval-not-covered"
        and args.approval_class == "push-merge"
        and _approved_remote_status(ctx, record) != "met"
    )
    if args.approval_class and args.approval_class in approved and not remote_mismatch:
        print(
            f"rejected: the approvals already answer {args.approval_class}",
            file=sys.stderr,
        )
        return EXIT_MALFORMED
    entry = {'category': args.category, 'evidence': args.evidence[:2000], 'open': True, 'at': _now(),
             'approval_class': args.approval_class, 'request': _json_request(getattr(args, 'request', '{}')),
             'purpose': getattr(args, 'purpose', None), 'why': getattr(args, 'why', None)}
    approval_binding.add_blocker(record, entry)
    _write_record(ctx.record_path(), record)
    print(f"BLOCKED: {args.category}")
    return EXIT_BLOCKED


# --------------------------------------------------------------------------- cli



def _continuation_record(args: argparse.Namespace) -> tuple[RepoContext, dict, dict, Path] | int:
    """Load the verified owner and scoped view, including open blockers but never tampering."""
    if _scoped(args):
        module = _minor_module()
        ctx = module.repo_context(sys.modules[__name__], args)
        state = module.load_minor(sys.modules[__name__], ctx, args.minor, args.session, accept_completed=True)
        record = state.record
        if record is None:
            return state.forced[1] if state.forced else EXIT_MALFORMED
        view = project(record, args.member) if getattr(args, 'member', None) else record
        if view is None:
            raise Malformed('member is not in this approved minor')
        if state.forced:
            first = next((item for item in record.get('blockers', []) if isinstance(item, dict) and item.get('open')), None)
            suffix = f" ({first['version']})" if first and first.get('version') else ''
            allowed = f"BLOCKED: {first.get('category')}{suffix}" if first else None
            if state.forced[0] != allowed:
                print(state.forced[0])
                return state.forced[1]
        path = module.record_file(sys.modules[__name__], ctx, args.minor)
    else:
        loaded = _load_for_update(args)
        if isinstance(loaded, int):
            return loaded
        ctx, record = loaded
        view, path = record, ctx.record_path()
    if record.get('pause'):
        print('PAUSED')
        return EXIT_PAUSED
    if record.get('completed'):
        return _blocked('approval-not-covered')
    return ctx, record, view, path


def _validate_scoped_paths(root: Path, paths: object) -> None:
    if not isinstance(paths, list) or not all(isinstance(path, str) for path in paths):
        raise ValueError('request paths must be a list of literal repository paths')
    for path in paths:
        # Reuse the policy literal-path validator and then inspect actual filesystem routing.
        approval_binding.validate_policy({'planned_actions': [{'class': 'ask-first:path-scope', 'paths': [path]}]})
        if not (root / path).resolve().is_relative_to(root.resolve()):
            raise ValueError('a scoped path escapes the approved repository through a link')


def _validate_policy_paths(root: Path, value: object) -> None:
    policy = approval_binding.validate_policy(value)
    _validate_scoped_paths(root, policy['correction_paths'])
    for item in policy['planned_actions']:
        _validate_scoped_paths(root, item['paths'])


def _host_cwds(ctx: RepoContext) -> set[str]:
    paths = {str(ctx.root.resolve())}
    paths.update(str(Path(line[9:]).resolve()) for line in ctx._git_out('worktree', 'list', '--porcelain').splitlines() if line.startswith('worktree '))
    return paths


def _json_request(value: str) -> dict:
    try:
        result = json.loads(value)
    except ValueError as exc:
        raise Malformed('request must be a JSON object') from exc
    if not isinstance(result, dict):
        raise Malformed('request must be a JSON object')
    return result


@minor_operation
def cmd_record_adopt_policy(args: argparse.Namespace) -> int:
    loaded = _continuation_record(args)
    if isinstance(loaded, int):
        return loaded
    ctx, record, _view, path = loaded
    if args.session != record.get('session_id'):
        return _refused('session-mismatch')
    try:
        instruction = Path(args.instruction_file).read_text(encoding='utf-8')
        policy = json.loads(Path(args.policy).read_text(encoding='utf-8'))
        _validate_policy_paths(ctx.root, policy)
        cwds = _host_cwds(ctx)
        approval_binding.adopt_policy(_runs_dir(), record, instruction, policy,
            Path(args.host_transcript) if args.host_transcript else None, cwds,
            historical_cwds=historical_host_cwds(record))
    except (OSError, ValueError, approval_binding.Refusal) as exc:
        print(f'policy not adopted: {exc}', file=sys.stderr)
        return EXIT_BLOCKED
    record['approvals_hmac'] = _sign(record, _secret(create=False) or b'')
    _write_record(path, record)
    print('ADOPTED approved-plan policy from genuine captured user instruction')
    return 0


@minor_operation
def cmd_record_authorize(args: argparse.Namespace) -> int:
    loaded = _continuation_record(args)
    if isinstance(loaded, int):
        return loaded
    ctx, record, view, path = loaded
    if args.session != record.get('session_id'):
        return _refused('session-mismatch')
    if _approved_remote_status(ctx, view) != 'met':
        return _blocked('approval-not-covered')
    try:
        current = approval_binding.current_host_context(_runs_dir(), record, _host_cwds(ctx),
            historical_cwds=historical_host_cwds(record))
        request = _json_request(args.request)
        _validate_scoped_paths(ctx.root, request.get('paths', []))
        event = approval_binding.authorization(view, args.approval_class, request, current)
    except ValueError as exc:
        print(f'authorization not covered: {exc}', file=sys.stderr)
        return EXIT_BLOCKED
    event['member'] = getattr(args, 'member', None)
    events = record['approvals'].setdefault('continuations', [])
    if event not in events:
        events.append(event)
        record['approvals_hmac'] = _sign(record, _secret(create=False) or b'')
        _write_record(path, record)
    print('AUTHORIZED ' + json.dumps(event, sort_keys=True))
    return 0


def _native_user_edit_probe(ctx: RepoContext, view: dict, entry: dict, current: dict) -> dict:
    """Only the unchanged installed official guard can establish that an edit condition is clean."""
    import argparse
    import contextlib
    import io
    import runpy
    policy = approval_binding.validate_policy(view.get('approvals', {}).get('autonomy_policy') or {})
    allowed = sorted({path for item in policy['planned_actions']
                      if item['class'] == 'ask-first:user-edit-baseline' for path in item['paths']})
    paths = (entry.get('request') or {}).get('paths') or allowed
    _validate_scoped_paths(ctx.root, paths)
    approval_binding.authorization(view, 'ask-first:user-edit-baseline', {'paths': paths}, current)
    guard = Path.home() / '.agents' / 'skills' / 'user-edit-preservation' / 'scripts' / 'edit_guard.py'
    if not guard.is_file() or any(guard.resolve().is_relative_to(Path(root)) for root in _host_cwds(ctx)):
        raise ValueError('official guard is unavailable outside the repository')
    functions = runpy.run_path(str(guard))
    store = functions['store_dir']()
    checks = []
    for path in paths:
        args = argparse.Namespace(path=str(ctx.root / path), session=str(view.get('session_id')), stamp=False)
        with contextlib.redirect_stdout(io.StringIO()):
            code = functions['cmd_check'](args, store)
        if code != 0:
            raise ValueError('official user-edit check still reports an unresolved condition')
        checks.append({'path': path, 'exit_code': code})
    return {'origin': 'native-user-edit-check', 'fingerprint': approval_binding.blocker_fingerprint(entry),
            'guard_sha256': hashlib.sha256(guard.read_bytes()).hexdigest(), 'checks': checks,
            'native_predicates_changed': False}


@minor_operation
def cmd_record_resolve(args: argparse.Namespace) -> int:
    loaded = _continuation_record(args)
    if isinstance(loaded, int):
        return loaded
    ctx, record, view, path = loaded
    if args.session != record.get('session_id'):
        return _refused('session-mismatch')
    if _approved_remote_status(ctx, view) != 'met':
        return _blocked('approval-not-covered')
    try:
        entry = record.get('blockers', [])[args.blocker]
        if getattr(args, 'member', None) is not None and entry.get('version') != args.member:
            raise ValueError('member differs from the blocker')
        current = approval_binding.current_host_context(_runs_dir(), record, _host_cwds(ctx),
            historical_cwds=historical_host_cwds(record))
        _validate_scoped_paths(ctx.root, (entry.get('request') or {}).get('paths', []))
        if entry.get('category') == 'user-edit-guard':
            if not entry.get('open') or approval_binding.blocker_fingerprint(entry) != args.fingerprint:
                raise ValueError('blocker is closed or its condition changed')
            result = _native_user_edit_probe(ctx, view, entry, current)
        elif entry.get('category') == 'no-progress' and not args.evidence_file:
            _validate_policy_paths(ctx.root, view.get('approvals', {}).get('autonomy_policy'))
            result = approval_binding.user_continuation(_runs_dir(), view, args.blocker, args.fingerprint,
                _host_cwds(ctx), historical_cwds=historical_host_cwds(record))
        else:
            result = approval_binding.resolution(view, args.blocker, args.fingerprint,
                        Path(args.evidence_file) if args.evidence_file else None, current)
    except (OSError, ValueError, IndexError, TypeError, approval_binding.Refusal) as exc:
        print(f'condition not resolved: {exc}', file=sys.stderr)
        return EXIT_BLOCKED
    entry.update(open=False, answered=_now(), resolution=result)
    # Blockers are mutable, but automatic provenance is also retained inside the signed approvals.
    record['approvals'].setdefault('resolutions', []).append({'blocker': args.blocker, **result})
    record['approvals_hmac'] = _sign(record, _secret(create=False) or b'')
    _write_record(path, record)
    print(f'RESOLVED blocker {args.blocker} ({result["origin"]})')
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_plan_completion", description=__doc__.splitlines()[0]
    )
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="print the completion verdict")
    check.add_argument("plan")
    check.add_argument("--json", action="store_true")
    check.add_argument("--session")
    check.set_defaults(func=cmd_check)
    score = sub.add_parser("score", help="print the monotonic progress score")
    score.add_argument("plan")
    score.add_argument("--session")
    score.set_defaults(func=cmd_score)
    check_minor = sub.add_parser("check-minor", help="print the minor verdict (schema-2 record)")
    check_minor.add_argument("minor", help="a minor scope token such as v0.5")
    check_minor.add_argument("--repo", default=".", help="a path inside the repository")
    check_minor.add_argument("--json", action="store_true")
    check_minor.add_argument("--session")
    check_minor.set_defaults(func=cmd_check_minor)
    member_check = sub.add_parser("check-member", help="read-only member check using parent minor approval")
    member_check.add_argument("--minor", required=True)
    member_check.add_argument("--member", required=True)
    member_check.add_argument("--session", required=True)
    member_check.add_argument("--repo", default=".", help="the parent minor controller repository")
    member_check.add_argument("--json", action="store_true")
    member_check.set_defaults(func=cmd_check_member)
    qualify = sub.add_parser("qualify-task", help="execute fixed native proof for an exact unchanged v4.15 task")
    qualify.add_argument("--minor", required=True)
    qualify.add_argument("--member", required=True)
    qualify.add_argument("--task", required=True)
    qualify.add_argument("--session", required=True)
    qualify.add_argument("--repo", default=".")
    qualify.set_defaults(func=cmd_qualify_task)
    score_minor = sub.add_parser("score-minor", help="print the minor's monotonic progress score")
    score_minor.add_argument("minor", help="a minor scope token such as v0.5")
    score_minor.add_argument("--repo", default=".", help="a path inside the repository")
    score_minor.add_argument("--session")
    score_minor.set_defaults(func=cmd_score_minor)
    members = sub.add_parser(
        "members", help="list a minor's member plans in version order (excluded ones on stderr)"
    )
    members.add_argument("minor", help="a minor scope token such as v0.5")
    members.add_argument("--integration-branch", default="develop")
    members.add_argument("--repo", default=".", help="a path inside the repository")
    members.set_defaults(func=cmd_members)
    record = sub.add_parser("record", help="write the run record").add_subparsers(
        dest="action", required=True
    )
    render = record.add_parser(
        "render", help="open an approval round and print the exact line the user pastes"
    )
    render.add_argument("plan", nargs="?")
    _add_minor_scope(render)
    render.add_argument(
        "--session",
        required=True,
        help="session id, or 'auto' to bind whichever session captures the paste",
    )
    render.add_argument(
        "--action", choices=approval_binding.ACTIONS, default="create"
    )
    render.add_argument("--approvals", help="JSON file of approval classes (create)")
    render.add_argument(
        "--summary",
        help="JSON file of the page's plain outcome bullets and parallel-plan check (create)",
    )
    render.add_argument("--blocker", type=int, help="open blocker index (answer)")
    render.add_argument("--class", dest="added_class", help="with --minor add-class: the class to add")
    render.add_argument("--member", help="with --minor: the member version for the selected member action")
    render.add_argument("--merge", help="with --minor supplement-scope: the exact reviewed merge")
    render.add_argument("--outputs", help="with --minor permit-outputs: exact write_paths JSON file")
    render.add_argument("--json", action="store_true", help="print the canonical page data")
    render.add_argument('--question', action='store_true', help='print an honest concise question and captured short-reply fallback')
    render.add_argument(
        "--page", action="store_true", help="print the plain-language approval page"
    )
    render.add_argument(
        "--platform",
        help="completion-levers row (e.g. claude, codex); picks the paste shape. "
        "Absent or unknown means unverified: the plain approval line approves",
    )
    render.set_defaults(func=cmd_record_render)
    create = record.add_parser("create")
    create.add_argument("plan", nargs="?")
    _add_minor_scope(create)
    create.add_argument(
        "--session",
        required=True,
        help="session id, or 'auto' to bind the session that captured the paste line",
    )
    create.add_argument(
        "--approvals",
        required=True,
        help="the same JSON file of approval classes the page was rendered from",
    )
    create.set_defaults(func=cmd_record_create)
    answer = record.add_parser("answer")
    answer.add_argument("plan", nargs="?")
    _add_minor_scope(answer)
    answer.add_argument("--session", required=True)
    answer.add_argument("--blocker", type=int, required=True)
    answer.add_argument("--member", help="with --minor: require this blocker's member version")
    answer.add_argument("--text", help="when given, must equal the pasted line")
    answer.set_defaults(func=cmd_record_answer)
    for name, func in (("pause", cmd_record_pause), ("resume", cmd_record_resume)):
        action = record.add_parser(name)
        action.add_argument("plan", nargs="?")
        _add_minor_scope(action)
        action.add_argument("--session", required=True)
        action.add_argument("--text", help="when given, must equal the pasted line")
        action.set_defaults(func=func)
    add_class = record.add_parser(
        "add-class", help="add one class to a running minor record from the user's pasted line (minor runs)"
    )
    add_class.add_argument("--minor", required=True)
    add_class.add_argument("--repo", default=".", help="a path inside the repository")
    add_class.add_argument("--session", required=True)
    add_class.add_argument("--class", dest="added_class", required=True, help="the class to add: archive-member")
    add_class.add_argument("--text", help="when given, must equal the pasted line")
    add_class.set_defaults(func=lambda args: _minor_module().cmd_record_add_class(sys.modules[__name__], args))
    supplement = record.add_parser("supplement-scope", help="append the reviewed exact historical scope from a genuine decision")
    supplement.add_argument("--minor", required=True)
    supplement.add_argument("--repo", default=".")
    supplement.add_argument("--session", required=True)
    supplement.add_argument("--member", required=True)
    supplement.add_argument("--merge", required=True)
    supplement.add_argument("--text", help="when given, must equal the captured decision")
    supplement.set_defaults(func=lambda args: _minor_module().cmd_record_supplement_scope(sys.modules[__name__], args))
    permit = record.add_parser("permit-manifest", help="capture the reviewed M5-only dormant manifest publication permission")
    permit.add_argument("--minor", required=True)
    permit.add_argument("--repo", default=".")
    permit.add_argument("--session", required=True)
    permit.add_argument("--member", required=True)
    permit.add_argument("--text", help="when given, must equal the captured decision")
    permit.set_defaults(func=lambda args: _minor_module().cmd_record_permit_manifest(sys.modules[__name__], args))
    outputs = record.add_parser("permit-outputs", help="capture exact v4.15 coordinator output permissions")
    outputs.add_argument("--minor", required=True)
    outputs.add_argument("--repo", default=".")
    outputs.add_argument("--session", required=True)
    outputs.add_argument("--member", required=True)
    outputs.add_argument("--outputs", required=True, help="JSON object containing literal write_paths")
    outputs.add_argument("--text", help="when given, must equal the captured decision")
    outputs.set_defaults(func=lambda args: _minor_module().cmd_record_permit_outputs(sys.modules[__name__], args))
    correction = record.add_parser("correct-ci-read", help="capture the exact v4.15.4 CI read correction")
    correction.add_argument("--minor", required=True)
    correction.add_argument("--repo", default=".")
    correction.add_argument("--session", required=True)
    correction.add_argument("--member", required=True, help="the fixed eligible member v4.15.4")
    correction.add_argument("--text", help="when given, must equal the captured decision")
    correction.set_defaults(func=lambda args: _minor_module().cmd_record_correct_ci_read(sys.modules[__name__], args))
    block = record.add_parser("block")
    block.add_argument("plan", nargs="?")
    _add_minor_scope(block)
    block.add_argument("--member", help="with --minor: the member version the blocker stops")
    block.add_argument("--session")
    block.add_argument("--category", required=True)
    block.add_argument("--evidence", required=True)
    block.add_argument("--approval-class")
    block.add_argument("--purpose", help="concrete action displayed for the decision")
    block.add_argument("--why", help="why that action is needed, bound into the challenge")
    block.add_argument("--request", default="{}", help="JSON action scope, bound into blocker identity")
    block.set_defaults(func=cmd_record_block)
    handoff = record.add_parser('controller-handoff')
    handoff.add_argument('--minor', required=True)
    handoff.add_argument('--session', required=True)
    handoff.add_argument('--repo', required=True)
    handoff.add_argument('--to', required=True)
    handoff.add_argument('--head', required=True)
    handoff.add_argument('--expected-generation', type=int, required=True)
    handoff.add_argument('--apply', action='store_true')
    handoff.set_defaults(func=lambda args: _minor_module().cmd_record_controller_handoff(sys.modules[__name__], args))
    for name, func in (('authorize', cmd_record_authorize), ('adopt-policy', cmd_record_adopt_policy), ('resolve', cmd_record_resolve)):
        operation = record.add_parser(name)
        operation.add_argument('plan', nargs='?')
        _add_minor_scope(operation)
        operation.add_argument('--session', required=True)
        operation.add_argument('--member')
        if name == 'authorize':
            operation.add_argument('--approval-class', required=True)
            operation.add_argument('--request', default='{}', help='JSON fields matching the frozen action scope')
        elif name == 'adopt-policy':
            operation.add_argument('--instruction-file', required=True)
            operation.add_argument('--policy', required=True)
            operation.add_argument('--host-transcript', help='canonical runtime-owned Codex session log, when old captures omitted mode')
        else:
            operation.add_argument('--blocker', type=int, required=True)
            operation.add_argument('--fingerprint', required=True)
            operation.add_argument('--evidence-file', help='fresh condition-repair receipt; no shell commands are executed')
        operation.set_defaults(func=func)
    implement = record.add_parser("member-implement-start", help="reserve a linked worker and its implementation scopes")
    implement.add_argument("--minor", required=True)
    implement.add_argument("--member", required=True)
    implement.add_argument("--session", required=True)
    implement.add_argument("--repo", default=".", help="the parent minor controller repository")
    implement.add_argument("--worktree", required=True, help="the dedicated canonical linked worktree")
    implement.add_argument("--head", required=True, help="the worker branch base commit")
    implement.add_argument("--claims", required=True, help="JSON depends_on, read_paths and write_paths")
    implement.set_defaults(func=cmd_record_member_implement_start)
    start = record.add_parser(
        "member-start", help="pass the member gate and record the member's start_head (minor runs)"
    )
    start.add_argument("--minor", required=True)
    start.add_argument("--member", required=True, help="the member version, such as v0.5.2")
    start.add_argument("--session", required=True)
    start.add_argument(
        "--head", required=True, help="the new member branch's base; must be the live integration tip"
    )
    start.add_argument("--repo", default=".", help="a path inside the repository")
    start.add_argument("--coordinator-claims", help="JSON publication-only write_paths for coordinator updates")
    start.set_defaults(func=cmd_record_member_start)
    where = record.add_parser("path", help="print the run record's path; exit 1 when none exists")
    where.add_argument("plan", nargs="?")
    _add_minor_scope(where)
    where.set_defaults(func=cmd_record_path)
    retire = record.add_parser(
        "retire", help="move a per-plan record aside so a minor run can hold the only authority"
    )
    retire.add_argument("plan")
    retire.add_argument(
        "--session", help="your session id; another session's live record needs the rendered retire line"
    )
    retire.add_argument("--text", help="when given, must equal the pasted line")
    retire.set_defaults(func=cmd_record_retire)
    return parser


def _add_minor_scope(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--minor", help="a minor scope token such as v0.5 (schema-2 record)")
    parser.add_argument("--repo", default=".", help="with --minor: a path inside the repository")


def cmd_record_path(args: argparse.Namespace) -> int:
    if _scoped(args):
        path = _minor_module().minor_record_path(sys.modules[__name__], args)
    else:
        path = Context(args.plan, Budget(BUDGET_SECONDS)).record_path()
    print(path)
    return 0 if path.is_file() else 1


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except _minor_module().ObservationUnavailable as exc:
        print(f"INCOMPLETE: {exc}")
        if getattr(args, "json", False):
            print(json.dumps({"verdict": f"INCOMPLETE: {exc}", "exit": EXIT_INCOMPLETE,
                              "met": None, "head": None, "members": {},
                              "minor": {str(exc): "cannot-verify"}}, sort_keys=True))
        else:
            print(f"{exc} cannot-verify")
        return EXIT_INCOMPLETE
    except MinorConflict as exc:
        print(f"BLOCKED: {exc}")
        return EXIT_BLOCKED
    except Malformed as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_MALFORMED


if __name__ == "__main__":
    raise SystemExit(main())
