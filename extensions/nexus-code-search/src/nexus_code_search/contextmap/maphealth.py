"""Map-health lint.

A small, fast, deterministic checker over the `.nexus/context/` article set:

- **orphan articles**: an article file not linked from `index.md`.
- **missing backlinks**: an article that does not link back to the context map.
- **staleness**: the map's embedded source fingerprint no longer matches the
  current one (the source files changed since the map was generated).

Richer semantic checks (prose quality, cross-doc consistency) deliberately stay
in the LLM-native `documentation-consistency` skill; this is only the mechanical,
CI-runnable half. It ships no new catalog skill.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from nexus_code_search.contextmap.generator import (
    CONTEXT_DIRNAME,
    INDEX_FILENAME,
    MAP_FILENAME,
    _read_source_hash,
    current_source_hash,
)

_LINK_RE = re.compile(r"\]\(([^)]+)\)")
_MAP_BACKLINK = "../CONTEXT-MAP.md"


@dataclass
class HealthReport:
    """Outcome of a map-health lint run."""

    map_present: bool = True
    orphans: list[str] = field(default_factory=list)
    missing_backlinks: list[str] = field(default_factory=list)
    stale: bool = False

    @property
    def healthy(self) -> bool:
        return (
            self.map_present
            and not self.orphans
            and not self.missing_backlinks
            and not self.stale
        )

    def to_dict(self) -> dict:
        return {
            "map_present": self.map_present,
            "healthy": self.healthy,
            "orphans": self.orphans,
            "missing_backlinks": self.missing_backlinks,
            "stale": self.stale,
        }


def lint_context_map(root: Path, index_dir: Path) -> HealthReport:
    """Lint the compiled context map under ``<root>/.nexus/``."""
    root = Path(root)
    nexus_dir = root / ".nexus"
    map_path = nexus_dir / MAP_FILENAME
    context_dir = nexus_dir / CONTEXT_DIRNAME
    if not map_path.exists():
        return HealthReport(map_present=False)

    articles = sorted(p for p in context_dir.glob("*.md") if p.name != INDEX_FILENAME)

    linked = _linked_filenames(context_dir / INDEX_FILENAME)
    orphans = [a.name for a in articles if a.name not in linked]

    missing_backlinks = [a.name for a in articles if _MAP_BACKLINK not in _read(a)]

    embedded = _read_source_hash(map_path)
    stale = embedded is not None and embedded != current_source_hash(root, index_dir)

    return HealthReport(
        map_present=True,
        orphans=orphans,
        missing_backlinks=missing_backlinks,
        stale=stale,
    )


def _linked_filenames(index_path: Path) -> set[str]:
    """Return the set of article filenames linked from the index."""
    if not index_path.exists():
        return set()
    names: set[str] = set()
    for match in _LINK_RE.finditer(_read(index_path)):
        target = match.group(1).split("#", 1)[0].strip()
        if target:
            names.add(Path(target).name)
    return names


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
