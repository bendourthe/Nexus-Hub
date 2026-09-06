"""Data model for the compiled context map.

Pure data plus a deterministic input fingerprint: no I/O and no rendering here.
The generator builds these records from the AST graph and renders them to
Markdown. Keeping the model rendering-free means the same records can later feed
additional output formats without touching the extraction path.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

# Bumped when the compiled-map format changes in a way that should invalidate a
# previously committed map even though the source tree is unchanged. It is part
# of the source fingerprint, so a format change forces a regeneration.
# v2 (Phase 2): adds Routes / Environment / Middleware sections.
# v3 (Phase 3): adds Schema / Components / Events sections.
# v4 (Phase 4): fills the Most-Imported Files section (file-level hot-file ranking).
GENERATOR_VERSION = "4"

# Node kinds that count as a "symbol" for the overview and per-module rollups.
# The synthetic ``file`` node and structural kinds (import / export / parameter
# / plain variable) are excluded so the counts reflect the declarations a reader
# actually navigates by.
SIGNIFICANT_KINDS: frozenset[str] = frozenset(
    {
        "class",
        "struct",
        "interface",
        "trait",
        "protocol",
        "function",
        "method",
        "enum",
        "type_alias",
        "namespace",
        "component",
        "route",
        "constant",
    }
)

# Bucket name for files that sit directly at the repository root (no top-level
# directory segment). Chosen so it sorts before real directory names and can
# never collide with one (parentheses are not valid in a path segment here).
ROOT_MODULE = "(root)"


@dataclass(frozen=True)
class SymbolEntry:
    """A single significant declaration surfaced in a module article."""

    name: str
    kind: str
    qualified_name: str
    file_path: str


@dataclass(frozen=True)
class FileEntry:
    """One indexed file and its significant-symbol count."""

    path: str
    language: str
    symbol_count: int


@dataclass(frozen=True)
class ModuleSummary:
    """A top-level module (directory) rollup for the compiled map."""

    name: str
    file_count: int
    symbol_count: int
    files: tuple[FileEntry, ...]
    key_symbols: tuple[SymbolEntry, ...]


@dataclass(frozen=True)
class RouteInfo:
    """One HTTP route surfaced from a framework `route` node in the graph."""

    framework: str
    method: str
    path: str
    params: tuple[str, ...]
    handler: str
    handler_file: str
    behavior_tags: tuple[str, ...]
    source_file: str


@dataclass(frozen=True)
class EnvVar:
    """One environment variable referenced in code or declared in a
    `.env.example`-style file. Values are NEVER read or stored - name only."""

    name: str
    required: bool
    source_file: str


@dataclass(frozen=True)
class MiddlewareInfo:
    """One middleware registration, categorized by a conservative name match."""

    name: str
    category: str
    framework: str
    source_file: str


@dataclass(frozen=True)
class FieldInfo:
    """One ORM model field."""

    name: str
    type: str
    primary_key: bool = False
    foreign_key: bool = False
    unique: bool = False


@dataclass(frozen=True)
class RelationInfo:
    """One relation from an ORM model to another model."""

    name: str
    target: str
    kind: str  # e.g. one-to-many, many-to-one, many-to-many, one-to-one, relation


@dataclass(frozen=True)
class ModelInfo:
    """One ORM model / table surfaced from the source."""

    name: str
    framework: str
    source_file: str
    fields: tuple[FieldInfo, ...] = ()
    relations: tuple[RelationInfo, ...] = ()


@dataclass(frozen=True)
class ComponentInfo:
    """One UI component with its props (names only)."""

    name: str
    framework: str
    props: tuple[str, ...]
    source_file: str


@dataclass(frozen=True)
class EventInfo:
    """One background-work / event surface (task, queue, topic, emitter)."""

    name: str
    kind: str
    source_file: str


@dataclass(frozen=True)
class ContextMapModel:
    """The full compiled-map content model, ready to render deterministically."""

    root_name: str
    total_files: int
    total_symbols: int
    languages: tuple[tuple[str, int], ...]
    modules: tuple[ModuleSummary, ...]
    source_hash: str
    routes: tuple[RouteInfo, ...] = ()
    env_vars: tuple[EnvVar, ...] = ()
    middleware: tuple[MiddlewareInfo, ...] = ()
    models: tuple[ModelInfo, ...] = ()
    components: tuple[ComponentInfo, ...] = ()
    events: tuple[EventInfo, ...] = ()
    hot_files: tuple[tuple[str, int], ...] = ()


def compute_source_hash(file_hash_rows: list[tuple[str, str]]) -> str:
    """Return a short, stable fingerprint of the graph's file set.

    The digest covers the sorted ``(path, content_hash)`` pairs plus the
    generator version, so an unchanged tree always regenerates to the same hash
    (the no-op guarantee) and a generator-format change invalidates old maps.
    Sixteen hex characters is ample collision resistance for a per-repo marker.
    """
    digest = hashlib.sha256()
    digest.update(GENERATOR_VERSION.encode("utf-8"))
    for path, content_hash in sorted(file_hash_rows):
        digest.update(b"\x00")
        digest.update(path.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(content_hash.encode("utf-8"))
    return digest.hexdigest()[:16]
