#!/usr/bin/env python3
"""Bind a recorded approval to the exact line the checker generated for its page.

Installed at ~/.nexus-hub/scripts/approval_binding.py beside
check_plan_completion.py, which imports it and stays a thin dispatcher. The rule
this module executes is owned by the completion contract
(catalog/skills/workflow/implement-phase/references/completion-contract.md,
"Approval origin"); read it before changing this file.

    render   build the canonical page, draw a fresh round nonce, derive the
             single-use code from HMAC-SHA256(runs secret, page + nonce), and
             write an owner-only pending file holding the page, code, nonce,
             render time, session, the exact paste line(s) the page shows, and the
             digests of every whole message that approves (alternatives: any one
             of them), sealed by an HMAC over the whole round so no field can be
             edited
    consume  refuse unless the seal verifies, the live page still yields the same
             code, the round has not been used or replaced, the session already
             had a captured prompt before the round was rendered, and it captured
             one approving message as a whole prompt exactly once; then delete the
             pending file and leave a used marker so a replay reads `code-used`

Only this module generates codes. Paste lines come from approval_page.py (the one
place their templates live), built from validated fields only (a version token, a
blocker index, a base32 code), never from plan text. Which line(s) a create round
shows, and which of them approve, follows the platform's goal capture there.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import math
import os
import re
import secrets
import time
from collections.abc import Callable
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from functools import wraps
from pathlib import Path

import approval_page  # installed as a sibling in ~/.nexus-hub/scripts/

SUPERSEDED_KEEP = 20
RECOVERABLE_MINOR_ACTIONS = frozenset({'add-class', 'permit-member-execution-paths', 'resume', 'supplement-v415-authority'})
RUNNER_ENV = "NEXUS_RUNNER_LAUNCH"
ACTIONS = ("create", "answer", "pause", "resume", "retire", "add-class", "supplement-scope", "permit-manifest", "permit-outputs", "correct-ci-read", "amend-minor")
SCOPE_RE = re.compile(r"^v\d+\.\d+(?:\.\d+)?\Z", re.ASCII)
CODE_RE = re.compile(r"^[A-Z2-7]{8}\Z", re.ASCII)
DIGEST_RE = re.compile(r"^[0-9a-f]{64}\Z", re.ASCII)

# Refusal reasons, each a fixed id so the checker can print it safely.
REASONS = (
    "runner-launched",
    "not-rendered",
    "pending-unreadable",
    "code-used",
    "code-superseded",
    "session-mismatch",
    "session-too-new",
    "page-changed",
    "approval-not-captured",
    "observer-session-required",
    "recovery-unreadable",
    "recovery-capacity",
    "recovery-not-supported",
    "recovery-condition-changed",
    "recovery-context-changed",
    "recovery-claim-owner-unavailable",
    "approval-round-busy",
)


class Refusal(Exception):
    """An approval that must not be recorded; `reason` is one of REASONS."""

    def __init__(self, reason: str) -> None:
        if reason not in REASONS:
            raise ValueError(f"unknown refusal reason: {reason}")
        super().__init__(reason)
        self.reason = reason


# --------------------------------------------------------------------------- primitives


def restrict(path: Path, directory: bool) -> None:
    """Owner-only permissions for records, pending files, and their directory.

    On Windows chmod is best-effort: ACLs are inherited from the user profile, so a
    failed chmod is not a leak.
    """
    try:
        os.chmod(path, 0o700 if directory else 0o600)
    except PermissionError:
        # Deliberately ignored: a path this user does not own (a shared parent such as
        # the runs directory's parent) or a Windows ACL that refuses the POSIX bits. The
        # file keeps its inherited, owner-scoped permissions, so nothing is exposed;
        # any other OSError (a missing path, a read-only volume) still propagates.
        return


def canonical(obj: object) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def normalize(text: str) -> str:
    return " ".join(text.split())


def digest(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def _clock() -> float:
    return time.time()


def runner_launched(env: dict[str, str] | None = None) -> bool:
    return (os.environ if env is None else env).get(RUNNER_ENV) == "1"


def compute_code(secret: bytes, page: dict, nonce: str) -> str:
    """First 8 base32 characters of HMAC-SHA256(secret, canonical page and nonce)."""
    mac = hmac.new(secret, canonical({"nonce": nonce, "page": page}), hashlib.sha256)
    return base64.b32encode(mac.digest()).decode("ascii")[:8]


def paste_lines(
    action: str,
    scope: str,
    code: str,
    blocker: int | None = None,
    platform: str | None = None,
) -> list[str]:
    """The exact line(s) the page shows, in paste order (templates: approval_page).

    Every field is validated first, so no plan, gap, git, or gh text can reach
    the line; a validation failure raises ValueError. Consumers compare against
    the digests stored at render, never this template.
    """
    return list(approval_page.paste_set(action, scope, code, blocker, platform).lines)


# --------------------------------------------------------------------------- pages


def create_page(
    *,
    rel: str,
    version: str,
    plan_sha256: str,
    repo: str,
    head: str,
    spec: dict,
) -> dict:
    """The canonical data an upfront approval page shows for a one-plan run."""
    cleanup = spec.get("cleanup") or {"branches": [], "worktrees": []}
    # `cleanup-merged` is offered to a one-plan run too (completion contract, "Cleanup receipt").
    merged = any(c.get("class") == "cleanup-merged" for c in spec.get("classes", []))
    return {
        "action": "create",
        "autonomy": validate_policy(spec["autonomy"]) if spec.get("autonomy") else None,
        "scope": {"kind": "plan", "version": version, "plan": rel},
        "members": [{"plan": rel, "version": version, "plan_sha256": plan_sha256}],
        "repo": repo,
        "head": head,
        "branches": {
            "source": spec.get("source_branch"),
            "target": spec.get("target_branch") or "develop",
        },
        "releases": [
            {
                "version": spec.get("release_version") or version,
                "tag": spec.get("tag") or version,
            }
        ],
        "cleanup": {"rule": "merged-and-idle" if merged else "run-owned", "estimate": cleanup},
        "migratable_gaps": [],
        "spend_caps": spec.get("spend_caps") or {},
        "classes": [
            {"class": c.get("class"), "bound": c.get("bound")}
            for c in spec.get("classes", [])
        ],
    }


def action_page(
    action: str,
    *,
    rel: str,
    version: str,
    record_nonce: str,
    blocker: int | None = None,
    category: str | None = None,
    fingerprint: str | None = None,
) -> dict:
    """The canonical data a mid-run answer, pause, or resume page shows."""
    page: dict = {
        "action": action,
        "scope": {"kind": "plan", "version": version, "plan": rel},
        "record_nonce": record_nonce,
    }
    if action == "answer":
        page["blocker"] = {"index": blocker, "category": category, "fingerprint": fingerprint}
    return page


# --------------------------------------------------------------------------- state


def pending_path(runs: Path, key: str) -> Path:
    return runs / "pending" / f"{key}.json"


def used_path(runs: Path, key: str) -> Path:
    return runs / "pending" / f"{key}.used.json"


def private_serialized_size(data: dict) -> int:
    """Match existing UTF-8 private-file serialization, including native newlines."""
    return len((json.dumps(data, indent=2, sort_keys=True) + '\n').replace('\n', os.linesep).encode('utf-8'))


def _write_private(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    restrict(path.parent.parent, directory=True)
    restrict(path.parent, directory=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    restrict(tmp, directory=False)
    os.replace(tmp, path)
    restrict(path, directory=False)


def _seal(secret: bytes, pending: dict) -> str:
    """HMAC over every field of a round except the seal itself.

    The code alone authenticates only the page: without this, editing the pending
    file's digests, expiry, or session (which needs no secret) retargets a round.
    """
    body = {k: v for k, v in pending.items() if k != "mac"}
    return hmac.new(secret, canonical(body), hashlib.sha256).hexdigest()


def _read_pending(path: Path, secret: bytes) -> dict:
    try:
        pending = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise Refusal("pending-unreadable") from exc
    if (
        not isinstance(pending, dict)
        or not isinstance(pending.get("page"), dict)
        or not isinstance(pending.get("nonce"), str)
        or not CODE_RE.match(str(pending.get("code", "")))
        or not isinstance(pending.get("rendered_at"), (int, float))
        or not isinstance(pending.get("paste_digests"), list)
        or not pending["paste_digests"]
        or not all(DIGEST_RE.match(str(d)) for d in pending["paste_digests"])
        or not hmac.compare_digest(str(pending.get("mac", "")), _seal(secret, pending))
    ):
        raise Refusal("pending-unreadable")
    return pending


def _last_used_action(runs: Path, key: str) -> str | None:
    """The action of the round consumed last for `key`, when no newer round is open."""
    try:
        used = json.loads(used_path(runs, key).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None
    return str(used.get("action")) if isinstance(used, dict) else None


def captured_prompts(runs: Path, session: str) -> list[tuple[str, float | None]]:
    """(whole-prompt digest, capture time) pairs the hook stored for a session.

    Oldest first; empty when the session has no capture file. An entry without a
    whole-prompt digest does not count, and one without a time carries None.
    """
    path = runs / "prompts" / f"{hashlib.sha256(session.encode('utf-8')).hexdigest()}.jsonl"
    if not path.is_file():
        return []
    prompts: list[tuple[str, float | None]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict) and DIGEST_RE.match(str(entry.get("prompt", ""))):
            at = entry.get("at")
            timed = float(at) if isinstance(at, (int, float)) and not isinstance(at, bool) else None
            prompts.append((str(entry["prompt"]), timed))
    return prompts


def approved_text(message: str) -> str:
    """One recorded line for a pasted message: its lines joined with ` / `."""
    return " / ".join(line.strip() for line in message.splitlines() if line.strip())


def pasted(pending: dict) -> str:
    """What a consumed round's user pasted, or every shown line for an older round."""
    return str(pending.get("pasted") or " / ".join(pending["paste_lines"]))


def resolve_session(runs: Path, wanted: list[str]) -> str | None:
    """The newest captured session whose whole prompts include any accepted digest."""
    prompts = runs / "prompts"
    if not prompts.is_dir():
        return None
    for path in sorted(prompts.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True):
        session, seen = None, set()
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if isinstance(entry, dict):
                session = entry.get("session") or session
                if DIGEST_RE.match(str(entry.get("prompt", ""))):
                    seen.add(str(entry["prompt"]))
        if session and seen & set(wanted):
            return str(session)
    return None


def resume_condition(record: dict) -> dict:
    """Bind a manual resume to the native owner and pause shown at render."""
    return {'owner_session': str(record['session_id']),
            'pause_sha256': hashlib.sha256(canonical(record.get('pause'))).hexdigest()}


def _condition_valid(value: object) -> bool:
    return (isinstance(value, dict) and set(value) == {'owner_session', 'pause_sha256'}
            and isinstance(value['owner_session'], str) and bool(value['owner_session'])
            and bool(DIGEST_RE.fullmatch(str(value['pause_sha256']))))


def _round_transaction(function):
    """Order mutations: native record lease, round key, then question marker."""
    @wraps(function)
    def locked(runs, key, *args, **kwargs):
        import check_plan_completion as ck
        identity = hashlib.sha256(str(key).encode('utf-8')).hexdigest()
        with ExitStack() as stack:
            try:
                stack.enter_context(ck._minor_os_lock(runs / 'round-locks' / (identity + '.lock'), ck.Budget(3)))
            except ck.MinorConflict as exc:
                raise Refusal('approval-round-busy') from exc
            return function(runs, key, *args, **kwargs)
    return locked


# --------------------------------------------------------------------------- render / consume


_TRANSCRIPT_DEADLINE: ContextVar[float | None] = ContextVar("transcript_deadline", default=None)


@contextmanager
def transcript_deadline(deadline: float | None = None):
    """One binding stage inherits its absolute native budget; direct calls get 60 seconds.

    The caller enters again after a legitimate native budget refresh. This scope
    retains only a deadline, never transcript data, and never clamps an explicit
    longer budget. Deadline checks are cooperative, not JSON-parser preemption.
    """
    inherited = _TRANSCRIPT_DEADLINE.get()
    selected = (inherited if inherited is not None else time.monotonic() + 60.0) if deadline is None else float(deadline)
    if not math.isfinite(selected):
        raise ValueError('invalid transcript operation deadline')
    if inherited is not None:
        selected = min(selected, inherited)
    token = _TRANSCRIPT_DEADLINE.set(selected)
    try:
        yield selected
    finally:
        _TRANSCRIPT_DEADLINE.reset(token)


def _transcript_operation(function):
    @wraps(function)
    def observed(*args, deadline: float | None = None, **kwargs):
        with transcript_deadline(deadline):
            return function(*args, **kwargs)
    return observed


def _check_transcript_deadline() -> None:
    deadline = _TRANSCRIPT_DEADLINE.get()
    if deadline is not None and time.monotonic() >= deadline:
        raise ValueError('transcript observation exceeded its operation deadline')


