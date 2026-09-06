"""Exclusive write lock that works on POSIX and Windows.

POSIX uses ``fcntl.flock``. Windows uses ``msvcrt.locking``. Either
import is selected at runtime. If both fail, a directory-create lock is
the fallback so a machine with neither primitive still serializes writers
rather than interleaving records.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from types import TracebackType


class FileLock:
    """Exclusive lock around one store file.

    The lock file is a sibling of the log (``entries.lock``), not the log
    itself, so the locked region and the append stream stay independent.
    """

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._fh: object | None = None
        self._dir_lock: Path | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            if self._acquire_msvcrt():
                return
        else:
            if self._acquire_fcntl():
                return
        self._acquire_mkdir()

    def release(self) -> None:
        fh = self._fh
        self._fh = None
        if fh is not None:
            try:
                if sys.platform == "win32":
                    import msvcrt

                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            except (OSError, ImportError, ValueError):
                pass
            try:
                fh.close()
            except OSError:
                pass
        if self._dir_lock is not None:
            try:
                self._dir_lock.rmdir()
            except OSError:
                pass
            self._dir_lock = None

    def __enter__(self) -> FileLock:
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.release()

    def _acquire_fcntl(self) -> bool:
        try:
            import fcntl
        except ImportError:
            return False
        fh = open(self.path, "a+b")
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        except OSError:
            fh.close()
            return False
        self._fh = fh
        return True

    def _acquire_msvcrt(self) -> bool:
        try:
            import msvcrt
        except ImportError:
            return False
        fh = open(self.path, "a+b")
        try:
            if fh.seek(0, os.SEEK_END) == 0:
                fh.write(b"0")
                fh.flush()
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        except OSError:
            fh.close()
            return False
        self._fh = fh
        return True

    def _acquire_mkdir(self) -> None:
        lock_dir = Path(str(self.path) + ".d")
        deadline = time.time() + 30
        while True:
            try:
                lock_dir.mkdir()
                self._dir_lock = lock_dir
                return
            except FileExistsError:
                if time.time() > deadline:
                    raise TimeoutError(f"timed out waiting for {lock_dir}")
                time.sleep(0.05)
