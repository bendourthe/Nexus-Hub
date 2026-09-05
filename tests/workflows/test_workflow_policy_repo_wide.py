"""Repository-wide workflow policy (v3.15.8 Phase 9.3).

Phase 4 asserted cost and safety properties for one workflow and compared it
against its two monitor siblings. Phase 9.3 audited all eight workflows
field-by-field against the plan's optimized format and found two gaps that were
uniform rather than per-workflow: six workflows declared no ``permissions`` at
all, and none declared ``timeout-minutes`` on any job.

These tests hold the whole directory to the properties that audit checked, so a
new workflow inherits the standard by failing here rather than by review. They
are deliberately repo-wide: the Phase 4 file stays focused on the GitHub monitor's
own build chain, and this one owns the invariants every workflow shares.

Two documented exceptions are encoded rather than hidden:

- ``codeql.yml`` declares ``security-events: write`` at job level because
  uploading analysis results requires it, and it has no top-level block. Adding
  one would not help (a job-level block replaces the default outright) and
  narrowing it would break the security scan.
- Any workflow producing a REQUIRED status check must NOT event-filter at all.
  GitHub leaves the absent context Pending forever on an unrelated PR, so such a
  filter makes the protected branch unmergeable without an administrator bypass.
  Those workflows classify paths INSIDE the workflow and gate their jobs with
  ``if:``, because a skipped job reports Success. The set is DERIVED from
  ``docs/policy/required-checks.json`` rather than hardcoded, so declaring a new
  required check enforces the rule on its producing workflow automatically
  (v3.17.6 Phase 2; ``presentify-extractor.yml`` has used this shape since
  v3.12.0, and ``ci.yml`` plus ``doc-colocation.yml`` joined it in v3.17.6).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"

# PyYAML parses the unquoted YAML 1.1 key `on:` as the boolean True.
ON_KEY = True

# codeql needs write access to upload results; it scopes that at job level.
PERMISSION_EXCEPTIONS = {"codeql.yml"}

REQUIRED_CHECKS_MANIFEST = REPO_ROOT / "docs" / "policy" / "required-checks.json"


def required_check_workflows() -> set[str]:
    """Workflow filenames that produce at least one required status check.

    Derived, not hardcoded (v3.17.6 Phase 2). A required check must be produced
    by a workflow that triggers unconditionally, so declaring a new required
    context in the manifest immediately holds its producing workflow to the
    no-event-filter rule -- no second edit here, and no way to add a required
    check while quietly leaving a filter on its workflow.

    Falls back to the known set if the manifest is unreadable, because this test
    must keep asserting something rather than silently exempt every workflow.
    """
    known = {"ci.yml", "doc-colocation.yml", "presentify-extractor.yml"}
    try:
        manifest = json.loads(REQUIRED_CHECKS_MANIFEST.read_text(encoding="utf-8"))
        contexts = {
            context
            for branch in manifest["branches"].values()
            for context in branch["contexts"]
        }
    except (OSError, KeyError, ValueError):
        return known

    # A matrix leg reports as `job (leg)`; resolve to the bare job id.
    jobs = {c.split(" (", 1)[0] for c in contexts}
    producing = set()
    for path in workflow_files():
        try:
            declared = set(load(path)["jobs"])
        except (KeyError, TypeError):
            continue
        if declared & jobs:
            producing.add(path.name)
    return producing or known


# Generous ceilings applied in Phase 9.3: far below the 6-hour default, high
# enough that a legitimately long suite is not failed. The repository Python
# suites run 17-28 minutes locally.
MAX_TIMEOUT_MINUTES = 60


def workflow_files() -> list[Path]:
    files = sorted(WORKFLOW_DIR.glob("*.yml"))
    assert files, "no workflows found"
    return files


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


ALL = [pytest.param(p, id=p.name) for p in workflow_files()]


@pytest.mark.parametrize("path", ALL)
def test_every_workflow_parses(path: Path) -> None:
    assert isinstance(load(path), dict)


@pytest.mark.parametrize("path", ALL)
def test_least_privilege_permissions_are_declared(path: Path) -> None:
    """A workflow that does not say what it needs runs on the repo default."""
    data = load(path)
    if path.name in PERMISSION_EXCEPTIONS:
        job_perms = [j.get("permissions") for j in data["jobs"].values()]
        assert any(job_perms), f"{path.name} is exempt but declares no job permissions"
        return
    assert data.get("permissions") == {"contents": "read"}, (
        f"{path.name} must declare top-level `permissions: contents: read`; "
        "add an exception here only with a reason if it genuinely needs more"
    )


@pytest.mark.parametrize("path", ALL)
def test_every_job_bounds_its_runtime(path: Path) -> None:
    """A hung job otherwise burns the 6-hour default before it is noticed."""
    for name, job in load(path)["jobs"].items():
        timeout = job.get("timeout-minutes")
        assert isinstance(timeout, int), f"{path.name}:{name} has no timeout-minutes"
        assert 1 <= timeout <= MAX_TIMEOUT_MINUTES, (
            f"{path.name}:{name} timeout {timeout} is outside 1-{MAX_TIMEOUT_MINUTES}"
        )


@pytest.mark.parametrize("path", ALL)
def test_every_action_is_pinned_to_a_full_sha(path: Path) -> None:
    """A floating ref is both non-reproducible and a supply-chain foothold."""
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- uses:") and not stripped.startswith("uses:"):
            continue
        ref = stripped.split("uses:", 1)[1].strip().split("#")[0].strip()
        if "@" not in ref:
            continue
        _, rev = ref.rsplit("@", 1)
        assert len(rev) == 40 and all(c in "0123456789abcdef" for c in rev), (
            f"{path.name} pins {ref!r}, which is not a full 40-char SHA"
        )


#: Workflows where cancel-in-progress is deliberately FALSE (v4.0.0).
#:
#: Cancelling superseded PULL-REQUEST validation is correct: a later commit
#: supersedes an earlier one and the earlier answer no longer matters.
#: Cancelling a release or a post-merge run is not. Each tag is a distinct
#: artifact and each merge a distinct state, so there is no later run that
#: covers the earlier one -- cancelling would silently drop the only signal that
#: state will ever get.
# v4.7.0: the scheduled supply-chain watch is a distinct audit per run; a manual
# dispatch must never cancel a scheduled run or the reverse.
NO_CANCEL = {"release.yml", "post-merge.yml", "supply-chain-watch.yml"}

#: Workflows scoped by EVENT rather than by path (v4.0.0).
#:
#: The cost rule below says a workflow with no required check should scope
#: itself to its own tree. These two are already scoped as tightly as the
#: lifecycle allows -- one fires only on a protected-branch merge, the other
#: only on a release tag -- and both are cheap by construction (post-merge runs
#: the fast profile; release runs no test suite). Adding a path filter would
#: make them skip the merge or the tag they exist to observe.
# v4.7.0: the supply-chain watch is scoped by EVENT too (schedule plus manual
# dispatch, never a pull request), so a path filter would be meaningless on it.
LIFECYCLE_EVENT_WORKFLOWS = {"post-merge.yml", "release.yml", "supply-chain-watch.yml"}


@pytest.mark.parametrize("path", ALL)
def test_superseded_runs_are_cancelled(path: Path) -> None:
    data = load(path)
    concurrency = data.get("concurrency")
    assert concurrency, f"{path.name} declares no concurrency group"
    expected = path.name not in NO_CANCEL
    assert concurrency.get("cancel-in-progress") is expected, (
        f"{path.name} sets cancel-in-progress="
        f"{concurrency.get('cancel-in-progress')!r}; expected {expected!r}. "
        "Pull-request validation cancels; release and post-merge runs do not."
    )


@pytest.mark.parametrize("path", ALL)
def test_no_ordinary_feature_branch_push_expansion(path: Path) -> None:
    """Pushes must stay scoped to the protected branches."""
    triggers = load(path)[ON_KEY]
    push = triggers.get("push")
    if not isinstance(push, dict):
        return

    # v4.0.0: a TAG-only push trigger is the release event, not a branch push.
    # release.yml declares `tags: ['v*']` and no `branches:` at all, which is
    # narrower than any branch list rather than broader.
    if "tags" in push and "branches" not in push:
        assert push["tags"], f"{path.name} declares an empty tag filter"
        return

    branches = push.get("branches")
    assert branches, f"{path.name} pushes on every branch"
    assert set(branches) <= {"main", "develop"}, (
        f"{path.name} pushes on {branches}, beyond the protected branches"
    )


@pytest.mark.parametrize("path", ALL)
def test_required_check_workflows_do_not_event_filter(path: Path) -> None:
    """A required check must never be gated by a workflow-level path filter.

    GitHub leaves a check from an untriggered workflow Pending forever, while a
    job skipped by an `if:` reports Success. So the same path scoping is safe per
    job and fatal per workflow. Shipping v3.17.5 took seven administrator
    bypasses in one day for exactly this reason.

    The complementary guard, scripts/check_required_check_coverage.py, works from
    the manifest inward (context -> producing job -> is its workflow filtered).
    This test works from the workflow outward, so a filter added to a
    required-check producer fails here even before the manifest is consulted.
    """
    if path.name not in required_check_workflows():
        pytest.skip(f"{path.name} produces no required status check")
    triggers = load(path)[ON_KEY]
    for event, cfg in triggers.items():
        if not isinstance(cfg, dict):
            continue
        for key in ("paths", "paths-ignore"):
            assert key not in cfg, (
                f"{path.name} produces a required status check but declares "
                f"`{key}:` on its `{event}` trigger. The check would sit Pending "
                "forever on a PR that touches nothing matching the filter. Move "
                "the scoping to a job-level `if:` instead -- a skipped job "
                "reports Success."
            )


@pytest.mark.parametrize("path", ALL)
def test_focused_workflows_filter_by_path(path: Path) -> None:
    """A workflow with no required check should scope itself to its own tree.

    This is the cost rule, and it applies only where it is safe. Its former
    exception list is gone: the required-check producers are now identified by
    the test above, which asserts the OPPOSITE property for them.
    """
    if path.name in required_check_workflows():
        pytest.skip(f"{path.name} produces a required check; filtering it is unsafe")
    if path.name in LIFECYCLE_EVENT_WORKFLOWS:
        pytest.skip(f"{path.name} is scoped by EVENT rather than by path")
    triggers = load(path)[ON_KEY]
    filtered = [
        name
        for name, cfg in triggers.items()
        if isinstance(cfg, dict) and ("paths" in cfg or "paths-ignore" in cfg)
    ]
    assert filtered, f"{path.name} declares no path filter on any trigger"
