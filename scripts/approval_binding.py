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
import os
import re
import secrets
import time
from collections.abc import Callable
from pathlib import Path

import approval_page  # installed as a sibling in ~/.nexus-hub/scripts/

SUPERSEDED_KEEP = 20
RUNNER_ENV = "NEXUS_RUNNER_LAUNCH"
ACTIONS = ("create", "answer", "pause", "resume", "retire")
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


# --------------------------------------------------------------------------- render / consume


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
    path = pending_path(runs, key)
    superseded: list[str] = []
    if path.exists():
        try:
            old = _read_pending(path, secret)
            if (old.get('action') == action and old.get('session') == session
                    and old.get('platform') == platform and old.get('allow_short_reply', False) == allow_short_reply
                    and canonical(old['page']) == canonical(page)):
                if check is not None:
                    check(old)
                activate_question(runs, key, secret, old)
                return old
            superseded = [*old.get("superseded", []), *old["paste_digests"]]
        except Refusal:
            superseded = []
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
    pending["mac"] = _seal(secret, pending)
    if check is not None:
        check(pending)
    _write_private(path, pending)
    activate_question(runs, key, secret, pending)
    used_path(runs, key).unlink(missing_ok=True)
    return pending


def consume(
    runs: Path,
    key: str,
    secret: bytes | None,
    *,
    action: str,
    live_page: dict,
    session: str,
    required_session: str | None = None,
) -> tuple[dict, str]:
    """Return (pending, bound session) and consume the round, or raise Refusal.

    `required_session` is the session an existing record is bound to: a mid-run
    answer, pause, or resume must be pasted in that session, never in another one.
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
    if event is not None:
        _claim_event(runs, session, event)
        pending['capture'] = host_capture_context(event, session)
    path.unlink()
    # The message the user actually pasted, so the record stores what was approved.
    lines = pending.get("approve_lines") or []
    if short is not None:
        pending["pasted"] = short
    elif len(lines) == len(wanted):
        pending["pasted"] = approved_text(lines[wanted.index(matched)])
    _write_private(
        used_path(runs, key),
        {"action": action, "code_sha256": digest(pending["code"]), "used_at": int(_clock())},
    )
    return pending, session


# --------------------------------------------------------------------------- host context and continuation

SHORT_REPLIES = {digest(word): word for word in ('Approve', 'Yes', 'Continue')}


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


def activate_question(runs: Path, key: str, secret: bytes, pending: dict) -> None:
    """Only one displayed short-answer challenge is active in a session."""
    if not pending.get('allow_short_reply') or not pending.get('session'):
        return
    active = {'key': key, 'nonce': pending['nonce'], 'session': pending['session']}
    active['mac'] = _seal(secret, active)
    _write_private(question_path(runs, pending['session']), active)


def _claim_event(runs: Path, session: str, event: dict) -> None:
    """Single consumption across records, including legacy captures with stable identity."""
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
    return {'origin': 'host-hook-capture', 'session_id': session,
            'permission_mode': event.get('permission_mode'), 'prompt_sha256': event['prompt'],
            'event_id': event.get('event_id'), 'at': event.get('at')}


def full_access_authorization(record: dict, context: dict | None = None) -> bool:
    """The caller must first verify the signed run; legacy records default conservative."""
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


def adopt_policy(runs: Path, record: dict, instruction: str, policy: dict,
                 transcript: Path | None = None, allowed_cwds: set[str] | None = None,
                 *, historical_cwds: set[str] | None = None) -> None:
    """Bind an exact unused instruction and independently current mode, without NLP inference."""
    policy = validate_policy(policy)
    session = str(record.get('session_id') or '')
    matches = [event for event in capture_events(runs, session)
               if event['prompt'] == digest(instruction)]
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
    context = host_capture_context(event, session)
    if context.get('permission_mode') != 'bypassPermissions':
        if transcript is None:
            raise ValueError('trusted host permission evidence is unavailable')
        context = codex_transcript_context(transcript, session, event, allowed_cwds or set(), historical_cwds=historical_cwds)
    if context.get('permission_mode') != 'bypassPermissions':
        raise ValueError('current host mode requires a genuine manual decision')
    # Selected instruction provenance is not proof of the latest permission mode.
    view = {**record, 'approvals': {**approvals, 'authorization_context': context}}
    current = current_host_context(runs, view, allowed_cwds or set(), historical_cwds=historical_cwds)
    if not full_access_authorization(record, current):
        raise ValueError('current trusted full-access evidence is unavailable')
    # Only an identical same-record retry may reuse already-consumed provenance.
    if retry:
        return
    _claim_event(runs, session, event)
    approvals['authorization_context'] = context
    approvals['autonomy_policy'] = policy
    approvals.setdefault('policy_adoptions', []).append({
        'origin': 'captured-user-instruction', 'prompt_sha256': event['prompt'],
        'event_id': event.get('event_id'), 'at': event['at'], 'policy': policy,
        'current_host_context': current})


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



def current_host_context(runs: Path, record: dict, allowed_cwds: set[str],
                         *, historical_cwds: set[str] | None = None) -> dict:
    """Refresh mode from genuine host evidence; creation mode is never sticky authority."""
    session = str(record.get('session_id') or '')
    original = record.get('approvals', {}).get('authorization_context') or {}
    events = capture_events(runs, session)
    current = host_capture_context(events[-1], session) if events else {}
    path = runs / 'host-context' / f'{hashlib.sha256(session.encode()).hexdigest()}.json'
    try:
        observed = json.loads(path.read_text(encoding='utf-8'))
        secret = (runs / '.secret').read_bytes()
        if (observed.get('session_id') == session
                and hmac.compare_digest(str(observed.get('mac', '')), _seal(secret, observed))
                and _timestamp(observed.get('at')) >= _timestamp(current.get('at', 0))):
            current = observed
    except (OSError, ValueError, TypeError, AttributeError):
        pass
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
    identity = digest(json.dumps([session, event.get('event_id'), event.get('at'), event['prompt']]))
    return not (runs / 'consumed-prompts' / f'{identity}.json').exists()
