#!/usr/bin/env python3
"""Minor-scope membership and the schema-2 run record for `/implement vX.Y`.

Installed at ~/.nexus-hub/scripts/completion_minor.py beside
check_plan_completion.py, which dispatches here and stays a thin dispatcher:

    check_plan_completion.py members vX.Y        one member plan path per line, in
                                                 version order; excluded plans and
                                                 their reason on stderr
    check_plan_completion.py record render|create --minor vX.Y --session ID --approvals F
    check_plan_completion.py record pause|resume --minor vX.Y --session ID
    check_plan_completion.py record path --minor vX.Y

The rules this module executes are owned by the completion contract
(catalog/skills/workflow/implement-phase/references/completion-contract.md,
"Run record" and "Minor membership"); read it before changing this file.

Every function takes the checker module as `ck` instead of importing it, so the
checker run as a script and the checker imported by a test share one module.
Output never carries free text from a plan, git, or gh: only repository-relative
plan paths, validated version tokens, and fixed reason ids.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import approval_binding  # installed as a sibling in ~/.nexus-hub/scripts/

if TYPE_CHECKING:
    from check_plan_completion import RepoContext

MINOR_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PLAN_VERSION_RE = re.compile(
    r"^\*\*Version\*\*:\s*v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\b", re.MULTILINE
)
ANY_VERSION_RE = re.compile(r"^\*\*Version\*\*:\s*v?\d+\.\d+\.\d+\b", re.MULTILINE)
STATUS_RE = re.compile(r"^\*\*Status\*\*:\s*`?([A-Za-z-]+)", re.MULTILINE)
SLUG_RE = re.compile(r"^\*\*Slug\*\*:\s*([A-Za-z0-9._-]+)", re.MULTILINE)
GAP_ID_RE = re.compile(r"^v\d+\.\d+(?:\.\d+)?#[A-Z]{2}-\d+$")
BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")

DONE_STATUSES = {"complete", "superseded", "shipped"}
MINOR_VALID_SECONDS = 14 * 24 * 3600
MINOR_BUDGET_SECONDS = 60.0
EXIT_EMPTY = 1
EXIT_MINOR_MALFORMED = 3  # a duplicate version or an unreadable plan stops the run

# Canonical, legacy, and archive layouts, in that order. Membership reads each
# plan's own `**Version**` line, so a directory only narrows the search.
PLAN_GLOBS = (
    "docs/releases/v{M}/v{M}.{m}/plans/*.md",
    "docs/v{M}/v{M}.{m}/plans/*.md",
    "docs/versions/v{M}/v{M}.{m}/plans/*.md",
    "docs/v{M}.{m}/plans/*.md",
    "docs/archives/v{M}/v{M}.{m}/plans/*.md",
    "docs/archive/v{M}/v{M}.{m}/plans/*.md",
    "docs/archive/versions/v{M}/v{M}.{m}/plans/*.md",
)


class MinorMalformed(Exception):
    """A minor whose plans cannot be ordered: exit 3 with `MALFORMED: ...`."""


@dataclass
class Plan:
    rel: str
    version: str
    order: tuple[int, int, int]
    status: str
    slug: str
    text: str


@dataclass
class Membership:
    members: list[Plan] = field(default_factory=list)
    excluded: list[tuple[Plan, str]] = field(default_factory=list)

    def undecidable(self) -> list[Plan]:
        return [p for p, reason in self.excluded if reason in ("cannot-verify-shipped", "cannot-verify-owned")]


@dataclass
class MinorState:
    record: dict | None = None
    forced: tuple[str, int] | None = None
    notices: list[str] = field(default_factory=list)
    # A verified record bound to another session: only a resume paste may adopt it.
    other_session: dict | None = None


# --------------------------------------------------------------------------- parsing


def parse_minor(ck: ModuleType, token: str) -> tuple[int, int]:
    """(major, minor) for `vMAJOR.MINOR`; anything else is usage, never a run."""
    match = MINOR_RE.match(token or "")
    if not match:
        raise ck.Malformed(f"not a minor scope token (expected vMAJOR.MINOR such as v0.5): {token!r}")
    return int(match.group(1)), int(match.group(2))


def scan_plans(root: Path, major: int, minor: int) -> list[Plan]:
    """Every plan of the minor across all layouts, deduplicated by path.

    Raises MinorMalformed for an unreadable plan or two plans with one version.
    """
    seen: dict[str, Path] = {}
    for pattern in PLAN_GLOBS:
        for path in sorted(root.glob(pattern.format(M=major, m=minor))):
            seen.setdefault(path.resolve().as_posix(), path)
    plans: list[Plan] = []
    for path in seen.values():
        rel = path.resolve().relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise MinorMalformed(f"plan unreadable {rel}") from exc
        found = PLAN_VERSION_RE.search(text)
        if not found:
            if ANY_VERSION_RE.search(text):
                # `v0.05.2` would order and key like v0.5.2 while reading as another plan.
                raise MinorMalformed(f"non-canonical version in {rel}")
            continue
        order = (int(found.group(1)), int(found.group(2)), int(found.group(3)))
        if order[:2] != (major, minor):
            continue
        status = STATUS_RE.search(text)
        slug = SLUG_RE.search(text)
        plans.append(
            Plan(
                rel=rel,
                version="v{}.{}.{}".format(*order),
                order=order,
                status=(status.group(1).lower() if status else ""),
                slug=(slug.group(1) if slug else path.stem),
                text=text,
            )
        )
    versions: dict[str, str] = {}
    for plan in sorted(plans, key=lambda p: (p.order, p.rel)):
        if plan.version in versions:
            raise MinorMalformed(f"duplicate version {plan.version}")
        versions[plan.version] = plan.rel
    return sorted(plans, key=lambda p: p.order)


# --------------------------------------------------------------------------- repository state


def repo_context(ck: ModuleType, args: argparse.Namespace) -> RepoContext:
    return ck.RepoContext(Path(getattr(args, "repo", ".") or ".").resolve(), ck.Budget(MINOR_BUDGET_SECONDS))


def hosting_repo(ck: ModuleType, rctx: RepoContext, frozen: str | None = None) -> str:
    """The owner/repo hosting calls are pinned to.

    A frozen record repository first, else `repo_host.resolve_repo` (the verified
    origin URL cross-checked with `gh`), else the verified push URL's repository,
    which is the destination the approval names.
    """
    repo, _reason = ck.repo_host.resolve_repo(
        rctx.root, record_repo=frozen, git=rctx.git, gh=rctx.gh or "", run=rctx.run
    )
    return repo or rctx.url_repo(rctx.push_remote_url) or ""


def shipped(ck: ModuleType, rctx: RepoContext, repo: str, tag: str) -> str:
    """`met` when the tag is local and remote AND its Release is published.

    `unmet` when either is definitely absent; `cannot-verify` otherwise, which keeps
    the plan out of the members and stops the run rather than rebuilding a release.
    """
    tag_status = ck._tag_status(rctx, tag)
    if tag_status != "met":
        return tag_status if tag_status == "cannot-verify" else "unmet"
    return ck._release_status(rctx, repo, tag)


@dataclass
class Heads:
    """Every `feat/*` tip the ownership rule reads, and whether origin answered."""

    refs: dict[str, str] = field(default_factory=dict)
    remote_ok: bool = True


def _feat_heads(ck: ModuleType, rctx: RepoContext) -> Heads:
    """Local branches, local remote-tracking refs, and origin's live heads under `feat/`.

    Remote names carry an `origin:` prefix. When `ls-remote` fails, `remote_ok` is
    False: the remote-tracking refs still count, but a plan no other rule owns is
    then undecidable rather than assumed free.
    """
    heads = Heads()
    rc, out = rctx.run(
        [rctx.git, "-C", str(rctx.root), "for-each-ref", "--format=%(objectname) %(refname)",
         "refs/heads/feat/", "refs/remotes/origin/feat/"]
    )
    for line in out.splitlines() if rc == 0 else []:
        sha, _, ref = line.partition(" ")
        if ref.startswith("refs/remotes/origin/"):
            heads.refs["origin:" + ref.removeprefix("refs/remotes/origin/")] = sha
        else:
            heads.refs[ref.removeprefix("refs/heads/")] = sha
    rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "ls-remote", "--heads", "origin"])
    if rc != 0:
        heads.remote_ok = False
        return heads
    for line in out.splitlines():
        sha, _, ref = line.partition("\t")
        if ref.startswith("refs/heads/feat/"):
            # The live remote tip wins over a stale remote-tracking ref for the same branch.
            heads.refs["origin:" + ref.removeprefix("refs/heads/")] = sha
    return heads


def _integration_ref(rctx: RepoContext, branch: str) -> str | None:
    for ref in (f"refs/remotes/origin/{branch}", f"refs/heads/{branch}"):
        rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "rev-parse", "--verify", "-q", ref])
        if rc == 0:
            return ref
    return None


def _merged(rctx: RepoContext, sha: str, integration: str | None) -> bool:
    if integration is None:
        return False  # nothing to compare against: treat the branch as live work
    rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "merge-base", "--is-ancestor", sha, integration])
    return rc == 0


def plan_records(ck: ModuleType, rctx: RepoContext, rel: str) -> list[Path]:
    """Both key paths of a plan's record (for their locks) plus every record found by content."""
    paths = list(ck.plan_record_paths(rctx.root, rctx.key_repo, rctx.remote_url, rel))
    for path in ck.plan_record_files(rctx.root, rctx.key_repo, rctx.remote_url, rel):
        if path not in paths:
            paths.append(path)
    return paths


