"""Nexus-Hub local-only static skill-security scanner.

The deterministic first stage of a two-stage skill-security scan. This engine
runs regex, Python-AST, taint-tracking, and MCP-declaration checks over a
skill's ``SKILL.md``, its bundled scripts, and any MCP config it ships, and
emits machine findings across 16 vulnerability classes with a severity-banded
risk score in terminal / JSON / Markdown / SARIF form.

The engine is deterministic and self-contained: stdlib only, zero outbound
calls by default, no LLM provider client, and no API key. The intent
adjudication of borderline findings is the ``skill-security-scan`` skill, run
by the user's own agent.

Public API:
    scan_target(target, ...)   -> ScanResult
    Scanner                    -> the configurable scanner object
    Finding, ScanResult, Severity, Band -> result types
    apply_allowlist, is_trusted_security_skill_body -> producer-catalog policy
"""

from __future__ import annotations

from .allowlist import apply_allowlist, is_trusted_security_skill_body
from .scanner import Scanner, scan_target
from .types import Band, Finding, ScanResult, Severity

__all__ = [
    "Scanner",
    "scan_target",
    "Finding",
    "ScanResult",
    "Severity",
    "Band",
    "apply_allowlist",
    "is_trusted_security_skill_body",
]

__version__ = "3.0.0"
