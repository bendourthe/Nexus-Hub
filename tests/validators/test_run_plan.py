"""Tests for scripts/run_plan.py (`nexus-hub run-plan`, v4.13.2 Phase 6).

Stub platform CLIs on PATH record their argv and advance a counter; a stub checker
(`NEXUS_RUNNER_CHECKER`) turns that counter into a verdict. Nothing launches a real
agent. The runner's own rules are asserted: resume until a terminal verdict,
stop on no progress, never create approvals, never pass a bypass flag, refuse an
unsafe plan path, one runner per record.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
RUNNER = REPO / "scripts" / "run_plan.py"
LEVERS = REPO / "docs" / "policy" / "completion-levers.json"
PLAN_REL = "docs/releases/v0/v0.2/plans/v0.2.0-demo.md"

sys.path.insert(0, str(REPO / "scripts"))
import run_plan

STUB_CHECKER = r'''
import json, os, sys
state = json.load(open(os.environ["STUB_STATE"], encoding="utf-8"))
counter_file = os.environ["STUB_COUNTER"]
count = int(open(counter_file).read()) if os.path.exists(counter_file) else 0
with open(os.environ["STUB_LOG"], "a", encoding="utf-8") as h:
    h.write(json.dumps(["checker", *sys.argv[1:]]) + "\n")
args = sys.argv[1:]
if args[:2] == ["record", "path"]:
    print(state.get("record") or "/nonexistent")
    sys.exit(0 if state.get("record") else 1)
if args[:2] == ["record", "block"]:
    sys.exit(3)
if args[0] == "check":
    if state.get("terminal"):
        print(state["terminal"][0]); sys.exit(state["terminal"][1])
    if count >= state.get("complete_at", 99):
        print("PLAN COMPLETE plan head nonce"); sys.exit(0)
    print("INCOMPLETE: task.T002"); sys.exit(1)
if args[0] == "score":
    print(f"{count if state.get('progress', True) else 0} head -"); sys.exit(0)
'''

STUB_CLI = r'''
import json, os, sys
with open(os.environ["STUB_LOG"], "a", encoding="utf-8") as h:
    h.write(json.dumps(["cli", os.path.basename(sys.argv[0]), *sys.argv[1:]]) + "\n")
counter_file = os.environ["STUB_COUNTER"]
count = int(open(counter_file).read()) if os.path.exists(counter_file) else 0
open(counter_file, "w").write(str(count + 1))
sys.exit(int(os.environ.get("STUB_CLI_RC", "0")))
'''


class Env:
    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.repo = tmp / "repo"
        self.bin = tmp / "bin"
        self.home = tmp / "home"
        for d in (self.repo, self.bin, self.home):
            d.mkdir()
        plan = self.repo / PLAN_REL
        plan.parent.mkdir(parents=True)
        plan.write_text("# Plan\n\n**Version**: v0.2.0\n\n- [ ] T001 a src/a.txt\n", encoding="utf-8")
        self.checker = tmp / "stub_checker.py"
        self.checker.write_text(STUB_CHECKER, encoding="utf-8")
        (tmp / "stub_cli.py").write_text(STUB_CLI, encoding="utf-8")
        self.record = tmp / "runs" / "abc.json"
        self.record.parent.mkdir()
        self.write_record([{"class": "push-merge", "text": "yes"}])
        self.state = {"record": str(self.record), "complete_at": 2, "progress": True}
        self.log = tmp / "log.jsonl"
        for name in ("claude", "codex", "opencode", "openclaw"):
            self.add_cli(name)

    def write_record(self, classes: list[dict]) -> None:
        self.record.write_text(json.dumps({"nonce": "n0nce", "approvals": {"classes": classes}}), encoding="utf-8")

    def add_cli(self, name: str) -> None:
        stub = self.tmp / "stub_cli.py"
        if os.name == "nt":
            (self.bin / f"{name}.cmd").write_text(f'@echo off\r\n"{sys.executable}" "{stub}" %*\r\n', encoding="utf-8")
        else:
            path = self.bin / name
            path.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{stub}" "$@"\n', encoding="utf-8")
            path.chmod(0o755)

    def run(self, *args: str, **env: str) -> subprocess.CompletedProcess:
        (self.tmp / "state.json").write_text(json.dumps(self.state), encoding="utf-8")
        full = dict(os.environ)
        full.update(PATH=str(self.bin) + os.pathsep + os.environ.get("PATH", ""), NEXUS_RUNNER_CHECKER=str(self.checker),
                    STUB_STATE=str(self.tmp / "state.json"), STUB_COUNTER=str(self.tmp / "counter"),
                    STUB_LOG=str(self.log), NEXUS_RUNNER_BACKOFF="0", HOME=str(self.home),
                    USERPROFILE=str(self.home), **env)
        return subprocess.run([sys.executable, str(RUNNER), *args], cwd=self.repo, env=full,
                              capture_output=True, text=True, timeout=120, check=False)

    def calls(self, kind: str) -> list[list[str]]:
        rows = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()] if self.log.exists() else []
        return [r[1:] for r in rows if r[0] == kind]


@pytest.fixture
def env(tmp_path: Path) -> Env:
    return Env(tmp_path)


def test_resumes_with_the_documented_flag_until_complete(env: Env) -> None:
    result = env.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().startswith("PLAN COMPLETE")
    clis = env.calls("cli")
    # Every cycle resumes the session whose upfront round created the record.
    assert clis[0][1:4] == ["exec", "resume", "--last"]
    assert clis[1][1:4] == ["exec", "resume", "--last"]
    assert clis[1][4] == f"Continue /implement {PLAN_REL}. The completion checker still reports it incomplete."


def test_no_progress_writes_a_blocker_and_stops(env: Env) -> None:
    env.state.update(progress=False, complete_at=99)
    result = env.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 3
    assert "BLOCKED: no-progress" in result.stdout
    blocks = [c for c in env.calls("checker") if c[:2] == ["record", "block"]]
    assert blocks and "no-progress" in blocks[0]
    assert len(env.calls("cli")) == 4


@pytest.mark.parametrize(
    ("verdict", "rc"),
    [("BLOCKED: platform-unavailable", 3), ("PAUSED: user", 4), ("PLAN COMPLETE plan head nonce", 0)],
)
def test_terminal_verdict_before_the_first_cycle_launches_nothing(
    env: Env, verdict: str, rc: int
) -> None:
    env.state["terminal"] = [verdict, rc]
    result = env.run(PLAN_REL, "--platform", "claude")
    assert result.returncode == rc, result.stderr
    assert result.stdout.strip() == verdict
    assert env.calls("cli") == []


def test_first_cycle_sets_a_headless_goal_naming_the_nonce(env: Env) -> None:
    env.run(PLAN_REL, "--platform", "claude")
    first = env.calls("cli")[0]
    assert first[1] == "-p"
    assert first[2].startswith("/goal ") and "n0nce" in first[2] and "PLAN COMPLETE" in first[2]


def test_openclaw_addresses_one_session_by_nonce(env: Env) -> None:
    env.run(PLAN_REL, "--platform", "openclaw")
    for call in env.calls("cli"):
        assert call[-2:] == ["--session-id", "n0nce"]


def test_never_creates_approvals_without_a_record(env: Env) -> None:
    env.state["record"] = None
    result = env.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 2
    assert "run /implement" in result.stderr
    assert env.calls("cli") == []


@pytest.mark.parametrize("plan", ["docs/releases/v0/v0.2/plans/a&b.md", "docs/plans/%PATH%.md", "notes/v0.2.0-demo.md"])
def test_unsafe_or_misplaced_plan_paths_are_refused(env: Env, plan: str) -> None:
    result = env.run(plan, "--platform", "codex")
    assert result.returncode == 2
    assert env.calls("cli") == []


def test_missing_platform_cli_is_reported(env: Env) -> None:
    result = env.run(PLAN_REL, "--platform", "kimi")
    assert result.returncode == 2
    assert "not installed" in result.stderr


def test_unavailable_platform_writes_a_blocker(env: Env) -> None:
    result = env.run(PLAN_REL, "--platform", "codex", STUB_CLI_RC="1")
    assert result.returncode == 3
    assert "platform-unavailable" in result.stdout


def test_configured_bypass_is_refused_unless_approved(env: Env) -> None:
    settings = env.home / ".claude" / "settings.json"
    settings.parent.mkdir()
    settings.write_text(json.dumps({"permissions": {"defaultMode": "bypassPermissions"}}), encoding="utf-8")
    refused = env.run(PLAN_REL, "--platform", "claude")
    assert refused.returncode == 2
    assert "bypasses approvals" in refused.stderr
    env.write_record([{"class": "unattended-with-bypass", "text": "yes"}])
    assert env.run(PLAN_REL, "--platform", "claude").returncode == 0


def test_a_second_runner_on_the_same_record_is_refused(env: Env) -> None:
    lock = env.record.with_name("abc.runner.lock")
    lock.write_text("123", encoding="utf-8")
    result = env.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 2
    assert "another runner" in result.stderr
    assert lock.exists()


@pytest.mark.parametrize("row", sorted(run_plan.TEMPLATES))
def test_no_template_carries_a_bypass_flag(row: str) -> None:
    launch, resume, _ = run_plan.TEMPLATES[row]
    for argv in (launch("prompt"), resume("prompt")):
        for arg in argv[1:]:
            assert arg not in run_plan.DENYLIST, f"{row} emits {arg}"


def test_offered_platforms_are_exactly_the_headless_verified_rows() -> None:
    rows = json.loads(LEVERS.read_text(encoding="utf-8"))["rows"]
    verified = {rid for rid, row in rows.items() if row["headless"]["status"] == "VERIFIED"}
    assert set(run_plan.TEMPLATES) == verified


@pytest.mark.parametrize("arg", ["a&b", "50%", 'say "hi"', "x|y"])
def test_cmd_shims_refuse_metacharacters(arg: str) -> None:
    with pytest.raises(run_plan.RunnerError):
        run_plan.check_argv(["C:/tools/agent.cmd", "-p", arg])


def test_denylisted_argument_is_refused_even_if_injected() -> None:
    with pytest.raises(run_plan.RunnerError):
        run_plan.check_argv(["/usr/bin/claude", "--dangerously-skip-permissions", "-p", "x"])
