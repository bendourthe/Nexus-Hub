"""Shared usage probe: current utilization of each tracked usage window.

Imported by the ``usage-guard`` hook (and, later, ``/usage``) and runnable as
``python _usage_probe.py --platform <claude|codex|cursor|copilot> --json``.

Contract
--------
``probe(platform)`` returns a :class:`ProbeResult` whose ``status`` is ``ok``,
``stale``, or ``unavailable``. Each window carries ``name`` (``five_hour``,
``weekly``, ``monthly``), ``percent`` (0-100 float), ``resets_at`` (ISO 8601 or
None, display only, never used for a trigger decision), and ``source``.
``probe`` never raises and never writes to stdout; only the ``--json`` CLI prints.

Sources (decision file v4.13.7, "Handoff guard decisions" (1) and (3)):

- ``claude``: ``~/.claude/.credentials.json`` (macOS: the login Keychain item,
  2-second timeout) -> ``GET https://api.anthropic.com/api/oauth/usage``.
  Windows ``five_hour`` and ``weekly`` (``seven_day`` and every model-scoped
  weekly figure, highest wins).
- ``codex``: ``$CODEX_HOME/auth.json`` or ``~/.codex/auth.json`` ->
  ``GET https://chatgpt.com/backend-api/wham/usage``. ``weekly`` only, chosen
  by window length, not position.
- ``cursor``: ``cursorAuth/accessToken`` from the local ``state.vscdb``, opened
  read-only -> ``POST https://api2.cursor.sh/aiserver.v1.DashboardService/
  GetCurrentPeriodUsage``. ``monthly``, taken as delivered, never recomputed.
- ``copilot``: ``~/.nexus-hub/state/usage-probe/copilot.json``, written by the
  Copilot Usage Monitor. No network call and no credential read. That path is
  also where every other provider's cache lives, so the probe never writes it.

Credential handling: tokens live only in local variables of the provider that
reads them. They are never logged, cached, printed, or placed in a reason
string, and every request goes only to that vendor's own host (redirects are
refused so an ``Authorization`` header cannot follow one elsewhere). The probe
never refreshes a token, so it never writes to a vendor's credential store.

Each live fetch (credential read, Keychain, DNS, connect, reads) runs under a
3-second wall-clock deadline, inside the guard's 5-second hook budget.

Switches: ``NEXUS_USAGE_PROBE_DISABLED=1`` turns the probe off;
``NEXUS_USAGE_PROBE_PROVIDERS`` (comma-separated subset of
``claude,codex,cursor,copilot``, default all) limits it. ``NEXUS_HOME``
relocates ``~/.nexus-hub`` as for the other hooks.

stdlib only. ``urllib`` and ``sqlite3`` are imported only on a live fetch, so a
cache hit stays cheap on every tool call. Part of Nexus-Hub.
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLATFORMS = ("claude", "codex", "cursor", "copilot")

# Cache policy (plan 6.1).
TTL_SECONDS = 300
TTL_NEAR_LIMIT_SECONDS = 60
NEAR_LIMIT_PERCENT = 90.0
STALE_MAX_SECONDS = 1800
# After a failed live fetch, wait this long before trying the network again, so
# an offline host does not pay the request timeout on every tool call.
FAILURE_BACKOFF_SECONDS = 60
REQUEST_TIMEOUT_SECONDS = 3.0
KEYCHAIN_TIMEOUT_SECONDS = 2.0
COPILOT_MAX_AGE_SECONDS = 1800
MAX_RESPONSE_BYTES = 1_000_000
CACHE_SCHEMA_VERSION = 1

CLAUDE_USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
CLAUDE_BETA_HEADER = "oauth-2025-04-20"
CLAUDE_KEYCHAIN_SERVICES = ("Claude Code-credentials", "Claude Code")
CODEX_USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"
CURSOR_USAGE_URL = (
    "https://api2.cursor.sh/aiserver.v1.DashboardService/GetCurrentPeriodUsage"
)
CURSOR_SESSION_KEY = "cursorAuth/accessToken"
CURSOR_SESSION_QUERY = "SELECT value FROM ItemTable WHERE key = ? LIMIT 1"

# One vendor host per provider; a provider's request to any other host is refused.
PROVIDER_HOSTS = {
    "claude": "api.anthropic.com",
    "codex": "chatgpt.com",
    "cursor": "api2.cursor.sh",
}
PROVIDER_SOURCES = {
    "claude": "anthropic-oauth-usage",
    "codex": "chatgpt-wham-usage",
    "cursor": "cursor-dashboard-rpc",
}
# Wall-clock budget for one whole live fetch: credential read (including the
# macOS Keychain), DNS, connect, and every read. REQUEST_TIMEOUT_SECONDS is per
# socket operation only, so a server dripping bytes could otherwise hold the
# hook far past the guard's 5-second budget.
FETCH_DEADLINE_SECONDS = 3.0

# Every reason a provider can report. A cached reason outside this set (or the
# HTTP-status pattern below) is replaced, so a tampered cache cannot inject text.
FIXED_REASONS = frozenset(
    {
        "credentials missing",
        "credentials unreadable",
        "credentials expired",
        "keychain read timed out",
        "endpoint timed out",
        "endpoint unreachable",
        "refused: host not allowlisted",
        "unexpected response",
        "unexpected response: not JSON",
        "unexpected response: too large",
        "unexpected response: no tracked window",
    }
)
HTTP_REASON_RE = re.compile(
    r"(?:credentials rejected|endpoint error|rate limited) \(HTTP [1-5][0-9]{2}\)"
)

# A window longer than this is the weekly window (Codex classifies by length).
SESSION_MAX_SECONDS = 6 * 3600


class ProbeError(Exception):
    """A provider failure carrying a fixed, credential-free reason string."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class Window:
    """One tracked usage window."""

    __slots__ = ("name", "percent", "resets_at", "source")

    def __init__(
        self, name: str, percent: float, resets_at: str | None, source: str
    ) -> None:
        self.name = name
        self.percent = percent
        self.resets_at = resets_at
        self.source = source

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "percent": self.percent,
            "resets_at": self.resets_at,
            "source": self.source,
        }


