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
    global_workflows) + ~/.gemini/GEMINI.md; CLI at ~/.gemini/antigravity-cli.
    """
    home = tmp_path / "home"
    cfg = home / ".gemini" / "config"
    (cfg / "skills" / "s").mkdir(parents=True)
    (cfg / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
    (cfg / "global_workflows").mkdir(parents=True)
    (cfg / "global_workflows" / "c.md").write_text("c", encoding="utf-8")
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
