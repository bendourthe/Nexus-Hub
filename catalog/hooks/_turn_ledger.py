#!/usr/bin/env python3
"""Turn ledger: stuck-turn notice and environment-fact replay (v4.15.5).

One stdlib-only helper behind two thin wrappers (``stuck-turn-notice.sh`` and
``.ps1``) and the two ``session-start`` wrappers. Subcommands:

``record``              read one hook payload on stdin, append a hashed outcome
                        to the per-user ledger, print at most one advisory
                        notice per turn, and (opt-in) update confirmed
                        environment facts. Always exits 0; silent on any error.
``rotate``              rotate an oversized ledger (session start only).
``facts``               print confirmed environment facts (``NEXUS_ENV_FACTS=on``).
``stats``               print the two local outcome proxies as JSON.
``replay-transcripts``  count how often each signal fires over local Claude Code
                        transcripts. Prints counts and turn identifiers only.

State lives under ``~/.nexus-hub/state/<16 hex of SHA-256 of the resolved
project root>/`` and nowhere in the project tree. Command and file text are
stored only as HMAC-SHA256 keys (key: ``~/.nexus-hub/state/ledger.key``, mode
0600). Plaintext appears only in ``env-facts.json`` and only for facts that pass
the allowlist grammar and the secret scan. The helper opens no socket, starts
no child process, and never writes a settings file.

Concurrency: a record is one append of one complete line, a partial last line
is ignored on read, and rotation moves the file (no rewrite of a live ledger).
Worst cases: a duplicate notice (lost ``notified`` marker) or a missed signal
(lost outcome from a parallel tool call). Fact-store updates write a temp file
and rename it; last writer wins, so a lost update delays a confirmation by one
session.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import tempfile
import stat
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA = 1
LEDGER = "turn-ledger.jsonl"
ROTATED = "turn-ledger.1.jsonl"
FACTS = "env-facts.json"
KEY_FILE = "ledger.key"
HOOK_NAME = "stuck-turn-notice"

MAX_STDIN = 1 << 20
LEDGER_CAP = 256 * 1024
TAIL_BYTES = 128 * 1024
RETENTION_DAYS = 30
WINDOW = 20
THRESHOLD_REPEAT = 3
THRESHOLD_STORM = 6
THRESHOLD_CHURN = 4
MAX_FACTS_SHOWN = 5
MAX_FACT_LINE = 120
CONFIRM_SESSIONS = 3
CONFIRM_DAYS = 2

# Platforms whose documented hook payloads let the detector run. Codex and
# Copilot expose no failure signal or file path in the fetched vendor
# documents, so the helper no-ops there (decision T007).
ACTIVE_PLATFORMS = frozenset({"claude", "gemini", "qwen", "kimi"})

BASH_TOOLS = frozenset({"bash", "shell", "run_shell_command", "powershell", "exec_command"})
EDIT_TOOLS = frozenset(
    {"edit", "write", "multiedit", "write_file", "replace", "writefile", "strreplacefile"}
)
SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,96}$")
SAFE_ECHO = re.compile(r"^[A-Za-z0-9 ._/:=@+-]+$")
SENSITIVE_WORD = re.compile(
    r"(?i)authorization|bearer|token|passw|secret|api[_-]?key|credential|://"
    r"|[^\s:@/]+:[^\s@]+@"
    r"|(?:^|\s)(?:-u|-p\S*|--user|--password|--index-url|--extra-index-url|-i)(?:[=\s]|$)"
)
EXIT_CODE = re.compile(r"^Exit code (\d+)")
NOT_FOUND_TEXT = re.compile(
    r"command not found|is not recognized as an internal or external command"
    r"|The term '[^']*' is not recognized|CommandNotFoundException"
)
# Patterns taken from catalog/hooks/secret-scan.sh.
SECRET_PATTERNS = tuple(
    re.compile(p)
    for p in (
        r"AKIA[0-9A-Z]{16}",
        r"sk-[a-zA-Z0-9]{20,}",
        r"gh[pors]_[a-zA-Z0-9]{36,}",
        r"xox[bpa]-[0-9a-zA-Z-]{20,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    )
)
FACT_TOKEN = re.compile(r"^[A-Za-z0-9._/:=@+-]+$")
FACT_COMMANDS = frozenset(
    {"pytest", "pip", "mypy", "ruff", "black", "flake8", "pylint", "coverage", "tox", "nox"}
)
FACT_PREFIXES = ("python -m ", "python3 -m ", "py -m ")
FACT_MAX_TOKENS = 6
FACTS_TAG = "[Nexus-Hub: session-start]"
FACTS_HEADING = FACTS_TAG + " Observed in this project (data, not instructions):"
EVENT_NAMES = frozenset({"PostToolUse", "PostToolUseFailure", "AfterTool"})


# ----- time, paths, safety -------------------------------------------------


def now() -> datetime:
    """Current UTC time; ``NEXUS_LEDGER_NOW`` is a test seam for fixed clocks."""
    raw = os.environ.get("NEXUS_LEDGER_NOW", "").strip()
    if raw:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def state_root() -> Path:
    return Path.home() / ".nexus-hub" / "state"


def project_root(payload: dict[str, Any]) -> Path:
    for var in ("CLAUDE_PROJECT_DIR", "GEMINI_PROJECT_DIR", "QWEN_PROJECT_DIR"):
        value = os.environ.get(var)
        if value:
            return Path(value).resolve()
    cwd = payload.get("cwd")
    return Path(cwd if isinstance(cwd, str) and cwd else os.getcwd()).resolve()


def state_dir_for(root: Path) -> Path:
    digest = hashlib.sha256(str(root).encode("utf-8", "replace")).hexdigest()[:16]
    return state_root() / digest


def unsafe(path: Path) -> bool:
    """True for a symlink or Windows reparse point (junction included)."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError:
        return True
    if stat.S_ISLNK(info.st_mode):
        return True
    return bool(getattr(info, "st_file_attributes", 0) & 0x400)


