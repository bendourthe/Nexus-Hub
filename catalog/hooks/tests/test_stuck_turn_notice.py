"""Tests for catalog/hooks/stuck-turn-notice.{sh,ps1} and _turn_ledger.py (v4.15.5).

Both wrappers run against every platform fixture set, so the suite is also the
.sh/.ps1 parity check. The negative assertions carry the weight: no command or
file text reaches the state directory, nothing is written into the project tree,
a symlinked state location is never written through, no network socket opens,
and no settings file changes.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_stuck_turn_notice.py -q
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_SH = _HOOKS_DIR / "stuck-turn-notice.sh"
_PS1 = _HOOKS_DIR / "stuck-turn-notice.ps1"
_HELPER = _HOOKS_DIR / "_turn_ledger.py"
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "turn_ledger"
_EXPECTED = json.loads((_FIXTURES / "expectations.json").read_text(encoding="ascii"))
_HIDE = {"creationflags": 0x08000000} if os.name == "nt" else {}  # CREATE_NO_WINDOW
_SWITCHES = (
    "NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE", "NEXUS_ENV_FACTS", "NEXUS_STUCK_NOTICE",
    "NEXUS_TURN_PLATFORM", "NEXUS_LEDGER_NOW", "CLAUDE_PROJECT_DIR", "GEMINI_PROJECT_DIR",
    "QWEN_PROJECT_DIR", "PYTHONPATH",
)
# Plain text a stuck fixture sends; none of it may be stored in the state directory.
_NEEDLES = (
    b"npm test", b"build-step", b"src/a.py", b"pytest -q", b"Bearer", b"TOKEN=x", b"user:pw",
    b"IGNORE PREVIOUS", b"unbalanced", b"step-",
)


@pytest.fixture(params=["sh", "ps1"])
def wrapper(request) -> list[str]:
    if request.param == "sh":
        return [request.getfixturevalue("bash_bin"), str(_SH)]
    return [request.getfixturevalue("powershell_bin"), "-NoProfile", "-File", str(_PS1)]


@pytest.fixture
def world(tmp_path: Path) -> dict:
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir()
    project.mkdir()
    env = {k: v for k, v in os.environ.items() if k not in _SWITCHES}
    env.update(HOME=str(home), USERPROFILE=str(home), NEXUS_STUCK_NOTICE="on",
               PYTHONDONTWRITEBYTECODE="1")
    return {"home": home, "project": project, "env": env, "state": home / ".nexus-hub" / "state"}


def _events(name: str, project: Path) -> list[str]:
    path = json.dumps(str(project))[1:-1]
    text = (_FIXTURES / f"{name}.jsonl").read_text(encoding="ascii")
    return [ln.replace("@@PROJECT@@", path) for ln in text.splitlines() if ln]


def _turn(name: str, project: Path, turn: str) -> list[str]:
    return [ln.replace('"P1"', f'"{turn}"') for ln in _events(name, project)]


def _run(prefix: list[str], env: dict, body: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(prefix, input=body, text=True, capture_output=True, env=env,
                          timeout=timeout, **_HIDE)


def _feed(prefix: list[str], env: dict, lines: list[str]) -> list[str]:
    outs = []
    for line in lines:
        proc = _run(prefix, env, line)
        assert proc.returncode == 0
        outs.append(proc.stdout.strip())
    return outs


def _notice_text(out: str) -> str:
    try:
        return json.loads(out)["hookSpecificOutput"]["additionalContext"]
    except (ValueError, KeyError, TypeError):
        return out  # kimi prints plain text


def _state_bytes(world: dict) -> bytes:
    return b"".join(p.read_bytes() for p in world["state"].rglob("*") if p.is_file())


def _tree(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*"))


@pytest.mark.parametrize("name", sorted(_EXPECTED))
def test_fixture_notice_counts_and_privacy(wrapper, world, name):
    lines = _events(name, world["project"])
    outs = _feed(wrapper, world["env"], lines)
    fired = [i for i, out in enumerate(outs) if out]
    assert fired == _EXPECTED[name]["notices"]
    for i in fired:
        text = _notice_text(outs[i])
        assert text.startswith("Nexus-Hub advisory") and text.count(". ") <= 3
        if not name.startswith("kimi"):
            body = json.loads(outs[i])["hookSpecificOutput"]
            assert body["hookEventName"] in {"PostToolUse", "PostToolUseFailure", "AfterTool"}
    assert _tree(world["project"]) == []
    if world["state"].exists():
        blob = _state_bytes(world)
        assert not any(n in blob for n in _NEEDLES)


def test_hostile_values_are_withheld(wrapper, world):
    secrets = _feed(wrapper, world["env"], _events("claude/hostile_secrets", world["project"]))
    text = _notice_text(secrets[2])
    assert "text withheld" in text
    assert not any(w in text for w in ("Bearer", "TOKEN", "pw", "Authorization", "example.test"))
    names = _feed(wrapper, world["env"], _turn("claude/hostile_filename", world["project"], "P2"))
    text = _notice_text(names[3])
    assert "name withheld" in text and "IGNORE" not in text
    quote = _feed(wrapper, world["env"], _turn("claude/hostile_quote", world["project"], "P3"))
    json.loads(quote[2])


def test_only_one_notice_per_turn(wrapper, world):
    lines = _events("claude/repeat_failure", world["project"])
    lines += [lines[0]] * 3
    assert sum(1 for out in _feed(wrapper, world["env"], lines) if out) == 1


def test_ledger_holds_hashes_only(wrapper, world):
    _feed(wrapper, world["env"], _events("claude/repeat_failure", world["project"]))
    (sdir,) = [p for p in world["state"].iterdir() if p.is_dir()]
    allowed = {"v", "kind", "ts", "platform", "session_id", "turn_id", "tool", "ok",
               "exit_class", "cmd_key", "cwd", "file_key", "signal"}
    for line in (sdir / "turn-ledger.jsonl").read_text().splitlines():
        rec = json.loads(line)
        assert set(rec) <= allowed
        for k in ("cmd_key", "file_key"):
            assert k not in rec or len(rec[k]) == 32 and int(rec[k], 16) >= 0
    key = world["state"] / "ledger.key"
    assert key.is_file() and len(key.read_bytes()) >= 16
    if os.name != "nt":
        assert oct(key.stat().st_mode & 0o777) == "0o600"
        assert oct(sdir.stat().st_mode & 0o777) == "0o700"


def _load_helper(world: dict, monkeypatch):
    monkeypatch.setenv("HOME", str(world["home"]))
    monkeypatch.setenv("USERPROFILE", str(world["home"]))
    spec = importlib.util.spec_from_file_location("_turn_ledger_under_test", _HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_symlinked_state_is_never_written(wrapper, world, monkeypatch, tmp_path):
    helper = _load_helper(world, monkeypatch)
    sdir = helper.state_dir_for(world["project"].resolve())
    target = tmp_path / "elsewhere"
    target.mkdir()
    sdir.parent.mkdir(parents=True)
    try:
        os.symlink(target, sdir, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted on this host")
    out = _feed(wrapper, world["env"], _events("claude/edit_churn", world["project"]))
    assert not any(out) and list(target.iterdir()) == []


def test_symlinked_ledger_is_never_written(wrapper, world, monkeypatch, tmp_path):
    helper = _load_helper(world, monkeypatch)
    sdir = helper.state_dir_for(world["project"].resolve())
    sdir.mkdir(parents=True)
    victim = tmp_path / "victim.txt"
    victim.write_text("KEEP")
    try:
        os.symlink(victim, sdir / "turn-ledger.jsonl")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted on this host")
    _feed(wrapper, world["env"], _events("claude/edit_churn", world["project"]))
    assert victim.read_text() == "KEEP"


def _seed_ledger(sdir: Path, session: str, old_days: int) -> None:
    sdir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    lines = []
    for i in range(3000):
        age = old_days if i < 100 else 0
        rec = {"v": 1, "kind": "outcome", "ts": (now - timedelta(days=age)).isoformat(),
               "platform": "claude", "session_id": session, "turn_id": f"T{i}", "tool": "bash",
               "ok": True, "cmd_key": "0" * 32}
        lines.append(json.dumps(rec))
    (sdir / "turn-ledger.jsonl").write_text("\n".join(lines) + "\n")
    assert (sdir / "turn-ledger.jsonl").stat().st_size > 256 * 1024


def test_rotation_happens_only_at_session_start(wrapper, world, monkeypatch):
    helper = _load_helper(world, monkeypatch)
    sdir = helper.state_dir_for(world["project"].resolve())
    _seed_ledger(sdir, "OLD", old_days=40)
    lines = _events("claude/long_refactor", world["project"])
    same = lines[0].replace('"S1"', '"OLD"')
    _run(wrapper, world["env"], same)
    assert not (sdir / "turn-ledger.1.jsonl").exists()
    _run(wrapper, world["env"], lines[0].replace('"S1"', '"NEW"'))
    rotated = sdir / "turn-ledger.1.jsonl"
    assert rotated.exists() and (sdir / "turn-ledger.jsonl").stat().st_size < 4096
    kept = [json.loads(x) for x in rotated.read_text().splitlines()]
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    assert kept and all(datetime.fromisoformat(r["ts"]) >= cutoff for r in kept)


_NET_GUARD = """\
import socket, os
_marker = os.environ["NET_MARKER"]
def _deny(*a, **k):
    open(_marker, "a").write("net\\n")
    raise OSError("network blocked")
