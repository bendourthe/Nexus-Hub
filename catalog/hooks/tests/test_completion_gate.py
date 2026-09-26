"""Tests for the completion-gate and approval-capture hooks (v4.13.2 Phase 4).

Both adapters are thin: they call the installed core
`~/.nexus-hub/scripts/completion_gate.py`. Each test installs that core into a
throwaway home beside a STUB checker whose verdict comes from the environment, so
the gate's own decisions are tested without building git fixtures (the real
checker has its own suite in tests/validators/test_check_plan_completion.py).

The `run` fixture is parametrized over both implementations, so every behavioral
assertion is also a `.sh` / `.ps1` parity assertion.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
REPO = HOOKS.parents[1]
CORE = REPO / "scripts" / "completion_gate.py"
SESSION = "gate-session"

STUB_CHECKER = '''
import json, os, sys
log = os.environ.get("GATE_STUB_LOG")
if log:
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(sys.argv[1:]) + "\\n")
command = sys.argv[1]
if command == "check":
    print(os.environ.get("GATE_STUB_LINE", "INCOMPLETE: task.T002 gaps.version"))
    sys.exit(int(os.environ.get("GATE_STUB_RC", "1")))
if command == "score":
    print(os.environ.get("GATE_STUB_SCORE", "3 abc -"))
    sys.exit(0)
sys.exit(3)
'''


class Home:
    def __init__(self, tmp: Path) -> None:
        self.root = tmp / "home"
        self.scripts = self.root / ".nexus-hub" / "scripts"
        self.runs = self.root / ".nexus-hub" / "runs"
        self.repo = tmp / "repo"
        self.log = tmp / "checker.log"
        self.scripts.mkdir(parents=True)
        self.runs.mkdir(parents=True)
        self.repo.mkdir()
        shutil.copy(CORE, self.scripts / "completion_gate.py")
        (self.scripts / "check_plan_completion.py").write_text(STUB_CHECKER, encoding="utf-8")
        record = {"schema": 1, "session_id": SESSION, "repo_root": str(self.repo),
                  "plan": "docs/releases/v0/v0.2/plans/v0.2.0-demo.md"}
        (self.runs / "abc.json").write_text(json.dumps(record), encoding="utf-8")

    def env(self, **extra: str) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("NEXUS_", "GATE_STUB"))}
        env.update(HOME=str(self.root), USERPROFILE=str(self.root), GATE_STUB_LOG=str(self.log))
        env.update(extra)
        return env

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def home(tmp_path: Path) -> Home:
    return Home(tmp_path)


@pytest.fixture(params=["sh", "ps1"])
def run(request, bash_bin: str, powershell_bin: str, home: Home):
    def _run(hook: str, payload: dict | str, cwd: Path | None = None, **env: str):
        if request.param == "sh":
            argv = [bash_bin, str(HOOKS / f"{hook}.sh")]
        else:
            argv = [powershell_bin, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HOOKS / f"{hook}.ps1")]
        body = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run(argv, input=body, text=True, capture_output=True, cwd=str(cwd or home.repo),
                              env=home.env(**env), timeout=120, check=False)

    return _run


def claude_stop(**extra) -> dict:
    return {"hook_event_name": "Stop", "session_id": SESSION, "stop_hook_active": False, **extra}


def test_incomplete_run_blocks_with_top_level_decision(run) -> None:
    result = run("completion-gate", claude_stop())
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    assert out["decision"] == "block"
    assert "task.T002 gaps.version" in out["reason"]


def test_stop_hook_active_never_releases(run) -> None:
    result = run("completion-gate", claude_stop(stop_hook_active=True))
    assert json.loads(result.stdout)["decision"] == "block"


@pytest.mark.parametrize(
    ("payload", "key", "value"),
    [
        ({"hook_event_name": "stop", "conversation_id": SESSION, "cursor_version": "2.4", "loop_count": 0},
         "followup_message", None),
        ({"hook_event_name": "AfterAgent", "session_id": SESSION}, "decision", "deny"),
    ],
    ids=["cursor", "gemini-cli"],
)
def test_payload_shape_selects_the_documented_format(run, payload: dict, key: str, value) -> None:
    out = json.loads(run("completion-gate", payload).stdout)
    assert key in out
    if value is not None:
        assert out[key] == value


def test_kimi_payload_continues_with_exit_2(run) -> None:
    payload = {"hook_event_name": "Stop", "session_id": SESSION, "session_title": "t", "client_type": "cli", "cwd": "."}
    result = run("completion-gate", payload)
    assert result.returncode == 2
    assert result.stdout.strip() == ""
    assert "task.T002" in result.stderr


@pytest.mark.parametrize(
    ("fmt", "probe"),
    [
        ("vscode-hook-specific-output", lambda o: o["hookSpecificOutput"]["decision"] == "block"),
        ("antigravity-continue", lambda o: o["decision"] == "continue"),
    ],
)
def test_explicit_format_overrides_inference(run, fmt: str, probe) -> None:
    result = run("completion-gate", claude_stop(), NEXUS_GATE_FORMAT=fmt)
    assert probe(json.loads(result.stdout))


@pytest.mark.parametrize(("rc", "line"), [("0", "PLAN COMPLETE p h n"), ("3", "BLOCKED: no-progress"), ("4", "PAUSED")])
def test_terminal_verdicts_allow_the_stop(run, rc: str, line: str) -> None:
    result = run("completion-gate", claude_stop(), GATE_STUB_RC=rc, GATE_STUB_LINE=line)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_other_session_is_never_touched(run, home: Home) -> None:
    result = run("completion-gate", claude_stop(session_id="someone-else"))
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert home.calls() == []


def test_malformed_payload_is_ignored(run) -> None:
    result = run("completion-gate", "not json")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_no_progress_releases_and_writes_a_blocker(run, home: Home) -> None:
    decisions = [run("completion-gate", claude_stop()).stdout.strip() for _ in range(4)]
    assert all(json.loads(d)["decision"] == "block" for d in decisions[:3])
    assert decisions[3] == ""
    blocks = [c for c in home.calls() if c[:2] == ["record", "block"]]
    assert blocks and "no-progress" in blocks[0]


def test_malformed_plan_writes_record_tampered(run, home: Home) -> None:
    result = run("completion-gate", claude_stop(), GATE_STUB_RC="2", GATE_STUB_LINE="error")
    assert result.returncode == 0
    assert any("record-tampered" in c for c in home.calls() if c[:2] == ["record", "block"])


def test_missing_checker_allows_the_stop(run, home: Home) -> None:
    (home.scripts / "check_plan_completion.py").unlink()
    result = run("completion-gate", claude_stop())
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert "allowing stop" in result.stderr


@pytest.mark.parametrize("control", [("NEXUS_DISABLED_HOOKS", "completion-gate"), ("NEXUS_HOOK_PROFILE", "minimal")])
def test_runtime_controls_disable_the_gate(run, home: Home, control: tuple[str, str]) -> None:
    result = run("completion-gate", claude_stop(), **{control[0]: control[1]})
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    assert home.calls() == []


def test_a_planted_core_in_the_repository_never_runs(run, home: Home) -> None:
    marker = home.repo / "planted-ran"
    planted = home.repo / "scripts"
    planted.mkdir()
    (planted / "completion_gate.py").write_text(
        f"open({str(marker)!r}, 'w').write('x')\n", encoding="utf-8"
    )
    run("completion-gate", claude_stop(), cwd=home.repo)
    assert not marker.exists()


def _captured(home: Home) -> list[dict]:
    path = home.runs / "prompts" / f"{hashlib.sha256(SESSION.encode()).hexdigest()}.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_capture_stores_digests_not_text(run, home: Home) -> None:
    prompt = "Yes, push and merge.\nAlso release v0.2.0."
    result = run("approval-capture", {"hook_event_name": "UserPromptSubmit", "session_id": SESSION, "prompt": prompt})
    assert result.returncode == 0
    assert result.stdout.strip() == ""
    entries = _captured(home)
    assert entries and entries[0]["session"] == SESSION
    wanted = hashlib.sha256(b"Also release v0.2.0.").hexdigest()
    assert wanted in entries[0]["digests"]
    assert "release" not in json.dumps(entries)


def test_cursor_capture_answers_with_continue(run) -> None:
    payload = {"hook_event_name": "beforeSubmitPrompt", "conversation_id": SESSION, "cursor_version": "2.4",
               "prompt": "go"}
    assert json.loads(run("approval-capture", payload).stdout) == {"continue": True}


def test_capture_is_disabled_by_name(run, home: Home) -> None:
    run("approval-capture", {"session_id": SESSION, "prompt": "go"}, NEXUS_DISABLED_HOOKS="approval-capture")
    assert _captured(home) == []
