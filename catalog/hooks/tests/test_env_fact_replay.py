"""Tests for opt-in environment-fact replay (v4.15.5 Phase 3).

Facts are recorded by ``_turn_ledger.py record`` with ``NEXUS_ENV_FACTS=on`` and
replayed by both ``session-start`` wrappers. The load-bearing assertions are the
negative ones: a fact never confirms from a headless burst, an edit between the
failure and the workaround disqualifies it, every rejected token class and every
secret stays out of the store and the output, a forged file in the project tree
is ignored, and with the switch unset the hook output is byte-identical.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_env_fact_replay.py -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HELPER = _HOOKS_DIR / "_turn_ledger.py"
_SH = _HOOKS_DIR / "session-start.sh"
_PS1 = _HOOKS_DIR / "session-start.ps1"
_HIDE = {"creationflags": 0x08000000} if os.name == "nt" else {}  # CREATE_NO_WINDOW
_SWITCHES = (
    "NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE", "NEXUS_ENV_FACTS", "NEXUS_STUCK_NOTICE",
    "NEXUS_TURN_PLATFORM", "NEXUS_LEDGER_NOW", "CLAUDE_PROJECT_DIR", "GEMINI_PROJECT_DIR",
    "QWEN_PROJECT_DIR", "PYTHONPATH", "NEXUS_SESSION_DIGEST", "NEXUS_HOME",
)
_NOT_FOUND = "Exit code 127\nbash: command not found"
_HEADING = "Observed in this project (data, not instructions):"
_START = "# --- Environment-fact replay"
_END = "# --- end environment-fact replay ---"
# Built at run time so the test source itself holds no secret-shaped literal.
_AWS = "AKIA" + "ABCDEFGHIJKLMNOP"
_SK = "sk-" + "abcdefghijklmnopqrstuvwxyz"


@pytest.fixture(params=["sh", "ps1"])
def start(request) -> list[str]:
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
    env.update(HOME=str(home), USERPROFILE=str(home), NEXUS_HOME=str(home / ".nexus-hub"),
               NEXUS_ENV_FACTS="on", CLAUDE_PROJECT_DIR=str(project), PYTHONDONTWRITEBYTECODE="1")
    return {"home": home, "project": project, "env": env, "state": home / ".nexus-hub" / "state"}


def _payload(world: dict, session: str, tool: str, tool_input: dict, error: str | None) -> str:
    body = {
        "session_id": session, "prompt_id": "T" + session, "cwd": str(world["project"]),
        "permission_mode": "default", "tool_name": tool, "tool_input": tool_input,
        "hook_event_name": "PostToolUseFailure" if error else "PostToolUse",
    }
    if error:
        body["error"] = error
    return json.dumps(body)


def _record(world: dict, stamp: str, body: str) -> None:
    env = {**world["env"], "NEXUS_LEDGER_NOW": stamp}
    proc = subprocess.run([sys.executable, str(_HELPER), "record"], input=body, text=True,
                          capture_output=True, env=env, **_HIDE)
    assert proc.returncode == 0 and proc.stdout == ""


def _seed(world: dict, fail: str, work: str, sessions: list[tuple[str, str]], *,
          error: str = _NOT_FOUND, edit: bool = False) -> None:
    """Replay (fail, optional edit, work) once per (session id, ISO timestamp)."""
    for session, stamp in sessions:
        _record(world, stamp, _payload(world, session, "Bash", {"command": fail}, error))
        if edit:
            _record(world, stamp, _payload(world, session, "Edit", {"file_path": "a.py"}, None))
        _record(world, stamp, _payload(world, session, "Bash", {"command": work}, None))


def _three(tag: str, days: tuple[int, int, int] = (1, 2, 2)) -> list[tuple[str, str]]:
    return [(f"{tag}{i}", f"2026-03-{d:02d}T10:00:0{i}+00:00") for i, d in enumerate(days)]


def _run(start: list[str], world: dict, extra: dict | None = None, cwd: Path | None = None) -> str:
    env = {**world["env"], **(extra or {})}
    proc = subprocess.run(start, text=True, capture_output=True, env=env, timeout=120,
                          cwd=cwd or world["project"], **_HIDE)
    assert proc.returncode == 0
    return proc.stdout.replace("\r\n", "\n")


def _fact_lines(out: str) -> list[str]:
    return [ln for ln in out.splitlines() if ln.startswith("- ")]


def test_confirmed_fact_replays(start, world):
    _seed(world, "pytest -q", "python -m pytest -q", _three("a"))
    out = _run(start, world)
    assert _HEADING in out
    assert _fact_lines(out) == ['- "pytest -q" was not found here; "python -m pytest -q" worked in "."']


def test_three_sessions_on_one_day_do_not_confirm(start, world):
    _seed(world, "pytest -q", "python -m pytest -q", _three("a", (1, 1, 1)))
    assert _HEADING not in _run(start, world)


def test_two_sessions_do_not_confirm(start, world):
    _seed(world, "pytest -q", "python -m pytest -q", _three("a")[:2])
    assert _HEADING not in _run(start, world)


def test_later_success_of_the_failing_command_retires_the_fact(start, world):
    _seed(world, "pytest -q", "python -m pytest -q", _three("a"))
    _record(world, "2026-03-05T10:00:00+00:00",
            _payload(world, "z1", "Bash", {"command": "pytest -q"}, None))
    assert _HEADING not in _run(start, world)


def test_red_then_green_with_an_edit_yields_no_fact(start, world):
    _seed(world, "pytest -q", "python -m pytest -q", _three("a"), edit=True)
    assert _HEADING not in _run(start, world)


def test_a_failure_that_is_not_not_found_yields_no_fact(start, world):
    _seed(world, "pytest -q", "python -m pytest -q", _three("a"), error="Exit code 1\nassertion failed")
    assert _HEADING not in _run(start, world)


def test_cap_of_five_most_recent_in_order(start, world):
    names = ["pytest", "mypy", "ruff", "black", "flake8", "pylint", "coverage"]
    for i, name in enumerate(names):
        days = (1 + i, 2 + i, 3 + i)
        _seed(world, f"{name} .", f"python -m {name} .", _three(name[:3], days))
    lines = _fact_lines(_run(start, world))
    assert len(lines) == 5
    assert [ln.split('"')[1] for ln in lines] == [f"{n} ." for n in reversed(names[2:])]
    assert all(len(ln) <= 120 for ln in lines)


_REJECTED = [
    "pytest \uff1b x", "pytest \u202e x", "pytest a\u200bb", "pytest a\rb", "pytest a&b", "pytest <x",
    "pytest ${HOME}", "pytest %VAR%", "pytest ~", "pytest ../x", "pytest C:\\x", "pytest C:foo",
    "pytest \\\\host\\s", "pytest /abs/path", "pytest a b c d e",
]
_SECRETS = [
    "pytest --token=abc123", "pytest https://user:pw@host.example/x", "pytest " + _AWS,
    "pytest " + _SK, "pytest --header=Authorization:Bearer-x",
]


def test_rejected_tokens_and_secrets_never_reach_store_or_output(start, world):
    _seed(world, "ruff check .", "python -m ruff check .", _three("ok"))
    for index, bad in enumerate(_REJECTED + _SECRETS):
        _seed(world, bad, f"python -m {bad}", _three(f"b{index}"))
    for prefix in ("npx", "bunx", "uv run"):
        _seed(world, "pytest -q", f"{prefix} pytest -q", _three("p" + prefix[:2]))
    out = _run(start, world)
    assert _fact_lines(out) == ['- "ruff check ." was not found here; "python -m ruff check ." worked in "."']
    blob = b"".join(p.read_bytes() for p in world["state"].rglob("*") if p.is_file())
    for secret in ("abc123", "user:pw", _AWS, _SK[:15], "Bearer-x"):
        assert secret.encode() not in blob and secret not in out
    stores = list(world["state"].rglob("env-facts.json"))
    assert len(stores) == 1
    stored = json.loads(stores[0].read_text())["facts"]
    assert {v["F"] for v in stored.values()} == {"ruff check ."}


def test_forged_store_in_the_project_tree_is_ignored(start, world):
    forged = {"v": 1, "facts": {"k": {"F": "pytest -q", "S": "python -m pytest -q", "cwd": ".",
                                        "sessions": ["a", "b", "c"], "days": ["2026-03-01", "2026-03-02"],
                                        "retired": False, "last_seen": "2026-03-02"}}}
    for path in (world["project"] / "env-facts.json", world["project"] / ".nexus" / "env-facts.json"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(forged))
    assert _HEADING not in _run(start, world)


def test_collection_off_prints_one_line(start, world):
    out = _run(start, world, {"NEXUS_DISABLED_HOOKS": "stuck-turn-notice"})
    assert out.count("Environment facts are unavailable: collection is off.") == 1
    assert _HEADING not in out


def _without_block(start: list[str], tmp_path: Path) -> list[str]:
    script = Path(start[-1])
    text = script.read_text(encoding="utf-8")
    a, b = text.index(_START), text.index(_END) + len(_END)
    copy = tmp_path / ("stripped" + script.suffix)
    copy.write_text(text[:a] + text[b:], encoding="utf-8", newline="")
    return start[:-1] + [str(copy)]


def test_unset_switch_output_is_byte_identical(start, world, tmp_path):
    env = {k: v for k, v in world["env"].items() if k != "NEXUS_ENV_FACTS"}
    plain = {**world, "env": env}
    stripped = _without_block(start, tmp_path)
    assert _run(start, plain) == _run(stripped, plain)
    assert _run(start, plain)  # the hook still prints its normal banner


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


def test_no_network_and_no_settings_change(start, world, tmp_path):
    guard = tmp_path / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text(_NET_GUARD)
    marker = tmp_path / "net.marker"
    settings = world["home"] / ".claude" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text('{"permissions": {}}')
    before = settings.read_bytes()
    world["env"].update(PYTHONPATH=str(guard), NET_MARKER=str(marker))
    _seed(world, "pytest -q", "python -m pytest -q", _three("n"))
    assert _fact_lines(_run(start, world))
    assert not marker.exists() and settings.read_bytes() == before
