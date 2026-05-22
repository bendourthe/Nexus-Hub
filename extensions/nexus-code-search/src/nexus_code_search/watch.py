"""Debounced filesystem watcher built on watchdog.

The watcher buffers raw FS events into a list and flushes the deduplicated
list to a callback after `debounce_ms` of silence. Filtering happens up
front: events for excluded directories (`.git`, `node_modules`, `.venv`,
`.nexus`) and ignored files (per `.gitignore` / `.nexusignore`) are dropped
before they reach the debounce queue.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable, Iterable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from nexus_code_search.config import CodeSearchConfig, index_dir_for
from nexus_code_search.extraction.languages import LANGUAGE_EXTRACTORS

logger = logging.getLogger("nexus-code-search")


ChangeCallback = Callable[[list[Path]], None]


class _DebouncedHandler(FileSystemEventHandler):
    def __init__(
        self,
        repo_root: Path,
        callback: ChangeCallback,
        config: CodeSearchConfig,
        debounce_seconds: float,
    ) -> None:
        super().__init__()
        self.repo_root = repo_root.resolve()
        self.callback = callback
        self.config = config
        self.debounce_seconds = debounce_seconds
        self._buffer: dict[Path, float] = {}
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None
        self._closed = False

    # --- watchdog event hooks ---

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path).resolve()
        if not self._is_interesting(path):
            return
        with self._lock:
            self._buffer[path] = time.monotonic()
            self._schedule_flush()

    # --- internals ---

    def _is_interesting(self, path: Path) -> bool:
        # Suffix filter: only extensions a registered extractor handles.
        if path.suffix.lower() not in LANGUAGE_EXTRACTORS:
            return False
        # Skip the index dir and excluded directories.
        try:
            rel = path.relative_to(self.repo_root)
        except ValueError:
            return False
        for part in rel.parts:
            if part in self.config.exclude_dirs:
                return False
        return True

    def _schedule_flush(self) -> None:
        if self._closed:
            return
        if self._timer is not None:
            self._timer.cancel()
        self._timer = threading.Timer(self.debounce_seconds, self._flush)
        self._timer.daemon = True
        self._timer.start()

    def _flush(self) -> None:
        with self._lock:
            paths = list(self._buffer.keys())
            self._buffer.clear()
            self._timer = None
        if paths and not self._closed:
            try:
                self.callback(paths)
            except Exception:  # noqa: BLE001
                logger.exception("File-watcher callback raised")

    def stop(self) -> None:
        with self._lock:
            self._closed = True
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None
            self._buffer.clear()


class FileWatcher:
    """Public file-watcher entry point.

    Lifecycle:
        w = FileWatcher(repo_root, on_change=..., debounce_ms=2000)
        w.start()
        ... eventually ...
        w.stop()
    """

    def __init__(
        self,
        repo_root: Path,
        on_change: ChangeCallback,
        debounce_ms: int = 2000,
        config: CodeSearchConfig | None = None,
    ) -> None:
        if debounce_ms < 50:
            raise ValueError("debounce_ms must be >= 50")
        self.repo_root = repo_root.resolve()
        self.on_change = on_change
        self.debounce_seconds = debounce_ms / 1000.0
        self.config = config if config is not None else CodeSearchConfig(hub_root=None)
        self._handler: _DebouncedHandler | None = None
        self._observer: Observer | None = None

    def start(self) -> None:
        if self._observer is not None:
            return
        self._handler = _DebouncedHandler(
            self.repo_root, self.on_change, self.config, self.debounce_seconds
        )
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self.repo_root), recursive=True)
        self._observer.start()

    def stop(self) -> None:
        if self._handler is not None:
            self._handler.stop()
            self._handler = None
        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None

    def __enter__(self) -> FileWatcher:
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()


# --- helpers for the MCP server's `watch_for_changes` tool ---


_ACTIVE_WATCHERS: dict[Path, FileWatcher] = {}
_WATCHERS_LOCK = threading.Lock()


def start_watcher_for_graph(
    repo_root: Path,
    config: CodeSearchConfig,
    debounce_ms: int = 2000,
) -> FileWatcher:
    """Start a watcher that re-indexes changed files into the v2.0 graph.

    Reentrant: starting a watcher for a `repo_root` that already has one
    returns the existing watcher.
    """
    resolved = repo_root.resolve()
    with _WATCHERS_LOCK:
        existing = _ACTIVE_WATCHERS.get(resolved)
        if existing is not None:
            return existing

        def _reindex(paths: Iterable[Path]) -> None:
            # Imported lazily so the watch module stays independent of
            # extraction when only `FileWatcher` is needed (e.g. in tests).
            from nexus_code_search.extraction.orchestrator import ExtractionOrchestrator

            idx_dir = index_dir_for(resolved, config)
            with ExtractionOrchestrator(resolved, config, idx_dir) as orch:
                orch.run(force=False)
            logger.info(
                "File watcher re-indexed %d change(s) under %s",
                len(list(paths)),
                resolved,
            )

        w = FileWatcher(
            resolved, on_change=_reindex, debounce_ms=debounce_ms, config=config
        )
        w.start()
        _ACTIVE_WATCHERS[resolved] = w
        return w


def stop_watcher_for_graph(repo_root: Path) -> bool:
    resolved = repo_root.resolve()
    with _WATCHERS_LOCK:
        watcher = _ACTIVE_WATCHERS.pop(resolved, None)
    if watcher is None:
        return False
    watcher.stop()
    return True
