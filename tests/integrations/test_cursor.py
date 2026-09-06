"""Tests for the Cursor integration parity surfaces (v3.15.0 Phase 2).

Covers the read-contract verified 2026-07-20 (docs/policy/platform-read-contracts.md,
parity_verification_v3_15_0 in the sibling .json):
  - skills flattened one level into .cursor/skills (native path only; the shared
    ~/.agents/skills is deliberately NOT written here to avoid a teardown conflict
    with the codex integration)
  - every catalog command emitted as a skill in .cursor/skills AND mirrored to the
    project-scoped .cursor/commands/ (in addition to the global ~/.cursor/commands/)
  - subagents copied verbatim to .cursor/agents
  - a Cursor-schema hooks.json (version 1) + the git-guardrails script, gated on
    hooks_supported
  - the pre-existing rules (.cursor/rules/*.mdc) + root AGENTS.md surfaces preserved
"""

from __future__ import annotations

import json
import os
from dataclasses import replace

from scripts.lib.integrations import cursor as cursor_module
from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.cursor import CursorIntegration

_CATEGORY_NAMES = ("ai-development", "workflow", "security", "orchestration", "code-review")


def test_cursor_workspace_flattens_skills(install_ctx: InstallContext):
    """Workspace install lays flattened skills under .cursor/skills, native path only."""
    get("cursor").install(install_ctx)
    root = install_ctx.target_root

    skills_dir = root / ".cursor" / "skills"
    assert skills_dir.is_dir(), f"{skills_dir} should exist"
    for category in _CATEGORY_NAMES:
        assert not (skills_dir / category).is_dir(), (
            f"category folder {category!r} leaked into {skills_dir} -- skills not flattened"
        )
    skill_dirs = [p for p in skills_dir.iterdir() if p.is_dir()]
    assert len(skill_dirs) >= 50, f"expected the full flat catalog; got {len(skill_dirs)}"
    for skill in skill_dirs[:10]:
        assert (skill / "SKILL.md").exists(), f"{skill.name}/ must contain SKILL.md directly"

    # Native-only: Cursor must NOT write the shared ~/.agents/skills (codex owns it).
    assert not (root / ".agents" / "skills").exists(), (
        "Cursor must write only its native skills dir, not the shared .agents/skills"
    )


def test_cursor_workspace_commands_as_skills_and_project_commands(install_ctx: InstallContext):
    """Every command surfaces as a skill in .cursor/skills AND in project .cursor/commands/."""
    get("cursor").install(install_ctx)
    root = install_ctx.target_root

    skill_md = root / ".cursor" / "skills" / "presentify" / "SKILL.md"
    assert skill_md.exists(), f"command-skill missing at {skill_md}"
    text = skill_md.read_text(encoding="utf-8")
    assert "name: presentify" in text
    assert "/presentify" in text, "command-skill description should carry the slash lead-in"
    assert "disable-model-invocation: true" in text

    project_cmd = root / ".cursor" / "commands" / "presentify.md"
    assert project_cmd.exists(), "project-scoped .cursor/commands/ mirror missing"


def test_cursor_workspace_writes_agents(install_ctx: InstallContext):
    """Subagents land at .cursor/agents as verbatim .md files (Cursor reads .md)."""
    get("cursor").install(install_ctx)
    agents_dir = install_ctx.target_root / ".cursor" / "agents"
    assert agents_dir.is_dir(), "subagents dir not written"
    md_files = list(agents_dir.glob("*.md"))
    assert len(md_files) >= 5, f"expected catalog agents copied; got {len(md_files)}"


def test_cursor_workspace_preserves_rules_and_root_agents_md(install_ctx: InstallContext):
    """The pre-existing rules (.mdc) + root AGENTS.md surfaces still install."""
    get("cursor").install(install_ctx)
    root = install_ctx.target_root
    assert (root / "AGENTS.md").exists(), "repo-root AGENTS.md not written"
    rules_dir = root / ".cursor" / "rules"
    assert rules_dir.is_dir() and list(rules_dir.glob("*.mdc")), "rules .mdc not written"