def _minor_record_live(ck: ModuleType, record: dict) -> bool:
    created = ck._parse_time(record.get("created"))
    if created is None or created.tzinfo is None:
        return True  # unreadable time: someone's record, never absorbed
    age = (dt.datetime.now(dt.timezone.utc) - created).total_seconds()
    return age <= MINOR_VALID_SECONDS and not record.get("completed")


def other_minor_owns(ck: ModuleType, rctx: RepoContext, version: str, own: Path | None) -> bool:
    """Another live minor record, anywhere in the runs directory, lists this version."""
    def lists(record: dict) -> bool:
        members = record.get("members") if isinstance(record.get("members"), list) else []
        return record.get("schema") == ck.SCHEMA_MINOR and any(
            isinstance(m, dict) and m.get("version") == version for m in members
        )

    for path in ck.find_records_by_content(rctx.root, lists):
        if own is not None and path.resolve() == own.resolve():
            continue
        record = ck.read_record(rctx, path)
        if record is None or _minor_record_live(ck, record):
            return True
    return False


def ownership(
    ck: ModuleType,
    rctx: RepoContext,
    plan: Plan,
    heads: Heads,
    integration: str | None,
    ours: set[str],
    own: Path | None = None,
) -> str | None:
    """`owned-by-another-run`, `cannot-verify-owned`, or None when the plan is free.

    Owned: a live per-plan record (at either key or found by content) or runner lock,
    another live minor record listing the version, or an unmerged `feat/<version>-*`
    branch (local, remote-tracking, or live on origin) that is not ours. When origin
    could not be asked, a plan none of these owns is undecidable.
    """
    for path in plan_records(ck, rctx, plan.rel):
        if ck.lock_live(path):
            return "owned-by-another-run"
        if path.is_file() and ck.record_live(rctx, path)[0]:
            return "owned-by-another-run"
    if other_minor_owns(ck, rctx, plan.version, own):
        return "owned-by-another-run"
    prefix = f"feat/{plan.version}-"
    for name, sha in heads.refs.items():
        branch = name.removeprefix("origin:")
        if branch.startswith(prefix) and branch not in ours and not _merged(rctx, sha, integration):
            return "owned-by-another-run"
    return None if heads.remote_ok else "cannot-verify-owned"


