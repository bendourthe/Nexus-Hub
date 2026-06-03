#!/usr/bin/env python3
"""Assert every version-carrying surface matches the canonical plugin version.

The v2.4.0 release shipped a CI failure whose root cause was *version drift*:
the canonical version in `.claude-plugin/plugin.json` had moved to `2.4.0`
while both installers were still pinned at `2.3.0`. The two-line installer
hotfix repaired that instance; this guard makes the whole *class* of bug
impossible to ship again by checking, in one place, that every surface that
carries the Nexus-Hub version agrees with the single canonical source.

Canonical source (the single source of truth):

    .claude-plugin/plugin.json  ->  top-level "version"

Checked surfaces (each must equal the canonical version, when present):

    data/marketplace.json       ->  plugin.version (JSON)
    scripts/installer.sh        ->  NEXUS_HUB_VERSION="X.Y.Z"
    scripts/installer.ps1       ->  $script:NexusHubVersion = "X.Y.Z"
    CHANGELOG.md                ->  first "## [X.Y.Z]" heading
    README.md                   ->  <!-- nexus-hub-version: X.Y.Z --> marker
    AGENTS.md                   ->  <!-- nexus-hub-version: X.Y.Z --> marker

This validator is stdlib-only (no PyYAML, no third-party deps) so it is
cross-platform from a single `.py` file, consistent with the other top-level
`.py`-only validators (`validate_no_personal_paths.py`,
`validate_unicode_safety.py`, `scan_supply_chain_iocs.py`,
`validate_workflow_security.py`, `validate_solution_frontmatter.py`) -- the
NI-v24-1 convention: a Python validator needs no `.ps1` sibling.

Surface semantics:

  * A surface file that is ABSENT under the scanned root is reported as
    "skipped" -- never a failure -- so the guard works on partial trees
    (e.g. the pytest fixtures, or a downstream fork lacking a surface).
  * A STRUCTURED surface that is present but carries no parseable version
    (a corrupt `installer.sh` with no constant, a `marketplace.json` whose
    `plugin.version` is missing) is a FINDING -- those surfaces must always
    declare a version.
  * A MARKER surface (README.md / AGENTS.md) that is present but carries no
    `<!-- nexus-hub-version: ... -->` comment is reported as "skipped" -- the
    marker is an optional, opt-in anchor for the `/update version` flow.
  * A surface whose version is present but differs from the canonical version
    is a DRIFT FINDING (the failure this guard exists to catch).

Exit codes:
    0 - every present, version-bearing surface matches the canonical version
    1 - one or more drift / unparseable findings (each named on stderr)
    2 - usage / IO error (the canonical plugin.json is missing or unparseable)

Usage:
    python scripts/check_version_sync.py
    python scripts/check_version_sync.py --root /path/to/repo
    python scripts/check_version_sync.py --json
    python scripts/check_version_sync.py --verbose
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Callable, Optional

# A semantic-version token, used by every regex-based surface extractor.
_SEMVER = r"(\d+\.\d+\.\d+)"

CANONICAL_REL = ".claude-plugin/plugin.json"

# Regex surface extractors. Each searches the file text and returns the first
# captured version, or None if the surface carries no version.
_INSTALLER_SH_RE = re.compile(r'NEXUS_HUB_VERSION="' + _SEMVER + r'"')
_INSTALLER_PS1_RE = re.compile(r'\$script:NexusHubVersion\s*=\s*"' + _SEMVER + r'"')
_CHANGELOG_RE = re.compile(r"^##\s*\[" + _SEMVER + r"\]", re.MULTILINE)
_VERSION_MARKER_RE = re.compile(r"<!--\s*nexus-hub-version:\s*" + _SEMVER + r"\s*-->")


class SurfaceError(Exception):
    """A present surface could not be parsed (corrupt JSON, IO error, etc.)."""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:  # pragma: no cover - exercised only on IO failure
        raise SurfaceError(f"cannot read {path}: {exc}") from exc


def _extract_json_version(path: Path, *keys: str) -> Optional[str]:
    """Return the version at a nested JSON key path, or None if it is missing."""
    try:
        data = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        raise SurfaceError(f"invalid JSON in {path}: {exc}") from exc
    node: object = data
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return str(node) if isinstance(node, (str, int, float)) else None


def _extract_regex_version(path: Path, pattern: re.Pattern[str]) -> Optional[str]:
    """Return the first version matched by `pattern` in the file, else None."""
    match = pattern.search(_read_text(path))
    return match.group(1) if match else None


# A surface is a labelled file with an extractor and a flag indicating whether a
# present-but-version-less file is tolerated (markers) or a finding (structured).
class Surface:
    def __init__(
        self,
        label: str,
        relpath: str,
        extractor: Callable[[Path], Optional[str]],
        *,
        marker_optional: bool = False,
    ) -> None:
        self.label = label
        self.relpath = relpath
        self.extractor = extractor
        self.marker_optional = marker_optional


def _build_surfaces() -> list[Surface]:
    """The ordered list of non-canonical surfaces the guard checks."""
    return [
        Surface(
            "data/marketplace.json (plugin.version)",
            "data/marketplace.json",
            lambda p: _extract_json_version(p, "plugin", "version"),
        ),
        Surface(
            "scripts/installer.sh (NEXUS_HUB_VERSION)",
            "scripts/installer.sh",
            lambda p: _extract_regex_version(p, _INSTALLER_SH_RE),
        ),
        Surface(
            "scripts/installer.ps1 ($script:NexusHubVersion)",
            "scripts/installer.ps1",
            lambda p: _extract_regex_version(p, _INSTALLER_PS1_RE),
        ),
        Surface(
            "CHANGELOG.md (latest heading)",
            "CHANGELOG.md",
            lambda p: _extract_regex_version(p, _CHANGELOG_RE),
        ),
        Surface(
            "README.md (version marker)",
            "README.md",
            lambda p: _extract_regex_version(p, _VERSION_MARKER_RE),
            marker_optional=True,
        ),
        Surface(
            "AGENTS.md (version marker)",
            "AGENTS.md",
            lambda p: _extract_regex_version(p, _VERSION_MARKER_RE),
            marker_optional=True,
        ),
    ]


# The outcome of checking one surface.
class Result:
    def __init__(
        self, surface: Surface, status: str, found: Optional[str], detail: str
    ) -> None:
        self.surface = surface
        self.status = status  # "match" | "drift" | "unparseable" | "skipped"
        self.found = found
        self.detail = detail

    @property
    def is_finding(self) -> bool:
        return self.status in {"drift", "unparseable"}


def check_surface(surface: Surface, root: Path, canonical: str) -> Result:
    """Check one surface against the canonical version, never raising."""
    path = root / surface.relpath
    if not path.exists():
        return Result(surface, "skipped", None, "file not present")
    try:
        found = surface.extractor(path)
    except SurfaceError as exc:
        return Result(surface, "unparseable", None, str(exc))
    if found is None:
        if surface.marker_optional:
            return Result(surface, "skipped", None, "no version marker found")
        return Result(surface, "unparseable", None, "no version string found")
    if found != canonical:
        return Result(surface, "drift", found, f"found {found}, expected {canonical}")
    return Result(surface, "match", found, f"matches {canonical}")


def read_canonical_version(root: Path) -> str:
    """Read the single source of truth, raising SurfaceError on any problem."""
    path = root / CANONICAL_REL
    if not path.exists():
        raise SurfaceError(f"canonical version file not found: {path}")
    version = _extract_json_version(path, "version")
    if version is None:
        raise SurfaceError(f"no top-level 'version' field in {path}")
    return version


def _emit_json(canonical: str, results: list[Result]) -> None:
    payload = {
        "canonical": canonical,
        "in_sync": not any(r.is_finding for r in results),
        "surfaces": [
            {
                "label": r.surface.label,
                "path": r.surface.relpath,
                "status": r.status,
                "found": r.found,
                "expected": canonical,
            }
            for r in results
        ],
    }
    print(json.dumps(payload, indent=2))


def _emit_text(canonical: str, results: list[Result], verbose: bool) -> None:
    findings = [r for r in results if r.is_finding]
    for r in findings:
        print(
            f"DRIFT: {r.surface.relpath}: {r.detail}",
            file=sys.stderr,
        )
    if verbose or not findings:
        # Show the full picture (every surface + its status) on a clean run or
        # whenever the caller asks for detail.
        stream = sys.stderr if findings else sys.stdout
        print(f"canonical version: {canonical} ({CANONICAL_REL})", file=stream)
        for r in results:
            print(f"  [{r.status:>11}] {r.surface.relpath}: {r.detail}", file=stream)
    if findings:
        print(
            f"\ncheck_version_sync: {len(findings)} version-drift finding(s) "
            f"across {len(results)} checked surface(s). Bump every surface to "
            f"{canonical} (the canonical {CANONICAL_REL} value).",
            file=sys.stderr,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root to scan (default: the repo containing this script).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON report on stdout (for CI).",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print every surface status."
    )
    args = parser.parse_args()

    root: Path = args.root.resolve()

    try:
        canonical = read_canonical_version(root)
    except SurfaceError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    surfaces = _build_surfaces()
    results = [check_surface(s, root, canonical) for s in surfaces]

    if args.json:
        _emit_json(canonical, results)
    else:
        _emit_text(canonical, results, args.verbose)

    return 1 if any(r.is_finding for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
