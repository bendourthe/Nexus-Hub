"""Tests for the `changes` job's path classifier in .github/workflows/ci.yml.

v3.17.6 Phase 2 moved path scoping off the workflow trigger and into this shell
step, which changed the consequence of a mistake. Under the old trigger filter a
misclassification meant the workflow never started, and GitHub reported the
required check Pending forever -- loud, and impossible to merge past. Now a
misclassification SKIPS a job, and GitHub reports a skipped job as **Success**.
The same bug that used to block a merge now silently waves it through.

So the classifier is tested as a unit: the actual `run:` script is extracted from
the committed workflow and executed against real git repositories, rather than
reimplemented here (which would test a copy, not the thing that ships).

The fail-closed cases matter most. Every path where the script cannot determine
the answer must yield `relevant=true`, because `true` costs Actions minutes while
`false` costs coverage.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# Explicit sys.path insert, matching the idiom already used in this directory:
# a bare `from conftest import ...` would resolve to tests/conftest.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from bash_helper import BASH

# Matches the idiom in tests/workflows/: a missing parser skips this file
# rather than erroring at collection and taking the whole tree with it.
yaml = pytest.importorskip("yaml")

REPO_ROOT = Path(__file__).resolve().parents[2]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

# BASH is resolved empirically by conftest, NOT via shutil.which: on Windows the
# System32 WSL launcher stub precedes Git Bash on PATH and exits 1, which failed
# this suite on the GitHub Windows runner while it passed locally and on ubuntu.
pytestmark = pytest.mark.skipif(
    BASH is None or shutil.which("git") is None,
    reason="the classifier is a bash script diffing a git repo; both are required",
)


def classifier_script() -> str:
    """Extract the shipped `run:` body of the changes job's classify step."""
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["changes"]["steps"]
    for step in steps:
        if step.get("id") == "classify":
            return step["run"]
    raise AssertionError("no step with id 'classify' in the changes job")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def make_repo(
    tmp_path: Path, base_files: list[str], changed_files: list[str]
) -> tuple[Path, str]:
    """Build a repo with a base commit and a second commit touching `changed_files`."""
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "T")

    for rel in base_files:
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("base\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    base_sha = git(repo, "rev-parse", "HEAD")

    for rel in changed_files:
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("changed\n", encoding="utf-8")
    git(repo, "add", "-A")
    # --allow-empty so the no-changed-files case (a back-merge shaped commit) is
    # constructible; git refuses an empty commit otherwise.
    git(repo, "commit", "-q", "--allow-empty", "-m", "change")
    return repo, base_sha


def run_classifier(
    repo: Path,
    tmp_path: Path,
    event_name: str = "pull_request",
    base_sha: str = "",
    before_sha: str = "",
) -> tuple[str, str]:
    """Execute the shipped script; return (relevant_value, stdout)."""
    script = tmp_path / "classify.sh"
    script.write_text(classifier_script(), encoding="utf-8", newline="\n")
    output = tmp_path / "github_output"
    output.write_text("", encoding="utf-8")

    env = dict(os.environ)
    env.update(
        {
            "EVENT_NAME": event_name,
            "BASE_SHA": base_sha,
            "BEFORE_SHA": before_sha,
            "GITHUB_OUTPUT": str(output),
        }
    )
    result = subprocess.run(
        [BASH, str(script)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, (
        "the classifier must never exit non-zero -- a failed step would skip every "
        f"gated job, and a skipped job reports Success.\nstderr: {result.stderr}"
    )
    written = output.read_text(encoding="utf-8")
    values = [
        line.split("=", 1)[1]
        for line in written.splitlines()
        if line.startswith("relevant=")
    ]
    assert len(values) == 1, f"expected exactly one relevant= output, got {written!r}"
    return values[0], result.stdout


BASE = ["README.md", "scripts/thing.py", "docs/v3/v3.17/plans/plan.md"]


@pytest.mark.parametrize(
    ("label", "changed", "expected"),
    [
        # Ignorable prose: the whole point of the optimization.
        ("plan doc", ["docs/v3/v3.17/plans/plan.md"], "false"),
        (
            "several prose docs",
            ["docs/v3/v3.17/plans/plan.md", "docs/guide.md"],
            "false",
        ),
        # Session histories are frozen records no test reads. They sit DEEPER than
        # development/*.md, which the old filter's single-level `*` also excluded.
        ("session history", ["docs/v3/v3.17/development/history/s.md"], "false"),
        # Validator-input docs paths: editing them must run the guard that reads them.
        ("policy", ["docs/policy/required-checks.json"], "true"),
        ("incidents", ["docs/incidents/note.md"], "true"),
        ("decisions", ["docs/decisions/implemented/tooling/d.md"], "true"),
        ("development contract", ["docs/v3/v3.17/development/contract.md"], "true"),
        # v4.0.0 canonical tree: one level deeper than the legacy v-bucket. The
        # contract branch matched three segments before development/, so after
        # the rename a contract-doc change fell through to "ignorable prose" and
        # skipped CI entirely. Both shapes are asserted so neither can regress.
        (
            "development contract, canonical tree",
            ["docs/releases/v3/v3.17/development/contract.md"],
            "true",
        ),
        (
            "plan doc, canonical tree",
            ["docs/releases/v3/v3.17/plans/plan.md"],
            "false",
        ),
        (
            "session history, canonical tree",
            ["docs/releases/v3/v3.17/development/history/s.md"],
            "false",
        ),
        # Anything outside docs/.
        ("code", ["scripts/thing.py"], "true"),
        ("workflow", [".github/workflows/ci.yml"], "true"),
        ("root doc", ["README.md"], "true"),
        # A single relevant path in an otherwise-ignorable change wins.
        ("mixed", ["docs/v3/v3.17/plans/plan.md", "scripts/thing.py"], "true"),
        ("prose plus policy", ["docs/guide.md", "docs/policy/x.json"], "true"),
    ],
)
def test_classification(
    tmp_path: Path, label: str, changed: list[str], expected: str
) -> None:
    repo, base_sha = make_repo(tmp_path, BASE, changed)
    relevant, stdout = run_classifier(repo, tmp_path, base_sha=base_sha)
    assert relevant == expected, (
        f"{label}: expected {expected}, got {relevant}\n{stdout}"
    )


def test_a_push_event_now_falls_through_to_running_everything(tmp_path: Path) -> None:
    """v4.0.0: ci.yml no longer HAS a push trigger, so the classifier drops that case.

    The classifier used to accept `github.event.before` for a push, because
    ci.yml ran on pushes to main and develop. It no longer does: post-merge work
    moved to post-merge.yml, and re-validating the merge commit was a full
    re-run of the tree the pull request had already proved.

    The `push` branch of the case statement is therefore gone, and a push now
    falls through to the fail-closed default. That is the correct direction for
    a case the workflow cannot reach: if it ever did reach it, running
    everything is the safe answer, because a wrong skip here reports Success.

    The behavior this test used to protect is not lost, only relocated: the
    pull-request path is covered by the parametrized cases below.
    """
    repo, base_sha = make_repo(tmp_path, BASE, ["docs/v3/v3.17/plans/plan.md"])
    relevant, stdout = run_classifier(
        repo, tmp_path, event_name="push", before_sha=base_sha
    )
    assert relevant == "true", stdout
    assert "no usable base sha for event push" in stdout


def test_ci_declares_no_push_trigger() -> None:
    """The premise of the test above, asserted rather than assumed."""
    ci = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"
    text = ci.read_text(encoding="utf-8")
    nl = chr(10)
    on_block = text.split(nl + "on:" + nl, 1)[1].split(nl + "permissions:", 1)[0]
    assert "push:" not in on_block, (
        "ci.yml regained a push trigger; the classifier case above must come back too"
    )


@pytest.mark.parametrize(
    ("label", "event", "base", "before"),
    [
        ("unknown event", "schedule", "", ""),
        ("workflow_dispatch", "workflow_dispatch", "", ""),
        ("missing base sha", "pull_request", "", ""),
        ("all-zero sentinel", "push", "", "0" * 40),
        ("nonexistent base sha", "pull_request", "d" * 40, ""),
        ("garbage base sha", "pull_request", "not-a-sha", ""),
    ],
)
def test_fails_closed_when_the_answer_is_unknown(
    tmp_path: Path, label: str, event: str, base: str, before: str
) -> None:
    """Every unknown must resolve to `true`.

    `true` overspends Actions minutes; `false` silently drops a required check to
    a passing skip. Only one of those is recoverable.
    """
    repo, _ = make_repo(tmp_path, BASE, ["docs/v3/v3.17/plans/plan.md"])
    relevant, stdout = run_classifier(
        repo, tmp_path, event_name=event, base_sha=base, before_sha=before
    )
    assert relevant == "true", (
        f"{label} failed OPEN, which is the dangerous direction\n{stdout}"
    )


def test_no_changed_files_fails_closed(tmp_path: Path) -> None:
    """An empty diff (a back-merge with no file changes) must run everything.

    This is the zero-file-PR case that could never satisfy a path-filtered
    required check at all, and it is the one an optimizer is most tempted to skip.
    """
    repo, _ = make_repo(tmp_path, BASE, [])
    head = git(repo, "rev-parse", "HEAD")
    relevant, stdout = run_classifier(repo, tmp_path, base_sha=head)
    assert relevant == "true", stdout


def test_every_gated_job_is_fail_closed_in_both_halves() -> None:
    """Assert the `if:` shape on every gated job, not just that a gate exists.

    `needs: changes` alone fails OPEN: GitHub skips a job whose dependency failed,
    and a skipped required check reports Success. `!cancelled()` overrides that
    skip, and `!= 'false'` treats a failed job's empty output as "run". A gate
    missing either half is a silent hole, so both are asserted textually.
    """
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    # `ci-required` also depends on `changes`, but it is the aggregate gate, not
    # a path-gated job: it uses `if: always()`, which is STRICTER than
    # `!cancelled()` because it reports even on cancellation. Its own invariants
    # live in tests/validators/test_ci_required_gate.py.
    gated = {
        name: job
        for name, job in workflow["jobs"].items()
        if "changes" in (job.get("needs") or []) and name != "ci-required"
    }
    assert gated, "no job depends on the changes job -- the migration is incomplete"
    for name, job in gated.items():
        condition = job.get("if", "")
        assert "!cancelled()" in condition, (
            f"{name}: `if:` lacks !cancelled(), so a failed `changes` job would skip "
            "it and report Success"
        )
        assert "!= 'false'" in condition, (
            f"{name}: `if:` does not compare with != 'false', so a missing output "
            "would skip it and report Success"
        )


def test_required_check_producers_are_not_gated() -> None:
    """A required check's own job must never be gated on the detector.

    Gating one would make it report Success without running -- green, untested,
    and indistinguishable from a real pass. The four expensive jobs ARE gated by
    design, so this asserts the two cheap always-run jobs stay ungated.
    """
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    for name in ("validate", "shellcheck"):
        job = workflow["jobs"][name]
        assert not job.get("needs"), f"{name} must not depend on the detector"
        assert not job.get("if"), f"{name} must run unconditionally"
