"""Skill seeding survives targets deeper than Windows MAX_PATH (AR-11, v4.13.11).

Antigravity's project seeding flattens ``catalog/skills/<cat>/<name>/`` into
``<project>/.agents/skills/<name>/``. A bundled ``references/examples/...`` file in
a deep repository passes 260 characters, and plain ``shutil.copytree`` then fails
with WinError 3 unless the host enabled the LongPathsEnabled policy. The copy
helpers now use extended-length paths on Windows, so these tests seed into a
target whose file paths exceed 260 characters without any host policy.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from scripts.lib.integrations._catalog_adapters import flatten_skills
from scripts.lib.integrations.base import InstallContext, IntegrationBase, long_path

pytestmark = pytest.mark.skipif(
    sys.platform != "win32", reason="MAX_PATH is a Windows-only limit"
)

SEGMENT = "deep-repository-segment-" + "x" * 24  # 48 characters


def _deep(root: Path) -> Path:
    """Return a directory under ``root`` whose path alone is over 260 chars."""
    path = root
    while len(str(path)) < 280:
        path = path / SEGMENT
    return path


def _skill_source(root: Path) -> Path:
    """A one-skill catalog with a nested bundled file, like the real ones."""
    skill = root / "src" / "skills" / "workflow" / "deep-skill"
    nested = skill / "references" / "examples"
    nested.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: deep-skill\n---\n", encoding="utf-8")
    (nested / "example-with-a-long-file-name.md").write_text("body", encoding="utf-8")
    return root / "src" / "skills"


def _exists(path: Path) -> bool:
    return os.path.isfile(long_path(path))


def test_flatten_skills_seeds_past_max_path(install_ctx: InstallContext):
    src = _skill_source(install_ctx.target_root)
    dst = _deep(install_ctx.target_root) / ".agents" / "skills"
    target = dst / "deep-skill" / "references" / "examples" / "example-with-a-long-file-name.md"
    assert len(str(target)) > 260

    actions = flatten_skills(install_ctx, "antigravity", src, dst)

    assert [a.action for a in actions] == ["created"]
    assert _exists(target), "nested skill file did not land past MAX_PATH"
    assert _exists(dst / "deep-skill" / "SKILL.md")
    # The manifest keeps the plain path, so teardown and reports stay readable.
    tracked = install_ctx.manifest.files_for("antigravity")
    assert str(dst / "deep-skill") in tracked


def test_reseeding_a_deep_tree_is_unchanged(install_ctx: InstallContext):
    src = _skill_source(install_ctx.target_root)
    dst = _deep(install_ctx.target_root) / ".agents" / "skills"
    flatten_skills(install_ctx, "antigravity", src, dst)

    again = flatten_skills(install_ctx, "antigravity", src, dst)

    assert [a.action for a in again] == ["unchanged"]


def test_copy_file_writes_past_max_path(install_ctx: InstallContext):
    src = install_ctx.target_root / "hook.sh"
    src.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    dst = _deep(install_ctx.target_root) / "hooks" / "hook.sh"

    action = IntegrationBase._copy_file(src, dst, install_ctx, "antigravity")

    assert action.action == "created"
    assert _exists(dst)


def test_long_path_leaves_short_and_relative_paths_usable(tmp_path: Path):
    assert str(long_path(tmp_path)).startswith("\\\\?\\")
    assert long_path(long_path(tmp_path)) == long_path(tmp_path)
    unc = Path("\\\\server\\share\\dir")
    assert str(long_path(unc)).startswith("\\\\?\\UNC\\server\\share")
