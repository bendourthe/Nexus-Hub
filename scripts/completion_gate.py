#!/usr/bin/env python3
"""Turn-end completion gate and prompt capture for a full /implement run.

Only `capture` runs in a default install. `stop` is opt-in: no default install registers
the turn-end hook (removed 2026-10-28; see docs/policy/completion-levers.md).

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
  - Usage-limit handoff (v4.13.7): the stop is allowed, with no refusal counted
    and no blocker written, only when BOTH the user's answer to the usage
    question in .nexus-hub/usage-decision.json (pending, wait, or handoff; the
    handoff itself is a prompt printed in the chat, so no handoff file is read)
    newer than the last refusal exists in the repository AND the usage probe confirms a
    tracked window at or over NEXUS_HANDOFF_THRESHOLD. The record is never marked
    complete or paused. The usage-guard and probe modules are read from the
    calling hook's directory (NEXUS_GATE_HOOK_DIR, set by the adapter) and never
    from inside the repository, so a repository cannot plant the evidence.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import importlib.util
import json
import os
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

# On Windows, a console program started by a process with no console of its own
# (a hook or agent launched without one, or a detached test) opens a visible
# window that takes keyboard focus. Every child here has its output captured and
# its prompts disabled, so it never needs a window.
NO_WINDOW: dict = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}

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
USAGE_LIMIT_NOTE = (
    "[Nexus-Hub: completion-gate] the run stopped for a usage-limit handoff or the user's "
    "credits-or-handoff answer; it resumes when the user answers or pastes the "
    "handoff prompt."
)
USAGE_PROBE_SECONDS = 4.5
REASON = (
    "The full /implement run is not complete ({ids}). Continue with the next unmet "
    "item; stop only when scripts/check_plan_completion.py reports a terminal verdict."
)


import runpy as _process_runpy
from pathlib import Path as _ProcessPath

_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[0] / "nexus_process.py"))
_PROCESS_POLICY["install_no_window_default"]()


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


def emit_continue(fmt: str, reason: str, source: str = "completion-gate") -> int:
    """Write the platform's documented refuse-the-stop output; return the exit code."""
    reason = f"[Nexus-Hub: {source}] {reason}"
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
        if path.name.endswith((".gate.json", ".continuation.json")):
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and record.get("session_id") == session:
            return path, record
    # No session marker means there is no sealed cross-session owner request.
    # Existence is only a lookup hint; native code below still verifies the seal.
    if not (runs / "questions" / (hashlib.sha256(session.encode()).hexdigest() + ".json")).exists():
        return None
    # Cross-session ownership changes only through native resume. A sealed
    # target marker permits observation of that request, never ordinary work.
    import approval_binding
    import check_plan_completion as ck
    try:
        secret = ck._secret(create=False)
        target = approval_binding.resume_target(runs, secret, session) if secret else None
        if target is not None:
            key, pending = target
            path = runs / (key + '.json')
            from run_plan import _bounded_json
            record = _bounded_json(path)
            if not approval_binding.pending_matches_owner(pending, record, session):
                return None
            _context, verified = ck.resolve_minor_controller(path, record['session_id'], budget_seconds=3,
                minor_protocol=ck.MINOR_AMENDMENT_PROTOCOL, execution_protocol=ck.MINOR_EXECUTION_PROTOCOL)
            if verified == record:
                return path, verified
    except (approval_binding.Refusal, ck.Malformed, ck._minor_module().ObservationUnavailable,
            OSError, ValueError, TypeError, KeyError):
        return None
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
            **NO_WINDOW,
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
        if (isinstance(body, dict) and type(body.get("met")) is int and body["met"] >= 0
                and isinstance(body.get("head"), str) and body["head"] not in ("", "-")):
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


def _parse_time(value: object) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.timestamp()


def _usage_guard(repo_root: Path):
    """(usage-guard module, its directory) from the calling hook's directory, or None.

    Both usage-guard.py and _usage_probe.py must sit outside the repository: a
    repository that could supply them could also report any usage it liked.
    """
    raw = os.environ.get("NEXUS_GATE_HOOK_DIR", "").strip()
    if not raw:
        return None
    directory = Path(raw)
    guard, probe = directory / "usage-guard.py", directory / "_usage_probe.py"
    if not guard.is_file() or not probe.is_file():
        return None
    if _is_inside(guard, repo_root) or _is_inside(probe, repo_root):
        return None
    try:
        spec = importlib.util.spec_from_file_location("nexus_usage_guard_for_gate", guard)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001 - an unloadable guard means "no exception applies"
        return None
    return module, directory