def resolve_members(
    ck: ModuleType,
    rctx: RepoContext,
    token: str,
    *,
    integration_branch: str = "develop",
    frozen_repo: str | None = None,
    ours: set[str] | None = None,
    own: Path | None = None,
) -> Membership:
    """Apply the membership predicate to every plan of the minor, in version order."""
    major, minor = parse_minor(ck, token)
    plans = scan_plans(rctx.root, major, minor)
    result = Membership()
    repo = ""
    heads: Heads | None = None
    integration: str | None = None
    for plan in plans:
        if plan.status in DONE_STATUSES:
            result.excluded.append((plan, f"status-{plan.status}"))
            continue
        if not repo:
            repo = hosting_repo(ck, rctx, frozen_repo)
        state = shipped(ck, rctx, repo, plan.version)
        if state == "met":
            result.excluded.append((plan, "shipped"))
            continue
        if state == "cannot-verify":
            result.excluded.append((plan, "cannot-verify-shipped"))
            continue
        if heads is None:
            heads = _feat_heads(ck, rctx)
            integration = _integration_ref(rctx, integration_branch)
        reason = ownership(ck, rctx, plan, heads, integration, ours or set(), own)
        if reason:
            result.excluded.append((plan, reason))
            continue
        result.members.append(plan)
    return result


