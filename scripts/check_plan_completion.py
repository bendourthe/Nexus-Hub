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

Exit codes: 0 PLAN COMPLETE, 1 INCOMPLETE, 3 BLOCKED, 4 PAUSED, 2 malformed input.

Output never carries free text from the plan, the gaps file, git, or gh: only
fixed predicate ids and statuses, so a gate can hand it to a model safely.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import approval_binding  # noqa: E402  (installed as a sibling in ~/.nexus-hub/scripts/)
import repo_host  # noqa: E402  (installed as a sibling in ~/.nexus-hub/scripts/)

EXIT_COMPLETE, EXIT_INCOMPLETE, EXIT_MALFORMED, EXIT_BLOCKED, EXIT_PAUSED = (
    0,
    1,
    2,
    3,
    4,
)
SCHEMA = 1
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
}
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
        "GIT_CEILING_DIRECTORIES", "GIT_PREFIX", "GIT_NAMESPACE",
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


class Context:
    def __init__(self, plan_arg: str, budget: Budget) -> None:
        self.budget = budget
        plan = Path(plan_arg).expanduser()
        if not plan.is_file():
            raise Malformed(f"plan not found: {plan_arg}")
        self.plan = plan.resolve()
        self.git = repo_host.absolute_tool("git", None)
        if not self.git:
            raise Malformed("git not found")
        rc, out = _run(
            [self.git, "-C", str(self.plan.parent), "rev-parse", "--show-toplevel"],
            budget,
        )
        if rc != 0:
            raise Malformed("plan is not inside a git repository")
        self.root = Path(out.strip()).resolve()
        # Re-resolve git outside the tree now that the tree is known.
        self.git = repo_host.absolute_tool("git", self.root)
        if not self.git:
            raise Malformed("git resolves inside the working tree; refusing")
        self.gh = repo_host.absolute_tool("gh", self.root)
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
        self.remote_url = self._git_out("remote", "get-url", "origin")
        self.push_remote_url = self._git_out("remote", "get-url", "--push", "--all", "origin")
        self._default_repo: str | None = None

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

    def url_repo(self, url: str) -> str | None:
        """The verified repository one remote URL names, or None."""
        repo, _reason = repo_host.repo_from_url(url, repo_root=self.root, run=self.run)
        return repo

    def _git_out(self, *args: str) -> str:
        rc, out = _run([self.git, "-C", str(self.root), *args], self.budget)
        return out.strip() if rc == 0 else ""

    def plan_hash(self) -> str:
        """sha256 of the plan with every checkbox normalized, so ticks do not count as edits."""
        return hashlib.sha256(
            CHECKBOX_RE.sub(r"\1[ ]", self.text).encode("utf-8")
        ).hexdigest()

    def record_path(self) -> Path:
        key = hashlib.sha256(
            "\n".join((str(self.root), self.remote_url, self.rel)).encode("utf-8")
        ).hexdigest()
        return _runs_dir() / f"{key}.json"


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


def _hmac_payload(record: dict) -> dict:
    return {
        k: record.get(k)
        for k in (
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
    }


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


def load_record(ctx: Context, session: str | None) -> RecordState:
    state = RecordState()
    path = ctx.record_path()
    if not path.is_file():
        return state
    tampered = ("BLOCKED: record-tampered", EXIT_BLOCKED)
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
            state.forced = tampered
            return state
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        state.forced = tampered
        return state
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
        or record.get("plan_sha256") != ctx.plan_hash()
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
    return results, deferred


def _approved_remote_status(ctx: Context, record: dict | None) -> str:
    if record is None:
        return "cannot-verify"
    approvals = record.get("approvals", {})
    expected_url = approvals.get("push_remote_url")
    if not expected_url or ctx.push_remote_url != expected_url:
        return "unmet"
    pushed_repo = ctx.url_repo(ctx.push_remote_url)
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
    for notice in state.notices:
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


def _approvals_from_file(path: str) -> dict:
    try:
        spec = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Malformed(f"approvals file unreadable: {exc.__class__.__name__}") from exc
    classes = spec.get("classes")
    if not isinstance(classes, list) or not classes:
        raise Malformed("approvals file needs a non-empty 'classes' list")
    for entry in classes:
        name = str(entry.get("class", ""))
        if not (name in APPROVAL_CLASSES or name.startswith("ask-first:")):
            raise Malformed(f"approval class not approvable in advance: {name}")
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


def cmd_record_render(args: argparse.Namespace) -> int:
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
    if args.action == "create":
        if not args.approvals:
            raise Malformed("record render --action create needs --approvals")
        page = _create_page(ctx, _approvals_from_file(args.approvals))
    else:
        loaded = _load_for_update(args)
        if isinstance(loaded, int):
            return loaded
        page = _action_page(ctx, loaded[1], args.action, args.blocker)
    session = None if args.session == "auto" else args.session
    try:
        pending = approval_binding.render(
            _runs_dir(),
            _round_key(ctx),
            _secret(create=True) or b"",
            action=args.action,
            scope=ctx.version,
            page=page,
            session=session,
            blocker=args.blocker if args.action == "answer" else None,
        )
    except approval_binding.Refusal as refusal:
        return _refused(refusal.reason)
    if args.json:
        print(
            json.dumps(
                {
                    "paste": pending["paste_lines"],
                    "page": pending["page"],
                    "expires_at": pending["expires_at"],
                },
                sort_keys=True,
            )
        )
    else:
        for line in pending["paste_lines"]:
            print(line)
    return 0


def cmd_record_create(args: argparse.Namespace) -> int:
    ctx = Context(args.plan, Budget(BUDGET_SECONDS))
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
    _write_record(ctx.record_path(), record)
    print(f"RECORDED {ctx.rel} nonce={record['nonce']}")
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
    consumed = _consume_action(args, "pause")
    if isinstance(consumed, int):
        return consumed
    ctx, record, pending = consumed
    record["pause"] = {"at": _now(), "text_sha256": pending["paste_digests"][0]}
    _write_record(ctx.record_path(), record)
    print("PAUSED")
    return 0


def cmd_record_resume(args: argparse.Namespace) -> int:
    consumed = _consume_action(args, "resume")
    if isinstance(consumed, int):
        return consumed
    ctx, record, _pending = consumed
    record["pause"] = None
    _write_record(ctx.record_path(), record)
    print("RESUMED")
    return 0


def cmd_record_block(args: argparse.Namespace) -> int:
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
    record = sub.add_parser("record", help="write the run record").add_subparsers(
        dest="action", required=True
    )
    render = record.add_parser(
        "render", help="open an approval round and print the exact line the user pastes"
    )
    render.add_argument("plan")
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
    render.add_argument("--json", action="store_true")
    render.set_defaults(func=cmd_record_render)
    create = record.add_parser("create")
    create.add_argument("plan")
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
        action.add_argument("plan")
        action.add_argument("--session", required=True)
        action.add_argument("--text", help="when given, must equal the pasted line")
        action.set_defaults(func=func)
    block = record.add_parser("block")
    block.add_argument("plan")
    block.add_argument("--session")
    block.add_argument("--category", required=True)
    block.add_argument("--evidence", required=True)
    block.add_argument("--approval-class")
    block.set_defaults(func=cmd_record_block)
    where = record.add_parser("path", help="print the run record's path; exit 1 when none exists")
    where.add_argument("plan")
    where.set_defaults(func=cmd_record_path)
    return parser


def cmd_record_path(args: argparse.Namespace) -> int:
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