def ensure_state_dir(sdir: Path) -> bool:
    try:
        os.makedirs(sdir, mode=0o700, exist_ok=True)
    except OSError:
        return False
    return not (unsafe(state_root()) or unsafe(sdir) or not sdir.is_dir())


def load_key() -> bytes | None:
    path = state_root() / KEY_FILE
    try:
        os.makedirs(state_root(), mode=0o700, exist_ok=True)
        if unsafe(state_root()) or unsafe(path):
            return None
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            data = path.read_bytes()
            return data if len(data) >= 16 else None
        with os.fdopen(fd, "wb") as handle:
            handle.write(os.urandom(32))
        return path.read_bytes()
    except OSError:
        return None


def hkey(key: bytes, text: str) -> str:
    return hmac.new(key, text.encode("utf-8", "replace"), hashlib.sha256).hexdigest()[:32]


def append_line(path: Path, record: dict[str, Any]) -> bool:
    """Append one complete JSON line with a single write; False when unsafe."""
    if unsafe(path.parent) or unsafe(path):
        return False
    line = (json.dumps(record, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, line)
        finally:
            os.close(fd)
    except OSError:
        return False
    return True


def read_tail(path: Path) -> list[dict[str, Any]]:
    """Parse the last TAIL_BYTES of a ledger; a partial or bad line is skipped."""
    if unsafe(path):
        return []
    try:
        size = path.stat().st_size
        with open(path, "rb") as handle:
            if size > TAIL_BYTES:
                handle.seek(size - TAIL_BYTES)
                handle.readline()
            raw = handle.read()
    except OSError:
        return []
    records: list[dict[str, Any]] = []
    for line in raw.split(b"\n"):
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if isinstance(item, dict) and item.get("v") == SCHEMA:
            records.append(item)
    return records


# ----- payload normalization -----------------------------------------------


def detect_platform(payload: dict[str, Any]) -> str:
    """Infer the platform from payload shape; ``NEXUS_TURN_PLATFORM`` overrides."""
    override = os.environ.get("NEXUS_TURN_PLATFORM", "").strip()
    if override:
        return override
    if "turn_id" in payload:
        return "codex"
    if "session_title" in payload or "client_type" in payload:
        return "kimi"
    if payload.get("hook_event_name") == "AfterTool":
        return "gemini"
    if "toolName" in payload or "toolResult" in payload:
        return "copilot"
    if "timestamp" in payload and "permission_mode" in payload:
        return "qwen"
    if "timestamp" in payload:
        return "copilot"
    return "claude"


def _safe_id(value: Any) -> str:
    return value if isinstance(value, str) and SAFE_ID.match(value) else ""


def _error_text(payload: dict[str, Any]) -> str:
    err = payload.get("error")
    if not err:
        response = payload.get("tool_response")
        err = response.get("error") if isinstance(response, dict) else None
    if isinstance(err, str):
        return err
    return json.dumps(err, default=str) if err else ""


def _exit_class(error: str) -> str:
    match = EXIT_CODE.match(error)
    if match and int(match.group(1)) in (127, 9009):
        return "not_found"
    return "not_found" if NOT_FOUND_TEXT.search(error[:400]) else "other"


def normalize(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Reduce a hook payload to the fields the detector uses, or None to skip."""
    name = payload.get("tool_name")
    if not isinstance(name, str) or payload.get("is_interrupt") is True:
        return None
    low = name.lower()
    family = "bash" if low in BASH_TOOLS else "edit" if low in EDIT_TOOLS else ""
    session = _safe_id(payload.get("session_id"))
    if not family or not session:
        return None
    tool_input = payload.get("tool_input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    error = _error_text(payload)
    event = str(payload.get("hook_event_name") or "")
    ok = not (error or event.lower() == "posttoolusefailure")
    command = tool_input.get("command") if family == "bash" else None
    target = None
    if family == "edit":
        for field in ("file_path", "path", "filePath"):
            if isinstance(tool_input.get(field), str):
                target = tool_input[field]
                break
    if family == "bash" and not isinstance(command, str):
        return None
    if family == "edit" and not target:
        return None
    return {
        "family": family,
        "ok": ok,
        "session_id": session,
        "turn_id": _safe_id(payload.get("prompt_id")) or _safe_id(payload.get("turn_id")),
        "command": command.strip() if isinstance(command, str) else None,
        "target": target,
        "exit_class": None if ok else _exit_class(error),
        "event": event if event in EVENT_NAMES else "PostToolUse",
    }


def relative_cwd(payload: dict[str, Any], root: Path) -> str | None:
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        return None
    try:
        rel = Path(cwd).resolve().relative_to(root).as_posix()
    except (OSError, ValueError):
        return None
    rel = rel or "."
    if ".." in rel.split("/") or not re.fullmatch(r"[A-Za-z0-9._/@+-]{1,80}", rel):
        return None
    return rel


# ----- detection -----------------------------------------------------------


def detect(outcomes: list[dict[str, Any]]) -> tuple[str, str] | None:
    """Return (signal, key) for the first signal that holds, else None."""
    failures: dict[str, int] = {}
    edits: dict[str, int] = {}
    failed = 0
    for rec in outcomes:
        if not rec.get("ok"):
            failed += 1
            key = rec.get("cmd_key")
            if key:
                failures[key] = failures.get(key, 0) + 1
        elif rec.get("tool") == "edit" and rec.get("file_key"):
            edits[rec["file_key"]] = edits.get(rec["file_key"], 0) + 1
    for key, count in failures.items():
        if count >= THRESHOLD_REPEAT:
            return "repeat", key
    if failed >= THRESHOLD_STORM:
        return "storm", ""
    for key, count in edits.items():
        if count >= THRESHOLD_CHURN:
            return "churn", key
    return None


def turn_records(
    records: list[dict[str, Any]], session: str, turn: str
) -> tuple[list[dict[str, Any]], bool]:
    """Walk backwards over one session's records; return (outcomes, notified)."""
    outcomes: list[dict[str, Any]] = []
    for rec in reversed(records):
        if rec.get("session_id") != session:
            continue
        if turn:
            if rec.get("turn_id") != turn:
                break
            if rec.get("kind") == "notified":
                return outcomes, True
        elif rec.get("kind") == "notified":
            break
        if rec.get("kind") == "outcome":
            outcomes.append(rec)
            if not turn and len(outcomes) >= WINDOW - 1:
                break
    outcomes.reverse()
    return outcomes, False


def echo_value(text: str | None) -> str | None:
    if not text or len(text) > 60 or not text.isascii():
        return None
    if not SAFE_ECHO.match(text) or SENSITIVE_WORD.search(text):
        return None
    if any(p.search(text) for p in SECRET_PATTERNS):
        return None
    return text


def notice_text(signal: str, command: str | None, target: str | None) -> str:
    if signal == "repeat":
        shown = echo_value(command)
        detail = (
            f"The same command has failed {THRESHOLD_REPEAT} times in this turn "
            + (f'(the repeated command was: "{shown}").' if shown else "(text withheld).")
        )
    elif signal == "storm":
        detail = f"{THRESHOLD_STORM} tool calls have failed in this turn."
    else:
        base = os.path.basename((target or "").replace("\\", "/"))
        shown = echo_value(base)
        detail = f"The same file has been changed {THRESHOLD_CHURN} times in this turn " + (
            f'(the file was: "{shown}").' if shown else "(name withheld)."
        )
    return (
        "[Nexus-Hub: stuck-turn-notice] This turn may be stuck. "
        + detail
        + " This is a notice only; consider a different approach before retrying."
    )


# ----- opt-in switches -----------------------------------------------------


def collection_disabled() -> bool:
    names = {n.strip() for n in os.environ.get("NEXUS_DISABLED_HOOKS", "").split(",")}
    return HOOK_NAME in names or os.environ.get("NEXUS_HOOK_PROFILE", "").strip() == "minimal"


def facts_on() -> bool:
    return os.environ.get("NEXUS_ENV_FACTS", "") == "on"


def notice_on() -> bool:
    return os.environ.get("NEXUS_STUCK_NOTICE", "") == "on"


# ----- environment facts ---------------------------------------------------


def _secret_in(text: str) -> bool:
    return bool(SENSITIVE_WORD.search(text)) or any(p.search(text) for p in SECRET_PATTERNS)


def fact_command_ok(text: str) -> bool:
    tokens = text.split(" ")
    if not text or len(tokens) > FACT_MAX_TOKENS or not text.isascii():
        return False
    if any(not FACT_TOKEN.match(t) for t in tokens):
        return False
    for tok in tokens:
        if ".." in tok.split("/") or tok.startswith(("/", "~")) or re.match(r"^[A-Za-z]:", tok):
            return False
    if tokens[0] in ("pip", "pip3") and any(t in ("install", "download", "wheel") for t in tokens[1:]):
        return False
    return not _secret_in(text)


def split_fact(command: str) -> str | None:
    """Return F when ``command`` is an allowed ``python -m <F>`` form."""
    for prefix in FACT_PREFIXES:
        if command.startswith(prefix):
            fail = command[len(prefix):]
            if fail.split(" ")[0] in FACT_COMMANDS and fact_command_ok(fail):
                return fail if fact_command_ok(command) else None
    return None


def load_facts(sdir: Path) -> dict[str, Any]:
    path = sdir / FACTS
    if unsafe(path):
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    ok = isinstance(data, dict) and data.get("v") == SCHEMA and isinstance(data.get("facts"), dict)
    return data["facts"] if ok else {}


def save_facts(sdir: Path, facts: dict[str, Any]) -> None:
    path = sdir / FACTS
    if unsafe(sdir) or unsafe(path):
        return
    tmp = None
    try:
        fd, tmp = tempfile.mkstemp(prefix=FACTS + ".", suffix=".tmp", dir=str(sdir))
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({"v": SCHEMA, "facts": facts}, handle, ensure_ascii=True)
        os.replace(tmp, path)
        tmp = None
    except OSError:
        return
    finally:
        if tmp is not None:
            try:
                os.unlink(tmp)
            except OSError:
                pass


def update_facts(
    sdir: Path, key: bytes, info: dict[str, Any], cwd: str | None, turn: list[dict[str, Any]]
) -> None:
    command = info["command"]
    facts = load_facts(sdir)
    changed = False
    for fact in facts.values():
        if info["ok"] and fact.get("F") == command and fact.get("cwd") == cwd and not fact.get("retired"):
            fact["retired"] = True
            changed = True
    fail = split_fact(command) if info["ok"] and info["turn_id"] and cwd else None
    if fail:
        fkey = hkey(key, fail)
        seen_failure = False
        for rec in turn:
            if rec.get("tool") == "edit":
                seen_failure = False
            elif rec.get("cmd_key") == fkey and rec.get("exit_class") == "not_found":
                seen_failure = rec.get("cwd") == cwd
        if seen_failure:
            entry = facts.setdefault(
                fail + "\x1f" + command + "\x1f" + cwd,
                {"F": fail, "S": command, "cwd": cwd, "sessions": [], "days": [], "retired": False},
            )
            day = now().strftime("%Y-%m-%d")
            if info["session_id"] not in entry["sessions"] and len(entry["sessions"]) < 10:
                entry["sessions"].append(info["session_id"])
            if day not in entry["days"] and len(entry["days"]) < 30:
                entry["days"].append(day)
            entry["last_seen"] = day
            changed = True
    if changed:
        save_facts(sdir, facts)


def _fact_cwd_ok(cwd: Any) -> bool:
    """The same grammar ``relative_cwd`` applies when a fact is recorded."""
    return (isinstance(cwd, str) and re.fullmatch(r"[A-Za-z0-9._/@+-]{1,80}", cwd) is not None
            and ".." not in cwd.split("/"))


def confirmed_facts(facts: dict[str, Any]) -> list[dict[str, Any]]:
    out = [
        f
        for f in facts.values()
        if isinstance(f, dict)
        and not f.get("retired")
        and len(f.get("sessions", [])) >= CONFIRM_SESSIONS
        and len(set(f.get("days", []))) >= CONFIRM_DAYS
        and fact_command_ok(str(f.get("F", "")))
        and split_fact(str(f.get("S", ""))) == f.get("F")
        and _fact_cwd_ok(f.get("cwd"))
        and isinstance(f.get("sessions"), list) and all(isinstance(s, str) for s in f["sessions"])
        and isinstance(f.get("days"), list) and all(isinstance(d, str) for d in f["days"])
    ]
    out.sort(key=lambda f: str(f.get("last_seen", "")), reverse=True)
    return out


# ----- subcommands ---------------------------------------------------------


def read_payload() -> dict[str, Any] | None:
    try:
        raw = sys.stdin.buffer.read(MAX_STDIN + 1)
        if not raw or len(raw) > MAX_STDIN:
            return None
        data = json.loads(raw.decode("utf-8-sig"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def maybe_rotate(sdir: Path, session: str | None) -> None:
    """Rotate an oversized ledger, only when ``session`` has no recent records."""
    path = sdir / LEDGER
    try:
        if unsafe(path) or path.stat().st_size <= LEDGER_CAP:
            return
    except OSError:
        return
    if session and any(r.get("session_id") == session for r in read_tail(path)):
        return
    rotated = sdir / ROTATED
    if unsafe(rotated):
        return
    try:
        os.replace(path, rotated)
    except OSError:
        return
    cutoff = now() - timedelta(days=RETENTION_DAYS)
    kept: list[str] = []
    try:
        for line in rotated.read_text(encoding="utf-8").splitlines():
            try:
                stamp = datetime.fromisoformat(json.loads(line)["ts"].replace("Z", "+00:00"))
                keep = stamp >= cutoff
            except (ValueError, KeyError, TypeError, AttributeError):
                continue
            if keep:
                kept.append(line)
        rotated.write_text("".join(x + "\n" for x in kept), encoding="utf-8")
    except OSError:
        return


def cmd_record(_args: Any) -> int:
    payload = read_payload()
    if payload is None or collection_disabled():
        return 0
    if not (notice_on() or facts_on()):
        return 0
    platform = detect_platform(payload)
    info = normalize(payload)
    if platform not in ACTIVE_PLATFORMS or info is None:
        return 0
    root = project_root(payload)
    sdir = state_dir_for(root)
    key = load_key()
    if key is None or not ensure_state_dir(sdir):
        return 0
    maybe_rotate(sdir, info["session_id"])
    ledger = sdir / LEDGER
    cwd = relative_cwd(payload, root)
    record: dict[str, Any] = {
        "v": SCHEMA, "kind": "outcome", "ts": now().isoformat(timespec="seconds"),
        "platform": platform, "session_id": info["session_id"], "turn_id": info["turn_id"],
        "tool": info["family"], "ok": info["ok"],
    }
    if info["family"] == "bash":
        record["cmd_key"] = hkey(key, info["command"])
        if cwd:
            record["cwd"] = cwd
        if info["exit_class"]:
            record["exit_class"] = info["exit_class"]
    else:
        record["file_key"] = hkey(key, info["target"])
    outcomes, notified = turn_records(read_tail(ledger), info["session_id"], info["turn_id"])
    if not append_line(ledger, record):
        return 0
    if facts_on() and info["family"] == "bash":
        update_facts(sdir, key, info, cwd, outcomes)
    if notified or not notice_on():
        return 0
    found = detect(outcomes + [record])
    if found is None:
        return 0
    signal, signal_key = found
    marker = {
        "v": SCHEMA, "kind": "notified", "ts": record["ts"], "platform": platform,
        "session_id": info["session_id"], "turn_id": info["turn_id"], "signal": signal,
    }
    marker["file_key" if signal == "churn" else "cmd_key"] = signal_key
    if not append_line(ledger, marker):
        return 0
    text = notice_text(signal, info["command"], info["target"])
    if platform == "kimi":
        sys.stdout.write(text + "\n")
    else:
        body = {"hookSpecificOutput": {"hookEventName": info["event"], "additionalContext": text}}
        sys.stdout.write(json.dumps(body, ensure_ascii=True) + "\n")
    return 0


def cmd_rotate(_args: Any) -> int:
    maybe_rotate(state_dir_for(project_root({})), None)
    return 0


def cmd_facts(_args: Any) -> int:
    if not facts_on():
        return 0
    if collection_disabled():
        print(FACTS_TAG + " Environment facts are unavailable: collection is off.")
        return 0
    sdir = state_dir_for(project_root({}))
    lines: list[str] = []
    shown: list[dict[str, Any]] = []
    for fact in confirmed_facts(load_facts(sdir)):
        line = (
            f"- {json.dumps(fact['F'])} was not found here; "
            f"{json.dumps(fact['S'])} worked in {json.dumps(fact['cwd'])}"
        )
        if len(line) <= MAX_FACT_LINE:
            lines.append(line)
            shown.append(fact)
        if len(lines) == MAX_FACTS_SHOWN:
            break
    if lines:
        print(FACTS_HEADING)
        print("\n".join(lines))
        key = load_key()
        if key is not None and ensure_state_dir(sdir):
            append_line(sdir / LEDGER, {
                "v": SCHEMA, "kind": "replayed", "ts": now().isoformat(timespec="seconds"),
                "f_keys": [hkey(key, f["F"]) for f in shown],
            })
    return 0


def cmd_stats(_args: Any) -> int:
    records = read_tail(state_dir_for(project_root({})) / LEDGER)
    notified_turns = quiet = replayed = reattempted = 0
    for i, rec in enumerate(records):
        if rec.get("kind") == "notified":
            notified_turns += 1
            sig = rec.get("cmd_key") or rec.get("file_key")
            nxt = [r for r in records[i + 1:] if r.get("kind") == "outcome"
                   and r.get("session_id") == rec.get("session_id")][:3]
            if not any(sig and sig in (r.get("cmd_key"), r.get("file_key")) for r in nxt):
                quiet += 1
        elif rec.get("kind") == "replayed":
            keys = set(rec.get("f_keys", []))
            replayed += len(keys)
            later = {r.get("cmd_key") for r in records[i + 1:] if r.get("kind") == "outcome"}
            reattempted += len(keys & later)
    out = {
        "notified_turns": notified_turns,
        "no_recurrence_share": round(quiet / notified_turns, 3) if notified_turns else None,
        "replayed_facts": replayed,
        "reattempted_after_replay": reattempted,
        "reattempt_rate": round(reattempted / replayed, 3) if replayed else None,
    }
    print(json.dumps(out))
    return 0


def _transcript_turns(path: Path) -> list[list[dict[str, Any]]]:
    """Rebuild per-prompt tool outcome sequences from one Claude Code transcript."""
    turns: list[list[dict[str, Any]]] = []
    pending: dict[str, dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line)
        except ValueError:
            continue
        if not isinstance(item, dict):
            continue
        msg = item.get("message")
        content = msg.get("content") if isinstance(msg, dict) else None
        if item.get("type") == "user" and isinstance(content, str):
            turns.append([])
        if not isinstance(content, list) or not turns:
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and item.get("type") == "user":
                turns.append([])
            elif block.get("type") == "tool_use":
                pending[str(block.get("id"))] = block
            elif block.get("type") == "tool_result":
                use = pending.pop(str(block.get("tool_use_id")), None)
                info = normalize({
                    "tool_name": (use or {}).get("name"), "tool_input": (use or {}).get("input"),
                    "session_id": "x", "error": "x" if block.get("is_error") else "",
                })
                if info:
                    turns[-1].append({
                        "ok": info["ok"], "tool": info["family"],
                        "cmd_key": info["command"] if info["family"] == "bash" else "",
                        "file_key": info["target"] if info["family"] == "edit" else "",
                    })
    return turns


def cmd_replay(args: Any) -> int:
    counts = {"repeat": 0, "storm": 0, "churn": 0}
    fired: list[str] = []
    total = 0
    for path in sorted(Path(args.directory).rglob("*.jsonl")):
        try:
            turns = _transcript_turns(path)
        except OSError:
            continue
        for index, turn in enumerate(turns):
            total += 1
            found = detect(turn)
            if found:
                counts[found[0]] += 1
                fired.append(f"{path.stem[:8]}:{index}:{found[0]}")
    per100 = {k: round(100 * v / total, 2) if total else None for k, v in counts.items()}
    print(json.dumps({"turns": total, "fired": counts, "per_100_turns": per100, "turn_ids": fired}))
    return 0


def main(argv: list[str] | None = None) -> int:
    args_in = sys.argv[1:] if argv is None else argv
    if args_in[:1] == ["record"] and len(args_in) == 1:
        try:  # fast path: the hook runs on every tool call, so skip argparse
            return cmd_record(None)
        except Exception:  # noqa: BLE001 - an advisory hook never fails the tool call
            return 0
    import argparse  # noqa: PLC0415 - only the slow-path subcommands need it

    parser = argparse.ArgumentParser(prog="_turn_ledger")
    sub = parser.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record")
    record.add_argument("--platform", default="auto")
    record.set_defaults(func=cmd_record)
    for name, func in (("rotate", cmd_rotate), ("facts", cmd_facts), ("stats", cmd_stats)):
        sub.add_parser(name).set_defaults(func=func)
    replay = sub.add_parser("replay-transcripts")
    replay.add_argument("directory")
    replay.set_defaults(func=cmd_replay)
    args = parser.parse_args(args_in)
    if args.command == "record":
        if args.platform != "auto":
            os.environ["NEXUS_TURN_PLATFORM"] = args.platform
        try:
            return args.func(args)
        except Exception:  # noqa: BLE001 - an advisory hook never fails the tool call
            return 0
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