# --------------------------------------------------------------------------- approvals and page


def minor_spec(ck: ModuleType, path: str) -> dict:
    """The approvals file for a minor run, validated.

    Per-plan classes apply to every member; `cleanup-merged`, `gap-migration`
    (bound: the frozen list of migratable gap ids), `archive-minor`, and
    `minor-close-pr` are minor-level. `defer-gaps` is refused: in a minor run a gap
    is fixed or migrated. `members` may override one member's branch, tag, or cleanup.
    """
    spec = ck._approvals_from_file(path, minor=True)
    for entry in spec["classes"]:
        name = entry.get("class")
        if name == "defer-gaps":
            raise ck.Malformed("defer-gaps is not available in a minor run: a gap is fixed or migrated")
        if name == "gap-migration":
            ids = entry.get("bound")
            if not isinstance(ids, list) or not all(isinstance(i, str) and GAP_ID_RE.match(i) for i in ids):
                raise ck.Malformed("gap-migration bound must list gap ids such as v0.5#WN-3")
    overrides = spec.get("members") or {}
    if not isinstance(overrides, dict):
        raise ck.Malformed("members must map a version to its overrides")
    for version, entry in overrides.items():
        if not isinstance(entry, dict):
            raise ck.Malformed(f"members.{version} must be an object")
        for key in ("source_branch", "target_branch", "tag"):
            if key in entry and not BRANCH_RE.match(str(entry[key])):
                raise ck.Malformed(f"members.{version}.{key} is not a valid ref name")
    target = spec.get("target_branch") or "develop"
    if not BRANCH_RE.match(str(target)):
        raise ck.Malformed("target_branch is not a valid ref name")
    return spec


# Run-wide classes: copying `spend` into each member would multiply its cap by the
# member count, and the unattended bypass is one decision for the whole run.
RUN_WIDE_CLASSES = {"spend", "unattended-with-bypass"}


def _split_classes(ck: ModuleType, spec: dict) -> tuple[list[dict], list[dict]]:
    minor_level = {"cleanup-merged", *ck.MINOR_ONLY_CLASSES, *RUN_WIDE_CLASSES}
    plan_classes = [c for c in spec["classes"] if c.get("class") not in minor_level]
    minor_classes = [c for c in spec["classes"] if c.get("class") in minor_level]
    return plan_classes, minor_classes


def member_entry(ck: ModuleType, spec: dict, plan: Plan) -> dict:
    over = (spec.get("members") or {}).get(plan.version) or {}
    plan_classes, _ = _split_classes(ck, spec)
    classes = [
        # A per-plan `release` approval is bound to that member's own version.
        {**c, "bound": plan.version} if c.get("class") == "release" else dict(c)
        for c in plan_classes
    ]
    return {
        "version": plan.version,
        "plan_path": plan.rel,
        "plan_sha256": ck.plan_hash_text(plan.text),
        "source_branch": over.get("source_branch") or f"feat/{plan.version}-{plan.slug}",
        "target_branch": over.get("target_branch") or spec.get("target_branch") or "develop",
        "release_version": plan.version,
        "tag": over.get("tag") or plan.version,
        "approvals": {
            "classes": classes,
            "cleanup": over.get("cleanup") or {"branches": [], "worktrees": []},
        },
    }


