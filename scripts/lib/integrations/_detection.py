"""Platform detection: is a tool present, judged by evidence Nexus-Hub did not create?

v4.14.7 Phase 1. Before this module, Kimi, Qwen, Hermes, and Pi treated "the
tool's home folder exists" as proof the tool was installed, while Nexus-Hub
wrote into that same folder. One earlier write therefore made every later
install count the tool as present (decision record
``docs/decisions/proposed/policy/2026-10-29-platform-detection-evidence-rule.md``).

Each gated integration declares a ``"detection"`` entry in its class-level
``config`` dict, and :func:`detect_platform` evaluates it in this order:

1. **Forced**: the user named the platform with ``--platforms`` this run
   (``ctx.forced_keys``) or on an earlier run (``manifest.is_forced``).
2. **Root**: the declared home root is a real directory holding at least one
   top-level entry that Nexus-Hub did not write; or one of the declared
   ``vendor_roots`` (folders only the tool writes) holds any entry outside the
   names Nexus-Hub is known to write there.
3. **Executable**: a declared command resolves on ``PATH``. Relative and empty
   ``PATH`` entries are skipped and the current directory is never searched,
   so running the installer from a folder that happens to contain a same-named
   script cannot fake a tool. A collision-prone name needs its resolved path to
   contain one of its ``corroborate`` markers.
4. **App**: one of the declared per-OS installed-application paths exists.

Classification of a root's top-level entries:

- **Nexus-Hub's** (not evidence): a name in ``nexus_entries``, or any path the
  manifest tracks for the key (regular, shared, organization, or action record)
  at or below that entry. Tracked merged configs land here too, so a user's
  config that Nexus-Hub merged into is never mistaken for proof either way.
- **Ignored** (neither): OS metadata and Nexus-Hub transient files
  (``*.nexus-hub.tmp``) and backups (``*.nexus-hub.bak``). A backup is neutral,
  not evidence: ``merge_config_hooks`` writes one whenever the config already
  existed, including a config Nexus-Hub seeded itself moments earlier.
- **Vendor evidence**: everything else.

A redirected root (symlink or junction) is never read through. It is
inconclusive for the root check, and evaluation falls through to ``PATH``.
The resolved executable is never run, sourced, or version-probed. Nothing here
writes to disk or creates the root it inspects.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, List, Mapping, Optional, Sequence

from ._owned import _is_junction, _is_symlink

#: OS metadata that a file manager drops into any folder it opens.
IGNORED_NAMES = frozenset({"desktop.ini", ".ds_store", "thumbs.db", "$recycle.bin"})
#: Nexus-Hub transient and backup suffixes; neutral for detection.
IGNORED_SUFFIXES = (".nexus-hub.tmp", ".nexus-hub.bak")

Which = Callable[[str], Optional[str]]


@dataclass(frozen=True)
class Detection:
    """The outcome of :func:`detect_platform`.

    ``kind`` is one of ``forced``, ``root``, ``executable``, ``app``, or
    ``absent``; ``evidence`` is a one-line, user-facing reason.
    """

    detected: bool
    evidence: str
    kind: str


def detection_spec(integration) -> Optional[Mapping[str, object]]:
    """Return the integration's declared detection spec, or None when ungated."""
    config = getattr(integration, "config", None) or {}
    spec = config.get("detection")
    return spec if isinstance(spec, Mapping) else None


def _strip_long_prefix(text: str) -> str:
    if text.startswith("\\\\?\\UNC\\"):
        return "\\\\" + text[8:]
    if text.startswith("\\\\?\\"):
        return text[4:]
    return text


def _norm(path: object) -> str:
    """Comparable spelling: no long-path prefix, normalized separators and case."""
    text = _strip_long_prefix(str(path))
    return os.path.normcase(os.path.normpath(os.path.abspath(text)))


def _is_wsl() -> bool:
    if not sys.platform.startswith("linux"):
        return False
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def _path_dirs(raw: Optional[str] = None) -> List[str]:
    """Absolute ``PATH`` directories, minus relative entries and WSL drive mounts.

    Under WSL a hit below ``/mnt/<drive>/`` is a Windows install, and the
    Windows tool never reads the Linux home this install writes into.
    """
    wsl = _is_wsl()
    dirs: List[str] = []
    for entry in (raw if raw is not None else os.environ.get("PATH", "")).split(os.pathsep):
        entry = entry.strip().strip('"')
        if not entry or not os.path.isabs(entry):
            continue
        if wsl and len(entry) >= 6 and entry.startswith("/mnt/") and entry[6:7] in ("/", ""):
            continue
        dirs.append(entry)
    return dirs


