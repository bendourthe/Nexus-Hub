#!/usr/bin/env python3
"""Deterministic target-content identity for an authorized analysis root.

The `application_audit` profile can bind a run either to an immutable checkout or
to a complete content manifest. This module produces the second one: the identity
of every in-scope file, plus enough classification to say whether the tree was
clean, dirty, or carrying untracked and submodule state at the moment it was
measured.

Three properties matter more than the field list, and each exists because the
obvious implementation is unsafe.

**Digests, never bytes.** The manifest records a streaming content digest and a
byte count. It never records file content, a config or source snippet, an
absolute path, or a symlink's target text. A manifest is written to disk, quoted
in evidence, and pasted into session history, so anything it carries is
effectively published. Symlink entries bind the target's LENGTH and DIGEST so a
change is still detectable without the text ever appearing.

**Git is invoked as an untrusted-adjacent tool over trusted plumbing only.**
Reading a repository means running git against configuration the repository
controls. Git config can specify hooks, filters, external diff commands, textconv
programs, credential helpers, an fsmonitor, and `include` directives, several of
which execute arbitrary programs. Pointing a stock `git status` at a hostile tree
is therefore closer to running its code than to reading its metadata. So the
executable is resolved from an explicitly trusted absolute path outside the
target, verified to be a regular non-link file, digested and version-recorded,
and invoked from an empty working directory with a minimal environment and an
allowlist of read-only plumbing commands with fixed options, no shell, a timeout,
and an output cap.

**Failure is total.** There is no partial manifest. An unsafe path, a special
file, an identity race, a command timeout, an output overflow, a budget breach,
or an unclassifiable file aborts with no valid output, because a manifest missing
exactly the interesting file is worse than no manifest at all.

When trusted isolation cannot be proven the manifest is still produced, with git
classification explicitly marked unavailable and a stable reason code. That is
the fail-closed direction: no git runs, and nothing pretends the tree was
classified.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import sys
import threading
import unicodedata
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    # Bundled siblings travel with this skill and are imported by name. The path
    # insert is what makes that work both for `python scripts/<name>.py` from an
    # arbitrary directory and for a test harness loading by file location.
    sys.path.insert(0, str(_HERE))

import _safe_artifact as safe

MANIFEST_VERSION = 1

#: Traversal budgets, bound into the manifest so a reader knows what bounded it.
MAX_DEPTH = 32
MAX_FILES = 100_000
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024

#: Per-git-command limits. No git call may hang or flood the parser.
GIT_TIMEOUT_SECONDS = 30
GIT_MAX_OUTPUT_BYTES = 32 * 1024 * 1024

#: Directories never traversed. Generated output and vendored trees carry no
#: audit signal and would dominate every budget above.
IGNORED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".nexus",
        "node_modules",
        "vendor",
        "dist",
        "build",
        "target",
        "out",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        "htmlcov",
        ".coverage",
    }
)

#: Environment names cleared before any git call. The loader group is the one
#: people forget: LD_PRELOAD alone is enough to run attacker code inside git.
_CLEARED_ENVIRONMENT = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_SYSTEM",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_ASKPASS",
    "GIT_SSH",
    "GIT_SSH_COMMAND",
    "GIT_PROXY_COMMAND",
    "GIT_PAGER",
    "GIT_EXTERNAL_DIFF",
    "GIT_ATTR_NOSYSTEM",
    "GIT_NAMESPACE",
    "GIT_TERMINAL_PROMPT",
    "PATH",
    "PATHEXT",
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "LD_AUDIT",
    "DYLD_INSERT_LIBRARIES",
    "DYLD_LIBRARY_PATH",
    "DYLD_FRAMEWORK_PATH",
)

#: Config forced on every invocation, disabling every execution surface git
#: would otherwise take from repository-controlled configuration.
_SAFE_CONFIG = (
    "protocol.ext.allow=never",
    "core.hooksPath=/dev/null",
    "core.fsmonitor=false",
    "core.useBuiltinFSMonitor=false",
    "core.askPass=",
    "core.pager=cat",
    "core.editor=false",
    "core.symlinks=false",
    "core.autocrlf=false",
    "diff.external=",
    "credential.helper=",
    "uploadpad.packObjectsHook=",
    "gc.auto=0",
    "advice.detachedHead=false",
)

#: The only git commands this module may run. Every one is read-only plumbing
#: with fixed options; nothing here writes, fetches, or checks anything out.
# Only these operations run against a sanitized index. No command reads objects,
# target config, submodule configuration, attributes, or a target HEAD file.
_ALLOWED_GIT_COMMANDS: dict[str, tuple[str, ...]] = {
    "version": ("--version",),
    "ls-files-stage": ("ls-files", "--stage", "-z"),
    "untracked": ("ls-files", "--others", "--exclude-standard", "-z"),
    "ignored": ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"),
}


class TargetManifestError(ValueError):
    """Raised when identity cannot be established safely. No partial output."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _reject(code: str, message: str) -> None:
    raise TargetManifestError(code, code)