def create_page(ck: ModuleType, rctx: RepoContext, token: str, spec: dict, membership: Membership, repo: str) -> dict:
    """The canonical data the minor approval page shows; the code is derived from it."""
    members = [member_entry(ck, spec, plan) for plan in membership.members]
    _, minor_classes = _split_classes(ck, spec)
    names = {c.get("class") for c in minor_classes}
    migratable = next((c.get("bound") for c in minor_classes if c.get("class") == "gap-migration"), []) or []
    return {
        "action": "create",
        "scope": {"kind": "minor", "minor": token},
        "members": [
            {k: m[k] for k in ("version", "plan_path", "plan_sha256", "source_branch", "target_branch", "tag")}
            for m in members
        ],
        "excluded": [{"version": p.version, "plan": p.rel, "reason": r} for p, r in membership.excluded],
        "repo": repo,
        "head": rctx._git_out("rev-parse", "HEAD"),
        "branches": {"target": spec.get("target_branch") or "develop"},
        "releases": [{"version": m["release_version"], "tag": m["tag"]} for m in members],
        "cleanup": {
            # Phase 3 fills today's estimate from the cleanup executor's dry run.
            "rule": "merged-and-idle" if "cleanup-merged" in names else "run-owned",
            "estimate": {m["version"]: m["approvals"]["cleanup"] for m in members},
        },
        "migratable_gaps": sorted(migratable),
        "spend_caps": spec.get("spend_caps") or {},
        "classes": [{"class": c.get("class"), "bound": c.get("bound")} for c in spec["classes"]],
    }


def action_page(token: str, action: str, record_nonce: str) -> dict:
    return {"action": action, "scope": {"kind": "minor", "minor": token}, "record_nonce": record_nonce}


# --------------------------------------------------------------------------- record


def record_file(ck: ModuleType, rctx: RepoContext, token: str) -> Path:
    """The minor record's path: its key, else a record for this root and minor elsewhere.

    The key names the resolved owner/repo, which a remote change moves; the content
    lookup keeps the record visible so the change is reported, not hidden.
    """
    path = rctx.scoped_record_path("minor:" + token)
    if path.is_file():
        return path
    found = ck.find_record_by_content(
        rctx.root, lambda r: r.get("schema") == ck.SCHEMA_MINOR and r.get("minor") == token
    )
    return found or path


def minor_record_path(ck: ModuleType, args: argparse.Namespace) -> Path:
    parse_minor(ck, args.minor)
    return record_file(ck, repo_context(ck, args), args.minor)


def load_minor(ck: ModuleType, rctx: RepoContext, token: str, session: str | None) -> MinorState:
    """Load and verify the schema-2 record for `token`.

    Integrity (any failure is `record-tampered`): outside every working tree,
    `schema` 2 with `scope` "minor" and this `minor`, a verifying HMAC, and every
    member, found BY VERSION across the canonical, legacy, and archive layouts,
    hashing to its frozen `plan_sha256`. Then validity: older than 14 days, or
    marked complete, is ignored; bound to another session is ignored until a
    resume paste adopts it; a pause is PAUSED; an open blocker is BLOCKED; and a
    member now owned by another run is `BLOCKED: owned-by-another-run (vX.Y.Z)`.
    """
    state = MinorState()
    path = record_file(ck, rctx, token)
    if not path.is_file():
        return state
    record = ck.read_record(rctx, path)
    if record is None or not _verified(ck, rctx, token, record):
        state.forced = ck.TAMPERED
        return state
    created = ck._parse_time(record.get("created"))
    if created is None or created.tzinfo is None or (
        dt.datetime.now(dt.timezone.utc) - created
    ).total_seconds() > MINOR_VALID_SECONDS:
        state.notices.append("minor run record older than 14 days ignored")
        return state
    if record.get("completed"):
        state.notices.append("minor run record already complete ignored")
        return state
    if session and record.get("session_id") != session:
        state.notices.append("minor run record bound to another session; paste its resume line here")
        state.other_session = record
        return state
    state.record = record
    if record.get("pause"):
        state.forced = ("PAUSED", ck.EXIT_PAUSED)
        return state
    open_blockers = [b for b in record.get("blockers", []) if isinstance(b, dict) and b.get("open")]
    if open_blockers:
        state.forced = (f"BLOCKED: {open_blockers[0].get('category')}", ck.EXIT_BLOCKED)
        return state
    owned = _owned_member(ck, rctx, record, path)
    if owned:
        state.forced = (f"BLOCKED: {owned[0]} ({owned[1]})", ck.EXIT_BLOCKED)
    return state


