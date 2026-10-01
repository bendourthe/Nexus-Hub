"""Tests for catalog/hooks/_usage_probe.py, the shared usage probe (v4.13.7 Phase 6).

No test touches the network or a real credential: the HTTP seam (`_open`) is
replaced by a recorder, the home directory and every credential location point
into `tmp_path`, and time is a controllable clock.

Fixture provenance:

- Claude, Codex, and Cursor payloads are sanitized reductions of the shapes the
  existing monitors map (`extensions/claude-usage-monitor/src/providers/claude.ts`,
  `extensions/codex-usage-monitor/src/providers/codex.ts`,
  `extensions/cursor-usage-monitor/src/providers/liveTransport.ts`), with
  invented numbers.
- The Copilot state file is a documented-schema fixture: written from the
  schema in `docs/releases/v4/v4.13/development/v4.13.7-decisions.md`
  ("Copilot usage monitor" item (6)), not from a captured file, because the
  Copilot Usage Monitor (Phase 2) has not shipped yet.

Every credential below is an example fixture string; the leak test fails if any
of them reaches a result, a cache file, a log line, or captured output.
"""

from __future__ import annotations

import importlib.util
import io
import json
import logging
import os
import sqlite3
import subprocess
import sys
import threading
import time
import types
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
PROBE_PATH = HOOKS_DIR / "_usage_probe.py"

CLAUDE_TOKEN = "sk-ant-oat01-example-fixture-claude-do-not-leak-0001"
CODEX_TOKEN = "eyJexample.fixture-codex-do-not-leak.0002"
CODEX_ACCOUNT = "acct-example-fixture-do-not-leak-0003"
CURSOR_TOKEN = "cursorExampleFixtureDoNotLeak0004abcdef"
SECRETS = (CLAUDE_TOKEN, CODEX_TOKEN, CODEX_ACCOUNT, CURSOR_TOKEN)

T0 = 1_790_000_000.0  # a fixed "now": 2026-09-21T14:13:20Z


def _load_probe() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("_usage_probe_under_test", PROBE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ----- fixtures -------------------------------------------------------------------

CLAUDE_PAYLOAD: dict[str, Any] = {
    "five_hour": {"utilization": 41.0, "resets_at": "2026-09-21T18:00:00+00:00"},
    "seven_day": {"utilization": 63.0, "resets_at": "2026-09-25T14:00:00+00:00"},
    "seven_day_opus": {"utilization": 77.5, "resets_at": "2026-09-25T14:00:00+00:00"},
    "seven_day_sonnet": None,
    "iguana_necktie": {"opaque": True},
    "extra_usage": {"is_enabled": False, "monthly_limit": 0, "used_credits": 0},
    "limits": [
        {"kind": "session", "percent": 42, "resets_at": "2026-09-21T18:00:00Z"},
        {"kind": "weekly_all", "percent": 64, "resets_at": "2026-09-25T14:00:00Z"},
        {
            "kind": "weekly_scoped",
            "percent": 12,
            "resets_at": "2026-09-25T14:00:00Z",
            "scope": {"model": {"id": "x", "display_name": "Sonnet"}},
        },
        {"kind": "something_new", "percent": 99},
    ],
}

CODEX_PAYLOAD_TWO_WINDOWS: dict[str, Any] = {
    "plan_type": "plus",
    "rate_limit": {
        "primary_window": {
            "used_percent": 97,
            "limit_window_seconds": 18000,
            "reset_at": 1_790_010_000,
        },
        "secondary_window": {
            "used_percent": 55,
            "limit_window_seconds": 604800,
            "reset_at": 1_790_300_000,
        },
    },
}

CODEX_PAYLOAD_WEEKLY_ONLY: dict[str, Any] = {
    "rate_limit": {
        "primary_window": {
            "used_percent": 81,
            "limit_window_seconds": 604800,
            "reset_at": 1_790_300_000,
        },
        "secondary_window": None,
    },
}

CURSOR_PAYLOAD: dict[str, Any] = {
    "billingCycleStart": "1788000000000",
    "billingCycleEnd": "1790600000000",
    "planUsage": {
        "totalPercentUsed": 23.97,
        "autoPercentUsed": 10.0,
        "apiPercentUsed": 40.0,
    },
    "enabled": False,
}


def copilot_state(**overrides: Any) -> dict[str, Any]:
    """Documented-schema Copilot state file (decision file item (6))."""
    state: dict[str, Any] = {
        "schema_version": 1,
        "provider": "copilot",
        "fetched_at": "2026-09-21T14:10:00Z",
        "approximate": False,
        "windows": [
            {
                "name": "monthly",
                "percent": 82.6,
                "resets_at": "2026-10-01T00:00:00Z",
                "source": "organization",
            }
        ],
    }
    state.update(overrides)
    return state


class FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, status: int = 200) -> None:
        super().__init__(body)
        self.status = status


