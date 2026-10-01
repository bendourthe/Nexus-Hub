#!/usr/bin/env python3
"""usage-guard: direct a session hand-off before a usage window runs out.

Part of Nexus-Hub (v4.13.7). Registered on ``UserPromptSubmit``,
``PostToolUse``, and ``Stop`` in ``catalog/hooks/settings.json``, and natively on
Cursor ``postToolUse`` / ``stop``. It reads the platform's own usage through the
shared ``_usage_probe`` module beside it and, when a tracked window is at or over
``NEXUS_HANDOFF_THRESHOLD`` percent (integer 1-100, default 99), tells the agent
to finish the current step and run the session-handoff procedure (``/handoff``).

Behavior
--------
- Mid-session, the first crossing of a window in a session emits one directive
  through the platform's context channel. A window counts as announced only
  once a message about it was emitted.
- At turn end, every window over the threshold whose continuation was not yet
  sent gets one continuation asking for the hand-off, the highest first, one per
  turn end. The platform's prior-continuation flag (``stop_hook_active`` on
  Claude Code, Codex, and Copilot; ``loop_count > 0`` on Cursor) is honored only
  when this guard's own continuation caused that turn, because the completion
  gate sets it on every chained turn. A window is skipped once
  ``.nexus-hub/handoff.md`` carries a ``usage-limit`` trigger written at or after
  its announcement. A routine checkpoint does not count, because it prints no
  paste-ready prompt.
- A window that falls below the clear line (the threshold minus up to 5 points),
  or whose reset time moves to a new period, is forgotten, so the next crossing
  warns again.
- Everything else is silent with exit 0: an unrecognized platform (Qwen, Gemini
  CLI, Kimi, anything new), malformed stdin, an ``unavailable`` probe, a
  ``stale`` reading older than 30 minutes, a state file that cannot be written
  (so a broken state directory can never cause a repeated prompt), and a probe
  that overruns the 5-second hook budget. The probe's own 3-second fetch
  deadline sits inside that budget.

Platform detection follows decision (2) of the v4.13.7 handoff guard decisions:
positive signatures only, tested in the order Cursor, Codex, Kimi, Gemini CLI,
Qwen, Claude Code, Copilot. A Cursor payload arriving through a ``.claude/hooks/``
path (Cursor's import of Claude hooks) is silent, so Cursor hears the guard once,
through its native ``hooks.json``. Copilot runs through ``copilot-hook-compat.py``,
which rewrites the payload, so its signature is the install directory plus the
ISO-8601 ``timestamp`` VS Code sends.

Per-session state lives in ``~/.nexus-hub/state/usage-guard/<platform>-<session>.json``
with ``triggered_window``, ``triggered_at``, ``continuation_sent`` (the latest
announcement), and per window its reset time, announcement time, and
continuation flag. It holds no credential, no usage response, and no prompt text.

Runtime controls: ``NEXUS_DISABLED_HOOKS=usage-guard`` or
``NEXUS_HOOK_PROFILE=minimal`` disables the hook; ``NEXUS_HOME`` relocates
``~/.nexus-hub``. stdlib only; makes no network call of its own.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOOK_NAME = "usage-guard"
DEFAULT_THRESHOLD = 99
HOOK_BUDGET_SECONDS = 5.0
BUDGET_MARGIN_SECONDS = 0.5
STALE_LIMIT_SECONDS = 1800
LOCK_WAIT_SECONDS = 0.5
LOCK_STALE_SECONDS = 10.0
STATE_RETENTION_SECONDS = 7 * 24 * 3600
STATE_SCHEMA = 2
HYSTERESIS_POINTS = 5.0
PERIOD_SHIFT_SECONDS = 1800
MAX_STDIN_BYTES = 8 * 1024 * 1024

DISPLAY_NAMES = {
    "claude": "Claude Code",
    "codex": "Codex",
    "cursor": "Cursor",
    "copilot": "GitHub Copilot",
}

GEMINI_EVENTS = frozenset(
    {"BeforeTool", "AfterTool", "BeforeAgent", "AfterAgent", "BeforeModel", "AfterModel"}
)
COPILOT_EVENTS = frozenset({"UserPromptSubmit", "PostToolUse", "Stop"})

# (platform, payload event) -> "prompt" | "tool" | "stop". Events with no
# context channel are absent: Cursor's beforeSubmitPrompt and VS Code's
# UserPromptSubmit carry no context field, so the next tool call delivers it.
EVENT_KINDS = {
    ("claude", "UserPromptSubmit"): "prompt",
    ("claude", "PostToolUse"): "tool",
    ("claude", "Stop"): "stop",
    ("codex", "UserPromptSubmit"): "prompt",
    ("codex", "PostToolUse"): "tool",
    ("codex", "Stop"): "stop",
    ("cursor", "postToolUse"): "tool",
    ("cursor", "stop"): "stop",
    ("copilot", "PostToolUse"): "tool",
    ("copilot", "Stop"): "stop",
}

HEADER_RE = re.compile(
    r"^# Handoff \| (?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \| [a-z0-9-]+ \| "
    r"(?P<trigger>usage-limit (?:five_hour|weekly|monthly) \d+(?:\.\d+)?|manual|checkpoint)\s*$"
)
ISO_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")
SAFE_SESSION_RE = re.compile(r"^[A-Za-z0-9._-]{1,96}$")


# ----- switches and input ------------------------------------------------------


def hook_disabled() -> bool:
    """True when opted out via NEXUS_DISABLED_HOOKS or the minimal profile."""
    names = {n.strip() for n in os.environ.get("NEXUS_DISABLED_HOOKS", "").split(",")}
    if HOOK_NAME in names:
        return True
    return os.environ.get("NEXUS_HOOK_PROFILE", "").strip() == "minimal"


def threshold() -> int:
    """NEXUS_HANDOFF_THRESHOLD as an integer 1-100; anything else means 99."""
    raw = os.environ.get("NEXUS_HANDOFF_THRESHOLD", "").strip()
    if not re.fullmatch(r"\d{1,3}", raw):
        return DEFAULT_THRESHOLD
    value = int(raw)
    return value if 1 <= value <= 100 else DEFAULT_THRESHOLD


def read_payload(stream: Any) -> dict[str, Any] | None:
    """Parse the hook's JSON object from ``stream``; None when it is not one."""
    try:
        raw = stream.read(MAX_STDIN_BYTES + 1)
    except (OSError, ValueError):
        return None
    if not raw or len(raw) > MAX_STDIN_BYTES:
        return None
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


