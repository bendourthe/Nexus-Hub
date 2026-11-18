#!/usr/bin/env python3
"""Read-only claims pre-check: compare a draft claims file with every admitted member.

Summary: before a worker submits `member-implement-start --claims`, it runs this to
see every pair of paths the native checker would refuse as an implementation scope
conflict, plus draft-claims hygiene (exact files only, coordinator-owned paths) and
the CI follow-up files a change usually needs. It reads the minor run record and the
draft; it writes nothing and signs nothing.

Usage:
    python claims_precheck.py --record <run-record.json> --claims <draft.json>
        [--member vX.Y.Z] [--json]

`--member` names the draft's own version so an already-admitted copy of it is not
compared with itself. Exit codes: 0 no error finding (warnings may print); 1 at least
one conflict or checker-equivalent refusal; 2 usage or unreadable input.

Every object carrying both `version` and `implementation` is compared, at any depth,
so members added by amend-minor (which live under amendment pages and runtime
descriptors, not the top-level `members` list) are included. A member already merged
on the integration base is skipped by the native checker but cannot be proven merged
offline, so this pre-check is the stricter of the two; confirm any such pair by hand.
The overlap rule mirrors `completion_minor._overlap` (casefold, directory prefix);
a parity test pins the two together. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
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


def run(record: object, draft_raw: object, member: str | None) -> dict:
    draft, findings = validate_draft(draft_raw)
    others = {v: c for v, c in find_members(record).items() if v != member}
    pairs = conflicts(draft, others) if draft else []
    if draft:
        findings += follow_up_findings(draft)
    return {"members_compared": sorted(others), "conflicts": pairs, "findings": findings,
            "ok": not pairs and not any(f["level"] == "error" for f in findings)}


def load(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only claims pre-check against every admitted member.")
    ap.add_argument("--record", required=True, help="minor run record JSON (read only)")
    ap.add_argument("--claims", required=True, help="draft claims JSON: depends_on, read_paths, write_paths")
    ap.add_argument("--member", help="the draft's own version, excluded from the comparison")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = ap.parse_args(argv)
    if args.member and not VERSION_RE.match(args.member):
        print("usage error: --member must look like v4.15.6", file=sys.stderr)
        return 2
    try:
        report = run(load(args.record), load(args.claims), args.member)
    except (OSError, ValueError) as exc:
        print(f"usage error: cannot read input: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Compared with {len(report['members_compared'])} admitted member(s): {', '.join(report['members_compared']) or 'none'}")
        for c in report["conflicts"]:
            print(f"CONFLICT {c['kind']}: {c['draft']} <-> {c['member']} {c['path']}")
        for f in report["findings"]:
            print(f"{f['level'].upper()} {f['code']}: {f['detail']}")
        print("CLEAN: safe to submit" if report["ok"] else "REFUSED: the native admission would reject this draft")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
