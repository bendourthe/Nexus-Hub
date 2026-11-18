"""lane_health classifies minor-run worker lanes from heartbeats and worktree state."""

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "catalog/skills/workflow/implement-phase/scripts/lane_health.py"
NOW = "2026-11-18T12:00:00Z"
NOW_EPOCH = 1795003200  # 2026-11-18T12:00:00Z
OLD_EPOCH = NOW_EPOCH - 3 * 86400
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
PLAN = "docs/plan.md"
PLAN_BODY = ("## Phase 1: Alpha\n\n- [x] T1 one\n\n## Phase 2: Beta\n\n- [ ] T2 two\n")


@pytest.fixture
def lh():
    spec = importlib.util.spec_from_file_location("lane_health", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(path, *args, env=None):
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True,
                   stdin=subprocess.DEVNULL, creationflags=NO_WINDOW, env=env)


def make_repo(path, commit_date, body=PLAN_BODY):
    path.mkdir(parents=True)
    (path / "docs").mkdir()
    (path / PLAN).write_text(body, encoding="utf-8")
    git(path, "init", "-q")
    git(path, "add", "-A")
    env = {**os.environ, "GIT_AUTHOR_DATE": commit_date, "GIT_COMMITTER_DATE": commit_date}
    git(path, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q",
        "-m", "init", env=env)


def member(version, worktree, nested=False):
    return {"version": version, "plan_path": PLAN, "tag": version,
            "implementation": {"branch": "feat/x", "worktree": str(worktree), "base_head": "0" * 40}}


def write_record(tmp_path, members, amendments=()):
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "rec1.json").write_text(json.dumps(
        {"members": members, "minor_amendment_members": list(amendments), "nested": {"deep": [amendments[:0]]}}),
        encoding="utf-8")
    return runs


def run_check(lh, runs, *extra):
    return json.loads(run_json(lh, runs, *extra))


def run_json(lh, runs, *extra, capsys=None):
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        lh.main(["check", "--record", "rec1", "--runs-dir", str(runs), "--now", NOW, "--json",
                 "--legacy-dir", str(runs / "no-legacy"), *extra])
    return buf.getvalue()


def lanes(report):
    return {lane["member"]: lane for lane in report["lanes"]}


def test_classifies_active_stalled_and_nested_members(lh, tmp_path):
    fresh = tmp_path / "fresh"
    old = tmp_path / "old"
    make_repo(fresh, "2026-11-18T11:50:00+00:00")
    make_repo(old, "2026-11-17T08:00:00+00:00")
    runs = write_record(tmp_path, [member("v1.0.1", fresh)], [member("v1.0.2", old)])
    found = lanes(run_check(lh, runs))
    assert found["v1.0.1"]["state"] == "active"
    assert found["v1.0.2"]["state"] == "stalled"
    assert "resume" in found["v1.0.2"] and "Phase 1 (Alpha)" in found["v1.0.2"]["resume"]
    assert found["v1.0.2"]["last_completed_phase"] == 1


