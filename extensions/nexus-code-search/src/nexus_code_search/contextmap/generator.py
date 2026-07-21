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

import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

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
from nexus_code_search.contextmap.tokens import count_tokens
from nexus_code_search.db.schema import open_database

MAP_FILENAME = "CONTEXT-MAP.md"
CONTEXT_DIRNAME = "context"
INDEX_FILENAME = "index.md"

# Cap on how many key symbols an individual module article lists, so a large
# module does not blow up the map. Files and counts are always complete.
MAX_KEY_SYMBOLS = 25

_META_PREFIX = "<!-- nexus-context-map"
_TOKENS_RE = re.compile(r"tokens:\s*(\d+)")
_SOURCE_HASH_RE = re.compile(r"source-hash:\s*([0-9a-f]+)")

_INTRO = (
    "This map is a deterministic, committed summary of the codebase, compiled "
    "from a local AST graph by `nexus-code-search`. Regenerate it with "
    "`nexus-hub map` or the `generate_context_map` tool. Do not edit by hand."
)
_MOST_IMPORTED_PLACEHOLDER = (
    "Populated by the graph-enrichment pass (file-level import-edge ranking), a "
    "view distinct from symbol-level impact. Not yet available in this map."
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
        model = _load_model(conn, root_path.name)
    finally:
        conn.close()

    nexus_dir = root_path / ".nexus"
    map_path = nexus_dir / MAP_FILENAME
    context_dir = nexus_dir / CONTEXT_DIRNAME

    if not force and _is_unchanged(map_path, context_dir, model.source_hash):
        return _collect_result(root_path, model, skipped=True)

    _write_outputs(root_path, model)
    return _collect_result(root_path, model, skipped=False)


# --- Graph -> model ---------------------------------------------------------


def _load_model(conn: sqlite3.Connection, root_name: str) -> ContextMapModel:
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
    source_hash = compute_source_hash([(p, h) for _, p, _, h in file_rows])

    return ContextMapModel(
        root_name=root_name,
        total_files=len(files_by_id),
        total_symbols=total_symbols,
        languages=languages,
        modules=tuple(modules),
        source_hash=source_hash,
    )


def _module_of(path: str) -> str:
    parts = path.split("/")
    return parts[0] if len(parts) > 1 else ROOT_MODULE


def _symbol_sort_key(symbol: SymbolEntry) -> tuple[str, str, str]:
    return (symbol.kind, symbol.name, symbol.qualified_name)


# --- Rendering --------------------------------------------------------------


def _document(h1: str, body_lines: list[str], source_hash: str) -> str:
    """Render a document with a token-count header placed after the H1.

    The token count is measured over the document EXCLUDING its own metadata
    line, which avoids the circular dependency where the digit count would
    change the token count. Every output file carries this header.
    """
    without_meta = "\n".join([h1, "", *body_lines]) + "\n"
    tokens = count_tokens(without_meta)
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

    lines.extend(["", "## Most-Imported Files", "", _MOST_IMPORTED_PLACEHOLDER])

    lines.extend(["", "## Context Articles", ""])
    lines.append("Per-module detail lives under `.nexus/context/`:")
    lines.append("")
    lines.append(f"- [Overview]({CONTEXT_DIRNAME}/{INDEX_FILENAME})")
    for module in model.modules:
        filename = _article_filename(module.name)
        lines.append(f"- [`{module.name}`]({CONTEXT_DIRNAME}/{filename})")
    return lines


def _index_body_lines(model: ContextMapModel) -> list[str]:
    lines: list[str] = [
        "Back to the [context map](../CONTEXT-MAP.md).",
        "",
        "Per-module articles:",
        "",
    ]
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
    )