def usage_limit_stop(payload: dict, record_path: Path, record: dict, repo_root: Path, budget_end: float) -> bool:
    """True when this stop is a confirmed usage-limit handoff (see the module docstring)."""
    loaded = _usage_guard(repo_root)
    if loaded is None:
        return False
    guard, directory = loaded
    try:
        platform = guard.detect_platform(payload, directory)
        if platform is None:
            return False
        shared_reader = getattr(guard, "pending_decision", None)
        if shared_reader is not None:
            shared = shared_reader(platform, payload, (repo_root,))
            if shared is not None:
                exhausted = (shared.get("decision") == "credits"
                             and (shared.get("current_credit", shared.get("credit")) or {}).get("state") == "exhausted")
                if shared.get("decision") not in ("pending", "wait", "handoff") and not exhausted:
                    return False
                deadline = min(time.monotonic() + USAGE_PROBE_SECONDS, budget_end - BLOCK_RESERVE_SECONDS)
                current = guard.usage_limit_window(payload, directory, deadline)
                return (current is not None
                        and guard._decision_active(shared, [current[1]], time.time()))
        state = _load_gate_state(record_path.with_name(record_path.stem + ".gate.json"))
        since = _parse_time(state.get("updated")) or _parse_time(record.get("created"))
        if since is None:
            since = record_path.stat().st_mtime
        written_at = getattr(guard, "usage_limit_stop_time", guard.usage_limit_handoff_time)
        written = written_at(platform, payload, (repo_root,))
        if written is None or written <= since:
            return False
        deadline = min(time.monotonic() + USAGE_PROBE_SECONDS, budget_end - BLOCK_RESERVE_SECONDS)
        return guard.usage_limit_window(payload, directory, deadline) is not None
    except Exception:  # noqa: BLE001 - any failure keeps today's behavior
        return False



def _verified_minor_root(path: Path, record: dict, session: str) -> tuple[Path, dict]:
    """Only the trusted installed checker sibling resolves the signed operational root."""
    import importlib.util
    checker = _checker()
    if not checker.is_file() or _is_inside(checker, Path(str(record.get('repo_root', '')))):
        raise ValueError('trusted checker unavailable')
    name = '_nexus_gate_controller_checker'
    spec = importlib.util.spec_from_file_location(name, checker)
    if spec is None or spec.loader is None:
        raise ValueError('trusted checker unavailable')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    # Resolve the checker's exception classes before the call: an except tuple is evaluated only
    # once an error is in flight, so a missing attribute there would escape and fail the hook open.
    try:
        refusals = (module.Malformed, module._minor_module().ObservationUnavailable)
    except Exception as exc:
        raise ValueError('minor controller cannot be verified') from exc
    try:
        ctx, verified = module.resolve_minor_controller(path, session, budget_seconds=min(5.0, _budget()), minor_protocol=1, execution_protocol=1)
    # TypeError/AttributeError: an older sibling checker that lacks the protocol keywords. A
    # mixed helper bundle must keep the run unresolved, never crash the hook and fail open.
    except (OSError, ValueError, TypeError, AttributeError, *refusals) as exc:
        raise ValueError('minor controller cannot be verified') from exc
    if _is_inside(checker, ctx.root):
        raise ValueError('checker is inside operational worktree')
    return ctx.root, verified