# --------------------------------------------------------------------------
# Canonical path identity
# --------------------------------------------------------------------------

#: Windows reserved device names. Opening one of these by name talks to a device
#: rather than a file, so they must never enter a manifest as ordinary paths.
_WINDOWS_DEVICES = frozenset(
    {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
     "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
     "LPT6", "LPT7", "LPT8", "LPT9"}
)

# Reject recognizable sensitive values before the path becomes receipt metadata.
# Ordinary credential filenames (for example .env or credentials.json) reveal
# existence only; embedded values and personal addresses must not be emitted.
_SENSITIVE_PATH = re.compile(
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|"
    r"(?:password|secret|token|api[_-]?key|credential)=[^/]+|"
    r"(?:gh[pousr]_[A-Z0-9]{20,}|sk-[A-Z0-9_-]{20,}|AKIA[A-Z0-9]{16})|"
    r"eyJ[A-Z0-9_-]{8,}\.[A-Z0-9_-]{8,}\.[A-Z0-9_-]{8,}", re.IGNORECASE,
)


def canonical_path_identity(relative: Path) -> dict[str, str]:
    """Bind one repository-relative path to a display form and a byte digest.

    Returns an escaped display form plus a digest of the RAW bytes, and fails
    closed rather than emitting a path it cannot represent losslessly.

    The digest is the load-bearing half. POSIX filenames are arbitrary bytes, not
    text, so two visually identical names can differ in bytes and two different
    byte sequences can normalize to the same text. A manifest keyed on the
    display form alone would treat those as one entry, which is exactly the
    collision an attacker wants.
    """
    parts = relative.parts
    if not parts:
        _reject("empty_path", "path has no components")
    if relative.is_absolute():
        _reject("absolute_path", "manifest paths must be repository-relative")

    for part in parts:
        if part in (".", ".."):
            _reject("dot_segment", "path contains a dot segment")
        if "\x00" in part:
            _reject("null_byte_in_path", "path contains a NUL byte")
        if any(ord(character) < 32 or ord(character) == 127 for character in part):
            _reject("control_character_in_path", "path contains a control character")
        if ":" in part:
            # An alternate data stream rides on a colon and reads different bytes
            # than the visible name suggests.
            _reject("alternate_data_stream", "path contains a stream separator")
        if part.endswith((" ", ".")) or any(char in part for char in '<>"|?*'):
            _reject("path_alias_unsupported", "path has platform-dependent spelling")
        if part.split(".")[0].upper() in _WINDOWS_DEVICES:
            _reject("device_name_in_path", f"path component {part!r} names a device")

    text = "/".join(parts)
    if _SENSITIVE_PATH.search(text):
        _reject("sensitive_path_metadata", "path is not safe receipt metadata")
    try:
        raw = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        _reject("unencodable_path", "path is not representable as UTF-8")
        raise

    if raw.decode("utf-8", errors="strict") != text:
        _reject("path_round_trip_failed", "path does not survive a byte round trip")

    return {
        "display": text,
        "byte_digest": hashlib.sha256(raw).hexdigest(),
        "normalization_key": unicodedata.normalize("NFC", text).casefold(),
    }