def test_fresh_heartbeat_keeps_old_commit_lane_active(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-17T08:00:00+00:00")
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    lh.main(["beat", "--record", "rec1", "--runs-dir", str(runs), "--member", "v1.0.1",
             "--phase", "phase 2", "--state", "started", "--now", "2026-11-18T11:55:00Z"])
    lane = lanes(run_check(lh, runs))["v1.0.1"]
    assert lane["state"] == "active" and lane["heartbeat_phase"] == "phase-2"
    beat_file = runs / "rec1.lanes" / "v1.0.1.heartbeat"
    assert beat_file.read_text(encoding="utf-8") == "2026-11-18T11:55:00Z v1.0.1 phase-2 started\n"


def test_stale_heartbeat_and_threshold_is_configurable(lh, tmp_path):
    fresh = tmp_path / "fresh"
    make_repo(fresh, "2026-11-18T11:50:00+00:00")
    runs = write_record(tmp_path, [member("v1.0.1", fresh)])
    assert lanes(run_check(lh, runs, "--stale-minutes", "5"))["v1.0.1"]["state"] == "stalled"
    assert lanes(run_check(lh, runs, "--stale-minutes", "60"))["v1.0.1"]["state"] == "active"


def test_ready_heartbeat_marks_lane_finished_even_when_old(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-10T08:00:00+00:00")
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    lh.main(["beat", "--record", "rec1", "--runs-dir", str(runs), "--member", "v1.0.1",
             "--phase", "all", "--state", "implementation-ready", "--now", "2026-11-10T09:00:00Z"])
    lane = lanes(run_check(lh, runs))["v1.0.1"]
    assert lane["state"] == "ready" and lane["signal"] == "heartbeat"


def test_missing_worktree_and_missing_heartbeat_is_unknown(lh, tmp_path):
    runs = write_record(tmp_path, [member("v1.0.1", tmp_path / "gone")])
    lane = lanes(run_check(lh, runs))["v1.0.1"]
    assert lane["state"] == "unknown" and lane["worktree_present"] is False
    assert lane["last_heartbeat"] is None and "resume" not in lane


def test_dirty_worktree_is_reported_in_resume_instruction(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-17T08:00:00+00:00")
    scratch = old / "scratch.txt"
    scratch.write_text("wip", encoding="utf-8")
    os.utime(scratch, (OLD_EPOCH, OLD_EPOCH))
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    lane = lanes(run_check(lh, runs))["v1.0.1"]
    assert lane["dirty"] is True and "uncommitted edits" in lane["resume"]


def test_malformed_heartbeat_lines_are_skipped(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-17T08:00:00+00:00")
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    lane_dir = runs / "rec1.lanes"
    lane_dir.mkdir()
    (lane_dir / "v1.0.1.heartbeat").write_text(
        "2026-11-18T11:58:00Z v1.0.1 phase-1 ended\nnot a heartbeat line\n", encoding="utf-8")
    assert lanes(run_check(lh, runs))["v1.0.1"]["state"] == "active"


def test_merged_lane_is_finished(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-17T08:00:00+00:00")
    git(old, "tag", "v1.0.1")
    runs = write_record(tmp_path, [{**member("v1.0.1", old), }])
    data = json.loads((runs / "rec1.json").read_text(encoding="utf-8"))
    data["repo_root"] = str(old)
    (runs / "rec1.json").write_text(json.dumps(data), encoding="utf-8")
    assert lanes(run_check(lh, runs))["v1.0.1"]["state"] == "finished"


def test_cli_prints_table_json_and_never_modifies_the_record(tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-17T08:00:00+00:00")
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    record = runs / "rec1.json"
    before = record.read_bytes()
    done = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--record", "rec1", "--runs-dir", str(runs),
         "--now", NOW], capture_output=True, text=True, check=True,
        stdin=subprocess.DEVNULL, creationflags=NO_WINDOW)
    assert "STALLED v1.0.1" in done.stdout and "member" in done.stdout.splitlines()[1]
    payload = json.loads(done.stdout.strip().splitlines()[-1])
    assert payload["stalled"] == ["v1.0.1"]
    assert record.read_bytes() == before
    assert not (runs / "rec1.lanes").exists()


def test_unknown_record_exits_with_message(lh, tmp_path):
    with pytest.raises(SystemExit) as exc:
        lh.main(["check", "--record", "nope", "--runs-dir", str(tmp_path)])
    assert "no run record" in str(exc.value)


PLAN_WAITING = ("## Phase 1: Alpha\n\n- [x] T1 build\n- [ ] Phase exit item\n\n## Phase 2: Final\n\n"
                "- [x] T2 review\n- [ ] T3 Testing and Stabilization\n- [ ] T4 Publication and integration\n")
PLAN_OPEN_WORK = PLAN_WAITING.replace("- [ ] T3 Testing and Stabilization", "- [ ] T3 Tier 3 deep pass")


def test_lane_waiting_only_on_publication_is_ready_not_stalled(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-17T08:00:00+00:00", PLAN_WAITING)
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    assert lanes(run_check(lh, runs))["v1.0.1"]["state"] == "ready"


def test_lane_with_real_open_work_stays_stalled(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-17T08:00:00+00:00", PLAN_OPEN_WORK)
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    assert lanes(run_check(lh, runs))["v1.0.1"]["state"] == "stalled"


def test_dirty_worktree_with_recent_file_change_is_active(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-17T08:00:00+00:00")
    edit = old / "docs" / "plan.md"
    edit.write_text(PLAN_BODY + "\nedit\n", encoding="utf-8")
    os.utime(edit, (NOW_EPOCH - 600, NOW_EPOCH - 600))
    fresh = old / "new.txt"
    fresh.write_text("x", encoding="utf-8")
    os.utime(fresh, (NOW_EPOCH - 300, NOW_EPOCH - 300))
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    lane = lanes(run_check(lh, runs))["v1.0.1"]
    assert lane["state"] == "active" and lane["signal"] == "file-mtime" and lane["dirty"] is True
    os.utime(fresh, (OLD_EPOCH, OLD_EPOCH))
    os.utime(edit, (OLD_EPOCH, OLD_EPOCH))
    lane = lanes(run_check(lh, runs))["v1.0.1"]
    assert lane["state"] == "stalled" and lane["signal"] == "commit"


def test_legacy_heartbeat_location_is_a_fallback(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-17T08:00:00+00:00")
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "v1.0.1-heartbeat.log").write_text(
        "2026-11-18T11:40:00Z phase-1 started\n2026-11-18T11:50:00Z phase-1 committed abc123\n",
        encoding="utf-8")
    report = json.loads(run_json(lh, runs, "--legacy-dir", str(legacy)))
    lane = lanes(report)["v1.0.1"]
    assert lane["state"] == "active" and lane["legacy_heartbeat"] is True
    assert lane["heartbeat_phase"] == "phase-1" and lane["heartbeat_state"] == "committed"
    # The official file wins once it exists.
    lh.main(["beat", "--record", "rec1", "--runs-dir", str(runs), "--member", "v1.0.1",
             "--phase", "p", "--state", "ready", "--now", "2026-11-18T11:51:00Z"])
    report = json.loads(run_json(lh, runs, "--legacy-dir", str(legacy)))
    assert lanes(report)["v1.0.1"]["legacy_heartbeat"] is False
    assert lanes(report)["v1.0.1"]["state"] == "ready"


def test_blocked_heartbeat_keeps_old_lane_blocked_until_cleared(lh, tmp_path):
    old = tmp_path / "old"
    make_repo(old, "2026-11-10T08:00:00+00:00")
    runs = write_record(tmp_path, [member("v1.0.1", old)])
    lh.main(["beat", "--record", "rec1", "--runs-dir", str(runs), "--member", "v1.0.1",
             "--phase", "phase-2", "--state", "blocked:coordinator-deltas",
             "--now", "2026-11-10T09:00:00Z"])
    lane = lanes(run_check(lh, runs))["v1.0.1"]
    assert lane["state"] == "blocked" and lane["detail"] == "coordinator-deltas"
    assert "resume" not in lane
    lh.main(["beat", "--record", "rec1", "--runs-dir", str(runs), "--member", "v1.0.1",
             "--phase", "phase-2", "--state", "started", "--now", "2026-11-10T10:00:00Z"])
    lane = lanes(run_check(lh, runs))["v1.0.1"]
    assert lane["state"] == "stalled" and lane["detail"] is None