def _report_fingerprint(disposition: dict, progress: str) -> str:
    """Identify required reporting obligations without counting them as progress."""
    data = {"progress": progress,
        "requests": sorted((item.get("id"), item.get("kind"))
                           for item in disposition.get("requests", [])),
        "jobs": sorted((item.get("id"), item.get("handle"), item.get("url"), item.get("status"))
                       for item in disposition.get("jobs", [])),
        "conditions": sorted((item.get("id"), item.get("resume_when"))
                             for item in disposition.get("external_conditions", []))}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _reconcile_stop(payload: dict, record_path: Path, record: dict, repo_root: Path,
                    rc: int, out: str, score: list[str]) -> int:
    """Default typed-fact consumer; legitimate waits never prompt another loop."""
    from types import SimpleNamespace
    import run_plan

    scope = SimpleNamespace(minor=record.get("schema") == 2,
        label=str(record.get("minor") if record.get("schema") == 2 else record.get("plan", "")), repo_root=repo_root, observer_session=_session(payload))
    try:
        import approval_binding
        import check_plan_completion as ck
        secret = ck._secret(create=False)
        if secret:
            approval_binding.observe_issued_request(record_path.parent, record_path.stem, secret, record,
                                                   payload.get('last_assistant_message'), observer_session=_session(payload))
        disposition = run_plan.continuation_for_run(scope, record_path, record, rc, out, claim_refresh=True)
        if disposition is None:
            if rc in (0, 4):
                return 0
            raise run_plan.RunnerError("no current run-bound observation; reconcile the objective, pending owner requests, jobs and remaining authorized work")
    except (run_plan.RunnerError, approval_binding.Refusal, OSError, ValueError, KeyError, TypeError) as exc:
        disposition = {"directive": "continue", "state": "reconciliation_required",
            "reason": "Reconcile this unfinished run before ending: " + str(exc), "fingerprint": "invalid:" + str(exc)}
    path = record_path.with_name(record_path.stem + ".continuation.gate.json")
    try:
        with ck._minor_os_lock(path.with_suffix('.mutation.lock'), ck.Budget(3)):
            state = _load_gate_state(path)
            fingerprint = run_plan.continuation_progress(disposition)
            report_fingerprint = _report_fingerprint(disposition, fingerprint)
            same = state.get("fingerprint") == fingerprint
            progressed = bool(score and (int(score[0]) > int(state.get("met", -1)) or score[1] != state.get("head")))
            same = same and not progressed
            refusals = int(state.get("refusals", 0)) + 1 if same else 0
            next_state = {"fingerprint": fingerprint, "report_fingerprint": report_fingerprint, "refusals": refusals,
                          "threshold_reported": state.get("threshold_reported", False) if same else False}
            if 'owner_refresh' in state:
                next_state['owner_refresh'] = state['owner_refresh']
            if score:
                next_state.update(met=int(score[0]), head=score[1])
            _save_gate_state(path, next_state)
            if (disposition['directive'] == 'wait' and disposition['state'] in run_plan.continuation_module().STATES
                    and isinstance(payload.get('last_assistant_message'), str)):
                reporter = run_plan.reporting_module('status_report')
                required = [reporter.state_heading(disposition), *reporter.required_parts(disposition)]
                for number, decision in enumerate(reporter.pending_decisions(disposition), 1):
                    required.extend(reporter.decision_parts(decision, True, number=number))
                delivered = payload['last_assistant_message']
                missing = [part for part in required if part != '---' and part not in delivered]
                goals = re.search(r'(?m)^#{1,6} [^\n]*\bGoals\b', delivered)
                buried = goals is not None and any(part.startswith('### ') and delivered.find(part) > goals.start()
                                                  for part in required if part in delivered)
                if missing or buried or not delivered.lstrip().startswith(required[0]):
                    correction = (int(state.get('report_corrections', 0)) + 1
                                  if same and state.get('report_fingerprint') == report_fingerprint else 1)
                    next_state['report_corrections'] = correction
                    _save_gate_state(path, next_state)
                    if correction <= NO_PROGRESS_REFUSALS:
                        return emit_continue(resolve_format(payload), 'Correct the waiting report before ending. Open with the waiting banner and show the required actions before Goals. Preserve the objective and measured progress.\n\n' + '\n\n'.join(required), 'implementation-state')
                    if correction == NO_PROGRESS_REFUSALS + 1:
                        print('[Nexus-Hub: implementation-state] Waiting report correction limit reached; the outstanding owner request remains recorded. No request or job was invented or retired.', file=sys.stderr)
                    return 0
            if disposition["directive"] != "continue":
                if not same:
                    print("[Nexus-Hub: implementation-state] " + run_plan.waiting_line(disposition), file=sys.stderr)
                return 0
            if refusals >= NO_PROGRESS_REFUSALS:
                if not state.get("threshold_reported"):
                    print("[Nexus-Hub: implementation-state] Waiting for controller reconciliation: the same unfinished condition remained unchanged; no job was restarted and no native blocker was cleared.", file=sys.stderr)
                    next_state["threshold_reported"] = True
                    _save_gate_state(path, next_state)
                return 0
            return emit_continue(resolve_format(payload), disposition["reason"], "implementation-state")

    except ck.MinorConflict:
        print('[Nexus-Hub: implementation-state] Continuation observations are busy; existing requests and refresh claims remain unresolved.', file=sys.stderr)
        return 0


