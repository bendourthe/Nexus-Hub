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
) -> dict:
    """The canonical data a mid-run answer, pause, or resume page shows."""
    page: dict = {
        "action": action,
        "scope": {"kind": "plan", "version": version, "plan": rel},
        "record_nonce": record_nonce,
    }
    if action == "answer":
        page["blocker"] = {"index": blocker, "category": category}
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
    matched = next((d for d in wanted if digests.count(d) == 1), None)
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
    path.unlink()
    # The message the user actually pasted, so the record stores what was approved.
    lines = pending.get("approve_lines") or []
    if len(lines) == len(wanted):
        pending["pasted"] = approved_text(lines[wanted.index(matched)])
    _write_private(
        used_path(runs, key),
        {"action": action, "code_sha256": digest(pending["code"]), "used_at": int(_clock())},
    )
    return pending, session
