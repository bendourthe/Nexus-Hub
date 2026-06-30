#!/usr/bin/env python3
"""Verify an installed Nexus-Hub catalog against its published SHA-256 manifest.

This is the logic behind ``nexus-hub verify``. It recomputes the SHA-256 of
every file recorded in the installed ``MANIFEST.sha256`` and diffs the result
against the manifest, classifying each path as:

* ``OK``       - the file exists and its hash matches the manifest;
* ``MODIFIED`` - the file exists but its hash differs from the manifest;
* ``MISSING``  - the manifest lists the path but it is absent on disk;
* ``EXTRA``    - the file is present under a covered root but absent from the
                 manifest (an unexpected addition).

It prints a concise report (non-OK entries individually; OK entries as a count,
per the Output Minimization rule) ending in a single ``verify: PASS`` or
``verify: FAIL (<n> modified, <n> missing, <n> extra)`` line, and exits 0 on
PASS, non-zero on FAIL.

THREAT-MODEL BOUNDARY (read this before trusting the result): a local manifest
detects on-disk tampering AFTER install, relative to the published catalog. It
is trustworthy only to the extent the manifest itself came from the signed
release tag the install bootstrap already trusts (the materialized source tree
under ``~/.nexus-hub/src``). It is NOT a code signature and NOT a substitute for
verifying the download channel: an attacker who can rewrite both a file and the
manifest in the same tree defeats it. Use it to catch accidental corruption and
post-install drift, not to establish first-trust in the bytes.

This tool is strictly local and read-only: it reads the installed manifest and
the installed files, makes NO network call, requires NO credential, and adds no
third-party dependency (stdlib ``hashlib`` only, reused via
``scripts/lib/integrations/manifest.py``).

Path resolution (override any of these for tests / non-standard installs):

    NEXUS_HUB_HOME           install root            (default: ~/.nexus-hub)
    --root DIR               catalog root to verify  (default: <home>/src)
    --manifest FILE          manifest to verify against
                             (default: <root>/MANIFEST.sha256, else <home>/MANIFEST.sha256)
    --ignore-extra           do not let EXTRA files cause FAIL (still reported)

Usage:
    nexus-hub verify
    python ~/.nexus-hub/scripts/verify_install.py --root DIR --manifest FILE

Exit codes:
    0  verify PASS (every manifest entry matched; no disqualifying deviation)
    1  verify FAIL (one or more MODIFIED / MISSING / EXTRA)
    2  could not verify (no manifest or catalog root found)
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple

# --- reuse the shared scope logic + the manifest hashing (no duplication) ---
# Same dual-location shim as generate_manifest.py / import_skills.py: support the
# in-repo tree (scripts/...) and the installed tree (~/.nexus-hub/scripts/...).
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
for _p in (str(_REPO_ROOT), str(_SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:  # in-repo layout
    from scripts.generate_manifest import (
        iter_catalog_files,
        parse_manifest,
    )
    from scripts.lib.integrations.manifest import _hash_path
except ModuleNotFoundError:  # pragma: no cover - installed layout
    from generate_manifest import (  # type: ignore[no-redef]
        iter_catalog_files,
        parse_manifest,
    )
    from lib.integrations.manifest import _hash_path  # type: ignore[no-redef]


def install_home() -> Path:
    """The install root (`~/.nexus-hub`), overridable via NEXUS_HUB_HOME."""
    override = os.environ.get("NEXUS_HUB_HOME")
    if override:
        return Path(override)
    return Path.home() / ".nexus-hub"


def _eprint(message: str) -> None:
    print(message, file=sys.stderr)


def resolve_catalog_root(root_override: Path | None) -> Path | None:
    """Resolve the catalog root to verify.

    Order: an explicit ``--root`` > ``<home>/src`` (the tree the one-line
    bootstrap materializes, a 1:1 mirror of the repo whose layout matches the
    manifest's repo-relative paths). Returns the directory if it exists, else
    None.

    The bare install root (``<home>``) is deliberately NOT a fallback: the
    installer fans the catalog out to per-platform locations, so ``<home>`` does
    not mirror the repo layout and verifying against it would report every
    ``catalog/...`` entry as MISSING. A developer running from a checkout passes
    ``--root <checkout>`` explicitly.
    """
    if root_override is not None:
        return root_override if root_override.is_dir() else None
    src = install_home() / "src"
    return src if src.is_dir() else None


def resolve_manifest(root: Path, manifest_override: Path | None) -> Path | None:
    """Resolve the manifest path.

    Order: an explicit ``--manifest`` > ``<root>/MANIFEST.sha256`` (rides inside
    the tarball next to the catalog) > ``<home>/MANIFEST.sha256`` (the copy the
    installer drops at the install root). Returns the first that exists, else
    None.
    """
    if manifest_override is not None:
        return manifest_override if manifest_override.is_file() else None
    in_root = root / "MANIFEST.sha256"
    if in_root.is_file():
        return in_root
    at_home = install_home() / "MANIFEST.sha256"
    if at_home.is_file():
        return at_home
    return None


class VerifyResult:
    """Classification outcome of a verify run."""

    def __init__(self) -> None:
        self.ok: int = 0
        self.modified: List[str] = []
        self.missing: List[str] = []
        self.extra: List[str] = []

    def failed(self, ignore_extra: bool) -> bool:
        if self.modified or self.missing:
            return True
        return bool(self.extra) and not ignore_extra


def classify(root: Path, manifest_text: str) -> VerifyResult:
    """Diff the on-disk ``root`` against ``manifest_text`` and classify paths."""
    expected = parse_manifest(manifest_text)
    result = VerifyResult()

    # MODIFIED / MISSING / OK: every manifest entry, recomputed against disk.
    for rel_path, expected_hash in expected.items():
        on_disk = root / rel_path
        actual_hash = _hash_path(on_disk)
        if actual_hash is None:
            result.missing.append(rel_path)
        elif actual_hash != expected_hash:
            result.modified.append(rel_path)
        else:
            result.ok += 1

    # EXTRA: files present under a covered root but absent from the manifest.
    on_disk_paths = {
        file_path.relative_to(root).as_posix() for file_path in iter_catalog_files(root)
    }
    result.extra = sorted(on_disk_paths - set(expected.keys()))

    result.modified.sort()
    result.missing.sort()
    return result


def format_report(result: VerifyResult, ignore_extra: bool) -> Tuple[str, bool]:
    """Render the report text and return ``(text, passed)``."""
    lines: List[str] = []
    for path in result.modified:
        lines.append(f"  MODIFIED  {path}")
    for path in result.missing:
        lines.append(f"  MISSING   {path}")
    if not ignore_extra:
        for path in result.extra:
            lines.append(f"  EXTRA     {path}")
    elif result.extra:
        lines.append(f"  (ignoring {len(result.extra)} EXTRA file(s) per --ignore-extra)")

    lines.append(f"  OK        {result.ok} file(s) match")

    passed = not result.failed(ignore_extra)
    if passed:
        lines.append("verify: PASS")
    else:
        lines.append(
            "verify: FAIL "
            f"({len(result.modified)} modified, "
            f"{len(result.missing)} missing, "
            f"{len(result.extra)} extra)"
        )
    return "\n".join(lines), passed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-hub verify",
        description="Verify the installed catalog against its SHA-256 manifest.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Catalog root to verify (default: <NEXUS_HUB_HOME>/src).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Manifest to verify against (default: <root>/MANIFEST.sha256).",
    )
    parser.add_argument(
        "--ignore-extra",
        action="store_true",
        help="Report EXTRA files but do not let them cause a FAIL.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    root = resolve_catalog_root(args.root)
    if root is None:
        _eprint(
            "verify: no catalog root found "
            f"(looked for {install_home() / 'src'}). Re-run the install bootstrap, "
            "or pass --root <checkout> to verify a local checkout."
        )
        return 2

    manifest_path = resolve_manifest(root, args.manifest)
    if manifest_path is None:
        _eprint(
            "verify: no MANIFEST.sha256 found "
            f"(looked in {root} and {install_home()}). "
            "This install predates supply-chain manifests, or the manifest was removed."
        )
        return 2

    manifest_text = manifest_path.read_text(encoding="utf-8", errors="replace")
    result = classify(root, manifest_text)
    report, passed = format_report(result, args.ignore_extra)

    _eprint(f"verify: checking {root} against {manifest_path}")
    print(report)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
