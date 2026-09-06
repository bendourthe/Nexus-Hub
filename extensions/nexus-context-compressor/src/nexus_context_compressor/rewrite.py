"""Single-source command-rewrite decision (exit 0/1/2/3).

0 allow -- apply the rewritten command without asking
1 passthrough -- no rewrite to offer
2 deny -- refuse the command
3 ask -- rewrite is available but needs approval

The default when a rewrite exists and the host has not explicitly allowed
every segment is 3. The default is never 0.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ALLOW = 0
PASSTHROUGH = 1
DENY = 2
ASK = 3

_QUOTE_CHARS = {'"', "'"}


@dataclass(frozen=True)
class HostPermissions:
    """Prefix rules from a host agent's own permission file."""

    deny: tuple[str, ...] = ()
    ask: tuple[str, ...] = ()
    allow: tuple[str, ...] = ()


def split_segments(command: str) -> list[str]:
    """Split a compound command on ``&&`` ``||`` ``;`` ``|`` outside quotes."""
    segments: list[str] = []
    buf: list[str] = []
    quote = ""
    i = 0
    text = command.strip()
    while i < len(text):
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = ""
            i += 1
            continue
        if ch in _QUOTE_CHARS:
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if text.startswith("&&", i) or text.startswith("||", i):
            _flush(segments, buf)
            i += 2
            continue
        if ch in ";|":
            _flush(segments, buf)
            i += 1
            continue
        buf.append(ch)
        i += 1
    _flush(segments, buf)
    return segments or [""]


def _flush(segments: list[str], buf: list[str]) -> None:
    piece = "".join(buf).strip()
    buf.clear()
    if piece:
        segments.append(piece)


def _normalize_rule(rule: str) -> str:
    """Strip Claude-style ``Bash(...)`` wrappers and a trailing glob star."""
    rule = rule.strip()
    if rule.startswith("Bash(") and rule.endswith(")"):
        rule = rule[5:-1].strip()
    if rule.endswith("*"):
        rule = rule[:-1].rstrip()
    return rule


def _matches(rule: str, segment: str) -> bool:
    rule = _normalize_rule(rule)
    segment = segment.strip()
    if not rule:
        return False
    if segment == rule or segment.startswith(rule + " "):
        return True
    first = segment.split(None, 1)[0] if segment else ""
    return first == rule


def _any_match(rules: tuple[str, ...], segment: str) -> bool:
    return any(_matches(rule, segment) for rule in rules)


def load_host_permissions(path: Path | None) -> HostPermissions:
    """Load deny/ask/allow prefix lists. Missing file => empty rules."""
    if path is None or not path.is_file():
        return HostPermissions()
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return HostPermissions()
    block = raw.get("permissions", raw)
    if not isinstance(block, dict):
        return HostPermissions()

    def _list(key: str) -> tuple[str, ...]:
        value = block.get(key, [])
        if not isinstance(value, list):
            return ()
        return tuple(str(item) for item in value if str(item).strip())

    return HostPermissions(deny=_list("deny"), ask=_list("ask"), allow=_list("allow"))


def propose_rewrite(command: str) -> str | None:
    """Return an equivalent rewrite, or None when the command should pass through.

    This catalog does not auto-rewrite arbitrary commands. A rewrite is only
    proposed when a caller injects one (tests, or a future equivalent map).
    """
    del command
    return None


def decide(
    command: str,
    permissions: HostPermissions | None = None,
    proposed: str | None = None,
) -> tuple[int, str]:
    """Return ``(exit_code, stdout)`` for one command.

    Host precedence: Deny > Ask > Allow > default(ask). A compound command is
    allowed only when every segment independently matches allow. The default
    for a proposed rewrite is ASK, never ALLOW.
    """
    perms = permissions or HostPermissions()
    segments = split_segments(command)
    if any(_any_match(perms.deny, segment) for segment in segments):
        return DENY, ""
    if any(_any_match(perms.ask, segment) for segment in segments):
        return ASK, proposed or ""
    all_allowed = bool(perms.allow) and all(
        _any_match(perms.allow, segment) for segment in segments
    )
    rewrite = proposed if proposed is not None else propose_rewrite(command)
    if rewrite is None:
        return PASSTHROUGH, ""
    if all_allowed:
        return ALLOW, rewrite
    return ASK, rewrite
