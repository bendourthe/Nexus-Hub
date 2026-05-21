"""Install manifest -- tracks the files each integration creates.

The manifest is a JSON file written to `<target_root>/.nexus-hub/install-manifest.json`
that maps integration key -> list of created paths. Teardown reads this file to
know what to remove.

The manifest is intentionally simple (no schema versioning yet). v2.2.0+ MAY
introduce a schema version field if the format evolves.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


class InstallManifest:
    """Per-invocation manifest of files created by each integration.

    The manifest persists to disk on demand via `save()`. Teardown reads it
    back with `load()`.
    """

    def __init__(self) -> None:
        self._tracked: Dict[str, List[str]] = {}
        self._shared: Dict[str, List[str]] = {}
        self._logs: List[str] = []

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

    def to_dict(self) -> Dict[str, object]:
        return {
            "tracked": self._tracked,
            "shared": self._shared,
            "logs": self._logs,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "InstallManifest":
        m = cls()
        m._tracked = dict(data.get("tracked", {}))
        m._shared = dict(data.get("shared", {}))
        m._logs = list(data.get("logs", []))
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
