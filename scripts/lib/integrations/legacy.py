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

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from ._paths import long_path
from .result import FileAction

if TYPE_CHECKING:  # type-only: `base` imports this module lazily, so a runtime import would be a cycle
    from .base import InstallContext

CleanupFn = Callable[["InstallContext"], Optional[FileAction]]


import runpy as _process_runpy
from pathlib import Path as _ProcessPath

_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[2] / "nexus_process.py"))
_PROCESS_POLICY["install_no_window_default"]()


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
    if ctx.scope == "global" and ctx.explicit_target:
        return []
    actions: List[FileAction] = []
    for fn in LEGACY_CLEANUPS.get(integration_key, []):
        action = fn(ctx)
        if action is not None:
            actions.append(action)
    return actions


# ---------------------------------------------------------------------------
# v4.14.7 Phase 6: obsolete home-folder layouts (~/.agent, home-root ~/.opencode)
#
# Unlike the cleanups above, these never run during an install. A layout tree is
# classified file by file against `legacy_layout_fingerprints.json` (built from
# git history by scripts/build_legacy_layout_fingerprints.py) and removed only by
# `nexus-hub prune-undetected --yes`, and only when EVERY entry is recognized
# Nexus-Hub output (decision D4). Anything else keeps the whole tree.
# ---------------------------------------------------------------------------

LAYOUT_FINGERPRINTS = Path(__file__).resolve().parents[1] / "installer" / "legacy_layout_fingerprints.json"
LAYOUT_SCHEMA = 1


@dataclass
class LegacyLayoutVerdict:
    """The classification of one obsolete layout tree under a home folder.

    ``status`` is ``absent`` (no tree), ``removable`` (every entry recognized),
    ``kept`` (at least one unrecognized entry, or nothing recognized), or
    ``unavailable`` (the fingerprint set could not be read).
    """

    layout: str
    root: Path
    status: str
    reason: str = ""
    recognized: List[Path] = field(default_factory=list)
    unrecognized: List[str] = field(default_factory=list)
    snapshot: Dict[str, tuple] = field(default_factory=dict)


