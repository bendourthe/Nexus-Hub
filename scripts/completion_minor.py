#!/usr/bin/env python3
"""Minor-scope membership and the schema-2 run record for `/implement vX.Y`.

Installed at ~/.nexus-hub/scripts/completion_minor.py beside
check_plan_completion.py, which dispatches here and stays a thin dispatcher:

    check_plan_completion.py members vX.Y        one member plan path per line, in
                                                 version order; excluded plans and
                                                 their reason on stderr
    check_plan_completion.py record render|create --minor vX.Y --session ID --approvals F
    check_plan_completion.py record answer --minor vX.Y --session ID --blocker N [--member vX.Y.Z]
    check_plan_completion.py record pause|resume --minor vX.Y --session ID
    check_plan_completion.py record add-class --minor vX.Y --session ID --class archive-member
                                                 (after record render --action add-class --class ...)
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
import fnmatch
import hashlib
import hmac
import json
import os
import re
import sys
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import approval_binding  # installed as a sibling in ~/.nexus-hub/scripts/
import approval_page  # installed as a sibling in ~/.nexus-hub/scripts/
from completion_budget import (
    CHECK_MINOR_TOTAL_SECONDS as CHECK_MINOR_TOTAL_SECONDS,
    check_minor_seconds as check_minor_seconds,
)

if TYPE_CHECKING:
    from check_plan_completion import RepoContext

MINOR_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\Z", re.ASCII)
PLAN_VERSION_RE = re.compile(
    r"^\*\*Version\*\*:\s*v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\b", re.MULTILINE
)
ANY_VERSION_RE = re.compile(r"^\*\*Version\*\*:\s*v?\d+\.\d+\.\d+\b", re.MULTILINE)
STATUS_RE = re.compile(r"^\*\*Status\*\*:\s*`?([A-Za-z-]+)", re.MULTILINE)
SLUG_RE = re.compile(r"^\*\*Slug\*\*:\s*([A-Za-z0-9._-]+)", re.MULTILINE)
GAP_ID_RE = re.compile(r"^v\d+\.\d+(?:\.\d+)?#[A-Z]{2,4}-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\Z", re.ASCII)
BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]+\Z", re.ASCII)
PLAN_TOKEN_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\Z", re.ASCII)

DONE_STATUSES = {"complete", "superseded", "shipped"}
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


class ObservationUnavailable(Exception):
    """A required observation did not run; no negative fact was established."""


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
    """Live until MINOR COMPLETE stamps it `completed`; there is no expiry."""
    return not record.get("completed")


def other_minor_owns(ck: ModuleType, rctx: RepoContext, version: str, own: Path | None) -> bool:
    """Another live minor record, anywhere in the runs directory, lists this version."""
    def lists(record: dict) -> bool:
        members = record.get("members") if isinstance(record.get("members"), list) else []
        return record.get("schema") == ck.SCHEMA_MINOR and any(
            isinstance(m, dict) and m.get("version") == version for m in members
        )

    for path in authority_records(ck, rctx, lists):
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
    # Definition of Done 2: a minor completes only after the final cleanup pass, the
    # merged closing pull request, and the archive, so a minor run cannot be approved
    # without the three classes that authorize them.
    present = {entry.get("class") for entry in spec["classes"]}
    missing = [name for name in REQUIRED_MINOR_CLASSES if name not in present]
    if missing:
        raise ck.Malformed(
            "a minor run needs the " + ", ".join(missing) + " approval(s): it completes only after "
            "the final cleanup, the merged closing pull request, and the archive"
        )
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


# The closing classes every minor run needs (Definition of Done 2).
REQUIRED_MINOR_CLASSES = ("cleanup-merged", "archive-minor", "minor-close-pr")


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
    try:
        ck._validate_policy_paths(rctx.root, spec.get('autonomy') or {})
    except ValueError as exc:
        raise ck.Malformed(str(exc)) from exc
    members = [member_entry(ck, spec, plan) for plan in membership.members]
    _, minor_classes = _split_classes(ck, spec)
    names = {c.get("class") for c in minor_classes}
    migratable = next((c.get("bound") for c in minor_classes if c.get("class") == "gap-migration"), []) or []
    check_migratable(ck, rctx.root, minor_classes)
    return {
        'autonomy': approval_binding.validate_policy(spec['autonomy']) if spec.get('autonomy') else None,
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


def check_migratable(ck: ModuleType, root: Path, minor_classes: list[dict]) -> None:
    """Refuse a page whose frozen `gap-migration` list the ledgers do not support.

    A listed id that a ledger holds must be one open, unambiguous gap there, and a
    listed id that is security or high-severity must also be in `named`, so the page
    shows it on its own line. An id no ledger holds yet is allowed: it can never
    migrate, because `migration_gate` requires it open at the record's start. The
    same page is rendered and consumed, so this holds for `record render` and
    `record create` alike.
    """
    entry = next((c for c in minor_classes if c.get("class") == "gap-migration"), None)
    if entry is None:
        return
    named = {normalize_gap_id(str(i)) for i in entry.get("named") or []}
    ledgers, _unreadable = load_ledgers(root)
    for raw in entry.get("bound") or []:
        pid = normalize_gap_id(str(raw))
        if pid is None:
            raise ck.Malformed(f"gap-migration bound lists {raw!r}, which is not a gap id")
        token, gid = pid.split("#")
        held = [i for l in ledgers if l.minor == minor_of(token) for i in l.items if i.gid == gid]
        if not held:
            continue
        found = [i for i in held if i.state == "open"]
        if len(found) != 1:
            state = "ambiguous" if found else "not an open gap"
            raise ck.Malformed(f"gap-migration bound lists {pid}, which is {state} in its ledger")
        if any(i.sensitive() for i in held) and pid not in named:
            raise ck.Malformed(
                f"gap-migration bound lists {pid}, a security or high-severity gap; list it in named too"
            )


_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_GOAL_RE = re.compile(r"^\*\*Goal\*\*:\s*(.+?)\s*$", re.MULTILINE)
DISPLAY_GAPS = 50
DISPLAY_PHASES = 40
_PHASE_RE = re.compile(r"^## Phase (\d+):", re.MULTILINE)
_TIER_RE = re.compile(r"^\*\*Recommended model tier\*\*:\s*`?([a-z]+)`?", re.MULTILINE)
_EFFORT_RE = re.compile(r"^\*\*Recommended effort level\*\*:\s*`?([a-z]+)`?", re.MULTILINE)
_OPEN_TASK_RE = re.compile(r"^- \[ \] T\d{3,}\b", re.MULTILINE)
_SUMMARY_VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+\Z", re.ASCII)
_SUMMARY_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,99}\Z", re.ASCII)


def plan_phases(version: str, text: str) -> list[dict]:
    """Each `## Phase N:` section's recommended tier and effort and its open task count.

    The values are raw tokens; the page renders only those that match its fixed
    tier and effort lists, so no other plan text reaches the summary.
    """
    found = list(_PHASE_RE.finditer(text))
    phases = []
    for index, match in enumerate(found):
        end = found[index + 1].start() if index + 1 < len(found) else len(text)
        body = text[match.end():end]
        tier, effort = _TIER_RE.search(body), _EFFORT_RE.search(body)
        phases.append({
            "version": version,
            "phase": int(match.group(1)),
            "tier": tier.group(1) if tier else "",
            "effort": effort.group(1) if effort else "",
            "tasks": len(_OPEN_TASK_RE.findall(body)),
        })
    return phases


def summary_input(ck: ModuleType, root: Path, path: str | None) -> dict:
    """The agent's `--summary` file: plain outcome bullets and the parallel-plan check.

    `{"outcomes": [str, ...], "parallel": {"checked": bool, "plans": [{"version",
    "slug"}]}}`. The page validates every outcome before showing it; here each named
    parallel plan must exist as a plan file, so the page never names a plan that is
    not there. No file means the summary says the parallel check was not run.
    """
    if not path:
        return {}
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ck.Malformed(f"--summary is not a readable JSON file: {exc}") from None
    if not isinstance(data, dict) or not set(data) <= {"outcomes", "parallel"}:
        raise ck.Malformed("--summary holds only outcomes and parallel")
    parallel = data.get("parallel") or {"checked": False, "plans": []}
    plans = parallel.get("plans") if isinstance(parallel, dict) else None
    if not isinstance(plans, list) or not isinstance(parallel.get("checked"), bool):
        raise ck.Malformed("--summary parallel needs checked (true or false) and a plans list")
    for entry in plans:
        version = str((entry or {}).get("version", "")) if isinstance(entry, dict) else ""
        slug = str(entry.get("slug", "")) if isinstance(entry, dict) else ""
        if not _SUMMARY_VERSION_RE.match(version) or not _SUMMARY_SLUG_RE.match(slug):
            raise ck.Malformed("--summary parallel plans need a vX.Y.Z version and a plain slug")
        if not any((root / "docs").glob(f"**/plans/{version}-{slug}.md")):
            raise ck.Malformed(f"--summary names {version}-{slug}, which is not a plan file")
    return {"outcomes": data.get("outcomes") or [], "parallel": {"checked": parallel["checked"], "plans": plans}}


def page_display(
    root: Path, scope: str, plans: list[tuple[str, str, str]], *, earlier: bool, summary: dict | None = None
) -> dict:
    """What the approval page shows beside the hashed page, never bound by the code.

    `plans` is (version, repository-relative path, plan text) per member. Gap counts
    are the open items in each ledger at `scope`'s minor and, when `earlier`, every
    earlier minor too (a minor run's gap scope). Titles and goals are raw text: the
    page renders them only as quoted data in its details list.
    """
    shown, phases = [], []
    for version, rel, text in plans:
        phases += plan_phases(version, text)
        title = _TITLE_RE.search(text)
        goal = _GOAL_RE.search(text)
        shown.append({"version": version, "path": rel, "title": title.group(1) if title else "",
                      "goal": goal.group(1) if goal else ""})
    major, minor = minor_of(scope)
    try:
        ledgers, unreadable = load_ledgers(root)
    except OSError:
        ledgers, unreadable = [], ["?"]
    counts: dict[str, int] = {}
    gaps: list[dict] = []
    for ledger in ledgers:
        if ledger.minor > (major, minor) or (not earlier and ledger.minor != (major, minor)):
            continue
        open_items = [i for i in ledger.items if i.state == "open"]
        if open_items:
            counts[ledger.token()] = counts.get(ledger.token(), 0) + len(open_items)
        gaps += [{"id": f"{ledger.token()}#{i.gid}", "title": i.title.lstrip(":").strip()} for i in open_items]
    return {
        "plans": shown,
        "gap_counts": counts,
        "gaps": gaps[:DISPLAY_GAPS],
        "gaps_unreadable": bool(unreadable) or any(l.problems for l in ledgers),
        "phases": phases[:DISPLAY_PHASES],
        **(summary or {}),
    }


def action_page(token: str, action: str, record_nonce: str) -> dict:
    return {"action": action, "scope": {"kind": "minor", "minor": token}, "record_nonce": record_nonce}


def answer_page(ck: ModuleType, token: str, record: dict, index: int | None, member: str | None) -> dict:
    """Bind one open blocker and its actual member to the existing answer round."""
    blockers = record.get("blockers") or []
    if not isinstance(blockers, list) or not isinstance(index, int) or isinstance(index, bool) or not 0 <= index < len(blockers):
        raise ck.Malformed("no open blocker at that index")
    entry = blockers[index]
    if not isinstance(entry, dict) or not entry.get("open"):
        raise ck.Malformed("no open blocker at that index")
    versions = {m.get("version") for m in record["members"]}
    version = entry.get("version")
    if version is not None and (not isinstance(version, str) or version not in versions):
        raise ck.Malformed("blocker names a member outside this minor")
    if member is not None and (member not in versions or member != version):
        raise ck.Malformed("--member does not match this blocker's member")
    category = entry.get("category")
    if category not in ck.BLOCKER_CATEGORIES:
        raise ck.Malformed("unknown blocker category")
    page = action_page(token, "answer", str(record.get("nonce", "")))
    page["blocker"] = {"index": index, "category": category, "version": version,
                       "fingerprint": approval_binding.blocker_fingerprint(entry), "request": entry.get("request") or {},
                       "purpose": entry.get("purpose"), "why": entry.get("why")}
    return page


# --------------------------------------------------------------------------- record



# Operational handoff reuses the original signed minor record and conditional binding.
def _controller_metadata(ck: ModuleType, record: dict, path: Path) -> dict:
    """Authenticate immutable controller metadata before any Git ownership probe."""
    key = ck._secret(create=False)
    if (key is None or record.get('schema') != ck.SCHEMA_MINOR or record.get('scope') != 'minor'
            or not hmac.compare_digest(str(record.get('approvals_hmac', '')), ck._sign(record, key))):
        raise ck.MinorConflict('record-tampered')
    token = record.get('minor')
    parse_minor(ck, token)
    binding = record.get('implementation_controller')
    if binding is None:
        origin = str(record.get('repo_root', ''))
        current, generation = origin, 0
        common = None  # Authenticate origin/key before probing legacy Git ownership.
    elif isinstance(binding, dict):
        current = binding.get('repo_root')
        common = binding.get('git_common_dir')
        generation = binding.get('generation', 0)
        origin = binding.get('origin_root', current)
        legacy_fields = {'repo_root', 'git_common_dir'}
        transferred_fields = legacy_fields | {'origin_root', 'origin_record_key', 'generation', 'previous_root', 'head', 'at'}
        if set(binding) != (transferred_fields if generation else legacy_fields):
            raise ck.MinorConflict('invalid-controller-binding-fields')
        if (type(generation) is not int or generation < 0
                or (generation and (not isinstance(binding.get('previous_root'), str)
                                    or not re.fullmatch(r'[0-9a-f]{40}', str(binding.get('head', '')))
                                    or not isinstance(binding.get('at'), str)))):
            raise ck.MinorConflict('invalid-controller-binding')
    else:
        raise ck.MinorConflict('invalid-controller-binding')
    if not all(isinstance(value, str) and value and Path(value).is_absolute()
               and str(Path(value).resolve()) == value for value in (origin, current)):
        raise ck.MinorConflict('noncanonical-controller-binding')
    original_key = ck.record_key(Path(origin), str(record.get('repo', '')).lower(), 'minor:' + token)
    if (path.stem != original_key or record.get('repo_root') != origin
            or record.get('worktree') != origin
            or (generation and binding.get('origin_record_key') != original_key)):
        raise ck.MinorConflict('controller-origin-or-common-dir-mismatch')
    if common is not None and (not isinstance(common, str) or not common or not Path(common).is_absolute()
                               or str(Path(common).resolve()) != common):
        raise ck.MinorConflict('controller-ownership-unavailable')
    return {'origin_root': origin, 'repo_root': current, 'generation': generation,
            'git_common_dir': common, 'origin_record_key': original_key}


def controller_identity(ck: ModuleType, rctx: RepoContext, record: dict, path: Path, *, same_common: bool = True) -> dict:
    identity = _controller_metadata(ck, record, path)
    common = identity['git_common_dir']
    if common is None:
        # A failed observation raises; a verified unavailable origin stays a conflict.
        common = _common_dir(rctx, Path(identity['origin_root']))
        if not common:
            raise ck.MinorConflict('controller-ownership-unavailable')
    if same_common and common != _common_dir(rctx, rctx.root):
        raise ck.MinorConflict('controller-origin-or-common-dir-mismatch')
    return {**identity, 'git_common_dir': common}


def require_controller(ck: ModuleType, rctx: RepoContext, record: dict, path: Path) -> dict:
    identity = controller_identity(ck, rctx, record, path)
    if identity['repo_root'] != str(rctx.root):
        raise ck.MinorConflict('controller-mismatch')
    return identity


def minor_candidates(ck: ModuleType, rctx: RepoContext, token: str | None = None,
                     *, include_linked: bool = False, predicate=None) -> list[Path]:
    """Authenticated common-directory ownership includes the legacy absent-binding form."""
    found = []
    direct = rctx.scoped_record_path('minor:' + token) if token else None
    common = _common_dir(rctx, rctx.root)
    if not common:
        raise ck.MinorConflict('controller-ownership-unavailable')
    try:
        store = ck._runs_dir()
        try:
            store.stat()
        except FileNotFoundError:
            return []
        paths = sorted(path for path in store.iterdir() if path.name.endswith('.json'))
        for path in paths:
            if path.name.endswith('.gate.json'):
                continue
            record = ck.read_record(rctx, path)
            if record is None:
                # No absent-create decision may hide an unreadable possible owner.
                if include_linked or token is None or path == direct:
                    raise ck.MinorConflict('controller-ownership-unavailable')
                continue
            if record.get('schema') != ck.SCHEMA_MINOR:
                continue
            if token and record.get('minor') != token:
                continue
            if predicate is not None and not predicate(record):
                _controller_metadata(ck, record, path)
                continue
            identity = controller_identity(ck, rctx, record, path, same_common=False)
            if identity['git_common_dir'] != common:
                continue
            if token and not include_linked and str(rctx.root) not in {
                    identity['origin_root'], identity['repo_root']} and path != direct:
                continue
            found.append(path)
    except OSError as exc:
        raise ck.MinorConflict('controller-ownership-unavailable') from exc
    return found


def authority_records(ck: ModuleType, rctx: RepoContext, predicate) -> list[Path]:
    paths = ck.find_records_by_content(rctx.root, predicate)
    for path in minor_candidates(ck, rctx, predicate=predicate):
        record = ck.read_record(rctx, path)
        if predicate(record) and path not in paths:
            paths.append(path)
    return paths


def minor_creator(function):
    """Common/scope discovery and absent creation are one serialized operation."""
    @wraps(function)
    def wrapped(ck, args):
        ctx = repo_context(ck, args)
        try:
            with ck.minor_creation_lease(ctx, args.minor):
                owners = minor_candidates(ck, ctx, args.minor, include_linked=True)
                if len(owners) > 1:
                    raise ck.MinorConflict('multiple-minor-authorities')
                if owners:
                    raise ck.MinorConflict('minor-authority-already-exists')
                path = ctx.scoped_record_path('minor:' + args.minor)
                with ck.minor_lease(path, None, ctx):
                    return function(ck, args)
        except OSError as exc:
            raise ck.MinorConflict('controller-ownership-unavailable') from exc
    return wrapped


def minor_writer(function):
    """Acquire the shared lease before native minor command side effects."""
    @wraps(function)
    def wrapped(ck, args, *extra):
        ctx = repo_context(ck, args)
        path = record_file(ck, ctx, args.minor)
        raw = path.read_bytes() if path.exists() else None
        expected = hashlib.sha256(raw).hexdigest() if raw is not None else None
        with ck.minor_lease(path, expected, ctx):
            return function(ck, args, *extra)
    return wrapped


def _handoff_target(ck: ModuleType, source: RepoContext, record: dict, target: Path, head: str) -> RepoContext:
    raw = target
    try:
        target = target.resolve(strict=True)
    except OSError as exc:
        raise ck.MinorConflict('target-unavailable') from exc
    if not raw.is_absolute() or str(raw) != str(target):
        raise ck.MinorConflict('noncanonical-controller-target')
    listing = source._git_out('worktree', 'list', '--porcelain')
    registered = {str(Path(line[9:]).resolve()) for line in listing.splitlines() if line.startswith('worktree ')}
    if str(target) not in registered or target == source.root:
        raise ck.MinorConflict('target-not-distinct-registered-worktree')
    ctx = ck.RepoContext(target, source.budget)
    if _common_dir(ctx, target) != _common_dir(source, source.root):
        raise ck.MinorConflict('target-common-directory-mismatch')
    forbidden = {str(Path(record['repo_root']).resolve())}
    branches = set()
    for member in record['members']:
        cleanup = member.get('approvals', {}).get('cleanup') or {}
        forbidden.update(str(Path(path).resolve()) for path in cleanup.get('worktrees', []))
        branches.update(cleanup.get('branches') or [member['source_branch']])
        implementation = member.get('implementation') or {}
        if implementation.get('worktree'):
            forbidden.add(str(Path(implementation['worktree']).resolve()))
    for block in listing.split('\n\n'):
        rows = block.splitlines()
        branch = next((line[18:] for line in rows if line.startswith('branch refs/heads/')), '')
        root = next((line[9:] for line in rows if line.startswith('worktree ')), '')
        if branch in branches and root:
            forbidden.add(str(Path(root).resolve()))
    if any(target == Path(path) or target.is_relative_to(Path(path)) for path in forbidden):
        raise ck.MinorConflict('target-is-frozen-cleanup-or-worker-path')
    rc, status = ctx.run([ctx.git, '-C', str(target), 'status', '--porcelain=v1', '--untracked-files=all'])
    flags_rc, flags_text = ctx.run([ctx.git, '-C', str(target), 'ls-files', '-v'])
    flags = flags_text.splitlines()
    index_rc, _ = ctx.run([ctx.git, '-C', str(target), 'ls-files', '--stage'])
    if rc or status.strip() or index_rc or flags_rc or any(line and (line[0].islower() or line[0] == 'S') for line in flags):
        raise ck.MinorConflict('target-index-not-provably-clean')
    if not re.fullmatch(r'[0-9a-f]{40}', head) or ctx._git_out('rev-parse', 'HEAD') != head:
        raise ck.MinorConflict('target-head-mismatch')
    target_branch = _target(record)
    tip = _ls_remote_tip(ctx, target_branch)
    if tip != head or ctx._git_out('rev-parse', 'refs/remotes/origin/' + target_branch) != tip:
        raise ck.MinorConflict('target-not-fresh-integration-tip')
    if _ancestor(ctx, str(record['start_head']), head) != 'met':
        raise ck.MinorConflict('original-start-not-in-target')
    for member in record['members']:
        view = ck.project(record, member['version'])
        if ck._approved_remote_status(ctx, view) != 'met':
            raise ck.MinorConflict('target-remote-outside-approval')
        if member.get('start_head') and _ancestor(ctx, member['start_head'], head) != 'met':
            raise ck.MinorConflict('member-start-not-in-target')
        pull = ck._gh_json(ctx, str(record['repo']), 'pr', 'view', member['source_branch'], '--json', 'state,mergeCommit')
        if pull is ck.GH_NOT_FOUND:
            continue
        if not isinstance(pull, dict):
            raise ck.MinorConflict('member-history-cannot-verify')
        if pull.get('state') == 'MERGED':
            merge_info = pull.get('mergeCommit')
            if not isinstance(merge_info, dict):
                raise ck.MinorConflict('member-history-cannot-verify')
            merge = merge_info.get('oid', '')
            tag = str(member.get('tag') or member['version'])
            if (_ancestor(ctx, merge, head) != 'met' or _tag_in(ctx, tag, head) != 'met'
                    or ck._release_status(ctx, str(record['repo']), tag) != 'met'):
                raise ck.MinorConflict('member-release-history-not-in-target')
    major, minor = parse_minor(ck, record['minor'])
    plans = {plan.version: plan for plan in scan_plans(target, major, minor)}
    if any(member['version'] not in plans or not member_identity_ok(ck, member, plans[member['version']])
           for member in record['members']):
        raise ck.MinorConflict('target-frozen-plan-mismatch')
    return ctx


def cmd_record_controller_handoff(ck: ModuleType, args: argparse.Namespace) -> int:
    target = Path(args.to)
    # An exact completed retry can resolve at the surviving destination after source removal.
    start = Path(args.repo) if Path(args.repo).is_dir() else target
    ctx = ck.RepoContext(start, ck.Budget(ck.BUDGET_SECONDS))
    path = record_file(ck, ctx, args.minor)
    record = ck.read_record(ctx, path)
    if record is None:
        raise ck.MinorConflict('minor-record-unavailable')
    identity = controller_identity(ck, ctx, record, path)
    binding = record.get('implementation_controller') or {}
    same = (identity['repo_root'] == str(target.resolve()) and identity['generation'] == args.expected_generation + 1
            and binding.get('previous_root') == str(Path(args.repo).resolve()) and binding.get('head') == args.head)
    if record.get('session_id') != args.session:
        raise ck.MinorConflict('session-mismatch')
    if same:
        ctx = ck.RepoContext(target, ck.Budget(ck.BUDGET_SECONDS))
        record = ck.read_record(ctx, path)
        require_controller(ck, ctx, record, path)
        if not _verified(ck, ctx, args.minor, record):
            raise ck.MinorConflict('minor-authority-unverified')
        print('ALREADY TRANSFERRED ' + str(path))
        return 0
    if (identity['repo_root'] != str(ctx.root) or identity['repo_root'] != str(Path(args.repo).resolve())
            or identity['generation'] != args.expected_generation):
        raise ck.MinorConflict('controller-generation-mismatch')
    state = load_minor(ck, ctx, args.minor, args.session)
    if state.record is None or state.forced or record.get('completed'):
        raise ck.MinorConflict('minor-not-transferable')
    _handoff_target(ck, ctx, record, target, args.head)
    if not args.apply:
        print('WOULD TRANSFER ' + json.dumps({'record': str(path), 'from': str(ctx.root),
              'to': str(target), 'generation': args.expected_generation + 1, 'head': args.head}, sort_keys=True))
        return 0
    # The pre-lease validation can spend most of the budget on a minor with many
    # members; the lease and the in-lease revalidation repeat that work on their own.
    ctx.budget = ck.Budget(ck.BUDGET_SECONDS)
    with ck.minor_transaction(record):
        if ck.lock_live(path):
            raise ck.MinorConflict('runner-live')
        _handoff_target(ck, ctx, record, target, args.head)
        record['implementation_controller'] = {**identity, 'repo_root': str(target),
            'generation': args.expected_generation + 1, 'previous_root': str(ctx.root),
            'head': args.head, 'at': ck._now()}
        record['approvals_hmac'] = ck._sign(record, ck._secret(create=False) or b'')
        ck._write_record(path, record)
    print('TRANSFERRED ' + str(path))
    return 0


def record_file(ck: ModuleType, rctx: RepoContext, token: str) -> Path:
    matches = minor_candidates(ck, rctx, token)
    if len(matches) > 1:
        raise ck.MinorConflict('multiple-minor-authorities')
    return matches[0] if matches else rctx.scoped_record_path('minor:' + token)


def minor_record_path(ck: ModuleType, args: argparse.Namespace) -> Path:
    parse_minor(ck, args.minor)
    return record_file(ck, repo_context(ck, args), args.minor)


def load_minor(
    ck: ModuleType, rctx: RepoContext, token: str, session: str | None, *, accept_completed: bool = False,
) -> MinorState:
    """Load and verify the schema-2 record for `token`.

    Integrity (any failure is `record-tampered`): outside every working tree,
    `schema` 2 with `scope` "minor" and this `minor`, a verifying HMAC, and every
    member, found BY VERSION across the canonical, legacy, and archive layouts,
    hashing to its frozen `plan_sha256`. Then validity: marked complete is
    ignored (there is no expiry); bound to another session is ignored until a
    resume paste adopts it; a pause is PAUSED; an open blocker is BLOCKED; and a
    member now owned by another run is `BLOCKED: owned-by-another-run (vX.Y.Z)`.
    A blocker recorded against one member reads `BLOCKED: <category> (vX.Y.Z)`.
    `accept_completed` keeps a completed record loaded, so `check-minor` still
    reports `MINOR COMPLETE` after it marked the record complete.
    """
    state = MinorState()
    try:
        path = record_file(ck, rctx, token)
    except ck.MinorConflict as exc:
        if str(exc) != "record-tampered":
            raise
        state.forced = ck.TAMPERED
        return state
    if not path.is_file():
        return state
    record = ck.read_record(rctx, path)
    if record is None or not _verified(ck, rctx, token, record):
        state.forced = ck.TAMPERED
        return state
    if record.get("completed") and not accept_completed:
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
        first = open_blockers[0]
        version = first.get("version")
        suffix = f" ({version})" if isinstance(version, str) and PLAN_TOKEN_RE.match(version) else ""
        state.forced = (f"BLOCKED: {first.get('category')}{suffix}", ck.EXIT_BLOCKED)
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
    try:
        path = getattr(record, "record_path", rctx.scoped_record_path("minor:" + token))
        require_controller(ck, rctx, record, path)
    except ck.MinorConflict:
        return False
    major, minor = parse_minor(ck, token)
    try:
        by_version = {p.version: p for p in scan_plans(rctx.root, major, minor)}
    except MinorMalformed:
        return False
    for member in members:
        plan = by_version.get(str(member.get("version")))
        # Schema 2 is new in v4.13.6, so only the current hash rule applies.
        if plan is None or not member_identity_ok(ck, member, plan):
            return False
    return True


# The folders under a minor's active tree whose `<version>-` entries one member owns
# (completion contract, "Member archive"); everything else in the tree is shared.
MEMBER_OWNED_DIRS = ("plans", "development", "development/history", "research", "analysis")


def member_identity_ok(ck: ModuleType, member: dict, plan: Plan) -> bool:
    """True when `plan` is the member's frozen plan or its signed member-archive copy.

    A member archived on release keeps its frozen `plan_sha256`; the archive signs the
    archived path and hash beside it in `archived`, and only that exact path with that
    exact hash counts. A member without `archived` verifies exactly as before.
    """
    digest = ck.plan_hash_text(plan.text)
    if digest == member.get("plan_sha256"):
        return True
    archived = member.get("archived")
    return (isinstance(archived, dict) and plan.rel == archived.get("plan_path")
            and digest == archived.get("plan_sha256"))


def member_moves(version: str, tree: str, tracked: list[str], plan_rel: str | None = None) -> list[tuple[str, str]]:
    """(old prefix, new prefix) for every path member `version` owns in the active `tree`.

    Owned: the frozen plan (`plan_rel`), and each entry directly under one of
    MEMBER_OWNED_DIRS whose name starts with exactly `<version>-`, so `v4.14.1-` never
    matches `v4.14.10-`. `tracked` lists repository-relative files. The new prefix
    mirrors the final archive layout, so the minor close composes with it.
    """
    major, minor = minor_of(version)
    dest = ARCHIVE_TREE.format(M=major, m=minor)
    owned: set[str] = set()
    for rel in tracked:
        if not rel.startswith(tree + "/"):
            continue
        if plan_rel and rel == plan_rel and rel.startswith(f"{tree}/plans/"):
            owned.add(rel)
        for folder in MEMBER_OWNED_DIRS:
            base = f"{tree}/{folder}/"
            if rel.startswith(base):
                entry = rel[len(base):].split("/", 1)[0]
                if entry.startswith(version + "-"):
                    owned.add(base + entry)
    return [(old, dest + old[len(tree):]) for old in sorted(owned)]


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
    mode = ck.render_mode(args)  # a flag conflict is refused before any round opens
    rctx = repo_context(ck, args)
    token = args.minor
    parse_minor(ck, token)
    if getattr(args, "member", None) is not None and args.action != "answer":
        raise ck.Malformed("--member requires --action answer")
    if getattr(args, "added_class", None) is not None and args.action != "add-class":
        raise ck.Malformed("--class requires --action add-class")
    if args.action == "create":
        if not args.approvals:
            raise ck.Malformed("record render --action create needs --approvals")
        spec = minor_spec(ck, args.approvals)
        found = _membership_or_exit(ck, rctx, token, spec)
        if isinstance(found, int):
            return found
        page = create_page(ck, rctx, token, spec, *found)
        display = page_display(
            rctx.root, token, [(p.version, p.rel, p.text) for p in found[0].members], earlier=True,
            summary=summary_input(ck, rctx.root, getattr(args, "summary", None)),
        )
    elif args.action in ("answer", "pause", "resume"):
        record = _record_for_action(ck, rctx, token, args.action, args.session)
        if isinstance(record, int):
            return record
        page = (answer_page(ck, token, record, args.blocker, getattr(args, "member", None))
                if args.action == "answer" else action_page(token, args.action, str(record.get("nonce", ""))))
        display = None
    elif args.action == "add-class":
        record = _record_for_add_class(ck, rctx, token, args.session)
        if isinstance(record, int):
            return record
        page = add_class_page(ck, token, record, getattr(args, "added_class", None))
        display = None
    else:
        raise ck.Malformed("a minor record supports create, answer, pause, resume or add-class")
    session = None if args.session == "auto" else args.session
    blocker = args.blocker if args.action == "answer" else None
    try:
        pending = approval_binding.render(
            ck._runs_dir(),
            _round_key(rctx, token),
            ck._secret(create=True) or b"",
            action=args.action,
            scope=token,
            page=page,
            session=session,
            blocker=blocker,
            platform=args.platform,
            allow_short_reply=mode == "question",
            check=lambda pending: approval_page.render_page(
                approval_page.render_data(pending, scope=token, blocker=blocker, display=display)
            ),
        )
    except approval_binding.Refusal as refusal:
        return ck._refused(refusal.reason)
    except approval_page.PageError as exc:
        print(f"approval page not rendered: {exc}", file=sys.stderr)
        return ck.EXIT_MALFORMED
    data = approval_page.render_data(pending, scope=token, blocker=blocker, display=display)
    return approval_page.emit(data, mode)


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


@minor_creator
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
    paste = approval_binding.pasted(pending)
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
            "authorization_context": pending.get('capture'),
            "autonomy_policy": page.get('autonomy'),
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
    """The verified record an answer, pause or resume applies to.

    A resume may adopt a record bound to another session (the cross-session
    resume); a pause applies only in the record's own session.
    """
    state = load_minor(ck, rctx, token, None if session == "auto" else session, accept_completed=action == "answer")
    record = state.record or (state.other_session if action == "resume" else None)
    if record is not None:
        return record
    if state.forced and state.forced[1] == ck.EXIT_BLOCKED:
        return ck._blocked(state.forced[0].removeprefix("BLOCKED: "))
    for notice in state.notices:
        print(f"notice: {notice}", file=sys.stderr)
    print("no minor run record for this scope and session", file=sys.stderr)
    return ck.EXIT_MALFORMED


@minor_writer
def cmd_record_answer(ck: ModuleType, args: argparse.Namespace) -> int:
    rctx = repo_context(ck, args)
    token = args.minor
    parse_minor(ck, token)
    record = _record_for_action(ck, rctx, token, "answer", args.session)
    if isinstance(record, int):
        return record
    page = answer_page(ck, token, record, args.blocker, getattr(args, "member", None))
    consumed = _consume(ck, rctx, token, "answer", page, args.session, str(record.get("session_id") or ""))
    if isinstance(consumed, int):
        return consumed
    pending, _session = consumed
    if args.text is not None and approval_binding.normalize(args.text) not in {
        approval_binding.normalize(x) for x in [*pending["paste_lines"], approval_binding.pasted(pending)]
    }:
        return ck._refused("approval-not-captured")
    record["blockers"][args.blocker].update(
        open=False, answered=ck._now(), answer_text=approval_binding.pasted(pending),
    )
    # Blockers are unsigned; an answer never changes the frozen approval classes.
    ck._write_record(record_file(ck, rctx, token), record)
    print(f"ANSWERED blocker {args.blocker} minor {token}")
    return 0


@minor_writer
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
        approval_binding.normalize(x) for x in [*pending["paste_lines"], approval_binding.pasted(pending)]
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


# Classes a running minor record may gain by one genuine decision of its own (completion
# contract, "Member archive"); every other class is fixed at `record create`.
ADDABLE_CLASSES = ("archive-member",)


def add_class_page(ck: ModuleType, token: str, record: dict, name: str | None) -> dict:
    """The canonical page that adds one class to a running minor record."""
    if name not in ADDABLE_CLASSES:
        raise ck.Malformed("--class must be one of " + ", ".join(ADDABLE_CLASSES))
    present = _classes(record)
    if name in present:
        raise ck.Malformed(f"the minor record already carries {name}")
    if "archive-minor" not in present:
        raise ck.Malformed(f"{name} is valid only with archive-minor, which this record does not carry")
    page = action_page(token, "add-class", str(record.get("nonce", "")))
    page["class"] = name
    return page


def _record_for_add_class(ck: ModuleType, rctx: RepoContext, token: str, session: str) -> dict | int:
    """The verified, live record a class is added to; completed, paused, blocked, or tampered refuses."""
    state = load_minor(ck, rctx, token, None if session == "auto" else session)
    if state.forced is not None:
        print(state.forced[0])
        return state.forced[1]
    if state.record is None:
        for notice in state.notices:
            print(f"notice: {notice}", file=sys.stderr)
        print("no live minor run record for this scope and session", file=sys.stderr)
        return ck.EXIT_MALFORMED
    return state.record


@minor_writer
def cmd_record_add_class(ck: ModuleType, args: argparse.Namespace) -> int:
    """Add one ADDABLE_CLASSES class to a running minor record from the user's genuine paste.

    The same round as answer, pause and resume: `record render --action add-class`
    shows the page, the user pastes its line in the record's own session, and this
    consumes that captured prompt once. Only the named class is added, with its
    provenance, and the record is re-signed; nothing else in the record changes.
    """
    rctx = repo_context(ck, args)
    token = args.minor
    parse_minor(ck, token)
    record = _record_for_add_class(ck, rctx, token, args.session)
    if isinstance(record, int):
        return record
    name = args.added_class
    if name in ADDABLE_CLASSES and name in _classes(record):
        print(f"ALREADY ADDED {name} minor {token}")
        return 0
    page = add_class_page(ck, token, record, name)
    consumed = _consume(ck, rctx, token, "add-class", page, args.session, str(record.get("session_id") or ""))
    if isinstance(consumed, int):
        return consumed
    pending, _session = consumed
    if args.text is not None and approval_binding.normalize(args.text) not in {
        approval_binding.normalize(x) for x in [*pending["paste_lines"], approval_binding.pasted(pending)]
    }:
        return ck._refused("approval-not-captured")
    record["approvals"]["classes"].append({
        "class": name,
        "text": approval_binding.pasted(pending),
        "added": {
            "at": ck._now(),
            "page_sha256": hashlib.sha256(approval_binding.canonical(page)).hexdigest(),
            "authorization_context": pending.get("capture"),
        },
    })
    # `approvals` is signed, so the added class is a signed update, never an unsigned edit.
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    ck._write_record(record_file(ck, rctx, token), record)
    print(f"ADDED {name} minor {token}")
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

_MINOR_DIR_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\Z", re.ASCII)
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
# Fields a gap entry carries: the tracker's entry template and the carry-forward contract.
# A heading outside every item whose own text holds two of them is a gap that lost its id;
# grouping and checkpoint headings in real ledgers carry at most one.
_GAP_FIELD_RE = re.compile(
    r"^\s{0,3}(?:[-*+]\s+)?\*\*(?P<field>Source phase|Plan reference|Reason|Suggested next step|Owner"
    r"|Owner and next step|Severity|Blocker|Acceptance|Proving command|Current state|Reason it is open"
    r"|Migrated from|Carried from)\*\*\s*:",
    re.IGNORECASE,
)
_CLOSURE_WORD_RE = re.compile(r"\b(?:RESOLVED|CLOSED)\b")
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
    starts like an item id but is not an item, a heading outside any item that reads
    as a gap entry without an id (two entry fields in its own text, or a MIGRATED
    marker), an id shared by an unresolved item and any other item in the same patch
    section, or a header
    `**Open items**: N` that disagrees with the number of open items parsed.
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
    # A short id may recur across patch sections (`v0.2.0#WN-3` and `v0.2.1#WN-3` are
    # distinct items the carry tooling addresses by section); only a repeat inside one
    # section is ambiguous.
    seen: dict[tuple[str, str], int] = {}
    for item in items:
        seen[(item.section, item.gid)] = seen.get((item.section, item.gid), 0) + 1
    for gid in dict.fromkeys(
        i.gid for i in items if i.state != "resolved" and seen[(i.section, i.gid)] > 1
    ):
        problems.append(f"duplicate-id {gid}")
    next_heading = {line: (headings[h + 1][0] if h + 1 < len(headings) else len(lines))
                    for h, (line, *_rest) in enumerate(headings)}
    subsection = ""
    for index, raw in enumerate(lines):
        if mask[index] or index in item_lines:
            continue
        heading = _HEADING_RE.match(raw.rstrip("\r\n"))
        if heading:
            level, title = len(heading.group(1)), heading.group(2) or ""
            if level <= 3:
                subsection = title if level == 3 else ""
            own = range(index + 1, next_heading.get(index, index + 1))
            if level >= 3 and _lost_id(title, subsection, [lines[k] for k in own if not mask[k]]):
                problems.append(f"line {index + 1} heading-without-id")
            continue
        row = _ROW_RE.match(raw.rstrip("\r\n"))
        if row and _ITEM_LIKE_RE.match(row.group("rest")) and not subsection.lower().startswith("resolved"):
            problems.append(f"line {index + 1} row")
    header = _header(text, lines, mask)
    stated = _OPEN_ITEMS_LINE_RE.search(header)
    if stated and int(stated.group(1)) != sum(1 for i in items if i.state == "open"):
        problems.append("open-items-count")
    return items, problems


def _lost_id(title: str, subsection: str, body: list[str]) -> bool:
    """A non-item heading that reads as a gap entry whose id was removed.

    Closed and Resolved-section headings never count: losing the id of resolved work
    hides nothing that is still owed.
    """
    if subsection.lower().startswith("resolved") or _CLOSURE_WORD_RE.search(title):
        return False
    if MIGRATED_RE.search(title):
        return True
    fields = {m.group("field").lower() for m in map(_GAP_FIELD_RE.match, body) if m}
    return len(fields) >= 2


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


def load_ledgers_at(rctx: RepoContext, ref: str) -> tuple[list[Ledger], list[str]] | None:
    """Every ledger at a layout path as committed on `ref`, and the paths git could not show.

    None when git cannot list the ref. The minor verdict reads ledgers here, never from
    the working tree: an uncommitted or unmerged migration is not a closed gap.
    """
    rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "ls-tree", "-r", "--name-only", ref, "--", "docs"])
    if rc != 0:
        return None
    ledgers: list[Ledger] = []
    unreadable: list[str] = []
    for rel in (line.strip() for line in out.splitlines()):
        parts = rel.split("/")
        if parts[-1] != "known-gaps.md" or len(parts) < 3:
            continue
        match = _MINOR_DIR_RE.match(parts[-2])
        if not match:
            continue
        minor = (int(match.group(1)), int(match.group(2)))
        layout = _layout_of(rel, *minor)
        if layout is None:
            continue
        rc, text = rctx.run([rctx.git, "-C", str(rctx.root), "show", f"{ref}:{rel}"])
        if rc != 0:
            unreadable.append(rel)
            continue
        items, problems = parse_ledger_full(text)
        ledgers.append(Ledger(rctx.root / rel, rel, minor, layout, text, items, problems))
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


def migration_copy_status(
    ledgers: list[Ledger], target: str, source: Ledger, item: GapItem, *,
    label: str | None = None, allow_carried: bool = False, require_reason: bool = False,
) -> tuple[str, tuple[Ledger, GapItem] | None]:
    """Prove one destination retains the source's title and complete reconciled body.

    Write preflight requires the target .0 section. Read-only verification also
    permits a later patch carrying the explicit .0 origin. Archive comparisons
    repair only moves proved by a unique archived ledger with no active peer.
    """
    # Import lazily: the write helper already imports this read-only module.
    from minor_close import (
        _TITLE_VERSION_RE,
        rewrite_links,
        rewrite_mentions,
    )

    def proof_lines(body: str) -> list[str]:
        lines = body.splitlines(keepends=True)
        mask, _ = fence_mask(lines)
        clean_lines = [re.sub(r"\S", " ", line) if mask[index] else line for index, line in enumerate(lines)]
        code_spans = re.compile(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)", re.DOTALL)
        start = 0
        for end in range(len(lines) + 1):
            if end == len(lines) or mask[end] or not lines[end].strip():
                paragraph = "".join(lines[start:end])
                clean_lines[start:end] = code_spans.sub(
                    lambda match: re.sub(r"\S", " ", match.group(0)), paragraph,
                ).splitlines(keepends=True)
                start = end + 1
        in_comment = False
        visible = []
        for index, line in enumerate(lines):
            was_in_comment = in_comment
            clean = clean_lines[index]
            comments = [] if mask[index] else list(re.finditer(r"<!--|--!?>", clean))
            for comment in comments:
                in_comment = comment.group(0) == "<!--"
            visible.append("" if mask[index] or was_in_comment or in_comment or comments else clean)
        return visible

    def origin_label(match: re.Match) -> str | None:
        if label is None:
            return f"{match.group('minor')}#{match.group('id')}"
        qualified = PLAN_MIGRATED_FROM_RE.search(match.group(0))
        return f"{qualified.group('version')}#{qualified.group('id')}" if qualified else None

    targets = [ledger for ledger in ledgers if ledger.minor == minor_of(target)]
    matches: list[tuple[Ledger, GapItem]] = []
    reasons: list[str | None] = []
    hidden_provenance = False
    hidden_destination = False
    for ledger in targets:
        ledger_lines = ledger.text.splitlines(keepends=True)
        ledger_visible = proof_lines(ledger.text)
        ledger_fences, _ = fence_mask(ledger_lines)
        section_visible = True
        item_visible = []
        line_indices = {}
        offset = 0
        for index, line in enumerate(ledger_lines):
            line_indices[offset] = index
            offset += len(line)
            heading = _HEADING_RE.match(line.rstrip("\r\n")) if not ledger_fences[index] else None
            if heading and len(heading.group(1)) == 2:
                section_visible = bool(ledger_visible[index].strip())
            item_visible.append(section_visible and bool(ledger_visible[index].strip()))
        for copy in ledger.items:
            lines = copy.body.splitlines(keepends=True)
            visible = proof_lines(copy.body)
            origins = []
            for index, line in enumerate(lines):
                for match in MIGRATED_FROM_RE.finditer(line):
                    origin = origin_label(match)
                    if origin == (label or f"{source.token()}#{item.gid}"):
                        proof = next((candidate for candidate in MIGRATED_FROM_RE.finditer(visible[index])
                                      if origin_label(candidate) == origin), None)
                        origins.append(proof or match)
                        hidden_provenance = hidden_provenance or proof is None
            if origins:
                matches.append((ledger, copy))
                hidden_destination = hidden_destination or not item_visible[line_indices[copy.start]]
                for origin in origins:
                    reason = MIGRATION_REASON_RE.search(origin.group("rest"))
                    reasons.append(reason.group("reason") if reason else None)
    found = matches[0] if matches else None
    if len(targets) > 1 or len(matches) > 1 or len(reasons) > 1:
        return "migration-target-ambiguous", found
    if found is None:
        return "migration-target-missing", None
    destination, copy = found
    if destination.problems:
        return "migration-target-malformed", found
    if hidden_destination:
        return "migration-target-hidden", found
    if hidden_provenance:
        return "migration-provenance-hidden", found
    if require_reason and reasons[0] not in MIGRATION_REASONS:
        return "migration-reason-invalid", found
    version = section_version(copy.section)
    lineage = [match for match in CARRIED_FROM_RE.finditer("".join(proof_lines(copy.body)))
               if match.group("version") == target]
    carried_id = LEDGER_ITEM_RE.match(lineage[0].group("id") or "") if len(lineage) == 1 else None
    carried = (
        allow_carried and version is not None and minor_of(version) == destination.minor
        and version_order(version) > version_order(target)
        and carried_id is not None and carried_id.group("kind") == copy.kind
    )
    if version != target and not carried:
        return "migration-target-wrong-section", found

    moves: list[tuple[str, str]] = []
    for archived in ledgers:
        if archived.layout != "archive" or any(
            other.minor == archived.minor and other is not archived for other in ledgers
        ):
            continue
        directory = archived.rel.rsplit("/", 1)[0]
        moves.extend((tree.format(M=archived.minor[0], m=archived.minor[1]), directory)
                     for tree in ACTIVE_TREES)

    def moved(path: str) -> str:
        for old, new in moves:
            if path == old or path.startswith(old + "/"):
                return new + path[len(old):]
        return path

    def repaired(body: str, old_dir: str) -> str:
        body, _ = rewrite_links(body, old_dir, destination.rel.rsplit("/", 1)[0], moved)
        for old, new in moves:
            body, _ = rewrite_mentions(body, old, new, markdown=True)
        return body.replace("\r\n", "\n").strip("\n").rstrip()

    required = repaired(item.body, source.rel.rsplit("/", 1)[0])
    actual = repaired(copy.body, destination.rel.rsplit("/", 1)[0])

    def starts_block(text: str) -> bool:
        return not required or (
            text.startswith(required)
            and (len(text) == len(required) or text[len(required)] == "\n")
        )

    def title(text: str) -> str:
        return _RESOLVED_PREFIX_RE.sub(
            "", _RESOLVED_END_RE.sub("", MIGRATED_RE.sub("", text))
        ).rstrip()

    source_title = title(item.title)
    expected_title = _TITLE_VERSION_RE.sub(
        lambda match: f"{match.group(1)}({version})", source_title, count=1
    ) if carried else source_title
    if expected_title.strip() == title(copy.title).strip():
        return ("migration-copy-complete" if starts_block(actual) else "migration-body-not-preserved"), found
    original_heading = item.gid + source_title
    lines = actual.splitlines(keepends=True)
    visible = proof_lines(actual)
    saw_title = False
    for index, line in enumerate(lines):
        heading = _HEADING_RE.match(line.rstrip("\n"))
        callout = re.match(r"^\s*(?:-\s+)?\*\*Original source\*\*:\s*(.*?)\s*$", line)
        text = heading.group(2) if heading else "Original source: " + callout.group(1) if callout else ""
        if visible[index] and (
            title(text) == "Original source: " + original_heading
        ):
            saw_title = True
            if starts_block("".join(lines[index + 1:]).lstrip("\n")):
                return "migration-copy-complete", found
    return ("migration-body-not-preserved" if saw_title else "migration-title-not-preserved"), found


def _ledger_blob(rctx: RepoContext, commit: str, rel: str) -> tuple[str, str]:
    """Reuse only successful immutable blob reads within this evaluation context."""
    key = (commit.lower(), rel) if re.fullmatch(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})", commit) else None
    cache = getattr(rctx, "_minor_blob_cache", None)
    if cache is None:
        cache = rctx._minor_blob_cache = {}
    if key is not None and key in cache:
        return "met", cache[key]
    rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "cat-file", "-e", f"{commit}:{rel}"])
    if rc == -1:
        return "cannot-verify", ""
    if rc != 0:
        return "unmet", ""
    rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "show", f"{commit}:{rel}"])
    if rc != 0:
        return "cannot-verify", ""
    if key is not None:
        cache[key] = out
    return "met", out


def existed_at(rctx: RepoContext, commit: str, minor: tuple[int, int], gid: str) -> str:
    """`met` when the minor's ledger at `commit` already held item `gid`, else `unmet`.

    Every layout path is tried, so a ledger archived since `commit` still resolves.
    `cannot-verify` when git cannot answer.
    """
    for rel in ledger_rels(*minor):
        status, out = _ledger_blob(rctx, commit, rel)
        if status == "cannot-verify":
            return status
        if status != "met":
            continue
        if any(item.gid == gid for item in parse_ledger(out)):
            return "met"
    return "unmet"


def items_at(rctx: RepoContext, commit: str, minor: tuple[int, int], gid: str) -> tuple[str, list[GapItem]]:
    """("met", the items with id `gid`) in the minor's ledger as committed at `commit`.

    `unmet` with no items when no ledger held the id then; `cannot-verify` when git
    cannot answer. Every layout path is tried, so an archived ledger still resolves.
    """
    for rel in ledger_rels(*minor):
        status, out = _ledger_blob(rctx, commit, rel)
        if status == "cannot-verify":
            return status, []
        if status != "met":
            continue
        found = [item for item in parse_ledger(out) if item.gid == gid]
        if found:
            return "met", found
    return "unmet", []


def planned_followon_entry(ck: ModuleType, plan: Plan, task_id: str, frozen: str) -> tuple[str, str] | None:
    """Canonical recording-only opportunity from one exact frozen numbered task."""
    if ck.plan_hash_text(plan.text) != frozen:
        return None
    lines = plan.text.splitlines(keepends=True)
    mask, unclosed = fence_mask(lines)
    if unclosed:
        return None
    text = ''.join('\n' if mask[i] else line for i, line in enumerate(lines))
    all_tasks = list(re.finditer(r'^- \[[ xX]\] (T\d{3,}) (.+)$', text, re.MULTILINE))
    if sum(m[1] == task_id for m in all_tasks) != 1:
        return None
    for phase in re.finditer(r'^## Phase (\d+):[^\n]*\n(.*?)(?=^## |\Z)', text, re.MULTILINE | re.DOTALL):
        block = phase[2]
        tasks = list(re.finditer(r'^- \[[ xX]\] (T\d{3,}) (.+)$', block, re.MULTILINE))
        sections = list(re.finditer(r'^#### (\d+)\.(\d+) --[^\n]*\n(.*?)(?=^#### |^- \[[ xX]\] T\d|\Z)', block, re.MULTILINE | re.DOTALL))
        if len(tasks) != len(sections) or not tasks:
            continue
        if any(s[1] != phase[1] or int(s[2]) != n + 1 for n, s in enumerate(sections)):
            continue
        for index, task in enumerate(tasks):
            if task[1] != task_id:
                continue
            scope = re.fullmatch(r'File (.+) as a known gap (docs/\S+/known-gaps\.md)', task[2])
            prompts = re.findall(r'^> (.+)$', sections[index][3], re.MULTILINE)
            if scope is None or len(prompts) != 1:
                return None
            if scope[2] not in ledger_rels(*minor_of(plan.version)):
                return None
            prompt = prompts[0]
            fields = re.search(r'Reason: (.+?); Suggested next step: (.+?)\. Acceptance:', prompt)
            reference = re.search(r'Plan reference \x60([^\x60]+)\x60', prompt)
            if fields is None or reference is None or reference[1] != Path(plan.rel).name:
                return None
            title = ': Planned follow-on: ' + scope[1]
            task_hash = hashlib.sha256((task_id + ' ' + task[2]).encode('utf-8')).hexdigest()
            body = '\n\n'.join([
                '**Disposition**: planned-follow-on (OPEN)',
                f'**Source phase**: {plan.version} Phase {phase[1]} {task_id}',
                f'**Plan reference**: {Path(plan.rel).name}',
                f'**Frozen plan sha256**: {frozen}',
                f'**Frozen task sha256**: {task_hash}',
                f'**Reason**: {fields[1]}',
                f'**Suggested next step**: {fields[2]}.',
            ])
            return title, body
    return None


# A frozen task that records known gaps without the `File <scope> as a known gap` template:
# its line names this minor's ledger and says it records a gap, its line reconciles known gaps
# including a parked item, or its own sub-task prompt says "record a known gap" or "add one
# entry per/for each". The plan cannot supply the reason, so each entry binds every other field
# exactly, names a scope the frozen plan states verbatim, and carries its reason and next step
# as single lines.
RECORDED_TASK_RE = re.compile(r"\b(?:record|file|make)\b.*\bknown[- ]gap\b", re.IGNORECASE)
RECORDED_PARKED_RE = re.compile(r"\breconcile known gaps\b.*\bparked\b", re.IGNORECASE)
RECORDED_PROMPT_RE = re.compile(r"\brecord an? known gap\b|\badd one entry (?:per|for each)\b", re.IGNORECASE)
RECORDED_TITLE_RE = re.compile(r": Planned follow-on: (?P<scope>\S[^\n]{7,})")
RECORDED_BODY_RE = re.compile(
    r"\*\*Disposition\*\*: planned-follow-on \(OPEN\)\n\n"
    r"\*\*Source phase\*\*: (?P<version>v\d+\.\d+\.\d+) Phase (?P<phase>\d+) (?P<task>T\d{3,})\n\n"
    r"\*\*Plan reference\*\*: (?P<plan>[^\n]+)\n\n"
    r"\*\*Frozen plan sha256\*\*: (?P<frozen>[0-9a-f]{64})\n\n"
    r"\*\*Frozen task sha256\*\*: (?P<task_hash>[0-9a-f]{64})\n\n"
    r"\*\*Reason\*\*: [^\n]*\S[^\n]*\n\n"
    r"\*\*Suggested next step\*\*: [^\n]*\S[^\n]*\."
)


def recorded_followon_task(ck: ModuleType, plan: Plan, task_id: str, frozen: str) -> tuple[str, str] | None:
    """(phase number, task sha256) when one exact frozen task records a known gap in its minor's ledger.

    A task the exact template derives keeps its derived reason and next step, so it never qualifies here.
    """
    if ck.plan_hash_text(plan.text) != frozen or planned_followon_entry(ck, plan, task_id, frozen) is not None:
        return None
    lines = plan.text.splitlines(keepends=True)
    mask, unclosed = fence_mask(lines)
    if unclosed:
        return None
    text = ''.join('\n' if mask[i] else line for i, line in enumerate(lines))
    tasks = [m for m in re.finditer(r'^- \[[ xX]\] (T\d{3,}) (.+)$', text, re.MULTILINE) if m[1] == task_id]
    if len(tasks) != 1:
        return None
    task = tasks[0]
    phases = [p for p in re.finditer(r'^## Phase (\d+):[^\n]*\n', text, re.MULTILINE) if p.end() <= task.start()]
    if not phases:
        return None
    phase = phases[-1]
    if re.search(r'^## ', text[phase.end():task.start()], re.MULTILINE):
        return None
    sections = [s for s in re.finditer(r'^#### \d+\.\d+ -{1,2} [^\n]*\n', text, re.MULTILINE)
                if phase.end() <= s.start() < task.start()]
    prompt = ' '.join(re.findall(r'^> (.+)$', text[sections[-1].end():task.start()], re.MULTILINE)) if sections else ''
    names_ledger = (task[2].rsplit(' ', 1)[-1] in ledger_rels(*minor_of(plan.version))
                    and RECORDED_TASK_RE.search(task[2]) is not None)
    if not (names_ledger or RECORDED_PARKED_RE.search(task[2]) or RECORDED_PROMPT_RE.search(prompt)):
        return None
    return phase[1], hashlib.sha256((task_id + ' ' + task[2]).encode('utf-8')).hexdigest()


def recorded_followon(ck: ModuleType, rctx: RepoContext, plan: Plan, frozen: str,
                      source_minor: tuple[int, int], title: str, body: str) -> bool:
    """A bound entry whose scope the frozen plan names; a second entry with the same task and title is refused."""
    found = RECORDED_BODY_RE.fullmatch(body)
    titled = RECORDED_TITLE_RE.fullmatch(title)
    if found is None or titled is None or titled['scope'] not in plan.text.replace('\r\n', '\n'):
        return False
    if found['version'] != plan.version or found['plan'] != Path(plan.rel).name or found['frozen'] != frozen:
        return False
    if recorded_followon_task(ck, plan, found['task'], frozen) != (found['phase'], found['task_hash']):
        return False
    ledgers, unreadable = load_ledgers(rctx.root)
    if unreadable:
        return False
    line = f"**Source phase**: {plan.version} Phase {found['phase']} {found['task']}"
    citing = [i for ledger in ledgers if ledger.minor == source_minor for i in ledger.items
              if line in i.body.replace('\r\n', '\n').splitlines() and MIGRATED_RE.sub('', i.title).rstrip() == title]
    return len(citing) == 1


def planned_followon(rctx: RepoContext, record: dict | None, source_minor: tuple[int, int], item: GapItem | None) -> bool:
    """Recording-task disposition; callers already loaded a verified schema-2 record.

    No approval, migration bound, budget or record is changed. Free-form additions
    are defects, not the exact predeclared opportunity, and fail closed.
    """
    if not record or record.get('schema') != 2 or record.get('scope') not in {'minor', 'member'}:
        return False
    if item is None or item.kind != 'DF' or item.sensitive() or item.state not in {'open', 'migrated'}:
        return False
    if source_minor != minor_of(str(record.get('minor') or 'v0.0')):
        return False
    body = item.body.replace('\r\n', '\n').strip()
    source = re.search(r'^\*\*Source phase\*\*: (v\d+\.\d+\.\d+) Phase \d+ (T\d{3,})$', body, re.MULTILINE)
    if source is None or section_version(item.section) != source[1]:
        return False
    if record.get('scope') == 'minor':
        members = [m for m in record.get('members') or [] if m.get('version') == source[1]]
    else:
        members = [record] if record.get('version') == source[1] else []
    if len(members) != 1:
        return False
    import check_plan_completion as ck
    try:
        plans = [p for p in scan_plans(rctx.root, *source_minor) if p.version == source[1]]
    except (MinorMalformed, OSError, ValueError):
        return False
    if len(plans) != 1:
        return False
    member, plan = members[0], plans[0]
    if not member_identity_ok(ck, member, plan):
        return False
    expected = planned_followon_entry(ck, plan, source[2], str(member['plan_sha256']))
    title = MIGRATED_RE.sub('', item.title).rstrip()
    if expected == (title, body) or recorded_followon(ck, rctx, plan, str(member['plan_sha256']), source_minor, title, body):
        return True
    original = archived_followon_plan(rctx, record, member, plan, ck)
    if original is None:
        return False
    frozen = ck.plan_hash_text(original.text)
    expected = planned_followon_entry(ck, original, source[2], frozen)
    return expected == (title, body) or recorded_followon(ck, rctx, original, frozen, source_minor, title, body)


def archived_followon_plan(rctx: RepoContext, record: dict, member: dict, plan: Plan, ck: ModuleType) -> Plan | None:
    """Recover only the signed publication-start plan behind an actual archive repair."""
    archived = member.get('archived')
    if archived is not None:
        return _signed_original_plan(rctx, record, member, plan, ck)
    major, minor = minor_of(plan.version)
    archive = ARCHIVE_TREE.format(M=major, m=minor)
    name = Path(plan.rel).name
    if plan.rel != f'{archive}/plans/{name}' or member.get('plan_path') != plan.rel:
        return None
    if not any(c.get('class') == 'archive-minor' for c in record.get('approvals', {}).get('classes', [])):
        return None
    active = [t.format(M=major, m=minor) for t in ACTIVE_TREES]
    if any((rctx.root / tree).exists() for tree in active):
        return None
    start = member.get('member_start_head') if record.get('scope') == 'member' else member.get('start_head')
    if not isinstance(start, str) or re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', start) is None:
        return None
    from minor_close import rewrite_links, rewrite_mentions
    matches = []
    for tree in active:
        rel = f'{tree}/plans/{name}'
        rc, text = rctx.run([rctx.git, '-C', str(rctx.root), 'show', f'{start}:{rel}'])
        if rc == -1:
            return None
        if rc != 0:
            continue
        versions = list(PLAN_VERSION_RE.finditer(text))
        if len(versions) != 1 or 'v' + '.'.join(versions[0].groups()) != plan.version:
            return None
        moved = lambda path: archive + path[len(tree):] if path == tree or path.startswith(tree + '/') else path
        repaired, _ = rewrite_links(text, rel.rsplit('/', 1)[0], plan.rel.rsplit('/', 1)[0], moved)
        repaired, _ = rewrite_mentions(repaired, tree, archive, markdown=True)
        if ck.plan_hash_text(repaired) != member.get('plan_sha256'):
            return None
        matches.append(Plan(rel, plan.version, plan.order, plan.status, plan.slug, text))
    return matches[0] if len(matches) == 1 else None


def _signed_original_plan(rctx: RepoContext, record: dict, member: dict, plan: Plan, ck: ModuleType) -> Plan | None:
    """The original plan a signed `archived` entry names: its text at the member start.

    The member archive (or the minor close's re-freeze) signed the plan's original path
    (`from`) and frozen hash (`original_sha256`), so the original is read back from git
    and must hash to that value exactly; no tree replay and no active-tree rule apply.
    """
    archived = member.get('archived')
    if not isinstance(archived, dict) or not member_identity_ok(ck, member, plan):
        return None
    source, original = archived.get('from'), archived.get('original_sha256')
    if not isinstance(source, str) or not isinstance(original, str) or Path(source).name != Path(plan.rel).name:
        return None
    if not any(c.get('class') == 'archive-minor' for c in record.get('approvals', {}).get('classes', [])):
        return None
    start = member.get('member_start_head') if record.get('scope') == 'member' else member.get('start_head')
    if not start:
        start = record.get('minor_start_head') if record.get('scope') == 'member' else record.get('start_head')
    if not isinstance(start, str) or re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', start) is None:
        return None
    rc, text = rctx.run([rctx.git, '-C', str(rctx.root), 'show', f'{start}:{source}'])
    if rc != 0:
        return None
    versions = list(PLAN_VERSION_RE.finditer(text))
    if len(versions) != 1 or 'v' + '.'.join(versions[0].groups()) != plan.version:
        return None
    if ck.plan_hash_text(text) != original:
        return None
    return Plan(source, plan.version, plan.order, plan.status, plan.slug, text)


def planned_followon_copy(source: str, item: GapItem, copy: GapItem) -> bool:
    """One OPEN, exact canonical copy; shared write preflight and read-only proof."""
    suffix = copy.body.replace('\r\n', '\n').strip().removeprefix(item.body.replace('\r\n', '\n').strip())
    tail = (r'\n\n- \*\*Migrated from\*\*: ' + re.escape(f'{source}#{item.gid}')
            + r' on \d{4}-\d{2}-\d{2} \(reason: user-deferred\)'
            + r'\n- \*\*Migration evidence\*\*: [^\n]+')
    return (copy.state == 'open' and copy.kind == item.kind and not copy.sensitive()
            and copy.title == MIGRATED_RE.sub('', item.title).rstrip()
            and re.fullmatch(tail, suffix) is not None)


def migration_gate(
    rctx: RepoContext, record: dict | None, source_minor: tuple[int, int], gid: str,
    current: GapItem | None,
) -> tuple[str, str]:
    """(status, reason) for whether gap `source#gid` may migrate under `record`.

    The one gate every write and verify path shares. An exact frozen-plan
    recording-only opportunity has its own disposition and leaves future work open.
    Ordinary ids must be in the frozen `gap-migration` list and have existed, open and
    unambiguous, at the record's `start_head`: the approved baseline. A security
    or high-severity item must also be named individually, and sensitivity is
    judged on the baseline text as well as the current text, so editing a
    `**Severity**` line during the run cannot lift the naming requirement.
    """
    pid = "v{}.{}#{}".format(*source_minor, gid)
    bound, named = migration_class(record)
    if pid not in bound:
        if planned_followon(rctx, record, source_minor, current):
            return "met", "planned-follow-on"
        return "unmet", "migration-not-approved"
    start = str((record or {}).get("minor_start_head") or (record or {}).get("start_head") or "")
    if not start:
        return "cannot-verify", "no-start-head"
    status, baseline = items_at(rctx, start, source_minor, gid)
    if status != "met":
        return status, "created-during-run" if status == "unmet" else "history-unreadable"
    open_then = [item for item in baseline if item.state == "open"]
    if len(open_then) != 1:
        return "unmet", "not-open-at-start" if not open_then else "gap-ambiguous"
    if (open_then[0].sensitive() or (current is not None and current.sensitive())) and pid not in named:
        return "unmet", "security-not-named"
    return "met", "approved"


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
    copy_reason, found = migration_copy_status(
        ledgers, target, ledger, item, allow_carried=True,
        require_reason=target_minor > minor_of(run_token),
    )
    if found is None:
        return "unmet", copy_reason
    if target_minor <= minor_of(run_token):
        if copy_reason != "migration-copy-complete":
            return ("cannot-verify" if copy_reason == "migration-target-malformed" else "unmet"), copy_reason
        return "met", "in-scope-copy"
    if "v{}.{}".format(*target_minor) != next_minor(run_token):
        return "unmet", "migration-target-not-next-minor"
    copy = found[1]
    gate, reason = migration_gate(rctx, record, ledger.minor, item.gid, item)
    if gate != "met":
        return gate, reason
    if reason == "planned-follow-on" and not planned_followon_copy(source, item, copy):
        return "unmet", "planned-followon-copy-altered"
    if copy_reason != "migration-copy-complete":
        return ("cannot-verify" if copy_reason == "migration-target-malformed" else "unmet"), copy_reason
    reasons = [r for m, i, r in copy.provenance() if m == source and i == item.gid]
    if not reasons or reasons[-1] not in MIGRATION_REASONS:
        return "unmet", "migration-reason-invalid"
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
    for path in authority_records(
        ck, rctx, lambda r: r.get("schema") != ck.SCHEMA_MINOR or _minor_record_live(ck, r),
    ):
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
    for name, sha in dict.fromkeys(tips):
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
    if rctx.budget.remaining() <= 0:
        return None
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
    own_path = (record.record_path if isinstance(record, ck.MinorSnapshot)
                else record_file(ck, rctx, token) if record is not None else None)
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
    return excluded if rctx.budget.remaining() > 0 else None


def gaps_minor_status(
    ck: ModuleType, rctx: RepoContext, token: str, record: dict | None,
    loaded: tuple[list[Ledger], list[str]] | None = None,
) -> tuple[str, list[str]]:
    """(`gaps.minor` status, notices of fixed ids and repository-relative paths only).

    Met when every item in every ledger for a version at or below the run's minor
    (canonical, legacy, and archive layouts) is resolved or verifiably migrated.
    Ledgers for later versions are out of scope, so a migrated copy there never
    reopens the verdict. There is no deferrable state. `cannot-verify` when a ledger is
    unreadable or has a parse problem, when the scope cannot be decided, or when a
    ledger excluded for another live run's work still holds an open item. `loaded`
    supplies the ledgers (the minor verdict passes those on the integration branch);
    without it the working tree is read, as `minor_close.py status` does on the
    closing branch.
    """
    parse_minor(ck, token)
    run_minor = minor_of(token)
    ledgers, unreadable = loaded if loaded is not None else load_ledgers(rctx.root)
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
    """`archive.minor`: `unmet` without an `archive-minor` approval (a minor completes
    only once archived, so the absence is never `n/a`); else met when every active tree
    of the minor is absent on the integration branch and the archive tree is present
    there (the remote-tracking ref first, then the local branch)."""
    classes = ((record or {}).get("approvals") or {}).get("classes") or []
    if not any(isinstance(c, dict) and c.get("class") == "archive-minor" for c in classes):
        return "unmet"
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


def task_origin(version: str, path: str, archived: object) -> str | None:
    """The original location of a task path a member archive or the minor close re-pointed at
    the archive: the same path under the active tree beside the signed original plan path.
    It mirrors the layout, so a folder or glob path maps the same way as a file."""
    source = archived.get("from") if isinstance(archived, dict) else None
    major, minor = minor_of(version)
    dest = ARCHIVE_TREE.format(M=major, m=minor)
    if not isinstance(source, str) or "/plans/" not in source or not path.startswith(dest + "/"):
        return None
    return source.rsplit("/plans/", 1)[0] + path[len(dest):]


def archive_task_status(rctx: RepoContext, version: str, path: str, start: str, record: dict) -> str:
    """`task.T###` in a minor where a member archive or the minor close happened.

    An archive rewrites task-line paths and shared tracker files, and its own commit
    creates or deletes them, so it must never count as anyone's task work. Git pathspec
    matching is kept (a folder or glob path matches as before); the path's original
    location is searched too, and every excluded commit of the `Landing` is dropped. A
    task line on the paths of an archive the history could not verify is `cannot-verify`.
    """
    landing = archive_landing(rctx, record)
    if landing is None:
        return "cannot-verify"
    origin = task_origin(version, path, record.get("archived"))
    specs = [path, *((origin,) if origin else ())]
    rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "log", "--format=%H", f"{start}..HEAD", "--", *specs])
    if rc != 0:
        return "cannot-verify"
    shas = set(out.split())
    if uncertain_for(landing, specs, shas):
        return "cannot-verify"
    return "met" if shas - landing.excluded else "unmet"


def archive_member_status(ck: ModuleType, rctx: RepoContext, record: dict, member: dict) -> str:
    """`<version>:archive.member` (completion contract, "Member archive").

    `n/a` without the `archive-member` approval. Met once `archive.minor` is met (the
    final archive moves every member), or when, on the integration branch, the signed
    `archived.plan_path` hashes to `archived.plan_sha256` and no active tree of the
    minor still lists a path this member owns.
    """
    if "archive-member" not in _classes(record):
        return "n/a"
    token = str(record.get("minor"))
    archived = member.get("archived")
    ref = _integration_ref(rctx, _target(record))
    if archive_entries(archived) is not None:
        # A signed member archive counts only through a verified archive commit the
        # integration branch reaches; one that landed rewritten (amended, rebased,
        # squash-merged, changed by a hook) is never read as archived.
        landing = archive_landing(rctx, record, ref) if ref else None
        version = str(member.get("version"))
        if landing is None:
            return "cannot-verify"
        if version not in landing.verified:
            landed = any(commit is None and paths == frozenset(archive_entries(archived) or {})
                         for commit, paths in landing.uncertain)
            return "cannot-verify" if landed else "unmet"
    if archive_minor_status(ck, rctx, token, record) == "met":
        return "met"
    if not isinstance(archived, dict) or not isinstance(archived.get("plan_path"), str):
        return "unmet"
    if ref is None:
        return "cannot-verify"
    rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "cat-file", "-e", f"{ref}:{archived['plan_path']}"])
    if rc == -1:
        return "cannot-verify"
    if rc != 0:
        return "unmet"
    rc, text = rctx.run([rctx.git, "-C", str(rctx.root), "show", f"{ref}:{archived['plan_path']}"])
    if rc != 0:
        return "cannot-verify"
    if ck.plan_hash_text(text) != archived.get("plan_sha256"):
        return "unmet"
    major, minor = parse_minor(ck, token)
    version = str(member.get("version"))
    for pattern in ACTIVE_TREES:
        tree = pattern.format(M=major, m=minor)
        rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "ls-tree", "-r", "--name-only", ref, "--", tree])
        if rc != 0:
            return "cannot-verify"
        tracked = [line.strip() for line in out.splitlines() if line.strip()]
        if member_moves(version, tree, tracked, archived.get("from")):
            return "unmet"
    return "met"


# --------------------------------------------------------------------------- minor verdict
#
# `check-minor` and `score-minor`. The verdicts, their precedence, the member gate,
# and every minor-level predicate are owned by the completion contract, "Minor
# verdict"; this section executes them and restates none of them.

MEMBER_BUDGET_SECONDS = 20.0  # each member's own share: the per-plan check's budget
MEMBER_MIN_SECONDS = 1.0  # below this a member is not evaluated and reads cannot-verify
CLOSE_BRANCH = "chore/close-{token}"
_MET = ("met", "deferred", "n/a")


@dataclass
class MemberResult:
    version: str
    status: str = "unmet"  # met | unmet | cannot-verify
    gate: str = "n/a"  # member.gate: met | n/a | unmet | cannot-verify
    lines: list[tuple[str, str]] = field(default_factory=list)
    exhausted: bool = False


@dataclass
class MinorVerdict:
    line: str
    code: int
    members: list[MemberResult] = field(default_factory=list)
    minor: list[tuple[str, str]] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    record: dict | None = None

    def ids(self) -> list[str]:
        """Every unmet or unverifiable id, member ids prefixed by their version."""
        out: list[str] = []
        for member in self.members:
            if member.exhausted:
                out.append(f"member.{member.version}")
                continue
            if member.gate not in _MET:
                out.append(f"{member.version}:member.gate")
            out.extend(f"{member.version}:{pid}" for pid, status in member.lines if status not in _MET)
        out.extend(pid for pid, status in self.minor if status not in _MET)
        return out

    def met(self) -> int | None:
        # A partial observation cannot establish a comparable progress score.
        if (any(m.exhausted or m.status == "cannot-verify" or m.gate == "cannot-verify"
                or any(status == "cannot-verify" for _, status in m.lines) for m in self.members)
                or any(status == "cannot-verify" for _, status in self.minor)):
            return None
        count = sum(1 for m in self.members for _, status in m.lines if status in _MET)
        count += sum(1 for m in self.members if m.gate in _MET and not m.exhausted)
        return count + sum(1 for _, status in self.minor if status in _MET)


def minor_context(ck: ModuleType, repo: str) -> RepoContext:
    return ck.RepoContext(Path(repo or ".").resolve(), ck.Budget(check_minor_seconds()))


def version_order(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.lstrip("v").split("."))


def ordered_members(record: dict) -> list[dict]:
    members = [
        m for m in record.get("members") or []
        if isinstance(m, dict) and PLAN_TOKEN_RE.match(str(m.get("version")))
    ]
    return sorted(members, key=lambda m: version_order(str(m["version"])))


def _classes(record: dict | None) -> set[str]:
    return {
        str(c.get("class")) for c in ((record or {}).get("approvals") or {}).get("classes") or []
        if isinstance(c, dict)
    }


def _target(record: dict | None) -> str:
    return str(((record or {}).get("approvals") or {}).get("target_branch") or "develop")


def _tag_in(rctx: RepoContext, tag: str, commit: str) -> str:
    """`met` when `commit` contains `tag`; `unmet` when it does not or the tag exists nowhere.

    A tag present on origin but not fetched is `cannot-verify`: fetch tags and ask again.
    """
    rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "rev-parse", "--verify", "-q", f"refs/tags/{tag}^{{commit}}"])
    if rc == -1:
        return "cannot-verify"
    if rc != 0:
        rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "ls-remote", "--tags", "origin", f"refs/tags/{tag}"])
        if rc != 0 or out.strip():
            return "cannot-verify"
        return "unmet"
    rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "merge-base", "--is-ancestor", f"refs/tags/{tag}", commit])
    return "met" if rc == 0 else "unmet" if rc == 1 else "cannot-verify"


def _ancestor(rctx: RepoContext, older: str, newer: str) -> str:
    rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "merge-base", "--is-ancestor", older, newer])
    return "met" if rc == 0 else "unmet" if rc == 1 else "cannot-verify"


def _merge_commit(ck: ModuleType, rctx: RepoContext, repo: str, branch: str) -> tuple[str, str | None]:
    """("merged", oid) | ("not-merged", None) | ("cannot-verify", None) for `branch`'s pull request."""
    data = ck._gh_json(rctx, repo, "pr", "view", branch, "--json", "state,mergeCommit")
    if data is ck.GH_NOT_FOUND:
        return "not-merged", None
    if not isinstance(data, dict):
        return "cannot-verify", None
    if data.get("state") != "MERGED":
        return "not-merged", None
    commit = data.get("mergeCommit")
    oid = commit.get("oid") if isinstance(commit, dict) else None
    return ("merged", str(oid)) if oid else ("cannot-verify", None)


GATE_VIOLATED = "violated"


def member_gate(ck: ModuleType, rctx: RepoContext, repo: str, previous: dict | None, member: dict) -> str:
    """`member.gate` for one member: `met`, `n/a`, `unmet`, `cannot-verify`, or `violated`.

    Every member after the first must have passed `record member-start`: without a
    recorded `start_head` it is `unmet`, never `n/a`, so skipping the gate can never
    reach MINOR COMPLETE. A recorded base must contain the previous member's release
    tag, and once the member's pull request is merged the base must be an ancestor
    of that merge; either failure is `violated` (the verdict is BLOCKED). The first
    member without a recorded start is `n/a`.
    """
    start = member.get("start_head")
    if not isinstance(start, str) or not start:
        return "n/a" if previous is None else "unmet"
    if previous is not None:
        tag = _tag_in(rctx, str(previous.get("tag") or previous.get("version")), start)
        if tag != "met":
            return GATE_VIOLATED if tag == "unmet" else tag
    state, merge = _merge_commit(ck, rctx, repo, str(member.get("source_branch") or ""))
    if state == "cannot-verify":
        return "cannot-verify"
    if merge:
        based = _ancestor(rctx, start, merge)
        if based != "met":
            return GATE_VIOLATED if based == "unmet" else based
    return "met"


def new_members(ck: ModuleType, rctx: RepoContext, record: dict, repo: str) -> tuple[str, str | None]:
    """(`members.approved` status, the first version added to the minor after approval)."""
    major, minor = parse_minor(ck, str(record.get("minor")))
    known = {str(m.get("version")) for m in record.get("members") or [] if isinstance(m, dict)}
    known |= {str(e.get("version")) for e in record.get("excluded") or [] if isinstance(e, dict)}
    try:
        plans = scan_plans(rctx.root, major, minor)
    except MinorMalformed:
        return "cannot-verify", None
    for plan in plans:
        # Decided by the release, never by the Status line: a Status edit is not a release.
        if plan.version in known:
            continue
        state = shipped(ck, rctx, repo, plan.version)
        if state == "met":
            continue
        if state == "cannot-verify":
            return "cannot-verify", None
        return "unmet", plan.version
    return "met", None


def evaluate_member(
    ck: ModuleType, rctx: RepoContext, record: dict, member: dict, plan: Plan, notices: list[str],
) -> MemberResult:
    """One member through `project()` and the per-plan `evaluate`, inside its own budget."""
    version = str(member["version"])
    result = MemberResult(version)
    total = rctx.budget
    if total.remaining() < MEMBER_MIN_SECONDS:
        result.status, result.exhausted = "cannot-verify", True
        notices.append(f"check-minor budget exhausted before {version}")
        return result
    budget = ck.Budget(min(MEMBER_BUDGET_SECONDS, total.remaining()))
    try:
        ctx = ck.Context(str(rctx.root / plan.rel), budget)
    except ck.Malformed:
        if budget.remaining() > 0:
            raise
        result.status, result.exhausted = "cannot-verify", True
        notices.append(f"check-minor budget exhausted in {version}")
        return result
    identity = []
    if member.get("implementation") is not None:
        ctx, status, _retired = _worker_context(ck, rctx, record, member, budget)
        identity = [("implementation.identity", status)]
        if ctx is None or status != "met":
            result.lines = identity
            result.status = "unmet" if status == "unmet" else "cannot-verify"
            return result
    results, _deferred = ck.evaluate(ctx, ck.project(record, version))
    results = identity + results
    if "archive-member" in _classes(record):
        # Only a record carrying the class reports the line, so a record without it
        # prints, scores, and completes exactly as before.
        results.append(("archive.member", archive_member_status(ck, rctx, record, member)))
    notices.extend(f"{version}: {n}" for n in ctx.notices)
    if budget.remaining() <= 0:
        notices.append(f"check-minor member budget exhausted in {version}")
    result.lines = results
    statuses = {status for _, status in results}
    result.status = "met" if statuses <= set(_MET) else "unmet" if "unmet" in statuses else "cannot-verify"
    return result


def _combine(*statuses: str) -> str:
    if all(s in _MET for s in statuses):
        return "met"
    return "unmet" if "unmet" in statuses else "cannot-verify"


def back_merged(rctx: RepoContext, target: str) -> str:
    """`met` when the live integration branch contains the live `main` tip."""
    rc, out = rctx.run(
        [rctx.git, "-C", str(rctx.root), "ls-remote", "origin", "refs/heads/main", f"refs/heads/{target}"]
    )
    if rc != 0:
        return "cannot-verify"
    tips = {ref: sha for sha, _, ref in (line.partition("\t") for line in out.splitlines())}
    main, integration = tips.get("refs/heads/main"), tips.get(f"refs/heads/{target}")
    if not main or not integration:
        return "cannot-verify"
    rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "merge-base", "--is-ancestor", main, integration])
    return "met" if rc == 0 else "unmet" if rc == 1 else "cannot-verify"


