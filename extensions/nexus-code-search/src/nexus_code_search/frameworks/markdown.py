"""Local Markdown-heading context provider."""

from __future__ import annotations

import re
from pathlib import Path

from nexus_code_search.frameworks.base import ContextProvider
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")


def _slug(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return normalized or "heading"


class MarkdownContextProvider(ContextProvider):
    """Contribute Markdown headings and hierarchy to the native graph."""

    name = "markdown"
    file_patterns = ("*.md",)

    def resolve(
        self,
        file_path: Path,
        source: bytes,
        ast_nodes: list[Node],
    ) -> tuple[list[Node], list[Edge]]:
        text = source.decode("utf-8", errors="replace")
        nodes: list[Node] = []
        edges: list[Edge] = []
        ancestors: list[tuple[int, int]] = []
        offset = len(ast_nodes)

        for line_number, line in enumerate(text.splitlines(), start=1):
            match = _HEADING_RE.match(line)
            if match is None:
                continue
            level = len(match.group(1))
            title = match.group(2).strip()
            local_id = offset + len(nodes)
            nodes.append(
                Node(
                    name=title,
                    kind=NodeKind.MODULE,
                    qualified_name=f"markdown:{file_path.as_posix()}#{_slug(title)}",
                    file_path=file_path.as_posix(),
                    start_line=line_number,
                    end_line=line_number,
                    signature=line.strip(),
                )
            )
            while ancestors and ancestors[-1][0] >= level:
                ancestors.pop()
            if ancestors:
                edges.append(
                    Edge(
                        source_id=ancestors[-1][1],
                        target_id=local_id,
                        kind=EdgeKind.CONTAINS,
                        call_site_line=line_number,
                    )
                )
            ancestors.append((level, local_id))
        return nodes, edges
