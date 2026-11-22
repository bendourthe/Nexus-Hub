"""lane_health flags idle minor-run members: unadmitted, resumable and needs-user."""

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "catalog/skills/workflow/implement-phase/scripts"
NOW = datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def lh():
    return load("lane_health")


def lane(member, state="active", detail=None, beat="2026-11-18T09:00:00+00:00"):
    return {
        "member": member,
        "state": state,
        "detail": detail,
        "heartbeat_state": f"blocked:{detail}" if detail else None,
        "last_heartbeat": beat,
        "idle_minutes": 180,
    }


def test_unadmitted_member_without_lane_is_idle(lh):
    idle = lh.classify_idle(
        [lane("v1.0.1")], ["v1.0.0", "v1.0.1", "v1.0.2"], {"v1.0.0"}.__contains__, NOW
    )
    assert idle == [
        {
            "member": "v1.0.2",
            "kind": "unadmitted",
            "detail": "in the minor record with no worker lane",
        }
    ]


def test_blocked_lane_whose_prerequisite_shipped_is_resumable(lh):
    lanes = [lane("v1.0.3", "blocked", "T027-waits-v1.0.1-merge")]
    idle = lh.classify_idle(lanes, ["v1.0.3"], {"v1.0.1"}.__contains__, NOW)
    assert [(i["member"], i["kind"]) for i in idle] == [("v1.0.3", "resumable")]


def test_blocked_on_unreleased_member_is_not_idle(lh):
    lanes = [lane("v1.0.3", "blocked", "waits-v1.0.2")]
    assert lh.classify_idle(lanes, ["v1.0.3"], lambda v: False, NOW) == []


def test_blocked_on_user_past_threshold_needs_user(lh):
    lanes = [lane("v1.0.4", "blocked", "coordinator-and-sensitive-deltas")]
    idle = lh.classify_idle(lanes, ["v1.0.4"], lambda v: False, NOW)
    assert idle[0]["kind"] == "needs-user" and "180 min" in idle[0]["detail"]
    assert (
        lh.classify_idle(
            lanes, ["v1.0.4"], lambda v: False, NOW, needs_user_minutes=240
        )
        == []
    )


def test_healthy_run_has_no_idle_members(lh):
    lanes = [lane("v1.0.1"), lane("v1.0.2", "finished")]
    assert lh.classify_idle(lanes, ["v1.0.1", "v1.0.2"], lambda v: False, NOW) == []


def test_record_versions_reads_signed_and_amended_members(lh):
    data = {
        "members": [{"version": "v1.0.0"}, "v1.0.1"],
        "minor_amendment_members": [{"version": "v1.0.2"}, {"version": "bad"}],
    }
    assert lh.record_versions(data) == ["v1.0.0", "v1.0.1", "v1.0.2"]


def test_notice_prints_one_line_for_this_repository(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "-q", str(repo)],
        check=True,
        stdin=subprocess.DEVNULL,
        creationflags=NO_WINDOW,
    )
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "rec.json").write_text(
        json.dumps(
            {
                "minor": "v1.0",
                "repo_root": str(repo),
                "completed": None,
                "pause": None,
                "members": [{"version": "v1.0.0"}],
                "minor_amendment_members": [{"version": "v1.0.1"}],
            }
        ),
        encoding="utf-8",
    )
    done = subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCRIPTS / "lane_health.py"),
            "notice",
            "--repo",
            str(repo),
            "--runs-dir",
            str(runs),
        ],
        capture_output=True,
        text=True,
        check=True,
        stdin=subprocess.DEVNULL,
        creationflags=NO_WINDOW,
    )
    assert done.stdout.strip() == (
        "Minor v1.0: 2 idle members (v1.0.0 unadmitted, v1.0.1 unadmitted). Dispatch eligible "
        "members (implement-phase runbook, Refill available slots)."
    )
    other = tmp_path / "other"
    other.mkdir()
    subprocess.run(
        ["git", "init", "-q", str(other)],
        check=True,
        stdin=subprocess.DEVNULL,
        creationflags=NO_WINDOW,
    )
    quiet = subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCRIPTS / "lane_health.py"),
            "notice",
            "--repo",
            str(other),
            "--runs-dir",
            str(runs),
        ],
        capture_output=True,
        text=True,
        check=True,
        stdin=subprocess.DEVNULL,
        creationflags=NO_WINDOW,
    )
    assert quiet.stdout == ""


def test_report_shows_idle_section_only_when_present():
    report = load("status_report")
    data = json.loads(
        (SCRIPTS.parent / "references/status-snapshot.json").read_text(encoding="utf-8")
    )
    for mode in ("full", "compact"):
        assert "Idle lanes" not in report.render(data, mode)
    data["idle_lanes"] = [
        {"member": "v1.0.2", "kind": "resumable", "detail": "v1.0.1 released"}
    ]
    assert "v1.0.2" in report.render(data, "full") and "Idle lanes" in report.render(
        data, "compact"
    )
    data["idle_lanes"] = [{"member": "v1.0.2", "kind": "bogus", "detail": "x"}]
    with pytest.raises(ValueError):
        report.render(data, "full")


def test_structured_waits_merge_is_read_directly(lh):
    lanes = [lane("v1.0.3", "blocked", "waits-merge:v1.0.1")]
    assert lh.classify_idle(lanes, ["v1.0.3"], {"v1.0.1"}.__contains__, NOW)[0]["kind"] == "resumable"
    assert lh.classify_idle(lanes, ["v1.0.3"], lambda v: False, NOW) == []


def test_structured_needs_user_is_reported_without_waiting(lh):
    fresh = [lane("v1.0.4", "blocked", "needs-user:workflow-grant", beat="2026-11-18T11:59:00+00:00")]
    idle = lh.classify_idle(fresh, ["v1.0.4"], lambda v: False, NOW)
    assert idle == [{"member": "v1.0.4", "kind": "needs-user", "detail": "workflow-grant for 1 min"}]


def test_free_text_blocker_needs_user_only_after_threshold(lh):
    fresh = [lane("v1.0.5", "blocked", "coordinator-deltas", beat="2026-11-18T11:30:00+00:00")]
    assert lh.classify_idle(fresh, ["v1.0.5"], lambda v: False, NOW) == []


@pytest.mark.parametrize("state, ok", [
    ("blocked:waits-merge:v4.15.5", True), ("blocked:needs-user:workflow-grant", True),
    ("blocked:coordinator-deltas", True), ("blocked:waits-merge:soon", False),
    ("blocked:needs-user:", False),
])
def test_beat_validates_structured_blocked_states(lh, tmp_path, state, ok):
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / "rec.json").write_text(json.dumps({"members": []}), encoding="utf-8")
    argv = ["beat", "--record", "rec", "--runs-dir", str(runs), "--member", "v1.0.1",
            "--phase", "wait", "--state", state]
    if ok:
        assert lh.main(argv) == 0
        assert (runs / "rec.lanes" / "v1.0.1.heartbeat").read_text(encoding="utf-8").split()[-1] == state
    else:
        with pytest.raises(SystemExit):
            lh.main(argv)
        assert not (runs / "rec.lanes" / "v1.0.1.heartbeat").exists()
