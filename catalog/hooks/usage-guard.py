#!/usr/bin/env python3
"""Usage guard: one host-native decision per project, platform and usage period.

The home-owned ledger reserves delivery atomically and binds a genuine request
and submitted response. Only an explicit credits response permits paid work.
Repeated hooks and sessions reuse pending or answered decisions. Probe and
ledger writers share _usage_probe.ActivityLock with the reviewed adopter;
active transactions use cached reads and never write install state.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import sys
import tempfile
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
# A decision record dated further ahead than this is ignored: no honest writer
# stamps the future, and a committed far-future record would otherwise silence
# the turn-end reminder and satisfy the completion gate forever.
FUTURE_SKEW_SECONDS = 300
MAX_STDIN_BYTES = 8 * 1024 * 1024
SUBSCRIPTION_WINDOWS = frozenset({"five_hour", "weekly", "monthly"})
CREDIT_WINDOW = "extra_credits"
CREDIT_STATES = frozenset({"capped", "uncapped", "none", "exhausted"})
CREDIT_UNIT_RE = re.compile(r"^[A-Za-z]{1,12}$")
CREDIT_TIERS = (50, 75, 90)
# Spend between reminders, in the provider's credit unit, when no setting exists.
DEFAULT_REMINDER_STEPS = {"claude": 50.0, "cursor": 50.0, "codex": 500.0}
MAX_REMINDER_STEP = 1_000_000_000.0
DECISIONS = frozenset({"pending", "credits", "wait", "handoff"})
MAX_DECISION_BYTES = 4096
APPROVAL_SCHEMA = 1
APPROVAL_MAX_AGE_SECONDS = 32 * 24 * 3600

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
    if Path(__file__).is_file():
        return Path(__file__).resolve().parent
    # stdin has no __file__ directory. Prefer an explicit local sibling root.
    override = os.environ.get("NEXUS_USAGE_GUARD_DIR")
    candidates = ([Path(override)] if override else [
        _nexus_home() / "hooks", _nexus_home() / "src" / "catalog" / "hooks",
        Path.home() / ".claude" / "hooks", Path.home() / ".codex" / "hooks",
        Path.home() / ".cursor" / "hooks",
    ])
    for candidate in candidates:
        if not candidate.is_absolute():
            raise ValueError("NEXUS_USAGE_GUARD_DIR must be an absolute trusted hook directory")
        if (candidate / "_usage_probe.py").is_file():
            return candidate.resolve()
    raise FileNotFoundError("stdin execution needs NEXUS_USAGE_GUARD_DIR pointing to the hook directory")


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
        if not isinstance(name, str) or name not in SUBSCRIPTION_WINDOWS or isinstance(percent, bool):
            continue
        if not isinstance(percent, (int, float)) or math.isnan(percent):
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


def spend_info(result: dict[str, Any] | None, now: float) -> dict[str, Any] | None:
    """The ``extra_credits`` reading (state, percent, used, limit, unit), or None when unknown."""
    if not result or not _usable(result, now):
        return None
    for window in result.get("windows") or []:
        if not isinstance(window, dict) or window.get("name") != CREDIT_WINDOW:
            continue
        state, unit = window.get("state"), window.get("unit")
        if state not in CREDIT_STATES or not isinstance(unit, str) or not CREDIT_UNIT_RE.match(unit):
            return None
        return {
            "state": state,
            "percent": _finite(window.get("percent")),
            "used": _finite(window.get("used")),
            "limit": _finite(window.get("limit")),
            "unit": unit,
        }
    return None


def _finite(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and value >= 0 else None


def reminder_settings(platform: str) -> tuple[float, bool]:
    """(spend step between reminders, whether the step also applies under a cap).

    Read from ``~/.nexus-hub/config/credit-reminders-<platform>.json``
    with the shared ``credit-reminders.json`` as a legacy fallback
    (``{"providers": {"claude": {"step": 50, "when_capped": false}}}``), which
    the usage monitor extensions write from their settings; the step is in the
    provider's credit unit (USD for Claude Code and Cursor, credits for Codex).
    A step of 0 turns spend reminders off.
    """
    step, when_capped = DEFAULT_REMINDER_STEPS.get(platform, 0.0), False
    directory = _nexus_home() / "config"
    paths = (directory / f"credit-reminders-{platform}.json", directory / "credit-reminders.json")
    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as handle:
                raw = handle.read(MAX_DECISION_BYTES + 1)
            data = json.loads(raw) if len(raw) <= MAX_DECISION_BYTES else None
        except (OSError, ValueError):
            continue
        providers = data.get("providers") if isinstance(data, dict) else None
        entry = providers.get(platform) if isinstance(providers, dict) else None
        if isinstance(entry, dict):
            configured = _finite(entry.get("step"))
            if configured is not None and configured <= MAX_REMINDER_STEP:
                step = configured
            if isinstance(entry.get("when_capped"), bool):
                when_capped = entry["when_capped"]
            break
    return step, when_capped


def _step_applies(credit: dict[str, Any] | None, step: float, when_capped: bool) -> bool:
    if not credit or step <= 0 or credit["used"] is None:
        return False
    return credit["state"] == "uncapped" or (credit["state"] == "capped" and when_capped)


# ----- directive and renderers --------------------------------------------------


def _format_percent(value: float) -> str:
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


def _amount(value: float, unit: str) -> str:
    if unit == "USD":
        return f"${value:,.2f}"
    text = f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{text} {unit}" if unit.isupper() else f"{text} {unit}s"


STEP_SETTING = (
    "the step is the usage monitor's credit reminder setting "
    "(provider files in ~/.nexus-hub/config/; legacy credit-reminders.json is a fallback)"
)


def _tiers_text() -> str:
    return ", ".join(f"{t}%" for t in CREDIT_TIERS[:-1]) + f", and {CREDIT_TIERS[-1]}%"


def _spent(credit: dict[str, Any]) -> str:
    """How much of the allowance is spent, in the provider's own figures."""
    unit, used, cap, percent = credit["unit"], credit["used"], credit["limit"], credit["percent"]
    if used is not None and cap is not None:
        text = f"{_amount(used, unit)} of {_amount(cap, unit)}"
        return f"{text} ({_format_percent(percent)}%)" if percent is not None else text
    if percent is not None:
        return f"{_format_percent(percent)}% of the allowance"
    return f"{_amount(used, unit)} this period" if used is not None else "an unknown amount"


