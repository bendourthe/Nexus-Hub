"""Codex native agent + hook delivery (v3.15.8 Phase 5).

Covers the contract the Phase 1 ownership matrix requires before a Codex row may
move from finding-only to enforceable: schema conformance, user-file collision,
idempotent upgrade, structured merge that preserves user entries, malformed-input
rollback, cross-shell parity, and teardown that removes only owned entries.

These tests drive ``_install_native`` (and the pure adapters underneath) rather
than a full ``install()``, so they exercise the same code the installer runs
without paying for a 270-skill catalog copy per test.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations._codex_native import (
    CODEX_EVENT_ALIASES,
    CODEX_HOOK_EVENTS,
    CODEX_TOOL_MATCHERS,
    build_hook_entries,
    infer_sandbox_mode,
    merge_hooks_json,
    render_agent_toml,
)
from scripts.lib.integrations.base import InstallContext

REQUIRED_AGENT_FIELDS = ("name", "description", "developer_instructions")


@pytest.fixture
def codex():
    return get("codex")


@pytest.fixture
def codex_root(install_ctx: InstallContext) -> Path:
    return (install_ctx.target_root / ".codex").resolve()


def _install_native(codex, ctx: InstallContext, root: Path):
    return codex._install_native(root, ctx, scope="workspace")


def _hooks(root: Path) -> dict:
    return json.loads((root / "hooks.json").read_text(encoding="utf-8"))


def _handlers(data: dict, event: str) -> list[dict]:
    return [h for group in data["hooks"].get(event, []) for h in group["hooks"]]


# ----- agents: schema ------------------------------------------------------


def test_every_catalog_agent_becomes_valid_codex_toml(codex, install_ctx, codex_root):
    """Each catalog agent parses as TOML and carries all three required fields."""
    _install_native(codex, install_ctx, codex_root)
    emitted = sorted((codex_root / "agents").glob("*.toml"))
    assert len(emitted) == len(list((install_ctx.repo_root / "catalog" / "agents").glob("*.md")))
    for path in emitted:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        for field in REQUIRED_AGENT_FIELDS:
            assert data.get(field), f"{path.name} is missing required field {field!r}"
        assert path.stem == data["name"] or data["name"], path.name


def test_agent_body_survives_the_transform(codex, install_ctx, codex_root):
    """developer_instructions carries the Markdown body, not a truncated summary."""
    _install_native(codex, install_ctx, codex_root)
    data = tomllib.loads((codex_root / "agents" / "planner.toml").read_text(encoding="utf-8"))
    source = (install_ctx.repo_root / "catalog" / "agents" / "planner.md").read_text(
        encoding="utf-8"
    )
    assert "# Planner Agent" in data["developer_instructions"]
    assert data["developer_instructions"].strip() in source


@pytest.mark.parametrize(
    "tools,expected",
    [
        ("Read, Glob, Grep", "read-only"),
        ("Read", "read-only"),
        ("Read, Write", None),
        ("Bash", None),
        ("", None),
    ],
)
def test_sandbox_mode_inference_only_ever_restricts(tools, expected):
    assert infer_sandbox_mode(tools) == expected


def test_agent_with_quotes_and_delimiters_round_trips():
    """A body containing TOML string delimiters still parses back correctly."""
    body = "Say '''hello''' and \"quoted\" and a backslash \\ here."
    markdown = f'---\nname: tricky\ndescription: A "tricky" agent\n---\n\n{body}\n'
    rendered = render_agent_toml("tricky", markdown)
    data = tomllib.loads(rendered.decode("utf-8"))
    assert data["description"] == 'A "tricky" agent'
    assert data["developer_instructions"].strip() == body


def test_agent_missing_required_fields_is_skipped():
    assert render_agent_toml("empty", "---\nname: empty\n---\n\n") is None
    assert render_agent_toml("nobody", "---\nname: n\ndescription: d\n---\n\n") is None


# ----- agents: ownership ---------------------------------------------------


def test_user_authored_agent_is_never_overwritten(codex, install_ctx, codex_root):
    (codex_root / "agents").mkdir(parents=True)
    mine = codex_root / "agents" / "planner.toml"
    mine.write_text('name = "mine"\n', encoding="utf-8")

    actions = _install_native(codex, install_ctx, codex_root)

    assert mine.read_text(encoding="utf-8") == 'name = "mine"\n'
    kept = [a for a in actions if a.path == str(mine)]
    assert kept and kept[0].action == "kept"


def test_owned_agent_is_refreshed_on_upgrade(codex, install_ctx, codex_root):
    """A file we own is replaced on upgrade; that is what makes repair work."""
    _install_native(codex, install_ctx, codex_root)
    owned = codex_root / "agents" / "planner.toml"
    owned.write_text("drifted", encoding="utf-8")

    actions = _install_native(codex, replace(install_ctx, manifest=install_ctx.manifest), codex_root)

    assert owned.read_text(encoding="utf-8") != "drifted"
    assert [a.action for a in actions if a.path == str(owned)] == ["updated"]


def test_reinstall_is_idempotent(codex, install_ctx, codex_root):
    _install_native(codex, install_ctx, codex_root)
    actions = _install_native(codex, replace(install_ctx, manifest=install_ctx.manifest), codex_root)
    assert not [a for a in actions if a.action in {"created", "updated"}]


# ----- hooks: event and matcher mapping ------------------------------------


def test_only_codex_supported_matchers_are_emitted(codex, install_ctx, codex_root):
    """PowerShell / MultiEdit / Skill have no Codex equivalent and must not ship."""
    _install_native(codex, install_ctx, codex_root)
    data = _hooks(codex_root)
    for event, groups in data["hooks"].items():
        for group in groups:
            matcher = group.get("matcher")
            if matcher is None:
                continue
            for token in matcher.split("|"):
                assert token in CODEX_TOOL_MATCHERS, f"{event}: unsupported matcher {token!r}"


def test_unmappable_hooks_are_dropped_not_approximated(install_ctx):
    settings = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "PowerShell", "hooks": [{"command": "bash x/git-guardrails.sh"}]},
                {"matcher": "Bash", "hooks": [{"command": "bash x/git-guardrails.sh"}]},
            ],
            "PostToolUse": [{"matcher": "Skill", "hooks": [{"command": "bash x/lint-on-write.sh"}]}],
            "NotAnEvent": [{"hooks": [{"command": "bash x/git-guardrails.sh"}]}],
        }
    }
    src = install_ctx.repo_root / "catalog" / "hooks"
    events, scripts, skipped = build_hook_entries(settings, src, "/hooks")

    assert set(events) == {"PreToolUse"}
    assert [g["matcher"] for g in events["PreToolUse"]] == ["Bash"]
    assert "git-guardrails.sh" in scripts
    assert any("PowerShell" in reason for reason in skipped)
    assert any("Skill" in reason for reason in skipped)
    assert any("NotAnEvent" in reason for reason in skipped)


def test_matcherless_events_omit_the_matcher(codex, install_ctx, codex_root):
    """Codex ignores a matcher on Stop / UserPromptSubmit, so emitting one lies."""
    _install_native(codex, install_ctx, codex_root)
    data = _hooks(codex_root)
    for event in ("Stop", "UserPromptSubmit"):
        for group in data["hooks"][event]:
            assert "matcher" not in group


def test_multi_edit_matcher_is_normalized_to_codex_aliases(install_ctx):
    settings = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Edit|MultiEdit|Write", "hooks": [{"command": "python3 x/skill-guard.py"}]}
            ]
        }
    }
    events, _, _ = build_hook_entries(settings, install_ctx.repo_root / "catalog" / "hooks", "/h")
    assert events["PreToolUse"][0]["matcher"] == "Edit|Write"


# ----- hooks: cross-shell parity -------------------------------------------


def test_every_handler_carries_a_windows_command(codex, install_ctx, codex_root):
    """commandWindows is what gives a Windows user the same guardrail."""
    _install_native(codex, install_ctx, codex_root)
    data = _hooks(codex_root)
    handlers = [h for groups in data["hooks"].values() for g in groups for h in g["hooks"]]
    assert handlers
    for handler in handlers:
        assert handler["commandWindows"], handler
        assert handler["type"] == "command"


def test_shell_hooks_point_at_their_powershell_sibling(codex, install_ctx, codex_root):
    _install_native(codex, install_ctx, codex_root)
    data = _hooks(codex_root)
    handlers = _handlers(data, "SessionStart")
    assert {Path(handler["command"].split()[-1]).stem for handler in handlers} >= {
        "session-start",
    }
    for handler in handlers:
        script = Path(handler["command"].split()[-1])
        if script.suffix == ".py":
            assert handler["command"].startswith("python3 ")
            assert handler["commandWindows"].startswith("python ")
            assert Path(handler["commandWindows"].split()[-1]).name == script.name
            continue
        shell_stem = Path(handler["command"].split()[-1]).stem
        windows_stem = Path(handler["commandWindows"].split()[-1]).stem
        assert handler["command"].endswith(f"{shell_stem}.sh")
        assert handler["commandWindows"].endswith(f"{shell_stem}.ps1")
        assert windows_stem == shell_stem
        assert "powershell" in handler["commandWindows"]


def test_both_script_siblings_are_installed(codex, install_ctx, codex_root):
    _install_native(codex, install_ctx, codex_root)
    installed = {p.name for p in (codex_root / "hooks").iterdir()}
    assert "git-guardrails.sh" in installed
    assert "git-guardrails.ps1" in installed


# ----- hooks: structured merge ---------------------------------------------


def _user_hook() -> dict:
    return {"type": "command", "command": "bash /home/me/my-own-hook.sh"}


def test_merge_preserves_user_hooks_and_unrelated_keys(codex, install_ctx, codex_root):
    _install_native(codex, install_ctx, codex_root)
    data = _hooks(codex_root)
    data["description"] = "my workspace hooks"
    data["hooks"].setdefault("Stop", []).append({"hooks": [_user_hook()]})
    (codex_root / "hooks.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    _install_native(codex, replace(install_ctx, manifest=install_ctx.manifest), codex_root)

    after = _hooks(codex_root)
    assert after["description"] == "my workspace hooks"
    commands = [h["command"] for h in _handlers(after, "Stop")]
    assert "bash /home/me/my-own-hook.sh" in commands


def test_merge_does_not_duplicate_owned_entries(codex, install_ctx, codex_root):
    _install_native(codex, install_ctx, codex_root)
    first = _handlers(_hooks(codex_root), "Stop")
    for _ in range(2):
        _install_native(codex, replace(install_ctx, manifest=install_ctx.manifest), codex_root)
    assert _handlers(_hooks(codex_root), "Stop") == first


def test_user_handler_inside_an_owned_group_survives(codex, install_ctx, codex_root):
    """Ownership is per handler, so a user editing our group keeps their entry."""
    _install_native(codex, install_ctx, codex_root)
    data = _hooks(codex_root)
    data["hooks"]["SessionStart"][0]["hooks"].append(_user_hook())
    (codex_root / "hooks.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    _install_native(codex, replace(install_ctx, manifest=install_ctx.manifest), codex_root)

    commands = [h["command"] for h in _handlers(_hooks(codex_root), "SessionStart")]
    assert "bash /home/me/my-own-hook.sh" in commands


def test_malformed_hooks_json_is_never_clobbered(codex, install_ctx, codex_root):
    codex_root.mkdir(parents=True, exist_ok=True)
    broken = codex_root / "hooks.json"
    broken.write_text("{ not json at all", encoding="utf-8")

    actions = _install_native(codex, install_ctx, codex_root)

    assert broken.read_text(encoding="utf-8") == "{ not json at all"
    assert [a.action for a in actions if a.path == str(broken)] == ["kept"]


def test_non_object_hooks_json_is_kept(install_ctx, codex_root):
    codex_root.mkdir(parents=True, exist_ok=True)
    dst = codex_root / "hooks.json"
    dst.write_text("[1, 2, 3]", encoding="utf-8")
    action = merge_hooks_json(install_ctx, "codex", dst, {"Stop": []}, "/h")
    assert action.action == "kept"
    assert dst.read_text(encoding="utf-8") == "[1, 2, 3]"


def test_existing_file_is_backed_up_before_mutation(codex, install_ctx, codex_root):
    codex_root.mkdir(parents=True, exist_ok=True)
    dst = codex_root / "hooks.json"
    dst.write_text('{"hooks": {}}', encoding="utf-8")

    _install_native(codex, install_ctx, codex_root)

    backup = codex_root / "hooks.json.nexus-hub.bak"
    assert backup.read_text(encoding="utf-8") == '{"hooks": {}}'
    assert not (codex_root / "hooks.json.nexus-hub.tmp").exists()


# ----- teardown ------------------------------------------------------------


def test_teardown_removes_only_owned_entries(codex, install_ctx, codex_root):
    _install_native(codex, install_ctx, codex_root)
    data = _hooks(codex_root)
    data["hooks"].setdefault("Stop", []).append({"hooks": [_user_hook()]})
    (codex_root / "hooks.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _install_native(codex, replace(install_ctx, manifest=install_ctx.manifest), codex_root)

    codex.teardown(replace(install_ctx, manifest=install_ctx.manifest))

    remaining = _hooks(codex_root)
    assert list(remaining["hooks"]) == ["Stop"]
    assert [h["command"] for h in _handlers(remaining, "Stop")] == [
        "bash /home/me/my-own-hook.sh"
    ]


def test_teardown_removes_hooks_json_when_nothing_else_remains(codex, install_ctx, codex_root):
    _install_native(codex, install_ctx, codex_root)
    codex.teardown(replace(install_ctx, manifest=install_ctx.manifest))
    assert not (codex_root / "hooks.json").exists()


def test_teardown_leaves_no_dead_directories(codex, install_ctx, codex_root):
    _install_native(codex, install_ctx, codex_root)
    codex.teardown(replace(install_ctx, manifest=install_ctx.manifest))
    assert not (codex_root / "agents").exists()
    assert not (codex_root / "hooks").exists()


def test_teardown_keeps_a_user_authored_agent_and_its_directory(codex, install_ctx, codex_root):
    (codex_root / "agents").mkdir(parents=True)
    mine = codex_root / "agents" / "planner.toml"
    mine.write_text('name = "mine"\n', encoding="utf-8")
    _install_native(codex, install_ctx, codex_root)

    codex.teardown(replace(install_ctx, manifest=install_ctx.manifest))

    assert mine.read_text(encoding="utf-8") == 'name = "mine"\n'


# ----- hook discovery has no mandatory feature switch --------------------


def test_workspace_install_does_not_create_or_advise_a_feature_switch(
    codex, install_ctx, codex_root
):
    result = codex.install_workspace(install_ctx)
    assert not (codex_root / "config.toml").exists()
    assert not any("[features]" in note or "hooks = true" in note for note in result.notes)


def test_install_summary_does_not_claim_hooks_are_active(codex, install_ctx):
    """Codex hooks need per-hook trust, so the summary must not overpromise."""
    result = codex.install_workspace(install_ctx)
    assert any("/hooks" in note and "inert" in note for note in result.notes)


# ---------------------------------------------------------------------------
# End-of-task notification delivery (v3.15.11)
#
# Two defects v3.15.10 shipped to Codex, both of the same shape: a hook that is
# copied and registered but permanently inert.
#
#   1. The Notification chain was dropped as "no Codex event of that name".
#      Codex's equivalent is PermissionRequest, verified against the Codex
#      implementation (codex-rs/hooks/src/events/permission_request.rs and the
#      serde wire names in codex-rs/hooks/src/lib.rs) because openai/codex ships
#      no docs/hooks.md.
#   2. notify-on-complete.sh WAS delivered, but _notify_common.sh was not. The
#      hook sources that module from its own directory, so it exited silently on
#      every run.
# ---------------------------------------------------------------------------


def _entries(src_hooks: Path):
    settings = json.loads((src_hooks / "settings.json").read_text(encoding="utf-8"))
    return build_hook_entries(settings, src_hooks, "~/.codex/hooks")


def test_permission_request_is_a_real_codex_event():
    """The alias target must exist in the verified event set, or it is a no-op."""
    assert CODEX_EVENT_ALIASES["Notification"] == "PermissionRequest"
    assert "PermissionRequest" in CODEX_HOOK_EVENTS


def test_notification_chain_reaches_codex_as_permission_request(repo_root: Path):
    events, _, skipped = _entries(repo_root / "catalog" / "hooks")

    assert "PermissionRequest" in events, (
        f"the Notification chain was dropped; skips were: {skipped}"
    )
    assert "notify-attention-required" in json.dumps(events["PermissionRequest"])
    assert not any("Notification" in s for s in skipped), (
        f"Notification should be aliased, not skipped: {skipped}"
    )


def test_completion_hook_reaches_codex_on_stop(repo_root: Path):
    events, _, _ = _entries(repo_root / "catalog" / "hooks")

    assert "notify-on-complete" in json.dumps(events.get("Stop", []))


def test_shared_module_ships_with_the_hooks_that_source_it(repo_root: Path):
    """Without the module the hooks are registered, executable, and inert."""
    _, scripts, _ = _entries(repo_root / "catalog" / "hooks")

    assert "_notify_common.sh" in scripts, (
        "notify hooks source _notify_common.sh; without it they exit silently"
    )
    assert "_notify_common.ps1" in scripts, (
        "the .ps1 hook needs the .ps1 module, which no .sh body names"
    )


def test_codex_never_registers_a_notifier_on_a_subagent_event(repo_root: Path):
    """A sub-task milestone must never interrupt a human."""
    events, _, _ = _entries(repo_root / "catalog" / "hooks")

    for event in ("SubagentStop", "SubagentStart"):
        assert "notify-" not in json.dumps(events.get(event, [])), (
            f"a notification hook is wired to {event}"
        )
