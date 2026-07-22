"""ORM schema extraction.

Surfaces data models (tables) with their fields, primary/foreign keys, unique
constraints, and relations across a prioritized ORM set:

- SQLAlchemy (Python): `Column` / `mapped_column` fields + `relationship()`.
- Django ORM (Python): `models.XField` fields + ForeignKey / OneToOne / M2M.
- Prisma (`.prisma` DSL): `model` blocks with `@id` / `@unique` / relations.

Class-based ORMs are located from the `class` nodes already in the graph and
parsed from their source span; Prisma is parsed from the `.prisma` files. Other
ORMs (TypeORM, Drizzle, ActiveRecord, GORM) are deferred - each needs its own
detector and fixture. Detection keys on ORM-specific tokens, so a plain class is
not mistaken for a model.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from nexus_code_search.contextmap.model import FieldInfo, ModelInfo, RelationInfo

# Nested config classes that are not models.
_SKIP_CLASS_NAMES = frozenset({"Meta", "Config"})

_DJANGO_RELATION_KINDS = {
    "ForeignKey": "many-to-one",
    "OneToOneField": "one-to-one",
    "ManyToManyField": "many-to-many",
}

_PRISMA_SCALARS = frozenset(
    {
        "String",
        "Boolean",
        "Int",
        "BigInt",
        "Float",
        "Decimal",
        "DateTime",
        "Json",
        "Bytes",
    }
)

_DJANGO_FIELD = re.compile(r"^(\w+)\s*=\s*models\.(\w+)\((.*)\)\s*$", re.DOTALL)
_SA_RELATIONSHIP = re.compile(
    r"^(\w+)\s*(?::\s*[^=]+)?=\s*relationship\((.*)\)\s*$", re.DOTALL
)
_SA_COLUMN = re.compile(
    r"^(\w+)\s*(?::\s*[^=]+)?=\s*(?:Column|mapped_column)\((.*)\)\s*$", re.DOTALL
)
_PRISMA_MODEL = re.compile(r"model\s+(\w+)\s*\{([^}]*)\}", re.DOTALL)
_PRISMA_FIELD = re.compile(r"^(\w+)\s+(\S+)(.*)$")


def extract_schema(conn: sqlite3.Connection, root: Path) -> list[ModelInfo]:
    """Return every ORM model detected in the graph's classes and .prisma files."""
    models: list[ModelInfo] = []
    models.extend(_extract_class_models(conn, root))
    models.extend(_extract_prisma_models(root))
    models.sort(key=lambda m: (m.source_file, m.name))
    return models


# --- Class-based ORMs (SQLAlchemy, Django) ----------------------------------


def _extract_class_models(conn: sqlite3.Connection, root: Path) -> list[ModelInfo]:
    cur = conn.cursor()
    files_by_id = {fid: path for fid, path in cur.execute("SELECT id, path FROM files")}
    class_rows = cur.execute(
        "SELECT name, file_id, start_line, end_line FROM nodes WHERE kind = 'class'"
    ).fetchall()

    cache: dict[str, list[str]] = {}
    models: list[ModelInfo] = []
    for name, file_id, start_line, end_line in class_rows:
        if name in _SKIP_CLASS_NAMES:
            continue
        rel_path = files_by_id.get(file_id, "")
        source = _slice(root, rel_path, start_line, end_line, cache)
        if not source:
            continue
        first_line = source.splitlines()[0] if source else ""
        framework = _detect_class_orm(first_line, source)
        if framework is None:
            continue
        fields, relations = (
            _parse_django(source)
            if framework == "django"
            else _parse_sqlalchemy(source)
        )
        models.append(
            ModelInfo(
                name=name,
                framework=framework,
                source_file=rel_path,
                fields=tuple(fields),
                relations=tuple(relations),
            )
        )
    return models


def _detect_class_orm(first_line: str, body: str) -> str | None:
    if "models.Model" in first_line or re.search(r"=\s*models\.\w+\(", body):
        return "django"
    if re.search(r"=\s*(?:Column|mapped_column)\(", body) or "relationship(" in body:
        return "sqlalchemy"
    return None


def _parse_django(source: str) -> tuple[list[FieldInfo], list[RelationInfo]]:
    fields: list[FieldInfo] = []
    relations: list[RelationInfo] = []
    for stmt in _statements(source):
        match = _DJANGO_FIELD.match(stmt)
        if not match:
            continue
        name, ftype, args = match.group(1), match.group(2), match.group(3)
        if ftype in _DJANGO_RELATION_KINDS:
            relations.append(
                RelationInfo(
                    name=name,
                    target=_first_arg(args),
                    kind=_DJANGO_RELATION_KINDS[ftype],
                )
            )
        else:
            fields.append(
                FieldInfo(
                    name=name,
                    type=ftype,
                    primary_key="primary_key=True" in args,
                    unique="unique=True" in args,
                )
            )
    return fields, relations


