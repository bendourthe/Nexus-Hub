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


# ---------------------------------------------------------------------------
# Windows auth-monitor scheduled-task cleanup (v3.14.1 Phase 2)
# ---------------------------------------------------------------------------


def _fake_schtasks(task_present: bool, delete_rc: int = 0, call_log=None):
    """Return a fake `subprocess.run` for the schtasks Query/Delete calls."""

    class _Result:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode
            self.stdout = ""

    def _run(args, **kwargs):
        if call_log is not None:
            call_log.append(list(args))
        if "/Query" in args:
            return _Result(0 if task_present else 1)
        if "/Delete" in args:
            return _Result(delete_rc)
        return _Result(0)

    return _run


def test_auth_monitor_task_removed_when_present(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Task present on Windows -> removed, and `schtasks /Delete` was invoked."""
    monkeypatch.setattr(legacy.os, "name", "nt")
    monkeypatch.setattr(legacy.shutil, "which", lambda name: "schtasks.exe")
    calls: list = []
    monkeypatch.setattr(
        legacy.subprocess, "run", _fake_schtasks(task_present=True, call_log=calls)
    )
    ctx = _make_ctx(tmp_path, tmp_path)

    action = legacy._cleanup_windows_auth_monitor_task(ctx)

    assert isinstance(action, FileAction)
    assert action.path == "Claude Code Auth Monitor"
    assert action.action == "removed"
    assert any("/Delete" in c for c in calls)


def test_auth_monitor_task_absent_returns_none(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`schtasks /Query` non-zero (task absent) -> None; no delete attempted."""
    monkeypatch.setattr(legacy.os, "name", "nt")
    monkeypatch.setattr(legacy.shutil, "which", lambda name: "schtasks.exe")
    calls: list = []
    monkeypatch.setattr(
        legacy.subprocess, "run", _fake_schtasks(task_present=False, call_log=calls)
    )
    ctx = _make_ctx(tmp_path, tmp_path)

    assert legacy._cleanup_windows_auth_monitor_task(ctx) is None
    assert all("/Delete" not in c for c in calls)


def test_auth_monitor_noop_off_windows(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Not Windows -> None with no subprocess call at all."""
    monkeypatch.setattr(legacy.os, "name", "posix")

    def _fail(*args, **kwargs):
        raise AssertionError("subprocess.run must not run off Windows")

    monkeypatch.setattr(legacy.subprocess, "run", _fail)
    ctx = _make_ctx(tmp_path, tmp_path)

    assert legacy._cleanup_windows_auth_monitor_task(ctx) is None


def test_auth_monitor_noop_without_schtasks(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`schtasks` not on PATH -> None with no subprocess call."""
    monkeypatch.setattr(legacy.os, "name", "nt")
    monkeypatch.setattr(legacy.shutil, "which", lambda name: None)

    def _fail(*args, **kwargs):
        raise AssertionError("subprocess.run must not run without schtasks")

    monkeypatch.setattr(legacy.subprocess, "run", _fail)
    ctx = _make_ctx(tmp_path, tmp_path)

    assert legacy._cleanup_windows_auth_monitor_task(ctx) is None


def test_auth_monitor_dry_run_reports_without_deleting(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """dry_run + task present -> FileAction returned, but no `/Delete` ran."""
    monkeypatch.setattr(legacy.os, "name", "nt")
    monkeypatch.setattr(legacy.shutil, "which", lambda name: "schtasks.exe")
    calls: list = []
    monkeypatch.setattr(
        legacy.subprocess, "run", _fake_schtasks(task_present=True, call_log=calls)
    )
    ctx = _make_ctx(tmp_path, tmp_path, dry_run=True)

    action = legacy._cleanup_windows_auth_monitor_task(ctx)

    assert isinstance(action, FileAction)
    assert action.path == "Claude Code Auth Monitor"
    assert all("/Delete" not in c for c in calls)


def test_auth_monitor_task_idempotent(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """First pass removes the task; a second pass (now absent) returns None."""
    monkeypatch.setattr(legacy.os, "name", "nt")
    monkeypatch.setattr(legacy.shutil, "which", lambda name: "schtasks.exe")
    state = {"present": True}

    class _Result:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode
            self.stdout = ""

    def _run(args, **kwargs):
        if "/Query" in args:
            return _Result(0 if state["present"] else 1)
        if "/Delete" in args:
            state["present"] = False
            return _Result(0)
        return _Result(0)

    monkeypatch.setattr(legacy.subprocess, "run", _run)
    ctx = _make_ctx(tmp_path, tmp_path)

    first = legacy._cleanup_windows_auth_monitor_task(ctx)
    second = legacy._cleanup_windows_auth_monitor_task(ctx)

    assert isinstance(first, FileAction)
    assert second is None


# ---------------------------------------------------------------------------
# Auth-monitor leftover launcher files (v3.14.1 Phase 2, 2.2)
# ---------------------------------------------------------------------------


def test_auth_monitor_leftover_vbs_removed(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    """A leftover ~/.devai-hub/scripts/run-auth-monitor.vbs is swept, and the
    whole ~/.devai-hub/ tree is NOT removed by this sweep (that stays gated on
    ~/.nexus-hub/ existing in the separate global-dir cleanup).
    """
    scripts_dir = fake_home / ".devai-hub" / "scripts"
    scripts_dir.mkdir(parents=True)
    vbs = scripts_dir / "run-auth-monitor.vbs"
    vbs.write_text("' stale launcher")

    ctx = _make_ctx(tmp_path, tmp_path)
    action = legacy._cleanup_devai_hub_auth_monitor_vbs(ctx)

    assert isinstance(action, FileAction)
    assert action.path == str(vbs)
    assert action.action == "removed"
    assert not vbs.exists()
    # No ~/.nexus-hub/ present, so the gated tree cleanup must NOT fire here.
    assert (fake_home / ".devai-hub").exists()


def test_auth_monitor_leftover_ps1_removed(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    """A leftover ~/.devai-hub/scripts/claude-auth-monitor.ps1 is swept."""
    scripts_dir = fake_home / ".devai-hub" / "scripts"
    scripts_dir.mkdir(parents=True)
    ps1 = scripts_dir / "claude-auth-monitor.ps1"
    ps1.write_text("# stale launcher")

    ctx = _make_ctx(tmp_path, tmp_path)
    action = legacy._cleanup_devai_hub_auth_monitor_ps1(ctx)

    assert isinstance(action, FileAction)
    assert action.path == str(ps1)
    assert not ps1.exists()


def test_auth_monitor_leftover_absent_returns_none(
    fake_home: Path, disable_vscode: None, tmp_path: Path
) -> None:
    """No leftover launcher -> None (the normal case on every system)."""
    ctx = _make_ctx(tmp_path, tmp_path)
    assert legacy._cleanup_devai_hub_auth_monitor_vbs(ctx) is None
    assert legacy._cleanup_devai_hub_auth_monitor_ps1(ctx) is None