@_transcript_operation
@_round_transaction
def render(
    runs: Path,
    key: str,
    secret: bytes,
    *,
    action: str,
    scope: str,
    page: dict,
    session: str | None,
    blocker: int | None = None,
    platform: str | None = None,
    check: Callable[[dict], object] | None = None,
    allow_short_reply: bool = False,
    host_transcript: Path | None = None,
    allowed_cwds: set[str] | None = None,
    recovery_condition: dict | None = None,
    render_context: dict | None = None,
) -> dict:
    """Open a new approval round for `key`, invalidating any older round.

    `check` receives the sealed round before anything is written and may raise
    (approval_page.PageError when the page cannot be rendered): then no file
    changes, so the user's previous valid round stays open and unsuperseded.

    `platform` is a completion-levers row; it picks the create round's paste
    shape (approval_page.paste_set). An unknown or absent platform is treated as
    `unverified`, so the plain approval line is the one that approves.
    """
    if runner_launched():
        raise Refusal("runner-launched")
    if host_transcript is not None:
        if not session:
            raise Refusal('session-mismatch')
        try:
            _transcript_path(host_transcript, session)
        except (OSError, ValueError, TypeError) as exc:
            raise Refusal('approval-not-captured') from exc
    if recovery_condition is not None and (action != 'resume' or not _condition_valid(recovery_condition)):
        raise Refusal('pending-unreadable')
    if render_context is not None and not isinstance(render_context, dict):
        raise Refusal('pending-unreadable')
    path = pending_path(runs, key)
    superseded: list[str] = []
    if path.exists():
        try:
            old = _read_pending(path, secret)
        except Refusal:
            superseded = []
        else:
            if (old.get('action') == action and old.get('session') == session
                    and old.get('platform') == platform and old.get('allow_short_reply', False) == allow_short_reply
                    and bool(old.get('transcript_source')) == (host_transcript is not None)
                    and (host_transcript is None or old['transcript_source']['path'] == str(host_transcript.resolve()))
                    and canonical(old.get('recovery_condition')) == canonical(recovery_condition)
                    and canonical(old.get('render_context')) == canonical(render_context)
                    and canonical(old['page']) == canonical(page)
                    and (host_transcript is None or _transcript_round_reusable(runs, key, secret, old, allowed_cwds or set()))):
                if check is not None:
                    check(old)
                activate_question(runs, key, secret, old)
                return old
            superseded = [*old.get("superseded", []), *old["paste_digests"]]
    nonce = secrets.token_hex(16)  # 128-bit round nonce
    code = compute_code(secret, page, nonce)
    shown = approval_page.paste_set(action, scope, code, blocker, platform)
    now = _clock()
    pending = {
        "action": action,
        "page": page,
        "nonce": nonce,
        "code": code,
        "created_at": int(now),
        "rendered_at": now,
        "session": session,
        "platform": platform,
        "shape": shown.shape,
        "allow_short_reply": allow_short_reply,
        # Every line the page shows, and `paste_digests`: every whole message that
        # approves. Any ONE of them, captured once, approves the round (paste_set).
        "paste_lines": list(shown.lines),
        "approve_lines": list(shown.approve),
        "paste_digests": [digest(line) for line in shown.approve],
        "superseded": superseded[-SUPERSEDED_KEEP:],
    }
    if recovery_condition is not None:
        pending['recovery_condition'] = json.loads(canonical(recovery_condition))
    if render_context is not None:
        pending['render_context'] = json.loads(canonical(render_context))
    if host_transcript is not None:
        if not session:
            raise Refusal('session-mismatch')
        pending['transcript_source'] = transcript_anchor(host_transcript, session, allowed_cwds or set())
    pending["mac"] = _seal(secret, pending)
    if check is not None:
        check(pending)
    if sum(row.get('action') in RECOVERABLE_MINOR_ACTIONS
           and consumed_capture_valid(runs, row.get('capture'), row['rendered_at'])
           for row in used_recovery_rounds(runs, key, secret)) >= 64:
        # Keep the old operations recoverable instead of opening an unclaimable
        # newer round that would prevent their exact-operation retry.
        raise Refusal('recovery-capacity')
    # Refuse before replacing the old question, leaving earlier claimed work
    # recoverable with its original consent and without a newer-round barrier.
    base = _used_marker(runs, key, secret, _capture_reservation(pending))
    if (private_serialized_size(pending) > RECOVERY_MAX_BYTES
            or private_serialized_size(base) + RECOVERY_CAPTURE_GROWTH_BYTES > RECOVERY_MAX_BYTES):
        raise Refusal('recovery-capacity')
    _write_private(path, pending)
    activate_question(runs, key, secret, pending)
    if not any(row.get('action') in RECOVERABLE_MINOR_ACTIONS
               and consumed_capture_valid(runs, row.get('capture'), row['rendered_at'])
               for row in used_recovery_rounds(runs, key, secret)) and completed_resume_pointer(runs, key, secret) is None:
        used_path(runs, key).unlink(missing_ok=True)
    return pending


@_transcript_operation
@_round_transaction
def consume(
    runs: Path,
    key: str,
    secret: bytes | None,
    *,
    action: str,
    live_page: dict,
    session: str,
    required_session: str | None = None,
    pasted_line: str | None = None,
    allowed_cwds: set[str] | None = None,
    recovery_condition: dict | None = None,
) -> tuple[dict, str]:
    """Return (pending, bound session) and consume the round, or raise Refusal.

    `required_session` restricts pause and blocker answers to the existing owner.
    Resume omits it so its genuine capture can bind the new owning session.
    A session with no capture file refuses; there is no terminal fallback, because
    a process that owns the console or a pty can type into it.
    """
    if runner_launched():
        raise Refusal("runner-launched")
    path = pending_path(runs, key)
    if not path.exists():
        raise Refusal("code-used" if _last_used_action(runs, key) == action else "not-rendered")
    if secret is None:
        raise Refusal("not-rendered")
    pending = _read_pending(path, secret)
    if pending.get("action") != action:
        raise Refusal("not-rendered")
    # No expiry: a round stays open until it is consumed once or replaced by a newer
    # render for the same record, so the user may paste it whenever they come back.
    if not hmac.compare_digest(
        compute_code(secret, live_page, pending["nonce"]), str(pending["code"])
    ) or canonical(live_page) != canonical(pending["page"]):
        raise Refusal("page-changed")
    wanted = [str(d) for d in pending["paste_digests"]]
    superseded = set(pending.get("superseded", []))
    if session == "auto":
        resolved = resolve_session(runs, wanted)
        if resolved is None:
            raise Refusal("approval-not-captured")
        session = resolved
    bound = pending.get("session")
    if (bound and bound != session) or (required_session and required_session != session):
        raise Refusal("session-mismatch")
    if recovery_condition is not None or pending.get('recovery_condition') is not None:
        if action != 'resume' or not _condition_valid(recovery_condition):
            raise Refusal('pending-unreadable')
        if pending.get('recovery_condition') != recovery_condition:
            # Compare the sealed render state before any irreversible claim.
            raise Refusal('recovery-condition-changed')
    if pending.get('transcript_source') is not None:
        return _consume_transcript(runs, key, secret, pending, session, pasted_line, allowed_cwds)
    captured = captured_prompts(runs, session)
    digests = [d for d, _ in captured]
    events = capture_events(runs, session)
    candidates = [row for row in reversed(events) if row['prompt'] in wanted
                  and isinstance(row.get('at'), (int, float)) and not isinstance(row['at'], bool)
                  and row['at'] >= pending['rendered_at']]
    event = next((row for row in candidates if event_available(runs, session, row)), None)
    if event is None and candidates:
        raise Refusal('code-used')
    matched = event['prompt'] if event is not None else None
    short = None
    if matched is None and pending.get('allow_short_reply') and events:
        candidate = events[-1]
        question = candidate.get('question') or {}
        at = candidate.get('at')
        if (question == {'key': key, 'nonce': pending['nonce']}
                and isinstance(at, (int, float)) and at >= pending['rendered_at']
                and candidate['prompt'] in SHORT_REPLIES):
            if not event_available(runs, session, candidate):
                raise Refusal('code-used')
            event, short = candidate, SHORT_REPLIES[candidate['prompt']]
            matched = candidate['prompt']
    if matched is None:
        if superseded & set(digests):
            raise Refusal("code-superseded")
        raise Refusal("approval-not-captured")
    # The user typed something in this session before the page existed (at least
    # the /implement request). A session whose first prompt is the paste line is
    # the signature of a headless CLI the agent launched to submit it.
    rendered_at = float(pending["rendered_at"])
    if not any(at is not None and at < rendered_at and d not in wanted for d, at in captured):
        raise Refusal("session-too-new")
    lines = pending.get("approve_lines") or []
    actual = short if short is not None else (
        approved_text(lines[wanted.index(matched)]) if len(lines) == len(wanted) else pasted(pending)
    )
    if pasted_line is not None and normalize(pasted_line) not in {
        normalize(line) for line in [*pending['paste_lines'], actual]
    }:
        # Validate caller input before claiming the genuine capture or spending the round.
        raise Refusal('approval-not-captured')
    if event is not None:
        context = host_capture_context(event, session)
        if not capture_context_valid(context, session, matched):
            raise Refusal('approval-not-captured')
        pending['capture'] = context
        if pending.get('session') is None:
            pending['session'] = session  # Only the genuinely matched capture binds auto.
    # The message the user actually pasted, so the record stores what was approved.
    if short is not None:
        pending["pasted"] = short
    elif len(lines) == len(wanted):
        pending["pasted"] = approved_text(lines[wanted.index(matched)])
    _retain_used_round(runs, key, secret, pending)
    if event is not None:
        _claim_event(runs, session, event)
    path.unlink()
    return pending, session


# --------------------------------------------------------------------------- host context and continuation

SHORT_REPLIES = {digest(word): word for word in ('Approve', 'Yes', 'Continue')}

_CAPTURE_FIELDS = {'origin', 'session_id', 'permission_mode', 'prompt_sha256', 'event_id', 'at'}
_TRANSCRIPT_FIELDS = _CAPTURE_FIELDS | {'transcript_path', 'transcript_proof'}
_SOURCE_FIELDS = {'format', 'path', 'session', 'prefix_length', 'prefix_sha256', 'device', 'inode', 'allowed_cwds'}
_PROOF_FIELDS = {'source', 'event_offset', 'event_sha256', 'key', 'round_nonce', 'page_sha256', 'rendered_at', 'action'}
_TRANSCRIPT_RECEIPT_DOMAIN = 'nexus-codex-transcript-consumption-v1'


def _strict_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for name, value in pairs:
        if name in result:
            raise ValueError('duplicate transcript key')
        result[name] = value
    return result


def _transcript_path(path: Path, session: str) -> Path:
    """Only the canonical runtime source is eligible; a supplied path is no authority."""
    _check_transcript_deadline()
    root = Path.home() / '.codex' / 'sessions'
    if not path.is_absolute() or not re.fullmatch(r'[A-Za-z0-9-]+', session):
        raise ValueError('invalid transcript source identity')
    for component in (path, *path.parents):
        if component.is_symlink() or getattr(component.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('transcript source cannot traverse a link or junction')
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root.resolve(strict=True)) or not resolved.name.endswith(f'-{session}.jsonl'):
        raise ValueError('transcript source is not the canonical session log')
    if not resolved.is_file():
        raise ValueError('transcript source must be a regular file')
    matches: list[Path] = []
    examined = 0
    for directory, children, files in os.walk(root, followlinks=False, onerror=_transcript_discovery_error):
        _check_transcript_deadline()
        examined += len(children) + len(files)
        if examined > 50000:
            raise ValueError('canonical transcript discovery exceeds the bounded inventory')
        children[:] = [name for name in children if not (
            (Path(directory) / name).is_symlink()
            or getattr((Path(directory) / name).lstat(), 'st_file_attributes', 0) & 0x400)]
        matches.extend(Path(directory) / name for name in files if name.endswith(f'-{session}.jsonl'))
        if len(matches) > 1:
            raise ValueError('canonical transcript session selector is ambiguous')
    if matches != [resolved]:
        raise ValueError('canonical transcript session selector is unavailable')
    return resolved


def _transcript_discovery_error(error: OSError) -> None:
    raise error


_TRANSCRIPT_SCAN_BYTES = 512 * 1024 * 1024
_TRANSCRIPT_RECORD_BYTES = 64 * 1024 * 1024


def _context_status(context: object, allowed_cwds: set[str]) -> dict:
    """Keep historical validity without retaining or prematurely rejecting its payload."""
    try:
        mode = _transcript_mode(context, allowed_cwds)
    except (OSError, ValueError, TypeError):
        return {'valid': False, 'permission_mode': 'manual'}
    return {'valid': True, **mode}


def _event_matches(event: dict | None, message: str) -> bool:
    if event is None:
        return False
    raw = message.encode('utf-8')
    return event['text_utf8_length'] == len(raw) and event['text_sha256'] == hashlib.sha256(raw).hexdigest()


@_transcript_operation
def _read_transcript(path: Path, session: str, allowed_cwds: set[str], *,
                     prefix_length: int | None = None, boundary: int | None = None,
                     selected_offset: int | None = None) -> dict:
    """Strictly scan finite source bytes, retaining only constant-count digest summaries.

    The 512 MiB scan ceiling is distinct from the retained 64 MiB physical-record
    limit. Python parsing can use additional bounded-per-record memory; this is
    not a 64 MiB heap quota. Format-1 hashes and offsets cover original bytes.
    """
    _check_transcript_deadline()
    resolved = _transcript_path(path, session)
    initial = resolved.stat()
    if initial.st_size > _TRANSCRIPT_SCAN_BYTES:
        raise ValueError('transcript source exceeds the bounded reader')
    identity = (initial.st_dev, initial.st_ino)
    fingerprint = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
    complete_hash, prefix_hash = hashlib.sha256(), hashlib.sha256()
    result = {'source_identity': identity, 'complete_length': 0, 'partial': False,
              'has_ordinary_event': False, 'last_event': None, 'post_boundary_count': 0,
              'post_boundary_event': None, 'selected_event': None}
    meta_seen = False
    context = None
    context_is_object = False
    total = 0
    permitted = {str(Path(value).resolve()) for value in allowed_cwds}
    with resolved.open('rb') as handle:
        if fingerprint(os.fstat(handle.fileno())) != fingerprint(initial):
            raise ValueError('transcript source changed before observation')
        while True:
            _check_transcript_deadline()
            line = handle.readline(min(_TRANSCRIPT_RECORD_BYTES + 1, _TRANSCRIPT_SCAN_BYTES - total + 1))
            _check_transcript_deadline()
            if not line:
                break
            total += len(line)
            if total > _TRANSCRIPT_SCAN_BYTES:
                raise ValueError('transcript source exceeds the bounded reader')
            if len(line) > _TRANSCRIPT_RECORD_BYTES:
                raise ValueError('transcript physical record exceeds the bounded reader')
            if not line.endswith(b'\n'):
                result['partial'] = True
                break
            offset = result['complete_length']
            complete_hash.update(line)
            if prefix_length is not None and offset < prefix_length:
                prefix_hash.update(memoryview(line)[:min(len(line), prefix_length - offset)])
            result['complete_length'] += len(line)
            row = json.loads(line.decode('utf-8'), object_pairs_hook=_strict_object)
            _check_transcript_deadline()
            if not isinstance(row, dict) or not isinstance(row.get('payload'), dict):
                raise TypeError('malformed completed transcript record')
            payload = row['payload']
            if row.get('type') == 'session_meta':
                if meta_seen or payload.get('id') != session or payload.get('originator') != 'codex_vscode' or payload.get('source') != 'vscode':
                    raise ValueError('transcript metadata does not establish this session')
                meta_seen = True
            elif row.get('type') == 'turn_context':
                context_is_object = True
                context = _context_status(payload, permitted)
            elif row.get('type') == 'event_msg' and payload.get('type') == 'user_message':
                if not meta_seen or not isinstance(payload.get('message'), str):
                    raise ValueError('user event has no canonical session identity')
                at = _timestamp(row.get('timestamp'))
                if at > _clock():
                    raise ValueError('future transcript user event')
                if _human_user_event(row, payload):
                    message = payload['message']
                    text_bytes = message.encode('utf-8')
                    ordinary = (message not in ('Approve', 'Yes', 'Continue')
                                and not re.fullmatch(r'.*\(approval [A-Z2-7]{8}\)', message))
                    event = {'at': at, 'offset': offset, 'sha256': hashlib.sha256(line).hexdigest(),
                             'prompt_sha256': digest(message), 'text_utf8_length': len(text_bytes),
                             'text_sha256': hashlib.sha256(text_bytes).hexdigest(), 'is_ordinary': bool(ordinary),
                             'context': context}
                    result['last_event'] = event
                    result['has_ordinary_event'] |= bool(ordinary)
                    if boundary is not None and offset >= boundary:
                        result['post_boundary_count'] = min(2, result['post_boundary_count'] + 1)
                        result['post_boundary_event'] = event if result['post_boundary_count'] == 1 else None
                    if offset == selected_offset:
                        result['selected_event'] = event
                    del message, text_bytes, event
            del row, payload, line
        opened_after = os.fstat(handle.fileno())
    _check_transcript_deadline()
    if (fingerprint(opened_after) != fingerprint(initial) or fingerprint(resolved.stat()) != fingerprint(initial)
            or total != initial.st_size):
        raise ValueError('transcript source changed during observation')
    if not meta_seen or not context_is_object:
        raise ValueError('transcript lacks runtime session context')
    if not context['valid']:
        raise ValueError('transcript context does not match an approved worktree')
    result['current'] = {'permission_mode': context['permission_mode']}
    result['complete_sha256'] = complete_hash.hexdigest()
    result['anchored_prefix_sha256'] = prefix_hash.hexdigest() if prefix_length is not None else result['complete_sha256']
    return result


