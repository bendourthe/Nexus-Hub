"""Install manifest -- tracks the files each integration creates.

The manifest is a JSON file written to `<target_root>/.nexus-hub/install-manifest.json`
that maps integration key -> list of created paths. Teardown reads this file to
know what to remove.

v2.3.0 (Phase 4 / T010) added an additive `actions` field that records the
full `FileAction` history (action vocabulary + SHA-256 + mtime) the runner
captures on every install. `doctor` reads this field to detect drift and
`repair` uses it to know which managed files to re-write. The pre-existing
`_tracked` / `_shared` / `_logs` fields are untouched so the existing 50-case
integration contract suite stays green.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional

from ._paths import long_path

# The `logs` list is a diagnostic trail that nothing reads back, but every
# install loaded the previous trail, appended its own lines and saved the whole
# file again. With no bound it reached 159,119 lines (13 MB) on a long-lived
# machine, so every save rewrote megabytes of history. One full install writes
# about 2,500 lines, so this keeps the latest run and some history.
MAX_LOGS = 5000


def _hash_path(path: Path) -> Optional[str]:
    """Return SHA-256 hex of `path` if it is a regular file, else None.

    Directories return None (they have no content hash on their own). Symlinks,
    missing files, and unreadable files also return None.
    """
    try:
        if not path.is_file():
            return None
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _mtime(path: Path) -> Optional[float]:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


class InstallManifest:
    """Per-invocation manifest of files created by each integration.

    The manifest persists to disk on demand via `save()`. Teardown reads it
    back with `load()`.
    """

    def __init__(self) -> None:
        self._tracked: Dict[str, List[str]] = {}
        self._shared: Dict[str, List[str]] = {}
        self._org_tracked: Dict[str, List[str]] = {}
        self._org_shared: Dict[str, List[str]] = {}
        self._logs: List[str] = []
        # v2.3.0 additive: per-integration list of recorded action dicts
        # `{path, action, sha256, mtime}`. Populated by `record_actions()` from
        # the runner after each integration install. Stored separately so
        # legacy callers / tests that only touch `_tracked` keep working.
        self._actions: Dict[str, List[Dict[str, object]]] = {}
        # v3.16.1 Phase 5.4 -- the serialized install-selection plan, or None
        # when the install was not selector-driven.
        #
        # `None` and "absent" mean the same thing here, and both mean FULL. A
        # manifest written before v3.16.1 has no `selection` key at all, and
        # `from_dict` reads it with a default, so an old manifest loads cleanly
        # and is correctly interpreted as the full install it was. That is why
        # this is an additive key rather than a schema bump: there is no
        # migration to run and no reader to change.
        self._selection: Optional[Dict[str, object]] = None
        # v4.14.7 Phase 1 -- platforms the user forced with --platforms
        # (decision D5). Detection treats them as present on every later
        # install, and the stale-surface report never offers them for removal.
        # Emitted only when non-empty, so an ordinary install writes the same
        # manifest bytes it wrote before.
        self._forced: Dict[str, bool] = {}

    def set_forced(self, integration_key: str) -> None:
        self._forced[integration_key] = True
        self._logs.append(f"[{integration_key}] forced")

    def clear_forced(self, integration_key: str) -> None:
        self._forced.pop(integration_key, None)

    def is_forced(self, integration_key: str) -> bool:
        return bool(self._forced.get(integration_key))

    def track(self, integration_key: str, path: str) -> None:
        bucket = self._tracked.setdefault(integration_key, [])
        if path not in bucket:
            bucket.append(path)
        self._logs.append(f"[{integration_key}] track: {path}")

    def untrack(self, integration_key: str, path: str) -> None:
        bucket = self._tracked.get(integration_key, [])
        if path in bucket:
            bucket.remove(path)
        self._logs.append(f"[{integration_key}] untrack: {path}")

    def track_shared(self, integration_key: str, path: str) -> None:
        """Track a marker-managed shared file.

        Files registered via `track_shared` are NOT unlinked during teardown;
        instead the integration's own teardown removes its marker-delimited
        section while preserving any user content elsewhere in the file.
        """
        bucket = self._shared.setdefault(integration_key, [])
        if path not in bucket:
            bucket.append(path)
        self._logs.append(f"[{integration_key}] track-shared: {path}")

    def untrack_shared(self, integration_key: str, path: str) -> None:
        bucket = self._shared.get(integration_key, [])
        if path in bucket:
            bucket.remove(path)
        self._logs.append(f"[{integration_key}] untrack-shared: {path}")

    def shared_for(self, integration_key: str) -> List[str]:
        return list(self._shared.get(integration_key, []))

    def track_org(self, integration_key: str, path: str) -> None:
        """Track an organization-owned file or directory for selective cleanup."""

        self.track(integration_key, path)
        bucket = self._org_tracked.setdefault(integration_key, [])
        if path not in bucket:
            bucket.append(path)
        self._logs.append(f"[{integration_key}] track-org: {path}")

    def untrack_org(self, integration_key: str, path: str) -> None:
        bucket = self._org_tracked.get(integration_key, [])
        if path in bucket:
            bucket.remove(path)
        self.untrack(integration_key, path)
        self._logs.append(f"[{integration_key}] untrack-org: {path}")

    def org_files_for(self, integration_key: str) -> List[str]:
        return list(self._org_tracked.get(integration_key, []))

    def track_org_shared(self, integration_key: str, path: str) -> None:
        """Track a shared instruction file containing an organization marker block."""

        bucket = self._org_shared.setdefault(integration_key, [])
        if path not in bucket:
            bucket.append(path)
        self._logs.append(f"[{integration_key}] track-org-shared: {path}")

    def untrack_org_shared(self, integration_key: str, path: str) -> None:
        bucket = self._org_shared.get(integration_key, [])
        if path in bucket:
            bucket.remove(path)
        self._logs.append(f"[{integration_key}] untrack-org-shared: {path}")

    def org_shared_for(self, integration_key: str) -> List[str]:
        return list(self._org_shared.get(integration_key, []))

    def all_org_keys(self) -> List[str]:
        return sorted(
            {key for key, paths in self._org_tracked.items() if paths}
            | {key for key, paths in self._org_shared.items() if paths}
        )

    def log(self, integration_key: str, message: str) -> None:
        self._logs.append(f"[{integration_key}] {message}")

    def files_for(self, integration_key: str) -> List[str]:
        return list(self._tracked.get(integration_key, []))

    def all_keys(self) -> List[str]:
        return list(self._tracked.keys())

    # ------------------------------------------------------------------
    # v2.3.0 / Phase 4 / T010 -- action recording for doctor / repair
    # ------------------------------------------------------------------

    def record_actions(self, integration_key: str, file_actions) -> None:
        """Replace the action record for `integration_key` with the
        actions in `file_actions` (an iterable of `FileAction`).

        Each entry is stored as `{path, action, sha256, mtime, recorded_at}`.
        Hash and mtime are captured at record time; `doctor` compares them
        later to detect drift. `recorded_at` is the wall-clock install time:
        a copied folder keeps its source's mtime, so only this stamp tells a
        file changed after install from one copied with an older timestamp. Replacement (not append) so successive installs of the
        same integration in one invocation do not pile up duplicate records.
        """
        from .result import REPORT_ACTIONS

        captured: List[Dict[str, object]] = []
        recorded_at = time.time()
        for fa in file_actions:
            if fa.action in REPORT_ACTIONS:
                # A detection report or a backup is not a file this install owns.
                continue
            path = Path(fa.path)
            captured.append(
                {
                    "path": fa.path,
                    "action": fa.action,
                    "sha256": _hash_path(path),
                    "mtime": _mtime(path),
                    "recorded_at": recorded_at,
                }
            )
        self._actions[integration_key] = captured
        self._logs.append(
            f"[{integration_key}] record-actions: {len(captured)} entries"
        )

    def retain_actions(self, integration_key: str, keep) -> None:
        """Keep only the action records ``keep(record)`` accepts (v4.14.7).

        Used after stale-surface removal so records survive for the files that
        were kept and disappear for the files that were removed.
        """
        kept = [r for r in self._actions.get(integration_key, []) if keep(r)]
        if kept:
            self._actions[integration_key] = kept
        else:
            self._actions.pop(integration_key, None)

    def actions_for(self, integration_key: str) -> List[Dict[str, object]]:
        """Return the recorded action entries for `integration_key`."""
        return list(self._actions.get(integration_key, []))

    def all_action_keys(self) -> List[str]:
        """Return every integration key with at least one recorded action."""
        return sorted(self._actions.keys())

    # ------------------------------------------------------------------
    # v3.16.1 / Phase 5.4 -- install-selection state
    # ------------------------------------------------------------------

    def set_selection(self, plan: Optional[Dict[str, object]]) -> None:
        """Record the resolved selection plan (or None for a full install)."""
        self._selection = dict(plan) if plan is not None else None

    def selection(self) -> Optional[Dict[str, object]]:
        """The recorded plan, or None when this install was full.

        Callers MUST treat None as "full", not as "unknown". A pre-v3.16.1
        manifest is indistinguishable from a v3.16.1 full install here, and that
        is correct: both installed the whole catalog.
        """
        return dict(self._selection) if self._selection is not None else None

    def selection_hash(self) -> Optional[str]:
        if not self._selection:
            return None
        value = self._selection.get("hash")
        return str(value) if value is not None else None

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "tracked": self._tracked,
            "shared": self._shared,
            "logs": self._logs[-MAX_LOGS:],
            "actions": self._actions,
        }
        if any(self._org_tracked.values()):
            data["org_tracked"] = self._org_tracked
        if any(self._org_shared.values()):
            data["org_shared"] = self._org_shared
        # Emitted only when a selection exists, so a full install writes exactly
        # the same manifest bytes it wrote before v3.16.1. The contract's
        # byte-equivalence requirement covers the installed tree; keeping the
        # manifest identical too means an existing diff-based check does not
        # start reporting a change on every full install.
        if self._selection is not None:
            data["selection"] = self._selection
        if self._forced:
            data["forced"] = dict(self._forced)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "InstallManifest":
        m = cls()
        m._tracked = dict(data.get("tracked", {}))
        m._shared = dict(data.get("shared", {}))
        m._org_tracked = dict(data.get("org_tracked", {}))
        m._org_shared = dict(data.get("org_shared", {}))
        m._logs = list(data.get("logs", []))[-MAX_LOGS:]
        m._actions = dict(data.get("actions", {}))
        selection = data.get("selection")
        m._selection = dict(selection) if isinstance(selection, dict) else None
        forced = data.get("forced")
        m._forced = {str(k): True for k, v in forced.items() if v} if isinstance(forced, dict) else {}
        return m

    def save(self, path: Path) -> None:
        """Write the manifest atomically (v4.14.7 Phase 1).

        A temporary sibling is written and then swapped in with ``os.replace``,
        so an interrupted or failed write leaves the previous manifest intact
        rather than a truncated file that would cost every later doctor and
        removal run its ownership data.
        """
        io_path = long_path(path)  # AR-11: a deep project root passes MAX_PATH
        io_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = io_path.with_name(f"{io_path.name}.{os.getpid()}.tmp")
        try:
            tmp.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
            os.replace(tmp, io_path)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    # Best effort: the manifest itself is already swapped in (or the
                    # original error is propagating), and a leftover ``*.tmp`` is harmless.
                    pass

    @classmethod
    def load(cls, path: Path) -> "InstallManifest":
        """Read the manifest; a corrupt file is set aside, never fatal.

        v4.14.7 Phase 1: an unreadable manifest used to raise before detection
        ran. It is now renamed to ``<name>.corrupt-<timestamp>`` (kept for
        inspection, never deleted), one warning is printed, and an empty
        manifest is returned, so detection falls back to the declared Nexus-Hub
        entry names.
        """
        io_path = long_path(path)
        if not io_path.exists():
            return cls()
        try:
            data = json.loads(io_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("manifest root is not an object")
            _check_shape(data)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            aside = io_path.with_name(f"{io_path.name}.corrupt-{time.strftime('%Y%m%d%H%M%S')}")
            try:
                os.replace(io_path, aside)
                where = f"moved to {aside.name}"
            except OSError:
                where = "left in place"
            print(
                f"[warn] install manifest {path} is unreadable ({exc}); {where}. "
                "Starting from an empty manifest.",
                file=sys.stderr,
            )
            return cls()
        return cls.from_dict(data)


_LIST_FIELDS = ("tracked", "shared", "org_tracked", "org_shared")


def _check_shape(data: Dict[str, object]) -> None:
    """Reject valid JSON whose fields have the wrong type.

    Every later reader assumes ``{key: [path, ...]}`` for the tracked and shared
    maps and ``{key: [record, ...]}`` for actions. A manifest that parses but
    does not have that shape used to crash doctor, prune, and install with a
    traceback; it is now set aside like any other unreadable manifest.
    """
    for name in _LIST_FIELDS:
        value = data.get(name, {})
        if not isinstance(value, dict) or not all(
            isinstance(k, str) and isinstance(v, list) and all(isinstance(p, str) for p in v)
            for k, v in value.items()
        ):
            raise ValueError(f"manifest field {name!r} is not a map of path lists")
    actions = data.get("actions", {})
    if not isinstance(actions, dict) or not all(
        isinstance(v, list) and all(isinstance(r, dict) and isinstance(r.get("path", ""), str) for r in v)
        for v in actions.values()
    ):
        raise ValueError("manifest field 'actions' is not a map of record lists")
    if not isinstance(data.get("logs", []), list):
        raise ValueError("manifest field 'logs' is not a list")


class ManifestLockTimeout(RuntimeError):
    """Another live Nexus-Hub run holds the manifest lock past the timeout."""


def _try_lock(fd: int) -> bool:
    """Take an exclusive, non-blocking operating-system lock on ``fd``."""
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock(fd: int) -> None:
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        # The operating system drops the lock when the descriptor closes just
        # below (or when the process ends), so a failed explicit unlock changes nothing.
        pass


@contextmanager
def manifest_lock(path: Path, timeout: float = 30.0):
    """Serialize load-modify-save of one manifest across processes (v4.14.7).

    Holds an operating-system lock (``msvcrt.locking`` on Windows, ``flock``
    elsewhere) on ``<manifest>.lock`` for the duration. The operating system
    releases it when the holding process ends, so a crashed run can never leave
    a stale lock behind and there is no stale-lock guessing, which two runs
    could otherwise both win. The lock file itself is never deleted: removing
    it while another run waits on the old file would let two runs hold
    different files. If a live holder keeps the lock past ``timeout`` seconds
    this raises ``ManifestLockTimeout`` instead of continuing, because two runs
    that each load the manifest and then save it overwrite one another's
    entries, and a manifest that loses a platform's records can no longer prove
    which files Nexus-Hub owns. Waiting and retrying is the safe outcome.
    """
    lock = long_path(path).with_name(Path(path).name + ".lock")
    fd = None
    try:
        lock.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(lock), os.O_RDWR | os.O_CREAT)
    except OSError:
        fd = None  # a read-only location: the save will report its own error
    held = False
    if fd is not None:
        deadline = time.monotonic() + timeout
        while not (held := _try_lock(fd)):
            if time.monotonic() >= deadline:
                os.close(fd)
                raise ManifestLockTimeout(
                    f"{lock} is held by another running Nexus-Hub install or prune. "
                    "Wait for it to finish, then run this command again."
                )
            time.sleep(0.2)
    try:
        yield held
    finally:
        if fd is not None:
            if held:
                _unlock(fd)
            os.close(fd)
