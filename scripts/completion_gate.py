#!/usr/bin/env python3
"""Turn-end completion gate and prompt capture for a full /implement run.

Installed at ~/.nexus-hub/scripts/completion_gate.py and called by the thin
catalog adapters `completion-gate.{sh,ps1}` and `approval-capture.{sh,ps1}`.

    completion_gate.py stop      read a turn-end payload; refuse or continue the
                                 stop while the run's checker verdict is INCOMPLETE
    completion_gate.py capture   read a prompt-submit payload; store the digest of the
                                 user's whole prompt for the approval-origin rule
                                 (skipped when NEXUS_RUNNER_LAUNCH=1)

The definition of "done" belongs to the completion contract
(catalog/skills/workflow/implement-phase/references/completion-contract.md) and
to scripts/check_plan_completion.py; this module never evaluates a predicate.

Rules this module keeps:
  - A session with no bound run record is never touched: exit 0, no output.
  - A schema-2 (minor) record is judged by one `check-minor --json` run, whose
    verdict and met count come from the same evaluation, so the no-progress rule
    applies to the minor score; a schema-1 record keeps `check` then `score`.
  - A refusal counts toward no-progress only when a score was read; a score that
    timed out or could not be parsed never does. Part of the budget is reserved for
    writing the blocker.
  - A gate that cannot evaluate (checker missing, too slow) allows the stop and
    says so on stderr. Trapping a session is worse than letting the runner resume.
  - `stop_hook_active` is never a release condition.
  - The continuation reason names only predicate ids, never text from the plan.
  - The output shape follows NEXUS_GATE_FORMAT when set, else the payload shape.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BUDGET_SECONDS = 30.0
BLOCK_RESERVE_SECONDS = 5.0  # kept back from the evaluation for the blocker write
NO_PROGRESS_REFUSALS = 3
PROMPT_RETENTION_SECONDS = 72 * 3600
FORMATS = (
    "top-level-block",
    "vscode-hook-specific-output",
    "cursor-followup-message",
    "antigravity-continue",
    "gemini-deny",
    "exit-2",
    "plugin",
)
REASON = (
    "The full /implement run is not complete ({ids}). Continue with the next unmet "
    "item; stop only when scripts/check_plan_completion.py reports a terminal verdict."
)


def _home() -> Path:
    return Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())


def _runs_dir() -> Path:
    override = os.environ.get("NEXUS_HUB_RUNS_DIR")
    return Path(override) if override else _home() / ".nexus-hub" / "runs"


def _checker() -> Path:
    return _home() / ".nexus-hub" / "scripts" / "check_plan_completion.py"


def _read_payload() -> dict:
    try:
        # A byte-order mark from a Windows console encoding is not part of the payload.
        payload = json.loads(sys.stdin.read().replace("\ufeff", "").strip() or "{}")
    except (ValueError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _session(payload: dict) -> str:
    for key in ("session_id", "sessionId", "conversation_id", "conversationId"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


# --------------------------------------------------------------------------- stop


def resolve_format(payload: dict) -> str:
    explicit = os.environ.get("NEXUS_GATE_FORMAT", "")
    if explicit in FORMATS:
        return explicit
    if "cursor_version" in payload:
        return "cursor-followup-message"
    if str(payload.get("hook_event_name", "")) == "AfterAgent":
        return "gemini-deny"
    # Kimi's documented base payload carries session_title and client_type, which
    # no other supported host sends; its hook schema has no env field to set the
    # format, and exit 2 is its documented continuation.
    if "client_type" in payload and "session_title" in payload:
        return "exit-2"
    return "top-level-block"


def emit_continue(fmt: str, reason: str) -> int:
    """Write the platform's documented refuse-the-stop output; return the exit code."""
    if fmt == "exit-2":
        print(reason, file=sys.stderr)
        return 2
    shapes = {
        "top-level-block": {"decision": "block", "reason": reason},
        "vscode-hook-specific-output": {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "decision": "block",
                "reason": reason,
            }
        },
        "cursor-followup-message": {"followup_message": reason},
        "antigravity-continue": {"decision": "continue", "reason": reason},
        "gemini-deny": {"decision": "deny", "reason": reason},
        # Typed plugins (OpenCode, OpenClaw, Pi, Hermes) translate this into
        # their own continuation call.
        "plugin": {"decision": "continue", "reason": reason},
    }
    sys.stdout.write(json.dumps(shapes[fmt]) + "\n")
    return 0


