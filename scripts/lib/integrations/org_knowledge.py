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
import os
import re
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .result import FileAction

SCHEMA_VERSION = 1
CORE_LINE_BUDGET = 200
DEFAULT_CORE = "core.md"
DEFAULT_RULES_DIR = "rules/"
DEFAULT_REFERENCES_DIR = "references/"
DEFAULT_PRECEDENCE_STATEMENT = (
    "The organization standards in this section take precedence over any "
    "conflicting generic guidance elsewhere in this file."
)
ORG_START_MARKER = "<!-- NEXUS_HUB_ORG_START -->"
ORG_END_MARKER = "<!-- NEXUS_HUB_ORG_END -->"
NEXUS_END_MARKER = "<!-- NEXUS_HUB_END -->"

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


@dataclass(frozen=True)
class PlatformPosture:
    """One static classification for an organization projection surface."""

    classification: str
    justification: str


_UNCLASSIFIED_POSTURE = PlatformPosture(
    "advisory (unclassified)",
    "No verified platform precedence mechanism is recorded; treat the projection as guidance only.",
)

PLATFORM_POSTURES: dict[str, PlatformPosture] = {
    "aider": _UNCLASSIFIED_POSTURE,
    "antigravity": PlatformPosture(
        "default", "General-to-specific instruction loading applies to the projected rules file."
    ),
    "antigravity2": PlatformPosture(
        "default", "General-to-specific instruction loading applies to the projected AGENTS.md surface."
    ),
    "claude": PlatformPosture(
        "default", "The projected local instruction layer is loaded, but it is not a managed policy layer."
    ),
    "codex": PlatformPosture(
        "default", "AGENTS.md participates in Codex's root-to-leaf instruction hierarchy."
    ),
    "copilot": PlatformPosture(
        "advisory",
        "Personal > Repository > Organization; this personal-over-org documented inversion is soft priority only.",
    ),
    "cursor": PlatformPosture(
        "default", "The projected project instruction layer sits below Team Rules and above user rules."
    ),
    "gemini": PlatformPosture(
        "default", "General-to-specific instruction loading applies to the projected GEMINI.md surface."
    ),
    "gemini-cli": PlatformPosture(
        "default", "General-to-specific instruction loading applies to the projected GEMINI.md surface."
    ),
    "hermes": _UNCLASSIFIED_POSTURE,
    "kimi": _UNCLASSIFIED_POSTURE,
    "nexus-ai": _UNCLASSIFIED_POSTURE,
    "openclaw": _UNCLASSIFIED_POSTURE,
    "opencode": _UNCLASSIFIED_POSTURE,
    "qwen": _UNCLASSIFIED_POSTURE,
    "windsurf": _UNCLASSIFIED_POSTURE,
}


def platform_posture(key: str) -> PlatformPosture:
    """Return a posture without raising when a new integration is unclassified."""

    return PLATFORM_POSTURES.get(key, _UNCLASSIFIED_POSTURE)


def platform_posture_rows(
    platform_keys: list[str] | None = None,
) -> list[tuple[str, str, str]]:
    """Return stable posture rows for the registry or an explicit key list."""

    if platform_keys is None:
        # The installed CLI loads this file as a standalone module to avoid
        # importing the full integration registry. Tests assert this static
        # roster remains identical to the registry's registered keys.
        platform_keys = list(PLATFORM_POSTURES)
    return [
        (key, platform_posture(key).classification, platform_posture(key).justification)
        for key in sorted(platform_keys)
    ]


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


def render_org_block(report: BundleReport) -> str:
    """Render the deterministic body placed between organization markers."""

    if not report.valid:
        raise ValueError("cannot render an invalid organization bundle")
    manifest = report.manifest
    core_path = report.bundle_path / str(manifest.get("core", DEFAULT_CORE))
    references_path = report.bundle_path / str(
        manifest.get("references_dir", DEFAULT_REFERENCES_DIR)
    )
    core = core_path.read_text(encoding="utf-8").strip()
    org_name = str(manifest["org_name"]).strip()
    precedence = str(
        manifest.get("precedence_statement", DEFAULT_PRECEDENCE_STATEMENT)
    ).strip()
    return (
        f"## Organization Standards ({org_name})\n\n"
        f"{precedence}\n\n"
        f"{core}\n\n"
        f"On-demand organization references: `{references_path}`."
    )


def _install_home() -> Path:
    override = os.environ.get("NEXUS_HUB_HOME")
    return Path(override).expanduser() if override else Path.home() / ".nexus-hub"


