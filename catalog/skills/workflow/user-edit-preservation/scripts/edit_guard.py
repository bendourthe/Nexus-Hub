#!/usr/bin/env python3
"""Remember what an agent last saw of a file, and detect when the user changed it since.

A cross-session store keyed by the canonical path records the agent's last-known state
of every file it reads, writes, or changes by command: a content fingerprint and (for
non-secret files under a size cap) a copy of the file as the agent left it. Office files
are fingerprinted by their content parts only, so AutoSave and sync rewriting
`docProps/*` metadata is not a change. Standard library only; `python-pptx`,
`python-docx`, and `openpyxl` are optional and only improve `diff` output.

Subcommands and exit codes:

    record <path> [--from read|write|command]   0 recorded; 3 refused (changed since the last record)
    check  <path>                               0 unchanged; 3 changed; 4 no record; 5 cannot verify; 2 error
    diff   <path>                               0 shown (and remembered for accept); 4 no record; 2 error
    accept <path>                               0 re-baselined; 3 refused (no diff of this exact content)
    log    [--since ISO]                        prints accepts, for the end-of-task summary
    purge  [--path PATH]                        deletes records and copies

`accept` is the only way to release a block. It works only after `diff` ran on that path
for the same session (`--session` or NEXUS_EDIT_GUARD_SESSION; without one, within 30
minutes), and only while the file still has the exact content that `diff` showed.
Records older than 30 days are pruned on every run.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import fnmatch
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import zipfile
from pathlib import Path

EXIT_OK, EXIT_ERROR, EXIT_CHANGED, EXIT_NO_RECORD, EXIT_CANNOT_VERIFY = 0, 2, 3, 4, 5
RETENTION_DAYS = 30
COPY_CAP_BYTES = 10 * 1024 * 1024
DIFF_WINDOW_SECONDS = 30 * 60
OFFICE_EXTS = {".pptx", ".pptm", ".docx", ".docm", ".xlsx", ".xlsm", ".potx", ".dotx", ".xltx"}
METADATA_PREFIX = "docProps/"
SECRET_PATTERNS = (".env", ".env.*", "*.pem", "*.key", "id_*", "credentials*", "*.kdbx", "*.p12", "*.pfx")
SYNC_ROOT_NAMES = re.compile(r"^(onedrive( - .+)?|dropbox( \(.+\))?|sharepoint.*)$", re.IGNORECASE)
# Windows attributes of a OneDrive "online-only" placeholder: reading it would download it.
PLACEHOLDER_ATTRS = 0x00001000 | 0x00040000 | 0x00400000  # OFFLINE | RECALL_ON_OPEN | RECALL_ON_DATA_ACCESS
CHUNK = 1024 * 1024


class GuardError(Exception):
    """Exit 2: an input or store problem; never reported as 'unchanged'."""


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


# --- paths --------------------------------------------------------------------


def _long_path(path: str) -> str:
    """Expand Windows 8.3 short names (PROGRA~1) so one file has one key."""
    if os.name != "nt":
        return path
    import ctypes

    buf = ctypes.create_unicode_buffer(32768)
    size = ctypes.windll.kernel32.GetLongPathNameW(path, buf, len(buf))
    return buf.value if 0 < size < len(buf) else path


def canonical(path: str | Path) -> str:
    """Absolute, links and junctions resolved, 8.3 expanded, '/' separators, case-folded where the OS is."""
    resolved = os.path.realpath(os.path.abspath(str(path)))
    resolved = _long_path(resolved).replace("\\", "/")
    if os.name == "nt" or sys.platform == "darwin":
        resolved = resolved.casefold()
    return resolved


def key_for(path: str | Path) -> str:
    return hashlib.sha256(canonical(path).encode("utf-8")).hexdigest()


def is_secret_looking(path: Path) -> bool:
    name = path.name.lower()
    return any(fnmatch.fnmatch(name, pattern) for pattern in SECRET_PATTERNS)


def _synced_roots() -> list[str]:
    roots = [os.environ.get(v, "") for v in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer")]
    return [canonical(r) for r in roots if r]


def in_synced_root(path: Path) -> bool:
    canon = canonical(path)
    if any(canon == r or canon.startswith(r + "/") for r in _synced_roots()):
        return True
    return any(SYNC_ROOT_NAMES.match(part) for part in Path(os.path.realpath(str(path))).parts)


def in_git_repo(path: Path) -> bool:
    for parent in [path, *path.parents]:
        if (parent / ".git").exists():
            return True
    return False


# --- store ----------------------------------------------------------------------


def store_dir() -> Path:
    """The store root, refusing any location that would leak copies of user files."""
    raw = os.environ.get("NEXUS_EDIT_GUARD_DIR") or str(Path.home() / ".nexus-hub" / "cache" / "edit-guard")
    root = Path(os.path.abspath(raw))
    cwd = Path(os.path.realpath(os.getcwd()))
    real = Path(os.path.realpath(str(root)))
    if real == cwd or cwd in real.parents:
        raise GuardError(f"refusing a store inside the current workspace: {root}")
    if in_git_repo(real):
        raise GuardError(f"refusing a store inside a git repository: {root}")
    if in_synced_root(real):
        raise GuardError(f"refusing a store inside a synced drive (OneDrive, SharePoint, Dropbox): {root}")
    for sub in (root, root / "records", root / "copies"):
        sub.mkdir(parents=True, exist_ok=True)
        _owner_only(sub, directory=True)
    return root


def _owner_only(path: Path, *, directory: bool) -> None:
    """Mode 0700/0600, and an owner-rights-only DACL on Windows, where chmod cannot restrict reads.

    Mirrors `_windows_owner_only` in scripts/lib/installer/instruction_merge.py; this
    script runs from an installed skill folder and cannot import the repository.
    """
    os.chmod(path, 0o700 if directory else 0o600)
    if os.name != "nt":
        return
    import ctypes
    from ctypes import wintypes

    security = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = security.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(wintypes.LPVOID),
                        ctypes.POINTER(wintypes.DWORD)]
    convert.restype = wintypes.BOOL
    get_dacl = security.GetSecurityDescriptorDacl
    get_dacl.argtypes = [wintypes.LPVOID, ctypes.POINTER(wintypes.BOOL), ctypes.POINTER(wintypes.LPVOID),
                         ctypes.POINTER(wintypes.BOOL)]
    get_dacl.restype = wintypes.BOOL
    set_acl = security.SetNamedSecurityInfoW
    set_acl.argtypes = [wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.LPVOID,
                        wintypes.LPVOID, wintypes.LPVOID]
    set_acl.restype = wintypes.DWORD
    kernel.LocalFree.argtypes = [wintypes.HLOCAL]
    kernel.LocalFree.restype = wintypes.HLOCAL
    descriptor = wintypes.LPVOID()
    flags = "OICI" if directory else ""
    if not convert(f"D:P(A;{flags};FA;;;OW)", 1, ctypes.byref(descriptor), None):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        present, defaulted, dacl = wintypes.BOOL(), wintypes.BOOL(), wintypes.LPVOID()
        if not get_dacl(descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)) \
                or not present.value or not dacl:
            raise GuardError("cannot build an owner-only ACL for the edit-guard store")
        status = set_acl(str(path), 1, 0x80000004, None, None, dacl, None)
        if status:
            raise GuardError(f"cannot restrict the edit-guard store ACL (error {status})")
    finally:
        kernel.LocalFree(descriptor)


def _write_private(path: Path, data: bytes) -> None:
    staging = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(staging, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        _owner_only(staging, directory=False)
        os.replace(staging, path)
    finally:
        staging.unlink(missing_ok=True)


def load_record(root: Path, key: str) -> dict | None:
    path = root / "records" / f"{key}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GuardError(f"corrupt edit-guard record {path.name}: {exc}") from exc


def save_record(root: Path, key: str, record: dict) -> None:
    _write_private(root / "records" / f"{key}.json", json.dumps(record, indent=1).encode("utf-8"))


def append_log(root: Path, entry: dict) -> None:
    entry = {"at": now().isoformat(timespec="seconds"), **entry}
    path = root / "log.jsonl"
    existing = path.read_bytes() if path.is_file() else b""
    _write_private(path, existing + (json.dumps(entry) + "\n").encode("utf-8"))


def prune(root: Path) -> int:
    cutoff = now() - dt.timedelta(days=RETENTION_DAYS)
    removed = 0
    for record_path in (root / "records").glob("*.json"):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
            stamp = dt.datetime.fromisoformat(record["at"])
        except (OSError, ValueError, KeyError):
            continue
        if stamp < cutoff:
            _delete(root, record_path.stem)
            removed += 1
    return removed


def _delete(root: Path, key: str) -> None:
    (root / "records" / f"{key}.json").unlink(missing_ok=True)
    (root / "copies" / f"{key}.bin").unlink(missing_ok=True)


# --- fingerprints ---------------------------------------------------------------


def _stream_sha(stream) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(CHUNK), b""):
        digest.update(chunk)
    return digest.hexdigest()


def _regular_file(path: Path) -> os.stat_result:
    """The file's stat, refusing a missing path, a non-regular file, or a link at the leaf.

    Links in parent directories (a redirected Documents folder) are resolved by
    `canonical`; a symlink or junction AT the path is refused, because following it
    would guard a different file than the one named.
    """
    try:
        leaf = os.lstat(path)
    except FileNotFoundError as exc:
        raise GuardError(f"no such file: {path}") from exc
    except OSError as exc:
        raise GuardError(f"cannot stat {path}: {exc}") from exc
    if stat.S_ISLNK(leaf.st_mode) or getattr(leaf, "st_file_attributes", 0) & 0x400:  # REPARSE_POINT
        raise GuardError(f"refusing a symlink or junction: {path}")
    try:
        info = os.stat(path)
    except FileNotFoundError as exc:
        raise GuardError(f"no such file: {path}") from exc
    except OSError as exc:
        raise GuardError(f"cannot stat {path}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise GuardError(f"not a regular file: {path}")
    return info


def is_placeholder(info: os.stat_result) -> bool:
    return bool(getattr(info, "st_file_attributes", 0) & PLACEHOLDER_ATTRS)


def fingerprint(path: Path) -> dict:
    """Streamed content fingerprint; Office files by content part, excluding docProps/*."""
    info = _regular_file(path)
    if path.suffix.lower() in OFFICE_EXTS:
        try:
            with zipfile.ZipFile(path) as archive:
                parts = {}
                for member in sorted(archive.namelist()):
                    if member.endswith("/") or member.startswith(METADATA_PREFIX):
                        continue
                    with archive.open(member) as stream:
                        parts[member] = _stream_sha(stream)
        except (zipfile.BadZipFile, OSError, KeyError) as exc:
            raise GuardError(f"unreadable Office archive {path}: {exc}") from exc
        combined = hashlib.sha256(json.dumps(parts, sort_keys=True).encode("utf-8")).hexdigest()
        return {"kind": "office", "sha256": combined, "parts": parts, "size": info.st_size}
    with open(path, "rb") as stream:
        return {"kind": "file", "sha256": _stream_sha(stream), "size": info.st_size}


def open_or_conflicting(path: Path) -> list[str]:
    """Office lock files and OneDrive conflict copies beside the file."""
    found = []
    lock = path.with_name("~$" + path.name[2:] if len(path.name) > 2 else "~$" + path.name)
    for candidate in {lock, path.with_name("~$" + path.name)}:
        if candidate.exists():
            found.append(f"lock file {candidate.name}")
    machine = re.compile(r"^[A-Z0-9][A-Z0-9-]{2,30}$")
    local = (os.environ.get("COMPUTERNAME") or "").upper()
    for sibling in path.parent.glob(f"{path.stem}-*{path.suffix}"):
        token = sibling.stem[len(path.stem) + 1:]
        if sibling != path and (machine.match(token) or (local and token.upper() == local)):
            found.append(f"conflict copy {sibling.name}")
    return sorted(found)


def summarize(old: dict, new: dict) -> str:
    if old.get("kind") == "office" and new.get("kind") == "office":
        a, b = old.get("parts", {}), new.get("parts", {})
        changed = sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))
        return "changed parts: " + ", ".join(changed[:12]) + (" ..." if len(changed) > 12 else "")
    return f"content changed (size {old.get('size')} -> {new.get('size')} bytes)"


# --- diff -----------------------------------------------------------------------


def _office_text(path: Path, suffix: str) -> dict[str, list[str]] | None:
    """Per-unit text (slide, paragraph block, or sheet), or None when the library is absent.

    `suffix` comes from the ORIGINAL file: the stored copy is named `<key>.bin`.
    """
    suffix = suffix.lower()
    try:
        if suffix in {".pptx", ".pptm", ".potx"}:
            from pptx import Presentation

            units = {}
            for number, slide in enumerate(Presentation(str(path)).slides, start=1):
                units[f"slide {number}"] = _slide_lines(slide)
            return units
        if suffix in {".docx", ".docm", ".dotx"}:
            import docx

            document = docx.Document(str(path))
            lines = [p.text for p in document.paragraphs]
            for table in document.tables:
                lines += [" | ".join(c.text for c in row.cells) for row in table.rows]
            return {"document": lines}
        if suffix in {".xlsx", ".xlsm", ".xltx"}:
            import openpyxl

            book = openpyxl.load_workbook(str(path), data_only=False, read_only=True)
            return {f"sheet {ws.title}": [f"{c.coordinate}={c.value!r}" for row in ws.iter_rows() for c in row
                                          if c.value is not None] for ws in book.worksheets}
    except ImportError as exc:
        print(f"note: install {exc.name} for a readable diff (pip install python-pptx python-docx openpyxl)")
        return None
    return None


def _slide_lines(slide) -> list[str]:
    lines: list[str] = []

    def walk(shapes) -> None:
        for shape in shapes:
            if getattr(shape, "shape_type", None) == 6 and hasattr(shape, "shapes"):  # group
                walk(shape.shapes)
            if getattr(shape, "has_text_frame", False) and shape.text_frame.text:
                lines.append(shape.text_frame.text)
            if getattr(shape, "has_table", False):
                lines.extend(" | ".join(c.text for c in row.cells) for row in shape.table.rows)
    walk(slide.shapes)
    if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text:
        lines.append("notes: " + slide.notes_slide.notes_text_frame.text)
    return lines


def render_diff(path: Path, record: dict, current: dict, copy: Path | None) -> str:
    if record["sha256"] == current["sha256"]:
        return "unchanged since the agent last saw this file"
    out: list[str] = []
    if copy is not None and copy.is_file():
        if current["kind"] == "office":
            before, after = _office_text(copy, path.suffix), _office_text(path, path.suffix)
            if before is not None and after is not None:
                if len(before) != len(after):
                    out.append(f"unit count changed: {len(before)} -> {len(after)}")
                for unit in sorted(set(before) | set(after), key=_unit_order):
                    delta = list(difflib.unified_diff(before.get(unit, []), after.get(unit, []),
                                                      f"{unit} (agent)", f"{unit} (now)", lineterm="", n=0))
                    out += delta
        else:
            try:
                before_text = copy.read_text(encoding="utf-8").splitlines()
                after_text = path.read_text(encoding="utf-8").splitlines()
                out += difflib.unified_diff(before_text, after_text, "agent version", "current", lineterm="")
            except UnicodeDecodeError:
                out.append("binary file: content changed")
    else:
        out.append("no stored copy (secret-looking path or over the size cap): only the fingerprint is known")
    if current["kind"] == "office" and not any(line.startswith(("+", "-")) for line in out
                                                 if not line.startswith(("+++", "---"))):
        out.append("non-text change: " + summarize(record, current))
    elif current["kind"] == "office":
        out.append(summarize(record, current))
    return "\n".join(out)


def _unit_order(unit: str) -> tuple:
    match = re.search(r"(\d+)$", unit)
    return (0, int(match.group(1))) if match else (1, unit)


# --- commands -------------------------------------------------------------------


def session_id(args) -> str:
    return getattr(args, "session", None) or os.environ.get("NEXUS_EDIT_GUARD_SESSION", "")


def cmd_record(args, root: Path) -> int:
    path = Path(args.path)
    key = key_for(path)
    existing = load_record(root, key)
    current = fingerprint(path)
    if existing and existing["sha256"] != current["sha256"] and args.source == "read":
        print(f"refused: {path} changed since the agent last recorded it; run diff and review before re-recording")
        append_log(root, {"event": "record-refused", "path": canonical(path)})
        return EXIT_CHANGED
    copy_note = None
    copy_path = root / "copies" / f"{key}.bin"
    if is_secret_looking(path):
        copy_note = "secret-looking path: no copy kept"
        copy_path.unlink(missing_ok=True)
    elif current["size"] > COPY_CAP_BYTES:
        copy_note = f"over the {COPY_CAP_BYTES // (1024 * 1024)} MB copy cap: no copy kept"
        copy_path.unlink(missing_ok=True)
    else:
        staging = copy_path.with_name(f".{copy_path.name}.{os.getpid()}.tmp")
        shutil.copyfile(path, staging)
        _owner_only(staging, directory=False)
        os.replace(staging, copy_path)
    record = {
        "path": canonical(path), "display": str(path), "seq": (existing or {}).get("seq", 0) + 1,
        "from": args.source, "at": now().isoformat(timespec="seconds"), "copy": copy_note is None,
        "copy_note": copy_note, **current,
    }
    save_record(root, key, record)
    print(f"recorded {path} (seq {record['seq']}, from {args.source})" + (f"; {copy_note}" if copy_note else ""))
    return EXIT_OK


def cmd_check(args, root: Path) -> int:
    path = Path(args.path)
    key = key_for(path)
    record = load_record(root, key)
    if record is None:
        print(f"no record: the agent never recorded {path}")
        return EXIT_NO_RECORD
    info = _regular_file(path)
    if is_placeholder(info):
        print(f"cannot verify: {path} is an online-only placeholder (not downloaded to check it)")
        append_log(root, {"event": "check", "result": "cannot-verify", "path": canonical(path)})
        return EXIT_CANNOT_VERIFY
    others = open_or_conflicting(path)
    if others:
        print(f"changed: open or conflicting copy ({', '.join(others)})")
        append_log(root, {"event": "check", "result": "open-or-conflicting", "path": canonical(path)})
        return EXIT_CHANGED
    current = fingerprint(path)
    if current["sha256"] == record["sha256"]:
        print(f"unchanged: {path}")
        append_log(root, {"event": "check", "result": "unchanged", "path": canonical(path)})
        return EXIT_OK
    kind = "non-text change" if current["kind"] == "office" and _text_equal(root, key, path) else "changed"
    print(f"{kind}: {path} differs from the agent's last-known state; {summarize(record, current)}")
    append_log(root, {"event": "check", "result": "changed", "path": canonical(path)})
    return EXIT_CHANGED


def _text_equal(root: Path, key: str, path: Path) -> bool:
    copy = root / "copies" / f"{key}.bin"
    if not copy.is_file():
        return False
    before, after = _office_text(copy, path.suffix), _office_text(path, path.suffix)
    return before is not None and before == after


def cmd_diff(args, root: Path) -> int:
    path = Path(args.path)
    key = key_for(path)
    record = load_record(root, key)
    if record is None:
        print(f"no record: the agent never recorded {path}")
        return EXIT_NO_RECORD
    current = fingerprint(path)
    copy = root / "copies" / f"{key}.bin"
    print(render_diff(path, record, current, copy if record.get("copy") else None))
    record["diffed"] = {"session": session_id(args), "sha256": current["sha256"],
                        "at": now().isoformat(timespec="seconds")}
    save_record(root, key, record)
    append_log(root, {"event": "diff", "path": canonical(path), "session": session_id(args)})
    return EXIT_OK


def cmd_accept(args, root: Path) -> int:
    path = Path(args.path)
    key = key_for(path)
    record = load_record(root, key)
    if record is None:
        print(f"no record: the agent never recorded {path}")
        return EXIT_NO_RECORD
    diffed = record.get("diffed")
    if not diffed:
        print(f"refused: run `edit_guard.py diff {path}` and review the user's changes before accepting")
        return EXIT_CHANGED
    session = session_id(args)
    age = (now() - dt.datetime.fromisoformat(diffed["at"])).total_seconds()
    same_session = diffed["session"] == session if (diffed["session"] or session) else age <= DIFF_WINDOW_SECONDS
    if not same_session:
        print("refused: the diff was not shown in this session; run diff again")
        return EXIT_CHANGED
    current = fingerprint(path)
    if current["sha256"] != diffed["sha256"]:
        print("refused: the file changed after the diff was shown; run diff again")
        return EXIT_CHANGED
    args.source = "write"
    record.pop("diffed", None)
    save_record(root, key, record)
    status = cmd_record(args, root)
    append_log(root, {"event": "accept", "path": canonical(path), "display": str(path), "session": session})
    print(f"accepted: {path} re-baselined after review")
    return status


def cmd_log(args, root: Path) -> int:
    path = root / "log.jsonl"
    since = dt.datetime.fromisoformat(args.since) if args.since else None
    if not path.is_file():
        return EXIT_OK
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if entry.get("event") != "accept":
            continue
        if since and dt.datetime.fromisoformat(entry["at"]) < since:
            continue
        print(f"{entry['at']} accepted {entry.get('display', entry['path'])}")
    return EXIT_OK


def cmd_purge(args, root: Path) -> int:
    if args.path:
        _delete(root, key_for(args.path))
        print(f"purged {args.path}")
    else:
        for record_path in (root / "records").glob("*.json"):
            _delete(root, record_path.stem)
        (root / "log.jsonl").unlink(missing_ok=True)
        print("purged every edit-guard record")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", help="session id; defaults to NEXUS_EDIT_GUARD_SESSION")
    sub = parser.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record")
    record.add_argument("path")
    record.add_argument("--from", dest="source", choices=("read", "write", "command"), default="write")
    for name in ("check", "diff", "accept"):
        sub.add_parser(name).add_argument("path")
    log = sub.add_parser("log")
    log.add_argument("--since")
    purge = sub.add_parser("purge")
    purge.add_argument("--path")
    args = parser.parse_args(argv)
    handlers = {"record": cmd_record, "check": cmd_check, "diff": cmd_diff, "accept": cmd_accept,
                "log": cmd_log, "purge": cmd_purge}
    try:
        root = store_dir()
        prune(root)
        return handlers[args.command](args, root)
    except GuardError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