def _verified(ck: ModuleType, rctx: RepoContext, token: str, record: dict) -> bool:
    key = ck._secret(create=False)
    members = record.get("members")
    if (
        key is None
        or record.get("schema") != ck.SCHEMA_MINOR
        or record.get("scope") != "minor"
        or record.get("minor") != token
        or not isinstance(members, list)
        or not members
        or not all(isinstance(m, dict) for m in members)
        or not hmac.compare_digest(str(record.get("approvals_hmac", "")), ck._sign(record, key))
    ):
        return False
    major, minor = parse_minor(ck, token)
    try:
        by_version = {p.version: p for p in scan_plans(rctx.root, major, minor)}
    except MinorMalformed:
        return False
    for member in members:
        plan = by_version.get(str(member.get("version")))
        # Schema 2 is new in v4.13.6, so only the current hash rule applies.
        if plan is None or member.get("plan_sha256") != ck.plan_hash_text(plan.text):
            return False
    return True


def _owned_member(ck: ModuleType, rctx: RepoContext, record: dict, own: Path) -> tuple[str, str] | None:
    """(blocker category, version) for the first member another run owns or that cannot be decided."""
    ours = {str(m.get("source_branch")) for m in record["members"]}
    heads = _feat_heads(ck, rctx)
    integration = _integration_ref(rctx, str((record.get("approvals") or {}).get("target_branch") or "develop"))
    major, minor = parse_minor(ck, str(record.get("minor")))
    try:
        by_version = {p.version: p for p in scan_plans(rctx.root, major, minor)}
    except MinorMalformed:
        # cannot tell: stop, never guess
        return "platform-unavailable", str(record["members"][0].get("version"))
    for member in record["members"]:
        plan = by_version.get(str(member.get("version")))
        reason = None if plan is None else ownership(ck, rctx, plan, heads, integration, ours, own)
        if reason == "owned-by-another-run":
            return reason, plan.version
        if reason == "cannot-verify-owned":
            return "platform-unavailable", plan.version
    return None


def _membership_or_exit(ck: ModuleType, rctx: RepoContext, token: str, spec: dict) -> tuple[Membership, str] | int:
    """Members for a page, or the exit code of the refusal that stops the round."""
    own = record_file(ck, rctx, token)
    if ck.lock_live(own):
        return ck._blocked(f"owned-by-another-run ({token})")
    live = load_minor(ck, rctx, token, None)
    if live.record is not None:
        print(f"BLOCKED: approval-not-covered (minor record {token} is live; resume or complete it)")
        return ck.EXIT_BLOCKED
    repo = str(spec.get("repo") or hosting_repo(ck, rctx))
    try:
        membership = resolve_members(
            ck,
            rctx,
            token,
            integration_branch=str(spec.get("target_branch") or "develop"),
            frozen_repo=repo or None,
            own=own,
        )
    except MinorMalformed as exc:
        print(f"MALFORMED: {exc}")
        return EXIT_MINOR_MALFORMED
    undecidable = membership.undecidable()
    if undecidable:
        return ck._blocked(f"platform-unavailable ({undecidable[0].version})")
    if not membership.members:
        print(f"No queued plans in {token}")
        return EXIT_EMPTY
    for plan in membership.members:
        existing = [p for p in plan_records(ck, rctx, plan.rel) if p.is_file()]
        if existing:
            # Two authorities never merge: the per-plan record is retired first.
            print(f"BLOCKED: approval-not-covered (per-plan record exists for {plan.version})")
            print(f"retire it with: check_plan_completion.py record retire {plan.rel}")
            return ck.EXIT_BLOCKED
    return membership, repo