def _human_user_event(row: dict, payload: dict) -> bool:
    """A user-role transport wrapper is not a human instruction or approval."""
    if re.match(r'<(?:codex_internal_context|send_user_message_question_reply|system_reminder)\b', payload['message'].lstrip()):
        return False
    metadata = [row, payload]
    metadata.extend(value.get(name) for value in (row, payload) for name in ('metadata', '_meta')
                    if isinstance(value.get(name), dict))
    for value in metadata:
        if any(name in value and value[name] not in ('user', 'human')
               for name in ('origin', 'message_origin', 'source', 'author')):
            return False
        if 'role' in value and value['role'] != 'user':
            return False
        if any(name in value and value[name] is not False
               for name in ('generated', 'is_generated', 'is_internal', 'is_system', 'synthetic')):
            return False
    return True


def _transcript_mode(context: object, allowed_cwds: set[str]) -> dict:
    if (not isinstance(context, dict) or not isinstance(context.get('cwd'), str)
            or str(Path(context['cwd']).resolve()) not in allowed_cwds):
        raise ValueError('transcript context does not match an approved worktree')
    full = context.get('approval_policy') == 'never' and context.get('sandbox_policy') == {'type': 'danger-full-access'}
    return {'permission_mode': 'bypassPermissions' if full else 'manual'}


@_transcript_operation
def transcript_anchor(path: Path, session: str, allowed_cwds: set[str]) -> dict:
    """Seal an explicit source at render time; no earlier answer may be recovered."""
    try:
        resolved = _transcript_path(path, session)
        scanned = _read_transcript(resolved, session, allowed_cwds)
        if (scanned['partial'] or not scanned['has_ordinary_event']
                or scanned['last_event']['at'] >= _clock() or scanned['current']['permission_mode'] != 'bypassPermissions'):
            raise ValueError('render needs a prior ordinary prompt and current full-access context')
        info = resolved.stat()
        if (info.st_dev, info.st_ino) != scanned['source_identity']:
            raise ValueError('transcript identity changed after observation')
        return {'format': 1, 'path': str(resolved), 'session': session, 'prefix_length': scanned['complete_length'],
                'prefix_sha256': scanned['complete_sha256'], 'device': info.st_dev, 'inode': info.st_ino,
                'allowed_cwds': sorted(str(Path(value).resolve()) for value in allowed_cwds)}
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        raise Refusal('approval-not-captured') from exc


def _source_valid(source: object) -> bool:
    return (isinstance(source, dict) and set(source) == _SOURCE_FIELDS and type(source['format']) is int and source['format'] == 1
            and isinstance(source['path'], str) and isinstance(source['session'], str)
            and all(type(source[name]) is int and source[name] >= 0 for name in ('prefix_length', 'device', 'inode'))
            and bool(DIGEST_RE.fullmatch(str(source['prefix_sha256'])))
            and isinstance(source['allowed_cwds'], list) and bool(source['allowed_cwds'])
            and all(isinstance(value, str) for value in source['allowed_cwds']))


def _transcript_round_reusable(runs: Path, key: str, secret: bytes, pending: dict, allowed_cwds: set[str]) -> bool:
    """Keep a valid displayed answer; renew only a genuinely superseded source round."""
    try:
        source = pending['transcript_source']
        if not _source_valid(source):
            raise Refusal('pending-unreadable')
        path = _transcript_path(Path(source['path']), source['session'])
        info = path.stat()
        scanned = _read_transcript(path, source['session'], allowed_cwds,
                                   prefix_length=source['prefix_length'], boundary=source['prefix_length'])
        if ((info.st_dev, info.st_ino) != (source['device'], source['inode'])
                or scanned['source_identity'] != (source['device'], source['inode'])
                or scanned['complete_length'] < source['prefix_length']
                or scanned['anchored_prefix_sha256'] != source['prefix_sha256']):
            raise Refusal('approval-not-captured')
        if pending.get('allow_short_reply'):
            question = json.loads(question_path(runs, source['session']).read_text(encoding='utf-8'))
            if (question.get('key') != key or question.get('nonce') != pending['nonce']
                    or not hmac.compare_digest(str(question.get('mac', '')), _seal(secret, question))):
                return False
        if scanned['partial']:
            return True
        if not scanned['post_boundary_count']:
            return True
        if scanned['post_boundary_count'] != 1:
            return False
        event = scanned['post_boundary_event']
        return (any(_event_matches(event, message) for message in pending.get('approve_lines') or [])
                or (pending.get('allow_short_reply') and any(_event_matches(event, message) for message in SHORT_REPLIES.values())
                    and type(question.get('activated_at')) in (int, float)
                    and event['at'] >= question['activated_at']))
    except Refusal:
        raise
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise Refusal('approval-not-captured') from exc


CHECKPOINT_PROTOCOL = 1
AUTHORITY_BRIDGE_PROTOCOL = 1


def capture_context_valid(context: object, session: str | None = None, prompt_sha256: str | None = None) -> bool:
    """One strict typed provenance validator shared by all immutable native histories."""
    if not isinstance(context, dict):
        return False
    fields = _CAPTURE_FIELDS if context.get('origin') == 'host-hook-capture' else _TRANSCRIPT_FIELDS
    if (context.get('origin') not in {'host-hook-capture', 'codex-host-transcript'} or set(context) != fields
            or not isinstance(context.get('session_id'), str) or not context['session_id']
            or not DIGEST_RE.fullmatch(str(context.get('prompt_sha256', '')))
            or (session is not None and context['session_id'] != session)
            or (prompt_sha256 is not None and context['prompt_sha256'] != prompt_sha256)):
        return False
    if context['origin'] == 'host-hook-capture':
        return True
    proof = context['transcript_proof']
    return (isinstance(proof, dict) and set(proof) == _PROOF_FIELDS and _source_valid(proof['source'])
            and proof['source']['session'] == context['session_id']
            and proof['source']['path'] == context['transcript_path']
            and type(proof['event_offset']) is int and proof['event_offset'] >= proof['source']['prefix_length']
            and all(DIGEST_RE.fullmatch(str(proof[name])) for name in ('event_sha256', 'page_sha256'))
            and bool(re.fullmatch(r'[0-9a-f]{32}', str(proof['round_nonce'])))
            and isinstance(proof['key'], str) and bool(re.fullmatch(r'[A-Za-z0-9_-]+', proof['key']))
            and isinstance(proof['action'], str) and isinstance(context['event_id'], str)
            and bool(DIGEST_RE.fullmatch(context['event_id']))
            and type(context['at']) in (int, float) and type(proof['rendered_at']) in (int, float)
            and float('-inf') < proof['rendered_at'] <= context['at'] < float('inf'))


def _receipt_path(runs: Path, context: dict) -> Path:
    return runs / 'transcript-receipts' / (context['event_id'] + '.json')


def _transcript_receipt_valid(runs: Path, context: dict, rendered_at: object) -> bool:
    if not capture_context_valid(context) or context['transcript_proof']['rendered_at'] != rendered_at:
        return False
    try:
        receipt = json.loads(_receipt_path(runs, context).read_text(encoding='utf-8'))
        key = (runs / '.secret').read_bytes()
        return (isinstance(receipt, dict) and set(receipt) == {'domain', 'context', 'mac'}
                and receipt['domain'] == _TRANSCRIPT_RECEIPT_DOMAIN and receipt['context'] == context
                and hmac.compare_digest(str(receipt['mac']), _seal(key, receipt)))
    except (OSError, ValueError, TypeError):
        return False


def _claim_transcript(runs: Path, context: dict, secret: bytes) -> None:
    receipt = {'domain': _TRANSCRIPT_RECEIPT_DOMAIN, 'context': context}
    receipt['mac'] = _seal(secret, receipt)
    target = _receipt_path(runs, context)
    target.parent.mkdir(parents=True, exist_ok=True)
    restrict(target.parent, directory=True)
    try:
        with target.open('x', encoding='utf-8') as handle:
            json.dump(receipt, handle, sort_keys=True)
    except FileExistsError:
        raise Refusal('code-used') from None
    restrict(target, directory=False)


def _consume_transcript(runs: Path, key: str, secret: bytes, pending: dict, session: str,
                        pasted_line: str | None, allowed_cwds: set[str] | None) -> tuple[dict, str]:
    try:
        source = pending['transcript_source']
        if not _source_valid(source) or source['session'] != session:
            raise Refusal('session-mismatch')
        path = _transcript_path(Path(source['path']), session)
        info = path.stat()
        permitted = set(source['allowed_cwds']) if allowed_cwds is None else allowed_cwds
        length = source['prefix_length']
        scanned = _read_transcript(path, session, permitted, prefix_length=length, boundary=length)
        if (scanned['partial'] or (info.st_dev, info.st_ino) != (source['device'], source['inode'])
                or scanned['source_identity'] != (source['device'], source['inode'])
                or scanned['complete_length'] < length or scanned['anchored_prefix_sha256'] != source['prefix_sha256']
                or scanned['current']['permission_mode'] != 'bypassPermissions'):
            raise Refusal('approval-not-captured')
        event = scanned['post_boundary_event']
        if scanned['post_boundary_count'] != 1 or event['at'] < pending['rendered_at']:
            raise Refusal('approval-not-captured')
        if not event['context'] or not event['context']['valid'] or event['context']['permission_mode'] != 'bypassPermissions':
            raise Refusal('approval-not-captured')
        permitted_messages = [*(pending.get('approve_lines') or []), *('Approve', 'Yes', 'Continue')]
        message = next((text for text in permitted_messages if _event_matches(event, text)), None)
        exact = message in (pending.get('approve_lines') or [])
        short = pending.get('allow_short_reply') and message in ('Approve', 'Yes', 'Continue')
        if short:
            question = json.loads(question_path(runs, session).read_text(encoding='utf-8'))
            if (question.get('key') != key or question.get('nonce') != pending['nonce']
                    or question.get('session') != session
                    or type(question.get('activated_at')) not in (int, float)
                    or event['at'] < question['activated_at']
                    or not hmac.compare_digest(str(question.get('mac', '')), _seal(secret, question))):
                raise Refusal('approval-not-captured')
        if not (exact or short) or (pasted_line is not None and pasted_line != message):
            raise Refusal('approval-not-captured')
        proof = {'source': source, 'event_offset': event['offset'], 'event_sha256': event['sha256'],
                 'key': key, 'round_nonce': pending['nonce'], 'page_sha256': hashlib.sha256(canonical(pending['page'])).hexdigest(),
                 'rendered_at': pending['rendered_at'], 'action': pending['action']}
        identity = hashlib.sha256(canonical([session, source['path'], source['device'], source['inode'],
                                             event['offset'], event['sha256']])).hexdigest()
        context = {'origin': 'codex-host-transcript', 'session_id': session, 'permission_mode': 'bypassPermissions',
                   'prompt_sha256': digest(message), 'event_id': identity, 'at': event['at'],
                   'transcript_path': source['path'], 'transcript_proof': proof}
        checked = _read_transcript(path, session, permitted, prefix_length=length, boundary=length)
        latest = path.stat()
        if (checked['partial'] or checked['complete_length'] != scanned['complete_length']
                or checked['complete_sha256'] != scanned['complete_sha256']
                or checked['source_identity'] != scanned['source_identity']
                or (latest.st_dev, latest.st_ino) != (source['device'], source['inode'])):
            raise Refusal('approval-not-captured')
        # The exclusive receipt is the cross-record consumption claim. A concurrent
        # consumer can never turn this same source event into a second decision.
        _check_transcript_deadline()
        pending['capture'] = context
        pending['pasted'] = message
        _retain_used_round(runs, key, secret, pending)
        _claim_transcript(runs, context, secret)
        pending_path(runs, key).unlink()
        return pending, session
    except Refusal:
        raise
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise Refusal('approval-not-captured') from exc


def capture_events(runs: Path, session: str) -> list[dict]:
    """Read genuine capture events; old digest-only rows remain valid for exact pastes."""
    path = runs / 'prompts' / f'{hashlib.sha256(session.encode()).hexdigest()}.jsonl'
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
    except OSError:
        return []
    events = []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get('session') == session and DIGEST_RE.fullmatch(str(row.get('prompt', ''))):
            events.append(row)
    return events


def question_path(runs: Path, session: str) -> Path:
    return runs / 'questions' / f'{hashlib.sha256(session.encode()).hexdigest()}.json'


@contextmanager
def _question_mutation(runs: Path, session: str):
    """Use the existing bounded native OS lease for this shared session marker."""
    import check_plan_completion as ck
    try:
        with ck._minor_os_lock(question_path(runs, session).with_suffix('.mutation.lock'), ck.Budget(3)):
            yield
    except ck.MinorConflict as exc:
        raise Refusal('pending-unreadable') from exc