def _observe_question_event(payload: dict) -> int:
    """Observe only question events; unrelated tools remain silent and unchanged."""
    import approval_binding
    import check_plan_completion as ck
    parsed = approval_binding._question_payload(payload)
    session = _session(payload)
    if parsed is None or not session or os.environ.get('NEXUS_RUNNER_LAUNCH') == '1':
        return 0
    found = find_record(session)
    try:
        if found is None:
            pending = ck.precreate_owner_context(session, allow_resume=True)
            if pending is None:
                return 0
            _context, path, record = pending
        else:
            path, record = found
            if record.get('schema') == 1:
                _context, record = ck.resolve_plan_controller(path, session)
            elif record.get('schema') == 2:
                _context, record = ck.resolve_minor_controller(path, record['session_id'], budget_seconds=3,
                    minor_protocol=ck.MINOR_AMENDMENT_PROTOCOL, execution_protocol=ck.MINOR_EXECUTION_PROTOCOL)
            else:
                raise ck.Malformed('unknown native owner schema')
        secret = ck._secret(create=False)
        if not secret:
            return 0
        native_payload = dict(payload, session_id=session)
        if payload.get('hook_event_name') in {'PreToolUse', 'preToolUse'}:
            approval_binding.observe_question_attempt(path.parent, path.stem, secret, record, native_payload)
        else:
            approval_binding.observe_question_result(path.parent, path.stem, secret, record, native_payload)
    except (approval_binding.Refusal, ck.Malformed, ck._minor_module().ObservationUnavailable,
            OSError, ValueError, KeyError, TypeError):
        print('[Nexus-Hub: implementation-state] The native question binding could not be verified. Existing approval authority is unchanged; reconcile the capture method before asking again.', file=sys.stderr)
    return 0


def _precreate_stop(payload: dict, session: str) -> int:
    """Report delivered create obligations without manufacturing a run record."""
    if not session or not (_runs_dir() / "questions" / (hashlib.sha256(session.encode()).hexdigest() + ".json")).exists():
        return 0
    import approval_binding
    import check_plan_completion as ck
    import run_plan
    from types import SimpleNamespace
    try:
        resolved = ck.precreate_owner_context(session, allow_resume=True)
        if resolved is None:
            return 0
        ctx, path, metadata = resolved
        if metadata.get('schema') == 1:
            return _reconcile_stop(payload, path, metadata, ctx.root,
                4 if metadata.get('pause') else 1, 'PAUSED' if metadata.get('pause') else 'INCOMPLETE: native resume pending', [])
        approval_binding.observe_issued_request(path.parent, path.stem, ck._secret(False), metadata,
            payload.get('last_assistant_message'))
        scope = SimpleNamespace(minor=False, label=str(ctx.plan), repo_root=ctx.root)
        previous_path = run_plan.continuation_path(path)
        previous = run_plan._bounded_json(previous_path) if previous_path.exists() else None
        facts = run_plan.precreate_owner_observation(scope, path, metadata, previous)
        if facts is None:
            return 0
        disposition = run_plan.continuation_module().reconcile(facts, (previous or {}).get('disposition'))
        # This unsigned observation contains no native execution authority.
        frame = {'contract': 'implementation-continuation-v1',
            'binding': run_plan.continuation_binding(scope, path, metadata),
            'observation': facts, 'disposition': disposition, 'captured_at': time.time(),
            'refresh_attempts': (previous or {}).get('refresh_attempts', [])}
        owner_pending = facts.get('owner_replies') or facts.get('owner_recovery')
        if owner_pending:
            fingerprint = hashlib.sha256(approval_binding.canonical(owner_pending)).hexdigest()
            attempted = fingerprint in frame['refresh_attempts']
            if not attempted:
                frame['refresh_attempts'] = [*frame['refresh_attempts'][-63:], fingerprint]
            run_plan.save_continuation(path, frame)
            if attempted:
                return 0
            return emit_continue(resolve_format(payload), owner_pending[0]['reason'] +
                ' Reconcile the native record-create owner now. No phase work is authorized before its persisted record verifies.', 'implementation-state')
        run_plan.save_continuation(path, frame)
        reporter = run_plan.reporting_module('status_report')
        required = [reporter.state_heading(disposition), *reporter.required_parts(disposition)]
        for number, decision in enumerate(reporter.pending_decisions(disposition), 1):
            required.extend(reporter.decision_parts(decision, True, number=number))
        message = payload.get('last_assistant_message', '')
        if isinstance(message, str) and message.lstrip().startswith(required[0]) and all(part == '---' or part in message for part in required):
            return 0
        gate_path = path.with_name(path.stem + '.continuation.gate.json')
        prior = _load_gate_state(gate_path)
        fingerprint = run_plan.continuation_progress(disposition)
        report_fingerprint = _report_fingerprint(disposition, fingerprint)
        corrections = (int(prior.get('report_corrections', 0)) + 1
                       if prior.get('report_fingerprint') == report_fingerprint else 1)
        _save_gate_state(gate_path, {'fingerprint': fingerprint, 'report_fingerprint': report_fingerprint,
                                    'report_corrections': corrections})
        if corrections > NO_PROGRESS_REFUSALS:
            return 0
        return emit_continue(resolve_format(payload), '\n\n'.join(required), 'implementation-state')
    except (approval_binding.Refusal, ck.Malformed, run_plan.RunnerError, OSError, ValueError, KeyError, TypeError) as exc:
        return emit_continue(resolve_format(payload), 'Pre-create native context requires reconciliation: ' + str(exc), 'implementation-state')