# --------------------------------------------------------------------------
# Trusted git resolution and isolated invocation
# --------------------------------------------------------------------------


def resolve_trusted_git(
    git_path: Path | None, forbidden_roots: tuple[Path, ...]
) -> dict[str, Any] | None:
    """Verify an explicitly configured git executable, or return None.

    None means "do not classify with git", which is the fail-closed answer. The
    executable is never discovered from `PATH`: a target that can place a file
    named `git` earlier on the search path would otherwise choose the program
    this module runs.
    """
    if git_path is None:
        return None
    candidate = Path(git_path)
    if not candidate.is_absolute():
        return None
    try:
        info = candidate.lstat()
    except OSError:
        return None
    if stat.S_ISLNK(info.st_mode) or safe.is_link_like(candidate):
        # A link could be repointed after verification and before use.
        return None
    if not stat.S_ISREG(info.st_mode):
        return None
    if info.st_nlink != 1:
        return None
    if not os.access(candidate, os.X_OK):
        return None

    try:
        resolved = safe.assert_no_reparse_in_chain(candidate.parent, candidate)
    except (safe.UnsafeArtifactError, OSError):
        return None
    for forbidden in forbidden_roots:
        try:
            forbidden_resolved = forbidden.resolve(strict=True)
        except OSError:
            continue
        if resolved == forbidden_resolved or forbidden_resolved in resolved.parents:
            # An executable inside the tree under audit is target-controlled.
            return None

    try:
        digest, _size = safe.digest_contained_file(resolved.parent, resolved)
    except (OSError, safe.UnsafeArtifactError):
        return None

    return {"path": resolved, "content_digest": digest}


#: Deliberately SET on every call, and therefore never subject to the clear
#: list below. An earlier version applied these first and then popped every name
#: in `_CLEARED_ENVIRONMENT`, which contains two of them, so the hardening
#: silently deleted its own `GIT_TERMINAL_PROMPT` and `GIT_CONFIG_NOSYSTEM`.
#: Order matters here: clear what might be inherited, then apply what we mean.
_FORCED_ENVIRONMENT = {
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_ATTR_NOSYSTEM": "1",
    "GIT_FLUSH": "1",
    "LC_ALL": "C",
}


def _git_environment() -> dict[str, str]:
    """A minimal allowlisted environment with no inherited search paths."""
    environment: dict[str, str] = {}
    # Obtain the OS directory from the OS itself, never from target-controlled
    # environment text. Windows needs it to locate its system components.
    if os.name == "nt":
        import ctypes

        buffer = ctypes.create_unicode_buffer(32768)
        length = ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer))
        if not length or length >= len(buffer):
            _reject("git_environment_unavailable", "OS directory could not be established")
        environment["SystemRoot"] = buffer.value

    for cleared in _CLEARED_ENVIRONMENT:
        environment.pop(cleared, None)

    # Applied LAST so the clear list can never remove them.
    environment.update(_FORCED_ENVIRONMENT)
    environment.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull})
    return environment


