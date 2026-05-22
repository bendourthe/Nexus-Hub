"""SQLite schema bootstrap + connection helper for the v2.0 AST graph."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = "2.0.0"
DB_FILENAME = "codegraph.db"

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def schema_sql() -> str:
    """Return the DDL string applied by `apply_schema`."""
    return _SCHEMA_PATH.read_text(encoding="utf-8")


def apply_schema(conn: sqlite3.Connection) -> None:
    """Apply the v2.0 schema to `conn` and record the schema version.

    Idempotent: every DDL statement uses `IF NOT EXISTS`. Safe to call against
    an existing v2.0 database.
    """
    conn.executescript(schema_sql())
    conn.execute(
        "INSERT INTO schema_meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (SCHEMA_VERSION,),
    )
    conn.commit()


def open_database(index_dir: Path) -> sqlite3.Connection:
    """Open (and bootstrap, if needed) the graph database under `index_dir`.

    Caller owns the connection. Foreign keys are enabled on every connection.
    """
    index_dir.mkdir(parents=True, exist_ok=True)
    db_path = index_dir / DB_FILENAME
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON")
    apply_schema(conn)
    return conn