def _cmd_stop(reconcile_only: bool = False) -> int:
    payload = _read_payload()
    session = _session(payload)
    if not session:
        return 0
    if reconcile_only and payload.get('hook_event_name') in {'PreToolUse', 'preToolUse', 'PostToolUse', 'postToolUse'}:
        return _observe_question_event(payload)
    _observe_permission(payload)
    session = _session(payload)
    found = find_record(session)
    if found is None:
        return _precreate_stop(payload, session)
    record_path, record = found
    checker = _checker()
    repo_root = Path(str(record.get("repo_root", "")))
    if not checker.is_file():
        print("[Nexus-Hub: completion-gate] checker not installed outside the working tree; allowing stop", file=sys.stderr)
        return 0
    if record.get('schema') == 2:
        try:
            repo_root, record = _verified_minor_root(record_path, record, str(record.get("session_id") or ""))
        except ValueError:
            return emit_continue(resolve_format(payload), 'Minor controller verification failed; keep the run unresolved.')
    elif record.get('schema') == 1:
        import check_plan_completion as ck
        try:
            if Path(ck.__file__).resolve() != checker.resolve():
                raise ck.Malformed('matching trusted plan checker unavailable')
            ctx, record = ck.resolve_plan_controller(record_path, session)
            repo_root = ctx.root
        except (ck.Malformed, OSError, ValueError, KeyError, TypeError):
            return emit_continue(resolve_format(payload), 'Plan controller verification failed; keep the run unresolved.')
    else:
        return emit_continue(resolve_format(payload), 'Unknown native controller schema; keep the run unresolved.')
    if not checker.is_file() or _is_inside(checker, repo_root):
        print(
            "[Nexus-Hub: completion-gate] checker not installed outside the working tree; allowing stop",
            file=sys.stderr,
        )
        return 0
    scope = _scope_args(record, repo_root, str(record.get("session_id") or ""))
    if scope is None:
        return 0
    check_args, score_args, block_args = scope
    budget = _budget()
    budget_end = time.monotonic() + budget
    if usage_limit_stop(payload, record_path, record, repo_root, budget_end):
        print(USAGE_LIMIT_NOTE, file=sys.stderr)
        return 0
    # The evaluation stops early enough that a blocker can still be written.
    eval_end = budget_end - min(BLOCK_RESERVE_SECONDS, budget * 0.3)
    # check-minor spreads its own budget over the members; keep it inside the evaluation's.
    limit = max(1, int(eval_end - time.monotonic()) - 2)
    try:
        limit = min(limit, max(1.0, float(os.environ.get("NEXUS_CHECK_MINOR_BUDGET_SECONDS", limit))))
    except ValueError:
        # An invalid caller limit keeps the gate-derived evaluation limit.
        pass
    os.environ["NEXUS_CHECK_MINOR_BUDGET_SECONDS"] = str(limit)
    rc, out = _run_checker(check_args, eval_end, str(repo_root))
    if rc == -1:
        print(
            "[Nexus-Hub: completion-gate] checker did not finish in time; allowing stop",
            file=sys.stderr,
        )
        return 0
    if reconcile_only or record_path.with_name(record_path.stem + ".continuation.json").exists():
        score = _json_score(out)
        if rc == 1 and score_args:
            score_rc, score_out = _run_checker(score_args, eval_end, str(repo_root))
            fields = score_out.split()[:2] if score_rc == 0 else []
            score = fields if len(fields) == 2 and fields[0].isascii() and fields[0].isdigit() else []
        return _reconcile_stop(payload, record_path, record, repo_root, rc, out, score)
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
        print("[Nexus-Hub: completion-gate] progress score unavailable; refusal not counted", file=sys.stderr)
    state["refusals"] = refusals
    state["updated"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    _save_gate_state(state_path, state)
    if score and refusals >= NO_PROGRESS_REFUSALS:
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


def cmd_stop(reconcile_only: bool = False) -> int:
    """A missing native sibling is unavailable, never completion or new authority."""
    try:
        return _cmd_stop(reconcile_only)
    except ModuleNotFoundError as exc:
        if exc.name not in {"check_plan_completion", "approval_binding", "approval_page", "run_plan", "completion_minor", "completion_budget", "repo_host"}:
            raise
        print(f"[Nexus-Hub: completion-gate] native helper bundle unavailable ({exc.name}); allowing stop; native run remains unresolved", file=sys.stderr)
        return 0


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
    _observe_permission(payload)
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
            entry = {"session": session, "prompt": whole, "digests": [whole], "at": time.time(),
                     "event_id": secrets.token_hex(16)}
            mode = payload.get('permission_mode')
            if isinstance(mode, str):
                entry['permission_mode'] = mode
            # Only the installed renderer can present a sealed active short-answer round.
            # No callback fields or agent-provided tool result are interpreted as user input.
            try:
                active = json.loads((_runs_dir() / 'questions' / f'{hashlib.sha256(session.encode()).hexdigest()}.json').read_text(encoding='utf-8'))
                key = (_runs_dir() / '.secret').read_bytes()
                body = {k: v for k, v in active.items() if k != 'mac'}
                mac = hmac.new(key, json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode(), hashlib.sha256).hexdigest()
                if active.get('session') == session and hmac.compare_digest(str(active.get('mac', '')), mac):
                    entry['question'] = {k: active[k] for k in ('key', 'nonce')}
            except (OSError, ValueError, KeyError, TypeError):
                pass
            handle.write(json.dumps(entry) + "\n")
        os.chmod(path, 0o600)
        if '<send_user_message_question_reply>' in prompt:
            import approval_binding
            import check_plan_completion as ck
            secret = ck._secret(create=False)
            observed = False
            try:
                observed = bool(secret and approval_binding.observe_question_reply(_runs_dir(), secret, session, prompt, entry))
            except (approval_binding.Refusal, ck.Malformed, OSError, ValueError, KeyError, TypeError):
                pass  # Preserve the genuine whole-prompt capture even when UI interpretation is unavailable.
            if not observed:
                print('[Nexus-Hub: implementation-state] The whole owner reply was captured, but its question call, current round or reviewed scope could not be verified. No synthetic approval was created.', file=sys.stderr)
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
    if mode == "reconcile-stop":
        return cmd_stop(reconcile_only=True)
    print("usage: completion_gate.py stop|capture|reconcile-stop", file=sys.stderr)
    return 0




def _observe_permission(payload: dict) -> None:
    """Retain the current host-reported mode for continuation, including downgrades."""
    session = _session(payload)
    if not session or os.environ.get('NEXUS_RUNNER_LAUNCH') == '1':
        return
    try:
        runs = _runs_dir()
        key = (runs / '.secret').read_bytes()
        mode = payload.get('permission_mode')
        body = {'origin': 'host-hook-capture', 'session_id': session,
                'permission_mode': mode if isinstance(mode, str) else None, 'at': time.time()}
        body['mac'] = hmac.new(key, json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode(), hashlib.sha256).hexdigest()
        folder = runs / 'host-context'
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f'{hashlib.sha256(session.encode()).hexdigest()}.json'
        path.write_text(json.dumps(body), encoding='utf-8')
        os.chmod(folder, 0o700)
        os.chmod(path, 0o600)
    except (OSError, ValueError):
        pass  # no observation grants no additional authority

if __name__ == "__main__":
    raise SystemExit(main())