def safe_which(name: str, path: Optional[str] = None) -> Optional[str]:
    """Resolve ``name`` on ``PATH`` without ever searching the current directory."""
    if os.sep in name or (os.altsep and os.altsep in name):
        return None
    if os.name == "nt":
        exts = [e for e in os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD").split(";") if e]
        if os.path.splitext(name)[1].upper() in {e.upper() for e in exts}:
            exts = [""]
    else:
        exts = [""]
    for directory in _path_dirs(path):
        for ext in exts:
            candidate = os.path.join(directory, name + ext)
            if os.path.isfile(candidate) and (os.name == "nt" or os.access(candidate, os.X_OK)):
                return os.path.abspath(candidate)
    return None


def _tracked_paths(manifest, key: str) -> List[str]:
    """Every path the manifest attributes to ``key``, in any bucket."""
    if manifest is None:
        return []
    paths: List[str] = []
    for getter in ("files_for", "shared_for", "org_files_for", "org_shared_for"):
        method = getattr(manifest, getter, None)
        if method is not None:
            paths.extend(str(p) for p in method(key))
    actions = getattr(manifest, "actions_for", None)
    if actions is not None:
        paths.extend(str(a.get("path")) for a in actions(key) if a.get("path"))
    return paths


def _owned_top_level(root: Path, tracked: Iterable[str]) -> set:
    """Lower-cased names of root's top-level entries that hold a tracked path."""
    base = _norm(root)
    prefix = base.rstrip(os.sep) + os.sep
    owned = set()
    for raw in tracked:
        spelled = _norm(raw)
        if spelled == base or not spelled.startswith(prefix):
            continue
        owned.add(spelled[len(prefix):].split(os.sep, 1)[0].lower())
    return owned


def _ignored(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered in IGNORED_NAMES
        or lowered.startswith("._")
        or lowered.endswith(IGNORED_SUFFIXES)
    )


def vendor_entries(root: Path, nexus_entries: Sequence[str], tracked: Iterable[str]) -> List[str]:
    """Top-level entries of ``root`` that are neither Nexus-Hub's nor ignored.

    Raises OSError when the directory cannot be listed; the caller reports it.
    """
    declared = {name.lower() for name in nexus_entries}
    owned = _owned_top_level(root, tracked)
    found: List[str] = []
    with os.scandir(root) as listing:
        for entry in listing:
            lowered = entry.name.lower()
            if _ignored(entry.name) or lowered in declared or lowered in owned:
                continue
            found.append(entry.name)
    return sorted(found)


def _root_check(root: Path, spec: Mapping[str, object], ctx, key: str) -> Optional[Detection]:
    """A positive or inconclusive root verdict; None when there is nothing there."""
    if _is_symlink(root) or _is_junction(root):
        return Detection(False, f"{_display(root)} is a redirected folder (not evaluated)", "redirected")
    if not root.exists():
        return None
    if not root.is_dir():
        return Detection(False, f"{_display(root)} is not a folder", "absent")
    nexus = [str(n) for n in spec.get("nexus_entries", ()) or ()]
    try:
        vendor = vendor_entries(root, nexus, _tracked_paths(getattr(ctx, "manifest", None), key))
    except OSError as exc:
        return Detection(False, f"{_display(root)} could not be read ({exc.strerror or exc})", "absent")
    if vendor:
        return Detection(True, f"{_display(root)} holds {vendor[0]}", "root")
    if any(True for _ in _safe_iterdir(root)):
        return Detection(False, f"{_display(root)} holds only Nexus-Hub files", "absent")
    return Detection(False, f"{_display(root)} is empty", "absent")


def _safe_iterdir(root: Path):
    try:
        yield from (p for p in root.iterdir() if not _ignored(p.name))
    except OSError:
        return


def _display(path: Path) -> str:
    """``~/``-relative spelling for messages when the path is under the home."""
    try:
        return "~/" + path.relative_to(Path.home()).as_posix()
    except ValueError:
        return str(path)


def _vendor_root_check(spec: Mapping[str, object], global_root: Path) -> Optional[Detection]:
    """Folders only the tool writes; any entry there, minus the names Nexus-Hub
    is known to write into it, is evidence (for example OpenCode's
    ``~/.local/share/opencode`` or Nexus AI Studio's ``~/.nexus``)."""
    roots = spec.get("vendor_roots") or {}
    if not isinstance(roots, Mapping):
        roots = {str(r): () for r in roots}
    for rel, excluded in roots.items():
        path = global_root / str(rel)
        if _is_symlink(path) or _is_junction(path) or not path.is_dir():
            continue
        try:
            entries = vendor_entries(path, [str(n) for n in excluded or ()], ())
        except OSError:
            continue
        if entries:
            return Detection(True, f"{_display(path)} holds {entries[0]}", "root")
    return None


def _executable_check(spec: Mapping[str, object], which: Which) -> Optional[Detection]:
    corroborate = spec.get("corroborate") or {}
    for name in spec.get("executables", ()) or ():
        resolved = which(str(name))
        if not resolved:
            continue
        markers = corroborate.get(name) if isinstance(corroborate, Mapping) else None
        if markers and not any(str(m).lower() in str(resolved).lower() for m in markers):
            continue
        return Detection(True, f"{name} found at {resolved}", "executable")
    return None


def _app_check(spec: Mapping[str, object]) -> Optional[Detection]:
    app_paths = spec.get("app_paths") or {}
    if not isinstance(app_paths, Mapping):
        return None
    for platform, templates in app_paths.items():
        if not sys.platform.startswith(str(platform)):
            continue
        for template in templates or ():
            expanded = os.path.expandvars(os.path.expanduser(str(template)))
            if "%" in expanded or "$" in expanded:
                continue  # an undefined variable; never guess a location
            if os.path.exists(expanded):
                return Detection(True, f"application found at {expanded}", "app")
    return None


def _describe_absent(spec: Mapping[str, object], root_verdict: Optional[Detection], root: Optional[Path]) -> str:
    parts: List[str] = []
    executables = [str(n) for n in spec.get("executables", ()) or ()]
    if executables:
        parts.append(f"{' / '.join(executables)} not on PATH")
    if root_verdict is not None:
        parts.append(root_verdict.evidence)
    elif root is not None:
        parts.append(f"{_display(root)} absent")
    if spec.get("app_paths"):
        parts.append("application not installed")
    return "; ".join(parts) or "no detection evidence"


def detect_platform(ctx, integration) -> Detection:
    """Decide whether ``integration``'s tool is present on this machine.

    An integration without a ``detection`` spec is not gated and is reported
    as detected with kind ``ungated``.
    """
    key = getattr(integration, "key", "")
    spec = detection_spec(integration)
    if spec is None:
        return Detection(True, "not detection-gated", "ungated")
    manifest = getattr(ctx, "manifest", None)
    forced = key in (getattr(ctx, "forced_keys", None) or ())
    if not forced and manifest is not None and hasattr(manifest, "is_forced"):
        forced = bool(manifest.is_forced(key))
    if forced:
        return Detection(True, f"named with --platforms {key}", "forced")
    root: Optional[Path] = None
    root_verdict: Optional[Detection] = None
    if spec.get("root"):
        root = Path(ctx.global_root) / str(spec["root"])
        root_verdict = _root_check(root, spec, ctx, key)
        if root_verdict is not None and root_verdict.detected:
            return root_verdict
    vendor = _vendor_root_check(spec, Path(ctx.global_root))
    if vendor is not None:
        return vendor
    which = getattr(ctx, "which", None) or safe_which
    found = _executable_check(spec, which)
    if found is not None:
        return found
    app = _app_check(spec)
    if app is not None:
        return app
    return Detection(False, _describe_absent(spec, root_verdict, root), "absent")


__all__ = [
    "Detection",
    "IGNORED_NAMES",
    "IGNORED_SUFFIXES",
    "detect_platform",
    "detection_spec",
    "safe_which",
    "vendor_entries",
]