class ProbeResult:
    """The probe's answer for one platform."""

    __slots__ = ("cached", "fetched_at", "platform", "reason", "status", "windows")

    def __init__(
        self,
        platform: str,
        status: str,
        windows: list[Window] | None = None,
        cached: bool = False,
        fetched_at: str | None = None,
        reason: str | None = None,
    ) -> None:
        self.platform = platform
        self.status = status
        self.windows = windows or []
        self.cached = cached
        self.fetched_at = fetched_at
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "status": self.status,
            "cached": self.cached,
            "fetched_at": self.fetched_at,
            "windows": [w.to_dict() for w in self.windows],
            "reason": self.reason,
        }


def _unavailable(platform: str, reason: str) -> ProbeResult:
    return ProbeResult(platform, "unavailable", reason=reason)


# ----- small helpers ----------------------------------------------------------


def _iso(epoch_seconds: float) -> str:
    return (
        datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _safe_iso(epoch_seconds: float | None) -> str | None:
    """``_iso`` that returns None for an unrepresentable instant."""
    if epoch_seconds is None:
        return None
    try:
        return _iso(epoch_seconds)
    except (OverflowError, OSError, ValueError):
        return None


def _parse_iso(value: object) -> float | None:
    """Epoch seconds for an ISO 8601 string, or None."""
    if not isinstance(value, str) or not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (OverflowError, OSError, ValueError):
        return None


def _number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str) and value.strip():
        try:
            number = float(value)
        except ValueError:
            return None
    else:
        return None
    return number if math.isfinite(number) else None


def _percent(value: object) -> float | None:
    number = _number(value)
    if number is None:
        return None
    return round(min(max(number, 0.0), 100.0), 2)


def _reset_iso(value: object) -> str | None:
    """Normalize an ISO string or an epoch number (s or ms) to ISO, else None.

    An out-of-range date (year 1, year 9999 with an offset, before 1970 on
    Windows) drops the reset time and keeps the window: reset times are
    display-only, so an unrepresentable one must never cost the percentage.
    """
    try:
        if isinstance(value, str):
            parsed = _parse_iso(value)
            if parsed is not None:
                return _iso(parsed)
        number = _number(value)
        if number is None or number <= 0:
            return None
        return _iso(number / 1000.0 if number >= 1e12 else number)
    except (OverflowError, OSError, ValueError):
        return None