def frozen_unresolved(record: dict, ledgers: list[Ledger]) -> list[tuple[Ledger, GapItem]]:
    """Frozen migratable items that are not resolved in `ledgers`: still open, or migrated."""
    bound, _named = migration_class(record)
    return [
        (ledger, item) for ledger in ledgers for item in ledger.items
        if f"{ledger.token()}#{item.gid}" in bound and item.state != "resolved"
    ]


def close_required(record: dict, ledgers: list[Ledger]) -> bool:
    """The closing pull request is always required: it carries the archive, which every
    minor needs (Definition of Done 2), plus any migrations. `minor.close-pr` is never `n/a`."""
    return True


def close_carries(
    rctx: RepoContext, record: dict, ledgers: list[Ledger], token: str, base: str, merge: str,
) -> tuple[str, str | None]:
    """(status, missing path) for whether the closing merge brought the migrations and the archive.

    No frozen id may still be open on the integration branch. Each ledger holding a
    migrated frozen id must differ between the last member's
    release and the merge, and, when the archive is approved, something under the
    archive tree must too. When only the archive remains, only the archive is required.
    """
    unresolved = frozen_unresolved(record, ledgers)
    still_open = next((f"{ledger.token()}#{item.gid}" for ledger, item in unresolved if item.state == "open"), None)
    if still_open:
        # A merged close that leaves a frozen id open carried neither its fix nor its migration.
        return "unmet", still_open
    required = sorted({ledger.rel for ledger, item in unresolved if item.state == "migrated"})
    rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "diff", "--name-only", base, merge])
    if rc != 0:
        return "cannot-verify", None
    changed = {line.strip() for line in out.splitlines() if line.strip()}
    for rel in required:
        if rel not in changed:
            return "unmet", rel
    if "archive-minor" in _classes(record):
        prefix = ARCHIVE_TREE.format(M=minor_of(token)[0], m=minor_of(token)[1]) + "/"
        if not any(path.startswith(prefix) for path in changed):
            return "unmet", prefix
    return "met", None