def run_git(
    git: dict[str, Any], command_key: str, target_root: Path, working_directory: Path
) -> bytes:
    """Run one allowlisted read-only plumbing command and return raw stdout."""
    if command_key not in _ALLOWED_GIT_COMMANDS:
        _reject("git_command_not_allowed", f"{command_key} is not an allowlisted command")

    argv: list[str] = [str(git["path"])]
    for setting in _SAFE_CONFIG:
        argv.extend(["-c", setting])
    if command_key != "version":
        metadata = git.get("sanitized_metadata")
        if not isinstance(metadata, Path):
            _reject("git_metadata_unsanitized", "sanitized metadata is required")
        argv.extend(["--git-dir", str(metadata), "--work-tree", str(target_root)])
    argv.extend(_ALLOWED_GIT_COMMANDS[command_key])

    try:
        process = subprocess.Popen(
            argv,
            cwd=str(working_directory),
            env=_git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )
    except OSError as exc:
        raise TargetManifestError("git_unrunnable", "cannot run trusted git") from exc
    outputs: list[bytearray] = [bytearray(), bytearray()]
    overflow = threading.Event()

    def drain(stream: Any, output: bytearray) -> None:
        with stream:
            while chunk := stream.read(65536):
                if len(output) + len(chunk) > GIT_MAX_OUTPUT_BYTES:
                    overflow.set()
                    process.kill()
                    return
                output.extend(chunk)

    readers = [threading.Thread(target=drain, args=(stream, output))
               for stream, output in zip((process.stdout, process.stderr), outputs)]
    for reader in readers:
        reader.start()
    try:
        process.wait(timeout=GIT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.wait()
        raise TargetManifestError("git_timeout", "trusted git exceeded its deadline") from exc
    finally:
        for reader in readers:
            reader.join()
    if overflow.is_set():
        _reject("git_output_overflow", "trusted git exceeded its output budget")
    if process.returncode:
        _reject("git_command_failed", "trusted git command failed")
    return bytes(outputs[0])


def _parse_nul_fields(payload: bytes) -> list[bytes]:
    """Split NUL-delimited git output as BYTES.

    NUL delimiting plus byte parsing is the only combination that survives a
    filename containing a newline, a quote, or invalid UTF-8. Git's default
    output quotes such names, and a text-mode line split silently mis-parses
    them, which is a filename-controlled parser bug.
    """
    return [field for field in payload.split(b"\x00") if field]


# --------------------------------------------------------------------------
# Manifest construction
# --------------------------------------------------------------------------


def _classify_with_git(
    git: dict[str, Any], target_root: Path, working_directory: Path,
    authorized_root: Path | None = None,
    metadata_roots: tuple[Path, ...] = (),
    scope: tuple[str, ...] = (),
) -> dict[str, Any]:
    # The version is recorded alongside the content digest because the digest
    # alone identifies the bytes without saying what they are. A reader
    # reconciling two manifests taken months apart needs to know whether a
    # classification difference came from the tree or from a git upgrade.
    boundary = authorized_root or target_root
    metadata, metadata_boundary, common, common_boundary = _metadata_directory(target_root, boundary, metadata_roots)
    snapshot = working_directory / "metadata"
    snapshot.mkdir(mode=0o700)
    (snapshot / "objects").mkdir(mode=0o700)
    (snapshot / "refs").mkdir(mode=0o700)
    (snapshot / "info").mkdir(mode=0o700)
    (snapshot / "hooks").mkdir(mode=0o700)
    (snapshot / "config").write_bytes(b"")
    (snapshot / "HEAD").write_bytes(b"ref: refs/heads/isolated\n")
    index = b""
    if (metadata / "index").exists():
        index = safe.open_contained_bytes(metadata_boundary, metadata / "index", 8 * 1024 * 1024)
        safe.atomic_write_bytes(snapshot / "index", index)
    for candidate in metadata.glob("sharedindex.*"):
        if not re.fullmatch(r"sharedindex\.[0-9a-f]{40,64}", candidate.name):
            _reject("git_index_ambiguous", "unrecognized shared index")
        safe.safe_copy_file(metadata_boundary, candidate, snapshot / candidate.name)
    if (common / "info/exclude").exists():
        safe.safe_copy_file(common_boundary, common / "info/exclude", snapshot / "info/exclude")
    head = _head_identity(metadata, metadata_boundary, common, common_boundary)
    isolated_git = {**git, "sanitized_metadata": snapshot}
    version = run_git(isolated_git, "version", target_root, working_directory)
    staged = run_git(isolated_git, "ls-files-stage", target_root, working_directory)
    untracked_output = run_git(isolated_git, "untracked", target_root, working_directory)
    ignored_output = run_git(isolated_git, "ignored", target_root, working_directory)
    dirty: set[str] = set()
    tracked: list[str] = []
    submodules: list[dict[str, Any]] = []
    aliases: dict[str, str] = {}
    for field in _parse_nul_fields(staged):
        header, separator, path_bytes = field.partition(b"\t")
        fields = header.split(b" ")
        if not separator or len(fields) != 3 or fields[2] != b"0":
            _reject("git_index_ambiguous", "index entry is malformed or unmerged")
        name = _git_path(path_bytes)
        key = canonical_path_identity(Path(name))["normalization_key"]
        if key in aliases:
            _reject("path_normalization_collision", "index paths alias")
        aliases[key] = name
        mode, oid, _stage = fields
        path = target_root / name
        relative = path.relative_to(boundary)
        if any(part in IGNORED_DIRECTORY_NAMES for part in relative.parts[:-1]):
            continue
        if scope and not any(relative.as_posix() == prefix or relative.as_posix().startswith(prefix + "/")
                             or (mode == b"160000" and prefix.startswith(relative.as_posix() + "/"))
                             for prefix in scope):
            continue
        tracked.append(name)
        if mode == b"160000":
            safe.assert_no_reparse_in_chain(boundary, path)
            if not path.is_dir() or not (path / ".git").exists():
                _reject("submodule_incomplete", "submodule metadata is unavailable")
            with safe.owned_temp_root(prefix="nexus-submodule-") as sub_cwd:
                if len(path.relative_to(boundary).parts) > MAX_DEPTH:
                    _reject("depth_exceeded", "submodule nesting exceeds budget")
                child = _classify_with_git(git, path, sub_cwd, boundary, metadata_roots, scope)
            submodules.append({"path": name, "gitlink": oid.decode("ascii"),
                               "classification": child})
            if child["head_revision"] != oid.decode("ascii") or child["dirty_paths"] or child["untracked_paths"]:
                dirty.add(name)
        elif not path.exists():
            dirty.add(name)
        elif mode in (b"100644", b"100755"):
            payload = safe.open_contained_bytes(boundary, path, MAX_FILE_BYTES)
            if len(oid) not in (40, 64) or not re.fullmatch(b"[0-9a-f]+", oid):
                _reject("git_index_ambiguous", "index object id is invalid")
            algorithm = "sha1" if len(oid) == 40 else "sha256"
            actual = hashlib.new(algorithm, b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()
            executable_changed = os.name != "nt" and bool(path.stat().st_mode & 0o111) != (mode == b"100755")
            if actual != oid.decode("ascii") or executable_changed:
                dirty.add(name)
        elif mode == b"120000":
            dirty.add(name)
        else:
            _reject("git_index_ambiguous", "unsupported index mode")
    def scoped_names(output: bytes) -> list[str]:
        names = [_git_path(item) for item in _parse_nul_fields(output)]
        return sorted(name for name in names if
                      not any(part in IGNORED_DIRECTORY_NAMES for part in Path(name).parts[:-1]) and
                      (not scope or any((target_root / name).relative_to(boundary).as_posix() == prefix or
                       (target_root / name).relative_to(boundary).as_posix().startswith(prefix + "/") for prefix in scope)))

    untracked = scoped_names(untracked_output)
    ignored = scoped_names(ignored_output)
    for name in [*untracked, *ignored]:
        key = canonical_path_identity(Path(name))["normalization_key"]
        if key in aliases and aliases[key] != name:
            _reject("path_normalization_collision", "index and working tree paths alias")
        aliases[key] = name
    if index != (safe.open_contained_bytes(metadata_boundary, metadata / "index") if (metadata / "index").exists() else b"") or head != _head_identity(metadata, metadata_boundary, common, common_boundary):
        _reject("git_metadata_changed", "metadata changed during classification")
    return {
        "available": True,
        "head_revision": head,
        "index_digest": hashlib.sha256(index).hexdigest(),
        "index_entries_digest": hashlib.sha256(staged).hexdigest(),
        "tracked_paths": sorted(tracked),
        "dirty_paths": sorted(dirty),
        "untracked_paths": untracked,
        "ignored_paths": ignored,
        "submodules": submodules,
        "git_content_digest": git["content_digest"],
        "git_version": version.decode("ascii", errors="strict").strip(),
        "isolation": "sanitized_metadata",
        "environment_policy": "fixed_values_and_os_queried_SystemRoot_only",
    }


def _git_path(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError:
        _reject("unencodable_path", "git path cannot round-trip")
    identity = canonical_path_identity(Path(text))
    if identity["display"].encode("utf-8") != raw:
        _reject("path_round_trip_failed", "git path is not canonical")
    return identity["display"]


def _metadata_directory(target: Path, boundary: Path, metadata_roots: tuple[Path, ...]) -> tuple[Path, Path, Path, Path]:
    metadata = target / ".git"
    if metadata.is_file():
        raw = safe.open_contained_bytes(boundary, metadata, 4096)
        if not raw.startswith(b"gitdir: "):
            _reject("git_metadata_ambiguous", "invalid git directory declaration")
        try:
            metadata = Path(os.path.abspath(target / raw[8:].strip().decode("utf-8")))
        except UnicodeError:
            _reject("git_metadata_ambiguous", "invalid metadata path encoding")
    allowed = (boundary, *metadata_roots)

    def contained_by(candidate: Path) -> Path:
        for permitted in allowed:
            if candidate == permitted or permitted in candidate.parents:
                safe.assert_no_reparse_in_chain(permitted, candidate)
                return permitted
        _reject("git_metadata_outside_root", "metadata leaves its authorized roots")

    metadata_boundary = contained_by(metadata)
    if not metadata.is_dir():
        _reject("git_metadata_unavailable", "metadata directory is unavailable")
    common = metadata
    common_boundary = metadata_boundary
    if (metadata / "commondir").exists():
        raw = safe.open_contained_bytes(metadata_boundary, metadata / "commondir", 4096)
        try:
            common = Path(os.path.abspath(metadata / raw.strip().decode("utf-8")))
        except UnicodeError:
            _reject("git_metadata_ambiguous", "invalid common directory encoding")
        common_boundary = contained_by(common)
        if not common.is_dir():
            _reject("git_metadata_unavailable", "common directory is unavailable")
    return metadata, metadata_boundary, common, common_boundary


def _head_identity(metadata: Path, boundary: Path, common: Path, common_boundary: Path) -> str | None:
    raw = safe.open_contained_bytes(boundary, metadata / "HEAD", 4096).strip()
    if raw.startswith(b"ref: "):
        ref = _git_path(raw[5:])
        if not ref.startswith("refs/"):
            _reject("git_ref_ambiguous", "HEAD must refer to refs")
        if (common / ref).exists():
            raw = safe.open_contained_bytes(common_boundary, common / ref, 4096).strip()
        elif (common / "packed-refs").exists():
            packed = safe.open_contained_bytes(common_boundary, common / "packed-refs")
            matches = [line.split(b" ", 1)[0] for line in packed.splitlines()
                       if line.endswith(b" " + ref.encode("utf-8"))]
            if len(matches) > 1:
                _reject("git_ref_ambiguous", "duplicate packed ref")
            if not matches:
                return None
            raw = matches[0]
        else:
            return None
    if not re.fullmatch(b"[0-9a-f]{40}|[0-9a-f]{64}", raw):
        _reject("git_ref_ambiguous", "HEAD object identity is malformed")
    return raw.decode("ascii")


def build_target_manifest(
    target_root: Path,
    scope: tuple[str, ...] = (),
    git_path: Path | None = None,
    metadata_roots: tuple[Path, ...] = (),
) -> dict[str, Any]:
    """Return one complete, deterministic manifest, or raise.

    `scope` is the declared in-scope relative prefix set. An empty scope means
    the whole root is in scope.

    Every failure surfaces as `TargetManifestError`. Containment refusals from
    the bundled artifact helper are translated rather than allowed to escape,
    because a caller should catch one exception family to handle one failure,
    not two that happen to share a base class.
    """
    try:
        return _build_target_manifest(target_root, scope, git_path, metadata_roots)
    except safe.UnsafeArtifactError as exc:
        raise TargetManifestError(exc.code, str(exc)) from exc
    except (OSError, UnicodeError) as exc:
        raise TargetManifestError("target_io_failed", "target identity could not be established") from exc


def _build_target_manifest(
    target_root: Path,
    scope: tuple[str, ...],
    git_path: Path | None,
    metadata_roots: tuple[Path, ...],
) -> dict[str, Any]:
    safe.require_race_safe_primitives()
    if safe.is_link_like(target_root):
        _reject("root_is_link", "the authorized root is a link or reparse point")
    root = safe.assert_no_reparse_in_chain(target_root, target_root)
    metadata_roots = tuple(safe.assert_no_reparse_in_chain(path, path) for path in metadata_roots)
    git = resolve_trusted_git(git_path, forbidden_roots=(root, *metadata_roots))
    for prefix in scope:
        canonical_path_identity(Path(prefix))

    entries: list[dict[str, Any]] = []
    normalization_seen: dict[str, str] = {}
    inode_aliases: dict[tuple[int, int], list[str]] = {}
    total_bytes = 0
    file_count = 0
    directories: list[tuple[Path, tuple[int, int], int]] = []
    leaves: list[tuple[Path, tuple[int, int, int, int, int, int]]] = []

    def leaf_stamp(info: os.stat_result) -> tuple[int, int, int, int, int, int]:
        return (*safe._identity(info), info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)

    def walk_error(_error: OSError) -> None:
        _reject("traversal_failed", "target traversal did not complete")

    for directory, subdirectories, filenames in os.walk(root, followlinks=False, onerror=walk_error):
        here = Path(directory)
        safe.assert_no_reparse_in_chain(root, here)
        info = here.lstat()
        directories.append((here, safe._identity(info), info.st_mtime_ns))
        depth = len(here.relative_to(root).parts)
        if depth > MAX_DEPTH:
            _reject("depth_exceeded", f"traversal reached depth {depth}")
        directory_links = [name for name in subdirectories if safe.is_link_like(here / name)]
        subdirectories[:] = sorted(
            name
            for name in subdirectories
            if name not in IGNORED_DIRECTORY_NAMES
            and not safe.is_link_like(here / name)
        )

        for filename in sorted([*filenames, *directory_links]):
            absolute = here / filename
            relative = absolute.relative_to(root)
            if scope and not any(
                relative.as_posix() == prefix or relative.as_posix().startswith(prefix + "/")
                for prefix in scope
            ):
                continue

            identity = canonical_path_identity(relative)
            key = identity["normalization_key"]
            if key in normalization_seen and normalization_seen[key] != identity["display"]:
                _reject(
                    "path_normalization_collision",
                    f"{identity['display']} collides with {normalization_seen[key]}",
                )
            normalization_seen[key] = identity["display"]

            info = absolute.lstat()
            leaves.append((absolute, leaf_stamp(info)))
            file_count += 1
            if file_count > MAX_FILES:
                _reject("file_budget_exceeded", "file budget exceeded")
            if safe.is_link_like(absolute):
                # Bind type, length, and a digest of the target WITHOUT following
                # it and without ever recording the target text.
                try:
                    link_target = os.readlink(absolute)
                except OSError:
                    _reject("unreadable_link_metadata", "cannot bind link metadata")
                entries.append(
                    {
                        "path": identity,
                        "kind": "link",
                        "link_target_length": len(link_target),
                        "link_target_digest": hashlib.sha256(
                            link_target.encode("utf-8", errors="surrogatepass")
                        ).hexdigest(),
                    }
                )
                continue

            if not stat.S_ISREG(info.st_mode):
                _reject("special_file", f"{identity['display']} is not a regular file")

            if info.st_size > MAX_FILE_BYTES:
                _reject(
                    "file_too_large",
                    f"{identity['display']} is {info.st_size} bytes",
                )
            total_bytes += info.st_size
            if total_bytes > MAX_TOTAL_BYTES:
                _reject("byte_budget_exceeded", f"more than {MAX_TOTAL_BYTES} bytes in scope")

            link_count = getattr(info, "st_nlink", 1)
            if link_count > 1:
                alias_key = (getattr(info, "st_dev", 0), getattr(info, "st_ino", 0))
                inode_aliases.setdefault(alias_key, []).append(identity["display"])
                entries.append({"path": identity, "kind": "hard_link", "link_count": link_count,
                                "file_identity": list(alias_key)})
                continue

            digest, size = safe.digest_contained_file(root, absolute, MAX_FILE_BYTES)
            entries.append(
                {
                    "path": identity,
                    "kind": "file",
                    "content_digest": digest,
                    "byte_size": size,
                    "link_count": link_count,
                }
            )

    for alias_key, aliases in inode_aliases.items():
        if aliases:
            _reject(
                "unsafe_hard_link",
                "hard-linked aliases inside the analysis scope: " + ", ".join(sorted(aliases)),
            )

    if git is None:
        classification: dict[str, Any] = {
            "available": False,
            "reason_code": "trusted_git_unavailable",
        }
    else:
        with safe.owned_temp_root(prefix="nexus-git-cwd-") as cwd:
            classification = _classify_with_git(git, root, cwd, metadata_roots=metadata_roots, scope=scope)
        for name in classification["tracked_paths"]:
            key = canonical_path_identity(Path(name))["normalization_key"]
            if key in normalization_seen and normalization_seen[key] != name:
                _reject("path_normalization_collision", "index and working tree paths alias")

    for directory, identity, modified in directories:
        safe.assert_no_reparse_in_chain(root, directory)
        after = directory.lstat()
        if safe._identity(after) != identity or after.st_mtime_ns != modified:
            _reject("directory_changed", "target directories changed during traversal")

    for leaf, stamp in leaves:
        safe.assert_no_reparse_in_chain(root, leaf.parent)
        if leaf_stamp(leaf.lstat()) != stamp:
            _reject("leaf_changed", "target leaf changed during traversal")

    entries.sort(key=lambda entry: entry["path"]["display"])
    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "target_root_fingerprint": hashlib.sha256(str(root).encode("utf-8")).hexdigest(),
        "entry_count": len(entries),
        "total_byte_size": total_bytes,
        "budgets": {
            "max_depth": MAX_DEPTH,
            "max_files": MAX_FILES,
            "max_file_bytes": MAX_FILE_BYTES,
            "max_total_bytes": MAX_TOTAL_BYTES,
        },
        "declared_scope": sorted(scope),
        "excluded_directory_names": sorted(IGNORED_DIRECTORY_NAMES),
        "git_classification": classification,
        "platform_guarantee": safe.platform_guarantee(),
        "entries": entries,
    }
    manifest["manifest_digest"] = manifest_digest(manifest)
    return manifest


def manifest_digest(manifest: dict[str, Any]) -> str:
    """A stable digest over everything except the digest field itself."""
    import json

    payload = {key: value for key, value in manifest.items() if key != "manifest_digest"}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
