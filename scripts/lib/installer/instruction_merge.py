"""Marker-delimited section replacement for shared instruction files.

Background
----------
Nexus-Hub installs to shared, user-owned files like `CLAUDE.md`, `AGENTS.md`,
and `.cursor/rules/*.mdc`. Older installer code overwrote those files wholesale,
clobbering any user edits. CodeGraph's `targets/shared.ts` (functions
`replaceOrAppendMarkedSection` and `removeMarkedSection`) defines the canonical
algorithm:

  1. If the file does not exist, create it with the marker-wrapped block.
  2. If the file exists and contains both markers, replace the slice between
     them with the new body.
  3. If the file exists and contains a literal pre-marker section header
     (e.g., the v2.1 `## Nexus-Hub` heading), migrate it inline to the marker
     block.
  4. Otherwise, append the marker-wrapped block after a single trailing blank
     line.

Byte-identical re-runs return the `unchanged` action so the runner can short-
circuit per the new WriteResult vocabulary (see scripts/lib/integrations/result.py).

The module is stdlib-only on purpose: this helper runs under the same Python
3.10+ baseline as the rest of the registry runner.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator, Optional

if TYPE_CHECKING:
    from scripts.lib.integrations.result import Action, FileAction

DEFAULT_START_MARKER = "<!-- NEXUS_HUB_START -->"
DEFAULT_END_MARKER = "<!-- NEXUS_HUB_END -->"
_BOM = b"\xef\xbb\xbf"
#: Seconds a writer waits for another cooperating installer's per-target lock.
LOCK_TIMEOUT_SECONDS = 30.0


def _file_action(file_path: Path, action: Action) -> FileAction:
    """Create a result without importing the integration registry at load time."""
    from scripts.lib.integrations.result import FileAction

    return FileAction(path=str(file_path), action=action)


def _build_block(body: str, start_marker: str, end_marker: str) -> str:
    """Return the marker-wrapped block exactly as it should appear on disk.

    Body is stripped of leading/trailing whitespace so the wrapping is
    canonical (one newline between marker and body on each side).
    """
    return f"{start_marker}\n{body.strip()}\n{end_marker}\n"


#: Bounded retry for a rename another process transiently blocks. On Windows
#: `os.replace` fails with PermissionError while an on-access scanner or indexer
#: holds a handle to the just-written destination, and the same call succeeds
#: once it is released (the v4.9 BG-1 class, handled the same way in
#: `nexus_hub_cli._replace_path_with_retry`). The last attempt re-raises, so a
#: permanent permission problem still reaches the caller.
_REPLACE_RETRY_DELAYS = (0.05, 0.15, 0.3, 0.5)


def _replace_with_retry(src: Path, dst: Path) -> None:
    for delay in _REPLACE_RETRY_DELAYS:
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            time.sleep(delay)
    os.replace(src, dst)


def _atomic_replace_bytes(file_path: Path, content: bytes) -> None:
    """Replace one existing file atomically with bytes staged beside it."""

    mode = file_path.stat().st_mode
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=file_path.parent, prefix=f".{file_path.name}.", delete=False
        ) as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.chmod(temporary, mode)
        _replace_with_retry(temporary, file_path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def merge_marker_section(
    file_path: Path,
    body: str,
    start_marker: str = DEFAULT_START_MARKER,
    end_marker: str = DEFAULT_END_MARKER,
    legacy_header: Optional[str] = None,
    dry_run: bool = False,
) -> FileAction:
    """Merge `body` into `file_path` as a marker-delimited section.

    Parameters
    ----------
    file_path : Path
        Destination file. Created if missing.
    body : str
        The Markdown body to wrap between the markers. Leading/trailing
        whitespace is stripped.
    start_marker / end_marker : str
        HTML-comment markers used to bracket the Nexus-Hub-owned section.
        Defaults to `<!-- NEXUS_HUB_START -->` / `<!-- NEXUS_HUB_END -->`.
    legacy_header : str, optional
        If supplied, an existing literal header (e.g., `## Nexus-Hub`) without
        markers is migrated inline. Migration runs only when both markers are
        absent AND the header is present.
    dry_run : bool
        When True, no bytes are written; the returned FileAction still reflects
        the action that would happen.

    Returns
    -------
    FileAction
        action="created"   - file did not exist
        action="updated"   - file existed; the marker block was rewritten or
                              the legacy header was migrated, OR the block was
                              appended
        action="unchanged" - the resulting bytes match the existing bytes
    """
    existing = file_path.read_bytes() if file_path.exists() else None
    new_bytes = render_marker_merge(existing, body, start_marker, end_marker, legacy_header)
    if existing is None:
        if not dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(new_bytes)
        return _file_action(file_path, "created")
    if existing == new_bytes:
        return _file_action(file_path, "unchanged")
    if not dry_run:
        _atomic_replace_bytes(file_path.resolve(), new_bytes)
    return _file_action(file_path, "updated")


def render_marker_merge(
    existing: Optional[bytes],
    body: str,
    start_marker: str = DEFAULT_START_MARKER,
    end_marker: str = DEFAULT_END_MARKER,
    legacy_header: Optional[str] = None,
) -> bytes:
    """Return the bytes `merge_marker_section` would write, without touching disk.

    Byte-preserving: a leading UTF-8 BOM is kept, a file that uses CRLF for
    every line ending keeps CRLF (the new block included), and every byte
    outside the replaced region is carried over verbatim. Mixed line endings
    are left exactly as found. Raises UnicodeDecodeError on non-UTF-8 input,
    matching the previous `read_text` behavior.
    """
    new_block = _build_block(body, start_marker, end_marker)
    if existing is None:
        return new_block.encode("utf-8")
    bom = existing.startswith(_BOM)
    text = existing[len(_BOM):].decode("utf-8") if bom else existing.decode("utf-8")
    crlf = "\r\n" in text and "\n" not in text.replace("\r\n", "")
    if crlf:
        text = text.replace("\r\n", "\n")
    if start_marker in text and end_marker in text:
        new_text = _replace_between_markers(text, new_block, start_marker, end_marker)
    elif legacy_header and legacy_header in text:
        new_text = _migrate_legacy_header(text, legacy_header, new_block)
    else:
        new_text = _append_block(text, new_block)
    if crlf:
        new_text = new_text.replace("\n", "\r\n")
    return (_BOM if bom else b"") + new_text.encode("utf-8")


def remove_marker_section(
    file_path: Path,
    start_marker: str = DEFAULT_START_MARKER,
    end_marker: str = DEFAULT_END_MARKER,
    dry_run: bool = False,
) -> FileAction:
    """Strip the marker-delimited section out of `file_path`.

    Returns:
        action="not-found" - file does not exist
        action="kept"      - file exists but contains no marker pair
        action="removed"   - the marker block was removed; file rewritten
                              without it. If the file becomes empty (only the
                              block was present), the file itself is deleted.
        action="unchanged" - file exists, markers present, but resulting bytes
                              match the existing bytes (edge case where the
                              block was already a no-op).
    """
    if not file_path.exists():
        return _file_action(file_path, "not-found")
    existing = file_path.read_text(encoding="utf-8")
    if start_marker not in existing or end_marker not in existing:
        return _file_action(file_path, "kept")
    new_text = _strip_between_markers(existing, start_marker, end_marker)
    new_bytes = new_text.encode("utf-8")
    if existing.encode("utf-8") == new_bytes:
        return _file_action(file_path, "unchanged")
    if not new_text.strip():
        if not dry_run:
            file_path.unlink(missing_ok=True)
        return _file_action(file_path, "removed")
    if not dry_run:
        _atomic_replace_bytes(file_path, new_bytes)
    return _file_action(file_path, "removed")


def _replace_between_markers(
    text: str, new_block: str, start_marker: str, end_marker: str
) -> str:
    # Use rindex so the marker block can quote itself in body text without
    # accidentally truncating at the first nested mention. (A shared instruction
    # template may literally reference both markers when explaining the merge
    # mechanism to the user, e.g. an inline "between <!-- NEXUS:BEGIN --> and
    # <!-- NEXUS:END -->" note in the body.)
    start = text.index(start_marker)
    end = text.rindex(end_marker, start) + len(end_marker)
    # Preserve the trailing newline after the end marker if it existed; otherwise
    # add one so the new block is line-terminated.
    trailing = ""
    rest = text[end:]
    if rest.startswith("\r\n"):
        trailing = "\r\n"
    elif rest.startswith("\n"):
        trailing = "\n"
    head = text[:start]
    tail = text[end + len(trailing) :]
    # `new_block` already ends with \n; preserve the trailing newline that was
    # there before so the file does not grow / shrink an extra blank line.
    block = new_block if new_block.endswith("\n") else new_block + "\n"
    return f"{head}{block.rstrip()}{trailing}{tail}"


def _migrate_legacy_header(text: str, legacy_header: str, new_block: str) -> str:
    """Replace the legacy header section with the marker block.

    The legacy section runs from `legacy_header` to either the next top-level
    heading at the same depth or end of file. We detect depth by counting
    leading `#` characters on the header line.
    """
    idx = text.index(legacy_header)
    header_line_end = text.index("\n", idx) if "\n" in text[idx:] else len(text)
    # Determine heading depth (number of leading `#`).
    raw_header = text[idx:header_line_end].lstrip()
    depth = 0
    for ch in raw_header:
        if ch == "#":
            depth += 1
        else:
            break
    # Find next heading at the same depth or shallower.
    cursor = header_line_end + 1
    next_idx = len(text)
    while cursor < len(text):
        line_end = text.index("\n", cursor) if "\n" in text[cursor:] else len(text)
        line = text[cursor:line_end].lstrip()
        if line.startswith("#"):
            other_depth = 0
            for ch in line:
                if ch == "#":
                    other_depth += 1
                else:
                    break
            if other_depth <= depth:
                next_idx = cursor
                break
        cursor = line_end + 1
    head = text[:idx].rstrip()
    tail = text[next_idx:].lstrip("\n")
    block = new_block.rstrip("\n")
    if head:
        return f"{head}\n\n{block}\n" + (f"\n{tail}" if tail else "")
    return f"{block}\n" + (f"\n{tail}" if tail else "")


def _strip_between_markers(text: str, start_marker: str, end_marker: str) -> str:
    # Mirror the rindex semantics from _replace_between_markers so the
    # uninstall path agrees with the install path on where the block ends.
    start = text.index(start_marker)
    end = text.rindex(end_marker, start) + len(end_marker)
    # Eat one trailing newline that bracketed the block.
    if end < len(text) and text[end] == "\n":
        end += 1
    head = text[:start].rstrip("\n")
    tail = text[end:].lstrip("\n")
    if head and tail:
        return f"{head}\n\n{tail}"
    if head:
        return f"{head}\n"
    if tail:
        return tail
    return ""


def _append_block(existing: str, new_block: str) -> str:
    trimmed = existing.rstrip()
    block = new_block.rstrip("\n")
    if not trimmed:
        return f"{block}\n"
    return f"{trimmed}\n\n{block}\n"


# ---------------------------------------------------------------------------
# Cleanup-aware shared-instruction owner (v4.13.3 Phase 4)
#
# Every marker-merged instruction writer goes through `merge_instruction`. It
# serializes cooperating installer writers with a per-target lock, reads the
# target ONCE, keeps a verified content-addressed backup before any write, and
# removes a candidate Legacy Instruction Block only when the install context
# carries that span's `consent_sha256` from the current bytes. Detection itself
# lives in `legacy_instruction_block`; the report the user copies a consent
# token from is built by `collect_legacy_report` AFTER every writer finished, so
# a token printed by one install matches the next unchanged install even when
# several integrations write the same file.
#
# Residual risk (documented, not solved): a writer that ignores the lock can
# still change the file between the final re-hash and the atomic replace. The
# verified pre-write backup is the recovery path for that race.
# ---------------------------------------------------------------------------


@dataclass
class LegacyRun:
    """Per-invocation bookkeeping shared by every merge in one install."""

    owner: str = ""
    touched: dict[str, str] = field(default_factory=dict)
    consumed: set[str] = field(default_factory=set)
    backups: list[tuple[str, str, str]] = field(default_factory=list)
    notes: list[tuple[str, str]] = field(default_factory=list)


def legacy_run(ctx: Any) -> Optional[LegacyRun]:
    """Return (creating on first use) the run state carried on `ctx`."""
    if ctx is None:
        return None
    run = getattr(ctx, "legacy_run", None)
    if run is None:
        run = LegacyRun()
        try:
            ctx.legacy_run = run
        except AttributeError:
            return None
    return run


def state_root(ctx: Any) -> Path:
    """`~/.nexus-hub/state`, following an explicit global install target."""
    if getattr(ctx, "scope", "") == "global" and getattr(ctx, "global_root", None) is not None:
        return Path(ctx.global_root) / ".nexus-hub" / "state"
    return Path.home() / ".nexus-hub" / "state"


class LockTimeout(Exception):
    """Another cooperating installer held the target lock for too long."""


@contextmanager
def _target_lock(lock_dir: Path, target: Path, timeout: float) -> Iterator[bool]:
    """Hold an exclusive cross-process lock for `target`; yield False when no lock dir is usable.

    The lock is an OS advisory lock (fcntl / msvcrt) on a per-target file under
    the state directory, so it is released automatically if the process dies.
    """
    try:
        lock_dir.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:32]
        fd = os.open(lock_dir / f"{digest}.lock", os.O_RDWR | os.O_CREAT, 0o600)
    except OSError:
        yield False
        return
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                if os.name == "nt":
                    import msvcrt

                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise LockTimeout(str(target)) from None
                time.sleep(0.05)
        try:
            yield True
        finally:
            if os.name == "nt":
                import msvcrt

                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def backup_bytes(backup_dir: Path, target: Path, content: bytes) -> Optional[Path]:
    """Keep one owner-only, content-addressed copy of `content`; None on any failure.

    The name is `<sha256>.<basename>`, so identical bytes are stored once and a
    backup is never rotated, overwritten, or deleted by the installer. The copy
    is re-read and hash-verified before it counts.
    """
    digest = hashlib.sha256(content).hexdigest()
    dst = backup_dir / f"{digest}.{target.name}"
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(backup_dir, 0o700)
        except OSError:
            pass
        if not dst.exists():
            staging = backup_dir / f".{dst.name}.{os.getpid()}.tmp"
            fd = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(staging, dst)
            finally:
                staging.unlink(missing_ok=True)
        if hashlib.sha256(dst.read_bytes()).hexdigest() != digest:
            return None
    except OSError:
        return None
    return dst


def _note(run: Optional[LegacyRun], message: str) -> None:
    if run is not None:
        run.notes.append((run.owner, message))


def merge_instruction(
    file_path: Path,
    body: str,
    *,
    ctx: Any,
    start_marker: str = DEFAULT_START_MARKER,
    end_marker: str = DEFAULT_END_MARKER,
    legacy_header: Optional[str] = None,
) -> FileAction:
    """Merge `body` into a shared instruction file through the one cleanup-aware owner.

    Same result vocabulary as `merge_marker_section`, plus a `kept` refusal
    (`refuse-concurrent-change`, `refuse-lock-timeout`) when writing would lose
    another writer's update. Without matching consent nothing outside the
    managed block changes; with it, exactly the consented spans are removed and
    the managed block is rendered from the same snapshot in one atomic write.
    """
    from scripts.lib.installer.legacy_instruction_block import detect_bytes

    dry_run = bool(getattr(ctx, "dry_run", False))
    run = legacy_run(ctx)
    consents = frozenset(getattr(ctx, "legacy_removal_hashes", None) or ())
    if run is not None:
        run.touched[str(file_path)] = run.owner
    if not file_path.exists():
        if not dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        return merge_marker_section(
            file_path, body, start_marker, end_marker, legacy_header, dry_run=dry_run
        )
    real = file_path.resolve()
    root = state_root(ctx)
    try:
        with _target_lock(root / "locks", real, LOCK_TIMEOUT_SECONDS) as locked:
            snapshot = real.read_bytes()
            spans = []
            detection = detect_bytes(real, snapshot)
            if detection.status == "ok":
                spans = detection.spans
            removal = [s for s in spans if s.consent_sha256 in consents]
            if removal and not locked:
                _note(run, f"legacy removal skipped for {file_path}: no usable lock under {root}")
                removal = []
            base = snapshot
            for span in sorted(removal, key=lambda s: s.start_byte, reverse=True):
                base = base[: span.start_byte] + base[span.end_byte :]
            new = render_marker_merge(base, body, start_marker, end_marker, legacy_header)
            if dry_run:
                if run is not None:
                    run.consumed.update(s.consent_sha256 for s in removal)
                return _file_action(file_path, "unchanged" if new == snapshot else "updated")
            if new == snapshot and not spans:
                return _file_action(file_path, "unchanged")
            backup = backup_bytes(root / "backups", real, snapshot) if locked else None
            if backup is None:
                _note(run, f"no verified backup of {file_path} under {root / 'backups'}; legacy removal skipped")
                if removal:
                    removal = []
                    new = render_marker_merge(snapshot, body, start_marker, end_marker, legacy_header)
            elif run is not None:
                run.backups.append((run.owner, str(file_path), str(backup)))
            if new == snapshot:
                return _file_action(file_path, "unchanged")
            if real.read_bytes() != snapshot:
                return _refusal(file_path, "refuse-concurrent-change")
            _atomic_replace_bytes(real, new)
            if run is not None:
                run.consumed.update(s.consent_sha256 for s in removal)
            return _file_action(file_path, "updated")
    except LockTimeout:
        return _refusal(file_path, "refuse-lock-timeout")


def _refusal(file_path: Path, reason: str) -> FileAction:
    from scripts.lib.integrations.result import FileAction

    return FileAction(path=str(file_path), action="kept", reason=reason)


@dataclass(frozen=True)
class LegacyCandidate:
    owner: str
    path: str
    start_line: int
    end_line: int
    line_count: int
    tokens: int
    consent_sha256: str
    diff_path: Optional[str]


def _estimate_tokens(text: str) -> int:
    try:
        from scripts.check_memory_integration_budget import estimate_tokens
    except ImportError:
        return len(text.split())
    return estimate_tokens(text)


def _write_diff(diff_dir: Path, path: str, lines: list[str], start: int, consent: str) -> Optional[str]:
    body = [f"--- {path}", f"+++ {path} (legacy span removed)", f"@@ -{start},{len(lines)} +{start},0 @@"]
    body.extend(f"-{line}" for line in lines)
    dst = diff_dir / f"{consent}.diff"
    try:
        diff_dir.mkdir(parents=True, exist_ok=True)
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(body) + "\n")
    except OSError:
        return None
    return str(dst)


def collect_legacy_report(ctx: Any) -> tuple[list[LegacyCandidate], list[str]]:
    """Detect every touched instruction file from its final on-disk bytes.

    Returns the candidates (each with the consent token valid for the next
    unchanged install and, outside a dry run, an owner-only diff file) and the
    supplied consent tokens that matched no span and so removed nothing.
    """
    from scripts.lib.installer.legacy_instruction_block import detect

    run = legacy_run(ctx)
    if run is None:
        return [], []
    dry_run = bool(getattr(ctx, "dry_run", False))
    diff_dir = state_root(ctx) / "legacy-candidates"
    candidates: list[LegacyCandidate] = []
    for path, owner in run.touched.items():
        detection = detect(Path(path))
        if detection.status != "ok" or not detection.spans:
            continue
        lines = Path(path).read_bytes().decode("utf-8-sig").splitlines()
        for span in detection.spans:
            chunk = lines[span.start_line - 1 : span.end_line]
            candidates.append(
                LegacyCandidate(
                    owner=owner,
                    path=path,
                    start_line=span.start_line,
                    end_line=span.end_line,
                    line_count=span.line_count,
                    tokens=_estimate_tokens("\n".join(chunk)),
                    consent_sha256=span.consent_sha256,
                    diff_path=None
                    if dry_run
                    else _write_diff(diff_dir, path, chunk, span.start_line, span.consent_sha256),
                )
            )
    supplied = frozenset(getattr(ctx, "legacy_removal_hashes", None) or ())
    return candidates, sorted(supplied - run.consumed)