def close_pr_status(
    ck: ModuleType, rctx: RepoContext, record: dict, token: str, repo: str, ledgers: list[Ledger],
    notices: list[str],
) -> str:
    """`minor.close-pr` (completion contract, "Minor verdict").

    The closing pull request merged; its merge commit is on the target branch and
    descends from both the record's `start_head` and the last member's release tag,
    so it was merged after the approval and after the last release; the merge brought
    the migrations and the archive (`close_carries`); its required checks passed; and
    main is back-merged. A branch name alone never satisfies it.
    """
    if not close_required(record, ledgers):
        return "n/a"
    if "minor-close-pr" not in _classes(record):
        notices.append("minor.close-pr needs the minor-close-pr approval")
        return "unmet"
    branch = CLOSE_BRANCH.format(token=token)
    target = _target(record)
    state, merge = _merge_commit(ck, rctx, repo, branch)
    if state != "merged" or not merge:
        return "unmet" if state == "not-merged" else "cannot-verify"
    integration = _integration_ref(rctx, target)
    members = ordered_members(record)
    if integration is None or not members:
        return "cannot-verify"
    last_tag = f"refs/tags/{members[-1].get('tag') or members[-1].get('version')}"
    checks = [_ancestor(rctx, merge, integration), _ancestor(rctx, str(record.get("start_head") or ""), merge)]
    checks.append(_ancestor(rctx, last_tag, merge))
    if "unmet" in checks:
        notices.append("minor.close-pr merge is not on the target branch after the last release")
    if all(c == "met" for c in checks):
        carried, missing = close_carries(rctx, record, ledgers, token, last_tag, merge)
        if carried == "unmet":
            notices.append(f"minor.close-pr merge does not carry {missing}")
        checks.append(carried)
    start = str(record.get("start_head") or "") or None
    checks += [ck._pr_checks(rctx, repo, branch, target, start), back_merged(rctx, target)]
    return _combine(*checks)