def _budget() -> float:
    """The evaluation budget; a plugin host with a shorter handler limit lowers it.

    OpenClaw gives each handler 15 seconds, so its plugin asks for 10. The value
    is clamped to 1..30 seconds: a caller can shorten the budget, never extend it.
    """
    try:
        requested = float(os.environ.get("NEXUS_GATE_BUDGET_SECONDS", BUDGET_SECONDS))
    except ValueError:
        return BUDGET_SECONDS
    return min(BUDGET_SECONDS, max(1.0, requested))


def find_record(session: str) -> tuple[Path, dict] | None:
    runs = _runs_dir()
    if not session or not runs.is_dir():
        return None
    for path in sorted(runs.glob("*.json")):
        if path.name.endswith(".gate.json"):
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and record.get("session_id") == session:
            return path, record
    return None


def _run_checker(args: list[str], budget_end: float, cwd: str) -> tuple[int, str]:
    remaining = budget_end - time.monotonic()
    if remaining <= 0:
        return -1, ""
    try:
        proc = subprocess.run(
            [sys.executable, str(_checker()), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=remaining,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return -1, ""
    return proc.returncode, proc.stdout


def _scope_args(record: dict, repo_root: Path, session: str) -> tuple[list[str], list[str], list[str]] | None:
    """(check argv, score argv, block argv prefix) for the record's scope, or None when unusable."""
    if record.get("schema") == 2:
        minor = record.get("minor")
        if record.get("scope") != "minor" or not isinstance(minor, str) or not minor:
            return None
        scope = ["--repo", str(repo_root), "--session", session]
        # One run: `--json` carries the met count and head, so there is no score argv.
        return (
            ["check-minor", minor, *scope, "--json"],
            [],
            ["record", "block", "--minor", minor, *scope],
        )
    plan = str(repo_root / str(record.get("plan", "")))
    return (
        ["check", plan, "--session", session],
        ["score", plan, "--session", session],
        ["record", "block", plan, "--session", session],
    )


def _json_score(out: str) -> list[str]:
    """[met, head] from a `check-minor --json` line, or [] when it is absent or unreadable."""
    for line in out.splitlines()[1:]:
        try:
            body = json.loads(line)
        except ValueError:
            continue
        if isinstance(body, dict) and isinstance(body.get("met"), int) and isinstance(body.get("head"), str):
            return [str(body["met"]), body["head"]]
    return []


def _load_gate_state(path: Path) -> dict:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        return state if isinstance(state, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_gate_state(path: Path, state: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def cmd_stop() -> int:
    payload = _read_payload()
    session = _session(payload)
    found = find_record(session)
    if found is None:
        return 0
    record_path, record = found
    checker = _checker()
    repo_root = Path(str(record.get("repo_root", "")))
    if not checker.is_file() or _is_inside(checker, repo_root):
        print(
            "completion-gate: checker not installed outside the working tree; allowing stop",
            file=sys.stderr,
        )
        return 0
    scope = _scope_args(record, repo_root, session)
    if scope is None:
        return 0
    check_args, score_args, block_args = scope
    budget = _budget()
    budget_end = time.monotonic() + budget
    # The evaluation stops early enough that a blocker can still be written.
    eval_end = budget_end - min(BLOCK_RESERVE_SECONDS, budget * 0.3)
    # check-minor spreads its own budget over the members; keep it inside the evaluation's.
    os.environ["NEXUS_CHECK_MINOR_BUDGET_SECONDS"] = str(max(1, int(eval_end - time.monotonic()) - 2))
    rc, out = _run_checker(check_args, eval_end, str(repo_root))
    if rc == -1:
        print(
            "completion-gate: checker did not finish in time; allowing stop",
            file=sys.stderr,
        )
        return 0
    if rc in (0, 3, 4):
        return 0
    if rc == 2:
        _run_checker(
            [
                *block_args,
                "--category",
                "record-tampered",
                "--evidence",
                "check_plan_completion.py exited 2 on a plan valid at run start",
            ],
            budget_end,
            str(repo_root),
        )
        return 0
    first = out.splitlines()[0] if out else "INCOMPLETE:"
    ids = first.removeprefix("INCOMPLETE:").split()
    if score_args:
        score_rc, score_out = _run_checker(score_args, eval_end, str(repo_root))
        score = score_out.split()[:2] if score_rc == 0 else []
        if len(score) != 2 or not score[0].isdigit():
            score = []
    else:
        score = _json_score(out)
    state_path = record_path.with_name(record_path.stem + ".gate.json")
    state = _load_gate_state(state_path)
    refusals = int(state.get("refusals", 0))
    if score:
        progressed = int(score[0]) > int(state.get("met", -1)) or score[1] != state.get("head")
        refusals = 0 if progressed else refusals + 1
        state.update(met=int(score[0]), head=score[1])
    else:
        # An unreadable score is not evidence of no progress: the counter stays where it was.
        print("completion-gate: progress score unavailable; refusal not counted", file=sys.stderr)
    state["refusals"] = refusals
    state["updated"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    _save_gate_state(state_path, state)
    if refusals >= NO_PROGRESS_REFUSALS:
        _run_checker(
            [
                *block_args,
                "--category",
                "no-progress",
                "--evidence",
                f"progress score unchanged over {refusals} refusals: {' '.join(ids[:20])}",
            ],
            budget_end,
            str(repo_root),
        )
        return 0
    return emit_continue(
        resolve_format(payload), REASON.format(ids=" ".join(ids[:40]) or "unknown")
    )


# --------------------------------------------------------------------------- capture


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _digest(text: str) -> str:
    return hashlib.sha256(_normalize(text).encode("utf-8")).hexdigest()


def _prompt(payload: dict) -> str:
    for key in ("prompt", "user_prompt", "userPrompt", "message", "text"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _prune(prompts: Path) -> None:
    cutoff = time.time() - PROMPT_RETENTION_SECONDS
    for path in prompts.glob("*.jsonl"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except OSError:
            continue


def cmd_capture() -> int:
    payload = _read_payload()
    if "cursor_version" in payload:
        # Cursor's prompt-submit parser expects one JSON object on stdout.
        sys.stdout.write('{"continue":true}\n')
    if os.environ.get("NEXUS_RUNNER_LAUNCH") == "1":
        # A prompt the runner launched is not the user's (v4.13.2 WN-9).
        return 0
    session, prompt = _session(payload), _prompt(payload)
    if not session or not prompt:
        return 0
    # Only the whole prompt is stored: an approval must equal an entire submitted
    # prompt, so a line inside a longer prompt never counts (v4.13.2 WN-9).
    whole = _digest(prompt)
    prompts = _runs_dir() / "prompts"
    try:
        prompts.mkdir(parents=True, exist_ok=True)
        os.chmod(prompts.parent, 0o700)
        path = prompts / f"{hashlib.sha256(session.encode('utf-8')).hexdigest()}.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            # `at` lets record create require a prompt from before the round was
            # rendered, so a fresh agent-launched session cannot carry the paste.
            entry = {"session": session, "prompt": whole, "digests": [whole], "at": time.time()}
            handle.write(json.dumps(entry) + "\n")
        os.chmod(path, 0o600)
        _prune(prompts)
    except OSError:
        # Capture is best effort: a failed write leaves record create to fail closed.
        pass
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    mode = args[0] if args else "stop"
    if mode == "capture":
        return cmd_capture()
    if mode == "stop":
        return cmd_stop()
    print("usage: completion_gate.py stop|capture", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