def load_layout_fingerprints(path: Optional[Path] = None) -> Optional[dict]:
    """The committed layout set, or None when missing, unreadable, or of another schema."""
    try:
        doc = json.loads((path or LAYOUT_FINGERPRINTS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(doc, dict) or doc.get("schema") != LAYOUT_SCHEMA or not isinstance(doc.get("layouts"), dict):
        return None
    return doc


def _rendered_matches(path: Path, lines: Optional[set]) -> bool:
    """A rendered instruction file: every non-blank line was shipped by Nexus-Hub."""
    if not lines:
        return False
    from scripts.lib.installer.legacy_instruction_block import line_hash

    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    content = [line for line in text.splitlines() if line.strip()]
    return bool(content) and all(line_hash(line) in lines for line in content)


def classify_legacy_layout(home: Path, layout: str, fingerprints: Optional[dict] = None) -> LegacyLayoutVerdict:
    """Classify one obsolete layout tree under ``home``. Read-only and fail-closed."""
    doc = fingerprints if fingerprints is not None else load_layout_fingerprints()
    spec = (doc or {}).get("layouts", {}).get(layout)
    if not spec:
        return LegacyLayoutVerdict(layout, Path(home), "unavailable", "fingerprint set unavailable; nothing evaluated")
    root = Path(home) / str(spec["root"])
    verdict = LegacyLayoutVerdict(layout, root, "kept")
    if not os.path.lexists(long_path(root)):
        verdict.status = "absent"
        return verdict
    from ._owned import _is_junction, _is_symlink

    if _is_symlink(root) or _is_junction(root) or not root.is_dir():
        verdict.unrecognized.append(".")
        verdict.reason = "the folder is a link or not a folder"
        return verdict
    files: Dict[str, set] = {path: set(hashes) for path, hashes in spec.get("files", {}).items()}
    rendered = set(spec.get("rendered", ()))
    folders = {"/".join(p.split("/")[:i]) for p in list(files) + list(rendered) for i in range(1, p.count("/") + 1)}
    from scripts.lib.installer.legacy_instruction_block import load_fingerprints

    line_set = load_fingerprints() if rendered else None
    stack = [(root, "")]
    while stack:
        folder, prefix = stack.pop()
        try:
            entries = list(os.scandir(long_path(folder)))
        except OSError:
            verdict.unrecognized.append((prefix or ".") + " (unreadable)")
            continue
        for entry in entries:
            rel = f"{prefix}{entry.name}"
            path = folder / entry.name
            if _is_symlink(path) or _is_junction(path):
                verdict.unrecognized.append(rel + " (link)")
            elif entry.is_dir(follow_symlinks=False):
                if rel in folders:
                    stack.append((path, rel + "/"))
                else:
                    verdict.unrecognized.append(rel + "/")
            elif entry.is_file(follow_symlinks=False):
                info = entry.stat(follow_symlinks=False)
                if info.st_size == 0:
                    verdict.unrecognized.append(rel + " (empty file)")
                elif rel in rendered and _rendered_matches(path, line_set):
                    verdict.recognized.append(path)
                elif rel in files and _sha256_file(path) in files[rel]:
                    verdict.recognized.append(path)
                else:
                    verdict.unrecognized.append(rel)
                if verdict.recognized and verdict.recognized[-1] == path:
                    # os.lstat, not the scandir entry: on Windows the entry
                    # reports st_ino as 0, which never matches the re-check.
                    real = os.lstat(long_path(path))
                    verdict.snapshot[str(path)] = (real.st_size, real.st_mtime, real.st_ino)
            else:
                verdict.unrecognized.append(rel + " (not a regular file)")
    if verdict.unrecognized:
        verdict.reason = f"{len(verdict.unrecognized)} entries are not recognized Nexus-Hub output"
    elif not verdict.recognized:
        verdict.reason = "holds no recognized Nexus-Hub file"
    else:
        verdict.status = "removable"
        verdict.reason = f"all {len(verdict.recognized)} files are unchanged Nexus-Hub output"
    return verdict


def _sha256_file(path: Path) -> Optional[str]:
    try:
        return hashlib.sha256(long_path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def remove_legacy_layout(verdict: LegacyLayoutVerdict, dry_run: bool) -> List[FileAction]:
    """Remove a ``removable`` tree file by file; never ``rmtree``.

    Each file is re-checked (size, mtime, inode) right before it is unlinked; a
    change stops the removal and leaves the rest. Folders are removed bottom-up
    with ``rmdir``, so a file that appears after classification keeps its folder
    and the result is reported as partial.
    """
    if verdict.status != "removable":
        return []
    actions: List[FileAction] = []
    for path in verdict.recognized:
        try:
            info = os.lstat(long_path(path))
        except OSError:
            continue
        if (info.st_size, info.st_mtime, info.st_ino) != verdict.snapshot.get(str(path)):
            actions.append(FileAction(path=str(path), action="kept", reason="changed during removal; stopped"))
            return actions
        if not dry_run:
            try:
                long_path(path).unlink()
            except OSError as exc:  # read-only or open in another program: stop, keep the rest
                actions.append(FileAction(path=str(path), action="kept", reason=f"locked or read-only ({exc.strerror or exc}); stopped"))
                return actions
        actions.append(FileAction(path=str(path), action="removed"))
    folders = sorted({p.parent for p in verdict.recognized} | {verdict.root}, key=lambda p: len(str(p)), reverse=True)
    extra = set()
    for path in verdict.recognized:
        parent = path.parent
        while parent != verdict.root and verdict.root in parent.parents:
            extra.add(parent)
            parent = parent.parent
    for folder in sorted(set(folders) | extra, key=lambda p: len(str(p)), reverse=True):
        if dry_run:
            continue
        try:
            long_path(folder).rmdir()
            actions.append(FileAction(path=str(folder), action="removed"))
        except OSError:
            actions.append(FileAction(path=str(folder), action="kept", reason="not empty; partial removal"))
    return actions


__all__ = [
    "CleanupFn",
    "LEGACY_CLEANUPS",
    "LegacyLayoutVerdict",
    "classify_legacy_layout",
    "load_layout_fingerprints",
    "remove_legacy_layout",
    "run_cleanups",
]
