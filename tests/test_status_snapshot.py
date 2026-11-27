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


def fixture_work():
    return [{"id": "package", "title": "Implement the approved packaging change", "authorized": True,
             "feasible": True, "evidence": "Inert fixture's approved packaging scope"}]


def fixture_jobs(items):
    return [{"id": f"fixture-{i}", "handle": f"test-process-{i}", "status": "running",
             "observed_at": "2026-11-20T12:00:00Z", "resume_when": "The fixture process returns its result",
             "evidence": "Inert unit-test process observation", **item} for i, item in enumerate(items, 1)]


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
    snap = snapshot_module.build(repo.root, "v1.2", {"work": fixture_work()}, "develop", NOW)
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
    by = rows(snapshot_module.build(repo.root, "v1.2", {"work": fixture_work()}, "develop", NOW))
    assert by["v1.2.1"]["elapsed"] == "1.0 d"


def test_rate_comes_from_release_intervals(snapshot_module, repo):
    rate = snapshot_module.release_rate(
        snapshot_module.Repo(repo.root, "develop"),
        snapshot_module.plan_files(repo.root, "v*.md"),
    )
    # intervals 2 d / 10, 2 d / 10, 2 d / 20 tasks
    assert rate is not None and abs(rate[0] - 0.2) < 1e-9


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_task_pace_is_not_presented_as_full_release_time(snapshot_module, repo, mode):
    snap = snapshot_module.build(repo.root, "v1.2", {"work": fixture_work(),
        "next_release_condition": "owner capture and full qualification remain"}, "develop", NOW)
    task_estimate = rows(snap)["v1.2.3"]["remaining"]
    assert snap["next_release"]["remaining"] == (
        task_estimate + " implementation only; validation/release time additional"
    )
    assert snap["next_release"]["confidence"] == "low"
    assert "validation/release duration not measured" in snap["next_release"]["basis"]
    output = load("status_report").render(json.loads(json.dumps(snap)), mode)
    assert "implementation only; validation/release time additional" in output
    assert "owner capture and full qualification remain" in output


def test_whole_eta_cannot_undercut_started_serial_members(snapshot_module, repo):
    # Both plans have their own commits, but the second waits for the first.
    repo.git('checkout', '-q', '-b', 'feat/v1.2.4-work')
    repo.plan('v1.2.4', 2, 8, '2026-11-19T12:00:00Z')
    repo.git('checkout', '-q', 'develop')
    snap = snapshot_module.build(repo.root, 'v1.2',
        {'work': fixture_work(), 'dependencies': {'v1.2.4': 'after v1.2.3'}}, 'develop', NOW)
    members = [rows(snap)[name] for name in ('v1.2.3', 'v1.2.4')]
    assert [(row['done'], row['total']) for row in members] == [(4, 10), (2, 8)]
    assert all(row['elapsed'] != 'N/A' for row in members)
    # Six tasks each at the measured median of 0.2 days per task.
    assert all(row['remaining'].startswith('~1.2 d') for row in members)
    assert snap['remaining'].split()[1] == 'd'
    whole_days = float(snap['remaining'].split()[0].lstrip('~'))
    member_days = [float(row['remaining'].split()[0].lstrip('~')) for row in members]
    assert whole_days >= sum(member_days)
    assert whole_days >= max(member_days)
    assert snap['next_release']['version'] == 'v1.2.3'
    assert snap['next_release']['remaining'] == (
        members[0]['remaining'] + ' implementation only; validation/release time additional'
    )
    assert members[1]['dependency'] == 'after v1.2.3'


def test_without_history_the_plan_pace_is_used(snapshot_module, tmp_path):
    repo = Repo(tmp_path)
    (tmp_path / "README.md").write_text("x\n", encoding="utf-8")
    repo.git("add", "-A")
    repo.git("commit", "-q", "-m", "init", when="2026-11-01T00:00:00Z")
    repo.plan("v1.2.0", 0, 10, "2026-11-01T00:00:00Z")
    repo.git("checkout", "-q", "-b", "feat/v1.2.0-work")
    repo.plan("v1.2.0", 5, 10, "2026-11-19T12:00:00Z")
    snap = snapshot_module.build(repo.root, "v1.2", {"work": fixture_work()}, "develop", NOW)
    assert snap["rows"][0]["remaining"] == "~1.0 d"
    assert snap["last_released"] == "none released yet"