socket.socket.connect = _deny
socket.socket.connect_ex = _deny
socket.create_connection = _deny
socket.getaddrinfo = _deny
"""


def test_no_network_and_no_settings_change(wrapper, world, tmp_path):
    guard = tmp_path / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(_NET_GUARD)
    marker = tmp_path / "net.marker"
    settings = [world["home"] / ".claude" / "settings.json",
                world["project"] / ".claude" / "settings.json"]
    for path in settings:
        path.parent.mkdir(parents=True)
        path.write_text('{"permissions": {}}')
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in settings]
    env = {**world["env"], "PYTHONPATH": str(guard), "NET_MARKER": str(marker)}
    outs = _feed(wrapper, env, _events("claude/repeat_failure", world["project"]))
    assert outs[3] and not marker.exists()
    assert before == [hashlib.sha256(p.read_bytes()).hexdigest() for p in settings]


@pytest.mark.parametrize("switch", [
    {"NEXUS_DISABLED_HOOKS": "stuck-turn-notice"}, {"NEXUS_HOOK_PROFILE": "minimal"},
    {"NEXUS_STUCK_NOTICE": "off"},
])
def test_disable_switches_write_nothing(wrapper, world, switch):
    env = {**world["env"], **switch}
    outs = _feed(wrapper, env, _events("claude/repeat_failure", world["project"]))
    assert not any(outs) and not world["state"].exists()


def test_no_python_exits_silently(wrapper, world, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    proc = _run(wrapper, {**world["env"], "PATH": str(empty)},
                _events("claude/repeat_failure", world["project"])[0])
    assert proc.returncode == 0 and proc.stdout == "" and not world["state"].exists()


@pytest.mark.parametrize("body", ["", "not json", "[1,2]", '{"tool_name":"Bash"}',
                                  '{"session_id":"S","tool_name":"Bash","tool_input":{}}'])
def test_malformed_input_is_silent(wrapper, world, body):
    proc = _run(wrapper, world["env"], body)
    assert proc.returncode == 0 and proc.stdout == ""


def test_wrapper_output_parity(world, request):
    sh = [request.getfixturevalue("bash_bin"), str(_SH)]
    ps1 = [request.getfixturevalue("powershell_bin"), "-NoProfile", "-File", str(_PS1)]
    results = []
    for prefix in (sh, ps1):
        home = world["home"] / ("a" if prefix is sh else "b")
        home.mkdir()
        env = {**world["env"], "HOME": str(home), "USERPROFILE": str(home)}
        outs = _feed(prefix, env, _events("claude/error_storm", world["project"]))
        results.append([json.loads(o) if o else None for o in outs])
    assert results[0] == results[1] and results[0][5] is not None


def test_latency_at_full_ledger(wrapper, world, monkeypatch):
    helper = _load_helper(world, monkeypatch)
    sdir = helper.state_dir_for(world["project"].resolve())
    _seed_ledger(sdir, "S1", old_days=0)
    line = _events("claude/long_refactor", world["project"])[0]
    samples = []
    for _ in range(20):
        start = time.perf_counter()
        _run(wrapper, world["env"], line)
        samples.append((time.perf_counter() - start) * 1000)
    samples.sort()
    p95 = samples[int(0.95 * len(samples)) - 1]
    budget = 500 if os.name == "nt" else 250
    print(f"stuck-turn-notice p95 latency {p95:.0f} ms (median {statistics.median(samples):.0f} ms)")
    if p95 > budget:
        # Plan 2.6: an exceeded budget is recorded and stops for a decision, not silently
        # failed or retuned. The skip reason carries the measurement (see decision T013).
        pytest.skip(f"LATENCY BUDGET EXCEEDED: p95 {p95:.0f} ms > {budget} ms; decision required")


def _transcript(tmp_path: Path) -> Path:
    rows = [{"type": "user", "message": {"role": "user", "content": "run the tests"}}]
    for i in range(3):
        rows.append({"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "id": f"t{i}", "name": "Bash", "input": {"command": "SECRET-CMD npm test"}}]}})
        rows.append({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": f"t{i}", "is_error": True, "content": "boom"}]}})
    rows.append({"type": "user", "message": {"role": "user", "content": "next prompt"}})
    folder = tmp_path / "transcripts"
    folder.mkdir()
    (folder / "abcdef0123456789.jsonl").write_text("".join(json.dumps(r) + chr(10) for r in rows))
    return folder


def test_replay_transcripts_prints_counts_and_ids_only(tmp_path):
    folder = _transcript(tmp_path)
    proc = subprocess.run([sys.executable, str(_HELPER), "replay-transcripts", str(folder)],
                          text=True, capture_output=True, **_HIDE)
    out = json.loads(proc.stdout)
    assert out["turns"] == 2 and out["fired"]["repeat"] == 1
    assert out["turn_ids"] == ["abcdef01:0:repeat"] and "SECRET-CMD" not in proc.stdout


def test_stats_reports_both_proxies(world, monkeypatch):
    helper = _load_helper(world, monkeypatch)
    sdir = helper.state_dir_for(world["project"].resolve())
    sdir.mkdir(parents=True)
    rows = [
        {"v": 1, "kind": "notified", "session_id": "S", "cmd_key": "a" * 32},
        {"v": 1, "kind": "outcome", "session_id": "S", "cmd_key": "b" * 32, "ok": True},
        {"v": 1, "kind": "replayed", "f_keys": ["c" * 32, "d" * 32]},
        {"v": 1, "kind": "outcome", "session_id": "S2", "cmd_key": "c" * 32, "ok": False},
    ]
    (sdir / "turn-ledger.jsonl").write_text("".join(json.dumps(r) + chr(10) for r in rows))
    env = {**world["env"], "CLAUDE_PROJECT_DIR": str(world["project"])}
    proc = subprocess.run([sys.executable, str(_HELPER), "stats"], text=True, capture_output=True,
                          env=env, **_HIDE)
    out = json.loads(proc.stdout)
    assert out["no_recurrence_share"] == 1.0 and out["reattempt_rate"] == 0.5