def _unresolved_issued(runs: Path, secret: bytes, rows: list[dict]) -> list[dict]:
    """Keep every request unless its persisted signed native effect verifies."""
    import check_plan_completion as ck
    if ck._runs_dir().resolve() != runs.resolve():
        raise Refusal('pending-unreadable')
    kept = []
    budget = ck.Budget(10)
    for index, row in enumerate(rows):
        if budget.remaining() <= 0:
            return [*kept, *rows[index:]]

        if not isinstance(row, dict) or not hmac.compare_digest(str(row.get('mac', '')), _seal(secret, row)):
            raise Refusal('pending-unreadable')
        key = row.get('issuance', {}).get('key')
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', key):
            raise Refusal('pending-unreadable')
        path = runs / (key + '.json')
        try:
            info = path.lstat()
            if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400 or info.st_size > 1_048_576:
                raise Refusal('pending-unreadable')
            record = json.loads(path.read_text(encoding='utf-8'))
            if record.get('schema') == 1:
                if not callable(getattr(ck, 'resolve_plan_controller', None)) or not callable(getattr(ck, 'plan_owner_results', None)):
                    kept.append(row)
                    continue
                _context, record = ck.resolve_plan_controller(path, str(record.get('session_id') or ''),
                    budget_seconds=max(0.1, budget.remaining()))
                results = ck.plan_owner_results(_context, record, [row])
            else:
                _context, record = ck.resolve_minor_controller(path, str(record.get('session_id') or ''),
                    budget_seconds=budget.remaining(), minor_protocol=ck.MINOR_AMENDMENT_PROTOCOL,
                    execution_protocol=ck.MINOR_EXECUTION_PROTOCOL)
                results = ck._minor_module().continuation_owner_results(ck, record, [row])
            sidecar = path.with_name(path.stem + '.continuation.json')
            if sidecar.exists():
                from run_plan import _bounded_json
                frame = _bounded_json(sidecar)
                identity = 'native:' + key + ':' + row['nonce']
                if any(item.get('id') in {identity, identity + ':decision'}
                       for item in frame.get('disposition', {}).get('requests', [])):
                    kept.append(row)
                    continue  # Keep proof until its unsigned request has actually retired.
            if not results:
                kept.append(row)
        except (OSError, ValueError, TypeError, KeyError, ck.Malformed, ck._minor_module().ObservationUnavailable):
            kept.append(row)  # Unavailable observation never retires the request.
    return kept


def activate_question(runs: Path, key: str, secret: bytes, pending: dict) -> None:
    """Only one displayed short-answer challenge is active in a session."""
    if (not pending.get('allow_short_reply') and pending.get('action') != 'resume') or not pending.get('session'):
        return
    with _question_mutation(runs, str(pending['session'])):
        active = {'key': key, 'nonce': pending['nonce'], 'session': pending['session']}
        if pending.get('transcript_source') is not None:
            active['activated_at'] = _clock()
            try:
                previous = json.loads(question_path(runs, pending['session']).read_text(encoding='utf-8'))
                if (all(previous.get(name) == active[name] for name in ('key', 'nonce', 'session'))
                        and type(previous.get('activated_at')) in (int, float)
                        and hmac.compare_digest(str(previous.get('mac', '')), _seal(secret, previous))):
                    active['activated_at'] = previous['activated_at']
            except (OSError, ValueError, TypeError, AttributeError):
                pass
        previous_marker = _question_marker(runs, secret, pending['session'])
        if previous_marker.get('issued_rounds'):
            active['issued_rounds'] = _unresolved_issued(runs, secret, previous_marker['issued_rounds'])
        if previous_marker.get('question_attempts'):
            active['question_attempts'] = previous_marker['question_attempts']
        _write_question_marker(runs, secret, pending['session'], active)


def _question_marker(runs: Path, secret: bytes, session: str) -> dict:
    """Read the existing sealed question marker without trusting caller flags."""
    path = question_path(runs, session)
    if not path.exists():
        return {}
    info = path.lstat()
    if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400 or info.st_size > 1_048_576:
        raise Refusal('pending-unreadable')
    value = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(value, dict) or value.get('session') != session
            or not hmac.compare_digest(str(value.get('mac', '')), _seal(secret, value))):
        raise Refusal('pending-unreadable')
    return value


def observe_issued_request(runs: Path, key: str, secret: bytes, record: dict, message: object,
                           *, observer_session: str | None = None) -> bool:
    """Bind a delivered Stop response to a complete native review page.

    Rendering, an attempted tool invocation and a bare approval line do not
    establish issuance. Unsupported provider evidence stays unsupported. This
    records reporting provenance only and never grants or consumes authority.
    """
    if not isinstance(message, str) or not message.strip():
        return False
    session = observer_session or str(record.get('session_id') or '')
    with _question_mutation(runs, session):
        path = pending_path(runs, key)
        if not path.is_file() or path.is_symlink():
            return False
        pending = _read_pending(path, secret)
        if not pending_matches_owner(pending, record, session):
            return False
        scope = pending['page'].get('scope', {})
        label = scope.get('minor') if scope.get('kind') == 'minor' else scope.get('version') if scope.get('kind') == 'plan' else record.get('version')
        if not isinstance(label, str) or not SCOPE_RE.fullmatch(label):
            return False
        try:
            data = approval_page.render_data(pending, scope=label, blocker=None, display=pending.get('render_context', {}).get('display'))
            page = approval_page.render_page(data)
            review = page.replace('To approve, paste this line', 'Compatibility paste option').replace('Paste this line as your whole message, with nothing added.', 'For the primary decision, reply Approve, Yes or Continue. Decline leaves the action unapproved.')
        except (approval_page.PageError, KeyError, TypeError, ValueError):
            return False
        if not any(normalize(text) in normalize(message) for text in (page, review)):
            return False
        marker = _question_marker(runs, secret, session)
        issued = _unresolved_issued(runs, secret, marker.get('issued_rounds', []))
        if not isinstance(issued, list) or len(issued) > 64:
            raise Refusal('pending-unreadable')
        if any(row.get('nonce') == pending['nonce'] and row.get('issuance', {}).get('key') == key for row in issued):
            return True
        if len(issued) == 64:
            raise Refusal('pending-unreadable')  # Never silently discard an unresolved request.
        retained = dict(pending)
        retained['issuance'] = {'origin': 'host-stop-response', 'message_sha256': digest(message),
                                'observed_at': _clock(), 'key': key}
        retained['mac'] = _seal(secret, retained)
        marker.setdefault('key', key)
        marker.setdefault('nonce', pending['nonce'])
        marker['session'] = session
        marker['issued_rounds'] = [*issued, retained]
        marker['mac'] = _seal(secret, marker)
        if private_serialized_size(marker) > 1_048_576:
            raise Refusal('pending-unreadable')
        _write_private(question_path(runs, session), marker)
        return True


QUESTION_TOOLS = frozenset({'AskUserQuestion', 'AskQuestion', 'ask_question', 'cursor/ask_question',
                            'request_user_input', 'request_user_input_async'})


def _question_payload(payload: dict) -> tuple[str, str, list[dict]] | None:
    """Accept only an actual host question call with a bounded, explicit handle."""
    tool = str(payload.get('tool_name', '')).removeprefix('functions.')
    call = payload.get('tool_use_id', payload.get('tool_call_id'))
    value = payload.get('tool_input')
    if tool not in QUESTION_TOOLS or not isinstance(call, str) or not 0 < len(call) <= 256 or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in call):
        return None
    if isinstance(value, str):
        if len(value) > 1_048_576:
            return None
        try:
            value = json.loads(value)
        except ValueError:
            return None
    questions = value.get('questions') if isinstance(value, dict) else None
    if (not isinstance(questions, list) or not 0 < len(questions) <= 3
            or any(not isinstance(question, dict) for question in questions)
            or len(canonical(questions)) > 1_048_576):
        return None
    return tool, call, questions


def _reviewed_question(pending: dict, question: dict, marker: dict) -> tuple[str, str] | None:
    scope = pending['page'].get('scope', {})
    label = scope.get('minor') if scope.get('kind') == 'minor' else scope.get('version') if scope.get('kind') == 'plan' else None
    if not isinstance(label, str):
        return None
    data = approval_page.render_data(pending, scope=label, blocker=None, display=pending.get('render_context', {}).get('display'))
    try:
        expected = approval_page.question_data(data)
    except (approval_page.PageError, ValueError, KeyError, TypeError):
        return None
    text = next((question.get(field) for field in ('question', 'title', 'prompt')
                 if isinstance(question.get(field), str) and question[field].strip()), None)
    options = question.get('options')
    labels = [row.get('label') if isinstance(row, dict) else row for row in options] if isinstance(options, list) else []
    if (not isinstance(text, str) or any(not isinstance(label, str) for label in labels)
            or set(labels) != {'Approve', 'Decline'} or len(labels) != 2):
        return None
    if expected['question'] not in text:
        return None
    complete = any(normalize(page) in normalize(text) for page in (expected['review_page'], approval_page.render_page(data)))
    prior = any(row.get('nonce') == pending['nonce'] and row.get('session') == pending['session']
                for row in marker.get('issued_rounds', []))
    challenge = question.get('challenge') == pending['nonce'] or question.get('id') == 'native_' + pending['nonce']
    if not complete and not (prior and challenge):
        return None
    return text, digest(expected['review_page'])


def _question_attempt(pending: dict, key: str, tool: str, call: str, index: int,
                      question: dict, marker: dict) -> dict | None:
    reviewed = _reviewed_question(pending, question, marker)
    if reviewed is None:
        return None
    text, page_hash = reviewed
    return {'key': key, 'round': pending, 'tool': tool, 'call_id': call, 'question_index': index,
            'question_sha256': digest(text), 'review_page_sha256': page_hash, 'observed_at': _clock()}


def _write_question_marker(runs: Path, secret: bytes, session: str, marker: dict) -> None:
    marker['session'] = session
    marker['mac'] = _seal(secret, marker)
    if private_serialized_size(marker) > 1_048_576:
        raise Refusal('pending-unreadable')
    _write_private(question_path(runs, session), marker)


def observe_question_attempt(runs: Path, key: str, secret: bytes, record: dict, payload: dict) -> bool:
    """Remember a host-observed attempt, never label it delivered or approved."""
    parsed = _question_payload(payload)
    if (runner_launched() or parsed is None or payload.get('hook_event_name') not in {'PreToolUse', 'preToolUse'}
            or not isinstance(payload.get('session_id'), str)):
        return False
    path = pending_path(runs, key)
    if not path.is_file() or path.is_symlink():
        return False
    pending = _read_pending(path, secret)
    if not pending_matches_owner(pending, record, payload['session_id']):
        return False
    tool, call, questions = parsed
    with _question_mutation(runs, pending['session']):
        marker = _question_marker(runs, secret, pending['session'])
        if marker.get('issued_rounds'):
            marker['issued_rounds'] = _unresolved_issued(runs, secret, marker['issued_rounds'])
        attempts = marker.get('question_attempts', [])
        if not isinstance(attempts, list) or len(attempts) > 64:
            raise Refusal('pending-unreadable')
        fresh = []
        for index, question in enumerate(questions):
            attempt = _question_attempt(pending, key, tool, call, index, question, marker)
            if attempt is None:
                continue
            old = [row for row in attempts if (row['call_id'], row['question_index']) == (call, index)]
            if old:
                if any(old[0].get(field) != attempt[field] for field in ('key', 'round', 'tool', 'question_sha256', 'review_page_sha256')):
                    raise Refusal('pending-unreadable')
            else:
                fresh.append(attempt)
        if not fresh:
            return bool(any(row['call_id'] == call for row in attempts))
        if len(attempts) + len(fresh) > 64:
            raise Refusal('pending-unreadable')
        marker['question_attempts'] = [*attempts, *fresh]
        _write_question_marker(runs, secret, pending['session'], marker)
        return True


def _promote_question_answer(runs: Path, secret: bytes, marker: dict, attempt: dict,
                             choice: str, source: dict) -> bool:
    """A bound actual answer proves delivery, not a native permission grant."""
    pending = attempt['round']
    current = _read_pending(pending_path(runs, attempt['key']), secret)
    if (current['nonce'] != pending['nonce'] or canonical(current['page']) != canonical(pending['page'])
            or current.get('session') != pending.get('session')
            or not hmac.compare_digest(str(pending.get('mac', '')), _seal(secret, pending))):
        return False
    rows = _unresolved_issued(runs, secret, marker.get('issued_rounds', []))
    if not isinstance(rows, list) or len(rows) > 64:
        raise Refusal('pending-unreadable')
    existing = next((row for row in rows if row.get('nonce') == pending['nonce']
                     and row.get('issuance', {}).get('key') == attempt['key']), None)
    if existing and existing.get('decision_answer'):
        old = existing['decision_answer']
        return (old.get('choice') == choice and old.get('question_call_id') == attempt['call_id']
                and old.get('question_index') == attempt['question_index'])
    if existing is None and len(rows) == 64:
        raise Refusal('pending-unreadable')
    retained = dict(existing or pending)
    retained.setdefault('issuance', {'origin': 'host-question-answer', 'key': attempt['key'],
        'message_sha256': source.get('prompt_sha256', source.get('response_sha256')),
        'observed_at': source['at'], 'question_call_id': attempt['call_id']})
    retained['decision_answer'] = {'choice': choice, 'question_call_id': attempt['call_id'],
        'question_index': attempt['question_index'], 'question_sha256': attempt['question_sha256'],
        'review_page_sha256': attempt['review_page_sha256'], 'round_nonce': pending['nonce'], 'source': source}
    retained['mac'] = _seal(secret, retained)
    marker['issued_rounds'] = [row for row in rows if row is not existing] + [retained]
    marker['question_attempts'] = [row for row in marker.get('question_attempts', [])
        if (row['call_id'], row['question_index']) != (attempt['call_id'], attempt['question_index'])]
    _write_question_marker(runs, secret, pending['session'], marker)
    return True


def observe_question_reply(runs: Path, secret: bytes, session: str, prompt: str, capture: dict) -> bool:
    """Interpret only a whole genuine host reply envelope bound to a reviewed call.

    The original whole prompt remains the native capture. No synthetic Approve
    event is created and this observer never consumes an event or writes a run.
    """
    if runner_launched() or not isinstance(prompt, str) or len(prompt) > 1_048_576:
        return False
    matched = re.fullmatch(r'\s*<send_user_message_question_reply>\s*(.*?)\s*</send_user_message_question_reply>\s*', prompt, re.DOTALL)
    if matched is None:
        return False
    try:
        replies = json.loads(matched.group(1))
    except ValueError:
        return False
    if not isinstance(replies, list) or not 0 < len(replies) <= 3:
        return False
    if (capture.get('session') != session or capture.get('prompt') != digest(prompt)
            or capture not in capture_events(runs, session)):
        return False
    with _question_mutation(runs, session):
        marker = _question_marker(runs, secret, session)
        attempts = marker.get('question_attempts', [])
        chosen = []
        for reply in replies:
            if not isinstance(reply, dict) or set(reply) != {'questionItemId', 'question', 'answer'}:
                return False
            try:
                identity = json.loads(reply['questionItemId'])
            except (ValueError, TypeError):
                return False
            if (not isinstance(identity, list) or len(identity) != 3 or identity[0] != 'request_user_input_async'
                    or not isinstance(identity[1], str) or type(identity[2]) is not int
                    or not isinstance(reply['answer'], str) or reply['answer'] not in {'Approve', 'Decline'} or not isinstance(reply['question'], str)):
                return False
            matches = [row for row in attempts if (row['tool'], row['call_id'], row['question_index']) == tuple(identity)
                       and row['question_sha256'] == digest(reply['question'])]
            if len(matches) != 1:
                return False
            chosen.append((matches[0], reply['answer']))
        if len({(row[0]['call_id'], row[0]['question_index']) for row in chosen}) != len(chosen):
            return False
        for attempt, choice in chosen:
            source = {'origin': 'host-question-reply', 'session_id': session, 'prompt_sha256': capture['prompt'],
                      'event_id': capture['event_id'], 'at': capture['at']}
            if not _promote_question_answer(runs, secret, marker, attempt, choice, source):
                return False
        return bool(chosen)


