"""Copies of catalog items the catalog no longer ships are removed on upgrade (v4.15.5).

The /status removal showed that a refresh install removed a dropped command only
from folders synced wholesale; the command-skill, Codex prompt and workflow
copies survived. These tests pin the retirement rule: remove only unchanged
Nexus-Hub copies of items no longer in the catalog, keep everything else.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.lib.integrations._retired import (
    catalog_names,
    item_of,
    retire_removed_items,
)
from scripts.lib.integrations.result import FileAction, WriteResult

GONE = "retired-command-for-tests"


def _record(path: Path, action: str = "created") -> dict:
    return {
        "path": str(path),
        "action": action,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _write(path: Path, text: str = "body\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _retire(ctx, previous, current=None):
    return retire_removed_items(ctx, "gemini", previous, current or WriteResult())


def test_unchanged_copy_of_a_removed_command_is_removed_with_its_folder(install_ctx):
    skill = _write(install_ctx.target_root / ".gemini" / "skills" / GONE / "SKILL.md")
    install_ctx.manifest.track("gemini", str(skill))
    result = _retire(install_ctx, [_record(skill)])
    assert not skill.exists() and not skill.parent.exists()
    assert (install_ctx.target_root / ".gemini" / "skills").is_dir()
    assert [fa.action for fa in result.files] == ["removed", "removed"]
    assert str(skill) not in install_ctx.manifest.files_for("gemini")


@pytest.mark.parametrize(
    "relative",
    [
        ".codex/prompts/{}.md",
        ".agents/workflows/{}.md",
        ".windsurf/workflows/{}.md",
        ".qwen/commands/{}.toml",
    ],
)
def test_rendered_command_files_are_removed(install_ctx, relative):
    path = _write(install_ctx.target_root / relative.format(GONE))
    result = _retire(install_ctx, [_record(path)])
    assert not path.exists()
    assert result.files[0].action == "removed"


def test_an_edited_copy_is_kept_and_reported(install_ctx):
    path = _write(install_ctx.target_root / ".codex" / "prompts" / f"{GONE}.md")
    record = _record(path)
    path.write_text("my own notes\n", encoding="utf-8")
    result = _retire(install_ctx, [record])
    assert path.exists()
    assert (
        result.files[0].action == "kept"
        and "changed since install" in result.files[0].reason
    )


def test_an_item_still_in_the_catalog_is_never_touched(install_ctx):
    """A narrower selection or an opt-in surface turned off must not delete it."""
    path = _write(
        install_ctx.target_root / ".gemini" / "skills" / "progress" / "SKILL.md"
    )
    result = _retire(install_ctx, [_record(path)])
    assert path.exists() and result.files == []


def test_a_file_produced_this_run_is_never_touched(install_ctx):
    path = _write(install_ctx.target_root / ".codex" / "prompts" / f"{GONE}.md")
    current = WriteResult(files=[FileAction(path=str(path), action="unchanged")])
    assert _retire(install_ctx, [_record(path)], current).files == []
    assert path.exists()


def test_a_file_the_user_owned_is_never_touched(install_ctx):
    path = _write(install_ctx.target_root / ".codex" / "prompts" / f"{GONE}.md")
    assert _retire(install_ctx, [_record(path, action="kept")]).files == []
    assert path.exists()


def test_a_record_without_a_hash_is_kept(install_ctx):
    path = _write(install_ctx.target_root / ".codex" / "prompts" / f"{GONE}.md")
    record = dict(_record(path), sha256=None)
    assert _retire(install_ctx, [record]).files[0].action == "kept"
    assert path.exists()


def test_a_path_outside_the_install_target_is_kept(install_ctx, tmp_path_factory):
    outside = _write(
        tmp_path_factory.mktemp("elsewhere") / ".codex" / "prompts" / f"{GONE}.md"
    )
    result = _retire(install_ctx, [_record(outside)])
    assert outside.exists() and result.files[0].reason == "outside the install target"


@pytest.mark.parametrize("flag", ["dry_run", "instruction_only"])
def test_dry_run_and_instruction_only_installs_remove_nothing(install_ctx, flag):
    path = _write(install_ctx.target_root / ".codex" / "prompts" / f"{GONE}.md")
    setattr(install_ctx, flag, True)
    assert _retire(install_ctx, [_record(path)]).files == []
    assert path.exists()


@pytest.mark.parametrize(
    ("relative", "expected"),
    [
        (".gemini/skills/progress/SKILL.md", "progress"),
        ("skills/internal-comms/examples/status.md", "internal-comms"),
        (".codex/prompts/plan.md", "plan"),
        ("Code/User/prompts/plan.prompt.md", "plan"),
        (".qwen/commands/plan.toml", "plan"),
        (".cursor/rules/nexus-hub.mdc", None),
        (".codex/prompts/sub/plan.md", None),
        (".agents/skills/status/agents/openai.yaml", "status"),
        (".gemini/skills/skills/SKILL.md", "skills"),
    ],
)
def test_item_of_reads_the_catalog_item_name(tmp_path, relative, expected):
    found = item_of(tmp_path / relative, tmp_path)
    assert (found[0] if found else None) == expected


def test_a_skills_folder_above_the_target_does_not_mislead_item_of(tmp_path):
    root = tmp_path / "skills" / "project"
    found = item_of(root / ".codex" / "prompts" / "plan.md", root)
    assert found == ("plan", root / ".codex" / "prompts")


def test_nested_file_inside_a_retired_command_skill_is_removed(install_ctx):
    """Codex writes skills/<name>/agents/openai.yaml next to the SKILL.md."""
    folder = install_ctx.target_root / ".agents" / "skills" / GONE
    skill = _write(folder / "SKILL.md")
    policy = _write(folder / "agents" / "openai.yaml", "policy: x\n")
    _retire(install_ctx, [_record(skill), _record(policy)])
    assert not folder.exists()
    assert (install_ctx.target_root / ".agents" / "skills").is_dir()


def test_a_copy_already_removed_by_a_sharing_platform_is_untracked(install_ctx):
    """.agents/skills is shared by Codex and Antigravity; the second finds it gone."""
    skill = _write(install_ctx.target_root / ".agents" / "skills" / GONE / "SKILL.md")
    record = _record(skill)
    install_ctx.manifest.track("antigravity2", str(skill))
    retire_removed_items(install_ctx, "codex", [record], WriteResult())
    assert not skill.exists()
    result = retire_removed_items(install_ctx, "antigravity2", [record], WriteResult())
    assert result.files == []
    assert str(skill) not in install_ctx.manifest.files_for("antigravity2")


def test_example_files_inside_a_skill_do_not_keep_a_command_alive(install_ctx):
    """internal-comms ships examples/status.md; /status must still read as removed."""
    items, categories = catalog_names(install_ctx.repo_root)
    assert (
        "progress" in items and "internal-comms" in items and "workflow" in categories
    )
    assert "status" not in items


def test_a_sidecar_regenerated_inside_a_retired_folder_is_removed(install_ctx):
    """Codex rewrites agents/openai.yaml while the retired SKILL.md still exists."""
    folder = install_ctx.target_root / ".agents" / "skills" / GONE
    skill = _write(folder / "SKILL.md")
    sidecar = _write(folder / "agents" / "openai.yaml", "policy: x\n")
    previous = [_record(skill), _record(sidecar)]
    install_ctx.manifest.record_actions("codex", [FileAction(path=str(sidecar), action="unchanged")])
    current = WriteResult(files=[FileAction(path=str(sidecar), action="unchanged")])
    retire_removed_items(install_ctx, "codex", previous, current)
    assert not folder.exists()
    assert install_ctx.manifest.actions_for("codex") == []


def test_a_sidecar_for_a_users_own_skill_is_never_touched(install_ctx):
    """The user's SKILL.md is not a Nexus-Hub record, so its folder is not retired."""
    folder = install_ctx.target_root / ".agents" / "skills" / "my-own-skill"
    _write(folder / "SKILL.md", "---\nname: my-own-skill\n---\n")
    sidecar = _write(folder / "agents" / "openai.yaml", "policy: x\n")
    current = WriteResult(files=[FileAction(path=str(sidecar), action="unchanged")])
    assert retire_removed_items(install_ctx, "codex", [_record(sidecar)], current).files == []
    assert sidecar.exists()