# ----- platform detection ------------------------------------------------------


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def _under_claude_hooks(script_dir: Path) -> bool:
    return script_dir.name == "hooks" and script_dir.parent.name == ".claude"


def _under_copilot_hooks(script_dir: Path) -> bool:
    return (
        script_dir.name == "nexus-hub-scripts"
        and (script_dir / "copilot-hook-compat.py").is_file()
    )


def detect_platform(payload: dict[str, Any], script_dir: Path | None = None) -> str | None:
    """Return the platform key this payload came from, or None for silence."""
    where = script_dir or _script_dir()
    event = str(payload.get("hook_event_name") or "")
    if "cursor_version" in payload:
        # Cursor also runs imported Claude hooks; only the native path speaks.
        return None if _under_claude_hooks(where) else "cursor"
    if "turn_id" in payload and "model" in payload:
        return "codex"
    if "session_title" in payload and "client_type" in payload:
        return None  # Kimi: no usage source
    if "timestamp" in payload and event in GEMINI_EVENTS:
        return None  # Gemini CLI: no usage source
    if ("timestamp" in payload and "permission_mode" in payload) or os.environ.get(
        "QWEN_PROJECT_DIR"
    ):
        return None  # Qwen Code: no usage source
    foreign = ("timestamp", "turn_id", "cursor_version", "session_title", "client_type")
    if not any(key in payload for key in foreign):
        if "scratchpad_dir" in payload:
            return "claude"
        if ("prompt_id" in payload or "permission_mode" in payload) and os.environ.get(
            "CLAUDE_CODE_ENTRYPOINT"
        ):
            return "claude"
    stamp = payload.get("timestamp")
    if (
        _under_copilot_hooks(where)
        and isinstance(stamp, str)
        and ISO_TIMESTAMP_RE.match(stamp)
        and event in COPILOT_EVENTS
        and not any(
            key in payload
            for key in ("permission_mode", "turn_id", "scratchpad_dir", "session_title")
        )
    ):
        return "copilot"
    return None


def session_key(platform: str, payload: dict[str, Any]) -> str:
    """A filename-safe session identifier; a hash when the raw id is unusual."""
    field = "conversation_id" if platform == "cursor" else "session_id"
    raw = str(payload.get(field) or payload.get("session_id") or "no-session")
    if SAFE_SESSION_RE.match(raw):
        return raw
    return hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:32]


# ----- probe, under the hook budget ---------------------------------------------