def observe_question_result(runs: Path, key: str, secret: bytes, record: dict, payload: dict) -> bool:
    """Observe an explicitly answered post-tool result; pending acknowledgments do not count."""
    parsed = _question_payload(payload)
    if (runner_launched() or parsed is None or payload.get('hook_event_name') not in {'PostToolUse', 'postToolUse'}
            or not isinstance(payload.get('session_id'), str)):
        return False
    response = payload.get('tool_response', payload.get('tool_output'))
    try:
        response = json.loads(response) if isinstance(response, str) and len(response) <= 1_048_576 else response
    except ValueError:
        return False
    if not isinstance(response, dict) or len(canonical(response)) > 1_048_576:
        return False
    outcome = response.get('outcome')
    answered = outcome if isinstance(outcome, dict) else response
    if ((outcome is not None and (outcome.get('outcome') if isinstance(outcome, dict) else outcome) != 'answered')
            or payload.get('is_error') is True
            or any(answered.get(field) for field in ('cancelled', 'canceled', 'isError', 'is_error', 'error'))
            or answered.get('status') in {'cancelled', 'canceled', 'error', 'timeout', 'pending'}):
        return False
    answers = answered.get('answers')
    if not isinstance(answers, dict):
        return False  # Unsupported answer-list/option-ID formats stay explicit gaps.
    path = pending_path(runs, key)
    if not path.is_file() or path.is_symlink():
        return False
    pending = _read_pending(path, secret)
    if not pending_matches_owner(pending, record, payload['session_id']):
        return False
    tool, call, questions = parsed
    with _question_mutation(runs, pending['session']):
        marker = _question_marker(runs, secret, pending['session'])
        chosen = []
        for index, question in enumerate(questions):
            attempt = _question_attempt(pending, key, tool, call, index, question, marker)
            if attempt is None:
                continue
            keys = [question.get(field) for field in ('id', 'header', 'question', 'title', 'prompt')]
            values = [answers[item] for item in keys if isinstance(item, str) and item in answers]
            if not values or any(not isinstance(value, str) or value not in {'Approve', 'Decline'} for value in values) or len(set(values)) != 1:
                return False
            chosen.append((attempt, values[0]))
        if len(chosen) > 1:
            return False  # One native round cannot receive contradictory duplicate questions.
        for attempt, choice in chosen:
            source = {'origin': 'host-question-result', 'session_id': pending['session'], 'tool': tool,
                      'call_id': call, 'response_sha256': digest(json.dumps(response, sort_keys=True)), 'at': _clock()}
            if not _promote_question_answer(runs, secret, marker, attempt, choice, source):
                return False
        return bool(chosen)


def question_decision_valid(runs: Path, pending: dict) -> bool:
    """UI evidence is descriptive only; native authority still requires its owner."""
    answer = pending.get('decision_answer')
    if not isinstance(answer, dict) or answer.get('choice') not in {'Approve', 'Decline'}:
        return False
    source = answer.get('source') or {}
    if (answer.get('round_nonce') != pending.get('nonce') or source.get('session_id') != pending.get('session')
            or not isinstance(answer.get('question_call_id'), str) or not answer['question_call_id']
            or type(answer.get('question_index')) is not int or not 0 <= answer['question_index'] < 3
            or any(not DIGEST_RE.fullmatch(str(answer.get(field, ''))) for field in ('question_sha256', 'review_page_sha256'))
            or type(source.get('at')) not in (int, float) or source['at'] < pending['rendered_at']):
        return False
    if source.get('origin') == 'host-question-reply':
        return any(event.get('event_id') == source.get('event_id') and event.get('prompt') == source.get('prompt_sha256')
            and event.get('at') == source['at'] for event in capture_events(runs, pending['session']))
    return (source.get('origin') == 'host-question-result' and source.get('tool') in QUESTION_TOOLS
            and source.get('call_id') == answer['question_call_id']
            and bool(DIGEST_RE.fullmatch(str(source.get('response_sha256', '')))))


def pending_native_reply(runs: Path, key: str, pending: dict) -> dict | None:
    """Observe an existing exact native reply without consuming or replaying it."""
    if not pending_path(runs, key).is_file():
        return None
    events = capture_events(runs, pending['session'])
    captured = captured_prompts(runs, pending['session'])
    if not any(at is not None and at < pending['rendered_at'] and digest_ not in pending['paste_digests']
               for digest_, at in captured):
        return None
    for event in reversed(events):
        exact = event['prompt'] in pending['paste_digests']
        short = (pending.get('allow_short_reply') and event['prompt'] in SHORT_REPLIES
                 and event.get('question') == {'key': key, 'nonce': pending['nonce']})
        if (type(event.get('at')) in (int, float) and event['at'] >= pending['rendered_at']
                and (exact or short) and event_available(runs, pending['session'], event)):
            return host_capture_context(event, pending['session'])
    return None


def pending_matches_owner(pending: dict, record: dict, observer_session: str) -> bool:
    """An observer may see only its exact resume challenge before ownership changes."""
    return (pending.get('session') == observer_session
        and pending.get('page', {}).get('record_nonce') == record.get('nonce')
        and (observer_session == record.get('session_id') or pending.get('action') == 'resume'))


def resume_target(runs: Path, secret: bytes, session: str) -> tuple[str, dict] | None:
    """Discover a sealed draft target without treating render as delivery or authority."""
    marker = _question_marker(runs, secret, session)
    key = marker.get('key')
    if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', key):
        return None
    path = pending_path(runs, key)
    if not path.is_file() or path.is_symlink():
        return None
    pending = _read_pending(path, secret)
    if (pending.get('action') != 'resume' or pending.get('session') != session
            or pending.get('nonce') != marker.get('nonce')):
        return None
    return key, pending


def issued_requests(runs: Path, key: str, secret: bytes, record: dict,
                    *, observer_session: str | None = None) -> list[dict]:
    """Read current and authenticated historical requests, never borrow owner authority."""
    owner = str(record.get('session_id') or '')
    if not owner:
        return []
    if observer_session is None:
        path = pending_path(runs, key)
        if path.is_file() and not path.is_symlink():
            pending = _read_pending(path, secret)
            if pending.get('action') == 'resume' and pending.get('session') != owner:
                raise Refusal('observer-session-required')
    observer = observer_session or owner
    sessions = [observer]
    if observer == owner:
        for entry in record.get('continuations', []):
            prior = entry.get('from_session')
            if isinstance(prior, str) and prior not in sessions and continuation_ancestor_valid(runs, record, prior, owner):
                sessions.append(prior)
    result = []
    for session in sessions:
        marker = _question_marker(runs, secret, session)
        rows = marker.get('issued_rounds', [])
        if not isinstance(rows, list) or len(rows) > 64:
            raise Refusal('pending-unreadable')
        for row in rows:
            if not isinstance(row, dict) or not hmac.compare_digest(str(row.get('mac', '')), _seal(secret, row)):
                raise Refusal('pending-unreadable')
            issuance = row.get('issuance') or {}
            if (issuance.get('key') == key and issuance.get('origin') in {'host-stop-response', 'host-question-answer'}
                    and row.get('session') == session and row.get('page', {}).get('record_nonce') == record.get('nonce')
                    and (observer == owner or row.get('action') == 'resume')):
                result.append(row)
    return result


def _claim_event(runs: Path, session: str, event: dict) -> None:
    """Single consumption across records, including legacy captures with stable identity."""
    if event.get('_transcript_context') is not None:
        _claim_transcript(runs, event['_transcript_context'], (runs / '.secret').read_bytes())
        return
    identity = digest(json.dumps([session, event.get('event_id'), event.get('at'), event['prompt']]))
    path = runs / 'consumed-prompts' / f'{identity}.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    restrict(path.parent, directory=True)
    try:
        with path.open('x', encoding='utf-8') as handle:
            json.dump({'session': session, 'event_id': event.get('event_id'), 'at': _clock()}, handle)
    except FileExistsError:
        raise Refusal('code-used') from None
    restrict(path, directory=False)


def host_capture_context(event: dict, session: str) -> dict:
    """Mode authority comes from parsed top-level host capture, never env or project config."""
    if event.get('_transcript_context') is not None:
        context = event['_transcript_context']
        if not capture_context_valid(context, session, event['prompt']):
            raise ValueError('invalid typed transcript instruction context')
        return context
    return {'origin': 'host-hook-capture', 'session_id': session,
            'permission_mode': event.get('permission_mode'), 'prompt_sha256': event['prompt'],
            'event_id': event.get('event_id'), 'at': event.get('at')}


# New claims reserve this physical serialized growth for capture, reply and bound
# session metadata. Historical receipts keep their existing provenance validation.
RECOVERY_MAX_BYTES = 1_048_576
RECOVERY_CAPTURE_GROWTH_BYTES = 65_536


def _capture_reservation(pending: dict) -> dict:
    value = dict(pending)
    value.pop('capture', None)
    value.pop('pasted', None)
    value['session'] = None
    return value


def _used_marker(runs: Path, key: str, secret: bytes, pending: dict) -> dict:
    """Build the same sealed retention payload before render and before claim."""
    retained = [row for row in used_recovery_rounds(runs, key, secret)
                if row['nonce'] != pending['nonce']
                and row.get('action') in RECOVERABLE_MINOR_ACTIONS
                and consumed_capture_valid(runs, row.get('capture'), row['rendered_at'])]
    if len(retained) >= 64:
        raise Refusal('recovery-capacity')
    recovery = dict(pending)
    recovery['mac'] = _seal(secret, recovery)
    used = {'action': pending['action'], 'code_sha256': digest(pending['code']),
            'used_at': int(_clock()), 'recovery': recovery, 'prior_recoveries': retained}
    completed = completed_resume_pointer(runs, key, secret)
    if completed is not None:
        used['completed_resume'] = completed
    used['mac'] = _seal(secret, used)
    return used


def _retain_used_round(runs: Path, key: str, secret: bytes, pending: dict) -> None:
    """Refuse before claim if retained evidence cannot fit; never truncate it."""
    used = _used_marker(runs, key, secret, pending)
    base = _used_marker(runs, key, secret, _capture_reservation(pending))
    physical_size = private_serialized_size(used)
    if (physical_size > RECOVERY_MAX_BYTES
            or physical_size - private_serialized_size(base) > RECOVERY_CAPTURE_GROWTH_BYTES):
        raise Refusal('recovery-capacity')
    _write_private(used_path(runs, key), used)


def _read_used_marker(path: Path, secret: bytes) -> dict:
    """Bound actual bytes read even if a file grows after its size check."""
    try:
        info = path.lstat()
        if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400 or info.st_size > RECOVERY_MAX_BYTES:
            raise Refusal('recovery-unreadable')
        with path.open('rb') as stream:
            raw = stream.read(RECOVERY_MAX_BYTES + 1)
        if len(raw) > RECOVERY_MAX_BYTES:
            raise Refusal('recovery-unreadable')
        used = json.loads(raw)
        if (not isinstance(used, dict) or (any(field in used for field in ('recovery', 'prior_recoveries', 'completed_resume'))
                and not hmac.compare_digest(str(used.get('mac', '')), _seal(secret, used)))):
            raise Refusal('recovery-unreadable')
        return used
    except FileNotFoundError:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise Refusal('recovery-unreadable') from exc


def used_recovery_rounds(runs: Path, key: str, secret: bytes) -> list[dict]:
    """Read bounded sealed recovery rounds; old replay markers remain compatible."""
    path = used_path(runs, key)
    try:
        used = _read_used_marker(path, secret)
        if 'recovery' not in used and 'prior_recoveries' not in used:
            return []  # Legacy replay marker has no reusable authority.
        if not hmac.compare_digest(str(used.get('mac', '')), _seal(secret, used)):
            raise Refusal('recovery-unreadable')
        prior = used.get('prior_recoveries', [])
        if not isinstance(prior, list) or len(prior) > 64:
            raise Refusal('recovery-unreadable')
        rows = ([used['recovery']] if isinstance(used.get('recovery'), dict) else []) + prior
        if len(rows) > 65 or len({row.get('nonce') for row in rows if isinstance(row, dict)}) != len(rows):
            raise Refusal('recovery-unreadable')
        for row in rows:
            if (not isinstance(row, dict) or not isinstance(row.get('page'), dict)
                    or not isinstance(row.get('nonce'), str)
                    or not isinstance(row.get('session'), str)
                    or not isinstance(row.get('paste_lines'), list) or not row['paste_lines']
                    or not all(isinstance(line, str) for line in row['paste_lines'])
                    or not isinstance(row.get('paste_digests'), list) or not row['paste_digests']
                    or not all(isinstance(value, str) and DIGEST_RE.fullmatch(value) for value in row['paste_digests'])
                    or not hmac.compare_digest(str(row.get('mac', '')), _seal(secret, row))
                    or not hmac.compare_digest(str(row.get('code', '')), compute_code(secret, row['page'], row['nonce']))):
                raise Refusal('recovery-unreadable')
        return rows
    except FileNotFoundError:
        return []
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise Refusal('recovery-unreadable') from exc