class FakeHTTP:
    """Records every request the probe would send and answers from a queue."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.answers: list[Any] = []

    def queue(self, answer: Any) -> None:
        self.answers.append(answer)

    def __call__(self, request: urllib.request.Request, timeout: float) -> Any:
        headers = dict(request.header_items())
        # Mirror http.client.putheader: a value with a newline is rejected with
        # an error that QUOTES the value, which is how a token could leak.
        for key, value in headers.items():
            if "\n" in value or "\r" in value:
                raise ValueError(f"Invalid header value {value!r} for {key}")
        self.calls.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "headers": headers,
                "body": request.data,
                "timeout": timeout,
            }
        )
        if not self.answers:
            raise AssertionError("unexpected HTTP call")
        answer = self.answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        if isinstance(answer, FakeResponse):
            return answer
        return FakeResponse(json.dumps(answer).encode("utf-8"))


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def time(self) -> float:
        return self.now


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> types.SimpleNamespace:
    probe = _load_probe()
    home = tmp_path / "home"
    home.mkdir()
    nexus = tmp_path / "nexus-home"
    appdata = tmp_path / "AppData" / "Roaming"
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    monkeypatch.setenv("NEXUS_HOME", str(nexus))
    monkeypatch.setenv("APPDATA", str(appdata))
    for name in (
        "CODEX_HOME",
        "XDG_CONFIG_HOME",
        "NEXUS_USAGE_PROBE_DISABLED",
        "NEXUS_USAGE_PROBE_PROVIDERS",
    ):
        monkeypatch.delenv(name, raising=False)
    http = FakeHTTP()
    monkeypatch.setattr(probe, "_open", http)
    clock = Clock()
    monkeypatch.setattr(probe, "time", types.SimpleNamespace(time=clock.time))
    monkeypatch.setattr(probe.sys, "platform", "linux")
    return types.SimpleNamespace(
        probe=probe, home=home, nexus=nexus, appdata=appdata, http=http, clock=clock
    )


def write_claude_creds(
    home: Path, token: str = CLAUDE_TOKEN, expires_ms: float | None = None
) -> Path:
    path = home / ".claude" / ".credentials.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    expires = expires_ms if expires_ms is not None else (T0 + 3600) * 1000
    oauth = {"accessToken": token, "expiresAt": expires}
    path.write_text(json.dumps({"claudeAiOauth": oauth}), encoding="utf-8")
    return path


def write_codex_auth(base: Path, account: str = CODEX_ACCOUNT) -> Path:
    path = base / "auth.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tokens = {"access_token": CODEX_TOKEN, "account_id": account}
    path.write_text(json.dumps({"tokens": tokens}), encoding="utf-8")
    return path


def write_cursor_db(path: Path, value: str = CURSOR_TOKEN) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute(
        "CREATE TABLE ItemTable (key TEXT UNIQUE ON CONFLICT REPLACE, value BLOB)"
    )
    connection.execute(
        "INSERT INTO ItemTable VALUES (?, ?)", ("cursorAuth/accessToken", value)
    )
    connection.execute(
        "INSERT INTO ItemTable VALUES (?, ?)", ("other/key", "unrelated")
    )
    connection.commit()
    connection.close()
    return path


def write_copilot(env: types.SimpleNamespace, state: Any) -> Path:
    path = env.nexus / "state" / "usage-probe" / "copilot.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = state if isinstance(state, str) else json.dumps(state)
    path.write_text(text, encoding="utf-8")
    return path


def windows(result: Any) -> dict[str, float]:
    return {w.name: w.percent for w in result.windows}


def windows_from(mapper: Any, payload: Any) -> dict[str, float]:
    return {w.name: w.percent for w in mapper(payload)}


def cursor_db_path(env: types.SimpleNamespace) -> Path:
    return env.appdata / "Cursor" / "User" / "globalStorage" / "state.vscdb"


@pytest.fixture
def cursor_env(env, monkeypatch):
    monkeypatch.setattr(env.probe.sys, "platform", "win32")
    write_cursor_db(cursor_db_path(env))
    return env


# ----- Claude Code ----------------------------------------------------------------


def test_claude_maps_five_hour_and_highest_weekly(env):
    write_claude_creds(env.home)
    env.http.queue(CLAUDE_PAYLOAD)

    result = env.probe.probe("claude")

    assert result.status == "ok" and result.cached is False
    # session 42 beats five_hour 41; seven_day_opus 77.5 is the highest weekly.
    assert windows(result) == {"five_hour": 42.0, "weekly": 77.5}
    assert all(w.source == "anthropic-oauth-usage" for w in result.windows)
    weekly = next(w for w in result.windows if w.name == "weekly")
    assert weekly.resets_at == "2026-09-25T14:00:00Z"


def test_claude_legacy_fields_and_unknown_model_window(env):
    legacy = {"five_hour": {"utilization": 5, "resets_at": None}}
    assert windows_from(env.probe.map_claude, legacy) == {"five_hour": 5.0}
    added = {
        "seven_day": {"utilization": 9.5},
        "seven_day_future_model": {"utilization": 30},
    }
    assert windows_from(env.probe.map_claude, added) == {"weekly": 30.0}


def test_claude_request_goes_only_to_anthropic_with_beta_header(env):
    write_claude_creds(env.home)
    env.http.queue(CLAUDE_PAYLOAD)

    env.probe.probe("claude")

    (call,) = env.http.calls
    assert call["url"] == "https://api.anthropic.com/api/oauth/usage"
    assert call["method"] == "GET"
    assert call["headers"]["Authorization"] == f"Bearer {CLAUDE_TOKEN}"
    assert call["headers"]["Anthropic-beta"] == "oauth-2025-04-20"
    assert call["timeout"] == 3.0


def test_claude_missing_credentials_is_unavailable_without_network(env):
    result = env.probe.probe("claude")

    assert (result.status, result.reason) == ("unavailable", "credentials missing")
    assert env.http.calls == []


def test_claude_malformed_credentials_is_unavailable(env):
    path = env.home / ".claude" / ".credentials.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")

    result = env.probe.probe("claude")

    assert (result.status, result.reason) == ("unavailable", "credentials unreadable")
    assert env.http.calls == []


def test_claude_expired_credentials_never_refresh_or_write(env):
    path = write_claude_creds(env.home, expires_ms=(T0 - 60) * 1000)
    before = path.read_bytes()

    result = env.probe.probe("claude")

    assert (result.status, result.reason) == ("unavailable", "credentials expired")
    assert env.http.calls == []
    assert path.read_bytes() == before


def test_claude_windows_credentials_path(env):
    assert (
        env.probe._claude_credentials_path()
        == env.home / ".claude" / ".credentials.json"
    )


def test_claude_macos_keychain_fallback(env, monkeypatch):
    monkeypatch.setattr(env.probe.sys, "platform", "darwin")
    seen: dict[str, Any] = {}

    def fake_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
        seen["cmd"], seen["timeout"] = cmd, kwargs.get("timeout")
        oauth = {"accessToken": CLAUDE_TOKEN, "expiresAt": (T0 + 60) * 1000}
        blob = json.dumps({"claudeAiOauth": oauth})
        return subprocess.CompletedProcess(cmd, 0, stdout=blob + "\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    env.http.queue(CLAUDE_PAYLOAD)

    result = env.probe.probe("claude")

    assert result.status == "ok"
    assert seen["cmd"][:2] == ["security", "find-generic-password"]
    assert "-w" in seen["cmd"]
    assert seen["timeout"] == 2.0


def test_claude_keychain_timeout_is_unavailable(env, monkeypatch):
    monkeypatch.setattr(env.probe.sys, "platform", "darwin")

    def slow_run(cmd: list[str], **kwargs: Any) -> None:
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 0))

    monkeypatch.setattr(subprocess, "run", slow_run)

    result = env.probe.probe("claude")

    assert (result.status, result.reason) == ("unavailable", "keychain read timed out")
    assert env.http.calls == []


# ----- Codex ----------------------------------------------------------------------


def test_codex_tracks_weekly_only_by_window_length(env):
    write_codex_auth(env.home / ".codex")
    env.http.queue(CODEX_PAYLOAD_TWO_WINDOWS)

    result = env.probe.probe("codex")

    # The 5-hour window at 97% is deliberately not tracked (resolved decision 5).
    assert windows(result) == {"weekly": 55.0}
    assert result.windows[0].source == "chatgpt-wham-usage"
    assert result.windows[0].resets_at == env.probe._iso(1_790_300_000)


def test_codex_weekly_only_plan_reports_its_primary_window(env):
    assert windows_from(env.probe.map_codex, CODEX_PAYLOAD_WEEKLY_ONLY) == {
        "weekly": 81.0
    }


def test_codex_window_without_length_falls_back_to_position(env):
    payload = {
        "rate_limit": {
            "primary_window": {"used_percent": 99},
            "secondary_window": {"used_percent": 12},
        }
    }
    assert windows_from(env.probe.map_codex, payload) == {"weekly": 12.0}


def test_codex_request_headers_and_codex_home(env, monkeypatch, tmp_path):
    custom = tmp_path / "custom-codex-home"
    write_codex_auth(custom)
    monkeypatch.setenv("CODEX_HOME", str(custom))
    env.http.queue(CODEX_PAYLOAD_WEEKLY_ONLY)

    env.probe.probe("codex")

    (call,) = env.http.calls
    assert call["url"] == "https://chatgpt.com/backend-api/wham/usage"
    assert call["headers"]["Authorization"] == f"Bearer {CODEX_TOKEN}"
    assert call["headers"]["Chatgpt-account-id"] == CODEX_ACCOUNT


def test_codex_synthetic_account_id_is_not_sent(env):
    write_codex_auth(env.home / ".codex", account="email_someone")
    env.http.queue(CODEX_PAYLOAD_WEEKLY_ONLY)

    env.probe.probe("codex")

    assert "Chatgpt-account-id" not in env.http.calls[0]["headers"]


def test_codex_missing_auth_is_unavailable(env):
    assert env.probe.probe("codex").reason == "credentials missing"
    assert env.http.calls == []


# ----- Cursor ---------------------------------------------------------------------


def test_cursor_state_path_per_os(env, monkeypatch, tmp_path):
    tail = ("Cursor", "User", "globalStorage", "state.vscdb")
    assert env.probe.cursor_state_path("win32") == env.appdata.joinpath(*tail)
    mac = env.probe.cursor_state_path("darwin")
    assert mac == env.home.joinpath("Library", "Application Support", *tail)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    assert env.probe.cursor_state_path("linux") == (tmp_path / "xdg").joinpath(*tail)
    monkeypatch.delenv("XDG_CONFIG_HOME")
    assert env.probe.cursor_state_path("linux") == env.home.joinpath(".config", *tail)
    monkeypatch.delenv("APPDATA")
    assert env.probe.cursor_state_path("win32") is None


def test_cursor_reads_token_read_only_and_maps_delivered_percent(cursor_env):
    env = cursor_env
    db = cursor_db_path(env)
    before = db.read_bytes()
    env.http.queue(CURSOR_PAYLOAD)

    result = env.probe.probe("cursor")

    assert windows(result) == {"monthly": 23.97}
    assert result.windows[0].resets_at == env.probe._iso(1_790_600_000)
    (call,) = env.http.calls
    assert call["url"] == (
        "https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage"
    )
    assert call["method"] == "POST" and call["body"] == b"{}"
    assert call["headers"]["Authorization"] == f"Bearer {CURSOR_TOKEN}"
    assert db.read_bytes() == before


def test_cursor_falls_back_to_the_higher_pool_percent(env):
    payload = {
        "billingCycleEnd": "1790600000000",
        "planUsage": {"autoPercentUsed": 10, "apiPercentUsed": 40},
    }
    assert windows_from(env.probe.map_cursor, payload) == {"monthly": 40.0}
    assert env.probe.map_cursor({"planUsage": {}}) == []


def test_cursor_missing_database_is_unavailable(env, monkeypatch):
    monkeypatch.setattr(env.probe.sys, "platform", "win32")
    assert env.probe.probe("cursor").reason == "credentials missing"
    assert env.http.calls == []


def test_cursor_locked_database_is_unavailable_not_raised(cursor_env):
    env = cursor_env
    locker = sqlite3.connect(cursor_db_path(env), isolation_level=None)
    locker.execute("BEGIN EXCLUSIVE")
    try:
        result = env.probe.probe("cursor")
    finally:
        locker.execute("ROLLBACK")
        locker.close()

    assert (result.status, result.reason) == ("unavailable", "credentials unreadable")
    assert env.http.calls == []


def test_cursor_rejects_a_malformed_session_value(env, monkeypatch):
    monkeypatch.setattr(env.probe.sys, "platform", "win32")
    write_cursor_db(cursor_db_path(env), value="short")
    assert env.probe.probe("cursor").reason == "credentials missing"


# ----- GitHub Copilot (documented-schema state file) --------------------------------


def test_copilot_reads_the_state_file_without_network(env):
    write_copilot(env, copilot_state())

    result = env.probe.probe("copilot")

    assert result.status == "ok"
    assert [w.to_dict() for w in result.windows] == [
        {
            "name": "monthly",
            "percent": 82.6,
            "resets_at": "2026-10-01T00:00:00Z",
            "source": "organization",
        }
    ]
    assert env.http.calls == []


def test_copilot_personal_source(env):
    state = copilot_state()
    state["windows"][0]["source"] = "personal"
    write_copilot(env, state)
    assert env.probe.probe("copilot").windows[0].source == "personal"


def test_copilot_probe_never_rewrites_the_monitor_file(env):
    path = write_copilot(env, copilot_state())
    before = path.read_bytes()

    env.probe.probe("copilot")
    env.probe.probe("copilot")

    assert path.read_bytes() == before
    assert sorted(p.name for p in path.parent.iterdir()) == ["copilot.json"]


def test_copilot_drops_keys_outside_the_schema(env):
    # Not a schema field: the test only proves an unexpected key is dropped and
    # never copied into the result.
    write_copilot(env, copilot_state(unexpected_extra_key="IGNORED-VALUE"))
    assert "IGNORED-VALUE" not in json.dumps(env.probe.probe("copilot").to_dict())


_NO_PERCENT = [
    {"name": "monthly", "percent": None, "resets_at": None, "source": "personal"}
]


@pytest.mark.parametrize(
    ("state", "reason"),
    [
        (None, "state file missing (Copilot Usage Monitor not running)"),
        ("{truncated", "state file unreadable"),
        (copilot_state(schema_version=2), "state file schema not recognized"),
        (copilot_state(provider="codex"), "state file schema not recognized"),
        (copilot_state(fetched_at="yesterday"), "state file schema not recognized"),
        (copilot_state(windows="monthly"), "state file schema not recognized"),
        (
            copilot_state(fetched_at="2026-09-21T13:40:00Z"),
            "state file older than 30 minutes",
        ),
        (
            copilot_state(fetched_at="2026-09-21T14:30:00Z"),
            "state file timestamp in the future",
        ),
        (copilot_state(windows=[]), "no percentage reported (no readable quota)"),
        (
            copilot_state(windows=_NO_PERCENT),
            "no percentage reported (no readable quota)",
        ),
    ],
)
def test_copilot_failure_modes_are_unavailable(env, state, reason):
    if state is not None:
        write_copilot(env, state)

    result = env.probe.probe("copilot")

    assert (result.status, result.reason, result.windows) == ("unavailable", reason, [])
    assert env.http.calls == []


# ----- cache ------------------------------------------------------------------------


def test_second_probe_within_ttl_is_cached(env):
    write_claude_creds(env.home)
    env.http.queue(CLAUDE_PAYLOAD)
    first = env.probe.probe("claude")
    env.clock.now += 299

    second = env.probe.probe("claude")

    assert second.cached is True and second.status == "ok"
    assert windows(second) == windows(first)
    assert len(env.http.calls) == 1


def test_ttl_is_300_seconds_below_90_percent(env):
    write_claude_creds(env.home)
    env.http.queue(CLAUDE_PAYLOAD)
    env.http.queue(CLAUDE_PAYLOAD)
    env.probe.probe("claude")
    env.clock.now += 120
    assert env.probe.probe("claude").cached is True
    env.clock.now += 181  # 301 s after the fetch

    assert env.probe.probe("claude").cached is False
    assert len(env.http.calls) == 2


def test_ttl_drops_to_60_seconds_at_90_percent(env):
    write_claude_creds(env.home)
    hot = json.loads(json.dumps(CLAUDE_PAYLOAD))
    hot["limits"][0]["percent"] = 90
    env.http.queue(hot)
    env.http.queue(hot)
    env.probe.probe("claude")
    env.clock.now += 59
    assert env.probe.probe("claude").cached is True
    env.clock.now += 2  # 61 s after the fetch

    assert env.probe.probe("claude").cached is False
    assert len(env.http.calls) == 2


def test_failure_after_ttl_returns_stale_cache_then_unavailable(env):
    write_claude_creds(env.home)
    env.http.queue(CLAUDE_PAYLOAD)
    env.probe.probe("claude")
    env.clock.now += 400
    env.http.queue(TimeoutError())

    stale = env.probe.probe("claude")

    assert stale.status == "stale" and stale.cached is True
    assert stale.reason == "endpoint timed out"
    assert windows(stale) == {"five_hour": 42.0, "weekly": 77.5}

    env.clock.now += 1800  # the cached data is now older than 30 minutes
    env.http.queue(TimeoutError())
    gone = env.probe.probe("claude")
    assert (gone.status, gone.reason, gone.windows) == (
        "unavailable",
        "endpoint timed out",
        [],
    )


def test_failure_backoff_skips_the_network_for_60_seconds(env):
    write_claude_creds(env.home)
    env.http.queue(urllib.error.URLError("offline"))
    assert env.probe.probe("claude").reason == "endpoint unreachable"
    env.clock.now += 30

    again = env.probe.probe("claude")

    assert again.reason == "endpoint unreachable"
    assert len(env.http.calls) == 1
    env.clock.now += 31
    env.http.queue(CLAUDE_PAYLOAD)
    assert env.probe.probe("claude").status == "ok"
    assert len(env.http.calls) == 2


def test_cache_holds_percentages_only(env):
    write_claude_creds(env.home)
    env.http.queue(CLAUDE_PAYLOAD)
    env.probe.probe("claude")

    cache_file = env.nexus / "state" / "usage-probe" / "claude.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8"))

    assert set(cache) == {"schema_version", "platform", "data_at", "windows"}
    for window in cache["windows"]:
        assert set(window) == {"name", "percent", "resets_at", "source"}
    assert "iguana_necktie" not in json.dumps(cache)


def test_concurrent_cache_writes_never_expose_a_partial_file(env):
    probe = env.probe
    window = {"name": "weekly", "percent": 1, "resets_at": None, "source": "s"}
    payloads = [
        {
            "schema_version": 1,
            "platform": "codex",
            "data_at": T0 + i,
            "windows": [window] * 50,
        }
        for i in range(40)
    ]
    errors: list[str] = []
    stop = threading.Event()

    def writer(start: int) -> None:
        for payload in payloads[start::4]:
            probe._write_cache("codex", payload)

    def reader() -> None:
        path = probe._cache_path("codex")
        while not stop.is_set():
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            try:
                data = json.loads(text)
            except ValueError:
                errors.append("partial read")
                return
            if len(data["windows"]) != 50:
                errors.append("truncated windows")

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(4)]
    watcher = threading.Thread(target=reader)
    watcher.start()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    stop.set()
    watcher.join()

    assert errors == []
    names = [p.name for p in probe.state_dir().iterdir()]
    assert names == ["codex.json"], "a temp sibling was left behind"
    assert probe._read_cache("codex") is not None


# ----- failure modes common to the network providers ----------------------------------


def _http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://api.anthropic.com/", code, "x", {}, None)


@pytest.mark.parametrize(
    ("answer", "reason"),
    [
        (_http_error(401), "credentials rejected (HTTP 401)"),
        (_http_error(429), "rate limited (HTTP 429)"),
        (_http_error(302), "endpoint error (HTTP 302)"),
        (_http_error(503), "endpoint error (HTTP 503)"),
        (TimeoutError("timed out"), "endpoint timed out"),
        (urllib.error.URLError("dns"), "endpoint unreachable"),
        (FakeResponse(b"<html>not json</html>"), "unexpected response: not JSON"),
        (FakeResponse(b"x" * 1_000_001), "unexpected response: too large"),
        ({"totally": "different"}, "unexpected response: no tracked window"),
        ([1, 2, 3], "unexpected response: no tracked window"),
    ],
)
def test_network_failures_are_unavailable(env, answer, reason):
    write_claude_creds(env.home)
    env.http.queue(answer)

    result = env.probe.probe("claude")

    assert (result.status, result.reason, result.windows) == ("unavailable", reason, [])


@pytest.mark.parametrize(
    ("url", "host"),
    [
        ("https://example.com/usage", "api.anthropic.com"),
        ("http://api.anthropic.com/api/oauth/usage", "api.anthropic.com"),
        ("https://api.anthropic.com.evil.example/x", "api.anthropic.com"),
        # Another provider's vendor host is refused too: hosts are pinned per
        # provider, not shared in one global allowlist.
        ("https://api.anthropic.com/api/oauth/usage", "chatgpt.com"),
        ("https://api2.cursor.sh/x", "api.anthropic.com"),
    ],
)
def test_http_layer_pins_the_host_per_provider(env, url, host):
    with pytest.raises(env.probe.ProbeError, match="not allowlisted"):
        env.probe._http_json("GET", url, {}, expected_host=host)
    assert env.http.calls == []


def test_a_provider_url_pointing_at_another_vendor_is_refused(env, monkeypatch):
    write_codex_auth(env.home / ".codex")
    monkeypatch.setattr(env.probe, "CODEX_USAGE_URL", env.probe.CLAUDE_USAGE_URL)

    result = env.probe.probe("codex")

    assert result.reason == "refused: host not allowlisted"
    assert env.http.calls == []


def test_opener_refuses_redirects(env):
    opener = env.probe._opener()
    handlers = [
        h for h in opener.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)
    ]
    assert handlers
    request = urllib.request.Request("https://api.anthropic.com/api/oauth/usage")
    for handler in handlers:
        target = "https://elsewhere.example/"
        assert handler.redirect_request(request, None, 302, "Found", {}, target) is None


def test_a_provider_bug_becomes_a_recorded_failure(env, monkeypatch):
    def broken() -> list[Any]:
        raise RuntimeError(f"boom {CLAUDE_TOKEN}")

    monkeypatch.setitem(env.probe._FETCHERS, "claude", broken)

    result = env.probe.probe("claude")

    assert (result.status, result.reason) == ("unavailable", "unexpected response")
    cache = env.probe._read_cache("claude")
    assert cache["failed_at"] == T0 and cache["reason"] == "unexpected response"
    assert CLAUDE_TOKEN not in json.dumps(cache)


def test_a_core_bug_outside_the_fetch_never_raises(env, monkeypatch):
    def broken(platform: str) -> None:
        raise RuntimeError("cache layer bug")

    monkeypatch.setattr(env.probe, "_read_cache", broken)

    result = env.probe.probe("claude")

    assert (result.status, result.reason) == ("unavailable", "internal error")


def test_header_error_quoting_the_token_does_not_leak(env):
    write_claude_creds(env.home, token=CLAUDE_TOKEN + "\ninjected")

    result = env.probe.probe("claude")

    assert (result.status, result.reason) == ("unavailable", "endpoint unreachable")
    assert CLAUDE_TOKEN not in json.dumps(result.to_dict())


# ----- switches and CLI -------------------------------------------------------------


def test_global_off_switch(env, monkeypatch):
    write_claude_creds(env.home)
    monkeypatch.setenv("NEXUS_USAGE_PROBE_DISABLED", "1")

    result = env.probe.probe("claude")

    assert result.status == "unavailable"
    assert result.reason == "disabled by NEXUS_USAGE_PROBE_DISABLED"
    assert env.http.calls == []


def test_provider_subset_switch(env, monkeypatch):
    monkeypatch.setenv("NEXUS_USAGE_PROBE_PROVIDERS", "codex, cursor")
    reason = "provider disabled by NEXUS_USAGE_PROBE_PROVIDERS"
    assert env.probe.probe("claude").reason == reason
    write_copilot(env, copilot_state())
    assert env.probe.probe("copilot").reason == reason


@pytest.mark.parametrize("platform", ["qwen", "gemini-cli", "kimi", "", "claude-x"])
def test_platform_without_a_source_is_unavailable(env, platform):
    result = env.probe.probe(platform)
    assert (result.status, result.reason) == (
        "unavailable",
        "no usage source for this platform",
    )


def test_cli_json_prints_one_object_and_exits_zero(env, capsys):
    write_copilot(env, copilot_state())

    assert env.probe.main(["--platform", "copilot", "--json"]) == 0

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "ok" and out["windows"][0]["percent"] == 82.6


def test_cli_without_json_writes_nothing_to_stdout(env, capsys):
    assert env.probe.main(["--platform", "qwen"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unavailable" in captured.err


def test_cli_subprocess_exits_zero_when_unavailable(tmp_path):
    child_env = {
        **os.environ,
        "NEXUS_HOME": str(tmp_path),
        "NEXUS_USAGE_PROBE_DISABLED": "1",
    }
    done = subprocess.run(
        [sys.executable, str(PROBE_PATH), "--platform", "claude", "--json"],
        capture_output=True,
        text=True,
        timeout=30,
        env=child_env,
        check=False,
    )
    assert done.returncode == 0
    assert json.loads(done.stdout)["status"] == "unavailable"


# ----- out-of-range dates and mapper failures (review F1) ----------------------------

_OUT_OF_RANGE = "0001-01-01T00:00:00+01:00"  # its UTC instant falls before year 1


@pytest.mark.parametrize(
    "value",
    [
        "1960-01-01T00:00:00Z",
        _OUT_OF_RANGE,
        "9999-12-31T23:59:59-14:00",
        -5e9,
        1e30,
        float("nan"),
        "not a date",
        None,
    ],
)
def test_reset_conversion_never_raises(env, value):
    assert isinstance(env.probe._reset_iso(value), (str, type(None)))


def test_out_of_range_reset_drops_the_time_and_keeps_the_window(env):
    write_claude_creds(env.home)
    payload = {
        "limits": [{"kind": "session", "percent": 95, "resets_at": _OUT_OF_RANGE}]
    }
    env.http.queue(payload)

    result = env.probe.probe("claude")

    assert result.status == "ok"
    assert [(w.name, w.percent, w.resets_at) for w in result.windows] == [
        ("five_hour", 95.0, None)
    ]


def _deep_json(depth: int = 100_000) -> bytes:
    return b"[" * depth + b"]" * depth


@pytest.mark.parametrize(
    ("break_it", "reason"),
    [
        ("mapper", "unexpected response"),
        ("recursion", "unexpected response: not JSON"),
    ],
)
def test_cached_95_then_a_failing_fetch_is_stale_with_backoff(
    env, monkeypatch, break_it, reason
):
    write_claude_creds(env.home)
    hot = {"limits": [{"kind": "session", "percent": 95, "resets_at": None}]}
    env.http.queue(hot)
    assert windows(env.probe.probe("claude")) == {"five_hour": 95.0}
    env.clock.now += 61  # past the 60-second near-limit TTL
    if break_it == "mapper":

        def overflow(payload: object) -> list[Any]:
            raise OverflowError("date value out of range")

        monkeypatch.setattr(env.probe, "map_claude", overflow)
        env.http.queue(hot)
    else:
        env.http.queue(FakeResponse(_deep_json()))

    stale = env.probe.probe("claude")

    assert (stale.status, stale.reason) == ("stale", reason)
    assert windows(stale) == {"five_hour": 95.0}
    assert len(env.http.calls) == 2
    cache = env.probe._read_cache("claude")
    assert cache["failed_at"] == env.clock.now and cache["reason"] == reason
    env.clock.now += 10
    assert env.probe.probe("claude").status == "stale"
    assert len(env.http.calls) == 2, "the backoff must skip the network"


def test_copilot_out_of_range_dates_do_not_raise(env):
    state = copilot_state()
    state["windows"][0]["resets_at"] = _OUT_OF_RANGE
    write_copilot(env, state)
    result = env.probe.probe("copilot")
    assert (result.status, result.windows[0].resets_at) == ("ok", None)

    write_copilot(env, copilot_state(fetched_at=_OUT_OF_RANGE))
    ancient = env.probe.probe("copilot")
    assert (ancient.status, ancient.reason) == (
        "unavailable",
        "state file older than 30 minutes",
    )


def test_copilot_deeply_nested_file_is_unreadable_not_raised(env):
    path = env.nexus / "state" / "usage-probe" / "copilot.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_deep_json())
    assert env.probe.probe("copilot").reason == "state file unreadable"


# ----- total fetch deadline (review F3) ----------------------------------------------


def _join_fetch_workers(timeout: float = 10.0) -> None:
    for thread in threading.enumerate():
        if thread.name == "usage-probe-fetch":
            thread.join(timeout)


@pytest.fixture
def drip_server():
    """Loopback HTTP server that sends a 200, then one body byte every 0.25 s.

    A per-socket-operation timeout never fires against it, because no single
    read waits longer than 0.25 s; only a total deadline can bound the fetch.
    """
    import http.server

    body = b'{"ok": 1}'

    class Drip(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            for byte in body:
                self.wfile.write(bytes([byte]))
                self.wfile.flush()
                time.sleep(0.25)

        def log_message(self, *args: Any) -> None:
            return None

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Drip)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/"
    finally:
        server.shutdown()
        server.server_close()


def test_a_dripping_server_is_cut_off_at_the_total_deadline(
    env, monkeypatch, drip_server
):
    monkeypatch.setattr(env.probe, "FETCH_DEADLINE_SECONDS", 1.0)
    calls: list[float] = []
    no_proxy = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def drip_fetch() -> list[Any]:
        calls.append(time.monotonic())
        with no_proxy.open(drip_server, timeout=1.0) as response:
            response.read()
        # Reached only after the deadline: this late result must be discarded.
        return [env.probe.Window("five_hour", 12.0, None, "anthropic-oauth-usage")]

    monkeypatch.setitem(env.probe._FETCHERS, "claude", drip_fetch)

    started = time.monotonic()
    result = env.probe.probe("claude")
    elapsed = time.monotonic() - started

    assert (result.status, result.reason) == ("unavailable", "endpoint timed out")
    assert elapsed < 1.75, f"the fetch ran {elapsed:.2f} s against a 1 s deadline"
    _join_fetch_workers()  # let the late result arrive, then prove it was dropped
    cache = env.probe._read_cache("claude")
    assert cache["data_at"] is None and cache["windows"] == []
    assert cache["reason"] == "endpoint timed out"
    env.clock.now += 10
    assert env.probe.probe("claude").reason == "endpoint timed out"
    assert len(calls) == 1, "the backoff must skip a second slow fetch"


def test_a_hung_keychain_read_is_bounded_by_the_same_deadline(env, monkeypatch):
    monkeypatch.setattr(env.probe, "FETCH_DEADLINE_SECONDS", 1.0)
    monkeypatch.setattr(env.probe.sys, "platform", "darwin")
    release = threading.Event()

    def hung_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess:
        release.wait(10)  # ignores its own timeout, like a stuck GUI prompt
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", hung_run)

    started = time.monotonic()
    result = env.probe.probe("claude")
    elapsed = time.monotonic() - started

    release.set()
    _join_fetch_workers()
    assert (result.status, result.reason) == ("unavailable", "endpoint timed out")
    assert elapsed < 1.75


# ----- cached fields are re-validated (review F4) -------------------------------------


def _write_raw_cache(env: types.SimpleNamespace, platform: str, data: dict) -> None:
    path = env.nexus / "state" / "usage-probe" / f"{platform}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_tampered_cache_fields_are_normalised(env):
    _write_raw_cache(
        env,
        "claude",
        {
            "schema_version": 1,
            "platform": "claude",
            "data_at": T0 - 400,  # past the 300 s TTL, inside the stale window
            "windows": [
                {
                    "name": "five_hour",
                    "percent": 50,
                    "resets_at": "garbage <script>",
                    "source": "anthropic-oauth-usage",
                },
                {
                    "name": "weekly",
                    "percent": 60,
                    "resets_at": "2026-09-25T14:00:00+00:00",
                    "source": "attacker-source",
                },
                {
                    "name": "five_hour",
                    "percent": 40,
                    "resets_at": _OUT_OF_RANGE,
                    "source": "chatgpt-wham-usage",
                },
            ],
            "failed_at": T0 - 10,
            "reason": "injected <script> text",
        },
    )

    result = env.probe.probe("claude")

    assert (result.status, result.reason) == ("stale", "endpoint unreachable")
    assert [w.to_dict() for w in result.windows] == [
        {
            "name": "five_hour",
            "percent": 50.0,
            "resets_at": None,
            "source": "anthropic-oauth-usage",
        }
    ]
    assert env.http.calls == []


@pytest.mark.parametrize(
    "reason",
    [
        "credentials rejected (HTTP 401)",
        "endpoint error (HTTP 503)",
        "endpoint timed out",
    ],
)
def test_cached_reason_from_the_fixed_set_is_kept(env, reason):
    _write_raw_cache(
        env,
        "claude",
        {
            "schema_version": 1,
            "platform": "claude",
            "data_at": None,
            "windows": [],
            "failed_at": T0 - 5,
            "reason": reason,
        },
    )
    assert env.probe.probe("claude").reason == reason


def test_cached_resets_at_is_reformatted(env):
    _write_raw_cache(
        env,
        "codex",
        {
            "schema_version": 1,
            "platform": "codex",
            "data_at": T0 - 10,
            "windows": [
                {
                    "name": "weekly",
                    "percent": 30,
                    "resets_at": "2026-09-25T14:00:00+00:00",
                    "source": "chatgpt-wham-usage",
                }
            ],
        },
    )
    result = env.probe.probe("codex")
    assert result.cached is True
    assert result.windows[0].resets_at == "2026-09-25T14:00:00Z"


# ----- leak test (review F2) ----------------------------------------------------------


def _slices(secret: str, width: int = 12) -> set[str]:
    return {secret[i : i + width] for i in range(len(secret) - width + 1)}


SECRET_SLICES = {piece for secret in SECRETS for piece in _slices(secret)}


def _leaks(text: str) -> list[str]:
    return sorted(piece for piece in SECRET_SLICES if piece in text)


def _snapshot(directory: Path) -> dict[Path, tuple[int, int]]:
    found: dict[Path, tuple[int, int]] = {}
    try:
        entries = list(directory.iterdir())
    except OSError:
        return found
    for entry in entries:
        try:
            if entry.is_file():
                stat = entry.stat()
                found[entry] = (stat.st_size, stat.st_mtime_ns)
        except OSError:
            continue
    return found


def _exception_chain(error: BaseException) -> list[str]:
    texts: list[str] = []
    seen: set[int] = set()
    pending: list[BaseException | None] = [error]
    while pending:
        current = pending.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        texts += [str(current), repr(current), repr(getattr(current, "args", ()))]
        pending += [current.__context__, current.__cause__]
    return texts


def test_no_credential_reaches_any_output_cache_or_log(
    env, monkeypatch, capsys, caplog, tmp_path
):
    import tempfile

    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(env.probe.sys, "platform", "win32")
    write_codex_auth(env.home / ".codex")
    write_cursor_db(cursor_db_path(env))
    write_copilot(env, copilot_state())

    # Record every payload the probe writes, including ones later overwritten.
    written: list[str] = []
    real_write_cache = env.probe._write_cache

    def recording_write_cache(platform: str, payload: dict[str, Any]) -> None:
        written.append(json.dumps(payload, default=str))
        real_write_cache(platform, payload)

    monkeypatch.setattr(env.probe, "_write_cache", recording_write_cache)
    real_replace = os.replace

    def recording_replace(src: Any, dst: Any, *args: Any, **kwargs: Any) -> None:
        try:
            written.append(Path(src).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
        real_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", recording_replace)

    # Record every ProbeError so its __context__ / __cause__ chain is inspected.
    errors: list[BaseException] = []
    base_error = env.probe.ProbeError

    class RecordingProbeError(base_error):
        def __init__(self, reason: str) -> None:
            super().__init__(reason)
            errors.append(self)

    monkeypatch.setattr(env.probe, "ProbeError", RecordingProbeError)

    system_temp = Path(tempfile.gettempdir())
    temp_before = _snapshot(system_temp)
    outputs: list[str] = []
    scenarios: list[tuple[str, Any]] = [
        ("claude", CLAUDE_PAYLOAD),
        ("codex", CODEX_PAYLOAD_TWO_WINDOWS),
        ("cursor", CURSOR_PAYLOAD),
        ("claude", _http_error(401)),
        ("codex", _http_error(403)),
        ("codex", TimeoutError()),
        ("cursor", FakeResponse(b"garbage")),
        ("claude", {"unexpected": True}),
        ("claude", CLAUDE_PAYLOAD),
    ]
    for platform, answer in scenarios:
        env.clock.now += 3600  # expire the cache and the failure backoff
        write_claude_creds(env.home, expires_ms=(env.clock.now + 3600) * 1000)
        env.http.queue(answer)
        outputs.append(json.dumps(env.probe.probe(platform).to_dict()))
        env.http.answers.clear()
    outputs.append(json.dumps(env.probe.probe("copilot").to_dict()))
    env.clock.now += 3600
    bad = CLAUDE_TOKEN + "\nbad"
    write_claude_creds(env.home, token=bad, expires_ms=(env.clock.now + 3600) * 1000)
    outputs.append(json.dumps(env.probe.probe("claude").to_dict()))
    for platform in ("claude", "codex", "cursor", "copilot"):
        env.probe.main(["--platform", platform, "--json"])
        env.probe.main(["--platform", platform])

    captured = capsys.readouterr()
    haystack: dict[str, str] = {
        "probe results": "\n".join(outputs),
        "stdout": captured.out,
        "stderr": captured.err,
        "log records": caplog.text,
        "cache writes": "\n".join(written),
    }
    for index, error in enumerate(errors):
        haystack[f"ProbeError {index} chain"] = "\n".join(_exception_chain(error))
    # Credential SOURCES live under home/ and AppData/; every other file in the
    # test directory is something the probe produced.
    sources = (env.home, env.appdata)
    for path in tmp_path.rglob("*"):
        if path.is_file() and not any(src in path.parents for src in sources):
            haystack[str(path)] = path.read_text(encoding="utf-8", errors="replace")
    for path, stamp in _snapshot(system_temp).items():
        if temp_before.get(path) != stamp:
            try:
                haystack[str(path)] = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

    assert len(env.http.calls) >= 7, "the scenarios must exercise the providers"
    assert errors, "the scenarios must raise ProbeErrors for the chain walk"
    leaked = {where: _leaks(text) for where, text in haystack.items() if _leaks(text)}
    assert not leaked, f"fixture credential slices leaked into: {sorted(leaked)}"


# ----- delivery: sourced_modules() follows every helper (review F6) -------------------


def _sourced_modules() -> Any:
    repo_root = HOOKS_DIR.parent.parent
    sys.path.insert(0, str(repo_root))
    try:
        from scripts.lib.integrations._hooks_common import sourced_modules
    finally:
        sys.path.remove(str(repo_root))
    return sourced_modules


def _sourced(tmp_path: Path, files: dict[str, str], scripts: set[str]) -> set[str]:
    for name, body in files.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return _sourced_modules()(scripts, tmp_path)


_HELPERS = {
    "_a.py": "import _e\n",
    "_b.py": "X = 1\n",
    "_c.py": "X = 1\n",
    "_d.py": "X = 1\n",
    "_e.py": "X = 1\n",
    "_n.sh": "true\n",
    "_n.ps1": "$true\n",
    "__init__.py": "",
}


@pytest.mark.parametrize(
    ("hook", "body", "expected"),
    [
        ("plain.py", "import _b\n", {"_b.py"}),
        ("from.py", "from _b import X\n", {"_b.py"}),
        ("multi.py", "import os, _b\n", {"_b.py"}),
        ("comma.py", "import _c, _d\n", {"_c.py", "_d.py"}),
        ("alias.py", "import _c as c\n", {"_c.py"}),
        (
            "importlib.py",
            "import importlib\nm = importlib.import_module('_b')\n",
            {"_b.py"},
        ),
        ("transitive.py", "import _a\n", {"_a.py", "_e.py"}),
        ("doc.py", '"""Usage:\nimport _d\n"""\n# import _c\n', set()),
        ("dunder.py", "import __init__\n", set()),
        ("shell.sh", 'python3 "$DIR/_b.py"\n', {"_b.py"}),
        ("notify.sh", '. "$DIR/_n.sh"\n', {"_n.sh", "_n.ps1"}),
        ("commented.sh", "# like _b.py\ntrue\n", set()),
        ("commented.ps1", "<# like _b.py #>\n$true\n", set()),
        ("broken.py", "def (:\n", set()),
    ],
)
def test_sourced_modules_follows_every_helper(tmp_path, hook, body, expected):
    files = {**_HELPERS, hook: body}
    assert _sourced(tmp_path, files, {hook}) == expected


def test_sourced_modules_never_ships_a_test_only_helper(tmp_path):
    files = {
        "_shared.py": "X = 1\n",
        "hook.py": "import _shared\n",
        "tests/_fixture_helper.py": "X = 1\n",
        "tests/test_hook.py": "import _fixture_helper\n",
    }
    assert _sourced(tmp_path, files, {"hook.py"}) == {"_shared.py"}


def test_sourced_modules_on_the_real_catalog():
    sourced_modules = _sourced_modules()
    assert sourced_modules({"skill-activation-suggest.py"}, HOOKS_DIR) == {
        "_skill_rules.py"
    }
    assert sourced_modules({"notify-on-complete.sh"}, HOOKS_DIR) == {
        "_notify_common.sh",
        "_notify_common.ps1",
    }


# ----- single-flight fetch and process-local backoff (Phase 7 review, F5) -------


def _fetch_lock(env: types.SimpleNamespace, platform: str = "claude") -> Path:
    return env.nexus / "state" / "usage-probe" / f".{platform}.fetch.lock"


def test_a_fetch_in_progress_returns_the_cached_value_without_fetching(env):
    write_claude_creds(env.home)
    env.http.queue(CLAUDE_PAYLOAD)
    env.probe.probe("claude")
    env.clock.now += 400  # past the TTL
    lock = _fetch_lock(env)
    lock.write_text("", encoding="utf-8")
    os.utime(lock, (env.clock.now, env.clock.now))

    busy = env.probe.probe("claude")

    assert busy.status == "stale" and busy.reason == "fetch in progress"
    assert windows(busy) == {"five_hour": 42.0, "weekly": 77.5}
    assert len(env.http.calls) == 1
    assert lock.exists(), "a loser must not remove the winner's lock"


def test_a_fetch_in_progress_with_no_cache_is_unavailable(env):
    write_claude_creds(env.home)
    lock = _fetch_lock(env)
    lock.parent.mkdir(parents=True)
    lock.write_text("", encoding="utf-8")
    os.utime(lock, (env.clock.now, env.clock.now))

    result = env.probe.probe("claude")

    assert (result.status, result.reason) == ("unavailable", "fetch in progress")
    assert env.http.calls == []


def test_a_stale_fetch_lock_is_broken_and_released(env):
    write_claude_creds(env.home)
    lock = _fetch_lock(env)
    lock.parent.mkdir(parents=True)
    lock.write_text("", encoding="utf-8")
    old = env.clock.now - 60
    os.utime(lock, (old, old))
    env.http.queue(CLAUDE_PAYLOAD)

    assert env.probe.probe("claude").status == "ok"
    assert not lock.exists()


def test_the_winner_releases_the_lock_after_a_failure(env):
    write_claude_creds(env.home)
    env.http.queue(TimeoutError())
    env.probe.probe("claude")
    assert not _fetch_lock(env).exists()


def test_process_local_backoff_holds_when_the_cache_is_unwritable(env, monkeypatch):
    write_claude_creds(env.home)
    env.nexus.mkdir(parents=True)
    (env.nexus / "state").write_text("not a directory", encoding="utf-8")
    env.http.queue(urllib.error.URLError("offline"))
    assert env.probe.probe("claude").reason == "endpoint unreachable"
    env.clock.now += 30

    again = env.probe.probe("claude")

    assert again.reason == "endpoint unreachable"
    assert len(env.http.calls) == 1, "no second fetch inside the backoff"
    env.clock.now += 31
    env.http.queue(CLAUDE_PAYLOAD)
    assert env.probe.probe("claude").status == "ok"
    assert len(env.http.calls) == 2
