"""Tests for the per-integration legacy-state self-healing registry.

Covers the contract in scripts/lib/integrations/legacy.py:

* Filesystem cleanups remove the legacy artifact and return a
  FileAction(action="removed").
* They return None when the artifact is absent (the normal case on fresh
  installs).
* ctx.dry_run skips the disk write but still emits the FileAction.
* Path.home() is monkeypatched to tmp_path so the test never touches the
  real user home.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.integrations import legacy
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest
from scripts.lib.integrations.result import FileAction


def _make_ctx(repo_root: Path, target_root: Path, dry_run: bool = False) -> InstallContext:
    return InstallContext(
        repo_root=repo_root,
        target_root=target_root,
        scope="global",
        overwrite=False,
        dry_run=dry_run,
        manifest=InstallManifest(),
        template_vars={},
    )


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


@pytest.fixture
def disable_vscode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pretend the `code` CLI is not on PATH so the VS Code cleanup is a no-op.

    Tests that target the VS Code cleanup explicitly can override this by
    re-monkeypatching `shutil.which`.
    """
    monkeypatch.setattr(legacy.shutil, "which", lambda name: None)


# ---------------------------------------------------------------------------
# Filesystem cleanups
# ---------------------------------------------------------------------------


def test_devai_hub_global_dir_removed_when_new_install_present(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    """The legacy ~/.devai-hub/ is removed only when ~/.nexus-hub/ also exists."""
    legacy_dir = fake_home / ".devai-hub"
    legacy_dir.mkdir()
    (legacy_dir / "marker.txt").write_text("old")
    (fake_home / ".nexus-hub").mkdir()

    ctx = _make_ctx(tmp_path, tmp_path)
    actions = legacy.run_cleanups("claude", ctx)

    removed_paths = [a.path for a in actions if a.action == "removed"]
    assert str(legacy_dir) in removed_paths
    assert not legacy_dir.exists()


def test_devai_hub_global_dir_preserved_without_new_install(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    """Skip the cleanup if ~/.nexus-hub/ does not yet exist (the rename has
    not happened yet; destroying the legacy dir would lose user data).
    """
    legacy_dir = fake_home / ".devai-hub"
    legacy_dir.mkdir()
    (legacy_dir / "marker.txt").write_text("old")

    ctx = _make_ctx(tmp_path, tmp_path)
    actions = legacy.run_cleanups("claude", ctx)

    assert all(str(legacy_dir) != a.path for a in actions)
    assert legacy_dir.exists()
    assert (legacy_dir / "marker.txt").read_text() == "old"


def test_claude_skill_registry_removed(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    """The pre-2.0.0 ~/.claude/devai-hub-skills.json is purged."""
    claude_dir = fake_home / ".claude"
    claude_dir.mkdir()
    stale = claude_dir / "devai-hub-skills.json"
    stale.write_text("{}")

    ctx = _make_ctx(tmp_path, tmp_path)
    actions = legacy.run_cleanups("claude", ctx)

    paths = {a.path for a in actions if a.action == "removed"}
    assert str(stale) in paths
    assert not stale.exists()


def test_codex_skill_dir_removed(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    """The pre-2.0.0 ~/.codex/devai-hub-skills/ mirror dir is purged."""
    stale = fake_home / ".codex" / "devai-hub-skills"
    stale.mkdir(parents=True)
    (stale / "inside.json").write_text("x")

    ctx = _make_ctx(tmp_path, tmp_path)
    actions = legacy.run_cleanups("codex", ctx)

    paths = {a.path for a in actions if a.action == "removed"}
    assert str(stale) in paths
    assert not stale.exists()


def test_gemini_skill_dir_removed(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    """The pre-2.0.0 ~/.gemini/devai-hub-skills/ mirror dir is purged."""
    stale = fake_home / ".gemini" / "devai-hub-skills"
    stale.mkdir(parents=True)

    ctx = _make_ctx(tmp_path, tmp_path)
    actions = legacy.run_cleanups("gemini", ctx)

    paths = {a.path for a in actions if a.action == "removed"}
    assert str(stale) in paths
    assert not stale.exists()


# ---------------------------------------------------------------------------
# Dry-run behavior
# ---------------------------------------------------------------------------


def test_dry_run_does_not_touch_disk(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    legacy_dir = fake_home / ".devai-hub"
    legacy_dir.mkdir()
    (fake_home / ".nexus-hub").mkdir()

    ctx = _make_ctx(tmp_path, tmp_path, dry_run=True)
    actions = legacy.run_cleanups("claude", ctx)

    assert any(a.path == str(legacy_dir) for a in actions)
    assert legacy_dir.exists(), "dry_run must not delete the legacy dir"


# ---------------------------------------------------------------------------
# Idempotency: a second invocation returns no actions
# ---------------------------------------------------------------------------


def test_cleanup_is_idempotent(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    claude_dir = fake_home / ".claude"
    claude_dir.mkdir()
    stale = claude_dir / "devai-hub-skills.json"
    stale.write_text("{}")

    ctx = _make_ctx(tmp_path, tmp_path)
    first = legacy.run_cleanups("claude", ctx)
    second = legacy.run_cleanups("claude", ctx)

    assert any(a.path == str(stale) for a in first)
    assert all(a.path != str(stale) for a in second)


# ---------------------------------------------------------------------------
# Unknown integration keys: silently return []
# ---------------------------------------------------------------------------


def test_unknown_integration_returns_empty_list(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    ctx = _make_ctx(tmp_path, tmp_path)
    assert legacy.run_cleanups("not-a-real-key", ctx) == []


# ---------------------------------------------------------------------------
# VS Code extension cleanup
# ---------------------------------------------------------------------------


def test_vscode_cleanup_returns_none_when_code_not_on_path(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(legacy.shutil, "which", lambda name: None)
    ctx = _make_ctx(tmp_path, tmp_path)
    assert legacy._cleanup_claude_legacy_vscode_extension(ctx) is None


def test_vscode_cleanup_returns_none_when_extension_not_installed(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(legacy.shutil, "which", lambda name: "/usr/bin/code")

    class _FakeResult:
        returncode = 0
        stdout = "ms-python.python\nfoo.bar\n"

    monkeypatch.setattr(
        legacy.subprocess,
        "run",
        lambda *args, **kwargs: _FakeResult(),
    )
    ctx = _make_ctx(tmp_path, tmp_path)
    assert legacy._cleanup_claude_legacy_vscode_extension(ctx) is None


def test_vscode_cleanup_uninstalls_when_extension_installed(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(legacy.shutil, "which", lambda name: "/usr/bin/code")

    class _FakeListResult:
        returncode = 0
        stdout = "devai-hub.claude-usage-monitor\nfoo.bar\n"

    class _FakeUninstallResult:
        returncode = 0
        stdout = ""

    call_log = []

    def _fake_run(args, **kwargs):
        call_log.append(args)
        if args[1] == "--list-extensions":
            return _FakeListResult()
        return _FakeUninstallResult()

    monkeypatch.setattr(legacy.subprocess, "run", _fake_run)
    ctx = _make_ctx(tmp_path, tmp_path)
    action = legacy._cleanup_claude_legacy_vscode_extension(ctx)

    assert isinstance(action, FileAction)
    assert action.action == "removed"
    assert action.path == "devai-hub.claude-usage-monitor"
    # The cleanup should have invoked `code --uninstall-extension`.
    assert any("--uninstall-extension" in args for args in call_log)
