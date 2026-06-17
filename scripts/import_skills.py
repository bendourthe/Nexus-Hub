#!/usr/bin/env python3
"""Import-hygiene gate for the ``/skills import`` path.

This module hardens the LOCAL ``/skills import`` flow (the agent-driven
``import-skills`` operation that copies a skill into the active project) with
three catalog-hygiene disciplines reverse-engineered from a generic
catalog-stack pattern:

1. **HTTPS-only source validation** -- a remote source URL must be ``https://``
   (the single carve-out is ``http://localhost`` / ``127.0.0.1`` / ``[::1]``
   for a developer running a local catalog mirror). A plain local filesystem
   path has no scheme and is always allowed (that is the common case). Any
   other scheme (``http://`` to a non-loopback host, ``file://``, ``ftp://``,
   ``git://``, ...) is refused.
2. **Discovery-only ``install_allowed`` flag** -- a skill or source entry whose
   metadata sets ``install_allowed: false`` can be *listed* (discovery) but not
   *installed*. The gate surfaces a clear message and refuses the import.
3. **Hash-on-import** -- every artifact that is actually imported gets a
   recorded SHA-256, computed by reusing
   ``scripts/lib/integrations/manifest.py::_hash_path`` (no new hashing code).

This is LOCAL hygiene only. It introduces NO new outbound call, dependency, or
credential -- there is deliberately no network client here. Remote credentialed
catalog fetch (the declined comparison candidate N5) is out of scope. This
layer is ADDITIVE to, never a replacement for, the existing pre-install
security scan (``skill-security-scan`` / ``nexus-skill-scanner``,
``scripts/scan_skill_security.py``): a source that passes this gate must still
clear that scan before it is trusted.

Usage:
    python scripts/import_skills.py validate-source <source>
    python scripts/import_skills.py check-allowed <skill-dir>
    python scripts/import_skills.py hash <path> [<path> ...]
    python scripts/import_skills.py vet <skill-dir> [--source <source>] [--json]

Exit codes:
    0  the source / skill passed the gate (import may proceed)
    1  the source / skill was refused (non-HTTPS source or discovery-only)
    2  CLI usage error (handled by argparse) or an unreadable target
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

# --- reuse the existing manifest hashing (no new hashing code) -------------
# Two import layouts are supported: the in-repo tree (scripts/lib/...) and the
# installed tree (~/.nexus-hub/scripts/lib/...). Both put this file's parent
# (the scripts dir) and the repo root on sys.path, then try each module path.
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
for _p in (str(_REPO_ROOT), str(_SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:  # in-repo layout
    from scripts.lib.integrations.manifest import _hash_path
except ModuleNotFoundError:  # pragma: no cover - installed layout
    from lib.integrations.manifest import _hash_path  # type: ignore[no-redef]

# Loopback hosts allowed to use plain http:// (a local catalog mirror).
LOCALHOST_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

# A source is treated as a URL only when it begins with ``scheme://``. This
# deliberately excludes Windows drive paths (``C:\skills``) and POSIX paths
# (``/home/user/skill`` or ``./skill``), which are local filesystem imports.
_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


def is_url(source: str) -> bool:
    """Return True when ``source`` is a ``scheme://...`` URL (not a local path)."""
    return bool(_URL_RE.match(source.strip()))


def validate_https_source(source: str) -> tuple[bool, str]:
    """Validate a source against the HTTPS-only rule.

    Returns ``(ok, detail)``. A local filesystem path (no ``scheme://``) is
    always allowed. A URL is allowed only when it is ``https://`` or
    ``http://`` to a loopback host; every other URL is refused.
    """
    s = source.strip()
    if not s:
        return False, "empty source"
    if not is_url(s):
        return True, "local path (no network fetch)"

    parsed = urlparse(s)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()

    if scheme == "https":
        return True, "https"
    if scheme == "http" and host in LOCALHOST_HOSTS:
        return True, "http-localhost"
    if scheme == "http":
        return (
            False,
            f"refusing non-HTTPS remote source '{s}': only https:// "
            f"(or http://localhost) is allowed",
        )
    return (
        False,
        f"refusing non-HTTPS source scheme '{scheme}://': only https:// "
        f"(or http://localhost), or a local filesystem path, is allowed",
    )


def is_install_allowed(entry: Mapping[str, object]) -> bool:
    """Return whether a catalog/source/skill ``entry`` may be installed.

    ``install_allowed`` defaults to True (installable). Only an explicit
    falsey value (``False`` or the strings ``"false"`` / ``"no"`` / ``"0"``)
    marks the entry discovery-only.
    """
    val = entry.get("install_allowed", True)
    if isinstance(val, str):
        return val.strip().lower() not in {"false", "no", "0", ""}
    return bool(val)


def _parse_frontmatter_install_allowed(skill_md_text: str) -> bool:
    """Read the ``install_allowed`` flag from a SKILL.md frontmatter block.

    Mirrors the lightweight frontmatter scan used elsewhere in the repo (no
    YAML dependency). A missing block or missing key means installable (True).
    """
    if not skill_md_text.startswith("---"):
        return True
    end = skill_md_text.find("---", 3)
    if end == -1:
        return True
    for line in skill_md_text[3:end].splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        if key.strip() == "install_allowed":
            return is_install_allowed({"install_allowed": value.strip().strip('"').strip("'")})
    return True


