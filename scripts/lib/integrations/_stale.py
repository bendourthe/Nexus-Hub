"""Stale Nexus-Hub surfaces for platforms that are not installed (v4.14.7 Phase 5).

A *stale platform* is a detection-gated integration (it declares a
``"detection"`` spec) that is not detected, was not forced with
``--platforms``, has no redirected home folder, and still has entries in the
install manifest. ``nexus-hub doctor`` and the install summary report them;
``nexus-hub prune-undetected`` removes them, as a dry run unless ``--yes``.

Removal works per entry kind and never deletes what it cannot prove is
unchanged Nexus-Hub output:

- a tracked file with a recorded hash is unlinked only when its current hash
  still matches;
- a tracked directory carries no per-file hash, so a file inside it is
  unlinked only when it was not modified after the directory was recorded, and
  files added later are kept;
- a shared instruction file loses only its Nexus-Hub marker block;
- a merged settings file (Kimi ``config.toml``, Qwen ``settings.json``) loses
  only Nexus-Hub's hook entries, through the integration's own pruner;
- seeded settings files, ``*.nexus-hub.bak`` backups, links, and anything
  outside the platform's declared folder are always kept and reported.

Directories are removed bottom-up with ``rmdir`` only, so a folder that still
holds anything stays. Nothing here calls ``shutil.rmtree``.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from ._detection import _norm, detect_platform, detection_spec
from ._owned import _is_junction, _is_symlink
from .base import long_path
from .result import FileAction, WriteResult

#: Slack for coarse filesystem timestamps when comparing a file's mtime with the
#: directory's recorded mtime.
_MTIME_SLACK = 2.0

REMOVE, STRIP, KEEP, GONE = "remove", "strip", "keep", "gone"


@dataclass
class StaleEntry:
    path: str
    verdict: str
    reason: str
    size: Optional[int] = None
    mtime: Optional[float] = None


@dataclass
class StalePlatform:
    key: str
    display_name: str
    root: str
    evidence: str
    entries: List[StaleEntry] = field(default_factory=list)

    def counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for entry in self.entries:
            out[entry.verdict] = out.get(entry.verdict, 0) + 1
        return out


def _sha256(path: Path) -> Optional[str]:
    try:
        digest = hashlib.sha256()
        with long_path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _linked(path: Path) -> bool:
    if _is_symlink(path) or _is_junction(path):
        return True
    try:
        return path.is_file() and os.lstat(long_path(path)).st_nlink > 1
    except OSError:
        return False


def _within(path: Path, roots: List[Path]) -> bool:
    spelled = _norm(path)
    for root in roots:
        base = _norm(root)
        if spelled == base or spelled.startswith(base.rstrip(os.sep) + os.sep):
            return True
    return False


def _containment(ctx, spec) -> List[Path]:
    """The only folders removal may touch: the declared root and shared configs.

    Taken from the integration's own spec, never from the manifest, so a
    tampered manifest cannot steer a deletion elsewhere.
    """
    roots: List[Path] = []
    if spec.get("root"):
        roots.append(Path(ctx.global_root) / str(spec["root"]))
    return roots


def _shared_configs(ctx, spec) -> Dict[str, str]:
    """Normalized path -> pruner name for declared merged or seeded settings."""
    out: Dict[str, str] = {}
    for rel, pruner in (spec.get("shared_configs") or {}).items():
        out[_norm(Path(ctx.global_root) / str(rel))] = str(pruner or "")
    return out


def _records(manifest, key) -> Dict[str, dict]:
    return {_norm(r.get("path")): r for r in manifest.actions_for(key) if r.get("path")}


def _tracked(manifest, key) -> List[str]:
    seen: Dict[str, str] = {}
    for path in manifest.files_for(key) + [r["path"] for r in manifest.actions_for(key) if r.get("path")]:
        seen.setdefault(_norm(path), str(path))
    return list(seen.values())


def _classify_dir(directory: Path, record: Optional[dict], roots: List[Path]) -> List[StaleEntry]:
    recorded = (record or {}).get("mtime")
    entries: List[StaleEntry] = []

    def unreadable(error: OSError) -> None:
        entries.append(StaleEntry(str(getattr(error, "filename", directory)), KEEP, "a folder that could not be read"))

    for current, dirnames, filenames in os.walk(long_path(directory), onerror=unreadable, followlinks=False):
        here = Path(current)
        for name in dirnames:
            if _linked(here / name):
                entries.append(StaleEntry(str(here / name), KEEP, "a linked folder (never followed)"))
        dirnames[:] = [d for d in dirnames if not _linked(here / d)]
        for name in filenames:
            path = here / name
            try:
                info = os.lstat(path)
            except OSError:
                entries.append(StaleEntry(str(path), KEEP, "could not be read"))
                continue
            if _linked(path):
                entries.append(StaleEntry(str(path), KEEP, "a linked file"))
            elif name.lower().endswith(".nexus-hub.bak"):
                entries.append(StaleEntry(str(path), KEEP, "a backup of your configuration"))
            elif not isinstance(recorded, (int, float)):
                entries.append(StaleEntry(str(path), KEEP, "no install record for this folder"))
            elif info.st_mtime > recorded + _MTIME_SLACK:
                entries.append(StaleEntry(str(path), KEEP, "changed or added after Nexus-Hub installed it"))
            else:
                entries.append(StaleEntry(str(path), REMOVE, "unchanged since install", info.st_size, info.st_mtime))
    return entries


def _classify(ctx, integ, spec, roots: List[Path]) -> List[StaleEntry]:
    manifest = ctx.manifest
    key = integ.key
    records = _records(manifest, key)
    configs = _shared_configs(ctx, spec)
    shared = {_norm(p) for p in manifest.shared_for(key)}
    entries: List[StaleEntry] = []
    for raw in _tracked(manifest, key) + manifest.shared_for(key):
        path = Path(raw)
        spelled = _norm(path)
        if any(_norm(e.path) == spelled for e in entries):
            continue
        if spelled not in configs and not _within(path, roots):
            entries.append(StaleEntry(raw, KEEP, "outside the platform's folder"))
            continue
        if not os.path.lexists(long_path(path)):
            entries.append(StaleEntry(raw, GONE, "already removed"))
            continue
        if _linked(path):
            entries.append(StaleEntry(raw, KEEP, "a link (never followed)"))
        elif path.name.lower().endswith(".nexus-hub.bak"):
            entries.append(StaleEntry(raw, KEEP, "a backup of your configuration"))
        elif spelled in configs:
            if configs[spelled]:
                entries.append(StaleEntry(raw, STRIP, "your settings file: only Nexus-Hub's hook entries are removed"))
            else:
                entries.append(StaleEntry(raw, KEEP, "your settings file (seeded defaults are left in place)"))
        elif spelled in shared:
            entries.append(StaleEntry(raw, STRIP, "shared file: only the Nexus-Hub block is removed"))
        elif path.is_dir():
            entries.extend(_classify_dir(path, records.get(spelled), roots))
        else:
            record = records.get(spelled)
            recorded = (record or {}).get("sha256")
            if not recorded:
                entries.append(StaleEntry(raw, KEEP, "no install record for this file"))
            elif _sha256(path) == recorded:
                info = os.lstat(long_path(path))
                entries.append(StaleEntry(raw, REMOVE, "unchanged since install", info.st_size, info.st_mtime))
            else:
                entries.append(StaleEntry(raw, KEEP, "you changed it after install"))
    unique: Dict[str, StaleEntry] = {}
    for entry in entries:  # a tracked file can also sit inside a tracked folder
        unique.setdefault(_norm(entry.path), entry)
    return list(unique.values())


def plan_platform(ctx, integ) -> Optional[StalePlatform]:
    """Return the removal plan for one stale platform, or None when not stale."""
    spec = detection_spec(integ)
    if spec is None or ctx.manifest.is_forced(integ.key):
        return None
    if not (ctx.manifest.files_for(integ.key) or ctx.manifest.shared_for(integ.key) or ctx.manifest.actions_for(integ.key)):
        return None
    verdict = detect_platform(ctx, integ)
    if verdict.detected:
        return None
    roots = _containment(ctx, spec)
    root_label = str(roots[0]) if roots else str(ctx.global_root)
    stale = StalePlatform(integ.key, getattr(integ, "display_name", integ.key), root_label, verdict.evidence)
    if any(_is_symlink(root) or _is_junction(root) for root in roots):
        # A dotfiles-managed folder: never read through it, never offer removal.
        stale.entries.append(StaleEntry(root_label, KEEP, "redirected folder, not evaluated"))
        return stale
    stale.entries = _classify(ctx, integ, spec, roots)
    return stale


def find_stale(ctx, integrations) -> List[StalePlatform]:
    """Every stale platform among ``integrations``; read-only."""
    out: List[StalePlatform] = []
    for integ in integrations:
        try:
            stale = plan_platform(ctx, integ)
        except OSError:
            continue
        if stale is not None and any(e.verdict != GONE for e in stale.entries):
            out.append(stale)
    return out


def _unchanged(entry: StaleEntry) -> bool:
    try:
        info = os.lstat(long_path(Path(entry.path)))
    except OSError:
        return False
    return info.st_size == entry.size and info.st_mtime == entry.mtime and info.st_nlink <= 1


def _strip(ctx, integ, path: Path) -> FileAction:
    from scripts.lib.installer.instruction_merge import remove_marker_section

    pruner = _shared_configs(ctx, detection_spec(integ) or {}).get(_norm(path), "")
    if pruner == "kimi-config-hooks":
        from ._kimi_native import prune_config_hooks

        return prune_config_hooks(path, ctx.dry_run)
    if pruner == "settings-hooks":
        result = integ._teardown_settings_hooks([path.parent], ctx)
        return result.files[0] if result.files else FileAction(path=str(path), action="kept")
    return remove_marker_section(path, dry_run=ctx.dry_run)


def _remove_empty_dirs(roots: List[Path], touched: List[Path], result: WriteResult, dry_run: bool) -> None:
    candidates = set()
    for path in touched:
        parent = path.parent
        while _within(parent, roots):
            candidates.add(parent)
            if any(_norm(parent) == _norm(r) for r in roots):
                break
            parent = parent.parent
    for directory in sorted(candidates, key=lambda p: len(str(p)), reverse=True):
        try:
            if not dry_run:
                long_path(directory).rmdir()  # empty folders only; never rmtree
            elif any(long_path(directory).iterdir()):
                continue
            result.add(str(directory), "removed")
        except OSError:
            continue


def apply_platform(ctx, integ, stale: StalePlatform) -> WriteResult:
    """Carry out ``stale``'s plan. Re-checks detection and every file first."""
    result = WriteResult()
    if detect_platform(ctx, integ).detected:
        result.note(f"{stale.display_name} is detected now; nothing removed.")
        return result
    roots = _containment(ctx, detection_spec(integ) or {})
    touched: List[Path] = []
    for entry in stale.entries:
        path = Path(entry.path)
        if entry.verdict == REMOVE:
            if not _unchanged(entry):
                result.files.append(FileAction(path=entry.path, action="kept", reason="changed during removal"))
                continue
            try:
                if not ctx.dry_run:
                    long_path(path).unlink()
                result.add(entry.path, "removed")
                touched.append(path)
            except OSError as exc:
                result.files.append(FileAction(path=entry.path, action="kept", reason=f"locked or unreadable ({exc.strerror or exc})"))
        elif entry.verdict == STRIP:
            result.files.append(_strip(ctx, integ, path))
            touched.append(path)
        elif entry.verdict == GONE:
            touched.append(path)
    _remove_empty_dirs(roots, touched, result, ctx.dry_run)
    if not ctx.dry_run:
        _forget(ctx.manifest, integ.key, result)
    return result


def _forget(manifest, key: str, result: WriteResult) -> None:
    """Untrack every path that no longer exists, keeping records for the rest."""
    for path in manifest.files_for(key):
        if not os.path.lexists(long_path(Path(path))):
            manifest.untrack(key, path)
    for path in manifest.shared_for(key):
        if not os.path.lexists(long_path(Path(path))):
            manifest.untrack_shared(key, path)
    manifest.retain_actions(key, lambda record: os.path.lexists(long_path(Path(str(record.get("path"))))))


__all__ = ["StaleEntry", "StalePlatform", "apply_platform", "find_stale", "plan_platform"]
