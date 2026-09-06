"""Compile the local AST graph into a committed, deterministic context map.

The generator reads the nodes / edges / files the tree-sitter graph already
stores in ``codegraph.db`` and emits, under the repository's ``.nexus/``
directory only:

- ``.nexus/CONTEXT-MAP.md``     a single overview map with a token-count header.
- ``.nexus/context/index.md``   an article index.
- ``.nexus/context/<module>.md`` one article per top-level module.

Design guarantees, all exercised by the test suite:

- **Neutral path**: every write is confined to ``<root>/.nexus/``. AI-config
  files (CLAUDE.md, AGENTS.md, .cursorrules, ...) are owned by the Nexus-Hub
  installer and are never touched here.
- **Deterministic**: output is a pure function of the graph. No wall-clock
  timestamp is written, so the MCP tool and the ``nexus-hub map`` CLI produce
  byte-identical output for the same input.
- **Content-hash incremental**: a source fingerprint is embedded in the map;
  regenerating on an unchanged graph is a no-op unless ``force`` is set.

Local-only by policy: no network calls, no model downloads, no telemetry.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from nexus_code_search.contextmap.env import (
    audit_env_vars,
    env_example_fingerprint_files,
)
from nexus_code_search.contextmap.components import extract_components
from nexus_code_search.contextmap.events import detect_events
from nexus_code_search.contextmap.middleware import detect_middleware
from nexus_code_search.contextmap.model import (
    GENERATOR_VERSION,
    ROOT_MODULE,
    SIGNIFICANT_KINDS,
    ContextMapModel,
    FileEntry,
    ModuleSummary,
    SymbolEntry,
    compute_source_hash,
)
from nexus_code_search.contextmap.routes import extract_routes
from nexus_code_search.contextmap.schema import (
    extract_schema,
    prisma_fingerprint_files,
)
from nexus_code_search.contextmap.tokens import count_tokens
from nexus_code_search.db.schema import open_database
from nexus_code_search.graph.affected import most_imported_files

MAP_FILENAME = "CONTEXT-MAP.md"
CONTEXT_DIRNAME = "context"
INDEX_FILENAME = "index.md"
ROUTES_FILENAME = "routes.md"
DATABASE_FILENAME = "database.md"

# Cap on how many key symbols an individual module article lists, so a large
# module does not blow up the map. Files and counts are always complete.
MAX_KEY_SYMBOLS = 25

# Cap on how many routes the top-level map table lists inline; the full set
# always lives in the routes article.
MAX_ROUTES_IN_MAP = 100

# Cap on how many most-imported files the map lists.
MAX_HOT_FILES = 25

_META_PREFIX = "<!-- nexus-context-map"
_TOKENS_RE = re.compile(r"tokens:\s*(\d+)")
_SOURCE_HASH_RE = re.compile(r"source-hash:\s*([0-9a-f]+)")

_INTRO = (
    "This map is a deterministic, committed summary of the codebase, compiled "
    "from a local AST graph by `nexus-code-search`. Regenerate it with "
    "`nexus-hub map` or the `generate_context_map` tool. Do not edit by hand."
)
_HOT_FILES_NOTE = (
    "File-level ranking by inbound import count (which files break the most on "
    "change). This is a file-level view, distinct from the symbol-level "
    "`code_impact` blast radius."
)


@dataclass(frozen=True)
class ContextMapResult:
    """Outcome of a generation run, returned to the MCP tool and the CLI."""

    root: str
    map_path: str
    context_dir: str
    article_paths: list[str] = field(default_factory=list)
    map_tokens: int = 0
    total_tokens: int = 0
    source_hash: str = ""
    skipped: bool = False
    files_indexed: int = 0
    symbols: int = 0
    modules: int = 0
    routes_count: int = 0
    models_count: int = 0
    components_count: int = 0
    env_count: int = 0
    events_count: int = 0

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "map_path": self.map_path,
            "context_dir": self.context_dir,
            "article_paths": self.article_paths,
            "map_tokens": self.map_tokens,
            "total_tokens": self.total_tokens,
            "source_hash": self.source_hash,
            "skipped": self.skipped,
            "files_indexed": self.files_indexed,
            "symbols": self.symbols,
            "modules": self.modules,
            "routes_count": self.routes_count,
            "models_count": self.models_count,
            "components_count": self.components_count,
            "env_count": self.env_count,
            "events_count": self.events_count,
        }


def generate_context_map(
    root: Path | str, index_dir: Path | str, *, force: bool = False
) -> ContextMapResult:
    """Compile ``<root>/.nexus/CONTEXT-MAP.md`` (and articles) from the graph.

    ``index_dir`` is the code-search index directory that holds ``codegraph.db``
    (``<root>/.nexus/code-index`` in the default layout). Returns a
    :class:`ContextMapResult`; when the graph is unchanged and ``force`` is
    False, the existing files are left untouched and ``skipped`` is True.
    """
    root_path = Path(root).resolve()
    index_path = Path(index_dir).resolve()

    conn = open_database(index_path)
    try:
        model = _load_model(conn, root_path)
    finally:
        conn.close()

    nexus_dir = root_path / ".nexus"
    map_path = nexus_dir / MAP_FILENAME
    context_dir = nexus_dir / CONTEXT_DIRNAME

    if not force and _is_unchanged(map_path, context_dir, model.source_hash):
        return _collect_result(root_path, model, skipped=True)

    _write_outputs(root_path, model)
    return _collect_result(root_path, model, skipped=False)


@dataclass(frozen=True)
class TokenEstimate:
    """Token counts + entity counts for a map, computed WITHOUT writing files."""

    map_tokens: int
    total_tokens: int
    files_indexed: int
    routes_count: int
    models_count: int
    components_count: int
    env_count: int
    events_count: int


def estimate_map_tokens(root: Path | str, index_dir: Path | str) -> TokenEstimate:
    """Compute the map + article token counts in memory (no `.nexus/` writes).

    Used by the benchmark to measure a repo's map cost without polluting it. The
    per-document token counts match exactly what a written map would report
    (each is measured over the document minus its metadata line).
    """
    root_path = Path(root).resolve()
    conn = open_database(Path(index_dir).resolve())
    try:
        model = _load_model(conn, root_path)
    finally:
        conn.close()

    total = _document_tokens("# Codebase Context Map", _map_body_lines(model))
    map_tokens = total
    total += _document_tokens("# Context Articles", _index_body_lines(model))
    if model.routes:
        total += _document_tokens("# Routes", _routes_article_lines(model))
    if model.models:
        total += _document_tokens("# Database", _database_article_lines(model))
    for module in model.modules:
        total += _document_tokens(
            f"# Module: `{module.name}`", _article_body_lines(module)
        )

    return TokenEstimate(
        map_tokens=map_tokens,
        total_tokens=total,
        files_indexed=model.total_files,
        routes_count=len(model.routes),
        models_count=len(model.models),
        components_count=len(model.components),
        env_count=len(model.env_vars),
        events_count=len(model.events),
    )


# --- Graph -> model ---------------------------------------------------------


def _load_model(conn: sqlite3.Connection, root: Path) -> ContextMapModel:
    cur = conn.cursor()
    file_rows = cur.execute(
        "SELECT id, path, language, content_hash FROM files"
    ).fetchall()
    node_rows = cur.execute(
        "SELECT file_id, name, kind, qualified_name FROM nodes"
    ).fetchall()

    files_by_id: dict[int, tuple[str, str]] = {
        fid: (path, language) for fid, path, language, _ in file_rows
    }

    symbols_by_file: dict[int, list[SymbolEntry]] = defaultdict(list)
    for file_id, name, kind, qualified_name in node_rows:
        if kind not in SIGNIFICANT_KINDS:
            continue
        entry = files_by_id.get(file_id)
        if entry is None:
            continue
        symbols_by_file[file_id].append(
            SymbolEntry(
                name=name,
                kind=kind,
                qualified_name=qualified_name,
                file_path=entry[0],
            )
        )

    module_files: dict[str, list[FileEntry]] = defaultdict(list)
    module_symbols: dict[str, list[SymbolEntry]] = defaultdict(list)
    language_counts: dict[str, int] = defaultdict(int)
    total_symbols = 0

    for file_id, (path, language) in files_by_id.items():
        symbols = symbols_by_file.get(file_id, [])
        module = _module_of(path)
        module_files[module].append(
            FileEntry(path=path, language=language, symbol_count=len(symbols))
        )
        module_symbols[module].extend(symbols)
        language_counts[language] += 1
        total_symbols += len(symbols)

    modules: list[ModuleSummary] = []
    for name in sorted(module_files):
        files = tuple(sorted(module_files[name], key=lambda f: f.path))
        symbols = module_symbols[name]
        key_symbols = tuple(sorted(symbols, key=_symbol_sort_key)[:MAX_KEY_SYMBOLS])
        modules.append(
            ModuleSummary(
                name=name,
                file_count=len(files),
                symbol_count=len(symbols),
                files=files,
                key_symbols=key_symbols,
            )
        )

    languages = tuple(sorted(language_counts.items(), key=lambda kv: (-kv[1], kv[0])))

    # Framework-extraction passes. Routes/schema read the graph; env + middleware
    # + components + events scan the indexed source files (and env-example / .prisma
    # files for env NAMES / schema, which are not code nodes).
    code_files = [(path, language) for _, path, language, _ in file_rows]
    routes = tuple(extract_routes(conn, root))
    env_vars = tuple(audit_env_vars(root, code_files))
    middleware = tuple(detect_middleware(root, code_files))
    models = tuple(extract_schema(conn, root))
    components = tuple(extract_components(root, code_files))
    events = tuple(detect_events(root, code_files))
    hot_files = tuple(most_imported_files(conn, limit=MAX_HOT_FILES))

    source_hash = _source_fingerprint(root, [(p, h) for _, p, _, h in file_rows])

    return ContextMapModel(
        root_name=root.name,
        total_files=len(files_by_id),
        total_symbols=total_symbols,
        languages=languages,
        modules=tuple(modules),
        source_hash=source_hash,
        routes=routes,
        env_vars=env_vars,
        middleware=middleware,
        models=models,
        components=components,
        events=events,
        hot_files=hot_files,
    )


def _source_fingerprint(root: Path, file_rows: list[tuple[str, str]]) -> str:
    """Fingerprint over the graph's files PLUS any non-code file an extractor
    reads (env-example + .prisma), so a change to one still invalidates the map.
    Single source of truth, shared by the generator and the map-health lint."""
    fingerprint_rows = list(file_rows)
    for env_file in env_example_fingerprint_files(root):
        fingerprint_rows.append(
            (_relative(root, env_file), f"env:{_hash_file(env_file)}")
        )
    for prisma_file in prisma_fingerprint_files(root):
        fingerprint_rows.append(
            (_relative(root, prisma_file), f"prisma:{_hash_file(prisma_file)}")
        )
    return compute_source_hash(fingerprint_rows)


def current_source_hash(root: Path, index_dir: Path) -> str:
    """Recompute the current source fingerprint from the graph + non-code files.

    Used by the map-health lint to detect staleness (the map's embedded
    source-hash vs the current one). Matches exactly what the generator embeds.
    """
    conn = open_database(index_dir)
    try:
        file_rows = conn.execute("SELECT path, content_hash FROM files").fetchall()
    finally:
        conn.close()
    return _source_fingerprint(root, [(p, h) for p, h in file_rows])


def _hash_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        return "0"


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _module_of(path: str) -> str:
    parts = path.split("/")
    return parts[0] if len(parts) > 1 else ROOT_MODULE


def _symbol_sort_key(symbol: SymbolEntry) -> tuple[str, str, str]:
    return (symbol.kind, symbol.name, symbol.qualified_name)


# --- Rendering --------------------------------------------------------------


def _document_tokens(h1: str, body_lines: list[str]) -> int:
    """Token count of a document excluding its (not-yet-added) metadata line."""
    return count_tokens("\n".join([h1, "", *body_lines]) + "\n")


def _document(h1: str, body_lines: list[str], source_hash: str) -> str:
    """Render a document with a token-count header placed after the H1.

    The token count is measured over the document EXCLUDING its own metadata
    line, which avoids the circular dependency where the digit count would
    change the token count. Every output file carries this header.
    """
    tokens = _document_tokens(h1, body_lines)
    meta = (
        f"{_META_PREFIX} v{GENERATOR_VERSION} | "
        f"source-hash: {source_hash} | tokens: {tokens} -->"
    )
    return "\n".join([h1, meta, "", *body_lines]) + "\n"


def _map_body_lines(model: ContextMapModel) -> list[str]:
    lines: list[str] = [_INTRO, "", "## Overview", ""]
    lines.append(f"- Root: `{model.root_name}`")
    lines.append(f"- Files indexed: {model.total_files}")
    lines.append(f"- Symbols: {model.total_symbols}")
    lines.append(f"- Modules: {len(model.modules)}")
    if model.languages:
        langs = ", ".join(f"{lang} ({count})" for lang, count in model.languages)
    else:
        langs = "none detected"
    lines.append(f"- Languages: {langs}")
    frameworks = _detected_frameworks(model)
    if frameworks:
        lines.append(f"- Frameworks: {', '.join(frameworks)}")

    lines.extend(["", "## Module Structure", ""])
    if model.modules:
        lines.append("| Module | Files | Symbols |")
        lines.append("| --- | --- | --- |")
        for module in model.modules:
            lines.append(
                f"| `{module.name}` | {module.file_count} | {module.symbol_count} |"
            )
    else:
        lines.append(
            "No indexed files found. Run the `index_graph` tool (or "
            "`nexus-hub` indexing) for this repository first."
        )

    lines.extend(_routes_section(model, limit=MAX_ROUTES_IN_MAP))
    lines.extend(_environment_section(model))
    lines.extend(_middleware_section(model))
    lines.extend(_schema_section(model))
    lines.extend(_components_section(model))
    lines.extend(_events_section(model))

    lines.extend(_hot_files_section(model))

    lines.extend(["", "## Context Articles", ""])
    lines.append("Per-module detail lives under `.nexus/context/`:")
    lines.append("")
    lines.append(f"- [Overview]({CONTEXT_DIRNAME}/{INDEX_FILENAME})")
    if model.routes:
        lines.append(f"- [Routes]({CONTEXT_DIRNAME}/{ROUTES_FILENAME})")
    if model.models:
        lines.append(f"- [Database]({CONTEXT_DIRNAME}/{DATABASE_FILENAME})")
    for module in model.modules:
        filename = _article_filename(module.name)
        lines.append(f"- [`{module.name}`]({CONTEXT_DIRNAME}/{filename})")
    return lines


def _detected_frameworks(model: ContextMapModel) -> list[str]:
    """Best-effort frameworks, inferred from the detected routes and middleware."""
    names = {r.framework for r in model.routes if r.framework}
    names |= {m.framework for m in model.middleware if m.framework}
    return sorted(names)


def _routes_section(model: ContextMapModel, *, limit: int | None) -> list[str]:
    lines = ["", "## Routes", ""]
    if not model.routes:
        lines.append(
            "No routes detected. Framework route detection covers FastAPI, "
            "Flask, Django, and Express."
        )
        return lines
    shown = model.routes if limit is None else model.routes[:limit]
    lines.append("| Method | Path | Params | Tags | Handler | Source |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for route in shown:
        lines.append(_route_row(route))
    if limit is not None and len(model.routes) > limit:
        remaining = len(model.routes) - limit
        lines.append("")
        lines.append(
            f"...{remaining} more route(s) in "
            f"[{CONTEXT_DIRNAME}/{ROUTES_FILENAME}]({CONTEXT_DIRNAME}/{ROUTES_FILENAME})."
        )
    return lines


def _route_row(route) -> str:
    params = ", ".join(route.params) if route.params else "-"
    tags = ", ".join(route.behavior_tags) if route.behavior_tags else "-"
    handler = route.handler or "-"
    return (
        f"| {route.method} | `{route.path}` | {params} | {tags} | "
        f"`{handler}` | `{route.source_file}` |"
    )


def _environment_section(model: ContextMapModel) -> list[str]:
    lines = ["", "## Environment", ""]
    if not model.env_vars:
        lines.append("No environment variables detected.")
        return lines
    lines.append("| Variable | Required | Source |")
    lines.append("| --- | --- | --- |")
    for var in model.env_vars:
        required = "yes" if var.required else "no"
        lines.append(f"| `{var.name}` | {required} | `{var.source_file}` |")
    return lines


def _middleware_section(model: ContextMapModel) -> list[str]:
    lines = ["", "## Middleware", ""]
    if not model.middleware:
        lines.append("No middleware detected.")
        return lines
    lines.append("| Middleware | Category | Framework | Source |")
    lines.append("| --- | --- | --- | --- |")
    for mw in model.middleware:
        lines.append(
            f"| `{mw.name}` | {mw.category} | {mw.framework} | `{mw.source_file}` |"
        )
    return lines


def _schema_section(model: ContextMapModel) -> list[str]:
    lines = ["", "## Data Models", ""]
    if not model.models:
        lines.append(
            "No ORM models detected. Schema detection covers SQLAlchemy, Django "
            "ORM, and Prisma."
        )
        return lines
    lines.append("| Model | Framework | Fields | Relations | Source |")
    lines.append("| --- | --- | --- | --- | --- |")
    for m in model.models:
        lines.append(
            f"| `{m.name}` | {m.framework} | {len(m.fields)} | {len(m.relations)} | "
            f"`{m.source_file}` |"
        )
    lines.append("")
    lines.append(
        f"Full field / key / relation detail: "
        f"[{CONTEXT_DIRNAME}/{DATABASE_FILENAME}]({CONTEXT_DIRNAME}/{DATABASE_FILENAME})."
    )
    return lines


def _components_section(model: ContextMapModel) -> list[str]:
    lines = ["", "## Components", ""]
    if not model.components:
        lines.append("No UI components detected. Component detection covers React.")
        return lines
    lines.append("| Component | Framework | Props |")
    lines.append("| --- | --- | --- |")
    for comp in model.components:
        props = ", ".join(comp.props) if comp.props else "-"
        lines.append(f"| `{comp.name}` | {comp.framework} | {props} |")
    return lines


def _events_section(model: ContextMapModel) -> list[str]:
    lines = ["", "## Events", ""]
    if not model.events:
        lines.append("No background-work surfaces detected.")
        return lines
    lines.append("| Name | Kind | Source |")
    lines.append("| --- | --- | --- |")
    for event in model.events:
        lines.append(f"| `{event.name}` | {event.kind} | `{event.source_file}` |")
    return lines


def _hot_files_section(model: ContextMapModel) -> list[str]:
    lines = ["", "## Most-Imported Files", "", _HOT_FILES_NOTE, ""]
    if not model.hot_files:
        lines.append("No import relationships detected.")
        return lines
    lines.append("| File | Imported by |")
    lines.append("| --- | --- |")
    for path, count in model.hot_files:
        lines.append(f"| `{path}` | {count} |")
    return lines


def _index_body_lines(model: ContextMapModel) -> list[str]:
    lines: list[str] = [
        "Back to the [context map](../CONTEXT-MAP.md).",
        "",
    ]
    if model.routes or model.models:
        lines.append("Cross-cutting articles:")
        lines.append("")
        if model.routes:
            lines.append(f"- [Routes]({ROUTES_FILENAME}) - {len(model.routes)} routes")
        if model.models:
            lines.append(
                f"- [Database]({DATABASE_FILENAME}) - {len(model.models)} models"
            )
        lines.append("")
    lines.extend(["Per-module articles:", ""])
    if not model.modules:
        lines.append("No modules indexed yet.")
        return lines
    for module in model.modules:
        filename = _article_filename(module.name)
        lines.append(
            f"- [`{module.name}`]({filename}) - {module.file_count} files, "
            f"{module.symbol_count} symbols"
        )
    return lines


def _routes_article_lines(model: ContextMapModel) -> list[str]:
    lines = [
        "Back to the [context map](../CONTEXT-MAP.md) | [article index](index.md).",
        "",
        f"- Total routes: {len(model.routes)}",
        "",
        "## All Routes",
        "",
        "| Method | Path | Params | Tags | Handler | Source |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(_route_row(route) for route in model.routes)
    return lines


def _database_article_lines(model: ContextMapModel) -> list[str]:
    lines = [
        "Back to the [context map](../CONTEXT-MAP.md) | [article index](index.md).",
        "",
        f"- Total models: {len(model.models)}",
    ]
    for m in model.models:
        lines.extend(
            ["", f"## `{m.name}` ({m.framework})", "", f"Source: `{m.source_file}`", ""]
        )
        if m.fields:
            lines.append("| Field | Type | PK | FK | Unique |")
            lines.append("| --- | --- | --- | --- | --- |")
            for f in m.fields:
                lines.append(
                    f"| `{f.name}` | {f.type} | {_yn(f.primary_key)} | "
                    f"{_yn(f.foreign_key)} | {_yn(f.unique)} |"
                )
        else:
            lines.append("No scalar fields detected.")
        if m.relations:
            lines.extend(["", "Relations:", ""])
            for r in m.relations:
                lines.append(f"- `{r.name}` -> `{r.target}` ({r.kind})")
    return lines


def _yn(flag: bool) -> str:
    return "yes" if flag else "-"


def _article_body_lines(module: ModuleSummary) -> list[str]:
    lines: list[str] = [
        "Back to the [context map](../CONTEXT-MAP.md) | [article index](index.md).",
        "",
        f"- Files: {module.file_count}",
        f"- Symbols: {module.symbol_count}",
        "",
        "## Files",
        "",
    ]
    if module.files:
        lines.append("| File | Language | Symbols |")
        lines.append("| --- | --- | --- |")
        for file in module.files:
            lines.append(f"| `{file.path}` | {file.language} | {file.symbol_count} |")
    else:
        lines.append("No files in this module.")

    lines.extend(["", "## Key Symbols", ""])
    if module.key_symbols:
        lines.append("| Symbol | Kind | Location |")
        lines.append("| --- | --- | --- |")
        for symbol in module.key_symbols:
            lines.append(f"| `{symbol.name}` | {symbol.kind} | `{symbol.file_path}` |")
    else:
        lines.append("No significant symbols extracted for this module.")
    return lines


def _article_filename(module_name: str) -> str:
    if module_name == ROOT_MODULE:
        slug = "_root"
    else:
        slug = re.sub(r"[^A-Za-z0-9._-]", "-", module_name)
    return f"{slug}.md"


# --- Writing (neutral-path confined) ----------------------------------------


def _write_outputs(root: Path, model: ContextMapModel) -> None:
    nexus_dir = (root / ".nexus").resolve()
    context_dir = nexus_dir / CONTEXT_DIRNAME
    context_dir.mkdir(parents=True, exist_ok=True)

    # Clear stale, generator-owned articles so a removed module leaves no
    # orphan. Only *.md under our own context/ directory is touched.
    for stale in context_dir.glob("*.md"):
        _guard_neutral_path(stale, nexus_dir)
        stale.unlink()

    map_path = nexus_dir / MAP_FILENAME
    _write_document(
        map_path,
        _document("# Codebase Context Map", _map_body_lines(model), model.source_hash),
        nexus_dir,
    )

    index_path = context_dir / INDEX_FILENAME
    _write_document(
        index_path,
        _document("# Context Articles", _index_body_lines(model), model.source_hash),
        nexus_dir,
    )

    if model.routes:
        routes_path = context_dir / ROUTES_FILENAME
        _write_document(
            routes_path,
            _document("# Routes", _routes_article_lines(model), model.source_hash),
            nexus_dir,
        )

    if model.models:
        database_path = context_dir / DATABASE_FILENAME
        _write_document(
            database_path,
            _document("# Database", _database_article_lines(model), model.source_hash),
            nexus_dir,
        )

    for module in model.modules:
        article_path = context_dir / _article_filename(module.name)
        _write_document(
            article_path,
            _document(
                f"# Module: `{module.name}`",
                _article_body_lines(module),
                model.source_hash,
            ),
            nexus_dir,
        )


def _write_document(path: Path, content: str, nexus_dir: Path) -> None:
    _guard_neutral_path(path, nexus_dir)
    # Force LF newlines so output is byte-identical across operating systems.
    path.write_text(content, encoding="utf-8", newline="\n")


def _guard_neutral_path(path: Path, nexus_dir: Path) -> None:
    """Refuse to write anywhere outside ``<root>/.nexus/`` (defence in depth)."""
    if not path.resolve().is_relative_to(nexus_dir):
        raise RuntimeError(f"refusing to write outside .nexus/: {path.resolve()}")


# --- No-op detection + result assembly --------------------------------------


def _is_unchanged(map_path: Path, context_dir: Path, source_hash: str) -> bool:
    if not map_path.exists() or not context_dir.exists():
        return False
    return _read_source_hash(map_path) == source_hash


def _read_source_hash(path: Path) -> str | None:
    for line in _meta_lines(path):
        match = _SOURCE_HASH_RE.search(line)
        if match:
            return match.group(1)
    return None


def _read_token_header(path: Path) -> int:
    for line in _meta_lines(path):
        match = _TOKENS_RE.search(line)
        if match:
            return int(match.group(1))
    return 0


def _meta_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(_META_PREFIX)
    ]


def _collect_result(
    root: Path, model: ContextMapModel, *, skipped: bool
) -> ContextMapResult:
    nexus_dir = root / ".nexus"
    map_path = nexus_dir / MAP_FILENAME
    context_dir = nexus_dir / CONTEXT_DIRNAME
    article_paths = sorted(str(p) for p in context_dir.glob("*.md"))
    map_tokens = _read_token_header(map_path)
    total_tokens = map_tokens + sum(_read_token_header(Path(p)) for p in article_paths)
    return ContextMapResult(
        root=str(root),
        map_path=str(map_path),
        context_dir=str(context_dir),
        article_paths=article_paths,
        map_tokens=map_tokens,
        total_tokens=total_tokens,
        source_hash=model.source_hash,
        skipped=skipped,
        files_indexed=model.total_files,
        symbols=model.total_symbols,
        modules=len(model.modules),
        routes_count=len(model.routes),
        models_count=len(model.models),
        components_count=len(model.components),
        env_count=len(model.env_vars),
        events_count=len(model.events),
    )
