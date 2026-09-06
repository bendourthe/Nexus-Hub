"""Tests for the Antigravity 1.0 and Antigravity 2.0 + CLI integrations.

Added in v2.2.0 Phase 2 (T008). Covers:
  - Both integrations are registered and resolve via get(key)
  - Antigravity 1.0 lays files under .gemini/antigravity/
  - Antigravity 2.0 + CLI lays files under .agents/ (covers both desktop and CLI;
    paths verified 2026-05-29 against Google's public Antigravity CLI docs --
    binary `agy`, `.agents/` per-project dir, `AGENTS.md` instruction file --
    per docs/archive/v2/v2.2/antigravity-cli-probe.md)
  - WriteResult records carry the expected FileAction entries
  - The display_name reflects dual desktop+CLI coverage on the 2.0 integration
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from scripts.lib.integrations import _cascade_hook_compat as hook_compat
from scripts.lib.integrations import get
from scripts.lib.integrations._hooks_common import is_windows_host
from scripts.lib.integrations.base import InstallContext


def test_antigravity_10_install_workspace_lays_files(install_ctx: InstallContext):
    integ = get("antigravity")
    result = integ.install(install_ctx)
    assert (install_ctx.target_root / ".gemini" / "antigravity" / "rules.md").exists()
    assert (install_ctx.target_root / ".gemini" / "antigravity" / "skills").exists()
    assert result.files, "WriteResult should record at least one FileAction"


def test_antigravity_20_install_workspace_lays_files(install_ctx: InstallContext):
    integ = get("antigravity2")
    result = integ.install(install_ctx)
    assert (install_ctx.target_root / "AGENTS.md").exists()
    assert not (install_ctx.target_root / ".agents" / "AGENTS.md").exists()
    assert (install_ctx.target_root / ".agents" / "skills").exists()
    assert (install_ctx.target_root / ".agents" / "workflows").exists()
    assert (install_ctx.target_root / ".agents" / "agents").exists()
    assert result.files, "WriteResult should record at least one FileAction"


def test_antigravity_20_display_name_signals_dual_coverage():
    """Per T008 / probe finding, the Antigravity 2.0 integration covers BOTH
    the desktop IDE and the CLI. The display_name carries that dual-coverage
    signal so the installer logs reflect what the user is actually getting.
    """
    integ = get("antigravity2")
    assert "CLI" in integ.display_name, (
        f"antigravity2 display_name should mention CLI to reflect dual coverage; "
        f"got {integ.display_name!r}"
    )


def test_antigravity_20_uses_dedicated_template():
    """After T011, antigravity2 points at base-antigravity-20.md (not the
    legacy base-gemini.md). This protects against regressions if a future
    refactor reroutes the integration back to a shared Gemini template.
    """
    integ = get("antigravity2")
    template = integ.config.get("instruction_template", "")
    assert template.endswith("base-antigravity-20.md"), (
        f"antigravity2 should use base-antigravity-20.md; got {template!r}"
    )


def test_antigravity_10_uses_dedicated_template():
    integ = get("antigravity")
    template = integ.config.get("instruction_template", "")
    assert template.endswith("base-antigravity-10.md"), (
        f"antigravity should use base-antigravity-10.md; got {template!r}"
    )


def test_antigravity_20_idempotent_install(install_ctx: InstallContext, tmp_path: Path):
    """Second install on the same target should mark all files unchanged."""
    integ = get("antigravity2")
    integ.install(install_ctx)
    result = integ.install(install_ctx)
    actions = {a.action for a in result.files}
    assert "unchanged" in actions, (
        f"second install should produce at least one 'unchanged' action; "
        f"got actions={actions}"
    )


def test_antigravity_20_skills_are_flattened(install_ctx: InstallContext):
    """Antigravity discovers skills one level under skills/, so the catalog's
    `<category>/<skill-name>/SKILL.md` layout MUST be flattened to
    `skills/<skill-name>/SKILL.md`. A verbatim copy (with the category layer)
    is the bug that made every skill invisible in the 2.0 IDE.
    """
    integ = get("antigravity2")
    integ.install(install_ctx)
    skills_dir = install_ctx.target_root / ".agents" / "skills"

    # The category layer must be gone: known category names must NOT appear as
    # folders under skills/.
    for category in ("ai-development", "workflow", "security", "orchestration"):
        assert not (skills_dir / category).is_dir(), (
            f"category folder {category!r} leaked into skills/ -- skills were not "
            f"flattened"
        )

    # Every immediate child of skills/ is a skill folder holding a SKILL.md.
    skill_dirs = [p for p in skills_dir.iterdir() if p.is_dir()]
    assert len(skill_dirs) >= 50, f"expected the full flat catalog; got {len(skill_dirs)}"
    for skill in skill_dirs[:15]:
        assert (skill / "SKILL.md").exists(), (
            f"{skill.name}/ must contain SKILL.md directly (flat layout)"
        )


def test_antigravity_20_installs_hooks_and_registration(install_ctx: InstallContext):
    """Hooks: the curated scripts land under hooks/ and a hooks.json in
    Antigravity's named-group schema registers them with the confirmed
    `run_command` matcher and a workspace-relative command path.
    """
    integ = get("antigravity2")
    integ.install(install_ctx)
    agents = install_ctx.target_root / ".agents"

    for script in ("secret-scan.sh", "large-file-guard.sh", "git-guardrails.sh"):
        assert (agents / "hooks" / script).exists(), f"hook script {script} not installed"
    assert (agents / "hooks" / "antigravity-hook-compat.py").is_file()
    assert not (agents / "hooks" / "compress-output.sh").exists()

    hooks_json = agents / "hooks.json"
    assert hooks_json.exists(), "hooks.json registration not written"
    data = json.loads(hooks_json.read_text(encoding="utf-8"))
    assert "nexus-hub-guardrails" in data
    assert "nexus-hub-context-compressor" not in data
    guardrails = data["nexus-hub-guardrails"]
    assert guardrails["enabled"] is True
    commands = [h["command"] for entry in guardrails["PreToolUse"] for h in entry["hooks"]]
    hook_suffix = ".ps1" if is_windows_host() else ".sh"
    assert any(f".agents/hooks/secret-scan{hook_suffix}" in c for c in commands), (
        f"workspace hooks.json should reference the project-relative hook path; got {commands}"
    )
    assert all("antigravity-hook-compat.py" in command for command in commands)
    matchers = {entry["matcher"] for entry in guardrails["PreToolUse"]}
    assert matchers == {
        "write_to_file|replace_file_content|multi_replace_file_content",
        "run_command",
    }
    assert "" not in matchers, "unrelated tools must not invoke file-content guards"


def test_antigravity_hook_bridge_translates_host_payload_to_guard_contract():
    translated = hook_compat.translate_antigravity_payload(
        {
            "toolCall": {
                "name": "run_command",
                "args": {
                    "CommandLine": "git reset --hard",
                    "Cwd": "/repo",
                },
            },
            "conversationId": "conversation-123",
            "transcriptPath": "/tmp/transcript.jsonl",
        },
        "PreToolUse",
    )

    assert translated["hook_event_name"] == "PreToolUse"
    assert translated["session_id"] == "conversation-123"
    assert translated["transcript_path"] == "/tmp/transcript.jsonl"
    assert translated["tool_name"] == "run_command"
    assert translated["tool_input"]["command"] == "git reset --hard"
    assert translated["tool_input"]["cwd"] == "/repo"


@pytest.mark.parametrize(
    ("tool_name", "tool_args", "expected_content", "expected_edit_count"),
    [
        (
            "write_to_file",
            {
                "TargetFile": "/repo/secrets.txt",
                "CodeContent": "token = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'",
            },
            "token = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'",
            0,
        ),
        (
            "replace_file_content",
            {
                "TargetFile": "/repo/secrets.txt",
                "ReplacementContent": "token = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'",
            },
            "token = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'",
            0,
        ),
        (
            "multi_replace_file_content",
            {
                "TargetFile": "/repo/secrets.txt",
                "ReplacementChunks": [
                    {
                        "StartLine": 1,
                        "EndLine": 1,
                        "ReplacementContent": "token = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'",
                    },
                    {
                        "StartLine": 3,
                        "EndLine": 3,
                        "ReplacementContent": "safe = true",
                    },
                ],
            },
            "token = 'ghp_abcdefghijklmnopqrstuvwxyz1234567890'\nsafe = true",
            2,
        ),
    ],
)
def test_antigravity_hook_bridge_exposes_native_file_content_to_guards(
    monkeypatch,
    capsys,
    tool_name,
    tool_args,
    expected_content,
    expected_edit_count,
):
    payload = {"toolCall": {"name": tool_name, "args": tool_args}}
    child = (
        "import json,sys; "
        "payload=json.load(sys.stdin); "
        f"assert payload['tool_input']['content']=={expected_content!r}; "
        f"assert len(payload['tool_input'].get('edits',[]))=={expected_edit_count}; "
        "sys.exit(2 if 'ghp_' in payload['tool_input']['content'] else 0)"
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    wrapper_exit = hook_compat.main(
        ["antigravity", "PreToolUse", "--", sys.executable, "-c", child]
    )
    captured = capsys.readouterr()

    assert wrapper_exit == 0
    assert json.loads(captured.out)["decision"] == "deny"


def test_antigravity_hook_bridge_emits_documented_deny_for_guard_exit_two():
    output, wrapper_exit = hook_compat.translate_child_result(
        "antigravity",
        "PreToolUse",
        stdout="",
        stderr="BLOCKED: destructive git command",
        returncode=2,
    )

    assert wrapper_exit == 0
    assert output == {
        "decision": "deny",
        "reason": "BLOCKED: destructive git command",
    }


def test_antigravity_hook_bridge_end_to_end_denies_native_command(
    monkeypatch, capsys
):
    payload = {
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "git reset --hard", "Cwd": "/repo"},
        }
    }
    child = (
        "import json,sys; "
        "payload=json.load(sys.stdin); "
        "assert payload['tool_input']['command']=='git reset --hard'; "
        "print('BLOCKED: destructive git command',file=sys.stderr); "
        "sys.exit(2)"
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))

    wrapper_exit = hook_compat.main(
        ["antigravity", "PreToolUse", "--", sys.executable, "-c", child]
    )
    captured = capsys.readouterr()

    assert wrapper_exit == 0
    assert json.loads(captured.out) == {
        "decision": "deny",
        "reason": "BLOCKED: destructive git command",
    }


def test_antigravity_hook_bridge_does_not_auto_approve_clean_guard_result():
    output, wrapper_exit = hook_compat.translate_child_result(
        "antigravity",
        "PreToolUse",
        stdout="",
        stderr="",
        returncode=0,
    )

    assert wrapper_exit == 0
    assert output["decision"] == "ask"


def test_antigravity_20_global_targets_corrected_ide_and_cli_paths(install_ctx: InstallContext):
    """Global install must reach the CORRECTED IDE read-paths (~/.gemini/config/
    skills + global_workflows, ~/.gemini/GEMINI.md rules) and the CLI root
    (~/.gemini/antigravity-cli). It must NOT write to the old ~/.gemini/antigravity/
    root, which the IDE does not read. Uses dry_run so real home is never touched.
    """
    from dataclasses import replace

    integ = get("antigravity2")
    global_ctx = replace(install_ctx, scope="global")
    result = integ.dry_run(global_ctx)
    joined = " ".join(fa.path.replace("\\", "/") for fa in result.files)

    assert "/.gemini/config/skills/" in joined, "IDE global skills must land in ~/.gemini/config/skills"
    assert "/.gemini/config/global_workflows/" in joined, (
        "IDE global slash commands must land in ~/.gemini/config/global_workflows"
    )
    assert "/.gemini/GEMINI.md" in joined, "IDE global rules must land in ~/.gemini/GEMINI.md"
    assert "/.gemini/antigravity-cli/skills/" in joined, "CLI skills must land in ~/.gemini/antigravity-cli"
    assert "/.gemini/antigravity-cli/AGENTS.md" not in joined
    assert "/.gemini/antigravity-cli/workflows/" not in joined
    assert "/.gemini/antigravity-cli/hooks" not in joined
    assert "/.gemini/config/agents" in joined
    # Regression guard: the old (unread) IDE root must be gone.
    assert "/.gemini/antigravity/" not in joined, (
        "global install must NOT write to the old ~/.gemini/antigravity/ root"
    )


def test_antigravity_20_commands_are_also_skills(install_ctx: InstallContext):
    """Every command surfaces BOTH as a slash workflow AND as a skill, so a user
    can invoke /presentify or the skill form. Workspace scope check.
    """
    integ = get("antigravity2")
    integ.install(install_ctx)
    agents = install_ctx.target_root / ".agents"
    assert (agents / "workflows" / "presentify.md").exists(), "slash workflow missing"
    skill_md = agents / "skills" / "presentify" / "SKILL.md"
    assert skill_md.exists(), "command-skill missing"
    text = skill_md.read_text(encoding="utf-8")
    assert "name: presentify" in text
    assert "disable-model-invocation: true" in text
