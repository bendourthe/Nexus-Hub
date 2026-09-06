"""High-level extraction driver: walks files, dispatches to per-language
extractors, and flushes nodes / edges to SQLite.

Local-only by policy.
"""

from __future__ import annotations

import datetime as _dt
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.db.schema import open_database
from nexus_code_search.extraction.languages import LANGUAGE_EXTRACTORS
from nexus_code_search.extraction.parse_worker import parse_file
from nexus_code_search.frameworks import CONTEXT_PROVIDERS, FRAMEWORK_RESOLVERS
from nexus_code_search.indexer import hash_file, walk_files
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")


@dataclass
class ExtractionStats:
    """Summary of one extraction run."""

    files_indexed: int = 0
    nodes_inserted: int = 0
    edges_inserted: int = 0
    files_skipped: int = 0

    def to_dict(self) -> dict:
        return {
            "files_indexed": self.files_indexed,
            "nodes_inserted": self.nodes_inserted,
            "edges_inserted": self.edges_inserted,
            "files_skipped": self.files_skipped,
        }


class ExtractionOrchestrator:
    """Drive AST extraction against a repository root.

    Lifecycle:
        orch = ExtractionOrchestrator(repo_root, config, index_dir)
        stats = orch.run(force=False)
        orch.close()

    Re-running with `force=False` reuses cached rows for files whose content
    hash has not changed. The on-disk database lives at
    `<index_dir>/codegraph.db`.
    """

    def __init__(
        self,
        repo_root: Path,
        config: CodeSearchConfig,
        index_dir: Path,
        conn: sqlite3.Connection | None = None,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.config = config
        self.index_dir = index_dir.resolve()
        self._owns_conn = conn is None
        self.conn = conn if conn is not None else open_database(self.index_dir)

    def close(self) -> None:
        if self._owns_conn:
            self.conn.close()

    def __enter__(self) -> ExtractionOrchestrator:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def run(
        self,
        force: bool = False,
        progress_cb: Callable[[int, int], None] | None = None,
    ) -> ExtractionStats:
        """Index every supported file under `repo_root`.

        force=True drops every previously indexed row before re-extracting.
        progress_cb, if provided, receives (files_done, total_files).
        """
        stats = ExtractionStats()
        files = [
            p
            for p in walk_files(self.repo_root, self.config)
            if p.suffix.lower() in LANGUAGE_EXTRACTORS
            or any(provider.applies_to(p) for provider in CONTEXT_PROVIDERS)
        ]
        total = len(files)

        if force:
            self.conn.execute("DELETE FROM edges")
            self.conn.execute("DELETE FROM nodes")
            self.conn.execute("DELETE FROM files")
            self.conn.commit()

        cur = self.conn.cursor()

        for idx, path in enumerate(files, start=1):
            try:
                rel = path.relative_to(self.repo_root).as_posix()
            except ValueError:
                rel = path.as_posix()
            try:
                content_hash = hash_file(path)
            except OSError:
                stats.files_skipped += 1
                continue

            row = cur.execute(
                "SELECT id, content_hash FROM files WHERE path = ?", (rel,)
            ).fetchone()
            if row is not None and not force and row[1] == content_hash:
                if progress_cb is not None:
                    progress_cb(idx, total)
                continue

            if row is not None:
                # File changed: drop old rows and reinsert.
                cur.execute("DELETE FROM files WHERE id = ?", (row[0],))
                # Cascading FK deletes nodes; nodes_fts triggers handle FTS.

            source = self._read_bytes(path)
            if source is None:
                stats.files_skipped += 1
                continue

            language = _language_for(path)
            now = int(_dt.datetime.now(_dt.timezone.utc).timestamp())
            cur.execute(
                "INSERT INTO files(path, language, content_hash, indexed_at) VALUES(?,?,?,?)",
                (rel, language, content_hash, now),
            )
            file_id = cur.lastrowid

            if path.suffix.lower() in LANGUAGE_EXTRACTORS:
                ast_nodes, ast_edges = parse_file(path, source)
            else:
                ast_nodes, ast_edges = [], []
            framework_nodes, framework_edges = self._run_framework_resolvers(
                path, source, ast_nodes
            )
            provider_nodes, provider_edges = self._run_context_providers(
                Path(rel), source, [*ast_nodes, *framework_nodes]
            )
            all_nodes = [
                _node_with_file(n, rel)
                for n in (*ast_nodes, *framework_nodes, *provider_nodes)
            ]
            all_edges = [*ast_edges, *framework_edges, *provider_edges]
            local_to_db = self._insert_nodes(cur, all_nodes, file_id)
            self._insert_file_node(cur, all_nodes, local_to_db, file_id, rel, language)
            self._insert_edges(cur, all_edges, local_to_db)
            stats.nodes_inserted += len(all_nodes)
            stats.edges_inserted += len(all_edges)
            stats.files_indexed += 1

            if progress_cb is not None:
                progress_cb(idx, total)

        self.conn.commit()
        return stats

    def _run_framework_resolvers(
        self,
        path: Path,
        source: bytes,
        ast_nodes: list[Node],
    ) -> tuple[list[Node], list[Edge]]:
        """Invoke every registered framework resolver whose `applies_to` matches.

        Each resolver is passed the running `ast_nodes + prior framework
        nodes` list and emits new framework nodes with local indices that
        continue from `len(existing)`. Because the orchestrator merges every
        resolver's output into the same combined list (ast first, then each
        resolver's output in registration order), the indices remain valid in
        the final combined list without any rebasing.
        """
        extra_nodes: list[Node] = []
        extra_edges: list[Edge] = []
        for resolver in FRAMEWORK_RESOLVERS:
            if not resolver.applies_to(path):
                continue
            try:
                existing = ast_nodes + extra_nodes
                r_nodes, r_edges = resolver.resolve(path, source, existing)
            except Exception:  # noqa: BLE001
                logger.debug(
                    "Framework resolver %s failed for %s",
                    resolver.name,
                    path,
                    exc_info=True,
                )
                continue
            extra_nodes.extend(r_nodes)
            extra_edges.extend(r_edges)
        return extra_nodes, extra_edges

    def _run_context_providers(
        self,
        path: Path,
        source: bytes,
        existing_nodes: list[Node],
    ) -> tuple[list[Node], list[Edge]]:
        """Run matching local context providers through the resolver contract."""

        extra_nodes: list[Node] = []
        extra_edges: list[Edge] = []
        for provider in CONTEXT_PROVIDERS:
            if not provider.applies_to(path):
                continue
            try:
                current = [*existing_nodes, *extra_nodes]
                provider_nodes, provider_edges = provider.resolve(
                    path, source, current
                )
            except Exception:
                logger.debug(
                    "Context provider %s failed for %s",
                    provider.name,
                    path,
                    exc_info=True,
                )
                continue
            extra_nodes.extend(provider_nodes)
            extra_edges.extend(provider_edges)
        return extra_nodes, extra_edges

    def _read_bytes(self, path: Path) -> bytes | None:
        # Reuse the safe text path's size guard for binary content.
        try:
            if path.stat().st_size > self.config.max_file_bytes:
                return None
        except OSError:
            return None
        try:
            return path.read_bytes()
        except OSError:
            return None

    def _insert_nodes(
        self,
        cur: sqlite3.Cursor,
        nodes: Iterable[Node],
        file_id: int,
    ) -> dict[int, int]:
        """Insert each node and return a map local-index -> database id."""
        local_to_db: dict[int, int] = {}
        for local_idx, node in enumerate(nodes):
            cur.execute(
                "INSERT INTO nodes(name, kind, qualified_name, file_id, start_line, end_line, signature, docstring) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (
                    node.name,
                    node.kind.value,
                    node.qualified_name,
                    file_id,
                    node.start_line,
                    node.end_line,
                    node.signature,
                    node.docstring,
                ),
            )
            local_to_db[local_idx] = cur.lastrowid
        return local_to_db

    def _insert_file_node(
        self,
        cur: sqlite3.Cursor,
        nodes: list[Node],
        local_to_db: dict[int, int],
        file_id: int,
        rel: str,
        language: str,
    ) -> None:
        """Insert a synthetic `file` node and a `contains` edge to the
        first module node so file-level queries surface."""
        cur.execute(
            "INSERT INTO nodes(name, kind, qualified_name, file_id, start_line, end_line, signature, docstring) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (rel, NodeKind.FILE.value, rel, file_id, 1, 1, language, ""),
        )
        file_node_id = cur.lastrowid
        if 0 in local_to_db:
            cur.execute(
                "INSERT INTO edges(source_id, target_id, kind, call_site_line) VALUES(?,?,?,?)",
                (file_node_id, local_to_db[0], EdgeKind.CONTAINS.value, 0),
            )

    def _insert_edges(
        self,
        cur: sqlite3.Cursor,
        edges: Iterable[Edge],
        local_to_db: dict[int, int],
    ) -> None:
        for edge in edges:
            src = local_to_db.get(edge.source_id)
            tgt = local_to_db.get(edge.target_id)
            if src is None or tgt is None:
                continue
            cur.execute(
                "INSERT INTO edges(source_id, target_id, kind, call_site_line) VALUES(?,?,?,?)",
                (src, tgt, edge.kind.value, edge.call_site_line),
            )


def _language_for(path: Path) -> str:
    s = path.suffix.lower()
    if s in (".py", ".pyi"):
        return "python"
    if s in (".ts", ".mts", ".cts"):
        return "typescript"
    if s == ".tsx":
        return "tsx"
    if s == ".go":
        return "go"
    if s == ".rs":
        return "rust"
    if s == ".java":
        return "java"
    if s in (".cs", ".csx"):
        return "csharp"
    return s.lstrip(".") or "unknown"


def _node_with_file(node: Node, rel: str) -> Node:
    if node.file_path == rel:
        return node
    return Node(
        name=node.name,
        kind=node.kind,
        qualified_name=node.qualified_name,
        file_path=rel,
        start_line=node.start_line,
        end_line=node.end_line,
        signature=node.signature,
        docstring=node.docstring,
        id=node.id,
    )
