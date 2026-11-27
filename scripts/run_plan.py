#!/usr/bin/env python3
"""Relaunch a platform's headless CLI until a full /implement run reaches a terminal verdict.

    nexus-hub run-plan <plan> --platform <row> [--max-cycles N]
    nexus-hub run-plan vX.Y --platform <row> [--max-cycles N]     (a whole minor)

The completion gate keeps a live session going; this runner is the layer that
continues past a session that ended anyway (a platform's consecutive-block cap,
a crash, a closed terminal). After each cycle it asks
`check_plan_completion.py` for the verdict: a terminal verdict ends the loop, an
INCOMPLETE verdict with a higher progress score relaunches with the platform's
documented resume flag, and three cycles without progress record a
`no-progress` blocker and stop. A `vX.Y` scope drives the schema-2 minor record
the same way through `check-minor` and `score-minor`, so `no-progress` applies to
the minor score; the per-plan path is unchanged.

What this runner never does:
  - create approvals (the run record must already exist from /implement's
    upfront round); every session it launches carries NEXUS_RUNNER_LAUNCH=1,
    so the capture hook skips its prompts and `record create` refuses there,
  - add a permission-bypass, auto-approve, or config-override flag (a denylist
    is asserted per platform in tests), or launch when the platform's own
    configuration already bypasses approvals, unless the user approved the
    `unattended-with-bypass` class upfront,
  - invoke a shell: every launch is an argument list.

Launch and resume flags are hard-coded here from each vendor's CLI reference
(`docs/policy/completion-levers.json` documents the levers but is never read for
flags). The levers matrix decides which rows are offered: exactly the rows whose
headless lever is VERIFIED.
"""

from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
import re
import subprocess
import sys
import time
import tempfile
from collections.abc import Callable
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import approval_page  # installed as a sibling in ~/.nexus-hub/scripts/
from completion_budget import check_minor_seconds

NO_PROGRESS_CYCLES = 3
DEFAULT_MAX_CYCLES = 20
LOCK_STALE_SECONDS = 6 * 3600
SAFE_PLAN = re.compile(r"^[A-Za-z0-9._/\\:-]+$")
MINOR_TOKEN = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)$")
CMD_METACHARACTERS = set('&|<>^%!"')

# Flags that bypass approvals or override configuration. Never emitted by any
# template; the tests assert it for every row.
DENYLIST = (
    "--dangerously-skip-permissions",
    "--permission-mode",
    "bypassPermissions",
    "--dangerously-bypass-approvals-and-sandbox",
    "--full-auto",
    "danger-full-access",
    "approval_policy=never",
    "--approval-mode",
    "yolo",
    "--yolo",
    "--allow-all-tools",
    "--allow-all",
    "--force",
    "--yes-always",
)


# row id -> (launch(prompt), resume(prompt), supports a headless goal entry point).
# A headless goal is set only where the vendor documents `<cli> -p "/goal ..."`
# (docs/policy/completion-levers.json `native_goal.headless_entry`): Claude Code,
# Qwen Code, and Kimi Code CLI. Copilot CLI's documented headless path is
# `copilot --autopilot -p` with a bypass flag, not /goal, so it stays interactive.
TEMPLATES: dict[str, tuple] = {
    "claude": (
        lambda p: ["claude", "-p", p],
        lambda p: ["claude", "-p", p, "--continue"],
        True,
    ),
    "codex": (
        lambda p: ["codex", "exec", p],
        lambda p: ["codex", "exec", "resume", "--last", p],
        False,
    ),
    "cursor": (
        lambda p: ["agent", "-p", p],
        lambda p: ["agent", "--continue", "-p", p],
        False,
    ),
    "copilot": (
        lambda p: ["copilot", "-p", p],
        lambda p: ["copilot", "--continue", "-p", p],
        False,
    ),
    "copilot/cli": (
        lambda p: ["copilot", "-p", p],
        lambda p: ["copilot", "--continue", "-p", p],
        False,
    ),
    "gemini-cli": (
        lambda p: ["gemini", "-p", p],
        lambda p: ["gemini", "--resume", "latest", "-p", p],
        False,
    ),
    "antigravity2/cli": (
        lambda p: ["agy", "-p", p],
        lambda p: ["agy", "--continue", "-p", p],
        False,
    ),
    "qwen": (
        lambda p: ["qwen", "-p", p],
        lambda p: ["qwen", "--continue", "-p", p],
        True,
    ),
    "kimi": (
        lambda p: ["kimi", "-p", p],
        lambda p: ["kimi", "--continue", "-p", p],
        True,
    ),
    "opencode": (
        lambda p: ["opencode", "run", p],
        lambda p: ["opencode", "run", "-c", p],
        False,
    ),
    "windsurf/devin-cli": (
        lambda p: ["devin", "-p", p],
        lambda p: ["devin", "-c", "-p", p],
        False,
    ),
    "hermes": (
        lambda p: ["hermes", "chat", "-q", p],
        lambda p: ["hermes", "chat", "-c", "-q", p],
        False,
    ),
    "aider": (
        lambda p: ["aider", "--message", p],
        lambda p: ["aider", "--restore-chat-history", "--message", p],
        False,
    ),
    "pi": (lambda p: ["pi", "-p", p], lambda p: ["pi", "--continue", "-p", p], False),
    # OpenClaw needs a session selector on every call; SESSION is replaced with
    # the run nonce so launch and resume address the same session.
    "openclaw": (
        lambda p: ["openclaw", "agent", "--message", p, "--session-id", "SESSION"],
        lambda p: ["openclaw", "agent", "--message", p, "--session-id", "SESSION"],
        False,
    ),
}

# Extra flags on the goal-setting launch. Claude Code documents stream-json with
# --verbose so a long goal loop shows progress instead of looking stuck.
GOAL_FLAGS: dict[str, list[str]] = {"claude": ["--output-format", "stream-json", "--verbose"]}
# Kimi's prompt-mode goal exits 3 when the goal is blocked and 6 when it is paused
# (completion-levers.json `kimi.native_goal.goal_exit_codes`). Such an exit counts as
# a run, not a launch failure, only when the checker then reports BLOCKED or PAUSED;
# otherwise it is retried and, on the first cycle, recorded as platform-unavailable.
GOAL_EXITS: dict[str, set[int]] = {"kimi": {3, 6}}
# Rows whose goal command is documented for interactive use only: the runner cannot
# set it, so it prints the line for the user to type in that session.
INTERACTIVE_GOAL_ROWS = {"codex", "cursor", "copilot", "copilot/cli", "antigravity2/cli", "hermes", "openclaw"}
PLAN_VERSION = re.compile(r"^(v\d+\.\d+\.\d+)(?:-|\.md$)")


import runpy as _process_runpy
from pathlib import Path as _ProcessPath

_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[0] / "nexus_process.py"))
_PROCESS_POLICY["install_no_window_default"]()


class RunnerError(Exception):
    """Exit 2 with this message."""