def test_the_overlay_cannot_set_measured_values(snapshot_module, repo):
    with pytest.raises(ValueError, match="measured"):
        snapshot_module.build(
            repo.root, "v1.2", {"rows": [{"elapsed": "unknown"}]}, "develop", NOW
        )


def test_running_items_compute_elapsed_from_start(snapshot_module, repo):
    overlay = {
        "running": fixture_jobs([
            {"name": "CI", "state": "running", "started_at": "2026-11-20T11:30:00Z"}
        ]),
        "states": {"v1.2.3": "fix PR in CI"},
    }
    snap = snapshot_module.build(repo.root, "v1.2", overlay, "develop", NOW)
    assert (
        snap["running"][0]["elapsed"] == "30 min"
        and snap["running"][0]["remaining"] == "not estimated (no task list)"
    )
    assert rows(snap)["v1.2.3"]["state"] == "fix PR in CI"


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_the_rendered_report_never_says_unknown(snapshot_module, repo, mode):
    snap = snapshot_module.build(repo.root, "v1.2", {"work": fixture_work()}, "develop", NOW)
    output = load("status_report").render(json.loads(json.dumps(snap)), mode)
    assert "unknown" not in output.lower()


def test_cli_prints_a_snapshot_the_renderer_accepts(repo):
    overlay = repo.root / "report-observations.json"
    overlay.write_text(json.dumps({"work": fixture_work()}), encoding="utf-8")
    produced = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "status_snapshot.py"),
            "--repo",
            str(repo.root),
            "--scope",
            "v1.2",
            "--overlay",
            str(overlay),
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


def test_unexplained_unfinished_snapshot_requires_reconciliation(snapshot_module, repo):
    with pytest.raises(ValueError, match="unfinished"):
        snapshot_module.build(repo.root, "v1.2", {}, "develop", NOW)


def test_released_scope_still_reports_required_owner_capture(snapshot_module, repo):
    action = {"id": "capture", "kind": "action", "title": "Capture installed proof", "prerequisites": ["Open the installed app"],
              "steps": ["Run the displayed capture command", "Paste its receipt"], "expected_result": "A fresh receipt",
              "acknowledgment": "Reply with the receipt path"}
    snap = snapshot_module.build(repo.root, "v1.2.0", {"continuation": {"objective": "Complete the approved delivery proof",
        "requests": [action]}}, "develop", NOW)
    assert snap["active"] is False and snap["versions_left"] == 0
    assert snap["rows"][0]["done"] == snap["rows"][0]["total"]
    result = load("status_report").select_report(snap, None, "turn-end")
    assert result["mode"] == "full" and result["report"].startswith("Waiting for you: Capture installed proof")
    assert "Required actions" in result["report"]
    assert "No duration estimate is available for the outstanding obligations" in result["report"]
    assert "N/A does not mean the objective is complete" in result["report"]


