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
            "logs": self._logs,
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
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "InstallManifest":
        m = cls()
        m._tracked = dict(data.get("tracked", {}))
        m._shared = dict(data.get("shared", {}))
        m._org_tracked = dict(data.get("org_tracked", {}))
        m._org_shared = dict(data.get("org_shared", {}))
        m._logs = list(data.get("logs", []))
        m._actions = dict(data.get("actions", {}))
        selection = data.get("selection")
        m._selection = dict(selection) if isinstance(selection, dict) else None
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
