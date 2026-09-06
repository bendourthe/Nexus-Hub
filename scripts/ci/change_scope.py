"""Classify a diff into the groups a profile may skip.

The whole contract of this module is FAIL CLOSED, and it is worth stating why
before any code: under a workflow-level path filter, a classification mistake
meant the workflow did not start, which was loud (a required check Pending
forever). Applied as a job-level condition, the same mistake SKIPS a job, and a
skipped job reports Success -- silent.

So every ambiguous case must resolve to "run it":

- an unresolvable diff runs everything,
- an unrecognized path runs everything,
- a crash is caught and runs everything.

`classify()` never raises and never returns an empty set of required groups
without having successfully classified a non-empty diff.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

#: Every scope key a `Group` may declare. A group whose key is not here is a
#: programming error, caught by `tests/ci/test_ci_engine.py`.
SCOPE_KEYS = (
    "catalog",
    "docs",
    "extensions",
    "hooks",
    "installers",
    "platforms",
    "templates",
    "tests",
    "workflows",
)

#: Path prefixes that mark a change as relevant to a scope. Order matters only
#: for readability; a path may match several keys and activates all of them.
_PREFIX_MAP: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("catalog/skills/", ("catalog",)),
    ("catalog/commands/", ("catalog",)),
    ("catalog/agents/", ("catalog",)),
    ("catalog/rules/", ("catalog",)),
    ("catalog/style-guides/", ("catalog",)),
    ("catalog/mcp-configs/", ("catalog",)),
    ("catalog/hooks/", ("hooks", "tests")),
    ("data/", ("catalog",)),
    ("extensions/", ("extensions",)),
    ("scripts/lib/integrations/", ("platforms", "installers")),
    ("scripts/ci/", ("tests",)),
    ("scripts/", ("catalog", "platforms", "workflows", "docs")),
    ("templates/", ("templates", "platforms")),
    ("configs/", ("platforms",)),
    ("tests/", ("tests",)),
    (".github/workflows/", ("workflows",)),
    ("docs/policy/", ("docs", "platforms", "workflows")),
    ("docs/decisions/", ("docs",)),
    ("docs/incidents/", ("docs",)),
    ("docs/solutions/", ("docs",)),
)

#: Files at the repository root that affect everything.
_ROOT_WIDE = {
    "Makefile",
    "AGENTS.md",
    "CLAUDE.md",
    "install.sh",
    "install.ps1",
    ".pre-commit-config.yaml",
    ".gitattributes",
}


@dataclass
class ScopeDecision:
    """What a classification concluded, and why.

    `reason` is not decoration. Every skip must be explainable in the run
    summary, because a skip that reports Success and gives no reason is the
    shape of every fail-open defect this repository has shipped.
    """

    required: set[str] = field(default_factory=set)
    skipped: dict[str, str] = field(default_factory=dict)
    reason: str = ""
    #: True when classification could not be completed and everything runs.
    conservative: bool = False
    files: tuple[str, ...] = ()

    def is_required(self, scope_key: str | None) -> bool:
        """A group with no scope key always runs."""
        if scope_key is None:
            return True
        return scope_key in self.required


def _all_required(reason: str, files: tuple[str, ...] = ()) -> ScopeDecision:
    return ScopeDecision(
        required=set(SCOPE_KEYS),
        skipped={},
        reason=reason,
        conservative=True,
        files=files,
    )


def classify_paths(paths: list[str]) -> ScopeDecision:
    """Classify an explicit list of repository-relative paths."""
    if not paths:
        return _all_required("empty diff (nothing to classify; running everything)")

    required: set[str] = set()
    unknown: list[str] = []

    for raw in paths:
        path = raw.replace("\\", "/").strip()
        if not path:
            continue
        if path in _ROOT_WIDE:
            return _all_required(f"root-wide file changed: {path}", tuple(paths))
        matched = False
        for prefix, keys in _PREFIX_MAP:
            if path.startswith(prefix):
                required.update(keys)
                matched = True
                break
        if not matched:
            if path.startswith("docs/"):
                # Documentation prose that no validator reads. The one class it
                # is safe to skip, and the only reason this module exists.
                required.add("docs")
                matched = True
            else:
                unknown.append(path)

    if unknown:
        return _all_required(
            f"unrecognized path(s), running everything: {sorted(unknown)[:3]}",
            tuple(paths),
        )

    skipped = {k: "no changed path touches this scope" for k in SCOPE_KEYS if k not in required}
    return ScopeDecision(
        required=required,
        skipped=skipped,
        reason=f"classified {len(paths)} changed path(s)",
        conservative=False,
        files=tuple(paths),
    )


def changed_paths(base: str, head: str = "HEAD", repo_root: Path | None = None) -> list[str] | None:
    """Return the diff between two revisions, or None when it cannot be resolved.

    None is distinct from an empty list: empty means "nothing changed", None
    means "we could not find out", and the two lead to the same conservative
    decision by different reasoning.
    """
    if not base:
        return None
    if set(base) == {"0"}:
        # The all-zero sha is the "no previous commit" sentinel for a new branch
        # or tag. Nothing to diff against.
        return None
    try:
        proc = subprocess.run(
            ["git", "diff", "--name-only", base, head],
            cwd=str(repo_root) if repo_root else None,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return [line for line in proc.stdout.splitlines() if line.strip()]


def classify(base: str | None, head: str = "HEAD", repo_root: Path | None = None) -> ScopeDecision:
    """Classify the diff between `base` and `head`, failing closed throughout."""
    if not base:
        return _all_required("no base revision supplied; running everything")
    try:
        paths = changed_paths(base, head, repo_root)
    except Exception as exc:  # noqa: BLE001 - fail closed on ANY unexpected error
        return _all_required(f"classification raised {type(exc).__name__}; running everything")
    if paths is None:
        return _all_required(f"could not resolve diff {base}..{head}; running everything")
    return classify_paths(paths)
