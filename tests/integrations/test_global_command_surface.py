"""Tests for the user-global slash-command surfaces (v3.3.4).

Cursor and GitHub Copilot (VS Code) were confirmed empirically to surface a
*user-global* command directory in any repo with no local install:

  - Cursor:  ~/.cursor/commands/<name>.md            -> /<name>
  - Copilot: <vscode-user>/prompts/<name>.prompt.md  -> /<name>

These tests lock in: (1) the shared mirror+prune helper writes one file per
catalog command, is idempotent, prunes stale Nexus-Hub commands, and never
touches a user's own files; (2) cursor/copilot install_global wire it to the
right directory; (3) Antigravity (no global surface) seeds .agents/ via
wire_project_surfaces for `nexus-hub init`.
"""

from __future__ import annotations

from pathlib import Path

from scripts.lib.integrations import get
from scripts.lib.integrations._command_surface import mirror_command_surface
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _ctx(target: Path) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="global",
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
    )


def _catalog_command_stems() -> set[str]:
    return {p.stem for p in (REPO_ROOT / "catalog" / "commands").glob("*.md")}


# --- shared helper --------------------------------------------------------

def test_mirror_creates_one_file_per_command(tmp_path: Path):
    ctx = _ctx(tmp_path)
    dst = tmp_path / "commands"
    actions = mirror_command_surface(ctx, "testkey", dst, suffix=".md")
    stems = _catalog_command_stems()
    assert len(stems) >= 10, "expected the consolidated command set in catalog/commands"
    for stem in stems:
        assert (dst / f"{stem}.md").is_file(), f"missing mirrored command {stem}.md"
    assert any(a.action == "created" for a in actions)


def test_mirror_is_idempotent(tmp_path: Path):
    ctx = _ctx(tmp_path)
    dst = tmp_path / "commands"
    mirror_command_surface(ctx, "testkey", dst, suffix=".md")
    actions = mirror_command_surface(ctx, "testkey", dst, suffix=".md")
    assert actions, "second run should still report per-command actions"
    assert all(a.action in ("unchanged", "removed") for a in actions), (
        f"second run should be a no-op (unchanged); got {[a.action for a in actions]}"
    )


def test_mirror_supports_prompt_suffix(tmp_path: Path):
    ctx = _ctx(tmp_path)
    dst = tmp_path / "prompts"
    mirror_command_surface(ctx, "testkey", dst, suffix=".prompt.md")
    stems = _catalog_command_stems()
    for stem in stems:
        assert (dst / f"{stem}.prompt.md").is_file(), f"missing {stem}.prompt.md"


def test_mirror_prunes_stale_managed_commands(tmp_path: Path):
    ctx = _ctx(tmp_path)
    dst = tmp_path / "commands"
    dst.mkdir()
    # Simulate a previous install that left a now-deprecated command behind,
    # tracked in the manifest under this integration key.
    stale = dst / "analyze-codebase.md"
    stale.write_text("# deprecated command\n", encoding="utf-8")
    ctx.manifest.track("testkey", str(stale))

    mirror_command_surface(ctx, "testkey", dst, suffix=".md")
    assert not stale.exists(), "stale Nexus-Hub command should be pruned on reinstall"


def test_mirror_never_removes_user_files(tmp_path: Path):
    ctx = _ctx(tmp_path)
    dst = tmp_path / "commands"
    dst.mkdir()
    # A user's own command in the same dir, NOT tracked by Nexus-Hub.
    user_cmd = dst / "my-personal-command.md"
    user_cmd.write_text("# mine\n", encoding="utf-8")

    mirror_command_surface(ctx, "testkey", dst, suffix=".md")
    assert user_cmd.exists(), "a user's own command must never be pruned"


# --- integration wiring ---------------------------------------------------

def test_cursor_install_global_populates_cursor_commands(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    integ = get("cursor")
    result = integ.install_global(_ctx(tmp_path / "ws"))
    commands_dir = fake_home / ".cursor" / "commands"
    assert commands_dir.is_dir(), "cursor global install must create ~/.cursor/commands/"
    assert any(commands_dir.glob("*.md")), "cursor global install must write command .md files"
    assert any(fa.action in ("created", "unchanged") for fa in result.files)


def test_copilot_install_global_populates_vscode_prompts(tmp_path, monkeypatch):
    vscode_user = tmp_path / "Code" / "User"
    vscode_user.mkdir(parents=True)
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._vscode_user_dir", lambda: vscode_user
    )
    # Redirect the agents surface too (v3.15.8 Phase 8), so a global install in a
    # test never reaches the developer's real ~/.copilot.
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._copilot_home", lambda: tmp_path / ".copilot"
    )
    integ = get("copilot")
    integ.install_global(_ctx(tmp_path / "ws"))
    prompts_dir = vscode_user / "prompts"
    assert prompts_dir.is_dir(), "copilot global install must create the prompts/ dir"
    assert any(prompts_dir.glob("*.prompt.md")), "copilot must write *.prompt.md files"
    assert any((tmp_path / ".copilot" / "agents").glob("*.agent.md")), (
        "copilot global install must also write custom agents"
    )


def test_copilot_install_global_skips_when_copilot_is_absent(tmp_path, monkeypatch):
    """Both global surfaces must be absent for the install to skip.

    v3.15.8 Phase 8 added a second global surface (`~/.copilot/agents`) with its
    own detection signal, so patching only `_vscode_user_dir` no longer makes
    this a no-op -- and on a host that really has `~/.copilot`, leaving it
    unpatched would write into the developer's home directory. Redirect both
    accessors.
    """
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._vscode_user_dir", lambda: None
    )
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._copilot_home",
        lambda: tmp_path / "no-such-copilot",
    )
    integ = get("copilot")
    result = integ.install_global(_ctx(tmp_path / "ws"))
    assert not any(fa.action in ("created", "updated") for fa in result.files)
    assert result.notes, "should note that Copilot was not detected"


def test_antigravity20_wire_project_surfaces_seeds_workflows(tmp_path):
    ws = tmp_path / "repo"
    ws.mkdir()
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=ws,
        scope="workspace",
        manifest=InstallManifest(),
    )
    integ = get("antigravity2")
    result = integ.wire_project_surfaces(ctx)
    assert result is not None
    workflows = ws / ".agents" / "workflows"
    assert workflows.is_dir(), "nexus-hub init must seed .agents/workflows/ for Antigravity"
    assert any(workflows.glob("*.md")), ".agents/workflows/ must contain command files"
