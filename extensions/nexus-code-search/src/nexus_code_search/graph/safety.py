"""Read-only edit, delete, and rename preflight verdicts."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from nexus_code_search.graph.query_manager import GraphQueryManager
from nexus_code_search.graph.traverser import _node_to_dict
from nexus_code_search.types import EdgeKind, Node, NodeKind

_OPERATIONS = ("edit", "delete", "rename")
_DEPENDENCY_KINDS = (
    EdgeKind.CALLS.value,
    EdgeKind.IMPORTS.value,
    EdgeKind.REFERENCES.value,
    EdgeKind.INSTANTIATES.value,
    EdgeKind.DECORATES.value,
    EdgeKind.EXPORTS.value,
    EdgeKind.EXTENDS.value,
    EdgeKind.IMPLEMENTS.value,
    EdgeKind.OVERRIDES.value,
)

_VERDICTS = {
    "runtime_dependency": {
        "rank": 0,
        "meaning": "A cross-file, non-test production path depends on this symbol.",
    },
    "insufficient_data": {
        "rank": 1,
        "meaning": "The local graph lacks enough indexed evidence to rank mutation risk.",
    },
    "external_contract": {
        "rank": 2,
        "meaning": "Cross-file test dependents exercise this symbol's current contract.",
    },
    "internal_dependency": {
        "rank": 3,
        "meaning": "Known dependents are confined to the symbol's defining file.",
    },
    "no_known_callers": {
        "rank": 4,
        "meaning": "No incoming caller, importer, or reference is present in the local graph.",
    },
}

_ACTIONS = {
    "edit": {
        "runtime_dependency": "Preserve behavior and signature unless every production dependent moves in the same change, then run affected paths and tests.",
        "insufficient_data": "Refresh the graph index and retry before editing; incomplete evidence cannot justify a reassuring verdict.",
        "external_contract": "Preserve the current signature and update the implementation behind it, then run the indexed tests.",
        "internal_dependency": "Update the symbol and its same-file dependents together, then run focused tests.",
        "no_known_callers": "Review dynamic, configuration, generated, and cross-repository uses before editing this possible dead-code candidate.",
    },
    "delete": {
        "runtime_dependency": "Do not delete until every production caller, importer, and reference is removed or migrated in the same change.",
        "insufficient_data": "Refresh the graph index and retry before deleting; incomplete evidence is not deletion approval.",
        "external_contract": "Do not delete until every cross-file test dependent is removed or migrated and the suite is green.",
        "internal_dependency": "Remove or migrate the symbol and every same-file dependent together, then run focused tests.",
        "no_known_callers": "Check dynamic, configuration, generated, and cross-repository uses before deleting this possible dead-code candidate.",
    },
    "rename": {
        "runtime_dependency": "Rename the symbol and every indexed production caller, importer, and reference atomically, then run affected paths and tests.",
        "insufficient_data": "Refresh the graph index and retry before renaming; incomplete evidence cannot identify the required move set.",
        "external_contract": "Rename the symbol and every cross-file test dependent in one change, then run the indexed tests.",
        "internal_dependency": "Rename the symbol and its same-file dependents together, then run focused tests.",
        "no_known_callers": "Search dynamic strings, configuration, generated code, and other repositories before renaming this locally unreferenced symbol.",
    },
}


def _is_test_path(file_path: str) -> bool:
    normalized = file_path.replace("\\", "/").lower()
    parts = normalized.split("/")
    filename = parts[-1] if parts else normalized
    stem = filename.rsplit(".", 1)[0]
    return (
        "tests" in parts
        or "test" in parts
        or filename.startswith("test_")
        or stem.endswith("_test")
    )


def _index_evidence(
    *, present: bool, files: int = 0, nodes: int = 0
) -> dict[str, int | bool]:
    return {"present": present, "files": files, "nodes": nodes}


def _empty_evidence(index: dict[str, int | bool]) -> dict[str, Any]:
    return {
        "matches": [],
        "callers": [],
        "importers": [],
        "references": [],
        "production_dependents": [],
        "external_dependents": [],
        "internal_dependents": [],
        "test_coverage": {"present": False, "files": []},
        "complexity": [],
        "cross_repo_visibility": "unavailable",
        "index": index,
    }


def _result(
    operation: str, symbol: str, tier: str, evidence: dict[str, Any]
) -> dict[str, Any]:
    verdict = _VERDICTS[tier]
    return {
        "operation": operation,
        "symbol": symbol,
        "verdict": {
            "tier": tier,
            "rank": verdict["rank"],
            "meaning": verdict["meaning"],
        },
        "recommended_action": _ACTIONS[operation][tier],
        "evidence": evidence,
    }


def _readonly_connection(db_path: Path) -> sqlite3.Connection:
    uri = f"{db_path.resolve().as_uri()}?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    connection.execute("PRAGMA query_only = ON")
    return connection


def _incoming_dependencies(
    connection: sqlite3.Connection, target: Node
) -> list[dict[str, Any]]:
    placeholders = ",".join("?" for _ in _DEPENDENCY_KINDS)
    rows = connection.execute(
        "SELECT e.kind, e.call_site_line, n.id, n.name, n.kind, "
        "n.qualified_name, f.path, n.start_line, n.end_line, n.signature, "
        "n.docstring FROM edges e JOIN nodes n ON n.id = e.source_id "
        "JOIN files f ON f.id = n.file_id "
        f"WHERE e.target_id = ? AND e.kind IN ({placeholders}) "
        "ORDER BY f.path, n.start_line, n.qualified_name, e.kind",
        (target.id, *_DEPENDENCY_KINDS),
    ).fetchall()
    dependencies: list[dict[str, Any]] = []
    for row in rows:
        source = Node(
            id=row[2],
            name=row[3],
            kind=NodeKind(row[4]),
            qualified_name=row[5],
            file_path=row[6],
            start_line=row[7],
            end_line=row[8],
            signature=row[9],
            docstring=row[10],
        )
        dependencies.append(
            {
                "edge_kind": row[0],
                "call_site_line": row[1],
                "target": _node_to_dict(target),
                "source": _node_to_dict(source),
            }
        )
    return dependencies


def _indexed_imports(
    connection: sqlite3.Connection, target: Node
) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT n.id, n.name, n.kind, n.qualified_name, f.path, "
        "n.start_line, n.end_line, n.signature, n.docstring "
        "FROM nodes n JOIN files f ON f.id = n.file_id "
        "WHERE n.kind = ? AND (n.name = ? OR n.name LIKE ?) "
        "ORDER BY f.path, n.start_line, n.qualified_name",
        (NodeKind.IMPORT.value, target.name, f"%.{target.name}"),
    ).fetchall()
    imports: list[dict[str, Any]] = []
    for row in rows:
        source = Node(
            id=row[0],
            name=row[1],
            kind=NodeKind(row[2]),
            qualified_name=row[3],
            file_path=row[4],
            start_line=row[5],
            end_line=row[6],
            signature=row[7],
            docstring=row[8],
        )
        imports.append(
            {
                "edge_kind": EdgeKind.IMPORTS.value,
                "call_site_line": source.start_line,
                "target": _node_to_dict(target),
                "source": _node_to_dict(source),
            }
        )
    return imports


def evaluate_safety(
    db_path: Path, symbol: str, operation: str
) -> dict[str, Any]:
    """Return one evidence-backed verdict without mutating the graph or tree."""

    if operation not in _OPERATIONS:
        raise ValueError(f"unsupported safety operation: {operation}")
    if not db_path.is_file():
        return _result(
            operation,
            symbol,
            "insufficient_data",
            _empty_evidence(_index_evidence(present=False)),
        )

    try:
        with closing(_readonly_connection(db_path)) as connection:
            file_count = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            node_count = connection.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            index = _index_evidence(
                present=True, files=file_count, nodes=node_count
            )
            if file_count == 0 or node_count == 0:
                return _result(
                    operation,
                    symbol,
                    "insufficient_data",
                    _empty_evidence(index),
                )

            manager = GraphQueryManager(connection)
            matches = manager._resolve_symbol(symbol, None)
            if not matches:
                return _result(
                    operation,
                    symbol,
                    "insufficient_data",
                    _empty_evidence(index),
                )

            incoming: list[dict[str, Any]] = []
            complexity: list[dict[str, Any]] = []
            for match in matches:
                match_dependencies = _incoming_dependencies(connection, match)
                existing = {
                    (
                        item["edge_kind"],
                        item["source"]["id"],
                        item["target"]["id"],
                    )
                    for item in match_dependencies
                }
                for item in _indexed_imports(connection, match):
                    key = (
                        item["edge_kind"],
                        item["source"]["id"],
                        item["target"]["id"],
                    )
                    if key not in existing:
                        existing.add(key)
                        match_dependencies.append(item)
                incoming.extend(match_dependencies)
                complexity.append(
                    {
                        "qualified_name": match.qualified_name,
                        "span_lines": max(1, match.end_line - match.start_line + 1),
                        "incoming_dependencies": len(match_dependencies),
                    }
                )

            callers = [item for item in incoming if item["edge_kind"] == "calls"]
            importers = [item for item in incoming if item["edge_kind"] == "imports"]
            references = [
                item
                for item in incoming
                if item["edge_kind"] not in {"calls", "imports"}
            ]
            external = [
                item
                for item in incoming
                if item["source"]["file_path"] != item["target"]["file_path"]
            ]
            internal = [item for item in incoming if item not in external]
            production = [
                item
                for item in external
                if not _is_test_path(item["source"]["file_path"])
            ]
            test_files = sorted(
                {
                    item["source"]["file_path"]
                    for item in incoming
                    if _is_test_path(item["source"]["file_path"])
                }
            )
            evidence = {
                "matches": [_node_to_dict(match) for match in matches],
                "callers": callers,
                "importers": importers,
                "references": references,
                "production_dependents": production,
                "external_dependents": external,
                "internal_dependents": internal,
                "test_coverage": {
                    "present": bool(test_files),
                    "files": test_files,
                },
                "complexity": complexity,
                "cross_repo_visibility": "unavailable",
                "index": index,
            }
            if production:
                tier = "runtime_dependency"
            elif external:
                tier = "external_contract"
            elif internal:
                tier = "internal_dependency"
            else:
                tier = "no_known_callers"
            return _result(operation, symbol, tier, evidence)
    except sqlite3.Error:
        return _result(
            operation,
            symbol,
            "insufficient_data",
            _empty_evidence(_index_evidence(present=True)),
        )
