"""Skill seeding survives targets deeper than Windows MAX_PATH (AR-11, v4.13.11).

Antigravity's project seeding flattens ``catalog/skills/<cat>/<name>/`` into
``<project>/.agents/skills/<name>/``. A bundled ``references/examples/...`` file in
a deep repository passes 260 characters, and plain ``shutil.copytree`` then fails
with WinError 3 unless the host enabled the LongPathsEnabled policy. The copy
helpers now use extended-length paths on Windows, so these tests seed into a
target whose file paths exceed 260 characters without any host policy.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.lib.integrations import get as get_integration
from scripts.lib.integrations._catalog_adapters import commands_to_skills, flatten_skills
from scripts.lib.integrations._hooks_json_merge import prune_flat_hooks, prune_named_set
from scripts.lib.integrations._owned import write_owned_file
from scripts.lib.integrations.base import InstallContext, IntegrationBase, long_path
from scripts.lib.integrations.runner import main as runner_main

REPO_ROOT = Path(__file__).resolve().parents[2]

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


def test_commands_to_skills_seeds_past_max_path(install_ctx: InstallContext):
    # The same Antigravity seeding call writes command wrappers right after the
    # skill trees; `nexus-hub init` in a deep project crashed here (WinError 206).
    commands = install_ctx.target_root / "src" / "commands"
    commands.mkdir(parents=True)
    (commands / "deep-command.md").write_text("Run the deep command.\n", encoding="utf-8")
    dst = _deep(install_ctx.target_root) / ".agents" / "skills"
    target = dst / "deep-command" / "SKILL.md"
    assert len(str(target)) > 260

    actions = commands_to_skills(install_ctx, "antigravity", commands, dst)

    assert [a.action for a in actions] == ["created"]
    assert _exists(target), "command wrapper did not land past MAX_PATH"
    again = commands_to_skills(install_ctx, "antigravity", commands, dst)
    assert [a.action for a in again] == ["unchanged"]
    assert str(target) in install_ctx.manifest.files_for("antigravity")


def test_long_path_leaves_short_and_relative_paths_usable(tmp_path: Path):
    assert str(long_path(tmp_path)).startswith("\\\\?\\")
    assert long_path(long_path(tmp_path)) == long_path(tmp_path)
    unc = Path("\\\\server\\share\\dir")
    assert str(long_path(unc)).startswith("\\\\?\\UNC\\server\\share")


# ----- `nexus-hub init` and global installs in deep roots (cycle 3) ----------


def _root_of_length(base: Path, length: int) -> Path:
    """Create and return a directory under ``base`` whose path is ``length`` chars."""
    path = base
    while len(str(path)) < length - len(SEGMENT) - 1:
        path = path / SEGMENT
    remainder = length - len(str(path)) - 1
    assert remainder > 0
    path = path / ("z" * remainder)
    assert len(str(path)) == length
    os.makedirs(long_path(path), exist_ok=True)
    return path


def _isolate_home(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    """Point every home variable at ``home`` and hide the real editor CLIs."""
    home.mkdir(parents=True, exist_ok=True)
    for name in ("HOME", "USERPROFILE", "NEXUS_HUB_HOME"):
        monkeypatch.setenv(name, str(home))
    monkeypatch.setenv("APPDATA", str(home / "AppData" / "Roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(home / "AppData" / "Local"))
    kept = [
        entry
        for entry in os.environ.get("PATH", "").split(os.pathsep)
        if "vs code" not in entry.lower() and "cursor" not in entry.lower()
    ]
    monkeypatch.setenv("PATH", os.pathsep.join(kept))


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    _isolate_home(monkeypatch, tmp_path / "isolated-home")


@pytest.mark.parametrize("length", [219, 268])
def test_init_completes_in_a_deep_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, length: int
):
    # 219: the Cursor command mirror's atomic temp name crossed MAX_PATH. 268: the
    # root itself is past MAX_PATH, so every project write needs the long form.
    _isolate_home(monkeypatch, tmp_path / "home")
    root = _root_of_length(tmp_path, length)

    exit_code = runner_main(["init", "--target", str(root), "--quiet"])

    assert exit_code == 0, capsys.readouterr().err
    for relative in (
        ".cursor/rules/nexus-hub.mdc",
        ".cursor/commands/commands.md",
        ".claude/settings.json",
        ".agents/hooks.json",
    ):
        assert _exists(root / relative), f"{relative} missing under a {length}-char root"
    manifest_path = root / ".nexus-hub" / "install-manifest.json"
    manifest = json.loads(long_path(manifest_path).read_text(encoding="utf-8"))
    recorded = json.dumps(manifest)
    # Manifests keep the plain spelling so teardown and reports stay readable.
    assert "\\\\\\\\?\\\\" not in recorded
    assert json.dumps(str(root / ".cursor" / "commands" / "commands.md"))[1:-1] in recorded


def test_write_owned_file_survives_a_temp_name_past_max_path(install_ctx: InstallContext):
    # The final path fits under MAX_PATH, but the staging name adds 38 characters.
    directory = _root_of_length(install_ctx.target_root, 200)
    dst = directory / ("a" * (222 - len(str(directory)) - 4 - 1) + ".txt")
    assert len(str(dst)) == 222

    action = write_owned_file(install_ctx, "copilot", dst, b"agent body\n")

    assert action.action == "created"
    assert long_path(dst).read_bytes() == b"agent body\n"
    assert str(dst) in install_ctx.manifest.files_for("copilot")
    again = write_owned_file(install_ctx, "copilot", dst, b"agent body\n")
    assert again.action == "unchanged"


def test_global_copilot_install_with_a_deep_home(tmp_path: Path):
    # Cycle 2 B5: `~/.copilot/agents/<name>.agent.md` at 222+ characters failed
    # because the atomic temp name pushed it past 260.
    agents = sorted((REPO_ROOT / "catalog" / "agents").glob("*.md"))
    longest = max(len(f"{a.stem}.agent.md") for a in agents)
    home = _root_of_length(tmp_path, 240 - len("\\.copilot\\agents\\") - longest)
    os.makedirs(long_path(home / ".copilot"), exist_ok=True)
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "PATH")
    }
    env.update(
        HOME=str(home),
        USERPROFILE=str(home),
        APPDATA=str(home / "AppData" / "Roaming"),
        LOCALAPPDATA=str(home / "AppData" / "Local"),
        PATH=os.pathsep.join(
            entry
            for entry in os.environ.get("PATH", "").split(os.pathsep)
            if "vs code" not in entry.lower() and "cursor" not in entry.lower()
        ),
    )

    proc = subprocess.run(
        [sys.executable, "-m", "scripts.lib.integrations.runner", "install",
         "--scope", "global", "--integrations", "copilot", "--quiet"],
        cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=600,
    )

    assert proc.returncode == 0, proc.stderr
    written = [
        p for p in os.listdir(long_path(home / ".copilot" / "agents")) if p.endswith(".agent.md")
    ]
    assert len(written) == len(agents)
    assert not [p for p in os.listdir(long_path(home / ".copilot" / "agents")) if p.endswith(".tmp")]


def _hooks_document(shape: str, *, owned: bool, user: bool) -> dict:
    if shape == "named":
        return {
            **({"Nexus-Hub": {"enabled": True}} if owned else {}),
            **({"User": {"enabled": True, "command": "user-hook"}} if user else {}),
        }
    entries = ([{"command": "nexus-hook"}] if owned else []) + (
        [{"command": "user-hook"}] if user else []
    )
    return {"version": 1, "hooks": {"SessionStart": entries}}


def _prune_hooks(dst: Path, shape: str, *, dry_run: bool):
    if shape == "named":
        return prune_named_set(dst, "Nexus-Hub", dry_run)
    return prune_flat_hooks(dst, lambda entry: entry.get("command") == "nexus-hook", dry_run)


@pytest.mark.parametrize("shape", ["named", "flat"])
def test_deep_hook_prune_deletes_the_last_owned_registration(tmp_path: Path, shape: str):
    dst = _root_of_length(tmp_path, 268) / "hooks.json"
    original = json.dumps(_hooks_document(shape, owned=True, user=False)).encode()
    long_path(dst).write_bytes(original)

    preview = _prune_hooks(dst, shape, dry_run=True)

    assert (preview.action, preview.path) == ("removed", str(dst))
    assert long_path(dst).read_bytes() == original
    removed = _prune_hooks(dst, shape, dry_run=False)
    assert (removed.action, removed.path) == ("removed", str(dst))
    assert not _exists(dst)
    assert _prune_hooks(dst, shape, dry_run=False).action == "not-found"


@pytest.mark.parametrize("shape", ["named", "flat"])
@pytest.mark.parametrize("with_backup", [False, True])
def test_deep_hook_prune_preserves_user_entries_and_crlf(
    tmp_path: Path, shape: str, with_backup: bool
):
    dst = _root_of_length(tmp_path, 268) / "hooks.json"
    user = _hooks_document(shape, owned=False, user=True)
    expected = (json.dumps(user, indent=2) + "\n").replace("\n", "\r\n").encode()
    if with_backup:
        # Distinct formatting proves restoration uses the backup's exact bytes.
        expected = (json.dumps(user, indent=4) + "\n").replace("\n", "\r\n").encode()
        long_path(dst.with_suffix(".json.nexus-hub.bak")).write_bytes(expected)
    original = (json.dumps(_hooks_document(shape, owned=True, user=True), indent=2) + "\n").replace("\n", "\r\n").encode()
    long_path(dst).write_bytes(original)

    assert _prune_hooks(dst, shape, dry_run=True).action == "updated"
    assert long_path(dst).read_bytes() == original
    action = _prune_hooks(dst, shape, dry_run=False)
    assert (action.action, action.path) == ("updated", str(dst))
    assert long_path(dst).read_bytes() == expected
    assert json.loads(long_path(dst).read_bytes()) == user
    assert _prune_hooks(dst, shape, dry_run=False).action == "unchanged"


def test_deep_base_teardown_removes_owned_files_and_trees(install_ctx: InstallContext):
    root = _root_of_length(install_ctx.target_root, 268)
    source = install_ctx.target_root / "owned.txt"
    source.write_bytes(b"owned file\n")
    owned_file = root / "managed" / "owned.txt"
    IntegrationBase._copy_file(source, owned_file, install_ctx, "antigravity")
    skill_dst = root / "skills"
    flatten_skills(install_ctx, "antigravity", _skill_source(install_ctx.target_root), skill_dst)
    owned_tree = skill_dst / "deep-skill"
    nested = owned_tree / "references" / "examples" / "example-with-a-long-file-name.md"
    survivor = root / "user.txt"
    long_path(survivor).write_bytes(b"user file\n")
    assert _exists(owned_file) and _exists(nested)

    preview_ctx = replace(install_ctx, dry_run=True, manifest=deepcopy(install_ctx.manifest))
    preview = IntegrationBase.teardown(get_integration("antigravity"), preview_ctx)
    assert {a.path: a.action for a in preview.files} == {
        str(owned_file): "removed", str(owned_tree): "removed"
    }
    assert _exists(owned_file) and _exists(nested)
    result = IntegrationBase.teardown(get_integration("antigravity"), install_ctx)
    assert {a.path: a.action for a in result.files} == {
        str(owned_file): "removed", str(owned_tree): "removed"
    }
    assert not _exists(owned_file)
    assert not long_path(owned_tree).exists()
    assert long_path(survivor).read_bytes() == b"user file\n"
    assert install_ctx.manifest.files_for("antigravity") == []
    assert IntegrationBase.teardown(get_integration("antigravity"), install_ctx).files == []


def test_deep_base_teardown_unlinks_without_following_a_file_symlink(install_ctx: InstallContext):
    outside = install_ctx.target_root / "user-owned.txt"
    outside.write_bytes(b"keep user target\n")
    link = _root_of_length(install_ctx.target_root, 268) / "owned-link.txt"
    try:
        long_path(link).symlink_to(outside)
    except OSError as exc:
        if exc.winerror == 1314:
            pytest.skip("Windows symlink creation privilege is unavailable")
        raise
    install_ctx.manifest.track("antigravity", str(link))

    result = IntegrationBase.teardown(get_integration("antigravity"), install_ctx)

    assert [(a.path, a.action) for a in result.files] == [(str(link), "removed")]
    assert not long_path(link).is_symlink()
    assert outside.read_bytes() == b"keep user target\n"


def test_deep_base_teardown_removes_a_junction_without_touching_its_target(install_ctx: InstallContext):
    import _winapi

    outside = install_ctx.target_root / "user-directory"
    outside.mkdir()
    sentinel = outside / "user-owned.txt"
    sentinel.write_bytes(b"keep junction target\n")
    junction = _root_of_length(install_ctx.target_root, 268) / "owned-junction"
    _winapi.CreateJunction(str(outside), str(long_path(junction)))
    assert long_path(junction).is_junction()
    install_ctx.manifest.track("antigravity", str(junction))

    result = IntegrationBase.teardown(get_integration("antigravity"), install_ctx)

    assert [(a.path, a.action) for a in result.files] == [(str(junction), "removed")]
    assert not long_path(junction).exists()
    assert sentinel.read_bytes() == b"keep junction target\n"


def test_deep_file_has_a_native_max_path_negative_control(tmp_path: Path):
    import winreg

    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\FileSystem") as key:
        enabled, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
    if enabled:
        pytest.skip("Host policy already enables unprefixed long paths")
    dst = _root_of_length(tmp_path, 268) / "control.txt"
    long_path(dst).write_bytes(b"native file\n")

    assert _exists(dst)
    assert not dst.is_file(), "unprefixed path did not exercise native MAX_PATH"
