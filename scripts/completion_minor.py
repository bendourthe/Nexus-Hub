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
GAP_ID_RE = re.compile(r"^v\d+\.\d+(?:\.\d+)?#[A-Z]{2,4}-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
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


def scan_plans(root: Path, major: int, minor: int, *, strict: bool = True) -> list[Plan]:
    """Every plan of the minor across all layouts, deduplicated by path.

    Raises MinorMalformed for an unreadable plan or, when `strict`, two plans with
    one version. The gap scope reads historical minors plan by plan, where a
    duplicate version does not change which plans a live run owns (`strict=False`).
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
        if plan.version in versions and strict:
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
            # A security or high-severity gap migrates only when it is also named here,
            # so the page shows it on its own line rather than inside the frozen list.
            named = entry.get("named", [])
            if not isinstance(named, list) or not set(named) <= set(ids):
                raise ck.Malformed("gap-migration named must list ids that are also in bound")
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
            # Today's estimate from `cleanup_merged.py --dry-run` is shown beside the page, never
            # hashed into it: the approval covers the rule, not a frozen list, and a hashed live
            # estimate would refuse the paste whenever one item changed state (Phase 6 renders it).
            "rule": "merged-and-idle" if "cleanup-merged" in names else "run-owned",
            "estimate": {m["version"]: m["approvals"]["cleanup"] for m in members},
        },
        "migratable_gaps": sorted(migratable),
        "spend_caps": spec.get("spend_caps") or {},
        "classes": [
            {"class": c.get("class"), "bound": c.get("bound"), **({"named": c["named"]} if "named" in c else {})}
            for c in spec["classes"]
        ],
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


# --------------------------------------------------------------------------- known-gaps ledgers
#
# The rules below (which items are open, which migrations count, which files are in
# scope) are owned by the completion contract, "Minor gaps and archive". The
# executor that writes migrations and archives a minor is the sibling minor_close.py.

# Every layout a known-gaps ledger can live in, active first.
LEDGER_LAYOUTS = (
    ("docs/releases/v{M}/v{M}.{m}/known-gaps.md", "active"),
    ("docs/v{M}/v{M}.{m}/known-gaps.md", "active"),
    ("docs/versions/v{M}/v{M}.{m}/known-gaps.md", "active"),
    ("docs/v{M}.{m}/known-gaps.md", "active"),
    ("docs/archives/v{M}/v{M}.{m}/known-gaps.md", "archive"),
    ("docs/archive/v{M}/v{M}.{m}/known-gaps.md", "archive"),
    ("docs/archive/versions/v{M}/v{M}.{m}/known-gaps.md", "archive"),
)
LEDGER_GLOBS = (
    "docs/releases/v*/v*/known-gaps.md",
    "docs/v*/v*/known-gaps.md",
    "docs/versions/v*/v*/known-gaps.md",
    "docs/v*/known-gaps.md",
    "docs/archives/v*/v*/known-gaps.md",
    "docs/archive/v*/v*/known-gaps.md",
    "docs/archive/versions/v*/v*/known-gaps.md",
)
# The active trees a minor archive moves from (canonical first) and the one it moves to.
ACTIVE_TREES = ("docs/releases/v{M}/v{M}.{m}", "docs/v{M}/v{M}.{m}", "docs/versions/v{M}/v{M}.{m}", "docs/v{M}.{m}")
ARCHIVE_TREE = "docs/archives/v{M}/v{M}.{m}"

_MINOR_DIR_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)$")
# An ATX heading per CommonMark: up to three spaces, 1-6 `#`, and an optional closing run.
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_FENCE_CLOSE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})[ \t]*$")
GAP_ID = r"[A-Z]{2,4}-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*"
# An item heading: `#### WN-3: title`, `##### WN-3 - title`, `### WN-D ...`, `#### DF-v24 ...`.
LEDGER_ITEM_RE = re.compile(r"^(?P<id>(?P<kind>[A-Z]{2,4})-(?P<num>[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*))(?![A-Za-z0-9-])(?P<title>.*)$")
# Text that starts like an item id; a heading or row like this that does not parse as an
# item makes the ledger unreadable for the verdict rather than silently skipped.
_ITEM_LIKE_RE = re.compile(r"^\*{0,2}\[?[A-Z]{2,4}-[A-Za-z0-9]")
_ROW_RE = re.compile(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+|\|\s*)(?P<rest>.*)$")
MIGRATED_RE = re.compile(r"\s-{1,2}\s*MIGRATED to (?P<target>v\d+\.\d+\.\d+)\s*$")
# The tracker's RESOLVED marker and the CLOSED marker archive reconciliation writes,
# either as the heading's status prefix (`NI-1 - CLOSED: ...`) or at its end, optionally
# followed by a date or a short parenthetical (`... - RESOLVED 2026-09-22`).
_RESOLVED_END_RE = re.compile(
    r"\s-{1,2}\s*(?:RESOLVED|CLOSED)(?:\s+\d{4}-\d{2}-\d{2})?(?:\s*\([^()]*\))?\s*$"
)
_RESOLVED_PREFIX_RE = re.compile(r"^\s*(?::\s*)?-{1,2}\s*(?:RESOLVED|CLOSED)\b")
MIGRATED_FROM_RE = re.compile(
    r"\*\*Migrated from\*\*:\s*(?P<minor>v\d+\.\d+)(?:\.\d+)?#(?P<id>" + GAP_ID + r")(?![A-Za-z0-9-])(?P<rest>[^\n]*)"
)
MIGRATION_REASON_RE = re.compile(r"\(reason:\s*(?P<reason>[a-z-]+)")
MIGRATION_REASONS = ("vendor-feature", "user-credential", "user-deferred")
_OPEN_ITEMS_LINE_RE = re.compile(r"^\*\*Open items\*\*\s*:\s*(\d+)\s*$", re.MULTILINE | re.IGNORECASE)
_SEVERITY_RE = re.compile(r"\*\*Severity\*\*:\s*`?(high|critical)\b", re.IGNORECASE)
_SECURITY_FIELD_RE = re.compile(r"\*\*Security\*\*:\s*(?!no\b|none\b|n/a\b)\S", re.IGNORECASE)
_SECURITY_WORD_RE = re.compile(r"\bsecurity\b", re.IGNORECASE)


def fence_mask(lines: list[str]) -> tuple[list[bool], bool]:
    """(inside a fenced code block, per line; a fence is still open at the end).

    CommonMark fences: an opener is up to three spaces then at least three backticks or
    tildes, and a backtick opener's info string may not contain a backtick; the closer
    uses the same character, is at least as long as the opener, and carries nothing
    but trailing whitespace. The opener and closer lines count as inside. This is the
    one implementation the ledger parser and the archive's reference repair share.
    """
    mask = [False] * len(lines)
    fence: tuple[str, int] | None = None
    for index, raw in enumerate(lines):
        line = raw.rstrip("\r\n").lstrip("\ufeff") if index == 0 else raw.rstrip("\r\n")
        if fence is None:
            opener = _FENCE_OPEN_RE.match(line)
            if opener and not (opener.group(1)[0] == "`" and "`" in opener.group(2)):
                fence = (opener.group(1)[0], len(opener.group(1)))
                mask[index] = True
            continue
        mask[index] = True
        closer = _FENCE_CLOSE_RE.match(line)
        if closer and closer.group(1)[0] == fence[0] and len(closer.group(1)) >= fence[1]:
            fence = None
    return mask, fence is not None


def resolved_title(title: str) -> bool:
    return bool(_RESOLVED_END_RE.search(title) or _RESOLVED_PREFIX_RE.match(title))


@dataclass
class GapItem:
    gid: str  # "WN-3"
    kind: str  # "WN"
    title: str  # the heading text after the id
    state: str  # "open", "resolved", or "migrated"
    target: str | None  # "v0.6.0" for a migrated item
    section: str  # the enclosing `## ` heading text
    subsection: str  # the enclosing non-item `### ` heading text
    level: int  # 3 to 6
    start: int  # offset of the heading line
    heading_end: int  # offset just past the heading text (before any closing `#` run)
    end: int  # offset just past the item's block
    body: str  # the block after the heading line

    def provenance(self) -> list[tuple[str, str, str | None]]:
        """Every `**Migrated from**: <minor>#<id>` line as (minor, id, reason)."""
        found: list[tuple[str, str, str | None]] = []
        for match in MIGRATED_FROM_RE.finditer(self.body):
            reason = MIGRATION_REASON_RE.search(match.group("rest"))
            found.append((match.group("minor"), match.group("id"), reason.group("reason") if reason else None))
        return found

    def sensitive(self) -> bool:
        """Security or high-severity: migrates only when the approval names it individually.

        Leans to True: a heading or enclosing subsection naming security, a
        `**Security**` field, or a `**Severity**` of high or critical.
        """
        return bool(
            _SEVERITY_RE.search(self.body)
            or _SECURITY_FIELD_RE.search(self.body)
            or _SECURITY_WORD_RE.search(self.title)
            or _SECURITY_WORD_RE.search(self.subsection)
        )


@dataclass
class Ledger:
    path: Path
    rel: str
    minor: tuple[int, int]
    layout: str  # "active" or "archive"
    text: str
    items: list[GapItem]
    problems: list[str] = field(default_factory=list)  # why the ledger cannot be read reliably

    def token(self) -> str:
        return "v{}.{}".format(*self.minor)


def _header(text: str, lines: list[str], mask: list[bool]) -> str:
    """The file header: everything before the first level-1 or level-2 heading outside code."""
    pos = 0
    for index, line in enumerate(lines):
        match = None if mask[index] else _HEADING_RE.match(line.rstrip("\r\n"))
        if match and len(match.group(1)) == 2:
            return text[:pos]
        pos += len(line)
    return text


def ledger_header(text: str) -> str:
    lines = text.splitlines(keepends=True)
    return _header(text, lines, fence_mask(lines)[0])


def parse_ledger_full(text: str) -> tuple[list[GapItem], list[str]]:
    """(items, problems) of a known-gaps file.

    An item is a level-3 to level-6 heading whose text starts with an id such as
    `WN-3`, `WN-D`, or `DF-v24`. It is resolved by a RESOLVED or CLOSED marker as its
    status prefix or at the heading's end, or by sitting under a `### Resolved...`
    subsection; migrated when its heading ends with ` - MIGRATED to vX.Y.Z`; open
    otherwise, wherever it sits. Headings inside fenced code are ignored.

    A problem makes the whole ledger `cannot-verify` for the minor verdict: a fence
    left open at the end, a heading or a list or table row outside any item that
    starts like an item id but is not an item, or a header `**Open items**: N` that
    disagrees with the number of open items parsed.
    """
    lines = text.splitlines(keepends=True)
    offsets: list[int] = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line)
    mask, unclosed = fence_mask(lines)
    problems = ["unclosed-fence"] if unclosed else []
    headings: list[tuple[int, int, str, int]] = []  # (line, level, text, text end within line)
    for index, raw in enumerate(lines):
        if mask[index]:
            continue
        lead = 1 if index == 0 and raw.startswith("\ufeff") else 0
        match = _HEADING_RE.match(raw[lead:].rstrip("\r\n"))
        if match:
            headings.append((index, len(match.group(1)), match.group(2) or "", lead + match.end(2) if match.group(2) else lead))
    items: list[GapItem] = []
    item_lines: set[int] = set()
    section = subsection = ""
    for h, (index, level, heading, text_end) in enumerate(headings):
        found = LEDGER_ITEM_RE.match(heading) if level >= 3 else None
        if found is None:
            if _ITEM_LIKE_RE.match(heading):
                problems.append(f"line {index + 1} heading")
            if level <= 2:
                section, subsection = heading, ""
            elif level == 3:
                subsection = heading
            continue
        end_line = len(lines)
        for later_index, later_level, later_text, _ in headings[h + 1:]:
            if later_level <= level or (later_level >= 3 and LEDGER_ITEM_RE.match(later_text)):
                end_line = later_index
                break
        item_lines.update(range(index, end_line))
        start = offsets[index]
        body_start = offsets[index + 1] if index + 1 < len(lines) else len(text)
        end = offsets[end_line] if end_line < len(lines) else len(text)
        title = found.group("title")
        migrated = MIGRATED_RE.search(title)
        if resolved_title(title) or (not migrated and subsection.lower().startswith("resolved")):
            state = "resolved"
        elif migrated:
            state = "migrated"
        else:
            state = "open"
        items.append(GapItem(
            gid=found.group("id"), kind=found.group("kind"), title=title, state=state,
            target=migrated.group("target") if migrated else None, section=section,
            subsection=subsection, level=level, start=start, heading_end=start + text_end,
            end=end, body=text[body_start:end],
        ))
    section = subsection = ""
    for index, raw in enumerate(lines):
        if mask[index] or index in item_lines:
            continue
        heading = _HEADING_RE.match(raw.rstrip("\r\n"))
        if heading:
            if len(heading.group(1)) <= 3:
                subsection = (heading.group(2) or "") if len(heading.group(1)) == 3 else ""
            continue
        row = _ROW_RE.match(raw.rstrip("\r\n"))
        if row and _ITEM_LIKE_RE.match(row.group("rest")) and not subsection.lower().startswith("resolved"):
            problems.append(f"line {index + 1} row")
    header = _header(text, lines, mask)
    stated = _OPEN_ITEMS_LINE_RE.search(header)
    if stated and int(stated.group(1)) != sum(1 for i in items if i.state == "open"):
        problems.append("open-items-count")
    return items, problems


def parse_ledger(text: str) -> list[GapItem]:
    return parse_ledger_full(text)[0]


def ledger_rels(major: int, minor: int) -> list[str]:
    """Every path a ledger for this minor could have, active layouts first."""
    return [pattern.format(M=major, m=minor) for pattern, _ in LEDGER_LAYOUTS]


def _layout_of(rel: str, major: int, minor: int) -> str | None:
    for pattern, layout in LEDGER_LAYOUTS:
        if pattern.format(M=major, m=minor) == rel:
            return layout
    return None


def load_ledgers(root: Path) -> tuple[list[Ledger], list[str]]:
    """Every known-gaps ledger at a layout path, and the paths that could not be read."""
    seen: dict[str, Path] = {}
    for pattern in LEDGER_GLOBS:
        for path in sorted(root.glob(pattern)):
            seen.setdefault(path.resolve().as_posix(), path)
    ledgers: list[Ledger] = []
    unreadable: list[str] = []
    for path in seen.values():
        rel = path.resolve().relative_to(root).as_posix()
        match = _MINOR_DIR_RE.match(rel.split("/")[-2]) if "/" in rel else None
        if not match:
            continue
        minor = (int(match.group(1)), int(match.group(2)))
        layout = _layout_of(rel, *minor)
        if layout is None:
            continue  # the glob is wider than the layouts
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError):
            unreadable.append(rel)
            continue
        items, problems = parse_ledger_full(text)
        ledgers.append(Ledger(path, rel, minor, layout, text, items, problems))
    return sorted(ledgers, key=lambda l: (l.minor, l.layout != "active", l.rel)), unreadable


def normalize_gap_id(value: str) -> str | None:
    """`v0.5.2#WN-3` and `v0.5#WN-3` both name `v0.5#WN-3`: ids are unique per minor file."""
    match = re.match(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)(?:\.\d+)?#(" + GAP_ID + r")$", value or "")
    return f"v{match.group(1)}.{match.group(2)}#{match.group(3)}" if match else None


def migration_class(record: dict | None) -> tuple[set[str], set[str]]:
    """(frozen migratable ids, individually named ids) from the `gap-migration` class.

    Works on a schema-2 record and on its per-member projection alike.
    """
    classes = ((record or {}).get("approvals") or {}).get("classes") or []
    entry = next((c for c in classes if isinstance(c, dict) and c.get("class") == "gap-migration"), None)
    if entry is None:
        return set(), set()
    bound = {normalize_gap_id(str(i)) for i in entry.get("bound") or []} - {None}
    named = {normalize_gap_id(str(i)) for i in entry.get("named") or []} - {None}
    return bound, named & bound


def minor_of(version: str) -> tuple[int, int]:
    parts = version.lstrip("v").split(".")
    return int(parts[0]), int(parts[1])


def next_minor(token: str) -> str:
    major, minor = minor_of(token)
    return f"v{major}.{minor + 1}"


def find_migrated_copy(
    ledgers: list[Ledger], target: str, source: str, gid: str,
) -> tuple[Ledger, GapItem] | None:
    """The entry in the target minor's ledger whose provenance names `source#gid`."""
    tmin = minor_of(target)
    for ledger in ledgers:
        if ledger.minor != tmin:
            continue
        for item in ledger.items:
            if any(m == source and i == gid for m, i, _ in item.provenance()):
                return ledger, item
    return None


def existed_at(rctx: RepoContext, commit: str, minor: tuple[int, int], gid: str) -> str:
    """`met` when the minor's ledger at `commit` already held item `gid`, else `unmet`.

    Every layout path is tried, so a ledger archived since `commit` still resolves.
    `cannot-verify` when git cannot answer.
    """
    for rel in ledger_rels(*minor):
        rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "cat-file", "-e", f"{commit}:{rel}"])
        if rc == -1:
            return "cannot-verify"
        if rc != 0:
            continue
        rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "show", f"{commit}:{rel}"])
        if rc != 0:
            return "cannot-verify"
        if any(item.gid == gid for item in parse_ledger(out)):
            return "met"
    return "unmet"