def continuation_module():
    """Load the shared owner from this source tree or the common installed bundle.

    The working directory and observation file never choose executable code.
    """
    relative = Path("skills/workflow/implement-phase/scripts/continuation_state.py")
    source = SCRIPT_DIR.parent / "catalog" / relative
    installed = SCRIPT_DIR.parent / relative
    path = source if source.is_file() else installed
    if not path.is_file() or path.is_symlink():
        raise RunnerError("shared continuation resource is missing; repair the installed bundle")
    spec = importlib.util.spec_from_file_location("_nexus_continuation_state", path)
    if spec is None or spec.loader is None:
        raise RunnerError("shared continuation resource cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def continuation_path(record_path: Path) -> Path:
    return record_path.with_name(record_path.stem + ".continuation.json")


def _bounded_json(path: Path, *, with_hash: bool = False):
    """Read reporting data, refusing links and oversized or replaced files."""
    before = path.lstat()
    if path.is_symlink() or getattr(before, "st_file_attributes", 0) & 0x400:
        raise RunnerError("continuation evidence cannot be a link or reparse point")
    if before.st_size > 1024 * 1024:
        raise RunnerError("continuation evidence exceeds one MiB")
    with path.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        raw = handle.read(1024 * 1024 + 1)
    after = path.lstat()
    if ((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
            or len(raw) > 1024 * 1024):
        raise RunnerError("continuation evidence changed during observation")
    value = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(value, dict):
        raise RunnerError("continuation evidence must be an object")
    return (value, hashlib.sha256(raw).hexdigest()) if with_hash else value


def continuation_binding(scope, record_path: Path, record: dict) -> dict:
    label = scope.label if scope.minor else str((scope.repo_root / scope.label).resolve())
    return {"record_path": str(record_path.resolve()), "session_id": record.get("session_id", ""),
            "repo_root": str(scope.repo_root.resolve()), "scope": label, "run_nonce": record.get("nonce", "")}


def read_continuation(scope, record_path: Path, record: dict) -> dict | None:
    path = continuation_path(record_path)
    if not path.exists():
        return None
    frame = _bounded_json(path)
    expected = continuation_binding(scope, record_path, record)
    binding = frame.get('binding')
    if frame.get('contract') != 'implementation-continuation-v1' or not isinstance(binding, dict):
        raise RunnerError("continuation observation belongs to a different run or session")
    if (record.get('schema') == 1 and binding.get('run_nonce') is None
            and all(binding.get(key) == value for key, value in expected.items() if key not in {'run_nonce', 'session_id'})):
        import check_plan_completion as ck
        context, verified = ck.resolve_plan_controller(record_path, record.get('session_id'))
        if verified != record:
            raise RunnerError('native plan owner changed during create verification')
        results = ck.plan_owner_results(context, verified, ck.plan_issued_requests(context, verified))
        identity = 'native:' + record_path.stem + ':' + str(record.get('nonce'))
        if not any(result['request_id'] == identity for result in results):
            raise RunnerError('pre-create observation has no verified native create effect')
        if any(item.get('authorized') for item in frame.get('observation', {}).get('work', [])):
            raise RunnerError('pre-create observation carried phase authority')
        frame = copy.deepcopy(frame)
        frame['binding'] = dict(binding, run_nonce=expected['run_nonce'])
        binding = frame['binding']
        frame['capture_watermark'] = capture_watermark(record_path, verified)
    if binding != expected:
        import approval_binding
        import check_plan_completion as ck
        same_run = all(binding.get(key) == value for key, value in expected.items() if key != 'session_id')
        if not same_run or record.get('schema') not in (1, 2):
            raise RunnerError("continuation observation belongs to a different run or session")
        try:
            if record['schema'] == 2:
                _context, current = ck.resolve_minor_controller(record_path, record['session_id'],
                    minor_protocol=ck.MINOR_AMENDMENT_PROTOCOL, execution_protocol=ck.MINOR_EXECUTION_PROTOCOL)
            else:
                _context, current = ck.resolve_plan_controller(record_path, record['session_id'])
            valid = (current == record and approval_binding.continuation_ancestor_valid(
                record_path.parent, current, binding.get('session_id'), expected['session_id']))
        except (OSError, ValueError, TypeError, KeyError, ck.Malformed, ck._minor_module().ObservationUnavailable):
            valid = False
        if not valid:
            raise RunnerError("continuation observation belongs to a different run or session")
        frame = copy.deepcopy(frame)
        frame.setdefault('previous_capture_sources', []).append({'session_id': binding['session_id'],
            'watermark': frame.get('capture_watermark', '')})
        frame['binding'] = expected
        frame['capture_watermark'] = capture_watermark(record_path, current)
        frame['owner_result_watermark'] = hashlib.sha256(approval_binding.canonical(current)).hexdigest()
    return frame



def capture_watermark(record_path: Path, record: dict) -> str:
    """A genuine capture invalidates an old wait; it never grants approval here."""
    session = str(record.get("session_id") or "")
    path = record_path.parent / "prompts" / (hashlib.sha256(session.encode()).hexdigest() + ".jsonl")
    if not session or not path.is_file() or path.is_symlink():
        return ""
    if path.stat().st_size > 1024 * 1024:
        raise RunnerError("capture index exceeds one MiB; native capture review is required")
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("session") == session and event.get("event_id"):
            events.append(event)
    return str(events[-1]["event_id"]) if events else ""


def _authorization(scope, record: dict, item: dict, *, readonly: bool = False) -> bool:
    """Use the native owner; an observation's authorized flag is not consent."""
    if getattr(scope, 'observer_session', None) not in (None, record.get('session_id')):
        return False
    request = item.get("authorization")
    if not isinstance(request, dict) or not isinstance(request.get("class"), str):
        return False
    fields = request.get("request", {})
    if not isinstance(fields, dict):
        return False
    readonly = readonly or request["class"] == "supplement-v415-authority"
    if readonly:
        import check_plan_completion as ck
        from contextlib import redirect_stdout
        from io import StringIO
        args = argparse.Namespace(minor=scope.label if scope.minor else None,
            repo=str(scope.repo_root), plan=None if scope.minor else scope.label,
            session=record.get('session_id'), member=request.get('member'),
            approval_class=request['class'], request=json.dumps(fields))
        try:
            with redirect_stdout(StringIO()):
                result = ck.authorization_probe(args)
            return not isinstance(result, int) and result[2].get("execution_authorized") is not False
        except (OSError, ValueError, ck.Malformed):
            return False
    target = ["--minor", scope.label, "--repo", str(scope.repo_root)] if scope.minor else [scope.label]
    args = ["record", "authorize", *target, "--session", str(record.get("session_id", "")),
            "--approval-class", request["class"], "--request", json.dumps(fields)]
    if request.get("member"):
        args.extend(["--member", str(request["member"])])
    rc, out = _checker_run(args)
    return rc == 0 and out.startswith("AUTHORIZED ")


def _verified_result(receipt: object, expected: dict, *, not_before: float = 0) -> bool:
    """Require a fresh, hashed owner result bound to the existing item identity.

    This verifies a producer's recorded result, not a signature or an approval.
    It never executes the producer command or treats disappearance as success.
    """
    if not isinstance(receipt, dict) or not isinstance(receipt.get("path"), str):
        return False
    try:
        path = Path(receipt["path"])
        proof, digest = _bounded_json(path, with_hash=True)
        if digest != receipt.get("sha256"):
            return False
        if any(proof.get(key) != value for key, value in expected.items()):
            return False
        code = proof.get("exit_code")
        finished = dt.datetime.fromisoformat(str(proof.get("finished_at", "")).replace("Z", "+00:00"))
        return (type(code) is int and finished.tzinfo is not None
                and not_before <= finished.timestamp() <= time.time() + 5
                and (code == 0 if proof.get("status") != "failed" else code != 0))
    except (OSError, ValueError, TypeError, RunnerError):
        return False


def _reply_policy_matches(request: dict, resolution: dict, nonce: str) -> bool:
    """Fresh text must satisfy the request's original explicit reply policy."""
    policy, reply = request.get("reply_policy"), resolution.get("reply_text")
    if not isinstance(policy, dict) or not isinstance(reply, str):
        return False
    if policy.get("kind") in {"choice", "acknowledgment"}:
        choices = policy.get("choices" if policy["kind"] == "choice" else "accepted_replies")
        return (isinstance(choices, list) and bool(choices)
                and all(isinstance(item, str) and item.strip() for item in choices)
                and reply.strip().casefold() in {item.strip().casefold() for item in choices})
    if policy.get("kind") == "result_receipt" and isinstance(policy.get("predicate"), str):
        receipt = resolution.get("result_receipt")
        if not isinstance(receipt, dict) or not isinstance(receipt.get("path"), str):
            return False
        if reply.strip().strip('"') != receipt["path"]:
            return False
        return _verified_result(receipt, {"request_id": request["id"], "status": "succeeded", "predicate": policy["predicate"],
            "run_nonce": nonce}, not_before=float(request["requested_at"]))
    return False  # Native capture requires its native owner; generic Done grants nothing.


def _observe_process_jobs(observation: dict, nonce: str, native_jobs: dict | None = None) -> None:
    """Observe an exact process identity; disappearance never proves success."""
    for job in observation.get("jobs", []):
        if native_jobs is not None and job.get("id") in native_jobs and all(job.get(key) == value for key, value in native_jobs[job["id"]].items()):
            continue  # Re-observed by the verified native owner, never a serialized overlay.
        terminal = job.get("status") in {"succeeded", "failed"}
        if terminal:
            job["result_verified"] = _verified_result(job.get("result_receipt"), {
                "handle": job.get("handle") or job.get("url"), "status": job["status"], "run_nonce": nonce},
                not_before=float(job.get("job_created_at", 0)))
            if not job["result_verified"]:
                job["status"] = "observation-timeout"
                job["evidence"] = "Terminal result is not verified; retain the existing handle and obtain its bound result receipt."
        identity = job.get("process")
        if not isinstance(identity, dict):
            continue  # Native tool/pipeline handles retain their observer's evidence.
        # This timestamp describes this actual observation attempt, including an
        # unavailable observation. It must not reuse the last successful poll's time.
        job["observed_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            import psutil
            pid, created = identity["pid"], identity["created_at"]
            if type(pid) is not int or pid <= 0 or isinstance(created, bool) or not math.isfinite(float(created)):
                raise ValueError("invalid process identity")
            if job.get("handle") != f"process:{pid}:{float(created):.6f}":
                raise ValueError("process identity does not match its handle")
            process = psutil.Process(pid)
            if abs(process.create_time() - float(created)) > 0.001:
                raise ValueError("process identity changed")
            if not process.is_running() or process.status() == psutil.STATUS_ZOMBIE:
                raise ValueError("process is no longer running")
        except (ImportError, KeyError, TypeError, ValueError, OSError):
            if terminal and job.get("result_verified") is True:
                continue
            job["status"] = "observation-timeout"
            job["evidence"] = "Exact process cannot currently be verified; retain its handle and inspect its result."
            job["result_verified"] = False
        except Exception as exc:
            if terminal and job.get("result_verified") is True:
                continue
            # psutil exceptions differ by platform; unavailable observation is not completion.
            job["status"] = "observation-timeout"
            job["evidence"] = "Process observation unavailable (" + type(exc).__name__ + "); retain its handle."
            job["result_verified"] = False
        else:
            job["status"] = "running"
            job["evidence"] = f"Observed PID {pid} with matching creation time {created}."
            job["result_verified"] = False


def _external_predicate_unknowns(scope, record_path: Path, record: dict, output: str) -> bool:
    """Recognize only canonical external CI/main observations for approved members.

    This does not mark a predicate met or authorize publication. A separately
    verified local task may still proceed while those observations are unknown.
    Every native owner, context, plan and malformed observation stays fail closed.
    """
    if not scope.minor:
        return False
    lines = [line for line in output.splitlines() if 'cannot-verify' in line]
    parsed = [re.fullmatch(r'(v[0-9]+\.[0-9]+\.[0-9]+):(integration\.checks|release\.main) cannot-verify', line) for line in lines]
    if not parsed or any(match is None for match in parsed):
        return False
    import check_plan_completion as ck
    try:
        _context, verified = ck.resolve_minor_controller(record_path, str(record.get('session_id') or ''),
            minor_protocol=ck.MINOR_AMENDMENT_PROTOCOL, execution_protocol=ck.MINOR_EXECUTION_PROTOCOL)
        if (verified.get('nonce'), verified.get('session_id')) != (record.get('nonce'), record.get('session_id')):
            return False
        members = {member['version'] for member in ck._minor_module().effective_members(ck, verified)}
        return all(match.group(1) in members for match in parsed)
    except (OSError, ValueError, TypeError, KeyError, ck.Malformed, ck._minor_module().ObservationUnavailable):
        return False


def reconcile_observation(scope, record_path: Path, record: dict, observation: dict,
                          checker_rc: int, checker_out: str, previous: dict | None = None, *, readonly: bool = False) -> dict:
    """Reconcile descriptive facts without weakening native verdicts or consent."""
    if (checker_rc not in (0, 1, 3, 4)
            or any("record-tampered" in line for line in checker_out.splitlines()[:1])
            or "checker.observation" in checker_out
            or ("cannot-verify" in checker_out and not _external_predicate_unknowns(scope, record_path, record, checker_out))):
        raise RunnerError("native run authority could not be verified")
    facts = copy.deepcopy(observation)
    native = native_owner_observation(scope, record_path, record, previous,
                                      remaining_tasks=facts.get('remaining_tasks'))
    native_requests = {item['id']: item for item in (native or {}).get('requests', [])}
    native_jobs = {item['id']: item for item in (native or {}).get('jobs', []) if item.get('native_bridge')}
    facts['work'] = [item for item in facts.get('work', []) if not str(item.get('id', '')).startswith('bridge:codeql-reconcile:')]
    facts['work'].extend(copy.deepcopy([item for item in (native or {}).get('work', []) if str(item.get('id', '')).startswith('bridge:codeql-reconcile:')]))
    facts['jobs'] = [job for job in facts.get('jobs', []) if not str(job.get('id', '')).startswith('bridge:')]
    facts['jobs'].extend(copy.deepcopy(list(native_jobs.values())))
    for field, identity_key in (('external_conditions', 'id'), ('condition_resolutions', 'condition_id')):
        facts[field] = [item for item in facts.get(field, []) if not str(item.get(identity_key, '')).startswith('bridge:')]
        facts[field].extend(copy.deepcopy([item for item in (native or {}).get(field, []) if str(item.get(identity_key, '')).startswith('bridge:')]))
    for request in facts.get('requests', []):
        request.pop('native_reconciliation', None)
        if request.get('id') in native_requests:
            request.update(copy.deepcopy(native_requests[request['id']]))
    for key in ('owner_recovery', 'owner_replies'):
        facts.pop(key, None)
        if native and native.get(key):
            facts[key] = copy.deepcopy(native[key])
    facts["paused"] = checker_rc == 4  # Descriptive input cannot impersonate a genuine pause.
    facts["completion"] = {"verified": checker_rc == 0, "evidence": checker_out.strip() or "Native checker has not verified completion."}
    if checker_rc == 0:
        facts["remaining_tasks"] = 0
    prior = previous.get("disposition") if previous else None
    nonce = str(record.get("nonce", ""))
    prior_requests = {r["id"]: r for r in (prior or {}).get("requests", [])}
    for request in facts.get("requests", []):
        before = prior_requests.get(request.get("id"), {})
        if before:
            fields = ("kind", "title", "prerequisites", "steps", "expected_result", "acknowledgment",
                      "reply_policy", "options", "reply", "approval_class", "authorization")
            if any(request.get(key) != before.get(key) for key in fields):
                raise RunnerError("a pending request cannot change in place; retain it until verified resolution")
        request["requested_at"] = before.get("requested_at", time.time())
    prior_conditions = {item["id"]: item for item in (prior or {}).get("external_conditions", [])}
    for condition in facts.get("external_conditions", []):
        before = prior_conditions.get(condition.get("id"), {})
        if before and any(condition.get(key) != before.get(key) for key in ("title", "resume_when")):
            raise RunnerError("a pending external condition cannot change its identity or resumption predicate")
        condition["condition_created_at"] = before.get("condition_created_at", time.time())
    prior_jobs = {item["id"]: item for item in (prior or {}).get("jobs", [])}
    for job in facts.get("jobs", []):
        before = prior_jobs.get(job.get("id"), {})
        job["job_created_at"] = before.get("job_created_at", time.time() if job.get("status") not in {"succeeded", "failed"} else 0)
        if job.get("id") in native_jobs and "job_created_at" in native_jobs[job["id"]]:
            job["job_created_at"] = native_jobs[job["id"]]["job_created_at"]
    native_results = {r['request_id']: r for r in (native or {}).get('resolutions', [])}
    if native is not None:
        request_ids = {r['id'] for r in facts.get('requests', [])}
        facts.setdefault('requests', []).extend(r for r in native['requests'] if r['id'] not in request_ids)
        condition_ids = {r['id'] for r in facts.get('external_conditions', [])}
        facts.setdefault('external_conditions', []).extend(r for r in native.get('external_conditions', []) if r['id'] not in condition_ids)
        existing_conditions = {r.get('condition_id') for r in facts.get('condition_resolutions', [])}
        facts.setdefault('condition_resolutions', []).extend(r for r in native.get('condition_resolutions', []) if r['condition_id'] not in existing_conditions)
        facts.setdefault('resolutions', []).extend(r for r in native_results.values()
            if r['request_id'] not in {x.get('request_id') for x in facts.get('resolutions', [])})
    for resolution in facts.get("resolutions", []):
        if resolution.get('request_id') in native_results:
            resolution.update(native_results[resolution['request_id']])
            continue
        request = prior_requests.get(resolution.get("request_id"), {})
        if request.get("kind") == "decision":
            # The native record must already contain the consumed approval or authorization.
            receipt = resolution.get("authority_receipt")
            entries = [*record.get("approvals", {}).get("classes", []),
                       *record.get("approvals", {}).get("continuations", [])]
            authorization = request.get("authorization") or {}
            resolution["verified"] = bool(receipt and authorization.get("class") == request.get("approval_class") and any(
                hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == receipt
                and entry.get("class") == request.get("approval_class") for entry in entries)
                and _authorization(scope, record, request, readonly=readonly))
            if authorization.get("class") == "supplement-v415-authority":
                # The exact native consumer validates the signed receipt and current owner;
                # a supplement is never fabricated as an original approval-class entry.
                resolution["verified"] = bool(receipt and any(
                    hashlib.sha256(__import__("approval_binding").canonical(entry)).hexdigest() == receipt
                    for entry in record.get("v415_authority_receipts", []))
                    and _authorization(scope, record, request, readonly=True))
        else:
            # A fresh capture is a notification, not automatic interpretation of its answer.
            # The acknowledgment field contains instructions, not the user's answer.
            # Source-fact questions need no approval-shaped acknowledgment at all.
            reply = resolution.get("reply_text")
            digest = resolution.get("prompt_sha256")
            prompt_path = record_path.parent / "prompts" / (hashlib.sha256(str(record.get("session_id", "")).encode()).hexdigest() + ".jsonl")
            verified = False
            if request and _reply_policy_matches(request, resolution, nonce) and isinstance(reply, str) and reply.strip() and digest and prompt_path.is_file() and not prompt_path.is_symlink() and prompt_path.stat().st_size <= 1024 * 1024:
                expected_digest = hashlib.sha256(reply.replace("\r\n", "\n").replace("\r", "\n").strip().encode()).hexdigest()
                for line in prompt_path.read_text(encoding="utf-8").splitlines():
                    try:
                        event = json.loads(line)
                        verified = verified or (event.get("session") == record.get("session_id")
                            and event.get("prompt") == digest == expected_digest
                            and event.get("event_id") == resolution.get("capture_event_id")
                            and float(event.get("at", 0)) > float(request.get("requested_at", (previous or {}).get("captured_at", time.time()))))
                    except (ValueError, TypeError):
                        continue
            resolution["verified"] = verified
    native_conditions = {r['condition_id']: r for r in (native or {}).get('condition_resolutions', [])}
    for resolution in facts.get("condition_resolutions", []):
        if resolution.get('condition_id') in native_conditions:
            resolution.update(native_conditions[resolution['condition_id']])
            continue
        conditions = {item["id"]: item for item in [*(prior or {}).get("external_conditions", []),
                                                   *facts.get("external_conditions", [])]}
        condition = conditions.get(resolution.get("condition_id"), {})
        resolution["verified"] = _verified_result(resolution.get("verification_receipt"), {
            "condition_id": resolution.get("condition_id"), "status": "succeeded",
            "resume_when": condition.get("resume_when"), "run_nonce": nonce},
            not_before=float(condition.get("condition_created_at", time.time()))) and bool(condition)
    for work in facts.get("work", []):
        if work.get("authorized") is True and work.get("feasible") is True:
            # INCOMPLETE has the existing implementation authority. A signed blocker
            # permits only a separately covered action, never blanket reactivation.
            work["authorized"] = (getattr(scope, "observer_session", None) in (None, record.get("session_id"))
                and (checker_rc == 1 or _authorization(scope, record, work, readonly=readonly)))
    _observe_process_jobs(facts, nonce, native_jobs)
    disposition = continuation_module().reconcile(facts, prior)
    if facts.get('objective_complete') is False:
        disposition['objective_complete'] = False
        disposition['objective_source'] = facts.get('objective_source', 'unverified')
    facts.update(requests=disposition["requests"], jobs=disposition["jobs"],
                 external_conditions=disposition["external_conditions"], resolutions=[], condition_resolutions=[])
    frame = {"contract": "implementation-continuation-v1",
            "binding": continuation_binding(scope, record_path, record),
            "observation": facts, "disposition": disposition,
            "checker": {"exit_code": checker_rc, "verdict": checker_out.splitlines()[0] if checker_out else ""},
            "captured_at": time.time(), "capture_watermark": capture_watermark(record_path, record)}
    for key in ('previous_capture_sources', 'owner_result_watermark'):
        if previous and key in previous:
            frame[key] = copy.deepcopy(previous[key])
    return frame


def save_continuation(record_path: Path, frame: dict) -> None:
    path = continuation_path(record_path)
    if path.exists():
        _bounded_json(path)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(frame, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def cmd_reconcile(target: str, observations: str, *, observer_session: str | None = None) -> int:
    scope = Scope(target)
    scope.observer_session = observer_session
    rc, out = _checker_run(scope.path())
    if rc != 0:
        raise RunnerError("native run record is required before reconciliation")
    record_path = Path(out.strip())
    record = _bounded_json(record_path)
    if scope.minor:
        ctx, record = _verified_runner_minor(record_path, record)
        scope.repo_root = ctx.root
    checker_rc, checker_out = _checker_run(scope.check())
    previous = read_continuation(scope, record_path, record)
    frame = reconcile_observation(scope, record_path, record, _bounded_json(Path(observations)),
                                  checker_rc, checker_out, previous)
    if observer_session in (None, record.get('session_id')):
        save_continuation(record_path, frame)
    print(json.dumps(frame, ensure_ascii=True))
    return 0


def reporting_module(name: str):
    """Load a fixed shared reporting owner, never a path from an observation."""
    if name not in {'status_report', 'status_snapshot'}:
        raise RunnerError('unknown reporting resource')
    relative = Path('skills/workflow/implement-phase/scripts') / (name + '.py')
    source = SCRIPT_DIR.parent / 'catalog' / relative
    path = source if source.is_file() else SCRIPT_DIR.parent / relative
    if not path.is_file() or path.is_symlink():
        raise RunnerError('shared reporting resource is missing')
    spec = importlib.util.spec_from_file_location('_nexus_' + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_owner_rounds(*, record_path: Path, scope_label: str, rounds: list[dict],
                         results: list[dict], previous: dict | None, observation: dict,
                         secret: bytes, owner_session: str | None = None) -> dict:
    """Classify verified owner facts without loading, creating or authorizing a run.

    The native backend owns context/signature validation, task measurement and
    result proof. This shared factory owns only UI decisions, required capture
    actions, declines and the existing unsigned continuation observation.
    """
    import approval_binding
    facts = copy.deepcopy(observation)
    facts.pop('owner_recovery', None)
    facts.pop('owner_replies', None)
    known_answers = [(row, row.get('decision_answer')) for row in rounds
        if approval_binding.question_decision_valid(record_path.parent, row)
        and row.get('decision_answer', {}).get('choice') == 'Approve']
    resolved = {r['request_id'] for r in (previous or {}).get('disposition', {}).get('resolved_requests', [])}
    existing = {r['id'] for r in facts['requests']}
    owner_results = {result['request_id']: result for result in results}
    resolutions, recovery, replies, condition_resolutions = [], [], [], []
    conditions = {row['id'] for row in facts.get('external_conditions', [])}
    for pending in rounds:
        identity = 'native:' + record_path.stem + ':' + pending['nonce']
        decision_id = identity + ':decision'
        for request in facts['requests']:
            if request['id'] in {identity, decision_id}:
                request.pop('native_reconciliation', None)
        label = pending['action'] + (' for ' + pending['page']['member'] if pending['page'].get('member') else '')
        review = approval_page.render_page(approval_page.render_data(pending, scope=scope_label, blocker=None, display=pending.get('render_context', {}).get('display')))
        action = {'id': identity, 'kind': 'action', 'title': 'Record the reviewed native ' + label + ' choice',
            'requested_at': pending['issuance']['observed_at'],
            'prerequisites': ['Review the exact native scope shown in this required-action section.',
                              'Stay in the conversation where this reviewed page was shown.'],
            'steps': ['Use the native capture method in this same conversation.',
                      'Send this exact line as your complete message: ' + pending['paste_lines'][0]],
            'expected_result': 'The host captures the message, then the controller completes the exact native owner operation.',
            'acknowledgment': 'The exact message is the acknowledgment. Do not submit it a second time.',
            'review_page': review, 'native_round': {'key': record_path.stem, 'nonce': pending['nonce'], 'action': pending['action']}}
        decision = dict(action, id=decision_id, kind='decision', title='Choose whether to ' + label,
            manual_capture=True, options=[{'option': 'Approve', 'effect': 'Choose only the exact reviewed scope.'},
                {'option': 'Decline', 'effect': 'Leave that action unapproved.'}],
            reply='Choose Approve or Decline. A UI choice grants no native permission until its required capture completes.')
        decision['steps'] = ['Choose Approve or Decline using the displayed choices.',
            'If you choose Approve and native capture is still required, send this exact line as your complete message: ' + pending['paste_lines'][0]]
        answer = pending.get('decision_answer') if approval_binding.question_decision_valid(record_path.parent, pending) else None
        if answer is None and owner_session == pending.get('session'):
            # An authenticated prior UI answer can inform presentation of the
            # identical requested effect. It never grants native authority.
            answer = next((prior for row, prior in known_answers
                if row.get('session') != owner_session
                and approval_binding.canonical(row['page']) == approval_binding.canonical(pending['page'])), None)
        result = owner_results.get(identity)
        targets = []
        if pending['action'] == 'resume':
            targets = [action]
        elif identity in existing:
            targets = [action]
        elif decision_id not in resolved:
            targets = [decision]
        if answer is not None and result is None:
            if decision_id not in resolved:
                targets = [decision]
                resolutions.append({'request_id': decision_id, 'verified': True,
                    'authority_receipt': hashlib.sha256(approval_binding.canonical(answer)).hexdigest(),
                    'evidence': 'The genuine bound host question was answered ' + answer['choice'] + '; native permission was not granted by this UI observation.'})
            if answer['choice'] == 'Approve':
                if identity not in resolved:
                    targets.append(action)
            else:
                declined = identity + ':declined'
                if declined not in conditions:
                    facts['external_conditions'].append({'id': declined, 'title': 'The reviewed native scope was declined',
                        'evidence': 'The owner declined the exact reviewed question; host call ' + answer['question_call_id'] + '. No native permission was granted.',
                        'observed_at': dt.datetime.fromtimestamp(answer['source']['at'], dt.timezone.utc).isoformat(),
                        'resume_when': 'The owner explicitly reopens this scope and its native owner verifies any required new capture.'})
        for request in targets:
            if request['id'] not in existing and request['id'] not in resolved:
                facts['requests'].append(request)
                existing.add(request['id'])
        if result is not None:
            for request_id in (identity, decision_id):
                if request_id in existing and request_id not in resolved:
                    resolutions.append(dict(result, request_id=request_id))
            declined = identity + ':declined'
            if declined in conditions:
                condition_resolutions.append({'condition_id': declined, 'verified': True,
                    'evidence': 'The native owner now verifies the exact signed permission and consumed capture after the earlier decline.'})
            continue
        context = approval_binding.consumed_issued_request(record_path.parent, record_path.stem, secret, pending)
        outcome, reason, reply = None, None, None
        if context is not None:
            outcome = 'capture-consumed-effect-unverified'
            reason = 'The native capture is consumed, but its signed owner effect is not verified. Controller recovery is required; do not submit the approval again.'
        elif (owner_session is not None and pending.get('session') != owner_session
                and not (pending['action'] == 'resume'
                    and (active_resume := approval_binding.resume_target(record_path.parent, secret, pending['session'])) is not None
                    and active_resume[0] == record_path.stem and active_resume[1]['nonce'] == pending['nonce'])):
            outcome = 'owner-session-changed'
            reason = 'The issued round belongs to the prior session. The current native owner must reconcile or supersede its capture binding; do not submit the obsolete approval line. Any genuine prior choice is retained for the identical reviewed effect.'
        else:
            reply = approval_binding.pending_native_reply(record_path.parent, record_path.stem, pending)
            if reply is not None:
                outcome = 'reply-captured-operation-pending'
                reason = 'The exact native reply is already captured. The controller must consume it through its native owner; no further owner choice or repeated paste is required.'
        if outcome is not None:
            provenance = {'key': record_path.stem, 'run_nonce': pending['page'].get('record_nonce'),
                'round_nonce': pending['nonce'], 'round_seal': pending['mac'],
                'page_sha256': hashlib.sha256(approval_binding.canonical(pending['page'])).hexdigest(),
                'issued_session': pending.get('session'), 'owner_session': owner_session,
                'outcome': outcome, 'capture': context or reply}
            metadata = {'outcome': outcome, 'reason': reason,
                'evidence': 'Verified native request and current owner binding. No permission was granted and the native operation remains outstanding.',
                'resume_when': 'The native owner verifies the exact persisted effect or a provenance-bound replacement capture.',
                'provenance_sha256': hashlib.sha256(approval_binding.canonical(provenance)).hexdigest()}
            if answer is not None:
                metadata['prior_ui_choice'] = answer['choice']
                metadata['prior_ui_choice_sha256'] = hashlib.sha256(approval_binding.canonical(answer)).hexdigest()
            for request in facts['requests']:
                if request['id'] in {identity, decision_id}:
                    request['native_reconciliation'] = metadata
            item = {'request_id': identity, 'reason': reason, 'provenance': provenance}
            if reply is not None:
                replies.append(dict(item, capture=reply))
            else:
                recovery.append(item)
    facts['resolutions'] = resolutions
    facts['condition_resolutions'] = condition_resolutions
    if recovery:
        facts['owner_recovery'] = recovery
    if replies:
        facts['owner_replies'] = replies
    return facts


def _plan_owner_facts(context, previous: dict | None, remaining_tasks: int | None) -> dict:
    facts = copy.deepcopy(previous['observation']) if previous else {}
    facts['remaining_tasks'] = remaining_tasks if remaining_tasks is not None else sum(not done for _tid, done, _path in context.tasks)
    facts.setdefault('objective', 'Complete the approved plan ' + context.rel + ' (' + context.version + ')')
    facts.setdefault('objective_complete', False)
    facts.setdefault('objective_source', 'verified-native-plan; additional user wording has not been recovered')
    for key in ('work', 'requests', 'jobs', 'external_conditions'):
        facts.setdefault(key, [])
    return facts


def precreate_owner_observation(scope, record_path: Path, metadata: dict, previous: dict | None) -> dict | None:
    """Project a delivered create obligation without a record or phase authority."""
    import check_plan_completion as ck
    import approval_binding
    resolved = ck.precreate_owner_context(str(metadata.get('session_id') or ''))
    if resolved is None:
        return None
    context, expected_path, verified_metadata = resolved
    if record_path.resolve() != expected_path.resolve() or metadata != verified_metadata or scope.repo_root.resolve() != context.root.resolve():
        raise RunnerError('pre-create owner identity mismatch')
    secret = ck._secret(False)
    issued = approval_binding.issued_requests(record_path.parent, record_path.stem, secret, metadata)
    if not issued:
        return None
    facts = _plan_owner_facts(context, previous, None)
    if any(item.get('authorized') for item in facts['work']):
        raise RunnerError('pre-create observation cannot authorize phase work')
    return project_owner_rounds(record_path=record_path, scope_label=context.version, rounds=issued,
        results=[], previous=previous, observation=facts, secret=secret, owner_session=metadata['session_id'])


def native_owner_observation(scope, record_path: Path, record: dict, previous: dict | None,
                             *, remaining_tasks: int | None = None) -> dict | None:
    """Recover delivered native requests and exact signed results without model JSON.

    The sealed question marker is the existing native owner's issuance record;
    a pending render is deliberately insufficient. This reads no provider keys,
    starts no job and writes no signed state.
    """
    import approval_binding
    import check_plan_completion as ck
    if record.get('schema') == 1:
        context, verified = ck.resolve_plan_controller(record_path, str(record.get('session_id') or ''))
        if verified != record or scope.repo_root.resolve() != context.root.resolve():
            raise RunnerError('native plan owner identity changed')
        issued = ck.plan_issued_requests(context, verified, observer_session=getattr(scope, 'observer_session', None))
        if not issued:
            return None
        facts = _plan_owner_facts(context, previous, remaining_tasks)
        facts['paused'] = bool(verified.get('pause'))
        if getattr(scope, 'observer_session', None) not in (None, verified.get('session_id')):
            for work in facts.get('work', []):
                work['authorized'] = False
            facts['completion'] = {'verified': False, 'evidence': 'Native ownership still belongs to the previous session; the observing host must complete the exact resume capture first.'}
        return project_owner_rounds(record_path=record_path, scope_label=context.version, rounds=issued,
            results=ck.plan_owner_results(context, verified, issued), previous=previous,
            observation=facts, secret=ck._secret(False), owner_session=verified['session_id'])
    secret = ck._secret(create=False)
    if not secret:
        return None
    issued = approval_binding.issued_requests(record_path.parent, record_path.stem, secret, record,
        observer_session=getattr(scope, 'observer_session', None))
    if not issued and not record.get("v415_authority_receipts"):
        return None
    import hmac
    if not hmac.compare_digest(str(record.get('approvals_hmac', '')), ck._sign(record, secret,
            minor_protocol=ck.MINOR_AMENDMENT_PROTOCOL, execution_protocol=ck.MINOR_EXECUTION_PROTOCOL)):
        raise RunnerError('native owner record signature could not be verified')
    try:
        context, verified = ck.resolve_minor_controller(record_path, str(record.get('session_id') or ''),
            minor_protocol=ck.MINOR_AMENDMENT_PROTOCOL, execution_protocol=ck.MINOR_EXECUTION_PROTOCOL)
    except (OSError, ValueError, TypeError, ck.Malformed, ck._minor_module().ObservationUnavailable) as exc:
        raise RunnerError('native owner operational binding could not be verified') from exc
    if (verified.get('nonce'), verified.get('session_id')) != (record.get('nonce'), record.get('session_id')):
        raise RunnerError('native owner changed during operational verification')
    if scope.repo_root.resolve() != context.root.resolve():
        report_context = ck.RepoContext(scope.repo_root, ck.Budget(10))
        if ck._minor_module()._common_dir(report_context, scope.repo_root) != ck._minor_module()._common_dir(context, context.root):
            raise RunnerError('report repository differs from the verified operational owner')
    record = verified
    facts = copy.deepcopy(previous['observation']) if previous else {}
    if record.get("v415_authority_receipts"):
        facts["authority_bridge"] = ck._minor_module().authority_bridge_projection(ck, record)
        previous_jobs = facts.get("jobs", [])
        cached_jobs = [*previous_jobs, *(previous or {}).get("disposition", {}).get("completed_jobs", [])]
        facts["jobs"] = [job for job in previous_jobs if not str(job.get("id", "")).startswith("bridge:")]
        bridge_jobs = ck._minor_module().authority_bridge_jobs(ck, context, record, cached_jobs)
        codeql_reads = ck._minor_module().authority_bridge_read_state(ck, context, record, cached_jobs)
        bridge_jobs.extend(codeql_reads["jobs"])
        facts["work"] = [item for item in facts.get("work", []) if not str(item.get("id", "")).startswith("bridge:codeql-reconcile:")]
        facts["work"].extend(codeql_reads["work"])
        facts["jobs"].extend(bridge_jobs)
        conditions, resolutions = ck._minor_module().authority_bridge_host_failures(ck, context, record, bridge_jobs, (previous or {}).get("disposition", {}).get("external_conditions", []))
        conditions.extend(codeql_reads["external_conditions"])
        resolutions.extend(codeql_reads["condition_resolutions"])
        facts["external_conditions"] = [item for item in facts.get("external_conditions", []) if not str(item.get("id", "")).startswith("bridge:")] + conditions
        facts["condition_resolutions"] = [item for item in facts.get("condition_resolutions", []) if not str(item.get("condition_id", "")).startswith("bridge:")] + resolutions
    if remaining_tasks is None and 'remaining_tasks' not in facts:
        reporter = reporting_module('status_snapshot')
        repository = reporter.Repo(context.root, 'develop')
        approved = ck._minor_module().effective_members(ck, record)
        plans = {member['version']: context.root / (member.get('archived', {}).get('plan_path') or member['plan_path']) for member in approved}
        if not plans:
            raise RunnerError('native request recovered; remaining task measurement is unavailable')
        remaining_tasks = sum(reporter.measure_row(repository, version, path,
            dt.datetime.now(dt.timezone.utc), None, {})['_open'] for version, path in plans.items())
    if remaining_tasks is not None:
        facts['remaining_tasks'] = remaining_tasks
    if 'objective' not in facts:
        members = ck._minor_module().effective_members(ck, record)
        facts['objective'] = approval_page.goal_line(scope.label) + ' Approved members: ' + ', '.join(
            member['version'] + ' (' + member['plan_path'] + ')' for member in members)
        facts['objective_complete'] = False
        facts['objective_source'] = 'verified-native-scope; additional user wording has not been recovered'
    if previous and not record.get("v415_authority_receipts") and all('native:' + record_path.stem + ':' + pending['nonce'] in {
            r['request_id'] for r in previous.get('disposition', {}).get('resolved_requests', [])} for pending in issued):
        return None
    facts.setdefault('work', [])
    facts.setdefault('requests', [])
    facts.setdefault('jobs', [])
    facts.setdefault('external_conditions', [])
    if getattr(scope, 'observer_session', None) not in (None, record.get('session_id')):
        for work in facts.get('work', []):
            work['authorized'] = False
        facts['completion'] = {'verified': False, 'evidence': 'Native ownership still belongs to the previous session; the observing host must complete the exact resume capture first.'}
    projected = project_owner_rounds(record_path=record_path, scope_label=scope.label, rounds=issued,
        results=ck._minor_module().continuation_owner_results(ck, record, issued), previous=previous,
        observation=facts, secret=secret, owner_session=record.get('session_id'))
    if record.get("v415_authority_receipts"):
        projected['condition_resolutions'].extend(resolutions)
    return projected


def _owner_refresh_claim(scope, record_path: Path, record: dict, fingerprint: str, claim: bool) -> bool:
    """Claim one real native-result refresh using the existing unsigned gate file.

    A sidecar may not yet exist after issuance was saved but reconciliation
    failed. The claim must survive that causal path without inventing work.
    """
    import check_plan_completion as ck
    import completion_gate
    path = record_path.with_name(record_path.stem + '.continuation.gate.json')
    with ck._minor_os_lock(path.with_suffix('.mutation.lock'), ck.Budget(3)):
        state = _bounded_json(path) if path.exists() else {}
        binding = continuation_binding(scope, record_path, record)
        owner = state.get('owner_refresh', {})
        attempts = owner.get('attempts', []) if owner.get('binding') == binding else []
        if not isinstance(attempts, list) or any(not isinstance(item, str) for item in attempts):
            raise RunnerError('native owner refresh claims are malformed')
        already = fingerprint in attempts
        if claim and not already:
            state['owner_refresh'] = {'binding': binding, 'attempts': [*attempts[-63:], fingerprint]}
            completion_gate._save_gate_state(path, state)
        return already


def continuation_for_run(scope, record_path: Path, record: dict, rc: int, out: str,
                         *, claim_refresh: bool = False) -> dict | None:
    may_save = getattr(scope, 'observer_session', None) in (None, record.get('session_id'))
    previous = read_continuation(scope, record_path, record)
    fresh = _bounded_json(record_path)
    if (fresh.get('nonce'), fresh.get('session_id')) != (record.get('nonce'), record.get('session_id')):
        raise RunnerError('native owner changed during continuation observation')
    record = fresh
    native = native_owner_observation(scope, record_path, record, previous)
    if native is not None:
        try:
            frame = reconcile_observation(scope, record_path, record, native, rc, out, previous, readonly=True)
        except ValueError as exc:
            # A new native result can require real controller observations before
            # the seven-state owner can derive another disposition. Claim one
            # refresh, never manufacture feasible work or an external blocker.
            unfinished = ('unfinished implementation requires' in str(exc)
                or 'task marks alone do not establish verified completion' in str(exc))
            if not unfinished:
                raise
            for key, prefix, label in (('owner_replies', 'owner-reply:', 'capture consumption'),
                                       ('owner_recovery', 'owner-recovery:', 'recovery')):
                if native.get(key):
                    fingerprint = prefix + hashlib.sha256(__import__('approval_binding').canonical(native[key])).hexdigest()
                    claimed = _owner_refresh_claim(scope, record_path, record, fingerprint, claim_refresh)
                    return {'state': 'reconciliation_required', 'directive': 'wait' if claimed else 'continue',
                        'reason': 'Waiting for controller ' + label + ': ' + native[key][0]['reason'],
                        'fingerprint': fingerprint}
            if not native.get('resolutions'):
                raise
            fingerprint = 'owner-result:' + hashlib.sha256(__import__('approval_binding').canonical(native['resolutions'])).hexdigest()
            if _owner_refresh_claim(scope, record_path, record, fingerprint, claim_refresh):
                return {'state': 'reconciliation_required', 'directive': 'wait',
                    'reason': 'Waiting for controller reconciliation: the native owner result is verified, but remaining work has not been reconciled. No owner reply or duplicate capture is requested.',
                    'fingerprint': fingerprint}
            return {'state': 'reconciliation_required', 'directive': 'continue',
                'reason': 'The native owner result is verified. Reconcile actual remaining authorized tasks, live jobs and dependencies now, then continue feasible work. Do not request the captured approval again.',
                'fingerprint': fingerprint}
        if may_save:
            save_continuation(record_path, frame)
        return frame['disposition']
    if previous is None:
        return None
    if rc in (0, 4):
        # Completion cannot silently discard requests belonging to the full
        # objective. The shared owner rejects contradictory completion evidence.
        frame = reconcile_observation(scope, record_path, record, previous["observation"], rc, out, previous, readonly=True)
        if may_save:
            save_continuation(record_path, frame)
        return frame["disposition"]
    # A genuine new reply needs a fresh owner reconciliation, even when a stale
    # native marker still says blocked. It is not an approval or completed task.
    watermark = capture_watermark(record_path, record)
    if watermark and watermark != previous.get("capture_watermark", ""):
        attempted = previous.get("refresh_attempts", [])
        if watermark in attempted:
            return {"state": "reconciliation_required", "directive": "wait",
                "reason": "Waiting for controller reconciliation: the captured reply received one refresh attempt, but its owner has not published a verified resolution. No further owner reply or duplicate run is requested.",
                "fingerprint": "reply-attempted:" + watermark}
        if claim_refresh and may_save:
            previous["refresh_attempts"] = [*attempted[-63:], watermark]
            save_continuation(record_path, previous)
        return {"state": "reconciliation_required", "directive": "continue",
                "reason": "A new user reply arrived. Consume it through its owner, refresh the run state, and continue authorized work.",
                "fingerprint": "reply:" + watermark, "refresh_event_id": watermark}
    frame = reconcile_observation(scope, record_path, record, previous["observation"], rc, out, previous, readonly=True)
    return frame["disposition"]


def waiting_line(disposition: dict) -> str:
    state, reason = disposition["state"], disposition["reason"]
    if state in {"waiting_owner_action", "waiting_decision"}:
        return "Waiting for you: " + reason
    if state in {"waiting_job", "blocked_external"}:
        return "Waiting for " + reason
    return reason


def continuation_progress(disposition: dict) -> str:
    """Counter identity excludes cosmetic descriptions and observation timestamps."""
    data = {"state": disposition["state"],
            "work": sorted((item["id"], item["authorized"], item["feasible"])
                           for item in disposition.get("work", [])),
            "resolutions": [(item.get("request_id"), item.get("authority_receipt"), item.get("capture_event_id"))
                            for item in disposition.get("resolved_requests", [])],
            "results": [(item.get("id"), item.get("handle"), item.get("url"), item.get("status"),
                         item.get("result_receipt", {}).get("sha256"))
                        for item in disposition.get("completed_jobs", [])],
            "reply": disposition.get("fingerprint", "") if disposition["state"] == "reconciliation_required" else ""}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def runner_usage_stop(scope, row: str) -> bool:
    """Honor the existing usage owner's pending decision without refreshing telemetry."""
    directory = {"claude": ".claude", "codex": ".codex", "cursor": ".cursor"}.get(row)
    if directory is None:
        return False
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    raw = os.environ.get("NEXUS_GATE_HOOK_DIR")
    candidate = Path(raw) if raw else home / directory / "hooks"
    if not (candidate / "usage-guard.py").is_file():
        return False
    import completion_gate
    try:
        os.environ["NEXUS_GATE_HOOK_DIR"] = str(candidate)
        loaded = completion_gate._usage_guard(scope.repo_root)
    finally:
        if raw is None:
            os.environ.pop("NEXUS_GATE_HOOK_DIR", None)
        else:
            os.environ["NEXUS_GATE_HOOK_DIR"] = raw
    if loaded is None:
        return False
    guard, _directory = loaded
    try:
        pending = guard.pending_decision(row, {"cwd": str(scope.repo_root)}, (scope.repo_root,))
        if not pending:
            return False
        exhausted = pending.get("decision") == "credits" and (pending.get("current_credit", pending.get("credit")) or {}).get("state") == "exhausted"
        return ((pending.get("decision") in {"pending", "wait", "handoff"} or exhausted)
                and guard._decision_active(pending, [], time.time()))
    except (OSError, ValueError, TypeError, AttributeError):
        return False  # No new usage authority or changed threshold is inferred.


def _checker() -> Path:
    override = os.environ.get("NEXUS_RUNNER_CHECKER")
    return Path(override) if override else SCRIPT_DIR / "check_plan_completion.py"


def _checker_run(args: list[str]) -> tuple[int, str]:
    timeout = 120.0
    if args and args[0] in ("check-minor", "score-minor"):
        timeout = check_minor_seconds() + 5.0
    try:
        proc = subprocess.run(
            [sys.executable, str(_checker()), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        if args and args[0] in ("check", "check-minor"):
            return 1, "INCOMPLETE: checker.observation\nchecker.observation cannot-verify\n"
        return -1, ""
    return proc.returncode, proc.stdout


def progress_score(code: int, out: str) -> int | None:
    """Only a successfully observed numeric score can establish lack of progress."""
    fields = out.split()
    if code != 0 or len(fields) < 2 or not fields[0].isascii() or not fields[0].isdigit() or fields[1] == "-":
        return None
    return int(fields[0])


def validate_plan(plan: str) -> Path:
    if not SAFE_PLAN.match(plan):
        raise RunnerError(
            "plan path contains characters outside [A-Za-z0-9._/-]; refusing"
        )
    path = Path(plan)
    parts = path.as_posix().split("/")
    if path.suffix != ".md" or "plans" not in parts[:-1] or "docs" not in parts:
        raise RunnerError("plan must be a docs/**/plans/*.md file")
    if not path.is_file():
        raise RunnerError(f"plan not found: {plan}")
    return path


def _which_on_path(name: str) -> str | None:
    """Find `name` on PATH's absolute entries only, never in the current directory.

    `shutil.which` on Windows searches the current directory first, so a `claude.cmd`
    planted at the repository root would be launched as the platform CLI. Same rule
    as `repo_host._which_on_path`; kept local so the runner has no import
    dependency on the checker it invokes as a subprocess.
    """
    exts = [""]
    if os.name == "nt":
        exts = [e.lower() for e in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if e]
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        base = Path(entry)
        if not entry or not base.is_absolute():
            continue
        for ext in exts:
            candidate = base / (name + ext)
            if candidate.is_file() and (os.name == "nt" or os.access(candidate, os.X_OK)):
                return str(candidate)
    return None


def resolve_binary(argv0: str) -> str:
    found = _which_on_path(argv0)
    if not found:
        raise RunnerError(
            f"{argv0} is not installed or not on PATH; install the platform CLI first"
        )
    return found


def check_argv(argv: list[str]) -> None:
    """Refuse cmd metacharacters when the binary is a Windows .cmd/.bat shim.

    CreateProcess routes .cmd files through cmd.exe, which re-parses arguments,
    so an argument array is no longer shell-free there.
    """
    lowered = argv[0].lower()
    if lowered.endswith((".cmd", ".bat")):
        bad = [a for a in argv[1:] if CMD_METACHARACTERS & set(a)]
        if bad:
            raise RunnerError("refusing to pass cmd metacharacters through a .cmd shim")
    for arg in argv:
        if any(flag == arg or flag in arg.split("=") for flag in DENYLIST):
            raise RunnerError(f"refusing denylisted argument: {arg}")


# row -> (format, user-scope files under home, project-scope files under the launch
# directory, {key: values that remove approval}). Scopes are the documented ones in
# docs/policy/platform-defaults-levers.md: Claude `.claude/settings.json` and
# `.claude/settings.local.json`; Codex `.codex/config.toml` (trusted projects may
# override approval_policy and sandbox_mode since 2026-10-01); Gemini CLI and Qwen
# `.gemini/settings.json` / `.qwen/settings.json`; Cursor CLI's project file holds
# permissions only, so only its global `cli-config.json` is read. Copilot, OpenCode,
# and Kimi document no approval key a file can set, so they have no row here.
BYPASS_SETTINGS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...], dict[str, set[str]]]] = {
    "claude": (
        "json",
        (".claude/settings.json",),
        (".claude/settings.json", ".claude/settings.local.json"),
        {"defaultMode": {"bypassPermissions"}},
    ),
    "codex": (
        "toml",
        (".codex/config.toml",),
        (".codex/config.toml",),
        {"approval_policy": {"never"}, "sandbox_mode": {"danger-full-access"}},
    ),
    "gemini-cli": (
        "json",
        (".gemini/settings.json",),
        (".gemini/settings.json",),
        {"approvalMode": {"yolo"}, "defaultApprovalMode": {"yolo"}},
    ),
    "qwen": ("json", (".qwen/settings.json",), (".qwen/settings.json",), {"approvalMode": {"yolo"}}),
    "cursor": ("json", (".cursor/cli-config.json",), (), {"approvalMode": {"unrestricted"}}),
}


def _load_toml(text: str) -> object:
    try:
        import tomllib  # Python 3.11+
    except ImportError:  # pragma: no cover - installers still support 3.10
        import tomli as tomllib  # type: ignore[no-redef]  # ImportError falls through to the text scan
    return tomllib.loads(text)


def _has_bypass(node: object, keys: dict[str, set[str]]) -> bool:
    """True when any nested mapping sets one of `keys` to a bypassing value.
    Nested keys count everywhere (a Codex profile table, Claude's `permissions`):
    reporting a bypass that might not be active only asks for the approval."""
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(value, str) and value in keys.get(key, ()):
                return True
            if _has_bypass(value, keys):
                return True
    elif isinstance(node, list):
        return any(_has_bypass(item, keys) for item in node)
    return False


def _text_has_bypass(text: str, keys: dict[str, set[str]]) -> bool:
    """Fallback for a file that does not parse: match either quote style, so an
    unparseable file can never hide a bypass the parser would have found."""
    return any(
        re.search(rf"""["']?{re.escape(key)}["']?\s*[:=]\s*["']{re.escape(value)}["']""", text)
        for key, values in keys.items()
        for value in values
    )


def bypass_configured(row: str, launch_dir: Path | None = None) -> str | None:
    """Return a reason when the platform's own configuration, at user scope or in
    the project the runner launches from, bypasses approvals."""
    if row not in BYPASS_SETTINGS:
        return None
    fmt, user_files, project_files, keys = BYPASS_SETTINGS[row]
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    project = launch_dir or Path.cwd()
    candidates = [home / rel for rel in user_files] + [project / rel for rel in project_files]
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            # An unreadable config cannot declare a bypass; the next candidate is checked.
            continue
        try:
            found = _has_bypass(_load_toml(text) if fmt == "toml" else json.loads(text), keys)
        except (ImportError, ValueError):
            # ValueError covers JSONDecodeError and TOMLDecodeError.
            found = _text_has_bypass(text, keys)
        if found:
            return f"{path} bypasses approvals"
    return None


def goal_prompt(scope: str) -> str | None:
    """The approval page's goal line without an approval code, or None when the
    scope is not a version token. Runner-launched sessions are never captured, so
    the line sets only the goal; the checker stays the authority on done."""
    try:
        return approval_page.goal_line(scope)
    except approval_page.PageError:
        return None


class Scope:
    """The checker arguments for one plan or one minor; everything else in the loop is shared."""

    def __init__(self, target: str) -> None:
        self.minor = bool(MINOR_TOKEN.match(target))
        self.repo_root = Path.cwd().resolve()
        self.label = target if self.minor else validate_plan(target).as_posix()
        found = PLAN_VERSION.match(Path(self.label).name)
        self.version = target if self.minor else (found.group(1) if found else "")

    def path(self) -> list[str]:
        return ["record", "path", "--minor", self.label, "--repo", str(self.repo_root)] if self.minor else ["record", "path", self.label]

    def check(self) -> list[str]:
        return ["check-minor", self.label, "--repo", str(self.repo_root)] if self.minor else ["check", self.label]

    def score(self) -> list[str]:
        return ["score-minor", self.label, "--repo", str(self.repo_root)] if self.minor else ["score", self.label]

    def block(self, category: str, evidence: str) -> list[str]:
        scope = ["--minor", self.label, "--repo", str(self.repo_root)] if self.minor else [self.label]
        return ["record", "block", *scope, "--category", category, "--evidence", evidence]


class Lock:
    def __init__(self, record: Path) -> None:
        self.path = record.with_name(record.stem + ".runner.lock")
        self.held = False
        self.identity: tuple[int, int] | None = None
        self.pid_written = False

    def __enter__(self) -> Lock:  # noqa: PYI034 - typing.Self needs 3.11; installers support 3.10
        try:
            if (
                self.path.exists()
                and time.time() - self.path.stat().st_mtime > LOCK_STALE_SECONDS
            ):
                self.path.unlink()
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise RunnerError("another runner already holds this run record") from exc
        try:
            info = os.fstat(fd)
            self.identity = (info.st_dev, info.st_ino)
            self.held = True
            payload = str(os.getpid()).encode('ascii')
            if os.write(fd, payload) != len(payload):
                raise OSError('incomplete runner lock write')
            self.pid_written = True
        finally:
            os.close(fd)
        return self

    def refresh(self) -> None:
        """Mark the lock live; called every cycle so a long run never looks stale."""
        if self.held:
            try:
                os.utime(self.path)
            except OSError:
                # Best effort: a lock that cannot be touched only risks looking stale later.
                pass

    def __exit__(self, *_exc: object) -> None:
        # PID text alone cannot distinguish a replaced file from the one we created.
        if not self.held or self.identity is None:
            return
        try:
            entry = self.path.lstat()
            if (entry.st_dev, entry.st_ino) != self.identity:
                self.held = False
                return
            with self.path.open('r', encoding='ascii') as handle:
                opened = os.fstat(handle.fileno())
                if (opened.st_dev, opened.st_ino) != self.identity:
                    return
                owner = handle.read().strip()
            current = self.path.lstat()
            if (current.st_dev, current.st_ino) != self.identity:
                self.held = False
                return
            if self.pid_written and owner != str(os.getpid()):
                return
            self.path.unlink()
            self.held = False
        except (OSError, UnicodeError):
            # Uncertain filesystem ownership must never remove another entry.
            return


def record_blocker(scope: Scope, category: str, evidence: str) -> int:
    """Write a blocker and report it only when the checker confirms it was written.

    `record block` prints `BLOCKED: <category>` and exits 3 once the blocker is in the
    record. Any other answer (a tampered record, no record, a refusal) means nothing
    was written: that verdict is printed instead, never the blocker this runner meant.
    """
    rc, out = _checker_run(scope.block(category, evidence))
    first = out.splitlines()[0] if out else ""
    if rc == 3 and first == f"BLOCKED: {category}":
        print(first)
        return 3
    print(
        f"run-plan: the {category} blocker was not recorded (checker exit {rc}: {first or 'no output'})",
        file=sys.stderr,
    )
    if rc in (3, 4) and first:
        print(first)
        return rc
    return 2


def _launch(argv: list[str], backoff: float, settled: Callable[[int], bool] | None = None) -> int:
    """Run one session, retrying once. `settled(code)` may accept a non-zero exit
    (returning 0 for it) when the checker confirms what that exit claims."""
    # Every session this runner launches is marked, so its prompts are never
    # captured, and never recorded, as the user's approval (v4.13.2 WN-9).
    env = {**os.environ, "NEXUS_RUNNER_LAUNCH": "1"}
    for attempt in (1, 2):
        try:
            code = subprocess.run(argv, check=False, env=env).returncode
        except OSError:
            code = -1
        if code != 0 and settled is not None and settled(code):
            return 0
        if code == 0 or attempt == 2:
            return code
        time.sleep(backoff)
    return -1



def require_authority_process_capability() -> None:
    """Require the declared observer package before a new external dispatch."""
    try:
        import psutil
    except (ImportError, OSError) as exc:
        raise RunnerError("native-process-observation-unavailable: psutil (" + type(exc).__name__ + ")") from None
    try:
        created = psutil.Process().create_time()
    except (psutil.Error, OSError, ValueError, TypeError, AttributeError) as exc:
        raise RunnerError("native-process-observation-unavailable: psutil (" + type(exc).__name__ + ")") from None
    if type(created) not in (int, float) or not math.isfinite(created) or created <= 0:
        raise RunnerError("native-process-observation-unavailable: psutil (invalid process birth)")


def observe_authority_process(result: dict) -> dict:
    """Observe the original launch identity without signaling it or guessing its exit."""
    observed = {"state": "unavailable", "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "reason": "Exact original process observation unavailable; exit and host outcome remain unknown."}
    identity = result.get("process")
    if (not isinstance(identity, dict) or type(identity.get("pid")) is not int or identity["pid"] <= 0
            or type(identity.get("created_at")) not in (int, float) or not math.isfinite(identity["created_at"])
            or result.get("handle") != f"process:{identity['pid']}:{identity['created_at']:.6f}"):
        return observed
    observed["handle"] = result["handle"]
    if type(result.get("exit_code")) is int:
        return dict(observed, state="ended", reason="Original wait observed process termination; its retained exit code is unchanged.")
    if result.get("exit_code") is not None:
        return observed
    try:
        import psutil
    except (ImportError, OSError) as exc:
        return dict(observed, reason="native-process-observation-unavailable: psutil (" + type(exc).__name__ + ")")
    try:
        process = psutil.Process(identity["pid"])
        if (abs(process.create_time() - identity["created_at"]) > 0.001
                or not process.is_running() or process.status() == psutil.STATUS_ZOMBIE):
            return dict(observed, state="ended", reason="Original process identity has ended; exit code and host outcome remain unknown.")
    except psutil.NoSuchProcess:
        return dict(observed, state="ended", reason="Original process identity has ended; exit code and host outcome remain unknown.")
    except (psutil.AccessDenied, OSError, ValueError, TypeError, AttributeError):
        return observed
    return dict(observed, state="running", reason="Observed the exact original PID and creation time; host outcome remains unverified.")


def codeql_observation_directory(record_path: Path, run_nonce: str) -> Path:
    """Separate verified record/run observations without changing any finite effect ID."""
    scope = hashlib.sha256(json.dumps({"record": str(record_path.resolve()), "nonce": run_nonce},
        sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return record_path.parent / "hosted-codeql-observations" / scope


def dispatch_authority_operation(ctx, record_path: Path, operation_id: str, argv: list[str], *, run_nonce: str, artifact_read: dict | None = None) -> dict:
    """One native-reserved host process, observed through the existing job/result format.

    This function never retries. A timed-out process stays an explicitly observed
    job; its disappearance or exit code does not establish any remote effect.
    """
    import approval_binding
    import check_plan_completion as ck
    if (re.fullmatch(r"[0-9a-f]{64}", operation_id) is None or not isinstance(run_nonce, str)
            or not argv or argv[0] not in {ctx.git, ctx.gh}):
        raise RunnerError("reserved hosting command or observation budget unavailable")
    if artifact_read is not None:
        import hmac
        read_key = ck._secret(create=False)
        if read_key is None:
            raise RunnerError("fixed artifact observation key unavailable")
        def read_seal(value):
            return hmac.new(read_key, b"v415-codeql-artifact-observation\0" + approval_binding.canonical(
                {name: child for name, child in value.items() if name != "observation_hmac"}), hashlib.sha256).hexdigest()
        if (not isinstance(artifact_read, dict) or set(artifact_read) != {"artifact_id", "artifact_digest", "artifact_size", "run_id", "run_attempt", "publication_receipt_sha256"}
                or any(type(artifact_read.get(field)) is not int or artifact_read[field] <= 0 for field in ("artifact_id", "artifact_size", "run_id", "run_attempt"))
                or artifact_read["artifact_size"] > 16 * 1024 * 1024
                or re.fullmatch(r"sha256:[0-9a-f]{64}", str(artifact_read.get("artifact_digest"))) is None
                or re.fullmatch(r"[0-9a-f]{64}", str(artifact_read.get("publication_receipt_sha256"))) is None):
            raise RunnerError("fixed CodeQL artifact read context is invalid")
        expected_command = [ctx.gh, "api", "--hostname", "github.com", "--method", "GET",
            "repos/bendourthe/Nexus-Hub/actions/artifacts/" + str(artifact_read["artifact_id"]) + "/zip",
            "-H", "Accept: application/vnd.github+json", "-H", "X-GitHub-Api-Version: 2026-03-10"]
        expected_id = hashlib.sha256(approval_binding.canonical({"purpose": "codeql-artifact-observation", "context": artifact_read, "nonce": run_nonce})).hexdigest()
        if argv != expected_command or operation_id != expected_id:
            raise RunnerError("only the exact fixed CodeQL artifact GET may use read observation context")
    directory = codeql_observation_directory(record_path, run_nonce) if artifact_read is not None else record_path.parent / "publication-jobs"
    if directory.resolve() != directory.absolute() or any(path.is_symlink() for path in directory.parents):
        raise RunnerError("native job directory is not canonical")
    result_path = directory / (operation_id + ".json")
    if result_path.exists() or result_path.is_symlink():
        if artifact_read is None:
            raise RunnerError("one-dispatch result already exists; reconcile instead")
        retained = _bounded_json(result_path)
        if (not isinstance(retained, dict) or not hmac.compare_digest(str(retained.get("observation_hmac", "")), read_seal(retained))
                or retained.get("purpose") != "codeql-artifact-observation"
                or retained.get("observation_id") != operation_id or "operation_id" in retained
                or retained.get("read_context") != artifact_read or retained.get("run_nonce") != run_nonce
                or retained.get("command_sha256") != hashlib.sha256(approval_binding.canonical(argv)).hexdigest()):
            raise RunnerError("fixed artifact observation sidecar does not match")
        return {**retained, "result_receipt": {"path": str(result_path), "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}}
    if ctx.budget.remaining() <= 0:
        raise RunnerError("reserved hosting command or observation budget unavailable")
    require_authority_process_capability()
    import psutil
    directory.mkdir(parents=True, exist_ok=True)
    ck._restrict(directory, directory=True)
    out_fd, out_name = tempfile.mkstemp(prefix=operation_id + ".", suffix=".stdout", dir=directory)
    err_fd, err_name = tempfile.mkstemp(prefix=operation_id + ".", suffix=".stderr", dir=directory)
    started = time.time()
    with os.fdopen(out_fd, "wb") as stdout, os.fdopen(err_fd, "wb") as stderr:
        output_identity = os.fstat(stdout.fileno())
        process = subprocess.Popen(argv, cwd=ctx.root, env={**ck._env(), "NEXUS_RUNNER_LAUNCH": "1", "PYTHONDONTWRITEBYTECODE": "1"},
            stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        created = psutil.Process(process.pid).create_time()
        handle = f"process:{process.pid}:{created:.6f}"
        try:
            code = process.wait(timeout=max(0.001, ctx.budget.remaining()))
        except subprocess.TimeoutExpired:
            code = None
    with Path(out_name).open("rb") as captured:
        bounded_output = captured.read(32769) if code is not None else None
    proof = {"operation_id": operation_id, "handle": handle, "run_nonce": run_nonce,
             "status": "observation-timeout" if code is None else "succeeded" if code == 0 else "failed",
             "exit_code": code, "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
             "process": {"pid": process.pid, "created_at": created}, "job_created_at": started,
             "stdout_path": out_name, "stderr_path": err_name,
             "stdout_identity": {"device": output_identity.st_dev, "inode": output_identity.st_ino},
             "stdout_sha256": hashlib.sha256(bounded_output).hexdigest() if bounded_output is not None and len(bounded_output) <= 32768 else None,
             "command_sha256": hashlib.sha256(approval_binding.canonical(argv)).hexdigest()}
    if code is not None:
        proof["finished_at"] = proof["observed_at"]
    if artifact_read is not None:
        proof["purpose"] = "codeql-artifact-observation"
        proof["observation_id"] = proof.pop("operation_id")
        proof["read_context"] = artifact_read
        proof["observation_hmac"] = read_seal(proof)
    approval_binding._write_private(result_path, proof)
    return {**proof, "result_receipt": {"path": str(result_path), "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}}


def _verified_runner_minor(record_path: Path, record: dict):
    import check_plan_completion as ck
    try:
        refusals = (ck.Malformed, ck._minor_module().ObservationUnavailable)
    except Exception as exc:
        raise RunnerError('minor controller could not be verified') from exc
    try:
        ctx, verified = ck.resolve_minor_controller(record_path, str(record.get('session_id') or ''), minor_protocol=1, execution_protocol=1)
    # TypeError/AttributeError: an older sibling checker in a mixed helper bundle; stop with a
    # controlled runner error instead of a traceback.
    except (OSError, ValueError, TypeError, AttributeError, *refusals) as exc:
        raise RunnerError('minor controller could not be verified') from exc
    if Path.cwd().resolve() != ctx.root:
        raise RunnerError('restart run-plan from the verified operational controller')
    return ctx, verified


@contextmanager
def controller_runner_lock(scope, record_path: Path, record: dict):
    if not scope.minor:
        with Lock(record_path) as lock:
            yield lock
        return
    import check_plan_completion as ck
    lock = Lock(record_path)
    try:
        try:
            with ck.minor_transaction(record):
                lock.__enter__()
        except (ck.Malformed, OSError, ck._minor_module().ObservationUnavailable) as exc:
            raise RunnerError(f'minor runner acquisition failed: {exc}') from exc
        yield lock
    finally:
        # Covers lease-exit, CAS and I/O failures after exclusive lock creation.
        lock.__exit__(None, None, None)


def run(plan_arg: str, row: str, max_cycles: int) -> int:
    if row not in TEMPLATES:
        raise RunnerError(
            f"unknown platform {row!r}; choose one of: {', '.join(sorted(TEMPLATES))}"
        )
    scope = Scope(plan_arg)
    label = scope.label
    launch, resume, headless_goal = TEMPLATES[row]
    rc, out = _checker_run(scope.path())
    if rc != 0:
        raise RunnerError(
            f"no run record for {label}; run /implement {label} first to record the upfront approvals"
        )
    record_path = Path(out.strip())
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RunnerError(f"run record unreadable: {record_path}") from exc
    minor_ctx = None
    if scope.minor:
        minor_ctx, record = _verified_runner_minor(record_path, record)
        scope.repo_root = minor_ctx.root
    approved = {c.get("class") for c in record.get("approvals", {}).get("classes", [])}
    reason = bypass_configured(row)
    full_access = False
    context = record.get('approvals', {}).get('authorization_context') or {}
    if (context.get('origin') in {'host-hook-capture', 'codex-host-transcript'}
            and context.get('permission_mode') == 'bypassPermissions'
            and context.get('session_id') == record.get('session_id')):
        # record path only locates a file. A terminal check must authenticate it before this mode is trusted.
        verified_rc, verified_out = _checker_run(scope.check())
        if verified_rc not in (0, 1, 3, 4) or verified_out.startswith('BLOCKED: record-tampered'):
            raise RunnerError('run record authorization could not be verified')
        import approval_binding
        try:
            import check_plan_completion as ck
            roots = ck._host_cwds(minor_ctx) if minor_ctx is not None else {str(Path.cwd().resolve())}
            current = approval_binding.current_host_context(record_path.parent, record, roots,
                historical_cwds=ck.historical_host_cwds(record) if scope.minor else set())
            full_access = approval_binding.full_access_authorization(record, current)
        except ValueError:
            full_access = False
    if reason and "unattended-with-bypass" not in approved and not full_access:
        raise RunnerError(
            f"{reason}; approve the unattended-with-bypass class upfront or remove the setting"
        )
    backoff = float(os.environ.get("NEXUS_RUNNER_BACKOFF", "5"))
    with controller_runner_lock(scope, record_path, record) as lock:
        # A run whose verdict is already terminal (the first turn completed it, a
        # blocker was recorded, or the user paused it) has nothing to resume, and a
        # resumed session there only spends money restating the stop.
        rc, out = _checker_run(scope.check())
        if rc not in (0, 4) and runner_usage_stop(scope, row):
            print("Waiting for you: the existing usage decision must be resolved before implementation resumes.")
            return 1
        disposition = continuation_for_run(scope, record_path, record, rc, out)
        if disposition and disposition["directive"] == "wait" and rc != 4:
            print(waiting_line(disposition))
            return rc if rc == 3 else 1
        if disposition and disposition["directive"] == "continue" and rc == 3:
            rc = 1  # Independently covered work or fresh-reply reconciliation, not a cleared native blocker.
        if rc in (0, 3, 4):
            print(out.splitlines()[0] if out else "")
            return rc
        if rc != 1:
            raise RunnerError(f"checker exited {rc}")
        binary = resolve_binary(launch("x")[0])
        best = -1
        stalled = 0
        goal = goal_prompt(scope.version)
        if goal and row in INTERACTIVE_GOAL_ROWS:
            print(f"run-plan: {row} sets its goal only when you type it; to add it, type: {goal}", file=sys.stderr)
        for cycle in range(1, max_cycles + 1):
            lock.refresh()
            if runner_usage_stop(scope, row):
                print("Waiting for you: the existing usage decision must be resolved before implementation resumes.")
                return 1
            if disposition and disposition.get("refresh_event_id"):
                disposition = continuation_for_run(scope, record_path, record, rc, out, claim_refresh=True)
                if disposition and disposition["directive"] != "continue":
                    print(waiting_line(disposition))
                    return 1
            # Every cycle RESUMES: the run record exists only because /implement's
            # upfront round ran in a session, and a fresh session would carry a
            # different session id, so the turn-end gate bound to the record would
            # never fire in it. The first cycle also sets the goal where a platform
            # documents a headless goal entry point.
            goal_cycle = cycle == 1 and headless_goal and goal is not None
            if goal_cycle:
                argv = [*resume(goal), *GOAL_FLAGS.get(row, [])]
            else:
                argv = resume(
                    (f"Continue /implement {label}. " + disposition["reason"]
                     if disposition and disposition["directive"] == "continue" else
                     f"Continue /implement {label}. The completion checker still reports it incomplete.")
                )
            argv = [
                binary,
                *(
                    str(record.get("nonce", "run")) if a == "SESSION" else a
                    for a in argv[1:]
                ),
            ]
            check_argv(argv)
            documented = GOAL_EXITS.get(row, set()) if goal_cycle else set()

            def settled(code: int) -> bool:
                return code in documented and _checker_run(scope.check())[0] in (3, 4)

            if _launch(argv, backoff, settled) != 0 and cycle == 1:
                return record_blocker(scope, "platform-unavailable", f"{row} CLI failed twice on the first cycle")
            rc, out = _checker_run(scope.check())
            verdict = out.splitlines()[0] if out else ""
            disposition = continuation_for_run(scope, record_path, record, rc, out)
            if disposition and disposition["directive"] == "wait" and rc != 4:
                print(waiting_line(disposition))
                return rc if rc == 3 else 1
            if disposition and disposition["directive"] == "continue" and rc == 3:
                rc = 1
            if rc in (0, 3, 4):
                print(verdict)
                return rc
            if rc != 1:
                raise RunnerError(f"checker exited {rc}")
            score_rc, score_out = _checker_run(scope.score())
            met = progress_score(score_rc, score_out)
            if met is not None:
                stalled = 0 if met > best else stalled + 1
                best = max(best, met)
            print(f"cycle {cycle}: {verdict}", file=sys.stderr)
            if stalled >= NO_PROGRESS_CYCLES:
                return record_blocker(scope, "no-progress", f"score {best} unchanged over {stalled} runner cycles")
        print(f"INCOMPLETE after {max_cycles} cycles")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-hub run-plan",
        description="Relaunch a platform's headless CLI until the plan's completion verdict is terminal.",
        epilog="Platforms: " + ", ".join(sorted(TEMPLATES)),
    )
    parser.add_argument("plan", help="docs/**/plans/<plan>.md, or a minor scope such as v0.5")
    parser.add_argument("--platform", required=True, choices=sorted(TEMPLATES))
    parser.add_argument("--max-cycles", type=int, default=DEFAULT_MAX_CYCLES)
    return parser


def main(argv: list[str] | None = None) -> int:
    actual = sys.argv[1:] if argv is None else argv
    if actual and actual[0] == "reconcile":
        parser = argparse.ArgumentParser(prog="nexus-hub run-plan reconcile")
        parser.add_argument("plan")
        parser.add_argument("--observations", required=True)
        parser.add_argument("--observer-session", help="internal host session; grants no native ownership")
        args = parser.parse_args(actual[1:])
        try:
            return cmd_reconcile(args.plan, args.observations, observer_session=args.observer_session)
        except (RunnerError, OSError, ValueError, KeyError, TypeError) as exc:
            print(f"run-plan: reconciliation required: {exc}", file=sys.stderr)
            return 2
    args = build_parser().parse_args(actual)
    try:
        return run(args.plan, args.platform, max(1, args.max_cycles))
    except (RunnerError, ValueError, OSError, KeyError, TypeError) as exc:
        print(f"run-plan: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
