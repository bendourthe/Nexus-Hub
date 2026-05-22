"""FileWatcher tests (T027)."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from nexus_code_search.watch import FileWatcher


def test_filewatcher_debounces_and_fires_callback(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    fired: list[list[Path]] = []
    event = threading.Event()

    def on_change(paths: list[Path]) -> None:
        fired.append(paths)
        event.set()

    watcher = FileWatcher(tmp_path, on_change=on_change, debounce_ms=200)
    watcher.start()
    try:
        # Modify the file twice quickly; the debounce should collapse this
        # into a single callback invocation.
        (tmp_path / "a.py").write_text("x = 2\n", encoding="utf-8")
        time.sleep(0.05)
        (tmp_path / "a.py").write_text("x = 3\n", encoding="utf-8")
        assert event.wait(timeout=5.0), "watcher callback did not fire"
    finally:
        watcher.stop()

    assert len(fired) == 1
    flat = {p.name for batch in fired for p in batch}
    assert "a.py" in flat


def test_filewatcher_filters_unsupported_extensions(tmp_path: Path) -> None:
    fired: list[list[Path]] = []
    event = threading.Event()

    def on_change(paths: list[Path]) -> None:
        fired.append(paths)
        event.set()

    watcher = FileWatcher(tmp_path, on_change=on_change, debounce_ms=200)
    watcher.start()
    try:
        (tmp_path / "ignore.txt").write_text("hello\n", encoding="utf-8")
        # Wait longer than debounce; callback must NOT fire.
        assert not event.wait(timeout=1.0), "watcher fired on unsupported extension"
    finally:
        watcher.stop()

    assert fired == []


def test_filewatcher_filters_excluded_dirs(tmp_path: Path) -> None:
    nm = tmp_path / "node_modules"
    nm.mkdir()
    fired: list[list[Path]] = []
    event = threading.Event()

    def on_change(paths: list[Path]) -> None:
        fired.append(paths)
        event.set()

    watcher = FileWatcher(tmp_path, on_change=on_change, debounce_ms=200)
    watcher.start()
    try:
        (nm / "vendor.ts").write_text("export const x = 1;\n", encoding="utf-8")
        assert not event.wait(timeout=1.0), "watcher fired on excluded dir"
    finally:
        watcher.stop()

    assert fired == []


def test_filewatcher_rejects_invalid_debounce() -> None:
    with pytest.raises(ValueError):
        FileWatcher(Path("."), on_change=lambda p: None, debounce_ms=10)