def verify_migration(
    rctx: RepoContext, record: dict | None, run_token: str,
    ledgers: list[Ledger], ledger: Ledger, item: GapItem,
) -> tuple[str, str]:
    """(status, reason id) for one `- MIGRATED to vX.Y.Z` item in the gap scope.

    A migration only moves forward: its target is a later minor's `.0`, so a marker
    naming its own minor or an earlier one (a self-marker, or a cycle between two
    minors) never verifies. The copy must exist in the target ledger with matching
    provenance. A copy in a minor at or below the run's minor is itself in the gap
    scope and is judged on its own (open, resolved, or migrated forward again), which
    covers a gap an earlier run migrated into this one. A target beyond the run's
    minor must be exactly the next minor, with the id in the record's frozen list
    (and individually named when security or high-severity), a reason from the
    closed set, and the item present at the minor record's `start_head`.
    """
    source = ledger.token()
    target = str(item.target)
    target_minor = minor_of(target)
    if target_minor <= ledger.minor:
        return "unmet", "migration-not-forward"
    if not target.endswith(".0"):
        return "unmet", "migration-target-not-minor-start"
    found = find_migrated_copy(ledgers, target, source, item.gid)
    if found is None:
        return "unmet", "migration-target-missing"
    if target_minor <= minor_of(run_token):
        return "met", "in-scope-copy"
    if "v{}.{}".format(*target_minor) != next_minor(run_token):
        return "unmet", "migration-target-not-next-minor"
    copy = found[1]
    bound, named = migration_class(record)
    pid = f"{source}#{item.gid}"
    if pid not in bound:
        return "unmet", "migration-not-approved"
    if item.sensitive() and pid not in named:
        return "unmet", "security-not-named"
    reasons = [r for m, i, r in copy.provenance() if m == source and i == item.gid]
    if not reasons or reasons[-1] not in MIGRATION_REASONS:
        return "unmet", "migration-reason-invalid"
    start = str((record or {}).get("minor_start_head") or (record or {}).get("start_head") or "")
    if not start:
        return "cannot-verify", "no-start-head"
    existed = existed_at(rctx, start, ledger.minor, item.gid)
    if existed != "met":
        return existed, "created-during-run" if existed == "unmet" else "history-unreadable"
    return "met", "approved-migration"