def _connected_bundle() -> tuple[Path | None, str | None]:
    """Resolve the connected bundle, distinguishing no connection from damage."""

    connection = _install_home() / "org" / "connection.json"
    if not connection.exists():
        return None, None
    try:
        state = json.loads(connection.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"connection state is unreadable ({exc})"
    if not isinstance(state, dict):
        return None, "connection state must be a JSON object"
    source_type = state.get("source_type")
    if source_type == "git":
        return _install_home() / "org" / "repo", None
    if source_type == "dir" and isinstance(state.get("source"), str):
        return _expand(state["source"]), None
    return None, "connection state declares an unsupported source"


def _track_safely(ctx: Any, method: str, integration_key: str, path: Path) -> None:
    """Keep bookkeeping failures from breaking an otherwise valid install."""

    manifest = getattr(ctx, "manifest", None)
    if manifest is None:
        return
    try:
        getattr(manifest, method)(integration_key, str(path))
    except Exception:  # noqa: BLE001 - bookkeeping must never fail installation
        return


def _instruction_paths(integration: Any, ctx: Any) -> list[Path]:
    """Read actual instruction destinations registered by the current install."""

    manifest = getattr(ctx, "manifest", None)
    if manifest is None:
        return []
    candidates = [Path(path) for path in manifest.shared_for(integration.key)]
    if getattr(integration, "instruction_mode", "shared") == "dedicated":
        filename = integration.config.get("instruction_file")
        if filename:
            candidates.extend(
                Path(path)
                for path in manifest.files_for(integration.key)
                if Path(path).name == filename
            )
    return sorted({path for path in candidates if path.is_file()}, key=str)


def _declared_rules_root(integration: Any, ctx: Any) -> Path | None:
    """Resolve the existing rules root declared for the current install scope."""

    subdir = integration.config.get("rules_subdir")
    if not subdir:
        return None
    if getattr(ctx, "scope", None) == "global":
        parent = integration.config.get("global_dir")
        if parent is None:
            return None
        return _expand(parent) / subdir
    parent = integration.config.get("workspace_dir")
    if parent is None:
        return None
    return (Path(ctx.target_root) / parent).resolve() / subdir


def _rules_roots(integration: Any, ctx: Any) -> list[Path]:
    """Discover real rules roots, including custom multi-surface integrations."""

    subdir = integration.config.get("rules_subdir")
    if not subdir:
        return []
    roots = set()
    declared = _declared_rules_root(integration, ctx)
    if declared is not None and declared.is_dir():
        roots.add(declared)
    manifest = getattr(ctx, "manifest", None)
    if manifest is not None:
        for tracked in manifest.files_for(integration.key):
            path = Path(tracked)
            indices = [index for index, part in enumerate(path.parts) if part == subdir]
            if indices:
                root = Path(*path.parts[: indices[0] + 1])
                if root.is_dir() or getattr(ctx, "dry_run", False):
                    roots.add(root)
    return sorted(roots, key=str)


def _merge_org_after_nexus(path: Path, body: str, ctx: Any) -> FileAction:
    """Merge the org block and repair any legacy placement before Nexus-Hub."""

    from scripts.lib.installer.instruction_merge import (
        merge_marker_section,
        remove_marker_section,
    )

    from .result import FileAction

    text = path.read_text(encoding="utf-8")
    misplaced = (
        ORG_START_MARKER in text
        and ORG_END_MARKER in text
        and NEXUS_END_MARKER in text
        and text.index(ORG_START_MARKER) < text.index(NEXUS_END_MARKER)
    )
    if misplaced:
        if getattr(ctx, "dry_run", False):
            return FileAction(path=str(path), action="updated")
        remove_marker_section(
            path,
            start_marker=ORG_START_MARKER,
            end_marker=ORG_END_MARKER,
        )
    return merge_marker_section(
        path,
        body,
        start_marker=ORG_START_MARKER,
        end_marker=ORG_END_MARKER,
        dry_run=bool(getattr(ctx, "dry_run", False)),
    )


def seed_org_knowledge(integration_key: str, ctx: Any) -> list[FileAction]:
    """Project a connected organization bundle into one installed platform.

    The current install's manifest supplies the real instruction and rules
    destinations. This matters for custom writers such as Cursor and
    Antigravity, and it avoids inventing a platform config key or read path.
    Expected connection, validation, file, and bookkeeping failures degrade to
    one warning and an empty action list; they never fail the platform install.
    """

    from . import get

    bundle_path, connection_error = _connected_bundle()
    if bundle_path is None and connection_error is None:
        manifest = getattr(ctx, "manifest", None)
        if manifest is not None:
            manifest.log(integration_key, "org-knowledge: no connection; skipped")
        if getattr(ctx, "verbose", False):
            _note(f"{integration_key}: no connection; skipped")
        return []
    if connection_error is not None:
        _note(f"{integration_key}: {connection_error}; skipped")
        return []

    try:
        report = validate_bundle(bundle_path)
        if not report.valid:
            detail = report.errors[0] if report.errors else "validation failed"
            _note(f"{integration_key}: invalid bundle ({detail}); skipped")
            return []
        body = render_org_block(report)
        if len(body.splitlines()) > CORE_LINE_BUDGET:
            _note(
                f"{integration_key}: rendered organization block exceeds the "
                f"{CORE_LINE_BUDGET}-line always-on budget; content was not truncated"
            )
        integration = get(integration_key)
        actions: list[FileAction] = []
        for instruction_path in _instruction_paths(integration, ctx):
            actions.append(_merge_org_after_nexus(instruction_path, body, ctx))
            _track_safely(ctx, "track_shared", integration_key, instruction_path)

        rules_source = report.bundle_path / str(report.manifest["rules_dir"])
        for rules_root in _rules_roots(integration, ctx):
            org_destination = rules_root / "org"
            actions.append(
                integration._copy_tree(
                    rules_source, org_destination, ctx, integration_key
                )
            )
            for source_file in sorted(
                (path for path in rules_source.rglob("*") if path.is_file()), key=str
            ):
                target_file = org_destination / source_file.relative_to(rules_source)
                _track_safely(ctx, "track", integration_key, target_file)
        return actions
    except Exception as exc:  # noqa: BLE001 - org projection must degrade, never fail install
        _note(f"{integration_key}: could not materialize organization knowledge ({exc}); skipped")
        return []


__all__ = [
    "CORE_LINE_BUDGET",
    "DEFAULT_CORE",
    "DEFAULT_PRECEDENCE_STATEMENT",
    "DEFAULT_REFERENCES_DIR",
    "DEFAULT_RULES_DIR",
    "ORG_END_MARKER",
    "ORG_START_MARKER",
    "PLATFORM_POSTURES",
    "SCHEMA_VERSION",
    "BundleReport",
    "PlatformPosture",
    "platform_posture",
    "platform_posture_rows",
    "render_org_block",
    "seed_org_knowledge",
    "validate_bundle",
]