def _load_probe() -> Any:
    here = str(_script_dir())
    if here not in sys.path:
        sys.path.insert(0, here)
    import _usage_probe  # noqa: PLC0415 - imported only when a decision needs it

    return _usage_probe


def run_probe(platform: str, deadline: float) -> dict[str, Any] | None:
    """Call ``_usage_probe.probe`` in a worker; None when it overruns ``deadline``."""
    box: dict[str, Any] = {}

    def worker() -> None:
        try:
            box["result"] = _load_probe().probe(platform).to_dict()
        except Exception:  # noqa: BLE001 - a broken probe means "no reading"
            box["result"] = None

    thread = threading.Thread(target=worker, name="usage-guard-probe", daemon=True)
    thread.start()
    thread.join(max(0.0, deadline - time.monotonic()))
    if thread.is_alive():
        return None
    result = box.get("result")
    return result if isinstance(result, dict) else None


def _parse_iso(value: object) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _usable(result: dict[str, Any] | None, now: float) -> bool:
    if not result:
        return False
    status = result.get("status")
    if status == "stale":
        fetched = _parse_iso(result.get("fetched_at"))
        return fetched is not None and now - fetched <= STALE_LIMIT_SECONDS
    return status == "ok"


def classify_windows(
    result: dict[str, Any] | None, limit: int, now: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    """Split a usable reading into (crossing windows, highest first; cleared windows).

    A window is crossing at or over ``limit`` and cleared once it falls below the
    clear line, ``limit`` minus a small hysteresis band, so a percentage that
    wavers around the threshold cannot re-arm the warning on every reading.
    Returns None for an unusable reading (unavailable, unknown, or stale past
    30 minutes), which changes nothing.
    """
    if not result or not _usable(result, now):
        return None
    clear_line = limit - min(HYSTERESIS_POINTS, limit / 2)
    best: dict[str, dict[str, Any]] = {}
    for window in result.get("windows") or []:
        if not isinstance(window, dict):
            continue
        percent = window.get("percent")
        name = window.get("name")
        if not isinstance(name, str) or not name or isinstance(percent, bool):
            continue
        if not isinstance(percent, (int, float)) or percent != percent:
            continue
        resets = window.get("resets_at")
        entry = {
            "name": name,
            "percent": float(percent),
            "resets_at": resets if isinstance(resets, str) and resets else None,
        }
        if name not in best or entry["percent"] > best[name]["percent"]:
            best[name] = entry
    crossing = sorted(
        (w for w in best.values() if w["percent"] >= limit), key=lambda w: -w["percent"]
    )
    cleared = [w for w in best.values() if w["percent"] < clear_line]
    return crossing, cleared


def crossing_window(result: dict[str, Any] | None, limit: int, now: float) -> dict[str, Any] | None:
    """The highest window at or over ``limit``, from a usable reading only."""
    classified = classify_windows(result, limit, now)
    if not classified or not classified[0]:
        return None
    return classified[0][0]


# ----- directive and renderers --------------------------------------------------


def _format_percent(value: float) -> str:
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def directive(platform: str, window: dict[str, Any]) -> str:
    """The hand-off directive the session-handoff skill recognizes."""
    resets = window.get("resets_at")
    when = f" (resets {resets})" if isinstance(resets, str) and resets else ""
    percent = _format_percent(window["percent"])
    return (
        f"Usage limit: {DISPLAY_NAMES[platform]} {window['name']} usage is at "
        f"{percent}%{when}. Finish or safely stop the current step, then run the "
        "session-handoff procedure (/handoff): write .nexus-hub/handoff.md and "
        "print its paste-ready prompt. Start no new work. Record the trigger as "
        f"usage-limit {window['name']} {percent}. If another hook asks you to "
        "continue, write the handoff first."
    )


def render(platform: str, kind: str, event: str, message: str) -> dict[str, Any]:
    """The platform's documented output object for one event kind."""
    if platform == "cursor":
        if kind == "stop":
            return {"followup_message": message}
        return {"additional_context": message}
    if platform == "copilot" and kind == "stop":
        return {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "decision": "block",
                "reason": message,
            }
        }
    if kind == "stop":
        return {"decision": "block", "reason": message}
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": message}}


# ----- state ---------------------------------------------------------------------


def _nexus_home() -> Path:
    override = os.environ.get("NEXUS_HOME", "").strip()
    return Path(override) if override else Path.home() / ".nexus-hub"


def state_dir() -> Path:
    return _nexus_home() / "state" / "usage-guard"