def cmd_members(ck: ModuleType, args: argparse.Namespace) -> int:
    rctx = repo_context(ck, args)
    token = args.minor
    parse_minor(ck, token)
    own = load_minor(ck, rctx, token, None)
    ours = {str(m.get("source_branch")) for m in (own.record or {}).get("members", [])}
    # Only a verified record of this minor is "ours"; any other one still owns its versions.
    own_path = record_file(ck, rctx, token) if own.record is not None else None
    try:
        membership = resolve_members(
            ck,
            rctx,
            token,
            integration_branch=args.integration_branch,
            frozen_repo=(own.record or {}).get("repo"),
            ours=ours,
            own=own_path,
        )
    except MinorMalformed as exc:
        print(f"MALFORMED: {exc}")
        return EXIT_MINOR_MALFORMED
    for plan, reason in membership.excluded:
        print(f"{plan.version} {reason}", file=sys.stderr)
    if not membership.members:
        print(f"No queued plans in {token}")
        return EXIT_EMPTY
    for plan in membership.members:
        print(plan.rel)
    return 0


def covering_minor(ck: ModuleType, rctx: RepoContext, version: str) -> str | None:
    """The minor token whose valid, uncompleted record lists `version`, else None.

    A paused or blocked record still covers its members: it is the one authority
    until it completes, expires, or fails its integrity check.
    """
    match = re.match(r"^v?(\d+)\.(\d+)\.\d+$", version)
    if not match:
        return None
    token = f"v{int(match.group(1))}.{int(match.group(2))}"
    state = load_minor(ck, rctx, token, None)
    members = (state.record or {}).get("members") or []
    return token if any(m.get("version") == version for m in members) else None


def _round_key(rctx: RepoContext, token: str) -> str:
    return rctx.scoped_record_path("minor:" + token).stem


def cmd_record_render(ck: ModuleType, args: argparse.Namespace) -> int:
    rctx = repo_context(ck, args)
    token = args.minor
    parse_minor(ck, token)
    if args.action == "create":
        if not args.approvals:
            raise ck.Malformed("record render --action create needs --approvals")
        spec = minor_spec(ck, args.approvals)
        found = _membership_or_exit(ck, rctx, token, spec)
        if isinstance(found, int):
            return found
        page = create_page(ck, rctx, token, spec, *found)
    elif args.action in ("pause", "resume"):
        record = _record_for_action(ck, rctx, token, args.action, args.session)
        if isinstance(record, int):
            return record
        page = action_page(token, args.action, str(record.get("nonce", "")))
    else:
        raise ck.Malformed("a minor run answers blockers through its member plans")
    session = None if args.session == "auto" else args.session
    try:
        pending = approval_binding.render(
            ck._runs_dir(),
            _round_key(rctx, token),
            ck._secret(create=True) or b"",
            action=args.action,
            scope=token,
            page=page,
            session=session,
        )
    except approval_binding.Refusal as refusal:
        return ck._refused(refusal.reason)
    if args.json:
        print(json.dumps({"paste": pending["paste_lines"], "page": pending["page"],
                          "expires_at": pending["expires_at"]}, sort_keys=True))
    else:
        for line in pending["paste_lines"]:
            print(line)
    return 0


def _consume(ck: ModuleType, rctx: RepoContext, token: str, action: str, page: dict, session: str,
             required_session: str | None = None) -> tuple[dict, str] | int:
    try:
        return approval_binding.consume(
            ck._runs_dir(),
            _round_key(rctx, token),
            ck._secret(create=False),
            action=action,
            live_page=page,
            session=session,
            required_session=required_session,
        )
    except approval_binding.Refusal as refusal:
        return ck._refused(refusal.reason)


