"""Unit coverage for runner.py `verify` per-platform read-path checks (v3.11.0 Phase 7.4).

Loads the hyphen-free runner.py by path and exercises the pure `_verify_checks`
helper against fixture HOME / project directories, asserting PASS vs NEEDS-ACTION -
including the Antigravity 2.0 project-only `.agents/` surface (the reported bug).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

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
    (home / ".gemini" / "GEMINI.md").write_text("# Nexus-Hub Skill Index\n", encoding="utf-8")
    cli = home / ".gemini" / "antigravity-cli"
    (cli / "skills" / "s").mkdir(parents=True)
    (cli / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
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

    # Seed the project's .agents/workflows -> PASS.
    (proj / ".agents" / "workflows").mkdir(parents=True)
    (proj / ".agents" / "workflows" / "c.md").write_text("c", encoding="utf-8")
    labels2 = _by_label(runner._verify_checks(home, proj))
    assert _all_ok(labels2["Antigravity 2.0 (this project .agents/)"])


def test_codex_pass_and_needs_action(tmp_path):
    """Codex verify checks flattened skills (~/.codex/skills + ~/.agents/skills),
    legacy prompts, the AGENTS.md SKILL_INDEX, and (v3.15.8) the native agent,
    hook-registration, and hook-feature-switch surfaces.
    """
    home = tmp_path / "home"
    d = home / ".codex"
    (d / "skills" / "presentify").mkdir(parents=True)
    (d / "skills" / "presentify" / "SKILL.md").write_text("s", encoding="utf-8")
    (d / "prompts").mkdir(parents=True)
    (d / "prompts" / "presentify.md").write_text("p", encoding="utf-8")
    (d / "AGENTS.md").write_text("# Nexus-Hub Skill Index\n", encoding="utf-8")
    (d / "agents").mkdir(parents=True)
    (d / "agents" / "planner.toml").write_text('name = "planner"\n', encoding="utf-8")
    (d / "hooks.json").write_text(
        '{"hooks": {"Stop": [{"hooks": [{"statusMessage": "Nexus-Hub x"}]}]}}',
        encoding="utf-8",
    )
    (d / "config.toml").write_text("[features]\nhooks = true\n", encoding="utf-8")
    (home / ".agents" / "skills" / "presentify").mkdir(parents=True)
    (home / ".agents" / "skills" / "presentify" / "SKILL.md").write_text("s", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Codex / ChatGPT"]
    assert _all_ok(check)
    assert {name for name, _ in check[1]} >= {
        "custom agents",
        "hooks registration",
        "hooks feature switch",
    }

    # Remove the ~/.agents/skills mirror -> NEEDS-ACTION.
    import shutil
    shutil.rmtree(home / ".agents")
    check2 = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Codex / ChatGPT"]
    assert not _all_ok(check2)


def test_codex_hook_surfaces_flag_when_absent(tmp_path):
    """A Codex install missing the v3.15.8 hook surfaces reports NEEDS-ACTION.

    The feature switch matters as much as the registration: Codex ships the hook
    engine disabled, so a hooks.json without ``[features] hooks = true`` is a
    guardrail the user does not actually have.
    """
    home = tmp_path / "home"
    d = home / ".codex"
    (d / "skills" / "presentify").mkdir(parents=True)
    (d / "skills" / "presentify" / "SKILL.md").write_text("s", encoding="utf-8")
    (d / "prompts").mkdir(parents=True)
    (d / "prompts" / "presentify.md").write_text("p", encoding="utf-8")
    (d / "AGENTS.md").write_text("# Nexus-Hub Skill Index\n", encoding="utf-8")
    (d / "agents").mkdir(parents=True)
    (d / "agents" / "planner.toml").write_text('name = "planner"\n', encoding="utf-8")
    (d / "hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
    (d / "config.toml").write_text("[features]\nhooks = false\n", encoding="utf-8")
    (home / ".agents" / "skills" / "presentify").mkdir(parents=True)
    (home / ".agents" / "skills" / "presentify" / "SKILL.md").write_text("s", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Codex / ChatGPT"]
    assert not _all_ok(check)
    failing = {name for name, ok in check[1] if not ok}
    assert failing == {"hooks registration", "hooks feature switch"}


def test_cursor_verify_pass_and_needs_action(tmp_path):
    """v3.15.0 Phase 6: Cursor verify covers skills / commands / agents / hooks.json."""
    home = tmp_path / "home"
    c = home / ".cursor"
    (c / "skills" / "s").mkdir(parents=True)
    (c / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
    (c / "commands").mkdir(parents=True)
    (c / "commands" / "x.md").write_text("x", encoding="utf-8")
    (c / "agents").mkdir(parents=True)
    (c / "agents" / "a.md").write_text("a", encoding="utf-8")
    (c / "hooks.json").write_text("{}", encoding="utf-8")

    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Cursor"]
    assert _all_ok(check)
    assert {name for name, _ in check[1]} >= {"skills", "commands", "agents", "hooks.json"}

    # Remove the hooks.json file -> NEEDS-ACTION.
    (c / "hooks.json").unlink()
    check2 = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Cursor"]
    assert not _all_ok(check2)


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