def last_merge_branch(record: dict, token: str, close_status: str) -> str | None:
    if close_status != "n/a":
        return CLOSE_BRANCH.format(token=token)
    members = ordered_members(record)
    return str(members[-1].get("source_branch")) if members else None


def cleanup_minor_status(
    ck: ModuleType, rctx: RepoContext, record: dict, record_path: Path, token: str, repo: str, close_status: str,
) -> str:
    """`cleanup.merged` for a minor: the sealed final-pass receipt postdates the minor's last merge."""
    if "cleanup-merged" not in _classes(record):
        return "unmet"  # the final cleanup pass is part of done, never optional
    branch = last_merge_branch(record, token, close_status)
    if not branch:
        return "cannot-verify"
    data = ck._gh_json(rctx, repo, "pr", "view", branch, "--json", "state,mergeCommit")
    if data is ck.GH_NOT_FOUND:
        return "unmet"
    if not isinstance(data, dict):
        return "cannot-verify"
    if data.get("state") != "MERGED":
        return "unmet"
    commit = data.get("mergeCommit")
    merge = commit.get("oid") if isinstance(commit, dict) else None
    try:
        import cleanup_merged  # a sibling in ~/.nexus-hub/scripts/, imported only when needed
    except ImportError:
        return "cannot-verify"
    return cleanup_merged.receipt_status(
        rctx.root, rctx.git, rctx.run, record_path, record.get("nonce"), merge, _target(record)
    )