@_transcript_operation
@_round_transaction
def recover_consumed_round(runs: Path, key: str, secret: bytes | None, *, action: str,
                           live_page: dict, session: str, required_session: str | None = None,
                           pasted_line: str | None = None, ancestor_record: dict | None = None,
                           allowed_cwds: set[str] | None = None,
                           historical_cwds: set[str] | None = None,
                           recovery_condition: dict | None = None) -> tuple[dict, str] | None:
    """Finish only an identical already-consumed owner operation; never claim again.

    Opting-in native owners retain their full context checks and lease. Ordinary consume() deliberately continues rejecting replayed approval lines.
    """
    if runner_launched():
        raise Refusal('runner-launched')
    if action not in RECOVERABLE_MINOR_ACTIONS:
        raise Refusal('recovery-not-supported')
    if secret is None:
        return None
    rows = [row for row in used_recovery_rounds(runs, key, secret) if row.get('action') == action
            and consumed_capture_valid(runs, row.get('capture'), row.get('rendered_at'))]
    if not rows:
        return None
    path = pending_path(runs, key)
    if path.exists():
        current = _read_pending(path, secret)
        if current['nonce'] not in {row['nonce'] for row in rows}:
            return None  # A newer genuine round uses ordinary consumption, never recovery.
    exact = [row for row in rows if canonical(row['page']) == canonical(live_page)]
    if not exact:
        raise Refusal('page-changed')
    pending = exact[0]
    bound = pending.get('session')
    if session == 'auto':
        session = required_session or str(bound or '')
    context = pending.get('capture') or {}
    if not session or not bound or context.get('session_id') != bound or (required_session and required_session != session):
        raise Refusal('session-mismatch')
    if bound != session:
        if (action not in {'add-class', 'supplement-v415-authority'} or ancestor_record is None or required_session != session
                or not allowed_cwds or not continuation_ancestor_valid(runs, ancestor_record, bound, session)):
            raise Refusal('session-mismatch')
        try:
            current = current_host_context(runs, ancestor_record, allowed_cwds, historical_cwds=historical_cwds)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise Refusal('approval-not-captured') from exc
        if not full_access_authorization(ancestor_record, current):
            raise Refusal('approval-not-captured')
    if action == 'resume':
        if recovery_condition is None or pending.get('recovery_condition') != recovery_condition:
            raise Refusal('recovery-condition-changed')
        if not claimed_resume_context_valid(runs, pending, allowed_cwds or set()):
            raise Refusal('recovery-context-changed')
    wanted = set(pending.get('paste_digests', []))
    if pending.get('allow_short_reply') and pending.get('pasted') in ('Approve', 'Yes', 'Continue'):
        wanted.add(digest(pending['pasted']))
    if context.get('prompt_sha256') not in wanted:
        raise Refusal('approval-not-captured')
    proof = context.get('transcript_proof')
    if proof is not None and any(proof.get(field) != expected for field, expected in {
            'key': key, 'round_nonce': pending['nonce'], 'action': action,
            'page_sha256': hashlib.sha256(canonical(live_page)).hexdigest(), 'rendered_at': pending['rendered_at']}.items()):
        raise Refusal('approval-not-captured')
    if pasted_line is not None and normalize(pasted_line) not in {
            normalize(line) for line in [*pending['paste_lines'], pasted(pending)]}:
        raise Refusal('approval-not-captured')
    if context.get('origin') != 'codex-host-transcript':
        # A legacy global hook receipt does not prove which owner claimed it.
        # Keep historical validation and the unresolved request; never infer ownership.
        raise Refusal('recovery-claim-owner-unavailable')
    if path.exists():
        current = _read_pending(path, secret)
        if current['nonce'] != pending['nonce']:
            raise Refusal('code-superseded')
        path.unlink()  # The claim already exists; only the same retained round may be removed.
    return pending, session


def completed_resume_pointer(runs: Path, key: str, secret: bytes) -> dict | None:
    """A bounded pointer identifies an already-verified resume in signed native history."""
    used_recovery_rounds(runs, key, secret)
    path = used_path(runs, key)
    try:
        used = _read_used_marker(path, secret)
    except FileNotFoundError:
        return None
    value = used.get('completed_resume')
    if value is None:
        return None
    if (not hmac.compare_digest(str(used.get('mac', '')), _seal(secret, used))
            or not isinstance(value, dict) or set(value) != {'round_nonce', 'record_nonce', 'page_sha256', 'capture_sha256', 'session', 'sequence'}
            or not re.fullmatch(r'[0-9a-f]{32}', str(value.get('round_nonce')))
            or not all(isinstance(value.get(field), str) and value[field] for field in ('record_nonce', 'session'))
            or not all(DIGEST_RE.fullmatch(str(value.get(field))) for field in ('page_sha256', 'capture_sha256'))
            or type(value.get('sequence')) is not int or value['sequence'] < 1):
        raise Refusal('recovery-unreadable')
    return value


@_round_transaction
def retire_used_recovery(runs: Path, key: str, secret: bytes, pending: dict, *, resume_sequence: int | None = None) -> None:
    """Drop one recovery only after the native owner freshly verifies saved success."""
    rows = used_recovery_rounds(runs, key, secret)
    if not any(row['nonce'] == pending['nonce'] and row == pending for row in rows):
        return
    path = used_path(runs, key)
    used = _read_used_marker(path, secret)
    if pending['action'] == 'resume':
        if type(resume_sequence) is not int or resume_sequence < 1:
            raise Refusal('recovery-unreadable')
        previous = completed_resume_pointer(runs, key, secret)
        if (previous is None or previous['record_nonce'] != pending['page']['record_nonce']
                or previous['sequence'] <= resume_sequence):
            used['completed_resume'] = {'round_nonce': pending['nonce'], 'record_nonce': pending['page']['record_nonce'],
                'page_sha256': hashlib.sha256(canonical(pending['page'])).hexdigest(),
                'capture_sha256': hashlib.sha256(canonical(pending['capture'])).hexdigest(),
                'session': pending['session'], 'sequence': resume_sequence}
    if isinstance(used.get('recovery'), dict) and used['recovery']['nonce'] == pending['nonce']:
        used.pop('recovery')
    used['prior_recoveries'] = [row for row in used.get('prior_recoveries', []) if row['nonce'] != pending['nonce']]
    used['mac'] = _seal(secret, used)
    _write_private(path, used)
    current_path = pending_path(runs, key)
    if current_path.exists():
        current = _read_pending(current_path, secret)
        if current['nonce'] == pending['nonce'] and current['page'] == pending['page']:
            current_path.unlink()


def consumed_issued_request(runs: Path, key: str, secret: bytes, pending: dict) -> dict | None:
    """A consumed round is internal owner work, never another manual paste."""
    for recovery in used_recovery_rounds(runs, key, secret):
        if (all(recovery.get(field) == pending.get(field) for field in ('session', 'nonce', 'action', 'page', 'rendered_at'))
                and consumed_capture_valid(runs, recovery.get('capture'), pending['rendered_at'])):
            return recovery['capture']
    return None


def consumed_capture_valid(runs: Path, context: object, rendered_at: object) -> bool:
    """Check retained host provenance against its persistent single-consumption receipt."""
    if isinstance(context, dict) and context.get('origin') == 'codex-host-transcript':
        return _transcript_receipt_valid(runs, context, rendered_at)
    fields = {"origin", "session_id", "permission_mode", "prompt_sha256", "event_id", "at"}
    if (not isinstance(context, dict) or set(context) != fields or context["origin"] != "host-hook-capture"
            or not isinstance(context["session_id"], str) or not context["session_id"]
            or not DIGEST_RE.fullmatch(str(context["prompt_sha256"]))):
        return False
    at = context["at"]
    if (type(at) not in (int, float) or type(rendered_at) not in (int, float)
            or not float("-inf") < at < float("inf") or not float("-inf") < rendered_at < float("inf")
            or at < rendered_at):
        return False
    session = context["session_id"]
    for event in capture_events(runs, session):
        if host_capture_context(event, session) != context:
            continue
        identity = digest(json.dumps([session, event.get("event_id"), event.get("at"), event["prompt"]]))
        try:
            receipt = json.loads((runs / "consumed-prompts" / (identity + ".json")).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        return isinstance(receipt, dict) and receipt.get("session") == session and receipt.get("event_id") == event.get("event_id")
    return False


def append_continuation(record: dict, pending: dict, session: str, *, retain_hook: bool = False) -> None:
    """Retain original consent while authenticating a new native owning-session binding."""
    context = pending.get('capture')
    if not record.get('continuations') and not retain_hook and (not isinstance(context, dict) or context.get('origin') != 'codex-host-transcript'):
        return
    if not capture_context_valid(context, session):
        raise ValueError('continuation requires retained native capture provenance')
    record['continuation_format'] = 1
    record.setdefault('continuations', []).append({
        'from_session': record['session_id'], 'to_session': session, 'record_nonce': record['nonce'],
        'page': pending['page'], 'round_nonce': pending['nonce'], 'capture': context,
        'rendered_at': pending['rendered_at']})


def retain_transcript_decision(record: dict, pending: dict) -> bool:
    """Sign source participation for decisions whose legacy state was otherwise unsigned."""
    context = pending.get('capture')
    if not isinstance(context, dict) or context.get('origin') != 'codex-host-transcript':
        return False
    if not capture_context_valid(context):
        raise ValueError('decision requires typed native capture provenance')
    entry = {'record_nonce': record['nonce'], 'action': pending['action'], 'page': pending['page'],
             'round_nonce': pending['nonce'], 'rendered_at': pending['rendered_at'],
             'session_id': context['session_id'], 'capture': context}
    history = record['approvals'].setdefault('transcript_decisions', [])
    if history and history[-1] == entry:
        return False
    history.append(entry)
    return True


def transcript_decisions_valid(record: dict) -> bool:
    approvals = record.get('approvals') or {}
    if not isinstance(approvals, dict):
        return False
    if 'transcript_decisions' not in approvals:
        return True
    entries = approvals['transcript_decisions']
    if not isinstance(entries, list) or not entries:
        return False
    seen = set()
    for entry in entries:
        if (not isinstance(entry, dict) or set(entry) != {'record_nonce', 'action', 'page', 'round_nonce',
                'rendered_at', 'session_id', 'capture'} or entry['record_nonce'] != record.get('nonce')
                or not isinstance(entry['page'], dict) or entry['page'].get('action') != entry['action']
                or not capture_context_valid(entry['capture'], entry['session_id'])
                or entry['capture']['origin'] != 'codex-host-transcript'):
            return False
        context, proof = entry['capture'], entry['capture']['transcript_proof']
        page_nonce = entry['page'].get('record_nonce')
        nonce_bound = (entry['record_nonce'] == entry['round_nonce'] if entry['action'] == 'create' else
                       entry['record_nonce'] in page_nonce.split(',') if entry['action'] == 'retire' and isinstance(page_nonce, str) else
                       entry['record_nonce'] == page_nonce)
        if (proof['action'] != entry['action'] or proof['round_nonce'] != entry['round_nonce']
                or proof['rendered_at'] != entry['rendered_at']
                or proof['page_sha256'] != hashlib.sha256(canonical(entry['page'])).hexdigest()
                or not nonce_bound or context['event_id'] in seen):
            return False
        seen.add(context['event_id'])
    return True


def transcript_records_present(record: dict) -> bool:
    """Only recognized strict provenance locations activate the new signing domain."""
    approvals = record.get('approvals') or {}
    if not isinstance(approvals, dict):
        return False
    candidates = [approvals.get('authorization_context')]
    for name, field in (('continuations', 'capture'),):
        candidates.extend(entry.get(field) for entry in record.get(name, []) if isinstance(entry, dict))
    candidates.extend(entry.get('capture') for entry in approvals.get('transcript_decisions', []) if isinstance(entry, dict))
    candidates.extend(entry.get('current_host_context') for entry in approvals.get('policy_adoptions', []) if isinstance(entry, dict))
    classes = approvals.get('classes', [])
    if isinstance(classes, list):
        candidates.extend(entry['added'].get('authorization_context')
                          for entry in classes if isinstance(entry, dict) and isinstance(entry.get('added'), dict))
    histories = [record.get('minor_amendments', []), record.get('minor_execution_permissions', []), record.get('member_checkpoint_reconciliations', [])]
    member_fields = ('historical_scope_supplements', 'manifest_coordinator_permissions', 'v415_coordinator_permissions',
                     'v415_ci_read_corrections', 'member_read_corrections', 'member_path_permissions', 'implementation_withdrawals')
    for member in [*record.get('members', []), *record.get('minor_amendment_members', [])]:
        if isinstance(member, dict):
            histories.extend(member.get(name, []) for name in member_fields)
    for history in histories:
        if isinstance(history, list):
            candidates.extend(entry['accepted'].get('authorization_context') for entry in history
                              if isinstance(entry, dict) and isinstance(entry.get('accepted'), dict))
    return any(capture_context_valid(value) and value['origin'] == 'codex-host-transcript' for value in candidates)


def continuation_history_valid(record: dict) -> bool:
    present = ('continuation_format' in record, 'continuations' in record)
    if not any(present):
        return True
    if (not all(present) or type(record['continuation_format']) is not int or record['continuation_format'] != 1
            or not isinstance(record['continuations'], list) or not record['continuations']):
        return False
    previous = None
    seen = set()
    for entry in record['continuations']:
        if (not isinstance(entry, dict) or set(entry) != {'from_session', 'to_session', 'record_nonce',
                'page', 'round_nonce', 'capture', 'rendered_at'}
                or not all(isinstance(entry[name], str) and entry[name] for name in ('from_session', 'to_session'))
                or entry['record_nonce'] != record.get('nonce')
                or not isinstance(entry['page'], dict) or entry['page'].get('action') != 'resume'
                or entry['page'].get('record_nonce') != record.get('nonce')
                or not re.fullmatch(r'[0-9a-f]{32}', str(entry['round_nonce']))
                or not capture_context_valid(entry['capture'], entry['to_session'])
                or type(entry['rendered_at']) not in (int, float)
                or type(entry['capture']['at']) not in (int, float)
                or not float('-inf') < entry['rendered_at'] <= entry['capture']['at'] < float('inf')
                or (previous is not None and entry['from_session'] != previous)):
            return False
        context = entry['capture']
        identity = (context['origin'], context['event_id'], context['at'], context['prompt_sha256'])
        if identity in seen:
            return False
        seen.add(identity)
        if context['origin'] == 'codex-host-transcript':
            proof = context['transcript_proof']
            if (proof['action'] != 'resume' or proof['round_nonce'] != entry['round_nonce']
                    or proof['page_sha256'] != hashlib.sha256(canonical(entry['page'])).hexdigest()
                    or proof['rendered_at'] != entry['rendered_at']):
                return False
        previous = entry['to_session']
    return previous == record.get('session_id')


def continuation_ancestor_valid(runs: Path, record: dict, from_session: str, to_session: str) -> bool:
    """Verify signed minor ancestry and every consumed resume, without granting authority.

    Callers still resolve the full native operational record and current context before executing an operation.
    """
    try:
        import check_plan_completion as ck
    except ImportError:
        return False
    try:
        secret = ck._secret(create=False)
        if (record.get('schema') not in (1, 2) or not from_session or to_session != record.get('session_id')
                or runs.resolve() != ck._runs_dir().resolve() or secret is None
                or not hmac.compare_digest(str(record.get('approvals_hmac', '')), ck._sign(record, secret,
                    minor_protocol=ck.MINOR_AMENDMENT_PROTOCOL, execution_protocol=ck.MINOR_EXECUTION_PROTOCOL))
                or not continuation_history_valid(record)):
            return False
        if record['schema'] == 1:
            ctx = ck.Context(str(Path(record['repo_root']) / record['plan']), ck.Budget(15))
            loaded = ck.load_record(ctx, None)
            if loaded.record is None or canonical(loaded.record) != canonical(record):
                return False
            scope = {'kind': 'plan', 'plan': ctx.rel, 'version': ctx.version}
        else:
            scope = {'kind': 'minor', 'minor': record.get('minor')}
        found = False
        for entry in record.get('continuations', []):
            if (entry['page'].get('scope') != scope
                    or not consumed_capture_valid(runs, entry['capture'], entry['rendered_at'])):
                return False
            if entry['from_session'] == from_session:
                found = True
        return from_session == to_session or (found and bool(record.get('continuations'))
            and record['continuations'][-1]['to_session'] == to_session)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RuntimeError, ck.Malformed):
        return False