def record_branches(record: dict | None) -> set[str]:
    return {str(m.get("source_branch")) for m in (record or {}).get("members") or [] if isinstance(m, dict)}


def current_branch(rctx: RepoContext) -> str:
    return rctx._git_out("symbolic-ref", "--quiet", "--short", "HEAD")


def _collect_branches(value: object, found: set[str]) -> None:
    if isinstance(value, dict):
        for key, inner in value.items():
            if key == "source_branch" and isinstance(inner, str):
                found.add(inner)
            else:
                _collect_branches(inner, found)
    elif isinstance(value, list):
        for inner in value:
            _collect_branches(inner, found)


def live_branches(ck: ModuleType, rctx: RepoContext, record: dict | None, repo: str) -> set[str] | None:
    """Branches that belong to live work: checked out in another worktree, named by a
    live run record other than this run's, or the head of an open pull request. None
    when any of the three cannot be read. A stale branch is none of these."""
    names: set[str] = set()
    rc, listing = rctx.run([rctx.git, "-C", str(rctx.root), "worktree", "list", "--porcelain"])
    if rc != 0:
        return None
    for block in listing.split("\n\n"):
        lines = block.splitlines()
        path = next((l[len("worktree "):] for l in lines if l.startswith("worktree ")), None)
        branch = next((l[len("branch refs/heads/"):] for l in lines if l.startswith("branch refs/heads/")), None)
        if path and branch and Path(path).resolve() != rctx.root:
            names.add(branch)
    own_nonce = (record or {}).get("nonce")
    for path in ck.find_records_by_content(rctx.root, lambda r: True):
        other = ck.read_record(rctx, path)
        if other is None or (own_nonce and other.get("nonce") == own_nonce):
            continue
        live = ck.record_live(rctx, path)[0] if other.get("schema") == ck.SCHEMA else _minor_record_live(ck, other)
        if live:
            _collect_branches(other, names)
    if not rctx.gh or not repo:
        return None
    rc, out = rctx.run([rctx.gh, "pr", "list", "--repo", repo, "--state", "open",
                        "--limit", "1000", "--json", "headRefName"])
    try:
        pulls = json.loads(out) if rc == 0 else None
    except ValueError:
        pulls = None
    if not isinstance(pulls, list) or len(pulls) >= 1000:
        return None
    names.update(str(p.get("headRefName")) for p in pulls if isinstance(p, dict) and p.get("headRefName"))
    return names