def _record(value: object) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _keep_highest(windows: dict[str, Window], candidate: Window | None) -> None:
    if candidate is None:
        return
    current = windows.get(candidate.name)
    if current is None or candidate.percent > current.percent:
        windows[candidate.name] = candidate


def nexus_home() -> Path:
    override = os.environ.get("NEXUS_HOME", "").strip()
    return Path(override) if override else Path.home() / ".nexus-hub"


def state_dir() -> Path:
    return nexus_home() / "state" / "usage-probe"


# ----- HTTP layer (the only network seam; tests stub `_open`) -----------------


def _opener() -> Any:
    """Build a urllib opener that refuses every redirect.

    urllib forwards request headers, including ``Authorization``, to a redirect
    target, so following one could hand a token to a host that is not the
    vendor's. A refused redirect surfaces as an ``HTTPError`` with the 3xx code.
    """
    import urllib.request

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args: Any, **kwargs: Any) -> None:
            return None

    return urllib.request.build_opener(_NoRedirect())


def _open(request: Any, timeout: float) -> Any:
    """Open ``request`` with redirects refused, returning the response object."""
    return _opener().open(request, timeout=timeout)


def _http_json(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None = None,
    *,
    expected_host: str,
) -> Any:
    """Send one request to ``expected_host`` over https and decode a JSON body.

    Raises :class:`ProbeError` with a fixed reason on every failure. No
    exception text is carried into the reason, because a header-validation
    error from ``http.client`` can quote the header value (the token). Each
    ProbeError is raised after its ``except`` block has closed, so it carries
    no ``__context__``: the original exception, which may quote a header or a
    response body, is released rather than chained.
    """
    import urllib.error
    import urllib.parse
    import urllib.request

    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or (parts.hostname or "") != expected_host:
        raise ProbeError("refused: host not allowlisted")
    request = urllib.request.Request(url, data=body, method=method)
    for key, value in headers.items():
        request.add_header(key, value)
    failure = ""
    status, raw = 0, b""
    try:
        with _open(request, REQUEST_TIMEOUT_SECONDS) as response:
            status = getattr(response, "status", 200)
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        code = int(exc.code)
        if code in (401, 403):
            failure = f"credentials rejected (HTTP {code})"
        elif code == 429:
            failure = "rate limited (HTTP 429)"
        else:
            failure = f"endpoint error (HTTP {code})"
    except TimeoutError:
        failure = "endpoint timed out"
    except (urllib.error.URLError, OSError, ValueError):
        failure = "endpoint unreachable"
    if failure:
        raise ProbeError(failure)
    if status != 200:
        raise ProbeError(f"endpoint error (HTTP {int(status)})")
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ProbeError("unexpected response: too large")
    payload = _loads(raw)
    if payload is _INVALID:
        raise ProbeError("unexpected response: not JSON")
    return payload


_INVALID = object()


def _loads(raw: bytes | str) -> Any:
    """Decode JSON, returning ``_INVALID`` (never raising) on any bad input.

    A ``JSONDecodeError`` keeps the whole document in ``.doc``; returning a
    sentinel instead of raising means that object is dropped here and never
    chained onto a later exception.
    """
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return json.loads(text)
    except (UnicodeDecodeError, ValueError, RecursionError):
        return _INVALID


# ----- Claude Code ------------------------------------------------------------


def _claude_credentials_path() -> Path:
    return Path.home() / ".claude" / ".credentials.json"


def _claude_parse_credentials(raw: str) -> dict[str, Any] | None:
    root = _record(_loads(raw))
    oauth = _record(root.get("claudeAiOauth")) if root else None
    if oauth is None or not _first_string(oauth.get("accessToken")):
        return None
    return oauth


