"""Tests for the Aider and Windsurf integration subclasses (v3.4.0 Phase 2).

These complement the parameterized contract suite (test_contract.py), which
already exercises the five lifecycle invariants for every registered key. Here
we assert the platform-specific behavior:

  - both keys are registered in `_register_builtins()`;
  - Aider remains a behavioral-only surface;
  - Aider writes a project-root CONVENTIONS.md at workspace scope and is a
    no-op-with-note at global scope;
  - Devin Desktop writes current AGENTS.md, `.devin/rules`, native skills,
    workflows, and Cascade hooks while retaining `.windsurfrules`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import get, list_keys  # noqa: E402
from scripts.lib.integrations._cascade_hook_compat import translate_payload  # noqa: E402
from scripts.lib.integrations.base import (  # noqa: E402
    InstallContext,
    MarkdownIntegration,
    SkillsIntegration,
)
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


def _ctx(target: Path, scope: str = "workspace") -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope=scope,
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "test-project"},
    )


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


# ---------------------------------------------------------------------------
# Registration + classification
# ---------------------------------------------------------------------------


def test_aider_and_windsurf_registered() -> None:
    keys = set(list_keys())
    assert {"aider", "windsurf"}.issubset(keys)


def test_aider_behavioral_guardrails_not_skills_mirror() -> None:
    integ = get("aider")
    assert isinstance(integ, MarkdownIntegration)
    assert not isinstance(integ, SkillsIntegration)
    for cfg_key in ("skills_subdir", "commands_subdir", "agents_subdir", "hooks_subdir"):
        assert cfg_key not in integ.config


def test_windsurf_declares_current_native_surfaces() -> None:
    integ = get("windsurf")
    assert isinstance(integ, MarkdownIntegration)
    assert integ.config["skills_subdir"] == "skills"
    assert integ.config["commands_subdir"] == "workflows"
    assert integ.config["hooks_subdir"] == "hooks"
    assert integ.config["hooks_supported"] is True


def test_windsurf_hook_bridge_maps_documented_conversation_identity() -> None:
    translated = translate_payload(
        {
            "trajectory_id": "conversation-123",
            "execution_id": "turn-456",
            "tool_info": {"command_line": "git status", "cwd": "/repo"},
        },
        "pre_run_command",
        "Bash",
    )

    assert translated["session_id"] == "conversation-123"
    assert "transcript_path" not in translated
    assert translated["tool_input"] == {"command": "git status", "cwd": "/repo"}


# ---------------------------------------------------------------------------
# Aider
# ---------------------------------------------------------------------------


def test_aider_workspace_writes_root_conventions(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    integ = get("aider")
    result = integ.install(_ctx(target, scope="workspace"))

    conventions = target / "CONVENTIONS.md"
    assert conventions.is_file(), "Aider must write a project-root CONVENTIONS.md"
    body = conventions.read_text(encoding="utf-8")
    # The SKILL_INDEX block is embedded (a known index row proves substitution ran).
    assert "catalog/skills/" in body
    assert "test-project" in body
    assert any(fa.path == str(conventions) for fa in result.files)


def test_aider_global_is_noop_with_note(fake_home: Path, tmp_path: Path) -> None:
    integ = get("aider")
    result = integ.install(_ctx(tmp_path, scope="global"))
    assert result.files == [], "Aider has no global instruction surface"
    assert result.notes, "Aider global install should explain the no-op via a note"


# ---------------------------------------------------------------------------
# Windsurf
# ---------------------------------------------------------------------------


def test_windsurf_workspace_writes_root_windsurfrules(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    integ = get("windsurf")
    integ.install(_ctx(target, scope="workspace"))

    rules = target / ".windsurfrules"
    assert rules.is_file(), "Windsurf must write a project-root .windsurfrules"
    body = rules.read_text(encoding="utf-8")
    assert "catalog/skills/" in body
    assert (target / "AGENTS.md").is_file()
    assert (target / ".devin" / "rules" / "nexus-hub.md").is_file()
    assert (target / ".windsurf" / "skills").is_dir()
    assert (target / ".windsurf" / "workflows").is_dir()

    hooks_file = target / ".windsurf" / "hooks.json"
    hooks = __import__("json").loads(hooks_file.read_text(encoding="utf-8"))["hooks"]
    assert {"pre_run_command", "pre_write_code", "post_write_code"}.issubset(hooks)
    entry = hooks["pre_run_command"][0]
    assert "command" in entry and "powershell" in entry
    assert ".windsurf/hooks/cascade-hook-compat.py" in entry["command"]
    assert (target / ".windsurf" / "hooks" / "cascade-hook-compat.py").is_file()


def test_windsurf_global_writes_when_detected(fake_home: Path) -> None:
    # Simulate Windsurf installed: the ~/.codeium config root exists.
    (fake_home / ".codeium").mkdir()
    integ = get("windsurf")
    result = integ.install(_ctx(fake_home, scope="global"))

    global_rules = fake_home / ".codeium" / "windsurf" / "memories" / "global_rules.md"
    assert global_rules.is_file(), "Windsurf global rules must be written when detected"
    assert any(fa.path == str(global_rules) for fa in result.files)
    windsurf = fake_home / ".codeium" / "windsurf"
    assert (windsurf / "skills").is_dir()
    assert (windsurf / "global_workflows").is_dir()
    assert (windsurf / "hooks.json").is_file()


def test_windsurf_global_skips_when_not_detected(fake_home: Path) -> None:
    # ~/.codeium absent -> Windsurf not installed -> skip with a note.
    integ = get("windsurf")
    result = integ.install(_ctx(fake_home, scope="global"))
    assert result.files == []
    assert result.notes, "Windsurf global install should skip-with-note when undetected"
    assert not (fake_home / ".codeium").exists()


def test_windsurf_preserves_user_hook_entries(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    hooks_file = target / ".windsurf" / "hooks.json"
    hooks_file.parent.mkdir(parents=True)
    user_commands = [
        'python ".windsurf/hooks/my-user-hook.py"',
        'python mine.py --policy ".windsurf/hooks/user-policy.json"',
    ]
    hooks_file.write_text(
        __import__("json").dumps(
            {
                "hooks": {
                    "pre_run_command": [
                        {"command": command} for command in user_commands
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    get("windsurf").install(_ctx(target, scope="workspace"))
    data = __import__("json").loads(hooks_file.read_text(encoding="utf-8"))
    commands = [entry["command"] for entry in data["hooks"]["pre_run_command"]]
    assert set(user_commands).issubset(commands)


def test_windsurf_teardown_preserves_user_hooks_in_native_directory(
    fake_home: Path, tmp_path: Path
) -> None:
    target = tmp_path / "ws"
    ctx = _ctx(target, scope="workspace")
    integration = get("windsurf")
    integration.install(ctx)
    hooks_file = target / ".windsurf" / "hooks.json"
    data = __import__("json").loads(hooks_file.read_text(encoding="utf-8"))
    user_command = 'python ".windsurf/hooks/my-user-hook.py"'
    data["hooks"]["pre_run_command"].append({"command": user_command})
    hooks_file.write_text(__import__("json").dumps(data), encoding="utf-8")

    integration.teardown(ctx)

    remaining = __import__("json").loads(hooks_file.read_text(encoding="utf-8"))
    entries = remaining["hooks"]["pre_run_command"]
    assert [entry["command"] for entry in entries] == [user_command]
    assert all("cascade-hook-compat.py" not in entry["command"] for entry in entries)
