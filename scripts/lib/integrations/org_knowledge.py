"""Validate organization knowledge bundles without mutating their contents.

The contract is declared in ``configs/org-bundle.schema.json`` and documented
in ``configs/README.md``. Validation is hand-rolled against that small schema
so installer and CLI paths gain no third-party dependency. Expected input
failures are returned in a typed ``BundleReport`` rather than raised.

Three rules govern this module:

1. **Read only.** Validation never writes to the bundle or normalizes it in
   place. Defaults are applied only to the report's copied manifest.
2. **Collect actionable diagnostics.** Missing, malformed, or unreadable files
   are named individually, and validation continues wherever possible.
3. **Keep always-on content concise without deleting it.** A core over 200
   lines produces a warning based on Anthropic's CLAUDE.md guidance; content is
   never truncated.

The bootstrap materializes the full checkout under ``~/.nexus-hub/src``. Both
installers also recursively copy the whole ``scripts/lib`` tree to
``~/.nexus-hub/scripts/lib`` via ``safe_folder_copy`` / ``Safe-Folder-Copy``.
This module therefore ships through the existing tree copy and needs no
explicit installer filename entry.
"""

from __future__ import annotations

import json
import re
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Tuple

SCHEMA_VERSION = 1
CORE_LINE_BUDGET = 200
DEFAULT_CORE = "core.md"
DEFAULT_RULES_DIR = "rules/"
DEFAULT_REFERENCES_DIR = "references/"

_KNOWN_KEYS = frozenset(
    {
        "schema_version",
        "org_name",
        "core",
        "rules_dir",
        "references_dir",
        "precedence_statement",
    }
)
_REQUIRED_KEYS = ("schema_version", "org_name", "core")
_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


@dataclass
class BundleReport:
    """Structured, non-raising validation result for one bundle directory."""

    bundle_path: Path
    manifest: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        """Return ``True`` when validation found no blocking errors."""

        return not self.errors

    def summary(self) -> str:
        """Return a stable one-line result suitable for CLI output."""

        status = "valid" if self.valid else "invalid"
        return (
            f"{status}: {self.bundle_path} "
            f"({len(self.errors)} errors, {len(self.warnings)} warnings)"
        )


def _note(message: str) -> None:
    """Emit one diagnostic line for future installer-side seeding paths."""

    print(f"note: org-knowledge: {message}", file=sys.stderr)


def _expand(path: str | Path) -> Path:
    """Expand ``~`` through ``Path.home()`` so isolated tests stay isolated.

    ``os.path.expanduser`` reads process environment variables and can escape a
    test that patches ``Path.home()``. This follows the installer integration
    convention established by ``platform_defaults.py``.
    """

    raw = str(path)
    if raw == "~":
        return Path.home()
    if raw.startswith("~/") or raw.startswith("~\\"):
        return Path.home() / raw[2:]
    return Path(raw)


def _referenced_path(
    root: Path,
    key: str,
    value: Any,
    report: BundleReport,
) -> Optional[Path]:
    """Resolve one declared relative path while enforcing bundle containment."""

    if not isinstance(value, str) or not value.strip():
        report.errors.append(f"{key}: expected a non-empty relative path string")
        return None

    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if (
        normalized.startswith("/")
        or value.startswith("\\")
        or _WINDOWS_DRIVE.match(normalized)
        or pure == PurePosixPath(".")
        or ".." in pure.parts
    ):
        report.errors.append(
            f"{key}: {value!r} must be a relative path contained within the bundle"
        )
        return None

    try:
        root_resolved = root.resolve(strict=False)
        target = root.joinpath(*pure.parts)
        target.resolve(strict=False).relative_to(root_resolved)
    except (OSError, RuntimeError, ValueError):
        report.errors.append(
            f"{key}: {value!r} cannot be resolved safely within {root}"
        )
        return None
    return target


def _read_markdown(path: Path, label: str, report: BundleReport) -> Optional[str]:
    """Read one UTF-8 text file, returning an error instead of raising."""

    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report.errors.append(f"{label}: cannot read {path} as UTF-8 ({exc})")
        return None


def _validate_file(path: Path, key: str, report: BundleReport) -> Optional[str]:
    """Validate a declared file and return its text when readable."""

    try:
        mode = path.stat().st_mode
    except FileNotFoundError:
        report.errors.append(f"{key}: referenced file does not exist: {path}")
        return None
    except OSError as exc:
        report.errors.append(f"{key}: cannot access {path} ({exc})")
        return None
    if not stat.S_ISREG(mode):
        report.errors.append(f"{key}: referenced path is not a file: {path}")
        return None
    return _read_markdown(path, key, report)


