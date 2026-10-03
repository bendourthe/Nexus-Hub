"""The completion gate and usage-guard on one turn end (v4.13.7 Phase 7, finding F3).

Both hooks run on Stop in catalog/hooks/settings.json order (completion-gate,
then usage-guard), and on Cursor's native stop in hooks.json order. These tests
drive both against one full-run record with a stub checker, a primed usage-probe
cache (no network), and the real hook files from catalog/hooks:

- at 99.5% with a usage-limit handoff written after the gate's last refusal, the
  turn ends: the gate allows the stop without counting a refusal or writing a
  blocker, and the guard stays silent;
- at 99.5% without the handoff, the guard's continuation asks for it (the gate
  refuses as it always did);
- a usage-limit handoff with the probe at 50% is a fake: the gate refuses as today;
- usage-guard and the probe planted inside the repository are never trusted.

The gate's `run` fixture is parametrized over the .sh and .ps1 adapters, so each
assertion is also an exit-code parity check.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
REPO = HOOKS.parents[1]
CORE = REPO / "scripts" / "completion_gate.py"
SESSION = "usage-gate-session"
NOTE = "the run stopped for a usage-limit handoff"

STUB_CHECKER = '''
import json, os, sys
log = os.environ.get("GATE_STUB_LOG")
if log:
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(sys.argv[1:]) + "\\n")
command = sys.argv[1]
if command == "check":
    print("INCOMPLETE: task.T002")
    sys.exit(1)
if command == "score":
    print("3 abc -")
    sys.exit(0)
sys.exit(3)
'''

PLATFORMS = {
    "claude": {
        "probe": "claude",
        "source": "anthropic-oauth-usage",
        "window": "weekly",
    },
    "cursor": {
        "probe": "cursor",
        "source": "cursor-dashboard-rpc",
        "window": "monthly",
    },
}


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class World:
    def __init__(self, tmp: Path) -> None:
        self.root = tmp / "home"
        self.scripts = self.root / ".nexus-hub" / "scripts"
        self.runs = self.root / ".nexus-hub" / "runs"
        self.repo = tmp / "repo"
        self.log = tmp / "checker.log"
        self.scripts.mkdir(parents=True)
        self.runs.mkdir(parents=True)
        (self.repo / ".git").mkdir(parents=True)
        shutil.copy(CORE, self.scripts / "completion_gate.py")
        (self.scripts / "check_plan_completion.py").write_text(STUB_CHECKER, encoding="utf-8")
        record = {
            "schema": 1,
            "session_id": SESSION,
            "repo_root": str(self.repo),
            "plan": "docs/releases/v0/v0.2/plans/v0.2.0-demo.md",
            "created": _iso(time.time() - 3600),
        }
        self.record = self.runs / "abc.json"
        self.record.write_text(json.dumps(record), encoding="utf-8")

    def env(self) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("NEXUS_", "GATE_STUB", "CLAUDE_", "QWEN_"))}
        env.update(HOME=str(self.root), USERPROFILE=str(self.root), GATE_STUB_LOG=str(self.log))
        return env

    def prime(self, platform: str, percent: float) -> None:
        spec = PLATFORMS[platform]
        cache = self.root / ".nexus-hub" / "state" / "usage-probe" / f"{spec['probe']}.json"
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps({
                "schema_version": 1,
                "platform": spec["probe"],
                "data_at": time.time(),
                "windows": [{"name": spec["window"], "percent": percent, "resets_at": None, "source": spec["source"]}],
            }),
            encoding="utf-8",
        )

    def handoff(self, stamp: float, trigger: str = "usage-limit weekly 99.5") -> None:
        path = self.repo / ".nexus-hub" / "handoff.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Handoff | {_iso(stamp)} | claude | {trigger}\n\n## Goal\n", encoding="utf-8")

    def gate_state(self) -> dict:
        path = self.runs / "abc.gate.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def blockers(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        calls = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        return [c for c in calls if c[:2] == ["record", "block"]]


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


def stop_payload(platform: str, world: World) -> dict:
    if platform == "cursor":
        return {
            "hook_event_name": "stop", "conversation_id": SESSION, "cursor_version": "2.4.0",
            "loop_count": 0, "status": "completed", "workspace_roots": [str(world.repo)],
        }
    return {
        "hook_event_name": "Stop", "session_id": SESSION, "cwd": str(world.repo),
        "permission_mode": "default", "scratchpad_dir": "/tmp/s", "stop_hook_active": False,
    }


@pytest.fixture(params=["sh", "ps1"])
def turn_end(request, bash_bin: str, powershell_bin: str, world: World):
    """Run both Stop hooks in registration order; return (gate, guard) results."""

    def gate_argv(hooks_dir: Path) -> list[str]:
        if request.param == "sh":
            return [bash_bin, str(hooks_dir / "completion-gate.sh")]
        return [powershell_bin, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(hooks_dir / "completion-gate.ps1")]

    def _run(platform: str, hooks_dir: Path = HOOKS):
        body = json.dumps(stop_payload(platform, world))
        common = dict(input=body, text=True, capture_output=True, cwd=str(world.repo), env=world.env(), timeout=120, check=False)
        if platform == "cursor":
            compat = [sys.executable, str(HOOKS / "cursor-hook-compat.py")]
            gate = subprocess.run([*compat, *gate_argv(hooks_dir)], **common)
            guard = subprocess.run([*compat, sys.executable, str(hooks_dir / "usage-guard.py")], **common)
        else:
            gate = subprocess.run(gate_argv(hooks_dir), **common)
            guard = subprocess.run([sys.executable, str(hooks_dir / "usage-guard.py")], **common)
        return gate, guard

    return _run


def _out(result: subprocess.CompletedProcess[str]) -> dict:
    text = result.stdout.strip()
    return json.loads(text) if text else {}


def _continues(platform: str, out: dict) -> str | None:
    if platform == "cursor":
        return out.get("followup_message")
    return out.get("reason") if out.get("decision") == "block" else None


@pytest.mark.parametrize("platform", ["claude", "cursor"])
def test_usage_limit_handoff_ends_the_turn_without_a_blocker(turn_end, world, platform):
    world.prime(platform, 99.5)
    gate, guard = turn_end(platform)
    assert "full /implement run is not complete" in (_continues(platform, _out(gate)) or "")
    assert (_continues(platform, _out(guard)) or "").startswith("Usage limit:")
    refusals = world.gate_state().get("refusals")
    updated = world.gate_state().get("updated")

    world.handoff(time.time() + 2)
    gate, guard = turn_end(platform)

    assert gate.returncode == 0
    assert _continues(platform, _out(gate)) is None
    assert NOTE in gate.stderr
    assert _continues(platform, _out(guard)) is None
    assert world.gate_state().get("refusals") == refusals, "no refusal counted"
    assert world.gate_state().get("updated") == updated
    assert world.blockers() == [], "no no-progress blocker written"
    assert json.loads(world.record.read_text(encoding="utf-8")).get("status") is None


@pytest.mark.parametrize("platform", ["claude", "cursor"])
def test_without_the_handoff_the_guard_asks_for_it(turn_end, world, platform):
    world.prime(platform, 99.5)
    gate, guard = turn_end(platform)
    message = _continues(platform, _out(guard))
    assert message and "run the session-handoff procedure (/handoff)" in message
    assert _continues(platform, _out(gate)) is not None, "the gate refuses as it always did"
    assert NOTE not in gate.stderr


@pytest.mark.parametrize("platform", ["claude", "cursor"])
def test_a_fake_handoff_below_the_threshold_is_refused_as_today(turn_end, world, platform):
    world.prime(platform, 50)
    world.handoff(time.time() + 2)
    gate, guard = turn_end(platform)
    assert "full /implement run is not complete" in (_continues(platform, _out(gate)) or "")
    assert NOTE not in gate.stderr
    assert _continues(platform, _out(guard)) is None
    assert world.gate_state().get("updated"), "the refusal was recorded as today"


def test_a_handoff_older_than_the_last_refusal_does_not_count(turn_end, world):
    world.prime("claude", 99.5)
    gate, _ = turn_end("claude")
    assert _out(gate).get("decision") == "block"
    world.handoff(time.time() - 600)  # dated before that refusal
    gate, _ = turn_end("claude")
    assert _out(gate).get("decision") == "block"
    assert NOTE not in gate.stderr


@pytest.mark.parametrize("trigger", ["checkpoint", "manual"])
def test_a_non_usage_limit_handoff_does_not_count(turn_end, world, trigger):
    world.prime("claude", 99.5)
    world.handoff(time.time() + 2, trigger=trigger)
    gate, _ = turn_end("claude")
    assert _out(gate).get("decision") == "block"


def test_guard_and_probe_planted_in_the_repository_are_ignored(turn_end, world):
    planted = world.repo / ".claude" / "hooks"
    planted.mkdir(parents=True)
    for name in ("completion-gate.sh", "completion-gate.ps1", "usage-guard.py", "_usage_probe.py", "cursor-hook-compat.py"):
        shutil.copy2(HOOKS / name, planted / name)
    world.prime("claude", 99.5)
    world.handoff(time.time() + 2)
    gate, _ = turn_end("claude", hooks_dir=planted)
    assert _out(gate).get("decision") == "block"
    assert NOTE not in gate.stderr


def test_an_unrecognized_platform_keeps_todays_behavior(turn_end, world, bash_bin):
    world.prime("claude", 99.5)
    world.handoff(time.time() + 2)
    body = {"hook_event_name": "Stop", "session_id": SESSION, "cwd": str(world.repo), "timestamp": _iso(time.time()),
            "permission_mode": "default"}  # Qwen-shaped
    gate = subprocess.run([bash_bin, str(HOOKS / "completion-gate.sh")], input=json.dumps(body), text=True,
                          capture_output=True, cwd=str(world.repo), env=world.env(), timeout=120, check=False)
    assert _out(gate).get("decision") == "block"