def read_install_allowed_from_skill(skill_dir: Path) -> bool:
    """Return the ``install_allowed`` flag declared in ``skill_dir/SKILL.md``.

    A missing SKILL.md or missing flag means installable (True).
    """
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return True
    try:
        return _parse_frontmatter_install_allowed(skill_md.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return True


def hash_on_import(path: Path) -> str | None:
    """Return the SHA-256 of ``path`` reusing the manifest hasher (None if not a file)."""
    return _hash_path(path)


def hash_tree(root: Path) -> dict[str, str]:
    """Return ``{relative-posix-path: sha256}`` for every file under ``root``.

    If ``root`` is a single file, the one entry is keyed by its name. Skips
    housekeeping artifacts (``__pycache__``, ``.DS_Store``).
    """
    hashes: dict[str, str] = {}
    if root.is_file():
        digest = hash_on_import(root)
        if digest is not None:
            hashes[root.name] = digest
        return hashes
    for entry in sorted(root.rglob("*")):
        if not entry.is_file():
            continue
        if entry.name == ".DS_Store" or "__pycache__" in entry.parts:
            continue
        digest = hash_on_import(entry)
        if digest is not None:
            hashes[entry.relative_to(root).as_posix()] = digest
    return hashes


def vet_import(source: str, skill_dir: Path | None = None) -> dict[str, object]:
    """Run the full import-hygiene gate and return a structured record.

    The record reports each check, an overall ``ok`` flag, any blocking
    ``errors``, and (only when every gate passes) the per-artifact
    ``hashes``. Hashing happens after the gate so the recorded digests reflect
    exactly what would be imported.
    """
    record: dict[str, object] = {
        "source": source,
        "ok": True,
        "checks": {},
        "errors": [],
        "hashes": {},
    }
    checks = record["checks"]
    errors = record["errors"]
    assert isinstance(checks, dict) and isinstance(errors, list)  # for type-checkers

    https_ok, https_detail = validate_https_source(source)
    checks["https"] = {"ok": https_ok, "detail": https_detail}
    if not https_ok:
        record["ok"] = False
        errors.append(https_detail)

    if skill_dir is not None:
        allowed = read_install_allowed_from_skill(skill_dir)
        checks["install_allowed"] = allowed
        if not allowed:
            record["ok"] = False
            errors.append(
                f"'{skill_dir}' is marked install_allowed: false (discovery-only); "
                f"it can be listed but not imported"
            )

    # Hash-on-import: only record digests for an import that actually proceeds.
    if record["ok"] and skill_dir is not None and skill_dir.exists():
        record["hashes"] = hash_tree(skill_dir)

    return record


def _cmd_validate_source(args: argparse.Namespace) -> int:
    ok, detail = validate_https_source(args.source)
    if ok:
        print(f"OK: source accepted ({detail}).")
        return 0
    print(f"REFUSED: {detail}", file=sys.stderr)
    return 1


def _cmd_check_allowed(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir)
    if not skill_dir.exists():
        print(f"Error: skill directory not found: {skill_dir}", file=sys.stderr)
        return 2
    allowed = read_install_allowed_from_skill(skill_dir)
    if allowed:
        print(f"OK: {skill_dir} is installable (install_allowed not false).")
        return 0
    print(
        f"REFUSED: {skill_dir} is marked install_allowed: false (discovery-only).",
        file=sys.stderr,
    )
    return 1


def _cmd_hash(args: argparse.Namespace) -> int:
    rc = 0
    for raw in args.paths:
        path = Path(raw)
        digest = hash_on_import(path)
        if digest is None:
            print(f"SKIP (not a regular file): {path}", file=sys.stderr)
            rc = 2
            continue
        print(f"{digest}  {path}")
    return rc


def _cmd_vet(args: argparse.Namespace) -> int:
    skill_dir = Path(args.skill_dir)
    if not skill_dir.exists():
        print(f"Error: skill directory not found: {skill_dir}", file=sys.stderr)
        return 2
    source = args.source if args.source is not None else str(skill_dir)
    record = vet_import(source, skill_dir=skill_dir)
    if args.json:
        print(json.dumps(record, indent=2))
    else:
        status = "OK" if record["ok"] else "REFUSED"
        print(f"{status}: source={source}")
        for name, result in record["checks"].items():  # type: ignore[union-attr]
            print(f"  - {name}: {result}")
        if record["hashes"]:
            print(f"  - hashed {len(record['hashes'])} artifact(s)")  # type: ignore[arg-type]
        for err in record["errors"]:  # type: ignore[union-attr]
            print(f"  ! {err}", file=sys.stderr)
    print(
        "Note: this hygiene gate is additive to the skill-security scan "
        "(skill-security-scan / nexus-skill-scanner); run that scan before trusting an import.",
        file=sys.stderr,
    )
    return 0 if record["ok"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import-hygiene gate for the /skills import path "
        "(HTTPS-only validation, discovery-only flag, hash-on-import).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser(
        "validate-source", help="HTTPS-only validation of a source (URL or local path)."
    )
    p_validate.add_argument("source", help="The import source (https:// URL or a local path).")
    p_validate.set_defaults(func=_cmd_validate_source)

    p_allowed = sub.add_parser(
        "check-allowed", help="Check a skill's install_allowed (discovery-only) flag."
    )
    p_allowed.add_argument("skill_dir", help="Path to a skill directory containing SKILL.md.")
    p_allowed.set_defaults(func=_cmd_check_allowed)

    p_hash = sub.add_parser("hash", help="Print the SHA-256 of one or more files.")
    p_hash.add_argument("paths", nargs="+", help="Files to hash.")
    p_hash.set_defaults(func=_cmd_hash)

    p_vet = sub.add_parser(
        "vet", help="Run the full gate (https + install_allowed + hash-on-import)."
    )
    p_vet.add_argument("skill_dir", help="Path to the skill directory to vet.")
    p_vet.add_argument(
        "--source",
        default=None,
        help="The source the skill came from (defaults to the skill directory path).",
    )
    p_vet.add_argument("--json", action="store_true", help="Emit the record as JSON.")
    p_vet.set_defaults(func=_cmd_vet)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