def test_controller_envelope_is_read_only_and_bound_to_repo_scope_and_session(snapshot_module, repo, tmp_path):
    record = tmp_path / "record.json"
    record.write_text(json.dumps({"session_id": "owner-1", "nonce": "run-1"}), encoding="utf-8")
    observation = {"objective": "Complete all approved work", "remaining_tasks": 4, "work": fixture_work()}
    frame = {"contract": "implementation-continuation-v1", "binding": {"repo_root": str(repo.root),
        "scope": "v1.2", "session_id": "owner-1", "run_nonce": "run-1", "record_path": str(record)}, "observation": observation,
        "disposition": load("continuation_state").reconcile(observation), "captured_at": NOW.timestamp()}
    path = tmp_path / "state.json"
    path.write_text(json.dumps(frame), encoding="utf-8")
    before = path.read_bytes()
    record_before = record.read_bytes()
    result = snapshot_module.continuation_overlay(path, repo.root, "v1.2", record)
    assert result["continuation"] == observation and path.read_bytes() == before
    for key, value in (("scope", "v9.9"), ("session_id", "other-owner"), ("run_nonce", "other-run"), ("repo_root", str(tmp_path / "other"))):
        bad = json.loads(before)
        bad["binding"][key] = value
        path.write_text(json.dumps(bad), encoding="utf-8")
        rejected_frame = path.read_bytes()
        with pytest.raises(ValueError):
            snapshot_module.continuation_overlay(path, repo.root, "v1.2", record)
        assert path.read_bytes() == rejected_frame and record.read_bytes() == record_before


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_snapshot_renderer_preserves_job_retirement_and_later_history(snapshot_module, repo, mode):
    old = fixture_jobs([{"id": f"old-{i}", "name": f"Retired validation {i}", "state": "running",
                         "started_at": "2026-11-20T11:00:00Z"} for i in range(2)])
    first = snapshot_module.build(repo.root, "v1.2", {"running": old}, "develop", NOW)
    terminal = [{**job, "status": "succeeded", "result_verified": True} for job in first["continuation"]["jobs"]]
    active = fixture_jobs([{"id": f"current-{i}", "name": f"Current validation {i}", "state": "running",
                            "started_at": "2026-11-20T11:30:00Z"} for i in range(3)])
    second = snapshot_module.build(repo.root, "v1.2", {"running": active, "continuation": {"jobs": terminal},
        "previous_continuation": first["continuation"]}, "develop", NOW)
    assert len(second["continuation"]["jobs"]) == 3
    assert second["continuation"]["completed_jobs"] == terminal
    report = load("status_report")
    assert report.continuation(second) == second["continuation"]
    output = report.render(json.loads(json.dumps(second)), mode)
    assert all(job["name"] not in output for job in old)
    assert all(job["name"] in output for job in active)
    third = snapshot_module.build(repo.root, "v1.2", {"running": active,
        "previous_continuation": second["continuation"]}, "develop", NOW)
    assert report.continuation(third)["completed_jobs"] == terminal
    assert len(report.continuation(third)["jobs"]) == 3


def retirement_request(source):
    request = {"id": "retiring-request", "title": "Retired owner obligation", "detail": "Private descriptive fixture"}
    if source == "manual_actions":
        request.update(prerequisites=["Review fixture"], steps=["Supply fixture result"],
                       expected_result="Fixture result received", acknowledgment="Reply with the fixture result")
    elif source == "decisions":
        request.update(options=[{"option": "A", "effect": "Continue fixture"}, {"option": "B", "effect": "Stop fixture"}],
                       reply="Reply A or B")
    return request


@pytest.mark.parametrize("source", ["manual_actions", "questions", "decisions"])
@pytest.mark.parametrize("mode", ["compact", "full"])
def test_snapshot_renderer_preserves_nested_request_resolution(snapshot_module, repo, source, mode):
    request = retirement_request(source)
    first = snapshot_module.build(repo.root, "v1.2", {source: [request]}, "develop", NOW)
    resolution = {"request_id": request["id"], "verified": True, "evidence": "Private descriptive resolution"}
    if source == "decisions":
        resolution["authority_receipt"] = "synthetic-descriptive-fixture-only"
    second = snapshot_module.build(repo.root, "v1.2", {source: [request], "work": fixture_work(),
        "continuation": {"resolutions": [resolution]}, "previous_continuation": first["continuation"]}, "develop", NOW)
    assert second["continuation"]["requests"] == []
    report = load("status_report")
    assert report.continuation(second) == second["continuation"]
    assert request["title"] not in report.render(json.loads(json.dumps(second)), mode)
    third = snapshot_module.build(repo.root, "v1.2", {"work": fixture_work(),
        "previous_continuation": second["continuation"]}, "develop", NOW)
    assert report.continuation(third)["requests"] == []
    assert report.continuation(third)["resolved_requests"] == [resolution]


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_snapshot_renderer_preserves_nested_condition_resolution(snapshot_module, repo, mode):
    condition = {"id": "endpoint", "title": "Retired endpoint outage", "evidence": "Private endpoint fixture failed",
                 "resume_when": "The fixture endpoint returns healthy", "observed_at": "2026-11-20T11:00:00Z"}
    first = snapshot_module.build(repo.root, "v1.2", {"external_conditions": [condition]}, "develop", NOW)
    resolution = {"condition_id": "endpoint", "verified": True, "evidence": "Private descriptive success"}
    second = snapshot_module.build(repo.root, "v1.2", {"work": fixture_work(), "external_conditions": [condition],
        "continuation": {"condition_resolutions": [resolution]}, "previous_continuation": first["continuation"]}, "develop", NOW)
    assert second["continuation"]["external_conditions"] == []
    report = load("status_report")
    assert report.continuation(second) == second["continuation"]
    assert condition["title"] not in report.render(json.loads(json.dumps(second)), mode)
    third = snapshot_module.build(repo.root, "v1.2", {"work": fixture_work(),
        "previous_continuation": second["continuation"]}, "develop", NOW)
    assert report.continuation(third)["external_conditions"] == []


