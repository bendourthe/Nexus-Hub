#!/usr/bin/env python3
"""Read-only claims pre-check: compare a draft claims file with every admitted member.

Summary: before a worker submits `member-implement-start --claims`, it runs this to
see every pair of paths the native checker would refuse as an implementation scope
conflict, plus draft-claims hygiene (exact files only, coordinator-owned paths) and
the CI follow-up files a change usually needs. It reads the minor run record and the
draft; it writes nothing and signs nothing.

Usage:
    python claims_precheck.py --record <run-record.json> --claims <draft.json>
        [--member vX.Y.Z] [--merged vX.Y.Z ...] [--no-merge-check] [--base REF] [--json]
    python claims_precheck.py --record <run-record.json> --coordinator-claims <paths.json>
        [--member vX.Y.Z] [--merged vX.Y.Z ...] [--no-merge-check] [--base REF] [--json]

`--member` names the draft's own version so an already-admitted copy of it is not
compared with itself. Exit codes: 0 no error finding (warnings may print); 1 at least
one conflict or checker-equivalent refusal; 2 usage or unreadable input.

Every object carrying both `version` and `implementation` is compared, at any depth,
so members added by amend-minor (which live under amendment pages and runtime
descriptors, not the top-level `members` list) are included. A member already merged
on the integration base is skipped, exactly as the native checker skips it
(`completion_minor._merged_on_base`): the member's `source_branch` pull request is MERGED
(`gh pr view`), its merge commit is an ancestor of the base (`--base`, default HEAD), and
`--merged` names any further member to treat as merged. A member that cannot be verified
(no `gh`, no `source_branch`, lookup failure) is kept as active, the stricter reading, and
is listed under `unverified`. `--no-merge-check` skips the lookups (offline).
`--coordinator-claims` evaluates a publication-only coordinator claim the way `record
member-start --coordinator-claims` does (`_coordinator_conflict`): the coordinator write
paths must not overlap another active member's reads, writes, or coordinator paths. It does
not raise the coordinator-owned-path error, since those paths are what a coordinator owns.
The overlap rule mirrors `completion_minor._overlap` (casefold, directory prefix);
a parity test pins the two together. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+$")
KEYS = {"depends_on", "read_paths", "write_paths"}
# Mirrors completion_minor._coordinator_paths / _coordinator_name: workers propose deltas to these.
COORDINATOR_FIXED = (".nexus-hub/", "docs/todos.md", "CHANGELOG.md", "RELEASE_NOTES.md", "DEVLOG.md", "VERSION",
                     "version.txt", "package.json", "package-lock.json", "pyproject.toml", ".bumpversion.cfg",
                     "README.md", "AGENTS.md", "CLAUDE.md", "docs/README.md", "docs/DEVLOG.md",
                     "data/skills.json", "data/SKILL_INDEX.md", "data/marketplace.json", "data/bundles.json",
                     ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json")
PROTECTED = (".github/", "configs/permissions/", ".nexus-hub/", ".pre-commit-config.yaml", ".gitlab-ci.yml",
             "Jenkinsfile", "azure-pipelines.yml", "catalog/hooks/settings.json")
SHARED_FOLDERS = ("docs/", "docs/decisions/", "docs/releases/", "docs/handbooks/", "scripts/", "catalog/", "tests/",
                  "data/", "templates/", "guides/", "configs/", "extensions/", ".github/", "catalog/skills/",
                  "catalog/hooks/", "catalog/commands/")
# (write-path regex, files that must also be claimed, message). Heuristics from past CI/doc follow-ups.
FOLLOW_UPS = (
    (re.compile(r"^(tests|catalog/hooks/tests)/.*test_[^/]*\.py$"), ("scripts/ci/profiles.py",),
     "a new test file needs a shard in scripts/ci/profiles.py (claim it, or confirm the test lands in a directory a shard already runs)"),
    (re.compile(r"^templates/ai-instructions/"), ("scripts/lib/installer/legacy_fingerprints.json",),
     "template edits need regenerated legacy fingerprints (scripts/build_legacy_fingerprints.py) and the doc-budget check"),
    (re.compile(r"^scripts/installer\.(sh|ps1)$"),
     ("docs/handbooks/distribution.html", "docs/handbooks/_sources/distribution/model.json", "guides/website/nexus-hub-guide.html"),
     "installer edits stale the distribution handbook evidence and the guide's data-src line citations; claim them or hand them to the coordinator"),
)


def overlap(left: str, right: str) -> bool:
    """Same semantics as completion_minor._overlap (casefold, directory prefix)."""
    a, b = left.casefold(), right.casefold()
    return a.rstrip("/") == b.rstrip("/") or (a.endswith("/") and b.startswith(a)) or (b.endswith("/") and a.startswith(b))


def coordinator_owned(path: str) -> bool:
    name = path.rstrip("/").rsplit("/", 1)[-1].casefold()
    if "known-gaps" in name or name in {"changelog.md", "release_notes.md", "release-notes.md", "version", "version.txt"}:
        return True
    return any(overlap(path, c) for c in COORDINATOR_FIXED)


def find_members(node: object, found: dict[str, dict] | None = None) -> dict[str, dict]:
    """Every object with `version` and `implementation`, at any depth, merged per version."""
    found = {} if found is None else found
    if isinstance(node, dict):
        impl, version = node.get("implementation"), node.get("version")
        if isinstance(impl, dict) and isinstance(version, str) and VERSION_RE.match(version):
            entry = found.setdefault(version, {"read": set(), "write": set(), "coordinator": set()})
            if isinstance(node.get("source_branch"), str):
                entry["source_branch"] = node["source_branch"]
            entry["read"] |= {p for p in impl.get("read_paths", []) if isinstance(p, str)}
            entry["write"] |= {p for p in impl.get("write_paths", []) if isinstance(p, str)}
            entry["coordinator"] |= {p for p in node.get("coordinator_paths", []) if isinstance(p, str)}
        for value in node.values():
            find_members(value, found)
    elif isinstance(node, list):
        for value in node:
            find_members(value, found)
    return found


def validate_draft(draft: object) -> tuple[dict[str, list[str]] | None, list[dict]]:
    errors: list[dict] = []
    if not isinstance(draft, dict) or set(draft) != KEYS:
        return None, [{"level": "error", "code": "invalid-implementation-claims",
                       "detail": "claims must be an object with exactly depends_on, read_paths, write_paths"}]
    for key in KEYS:
        value = draft[key]
        if not isinstance(value, list) or any(not isinstance(p, str) for p in value):
            return None, [{"level": "error", "code": "invalid-implementation-claims", "detail": f"{key} must be a list of strings"}]
        if len({p.casefold() for p in value}) != len(value):
            errors.append({"level": "error", "code": "duplicate-implementation-claim", "detail": key})
    if not draft["write_paths"]:
        errors.append({"level": "error", "code": "empty-implementation-write-scope", "detail": "write_paths is empty"})
    for key in ("read_paths", "write_paths"):
        for path in draft[key]:
            if path.startswith("/") or ".." in path.split("/") or "\\" in path or re.search(r"[*?\[]", path) or ":" in path[:3]:
                errors.append({"level": "error", "code": "non-literal-path", "detail": f"{key}: {path}"})
    for path in draft["write_paths"]:
        if coordinator_owned(path):
            errors.append({"level": "error", "code": "coordinator-owned-path",
                           "detail": f"{path} belongs to the coordinator; propose the delta separately"})
        if any(overlap(path, p) for p in PROTECTED):
            errors.append({"level": "warn", "code": "sensitive-implementation-path",
                           "detail": f"{path} is refused unless a typed permission is recorded"})
        if path.endswith("/"):
            shared = path.casefold() in SHARED_FOLDERS
            errors.append({"level": "error" if shared else "warn", "code": "shared-folder-write" if shared else "directory-write",
                           "detail": f"{path}: claim exact files only; a folder claim blocks every other plan under it"})
    return {k: list(draft[k]) for k in KEYS}, errors


def follow_up_findings(draft: dict[str, list[str]]) -> list[dict]:
    claimed = [*draft["write_paths"], *draft["read_paths"]]
    out, seen = [], set()
    for path in draft["write_paths"]:
        for pattern, required, message in FOLLOW_UPS:
            if pattern.match(path) and message not in seen and not all(any(overlap(r, c) for c in claimed) for r in required):
                seen.add(message)
                out.append({"level": "warn", "code": "ci-follow-up", "detail": f"{path}: {message}"})
    return out


def conflicts(draft: dict[str, list[str]], others: dict[str, dict]) -> list[dict]:
    """The checker's own rule: draft writes vs others' reads, writes and coordinator paths;
    others' writes and coordinator paths vs draft reads."""
    found = []
    for version, claim in sorted(others.items()):
        for w in draft["write_paths"]:
            for kind, paths in (("read", claim["read"]), ("write", claim["write"]), ("coordinator", claim["coordinator"])):
                found += [{"kind": f"draft-write/{kind}", "draft": w, "member": version, "path": p} for p in sorted(paths) if overlap(w, p)]
        for r in draft["read_paths"]:
            for kind, paths in (("write", claim["write"]), ("coordinator", claim["coordinator"])):
                found += [{"kind": f"draft-read/{kind}", "draft": r, "member": version, "path": p} for p in sorted(paths) if overlap(r, p)]
    return found


