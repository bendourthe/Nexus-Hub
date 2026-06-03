"""Analyzer registry.

``build_analyzers`` returns the ordered list of analyzer instances the scanner
runs over each file. The subsumed analyzers need the repo root (to load the
original validator scripts), so the registry is built per-scan rather than as a
module-level constant.
"""

from __future__ import annotations

from pathlib import Path

from .base import Analyzer
from .behavioral_ast import BehavioralASTAnalyzer
from .mcp import MCPConfigAnalyzer
from .subsumed import SecretsAnalyzer, SupplyChainAnalyzer, WorkflowSecurityAnalyzer
from .text_patterns import TextPatternAnalyzer


def build_analyzers(repo_root: Path | None) -> list[Analyzer]:
    """Instantiate every analyzer for a scan rooted at ``repo_root``."""
    return [
        TextPatternAnalyzer(),
        BehavioralASTAnalyzer(),
        MCPConfigAnalyzer(),
        SecretsAnalyzer(repo_root),
        SupplyChainAnalyzer(repo_root),
        WorkflowSecurityAnalyzer(repo_root),
    ]


__all__ = [
    "build_analyzers",
    "Analyzer",
    "TextPatternAnalyzer",
    "BehavioralASTAnalyzer",
    "MCPConfigAnalyzer",
    "SecretsAnalyzer",
    "SupplyChainAnalyzer",
    "WorkflowSecurityAnalyzer",
]
