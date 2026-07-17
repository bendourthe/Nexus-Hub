"""Per-integration legacy-state self-healing registry.

Every integration may register one or more cleanup functions in
``LEGACY_CLEANUPS``. The function inspects the disk (or, in the case of the
VS Code extension cleanup, the user's installed VS Code extensions; or, in the
case of the auth-monitor cleanup, the user's Windows scheduled tasks) for one
specific legacy artifact and returns:

  - ``FileAction(path=..., action="removed")`` when it cleaned something up
  - ``None`` when there was nothing to clean

``IntegrationBase.install_global`` / ``install_workspace`` invoke
``run_cleanups(self.key, ctx)`` at the start of every install so the legacy
artifacts get removed before the new content is written. This generalizes the
v2.1.0 VS Code extension cleanup (introduced in commit b52a038, the
``remove_legacy_vscode_extensions`` bash function) into a first-class registry
rather than per-platform ad-hoc code.

Design notes
------------

* Filesystem cleanups MUST be idempotent. A second invocation MUST return
  ``None`` for the same artifact (no double-clean errors).
* Cleanups MUST honor ``ctx.dry_run``: still return the ``FileAction`` they
  would have emitted, but skip the actual disk mutation.
* Cleanups MUST be safe to invoke on a system that never had the legacy
  artifact - that is the normal case. Use ``Path.exists()`` / ``shutil.which``
  guards before any destructive call.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .base import InstallContext
from .result import FileAction

CleanupFn = Callable[[InstallContext], Optional[FileAction]]


def _remove_path_if_exists(path: Path, dry_run: bool) -> Optional[FileAction]:
    if not path.exists() and not path.is_symlink():
        return None
    if dry_run:
        return FileAction(path=str(path), action="removed")
    try:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    except OSError:
        return None
    return FileAction(path=str(path), action="removed")


def _cleanup_devai_hub_legacy_global_dir(ctx: InstallContext) -> Optional[FileAction]:
    """Remove a leftover ``~/.devai-hub/`` directory once the v2.0.0 rename has settled.

    The v2.0.0 rename (DevAI-Hub -> Nexus-Hub) ships a one-way migration in
    ``scripts/installer.sh::migrate_legacy_install`` that renames
    ``~/.devai-hub/`` -> ``~/.nexus-hub/``. This Python cleanup handles the
    edge case where the bash rename was already performed (or the user did it
    manually) but ``~/.devai-hub/`` was recreated by a stale tool. Only purge
    when ``~/.nexus-hub/`` already exists so we never destroy unmigrated state.
    """
    legacy = Path.home() / ".devai-hub"
    current = Path.home() / ".nexus-hub"
    if not current.exists():
        return None
    return _remove_path_if_exists(legacy, ctx.dry_run)


def _cleanup_claude_legacy_skill_registry(ctx: InstallContext) -> Optional[FileAction]:
    """Remove the pre-2.0.0 Claude skill registry file.

    Pre-2.0.0 builds wrote ``~/.claude/devai-hub-skills.json`` as a side
    skill-discovery cache. The v2.0.0 cleanup discontinued this file; any copy
    still on disk after a v2.0.0+ install is stale.
    """
    target = Path.home() / ".claude" / "devai-hub-skills.json"
    return _remove_path_if_exists(target, ctx.dry_run)


def _cleanup_claude_legacy_vscode_extension(ctx: InstallContext) -> Optional[FileAction]:
    """Uninstall the renamed ``devai-hub.claude-usage-monitor`` VS Code extension.

    Mirrors the bash function ``remove_legacy_vscode_extensions`` introduced in
    commit b52a038. Returns a ``FileAction`` whose ``path`` is the extension
    ID and ``action`` is ``removed``. Returns ``None`` when:

      - the ``code`` CLI is not available on PATH
      - ``code --list-extensions`` reports the extension is not installed
      - the uninstall subprocess fails for any reason

    These conditions are normal on systems without VS Code, on freshly
    installed machines, and after a previous successful cleanup.
    """
    extension_id = "devai-hub.claude-usage-monitor"
    if shutil.which("code") is None:
        return None
    try:
        listed = subprocess.run(
            ["code", "--list-extensions"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if listed.returncode != 0:
        return None
    if extension_id not in listed.stdout.splitlines():
        return None
    if ctx.dry_run:
        return FileAction(path=extension_id, action="removed")
    try:
        result = subprocess.run(
            ["code", "--uninstall-extension", extension_id],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return FileAction(path=extension_id, action="removed")


_AUTH_MONITOR_TASK_NAME = "Claude Code Auth Monitor"


def _cleanup_windows_auth_monitor_task(ctx: InstallContext) -> Optional[FileAction]:
    """Unregister the orphaned DevAI-Hub "Claude Code Auth Monitor" scheduled task.

    DevAI-Hub v0.9.x registered a user-level Windows scheduled task named exactly
    ``Claude Code Auth Monitor`` that ran
    ``wscript.exe "...\\.devai-hub\\scripts\\run-auth-monitor.vbs"`` every two
    minutes. The auth monitor was removed and the ``~/.devai-hub/`` tree deleted,
    but nothing ever unregistered the task, so it still fires against a ``.vbs``
    that no longer exists and pops a "Can not find script file" Windows Script
    Host dialog. This cleanup removes the task, mirroring the ``code
    --uninstall-extension`` pattern in ``_cleanup_claude_legacy_vscode_extension``.

    Returns ``None`` (no-op) when:

      - not on Windows (``os.name != "nt"``)
      - ``schtasks`` is not on PATH
      - the task is absent (``schtasks /Query`` exits non-zero) - the normal case
      - the query or delete subprocess fails for any reason

    The task is user-level (``RunLevel Limited``), so no elevation is required.
    """
    if os.name != "nt" or shutil.which("schtasks") is None:
        return None
    try:
        query = subprocess.run(
            ["schtasks", "/Query", "/TN", _AUTH_MONITOR_TASK_NAME],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if query.returncode != 0:
        return None
    if ctx.dry_run:
        return FileAction(path=_AUTH_MONITOR_TASK_NAME, action="removed")
    try:
        deleted = subprocess.run(
            ["schtasks", "/Delete", "/TN", _AUTH_MONITOR_TASK_NAME, "/F"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if deleted.returncode != 0:
        return None
    return FileAction(path=_AUTH_MONITOR_TASK_NAME, action="removed")


def _cleanup_devai_hub_auth_monitor_vbs(ctx: InstallContext) -> Optional[FileAction]:
    """Sweep a leftover ``~/.devai-hub/scripts/run-auth-monitor.vbs`` launcher.

    Belt-and-suspenders for the auth-monitor task cleanup: the ``~/.devai-hub/``
    tree is usually already gone (removed by the v2.0.0 rename), so this is a
    no-op on almost every system. It never removes the whole ``~/.devai-hub/``
    directory - that stays gated on ``~/.nexus-hub/`` existing in
    ``_cleanup_devai_hub_legacy_global_dir``.
    """
    target = Path.home() / ".devai-hub" / "scripts" / "run-auth-monitor.vbs"
    return _remove_path_if_exists(target, ctx.dry_run)


def _cleanup_devai_hub_auth_monitor_ps1(ctx: InstallContext) -> Optional[FileAction]:
    """Sweep a leftover ``~/.devai-hub/scripts/claude-auth-monitor.ps1`` launcher.

    Companion to :func:`_cleanup_devai_hub_auth_monitor_vbs`; same
    belt-and-suspenders rationale and the same never-remove-the-whole-tree rule.
    """
    target = Path.home() / ".devai-hub" / "scripts" / "claude-auth-monitor.ps1"
    return _remove_path_if_exists(target, ctx.dry_run)


def _cleanup_gemini_legacy_skill_dir(ctx: InstallContext) -> Optional[FileAction]:
    """Remove the pre-2.0.0 ``~/.gemini/devai-hub-skills/`` mirror directory."""
    target = Path.home() / ".gemini" / "devai-hub-skills"
    return _remove_path_if_exists(target, ctx.dry_run)


def _cleanup_codex_legacy_skill_dir(ctx: InstallContext) -> Optional[FileAction]:
    """Remove the pre-2.0.0 ``~/.codex/devai-hub-skills/`` mirror directory."""
    target = Path.home() / ".codex" / "devai-hub-skills"
    return _remove_path_if_exists(target, ctx.dry_run)


LEGACY_CLEANUPS: Dict[str, List[CleanupFn]] = {
    "claude": [
        _cleanup_devai_hub_legacy_global_dir,
        _cleanup_claude_legacy_skill_registry,
        _cleanup_claude_legacy_vscode_extension,
        _cleanup_windows_auth_monitor_task,
        _cleanup_devai_hub_auth_monitor_vbs,
        _cleanup_devai_hub_auth_monitor_ps1,
    ],
    "codex": [
        _cleanup_codex_legacy_skill_dir,
    ],
    "gemini": [
        _cleanup_gemini_legacy_skill_dir,
    ],
}


def run_cleanups(integration_key: str, ctx: InstallContext) -> List[FileAction]:
    """Run every cleanup registered for ``integration_key`` against ``ctx``.

    Returns a list of ``FileAction`` records, one per cleanup that actually
    removed something. Cleanups that returned ``None`` (nothing to clean) are
    omitted. Order matches ``LEGACY_CLEANUPS[integration_key]`` insertion
    order so the rendered output is deterministic.
    """
    actions: List[FileAction] = []
    for fn in LEGACY_CLEANUPS.get(integration_key, []):
        action = fn(ctx)
        if action is not None:
            actions.append(action)
    return actions


__all__ = ["CleanupFn", "LEGACY_CLEANUPS", "run_cleanups"]