def test_cursor_workspace_writes_schema_valid_hooks_json(install_ctx: InstallContext):
    """A Cursor-schema hooks.json (version 1) + the git-guardrails script are written."""
    get("cursor").install(install_ctx)
    cursor_root = install_ctx.target_root / ".cursor"

    hooks_json = cursor_root / "hooks.json"
    assert hooks_json.exists(), "hooks.json not written"
    data = json.loads(hooks_json.read_text(encoding="utf-8"))
    assert data["version"] == 1, "Cursor hooks.json requires version: 1"
    assert "beforeShellExecution" in data["hooks"], "git-guardrails maps to beforeShellExecution"
    entry = data["hooks"]["beforeShellExecution"][0]
    expected_suffix = "git-guardrails.ps1\"" if os.name == "nt" else "git-guardrails.sh\""
    assert entry["command"].endswith(expected_suffix), entry
    assert entry["failClosed"] is True, "security-critical shell hook must fail closed"
    assert "cursor-hook-compat.py" in entry["command"]
    assert (cursor_root / "hooks" / "cursor-hook-compat.py").exists()
    assert (cursor_root / "hooks" / "git-guardrails.sh").exists(), "bash hook not copied"
    assert (cursor_root / "hooks" / "git-guardrails.ps1").exists(), "PowerShell hook not copied"


def test_cursor_windows_registration_uses_powershell(
    install_ctx: InstallContext, monkeypatch
):
    """A Windows install must never depend on bash being present or correctly mapped."""
    monkeypatch.setattr(cursor_module, "is_windows_host", lambda: True)

    get("cursor").install(install_ctx)

    cursor_root = install_ctx.target_root / ".cursor"
    data = json.loads((cursor_root / "hooks.json").read_text(encoding="utf-8"))
    commands = [entry["command"] for entries in data["hooks"].values() for entry in entries]
    assert commands
    assert all(command.startswith("python ") for command in commands)
    assert all("cursor-hook-compat.py" in command for command in commands)
    assert all(".ps1" in command and ".sh" not in command for command in commands)


def test_cursor_posix_registration_uses_bash(
    install_ctx: InstallContext, monkeypatch
):
    """macOS and Linux installs must retain the Bash sibling and Python 3 runner."""
    monkeypatch.setattr(cursor_module, "is_windows_host", lambda: False)

    get("cursor").install(install_ctx)

    cursor_root = install_ctx.target_root / ".cursor"
    data = json.loads((cursor_root / "hooks.json").read_text(encoding="utf-8"))
    commands = [entry["command"] for entries in data["hooks"].values() for entry in entries]
    assert commands
    assert all(command.startswith("python3 ") for command in commands)
    assert all("cursor-hook-compat.py" in command for command in commands)
    assert all("bash " in command and ".sh" in command and ".ps1" not in command for command in commands)


def test_cursor_stop_carries_the_completion_notification(install_ctx: InstallContext):
    """v3.15.10: `stop` is Cursor's documented agent-completion event.

    Verified 2026-08-04 against cursor.com/docs/agent/hooks, which documents
    `stop` as "Handle agent completion".
    """
    get("cursor").install(install_ctx)
    cursor_root = install_ctx.target_root / ".cursor"
    data = json.loads((cursor_root / "hooks.json").read_text(encoding="utf-8"))

    assert "stop" in data["hooks"], "the completion notification must ride Cursor's `stop`"
    entry = data["hooks"]["stop"][0]
    expected_suffix = "notify-on-complete.ps1\"" if os.name == "nt" else "notify-on-complete.sh\""
    assert entry["command"].endswith(expected_suffix), entry
    assert (cursor_root / "hooks" / "notify-on-complete.sh").exists()
    assert (cursor_root / "hooks" / "notify-on-complete.ps1").exists()


def test_cursor_ships_the_notify_helper_module_alongside_the_hook(install_ctx: InstallContext):
    """notify-on-complete.sh sources _notify_common.sh from its own directory.

    Without the module the hook exits silently on every run, which is the worst
    possible failure mode: registered, executable, and permanently inert.
    """
    get("cursor").install(install_ctx)
    hooks_dir = install_ctx.target_root / ".cursor" / "hooks"

    assert (hooks_dir / "_notify_common.sh").exists(), (
        "_notify_common.sh missing; notify-on-complete.sh would source nothing and no-op"
    )
    assert (hooks_dir / "_notify_common.ps1").exists(), (
        "_notify_common.ps1 missing; notify-on-complete.ps1 would import nothing and no-op"
    )


