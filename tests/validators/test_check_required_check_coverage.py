"""Tests for scripts/check_required_check_coverage.py.

Every defect this guard exists to catch fails SILENTLY in production: a required
check produced by a filtered workflow looks configured, and a renamed job looks
like it still has its gate. So the tests assert in both directions -- a clean
tree passes, and each individual defect exits 1 with its own failure class named.

The fail-open cases carry the most weight. A guard that cannot parse a workflow,
cannot import PyYAML, or is handed an empty manifest must FAIL rather than print
success over an assertion it never made. v3.17.5 shipped a fail-open validator
and had to patch it the same day, which is why those cases are tested explicitly
rather than assumed.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_required_check_coverage.py"

# The correct shape: no trigger-level filtering, filtering expressed per job.
CLEAN_WORKFLOW = """name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo validate
  tests:
    runs-on: ubuntu-latest
    steps:
      - run: echo tests
"""

# The defect: filtering hoisted to the trigger, which leaves the check Pending.
PATHS_FILTERED_WORKFLOW = """name: CI

on:
  push:
    branches: [main, develop]
    paths:
      - 'scripts/**'
  pull_request:
    branches: [main, develop]
    paths:
      - 'scripts/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo validate
"""

PATHS_IGNORE_WORKFLOW = """name: CI

on:
  push:
    branches: [main, develop]
    paths-ignore:
      - 'docs/**'
  pull_request:
    branches: [main, develop]
    paths-ignore:
      - 'docs/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo validate
"""

# The correctness case that separates this guard from a naive one: the SAME
# path-scoping intent, expressed as a job condition. A skipped job reports
# Success, so this is the shape the guard must accept.
JOB_LEVEL_IF_WORKFLOW = """name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      code: ${{ steps.filter.outputs.code }}
    steps:
      - id: filter
        run: echo "code=true" >> "$GITHUB_OUTPUT"
  validate:
    needs: changes
    if: needs.changes.outputs.code == 'true'
    runs-on: ubuntu-latest
    steps:
      - run: echo validate
"""

# Matrix legs report as `job (value)`; the values here are a runtime expression,
# exactly as in this repository, so resolution must fall back to the job id.
MATRIX_WORKFLOW = """name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  installer-smoke:
    strategy:
      matrix:
        os: ${{ fromJSON('["ubuntu-latest","macos-latest"]') }}
    runs-on: ${{ matrix.os }}
    steps:
      - run: echo smoke
"""

BRANCH_FILTERED_WORKFLOW = """name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo validate
"""

PUSH_ONLY_WORKFLOW = """name: CI

on:
  push:
    branches: [main, develop]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo validate
