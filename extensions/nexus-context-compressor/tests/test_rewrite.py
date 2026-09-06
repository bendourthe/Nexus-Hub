"""Command-rewrite decision contract (0 allow / 1 passthrough / 2 deny / 3 ask)."""

from __future__ import annotations

import json
from pathlib import Path

from nexus_context_compressor.rewrite import (
    ALLOW,
    ASK,
    DENY,
    PASSTHROUGH,
    HostPermissions,
    decide,
    load_host_permissions,
    split_segments,
)


def test_default_with_a_proposed_rewrite_is_ask_never_allow() -> None:
    code, stdout = decide("echo hi", proposed="echo hello")
    assert code == ASK
    assert code != ALLOW
    assert stdout == "echo hello"


def test_no_proposed_rewrite_is_passthrough() -> None:
    code, stdout = decide("git status")
    assert code == PASSTHROUGH
    assert stdout == ""


def test_host_deny_beats_allow() -> None:
    perms = HostPermissions(deny=("rm",), allow=("rm",))
    code, _ = decide("rm -rf /tmp/x", perms, proposed="rm -rf /tmp/x")
    assert code == DENY


def test_compound_command_requires_every_segment_allowed() -> None:
    perms = HostPermissions(allow=("echo",))
    code, _ = decide("echo a && rm -rf /tmp/x", perms, proposed="echo a")
    assert code == ASK
    code, _ = decide("echo a && echo b", perms, proposed="echo a && echo b")
    assert code == ALLOW


def test_split_ignores_pipes_inside_quotes() -> None:
    parts = split_segments('echo "a | b" && true')
    assert parts == ['echo "a | b"', "true"]


def test_bash_wrapped_host_deny_wins() -> None:
    perms = HostPermissions(deny=("Bash(curl *)",), allow=("Bash(curl *)",))
    code, _ = decide("curl https://example.invalid", perms, proposed="curl https://example.invalid")
    assert code == DENY


def test_load_host_permissions_from_json(tmp_path: Path) -> None:
    path = tmp_path / "perms.json"
    path.write_text(
        json.dumps({"permissions": {"deny": ["curl"], "ask": ["git push"], "allow": ["git status"]}}),
        encoding="utf-8",
    )
    perms = load_host_permissions(path)
    assert perms.deny == ("curl",)
    assert decide("curl https://example.invalid", perms)[0] == DENY
