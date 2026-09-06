"""Tests for the catalog-to-platform adapters (v3.12.0 Phase 1).

Covers the three shared helpers in
`scripts/lib/integrations/_catalog_adapters.py`:

  - flatten_skills:    catalog/skills/<category>/<name>/ -> <dst>/<name>/ (one level)
  - commands_to_skills: catalog/commands/<name>.md      -> <dst>/<name>/SKILL.md
  - commands_to_slash:  catalog/commands/<name>.md       -> <dst>/<name>.md (flat)

The tests build a tiny fixture catalog under the pytest tmp dir; the real
catalog and HOME are never touched.
"""

from __future__ import annotations

from pathlib import Path

from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest
from scripts.lib.integrations._catalog_adapters import (
    catalog_skill_names,
    commands_to_skills,
    commands_to_slash,
    flatten_skills,
)


def _ctx(tmp_path: Path, *, dry_run: bool = False, overwrite: bool = False) -> InstallContext:
    return InstallContext(
        repo_root=tmp_path,
        target_root=tmp_path,
        scope="workspace",
        overwrite=overwrite,
        dry_run=dry_run,
        manifest=InstallManifest(),
    )


def _make_catalog(root: Path) -> tuple[Path, Path]:
    """Create a minimal fixture catalog: 2 skills across 2 categories, 2 commands."""
    skills = root / "catalog" / "skills"
    (skills / "cat-a" / "skill-one").mkdir(parents=True)
    (skills / "cat-a" / "skill-one" / "SKILL.md").write_text("# skill one\n", encoding="utf-8")
    (skills / "cat-a" / "skill-one" / "references").mkdir()
    (skills / "cat-a" / "skill-one" / "references" / "ref.md").write_text("ref\n", encoding="utf-8")
    (skills / "cat-b" / "skill-two").mkdir(parents=True)
    (skills / "cat-b" / "skill-two" / "SKILL.md").write_text("# skill two\n", encoding="utf-8")

    commands = root / "catalog" / "commands"
    commands.mkdir(parents=True)
    (commands / "demo.md").write_text(
        '---\ndescription: Do the thing. SKIP - nothing here.\n---\n\n# /demo Command\n\nBody line.\n',
        encoding="utf-8",
    )
    # A command whose name collides with a real catalog skill folder.
    (commands / "skill-one.md").write_text(
        "---\ndescription: Colliding command.\n---\n\nCollide body.\n",
        encoding="utf-8",
    )
    return skills, commands


# ----- flatten_skills --------------------------------------------------------


def test_flatten_skills_drops_category_level(tmp_path: Path):
    skills, _ = _make_catalog(tmp_path)
    dst = tmp_path / "out" / "skills"
    ctx = _ctx(tmp_path)

    actions = flatten_skills(ctx, "codex", skills, dst)

    assert (dst / "skill-one" / "SKILL.md").exists()
    assert (dst / "skill-two" / "SKILL.md").exists()
    # Bundled subdirs are preserved.
    assert (dst / "skill-one" / "references" / "ref.md").exists()
    # The category layer must be gone.
    assert not (dst / "cat-a").exists()
    assert not (dst / "cat-b").exists()
    assert len(actions) == 2


def test_flatten_skills_missing_source_returns_not_found(tmp_path: Path):
    ctx = _ctx(tmp_path)
    actions = flatten_skills(ctx, "codex", tmp_path / "nope", tmp_path / "out")
    assert len(actions) == 1
    assert actions[0].action == "not-found"


def test_flatten_skills_dry_run_writes_nothing(tmp_path: Path):
    skills, _ = _make_catalog(tmp_path)
    dst = tmp_path / "out" / "skills"
    ctx = _ctx(tmp_path, dry_run=True)

    actions = flatten_skills(ctx, "codex", skills, dst)

    assert actions, "dry-run should still report FileActions"
    assert not (dst / "skill-one").exists(), "dry-run must not write to disk"


# ----- commands_to_skills ----------------------------------------------------


def test_commands_to_skills_synthesizes_skill_md(tmp_path: Path):
    _, commands = _make_catalog(tmp_path)
    dst = tmp_path / "out" / "skills"
    ctx = _ctx(tmp_path)

    commands_to_skills(ctx, "codex", commands, dst, existing_skill_names={"skill-one", "skill-two"})

    demo = dst / "demo" / "SKILL.md"
    assert demo.exists()
    text = demo.read_text(encoding="utf-8")
    assert "name: demo" in text
    assert "/demo" in text, "description should carry the slash-command lead-in"
    assert "Do the thing" in text, "description should carry the source command description"
    assert "disable-model-invocation: true" in text, (
        "command-skills must be user-invoked; the installer emits the flag"
    )
    assert "Body line." in text, "command body should become the skill body"