def _schedule(credit: dict[str, Any], step: float, when_capped: bool) -> str:
    """When Nexus-Hub will remind the user next, or why it cannot."""
    parts = []
    if credit["state"] == "capped" and credit["percent"] is not None:
        parts.append(f"at {_tiers_text()} of the allowance")
    if _step_applies(credit, step, when_capped):
        parts.append(f"every {_amount(step, credit['unit'])} spent ({STEP_SETTING})")
    if not parts:
        return (
            "Nexus-Hub cannot track this spend (no figure, or spend reminders set to 0), "
            "so tell the user it will not remind them"
        )
    return "Nexus-Hub reminds them " + " and ".join(parts)


def _spend_note(credit: dict[str, Any] | None, when: str, step: float, when_capped: bool) -> str:
    if credit is None:
        return (
            "Nexus-Hub cannot read pay-per-use credits here, so it cannot tell whether "
            "continuing will work and cannot remind the user as credits run down; say so. "
        )
    if credit["state"] == "none":
        return (
            "This account shows no pay-per-use credits (disabled, or a zero allowance), "
            f"so continuing will fail until the window resets{when} unless the user "
            "first enables credits in the provider's billing settings; offer that, "
            "waiting for the reset, or the handoff. "
        )
    if credit["state"] == "exhausted":
        return (
            f"The pay-per-use credit allowance is already used up ({_spent(credit)}), "
            "so continuing will fail unless the user raises the limit in the "
            "provider's billing settings; offer that, waiting for the reset, or the "
            "handoff. "
        )
    if credit["state"] == "uncapped":
        spent = f"pay-per-use credits have no spending cap ({_spent(credit)})"
    else:
        spent = f"pay-per-use credits used so far: {_spent(credit)}"
    return (
        f"Tell the user {spent}; if they continue, "
        f"{_schedule(credit, step, when_capped)}. "
    )


def directive(platform: str, window: dict[str, Any], credit: dict[str, Any] | None = None,
              step: float = 0.0, when_capped: bool = False) -> str:
    """Usage facts for the host-native decision delivery directive."""
    reset = window.get("resets_at") or "unknown (do not guess)"
    percent = _format_percent(window["percent"])
    return (f"Usage limit: {DISPLAY_NAMES[platform]} {window['name']} usage is at "
            f"{percent}% (resets {reset}). Finish or safely stop the current step. "
            + _spend_note(credit, f" (resets {reset})", step, when_capped))


def spend_directive(platform: str, credit: dict[str, Any], step: float = 0.0,
                    when_capped: bool = False) -> str:
    """Report spending once per reminder without replacing the recorded answer."""
    if credit["state"] == "exhausted":
        return (f"Usage credits: {DISPLAY_NAMES[platform]} pay-per-use credits are used up "
                f"({_spent(credit)}); further requests will fail. Stop requests. To raise the limit "
                "and resume requires a genuine new user instruction; do not infer approval.")
    return (f"Usage credits: {DISPLAY_NAMES[platform]} pay-per-use credits used so far: "
            f"{_spent(credit)}; {_schedule(credit, step, when_capped)}. "
            "Your existing choice remains recorded; do not ask a duplicate question.")


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
            # Best-effort cleanup of a temp file that may never have been
            # created; the caller already learns of the failure via False.
            pass
        return False
    return True


def _iso_now(now: float) -> str:
    return datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ----- project records -----------------------------------------------------------


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
    """When the user's newest recorded usage answer is ``handoff``, its time, else None.

    The session-handoff skill prints the handoff as a prompt in the chat and
    writes no file unless the user asks for one, so the ``handoff`` answer in
    ``.nexus-hub/usage-decision.json`` (see ``usage_decision``) is the evidence.
    A ``.nexus-hub/handoff.md`` file, whatever its header, is never read.
    """
    answer = usage_decision(platform, payload, extra_roots)
    return answer[1] if answer is not None and answer[0] == "handoff" else None


def usage_decision(
    platform: str, payload: dict[str, Any], extra_roots: tuple[Path, ...] = ()
) -> tuple[str, float] | None:
    """The newest (decision, recorded time) from ``.nexus-hub/usage-decision.json``.

    Looked for in ``extra_roots`` and in the payload's project directories, each
    walked up to its git root. A record naming another platform, an unknown
    decision, or a time beyond the clock-skew allowance is ignored.
    """
    newest: tuple[str, float] | None = None
    latest_allowed = time.time() + FUTURE_SKEW_SECONDS
    roots = list(extra_roots) + _handoff_roots(platform, payload)
    for root in dict.fromkeys(roots):
        path = root / ".nexus-hub" / "usage-decision.json"
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                raw = handle.read(MAX_DECISION_BYTES + 1)
        except OSError:
            continue
        if len(raw) > MAX_DECISION_BYTES:
            continue
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(data, dict):
            continue
        decision = data.get("decision")
        if not isinstance(decision, str) or decision not in DECISIONS:
            continue
        owner = data.get("platform")
        if owner is not None and owner != platform:
            continue
        recorded = _parse_iso(data.get("recorded_at"))
        if recorded is None or recorded > latest_allowed:
            continue
        if newest is None or recorded > newest[1]:
            newest = (decision, recorded)
    return newest


def usage_limit_stop_time(
    platform: str, payload: dict[str, Any], extra_roots: tuple[Path, ...] = ()
) -> float | None:
    """Newest evidence that a turn end is a usage-limit stop: the user's recorded
    answer to the usage question is pending, wait, or handoff."""
    answer = usage_decision(platform, payload, extra_roots)
    if answer is not None and answer[0] in ("pending", "wait", "handoff"):
        return answer[1]
    return None


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


def _same_period(entry: dict[str, Any], window: dict[str, Any]) -> bool:
    """False when the reset time moved enough to mean a new window period."""
    old = _parse_iso(entry.get("resets_at"))
    new = _parse_iso(window.get("resets_at"))
    if old is None or new is None:
        return True
    return abs(new - old) <= PERIOD_SHIFT_SECONDS