def unmerged_changes(rctx: RepoContext, integration: str, exempt: set[str]) -> dict[str, set[str]] | None:
    """{branch: paths it changes} for every branch (local, remote-tracking, or live on
    origin) whose tip is not merged into the integration ref, except the exempt ones.
    None when git cannot tell, including a live remote tip whose history is not local."""
    rc, out = rctx.run(
        [rctx.git, "-C", str(rctx.root), "for-each-ref", "--format=%(objectname) %(refname)",
         "refs/heads/", "refs/remotes/origin/"]
    )
    if rc != 0:
        return None
    tips: list[tuple[str, str]] = []
    for line in out.splitlines():
        sha, _, ref = line.partition(" ")
        tips.append((ref.removeprefix("refs/heads/").removeprefix("refs/remotes/origin/"), sha))
    rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "ls-remote", "--heads", "origin"])
    if rc != 0:
        return None
    for line in out.splitlines():
        sha, _, ref = line.partition("\t")
        if ref.startswith("refs/heads/"):
            tips.append((ref.removeprefix("refs/heads/"), sha))
    changed: dict[str, set[str]] = {}
    for name, sha in tips:
        if name in exempt or name == "HEAD" or _merged(rctx, sha, integration):
            continue
        rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "diff", "--name-only", f"{integration}...{sha}"])
        if rc != 0:
            return None
        changed.setdefault(name, set()).update(line.strip() for line in out.splitlines() if line.strip())
    return changed