"""

UNPARSEABLE_WORKFLOW = """name: CI
on:
  pull_request:
    branches: [main
jobs:
  validate:
     - this is not: valid yaml
  : :
"""


def build_tree(
    root: Path,
    workflows: dict[str, str],
    contexts: list[str] | None = None,
    manifest_text: str | None = None,
    branches: list[str] | None = None,
) -> Path:
    """Lay out a minimal repo: .github/workflows/* plus the policy manifest."""
    wf_dir = root / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    for name, body in workflows.items():
        (wf_dir / name).write_text(body, encoding="utf-8")

    policy_dir = root / "docs" / "policy"
    policy_dir.mkdir(parents=True, exist_ok=True)
    manifest = policy_dir / "required-checks.json"

    if manifest_text is not None:
        manifest.write_text(manifest_text, encoding="utf-8")
        return root

    data = {
        "meta": {"repository": "example/repo", "verified": "2026-08-19"},
        "branches": {
            branch: {"strict": True, "contexts": contexts or ["validate"]}
            for branch in (branches or ["main", "develop"])
        },
    }
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return root


def run(root: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(SCRIPT), "--root", str(root)]
    if extra:
        cmd.extend(extra)
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def test_clean_tree_passes(tmp_path: Path) -> None:
    """An unfiltered workflow producing every required context passes."""
    build_tree(tmp_path, {"ci.yml": CLEAN_WORKFLOW}, contexts=["validate", "tests"])
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout
    assert "4 declared context(s)" in result.stdout


def test_paths_filter_fails_as_conditional(tmp_path: Path) -> None:
    """Workflow-level `paths:` on a required check is the core defect."""
    build_tree(tmp_path, {"ci.yml": PATHS_FILTERED_WORKFLOW})
    result = run(tmp_path)
    assert result.returncode == 1
    assert "CONDITIONAL" in result.stderr
    assert "validate" in result.stderr
    assert "`paths:`" in result.stderr
    assert "job-level `if:`" in result.stderr


def test_paths_ignore_filter_fails_identically(tmp_path: Path) -> None:
    """`paths-ignore:` blocks a required check exactly as `paths:` does."""
    build_tree(tmp_path, {"ci.yml": PATHS_IGNORE_WORKFLOW})
    result = run(tmp_path)
    assert result.returncode == 1
    assert "CONDITIONAL" in result.stderr
    assert "`paths-ignore:`" in result.stderr


def test_job_level_if_is_not_flagged(tmp_path: Path) -> None:
    """The correctness case: a job-level `if:` is right and must pass.

    Flagging this would push authors back toward the workflow-level filter that
    causes the defect, so a false positive here is worse than a missed warning.
    """
    build_tree(tmp_path, {"ci.yml": JOB_LEVEL_IF_WORKFLOW})
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_unproduced_context_is_its_own_class(tmp_path: Path) -> None:
    """A context no workflow produces needs a different remedy than a filtered one."""
    build_tree(tmp_path, {"ci.yml": CLEAN_WORKFLOW}, contexts=["validate", "ghost-job"])
    result = run(tmp_path)
    assert result.returncode == 1
    assert "UNPRODUCED" in result.stderr
    assert "ghost-job" in result.stderr
    # The remedy hint must distinguish it from the CONDITIONAL case.
    assert "renamed" in result.stderr
    assert "CONDITIONAL" not in result.stderr


def test_matrix_context_resolves_to_its_job(tmp_path: Path) -> None:
    """`job (leg)` resolves by job id, since matrix values are runtime expressions."""
    build_tree(
        tmp_path,
        {"ci.yml": MATRIX_WORKFLOW},
        contexts=["installer-smoke (ubuntu-latest)", "installer-smoke (macos-latest)"],
    )
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_matrix_context_on_filtered_workflow_still_fails(tmp_path: Path) -> None:
    """Matrix resolution must not become an accidental escape hatch."""
    filtered = MATRIX_WORKFLOW.replace(
        "  pull_request:\n    branches: [main, develop]\n",
        "  pull_request:\n    branches: [main, develop]\n    paths:\n      - 'scripts/**'\n",
    )
    build_tree(
        tmp_path,
        {"ci.yml": filtered},
        contexts=["installer-smoke (ubuntu-latest)"],
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "CONDITIONAL" in result.stderr
    assert "installer-smoke (ubuntu-latest)" in result.stderr


def test_branch_filter_excluding_protected_branch_fails(tmp_path: Path) -> None:
    """Branch filtering strands the check on the branch it omits."""
    build_tree(tmp_path, {"ci.yml": BRANCH_FILTERED_WORKFLOW})
    result = run(tmp_path)
    assert result.returncode == 1
    assert "CONDITIONAL" in result.stderr
    assert "[develop]" in result.stderr
    assert "does not include 'develop'" in result.stderr
    # main IS in the filter, so it must not be reported.
    assert "[main]" not in result.stderr


def test_branches_filter_including_protected_branch_passes(tmp_path: Path) -> None:
    """`branches: [main, develop]` on a PR trigger is idiomatic and correct."""
    build_tree(tmp_path, {"ci.yml": CLEAN_WORKFLOW})
    assert run(tmp_path).returncode == 0


def test_workflow_without_pull_request_trigger_fails(tmp_path: Path) -> None:
    """A push-only workflow never reports on a PR, so it cannot back a gate."""
    build_tree(tmp_path, {"ci.yml": PUSH_ONLY_WORKFLOW})
    result = run(tmp_path)
    assert result.returncode == 1
    assert "CONDITIONAL" in result.stderr
    assert "no `pull_request` trigger" in result.stderr


def test_unparseable_workflow_fails_as_bad_not_skipped(tmp_path: Path) -> None:
    """A workflow the guard cannot read is fatal, never silently skipped."""
    build_tree(
        tmp_path,
        {"ci.yml": CLEAN_WORKFLOW, "broken.yml": UNPARSEABLE_WORKFLOW},
        contexts=["validate", "tests"],
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "BAD" in result.stderr
    assert "broken.yml" in result.stderr
    assert "unparseable" in result.stderr


def test_workflow_without_on_block_fails_as_bad(tmp_path: Path) -> None:
    """No `on:` block means the guard cannot judge reachability, so it fails."""
    build_tree(tmp_path, {"ci.yml": "name: CI\njobs:\n  validate:\n    steps: []\n"})
    result = run(tmp_path)
    assert result.returncode == 1
    assert "BAD" in result.stderr
    assert "no `on:` trigger block" in result.stderr


@pytest.mark.parametrize(
    ("label", "body"),
    [
        ("not json", "{ not json at all"),
        ("not an object", "[]"),
        ("no branches key", '{"meta": {}}'),
        ("empty branches", '{"branches": {}}'),
        ("empty contexts", '{"branches": {"main": {"contexts": []}}}'),
        ("non-string context", '{"branches": {"main": {"contexts": [7]}}}'),
        ("branch not an object", '{"branches": {"main": "validate"}}'),
    ],
)
def test_malformed_manifest_fails_as_bad(tmp_path: Path, label: str, body: str) -> None:
    """A manifest defect fails loudly; an empty one must not pass vacuously."""
    build_tree(tmp_path, {"ci.yml": CLEAN_WORKFLOW}, manifest_text=body)
    result = run(tmp_path)
    assert result.returncode == 1, f"{label} unexpectedly passed"
    assert "BAD" in result.stderr
    assert "manifest" in result.stderr


def test_missing_manifest_fails(tmp_path: Path) -> None:
    """No manifest means nothing was asserted, which is a failure not a pass."""
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (wf_dir / "ci.yml").write_text(CLEAN_WORKFLOW, encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode == 1
    assert "manifest not found" in result.stderr


def test_missing_workflow_directory_fails(tmp_path: Path) -> None:
    """No workflows at all cannot satisfy a declared required check."""
    policy = tmp_path / "docs" / "policy"
    policy.mkdir(parents=True)
    (policy / "required-checks.json").write_text(
        '{"branches": {"main": {"contexts": ["validate"]}}}', encoding="utf-8"
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "BAD" in result.stderr


def test_all_failures_collected_before_one_exit(tmp_path: Path) -> None:
    """One run shows the whole picture, not one item per fix-and-rerun cycle."""
    build_tree(
        tmp_path,
        {"ci.yml": PATHS_FILTERED_WORKFLOW},
        contexts=["validate", "ghost-one", "ghost-two"],
        branches=["main"],
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert result.stderr.count("CONDITIONAL") == 1
    assert result.stderr.count("UNPRODUCED") == 2
    assert "ghost-one" in result.stderr and "ghost-two" in result.stderr


def test_pyyaml_absence_fails_loudly_rather_than_passing(tmp_path: Path) -> None:
    """The fail-open case: no PyYAML must abort with a hint, never print OK.

    Mirrors the v3.17.5 regression, where a validator degraded to an empty pass
    when its parser was unavailable and therefore asserted nothing while
    reporting success.
    """
    build_tree(tmp_path, {"ci.yml": CLEAN_WORKFLOW}, contexts=["validate", "tests"])
    # A sitecustomize on an isolated path makes `import yaml` raise for this
    # subprocess only, without touching the interpreter running the suite.
    blocker = tmp_path / "blocker"
    blocker.mkdir()
    (blocker / "sitecustomize.py").write_text(
        "import sys\n"
        "class _Block:\n"
        "    def find_module(self, name, path=None):\n"
        "        return self if name == 'yaml' else None\n"
        "    def find_spec(self, name, path=None, target=None):\n"
        "        if name == 'yaml':\n"
        "            raise ImportError('blocked for test')\n"
        "        return None\n"
        "    def load_module(self, name):\n"
        "        raise ImportError('blocked for test')\n"
        "sys.meta_path.insert(0, _Block())\n",
        encoding="utf-8",
    )
    # cwd and a full env on purpose: a stripped environment makes the
    # interpreter and any CLI it touches fall back to relative paths for
    # user-site and state, and an earlier draft of this test left stray
    # directories in the repository working tree.
    env = dict(os.environ)
    env["PYTHONPATH"] = str(blocker)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env=env,
    )
    assert result.returncode != 0
    assert "OK" not in result.stdout
    assert "PyYAML" in result.stderr
    assert "pip install PyYAML" in result.stderr


LIST_FORM_WORKFLOW = """name: CI

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo validate
"""

WILDCARD_BRANCH_WORKFLOW = """name: CI

on:
  pull_request:
    branches: ['main', 'release/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo validate
"""

NEGATED_BRANCH_WORKFLOW = """name: CI

on:
  pull_request:
    branches: ['**', '!develop']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - run: echo validate
"""


def test_list_form_on_block_is_unconditional(tmp_path: Path) -> None:
    """`on: [push, pull_request]` carries no filters, so it must pass.

    A parser that only understood the mapping form would see no pull_request
    trigger here and report CONDITIONAL on a workflow that is in fact correct.
    """
    build_tree(tmp_path, {"ci.yml": LIST_FORM_WORKFLOW})
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_wildcard_branch_pattern_matches(tmp_path: Path) -> None:
    """A `**` pattern must be honoured rather than compared literally."""
    build_tree(
        tmp_path,
        {"ci.yml": WILDCARD_BRANCH_WORKFLOW},
        branches=["main", "release/3.17"],
    )
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr


def test_negated_branch_pattern_excludes_that_branch(tmp_path: Path) -> None:
    """`!develop` inside `branches:` strands the check on develop."""
    build_tree(tmp_path, {"ci.yml": NEGATED_BRANCH_WORKFLOW})
    result = run(tmp_path)
    assert result.returncode == 1
    assert "[develop]" in result.stderr
    assert "negates 'develop'" in result.stderr
    assert "[main]" not in result.stderr


def load_module():
    """Import the guard in-process so --sync internals are reachable.

    The rest of this suite drives the CLI as a subprocess on purpose (that is
    the surface a maintainer runs). `--sync` is the exception: it shells out to
    `gh`, and a stubbed `gh` on PATH is not portable -- on Windows Python
    resolves a bare `gh` to `gh.exe` only, so a `gh.bat` stub is skipped and the
    real CLI answers instead. Monkeypatching the one call is both portable and
    a tighter assertion.
    """
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    return importlib.import_module("check_required_check_coverage")


def test_sync_prints_and_never_writes_the_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--sync is a read-only reporter; refreshing the manifest stays a human act.

    Asserted rather than assumed: a --sync that quietly rewrote the manifest
    would make the guard grade itself against whatever protection happens to be
    configured, which is the opposite of a declared contract.
    """
    build_tree(tmp_path, {"ci.yml": CLEAN_WORKFLOW})
    manifest = tmp_path / "docs" / "policy" / "required-checks.json"
    before = manifest.read_bytes()

    mod = load_module()
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(
            cmd, 0, stdout='{"strict":true,"contexts":["validate"]}', stderr=""
        )

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    assert mod.run_sync("o/r") == 0

    out = capsys.readouterr().out
    assert "o/r" in out
    assert "main" in out and "develop" in out
    assert "validate" in out
    assert manifest.read_bytes() == before, "--sync must never write the manifest"
    # Read-only at the gh level too: `gh api` only, never a protection PUT.
    assert calls, "no gh invocation was made"
    for cmd in calls:
        assert cmd[:2] == ["gh", "api"]
        assert "--method" not in cmd and "-X" not in cmd


def test_sync_reports_failure_when_gh_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """No gh means no answer, and --sync says so instead of printing an empty list."""
    build_tree(tmp_path, {"ci.yml": CLEAN_WORKFLOW})
    manifest = tmp_path / "docs" / "policy" / "required-checks.json"
    before = manifest.read_bytes()

    mod = load_module()

    def boom(cmd, **kwargs):
        raise OSError("gh not found")

    monkeypatch.setattr(mod.subprocess, "run", boom)
    assert mod.run_sync("o/r") == 1
    assert "unavailable" in capsys.readouterr().err
    assert manifest.read_bytes() == before


def test_sync_without_repo_reports_detection_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An undetectable repository is reported, not silently treated as empty."""
    mod = load_module()

    def boom(cmd, **kwargs):
        raise OSError("gh not found")

    monkeypatch.setattr(mod.subprocess, "run", boom)
    assert mod.run_sync(None) == 1
    assert "could not determine the repository" in capsys.readouterr().err


def test_repo_manifest_matches_repo_workflows_structurally() -> None:
    """The shipped manifest must name real jobs, even before the migration.

    Phase 1 deliberately leaves the repo failing CONDITIONAL until Phase 2, so
    this asserts only that no context is UNPRODUCED -- a stale manifest or a
    renamed job would be a separate, silent defect hiding behind the expected
    failure.
    """
    result = run(REPO_ROOT)
    assert "UNPRODUCED" not in result.stderr, result.stderr
    assert "BAD" not in result.stderr, result.stderr
