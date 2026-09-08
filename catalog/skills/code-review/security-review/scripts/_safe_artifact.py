#!/usr/bin/env python3
"""Physical containment and lifecycle primitives for security-review artifacts.

Everything this audit pipeline reads comes from a tree it does not own, and
everything it writes must land somewhere it does own. Those are two different
problems and this module is the single owner of both, so the rules live in one
place instead of being re-derived per caller.

The reading rules exist because a path is not a file. Between deciding a path is
safe and opening it, the path can be replaced by a link pointing somewhere else
entirely, and the classic consequence is a "read the target's source" step that
reads `/etc/shadow` or a credential file outside the authorized root. So a read
here validates the ROOT, every ANCESTOR, and the LEAF, opens without following
links where the platform allows it, and then re-checks that the thing it opened
is still the thing it validated.

## Platform guarantee, stated rather than assumed

POSIX has `O_NOFOLLOW`, so a link at the leaf makes the open itself fail: that is
PREVENTION. Windows does not expose an equivalent flag through `os`, so the same
call there validates before opening and re-validates file identity afterwards:
that is DETECTION. A swap is caught and refused, but it is caught after the open
rather than prevented by it.

This asymmetry is real and is not hidden behind a uniform-looking API.
`platform_guarantee()` reports which of the two a caller is getting, callers that
record provenance must record it, and the residual Windows window is tracked as a
known gap rather than described as closed.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import sys
import tempfile
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

#: Ceiling for a single artifact read. A caller may lower it, never raise it.
MAX_ARTIFACT_BYTES = 8 * 1024 * 1024

#: Streaming chunk. Bounded so a large file never becomes one huge allocation.
_CHUNK = 1024 * 1024

#: Owner-only, for every directory and staging file this module creates.
_OWNER_ONLY_DIR = 0o700
_OWNER_ONLY_FILE = 0o600

#: Marks a temporary root as created by THIS module, so cleanup can refuse to
#: delete a directory it did not make. Cleanup that trusts its argument is how a
#: cleanup step becomes an arbitrary-deletion primitive.
_SENTINEL_NAME = ".nexus-security-review-owned"

_HAS_NOFOLLOW = hasattr(os, "O_NOFOLLOW")
_OWNED_ROOTS: dict[str, tuple[tuple[int, int], str]] = {}


class UnsafeArtifactError(ValueError):
    """Raised when a path or artifact fails a containment or identity check."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _reject(code: str, message: str) -> None:
    # Target-derived paths and exception text are never diagnostic payloads.
    raise UnsafeArtifactError(code, code)


def platform_guarantee() -> str:
    """Return `prevention` or `detection` for leaf-link handling on this host."""
    return "prevention" if _HAS_NOFOLLOW else "detection"


def require_race_safe_primitives() -> None:
    """Fail closed when neither prevention nor detection is available.

    Detection needs stable file identity from `lstat` and `fstat`. Without it
    there is no way to tell whether the opened file is the validated one, and the
    correct response is to refuse rather than to read hopefully.
    """
    probe = Path(tempfile.gettempdir())
    try:
        info = os.lstat(probe)
    except OSError as exc:
        _reject("no_race_safe_primitives", f"cannot lstat {probe}: {exc}")
        return
    if getattr(info, "st_ino", 0) == 0 and getattr(info, "st_dev", 0) == 0:
        _reject(
            "no_race_safe_primitives",
            "this platform reports no usable file identity, so a post-open swap "
            "could not be detected",
        )


# --------------------------------------------------------------------------
# Link, reparse, and hard-link classification
# --------------------------------------------------------------------------