def test_snapshot_renderer_pending_omission_and_unsigned_histories_do_not_retire_items(snapshot_module, repo):
    action = retirement_request("manual_actions")
    jobs = fixture_jobs([{"name": "Still pending process", "state": "running", "started_at": "2026-11-20T11:00:00Z"}])
    condition = {"id": "endpoint", "title": "Still pending endpoint", "evidence": "Private failed probe",
                 "resume_when": "The fixture endpoint succeeds", "observed_at": "2026-11-20T11:00:00Z"}
    first = snapshot_module.build(repo.root, "v1.2", {"manual_actions": [action], "running": jobs,
        "external_conditions": [condition]}, "develop", NOW)
    second = snapshot_module.build(repo.root, "v1.2", {"work": fixture_work(), "previous_continuation": first["continuation"],
        "continuation": {"completed_jobs": first["continuation"]["jobs"], "resolved_requests": [{"request_id": action["id"]}]}}, "develop", NOW)
    state = load("status_report").continuation(second)
    for key in ("requests", "jobs", "external_conditions"):
        assert state[key] == first["continuation"][key]
    assert state["completed_jobs"] == state["resolved_requests"] == []


def test_raw_continuation_observation_is_owned_by_producer_not_overlay(snapshot_module, repo):
    snap = snapshot_module.build(repo.root, "v1.2", {"work": fixture_work(),
        "continuation_observation": {"objective": "Untrusted replacement", "remaining_tasks": 0}}, "develop", NOW)
    assert snap["continuation_observation"]["objective"] == snap["continuation"]["objective"]
    assert snap["continuation_observation"]["remaining_tasks"] > 0
    assert load("status_report").continuation(snap) == snap["continuation"]


def test_running_work_with_tasks_gets_a_measured_estimate(snapshot_module, repo):
    overlay = {"running": fixture_jobs([{"name": "lane", "state": "implementing", "done": 4, "total": 10,
                            "started_at": "2026-11-18T12:00:00Z"}])}
    snap = snapshot_module.build(repo.root, "v1.2", overlay, "develop", NOW)
    assert snap["running"][0]["remaining"] == rows(snap)["v1.2.3"]["remaining"] != "N/A"


@pytest.mark.parametrize("item", [
    {"name": "CI", "state": "running"},
    {"name": "CI", "state": "running", "elapsed": "N/A", "started_at": "2026-11-20T11:30:00Z"},
    {"name": "CI", "state": "running", "remaining": "N/A", "started_at": "2026-11-20T11:30:00Z"},
])
def test_running_item_elapsed_is_measured_never_written(snapshot_module, repo, item):
    """A running item without a start time used to print N/A in Elapsed."""
    with pytest.raises(ValueError, match="started_at|measured"):
        snapshot_module.build(repo.root, "v1.2", {"running": [item]}, "develop", NOW)
