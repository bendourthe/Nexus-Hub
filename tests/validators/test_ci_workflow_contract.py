"""Event topology and profile-delegation contract for the workflows (v4.0.0 Phase 7).

`test_workflow_policy_repo_wide.py` owns the properties EVERY workflow shares
(permissions, timeouts, concurrency, push scoping). This file owns the v4.0.0
LIFECYCLE topology: which event runs which class of work, that the definitive
command list is not duplicated into YAML, and that the required aggregate always
resolves.

The assertions are written against workflow SHAPE wherever a shape will do, so
the file keeps meaning if a job is renamed. Where a specific file genuinely is
the contract (ci.yml is the one comprehensive gate), it is named.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
REQUIRED_CHECKS = REPO_ROOT / "docs" / "policy" / "required-checks.json"

CI = WORKFLOW_DIR / "ci.yml"
POST_MERGE = WORKFLOW_DIR / "post-merge.yml"
RELEASE = WORKFLOW_DIR / "release.yml"

PROTECTED = {"main", "develop"}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def triggers(path: Path) -> dict:
    """The `on:` mapping.

    PyYAML parses the bare key `on` as the BOOLEAN True (a YAML 1.1 legacy), so
    a reader that looks only for the string key finds no triggers in ANY
    workflow and passes vacuously. Both spellings are accepted for that reason;
    this repository has shipped that exact fail-open before.
    """
    data = load(path)
    on = data.get("on", data.get(True))
    assert isinstance(on, dict), f"{path.name} has no readable triggers"
    return on


ALL_WORKFLOWS = sorted(WORKFLOW_DIR.glob("*.yml"))


# ---------------------------------------------------------------------------
# The three lifecycle workflows exist and own distinct events.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", [CI, POST_MERGE, RELEASE])
def test_the_lifecycle_workflows_exist(path: Path):
    assert path.is_file(), f"{path.name} is missing"


def test_ci_is_the_integration_gate_and_not_a_post_merge_run():
    on = triggers(CI)
    assert "pull_request" in on, "ci.yml must run on the integration pull request"
    assert set(on["pull_request"]["branches"]) == PROTECTED
    assert "push" not in on, (
        "ci.yml must NOT run on a protected-branch push. Under a "
        "pull-request-only merge policy that push is the merge commit of the "
        "pull request that just ran, so it re-validates an identical tree."
    )


def test_ci_supports_the_merge_queue():
    assert "merge_group" in triggers(CI), (
        "the merge queue validates the queued merge result and needs the same gate"
    )


def test_post_merge_runs_only_on_a_protected_branch_push():
    on = triggers(POST_MERGE)
    assert "push" in on
    assert set(on["push"]["branches"]) == PROTECTED
    assert "pull_request" not in on, "post-merge work must not run on a pull request"


def test_release_runs_only_on_a_tag_or_an_explicit_dispatch():
    on = triggers(RELEASE)
    assert "push" in on
    assert on["push"].get("tags"), "release.yml must be tag-triggered"
    assert "branches" not in on["push"], "release.yml must not fire on a branch push"
    assert "pull_request" not in on


# ---------------------------------------------------------------------------
# No duplicate complete suite.
# ---------------------------------------------------------------------------


def test_post_merge_does_not_rerun_the_complete_suite():
    """The merge commit IS the tree the pull request validated."""
    text = POST_MERGE.read_text(encoding="utf-8")
    assert "--profile full" not in text, "post-merge must not run the full profile"
    assert "--profile platform" not in text, "post-merge must not run the platform matrix"
    assert "--profile fast" in text, "post-merge should still smoke-test the merged tree"


def test_release_does_not_rerun_the_complete_suite():
    text = RELEASE.read_text(encoding="utf-8")
    assert "--profile release" in text
    for forbidden in ("--profile full", "--profile platform", "pytest"):
        assert forbidden not in text, f"release.yml re-runs validation via {forbidden!r}"


def test_no_validation_workflow_pairs_a_pull_request_with_the_same_branch_push():
    """Repo-wide form of the rule, so a new workflow inherits it."""
    offenders = []
    for path in ALL_WORKFLOWS:
        on = triggers(path)
        pr = on.get("pull_request")
        push = on.get("push")
        if not isinstance(pr, dict) or not isinstance(push, dict):
            continue
        overlap = set(pr.get("branches") or []) & set(push.get("branches") or [])
        if not overlap:
            continue
        # A per-job `github.event_name` condition is how one file legitimately
        # carries both a pull-request gate and a post-merge step.
        if "github.event_name" in path.read_text(encoding="utf-8"):
            continue
        offenders.append(path.name)
    assert not offenders, (
        f"these workflows validate the same tree twice: {offenders}. Either move "
        "the post-merge work to its own workflow or gate the jobs on "
        "github.event_name."
    )


# ---------------------------------------------------------------------------
# Profile delegation: no duplicated command list.
# ---------------------------------------------------------------------------


def test_ci_delegates_its_validation_to_repository_native_profiles():
    text = CI.read_text(encoding="utf-8")
    assert "scripts/ci/run.py" in text, "ci.yml must call the repository-native engine"
    assert "--profile full" in text


def test_ci_does_not_re_declare_the_validator_list():
    """The defect this prevents is silent and has happened here before.

    ci.yml once re-declared the Makefile's validator sequence as 31 separate
    steps. The two lists diverged in production: a duplicate YAML key silently
    dropped validate_no_personal_paths.py from CI while the local list still ran
    it. A check that stops running still passes everywhere anyone looks.
    """
    text = CI.read_text(encoding="utf-8")
    inline = re.findall(r"run:\s*python scripts/(\w+)\.py", text)
    assert not inline, (
        f"ci.yml invokes repository validators directly: {sorted(set(inline))}. "
        "Add them to a group in scripts/ci/profiles.py instead, so the local "
        "run and the CI run cannot drift."
    )


def test_ci_enforces_the_guide_browser_contracts():
    """The browser gate must fail closed instead of quietly skipping MT-1."""
    jobs = load(CI)["jobs"]
    assert "guide-render" in jobs, "ci.yml has no dedicated guide browser job"

    job = jobs["guide-render"]
    assert job["needs"] == "changes"
    assert job["if"] == "${{ !cancelled() && needs.changes.outputs.relevant != 'false' }}"

    steps = job["steps"]
    commands = "\n".join(str(step.get("run", "")) for step in steps)
    assert "pip install pytest playwright" in commands
    assert "python -m playwright install --with-deps chromium" in commands

    test_step = next(
        step
        for step in steps
        if "tests/verification/test_visual_defect_detector.py" in str(step.get("run", ""))
    )
    assert test_step.get("env", {}).get("NEXUS_REQUIRE_RENDER") == "1"
    assert "tests/guides/" in test_step["run"]
    assert "guide-render" in jobs["ci-required"]["needs"]


def test_every_only_group_named_by_a_workflow_exists():
    """A typo in `--only` must be an error, not an empty selection."""
    import sys

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from scripts.ci.profiles import PROFILES

    known = {g.name for groups in PROFILES.values() for g in groups}
    for path in ALL_WORKFLOWS:
        for match in re.finditer(r"--only\s+([\w,-]+)", path.read_text(encoding="utf-8")):
            for name in match.group(1).split(","):
                assert name in known, f"{path.name} selects unknown group {name!r}"


# ---------------------------------------------------------------------------
# The required aggregate always resolves.
# ---------------------------------------------------------------------------


def test_ci_has_exactly_one_aggregate_and_it_runs_unconditionally():
    jobs = load(CI)["jobs"]
    assert "ci-required" in jobs
    assert jobs["ci-required"]["if"] == "always()", (
        "without always(), a failed dependency SKIPS the aggregate, and a "
        "skipped required check reports Success"
    )


def test_the_aggregate_needs_every_other_job():
    jobs = load(CI)["jobs"]
    needed = set(jobs["ci-required"]["needs"])
    others = set(jobs) - {"ci-required"}
    assert needed == others, (
        f"ci-required does not cover every job. missing: {sorted(others - needed)}; "
        f"stale: {sorted(needed - others)}"
    )


def test_the_aggregate_verdict_is_an_allowlist():
    """A denylist on failure/cancelled lets an unfamiliar result value through."""
    text = CI.read_text(encoding="utf-8")
    aggregate = text.split("\n  ci-required:\n", 1)[1]
    assert "success|skipped)" in aggregate
    assert "refusing to pass vacuously" in aggregate


def test_no_required_context_names_a_matrix_leg():
    """A job-level `if:` is evaluated BEFORE matrix expansion.

    A skipped matrix job publishes only its bare job name, so a per-leg context
    such as `installer-smoke (ubuntu-latest)` can sit Pending forever.
    """
    manifest = json.loads(REQUIRED_CHECKS.read_text(encoding="utf-8"))
    for branch, cfg in manifest["branches"].items():
        for context in cfg["contexts"]:
            assert "(" not in context, (
                f"{branch} requires a per-leg context {context!r}"
            )


def test_every_required_context_is_still_produced():
    """The manifest and the workflows must not drift apart silently."""
    manifest = json.loads(REQUIRED_CHECKS.read_text(encoding="utf-8"))
    produced = set()
    for path in ALL_WORKFLOWS:
        produced.update(load(path).get("jobs", {}))
    for branch, cfg in manifest["branches"].items():
        missing = [c for c in cfg["contexts"] if c not in produced]
        assert not missing, f"{branch} requires contexts no workflow produces: {missing}"


# ---------------------------------------------------------------------------
# Reporting.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", [CI, POST_MERGE, RELEASE])
def test_the_lifecycle_workflows_publish_a_run_summary(path: Path):
    text = path.read_text(encoding="utf-8")
    assert "GITHUB_STEP_SUMMARY" in text, f"{path.name} publishes no run summary"


def test_summary_publication_survives_a_failure():
    """A red run that reports nothing is only actionable by whoever caused it."""
    for path in (CI, POST_MERGE, RELEASE):
        text = path.read_text(encoding="utf-8")
        blocks = [
            block
            for block in text.split("      - name:")
            if "GITHUB_STEP_SUMMARY" in block
        ]
        assert blocks, f"{path.name} has no summary step"
        assert any("if: always()" in block for block in blocks), (
            f"{path.name} publishes its summary only on success"
        )


# ---------------------------------------------------------------------------
# Security and cost controls.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", ALL_WORKFLOWS)
def test_every_workflow_declares_least_privilege_permissions(path: Path):
    data = load(path)
    assert "permissions" in data, (
        f"{path.name} declares no workflow-level permissions, so a job added "
        "later inherits the repository default silently"
    )


@pytest.mark.parametrize("path", ALL_WORKFLOWS)
def test_every_action_reference_is_an_immutable_sha(path: Path):
    offenders = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.search(r"uses:\s*([^\s#]+)", line)
        if not match:
            continue
        ref = match.group(1)
        if ref.startswith("./"):
            continue
        if not re.search(r"@[0-9a-f]{40}$", ref):
            offenders.append(ref)
    assert not offenders, f"{path.name} has unpinned action refs: {offenders}"


def test_release_and_post_merge_do_not_cancel_themselves():
    """Each tag and each merge is a distinct state with no later covering run."""
    for path in (RELEASE, POST_MERGE):
        concurrency = load(path)["concurrency"]
        assert concurrency.get("cancel-in-progress") is False, (
            f"{path.name} cancels in progress; a superseded release or merge run "
            "has no later run that covers it"
        )


def test_pull_request_validation_does_cancel_superseded_runs():
    assert load(CI)["concurrency"]["cancel-in-progress"] is True


# ---------------------------------------------------------------------------
# Docs-only changes still resolve every required check.
# ---------------------------------------------------------------------------


def test_ci_triggers_carry_no_path_filter():
    """The whole v3.17.5 defect class, asserted directly.

    A required check from a path-filtered workflow stays Pending forever on a
    change the filter excludes, so the branch cannot merge without an
    administrator bypass. Shipping v3.17.5 took six of those in one day.
    """
    on = triggers(CI)
    for event, cfg in on.items():
        if isinstance(cfg, dict):
            assert "paths" not in cfg, f"ci.yml path-filters its {event} trigger"
            assert "paths-ignore" not in cfg, f"ci.yml path-ignores its {event} trigger"


def test_the_change_classifier_fails_closed():
    text = CI.read_text(encoding="utf-8")
    assert "relevant=true" in text and "fail closed" in text
    assert "exit 0" in text, "the classifier step must never exit non-zero"
    # Both halves of the consumer guard are load-bearing.
    assert "!cancelled() && needs.changes.outputs.relevant != 'false'" in text


def test_the_required_jobs_are_never_gated_by_the_classifier():
    """`validate` and `shellcheck` are required by name, so they must always run."""
    jobs = load(CI)["jobs"]
    for name in ("validate", "shellcheck"):
        assert "if" not in jobs[name], (
            f"{name} is a required context and must run unconditionally"
        )


# ---------------------------------------------------------------------------
# Repo-wide property: no guard that runs locally is missing from CI.
#
# This is the assertion that should have existed before the migration. Seven
# separate per-guard tests each grepped ci.yml for their own script name, and
# when the workflow started calling a profile they failed one at a time across
# three rounds of pushes. One property over the whole set catches the class in
# a single run, and it keeps catching it for guards added later.
# ---------------------------------------------------------------------------


def test_every_validator_make_validate_runs_is_reachable_from_ci():
    """A guard that runs locally and not in CI reads as coverage and is not.

    The reverse direction (a guard in CI but not in `make validate`) is
    deliberately NOT asserted: CI legitimately runs platform-specific work a
    developer machine cannot, and the profile engine is where that asymmetry is
    expressed.
    """
    import sys

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from tests.validators._ci_reachability import scripts_reachable_from_ci

    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    validate_target = makefile.split("\nvalidate:", 1)[1].split("\nlint:", 1)[0]
    local_guards = set(re.findall(r"python scripts/([\w-]+\.py)", validate_target))
    assert local_guards, "could not parse any guard out of the validate target"

    reachable = scripts_reachable_from_ci()
    missing = sorted(local_guards - reachable)
    assert not missing, (
        f"these guards run in `make validate` but are unreachable from any CI "
        f"job, so they guard nothing in CI: {missing}. Add each to the right "
        "Group in scripts/ci/profiles.py."
    )