def _parse_sqlalchemy(source: str) -> tuple[list[FieldInfo], list[RelationInfo]]:
    fields: list[FieldInfo] = []
    relations: list[RelationInfo] = []
    for stmt in _statements(source):
        rel = _SA_RELATIONSHIP.match(stmt)
        if rel:
            relations.append(
                RelationInfo(
                    name=rel.group(1), target=_first_arg(rel.group(2)), kind="relation"
                )
            )
            continue
        col = _SA_COLUMN.match(stmt)
        if col:
            name, args = col.group(1), col.group(2)
            fields.append(
                FieldInfo(
                    name=name,
                    type=_first_arg(args) or "Column",
                    primary_key="primary_key=True" in args,
                    foreign_key="ForeignKey(" in args,
                    unique="unique=True" in args,
                )
            )
    return fields, relations


# --- Prisma DSL -------------------------------------------------------------


def _extract_prisma_models(root: Path) -> list[ModelInfo]:
    models: list[ModelInfo] = []
    for schema_file in _find_prisma_files(root):
        rel = _relative(root, schema_file)
        text = _read(schema_file)
        for block in _PRISMA_MODEL.finditer(text):
            model_name, body = block.group(1), block.group(2)
            fields, relations = _parse_prisma_block(body)
            models.append(
                ModelInfo(
                    name=model_name,
                    framework="prisma",
                    source_file=rel,
                    fields=tuple(fields),
                    relations=tuple(relations),
                )
            )
    return models


def _parse_prisma_block(body: str) -> tuple[list[FieldInfo], list[RelationInfo]]:
    fields: list[FieldInfo] = []
    relations: list[RelationInfo] = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith("//") or line.startswith("@@"):
            continue
        match = _PRISMA_FIELD.match(line)
        if not match:
            continue
        name, type_raw, rest = match.group(1), match.group(2), match.group(3)
        base_type = type_raw.replace("[]", "").replace("?", "")
        is_list = "[]" in type_raw
        if base_type in _PRISMA_SCALARS:
            fields.append(
                FieldInfo(
                    name=name,
                    type=base_type,
                    primary_key="@id" in rest,
                    unique="@unique" in rest,
                )
            )
        elif base_type and (base_type[0].isupper() or "@relation" in rest):
            relations.append(
                RelationInfo(
                    name=name,
                    target=base_type,
                    kind="one-to-many" if is_list else "many-to-one",
                )
            )
    return fields, relations


def _find_prisma_files(root: Path) -> list[Path]:
    found = [
        p
        for p in root.rglob("*.prisma")
        if not any(part in {"node_modules", ".git", ".nexus"} for part in p.parts)
    ]
    return sorted(found)


def prisma_fingerprint_files(root: Path) -> list[Path]:
    """Public: the .prisma files that feed schema extraction (for the map's
    source fingerprint, so a change to one invalidates the compiled map)."""
    return _find_prisma_files(root)


# --- Shared helpers ---------------------------------------------------------


def _statements(source: str) -> list[str]:
    """Split a class body into logical statements, joining lines until parens
    balance so a multi-line field definition is one statement."""
    statements: list[str] = []
    buffer = ""
    depth = 0
    for line in source.splitlines():
        stripped = line.strip()
        if not buffer and not stripped:
            continue
        buffer = f"{buffer} {stripped}".strip() if buffer else stripped
        depth += line.count("(") - line.count(")")
        if depth <= 0:
            statements.append(buffer)
            buffer = ""
            depth = 0
    if buffer:
        statements.append(buffer)
    return statements


def _first_arg(args: str) -> str:
    """Return the first positional argument, de-quoted (best-effort)."""
    first = args.split(",", 1)[0].strip()
    if len(first) >= 2 and first[0] == first[-1] and first[0] in ("'", '"'):
        first = first[1:-1]
    # Django cross-app refs like 'app.Model' -> keep the model name.
    if "." in first and " " not in first:
        first = first.split(".")[-1]
    return first


def _slice(
    root: Path, rel_path: str, start_line: int, end_line: int, cache: dict
) -> str:
    if not rel_path:
        return ""
    lines = cache.get(rel_path)
    if lines is None:
        lines = _read(root / rel_path).splitlines()
        cache[rel_path] = lines
    start = max(start_line, 1)
    return "\n".join(lines[start - 1 : end_line])


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name