def run_exempt_branches(rctx: RepoContext, token: str, record: dict | None) -> tuple[str, set[str], set[str]]:
    """(target branch, the run's own branches, branches never counted as another's)."""
    target = str(((record or {}).get("approvals") or {}).get("target_branch") or "develop")
    ours = record_branches(record) | {current_branch(rctx), f"chore/close-{token}"}
    return target, ours, ours | {target, "main", "master"}


def _owned_by_live_run(
    ck: ModuleType, rctx: RepoContext, plan: Plan, live: set[str], own: Path | None,
) -> bool:
    """A live per-plan record or runner lock, another live minor record listing the
    version, or a live `feat/<version>-*` branch."""
    for path in plan_records(ck, rctx, plan.rel):
        if ck.lock_live(path) or (path.is_file() and ck.record_live(rctx, path)[0]):
            return True
    if other_minor_owns(ck, rctx, plan.version, own):
        return True
    return any(name.startswith(f"feat/{plan.version}-") for name in live)


def excluded_ledgers(
    ck: ModuleType, rctx: RepoContext, token: str, record: dict | None, ledgers: list[Ledger],
) -> dict[str, str] | None:
    """{ledger rel: reason} for ledgers another live run is working on, or None when unknown.

    Never the run's own minor. A ledger of an earlier minor is excluded when a live
    branch (see `live_branches`) that is not merged into the integration branch
    changes it (`changed-on-live-branch`), or when a live run owns a not-done plan of
    its minor (`owned-by-another-run`). A stale unmerged branch excludes nothing.
    """
    run_minor = minor_of(token)
    others = [l for l in ledgers if l.minor != run_minor]
    if not others:
        return {}
    target, ours, exempt = run_exempt_branches(rctx, token, record)
    integration = _integration_ref(rctx, target)
    if integration is None:
        return None
    changes = unmerged_changes(rctx, integration, exempt)
    if changes is None:
        return None
    live_cache: list[set[str] | None] = []

    def live() -> set[str] | None:
        if not live_cache:
            repo = hosting_repo(ck, rctx, (record or {}).get("repo"))
            live_cache.append(live_branches(ck, rctx, record, repo))
        return live_cache[0]

    excluded: dict[str, str] = {}
    rels = {l.rel for l in others}
    for name, files in changes.items():
        if not files & rels:
            continue
        branches = live()
        if branches is None:
            return None
        if name in branches:
            for rel in files & rels:
                excluded.setdefault(rel, "changed-on-live-branch")
    own_path = record_file(ck, rctx, token) if record is not None else None
    for minor in sorted({l.minor for l in others}):
        try:
            plans = scan_plans(rctx.root, *minor, strict=False)
        except MinorMalformed:
            return None  # an unreadable plan: who owns it cannot be told
        pending = [p for p in plans if p.status not in DONE_STATUSES]
        if not pending:
            continue
        branches = live()
        if branches is None:
            return None
        if any(_owned_by_live_run(ck, rctx, plan, branches - ours, own_path) for plan in pending):
            for ledger in others:
                if ledger.minor == minor:
                    excluded.setdefault(ledger.rel, "owned-by-another-run")
    return excluded


