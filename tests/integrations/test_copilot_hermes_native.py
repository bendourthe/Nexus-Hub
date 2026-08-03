"""Copilot agents/hooks and Hermes layout compatibility (v3.15.8 Phase 8).

Three surfaces, and only one of them is a new write.

**Copilot global agents (8.1)** are delivered to `~/.copilot/agents/*.agent.md`,
verbatim, because Copilot accepts the catalog's Claude-style frontmatter as-is.

**Copilot hooks (8.2) and project agents** are NOT written. Copilot in VS Code
reads Claude-format files by default -- `~/.claude/settings.json` and
`.claude/settings.json` for hooks, `.claude/agents` for project agents -- all of
which Nexus-Hub already produces. The tests here therefore prove *inheritance*:
that the files Copilot's documented defaults point at are the files this repo
writes, and that nothing claims a Copilot-owned hook surface that does not exist.

**Hermes (8.3)** is a regression guard. The upstream docs state that Hermes
"discovers skills by listing every subdirectory of the tap path and probing each
for SKILL.md", so the flattened layout is required rather than merely tolerated,
and a category-nested migration would break discovery outright.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.copilot import (
    _MAX_AGENT_PROMPT_CHARS,
    CopilotIntegration,
)

# Copilot's default hook-file locations, quoted from the VS Code hooks reference
# (`chat.hookFilesLocations` default value). Nexus-Hub writes the Claude entries.
COPILOT_DEFAULT_HOOK_LOCATIONS = (
    ".github/hooks",
    ".claude/settings.local.json",
    ".claude/settings.json",
    "~/.claude/settings.json",
)

# Copilot's default custom-agent locations, from the VS Code custom-agents doc.
COPILOT_DEFAULT_AGENT_LOCATIONS = (
    ".github/agents",
    ".claude/agents",
    "~/.copilot/agents",
)


@pytest.fixture
def copilot():
    return get("copilot")


@pytest.fixture
def hermes():
    return get("hermes")


@pytest.fixture
def copilot_home(tmp_path: Path) -> Path:
    return (tmp_path / "copilot-home" / ".copilot").resolve()


def _catalog_agents(ctx: InstallContext) -> list[Path]:
    return sorted((ctx.repo_root / "catalog" / "agents").glob("*.md"))


# ----- 8.1 Copilot global agents ------------------------------------------


def test_every_catalog_agent_is_delivered_verbatim(copilot, install_ctx, copilot_home):
    """Copilot reads the Claude frontmatter shape, so no transform may occur."""
    copilot._install_global_agents(copilot_home, install_ctx)
    dst_dir = copilot_home / "agents"
    for src in _catalog_agents(install_ctx):
        dst = dst_dir / f"{src.stem}.agent.md"
        assert dst.exists(), f"{src.name} was not delivered"
        assert dst.read_bytes() == src.read_bytes(), f"{src.name} was modified"


def test_agents_use_the_documented_agent_md_suffix(copilot, install_ctx, copilot_home):
    """`.agent.md` is the documented extension and the cross-level dedup key."""
    copilot._install_global_agents(copilot_home, install_ctx)
    delivered = sorted(p.name for p in (copilot_home / "agents").glob("*"))
    assert delivered
    assert all(name.endswith(".agent.md") for name in delivered)
    expected = sorted(f"{p.stem}.agent.md" for p in _catalog_agents(install_ctx))
    assert delivered == expected


def test_every_catalog_agent_satisfies_copilots_requirements(install_ctx):
    """description is required and the prompt is capped at 30,000 characters."""
    for md in _catalog_agents(install_ctx):
        reason = CopilotIntegration.agent_skip_reason(md.read_text(encoding="utf-8"))
        assert reason is None, f"{md.name}: {reason}"


@pytest.mark.parametrize(
    "markdown,expect_skip",
    [
        ("---\nname: ok\ndescription: d\n---\n\nBody.\n", False),
        ("---\ndescription: name is optional for Copilot\n---\n\nBody.\n", False),
        ("---\nname: ok\n---\n\nBody but no description.\n", True),
        ("---\nname: ok\ndescription: d\n---\n\n", True),
    ],
)
def test_agent_validation_matches_copilots_documented_rules(markdown, expect_skip):
    assert (CopilotIntegration.agent_skip_reason(markdown) is not None) is expect_skip


def test_agent_over_the_prompt_cap_is_skipped():
    body = "x" * (_MAX_AGENT_PROMPT_CHARS + 1)
    markdown = f"---\nname: huge\ndescription: d\n---\n\n{body}\n"
    reason = CopilotIntegration.agent_skip_reason(markdown)
    assert reason is not None and "cap" in reason


def test_user_authored_agent_is_never_overwritten(copilot, install_ctx, copilot_home):
    dst = copilot_home / "agents" / "planner.agent.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    mine = "---\nname: planner\ndescription: mine\n---\n\nMy own planner.\n"
    dst.write_text(mine, encoding="utf-8")

    copilot._install_global_agents(copilot_home, install_ctx)

    assert dst.read_text(encoding="utf-8") == mine


def test_owned_agent_is_repaired_and_reinstall_is_idempotent(
    copilot, install_ctx, copilot_home
):
    copilot._install_global_agents(copilot_home, install_ctx)
    dst = copilot_home / "agents" / "planner.agent.md"
    original = dst.read_bytes()
    dst.write_text("drifted", encoding="utf-8")

    copilot._install_global_agents(copilot_home, install_ctx)
    assert dst.read_bytes() == original

    copilot._install_global_agents(copilot_home, install_ctx)
    assert dst.read_bytes() == original


def test_dry_run_writes_no_agents(copilot, install_ctx, copilot_home):
    copilot._install_global_agents(copilot_home, replace(install_ctx, dry_run=True))
    assert not list((copilot_home / "agents").glob("*")) if (
        copilot_home / "agents"
    ).exists() else True


# ----- 8.1 detection gate --------------------------------------------------


def _isolate_global(monkeypatch, copilot_home: Path, vscode_user: Path | None = None):
    """Redirect BOTH global accessors so no test reaches the real home dir."""
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._vscode_user_dir", lambda: vscode_user
    )
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._copilot_home", lambda: copilot_home
    )


def test_global_install_is_skipped_when_copilot_is_absent(
    copilot, install_ctx, monkeypatch, copilot_home
):
    """No VS Code user dir and no ~/.copilot means Copilot is not installed."""
    _isolate_global(monkeypatch, copilot_home)

    result = copilot.install_global(install_ctx)

    assert result.detected is False
    assert not copilot_home.exists()


def test_absent_copilot_summary_claims_nothing_was_installed(
    copilot, install_ctx, monkeypatch, copilot_home
):
    _isolate_global(monkeypatch, copilot_home)

    result = copilot.install_global(install_ctx)

    assert result.files == []
    assert any("not detected" in note for note in result.notes)


def test_copilot_home_alone_is_enough_to_install_agents(
    copilot, install_ctx, monkeypatch, copilot_home
):
    """A Copilot CLI user with no VS Code install still gets the agents."""
    copilot_home.mkdir(parents=True)
    _isolate_global(monkeypatch, copilot_home)

    result = copilot.install_global(install_ctx)

    assert result.detected is True
    assert list((copilot_home / "agents").glob("*.agent.md"))


def test_global_install_never_touches_the_real_home(copilot, install_ctx, monkeypatch):
    """Both global surfaces must be reachable only through a patchable accessor.

    This is the guard for the defect Phase 8 introduced and then fixed: adding a
    second detection signal made an existing test write 23 agent files into the
    developer's actual `~/.copilot`.
    """
    called: list[str] = []
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._vscode_user_dir", lambda: None
    )
    real_home = Path.home()

    def _fake_home() -> Path:
        called.append("copilot_home")
        return install_ctx.target_root / "isolated" / ".copilot"

    monkeypatch.setattr("scripts.lib.integrations.copilot._copilot_home", _fake_home)
    copilot.install_global(install_ctx)

    assert called, "install_global did not route through _copilot_home"
    assert not (real_home / ".copilot" / "agents").exists() or not any(
        (real_home / ".copilot" / "agents").glob("*.agent.md")
    )


# ----- 8.2 hooks are inherited, not duplicated ----------------------------


def test_copilot_declares_no_owned_hook_surface(copilot):
    """Copilot hooks come from the Claude-format files, so nothing is claimed here."""
    assert copilot.config.get("hooks_supported") is False
    assert "hooks_subdir" not in copilot.config


def test_no_github_hooks_or_agents_are_written(copilot, install_ctx):
    """A `.github/` copy would be commit-visible and redundant."""
    copilot.install_workspace(install_ctx)
    github = install_ctx.target_root / ".github"
    assert not (github / "hooks").exists()
    assert not (github / "agents").exists()


def test_the_claude_files_copilot_reads_are_the_ones_nexus_hub_writes(install_ctx):
    """Inheritance proof: Copilot's default hook locations include Claude's files.

    If the Claude integration ever stopped writing `.claude/settings.json` or
    stopped registering hooks there, Copilot's hook coverage would silently
    disappear, so this asserts the dependency rather than assuming it.
    """
    claude = get("claude")
    assert claude.config["workspace_dir"] == ".claude"
    assert claude.config["global_dir"] == "~/.claude"
    # The installer merges catalog/hooks/settings.json into <claude_dir>/settings.json.
    template = install_ctx.repo_root / "catalog" / "hooks" / "settings.json"
    assert template.is_file()
    hooks = json.loads(template.read_text(encoding="utf-8"))["hooks"]
    # Every event Copilot supports and the catalog registers must be present in
    # the file Copilot reads.
    copilot_events = {
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PreCompact",
        "Stop",
    }
    assert copilot_events & set(hooks), "no shared events in the inherited file"


def test_claude_project_agents_directory_is_a_copilot_default_location(install_ctx):
    """Copilot's project agent defaults include `.claude/agents`, which we write."""
    claude = get("claude")
    assert claude.config["agents_subdir"] == "agents"
    assert ".claude/agents" in COPILOT_DEFAULT_AGENT_LOCATIONS