class StateLock:
    """An O_EXCL lock file around one session's read-modify-write."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.held = False

    def __enter__(self) -> StateLock:
        end = time.monotonic() + LOCK_WAIT_SECONDS
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                self.held = True
                return self
            except FileExistsError:
                try:
                    if time.time() - self.path.stat().st_mtime > LOCK_STALE_SECONDS:
                        self.path.unlink()
                        continue
                except OSError:
                    pass
                if time.monotonic() >= end:
                    return self
                time.sleep(0.02)
            except OSError:
                return self

    def __exit__(self, *_exc: object) -> None:
        if self.held:
            try:
                self.path.unlink()
            except OSError:
                pass


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_state(path: Path, state: dict[str, Any]) -> bool:
    """Write the state atomically; False when it could not be persisted."""
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        try:
            tmp.unlink()
        except OSError:
            pass
        return False
    return True


def prune_states(directory: Path, now: float) -> None:
    """Drop session state older than a week. Best effort."""
    try:
        for entry in directory.glob("*.json"):
            try:
                if now - entry.stat().st_mtime > STATE_RETENTION_SECONDS:
                    entry.unlink()
            except OSError:
                continue
    except OSError:
        return


def _iso_now(now: float) -> str:
    return datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ----- handoff file --------------------------------------------------------------


def _handoff_roots(platform: str, payload: dict[str, Any]) -> list[Path]:
    candidates: list[str] = []
    env_key = {"claude": "CLAUDE_PROJECT_DIR", "cursor": "CURSOR_PROJECT_DIR"}.get(platform)
    if env_key and os.environ.get(env_key):
        candidates.append(os.environ[env_key])
    roots = payload.get("workspace_roots")
    if isinstance(roots, list):
        candidates.extend(str(r) for r in roots if isinstance(r, str) and r)
    if isinstance(payload.get("cwd"), str) and payload["cwd"]:
        candidates.append(payload["cwd"])
    seen: list[Path] = []
    for raw in candidates:
        start = Path(raw)
        for directory in (start, *list(start.parents)[:20]):
            if directory not in seen:
                seen.append(directory)
            if (directory / ".git").exists():
                break
    return seen


def usage_limit_handoff_time(
    platform: str, payload: dict[str, Any], extra_roots: tuple[Path, ...] = ()
) -> float | None:
    """The newest ``usage-limit`` handoff header time found, or None.

    Looks for ``.nexus-hub/handoff.md`` in ``extra_roots`` and in the payload's
    project directories, each walked up to its git root. Only a first line that
    matches the session-handoff header grammar with a ``usage-limit`` trigger
    counts; a checkpoint or manual handoff printed no paste-ready prompt.
    """
    newest: float | None = None
    roots = list(extra_roots) + _handoff_roots(platform, payload)
    for root in dict.fromkeys(roots):
        path = root / ".nexus-hub" / "handoff.md"
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                first = handle.readline(512)
        except OSError:
            continue
        match = HEADER_RE.match(first.rstrip("\r\n"))
        if not match or not match.group("trigger").startswith("usage-limit"):
            continue
        written = _parse_iso(match.group("ts"))
        if written is not None and (newest is None or written > newest):
            newest = written
    return newest


def handoff_written_since(platform: str, payload: dict[str, Any], since: float) -> bool:
    """True when a usage-limit handoff header is dated at or after ``since``."""
    written = usage_limit_handoff_time(platform, payload)
    return written is not None and written >= int(since)


def usage_limit_window(
    payload: dict[str, Any], script_dir: Path | None, deadline: float
) -> tuple[str, dict[str, Any]] | None:
    """(platform, highest crossing window) for this payload, or None.

    The completion gate calls this to confirm a usage-limit handoff is real: a
    recognized platform whose probe reports ``ok`` (or ``stale`` under 30
    minutes) with a tracked window at or over the threshold.
    """
    platform = detect_platform(payload, script_dir)
    if platform is None:
        return None
    window = crossing_window(run_probe(platform, deadline), threshold(), time.time())
    return (platform, window) if window else None


# ----- decision -------------------------------------------------------------------


def _prior_continuation(platform: str, payload: dict[str, Any]) -> bool:
    if platform == "cursor":
        count = payload.get("loop_count")
        return isinstance(count, (int, float)) and not isinstance(count, bool) and count > 0
    return payload.get("stop_hook_active") is True


def _same_period(entry: dict[str, Any], window: dict[str, Any]) -> bool:
    """False when the reset time moved enough to mean a new window period."""
    old = _parse_iso(entry.get("resets_at"))
    new = _parse_iso(window.get("resets_at"))
    if old is None or new is None:
        return True
    return abs(new - old) <= PERIOD_SHIFT_SECONDS


def _window_entries(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = state.get("windows") if state.get("schema") == STATE_SCHEMA else None
    if not isinstance(raw, dict):
        return {}
    return {k: dict(v) for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}


def decide(
    platform: str,
    kind: str,
    payload: dict[str, Any],
    crossing: list[dict[str, Any]],
    cleared: list[dict[str, Any]],
    state: dict[str, Any],
    now: float,
) -> tuple[str | None, dict[str, Any]]:
    """Return (message to emit or None, updated state).

    A window counts as announced only once a message about it was emitted. The
    platform's prior-continuation flag (``stop_hook_active``, Cursor
    ``loop_count``) is honored only when this guard's own continuation caused
    the turn it reports, because another Stop hook (the completion gate) sets
    it on every chained turn. Each window period gets at most one directive and
    one continuation; a window that falls below the clear line, or whose reset
    time moves to a new period, is forgotten so the next crossing warns again.
    """
    windows = _window_entries(state)
    for window in cleared:
        windows.pop(window["name"], None)
    for window in crossing:
        entry = windows.get(window["name"])
        if entry is not None and not _same_period(entry, window):
            del windows[window["name"]]
    stamp = _iso_now(now)
    chosen: dict[str, Any] | None = None
    if kind != "stop":
        for window in crossing:
            if window["name"] not in windows:
                chosen = window
                windows[window["name"]] = {
                    "resets_at": window["resets_at"],
                    "announced_at": stamp,
                    "continuation_sent": False,
                }
                break
    else:
        pending = [w for w in crossing if not windows.get(w["name"], {}).get("continuation_sent")]
        ours = state.get("last_stop_continued") is True
        if pending and not (ours and _prior_continuation(platform, payload)):
            for window in pending:
                entry = windows.get(window["name"])
                since = _parse_iso(entry.get("announced_at")) if entry else None
                if since is not None and handoff_written_since(platform, payload, since):
                    # A usage-limit handoff already answered this window.
                    entry["continuation_sent"] = True  # type: ignore[index]
                    continue
                chosen = window
                windows[window["name"]] = {
                    "resets_at": window["resets_at"],
                    "announced_at": entry.get("announced_at") if entry else stamp,
                    "continuation_sent": True,
                }
                break
    updated: dict[str, Any] = {
        "schema": STATE_SCHEMA,
        "windows": windows,
        "last_stop_continued": kind == "stop" and chosen is not None,
    }
    if windows:
        latest = max(windows, key=lambda n: str(windows[n].get("announced_at") or ""))
        updated.update(
            triggered_window=latest,
            triggered_at=windows[latest].get("announced_at"),
            continuation_sent=windows[latest].get("continuation_sent") is True,
        )
    return (directive(platform, chosen) if chosen else None), updated


def evaluate(payload: dict[str, Any], started: float, script_dir: Path | None = None) -> dict[str, Any] | None:
    """The whole decision for one payload: the output object, or None."""
    platform = detect_platform(payload, script_dir)
    if platform is None:
        return None
    event = str(payload.get("hook_event_name") or "")
    kind = EVENT_KINDS.get((platform, event))
    if kind is None:
        return None
    deadline = started + HOOK_BUDGET_SECONDS - BUDGET_MARGIN_SECONDS
    result = run_probe(platform, deadline)
    now = time.time()
    classified = classify_windows(result, threshold(), now)
    if classified is None or time.monotonic() >= deadline:
        return None
    crossing, cleared = classified
    directory = state_dir()
    path = directory / f"{platform}-{session_key(platform, payload)}.json"
    if not crossing and not path.exists():
        return None
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    with StateLock(path.with_name(path.name + ".lock")) as lock:
        if not lock.held:
            return None
        state = load_state(path)
        message, updated = decide(platform, kind, payload, crossing, cleared, state, now)
        if updated != state and not save_state(path, updated):
            return None
    if not state:
        prune_states(directory, now)
    if message is None:
        return None
    return render(platform, kind, event, message)


def main() -> int:
    """Hook entry point. Always exits 0."""
    started = time.monotonic()
    try:
        if hook_disabled():
            return 0
        payload = read_payload(sys.stdin)
        if payload is None:
            return 0
        output = evaluate(payload, started)
        if output is not None:
            sys.stdout.write(json.dumps(output) + "\n")
            sys.stdout.flush()
    except Exception:  # noqa: BLE001 - a guard must never break the host's turn
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