def check_continuation_write(runs: Path, previous: dict, record: dict) -> None:
    """Every writer preserves the authenticated ordered prefix; only a consumed resume appends."""
    old, new = previous.get('continuations', []), record.get('continuations', [])
    if (not continuation_history_valid(record) or not isinstance(old, list)
            or not isinstance(new, list) or new[:len(old)] != old or len(new) not in (len(old), len(old) + 1)
            or (old and record.get('continuation_format') != previous.get('continuation_format'))):
        raise ValueError('continuation history must remain an unchanged ordered prefix')
    if len(new) == len(old) + 1:
        entry = new[-1]
        if (entry['from_session'] != previous.get('session_id')
                or not consumed_capture_valid(runs, entry['capture'], entry['rendered_at'])):
            raise ValueError('continuation append lacks its genuine consumed decision')
    elif old and record.get('session_id') != previous.get('session_id'):
        raise ValueError('session rebinding requires append-only continuation provenance')
    old_decisions = (previous.get('approvals') or {}).get('transcript_decisions', [])
    new_decisions = (record.get('approvals') or {}).get('transcript_decisions', [])
    if (not transcript_decisions_valid(record) or not isinstance(old_decisions, list)
            or new_decisions[:len(old_decisions)] != old_decisions
            or len(new_decisions) not in (len(old_decisions), len(old_decisions) + 1)):
        raise ValueError('native transcript decision history must remain append-only')
    if len(new_decisions) > len(old_decisions):
        entry = new_decisions[-1]
        if not consumed_capture_valid(runs, entry['capture'], entry['rendered_at']):
            raise ValueError('native transcript decision lacks its genuine consumption receipt')


def _record_host_binding(record: dict) -> dict:
    if not continuation_history_valid(record) or not transcript_decisions_valid(record):
        raise ValueError('native transcript provenance is invalid')
    session = record.get('session_id')
    original = (record.get('approvals') or {}).get('authorization_context') or {}
    candidates = [original, *(entry['capture'] for entry in record.get('continuations', [])),
                  *(entry['capture'] for entry in (record.get('approvals') or {}).get('transcript_decisions', []))]
    candidates = [value for value in candidates if isinstance(value, dict) and value.get('session_id') == session]
    return max(candidates, key=lambda value: _timestamp(value.get('at', 0))) if candidates else original


@_transcript_operation
def _transcript_current_context(runs: Path, context: dict, allowed_cwds: set[str]) -> dict:
    proof = context['transcript_proof']
    if not consumed_capture_valid(runs, context, proof['rendered_at']):
        raise ValueError('retained transcript proof is unavailable')
    source = proof['source']
    path = _transcript_path(Path(source['path']), context['session_id'])
    info = path.stat()
    scanned = _read_transcript(path, context['session_id'], allowed_cwds,
                               prefix_length=source['prefix_length'], selected_offset=proof['event_offset'])
    selected = scanned['selected_event']
    current = scanned['current']
    if (scanned['partial'] or (info.st_dev, info.st_ino) != (source['device'], source['inode'])
            or scanned['source_identity'] != (source['device'], source['inode'])
            or scanned['complete_length'] < source['prefix_length']
            or scanned['anchored_prefix_sha256'] != source['prefix_sha256']
            or selected is None or selected['sha256'] != proof['event_sha256']
            or selected['prompt_sha256'] != context['prompt_sha256'] or current['permission_mode'] != 'bypassPermissions'):
        raise ValueError('current transcript no longer establishes full-access authority')
    return {**context, **current}

def full_access_authorization(record: dict, context: dict | None = None) -> bool:
    """The caller must first verify the signed run; legacy records default conservative."""
    if context is None and (record.get('continuations') or (record.get('approvals') or {}).get('transcript_decisions')):
        context = _record_host_binding(record)
    context = context if context is not None else record.get('approvals', {}).get('authorization_context') or {}
    return (context.get('origin') in {'host-hook-capture', 'codex-host-transcript'}
            and context.get('permission_mode') == 'bypassPermissions'
            and context.get('session_id') == record.get('session_id'))


def validate_policy(value: object) -> dict:
    """An explicit, reviewable policy cannot add destinations, members or spending caps."""
    if not isinstance(value, dict) or not set(value) <= {'corrections', 'planned_actions', 'correction_paths'}:
        raise ValueError('policy holds corrections, correction_paths and planned_actions only')
    if value.get('corrections') not in (None, 'within-approved-scope'):
        raise ValueError('unknown correction policy')
    actions = value.get('planned_actions', [])
    if not isinstance(actions, list):
        raise ValueError('planned_actions must be a list')  # noqa: TRY004 - malformed JSON uses one controlled validation error
    correction_paths = value.get('correction_paths', [])
    if not isinstance(correction_paths, list):
        raise ValueError('correction_paths must be a list')  # noqa: TRY004 - malformed JSON uses one controlled validation error
    checks = [*actions, *([{'class': 'ask-first:correction', 'paths': correction_paths}] if correction_paths else [])]
    for item in checks:
        if not isinstance(item, dict) or set(item) != {'class', 'paths'}:
            raise ValueError('a planned action needs class and paths')
        name, paths = item['class'], item['paths']
        if not isinstance(name, str) or not (name == 'ci-security-change' or re.fullmatch(r'ask-first:[a-z][a-z0-9-]*', name)):
            raise ValueError('unsupported planned action class')
        if not isinstance(paths, list) or not paths:
            raise ValueError('a planned action needs literal repository paths')
        for path in paths:
            if (not isinstance(path, str) or not path or '\\' in path or ':' in path
                    or path.startswith('/') or any(part in {'', '.', '..'} for part in path.split('/'))
                    or any(char in path for char in '*?[')):
                raise ValueError('planned paths must be literal relative repository paths')
    return {'corrections': value.get('corrections'), 'planned_actions': actions, 'correction_paths': correction_paths}


def blocker_fingerprint(entry: dict) -> str:
    return hashlib.sha256(canonical({key: entry.get(key) for key in
        ('category', 'version', 'approval_class', 'request', 'purpose', 'why', 'evidence')})).hexdigest()


def add_blocker(record: dict, entry: dict) -> int:
    """Same open condition reuses its index; changed evidence invalidates its challenge."""
    blockers = record.setdefault('blockers', [])
    scope = ('category', 'version', 'approval_class', 'request')
    for index, old in enumerate(blockers):
        if isinstance(old, dict) and old.get('open') and all(old.get(k) == entry.get(k) for k in scope):
            fields = ('evidence', 'purpose', 'why')
            if any(old.get(key) != entry.get(key) for key in fields):
                old.update({key: entry.get(key) for key in fields}, at=entry['at'])
            return index
    blockers.append(entry)
    return len(blockers) - 1


def authorization(record: dict, approval_class: str, request: dict, context: dict | None = None) -> dict:
    """Report existing authority only; this probe spends no retry or money budget."""
    if not full_access_authorization(record, context):
        raise ValueError('trusted full-access authorization is unavailable')
    approvals = record.get('approvals') or {}
    if approval_class == 'release' and approvals.get('conditional_outcome') is not None:
        raise ValueError('a captured decline does not authorize a release')
    policy = validate_policy(approvals.get('autonomy_policy') or {})
    entries = [item for item in approvals.get('classes', []) if item.get('class') == approval_class]
    if not isinstance(request, dict):
        raise ValueError('request must be an object')  # noqa: TRY004 - malformed JSON uses one controlled validation error
    identity = {key: approvals.get(key) for key in ('repo', 'remote_url', 'push_remote_url',
                'source_branch', 'target_branch', 'release_version', 'tag')}
    permitted = set(identity) | {'paths', 'locally_reproduced', 'verified'}
    if not set(request) <= permitted:
        raise ValueError('request contains an unapproved scope field')
    if any(request[key] != identity[key] for key in set(request) & set(identity)):
        raise ValueError('request differs from the frozen approval scope')
    planned = [item for item in policy['planned_actions'] if item['class'] == approval_class]
    if planned:
        paths = request.get('paths')
        allowed = {path for item in planned for path in item['paths']}
        if not isinstance(paths, list) or not paths or not all(isinstance(path, str) for path in paths) or not set(paths) <= allowed:
            raise ValueError('request is outside the explicitly approved planned paths')
    elif not entries and not (approval_class == 'repush' and policy['corrections'] == 'within-approved-scope'
                              and any(item.get('class') == 'push-merge' for item in approvals.get('classes', []))):
        raise ValueError('action is outside the approved plan')
    correction = approval_class == 'repush' and policy['corrections'] == 'within-approved-scope'
    if correction:
        paths = request.get('paths')
        if not isinstance(paths, list) or not paths or not all(isinstance(path, str) for path in paths) or not set(paths) <= set(policy['correction_paths']):
            raise ValueError('correction paths are outside the approved correction scope')
    if approval_class == 'repush' and (request.get('locally_reproduced') is not True or request.get('verified') is not True):
        raise ValueError('a correction still requires local reproduction and fresh verification')
    return {'origin': 'approved-plan', 'class': approval_class, 'request': request,
            'scope': identity, 'bounds': [item.get('bound') for item in entries],
            'counters_consumed': False, 'consent_bound': None if correction else [item.get('bound') for item in entries],
            'verification_and_spend_limits_unchanged': True, 'authorization_prompt_sha256':
                (approvals.get('authorization_context') or {}).get('prompt_sha256')}



def _timestamp(value: object) -> float:
    import datetime
    import math
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise ValueError('invalid evidence timestamp')
        return float(value)
    if isinstance(value, str):
        return datetime.datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()  # noqa: FURB162 - Python 3.10 compatibility
    raise ValueError('missing evidence timestamp')


@_transcript_operation
def codex_transcript_context(path: Path, session: str, event: dict, allowed_cwds: set[str],
                             *, historical_cwds: set[str] | None = None) -> dict:
    """Corroborate an existing capture against its real runtime-owned Codex transcript.

    This adapter supports the locally verified vscode format only. A supplied path
    selects evidence; it does not supply permission values or an approval receipt.
    """
    root = Path.home() / '.codex' / 'sessions'
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError('host transcript must be a canonical Codex session log')
    if not resolved.name.endswith(f'-{session}.jsonl'):
        raise ValueError('host transcript filename does not match the bound session')
    meta = context = None
    matched = None
    with resolved.open(encoding='utf-8') as handle:
        for line in handle:
            _check_transcript_deadline()
            try:
                row = json.loads(line)
            except ValueError:
                continue  # a live append may end in one unfinished JSON line
            if not isinstance(row, dict):
                continue
            payload = row.get('payload')
            if not isinstance(payload, dict):
                continue
            if row.get('type') == 'session_meta':
                meta = payload
            elif row.get('type') == 'turn_context':
                context = payload
            elif row.get('type') == 'event_msg' and payload.get('type') == 'user_message':
                message = payload.get('message')
                if not isinstance(message, str) or digest(message) != event['prompt']:
                    continue
                at = _timestamp(row.get('timestamp'))
                if abs(at - _timestamp(event.get('at'))) > 10:
                    continue
                if (not isinstance(meta, dict) or meta.get('id') != session
                        or meta.get('originator') != 'codex_vscode' or meta.get('source') != 'vscode'
                        or not isinstance(context, dict) or context.get('approval_policy') != 'never'
                        or context.get('sandbox_policy') != {'type': 'danger-full-access'}
                        or str(Path(str(context.get('cwd', ''))).resolve()) not in (allowed_cwds | (historical_cwds or set()))):
                    raise ValueError('host transcript does not establish this session full-access context')
                matched = {'origin': 'codex-host-transcript', 'session_id': session,
                           'permission_mode': 'bypassPermissions', 'prompt_sha256': event['prompt'],
                           'at': event['at'], 'transcript_event_at': row['timestamp'],
                           'transcript_path': str(resolved), 'event_id': event.get('event_id')}
    # Permission may change after the instruction: inspect the latest actual turn context.
    if matched is not None and (not isinstance(context, dict) or context.get('approval_policy') != 'never'
            or context.get('sandbox_policy') != {'type': 'danger-full-access'}
            or str(Path(str(context.get('cwd', ''))).resolve()) not in allowed_cwds):
        matched['permission_mode'] = 'manual'
    if matched is None:
        raise ValueError('genuine user capture was not corroborated in the host transcript')
    return matched


def policy_adoption_declaration(record: dict, policy: dict) -> str:
    """Render the exact user declaration binding this run to its validated policy."""
    # Hook digests normalize whitespace, so JSON string spaces must remain distinct.
    encoded = canonical(validate_policy(policy)).decode('utf-8').replace(' ', r'\u0020')
    return f"Adopt autonomy policy for run {record['nonce']}: {encoded}"


