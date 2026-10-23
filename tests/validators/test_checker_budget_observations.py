"""Offline regressions for unavailable minor observations and bounded shared work."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import check_plan_completion as ck
import completion_minor as cm
import completion_gate as gate
import run_plan as runner
import minor_close
import cleanup_merged


def unavailable(*args, **kwargs):
    raise cm.ObservationUnavailable("controller.ownership")


def test_unknown_verdict_has_no_numeric_score():
    unknown = cm.MinorVerdict("INCOMPLETE: repository", 1, minor=[("repository", "cannot-verify")])
    assert unknown.met() is None
    partial = cm.MinorVerdict("INCOMPLETE: x", 1, members=[cm.MemberResult("v0.5.0", exhausted=True)])
    assert partial.met() is None
    genuine = cm.MinorVerdict("INCOMPLETE: x", 1, minor=[("x", "unmet"), ("y", "met")])
    assert genuine.met() == 1


def test_initial_repository_unknown_preserves_json(monkeypatch, capsys):
    monkeypatch.setattr(cm, "minor_context", unavailable)
    assert ck.main(["check-minor", "v0.5", "--json"]) == 1
    lines = capsys.readouterr().out.splitlines()
    body = json.loads(lines[1])
    assert body["met"] is None and body["head"] is None
    assert body["minor"] == {"controller.ownership": "cannot-verify"}
    assert gate._json_score("\n".join(lines)) == []


def test_score_minor_unknown_is_not_zero(monkeypatch, capsys):
    monkeypatch.setattr(cm, "minor_context", lambda *a: SimpleNamespace(_git_out=lambda *a: "head"))
    monkeypatch.setattr(cm, "check_minor", lambda *a: cm.MinorVerdict("INCOMPLETE: repository", 1,
        minor=[("repository", "cannot-verify")]))
    assert cm.cmd_score_minor(ck, SimpleNamespace(repo=".", minor="v0.5", session=None)) == 1
    assert not capsys.readouterr().out.strip().split()[0].isdigit()


def test_gate_unknown_controller_is_documented_failure(monkeypatch, tmp_path):
    class Loader:
        def create_module(self, spec):
            return None
        def exec_module(self, module):
            module.resolve_minor_controller = unavailable
            module.Malformed = ck.Malformed
            module._minor_module = lambda: cm
    checker = tmp_path / "checker.py"
    checker.touch()
    monkeypatch.setattr(gate, "_checker", lambda: checker)
    monkeypatch.setattr(importlib.util, "spec_from_file_location",
        lambda name, path: importlib.util.spec_from_loader(name, Loader()))
    with pytest.raises(ValueError, match="cannot be verified"):
        gate._verified_minor_root(tmp_path / "record.json", {"repo_root": str(tmp_path / "work")}, "s")


def test_runner_unknown_controller_is_documented_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(ck, "resolve_minor_controller", unavailable)
    with pytest.raises(runner.RunnerError, match="could not be verified"):
        runner._verified_runner_minor(tmp_path / "record.json", {"session_id": "s"})


def test_minor_close_unknown_does_not_escape(monkeypatch, capsys):
    monkeypatch.setattr(minor_close, "_context", unavailable)
    assert minor_close.main(["status", "--minor", "v0.5"]) == minor_close.EXIT_REFUSED
    assert "cannot-verify" in capsys.readouterr().out


def test_cleanup_unknown_does_not_escape(monkeypatch, capsys):
    monkeypatch.setattr(cleanup_merged, "Host", lambda *a: object())
    monkeypatch.setattr(cleanup_merged, "_checker", lambda: ck)
    monkeypatch.setattr(cleanup_merged, "_own_record", unavailable)
    monkeypatch.setattr(cleanup_merged, "run_pass", lambda *a: pytest.fail("cleanup must not run"))
    assert cleanup_merged.main(["--dry-run", "--minor", "v0.5"]) == cleanup_merged.EXIT_BLOCKED
    assert "cannot-verify" in capsys.readouterr().out


@pytest.mark.parametrize("limit", [None, "3"])
def test_runner_outer_timeout_covers_minor_budget(monkeypatch, limit):
    if limit is None:
        monkeypatch.delenv("NEXUS_CHECK_MINOR_BUDGET_SECONDS", raising=False)
    else:
        monkeypatch.setenv("NEXUS_CHECK_MINOR_BUDGET_SECONDS", limit)
    seen = []
    def run(*args, **kwargs):
        seen.append(kwargs["timeout"])
        return SimpleNamespace(returncode=1, stdout="INCOMPLETE: x")
    monkeypatch.setattr(runner.subprocess, "run", run)
    runner._checker_run(["check-minor", "v0.5"])
    runner._checker_run(["score-minor", "v0.5"])
    assert seen == [cm.check_minor_seconds() + 5.0] * 2


def test_runner_timeout_returns_unavailable(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
    monkeypatch.setattr(runner.subprocess, "run", timeout)
    rc, out = runner._checker_run(["check-minor", "v0.5"])
    assert rc == 1 and out.startswith("INCOMPLETE:")
    assert runner._checker_run(["score-minor", "v0.5"]) == (-1, "")


@pytest.mark.parametrize("score", [None, "bad", "True head", "-1 head"])
def test_runner_unavailable_score_is_not_a_stall(score):
    # Unknown observations leave both counters intact; genuine zero is countable.
    assert runner.progress_score(0, score or "") is None
    assert runner.progress_score(0, "0 head -") == 0


def test_exact_duplicate_tips_are_observed_once(tmp_path):
    sha, moved = "a" * 40, "b" * 40
    calls = []
    def run(argv):
        verb = argv[3]
        calls.append((verb, tuple(argv[4:])))
        if verb == "for-each-ref":
            return 0, f"{sha} refs/heads/topic\n{sha} refs/remotes/origin/topic\n{moved} refs/heads/other\n"
        if verb == "ls-remote":
            return 0, f"{sha}\trefs/heads/topic\n{moved}\trefs/heads/topic\n"
        if verb == "merge-base":
            return 1, ""
        if verb == "diff":
            return 0, "docs/gaps.md\n"
        pytest.fail(str(argv))
    ctx = SimpleNamespace(root=tmp_path, git="git", run=run)
    assert cm.unmerged_changes(ctx, "develop", set()) == {
        "topic": {"docs/gaps.md"}, "other": {"docs/gaps.md"}}
    assert sum(v == "diff" for v, _ in calls) == 3
    assert sum(v == "merge-base" for v, _ in calls) == 3


@pytest.mark.parametrize("commit,codes,expected", [
    ("a" * 40, [0, 0], 2),
    ("develop", [0, 0], 4),
    ("a" * 12, [0, 0], 4),
    ("a" * 40, [-1, -1], 2),
    ("a" * 40, [0, -1, 0, 0], 4),
])
def test_only_positive_full_sha_ledger_blobs_are_reused(monkeypatch, tmp_path, commit, codes, expected):
    calls = []
    answers = iter(codes)
    def run(argv):
        calls.append(argv)
        rc = next(answers, 0)
        return rc, "ledger" if argv[3] == "show" else ""
    monkeypatch.setattr(cm, "ledger_rels", lambda *a: ["gaps.md"])
    monkeypatch.setattr(cm, "parse_ledger", lambda text: [SimpleNamespace(gid="WN-1"), SimpleNamespace(gid="WN-2")])
    ctx = SimpleNamespace(root=tmp_path, git="git", run=run)
    cm.items_at(ctx, commit, (0, 5), "WN-1")
    cm.items_at(ctx, commit, (0, 5), "WN-2")
    assert len(calls) == expected


def test_missing_immutable_blob_is_not_cached(monkeypatch, tmp_path):
    calls = []
    def run(argv):
        calls.append(argv)
        return 1, ""
    monkeypatch.setattr(cm, "ledger_rels", lambda *a: ["gaps.md"])
    ctx = SimpleNamespace(root=tmp_path, git="git", run=run)
    assert cm.items_at(ctx, "a" * 40, (0, 5), "WN-1") == ("unmet", [])
    assert cm.items_at(ctx, "a" * 40, (0, 5), "WN-2") == ("unmet", [])
    assert len(calls) == 2


@pytest.mark.parametrize("known", [False, True])
def test_runner_only_counts_observed_no_progress(monkeypatch, tmp_path, known):
    record = tmp_path / "record.json"
    record.write_text('{"approvals": {"classes": []}}', encoding="utf-8")
    scope = SimpleNamespace(minor=False, label="fixture", version="", path=lambda: ["path"],
        check=lambda: ["check"], score=lambda: ["score"])
    monkeypatch.setattr(runner, "Scope", lambda target: scope)
    monkeypatch.setattr(runner, "bypass_configured", lambda row: None)
    monkeypatch.setattr(runner, "resolve_binary", lambda name: "fake-cli")
    monkeypatch.setattr(runner, "check_argv", lambda argv: None)
    monkeypatch.setattr(runner, "goal_prompt", lambda value: None)
    monkeypatch.setattr(runner, "_launch", lambda *a: 0)
    def checker(args):
        if args == ["path"]:
            return 0, str(record)
        if args == ["score"]:
            return (0, "0 head -") if known else (-1, "")
        return 1, "INCOMPLETE: x"
    monkeypatch.setattr(runner, "_checker_run", checker)
    blocks = []
    monkeypatch.setattr(runner, "record_blocker", lambda *a: blocks.append(a) or 3)
    assert runner.run("fixture", "claude", 5) == (3 if known else 1)
    assert bool(blocks) == known


def test_gate_unknown_preserves_counter_and_shorter_caller_limit(monkeypatch, tmp_path):
    checker = tmp_path / "checker.py"
    checker.touch()
    record = {"schema": 2, "scope": "minor", "repo_root": str(tmp_path / "work"), "minor": "v0.5"}
    path = tmp_path / "record.json"
    monkeypatch.setattr(gate, "_read_payload", lambda: {})
    monkeypatch.setattr(gate, "_observe_permission", lambda payload: None)
    monkeypatch.setattr(gate, "_session", lambda payload: "s")
    monkeypatch.setattr(gate, "find_record", lambda session: (path, record))
    monkeypatch.setattr(gate, "_checker", lambda: checker)
    monkeypatch.setattr(gate, "_verified_minor_root", lambda *a: (tmp_path / "work", record))
    monkeypatch.setattr(gate, "_budget", lambda: 30)
    monkeypatch.setattr(gate, "usage_limit_stop", lambda *a: False)
    monkeypatch.setattr(gate, "emit_continue", lambda *a: 0)
    monkeypatch.setattr(gate, "_load_gate_state", lambda path: {"refusals": 3, "met": 12, "head": "old"})
    saved, calls, limits = [], [], []
    monkeypatch.setattr(gate, "_save_gate_state", lambda path, state: saved.append(state))
    monkeypatch.setenv("NEXUS_CHECK_MINOR_BUDGET_SECONDS", "3")
    def run(args, *rest):
        calls.append(args)
        limits.append(float(gate.os.environ["NEXUS_CHECK_MINOR_BUDGET_SECONDS"]))
        return 1, 'INCOMPLETE: x\n{"met": null, "head": null}'
    monkeypatch.setattr(gate, "_run_checker", run)
    assert gate.cmd_stop() == 0
    assert saved[0]["refusals"] == 3 and saved[0]["met"] == 12 and saved[0]["head"] == "old"
    assert all(args[0] != "record" for args in calls)
    assert limits == [3.0]


def test_runner_lease_unknown_after_successful_verification(monkeypatch, tmp_path):
    from contextlib import contextmanager

    record = {"session_id": "s"}
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(ck, "resolve_minor_controller", lambda *a: (SimpleNamespace(root=tmp_path), record))
    path = tmp_path / "record.json"
    ctx, verified = runner._verified_runner_minor(path, record)
    assert ctx.root == tmp_path and verified is record

    @contextmanager
    def transaction(record):
        raise cm.ObservationUnavailable("controller.ownership")
        yield

    monkeypatch.setattr(ck, "minor_transaction", transaction)
    with pytest.raises(runner.RunnerError, match="minor runner acquisition failed"):
        with runner.controller_runner_lock(SimpleNamespace(minor=True), path, verified):
            pytest.fail("the runner must not launch without a verified lease")
    assert not path.with_name(path.stem + ".runner.lock").exists()
