"""The progress snapshot is measured from git, so a report never shows `unknown`."""

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "catalog/skills/workflow/implement-phase/scripts"
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def snapshot_module():
    return load("status_snapshot")


class Repo:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.git("init", "-q", "-b", "develop")
        self.git("config", "user.email", "t@example.test")
        self.git("config", "user.name", "Test")

    def git(self, *args, when="2026-11-01T00:00:00Z"):
        env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
        result = subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            text=True,
            env=env,
            stdin=subprocess.DEVNULL,
            creationflags=FLAGS,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout.strip()

    def plan(self, version, done, total, when):
        path = self.root / f"docs/releases/v1/v1.2/plans/{version}-work.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        tasks = [
            f"- [{'x' if i < done else ' '}] T{i + 1:03d} task" for i in range(total)
        ]
        path.write_text(
            f"# Plan - Work for {version}\n\n## Phase 1: Build\n\n"
            + "\n".join(tasks)
            + "\n",
            encoding="utf-8",
        )
        self.git("add", "-A")
        self.git("commit", "-q", "-m", f"plan {version} {done}/{total}", when=when)

    def release(self, version, total, start, end):
        """A plan branch with two commits, merged with --no-ff and tagged."""
        self.git("checkout", "-q", "-b", f"feat/{version}-work")
        self.plan(version, total // 2, total, start)
        self.plan(version, total, total, end)
        self.git("checkout", "-q", "develop")
        self.git(
            "merge",
            "-q",
            "--no-ff",
            "-m",
            f"Merge feat/{version}-work",
            f"feat/{version}-work",
            when=end,
        )
        self.git("tag", version)


@pytest.fixture
def repo(tmp_path):
    repo = Repo(tmp_path)
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    repo.git("add", "-A")
    repo.git("commit", "-q", "-m", "init", when="2026-10-01T00:00:00Z")
    repo.git("tag", "v1.1.0")
    repo.release("v1.2.0", 10, "2026-10-02T00:00:00Z", "2026-10-03T00:00:00Z")
    repo.release("v1.2.1", 10, "2026-10-04T00:00:00Z", "2026-10-05T00:00:00Z")
    repo.release("v1.2.2", 20, "2026-10-06T00:00:00Z", "2026-10-07T00:00:00Z")
    repo.plan("v1.2.3", 0, 10, "2026-10-08T00:00:00Z")  # plans land on develop first
    repo.git("checkout", "-q", "-b", "feat/v1.2.3-work")
    repo.plan("v1.2.3", 4, 10, "2026-11-18T12:00:00Z")
    repo.git("checkout", "-q", "develop")
    repo.plan("v1.2.4", 0, 8, "2026-11-19T00:00:00Z")
    return repo


def rows(snapshot):
    return {r["name"]: r for r in snapshot["rows"]}


def test_released_in_progress_and_not_started_rows_are_measured(snapshot_module, repo):
    snap = snapshot_module.build(repo.root, "v1.2", {}, "develop", NOW)
    by = rows(snap)
    assert (by["v1.2.0"]["done"], by["v1.2.0"]["total"]) == (10, 10)
    assert by["v1.2.0"]["elapsed"] == "1.0 d" and by["v1.2.0"]["remaining"] == "N/A"
    assert by["v1.2.3"]["elapsed"] == "2.0 d" and by["v1.2.3"]["remaining"].startswith(
        "~"
    )
    assert by["v1.2.4"]["elapsed"] == "N/A" and by["v1.2.4"]["remaining"].startswith(
        "~"
    )
    assert snap["last_released"] == "v1.2.2" and snap["versions_left"] == 2
    assert snap["next_release"]["version"] == "v1.2.3"


def test_a_deleted_branch_is_measured_through_its_merge(snapshot_module, repo):
    repo.git("branch", "-D", "feat/v1.2.1-work")
    by = rows(snapshot_module.build(repo.root, "v1.2", {}, "develop", NOW))
    assert by["v1.2.1"]["elapsed"] == "1.0 d"


def test_rate_comes_from_release_intervals(snapshot_module, repo):
    rate = snapshot_module.release_rate(
        snapshot_module.Repo(repo.root, "develop"),
        snapshot_module.plan_files(repo.root, "v*.md"),
    )
    # intervals 2 d / 10, 2 d / 10, 2 d / 20 tasks
    assert rate is not None and abs(rate[0] - 0.2) < 1e-9


def test_without_history_the_plan_pace_is_used(snapshot_module, tmp_path):
    repo = Repo(tmp_path)
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    repo.git("add", "-A")
    repo.git("commit", "-q", "-m", "init", when="2026-11-01T00:00:00Z")
    repo.plan("v1.2.0", 0, 10, "2026-11-01T00:00:00Z")
    repo.git("checkout", "-q", "-b", "feat/v1.2.0-work")
    repo.plan("v1.2.0", 5, 10, "2026-11-19T12:00:00Z")
    snap = snapshot_module.build(repo.root, "v1.2", {}, "develop", NOW)
    assert snap["rows"][0]["remaining"] == "~1.0 d"
    assert snap["last_released"] == "none released yet"


def test_the_overlay_cannot_set_measured_values(snapshot_module, repo):
    with pytest.raises(ValueError, match="measured"):
        snapshot_module.build(
            repo.root, "v1.2", {"rows": [{"elapsed": "unknown"}]}, "develop", NOW
        )


def test_running_items_compute_elapsed_from_start(snapshot_module, repo):
    overlay = {
        "running": [
            {"name": "CI", "state": "running", "started_at": "2026-11-20T11:30:00Z"}
        ],
        "states": {"v1.2.3": "fix PR in CI"},
    }
    snap = snapshot_module.build(repo.root, "v1.2", overlay, "develop", NOW)
    assert (
        snap["running"][0]["elapsed"] == "30 min"
        and snap["running"][0]["remaining"] == "N/A"
    )
    assert rows(snap)["v1.2.3"]["state"] == "fix PR in CI"


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_the_rendered_report_never_says_unknown(snapshot_module, repo, mode):
    snap = snapshot_module.build(repo.root, "v1.2", {}, "develop", NOW)
    output = load("status_report").render(json.loads(json.dumps(snap)), mode)
    assert "unknown" not in output.lower()


def test_cli_prints_a_snapshot_the_renderer_accepts(repo):
    produced = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "status_snapshot.py"),
            "--repo",
            str(repo.root),
            "--scope",
            "v1.2",
        ],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        creationflags=FLAGS,
    )
    assert produced.returncode == 0, produced.stderr
    rendered = subprocess.run(
        [sys.executable, str(SCRIPTS / "status_report.py"), "--event", "request"],
        input=produced.stdout,
        capture_output=True,
        text=True,
        creationflags=FLAGS,
    )
    assert rendered.returncode == 0, rendered.stderr
    assert (
        rendered.stdout.startswith("## Progress Update")
        and "unknown" not in rendered.stdout.lower()
    )