def check_minor(ck: ModuleType, rctx: RepoContext, token: str, session: str | None) -> MinorVerdict:
    """Keep unavailable observations distinct from verified integrity conflicts."""
    rctx._minor_blob_cache = {}
    try:
        return _check_minor(ck, rctx, token, session)
    except ObservationUnavailable as exc:
        return MinorVerdict(
            f"INCOMPLETE: {exc}", ck.EXIT_INCOMPLETE, minor=[(str(exc), "cannot-verify")],
            notices=[f"{exc} observation unavailable (command failed or budget exhausted)"],
        )


def _check_minor(ck: ModuleType, rctx: RepoContext, token: str, session: str | None) -> MinorVerdict:
    """The minor verdict (completion contract, "Minor verdict")."""
    parse_minor(ck, token)
    state = load_minor(ck, rctx, token, session, accept_completed=True)
    if state.forced is not None:
        # Tampered, paused, and blocked verdicts print no predicate lines: nothing a
        # member reports can change them, and evaluating every member spends the budget.
        return MinorVerdict(state.forced[0], state.forced[1], notices=state.notices, record=state.record)
    record = state.record
    if record is None:
        return MinorVerdict(
            "INCOMPLETE: record.minor", ck.EXIT_INCOMPLETE, minor=[("record.minor", "unmet")], notices=state.notices
        )
    notices = list(state.notices)
    repo = str(record.get("repo") or hosting_repo(ck, rctx))
    major, minor = parse_minor(ck, token)
    by_version = {p.version: p for p in scan_plans(rctx.root, major, minor)}
    members = ordered_members(record)
    gates: list[str] = []
    previous: dict | None = None
    for member in members:
        gates.append(member_gate(ck, rctx, repo, previous, member))
        previous = member
    for member, gate in zip(members, gates):
        if gate == GATE_VIOLATED:
            return MinorVerdict(
                f"BLOCKED: member-gate ({member['version']})", ck.EXIT_BLOCKED, notices=notices, record=record
            )
    approved, added = new_members(ck, rctx, record, repo)
    if added:
        notices.append("a plan added after approval needs a new approval round")
        return MinorVerdict(
            f"BLOCKED: new-member-not-approved ({added})", ck.EXIT_BLOCKED, notices=notices, record=record
        )
    results: list[MemberResult] = []
    for member, gate in zip(members, gates):
        result = evaluate_member(ck, rctx, record, member, by_version[str(member["version"])], notices)
        result.gate = gate
        results.append(result)
    integration = _integration_ref(rctx, _target(record))
    loaded = load_ledgers_at(rctx, integration) if integration else None
    if loaded is None:
        notices.append("gaps.minor integration branch unreadable")
        gaps = close = "cannot-verify"
    else:
        gaps, gap_notices = gaps_minor_status(ck, rctx, token, record, loaded)
        notices.extend(gap_notices)
        close = close_pr_status(ck, rctx, record, token, repo, loaded[0], notices)
    path = record.record_path
    for name, predicate in (("cleanup-merged", "cleanup.merged"), ("archive-minor", "archive.minor")):
        if name not in _classes(record):
            notices.append(f"{predicate} needs the {name} approval")
    lines = [
        ("members.approved", approved),
        ("gaps.minor", gaps),
        ("minor.close-pr", close),
        ("cleanup.merged", cleanup_minor_status(ck, rctx, record, path, token, repo, close)),
        ("archive.minor", archive_minor_status(ck, rctx, token, record)),
    ]
    verdict = MinorVerdict("", ck.EXIT_INCOMPLETE, results, lines, notices, record)
    unmet = verdict.ids()
    if unmet:
        verdict.line = "INCOMPLETE: " + " ".join(unmet)
        return verdict
    head = rctx._git_out("rev-parse", "HEAD") or "-"
    verdict.line, verdict.code = f"MINOR COMPLETE {token} {head} {record.get('nonce', '-')}", ck.EXIT_COMPLETE
    if not record.get("completed"):
        # `completed` is signed: it ends the record's authority (contract, "Schema 2", Validity).
        record["completed"] = {"at": ck._now(), "head": head}
        record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
        ck._write_record(path, record)
    return verdict


