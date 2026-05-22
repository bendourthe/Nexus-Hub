"""SQLite persistence layer for the nexus-code-search v2.0 AST graph.

The legacy JSON chunk index continues to live alongside this database: a v2.0
install can use both surfaces. The graph database lives at
`<repo>/.nexus/code-index/codegraph.db` (FTS5 virtual table + nodes / edges /
files schema).
"""

from __future__ import annotations

from nexus_code_search.db.schema import (
    SCHEMA_VERSION,
    apply_schema,
    open_database,
    schema_sql,
)
from nexus_code_search.db.migrate import migrate_v1_to_v2

__all__ = [
    "SCHEMA_VERSION",
    "apply_schema",
    "migrate_v1_to_v2",
    "open_database",
    "schema_sql",
]
