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
    record render|create|pause|resume|block|path --minor <vX.Y> ...
                                           the schema-2 minor record (completion_minor.py)
    record member-start --minor <vX.Y> --member <vX.Y.Z> --session ID --head SHA
                                           pass the member gate; record the member's start_head
    check-minor <vX.Y> [--json] [--session ID]
                                           the minor verdict, then per-member and minor lines
    score-minor <vX.Y> [--session ID]      the minor's progress score

Exit codes: 0 PLAN COMPLETE (or MINOR COMPLETE), 1 INCOMPLETE, 3 BLOCKED, 4 PAUSED, 2 malformed input.

Output never carries free text from the plan, the gaps file, git, or gh: only
fixed predicate ids and statuses, so a gate can hand it to a model safely.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import importlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

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
STALE_SECONDS = 72 * 3600

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
    "gap-migration",
    "archive-minor",
    "minor-close-pr",
}
MINOR_ONLY_CLASSES = {"gap-migration", "archive-minor", "minor-close-pr"}
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
    if record.get("schema") != SCHEMA:
        # Anything that is not a schema-1 record signs the minor fields too; a schema-1
        # payload stays exactly as it was, so existing records still verify.
        fields = _SIGNED_FIELDS + _SIGNED_MINOR_FIELDS
    return {k: record.get(k) for k in fields}


def _sign(record: dict, key: bytes) -> str:
    return hmac.new(key, _canonical(_hmac_payload(record)), hashlib.sha256).hexdigest()