def cmd_check_minor(ck: ModuleType, args: argparse.Namespace) -> int:
    rctx = minor_context(ck, args.repo)
    verdict = check_minor(ck, rctx, args.minor, args.session)
    for notice in [*verdict.notices, *rctx.notices]:
        print(f"notice: {notice}", file=sys.stderr)
    print(verdict.line)
    if args.json:
        head = rctx._git_out("rev-parse", "HEAD") or None
        body = {
            "verdict": verdict.line,
            "exit": verdict.code,
            # The score from this same run, so a gate never needs a second evaluation.
            "met": verdict.met() if head else None,
            "head": head,
            "members": {
                m.version: {"status": m.status, "gate": m.gate, "predicates": dict(m.lines)} for m in verdict.members
            },
            "minor": dict(verdict.minor),
        }
        print(json.dumps(body, sort_keys=True))
        return verdict.code
    for member in verdict.members:
        print(f"member.{member.version} {member.status}")
        print(f"{member.version}:member.gate {member.gate}")
        for pid, status in member.lines:
            print(f"{member.version}:{pid} {status}")
    for pid, status in verdict.minor:
        print(f"{pid} {status}")
    return verdict.code


def score_branch(record: dict | None, verdict: MinorVerdict, token: str) -> str | None:
    """The branch whose latest CI run the score names: the first unfinished member's, else the closing branch."""
    if record is None:
        return None
    by_version = {str(m.get("version")): m for m in ordered_members(record)}
    for member in verdict.members:
        if member.status != "met":
            return str(by_version.get(member.version, {}).get("source_branch") or "") or None
    return CLOSE_BRANCH.format(token=token)


def cmd_score_minor(ck: ModuleType, args: argparse.Namespace) -> int:
    """`<met-count> <head> <latest-ci-run-id|->`, summed over members and the minor-level lines."""
    rctx = minor_context(ck, args.repo)
    verdict = check_minor(ck, rctx, args.minor, args.session)
    head = rctx._git_out("rev-parse", "HEAD")
    met = verdict.met()
    if met is None or not head:
        print("INCOMPLETE: progress.score")
        return ck.EXIT_INCOMPLETE
    record = verdict.record
    branch = score_branch(record, verdict, args.minor)
    run_id = "-"
    if branch and record is not None:
        runs = ck._gh_json(
            rctx, str(record.get("repo") or ""), "run", "list", "--branch", branch, "--limit", "1", "--json", "databaseId"
        )
        if isinstance(runs, list) and runs and isinstance(runs[0], dict) and "databaseId" in runs[0]:
            run_id = str(runs[0]["databaseId"])
    print(f"{met} {head} {run_id}")
    return 0


# --------------------------------------------------------------------------- member gate and blockers


def _ls_remote_tip(rctx: RepoContext, branch: str) -> str | None:
    rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "ls-remote", "origin", f"refs/heads/{branch}"])
    if rc != 0:
        return None
    tips = (line.partition("\t") for line in out.splitlines())
    return next((sha for sha, _, ref in tips if ref == f"refs/heads/{branch}"), "")


def _gate_refusal(ck: ModuleType, version: str, reason: str) -> int:
    print(f"BLOCKED: member-gate ({version})")
    print(f"reason: {reason}")
    return ck.EXIT_BLOCKED


@minor_writer
def cmd_record_member_start(ck: ModuleType, args: argparse.Namespace) -> int:
    """Pass the member gate and record the member's `start_head`, re-signing the record.

    Refuses (exit 3, `BLOCKED: member-gate (vX.Y.Z)` and a fixed reason) unless the
    predecessor predicates other than cleanup pass, the local `origin/<target>` equals the live
    remote tip (the caller fetched), that tip contains the previous member's release
    tag (main was back-merged), and `--head`, when given, is that tip. Idempotent for
    an unchanged `start_head`; a different one is refused, because moving a member's
    base after it started would hide work done on the stale one.
    """
    rctx = repo_context(ck, args)
    token, version = args.minor, args.member
    parse_minor(ck, token)
    if not PLAN_TOKEN_RE.match(version or ""):
        raise ck.Malformed("--member must be a plan version such as v0.5.2")
    state = load_minor(ck, rctx, token, args.session)
    if state.forced is not None:
        print(state.forced[0])
        return state.forced[1]
    record = state.record
    if record is None:
        for notice in state.notices:
            print(f"notice: {notice}", file=sys.stderr)
        print("no minor run record for this scope and session", file=sys.stderr)
        return ck.EXIT_MALFORMED
    members = ordered_members(record)
    index = next((i for i, m in enumerate(members) if m.get("version") == version), None)
    if index is None:
        raise ck.Malformed(f"{version} is not a member of {token}")
    member = members[index]
    target = _target(record)
    tip = _ls_remote_tip(rctx, target)
    if not tip:
        return _gate_refusal(ck, version, "integration-branch-unreadable")
    if rctx._git_out("rev-parse", "--verify", "-q", f"refs/remotes/origin/{target}") != tip:
        return _gate_refusal(ck, version, "fetch-stale")
    if args.head and rctx._git_out("rev-parse", "--verify", "-q", f"{args.head}^{{commit}}") != tip:
        return _gate_refusal(ck, version, "head-not-integration-tip")
    if index > 0:
        previous = members[index - 1]
        major, minor = parse_minor(ck, token)
        plan = {p.version: p for p in scan_plans(rctx.root, major, minor)}[str(previous["version"])]
        result = evaluate_member(ck, rctx, record, previous, plan, [])
        previous_gate = member_gate(ck, rctx, str(record["repo"]), members[index - 2] if index > 1 else None, previous)
        if previous_gate not in _MET or not result.lines or any(
            status not in _MET for predicate, status in result.lines
            if not predicate.startswith(("cleanup.", "archive."))
        ):
            return _gate_refusal(ck, version, f"previous-member-incomplete ({previous['version']})")
        if _tag_in(rctx, str(previous.get("tag") or previous["version"]), tip) != "met":
            return _gate_refusal(ck, version, "back-merge-missing")
    coordinator_paths = member.get("coordinator_paths", [])
    if getattr(args, "coordinator_claims", None):
        if not member.get("implementation"):
            return _gate_refusal(ck, version, "coordinator-claims-require-implementation")
        try:
            value = json.loads(Path(args.coordinator_claims).read_text(encoding="utf-8"))
            proposed = _coordinator_claims(ck, rctx, record, member, value)
        except (OSError, ValueError, MinorMalformed):
            return _gate_refusal(ck, version, "invalid-coordinator-claims")
        if member.get("start_head") and proposed != coordinator_paths:
            return _gate_refusal(ck, version, "coordinator-claims-already-recorded")
        if _coordinator_conflict(ck, rctx, record, member, proposed, tip):
            return _gate_refusal(ck, version, "coordinator-scope-conflict")
        coordinator_paths = proposed
    if member.get("implementation") is not None:
        candidate = {**member, "start_head": tip, "coordinator_paths": coordinator_paths}
        worker, status, _ = _worker_context(ck, rctx, record, candidate, rctx.budget, base=tip, canonical_merged=False)
        if worker is None or status != "met":
            return _gate_refusal(ck, version, "implementation-worktree-unverified")
    existing = member.get("start_head")
    if existing:
        if existing == tip:
            print(f"STARTED {version} start_head={tip}")
            return 0
        return _gate_refusal(ck, version, "already-started")
    member["start_head"] = tip
    member["started"] = ck._now()
    if coordinator_paths:
        member["coordinator_paths"] = coordinator_paths
    # `members` is signed, so the gate's write is a signed update, never an unsigned edit.
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    ck._write_record(record_file(ck, rctx, token), record)
    print(f"STARTED {version} start_head={tip}")
    return 0


# --------------------------------------------------------------------------- parallel implementation admission


def _common_dir(rctx: RepoContext, root: Path) -> str:
    rc, out = rctx.run([rctx.git, "-C", str(root), "rev-parse", "--git-common-dir"])
    if rc == -1:
        raise ObservationUnavailable("controller.ownership")
    if rc or not out.strip():
        return ""
    path = Path(out.strip())
    return str((path if path.is_absolute() else root / path).resolve())


def _controller_valid(rctx: RepoContext, record: dict) -> bool:
    binding = record.get("implementation_controller")
    if binding is None:
        return True  # Existing minor records keep their original signature and behavior.
    return (
        isinstance(binding, dict)
        and binding.get("repo_root") == str(rctx.root)
        and binding.get("git_common_dir") == _common_dir(rctx, rctx.root)
    )


def _literal_path(root: Path, value: object) -> str:
    """Canonical literal claims; directory claims have an explicit trailing slash."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise MinorMalformed("invalid-implementation-path")
    if "\\" in value or any(c in value for c in ":*?[]") or any(ord(c) < 32 for c in value):
        raise MinorMalformed("invalid-implementation-path")
    parts = value.rstrip("/").split("/")
    if value != "/".join(parts) + ("/" if value.endswith("/") else ""):
        raise MinorMalformed("invalid-implementation-path")
    if any(not p or p in (".", "..") or p.endswith((".", " ")) for p in parts):
        raise MinorMalformed("invalid-implementation-path")
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
    if any(p.split(".")[0].casefold() in reserved or p.casefold() == ".git" for p in parts):
        raise MinorMalformed("invalid-implementation-path")
    path = root
    for part in parts:
        if path.is_dir():
            aliases = [p.name for p in path.iterdir() if p.name.casefold() == part.casefold()]
            if aliases and part not in aliases:
                raise MinorMalformed("implementation-path-alias")
        path = path / part
        if path.is_symlink() or path.resolve() != path.absolute():
            raise MinorMalformed("implementation-path-alias")
    if path.is_dir() != value.endswith("/") and path.exists():
        raise MinorMalformed("implementation-path-kind")
    return value


def _overlap(left: str, right: str) -> bool:
    a, b = left.casefold(), right.casefold()
    return a.rstrip("/") == b.rstrip("/") or (a.endswith("/") and b.startswith(a)) or (b.endswith("/") and a.startswith(b))


def _coordinator_paths(rctx: RepoContext, token: str, tracked: list[str] | None = None) -> list[str]:
    major, minor = (int(p) for p in token[1:].split("."))
    fixed = [".nexus-hub/", "docs/todos.md", "CHANGELOG.md", "RELEASE_NOTES.md", "DEVLOG.md",
             "VERSION", "version.txt", "package.json", "package-lock.json", "pyproject.toml", ".bumpversion.cfg",
             "README.md", "AGENTS.md", "CLAUDE.md", "docs/README.md", "docs/DEVLOG.md",
             "data/skills.json", "data/SKILL_INDEX.md", "data/marketplace.json", "data/bundles.json",
             ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"]
    fixed += ledger_rels(major, minor)
    if tracked is None:
        tracked = rctx._git_out("ls-files", "-z").split("\0")
    return fixed + [p for p in tracked if p and _coordinator_name(p)]


def _coordinator_name(path: str) -> bool:
    name = path.rstrip("/").rsplit("/", 1)[-1].casefold()
    return "known-gaps" in name or name in {"changelog.md", "release_notes.md", "release-notes.md", "version", "version.txt"}



def _sensitive_name(path: str) -> bool:
    parts = path.casefold().rstrip("/").split("/")
    name = parts[-1]
    return (
        any(p in {"secrets", "credentials", ".ssh", ".aws", ".azure"} for p in parts)
        or name == ".env" or name.startswith(".env.")
        or name in {"id_rsa", "id_ed25519", "secrets.json", "credentials.json"}
        or (path.casefold().startswith("configs/") and any(p in name for p in ("permission", "secret", "credential")))
    )


def _sensitive_write(rctx: RepoContext, path: str, tracked: list[str] | None = None) -> bool:
    protected = [".github/", "configs/permissions/", ".nexus-hub/", ".pre-commit-config.yaml",
                 ".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml", "catalog/hooks/settings.json"]
    if tracked is None:
        tracked = rctx._git_out("ls-files", "-z").split("\0")
    return _sensitive_name(path) or any(_overlap(path, p) for p in [*protected, *(p for p in tracked if p and _sensitive_name(p))])


def _claims(rctx: RepoContext, token: str, root: Path, value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {"depends_on", "read_paths", "write_paths"}:
        raise MinorMalformed("invalid-implementation-claims")
    result = {}
    for key in ("depends_on", "read_paths", "write_paths"):
        paths = value[key]
        if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
            raise MinorMalformed("invalid-implementation-claims")
        if len({p.casefold() for p in paths}) != len(paths):
            raise MinorMalformed("duplicate-implementation-claim")
        result[key] = sorted(paths) if key == "depends_on" else sorted(_literal_path(root, p) for p in paths)
    if not result["write_paths"]:
        raise MinorMalformed("empty-implementation-write-scope")
    tracked = rctx._git_out("ls-files", "-z").split("\0")
    if any(_sensitive_write(rctx, p, tracked) for p in result["write_paths"]):
        raise MinorMalformed("sensitive-implementation-path")
    protected = _coordinator_paths(rctx, token, tracked)
    if any(_coordinator_name(p) or any(_overlap(p, q) for q in protected) for p in result["write_paths"]):
        raise MinorMalformed("coordinator-owned-path")
    return result


def _implementation_paths(ctx: RepoContext, member: dict, base: str | None = None) -> str:
    implementation = member["implementation"]
    start = base or member.get("start_head") or implementation["base_head"]
    if not base:
        integration = _integration_ref(ctx, str(member.get("target_branch") or "develop"))
        if integration:
            refreshed = ctx._git_out("merge-base", "HEAD", integration)
            if refreshed and _ancestor(ctx, implementation["base_head"], refreshed) == "met" and (
                not member.get("start_head") or _ancestor(ctx, member["start_head"], refreshed) == "met"
            ):
                start = refreshed
    if _ancestor(ctx, start, "HEAD") != "met":
        return "cannot-verify"
    paths = set()
    for args in (("diff", "--name-only", "--no-renames", "-z", start, "HEAD", "--"),
                 ("diff", "--name-only", "--no-renames", "-z", "HEAD", "--"),
                 ("diff", "--cached", "--name-only", "--no-renames", "-z", "HEAD", "--"),
                 ("ls-files", "--others", "--exclude-standard", "-z")):
        rc, out = ctx.run([ctx.git, "-C", str(ctx.root), *args])
        if rc:
            return "cannot-verify"
        paths.update(p for p in out.split("\0") if p)
    writes = [*implementation["write_paths"], *(member.get("coordinator_paths", []) if member.get("start_head") else [])]
    try:
        for path in paths:
            _literal_path(ctx.root, path + "/" if (ctx.root / path).is_dir() else path)
            if _sensitive_write(ctx, path, []) or (_coordinator_name(path) and path not in member.get("coordinator_paths", [])):
                return "unmet"
            if not any(_overlap(path, claim) for claim in writes):
                return "unmet"
    except (MinorMalformed, OSError, ValueError):
        return "cannot-verify"
    return "met"



def archive_entries(archived: object) -> dict[str, str | None] | None:
    """Path -> the blob id a signed member archive's commit leaves there (None: deleted), or None.

    Each signed `moved` entry is `[old, new, new-side blob id]`; a repaired file that did
    not move is `[path, path, blob]`. An entry without its blob id cannot be verified.
    """
    pairs = archived.get("moved") if isinstance(archived, dict) else None
    if not isinstance(pairs, list) or not pairs:
        return None
    entries: dict[str, str | None] = {}
    for pair in pairs:
        if not isinstance(pair, list) or len(pair) != 3 or not all(isinstance(p, str) and p for p in pair):
            return None
        old, new, blob = pair
        entries[new] = blob
        if old != new:
            entries.setdefault(old, None)
    return entries


def _archive_sources(record: dict | None) -> list[dict]:
    return [m for m in (record or {}).get("members") or (record or {}).get("member_archives") or [] if isinstance(m, dict)]


def _archive_items(record: dict | None, exclude: str | None = None) -> list[tuple[str, dict[str, str | None], str]]:
    """(version, entries, signed archived plan path) of every verifiable signed member archive."""
    items = []
    for member in _archive_sources(record):
        archived = member.get("archived")
        entries = archive_entries(archived)
        if entries is not None and member.get("version") != exclude:
            items.append((str(member.get("version")), entries, str(archived.get("plan_path") or "")))
    return items


def signed_archives(record: dict | None, exclude: str | None = None) -> list[dict[str, str | None]]:
    """The verifiable signed member archives of a record (its `members`) or of a member view
    (its `member_archives`), except `exclude`'s."""
    return [entries for _version, entries, _plan in _archive_items(record, exclude)]