def cmd_record_create(ck: ModuleType, args: argparse.Namespace) -> int:
    rctx = repo_context(ck, args)
    token = args.minor
    parse_minor(ck, token)
    spec = minor_spec(ck, args.approvals)
    found = _membership_or_exit(ck, rctx, token, spec)
    if isinstance(found, int):
        return found
    membership, repo = found
    page = create_page(ck, rctx, token, spec, membership, repo)
    consumed = _consume(ck, rctx, token, "create", page, args.session)
    if isinstance(consumed, int):
        return consumed
    pending, session = consumed
    pushed = rctx.url_repo(rctx.push_remote_url)
    if not pushed or pushed.lower() != str(page["repo"]).lower():
        return ck._refused("push-remote-outside-approval")
    paste = " / ".join(pending["paste_lines"])
    members = [member_entry(ck, spec, plan) for plan in membership.members]
    for member in members:
        member["approvals"]["classes"] = [{**c, "text": paste} for c in member["approvals"]["classes"]]
    _, minor_classes = _split_classes(ck, spec)
    record = {
        "schema": ck.SCHEMA_MINOR,
        "scope": "minor",
        "minor": token,
        "repo_root": str(rctx.root),
        "remote_url": rctx.remote_url,
        "repo": page["repo"],
        "session_id": session,
        "worktree": str(rctx.root),
        "start_head": page["head"],
        "nonce": pending["nonce"],
        "created": ck._now(),
        "members": members,
        "excluded": page["excluded"],
        "approvals": {
            "remote_url": rctx.remote_url,
            "push_remote_url": rctx.push_remote_url,
            "repo": page["repo"],
            "target_branch": page["branches"]["target"],
            "classes": [{**c, "text": paste} for c in minor_classes],
            "spend_caps": page["spend_caps"],
            "page_sha256": hashlib.sha256(approval_binding.canonical(page)).hexdigest(),
        },
        "blockers": [],
        "pause": None,
        "completed": None,
    }
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=True) or b"")
    ck._write_record(rctx.scoped_record_path("minor:" + token), record)
    print(f"RECORDED minor {token} nonce={record['nonce']}")
    return 0


def _record_for_action(ck: ModuleType, rctx: RepoContext, token: str, action: str, session: str) -> dict | int:
    """The verified record a pause or resume applies to.

    A resume may adopt a record bound to another session (the cross-session
    resume); a pause applies only in the record's own session.
    """
    state = load_minor(ck, rctx, token, None if session == "auto" else session)
    record = state.record or (state.other_session if action == "resume" else None)
    if record is not None:
        return record
    if state.forced and state.forced[1] == ck.EXIT_BLOCKED:
        return ck._blocked(state.forced[0].removeprefix("BLOCKED: "))
    for notice in state.notices:
        print(f"notice: {notice}", file=sys.stderr)
    print("no minor run record for this scope and session", file=sys.stderr)
    return ck.EXIT_MALFORMED


def cmd_record_action(ck: ModuleType, args: argparse.Namespace, action: str) -> int:
    rctx = repo_context(ck, args)
    token = args.minor
    parse_minor(ck, token)
    record = _record_for_action(ck, rctx, token, action, args.session)
    if isinstance(record, int):
        return record
    page = action_page(token, action, str(record.get("nonce", "")))
    # A pause lands in the record's own session; a resume is the one-line paste
    # that carries the record into the session where it was captured.
    required = str(record.get("session_id") or "") if action == "pause" else None
    consumed = _consume(ck, rctx, token, action, page, args.session, required)
    if isinstance(consumed, int):
        return consumed
    pending, session = consumed
    if args.text is not None and approval_binding.normalize(args.text) not in {
        approval_binding.normalize(x) for x in pending["paste_lines"]
    }:
        return ck._refused("approval-not-captured")
    if action == "pause":
        record["pause"] = {"at": ck._now(), "text_sha256": pending["paste_digests"][0]}
        ck._write_record(record_file(ck, rctx, token), record)
        print(f"PAUSED minor {token}")
        return 0
    record["pause"] = None
    record["session_id"] = session  # signed, so the record is re-signed below
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    ck._write_record(record_file(ck, rctx, token), record)
    print(f"RESUMED minor {token} session bound")
    return 0
