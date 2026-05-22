"""Schema bootstrap + NodeKind / EdgeKind enum tests (T024)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.db import (
    SCHEMA_VERSION,
    apply_schema,
    open_database,
    schema_sql,
)
from nexus_code_search.db.migrate import detect_v1_index, migrate_v1_to_v2
from nexus_code_search.types import EdgeKind, NodeKind


def test_nodekind_has_22_values() -> None:
    expected = {
        "file",
        "module",
        "class",
        "struct",
        "interface",
        "trait",
        "protocol",
        "function",
        "method",
        "property",
        "field",
        "variable",
        "constant",
        "enum",
        "enum_member",
        "type_alias",
        "namespace",
        "parameter",
        "import",
        "export",
        "route",
        "component",
    }
    assert {k.value for k in NodeKind} == expected
    assert len(list(NodeKind)) == 22


def test_edgekind_has_12_values() -> None:
    expected = {
        "contains",
        "calls",
        "imports",
        "exports",
        "extends",
        "implements",
        "references",
        "type_of",
        "returns",
        "instantiates",
        "overrides",
        "decorates",
    }
    assert {k.value for k in EdgeKind} == expected
    assert len(list(EdgeKind)) == 12


def test_schema_sql_contains_core_tables() -> None:
    sql = schema_sql()
    for table in ("files", "nodes", "edges", "nodes_fts", "schema_meta"):
        assert table in sql, f"schema missing {table}"


def test_open_database_creates_all_tables(tmp_path: Path) -> None:
    conn = open_database(tmp_path)
    try:
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
            )
        }
        for expected in ("files", "nodes", "edges", "nodes_fts", "schema_meta"):
            assert expected in names
        row = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        assert row[0] == SCHEMA_VERSION
    finally:
        conn.close()


def test_open_database_is_idempotent(tmp_path: Path) -> None:
    open_database(tmp_path).close()
    conn = open_database(tmp_path)
    try:
        apply_schema(conn)  # second apply must not error
        row = conn.execute(
            "SELECT value FROM schema_meta WHERE key = 'schema_version'"
        ).fetchone()
        assert row[0] == SCHEMA_VERSION
    finally:
        conn.close()


def test_fts5_triggers_keep_nodes_fts_in_sync(tmp_path: Path) -> None:
    conn = open_database(tmp_path)
    try:
        conn.execute(
            "INSERT INTO files(path, language, content_hash, indexed_at) VALUES(?,?,?,?)",
            ("a.py", "python", "deadbeef", 0),
        )
        conn.execute(
            "INSERT INTO nodes(name, kind, qualified_name, file_id, start_line, end_line, signature, docstring) "
            "VALUES(?,?,?,?,?,?,?,?)",
            ("greet", "function", "a.greet", 1, 1, 3, "def greet()", "Say hello"),
        )
        conn.commit()
        rows = conn.execute(
            "SELECT name FROM nodes_fts WHERE nodes_fts MATCH 'greet'"
        ).fetchall()
        assert rows == [("greet",)]
        # Update docstring; FTS should follow.
        conn.execute("UPDATE nodes SET docstring = 'Say bonjour' WHERE name = 'greet'")
        conn.commit()
        rows = conn.execute(
            "SELECT name FROM nodes_fts WHERE nodes_fts MATCH 'bonjour'"
        ).fetchall()
        assert rows == [("greet",)]
        # Delete; FTS must clear.
        conn.execute("DELETE FROM nodes WHERE name = 'greet'")
        conn.commit()
        rows = conn.execute(
            "SELECT name FROM nodes_fts WHERE nodes_fts MATCH 'greet'"
        ).fetchall()
        assert rows == []
    finally:
        conn.close()


def test_migrate_v1_to_v2_renames_v1_index(tmp_path: Path) -> None:
    idx = tmp_path / "code-index"
    idx.mkdir()
    (idx / "chunks.json").write_text("[]", encoding="utf-8")
    (idx / "manifest.json").write_text("{}", encoding="utf-8")

    assert detect_v1_index(idx) is True
    result = migrate_v1_to_v2(idx)
    assert result.migrated is True
    assert result.backup_dir is not None
    assert result.backup_dir.exists()
    assert (result.backup_dir / "chunks.json").exists()
    assert not idx.exists()
    # Re-running on a now-absent v1 dir reports no-op.
    second = migrate_v1_to_v2(idx)
    assert second.migrated is False


def test_migrate_no_op_when_no_v1_index(tmp_path: Path) -> None:
    result = migrate_v1_to_v2(tmp_path / "missing")
    assert result.migrated is False
    assert result.backup_dir is None