def close_commits(record: dict | None) -> set[str]:
    """Every signed `archived.close_commit` (the minor close's archive commit) of a record or view."""
    commits = set()
    for member in [*_archive_sources(record), record or {}]:
        archived = member.get("archived")
        if isinstance(archived, dict) and isinstance(archived.get("close_commit"), str) and archived["close_commit"]:
            commits.add(archived["close_commit"])
    return commits


def archive_active(record: dict | None) -> bool:
    """True when any member of the record (or view) carries a signed `archived` identity."""
    return (any(isinstance(m.get("archived"), dict) for m in _archive_sources(record))
            or isinstance((record or {}).get("archived"), dict))


def _memo(rctx: RepoContext, name: str) -> dict:
    return rctx.__dict__.setdefault(name, {})


def commit_changes(rctx: RepoContext, span: str, *, first_parent: bool = False) -> list[tuple[str, int, frozenset[str]]] | None:
    """(commit, parent count, changed paths without rename detection) for every commit in `span`.

    With `first_parent`, only the first-parent chain, each merge listing what it changed
    against its first parent. Read with `-z`, so no path is ever C-quoted. Memoized on
    the context, so one evaluation shares one log.
    """
    cache = _memo(rctx, "_commit_changes")
    key = (span, first_parent)
    if key not in cache:
        extra = ["--first-parent", "--diff-merges=first-parent"] if first_parent else []
        rc, out = rctx.run([rctx.git, "-c", "core.quotePath=false", "-C", str(rctx.root), "log", *extra,
                            "--no-renames", "--name-only", "-z", "--format=@@%H %P", span, "--"])
        found: list[tuple[list[str], set[str]]] = []  # ([commit, parents...], changed paths)
        for token in out.split("\0") if rc == 0 else []:
            token = token.lstrip("\n")
            if token.startswith("@@"):
                found.append((token[2:].split(), set()))
            elif token and found:
                found[-1][1].add(token)
        cache[key] = None if rc != 0 else [(ids[0], len(ids) - 1, frozenset(p)) for ids, p in found if ids]
    return cache[key]


def raw_changes(rctx: RepoContext, *revs: str) -> dict[str, str] | None:
    """Path -> new blob id (all zeros when deleted) of one commit against its parent, or of `old new`."""
    cache = _memo(rctx, "_raw_changes")
    if revs not in cache:
        rc, out = rctx.run([rctx.git, "-c", "core.quotePath=false", "-C", str(rctx.root), "diff-tree",
                            "--no-commit-id", "--raw", "-r", "--no-renames", "-z", *revs])
        fields = out.split("\0") if rc == 0 else []
        changes: dict[str, str] = {}
        for index in range(0, len(fields) - 1, 2):
            meta, path = fields[index].split(), fields[index + 1]
            if len(meta) >= 5 and path:
                changes[path] = meta[3]
        cache[revs] = changes if rc == 0 else None
    return cache[revs]


def _content_ok(blob: str, expected: str | None) -> bool:
    return (expected is None and set(blob) == {"0"}) or (expected is not None and blob == expected)


def _archive_match(rctx: RepoContext, sha: str, parents: int, archives: list[dict[str, str | None]]) -> int | None:
    """The index of the signed archive `sha` carries exactly, file for file and blob for blob, or None."""
    if parents != 1 or not archives:
        return None
    raw = raw_changes(rctx, sha)
    if not raw:
        return None
    for index, entries in enumerate(archives):
        if set(raw) == set(entries) and all(_content_ok(raw[p], entries[p]) for p in raw):
            return index
    return None


def is_archive_commit(rctx: RepoContext, sha: str, parents: int, archives: list[dict[str, str | None]]) -> bool:
    """A verified member-archive commit: one parent, and exactly the paths and blob ids one signed
    archive names (each moved file at its signed new-side blob, each old path deleted).

    Recognized by content, never by name or message, so a commit that touches the same
    files with other content, or a signed identity whose commit never landed (a crash
    between signing and committing), is never one.
    """
    return _archive_match(rctx, sha, parents, archives) is not None


def _merge_sides(rctx: RepoContext, sha: str, parents: int) -> list[tuple[str, int, frozenset[str]]] | None:
    """Every commit a merge brings beside its first parent (all its other parents), or None."""
    side: list[tuple[str, int, frozenset[str]]] = []
    for index in range(2, parents + 1):
        found = commit_changes(rctx, f"{sha}^1..{sha}^{index}")
        if found is None:
            return None
        side += found
    return side


def merge_status(rctx: RepoContext, sha: str, parents: int, archives: list[dict[str, str | None]]) -> str:
    """`archive`, `uncertain`, or `other` for one commit read as a merge carrying member archives.

    `other`: some commit its other parents bring is not a verified archive commit, so it is
    judged like any merge. When they all are: `archive` when the merge adds nothing of its
    own (every changed blob is one those commits wrote, or, for a two-parent merge, its tree
    equals the clean automatic merge `git merge-tree --write-tree`, which covers an archive
    merged after a concurrent edit to a repaired shared file); otherwise `uncertain`
    (a different tree, a conflict, merge-tree unavailable, or an octopus merge), so a task
    line on the archive's signed paths reads cannot-verify and never counts the merge.
    """
    if parents < 2 or not archives:
        return "other"
    cache = _memo(rctx, "_merge_status")
    key = (sha, json.dumps(archives, sort_keys=True))
    if key in cache:
        return cache[key]
    side = _merge_sides(rctx, sha, parents)
    status = "other"
    if side and all(is_archive_commit(rctx, c, p, archives) for c, p, _changed in side):
        written: dict[str, set[str]] = {}
        for commit, _parents, _changed in side:
            for path, blob in (raw_changes(rctx, commit) or {}).items():
                written.setdefault(path, set()).add(blob)
        raw = raw_changes(rctx, f"{sha}^1", sha)
        status = "uncertain"
        if raw and all(blob in written.get(path, set()) for path, blob in raw.items()):
            status = "archive"
        elif parents == 2:
            # Writes the merged objects to the object store and may run configured merge drivers.
            rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "merge-tree", "--write-tree", f"{sha}^1", f"{sha}^2"])
            tree = out.splitlines()[0].strip() if rc == 0 and out.strip() else ""
            if rc == 0 and tree and tree == rctx._git_out("rev-parse", f"{sha}^{{tree}}"):
                status = "archive"
    cache[key] = status
    return status


def is_archive_merge(rctx: RepoContext, sha: str, parents: int, archives: list[dict[str, str | None]]) -> bool:
    """A verified archive merge (see `merge_status`)."""
    return merge_status(rctx, sha, parents, archives) == "archive"


@dataclass
class Landing:
    """How the signed archives landed in the history a ref reaches (contract, "Member archive").

    `excluded`: commits no task line may count (verified archive commits and merges, and the
    signed close commits). `uncertain`: (commit or None, paths) whose archive could not be
    verified, so a task line on those paths is `cannot-verify`: a merge merge-tree could not
    judge, or a signed archive whose plan sits in the tree with no verified commit reachable
    (amended, rebased, squash-merged, or rewritten by a hook). `verified`: versions whose
    archive commit is reachable.
    """

    excluded: set[str] = field(default_factory=set)
    uncertain: list[tuple[str | None, frozenset[str]]] = field(default_factory=list)
    verified: set[str] = field(default_factory=set)


_LANDINGS: dict[tuple, Landing | None] = {}  # one per repository, span, and signed archive set


def archive_landing(rctx: RepoContext, record: dict | None, ref: str = "HEAD") -> Landing | None:
    """The `Landing` of the record's signed archives in `<minor start>..<ref>`, or None when git cannot answer.

    Computed once per repository, span, and signed archive set for the whole process, so
    every task line and every member of one verdict share it.
    """
    items = _archive_items(record)
    closes = close_commits(record)
    if not items:
        return Landing(excluded=set(closes))
    base = str((record or {}).get("minor_start_head") or (record or {}).get("start_head") or "")
    head = rctx._git_out("rev-parse", "--verify", "-q", f"{ref}^{{commit}}")
    if not base or not head:
        return None
    key = (str(rctx.root), base, head, json.dumps([items, sorted(closes)], sort_keys=True))
    if key in _LANDINGS:
        return _LANDINGS[key]
    commits = commit_changes(rctx, f"{base}..{head}")
    landing: Landing | None = None
    if commits is not None:
        archives = [entries for _version, entries, _plan in items]
        keys = [frozenset(entries) for entries in archives]
        landing = Landing(excluded=set(closes))
        for sha, parents, changed in commits:
            if parents == 1 and changed in keys:
                index = _archive_match(rctx, sha, parents, archives)
                if index is not None:
                    landing.excluded.add(sha)
                    landing.verified.add(items[index][0])
            elif parents >= 2:
                status = merge_status(rctx, sha, parents, archives)
                if status == "archive":
                    landing.excluded.add(sha)
                elif status == "uncertain":
                    side = _merge_sides(rctx, sha, parents) or []
                    landing.uncertain.append((sha, frozenset(p for _c, _n, changed in side for p in changed)))
        for version, entries, plan in items:
            if version in landing.verified:
                continue
            rc, _ = rctx.run([rctx.git, "-C", str(rctx.root), "cat-file", "-e", f"{head}:{plan}"])
            if rc == -1:
                landing = None
                break
            if plan and rc == 0:  # the archive landed, but no verified commit carries it
                landing.uncertain.append((None, frozenset(entries)))
    if landing is None or rctx.budget.remaining() <= 0:
        # A git call that did not run (rc -1, the budget spent) may have misread a commit:
        # never trust or cache that landing.
        return None
    _LANDINGS[key] = landing
    return landing


def excluded_commits(rctx: RepoContext, record: dict | None, span: str) -> set[str] | None:
    """Every commit a task line must never count (see `Landing`); `span` is kept for callers."""
    landing = archive_landing(rctx, record)
    return None if landing is None else landing.excluded


def spec_matches(spec: str, path: str) -> bool:
    """Git's default pathspec meaning: the path itself, a folder prefix, or an fnmatch glob."""
    bare = spec.rstrip("/")
    if path == bare or path.startswith(bare + "/"):
        return True
    return any(c in spec for c in "*?[") and fnmatch.fnmatchcase(path, spec)


def uncertain_for(landing: Landing, specs: list[str], shas: set[str]) -> bool:
    """True when a task line on `specs` touches an archive the history could not verify."""
    for commit, paths in landing.uncertain:
        if commit is not None and commit not in shas:
            continue
        if any(spec_matches(spec, path) for spec in specs for path in paths):
            return True
    return False


def _archive_only_paths(rctx: RepoContext, record: dict | None, member: dict, base: str, merge: str) -> set[str] | None:
    """Paths that only another member's verified archive commits changed in `base..merge`.

    The span's first-parent chain is walked, a merge read against its first parent and
    counted as archive work only when it is a verified archive merge, so an archive that
    landed through a merge commit is recognized. A path some other commit also touched
    is never left out, so a later member that writes a coordinator file or a moved path
    is audited as usual.
    """
    archives = signed_archives(record, str(member.get("version")))
    if not archives:
        return set()
    commits = commit_changes(rctx, f"{base}..{merge}", first_parent=True)
    if commits is None:
        return None
    touched: dict[str, bool] = {}
    for sha, parents, changed in commits:
        archive = (is_archive_commit(rctx, sha, parents, archives) if parents == 1
                   else is_archive_merge(rctx, sha, parents, archives))
        for path in changed:
            touched[path] = touched.get(path, True) and archive
    return {path for path, only in touched.items() if only}


def _historical_claim_status(rctx: RepoContext, member: dict, merge: str, record: dict | None = None) -> str:
    """Audit the actual merged contribution before releasing a reservation.

    A two-parent merge is compared to its integration parent, including merge
    resolution edits. Single-parent histories conservatively retain the whole
    publication span because a squash and a multi-commit fast-forward cannot be
    distinguished reliably from the last commit alone. In such a span, a path that only
    other members' verified archive commits changed is the coordinator's, not this
    member's, so it is left out (completion contract, "Member archive"); a two-parent
    merge already excludes those commits through its integration parent.
    """
    implementation = member.get("implementation")
    if not isinstance(implementation, dict):
        return "met"
    start = member.get("start_head") or implementation.get("base_head")
    if not isinstance(start, str) or _ancestor(rctx, start, merge) != "met":
        return "cannot-verify"
    parents = rctx._git_out("rev-list", "--parents", "-n", "1", merge).split()
    if not parents:
        return "cannot-verify"
    base = start
    if len(parents) == 3:
        if any(_ancestor(rctx, start, parent) != "met" for parent in parents[1:]):
            return "cannot-verify"
        base = parents[1]
    rc, out = rctx.run([rctx.git, "-C", str(rctx.root), "diff", "--name-only", "--no-renames", "-z", base, merge, "--"])
    if rc:
        return "cannot-verify"
    try:
        writes = [*implementation["write_paths"], *(member.get("coordinator_paths", []) if member.get("start_head") else [])]
        if any(not isinstance(p, str) for p in writes):
            return "cannot-verify"
        archived = _archive_only_paths(rctx, record, member, base, merge) if len(parents) == 2 else set()
        if archived is None:
            return "cannot-verify"
        for path in (p for p in out.split("\0") if p and p not in archived):
            _literal_path(rctx.root, path + "/" if (rctx.root / path).is_dir() else path)
            if _sensitive_write(rctx, path, []) or (_coordinator_name(path) and path not in member.get("coordinator_paths", [])):
                return "unmet"
            if not any(_overlap(path, claim) for claim in writes):
                return "unmet"
    except (KeyError, TypeError, ValueError, OSError, MinorMalformed):
        return "cannot-verify"
    return "met"


def _merged_on_base(ck: ModuleType, rctx: RepoContext, record: dict, member: dict, base: str) -> bool:
    state, merge = _merge_commit(ck, rctx, str(record["repo"]), str(member["source_branch"]))
    return (state == "merged" and bool(merge) and _ancestor(rctx, str(merge), base) == "met"
            and _historical_claim_status(rctx, member, str(merge), record) == "met")


def _worker_context(ck: ModuleType, rctx: RepoContext, record: dict, member: dict, budget: object,
                    *, base: str | None = None, canonical_merged: bool = True) -> tuple[object | None, str, bool]:
    """Validate live identity before using a worker; merged evidence lives on the controller."""
    implementation = member.get("implementation")
    if not isinstance(implementation, dict) or not _controller_valid(rctx, record):
        return None, "cannot-verify", False
    try:
        required = {"base_head", "worktree", "branch", "depends_on", "read_paths", "write_paths", "started"}
        if set(implementation) != required or implementation["branch"] != member["source_branch"]:
            return None, "cannot-verify", False
        frozen_base = implementation["base_head"]
        if not isinstance(frozen_base, str) or not re.fullmatch(r"[0-9a-f]{40,64}", frozen_base):
            return None, "cannot-verify", False
        integration = _integration_ref(rctx, _target(record))
        merge_status, merge = _merge_commit(ck, rctx, str(record["repo"]), str(member["source_branch"]))
        if canonical_merged and integration and merge_status == "merged" and merge and _ancestor(rctx, merge, integration) == "met":
            historical = _historical_claim_status(rctx, member, merge, record)
            if historical != "met":
                return None, historical, True
            if _ancestor(rctx, merge, "HEAD") != "met":
                return None, "cannot-verify", True
            plans = scan_plans(rctx.root, *parse_minor(ck, str(record["minor"])))
            plan = next((p for p in plans if p.version == member["version"]), None)
            if plan is None or not member_identity_ok(ck, member, plan):
                return None, "cannot-verify", True
            return ck.Context(str(rctx.root / plan.rel), budget), "met", True
        raw = Path(implementation["worktree"])
        root = raw.resolve()
        if not raw.is_absolute() or raw != root or root == rctx.root or not root.is_dir():
            return None, "cannot-verify", False
        if any(p.is_symlink() for p in [raw, *raw.parents]):
            return None, "cannot-verify", False
        if _common_dir(rctx, root) != _common_dir(rctx, rctx.root):
            return None, "cannot-verify", False
        rc, listing = rctx.run([rctx.git, "-C", str(rctx.root), "worktree", "list", "--porcelain", "-z"])
        registered = [block.split("\0")[0][9:] for block in listing.split("\0\0") if block.startswith("worktree ")]
        if rc or str(root).replace("\\", "/").casefold() not in {p.replace("\\", "/").casefold() for p in registered}:
            return None, "cannot-verify", False
        rc, branch = rctx.run([rctx.git, "-C", str(root), "symbolic-ref", "--quiet", "--short", "HEAD"])
        if rc or branch.strip() != member["source_branch"]:
            return None, "cannot-verify", False
        claims = {key: implementation[key] for key in ("depends_on", "read_paths", "write_paths")}
        if _claims(rctx, str(record["minor"]), root, claims) != claims:
            return None, "cannot-verify", False
        plans = scan_plans(root, *parse_minor(ck, str(record["minor"])))
        plan = next((p for p in plans if p.version == member["version"]), None)
        if plan is None or not member_identity_ok(ck, member, plan):
            return None, "cannot-verify", False
        ctx = ck.Context(str(root / plan.rel), budget)
        if _ancestor(ctx, str(record["start_head"]), frozen_base) != "met":
            return None, "cannot-verify", False
        status = _implementation_paths(ctx, member, base)
        return ctx, status, False
    except (KeyError, TypeError, ValueError, OSError, MinorMalformed, ck.Malformed):
        return None, "cannot-verify", False