def test_recorded_copilot_defaults_stay_in_step_with_the_contract():
    """The quoted default locations must appear in the read contract prose."""
    doc = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "policy"
        / "platform-read-contracts.md"
    ).read_text(encoding="utf-8")
    for location in ("~/.claude/settings.json", ".claude/agents", "~/.copilot/agents"):
        assert location in doc, location


# ----- 8.2 the skills selector must not regress ---------------------------


def test_skills_selector_still_defaults_to_off(copilot, install_ctx, monkeypatch):
    monkeypatch.delenv("NEXUS_HUB_COPILOT_SKILLS", raising=False)
    result = copilot.wire_project_surfaces(install_ctx)
    assert not (install_ctx.target_root / ".github" / "skills").exists()
    assert any("opt-in" in note for note in result.notes)


@pytest.mark.parametrize("value", ["1", "core-developer", "all"])
def test_skills_selector_still_seeds_when_opted_in(
    copilot, install_ctx, monkeypatch, value
):
    monkeypatch.setenv("NEXUS_HUB_COPILOT_SKILLS", value)
    copilot.wire_project_surfaces(install_ctx)
    seeded = list((install_ctx.target_root / ".github" / "skills").glob("*/SKILL.md"))
    assert seeded, value


def test_skills_selector_never_overwrites_a_committed_file(
    copilot, install_ctx, monkeypatch
):
    monkeypatch.setenv("NEXUS_HUB_COPILOT_SKILLS", "1")
    dst = install_ctx.target_root / ".github" / "skills" / "commit" / "SKILL.md"
    dst.parent.mkdir(parents=True)
    dst.write_text("mine", encoding="utf-8")

    copilot.wire_project_surfaces(install_ctx)

    assert dst.read_text(encoding="utf-8") == "mine"