def _claude_keychain() -> str | None:
    """Read the macOS Keychain item, or None. Never waits on a GUI prompt."""
    import subprocess

    for service in CLAUDE_KEYCHAIN_SERVICES:
        timed_out = False
        try:
            done = subprocess.run(
                ["security", "find-generic-password", "-s", service, "-w"],
                capture_output=True,
                text=True,
                timeout=KEYCHAIN_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            # Its .output may hold the secret; flag it and let it go.
            timed_out = True
        except OSError:
            return None
        if timed_out:
            raise ProbeError("keychain read timed out")
        if done.returncode == 0 and done.stdout.strip():
            return done.stdout.strip()
    return None


def _claude_read_token() -> str:
    oauth: dict[str, Any] | None = None
    path = _claude_credentials_path()
    raw: str | None = None
    unreadable = False
    try:
        if path.is_file():
            raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        unreadable = True
    if raw is not None:
        oauth = _claude_parse_credentials(raw)
        unreadable = oauth is None
    if unreadable:
        raise ProbeError("credentials unreadable")
    if oauth is None and sys.platform == "darwin":
        raw = _claude_keychain()
        oauth = _claude_parse_credentials(raw) if raw else None
    if oauth is None:
        raise ProbeError("credentials missing")
    expires_at = _number(oauth.get("expiresAt"))
    if expires_at is not None and expires_at > 0 and time.time() * 1000 >= expires_at:
        raise ProbeError("credentials expired")
    return str(oauth["accessToken"])


def map_claude(payload: object) -> list[Window]:
    """Map the OAuth usage payload to ``five_hour`` and ``weekly`` windows.

    Reads the self-describing ``limits`` array and the older flat fields, and
    keeps the highest figure per window name, so a renamed or added model
    window raises the weekly figure rather than hiding it.
    """
    data = _record(payload)
    if data is None:
        return []
    source = "anthropic-oauth-usage"
    windows: dict[str, Window] = {}
    limits = data.get("limits")
    for entry in limits if isinstance(limits, list) else []:
        entry = _record(entry)
        if entry is None:
            continue
        kind = entry.get("kind")
        if kind == "session":
            name = "five_hour"
        elif kind in ("weekly_all", "weekly_scoped"):
            name = "weekly"
        else:
            name = ""
        percent = _percent(entry.get("percent"))
        if name and percent is not None:
            _keep_highest(
                windows,
                Window(name, percent, _reset_iso(entry.get("resets_at")), source),
            )
    for key, value in data.items():
        if key == "five_hour":
            name = "five_hour"
        elif key == "seven_day" or key.startswith("seven_day_"):
            name = "weekly"
        else:
            continue
        limit = _record(value)
        percent = _percent(limit.get("utilization")) if limit else None
        if limit is not None and percent is not None:
            _keep_highest(
                windows,
                Window(name, percent, _reset_iso(limit.get("resets_at")), source),
            )
    return [windows[n] for n in ("five_hour", "weekly") if n in windows]


def _fetch_claude() -> list[Window]:
    token = _claude_read_token()
    payload = _http_json(
        "GET",
        CLAUDE_USAGE_URL,
        {
            "Authorization": f"Bearer {token}",
            "anthropic-beta": CLAUDE_BETA_HEADER,
            "Accept": "application/json",
        },
        expected_host=PROVIDER_HOSTS["claude"],
    )
    return map_claude(payload)


# ----- Codex ------------------------------------------------------------------


def _codex_auth_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME", "").strip()
    base = Path(codex_home) if codex_home else Path.home() / ".codex"
    return base / "auth.json"


def _first_string(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return None


def _codex_read_credential() -> tuple[str, str | None]:
    path = _codex_auth_path()
    if not path.is_file():
        raise ProbeError("credentials missing")
    parsed: Any = _INVALID
    try:
        parsed = _loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        parsed = _INVALID
    if parsed is _INVALID:
        raise ProbeError("credentials unreadable")
    root = _record(parsed) or {}
    tokens = _record(root.get("tokens")) or {}
    token = _first_string(
        tokens.get("access_token"),
        tokens.get("accessToken"),
        root.get("access_token"),
        root.get("accessToken"),
    )
    if token is None:
        raise ProbeError("credentials missing")
    account = _first_string(
        tokens.get("account_id"),
        tokens.get("accountId"),
        root.get("account_id"),
        root.get("accountId"),
    )
    return token, account


def map_codex(payload: object) -> list[Window]:
    """Map ``wham/usage`` to the ``weekly`` window only (decision 3)."""
    data = _record(payload)
    if data is None:
        return []
    container = (
        _record(data.get("rate_limit")) or _record(data.get("rate_limits")) or data
    )
    positioned = (
        (container.get("primary_window"), False),
        (container.get("secondary_window"), True),
    )
    weekly: dict[str, Window] = {}
    for raw, is_secondary in positioned:
        window = _record(raw)
        if window is None:
            continue
        percent = _percent(window.get("used_percent"))
        if percent is None:
            continue
        seconds = _number(window.get("limit_window_seconds"))
        is_weekly = (
            seconds > SESSION_MAX_SECONDS if seconds is not None else is_secondary
        )
        if is_weekly:
            reset = _reset_iso(window.get("reset_at", window.get("resets_at")))
            _keep_highest(
                weekly, Window("weekly", percent, reset, "chatgpt-wham-usage")
            )
    return list(weekly.values())


def _fetch_codex() -> list[Window]:
    token, account = _codex_read_credential()
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if account and not account.startswith(("email_", "local_")):
        headers["chatgpt-account-id"] = account
    payload = _http_json(
        "GET", CODEX_USAGE_URL, headers, expected_host=PROVIDER_HOSTS["codex"]
    )
    return map_codex(payload)


# ----- Cursor -----------------------------------------------------------------


def cursor_state_path(platform: str | None = None) -> Path | None:
    """Return Cursor's global ``state.vscdb`` path for this OS, or None."""
    platform = platform or sys.platform
    if platform == "win32":
        appdata = os.environ.get("APPDATA", "").strip()
        if not appdata:
            return None
        return Path(appdata) / "Cursor" / "User" / "globalStorage" / "state.vscdb"
    if platform == "darwin":
        return (
            Path.home()
            / "Library"
            / "Application Support"
            / "Cursor"
            / "User"
            / "globalStorage"
            / "state.vscdb"
        )
    if platform.startswith("linux"):
        xdg = os.environ.get("XDG_CONFIG_HOME", "").strip()
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "Cursor" / "User" / "globalStorage" / "state.vscdb"
    return None


def _cursor_read_token() -> str:
    import sqlite3

    path = cursor_state_path()
    if path is None or not path.is_file():
        raise ProbeError("credentials missing")
    row: Any = None
    unreadable = False
    try:
        connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=1.0)
        try:
            row = connection.execute(
                CURSOR_SESSION_QUERY, (CURSOR_SESSION_KEY,)
            ).fetchone()
        finally:
            connection.close()
    except (sqlite3.Error, ValueError):
        unreadable = True
    if unreadable:
        raise ProbeError("credentials unreadable")
    value = row[0] if row else None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    token = value.strip() if isinstance(value, str) else ""
    if not 16 <= len(token) <= 8192 or any(
        ord(c) <= 0x20 or ord(c) == 0x7F for c in token
    ):
        raise ProbeError("credentials missing")
    return token


def map_cursor(payload: object) -> list[Window]:
    """Map the usage RPC to ``monthly``: delivered percentages, never derived."""
    data = _record(payload)
    if data is None:
        return []
    plan = _record(data.get("planUsage")) or {}
    percent = _percent(plan.get("totalPercentUsed"))
    if percent is None:
        pools = [_percent(plan.get(k)) for k in ("autoPercentUsed", "apiPercentUsed")]
        known = [p for p in pools if p is not None]
        percent = max(known) if known else None
    if percent is None:
        return []
    reset = _reset_iso(data.get("billingCycleEnd"))
    return [Window("monthly", percent, reset, "cursor-dashboard-rpc")]


def _fetch_cursor() -> list[Window]:
    token = _cursor_read_token()
    payload = _http_json(
        "POST",
        CURSOR_USAGE_URL,
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body=b"{}",
        expected_host=PROVIDER_HOSTS["cursor"],
    )
    return map_cursor(payload)


# ----- GitHub Copilot (state file only) ---------------------------------------


def copilot_state_path() -> Path:
    return state_dir() / "copilot.json"


def read_copilot(now: float | None = None) -> ProbeResult:
    """Read the Copilot Usage Monitor's percentages-only state file.

    Schema: decision file v4.13.7, Copilot usage monitor item (6). Unknown keys
    are ignored and never copied into the result.
    """
    now = time.time() if now is None else now
    path = copilot_state_path()
    try:
        data = _loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _unavailable(
            "copilot", "state file missing (Copilot Usage Monitor not running)"
        )
    except (OSError, UnicodeDecodeError):
        return _unavailable("copilot", "state file unreadable")
    if data is _INVALID:
        return _unavailable("copilot", "state file unreadable")
    data = _record(data)
    if (
        data is None
        or data.get("schema_version") != 1
        or data.get("provider") != "copilot"
    ):
        return _unavailable("copilot", "state file schema not recognized")
    fetched = _parse_iso(data.get("fetched_at"))
    if fetched is None:
        return _unavailable("copilot", "state file schema not recognized")
    if now - fetched > COPILOT_MAX_AGE_SECONDS:
        return _unavailable("copilot", "state file older than 30 minutes")
    if fetched - now > 300:
        return _unavailable("copilot", "state file timestamp in the future")
    raw_windows = data.get("windows")
    if not isinstance(raw_windows, list):
        return _unavailable("copilot", "state file schema not recognized")
    windows: dict[str, Window] = {}
    for raw in raw_windows:
        entry = _record(raw)
        if entry is None or entry.get("name") != "monthly":
            continue
        percent = _percent(entry.get("percent"))
        source = entry.get("source")
        if percent is None or source not in ("personal", "organization"):
            continue
        _keep_highest(
            windows,
            Window("monthly", percent, _reset_iso(entry.get("resets_at")), source),
        )
    if not windows:
        return _unavailable("copilot", "no percentage reported (no readable quota)")
    return ProbeResult(
        "copilot",
        "ok",
        list(windows.values()),
        cached=False,
        fetched_at=_safe_iso(fetched),
    )


# ----- cache --------------------------------------------------------------------


def _cache_path(platform: str) -> Path:
    return state_dir() / f"{platform}.json"


def _read_cache(platform: str) -> dict[str, Any] | None:
    try:
        data = _loads(_cache_path(platform).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
    data = _record(data)
    if data is None or data.get("schema_version") != CACHE_SCHEMA_VERSION:
        return None
    if data.get("platform") != platform:
        return None
    return data


def _cached_windows(platform: str, cache: dict[str, Any]) -> list[Window]:
    """Rebuild windows from the cache, re-validating every field.

    The cache is a file on disk; anything this probe would not itself have
    written (an unknown name or source, a malformed reset time) is dropped.
    """
    windows: list[Window] = []
    raw_windows = cache.get("windows")
    for raw in raw_windows if isinstance(raw_windows, list) else []:
        entry = _record(raw)
        if entry is None:
            continue
        percent = _percent(entry.get("percent"))
        name = entry.get("name")
        if percent is None or name not in ("five_hour", "weekly", "monthly"):
            continue
        if entry.get("source") != PROVIDER_SOURCES.get(platform):
            continue
        windows.append(
            Window(
                str(name), percent, _reset_iso(entry.get("resets_at")), entry["source"]
            )
        )
    return windows


def _safe_reason(value: object) -> str:
    """A cached reason, if it is one this probe produces; else a fixed default."""
    if isinstance(value, str) and (
        value in FIXED_REASONS or HTTP_REASON_RE.fullmatch(value)
    ):
        return value
    return "endpoint unreachable"


def _write_cache(platform: str, payload: dict[str, Any]) -> None:
    """Write the cache atomically (temp sibling + rename). Best effort."""
    import tempfile

    if platform == "copilot":  # the monitor owns that file; never overwrite it
        return
    directory = state_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(
            prefix=f".{platform}.", suffix=".tmp", dir=directory
        )
    except OSError:
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        os.replace(temp, _cache_path(platform))
    except OSError:
        try:
            os.unlink(temp)
        except OSError:
            pass


def _ttl_for(windows: list[Window]) -> int:
    if any(w.percent >= NEAR_LIMIT_PERCENT for w in windows):
        return TTL_NEAR_LIMIT_SECONDS
    return TTL_SECONDS


_FETCHERS: dict[str, Callable[[], list[Window]]] = {
    "claude": _fetch_claude,
    "codex": _fetch_codex,
    "cursor": _fetch_cursor,
}


def _run_with_deadline(fetcher: Callable[[], list[Window]]) -> list[Window]:
    """Run one fetch under FETCH_DEADLINE_SECONDS of wall-clock time.

    The fetch (credential read, Keychain, DNS, connect, every read) runs in a
    daemon thread. On overrun the caller gets ``endpoint timed out`` and the
    thread's eventual result is discarded: only the caller writes the cache,
    and it never sees a late result. Any exception inside the fetch, including
    a mapper bug or a RecursionError, becomes ``unexpected response`` so the
    failure record, backoff, and stale fallback still apply. No exception
    object leaves the thread, so a traceback holding a token is never kept.
    """
    import threading

    box: dict[str, Any] = {}

    def run() -> None:
        try:
            box["value"] = fetcher()
        except ProbeError as exc:
            box["error"] = exc.reason
        except Exception:  # noqa: BLE001 - converted to a fixed reason below
            box["error"] = "unexpected response"

    worker = threading.Thread(target=run, name="usage-probe-fetch", daemon=True)
    worker.start()
    worker.join(FETCH_DEADLINE_SECONDS)
    if worker.is_alive():
        raise ProbeError("endpoint timed out")
    if "error" in box:
        raise ProbeError(box["error"])
    value = box.get("value")
    return value if isinstance(value, list) else []


def _enabled_providers() -> set[str]:
    raw = os.environ.get("NEXUS_USAGE_PROBE_PROVIDERS", "").strip()
    if not raw:
        return set(PLATFORMS)
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


def _probe_network(platform: str, now: float) -> ProbeResult:
    cache = _read_cache(platform)
    data_at = _number(cache.get("data_at")) if cache else None
    windows = _cached_windows(platform, cache) if cache and data_at is not None else []
    age = now - data_at if data_at is not None else None

    if age is not None and 0 <= age < _ttl_for(windows) and windows:
        return ProbeResult(
            platform, "ok", windows, cached=True, fetched_at=_safe_iso(data_at)
        )

    failed_at = _number(cache.get("failed_at")) if cache else None
    if failed_at is not None and 0 <= now - failed_at < FAILURE_BACKOFF_SECONDS:
        reason = _safe_reason(cache.get("reason") if cache else None)
        return _fallback(platform, windows, data_at, age, reason)

    try:
        fresh = _run_with_deadline(_FETCHERS[platform])
        if not fresh:
            raise ProbeError("unexpected response: no tracked window")
    except ProbeError as exc:
        _write_cache(
            platform,
            {
                "schema_version": CACHE_SCHEMA_VERSION,
                "platform": platform,
                "data_at": data_at,
                "windows": [w.to_dict() for w in windows],
                "failed_at": now,
                "reason": exc.reason,
            },
        )
        return _fallback(platform, windows, data_at, age, exc.reason)

    _write_cache(
        platform,
        {
            "schema_version": CACHE_SCHEMA_VERSION,
            "platform": platform,
            "data_at": now,
            "windows": [w.to_dict() for w in fresh],
        },
    )
    return ProbeResult(platform, "ok", fresh, cached=False, fetched_at=_iso(now))


def _fallback(
    platform: str,
    windows: list[Window],
    data_at: float | None,
    age: float | None,
    reason: str,
) -> ProbeResult:
    if (
        windows
        and data_at is not None
        and age is not None
        and 0 <= age < STALE_MAX_SECONDS
    ):
        return ProbeResult(
            platform,
            "stale",
            windows,
            cached=True,
            fetched_at=_safe_iso(data_at),
            reason=reason,
        )
    return _unavailable(platform, reason)


def probe(platform: str) -> ProbeResult:
    """Return the current usage windows for ``platform``. Never raises."""
    key = str(platform or "").strip().lower()
    try:
        if os.environ.get("NEXUS_USAGE_PROBE_DISABLED", "").strip() == "1":
            return _unavailable(key, "disabled by NEXUS_USAGE_PROBE_DISABLED")
        if key not in PLATFORMS:
            return _unavailable(key, "no usage source for this platform")
        if key not in _enabled_providers():
            return _unavailable(key, "provider disabled by NEXUS_USAGE_PROBE_PROVIDERS")
        if key == "copilot":
            return read_copilot()
        return _probe_network(key, time.time())
    except Exception:  # noqa: BLE001 - the contract is "never raise into the hook"
        return _unavailable(key, "internal error")


def main(argv: list[str] | None = None) -> int:
    """CLI: ``--platform <key> [--json]``. Always exits 0."""
    args = list(sys.argv[1:] if argv is None else argv)
    platform = ""
    if "--platform" in args:
        index = args.index("--platform")
        platform = args[index + 1] if index + 1 < len(args) else ""
    result = probe(platform).to_dict()
    if "--json" in args:
        sys.stdout.write(json.dumps(result) + "\n")
    else:
        parts = [f"{w['name']} {w['percent']}%" for w in result["windows"]]
        summary = ", ".join(parts) or result.get("reason") or ""
        sys.stderr.write(f"{result['platform']}: {result['status']} {summary}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
