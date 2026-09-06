"""Relocatable store root and per-store tunables.

The default root is a local, user-scoped path. ``NEXUS_MEMORY_ROOT``
overrides it so the store can sit in a synced folder. A root inside a
git working tree is refused unless ``NEXUS_MEMORY_ALLOW_IN_REPO`` is set.
The read budget is a reading budget: changing it never recomputes stored
data.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path

ENV_ROOT = "NEXUS_MEMORY_ROOT"
ENV_ALLOW_IN_REPO = "NEXUS_MEMORY_ALLOW_IN_REPO"
CONFIG_NAME = "config.json"
MARKER_NAME = ".nexus-memory-store"

# Transport paging defaults match docs/policy/output-truncation-limits.md
# (Phase 1 safe default). Duplicated here so the extension does not import
# repo-level scripts at runtime.
DEFAULT_PAGE_MAX_BYTES = 16_000
DEFAULT_PAGE_MAX_LINES = 256

DEFAULT_RECORD_WIDTH = 1024
DEFAULT_MAX_ENTRY_LENGTH = 512
DEFAULT_READ_BUDGET = 200


@dataclass(frozen=True)
class StoreConfig:
    """Per-store tunables. ``record_width`` is sticky once a log exists."""

    record_width: int = DEFAULT_RECORD_WIDTH
    max_entry_length: int = DEFAULT_MAX_ENTRY_LENGTH
    read_budget: int = DEFAULT_READ_BUDGET
    page_max_bytes: int = DEFAULT_PAGE_MAX_BYTES
    page_max_lines: int = DEFAULT_PAGE_MAX_LINES

    def validate(self) -> None:
        if self.record_width < 32:
            raise ValueError(f"record_width must be >= 32, got {self.record_width}")
        if self.max_entry_length < 1:
            raise ValueError("max_entry_length must be >= 1")
        if self.max_entry_length + 4 > self.record_width:
            raise ValueError(
                "max_entry_length plus the 4-byte length prefix must fit "
                f"in record_width ({self.record_width})"
            )
        if self.read_budget < 1:
            raise ValueError("read_budget must be >= 1")
        if self.page_max_bytes < 1 or self.page_max_lines < 1:
            raise ValueError("paging limits must be >= 1")


class InRepoStoreError(ValueError):
    """The store root sits inside a git working tree and was refused."""


def allow_in_repo() -> bool:
    """Return True when the operator explicitly permits an in-repo root."""
    return os.environ.get(ENV_ALLOW_IN_REPO, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def is_inside_git_worktree(path: Path) -> bool:
    """Return True when *path* (or its parent) is inside a git working tree."""
    target = Path(path)
    try:
        target = target.resolve()
    except OSError:
        return False
    probe = target if target.is_dir() else target.parent
    try:
        result = subprocess.run(
            ["git", "-C", str(probe), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and result.stdout.strip() == "true"


def assert_root_allowed(root: Path) -> None:
    """Refuse a git-worktree root unless ``NEXUS_MEMORY_ALLOW_IN_REPO`` is set."""
    if allow_in_repo():
        return
    if is_inside_git_worktree(root):
        raise InRepoStoreError(
            f"{root} is inside a git working tree. Relocate the store "
            f"outside the repository, or set {ENV_ALLOW_IN_REPO}=1 if you "
            "accept that this log can be committed."
        )


def restrict_private(path: Path) -> None:
    """Best-effort owner-only permissions. POSIX 0700/0600; no-op on failure."""
    try:
        mode = 0o700 if path.is_dir() else 0o600
        os.chmod(path, mode)
    except OSError:
        return


def write_marker(root: Path) -> None:
    """Write the store marker the accidental-commit hook recognizes."""
    marker = Path(root) / MARKER_NAME
    if not marker.is_file():
        marker.write_text("nexus-memory-store\n", encoding="utf-8")
    restrict_private(marker)


def default_store_root() -> Path:
    """Return the user-scoped default, or ``NEXUS_MEMORY_ROOT`` when set.

    The default is never a project directory.
    """
    override = os.environ.get(ENV_ROOT, "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".nexus-hub" / "memory"


def load_config(root: Path) -> StoreConfig:
    """Load ``config.json`` from *root*, or return defaults if it is absent."""
    path = Path(root) / CONFIG_NAME
    if not path.is_file():
        cfg = StoreConfig()
        cfg.validate()
        return cfg
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a JSON object")
    cfg = StoreConfig(
        record_width=int(raw.get("record_width", DEFAULT_RECORD_WIDTH)),
        max_entry_length=int(raw.get("max_entry_length", DEFAULT_MAX_ENTRY_LENGTH)),
        read_budget=int(raw.get("read_budget", DEFAULT_READ_BUDGET)),
        page_max_bytes=int(raw.get("page_max_bytes", DEFAULT_PAGE_MAX_BYTES)),
        page_max_lines=int(raw.get("page_max_lines", DEFAULT_PAGE_MAX_LINES)),
    )
    cfg.validate()
    return cfg


def save_config(root: Path, config: StoreConfig) -> None:
    """Write *config* to ``<root>/config.json`` as UTF-8 JSON."""
    config.validate()
    root = Path(root)
    creating = not (root / CONFIG_NAME).is_file()
    if creating:
        assert_root_allowed(root)
    root.mkdir(parents=True, exist_ok=True)
    restrict_private(root)
    write_marker(root)
    path = root / CONFIG_NAME
    payload = json.dumps(asdict(config), indent=2, sort_keys=True) + "\n"
    _atomic_write_text(path, payload)
    restrict_private(path)


def _atomic_write_text(path: Path, payload: str) -> None:
    """Replace *path* with *payload* atomically.

    ``Path.write_text`` truncates before it writes, so a concurrent reader can
    observe a zero-byte file and fail to parse it. Writing a sibling temp file
    and replacing means a reader sees either the whole old file or the whole
    new one, never a partial state. The temp file is a sibling so the replace
    stays on one filesystem, which is what makes it atomic.
    """
    tmp = path.with_name(f"{path.name}.tmp.{os.getpid()}")
    try:
        tmp.write_text(payload, encoding="utf-8")
        restrict_private(tmp)
        # os.replace is atomic on POSIX and Windows, but on Windows it can
        # raise PermissionError while another process holds the destination
        # open for reading. That window is microseconds, so a short bounded
        # retry closes it without inventing a lock.
        last: OSError | None = None
        for attempt in range(10):
            try:
                os.replace(tmp, path)
                return
            except PermissionError as exc:  # pragma: no cover - Windows-only timing
                last = exc
                time.sleep(0.01 * (attempt + 1))
        raise last if last is not None else OSError(f"could not replace {path}")
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