def approval_path(platform: str) -> Path:
    return state_dir() / f"{platform}.credits.json"


def _approved_windows(approval: dict[str, Any]) -> dict[str, Any]:
    raw = approval.get("windows") if approval.get("schema") == APPROVAL_SCHEMA else None
    return dict(raw) if isinstance(raw, dict) else {}


def _approval_active(approval: dict[str, Any], crossing: list[dict[str, Any]], now: float) -> bool:
    """True while a credits approval covers a crossing window in the same period."""
    approved = _approved_windows(approval)
    when = _parse_iso(approval.get("approved_at"))
    if not approved or when is None or now - when > APPROVAL_MAX_AGE_SECONDS:
        return False
    return any(
        w["name"] in approved and _same_period({"resets_at": approved[w["name"]]}, w)
        for w in crossing
    )


def _approval_tiers(approval: dict[str, Any]) -> set[int]:
    raw = approval.get("credit_tiers")
    if not isinstance(raw, list):
        return set()
    return {t for t in raw if isinstance(t, int) and not isinstance(t, bool) and t in CREDIT_TIERS}


def _approval_bucket(approval: dict[str, Any]) -> int | None:
    raw = approval.get("amount_bucket")
    return raw if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0 else None


def _record_approval(
    approval: dict[str, Any],
    crossing: list[dict[str, Any]],
    credit: dict[str, Any] | None,
    reminders: tuple[float, bool],
    stamp: str,
    now: float,
) -> dict[str, Any]:
    """A credits approval for the crossing windows; what the user was just told counts as reminded."""
    active = _approval_active(approval, crossing, now)
    windows = _approved_windows(approval) if active else {}
    windows.update({w["name"]: w["resets_at"] for w in crossing})
    tiers = _approval_tiers(approval) if active else set()
    percent = credit["percent"] if credit else None
    if percent is not None:
        tiers.update(t for t in CREDIT_TIERS if t <= percent)
    step, when_capped = reminders
    bucket = int(credit["used"] // step) if _step_applies(credit, step, when_capped) else None
    return {
        "schema": APPROVAL_SCHEMA,
        "approved_at": stamp,
        "windows": windows,
        "credit_tiers": sorted(tiers),
        "amount_bucket": bucket,
        "exhausted_notified": bool(credit and credit["state"] == "exhausted"),
    }


def _spend_reminder_due(
    approval: dict[str, Any], credit: dict[str, Any] | None, reminders: tuple[float, bool]
) -> bool:
    """Update the approval's reminder marks in place; True when a reminder is due now."""
    if credit is None:
        return False
    if credit["state"] == "exhausted":
        due = approval.get("exhausted_notified") is not True
        approval["exhausted_notified"] = True
        return due
    approval["exhausted_notified"] = False
    due = False
    percent = credit["percent"]
    if credit["state"] == "capped" and percent is not None:
        # A figure below an asked tier means the allowance reset.
        tiers = {t for t in _approval_tiers(approval) if t <= percent}
        reached = [t for t in CREDIT_TIERS if t <= percent and t not in tiers]
        due = bool(reached)
        approval["credit_tiers"] = sorted(tiers | set(reached))
    step, when_capped = reminders
    if _step_applies(credit, step, when_capped):
        current = int(credit["used"] // step)
        marked = _approval_bucket(approval)
        if marked is not None and current > marked:
            due = True
        approval["amount_bucket"] = current
    return due


DECISION_SCHEMA = 3
PLATFORM_ALIASES = {"claude-code": "claude", "claude_code": "claude", "openai-codex": "codex",
                    "github-copilot": "copilot"}


def canonical_platform(platform: str) -> str:
    """Use the same provider slug at hook and command boundaries."""
    return PLATFORM_ALIASES.get(platform.lower(), platform.lower())


def resolve_project(project: Path) -> Path:
    """Keep non-git paths intact; use the nearest git root for subdirectories."""
    project = project.resolve()
    return next((p for p in (project, *project.parents) if (p / ".git").exists()), project)


def decision_path(platform: str, project: Path) -> Path:
    """A home-owned ledger; repository JSON cannot grant spending authority."""
    return _identity_path(canonical_platform(platform), resolve_project(project))


def _identity_path(platform: str, project: Path) -> Path:
    identity = str(project.resolve()) + "\0" + platform
    key = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return state_dir() / "decisions" / (key + ".json")


def _project_root(platform: str, payload: dict[str, Any]) -> Path | None:
    roots = _handoff_roots(platform, payload)
    if not roots:
        return None
    return resolve_project(roots[0])


def _warning_reference_valid(value: object) -> bool:
    return (isinstance(value, str) and 1 <= len(value) <= 512 and value == value.strip()
            and all(ord(char) >= 32 and ord(char) != 127 for char in value))


def pending_decision(platform: str, payload: dict[str, Any],
                     extra_roots: tuple[Path, ...] = (), *, decision_id: str = "") -> dict[str, Any] | None:
    """Read the shared decision without changing state or probing usage."""
    platform = canonical_platform(platform)
    roots = list(extra_roots) if extra_roots else _handoff_roots(platform, payload)
    if not roots:
        return None
    raw_project, project = roots[0].resolve(), resolve_project(roots[0])
    providers = [platform, *(alias for alias, target in PLATFORM_ALIASES.items() if target == platform)]
    paths = dict.fromkeys(_identity_path(provider, root) for root in (project, raw_project) for provider in providers)
    data = next((entry for path in paths if (entry := load_state(path))
                 and (not decision_id or entry.get("id") == decision_id)), {})
    if (data.get("schema") != DECISION_SCHEMA or not isinstance(data.get("platform"), str)
            or canonical_platform(data["platform"]) != platform
            or not isinstance(data.get("project"), str) or not Path(data["project"]).is_absolute()
            or resolve_project(Path(data["project"])) != project or not isinstance(data.get("id"), str)):
        return None
    created = _parse_iso(data.get("created_at"))
    recorded = _parse_iso(data.get("recorded_at"))
    delivery = data.get("delivery")
    windows = data.get("windows")
    decision = data.get("decision")
    if (not re.fullmatch(r"[0-9a-f]{32}", data["id"]) or not isinstance(decision, str) or decision not in DECISIONS
            or created is None or recorded is None or recorded < created
            or recorded > time.time() + FUTURE_SKEW_SECONDS
            or not isinstance(windows, dict)
            or (not windows and data.get("origin") != "host-warning")
            or any(name not in SUBSCRIPTION_WINDOWS for name in windows)
            or not isinstance(delivery, dict)
            or delivery.get("state") not in ("offered", "claimed", "delivered", "uncertain")):
        return None
    if data.get("origin") == "host-warning":
        if (not _warning_reference_valid(data.get("warning_reference")) or windows
                or data.get("confirmed_usage") != [] or data.get("credit") is not None):
            return None
    else:
        facts = data.get("confirmed_usage")
        if (not isinstance(facts, list) or not facts or any(
                not isinstance(item, dict) or item.get("name") not in windows
                or isinstance(item.get("percent"), bool)
                or not isinstance(item.get("percent"), (int, float))
                or not math.isfinite(item["percent"]) for item in facts)):
            return None
    cleared = data.get("cleared_windows", [])
    if not isinstance(cleared, list) or any(name not in windows for name in cleared):
        return None
    if delivery["state"] != "offered":
        claim, tool = delivery.get("claim_id"), delivery.get("tool")
        if (not isinstance(claim, str) or not re.fullmatch(r"[0-9a-f]{32}", claim)
                or not isinstance(tool, str) or not 1 <= len(tool) <= 128):
            return None
    request = delivery.get("request_id")
    if delivery["state"] == "delivered" and (not isinstance(request, str) or not 1 <= len(request) <= 256):
        return None
    if decision != "pending":
        response = data.get("response_id")
        if (delivery["state"] != "delivered" or not isinstance(response, str)
                or not 1 <= len(response) <= 256):
            return None
    return data


def _migrate_identity(platform: str, project: Path, data: dict[str, Any]) -> None:
    """Caller holds ActivityLock; preserve the original facts while moving the ledger key."""
    source = _identity_path(data["platform"], Path(data["project"]))
    target = decision_path(platform, project)
    if source != target and source.is_file():
        current = load_state(target)
        if current and current.get("id") != data["id"]:
            raise ValueError("legacy decision conflicts with the current project decision; use recovery status")
        if current:
            return  # The canonical ledger is authoritative, including an already saved answer.
        os.replace(source, target)


def _decision_active(data: dict[str, Any], crossing: list[dict[str, Any]], now: float) -> bool:
    if data.get("decision") == "pending":
        return True  # Recover the same unanswered question, even after a reset.
    if data.get("origin") == "host-warning":
        return False  # A warning answer never grants a new tracked usage period.
    if data.get("decision") == "credits":
        recorded = _parse_iso(data.get("recorded_at"))
        if recorded is None or now - recorded > APPROVAL_MAX_AGE_SECONDS:
            return False
    windows = data.get("windows")
    if not isinstance(windows, dict) or not windows or data.get("cleared_windows"):
        return False
    for window in crossing:
        if window["name"] in windows and not _same_period(
                {"resets_at": windows[window["name"]]}, window):
            return False  # An explicit same-window period change outranks future fallback.
    return any(w["name"] in windows and _same_period({"resets_at": windows[w["name"]]}, w)
               for w in crossing) or any(_parse_iso(reset) is None or _parse_iso(reset) > now
                                        for reset in windows.values())


def archive_answer(path: Path, data: dict[str, Any]) -> bool:
    """Keep immutable per-ID answer facts before rotating the current ledger.

    Existing history must match exactly. Partial or conflicting history fails
    closed and leaves the current answer in place; it is never overwritten.
    Caller holds ActivityLock. Mutable reminder/clear observations are omitted.
    """
    if data.get("decision") not in ("wait", "handoff", "credits"):
        return False
    fields = ("schema", "id", "project", "platform", "origin", "warning_reference",
              "created_at", "recorded_at", "decision", "windows", "confirmed_usage",
              "credit", "delivery", "response_id")
    immutable = {name: data[name] for name in fields if name in data}
    raw = (json.dumps(immutable, sort_keys=True) + "\n").encode("utf-8")
    history = path.parent / "history" / (data["id"] + ".json")
    try:
        history.parent.mkdir(parents=True, exist_ok=True)
        try:
            with history.open("xb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            return history.read_bytes() == raw
    except OSError:
        return False
    return True


def _archive_failure_notice(path: Path, data: dict[str, Any]) -> str | None:
    """A stop notice, never a new question or native lifecycle verdict."""
    if data.get("archive_failure_notified") is True:
        return None
    data["archive_failure_notified"] = True
    if not save_state(path, data):
        return None  # Never emit an unrecorded notice that could loop at Stop.
    prior = "credits" if data.get("decision") == "credits" else "usage"
    return (f"Usage state: the prior {prior} episode expired. Its answer history could not "
            "be preserved, so no new spending authority exists. Stop new work and recover "
            "the state before continuing; do not ask another question or reuse the prior answer.")


def decision_transition(platform: str, project: Path, decision_id: str, action: str,
                        *, tool: str = "", claim_id: str = "", request_id: str = "",
                        response_id: str = "", answer: str = "") -> dict[str, Any]:
    """Atomically claim delivery, bind the real request, or persist one user answer.

    IDs record a host interaction, not a new approval system. The caller must
    copy genuine IDs and the submitted answer from the host, never invent them.
    Hook answer capture does not require this legacy agent-driven protocol.
    """
    import secrets
    platform = canonical_platform(platform)
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", platform):
        raise ValueError("safe platform slug required")
    requested_project, project = project.resolve(), resolve_project(project)
    probe = _load_probe()
    if probe.adoption_active():
        raise ValueError("runtime adoption active; no decision writes")
    with probe.ActivityLock() as activity:
        if not activity.held:
            raise ValueError("usage activity busy; no decision writes")
        path = decision_path(platform, project)
        data = pending_decision(platform, {}, (requested_project,), decision_id=decision_id)
        if data is None or data["id"] != decision_id:
            stored = load_state(path)
            if not stored:
                stored = next((item for candidate in path.parent.glob("*.json")
                               if (item := load_state(candidate)).get("id") == decision_id), {})
            raise ValueError(f"stale or unknown decision; stored platform={stored.get('platform', platform)} "
                             f"project={stored.get('project', str(project))} decision_id={stored.get('id', 'none')}")
        if data.get("decision") != "pending":
            raise ValueError("decision already answered")
        _migrate_identity(platform, project, data)
        if action != "answer" and _deferred_answer(data) is not None:
            _consume_answer(platform, project, data)
            raise ValueError("decision already answered from a captured response")
        delivery = dict(data.get("delivery") or {})
        if action == "claim":
            if delivery.get("state") != "offered":
                return {"claimed": False, "decision": data}
            if not tool or len(tool) > 128:
                raise ValueError("actual exposed interaction tool or text required")
            delivery = {"state": "claimed", "tool": tool,
                        "claim_id": secrets.token_hex(16), "claimed_at": _iso_now(time.time())}
        else:
            if not claim_id or claim_id != delivery.get("claim_id"):
                raise ValueError("delivery claim mismatch")
            if action == "delivered":
                if delivery.get("state") not in ("claimed", "uncertain") or not request_id or len(request_id) > 256:
                    raise ValueError("real request ID required exactly once")
                delivery.update(state="delivered", request_id=request_id)
            elif action == "uncertain":
                if delivery.get("state") != "claimed":
                    raise ValueError("delivery already bound")
                delivery["state"] = "uncertain"
            elif action == "answer":
                if (delivery.get("state") != "delivered" or not request_id
                        or request_id != delivery.get("request_id") or not response_id
                        or len(response_id) > 256 or answer not in ("wait", "handoff", "credits")):
                    raise ValueError("matching genuine request, response and submitted choice required")
                receipt = _submitted_receipt(data, answer, "legacy-answer", delivery["tool"], response_id)
                receipt.update(delivery=delivery, response_id=response_id)
                _defer_answer(data, receipt)
                result = _consume_answer(platform, project, data)
                if result["decision"]["decision"] != answer:
                    raise ValueError("decision already answered: " + result["decision"]["decision"])
                return {"claimed": False, **result}
            else:
                raise ValueError("unknown decision action")
        data["delivery"] = delivery
        if not save_state(path, data):
            raise OSError("decision write failed")
        return {"claimed": action == "claim", "decision": data}


def decision_directive(data: dict[str, Any], message: str) -> str:
    """Tell the agent the executable delivery protocol, never assume host APIs."""
    marker = "[usage-decision:" + data["id"] + "]"
    return (message + " Decision ID " + data["id"] + ". Platform " + data["platform"] +
            "; project " + data["project"] + ". Ask once through an exposed native question tool "
            "(functions.request_user_input_async when available). Include " + marker +
            " in the question text and use usage_" + data["id"] + " as its question ID when supported. "
            "The post-tool hook saves the submitted answer; no agent claim or spending CLI is needed. "
            "If the tool or a legacy claim cannot succeed, ask one concise plain text question. Offer exactly: "
            "Wait for reset (Recommended), Hand off, Continue on credits, in that order. "
            "Never preselect credits. Explain the reported reset time, spending and consequence "
            "in the options. A typed reply credits, wait, handoff, or /usage credits|wait|handoff is "
            "also captured automatically. From the project directory above, user-run recovery: "
            "nexus-hub usage decide --platform " + data["platform"] +
            " --decision-id " + data["id"] + " --answer wait|handoff|credits. Pending means stop "
            "new work and await the existing response; wait stops until reset; handoff prints "
            "the session-handoff prompt and stops; only credits authorizes continued work.")


def _context_session(payload: dict[str, Any]) -> str | None:
    for key in ("session_id", "conversation_id"):
        value = payload.get(key)
        if isinstance(value, str) and SAFE_SESSION_RE.fullmatch(value):
            return value
    return None


def _decision_status(path: Path, data: dict[str, Any], payload: dict[str, Any]) -> str | None:
    """Share a stopping state once per session; never reserve another question."""
    session = _context_session(payload)
    notices = data.get("status_sessions", {})
    notices = {key: value for key, value in notices.items()
               if isinstance(key, str) and SAFE_SESSION_RE.fullmatch(key)
               and isinstance(value, str) and value in ("pending", "wait", "handoff")} if isinstance(notices, dict) else {}
    notices = dict(list(notices.items())[-128:])
    decision = data["decision"]
    if session is not None and notices.get(session) == decision:
        return None
    if session is not None:
        if session not in notices and len(notices) >= 128:
            del notices[next(iter(notices))]
        notices[session] = decision
        data["status_sessions"] = notices
        save_state(path, data)  # Failed notice persistence must never suppress the stopping context.
    action = {"pending": "Stop new work and await the existing response.",
              "wait": "Stop work until the reported reset.",
              "handoff": "Print the session-handoff prompt and stop."}[decision]
    return (f"Usage decision {data['id']}: {decision}; delivery {data['delivery']['state']}. "
            + action + " Reuse this decision. Do not claim or ask another question; this status grants no spending authority.")


def _answer_choice(value: Any) -> str | None:
    """Accept an explicit choice only, never a mention inside arbitrary prose."""
    if isinstance(value, dict):
        value = value.get("answers", value.get("optionIds"))
    if isinstance(value, list):
        value = value[0] if len(value) == 1 else None
    if not isinstance(value, str):
        return None
    return {"credits": "credits", "continue on credits": "credits", "wait": "wait",
            "wait for reset": "wait", "wait for reset (recommended)": "wait",
            "handoff": "handoff", "hand off": "handoff"}.get(value.strip().lower())


def _submitted_answer(data: dict[str, Any], payload: dict[str, Any]) -> str | None:
    event = payload.get("hook_event_name")
    if event in ("UserPromptSubmit", "beforeSubmitPrompt"):
        prompt = payload.get("prompt")
        if isinstance(prompt, str) and prompt.strip().lower().startswith("/usage "):
            prompt = prompt.strip()[7:]
        return _answer_choice(prompt)
    if event not in ("PostToolUse", "postToolUse"):
        return None
    tool = str(payload.get("tool_name", "")).removeprefix("functions.")
    if tool not in ("AskUserQuestion", "AskQuestion", "ask_question", "cursor/ask_question", "request_user_input",
                    "request_user_input_async"):
        return None
    tool_input = payload.get("tool_input")
    response = payload.get("tool_response", payload.get("tool_output"))
    try:
        tool_input = json.loads(tool_input) if isinstance(tool_input, str) else tool_input
        response = json.loads(response) if isinstance(response, str) else response
    except (ValueError, TypeError):
        return None
    if not isinstance(tool_input, dict) or not isinstance(response, dict):
        return None
    outcome = response.get("outcome")
    if isinstance(outcome, dict):
        if outcome.get("outcome") != "answered":
            return None
        response = outcome
    elif outcome is not None and outcome != "answered":
        return None
    if (any(response.get(key) for key in ("cancelled", "canceled", "isError", "is_error", "error"))
            or response.get("status") in ("cancelled", "canceled", "error", "timeout")
            or payload.get("is_error") is True):
        return None
    questions = tool_input.get("questions")
    answers = response.get("answers")
    if not isinstance(questions, list):
        return None
    found: list[str] = []
    for question in questions:
        if not isinstance(question, dict):
            continue
        keys = [question.get(key) for key in ("id", "header", "question", "title", "prompt")]
        if not any(isinstance(key, str) and (
                "[usage-decision:" + data["id"] + "]" in key or key == "usage_" + data["id"])
                   for key in keys):
            continue
        if isinstance(answers, dict):
            values = [answers[key] for key in keys if isinstance(key, str) and key in answers]
        elif isinstance(answers, list):
            values = [item for item in answers if isinstance(item, dict)
                      and item.get("questionId") in keys]
        else:
            continue
        for value in values:
            if isinstance(value, dict) and ("selectedOptionIds" in value or "optionIds" in value):
                selected = value.get("selectedOptionIds", value.get("optionIds"))
                if not isinstance(selected, list) or len(selected) != 1:
                    continue
                options = question.get("options")
                labels = [option.get("label") for option in options
                          if isinstance(option, dict) and option.get("id") == selected[0]] if isinstance(options, list) else []
                value = labels[0] if len(labels) == 1 else (selected[0] if not options else None)
            answer = _answer_choice(value)
            if answer is not None:
                found.append(answer)
    return found[0] if found and len(set(found)) == 1 else None


def _answer_receipt_path(ident: str, *, create: bool = False) -> Path:
    """Private capture inbox outside the install tree and its adoption baseline."""
    home = _nexus_home().resolve()
    key = hashlib.sha256(str(home).encode()).hexdigest()[:16]
    directory = home.parent / (".nexus-usage-answers-" + key)
    if create:
        directory.mkdir(mode=0o700, exist_ok=True)
    if directory.exists() or directory.is_symlink():
        info = directory.lstat()
        if (not stat.S_ISDIR(info.st_mode) or directory.is_symlink()
                or (hasattr(os, "getuid") and (info.st_uid != os.getuid() or info.st_mode & 0o077))):
            raise OSError("usage answer inbox must be a private user-owned directory")
    return directory / (ident + ".json")


def _deferred_answer(data: dict[str, Any]) -> dict[str, Any] | None:
    receipt = load_state(_answer_receipt_path(data["id"]))
    stamp = _parse_iso(receipt.get("submitted_at"))
    created = _parse_iso(data.get("created_at"))
    if (any(receipt.get(key) != data[key] for key in ("id", "platform", "project"))
            or receipt.get("answer") not in ("credits", "wait", "handoff")
            or stamp is None or created is None or not created <= stamp <= time.time() + FUTURE_SKEW_SECONDS
            or receipt.get("source") not in ("PostToolUse", "postToolUse", "UserPromptSubmit", "beforeSubmitPrompt",
                                             "user-cli", "legacy-answer")
            or any(not isinstance(receipt.get(key), str) or len(receipt[key]) > 256
                   for key in ("tool", "reference"))):
        return None
    if receipt["source"] == "legacy-answer":
        delivery = receipt.get("delivery")
        response = receipt.get("response_id")
        if (not isinstance(delivery, dict) or delivery != data.get("delivery")
                or delivery.get("state") != "delivered" or not isinstance(response, str)
                or not 1 <= len(response) <= 256):
            return None
    return receipt


def _defer_answer(data: dict[str, Any], receipt: dict[str, Any]) -> None:
    path = _answer_receipt_path(data["id"], create=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".answer-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(receipt, handle)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            if os.name == "nt":
                os.rename(temporary, path)  # Windows rename refuses an existing destination.
            else:
                os.link(temporary, path)  # POSIX rename would overwrite; a link publishes exclusively.
        except FileExistsError:
            if _deferred_answer(data) is None:
                raise OSError("usage answer receipt is unreadable; use recovery") from None
    finally:
        Path(temporary).unlink(missing_ok=True)


def _submitted_receipt(data: dict[str, Any], answer: str, source: str, tool: str,
                       reference: str = "") -> dict[str, Any]:
    return {**{key: data[key] for key in ("id", "platform", "project")}, "answer": answer,
            "submitted_at": _iso_now(time.time()), "source": source, "tool": tool[:128], "reference": reference[:256]}


def _consume_answer(platform: str, project: Path, data: dict[str, Any]) -> dict[str, Any]:
    """Caller holds ActivityLock; every writer commits the first published receipt."""
    receipt = _deferred_answer(data)
    if receipt is None:
        raise ValueError("submitted answer receipt unavailable")
    result = _save_submitted_answer(platform, project, data, receipt["answer"], receipt["source"],
                                    receipt["tool"], receipt["reference"], stamp=receipt["submitted_at"],
                                    delivery=receipt.get("delivery"), response_id=receipt.get("response_id"))
    try:
        _answer_receipt_path(data["id"]).unlink(missing_ok=True)
    except OSError:
        pass  # Answered ledgers reject replay even if receipt cleanup fails.
    return result


def capture_answer(platform: str, project: Path, payload: dict[str, Any]) -> bool:
    """Persist host-submitted answers before probing, including offline recovery."""
    candidate = pending_decision(platform, payload)
    if candidate is None or candidate["decision"] != "pending":
        return False
    receipt = _deferred_answer(candidate)
    answer = _submitted_answer(candidate, payload)
    if receipt is None and answer is None:
        return False
    if receipt is None:
        receipt = _submitted_receipt(candidate, answer, str(payload.get("hook_event_name")),
                                      str(payload.get("tool_name", "text")),
                                      str(payload.get("tool_use_id", payload.get("session_id", ""))))
        _defer_answer(candidate, receipt)  # Reserve before taking the shared lock, including on the fast path.
    probe = _load_probe()
    with probe.ActivityLock() as activity:
        if not activity.held:
            return True  # Replay this genuine answer on a later event, without asking again.
        data = pending_decision(platform, payload)
        if data is None or data["id"] != candidate["id"] or data["decision"] != "pending":
            return False
        _consume_answer(platform, project, data)
        return True


def _save_submitted_answer(platform: str, project: Path, data: dict[str, Any], answer: str,
                           source: str, tool: str, reference: str = "", *, stamp: str | None = None,
                           delivery: dict[str, Any] | None = None, response_id: str | None = None) -> dict[str, Any]:
    """Caller holds ActivityLock. Receipt IDs are local audit keys, not invented host IDs."""
    import secrets
    stamp = stamp or _iso_now(time.time())
    receipt = source + ":" + hashlib.sha256((data["id"] + "\0" + reference + "\0" + answer).encode()).hexdigest()
    data.update(decision=answer, recorded_at=stamp, response_id=response_id or receipt)
    data["delivery"] = delivery or {"state": "delivered", "tool": tool, "source": source,
                                   "claim_id": secrets.token_hex(16), "request_id": receipt}
    if answer == "credits":
        data["approval"] = dict(data.get("approval") or {}, approved_at=stamp)
    _migrate_identity(platform, project, data)
    if not save_state(decision_path(platform, project), data):
        raise OSError("decision write failed")
    return {"decision": data}


def _emit_offer(path: Path, data: dict[str, Any], platform: str, kind: str, event: str) -> dict[str, Any] | None:
    """Commit the delivery mark before output so repeated hooks never loop."""
    if data.get("instruction_sent") or data.get("stop_blocked") or data["delivery"]["state"] != "offered":
        return None
    data["instruction_sent"] = True
    if kind == "stop":
        data["stop_blocked"] = True
    return render(platform, kind, event, _offered_directive(data)) if save_state(path, data) else None


def _offered_directive(data: dict[str, Any]) -> str:
    """Recover an undelivered offer from its original facts, never a new question."""
    if data.get("origin") == "host-warning":
        facts = (f"Usage limit: a host warning was reported for {data['platform']}. "
                 "Usage percentage, reset time and cost are unknown; do not invent them. "
                 f"Warning reference: {data['warning_reference']}. ")
    else:
        facts = directive(data["platform"], data["confirmed_usage"][0], data.get("credit"),
                          *reminder_settings(data["platform"]))
    return decision_directive(data, facts)


def _evaluate_shared(payload: dict[str, Any], started: float,
                     script_dir: Path | None = None) -> dict[str, Any] | None:
    platform = detect_platform(payload, script_dir)
    if platform is None:
        return None
    event = str(payload.get("hook_event_name") or "")
    kind = EVENT_KINDS.get((platform, event))
    project = _project_root(platform, payload)
    if project is None or (kind is None and event not in ("beforeSubmitPrompt", "UserPromptSubmit")):
        return None
    if kind == "stop" and (payload.get("stop_hook_active") is True
                           or (platform == "cursor" and isinstance(payload.get("loop_count"), (int, float))
                               and payload["loop_count"] > 0)):
        return None
    probe = _load_probe()
    if capture_answer(platform, project, payload) or kind is None:
        return None
    if probe.adoption_active():
        return None
    deadline = started + HOOK_BUDGET_SECONDS - BUDGET_MARGIN_SECONDS
    result = run_probe(platform, deadline)
    now = time.time()
    classified = classify_windows(result, threshold(), now)
    if classified is None or time.monotonic() >= deadline:
        return None
    crossing, cleared = classified
    credit = spend_info(result, now)
    with probe.ActivityLock() as activity:
        if not activity.held:
            return None
        path = decision_path(platform, project)
        data = pending_decision(platform, payload)
        if data is not None:
            _migrate_identity(platform, project, data)
        if data is not None and data.get("decision") != "pending":
            marked = set(data.get("cleared_windows") or [])
            observed = {w["name"] for w in cleared if w["name"] in data["windows"]}
            if observed - marked:
                data["cleared_windows"] = sorted(marked | observed)
                if not save_state(path, data):
                    return None
        if not crossing:
            return None
        if data is not None and _decision_active(data, crossing, now):
            if data.get("decision") != "credits":
                if data["decision"] == "pending" and data["delivery"]["state"] == "offered":
                    offered = _emit_offer(path, data, platform, kind, event)
                    if offered is not None:
                        return offered
                notice = _decision_status(path, data, payload) if kind != "stop" else None
                return render(platform, kind, event, notice) if notice else None
            approval = dict(data.get("approval") or {})
            due = kind != "stop" and _spend_reminder_due(approval, credit, reminder_settings(platform))
            # Lower spend resets reminder marks too, even when no reminder is due.
            if approval != data.get("approval") or credit != data.get("current_credit", data.get("credit")):
                data["approval"], data["current_credit"] = approval, credit
                if not save_state(path, data):
                    return None
            if not due:
                return None
            return render(platform, kind, event,
                          spend_directive(platform, credit, *reminder_settings(platform)))

        if data is not None and data.get("decision") != "pending" and not archive_answer(path, data):
            if kind == "stop":
                return None  # Defer the warning to a tool event; never block this decision twice.
            notice = _archive_failure_notice(path, data)
            return render(platform, kind, event, notice) if notice else None
        import secrets
        stamp = _iso_now(now)
        data = {"schema": DECISION_SCHEMA, "id": secrets.token_hex(16),
                "project": str(project), "platform": platform, "origin": "tracked", "decision": "pending",
                "created_at": stamp, "recorded_at": stamp,
                "windows": {w["name"]: w.get("resets_at") for w in crossing},
                "confirmed_usage": crossing, "credit": credit,
                "delivery": {"state": "offered"},
                "approval": _record_approval({}, crossing, credit, reminder_settings(platform), stamp, now)}
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None
        session = _context_session(payload)
        if session is not None:
            data["status_sessions"] = {session: "pending"}
        if not save_state(path, data):
            return None
        return _emit_offer(path, data, platform, kind, event)


def offer_warning(platform: str, project: Path, warning_reference: str) -> dict[str, Any]:
    """Bootstrap a caller-attested actual host warning without inventing usage.

    Warning references are audit inputs from the real host, not probe readings
    or native approvals. An answer covers that warning episode only.
    """
    import secrets
    platform = canonical_platform(platform)
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,47}", platform):
        raise ValueError("safe platform slug required")
    if not _warning_reference_valid(warning_reference):
        raise ValueError("genuine host warning reference required")
    requested_project, project = project.resolve(), resolve_project(project)
    probe = _load_probe()
    if probe.adoption_active():
        raise ValueError("runtime adoption active; no decision writes")
    with probe.ActivityLock() as activity:
        if not activity.held:
            raise ValueError("usage activity busy; no decision writes")
        path = decision_path(platform, project)
        data = pending_decision(platform, {}, (requested_project,))
        if data is not None:
            _migrate_identity(platform, project, data)
            if data["decision"] == "pending" and _deferred_answer(data) is not None:
                data = _consume_answer(platform, project, data)["decision"]
            same_warning = (data.get("origin") == "host-warning"
                            and data.get("warning_reference") == warning_reference)
            if data["decision"] == "pending" or same_warning:
                message = (_offered_directive(data) if data["decision"] == "pending"
                           and data["delivery"]["state"] == "offered" else None)
                return {"created": False, "decision": data, "directive": message}
            if not archive_answer(path, data):
                return {"created": False, "decision": data, "error": "history unavailable",
                        "directive": _archive_failure_notice(path, data)}
        stamp = _iso_now(time.time())
        data = {"schema": DECISION_SCHEMA, "id": secrets.token_hex(16),
                "project": str(project), "platform": platform, "origin": "host-warning",
                "warning_reference": warning_reference, "decision": "pending",
                "created_at": stamp, "recorded_at": stamp, "windows": {},
                "confirmed_usage": [], "credit": None, "delivery": {"state": "offered"},
                "approval": {}}
        path.parent.mkdir(parents=True, exist_ok=True)
        if not save_state(path, data):
            raise OSError("decision write failed")
        return {"created": True, "decision": data, "directive": _offered_directive(data)}


def decision_cli(argv: list[str]) -> int:
    """Agent-accessible state transition; genuine host IDs are required inputs."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision-action", required=True,
                        choices=("offer-warning", "claim", "delivered", "uncertain", "answer"))
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--warning-reference", default="")
    for name in ("tool", "claim-id", "request-id", "response-id", "answer"):
        parser.add_argument("--" + name, default="")
    args = vars(parser.parse_args(argv))
    action = args.pop("decision_action")
    platform, project, ident = args.pop("platform"), args.pop("project"), args.pop("decision_id")
    reference = args.pop("warning_reference")
    try:
        result = (offer_warning(platform, project, reference) if action == "offer-warning"
                  else decision_transition(platform, project.resolve(), ident, action, **args))
        print(json.dumps(result))
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


def usage_cli(argv: list[str]) -> int:
    """User-run status and recovery; no agent claim or host IDs are required."""
    import argparse
    parser = argparse.ArgumentParser(prog="nexus-hub usage")
    parser.add_argument("action", choices=("status", "decide"))
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--platform", default="", help="Provider slug; claude-code is accepted as claude.")
    parser.add_argument("--decision-id", default="", help="Refuse to answer a different decision.")
    parser.add_argument("--answer", choices=("wait", "handoff", "credits"))
    args = parser.parse_args(argv)
    if args.action == "decide" and not args.answer:
        parser.error("decide requires an explicit --answer wait|handoff|credits")
    project = resolve_project(args.project)
    probe = _load_probe()
    try:
        with probe.ActivityLock() as activity:
            if not activity.held:
                raise ValueError("usage activity busy or runtime adoption active; no decision writes")
            platforms = [canonical_platform(args.platform)] if args.platform else sorted({
                canonical_platform(str(load_state(path).get("platform", "")))
                for path in (state_dir() / "decisions").glob("*.json")})
            records = [data for platform in platforms
                       if re.fullmatch(r"[a-z][a-z0-9-]{0,47}", platform)
                       if (data := pending_decision(platform, {}, (args.project,), decision_id=args.decision_id)) is not None]
            if args.action == "status":
                print(json.dumps({"project": str(project), "decisions": records}))
                return 0
            matches = [data for data in records if data["decision"] == "pending"
                       and (not args.decision_id or args.decision_id == data["id"])]
            if len(matches) != 1:
                details = [{key: data[key] for key in ("platform", "project", "id", "decision")}
                           for data in records]
                raise ValueError("one pending decision required; use --platform and --decision-id. "
                                 "Stored decisions: " + json.dumps(details))
            data = matches[0]
            receipt = _submitted_receipt(data, args.answer, "user-cli", "nexus-hub usage decide")
            _defer_answer(data, receipt)
            result = _consume_answer(data["platform"], project, data)
            if result["decision"]["decision"] != args.answer:
                raise ValueError("decision already answered: " + result["decision"]["decision"])
            print(json.dumps(result))
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


def evaluate(payload: dict[str, Any], started: float, script_dir: Path | None = None) -> dict[str, Any] | None:
    """The whole decision for one payload, shared across sessions."""
    return _evaluate_shared(payload, started, script_dir)


def main() -> int:
    """Hook entry point. Always exits 0."""
    if "--decision-action" in sys.argv[1:]:
        return decision_cli(sys.argv[1:])
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