def gaps_minor_status(
    ck: ModuleType, rctx: RepoContext, token: str, record: dict | None,
) -> tuple[str, list[str]]:
    """(`gaps.minor` status, notices of fixed ids and repository-relative paths only).

    Met when every item in every ledger for a version at or below the run's minor
    (canonical, legacy, and archive layouts) is resolved or verifiably migrated.
    Ledgers for later versions are out of scope, so a migrated copy there never
    reopens the verdict. There is no deferrable state. `cannot-verify` when a ledger is
    unreadable or has a parse problem, when the scope cannot be decided, or when a
    ledger excluded for another live run's work still holds an open item.
    """
    parse_minor(ck, token)
    run_minor = minor_of(token)
    ledgers, unreadable = load_ledgers(rctx.root)
    notices = [f"gaps.minor unreadable {rel}" for rel in unreadable]
    if unreadable:
        return "cannot-verify", notices
    scope = [l for l in ledgers if l.minor <= run_minor]
    excluded = excluded_ledgers(ck, rctx, token, record, scope)
    if excluded is None:
        return "cannot-verify", notices + ["gaps.minor scope undecidable"]
    unmet = unknown = False
    for ledger in scope:
        for problem in ledger.problems:
            notices.append(f"gaps.minor unparsed {ledger.rel} ({problem})")
            unknown = True
        if ledger.rel in excluded:
            notices.append(f"gaps.minor excluded {ledger.rel} ({excluded[ledger.rel]})")
            if any(i.state != "resolved" for i in ledger.items):
                notices.append(f"gaps.minor excluded {ledger.rel} still holds open items")
                unknown = True
            continue
        for item in ledger.items:
            if item.state == "resolved":
                continue
            if item.state == "open":
                notices.append(f"gaps.minor open {ledger.token()}#{item.gid}")
                unmet = True
                continue
            verdict, reason = verify_migration(rctx, record, token, ledgers, ledger, item)
            if verdict != "met":
                notices.append(f"gaps.minor migration {ledger.token()}#{item.gid} {reason}")
                unmet = unmet or verdict == "unmet"
                unknown = unknown or verdict != "unmet"
    return ("unmet" if unmet else "cannot-verify" if unknown else "met"), notices


def archive_minor_status(ck: ModuleType, rctx: RepoContext, token: str, record: dict | None) -> str:
    """`archive.minor`: `n/a` without an `archive-minor` approval; else met when every
    active tree of the minor is absent on the integration branch and the archive tree
    is present there (the remote-tracking ref first, then the local branch)."""
    classes = ((record or {}).get("approvals") or {}).get("classes") or []
    if not any(isinstance(c, dict) and c.get("class") == "archive-minor" for c in classes):
        return "n/a"
    major, minor = parse_minor(ck, token)
    target = str(((record or {}).get("approvals") or {}).get("target_branch") or "develop")
    ref = _integration_ref(rctx, target)
    if ref is None:
        return "cannot-verify"

    def present(path: str) -> bool | None:
        rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "ls-tree", "--name-only", ref, "--", path])
        return None if rc != 0 else bool(out.strip())

    for tree in ACTIVE_TREES:
        state = present(tree.format(M=major, m=minor))
        if state is None:
            return "cannot-verify"
        if state:
            return "unmet"
    state = present(ARCHIVE_TREE.format(M=major, m=minor))
    return "cannot-verify" if state is None else ("met" if state else "unmet")
