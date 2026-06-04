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
from .dependencies import DependencyVulnerabilityAnalyzer, OSVClient
from .mcp import MCPConfigAnalyzer
from .signatures import SignatureAnalyzer
from .subsumed import SecretsAnalyzer, SupplyChainAnalyzer, WorkflowSecurityAnalyzer
from .text_patterns import TextPatternAnalyzer


def build_analyzers(
    repo_root: Path | None,
    *,
    enable_signatures: bool = False,
    enable_osv: bool = False,
    osv_online: bool = False,
    osv_client: OSVClient | None = None,
) -> list[Analyzer]:
    """Instantiate the analyzers for a scan rooted at ``repo_root``.

    The six core analyzers (the deterministic Phase 6 engine) always run. The
    two Phase 7 modules are appended only when explicitly enabled, so a default
    scan is byte-identical to Phase 6 and makes no network call.
    """
    analyzers: list[Analyzer] = [
        TextPatternAnalyzer(),
        BehavioralASTAnalyzer(),
        MCPConfigAnalyzer(),
        SecretsAnalyzer(repo_root),
        SupplyChainAnalyzer(repo_root),
        WorkflowSecurityAnalyzer(repo_root),
    ]
    if enable_signatures:
        analyzers.append(SignatureAnalyzer())
    if enable_osv:
        analyzers.append(DependencyVulnerabilityAnalyzer(client=osv_client, online=osv_online))
    return analyzers


__all__ = [
    "build_analyzers",
    "Analyzer",
    "TextPatternAnalyzer",
    "BehavioralASTAnalyzer",
    "MCPConfigAnalyzer",
    "SecretsAnalyzer",
    "SupplyChainAnalyzer",
    "WorkflowSecurityAnalyzer",
    "SignatureAnalyzer",
    "DependencyVulnerabilityAnalyzer",
    "OSVClient",
]