def _write_record(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _restrict(path.parent, directory=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _restrict(tmp, directory=False)
    os.replace(tmp, path)


class RecordState:
    """The loaded record plus the verdict its state forces, if any."""

    def __init__(self) -> None:
        self.record: dict | None = None
        self.forced: tuple[str, int] | None = None  # (verdict line, exit code)
        self.notices: list[str] = []


TAMPERED = ("BLOCKED: record-tampered", EXIT_BLOCKED)


def read_record(ctx: RepoContext, path: Path) -> dict | None:
    """The raw record at `path`, or None when it sits in a working tree or is unreadable.

    Callers treat None for an existing file as `record-tampered`.
    """
    rc, out = _run(
        [ctx.git, "-C", str(path.parent), "rev-parse", "--is-inside-work-tree"],
        ctx.budget,
    )
    if rc == 0 and out.strip() == "true":
        tracked_rc, _ = _run(
            [ctx.git, "-C", str(path.parent), "ls-files", "--error-unmatch", "--", path.name],
            ctx.budget,
        )
        if tracked_rc != 1:
            return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    return record if isinstance(record, dict) else None


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
        created = _parse_time(record.get("created"))
        age = (
            (dt.datetime.now(dt.timezone.utc) - created).total_seconds()
            if created and created.tzinfo is not None
            else STALE_SECONDS + 1
        )
        reason = (
            "stale run record (older than 72 hours) ignored"
            if age > STALE_SECONDS
            else "run record bound to another session ignored"
        )
        state.notices.append(reason)
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
    # WN-13: a matching or unspecified session does not renew old approvals.
    created = _parse_time(record.get("created"))
    if created is None or created.tzinfo is None or (
        dt.datetime.now(dt.timezone.utc) - created
    ).total_seconds() > STALE_SECONDS:
        state.notices.append("stale run record (older than 72 hours) ignored")
        return state
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
        "page_sha256": minor.get("page_sha256"),
    }
    return {
        "schema": record.get("schema"),
        "scope": "member",
        "minor": record.get("minor"),
        "plan": member.get("plan_path"),
        "plan_sha256": member.get("plan_sha256"),
        "repo_root": record.get("repo_root"),
        "remote_url": record.get("remote_url"),
        "repo": record.get("repo"),
        "session_id": record.get("session_id"),
        "worktree": member.get("worktree") or record.get("worktree"),
        "start_head": member.get("start_head") or record.get("start_head"),
        # The run began at the minor record's start: a gap created after it never migrates.
        "minor_start_head": record.get("start_head"),
        "nonce": record.get("nonce"),
        "created": record.get("created"),
        "approvals": approvals,
        # Minor runs have no deferrable state: a gap is fixed or migrated.
        "deferrable_gap_types": [],
        "cleanup": cleanup,
        "blockers": record.get("blockers") or [],
        "pause": record.get("pause"),
    }


def _parse_time(value: object) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- predicates


def evaluate(ctx: Context, record: dict | None) -> tuple[list[tuple[str, str]], int]:
    """Return ([(predicate id, status)], deferred item count)."""
    results: list[tuple[str, str]] = []
    approvals = (record or {}).get("approvals", {})
    start = (record or {}).get("start_head")
    for tid, checked, path in ctx.tasks:
        results.append((f"task.{tid}", _task_status(ctx, checked, path, start)))
    gaps_status, deferred = _gaps_status(ctx, record)
    results.append(("gaps.version", gaps_status))
    evidence = _evidence_file(ctx)
    results.append(
        ("evidence.file", "met" if evidence and _has_sections(evidence) else "unmet")
    )
    results.append(("tests.evidence", _tests_status(ctx, evidence, start)))
    results.append(("approval.remote", _approved_remote_status(ctx, record)))
    repo = approvals.get("repo") or ctx.default_repo
    branch = approvals.get("source_branch") or f"feat/{ctx.version}-{ctx.slug}"
    target = approvals.get("target_branch") or "develop"
    results.append(("integration.merged", _pr_merged(ctx, repo, branch)))
    results.append(("integration.checks", _pr_checks(ctx, repo, branch, target)))
    tag = approvals.get("tag") or ctx.version
    results.append(("release.tag", _tag_status(ctx, tag)))
    results.append(("release.changelog", _changelog_status(ctx)))
    results.append(("release.version-sync", _version_sync(ctx)))
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
    return results, deferred


def _approved_remote_status(ctx: Context, record: dict | None) -> str:
    if record is None:
        return "cannot-verify"
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


def _task_status(ctx: Context, checked: bool, path: str, start: str | None) -> str:
    if not checked or not path:
        return "unmet"
    if not start:
        return "met"
    rc, out = _run(
        [
            ctx.git,
            "-C",
            str(ctx.root),
            "log",
            "--format=%H",
            f"{start}..HEAD",
            "--",
            path,
        ],
        ctx.budget,
    )
    if rc != 0:
        return "cannot-verify"
    return "met" if out.strip() else "unmet"


def _gaps_status(ctx: Context, record: dict | None) -> tuple[str, int]:
    gaps = ctx.version_dir / "known-gaps.md"
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
        if MIGRATED_MARKER_RE.search(item.group("title")) and _migration_met(ctx, record, gaps, item.group(0)):
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
    """True for a minor member's open item listed in the record's frozen `gap-migration` ids.

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
    bound, named = cm.migration_class(record)
    pid = f"{record['minor']}#{found.group(1)}"
    if pid not in bound:
        return False
    item = next((i for i in cm.parse_ledger(text) if i.gid == found.group(1)), None)
    # An item the ledger parser cannot see is treated as sensitive: never deferred on a guess.
    if item is None or (item.sensitive() and pid not in named):
        return False
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


def _evidence_file(ctx: Context) -> str | None:
    development = ctx.version_dir / "development"
    scoped = development / f"{ctx.version}-last-phase-evidence.md"
    for candidate, needs_name in (
        (scoped, False),
        (development / "last-phase-evidence.md", True),
    ):
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


def _required_contexts(ctx: Context, target: str) -> list[str] | None:
    manifest = ctx.root / "docs" / "policy" / "required-checks.json"
    if not manifest.is_file():
        return None
    try:
        branches = json.loads(manifest.read_text(encoding="utf-8")).get("branches", {})
    except ValueError:
        return None
    contexts = branches.get(target, {}).get("contexts")
    return list(contexts) if isinstance(contexts, list) else None


def _pr_checks(ctx: Context, repo: str, branch: str, target: str) -> str:
    required = _required_contexts(ctx, target)
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
    if rc != 0 or out.strip() != tag:
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


def _version_sync(ctx: Context) -> str:
    script = ctx.root / "scripts" / "check_version_sync.py"
    if not script.is_file():
        return "n/a"
    rc, _ = _run([sys.executable, str(script)], ctx.budget, cwd=ctx.root)
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
        if name in MINOR_ONLY_CLASSES and not minor:
            raise Malformed(f"approval class {name} belongs to a minor run (record ... --minor vX.Y)")
    defer = next((c.get("bound") for c in classes if c["class"] == "defer-gaps"), []) or []
    if not set(defer) <= GAP_TYPES:
        raise Malformed("defer-gaps bound must list gap types from NI DF BG MT WN QG")
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
    return approval_binding.action_page(
        action,
        rel=ctx.rel,
        version=ctx.version,
        record_nonce=str(record.get("nonce", "")),
        blocker=blocker,
        category=category,
    )


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
    if text is not None and normalize(text) not in {normalize(x) for x in pending["paste_lines"]}:
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
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
    display: dict | None = None
    if args.action == "create":
        if not args.approvals:
            raise Malformed("record render --action create needs --approvals")
        covered = _covering_minor(ctx)
        if covered is not None:
            return covered
        page = _create_page(ctx, _approvals_from_file(args.approvals))
        display = _minor_module().page_display(
            ctx.root, ctx.version, [(ctx.version, ctx.rel, ctx.text)], earlier=False
        )
    elif args.action == "retire":
        page = _retire_page(ctx)
        if page is None:
            print("no live run record to retire for this plan", file=sys.stderr)
            return EXIT_MALFORMED
    else:
        loaded = _load_for_update(args)
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
            check=lambda pending: approval_page.render_page(data_of(pending)),
        )
    except approval_binding.Refusal as refusal:
        return _refused(refusal.reason)
    except approval_page.PageError as exc:
        print(f"approval page not rendered: {exc}", file=sys.stderr)
        return EXIT_MALFORMED
    return approval_page.emit(data_of(pending), mode)


def render_mode(args: argparse.Namespace) -> str:
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
    paste = " / ".join(pending["paste_lines"])
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
    """(live, record): created within 72 hours, or unreadable (counted as someone's)."""
    record = read_record(ctx, path)
    created = _parse_time((record or {}).get("created"))
    if record is None or created is None or created.tzinfo is None:
        return True, record
    age = (dt.datetime.now(dt.timezone.utc) - created).total_seconds()
    return age <= STALE_SECONDS, record


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

    A stale record (older than 72 hours) or one bound to the caller's own `--session`
    moves at once. Another session's live record moves only after the user pastes
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


def _load_for_update(args: argparse.Namespace) -> tuple[Context, dict] | int:
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
    session = None if getattr(args, "session", None) == "auto" else args.session
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
) -> tuple[Context, dict, dict] | int:
    loaded = _load_for_update(args)
    if isinstance(loaded, int):
        return loaded
    ctx, record = loaded
    page = _action_page(ctx, record, action, getattr(args, "blocker", None))
    # The paste must land in the session the record is bound to: an answer captured
    # in any other session, such as one the agent launched, clears nothing.
    consumed = _consume(
        ctx, action, page, args.session, args.text, str(record.get("session_id") or "")
    )
    if isinstance(consumed, int):
        return consumed
    return ctx, record, consumed[0]


def cmd_record_answer(args: argparse.Namespace) -> int:
    consumed = _consume_action(args, "answer")
    if isinstance(consumed, int):
        return consumed
    ctx, record, pending = consumed
    record["blockers"][args.blocker].update(open=False, answered=_now())
    record["approvals"]["classes"].append(
        {"class": "answer", "blocker": args.blocker, "text": " / ".join(pending["paste_lines"])}
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
    ctx, record, pending = consumed
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
    ctx, record, _pending = consumed
    record["pause"] = None
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
    record.setdefault("blockers", []).append(
        {
            "category": args.category,
            "evidence": args.evidence[:2000],
            "open": True,
            "at": _now(),
        }
    )
    _write_record(ctx.record_path(), record)
    print(f"BLOCKED: {args.category}")
    return EXIT_BLOCKED


# --------------------------------------------------------------------------- cli


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
    render.add_argument("--blocker", type=int, help="open blocker index (answer)")
    render.add_argument("--json", action="store_true", help="print the canonical page data")
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
    answer.add_argument("plan")
    answer.add_argument("--session", required=True)
    answer.add_argument("--blocker", type=int, required=True)
    answer.add_argument("--text", help="when given, must equal the pasted line")
    answer.set_defaults(func=cmd_record_answer)
    for name, func in (("pause", cmd_record_pause), ("resume", cmd_record_resume)):
        action = record.add_parser(name)
        action.add_argument("plan", nargs="?")
        _add_minor_scope(action)
        action.add_argument("--session", required=True)
        action.add_argument("--text", help="when given, must equal the pasted line")
        action.set_defaults(func=func)
    block = record.add_parser("block")
    block.add_argument("plan", nargs="?")
    _add_minor_scope(block)
    block.add_argument("--member", help="with --minor: the member version the blocker stops")
    block.add_argument("--session")
    block.add_argument("--category", required=True)
    block.add_argument("--evidence", required=True)
    block.add_argument("--approval-class")
    block.set_defaults(func=cmd_record_block)
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
    except Malformed as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_MALFORMED


if __name__ == "__main__":
    raise SystemExit(main())
