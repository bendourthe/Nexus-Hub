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
from pathlib import Path
from typing import Dict, List, Optional


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
        self._logs: List[str] = []
        # v2.3.0 additive: per-integration list of recorded action dicts
        # `{path, action, sha256, mtime}`. Populated by `record_actions()` from
        # the runner after each integration install. Stored separately so
        # legacy callers / tests that only touch `_tracked` keep working.
        self._actions: Dict[str, List[Dict[str, object]]] = {}

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

        Each entry is stored as `{path, action, sha256, mtime}`. Hash and
        mtime are captured at record time; `doctor` compares them later to
        detect drift. Replacement (not append) so successive installs of the
        same integration in one invocation do not pile up duplicate records.
        """
        captured: List[Dict[str, object]] = []
        for fa in file_actions:
            path = Path(fa.path)
            captured.append(
                {
                    "path": fa.path,
                    "action": fa.action,
                    "sha256": _hash_path(path),
                    "mtime": _mtime(path),
                }
            )
        self._actions[integration_key] = captured
        self._logs.append(
            f"[{integration_key}] record-actions: {len(captured)} entries"
        )

    def actions_for(self, integration_key: str) -> List[Dict[str, object]]:
        """Return the recorded action entries for `integration_key`."""
        return list(self._actions.get(integration_key, []))

    def all_action_keys(self) -> List[str]:
        """Return every integration key with at least one recorded action."""
        return sorted(self._actions.keys())

    def to_dict(self) -> Dict[str, object]:
        return {
            "tracked": self._tracked,
            "shared": self._shared,
            "logs": self._logs,
            "actions": self._actions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "InstallManifest":
        m = cls()
        m._tracked = dict(data.get("tracked", {}))
        m._shared = dict(data.get("shared", {}))
        m._logs = list(data.get("logs", []))
        m._actions = dict(data.get("actions", {}))
        return m

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "InstallManifest":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)