_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def merged_on_base(record: dict, entry: dict, base: str) -> bool | None:
    """True merged, False not merged, None cannot verify. Mirrors completion_minor._merge_commit
    (PR state MERGED with a merge commit) and the ancestor test of _merged_on_base."""
    branch, repo = entry.get("source_branch"), record.get("repo") if isinstance(record, dict) else None
    if not branch or not repo:
        return None
    try:
        out = subprocess.run(["gh", "pr", "view", branch, "--repo", str(repo), "--json", "state,mergeCommit"],
                             capture_output=True, text=True, timeout=60, creationflags=_NO_WINDOW)
        if out.returncode:
            return False if "no pull requests found" in out.stderr.lower() else None
        data = json.loads(out.stdout)
        if data.get("state") != "MERGED":
            return False
        oid = (data.get("mergeCommit") or {}).get("oid")
        if not oid:
            return None
        anc = subprocess.run(["git", "merge-base", "--is-ancestor", str(oid), base], capture_output=True, creationflags=_NO_WINDOW)
        return anc.returncode == 0 if anc.returncode in (0, 1) else None
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def active_members(record: object, member: str | None, merged: set[str], check: bool, base: str,
                   lookup=merged_on_base) -> tuple[dict[str, dict], list[str], list[str]]:
    """Other members still active: not the draft's own, not merged. Returns (active, skipped, unverified)."""
    active, skipped, unverified = {}, [], []
    for version, claim in find_members(record).items():
        if version == member:
            continue
        state = True if version in merged else (lookup(record, claim, base) if check else None)
        if state is True:
            skipped.append(version)
            continue
        if state is None and check:
            unverified.append(version)
        active[version] = claim
    return active, sorted(skipped), sorted(unverified)