def _dependencies(ck: ModuleType, rctx: RepoContext, record: dict, version: str, claims: dict, base: str) -> str | None:
    members = {str(m["version"]): m for m in ordered_members(record)}
    graph = {v: (m.get("implementation") or {}).get("depends_on", []) for v, m in members.items()}
    graph[version] = claims["depends_on"]
    for owner, dependencies in graph.items():
        if not isinstance(dependencies, list) or any(not isinstance(d, str) or d not in members or d == owner for d in dependencies):
            return "invalid-implementation-dependency"
    active, done = set(), set()

    def visit(node: str) -> bool:
        if node in active:
            return False
        if node in done:
            return True
        active.add(node)
        if not all(visit(d) for d in graph[node]):
            return False
        active.remove(node)
        done.add(node)
        return True

    if not all(visit(v) for v in graph):
        return "cyclic-implementation-dependency"
    if any(not _merged_on_base(ck, rctx, record, members[d], base) for d in claims["depends_on"]):
        return "implementation-dependency-unmerged"
    return None



def _coordinator_claims(ck: ModuleType, rctx: RepoContext, record: dict, member: dict, value: object) -> list[str]:
    """Explicit publication-only file claims; never a broader worker grant."""
    if not isinstance(value, dict) or set(value) != {"write_paths"} or not isinstance(value["write_paths"], list):
        raise MinorMalformed("invalid-coordinator-claims")
    paths = sorted(_literal_path(rctx.root, p) for p in value["write_paths"])
    if len({p.casefold() for p in paths}) != len(paths) or any(p.endswith("/") for p in paths):
        raise MinorMalformed("invalid-coordinator-claims")
    plans = scan_plans(rctx.root, *parse_minor(ck, str(record["minor"])))
    plan = next(p for p in plans if p.version == member["version"])
    protected = _coordinator_paths(rctx, str(record["minor"]))
    for path in paths:
        lower = path.casefold()
        if _sensitive_write(rctx, path) or lower.startswith("catalog/hooks/"):
            raise MinorMalformed("coordinator-sensitive-path")
        if path not in protected and not _coordinator_name(path) and not re.search(r"(?<![A-Za-z0-9_./-])" + re.escape(path) + r"(?![A-Za-z0-9_./-])", plan.text):
            raise MinorMalformed("coordinator-path-outside-plan")
    return paths


def _coordinator_conflict(ck: ModuleType, rctx: RepoContext, record: dict, member: dict, paths: list[str], base: str) -> bool:
    for other in ordered_members(record):
        if other["version"] == member["version"] or _merged_on_base(ck, rctx, record, other, base):
            continue
        claims = other.get("implementation")
        if claims:
            _ctx, status, _retired = _worker_context(ck, rctx, record, other, rctx.budget, canonical_merged=False)
            if status != "met" or any(_overlap(p, q) for p in paths for q in [*claims["read_paths"], *claims["write_paths"], *other.get("coordinator_paths", [])]):
                return True
        else:
            branch = rctx._git_out("rev-parse", "--verify", "-q", f"refs/heads/{other['source_branch']}^{{commit}}")
            if other.get("start_head") or (branch and _ancestor(rctx, branch, base) != "met"):
                return True
    return False


def _implementation_refusal(ck: ModuleType, version: str, reason: str) -> int:
    print(f"BLOCKED: member-implementation ({version})")
    print(f"reason: {reason}")
    return ck.EXIT_BLOCKED


@minor_writer
def cmd_record_member_implement_start(ck: ModuleType, args: argparse.Namespace) -> int:
    """Reserve explicit scopes for one approved linked worktree, independently of release order."""
    rctx = repo_context(ck, args)
    token, version = args.minor, args.member
    parse_minor(ck, token)
    state = load_minor(ck, rctx, token, args.session)
    if state.forced:
        print(state.forced[0])
        return state.forced[1]
    record = state.record
    if record is None:
        raise ck.Malformed("no minor run record for this scope and session")
    member = next((m for m in ordered_members(record) if m["version"] == version), None)
    if member is None:
        raise ck.Malformed(f"{version} is not a member of {token}")
    if not _controller_valid(rctx, record):
        return _implementation_refusal(ck, version, "controller-identity-mismatch")
    try:
        raw = Path(args.worktree)
        root = raw.resolve()
        if not raw.is_absolute() or raw != root:
            raise MinorMalformed("invalid-implementation-worktree")
        with Path(args.claims).open(encoding="utf-8") as handle:
            claims = _claims(rctx, token, root, json.load(handle))
    except (OSError, ValueError, MinorMalformed) as exc:
        return _implementation_refusal(ck, version, str(exc) if isinstance(exc, MinorMalformed) else "invalid-implementation-claims")
    head = rctx._git_out("rev-parse", "--verify", "-q", f"{args.head}^{{commit}}")
    if not head or args.head != head:
        return _implementation_refusal(ck, version, "invalid-implementation-base")
    proposal = {"base_head": head, "worktree": str(root), "branch": member["source_branch"],
                **claims, "started": ck._now()}
    existing = member.get("implementation")
    if existing:
        if {k: v for k, v in existing.items() if k != "started"} != {k: v for k, v in proposal.items() if k != "started"}:
            return _implementation_refusal(ck, version, "implementation-already-started")
        proposal = existing
    problem = _dependencies(ck, rctx, record, version, claims, head)
    if problem:
        return _implementation_refusal(ck, version, problem)
    candidate = {**member, "implementation": proposal}
    worker, status, _retired = _worker_context(ck, rctx, record, candidate, rctx.budget, canonical_merged=False)
    if worker is None or status != "met":
        return _implementation_refusal(ck, version, "implementation-worktree-unverified")
    if not existing and (worker._git_out("rev-parse", "HEAD") != head or worker._git_out("status", "--porcelain")):
        return _implementation_refusal(ck, version, "implementation-base-not-clean-head")
    integration = _integration_ref(rctx, _target(record))
    if not integration or _ancestor(rctx, head, integration) != "met":
        return _implementation_refusal(ck, version, "implementation-base-not-integrated")
    for other in ordered_members(record):
        if other["version"] == version or _merged_on_base(ck, rctx, record, other, head):
            continue
        implementation = other.get("implementation")
        if not implementation:
            branch = rctx._git_out("rev-parse", "--verify", "-q", f"refs/heads/{other['source_branch']}^{{commit}}")
            if other.get("start_head") or (branch and _ancestor(rctx, branch, integration) != "met"):
                return _implementation_refusal(ck, version, "legacy-member-without-claims")
            continue
        _other_ctx, other_status, _ = _worker_context(ck, rctx, record, other, rctx.budget, canonical_merged=False)
        if other_status != "met":
            return _implementation_refusal(ck, version, "active-implementation-unverified")
        if any(_overlap(w, p) for w in claims["write_paths"] for p in [*implementation["read_paths"], *implementation["write_paths"], *other.get("coordinator_paths", [])]) or any(
            _overlap(w, p) for w in [*implementation["write_paths"], *other.get("coordinator_paths", [])] for p in claims["read_paths"]
        ):
            return _implementation_refusal(ck, version, "implementation-scope-conflict")
    if not existing:
        record.setdefault("implementation_controller", {"repo_root": str(rctx.root), "git_common_dir": _common_dir(rctx, rctx.root)})
        member["implementation"] = proposal
        record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
        ck._write_record(record_file(ck, rctx, token), record)
    print(f"IMPLEMENTING {version} base_head={head}")
    return 0


def cmd_check_member(ck: ModuleType, args: argparse.Namespace) -> int:
    """Read-only parent-bound member projection; never creates or rebinds approval."""
    rctx = minor_context(ck, args.repo)
    parse_minor(ck, args.minor)
    state = load_minor(ck, rctx, args.minor, args.session, accept_completed=True)
    if state.forced:
        print(state.forced[0])
        return state.forced[1]
    record = state.record
    if record is None:
        raise ck.Malformed("no minor run record for this scope and session")
    members = ordered_members(record)
    index = next((i for i, m in enumerate(members) if m["version"] == args.member), None)
    if index is None:
        raise ck.Malformed(f"{args.member} is not a member of {args.minor}")
    member = members[index]
    plans = scan_plans(rctx.root, *parse_minor(ck, args.minor))
    plan = next(p for p in plans if p.version == args.member)
    notices = []
    result = evaluate_member(ck, rctx, record, member, plan, notices)
    gate = member_gate(ck, rctx, str(record["repo"]), members[index - 1] if index else None, member)
    lines = [("member.gate", gate), *result.lines]
    missing = [pid for pid, status in lines if status not in _MET]
    line = "INCOMPLETE: " + " ".join(missing) if missing else f"PLAN COMPLETE {plan.rel} {rctx._git_out('rev-parse', 'HEAD')} {record['nonce']}"
    code = ck.EXIT_INCOMPLETE if missing else ck.EXIT_COMPLETE
    if gate == GATE_VIOLATED:
        line, code = f"BLOCKED: member-gate ({args.member})", ck.EXIT_BLOCKED
    for notice in [*state.notices, *notices]:
        print(f"notice: {notice}", file=sys.stderr)
    print(line)
    if args.json:
        print(json.dumps({"verdict": line, "exit": code, "minor": args.minor, "member": args.member,
                          "predicates": dict(lines), "implementation": member.get("implementation"),
                          "base_head": (ck.project(record, args.member) or {}).get("start_head")}, sort_keys=True))
    else:
        for predicate, status in lines:
            print(f"{predicate} {status}")
    return code


@minor_writer
def cmd_record_block(ck: ModuleType, args: argparse.Namespace) -> int:
    """Append an open blocker to the minor record, naming the member when one is given."""
    rctx = repo_context(ck, args)
    token = args.minor
    parse_minor(ck, token)
    if args.category not in ck.BLOCKER_CATEGORIES:
        raise ck.Malformed(f"unknown blocker category: {args.category}")
    session = None if args.session in (None, "auto") else args.session
    # A completed record still takes a blocker: its completion is signed, so this cannot be forged.
    state = load_minor(ck, rctx, token, session, accept_completed=True)
    record = state.record
    if record is None:
        if state.forced is not None:
            print(state.forced[0])
            return state.forced[1]
        print("no minor run record for this scope and session", file=sys.stderr)
        return ck.EXIT_MALFORMED
    member = None
    if args.member:
        member = next((m for m in record["members"] if m.get("version") == args.member), None)
        if member is None:
            raise ck.Malformed(f"{args.member} is not a member of {token}")
    member_classes = ((member or {}).get("approvals") or {}).get("classes") or []
    approved = _classes(record) | {str(c.get("class")) for c in member_classes if isinstance(c, dict)}
    if args.approval_class and args.approval_class in approved:
        print(f"rejected: the approvals already answer {args.approval_class}", file=sys.stderr)
        return ck.EXIT_MALFORMED
    entry = {"category": args.category, "evidence": args.evidence[:2000], "open": True, "at": ck._now(),
             'approval_class': args.approval_class, 'request': ck._json_request(getattr(args, 'request', '{}')),
             'purpose': getattr(args, 'purpose', None), 'why': getattr(args, 'why', None)}
    if member is not None:
        entry["version"] = args.member
    approval_binding.add_blocker(record, entry)
    ck._write_record(record_file(ck, rctx, token), record)
    suffix = f" ({args.member})" if member is not None else ""
    print(f"BLOCKED: {args.category}{suffix}")
    return ck.EXIT_BLOCKED


# --------------------------------------------------------------------------- single-plan carry and archive
#
# A one-plan run ends by recording every gap it leaves open in the next version and,
# when it is the last unshipped plan of its minor, by archiving the minor. The rules
# are owned by the completion contract, "Single-plan carry and archive"; the writes
# are `minor_close.py carry --plan` and `minor_close.py archive --plan`.

# Gap ids repeat across a ledger's version sections (`#### WN-3 (v4.13.7): ...` and
# `#### WN-3 (v4.13.8): ...`), so a one-plan carry names its source by version and id.
CARRIED_FROM_RE = re.compile(
    r"^\s*-\s*\*\*Carried from\*\*:\s*(?P<version>v\d+\.\d+\.\d+)(?:#(?P<id>" + GAP_ID + r"))?(?![A-Za-z0-9-])",
    re.MULTILINE,
)
PLAN_MIGRATED_FROM_RE = re.compile(
    r"\*\*Migrated from\*\*:\s*(?P<version>v\d+\.\d+\.\d+)#(?P<id>" + GAP_ID + r")(?![A-Za-z0-9-])"
)
_SECTION_VERSION_RE = re.compile(r"^(v\d+\.\d+\.\d+)\b")
PLAN_CARRY_REASON = "user-deferred"


def section_version(section: str) -> str | None:
    """The `vX.Y.Z` a ledger `## ` section heading names, or None."""
    found = _SECTION_VERSION_RE.match(section.strip())
    return found.group(1) if found else None


def carry_target(version: str, last: bool) -> str:
    """Where a plan's open gaps go: the next patch's section, or the next minor's `.0`."""
    major, minor, patch = version_order(version)[:3]
    return f"v{major}.{minor + 1}.0" if last else f"v{major}.{minor}.{patch + 1}"


def last_plan_status(ck: ModuleType, rctx: RepoContext, version: str, repo: str) -> str:
    """`met` when every other non-superseded plan of the version's minor is shipped.

    Then this plan is the minor's last, so its run carries every open gap of the
    minor to the next minor and archives the minor. `cannot-verify` when a plan's
    release cannot be read.
    """
    major, minor = minor_of(version)
    try:
        plans = scan_plans(rctx.root, major, minor, strict=False)
    except MinorMalformed:
        return "cannot-verify"
    for plan in plans:
        if plan.version == version or plan.status == "superseded":
            continue
        state = shipped(ck, rctx, repo, plan.version)
        if state != "met":
            return "unmet" if state == "unmet" else "cannot-verify"
    return "met"


def _ledger_items_at(rctx: RepoContext, commit: str, minor: tuple[int, int]) -> list[GapItem] | None:
    """Every item of the minor's ledger as committed at `commit`; [] when none existed."""
    for rel in ledger_rels(*minor):
        status, out = _ledger_blob(rctx, commit, rel)
        if status == "cannot-verify":
            return None
        if status == "met":
            return parse_ledger(out)
    return []


def plan_migration_met(ledgers: list[Ledger], ledger: Ledger, item: GapItem) -> bool:
    """A last plan's `- MIGRATED to vX.(Y+1).0` item: a copy in the next minor names its
    version and id (`**Migrated from**: vX.Y.Z#ID`), so a repeated id never matches."""
    if item.state != "migrated" or str(item.target) != next_minor(ledger.token()) + ".0":
        return False
    label = f"{section_version(item.section)}#{item.gid}"
    reason, _copy = migration_copy_status(
        ledgers, str(item.target), ledger, item, label=label, allow_carried=True,
    )
    return reason == "migration-copy-complete"



def carried_copy(ledger: Ledger, version: str, gid: str) -> bool:
    """True when a later version's section holds an item carried from `version#gid`."""
    for item in ledger.items:
        later = section_version(item.section)
        if later is None or version_order(later) <= version_order(version):
            continue
        if any(m.group("version") == version and (m.group("id") or item.gid) == gid
               for m in CARRIED_FROM_RE.finditer(item.body)):
            return True
    return False


def gaps_carried_status(
    ck: ModuleType, rctx: RepoContext, version: str, record: dict | None, last: str,
) -> str:
    """`gaps.carried` for a one-plan run (completion contract, "Single-plan carry and archive")."""
    if last == "cannot-verify":
        return "cannot-verify"
    minor = minor_of(version)
    ledgers, unreadable = load_ledgers(rctx.root)
    own = [l for l in ledgers if l.minor == minor]
    if unreadable and any(minor_of_rel(r) == minor for r in unreadable):
        return "cannot-verify"
    if not own:
        return "met"
    if len(own) > 1 or own[0].problems:
        return "cannot-verify"
    ledger = own[0]
    for item in ledger.items:
        mine = section_version(item.section) == version
        if last == "met":
            if item.state == "open" or (item.state == "migrated" and not plan_migration_met(ledgers, ledger, item)):
                return "unmet"
        elif mine and item.state != "resolved":
            return "unmet"
    start = str((record or {}).get("start_head") or "")
    if not start:
        return "met"
    baseline = _ledger_items_at(rctx, start, minor)
    if baseline is None:
        return "cannot-verify"
    for old in baseline:
        if section_version(old.section) != version or old.state != "open":
            continue
        # An item is its section's version plus its id: ids repeat across sections.
        if any(section_version(i.section) == version and i.gid == old.gid for i in ledger.items):
            continue  # still in its section: judged above
        if not carried_copy(ledger, version, old.gid):
            return "unmet"  # deleted, or moved without saying where it came from
    return "met"


def minor_of_rel(rel: str) -> tuple[int, int] | None:
    found = re.search(r"v(\d+)\.(\d+)/known-gaps\.md$", rel)
    return (int(found.group(1)), int(found.group(2))) if found else None


def empty_dirs_status(rctx: RepoContext) -> str:
    """`archive.empty-dirs`: no directory under docs/releases/ is left empty."""
    base = rctx.root / "docs" / "releases"
    if not base.is_dir():
        return "met"
    for path in sorted(base.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        try:
            if path.is_dir() and not any(path.iterdir()):
                return "unmet"
        except OSError:
            return "cannot-verify"
    return "met"