def _validate_directory(path: Path, key: str, report: BundleReport) -> None:
    """Validate a declared directory and every file below it, best effort."""

    try:
        mode = path.stat().st_mode
    except FileNotFoundError:
        report.errors.append(f"{key}: referenced directory does not exist: {path}")
        return
    except OSError as exc:
        report.errors.append(f"{key}: cannot access {path} ({exc})")
        return
    if not stat.S_ISDIR(mode):
        report.errors.append(f"{key}: referenced path is not a directory: {path}")
        return

    try:
        descendants = sorted(path.rglob("*"), key=lambda item: str(item))
    except OSError as exc:
        report.errors.append(f"{key}: cannot enumerate {path} ({exc})")
        return

    for descendant in descendants:
        try:
            is_file = descendant.is_file()
        except OSError as exc:
            report.errors.append(f"{key}: cannot inspect {descendant} ({exc})")
            continue
        if is_file:
            _read_markdown(descendant, key, report)


def _validate_scalar_fields(manifest: Dict[str, Any], report: BundleReport) -> None:
    """Validate non-path manifest fields against schema version 1."""

    for key in _REQUIRED_KEYS:
        if key not in manifest:
            report.errors.append(f"org.json: missing required key {key!r}")

    if "schema_version" in manifest:
        value = manifest["schema_version"]
        if isinstance(value, bool) or not isinstance(value, int):
            report.errors.append("schema_version: expected integer 1")
        elif value != SCHEMA_VERSION:
            report.errors.append(
                f"schema_version: unsupported value {value!r}; expected {SCHEMA_VERSION}"
            )

    if "org_name" in manifest:
        value = manifest["org_name"]
        if not isinstance(value, str) or not value.strip():
            report.errors.append("org_name: expected a non-empty string")

    if "precedence_statement" in manifest:
        value = manifest["precedence_statement"]
        if not isinstance(value, str) or not value.strip():
            report.errors.append("precedence_statement: expected a non-empty string")

    unknown = sorted(set(manifest) - _KNOWN_KEYS)
    if unknown:
        report.warnings.append(
            "org.json: unknown keys accepted for forward compatibility: "
            + ", ".join(unknown)
        )


def _load_manifest(root: Path, report: BundleReport) -> Optional[Dict[str, Any]]:
    """Load ``org.json`` with precise parse and read diagnostics."""

    manifest_path = root / "org.json"
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        report.errors.append(f"org.json: manifest does not exist: {manifest_path}")
        return None
    except (OSError, UnicodeError) as exc:
        report.errors.append(f"org.json: cannot read {manifest_path} as UTF-8 ({exc})")
        return None

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        report.errors.append(
            "org.json: malformed JSON at "
            f"line {exc.lineno}, column {exc.colno}, position {exc.pos}: {exc.msg}"
        )
        return None
    if not isinstance(data, dict):
        report.errors.append("org.json: expected a JSON object at the document root")
        return None
    return data


def validate_bundle(path: str | Path) -> BundleReport:
    """Validate one organization bundle and return every discovered issue.

    The bundle is never mutated. The copied manifest in the report includes
    defaults for optional directory fields so later phases can consume one
    stable shape.
    """

    root = _expand(path)
    report = BundleReport(bundle_path=root)

    try:
        mode = root.stat().st_mode
    except FileNotFoundError:
        report.errors.append(f"bundle directory does not exist: {root}")
        return report
    except (OSError, ValueError) as exc:
        report.errors.append(f"bundle directory is unreadable: {root} ({exc})")
        return report
    if not stat.S_ISDIR(mode):
        report.errors.append(f"bundle path is not a directory: {root}")
        return report

    manifest = _load_manifest(root, report)
    if manifest is None:
        return report

    report.manifest = dict(manifest)
    report.manifest.setdefault("rules_dir", DEFAULT_RULES_DIR)
    report.manifest.setdefault("references_dir", DEFAULT_REFERENCES_DIR)
    _validate_scalar_fields(manifest, report)

    core = None
    if "core" in manifest:
        core = _referenced_path(root, "core", manifest["core"], report)
    if core is not None:
        text = _validate_file(core, "core", report)
        if text is not None:
            line_count = len(text.splitlines())
            if line_count > CORE_LINE_BUDGET:
                report.warnings.append(
                    f"core: {line_count} lines exceeds the {CORE_LINE_BUDGET}-line "
                    "always-on budget; Anthropic recommends keeping CLAUDE.md under "
                    "200 lines because longer always-loaded instructions consume "
                    "context and reduce adherence"
                )

    for key, default in (
        ("rules_dir", DEFAULT_RULES_DIR),
        ("references_dir", DEFAULT_REFERENCES_DIR),
    ):
        target = _referenced_path(root, key, manifest.get(key, default), report)
        if target is not None:
            _validate_directory(target, key, report)

    return report


__all__ = [
    "BundleReport",
    "CORE_LINE_BUDGET",
    "DEFAULT_CORE",
    "DEFAULT_REFERENCES_DIR",
    "DEFAULT_RULES_DIR",
    "SCHEMA_VERSION",
    "validate_bundle",
]