@_transcript_operation
def adopt_policy(runs: Path, record: dict, instruction: str, policy: dict,
                 transcript: Path | None = None, allowed_cwds: set[str] | None = None,
                 *, historical_cwds: set[str] | None = None) -> None:
    """Bind declared policy intent and independently current mode, without NLP inference."""
    policy = validate_policy(policy)
    session = str(record.get('session_id') or '')
    matches = [event for event in capture_events(runs, session)
               if event['prompt'] == digest(instruction)]
    if not matches:
        selected = _transcript_instruction(runs, record, instruction, policy, allowed_cwds or set())
        matches = [selected] if selected is not None else []
    if not matches:
        raise ValueError('instruction must equal a genuine whole user capture')
    matches = [event for event in matches
               if _timestamp(event.get('at')) > _timestamp(record.get('created'))]
    if not matches:
        raise ValueError('policy adoption requires a user instruction after run creation')
    approvals = record['approvals']
    prior = approvals.get('policy_adoptions') or []
    available = [event for event in matches if event_available(runs, session, event)]
    current_adoption = prior[-1] if prior else {}
    retries = [event for event in matches
               if approvals.get('autonomy_policy') == policy
               and current_adoption.get('prompt_sha256') == event['prompt']
               and current_adoption.get('event_id') == event.get('event_id')
               and current_adoption.get('at') == event.get('at')
               and current_adoption.get('policy') == policy]
    candidates = available or retries
    if not candidates:
        raise Refusal('code-used')
    if len(candidates) != 1:
        raise ValueError('instruction matches multiple eligible genuine captures')
    event = candidates[0]
    retry = not available
    if not retry:
        if event.get('question'):
            raise ValueError('a question-bound reply cannot declare a new autonomy policy')
        if instruction != policy_adoption_declaration(record, policy):
            raise ValueError('policy adoption requires the exact run-bound policy declaration')
    context = host_capture_context(event, session)
    if context.get('permission_mode') != 'bypassPermissions':
        if transcript is None:
            raise ValueError('trusted host permission evidence is unavailable')
        context = codex_transcript_context(transcript, session, event, allowed_cwds or set(), historical_cwds=historical_cwds)
    if context.get('permission_mode') != 'bypassPermissions':
        raise ValueError('current host mode requires a genuine manual decision')
    # Selected instruction provenance is not proof of the latest permission mode.
    view = {**record, 'approvals': {**approvals, 'authorization_context': context}}
    current = current_host_context(runs, record if context.get('transcript_proof') is not None else view,
                                   allowed_cwds or set(), historical_cwds=historical_cwds)
    if not full_access_authorization(record, current):
        raise ValueError('current trusted full-access evidence is unavailable')
    # Only an identical same-record retry may reuse already-consumed provenance.
    if retry:
        return
    if event.get('_transcript_context') is not None:
        latest = _transcript_instruction(runs, record, instruction, policy, allowed_cwds or set())
        if latest != event:
            raise ValueError('a newer runtime user event superseded the policy instruction')
    _claim_event(runs, session, event)
    approvals['authorization_context'] = context
    approvals['autonomy_policy'] = policy
    approvals.setdefault('policy_adoptions', []).append({
        'origin': 'captured-user-instruction', 'prompt_sha256': event['prompt'],
        'event_id': event.get('event_id'), 'at': event['at'], 'policy': policy,
        'current_host_context': current})


@_transcript_operation
def user_continuation(runs: Path, record: dict, index: int, fingerprint: str,
                      allowed_cwds: set[str], *, historical_cwds: set[str] | None = None) -> dict:
    """Resume one legacy hook stop from a fresh user turn, never claim technical repair."""
    blockers = record.get('blockers') or []
    if (record.get('pause') or not 0 <= index < len(blockers)
            or not all(isinstance(item, dict) for item in blockers)
            or sum(bool(item.get('open')) for item in blockers) != 1):
        raise ValueError('continuation requires exactly one open blocker and no pause')
    entry = blockers[index]
    if (entry.get('open') is not True or blocker_fingerprint(entry) != fingerprint
            or set(entry) - {'at', 'category', 'evidence', 'open'}
            or entry.get('category') != 'no-progress'
            or not re.fullmatch(r'progress score unchanged over [1-9][0-9]* refusals: \S[^\r\n]*',
                                str(entry.get('evidence', '')))):
        raise ValueError('only the unchanged legacy hook no-progress stop can resume')
    policy = validate_policy(record.get('approvals', {}).get('autonomy_policy'))
    if policy.get('corrections') != 'within-approved-scope':
        raise ValueError('the signed plan does not authorize scoped correction continuation')
    session = str(record.get('session_id') or '')
    events = capture_events(runs, session)
    if not events or events[-1]['prompt'] != digest('Continue'):
        raise ValueError('the latest whole user capture must be Continue')
    event = events[-1]
    identity = digest(json.dumps([session, event.get('event_id'), event.get('at'), event['prompt']]))
    at = _timestamp(event.get('at'))
    identities = [digest(json.dumps([session, item.get('event_id'), item.get('at'), item['prompt']]))
                  for item in events]
    if (identities.count(identity) != 1
            or not max(_timestamp(entry.get('at')), _timestamp(record.get('created'))) < at <= _clock()
            or any(_timestamp(item.get('at')) > at for item in events)):
        raise ValueError('continuation needs a unique fresh nonfuture user event')
    if not event_available(runs, session, event):
        raise Refusal('code-used')
    captured_question = event.get('question') or {}
    if captured_question:
        key = captured_question.get('key') if isinstance(captured_question, dict) else None
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', key):
            raise ValueError('captured manual question provenance is unavailable')
        if pending_path(runs, key).exists():
            raise ValueError('the captured Continue answers a pending manual question')
    question = question_path(runs, session)
    if question.exists():
        active = json.loads(question.read_text(encoding='utf-8'))
        secret = (runs / '.secret').read_bytes()
        if (not isinstance(active, dict) or active.get('session') != session
                or not isinstance(active.get('key'), str)
                or not re.fullmatch(r'[A-Za-z0-9_-]+', active['key'])
                or not hmac.compare_digest(str(active.get('mac', '')), _seal(secret, active))):
            raise ValueError('active manual question provenance is unavailable')
        # A consumed create/answer leaves its question marker; only a pending round competes.
        if pending_path(runs, active['key']).exists():
            raise ValueError('a pending manual question requires its own answer')
    current = current_host_context(runs, record, allowed_cwds, historical_cwds=historical_cwds)
    if not full_access_authorization(record, current):
        raise ValueError('current trusted full-access evidence is unavailable')
    selected = host_capture_context(event, session)
    if selected.get('permission_mode') is None:
        if current.get('origin') != 'codex-host-transcript' or not current.get('transcript_path'):
            raise ValueError('the continuation lacks trusted host permission evidence')
        selected = codex_transcript_context(Path(current['transcript_path']), session, event,
                                           allowed_cwds, historical_cwds=historical_cwds)
    if not full_access_authorization(record, selected):
        raise ValueError('the user continuation was not captured in full-access mode')
    if capture_events(runs, session) != events:
        raise ValueError('a newer user capture superseded the continuation')
    _claim_event(runs, session, event)
    return {'origin': 'existing-approved-plan-user-continuation', 'event_id': event.get('event_id'),
            'event_identity_sha256': identity,
            'prompt_sha256': event['prompt'], 'at': event['at'], 'fingerprint': fingerprint,
            'policy': policy, 'capture_context': selected, 'current_host_context': current,
            'native_predicates_changed': False, 'technical_repair_claimed': False}


def resolution(record: dict, index: int, fingerprint: str, evidence_file: Path | None, context: dict | None = None) -> dict:
    """Resolve a repaired condition, preserving real predicates and honest evidence provenance."""
    if not full_access_authorization(record, context):
        raise ValueError('trusted full-access authorization is unavailable')
    blockers = record.get('blockers') or []
    if not 0 <= index < len(blockers) or not isinstance(blockers[index], dict):
        raise ValueError('no blocker at that index')
    entry = blockers[index]
    if not entry.get('open') or blocker_fingerprint(entry) != fingerprint:
        raise ValueError('blocker is closed or its condition changed')
    category = entry.get('category')
    if category in {'approval-not-covered', 'ci-security-change'}:
        name = entry.get('approval_class') or category
        covered = authorization(record, name, entry.get('request') or {}, context)
        return {'origin': 'existing-plan-authorization', 'fingerprint': fingerprint, 'coverage': covered}
    if category not in {'unreproducible-red-check', 'platform-unavailable', 'no-progress'}:
        raise ValueError('this condition requires a genuine manual decision')
    if evidence_file is None:
        raise ValueError('a fresh condition-repair receipt is required')
    raw = evidence_file.read_bytes()
    proof = json.loads(raw)
    if (not isinstance(proof, dict) or proof.get('condition') != fingerprint
            or type(proof.get('exit_code')) is not int or proof['exit_code'] != 0
            or not isinstance(proof.get('command'), list) or not proof['command']
            or not all(isinstance(item, str) and item for item in proof['command'])
            or _timestamp(proof.get('completed_at')) < _timestamp(entry.get('at'))
            or _timestamp(proof.get('completed_at')) > _clock() + 5):
        raise ValueError('repair receipt does not establish a fresh successful probe for this condition')
    expected = (entry.get('request') or {}).get('verification') or {}
    if not isinstance(expected, dict) or expected.get('command') != proof['command']:
        raise ValueError('repair receipt does not rerun the recorded failing probe')
    output = Path(str(proof.get('output_path', '')))
    if not output.is_file() or hashlib.sha256(output.read_bytes()).hexdigest() != proof.get('output_sha256'):
        raise ValueError('repair receipt output is absent or changed')
    return {'origin': 'agent-verification-receipt', 'fingerprint': fingerprint,
            'receipt_sha256': hashlib.sha256(raw).hexdigest(), 'receipt_path': str(evidence_file.resolve()),
            'probe': proof, 'native_predicates_changed': False}



def _observed_hook_context(runs: Path, session: str, *, strict: bool = False) -> dict:
    """Observe genuine hook mode evidence without granting any execution authority."""
    events = capture_events(runs, session)
    current = host_capture_context(events[-1], session) if events else {}
    path = runs / 'host-context' / f'{hashlib.sha256(session.encode()).hexdigest()}.json'
    try:
        info = path.lstat()
        if strict and (path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400 or info.st_size > 65536):
            raise ValueError('current hook context cannot be verified')
    except FileNotFoundError:
        return current
    except (OSError, ValueError):
        if strict:
            raise ValueError('current hook context cannot be verified') from None
        return current
    try:
        observed = json.loads(path.read_text(encoding='utf-8'))
        secret = (runs / '.secret').read_bytes()
        valid = (observed.get('session_id') == session
                 and hmac.compare_digest(str(observed.get('mac', '')), _seal(secret, observed)))
        if strict and not valid:
            raise ValueError('current hook context cannot be verified')
        if valid and _timestamp(observed.get('at')) >= _timestamp(current.get('at', 0)):
            current = observed
    except (OSError, ValueError, TypeError, AttributeError):
        if strict:
            raise ValueError('current hook context cannot be verified') from None
    return current


def claimed_resume_context_valid(runs: Path, pending: dict, allowed_cwds: set[str]) -> bool:
    """An unchanged manual resume claim can finish; unknown mode stays unknown."""
    try:
        context = pending.get('capture')
        if pending.get('action') != 'resume' or not consumed_capture_valid(runs, context, pending['rendered_at']):
            return False
        if context['origin'] == 'codex-host-transcript':
            observed = _transcript_current_context(runs, context, allowed_cwds)
            return observed.get('session_id') == pending['session'] and observed.get('permission_mode') == 'bypassPermissions'
        events = capture_events(runs, pending['session'])
        if not events:
            return False
        latest = host_capture_context(events[-1], pending['session'])
        observed = _observed_hook_context(runs, pending['session'], strict=True)
        if context.get('permission_mode') is None and latest != context:
            return False
        return (observed.get('session_id') == context['session_id']
                and observed.get('permission_mode') == context.get('permission_mode'))
    except (OSError, ValueError, TypeError, KeyError):
        return False


@_transcript_operation
def current_host_context(runs: Path, record: dict, allowed_cwds: set[str],
                         *, historical_cwds: set[str] | None = None) -> dict:
    """Refresh mode from genuine host evidence; creation mode is never sticky authority."""
    session = str(record.get('session_id') or '')
    original = _record_host_binding(record)
    current = _observed_hook_context(runs, session)
    if original.get('transcript_proof') is not None:
        if (isinstance(current.get('permission_mode'), str) and current['permission_mode'] != 'bypassPermissions'
                and _timestamp(current.get('at', 0)) >= _timestamp(original.get('at', 0))):
            raise ValueError('current host mode requires a genuine manual decision')
        return _transcript_current_context(runs, original, allowed_cwds)
    if isinstance(current.get('permission_mode'), str):
        if current['permission_mode'] != 'bypassPermissions':
            raise ValueError('current host mode requires a genuine manual decision')
        return current
    if original.get('origin') == 'codex-host-transcript' and original.get('transcript_path'):
        event = {'prompt': original.get('prompt_sha256'), 'at': original.get('at')}
        context = codex_transcript_context(Path(original['transcript_path']), session, event, allowed_cwds,
                                           historical_cwds=historical_cwds)
        if context.get('permission_mode') == 'bypassPermissions':
            return context
    raise ValueError('current trusted full-access evidence is unavailable')


def event_available(runs: Path, session: str, event: dict) -> bool:
    if event.get('_transcript_context') is not None:
        return not _receipt_path(runs, event['_transcript_context']).exists()
    identity = digest(json.dumps([session, event.get('event_id'), event.get('at'), event['prompt']]))
    return not (runs / 'consumed-prompts' / f'{identity}.json').exists()


@_transcript_operation
def _transcript_instruction(runs: Path, record: dict, instruction: str, policy: dict,
                            allowed_cwds: set[str]) -> dict | None:
    """Read an exact later policy instruction from an already authenticated native source."""
    origin = _record_host_binding(record)
    if not isinstance(origin, dict) or origin.get('transcript_proof') is None:
        return None
    _transcript_current_context(runs, origin, allowed_cwds)
    source = origin['transcript_proof']['source']
    scanned = _read_transcript(Path(source['path']), record['session_id'], allowed_cwds)
    event = scanned['last_event']
    if scanned['partial'] or not _event_matches(event, instruction) or scanned['current']['permission_mode'] != 'bypassPermissions':
        raise ValueError('policy adoption requires the latest complete genuine user instruction')
    if event['offset'] <= origin['transcript_proof']['event_offset']:
        expected = hashlib.sha256(canonical({'record_nonce': record['nonce'], 'policy': policy})).hexdigest()
        if (event['offset'] != origin['transcript_proof']['event_offset']
                or origin['transcript_proof']['action'] != 'adopt-policy'
                or origin['transcript_proof']['page_sha256'] != expected):
            return None
    if not event['context'] or not event['context']['valid'] or event['context']['permission_mode'] != 'bypassPermissions':
        raise ValueError('policy instruction was not received in full-access mode')
    proof = {**origin['transcript_proof'], 'event_offset': event['offset'], 'event_sha256': event['sha256'],
             'action': 'adopt-policy', 'page_sha256': hashlib.sha256(canonical({'record_nonce': record['nonce'], 'policy': policy})).hexdigest()}
    identity = hashlib.sha256(canonical([record['session_id'], source['path'], source['device'], source['inode'],
                                         event['offset'], event['sha256']])).hexdigest()
    context = {'origin': 'codex-host-transcript', 'session_id': record['session_id'], 'permission_mode': 'bypassPermissions',
               'prompt_sha256': digest(instruction), 'event_id': identity, 'at': event['at'],
               'transcript_path': source['path'], 'transcript_proof': proof}
    return {'session': record['session_id'], 'prompt': digest(instruction), 'event_id': identity, 'at': event['at'],
            'permission_mode': 'bypassPermissions', '_transcript_context': context}