def test_commands_to_skills_skips_name_collision(tmp_path: Path):
    _, commands = _make_catalog(tmp_path)
    dst = tmp_path / "out" / "skills"
    ctx = _ctx(tmp_path)

    actions = commands_to_skills(
        ctx, "codex", commands, dst, existing_skill_names={"skill-one"}
    )

    # 'demo' is written; 'skill-one' collides with a real skill and is skipped.
    assert (dst / "demo" / "SKILL.md").exists()
    assert not (dst / "skill-one").exists(), "a command must not shadow a real catalog skill"
    assert len(actions) == 1


def test_commands_to_skills_description_yaml_is_quoted(tmp_path: Path):
    _, commands = _make_catalog(tmp_path)
    dst = tmp_path / "out" / "skills"
    ctx = _ctx(tmp_path)

    commands_to_skills(ctx, "codex", commands, dst)

    text = (dst / "demo" / "SKILL.md").read_text(encoding="utf-8")
    # The description value is emitted as a quoted YAML scalar on one line.
    assert 'description: "' in text


# ----- commands_to_slash -----------------------------------------------------


def test_commands_to_slash_verbatim_is_byte_identical(tmp_path: Path):
    _, commands = _make_catalog(tmp_path)
    dst = tmp_path / "out" / "workflows"
    ctx = _ctx(tmp_path)

    commands_to_slash(ctx, "antigravity2", commands, dst, style="verbatim")

    assert (dst / "demo.md").read_bytes() == (commands / "demo.md").read_bytes()


def test_commands_to_slash_codex_prompts_is_top_level(tmp_path: Path):
    _, commands = _make_catalog(tmp_path)
    dst = tmp_path / "out" / "prompts"
    ctx = _ctx(tmp_path)

    commands_to_slash(ctx, "codex", commands, dst, style="codex_prompts")

    assert (dst / "demo.md").exists()
    # Top-level only -- no nesting introduced.
    assert not (dst / "demo").is_dir()


def test_commands_to_slash_rejects_unknown_style(tmp_path: Path):
    _, commands = _make_catalog(tmp_path)
    ctx = _ctx(tmp_path)
    try:
        commands_to_slash(ctx, "codex", commands, tmp_path / "out", style="bogus")
    except ValueError as exc:
        assert "bogus" in str(exc)
    else:  # pragma: no cover - the call must raise
        raise AssertionError("expected ValueError for an unknown slash style")


def test_commands_to_slash_idempotent(tmp_path: Path):
    _, commands = _make_catalog(tmp_path)
    dst = tmp_path / "out" / "workflows"
    ctx = _ctx(tmp_path)

    commands_to_slash(ctx, "antigravity2", commands, dst)
    second = commands_to_slash(ctx, "antigravity2", commands, dst)

    assert {a.action for a in second} == {"unchanged"}, (
        f"second run should be all-unchanged; got {[a.action for a in second]}"
    )


# ---------------------------------------------------------------------------
# A skill directory is DEFINED by its SKILL.md (v3.15.9 Phase 7)
#
# An in-progress or abandoned scaffold (a `<category>/<name>/` folder with no
# SKILL.md) must never be published. Every platform discovers skills by reading
# `<skills>/<name>/SKILL.md` one level deep, so copying the bare directory
# delivers a skill nothing can load and breaks the depth-1 platform contract.
# Git cannot track an empty directory, so these appear only in a working tree --
# which is exactly why they need a test rather than reviewer vigilance.
# ---------------------------------------------------------------------------


def test_flatten_skills_skips_directory_without_skill_md(tmp_path: Path):
    skills, _ = _make_catalog(tmp_path)
    # An abandoned scaffold, and one that got as far as a bundled subdir.
    (skills / "cat-a" / "scaffold-empty").mkdir(parents=True)
    (skills / "cat-b" / "scaffold-partial" / "scripts").mkdir(parents=True)
    dst = tmp_path / "out" / "skills"
    ctx = _ctx(tmp_path)

    flatten_skills(ctx, "hermes", skills, dst)

    assert not (dst / "scaffold-empty").exists(), (
        "scaffold with no SKILL.md was published"
    )
    assert not (dst / "scaffold-partial").exists(), "partial scaffold was published"
    # The real skills still arrive, so the guard is a filter and not a blanket stop.
    assert (dst / "skill-one" / "SKILL.md").is_file()
    assert (dst / "skill-two" / "SKILL.md").is_file()
    # Every delivered directory satisfies the depth-1 contract the platforms assert.
    for child in (p for p in dst.iterdir() if p.is_dir()):
        assert (child / "SKILL.md").is_file(), (
            f"{child.name} has no SKILL.md at depth 1"
        )


def test_catalog_skill_names_ignores_directory_without_skill_md(tmp_path: Path):
    skills, _ = _make_catalog(tmp_path)
    (skills / "cat-a" / "scaffold-empty").mkdir(parents=True)

    names = catalog_skill_names(skills)

    assert names == {"skill-one", "skill-two"}
    # A nameless scaffold must not reserve a name, or it would suppress a
    # legitimate command wrapper that happens to share it.
    assert "scaffold-empty" not in names