def is_link_like(path: Path) -> bool:
    """Whether `path` is a symlink, a junction, or any other reparse point.

    Deliberately broader than a junction-only check: for a security boundary the
    question is whether the name can redirect elsewhere, and every reparse tag
    can, including tags that did not exist when this code was written.
    """
    try:
        info = path.lstat()
    except OSError:
        return False
    if stat.S_ISLNK(info.st_mode):
        return True
    attributes = getattr(info, "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(reparse_flag and attributes & reparse_flag)


def _identity(info: os.stat_result) -> tuple[int, int]:
    return (getattr(info, "st_dev", 0), getattr(info, "st_ino", 0))


# --------------------------------------------------------------------------
# Containment
# --------------------------------------------------------------------------


def assert_contained(root: Path, target: Path) -> Path:
    """Return `target` proven to sit inside `root`, or raise.

    Both sides are resolved before comparison, because a containment check on
    unresolved paths is satisfied by `root/../../etc/passwd`.
    """
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as exc:
        _reject("root_unresolvable", f"cannot resolve root {root}: {exc}")
        raise  # unreachable, keeps type checkers honest
    try:
        resolved_target = target.resolve(strict=False)
    except OSError as exc:
        _reject("target_unresolvable", f"cannot resolve {target}: {exc}")
        raise

    if resolved_target != resolved_root and resolved_root not in resolved_target.parents:
        _reject(
            "outside_root",
            f"{resolved_target} is outside the authorized root {resolved_root}",
        )
    return resolved_target


def assert_no_reparse_in_chain(root: Path, target: Path) -> Path:
    """Reject a reparse point at the root, at any ancestor, or at the leaf.

    Checking only the leaf is the common mistake. A link one directory UP
    redirects every path beneath it, so a leaf-only check proves nothing about
    where the bytes actually come from.

    The chain is walked over the path AS SUPPLIED, deliberately BEFORE any
    resolution. Resolving first destroys the very evidence this check looks for:
    `resolve()` follows the link and hands back the real location, so a chain
    walk over the resolved path sees only genuine directories and reports clean.
    An earlier version of this function did exactly that, and a junction whose
    target happened to sit inside the root sailed through. Containment is
    therefore checked LAST, once the chain is proven link-free and resolution can
    no longer be redirected.
    """
    absolute_root = Path(os.path.abspath(root))
    for ancestor in [*reversed(absolute_root.parents), absolute_root]:
        if is_link_like(ancestor):
            _reject("root_is_link", "authorized root or ancestor is a reparse point")
    resolved_root = absolute_root.resolve(strict=True)

    if target.is_absolute():
        try:
            # Against the root AS SUPPLIED, not the resolved one. The two can be
            # different spellings of the same directory (an 8.3 short name such
            # as BEDOUR~1 versus its long form, or a differing case), and mixing
            # them makes relpath emit a spurious `..` that reads as an escape.
            # Target and root always arrive from the same caller in the same
            # spelling, so comparing like with like is what keeps this honest.
            relative = Path(os.path.relpath(target, root))
        except ValueError as exc:
            # Different drive on Windows; there is no relative path at all.
            _reject("outside_root", f"{target} shares no root with {resolved_root}: {exc}")
            raise
    else:
        relative = target

    if ".." in relative.parts:
        # A lexical escape, caught before any filesystem call can follow it.
        _reject("outside_root", f"{target} escapes the authorized root lexically")

    current = resolved_root
    for part in relative.parts:
        current = current / part
        if is_link_like(current):
            _reject(
                "link_in_chain",
                f"{current} is a link or reparse point inside the authorized root",
            )

    # Returned so callers never recompute the effective path. A caller that
    # re-derived it from a RELATIVE target would resolve it against the process
    # working directory instead of the root, which silently points the read
    # somewhere else entirely.
    return assert_contained(resolved_root, current)


# --------------------------------------------------------------------------
# Contained reads
# --------------------------------------------------------------------------


def _open_no_follow(path: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    if _HAS_NOFOLLOW:
        flags |= os.O_NOFOLLOW
    try:
        return os.open(path, flags)
    except OSError as exc:
        _reject("unopenable", f"cannot open {path}: {exc}")
        raise


def open_contained_bytes(
    root: Path, target: Path, max_bytes: int = MAX_ARTIFACT_BYTES
) -> bytes:
    """Read one contained regular file, refusing links, hard links, and swaps."""
    require_race_safe_primitives()
    assert_no_reparse_in_chain(root, root)
    target_path = target if target.is_absolute() else root / target
    with _directory_guard(target_path.parent):
        return _read_contained_bytes(root, target, max_bytes)


@contextmanager
def _directory_guard(directory: Path) -> Iterator[int | None]:
    """Hold directory identities throughout an operation, refusing reparses.

    Windows handles omit delete sharing so ancestors cannot be renamed while
    open. POSIX descriptors and before/after identity checks detect replacement.
    """
    absolute = Path(os.path.abspath(directory))
    paths = [*reversed(absolute.parents), absolute]
    observed = []
    handles = []
    close = None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        close = kernel.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        close.restype = wintypes.BOOL
    try:
        for path in paths:
            if is_link_like(path):
                _reject("link_in_chain", "directory is a reparse point")
            info = path.lstat()
            if not stat.S_ISDIR(info.st_mode):
                _reject("not_directory", "ancestor is not a directory")
            if os.name == "nt":
                handle = create(str(path), 0x80000000, 3, None, 3, 0x02200000, None)
                if handle == ctypes.c_void_p(-1).value:
                    _reject("no_race_safe_primitives", "directory cannot be locked")
                handles.append(handle)
            else:
                flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                descriptor = os.open(path, flags)
                handles.append(descriptor)
                if _identity(os.fstat(descriptor)) != _identity(info):
                    _reject("ancestor_swap", "ancestor changed during open")
            observed.append((path, _identity(info)))
        for path, identity in observed:
            if is_link_like(path) or _identity(path.lstat()) != identity:
                _reject("ancestor_swap", "ancestor identity changed")
        yield None if os.name == "nt" else handles[-1]
        for path, identity in observed:
            if is_link_like(path) or _identity(path.lstat()) != identity:
                _reject("ancestor_swap", "ancestor identity changed")
    finally:
        for handle in reversed(handles):
            if close:
                close(handle)
            else:
                os.close(handle)


def _read_contained_bytes(
    root: Path, target: Path, max_bytes: int, *, digest_only: bool = False,
    prefix_bytes: int | None = None,
) -> bytes | tuple[str, int]:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 0 <= max_bytes <= MAX_ARTIFACT_BYTES:
        _reject("invalid_byte_limit", "invalid byte limit")
    contained = assert_no_reparse_in_chain(root, target)

    try:
        before = os.lstat(contained)
    except OSError as exc:
        # A missing or unreachable path must surface as a stable code like every
        # other rejection here. Letting OSError escape would hand the caller an
        # error it cannot record as a reason code, and would look like a crash
        # rather than a refusal.
        raise UnsafeArtifactError(
            "unstattable", "cannot stat supplied artifact"
        ) from exc
    if not stat.S_ISREG(before.st_mode):
        _reject("not_regular_file", f"{contained} is not a regular file")
    if getattr(before, "st_nlink", 1) > 1:
        # A hard link has no distinguishable "real" path, so an alias outside the
        # authorized root reads identical bytes while defeating containment.
        _reject("hard_linked", f"{contained} has {before.st_nlink} links")
    if before.st_size > max_bytes:
        _reject(
            "artifact_too_large",
            f"{contained} is {before.st_size} bytes, over the {max_bytes} limit",
        )

    descriptor = _open_no_follow(contained)
    try:
        opened = os.fstat(descriptor)
        if _identity(opened) != _identity(before):
            _reject(
                "post_open_swap",
                f"{contained} was replaced between validation and open",
            )
        if not stat.S_ISREG(opened.st_mode):
            _reject("not_regular_file", f"{contained} is not a regular file")
        if getattr(opened, "st_nlink", 1) > 1:
            _reject("hard_linked", f"{contained} gained a second link before the read")

        assert_no_reparse_in_chain(root, target)

        chunks: list[bytes] = []
        hasher = hashlib.sha256() if digest_only else None
        total = 0
        while True:
            read_ceiling = min(max_bytes, prefix_bytes) if prefix_bytes is not None else max_bytes
            if total >= read_ceiling:
                break
            chunk = os.read(descriptor, min(_CHUNK, read_ceiling - total))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                _reject(
                    "artifact_too_large",
                    f"{contained} exceeded the {max_bytes} limit while reading",
                )
            if hasher is not None:
                hasher.update(chunk)
            else:
                chunks.append(chunk)
    finally:
        os.close(descriptor)

    after = os.lstat(contained)
    if (_identity(after) != _identity(before) or after.st_size != before.st_size
            or after.st_mtime_ns != before.st_mtime_ns or after.st_ctime_ns != before.st_ctime_ns):
        _reject("post_open_swap", f"{contained} was replaced during the read")
    return (hasher.hexdigest(), total) if hasher is not None else b"".join(chunks)


def peek_contained_bytes(root: Path, target: Path, max_bytes: int, count: int = 64) -> bytes:
    """Read only a bounded classification prefix using the regular read guards."""
    if type(count) is not int or not 0 <= count <= 64:
        _reject("invalid_prefix_limit", "classification prefix exceeds its limit")
    require_race_safe_primitives()
    assert_no_reparse_in_chain(root, root)
    target_path = target if target.is_absolute() else root / target
    with _directory_guard(target_path.parent):
        return _read_contained_bytes(root, target, max_bytes, prefix_bytes=count)


def digest_contained_file(
    root: Path, target: Path, max_bytes: int = MAX_ARTIFACT_BYTES
) -> tuple[str, int]:
    """Return `(sha256_hex, byte_count)` for a contained regular file.

    Only the digest and the size leave this function. Callers record provenance
    from a digest, never from the bytes, so raw content cannot leak into a
    receipt, a log, a fixture, or session history by way of this path.
    """
    require_race_safe_primitives()
    assert_no_reparse_in_chain(root, root)
    target_path = target if target.is_absolute() else root / target
    with _directory_guard(target_path.parent):
        return _read_contained_bytes(root, target, max_bytes, digest_only=True)


# --------------------------------------------------------------------------
# Owned temporary roots
# --------------------------------------------------------------------------


@contextmanager
def owned_temp_root(prefix: str = "nexus-appsec-") -> Iterator[Path]:
    """Create an exclusive owner-only temporary root and remove it afterwards.

    The root carries a sentinel file, which is what lets `cleanup_owned_root`
    prove the directory is one of ours before deleting anything.
    """
    temporary_base = Path(tempfile.gettempdir()).resolve(strict=True)
    root = Path(tempfile.mkdtemp(prefix=prefix, dir=temporary_base))
    try:
        if os.name == "nt":
            _windows_owner_only(root)
        else:
            os.chmod(root, _OWNER_ONLY_DIR)
    except (OSError, UnsafeArtifactError):
        root.rmdir()
        raise
    token = uuid.uuid4().hex
    (root / _SENTINEL_NAME).write_text(token, encoding="ascii")
    _OWNED_ROOTS[str(root)] = (_identity(root.lstat()), token)
    try:
        yield root
    finally:
        cleanup_owned_root(root)


def _windows_owner_only(root: Path) -> None:
    """Apply a protected, inheritable owner-rights DACL using the native API."""
    import ctypes
    from ctypes import wintypes

    security = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = security.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                        ctypes.POINTER(wintypes.LPVOID), ctypes.POINTER(wintypes.DWORD)]
    convert.restype = wintypes.BOOL
    apply = security.SetFileSecurityW
    apply.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID]
    apply.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel.LocalFree.restype = wintypes.HLOCAL
    descriptor = wintypes.LPVOID()
    if not convert("D:P(A;OICI;FA;;;OW)", 1, ctypes.byref(descriptor), None):
        _reject("owner_permissions_unavailable", "cannot construct private permissions")
    try:
        if not apply(str(root), 0x80000004, descriptor):
            _reject("owner_permissions_unavailable", "cannot apply private permissions")
    finally:
        kernel.LocalFree(descriptor)