def coordinator_conflicts(paths: list[str], others: dict[str, dict]) -> list[dict]:
    """_coordinator_conflict: paths vs each active member's reads, writes and coordinator paths."""
    return [{"kind": f"coordinator-write/{kind}", "draft": w, "member": v, "path": p}
            for v, claim in sorted(others.items())
            for w in paths
            for kind in ("read", "write", "coordinator")
            for p in sorted(claim[kind]) if overlap(w, p)]


def run(record: object, draft_raw: object, member: str | None, *, merged: set[str] | None = None,
        check_merged: bool = True, base: str = "HEAD", coordinator: bool = False, lookup=merged_on_base) -> dict:
    others, skipped, unverified = active_members(record, member, merged or set(), check_merged, base, lookup)
    if coordinator:
        raw = draft_raw.get("write_paths") if isinstance(draft_raw, dict) else draft_raw
        if not isinstance(raw, list) or not raw or any(not isinstance(x, str) for x in raw):
            findings = [{"level": "error", "code": "invalid-coordinator-claims",
                         "detail": "coordinator claims must be a non-empty list of paths (or an object with write_paths)"}]
            pairs = []
        else:
            findings = [{"level": "error", "code": "non-literal-path", "detail": f"coordinator-write: {x}"}
                        for x in raw if x.startswith("/") or ".." in x.split("/") or "\\" in x or re.search(r"[*?\[]", x)]
            pairs = coordinator_conflicts(raw, others)
    else:
        draft, findings = validate_draft(draft_raw)
        pairs = conflicts(draft, others) if draft else []
        if draft:
            findings += follow_up_findings(draft)
    return {"members_compared": sorted(others), "merged_skipped": skipped, "unverified": unverified,
            "conflicts": pairs, "findings": findings,
            "ok": not pairs and not any(f["level"] == "error" for f in findings)}


def load(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only claims pre-check against every admitted member.")
    ap.add_argument("--record", required=True, help="minor run record JSON (read only)")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--claims", help="draft claims JSON: depends_on, read_paths, write_paths")
    group.add_argument("--coordinator-claims", help="coordinator write paths JSON (list, or object with write_paths)")
    ap.add_argument("--merged", action="append", default=[], metavar="VERSION", help="treat this member as merged (repeatable)")
    ap.add_argument("--no-merge-check", action="store_true", help="do not look up pull requests; only --merged members are skipped")
    ap.add_argument("--base", default="HEAD", help="integration base for the merge-ancestor test (default HEAD)")
    ap.add_argument("--member", help="the draft's own version, excluded from the comparison")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = ap.parse_args(argv)
    if any(not VERSION_RE.match(v) for v in [*args.merged, *([args.member] if args.member else [])]):
        print("usage error: --member and --merged must look like v4.15.6", file=sys.stderr)
        return 2
    try:
        report = run(load(args.record), load(args.coordinator_claims or args.claims), args.member,
                     merged=set(args.merged), check_merged=not args.no_merge_check, base=args.base,
                     coordinator=bool(args.coordinator_claims))
    except (OSError, ValueError) as exc:
        print(f"usage error: cannot read input: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Compared with {len(report['members_compared'])} admitted member(s): {', '.join(report['members_compared']) or 'none'}")
        if report["merged_skipped"]:
            print(f"Skipped as already merged (as the native checker does): {', '.join(report['merged_skipped'])}")
        if report["unverified"]:
            print(f"Merge state unverified, kept as active: {', '.join(report['unverified'])}")
        for c in report["conflicts"]:
            print(f"CONFLICT {c['kind']}: {c['draft']} <-> {c['member']} {c['path']}")
        for f in report["findings"]:
            print(f"{f['level'].upper()} {f['code']}: {f['detail']}")
        print("CLEAN: safe to submit" if report["ok"] else "REFUSED: the native admission would reject this draft")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