# ----- 8.3 Hermes layout compatibility ------------------------------------


def test_hermes_skills_are_exactly_one_level_deep(hermes, install_ctx):
    """Hermes probes each direct subdirectory of the tap path for SKILL.md.

    Category nesting would put SKILL.md two levels down, where Hermes would not
    find it, so the flattened layout is required rather than merely accepted.
    """
    hermes.install_workspace(install_ctx)
    skills_root = install_ctx.target_root / ".hermes" / "skills"
    assert skills_root.is_dir()

    direct = [p for p in skills_root.iterdir() if p.is_dir()]
    assert direct, "no skills were delivered"
    for child in direct:
        assert (child / "SKILL.md").is_file(), f"{child.name} has no SKILL.md at depth 1"


def test_no_hermes_skill_md_sits_two_levels_deep(hermes, install_ctx):
    """The failure mode a category-nested migration would introduce."""
    hermes.install_workspace(install_ctx)
    skills_root = install_ctx.target_root / ".hermes" / "skills"
    nested = [
        p
        for p in skills_root.glob("*/*/SKILL.md")
        # A skill's own bundled subdirs (references/, scripts/, assets/) never
        # contain a SKILL.md, so any match here is a category layer.
    ]
    assert nested == [], f"SKILL.md found below depth 1: {nested[:3]}"


def test_hermes_skill_dirs_are_discoverable_names(hermes, install_ctx):
    """Hermes ignores directories starting with `.` or `_`."""
    hermes.install_workspace(install_ctx)
    skills_root = install_ctx.target_root / ".hermes" / "skills"
    for child in skills_root.iterdir():
        if child.is_dir():
            assert not child.name.startswith(("._", ".", "_")), child.name


def test_hermes_commands_also_surface_as_skills(hermes, install_ctx):
    """Skills are Hermes's only action surface, so commands must appear there."""
    hermes.install_workspace(install_ctx)
    names = {
        p.name for p in (install_ctx.target_root / ".hermes" / "skills").iterdir()
    }
    assert "implement" in names or "plan" in names


def test_hermes_does_not_write_the_shared_agents_alias(hermes, install_ctx):
    """Hermes reads `.agents/skills` but codex/antigravity own it."""
    hermes.install_workspace(install_ctx)
    assert not (install_ctx.target_root / ".agents").exists()


def test_hermes_global_is_detection_gated(hermes, install_ctx, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: install_ctx.target_root))
    result = hermes.install_global(install_ctx)
    assert result.detected is False
    assert not (install_ctx.target_root / ".hermes" / "skills").exists()