def cleanup_owned_root(root: Path) -> None:
    """Remove a root this module created, refusing anything it did not.

    Every check here is about refusing to become a general deletion tool: a
    cleanup helper that deletes whatever path it is handed is one bad variable
    away from removing a user's tree.
    """
    if is_link_like(root):
        _reject("cleanup_target_is_link", f"refusing to clean up link {root}")
    if not root.exists():
        _OWNED_ROOTS.pop(str(root), None)
        return
    if not (root / _SENTINEL_NAME).is_file():
        _reject(
            "cleanup_target_not_owned",
            f"{root} has no ownership sentinel, so it was not created here",
        )
    ownership = _OWNED_ROOTS.get(str(root))
    if ownership is None or ownership[0] != _identity(root.lstat()):
        _reject("cleanup_target_not_owned", "no matching process-held ownership")
    temp_root = Path(tempfile.gettempdir()).resolve(strict=True)
    resolved = Path(os.path.abspath(root))
    if resolved == temp_root or temp_root not in resolved.parents:
        _reject(
            "cleanup_target_outside_temp",
            f"{resolved} is not under the system temporary directory",
        )
    with _directory_guard(resolved):
        if _identity(resolved.lstat()) != ownership[0]:
            _reject("cleanup_target_not_owned", "owned root was replaced")
        sentinel = open_contained_bytes(root, root / _SENTINEL_NAME, 64)
        if sentinel != ownership[1].encode("ascii"):
            _reject("cleanup_target_not_owned", "ownership token does not match")
        assert_no_reparse_in_chain(root, root)
        if _identity(resolved.lstat()) != ownership[0]:
            _reject("cleanup_target_not_owned", "owned root was replaced")
        if os.name == "nt":
            # Root and ancestors deny delete sharing for the entire removal.
            for child in resolved.iterdir():
                if is_link_like(child):
                    if child.is_dir():
                        os.rmdir(child)
                    else:
                        child.unlink()
                elif child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        else:
            descriptor = os.open(resolved, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                if _identity(os.fstat(descriptor)) != ownership[0]:
                    _reject("cleanup_target_not_owned", "owned root was replaced")
                for name in os.listdir(descriptor):
                    info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        shutil.rmtree(name, dir_fd=descriptor)
                    else:
                        os.unlink(name, dir_fd=descriptor)
            finally:
                os.close(descriptor)
    # Nonrecursive removal cannot follow a replacement into another tree.
    if is_link_like(resolved) or _identity(resolved.lstat()) != ownership[0]:
        _reject("cleanup_target_not_owned", "owned root was replaced")
    os.rmdir(resolved)
    _OWNED_ROOTS.pop(str(root), None)


# --------------------------------------------------------------------------
# Safe copy and atomic write
# --------------------------------------------------------------------------


def safe_copy_file(
    source_root: Path,
    source: Path,
    destination: Path,
    max_bytes: int = MAX_ARTIFACT_BYTES,
) -> tuple[str, int]:
    """Copy one contained regular file's BYTES into a destination we own.

    Bytes are read through the contained-read path above and written fresh, so
    no link, reparse point, hard link, permission bit, or extended attribute
    from the source survives into the copy. A copy that preserved those would
    carry the source's redirection along with its content.
    """
    payload = open_contained_bytes(source_root, source, max_bytes)
    destination.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_bytes(destination, payload)
    return hashlib.sha256(payload).hexdigest(), len(payload)


def atomic_write_bytes(destination: Path, payload: bytes) -> None:
    """Write `payload` to `destination` atomically, owner-only while staging.

    The staging file is created owner-only rather than at the process umask,
    because `os.replace` carries the SOURCE's mode: a permissive staging mode
    becomes the final file's mode. When the destination already exists its mode
    is reapplied, so a refresh never silently widens or narrows what the user
    chose. This mirrors the convention the installer's own atomic writers use.
    """
    with _directory_guard(destination.parent):
        _atomic_write_bytes(destination, payload)


def _atomic_write_bytes(destination: Path, payload: bytes) -> None:
    if is_link_like(destination):
        _reject("destination_is_link", f"refusing to write through link {destination}")

    staging = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(
        staging,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
        _OWNER_ONLY_FILE,
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            existing_mode = stat.S_IMODE(destination.stat().st_mode)
        except OSError:
            existing_mode = None
        if existing_mode is not None:
            os.chmod(staging, existing_mode)
        os.replace(staging, destination)
        if sys.platform != "win32":
            # Directory fsync makes the rename itself durable. Windows has no
            # equivalent through os, and opening a directory there fails.
            dir_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    finally:
        staging.unlink(missing_ok=True)


@contextmanager
def _durable_directory(directory: Path, guarded_fd: int | None = None) -> Iterator[tuple[object, object]]:
    """Open and prove a directory flush primitive before publishing evidence."""
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        flush = kernel.FlushFileBuffers
        flush.argtypes = [wintypes.HANDLE]
        flush.restype = wintypes.BOOL
        close = kernel.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        handle = create(str(directory), 0xC0000000, 3, None, 3, 0x02200000, None)
        if handle == ctypes.c_void_p(-1).value:
            _reject("directory_sync_unavailable", "cannot open writable directory handle")
        try:
            def sync() -> None:
                if not flush(handle):
                    _reject("directory_sync_unavailable", "directory flush failed")
            sync()
            yield None, sync
        finally:
            close(handle)
    else:
        if guarded_fd is None:
            _reject("directory_sync_unavailable", "verified directory descriptor required")
        os.fsync(guarded_fd)
        yield guarded_fd, lambda: os.fsync(guarded_fd)


def _rename_exclusive(directory_fd: int, source: str, destination: str) -> None:
    """One native rename avoids an interruptible two-link publication state."""
    import ctypes
    import errno

    libc = ctypes.CDLL(None, use_errno=True)
    name, flag = ("renameatx_np", 4) if sys.platform == "darwin" else ("renameat2", 1)
    rename = getattr(libc, name, None)
    if rename is None:
        _reject("exclusive_publish_unavailable", "native no-replace rename unavailable")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    if rename(directory_fd, os.fsencode(source), directory_fd, os.fsencode(destination), flag):
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise FileExistsError("immutable destination exists")
        _reject("exclusive_publish_failed", "native no-replace publication failed")


def sync_contained_directory(root: Path, directory: Path) -> None:
    """Re-flush an existing identical artifact's parent during safe recovery."""
    directory = assert_no_reparse_in_chain(root, directory)
    with _directory_guard(directory) as guarded_fd, _durable_directory(directory, guarded_fd) as (_, sync):
        sync()


def atomic_publish_bytes(root: Path, destination: Path, payload: bytes) -> None:
    """Durably publish one new file; never replace an existing destination.

    Windows uses native MoveFileExW without REPLACE_EXISTING and a writable
    directory flush handle. POSIX uses a verified dirfd-anchored native atomic
    no-replace rename, then fsyncs the directory. Unsupported primitives
    fail closed. An interrupted final artifact is retained for verified recovery.
    """
    require_race_safe_primitives()
    if not isinstance(payload, bytes) or len(payload) > MAX_ARTIFACT_BYTES:
        _reject("invalid_payload", "exclusive publication payload exceeds limit")
    target = assert_no_reparse_in_chain(root, destination)
    with _directory_guard(target.parent) as guarded_fd, _durable_directory(target.parent, guarded_fd) as (directory_fd, sync):
        temporary_name = ".nexus-publish-" + uuid.uuid4().hex + ".tmp"
        temporary = target.parent / temporary_name
        kwargs = {"dir_fd": directory_fd} if directory_fd is not None else {}
        descriptor = os.open(temporary_name if directory_fd is not None else temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), _OWNER_ONLY_FILE, **kwargs)
        try:
            if os.name == "nt":
                _windows_owner_only(temporary)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            if os.name == "nt":
                import ctypes
                from ctypes import wintypes

                move = ctypes.WinDLL("kernel32", use_last_error=True).MoveFileExW
                move.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
                move.restype = wintypes.BOOL
                if not move(str(temporary), str(target), 8):
                    error = ctypes.get_last_error()
                    if error in {80, 183}:
                        raise FileExistsError("immutable destination exists")
                    _reject("exclusive_publish_failed", "native no-replace publication failed")
            else:
                _rename_exclusive(directory_fd, temporary_name, target.name)
            sync()
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if directory_fd is not None:
                try:
                    os.unlink(temporary_name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass
            else:
                temporary.unlink(missing_ok=True)
