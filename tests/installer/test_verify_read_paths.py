"""Unit coverage for runner.py `verify` per-platform read-path checks (v3.11.0 Phase 7.4).

Loads the hyphen-free runner.py by path and exercises the pure `_verify_checks`
helper against fixture HOME / project directories, asserting PASS vs NEEDS-ACTION -
including the Antigravity 2.0 project-only `.agents/` surface (the reported bug).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_RUNNER = (
    Path(__file__).resolve().parents[2]
    / "scripts" / "lib" / "integrations" / "runner.py"
)


def _load_runner():
    spec = importlib.util.spec_from_file_location("nh_runner_verify", _RUNNER)
    assert spec and spec.loader, f"cannot load {_RUNNER}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_runner()

from scripts.lib.integrations import _detection  # noqa: E402  (path set by the runner load)


@pytest.fixture(autouse=True)
def _no_real_path(monkeypatch):
    """v4.14.7: verify now probes PATH for gated platforms; never read the real one."""
    monkeypatch.setattr(_detection, "safe_which", lambda _name: None)


def _by_label(checks):
    return {c[0]: c for c in checks}


def _all_ok(check):
    return all(ok for _, ok in check[1])


def _mk_claude(home: Path, populated: bool) -> None:
    d = home / ".claude"
    (d / "commands").mkdir(parents=True)
    (d / "skills" / "s").mkdir(parents=True)
    if populated:
        (d / "commands" / "x.md").write_text("x", encoding="utf-8")
        (d / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
        (d / "CLAUDE.md").write_text("# Nexus-Hub Skill Index\n", encoding="utf-8")
    else:
        (d / "CLAUDE.md").write_text("no index here", encoding="utf-8")


def test_claude_pass(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    _mk_claude(home, populated=True)
    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Claude"]
    assert _all_ok(check)


def test_claude_needs_action_when_empty(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    _mk_claude(home, populated=False)
    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Claude"]
    assert not _all_ok(check)


def test_antigravity_ide_and_cli_global_pass(tmp_path):
    """Corrected v3.12.0 paths: IDE global at ~/.gemini/config (skills +
    workflows) + ~/.gemini/GEMINI.md; CLI at ~/.gemini/antigravity-cli.
    """
    home = tmp_path / "home"
    cfg = home / ".gemini" / "config"
    (cfg / "skills" / "s").mkdir(parents=True)
    (cfg / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
    (cfg / "workflows").mkdir(parents=True)
    (cfg / "workflows" / "c.md").write_text("c", encoding="utf-8")
    (cfg / "agents").mkdir(parents=True)
    (cfg / "agents" / "planner.md").write_text("a", encoding="utf-8")
    (home / ".gemini" / "GEMINI.md").write_text("# Nexus-Hub Skill Index\n", encoding="utf-8")
    cli = home / ".gemini" / "antigravity-cli"
    (cli / "skills" / "s").mkdir(parents=True)
    (cli / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
    (cli / "settings.json").write_text('{"agentMode": "default"}', encoding="utf-8")
    proj = tmp_path / "proj"
    proj.mkdir()

    labels = _by_label(runner._verify_checks(home, proj))
    assert _all_ok(labels["Antigravity 2.0 IDE (global)"])
    assert _all_ok(labels["Antigravity 2.0 CLI (agy)"])
    # The old (unread) ~/.gemini/antigravity global root must NOT be checked.
    assert "Antigravity 2.0 (global)" not in labels
    proj_check = labels["Antigravity 2.0 (this project .agents/)"]
    assert not _all_ok(proj_check)
    assert "nexus-hub init" in (proj_check[2] or "")

    # Seed the project's verified .agents surfaces -> PASS.
    (proj / ".agents" / "skills" / "s").mkdir(parents=True)
    (proj / ".agents" / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
    (proj / ".agents" / "workflows").mkdir(parents=True)
    (proj / ".agents" / "workflows" / "c.md").write_text("c", encoding="utf-8")
    (proj / ".agents" / "agents").mkdir(parents=True)
    (proj / ".agents" / "agents" / "planner.md").write_text("a", encoding="utf-8")
    labels2 = _by_label(runner._verify_checks(home, proj))
    assert _all_ok(labels2["Antigravity 2.0 (this project .agents/)"])

    # An obsolete global destination alone must not satisfy current discovery.
    (cfg / "workflows").rename(cfg / "global_workflows")
    obsolete = _by_label(runner._verify_checks(home, proj))
    assert not _all_ok(obsolete["Antigravity 2.0 IDE (global)"])


def test_codex_pass_and_needs_action(tmp_path):
    """Codex verifies shared skills, prompts, instructions, agents, and hooks.

    The undocumented ``~/.codex/skills`` duplicate and obsolete mandatory
    ``[features] hooks = true`` switch are deliberately absent.
    """
    home = tmp_path / "home"
    d = home / ".codex"
    (d / "prompts").mkdir(parents=True)
    (d / "prompts" / "presentify.md").write_text("p", encoding="utf-8")
    (d / "AGENTS.md").write_text("# Nexus-Hub Skill Index\n", encoding="utf-8")
    (d / "agents").mkdir(parents=True)
    (d / "agents" / "planner.toml").write_text('name = "planner"\n', encoding="utf-8")
    (d / "hooks.json").write_text(
        '{"hooks": {"Stop": [{"hooks": [{"statusMessage": "Nexus-Hub x"}]}]}}',
        encoding="utf-8",
    )
    (home / ".agents" / "skills" / "presentify").mkdir(parents=True)
    (home / ".agents" / "skills" / "presentify" / "SKILL.md").write_text("s", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Codex / ChatGPT"]
    assert _all_ok(check)
    assert {name for name, _ in check[1]} >= {
        "custom agents",
        "hooks registration",
    }
    assert "skills" not in {name for name, _ in check[1]}
    assert "hooks feature switch" not in {name for name, _ in check[1]}

    # Remove the ~/.agents/skills mirror -> NEEDS-ACTION.
    import shutil
    shutil.rmtree(home / ".agents")
    check2 = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Codex / ChatGPT"]
    assert not _all_ok(check2)


def test_codex_hook_surfaces_flag_when_absent(tmp_path):
    """A Codex install with no Nexus-Hub hook registration needs action."""
    home = tmp_path / "home"
    d = home / ".codex"
    (d / "prompts").mkdir(parents=True)
    (d / "prompts" / "presentify.md").write_text("p", encoding="utf-8")
    (d / "AGENTS.md").write_text("# Nexus-Hub Skill Index\n", encoding="utf-8")
    (d / "agents").mkdir(parents=True)
    (d / "agents" / "planner.toml").write_text('name = "planner"\n', encoding="utf-8")
    (d / "hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
    (home / ".agents" / "skills" / "presentify").mkdir(parents=True)
    (home / ".agents" / "skills" / "presentify" / "SKILL.md").write_text("s", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Codex / ChatGPT"]
    assert not _all_ok(check)
    failing = {name for name, ok in check[1] if not ok}
    assert failing == {"hooks registration"}


def test_cursor_verify_pass_and_needs_action(tmp_path):
    """Cursor verifies command-skills, agents, and hooks, not legacy commands."""
    home = tmp_path / "home"
    c = home / ".cursor"
    (c / "skills" / "s").mkdir(parents=True)
    (c / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
    (c / "agents").mkdir(parents=True)
    (c / "agents" / "a.md").write_text("a", encoding="utf-8")
    (c / "hooks.json").write_text("{}", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Cursor"]
    assert _all_ok(check)
    assert {name for name, _ in check[1]} >= {"skills", "agents", "hooks.json"}
    assert "commands" not in {name for name, _ in check[1]}

    # Remove the hooks.json file -> NEEDS-ACTION.
    (c / "hooks.json").unlink()
    check2 = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Cursor"]
    assert not _all_ok(check2)


def test_gemini_ide_verifies_instruction_only(tmp_path):
    home = tmp_path / "home"
    gemini = home / ".gemini"
    gemini.mkdir(parents=True)
    (gemini / "GEMINI.md").write_text("# instructions\n", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Gemini IDE"]

    assert _all_ok(check)
    assert [name for name, _ in check[1]] == ["GEMINI.md"]


def test_copilot_native_global_and_project_surfaces_pass(tmp_path):
    home = tmp_path / "home"
    copilot = home / ".copilot"
    (copilot / "agents").mkdir(parents=True)
    (copilot / "agents" / "planner.agent.md").write_text("a", encoding="utf-8")
    (copilot / "copilot-instructions.md").write_text("i", encoding="utf-8")
    (copilot / "hooks" / "nexus-hub-scripts").mkdir(parents=True)
    (copilot / "hooks" / "nexus-hub-scripts" / "guard.py").write_text("x", encoding="utf-8")
    (copilot / "hooks" / "nexus-hub.json").write_text(
        '{"version": 1, "hooks": {}}', encoding="utf-8"
    )
    project = tmp_path / "proj"
    github = project / ".github"
    (github / "agents").mkdir(parents=True)
    (github / "agents" / "planner.agent.md").write_text("a", encoding="utf-8")
    (github / "copilot-instructions.md").write_text("i", encoding="utf-8")
    (github / "hooks").mkdir(parents=True)
    (github / "hooks" / "nexus-hub.json").write_text(
        '{"version": 1, "hooks": {}}', encoding="utf-8"
    )

    labels = _by_label(runner._verify_checks(home, project))

    assert _all_ok(labels["GitHub Copilot"])
    assert _all_ok(labels["GitHub Copilot (this project)"])


def test_windsurf_native_global_and_project_surfaces_pass(tmp_path):
    home = tmp_path / "home"
    windsurf = home / ".codeium" / "windsurf"
    (windsurf / "memories").mkdir(parents=True)
    (windsurf / "memories" / "global_rules.md").write_text("r", encoding="utf-8")
    for subdir in ("skills", "global_workflows", "hooks"):
        (windsurf / subdir).mkdir(parents=True, exist_ok=True)
        (windsurf / subdir / "x").write_text("x", encoding="utf-8")
    (windsurf / "hooks.json").write_text(
        '{"hooks": {"pre_run_command": []}}', encoding="utf-8"
    )
    project = tmp_path / "proj"
    (project / ".windsurf" / "skills").mkdir(parents=True)
    (project / ".windsurf" / "skills" / "x").write_text("x", encoding="utf-8")
    (project / ".windsurf" / "workflows").mkdir(parents=True)
    (project / ".windsurf" / "workflows" / "x.md").write_text("x", encoding="utf-8")
    (project / ".windsurf" / "hooks.json").write_text(
        '{"hooks": {"pre_run_command": []}}', encoding="utf-8"
    )
    (project / ".devin" / "rules").mkdir(parents=True)
    (project / ".devin" / "rules" / "nexus-hub.md").write_text("r", encoding="utf-8")
    (project / "AGENTS.md").write_text("i", encoding="utf-8")
    (project / ".windsurfrules").write_text("i", encoding="utf-8")

    labels = _by_label(runner._verify_checks(home, project))

    assert _all_ok(labels["Devin Desktop / Windsurf"])
    assert _all_ok(labels["Devin Desktop / Windsurf (this project)"])


def test_openclaw_verifies_configured_workspace_without_hooks(tmp_path):
    home = tmp_path / "home"
    openclaw = home / ".openclaw"
    openclaw.mkdir(parents=True)
    (openclaw / "openclaw.json").write_text(
        '{"agents": {"defaults": {"workspace": "custom-workspace"}}}',
        encoding="utf-8",
    )
    workspace = home / "custom-workspace"
    workspace.mkdir()
    for name in ("AGENTS.md", "SOUL.md", "IDENTITY.md"):
        (workspace / name).write_text("x", encoding="utf-8")
    (workspace / "skills").mkdir()
    (workspace / "skills" / "x").write_text("x", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["OpenClaw"]

    assert _all_ok(check)
    assert "hooks" not in {name for name, _ in check[1]}


def test_openclaw_verifier_fails_soft_without_using_fallback_for_bad_config(
    tmp_path, monkeypatch
):
    for name in (
        "OPENCLAW_HOME",
        "OPENCLAW_STATE_DIR",
        "OPENCLAW_CONFIG_PATH",
        "OPENCLAW_WORKSPACE_DIR",
    ):
        monkeypatch.delenv(name, raising=False)
    home = tmp_path / "home"
    openclaw = home / ".openclaw"
    openclaw.mkdir(parents=True)
    (openclaw / "openclaw.json").write_text(
        "{agents: {defaults: {workspace: 'unterminated}}}",
        encoding="utf-8",
    )
    fallback = openclaw / "workspace"
    fallback.mkdir()
    for name in ("AGENTS.md", "SOUL.md", "IDENTITY.md"):
        (fallback / name).write_text("x", encoding="utf-8")
    (fallback / "skills").mkdir()
    (fallback / "skills" / "x").write_text("x", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["OpenClaw"]

    assert not _all_ok(check)
    assert all(ok is False for _, ok in check[1])


def _write_openclaw_surfaces(workspace: Path) -> None:
    workspace.mkdir(parents=True)
    for name in ("AGENTS.md", "SOUL.md", "IDENTITY.md"):
        (workspace / name).write_text("x", encoding="utf-8")
    (workspace / "skills").mkdir()
    (workspace / "skills" / "x").write_text("x", encoding="utf-8")


@pytest.mark.parametrize(
    "override",
    [
        "OPENCLAW_CONFIG_PATH",
        "OPENCLAW_STATE_DIR",
        "OPENCLAW_HOME",
        "OPENCLAW_WORKSPACE_DIR",
    ],
)
def test_openclaw_verifier_detects_override_only_location(
    tmp_path, monkeypatch, override
):
    for name in (
        "OPENCLAW_HOME",
        "OPENCLAW_STATE_DIR",
        "OPENCLAW_CONFIG_PATH",
        "OPENCLAW_WORKSPACE_DIR",
    ):
        monkeypatch.delenv(name, raising=False)
    home = tmp_path / "home"
    home.mkdir()

    if override == "OPENCLAW_CONFIG_PATH":
        workspace = home / "config-workspace"
        config_path = home / "service-config" / "openclaw.json5"
        config_path.parent.mkdir()
        config_path.write_text(
            "{agents: {defaults: {workspace: 'config-workspace'}}}",
            encoding="utf-8",
        )
        monkeypatch.setenv(override, str(config_path))
    elif override == "OPENCLAW_STATE_DIR":
        state_dir = home / "service-state"
        workspace = state_dir / "workspace"
        monkeypatch.setenv(override, str(state_dir))
    elif override == "OPENCLAW_HOME":
        openclaw_home = home / "service-home"
        workspace = openclaw_home / ".openclaw" / "workspace"
        monkeypatch.setenv(override, str(openclaw_home))
    else:
        workspace = home / "workspace-from-environment"
        monkeypatch.setenv(override, str(workspace))

    _write_openclaw_surfaces(workspace)

    labels = _by_label(runner._verify_checks(home, tmp_path / "proj"))

    assert not (home / ".openclaw").exists()
    assert _all_ok(labels["OpenClaw"])


def test_openclaw_unusable_explicit_config_is_visible_needs_action(
    tmp_path, monkeypatch, capsys
):
    for name in (
        "OPENCLAW_HOME",
        "OPENCLAW_STATE_DIR",
        "OPENCLAW_CONFIG_PATH",
        "OPENCLAW_WORKSPACE_DIR",
    ):
        monkeypatch.delenv(name, raising=False)
    home = tmp_path / "home"
    home.mkdir()
    missing_config = home / "service-config" / "missing.json5"
    monkeypatch.setenv("OPENCLAW_CONFIG_PATH", str(missing_config))
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    project = tmp_path / "proj"
    project.mkdir()
    args = runner.build_parser().parse_args(
        ["verify", "--target", str(project), "--quiet"]
    )

    assert runner.cmd_verify(args) == 0

    output = capsys.readouterr().out
    assert "[verify] NEEDS-ACTION OpenClaw" in output
    assert "no supported platform config dirs detected" not in output


def test_hermes_verifies_native_skills_only(tmp_path):
    home = tmp_path / "home"
    skills = home / ".hermes" / "skills"
    skills.mkdir(parents=True)
    (skills / "x").write_text("x", encoding="utf-8")
    # v4.14.7: an entry Hermes itself creates, so the root is real evidence.
    (home / ".hermes" / "logs").mkdir()

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Hermes"]

    assert _all_ok(check)
    assert [name for name, _ in check[1]] == ["native skills"]


def test_opencode_agents_verify_pass(tmp_path):
    """v3.15.0 Phase 6: OpenCode verify now includes the new agents surface."""
    home = tmp_path / "home"
    d = home / ".config" / "opencode"
    (d / "skills" / "s").mkdir(parents=True)
    (d / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
    (d / "agents").mkdir(parents=True)
    (d / "agents" / "a.md").write_text("a", encoding="utf-8")
    (d / "AGENTS.md").write_text("# Nexus-Hub Skill Index\n", encoding="utf-8")
    # v4.14.7: OpenCode's own config file, so the root is real evidence.
    (d / "opencode.json").write_text("{}", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["OpenCode"]
    assert _all_ok(check)
    assert any(name == "agents" for name, _ in check[1]), "agents surface must be verified"


def test_opencode_workspace_instruction_is_project_root_agents_md(tmp_path):
    home = tmp_path / "home"
    project = tmp_path / "proj"
    opencode = project / ".opencode"
    (opencode / "skills").mkdir(parents=True)
    (opencode / "skills" / "x").write_text("x", encoding="utf-8")
    (opencode / "agents").mkdir()
    (opencode / "agents" / "x.md").write_text("x", encoding="utf-8")
    (project / "AGENTS.md").write_text("i", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, project))["OpenCode (this project)"]

    assert _all_ok(check)
    assert not (opencode / "AGENTS.md").exists()


def _provision_qwen(home: Path) -> Path:
    """Lay down every Qwen surface the read contract verifies."""
    d = home / ".qwen"
    (d / "skills" / "s").mkdir(parents=True)
    # v4.14.7: an entry Qwen itself creates, so the root is real evidence.
    (d / "file-history").mkdir()
    (d / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
    (d / "commands").mkdir(parents=True)
    (d / "commands" / "x.md").write_text("x", encoding="utf-8")
    (d / "QWEN.md").write_text("# idx", encoding="utf-8")
    # v3.15.8 Phase 6: native hooks are a `hooks` key in settings.json plus the
    # owned script directory the handler commands point at.
    (d / "hooks").mkdir(parents=True)
    (d / "hooks" / "secret-scan.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (d / "settings.json").write_text(
        '{"hooks": {"PreToolUse": [{"hooks": [{"name": "nexus-hub:secret-scan"}]}]}}',
        encoding="utf-8",
    )
    return d


def test_qwen_verify_pass_and_needs_action(tmp_path):
    """v3.15.0 Phase 6 + v3.15.8 Phase 6: skills / commands / QWEN.md / hooks."""
    home = tmp_path / "home"
    d = _provision_qwen(home)

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Qwen Code"]
    assert _all_ok(check)
    names = {name for name, _ok in check[1]}
    assert {"hooks registration", "hook scripts"} <= names

    import shutil
    shutil.rmtree(d / "commands")
    check2 = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Qwen Code"]
    assert not _all_ok(check2)


def test_qwen_hook_surfaces_flag_when_absent(tmp_path):
    """A settings.json with no Nexus-Hub handler is NEEDS-ACTION, not a pass.

    Qwen enables hooks by default, so there is no feature switch to check. What
    a verify run can prove is that our handlers are actually registered, which
    is what distinguishes an installed guardrail from a settings file the user
    happens to have.
    """
    home = tmp_path / "home"
    d = _provision_qwen(home)
    # A user's own settings file, with no Nexus-Hub registration in it.
    (d / "settings.json").write_text('{"ui": {"theme": "dark"}}', encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Qwen Code"]
    assert not _all_ok(check)
    failed = {name for name, ok in check[1] if not ok}
    assert failed == {"hooks registration"}


def _provision_kimi(home: Path) -> Path:
    """Lay down every Kimi surface the read contract verifies."""
    d = home / ".kimi-code"
    (d / "skills" / "s").mkdir(parents=True)
    # v4.14.7: an entry Kimi itself creates, so the root is real evidence.
    (d / "sessions").mkdir()
    (d / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
    (d / "AGENTS.md").write_text("# idx", encoding="utf-8")
    # v3.15.8 Phase 7: verbatim agent Markdown plus the marker-managed hook block.
    (d / "agents").mkdir(parents=True)
    (d / "agents" / "planner.md").write_text("---\nname: p\n---\n", encoding="utf-8")
    (d / "hooks").mkdir(parents=True)
    (d / "hooks" / "secret-scan.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (d / "config.toml").write_text(
        "# >>> NEXUS_HUB_HOOKS_START >>>\n"
        '[[hooks]]\nevent = "PreToolUse"\ncommand = "bash x.sh"\n'
        "# <<< NEXUS_HUB_HOOKS_END <<<\n",
        encoding="utf-8",
    )
    return d


def test_kimi_verify_pass(tmp_path):
    """v3.15.0 Phase 6 + v3.15.8 Phase 7: skills / AGENTS.md / agents / hooks."""
    home = tmp_path / "home"
    _provision_kimi(home)

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Kimi Code CLI"]
    assert _all_ok(check)
    assert {"custom agents", "hooks registration", "hook scripts"} <= {
        name for name, _ok in check[1]
    }


def test_kimi_hook_block_absence_is_needs_action(tmp_path):
    """A config.toml with no managed block means the hooks were never installed."""
    home = tmp_path / "home"
    d = _provision_kimi(home)
    (d / "config.toml").write_text("verbose = true\n", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Kimi Code CLI"]
    assert not _all_ok(check)
    assert {name for name, ok in check[1] if not ok} == {"hooks registration"}


def test_no_platforms_detected(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert runner._verify_checks(home, tmp_path / "proj") == []


# --- Claude project instruction capability (v4.15.2, Phase 4) ---------------
# The decision is conservative: every unknown, unreadable, conflicting, or blocked
# input must select CLAUDE.md. Each case below pins one vendor-documented fact or
# one failure direction. No test needs the real `claude` binary or the real HOME.

import json  # noqa: E402

from scripts.lib.integrations import claude as claude_mod  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.claude import (  # noqa: E402
    ClaudeIntegration,
    classify_project_claude_md,
    claude_only_sections,
    decide_instruction_path,
    persist_decision,
    read_decision,
)
from scripts.lib.integrations.codex import CodexIntegration  # noqa: E402
from scripts.lib.integrations.cursor import CursorIntegration  # noqa: E402
from scripts.lib.integrations.opencode import OpenCodeIntegration  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ID = "cc-plugin-agents-md@builtin"
LEGACY_PLUGIN_ID = "agents-md@builtin"


def _ctx(tmp_path: Path, **kw) -> InstallContext:
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    return InstallContext(
        repo_root=REPO_ROOT, target_root=project, scope="workspace", instruction_only=True,
        manifest=kw.pop("manifest", InstallManifest()), **kw,
    )


def _env(tmp_path: Path, version: str | None = "2.1.281", **extra: str) -> dict:
    env = {"CLAUDE_CONFIG_DIR": str(tmp_path / "cfg"),
           "NEXUS_HUB_CLAUDE_MANAGED_SETTINGS": str(tmp_path / "managed.json")}
    if version is not None:
        env["NEXUS_HUB_CLAUDE_VERSION"] = version
    env.update(extra)
    return env


def _user_settings(tmp_path: Path, body) -> None:
    cfg = tmp_path / "cfg"
    cfg.mkdir(exist_ok=True)
    (cfg / "settings.json").write_text(body if isinstance(body, str) else json.dumps(body), encoding="utf-8")


def _entry(value=None, plugin_id=PLUGIN_ID, **options) -> dict:
    opts = dict(options)
    if value is not None:
        opts["instructionFiles"] = value
    return {"pluginConfigs": {plugin_id: {"options": opts}}}


def _decide(tmp_path: Path, **env_kw):
    return decide_instruction_path(_ctx(tmp_path), (tmp_path / "project").resolve(), _env(tmp_path, **env_kw))


@pytest.mark.parametrize("version,extra,path", [
    ("2.1.281", {}, "AGENTS.md"),
    ("2.1.277", {}, "AGENTS.md"),
    ("2.1.276", {}, "CLAUDE.md"),
    ("2.1.280", {"CLAUDE_CODE_USE_BEDROCK": "1"}, "CLAUDE.md"),
    ("2.1.281", {"CLAUDE_CODE_USE_BEDROCK": "1"}, "AGENTS.md"),
    ("2.1.280", {"CLAUDE_CODE_USE_VERTEX": "true"}, "CLAUDE.md"),
    ("2.1.280", {"CLAUDE_CODE_USE_FOUNDRY": "1"}, "CLAUDE.md"),
    ("2.1.280", {"ANTHROPIC_BASE_URL": "https://gateway.example"}, "CLAUDE.md"),
    ("2.1.281", {"ANTHROPIC_BASE_URL": "https://gateway.example"}, "AGENTS.md"),
    ("2.1.280", {"DISABLE_TELEMETRY": "1"}, "CLAUDE.md"),
    ("2.1.281", {"DISABLE_TELEMETRY": "1"}, "AGENTS.md"),
    (None, {}, "CLAUDE.md"),
    ("not-a-version", {}, "CLAUDE.md"),
])
def test_version_floor_and_provider_surface_select_the_effective_path(tmp_path, version, extra, path):
    decision = _decide(tmp_path, version=version, **extra)
    assert decision["effective_path"] == path, decision["reason"]
    if version in (None, "not-a-version"):
        assert decision["confidence"] == "unknown"


@pytest.mark.parametrize("plugin_id", [PLUGIN_ID, LEGACY_PLUGIN_ID])
@pytest.mark.parametrize("value,path", [
    ("claude-md-or-agents-md", "AGENTS.md"),
    ("claude-md-and-agents-md", "AGENTS.md"),
    ("claude-md", "CLAUDE.md"),
    ("managed-only", "CLAUDE.md"),
])
def test_each_instruction_files_value_under_either_plugin_id(tmp_path, plugin_id, value, path):
    _user_settings(tmp_path, _entry(value, plugin_id))
    decision = _decide(tmp_path)
    assert decision["effective_path"] == path
    assert decision["instruction_files"] == value and decision["instruction_files_scope"] == "user"


@pytest.mark.parametrize("legacy,path", [
    ("claude", "CLAUDE.md"), ("agents-fallback", "AGENTS.md"), ("both", "AGENTS.md"), ("none", "CLAUDE.md"),
])
def test_legacy_project_instructions_maps_only_when_instruction_files_is_unset(tmp_path, legacy, path):
    _user_settings(tmp_path, _entry(None, projectInstructions=legacy))
    assert _decide(tmp_path)["effective_path"] == path
    _user_settings(tmp_path, _entry("claude-md-or-agents-md", projectInstructions=legacy))
    assert _decide(tmp_path)["effective_path"] == "AGENTS.md", "instructionFiles wins over the legacy key"


def test_a_built_in_reader_disabled_through_plugin_selects_claude_md(tmp_path):
    _user_settings(tmp_path, {"enabledPlugins": {PLUGIN_ID: False}})
    decision = _decide(tmp_path)
    assert decision["effective_path"] == "CLAUDE.md" and "disabled" in decision["reason"]


@pytest.mark.parametrize("body", [
    "{not json",
    "[]",
    {"pluginConfigs": []},
    {"pluginConfigs": {PLUGIN_ID: {"options": {"instructionFiles": "agents-only"}}}},
    {"pluginConfigs": {PLUGIN_ID: {"options": {"projectInstructions": "bogus"}}}},
    {"pluginConfigs": {PLUGIN_ID: {"options": {"instructionFiles": "claude-md"}},
                       LEGACY_PLUGIN_ID: {"options": {"instructionFiles": "claude-md-or-agents-md"}}}},
])
def test_malformed_or_conflicting_settings_are_unknown_and_conservative(tmp_path, body):
    _user_settings(tmp_path, body)
    decision = _decide(tmp_path)
    assert decision["effective_path"] == "CLAUDE.md" and decision["confidence"] == "unknown"
    assert "unreadable" in decision["reason"]


def test_an_unreadable_managed_file_is_unknown_never_the_vendor_default(tmp_path):
    (tmp_path / "managed.json").write_text("{broken", encoding="utf-8")
    decision = _decide(tmp_path)
    assert decision["effective_path"] == "CLAUDE.md" and decision["confidence"] == "unknown"


def test_managed_settings_outrank_user_settings(tmp_path):
    _user_settings(tmp_path, _entry("claude-md-or-agents-md"))
    (tmp_path / "managed.json").write_text(json.dumps(_entry("claude-md")), encoding="utf-8")
    decision = _decide(tmp_path)
    assert decision["effective_path"] == "CLAUDE.md" and decision["instruction_files_scope"] == "managed"
    _user_settings(tmp_path, _entry("claude-md"))
    (tmp_path / "managed.json").write_text(json.dumps(_entry("claude-md-or-agents-md")), encoding="utf-8")
    assert _decide(tmp_path)["effective_path"] == "AGENTS.md"


def test_a_project_scoped_setting_is_ignored_by_the_decision(tmp_path):
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    (project / ".claude" / "settings.json").write_text(json.dumps(_entry("claude-md")), encoding="utf-8")
    (project / ".claude" / "settings.local.json").write_text(json.dumps(_entry("managed-only")), encoding="utf-8")
    decision = _decide(tmp_path)
    assert decision["effective_path"] == "AGENTS.md" and decision["instruction_files_scope"] == "default"


@pytest.mark.parametrize("blocker", ["CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"])
def test_a_project_claude_file_blocks_the_default_fallback(tmp_path, blocker):
    target = tmp_path / "project" / blocker
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# mine\n", encoding="utf-8")
    decision = _decide(tmp_path)
    assert decision["effective_path"] == "CLAUDE.md" and "takes precedence" in decision["reason"]
    assert decision["precedence_blockers"]
    _user_settings(tmp_path, _entry("claude-md-and-agents-md"))
    assert _decide(tmp_path)["effective_path"] == "AGENTS.md"


def test_a_claude_md_in_a_parent_directory_also_blocks(tmp_path):
    (tmp_path / "CLAUDE.md").write_text("# parent\n", encoding="utf-8")
    assert _decide(tmp_path)["effective_path"] == "CLAUDE.md"


def test_the_users_own_global_claude_md_does_not_block(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "CLAUDE.md").write_text("# global\n", encoding="utf-8")
    project = home / "work" / "proj"
    project.mkdir(parents=True)
    ctx = InstallContext(repo_root=REPO_ROOT, target_root=project, scope="workspace", instruction_only=True,
                         manifest=InstallManifest())
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    decision = decide_instruction_path(ctx, project.resolve(), _env(tmp_path))
    assert decision["effective_path"] == "AGENTS.md", decision["reason"]


def test_probe_uses_the_resolved_claude_binary_version(tmp_path):
    ctx = _ctx(tmp_path, which=lambda name: None)
    decision = decide_instruction_path(ctx, (tmp_path / "project").resolve(), _env(tmp_path, version=None))
    assert decision["effective_path"] == "CLAUDE.md" and decision["version"] is None


def test_decision_records_what_was_not_inspected_and_the_no_load_modes(tmp_path):
    decision = _decide(tmp_path)
    assert {"--settings", "mdm", "server-managed"} <= set(decision["not_inspected"])
    assert "CLAUDE_CODE_DISABLE_CLAUDE_MDS" in decision["no_load_modes"]


# --- persistence and transitions --------------------------------------------


def test_decisions_persist_chain_and_stay_stable_when_nothing_changes(tmp_path):
    ctx = _ctx(tmp_path)
    root = (tmp_path / "project").resolve()
    first = decide_instruction_path(ctx, root, _env(tmp_path))
    assert persist_decision(ctx, root, "claude", first).action == "created"
    assert persist_decision(ctx, root, "claude", first).action == "unchanged"
    saved = read_decision(root)
    assert saved["effective_path"] == "AGENTS.md" and saved["prior_decision"] is None
    downgrade = decide_instruction_path(ctx, root, _env(tmp_path, version="2.1.270"))
    assert persist_decision(ctx, root, "claude", downgrade).action == "updated"
    chained = read_decision(root)
    assert chained["effective_path"] == "CLAUDE.md" and chained["prior_decision"] == saved["decision_id"]


def test_read_decision_rejects_a_missing_or_corrupt_record(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    assert read_decision(root) is None
    (root / ".nexus-hub").mkdir()
    (root / ".nexus-hub" / "claude-instruction-decision.json").write_text("{x", encoding="utf-8")
    assert read_decision(root) is None


# --- install behavior ---------------------------------------------------------


def _install_claude(tmp_path, monkeypatch, version="2.1.281", manifest=None, migrate=False, **extra):
    for key, value in _env(tmp_path, version=version, **extra).items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("NEXUS_HUB_CLAUDE_MIGRATE", raising=False)
    if migrate:
        monkeypatch.setenv("NEXUS_HUB_CLAUDE_MIGRATE", "1")
    ctx = _ctx(tmp_path, manifest=manifest or InstallManifest())
    result = ClaudeIntegration().install_workspace(ctx)
    return ctx, result


def test_fresh_supported_install_writes_one_shared_body_and_no_project_claude_md(tmp_path, monkeypatch):
    ctx, _ = _install_claude(tmp_path, monkeypatch)
    project = ctx.target_root
    assert not (project / "CLAUDE.md").exists()
    agents = (project / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.count("<!-- NEXUS_HUB_START -->") == 1
    sidecar = (project / ".claude" / "rules" / "nexus-hub-claude.md").read_text(encoding="utf-8")
    for heading in ("## Agent Registry", "## Spending Controls", "## Environment Variables", "## MCP Integration"):
        assert heading in sidecar and heading not in agents
    # Both files carry a Context References section; only the sidecar's names Claude paths.
    assert ".claude/skills/" in sidecar and ".claude/skills/" not in agents
    assert read_decision(project.resolve())["effective_path"] == "AGENTS.md"
    assert str(project / "AGENTS.md") in ctx.manifest.shared_for("claude")


def test_sidecar_carries_the_claude_only_sections_verbatim(tmp_path, monkeypatch):
    ctx, _ = _install_claude(tmp_path, monkeypatch)
    template = ClaudeIntegration()._render(REPO_ROOT / "templates/ai-instructions/base-claude.md", ctx)
    sidecar = (ctx.target_root / ".claude" / "rules" / "nexus-hub-claude.md").read_text(encoding="utf-8")
    assert sidecar == claude_only_sections(template)
    for section in claude_mod.CLAUDE_ONLY_SECTIONS:
        assert f"## {section}" in template


def test_shared_body_is_the_template_every_consumer_renders(tmp_path, monkeypatch):
    ctx, _ = _install_claude(tmp_path, monkeypatch)
    claude_agents = (ctx.target_root / "AGENTS.md").read_text(encoding="utf-8")
    for index, integration in enumerate((CodexIntegration(), OpenCodeIntegration(), CursorIntegration())):
        other = tmp_path / f"other{index}"
        other.mkdir()
        octx = InstallContext(repo_root=REPO_ROOT, target_root=other, scope="workspace",
                              instruction_only=True, manifest=InstallManifest())
        integration.install_workspace(octx)
        assert (other / "AGENTS.md").read_text(encoding="utf-8") == claude_agents, integration.key


def test_unknown_below_floor_and_blocked_installs_keep_the_managed_claude_md(tmp_path, monkeypatch):
    ctx, _ = _install_claude(tmp_path, monkeypatch, version=None)
    assert (ctx.target_root / "CLAUDE.md").exists() and not (ctx.target_root / "AGENTS.md").exists()
    assert not (ctx.target_root / ".claude" / "rules" / "nexus-hub-claude.md").exists()
    assert read_decision(ctx.target_root.resolve())["effective_path"] == "CLAUDE.md"


def test_existing_user_claude_md_is_preserved_and_stays_the_effective_path(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    original = "# My rules\n\nKeep this exactly.\n"
    (project / "CLAUDE.md").write_text(original, encoding="utf-8")
    ctx, _ = _install_claude(tmp_path, monkeypatch)
    text = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert text.startswith(original.rstrip("\n")) and "<!-- NEXUS_HUB_START -->" in text
    assert not (project / "AGENTS.md").exists()
    assert read_decision(project.resolve())["effective_path"] == "CLAUDE.md"


def test_repeat_install_is_idempotent_on_both_paths(tmp_path, monkeypatch):
    ctx, _ = _install_claude(tmp_path, monkeypatch)
    before = {p: p.read_bytes() for p in ctx.target_root.rglob("*") if p.is_file()}
    _install_claude(tmp_path, monkeypatch, manifest=ctx.manifest)
    after = {p: p.read_bytes() for p in ctx.target_root.rglob("*") if p.is_file()}
    assert before == after


def test_downgrade_then_upgrade_records_new_decisions(tmp_path, monkeypatch):
    ctx, _ = _install_claude(tmp_path, monkeypatch, version="2.1.281")
    first = read_decision(ctx.target_root.resolve())
    _install_claude(tmp_path, monkeypatch, version="2.1.270", manifest=ctx.manifest)
    second = read_decision(ctx.target_root.resolve())
    assert second["effective_path"] == "CLAUDE.md" and second["prior_decision"] == first["decision_id"]
    assert (ctx.target_root / "CLAUDE.md").exists()


MANAGED_ONLY_FILE = "<!-- NEXUS_HUB_START -->\nbody\n<!-- NEXUS_HUB_END -->\n"


@pytest.mark.parametrize("content,state", [
    (None, "none"),
    (MANAGED_ONLY_FILE, "managed-only"),
    ("# mine\n\n" + MANAGED_ONLY_FILE, "mixed"),
    (MANAGED_ONLY_FILE + "\n# tail\n", "mixed"),
    ("# only mine\n", "user-authored"),
])
def test_project_claude_md_states_are_classified(tmp_path, content, state):
    if content is not None:
        (tmp_path / "CLAUDE.md").write_text(content, encoding="utf-8")
    assert classify_project_claude_md(tmp_path) == state


def test_migration_of_a_managed_only_file_deletes_it_and_converges(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text(MANAGED_ONLY_FILE, encoding="utf-8")
    ctx, _ = _install_claude(tmp_path, monkeypatch, migrate=True)
    assert not (project / "CLAUDE.md").exists() and (project / "AGENTS.md").exists()
    assert read_decision(project.resolve())["effective_path"] == "AGENTS.md"


def test_migration_of_a_mixed_file_keeps_user_bytes_and_is_not_called_converged(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("# mine\n\n" + MANAGED_ONLY_FILE, encoding="utf-8")
    ctx, _ = _install_claude(tmp_path, monkeypatch, migrate=True)
    remaining = (project / "CLAUDE.md").read_text(encoding="utf-8")
    assert "# mine" in remaining and "NEXUS_HUB_START" in remaining, "the managed block returns on the exception path"
    assert read_decision(project.resolve())["effective_path"] == "CLAUDE.md"
    assert not (project / "AGENTS.md").exists()


def test_migration_never_touches_a_user_authored_file(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_bytes(b"# mine only\r\nno markers\r\n")
    _install_claude(tmp_path, monkeypatch, migrate=True)
    assert (project / "CLAUDE.md").read_bytes().startswith(b"# mine only\r\nno markers")


def test_no_migration_happens_without_the_explicit_request(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text(MANAGED_ONLY_FILE, encoding="utf-8")
    _install_claude(tmp_path, monkeypatch)
    assert (project / "CLAUDE.md").exists()


def test_nexus_hub_init_writes_no_instruction_files_setting(tmp_path):
    ctx = _ctx(tmp_path)
    ClaudeIntegration().wire_project_surfaces(ctx)
    stub = (tmp_path / "project" / ".claude" / "settings.json").read_text(encoding="utf-8")
    assert "instructionFiles" not in stub and "pluginConfigs" not in stub and "projectInstructions" not in stub


@pytest.fixture(autouse=True)
def _isolated_nexus_home_v4152(tmp_path, monkeypatch):
    """The merge owner keeps lock and backup state under NEXUS_HUB_HOME; never the real home."""
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path / "nexus-home-v4152"))
