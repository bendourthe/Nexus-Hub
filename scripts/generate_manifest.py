#!/usr/bin/env python3
"""Generate a SHA-256 supply-chain manifest for the distributed catalog tree.

At release time this computes a SHA-256 over every file in the distributed
catalog tree and writes ``MANIFEST.sha256`` at the repo root, in the standard
``<sha256><space><space><relative-path>`` text format that ``sha256sum -c``
understands. The manifest is committed with the release and rides inside the
install tarball, so a user who later runs ``nexus-hub verify`` can prove their
on-disk install matches the published catalog (see ``verify_install.py``).

Trust-model note: this manifest is a *content-integrity* record, not a
signature. It detects post-install on-disk tampering relative to the published
catalog; it is trustworthy to the extent the manifest itself came from the
signed release tag the install bootstrap already trusts. It is NOT a substitute
for verifying the download channel.

Manifest scope (documented and stable):

* Covers the distributed catalog subtrees: ``catalog/`` (skills, commands,
  agents, hooks, rules, style-guides, ...), ``templates/`` (documentation
  templates AND the ``ai-instructions/base-*.md`` instruction templates),
  ``scripts/`` (the installer + the tools the installer copies, plus the
  integration registry under ``scripts/lib/``), and ``data/`` (the generated
  catalog metadata the installer distributes).
* Excludes VCS, caches, build output, virtual-envs, and per-user / generated
  files (see ``_EXCLUDED_DIRS`` / ``_EXCLUDED_FILE_NAMES`` /
  ``_EXCLUDED_FILE_SUFFIXES``). The manifest file itself is never listed.
* The ``extensions/`` MCP-server sources are intentionally out of the initial
  manifest scope (they are pip-installed into a venv at install time); this is a
  documented boundary recorded in the v3.10.0 known-gaps, not an oversight.

This tool is strictly local: stdlib ``hashlib`` only (reused from
``scripts/lib/integrations/manifest.py``), no network access, no credential, and
no third-party dependency. Output ordering is sorted by path so the manifest is
byte-stable across runs on the same tree.

Hashing source (v3.16.7, refined in v3.16.8). For a TRACKED file inside a git
work tree, the hash is taken over the bytes the file is **distributed** as: its
git blob (read from the index via ``git cat-file``) passed through the path's
``eol`` attribute, rather than the bytes sitting in the working tree.

Both halves of that are load-bearing, and each was learned from a shipped defect:

* **Blob, not working tree** (v3.16.7, the ``WN-1`` fix). With
  ``core.autocrlf=true`` and ``* text=auto``, a Windows checkout materializes
  every text file with CRLF, so hashing working-tree bytes produced a manifest
  that disagreed with the published artifact on essentially every text file --
  v3.16.5 shipped exactly that, and ``nexus-hub verify`` would have reported ~520
  spurious mismatches against a tarball install. Git stores the normalized (LF)
  form, so hashing the blob removes the generating host's line-ending settings
  from the result entirely.
* **Then the ``eol`` attribute** (v3.16.8, the ``BG-2`` fix). The blob alone is
  still not the distributed form, because ``git archive`` APPLIES
  ``.gitattributes``. This repo declares ``scripts/nexus-hub.cmd text eol=crlf``
  deliberately, so the Windows launcher ships with CRLF while its blob is LF.
  v3.16.7 shipped the blob-only version and the published tarball verified
  ``1230 OK, 1 MODIFIED`` -- a huge improvement on ~520, and still a FAIL verdict,
  because ``verify`` fails on any single mismatch. ``_git_eol_attrs`` therefore
  batches one ``git check-attr --stdin -z eol`` over the same path list and
  ``_apply_eol`` converts only the paths that resolve to ``crlf``.

Three consequences worth stating rather than discovering:

* The manifest reflects the INDEX, which is the content that will be committed.
  A tracked file with unstaged edits is therefore hashed as its staged form, and
  the tool prints a warning naming the dirty covered paths so a stale manifest
  cannot be generated silently. Stage first, then generate.
* An ``eol`` attribute added or changed in ``.gitattributes`` changes the manifest
  for every path it covers. That is correct rather than surprising -- it changes
  the distributed bytes -- but it means a ``.gitattributes`` edit is a
  manifest-affecting change and should be followed by a regeneration.
* Untracked-but-covered files, and any run outside a git work tree (an installed
  tree, an exported tarball), fall back to hashing file bytes exactly as before.
  ``verify_install.py`` needs no matching change: it runs against an extracted
  tarball, whose on-disk bytes are what this generator now models. A user who instead installs
  from a Windows git clone with autocrlf enabled would still see line-ending
  mismatches; that is a documented boundary, not a regression.
* Gitignored files under the covered roots are not hashed when git is available
  (v3.20.3, the ``WN-5`` fix). Enumeration is ``git ls-files -co --exclude-standard``
  over ``COVERED_ROOTS``, so a looping generator that left gitignored stubs cannot
  inflate ``MANIFEST.sha256``. ``verify_install.py`` still walks the extracted
  tree; an install tarball does not carry gitignored junk.

Usage:
    python scripts/generate_manifest.py            # write <repo>/MANIFEST.sha256
    python scripts/generate_manifest.py --root DIR --output FILE
    python scripts/generate_manifest.py --print     # write to stdout, not a file

Exit codes:
    0  the manifest was written (or printed) successfully
    2  the root directory does not exist
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

# --- reuse the existing manifest hashing (no new hashing code) -------------
# Two import layouts are supported: the in-repo tree (scripts/lib/...) and the
# installed tree (~/.nexus-hub/scripts/lib/...). Both put this file's parent
# (the scripts dir) and the repo root on sys.path, then try each module path.
# This mirrors the shim in scripts/import_skills.py exactly.
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
for _p in (str(_REPO_ROOT), str(_SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:  # in-repo layout
    from scripts.lib.integrations.manifest import _hash_path
except ModuleNotFoundError:  # pragma: no cover - installed layout
    from lib.integrations.manifest import _hash_path  # type: ignore[no-redef]


# --- manifest scope (the single source of truth, imported by verify_install) -

# Top-level subtrees the installer distributes. The verifier walks exactly these
# roots so an unexpected file outside them is simply ignored, not flagged EXTRA.
COVERED_ROOTS: Tuple[str, ...] = ("catalog", "templates", "scripts", "data")

# Directory names pruned anywhere in the walk (VCS, caches, build, venvs).
_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
    }
)

# Exact filenames never listed (the manifest itself, OS cruft).
_EXCLUDED_FILE_NAMES = frozenset({"MANIFEST.sha256", ".DS_Store", "Thumbs.db"})

# Filename suffixes never listed (compiled / generated bytecode and egg metadata).
_EXCLUDED_FILE_SUFFIXES: Tuple[str, ...] = (".pyc", ".pyo", ".egg-info")

# The manifest line format: "<sha256><space><space><relative-posix-path>\n".
# Two spaces is sha256sum text mode, so `sha256sum -c MANIFEST.sha256` works.
_LINE_SEP = "  "


def _is_excluded_dir(name: str) -> bool:
    return name in _EXCLUDED_DIRS or name.endswith(".egg-info")


def _is_excluded_file(name: str) -> bool:
    if name in _EXCLUDED_FILE_NAMES:
        return True
    return any(name.endswith(suffix) for suffix in _EXCLUDED_FILE_SUFFIXES)


def iter_catalog_files(root: Path) -> Iterator[Path]:
    """Yield every covered, non-excluded regular file under ``root``.

    Walks only the ``COVERED_ROOTS`` subtrees of ``root`` (so files outside them
    are neither hashed nor flagged), pruning excluded directories in place and
    skipping excluded filenames. Yields absolute paths; ordering is not
    guaranteed here (callers that need determinism sort the resulting entries).
    """
    for top in COVERED_ROOTS:
        base = root / top
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            # Prune excluded dirs in place so os.walk does not descend into them.
            dirnames[:] = sorted(d for d in dirnames if not _is_excluded_dir(d))
            for filename in sorted(filenames):
                if _is_excluded_file(filename):
                    continue
                yield Path(dirpath) / filename


def _relpath_posix(path: Path, root: Path) -> str:
    """Return ``path`` relative to ``root`` using forward slashes on every OS."""
    return path.relative_to(root).as_posix()


def _git(root: Path, *args: str, binary: bool = False):
    """Run a git command in ``root``; return the CompletedProcess, or None.

    Returns None for every "git is not usable here" case (git missing, not a work
    tree, non-zero exit), so callers degrade to file-byte hashing rather than
    failing. Never raises.
    """
    try:
        # Fixed argv, no shell: nothing here is user-controlled.
        return subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            check=False,
            text=not binary,
        )
    except (OSError, ValueError):  # pragma: no cover - git absent
        return None


def _git_eol_attrs(root: Path, paths: List[str]) -> Dict[str, str]:
    """Map ``relative-posix-path -> resolved ``eol`` attribute`` for ``paths``.

    Only paths whose attribute resolves to a concrete value are returned;
    ``unspecified`` / ``unset`` are omitted, so a caller can treat a missing key
    as "no conversion". One batched ``git check-attr --stdin`` for the whole set,
    matching the single-batch discipline of the ``cat-file`` call below.

    This exists because ``git archive`` -- and therefore the release tarball --
    APPLIES the ``eol`` attribute, while the blob stores the normalized form. For
    a path declared ``text eol=crlf`` the distributed bytes are CRLF and the blob
    is LF, so hashing the blob alone reports a false MODIFIED for that file. See
    the module docstring; this is the v3.16.7 ``BG-2`` defect.
    """
    if not paths:
        return {}
    try:
        # Fixed argv, no shell; paths come from git's own index listing.
        proc = subprocess.run(
            ["git", "-C", str(root), "check-attr", "--stdin", "-z", "eol"],
            input="\0".join(paths).encode("utf-8") + b"\0",
            capture_output=True,
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - git absent
        return {}
    if proc.returncode != 0:
        return {}

    # `-z` output is a flat NUL-separated stream of (path, attr, value) triples.
    fields = proc.stdout.decode("utf-8", "replace").split("\0")
    resolved: Dict[str, str] = {}
    for index in range(0, len(fields) - 2, 3):
        rel, _attr, value = fields[index], fields[index + 1], fields[index + 2]
        if rel and value in ("crlf", "lf"):
            resolved[rel] = value
    return resolved


def _apply_eol(payload: bytes, eol: str) -> bytes:
    """Return ``payload`` with the line endings ``git archive`` would produce.

    The blob is already LF-normalized, so ``lf`` is a no-op and only ``crlf``
    converts. Normalizing CRLF to LF first makes the conversion idempotent rather
    than doubling any CR that somehow survived into the blob.
    """
    if eol != "crlf":
        return payload
    return payload.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")


def _git_covered_relpaths(root: Path) -> List[str] | None:
    """Tracked plus untracked-not-ignored paths under ``COVERED_ROOTS``.

    Returns None when git is unusable so callers fall back to ``iter_catalog_files``
    (installed trees, exported tarballs, tmp fixtures with no ``.git``). An empty
    list means git worked and nothing is eligible -- including "everything on disk
    is gitignored", which must NOT fall back to ``os.walk`` (that was WN-5).
    """
    listing = _git(
        root,
        "ls-files",
        "-z",
        "-c",
        "-o",
        "--exclude-standard",
        "--",
        *COVERED_ROOTS,
    )
    if listing is None or listing.returncode != 0:
        return None
    rels: List[str] = []
    for rel in listing.stdout.split("\0"):
        if not rel:
            continue
        posix = rel.replace("\\", "/")
        name = Path(posix).name
        if _is_excluded_file(name):
            continue
        if any(_is_excluded_dir(part) for part in Path(posix).parts[:-1]):
            continue
        rels.append(posix)
    return rels


def _git_blob_sha256(root: Path) -> Dict[str, str]:
    """Map ``relative-posix-path -> sha256`` of each tracked file's DISTRIBUTED bytes.

    Returns an empty mapping when git is unusable, which makes every caller fall
    back to working-tree bytes. Reads the index (``git ls-files -s``) because the
    index holds the normalized content that will be committed and tarballed; see
    the module docstring for why the working tree is the wrong source. The blob is
    then passed through the path's ``eol`` attribute so the hash matches what
    ``git archive`` emits, not merely what the object store holds.
    """
    listing = _git(root, "ls-files", "-s", "-z", "--", *COVERED_ROOTS)
    if listing is None or listing.returncode != 0 or not listing.stdout:
        return {}

    oids: List[str] = []
    paths: List[str] = []
    for record in listing.stdout.split("\0"):
        if not record or "\t" not in record:
            continue
        meta, _, rel = record.partition("\t")
        fields = meta.split()
        if len(fields) < 2:
            continue
        mode, oid = fields[0], fields[1]
        if mode == "160000":  # a submodule gitlink has no blob to hash
            continue
        if _is_excluded_file(Path(rel).name):
            continue
        if any(_is_excluded_dir(part) for part in Path(rel).parts[:-1]):
            continue
        oids.append(oid)
        paths.append(rel)

    if not oids:
        return {}

    # One `cat-file --batch` for the whole set: a process per file would be
    # thousands of spawns on this catalog.
    try:
        # Fixed argv, no shell; oids come from git's own index listing.
        proc = subprocess.run(
            ["git", "-C", str(root), "cat-file", "--batch"],
            input="\n".join(oids).encode("ascii") + b"\n",
            capture_output=True,
            check=False,
        )
    except (OSError, ValueError):  # pragma: no cover - git absent
        return {}
    if proc.returncode != 0:
        return {}

    return _parse_cat_file_batch(proc.stdout, paths, _git_eol_attrs(root, paths))


def _parse_cat_file_batch(
    payload: bytes, paths: List[str], eol_attrs: Dict[str, str] | None = None
) -> Dict[str, str]:
    """Parse ``git cat-file --batch`` output into ``{path: sha256}``.

    The wire format per record is ``<oid> SP <type> SP <size> LF <contents> LF``.
    Sizes are read from the header rather than scanning for a delimiter, because
    blob contents are arbitrary bytes and may contain anything at all.

    ``eol_attrs`` maps a path to its resolved ``eol`` attribute; a path present
    there is converted to the line endings ``git archive`` would emit before it is
    hashed. Omitting the argument preserves pure blob hashing.
    """
    attrs = eol_attrs or {}
    result: Dict[str, str] = {}
    offset = 0
    for rel in paths:
        newline = payload.find(b"\n", offset)
        if newline == -1:
            break
        header = payload[offset:newline].split()
        if len(header) < 3:  # "<oid> missing" - skip this record
            offset = newline + 1
            continue
        try:
            size = int(header[2])
        except ValueError:
            break
        start = newline + 1
        contents = payload[start : start + size]
        if rel in attrs:
            contents = _apply_eol(contents, attrs[rel])
        result[rel] = hashlib.sha256(contents).hexdigest()
        offset = start + size + 1  # trailing LF after the contents
    return result


def _dirty_covered_paths(root: Path) -> List[str]:
    """Return covered paths with unstaged changes, so a stale manifest is loud."""
    status = _git(root, "status", "--porcelain", "--", *COVERED_ROOTS)
    if status is None or status.returncode != 0:
        return []
    dirty: List[str] = []
    for line in status.stdout.splitlines():
        if len(line) < 4:
            continue
        worktree_flag = line[1]
        if worktree_flag not in (" ", "?"):  # modified/deleted relative to the index
            dirty.append(line[3:].strip())
    return dirty


def compute_manifest(root: Path) -> List[Tuple[str, str]]:
    """Return a sorted list of ``(relative-posix-path, sha256-hex)`` entries.

    Tracked files are hashed over their git blob bytes so the manifest matches the
    distributed artifact regardless of the generating host's line-ending settings;
    untracked files (and any non-git tree) fall back to file bytes. Files that
    cannot be hashed (unreadable, vanished mid-walk) are skipped. The list is
    sorted by path so the serialized manifest is byte-stable.
    """
    blob_hashes = _git_blob_sha256(root)
    listed = _git_covered_relpaths(root)
    if listed is None:
        rels = [_relpath_posix(file_path, root) for file_path in iter_catalog_files(root)]
    else:
        rels = listed
    entries: List[Tuple[str, str]] = []
    for rel in rels:
        digest = blob_hashes.get(rel)
        if digest is None:
            digest = _hash_path(root / rel)
        if digest is None:
            continue
        entries.append((rel, digest))
    entries.sort(key=lambda entry: entry[0])
    return entries


def format_manifest(entries: List[Tuple[str, str]]) -> str:
    """Serialize ``(path, hash)`` entries to sha256sum text format with LF lines."""
    return "".join(f"{digest}{_LINE_SEP}{path}\n" for path, digest in entries)


def parse_manifest(text: str) -> Dict[str, str]:
    """Parse manifest text into a ``{relative-posix-path: sha256-hex}`` mapping.

    Tolerant of blank lines and either ``sha256sum`` mode marker (``  path`` for
    text, `` *path`` for binary). The path is everything after the first
    separator run, so paths containing spaces are preserved.
    """
    mapping: Dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n").rstrip("\r")
        if not line.strip():
            continue
        # Split on the first 2-char separator ("  " text mode or " *" binary).
        digest = line[:64].strip()
        remainder = line[64:]
        if remainder.startswith(_LINE_SEP):
            path = remainder[len(_LINE_SEP):]
        elif remainder.startswith(" *"):
            path = remainder[2:]
        else:
            path = remainder.strip()
        path = path.strip()
        if digest and path:
            mapping[path] = digest
    return mapping


def write_manifest(root: Path, out_path: Path) -> int:
    """Compute and write the manifest for ``root`` to ``out_path``.

    Writes UTF-8 bytes with explicit LF line endings (so the file is identical
    regardless of the writing OS's default newline). Returns the entry count.
    """
    entries = compute_manifest(root)
    out_path.write_bytes(format_manifest(entries).encode("utf-8"))
    return len(entries)


def _eprint(message: str) -> None:
    print(message, file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_manifest",
        description="Write a SHA-256 supply-chain manifest for the catalog tree.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=_REPO_ROOT,
        help="Repo root to hash (default: the repo this script lives in).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Manifest output path (default: <root>/MANIFEST.sha256).",
    )
    parser.add_argument(
        "--print",
        dest="to_stdout",
        action="store_true",
        help="Print the manifest to stdout instead of writing a file.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root: Path = args.root.resolve()
    if not root.is_dir():
        _eprint(f"generate_manifest: root directory not found: {root}")
        return 2

    # Tracked files are hashed from the INDEX, so unstaged edits would be recorded
    # in their staged form. Name them rather than let a stale manifest ship quietly.
    dirty = _dirty_covered_paths(root)
    if dirty:
        shown = ", ".join(dirty[:5]) + (f" (+{len(dirty) - 5} more)" if len(dirty) > 5 else "")
        _eprint(
            "generate_manifest: WARNING - unstaged changes under the covered roots "
            f"are hashed as their STAGED content: {shown}"
        )
        _eprint("generate_manifest: stage those changes first if they belong in this release.")

    if args.to_stdout:
        entries = compute_manifest(root)
        sys.stdout.write(format_manifest(entries))
        _eprint(f"generate_manifest: {len(entries)} files (stdout)")
        return 0

    out_path: Path = (args.output or (root / "MANIFEST.sha256")).resolve()
    count = write_manifest(root, out_path)
    _eprint(f"generate_manifest: wrote {count} entries to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