def test_cursor_does_not_wire_a_trigger_it_cannot_express(install_ctx: InstallContext):
    """Cursor documents no event meaning "blocked on the human".

    `beforeShellExecution` can return an "ask" status but fires before EVERY shell
    command, so notifying there would recreate the per-turn storm v3.15.10 removed.
    `subagentStop` exists in Cursor and must never carry a notifier either.
    """
    get("cursor").install(install_ctx)
    data = json.loads(
        (install_ctx.target_root / ".cursor" / "hooks.json").read_text(encoding="utf-8")
    )

    assert "subagentStop" not in data["hooks"], "a sub-task completion must never notify"
    for event, entries in data["hooks"].items():
        for entry in entries:
            if event != "stop":
                assert "notify-" not in entry.get("command", ""), (
                    f"a notification hook is wired to {event!r}, which does not mean "
                    f"'the human is needed'"
                )


def test_cursor_hooks_gated_on_hooks_supported(install_ctx: InstallContext):
    """A Cursor subclass with hooks_supported=False writes no hooks.json / hooks dir."""

    class _CursorNoHooks(CursorIntegration):
        key = "test-cursor-nohooks"
        config = {**CursorIntegration.config, "hooks_supported": False}

    result = _CursorNoHooks().install_workspace(install_ctx)
    cursor_root = install_ctx.target_root / ".cursor"
    assert not (cursor_root / "hooks.json").exists(), "hooks.json must be gated on hooks_supported"
    assert not any(fa.path.endswith("hooks.json") for fa in result.files)


def test_cursor_global_targets_cursor_root(install_ctx: InstallContext):
    """Global install writes skills/agents/commands/hooks under ~/.cursor (dry-run)."""
    result = get("cursor").dry_run(replace(install_ctx, scope="global"))
    joined = " ".join(fa.path.replace("\\", "/") for fa in result.files)

    assert "/.cursor/skills/" in joined, "global install must flatten skills into ~/.cursor/skills"
    # _copy_tree emits one directory-level FileAction (no trailing slash / filename).
    assert "/.cursor/agents" in joined, "global install must write ~/.cursor/agents"
    assert "/.cursor/commands/" in joined, "global install must write ~/.cursor/commands"
    assert "/.cursor/hooks.json" in joined, "global install must write ~/.cursor/hooks.json"
    # Native-only skills: no shared ~/.agents/skills write from Cursor.
    assert "/.agents/skills/" not in joined, "Cursor must not write the shared ~/.agents/skills"


def test_cursor_idempotent_workspace_install(install_ctx: InstallContext):
    """Second install on the same target should mark at least one file unchanged."""
    get("cursor").install(install_ctx)
    result = get("cursor").install(install_ctx)
    actions = {a.action for a in result.files}
    assert "unchanged" in actions, f"second install should produce 'unchanged'; got {actions}"


def test_cursor_wire_project_surfaces_seeds_rules_and_commands(install_ctx: InstallContext):
    """`nexus-hub init` seeds the rules stub AND project .cursor/commands/ (Phase 2, 2.3).

    The confirmed project command surface must be seeded on init, not only via a
    full workspace install; the rules stub behaviour is preserved.
    """
    result = get("cursor").wire_project_surfaces(install_ctx)
    root = install_ctx.target_root

    # Rules stub still seeded (pre-Phase-2 behaviour preserved).
    assert (root / ".cursor" / "rules" / "nexus-hub.mdc").exists(), "rules stub not seeded"

    # Project-scoped commands now seeded by init (sub-task 2.3 literal acceptance).
    commands_dir = root / ".cursor" / "commands"
    assert commands_dir.is_dir(), "project .cursor/commands/ not seeded by wire_project_surfaces"
    assert (commands_dir / "presentify.md").exists(), "expected a catalog command in .cursor/commands/"
    joined = " ".join(fa.path.replace("\\", "/") for fa in result.files)
    assert "/.cursor/commands/" in joined, "wire_project_surfaces should report the command mirror"
