"""The package must import no network module on any path."""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN = {
    "httpx",
    "requests",
    "urllib",
    "urllib.request",
    "urllib3",
    "aiohttp",
    "http.client",
    "socket",
}

SRC = Path(__file__).resolve().parents[1] / "src" / "nexus_memory"


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
            names.add(node.module)
    return names


def test_source_imports_no_network_module() -> None:
    hits: list[str] = []
    for path in SRC.glob("*.py"):
        imported = _imported_modules(path)
        bad = imported & FORBIDDEN
        if bad:
            hits.append(f"{path.name}: {sorted(bad)}")
    assert hits == [], "network modules imported: " + "; ".join(hits)
