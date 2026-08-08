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
- ``ci.yml`` uses ``paths-ignore`` rather than ``paths``, because it is the
  catch-all gate that must run for any non-docs change. Requiring ``paths`` of it
  would invert its purpose.
"""

from __future__ import annotations

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

# ci.yml is the catch-all gate, so it filters by exclusion instead.
PATHS_FILTER_EXCEPTIONS = {"ci.yml"}

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


@pytest.mark.parametrize("path", ALL)
def test_superseded_runs_are_cancelled(path: Path) -> None:
    data = load(path)
    concurrency = data.get("concurrency")
    assert concurrency, f"{path.name} declares no concurrency group"
    assert concurrency.get("cancel-in-progress") is True, path.name


@pytest.mark.parametrize("path", ALL)
def test_no_ordinary_feature_branch_push_expansion(path: Path) -> None:
    """Pushes must stay scoped to the protected branches."""
    triggers = load(path)[ON_KEY]
    push = triggers.get("push")
    if not isinstance(push, dict):
        return
    branches = push.get("branches")
    assert branches, f"{path.name} pushes on every branch"
    assert set(branches) <= {"main", "develop"}, (
        f"{path.name} pushes on {branches}, beyond the protected branches"
    )


@pytest.mark.parametrize("path", ALL)
def test_focused_workflows_filter_by_path(path: Path) -> None:
    """Everything except the catch-all gate should scope itself to its own tree."""
    if path.name in PATHS_FILTER_EXCEPTIONS:
        # The catch-all gate must not narrow itself to an allowlist. Two shapes
        # satisfy that, and the invariant is "runs by default, with exclusions",
        # not any particular key:
        #   1. `paths-ignore: [...]`                      - a denylist, or
        #   2. `paths: ['**', '!excluded/**', ...]`       - a catch-all followed
        #      by negations, which is behaviourally the same thing.
        #
        # Form 2 became necessary in v3.16.0 Phase 2: `docs/policy/` is validator
        # INPUT (it feeds verify_platform_contracts.py, the contract freshness
        # gate, and the lever-contract completeness tests), so a push touching
        # only that directory must still run CI. Re-including a subdirectory is
        # impossible in `paths-ignore` because GitHub Actions supports the `!`
        # negation character in `paths` ONLY, and the two filters cannot both be
        # set for one event. This test previously asserted the KEY (`paths-ignore`)
        # rather than the PROPERTY (does not narrow), so it failed a change that
        # widened coverage. It now checks the property.
        triggers = load(path)[ON_KEY]
        for name, cfg in triggers.items():
            if not isinstance(cfg, dict):
                continue
            if "paths-ignore" in cfg:
                return
            paths = cfg.get("paths")
            if isinstance(paths, list) and paths and paths[0] == "**":
                return
        raise AssertionError(
            f"{path.name} is the catch-all gate but narrows its trigger: it declares "
            "neither `paths-ignore` nor a `paths` list beginning with '**'. The "
            "repo-wide gate must run by default and subtract exclusions, never "
            "opt in to an allowlist."
        )
    triggers = load(path)[ON_KEY]
    filtered = [
        name
        for name, cfg in triggers.items()
        if isinstance(cfg, dict) and "paths" in cfg
    ]
    assert filtered, f"{path.name} declares no path filter on any trigger"
