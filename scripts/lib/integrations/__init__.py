"""Nexus-Hub Integration Registry.

Each supported AI coding platform is represented by a subclass of IntegrationBase
(or one of its specializations: MarkdownIntegration, TomlIntegration,
YamlIntegration, SkillsIntegration). The registry maps a string `key` to an
IntegrationBase instance and is consumed by `runner.py` to dispatch install /
teardown operations.

Design rationale: see docs/archive/v2/v2.1/adr/adr-001-integration-registry.md.
"""

from __future__ import annotations

from typing import Dict

from .base import IntegrationBase
from .result import FileAction, VALID_ACTIONS, WriteResult

INTEGRATION_REGISTRY: Dict[str, IntegrationBase] = {}


def _register(integration: IntegrationBase) -> None:
    """Register a single integration. Raises if the key is already taken."""
    if integration.key in INTEGRATION_REGISTRY:
        raise ValueError(f"Integration key already registered: {integration.key!r}")
    INTEGRATION_REGISTRY[integration.key] = integration


def _register_builtins() -> None:
    """Import and register every built-in integration in alphabetical order."""
    from .aider import AiderIntegration
    from .antigravity import Antigravity10Integration, Antigravity20Integration
    from .claude import ClaudeIntegration
    from .codex import CodexIntegration
    from .copilot import CopilotIntegration
    from .cursor import CursorIntegration
    from .gemini import GeminiIntegration
    from .gemini_cli import GeminiCliIntegration
    from .hermes import HermesIntegration
    from .kimi import KimiIntegration
    from .nexus_ai import NexusAiIntegration
    from .openclaw import OpenClawIntegration
    from .opencode import OpenCodeIntegration
    from .qwen import QwenIntegration
    from .windsurf import WindsurfIntegration

    _register(AiderIntegration())
    _register(Antigravity10Integration())
    _register(Antigravity20Integration())
    _register(ClaudeIntegration())
    _register(CodexIntegration())
    _register(CopilotIntegration())
    _register(CursorIntegration())
    _register(GeminiIntegration())
    _register(GeminiCliIntegration())
    _register(HermesIntegration())
    _register(KimiIntegration())
    _register(NexusAiIntegration())
    _register(OpenClawIntegration())
    _register(OpenCodeIntegration())
    _register(QwenIntegration())
    _register(WindsurfIntegration())


_register_builtins()


def get(key: str) -> IntegrationBase:
    """Look up an integration by key. Raises KeyError if unknown."""
    if key not in INTEGRATION_REGISTRY:
        known = ", ".join(sorted(INTEGRATION_REGISTRY))
        raise KeyError(f"Unknown integration {key!r}. Known: {known}")
    return INTEGRATION_REGISTRY[key]


def list_keys() -> list[str]:
    """Return the registered integration keys in alphabetical order."""
    return sorted(INTEGRATION_REGISTRY)


__all__ = [
    "INTEGRATION_REGISTRY",
    "FileAction",
    "IntegrationBase",
    "VALID_ACTIONS",
    "WriteResult",
    "get",
    "list_keys",
]
