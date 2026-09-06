"""Configuration resolution for nexus-code-search.

Mirrors the pattern used by nexus-skill-server: explicit NEXUS_HUB_ROOT
env var -> parent-walk from module location -> user global fallback.
All local-only. No network calls.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("nexus-code-search")


DEFAULT_INDEX_DIR_NAME = ".nexus/code-index"
MAX_FILE_BYTES = 1_000_000  # 1 MB
CHUNK_TARGET_SIZE = 600
CHUNK_OVERLAP = 80
DEFAULT_TOOL_PROFILE = "full"
TOOL_PROFILE_ENV = "NEXUS_CODE_SEARCH_TOOL_PROFILE"
DENSE_ENABLE_ENV = "NEXUS_CODE_SEARCH_DENSE"
DENSE_MODEL_DIR_ENV = "NEXUS_CODE_SEARCH_MODEL_DIR"
VALID_TOOL_PROFILES = frozenset({"minimal", "standard", "full"})

DEFAULT_EXCLUDE_DIRS = frozenset(
    {
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".env",
        "dist",
        "build",
        "__pycache__",
        ".git",
        ".nexus",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)

DEFAULT_EXCLUDE_PATTERNS = frozenset(
    {
        "*.lock",
        "*.min.js",
        "*.min.css",
        "*.map",
        "*.pyc",
        "*.pyo",
    }
)


@dataclass(frozen=True)
class CodeSearchConfig:
    """Resolved configuration for a code-search session."""

    hub_root: Path | None
    index_dir_name: str = DEFAULT_INDEX_DIR_NAME
    max_file_bytes: int = MAX_FILE_BYTES
    chunk_target_size: int = CHUNK_TARGET_SIZE
    chunk_overlap: int = CHUNK_OVERLAP
    tool_profile: str = DEFAULT_TOOL_PROFILE
    dense_enabled: bool = False
    dense_model_dir: str | None = None
    exclude_dirs: frozenset[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_DIRS)
    exclude_patterns: frozenset[str] = field(default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS)


def _find_hub_root() -> Path | None:
    """Three-tier resolution for the Nexus-Hub root directory.

    Matches nexus-skill-server's pattern: explicit env -> module-parent-walk -> home fallback.
    Returns None if no hub root can be identified; the server still works for arbitrary
    repos since hub_root is only used as a convenience.
    """
    env_root = os.environ.get("NEXUS_HUB_ROOT")
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if candidate.exists():
            logger.info("Hub root from NEXUS_HUB_ROOT: %s", candidate)
            return candidate
        logger.warning("NEXUS_HUB_ROOT set to %s but path does not exist", candidate)

    module_dir = Path(__file__).resolve().parent
    for _ in range(5):
        module_dir = module_dir.parent
        if (module_dir / "AGENTS.md").exists() and (module_dir / "data").exists():
            logger.info("Hub root auto-detected: %s", module_dir)
            return module_dir

    global_path = Path.home() / ".nexus-hub"
    if global_path.exists():
        logger.info("Hub root from global install: %s", global_path)
        return global_path

    return None


def resolve_config() -> CodeSearchConfig:
    """Resolve server configuration from environment and filesystem."""
    profile = os.environ.get(TOOL_PROFILE_ENV, DEFAULT_TOOL_PROFILE).strip().lower()
    if profile not in VALID_TOOL_PROFILES:
        logger.warning(
            "%s=%r is invalid; falling back to %r",
            TOOL_PROFILE_ENV,
            profile,
            DEFAULT_TOOL_PROFILE,
        )
        profile = DEFAULT_TOOL_PROFILE
    dense_enabled = os.environ.get(DENSE_ENABLE_ENV, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    dense_model_dir = os.environ.get(DENSE_MODEL_DIR_ENV) or None
    return CodeSearchConfig(
        hub_root=_find_hub_root(),
        tool_profile=profile,
        dense_enabled=dense_enabled,
        dense_model_dir=dense_model_dir,
    )


def index_dir_for(root: Path, config: CodeSearchConfig) -> Path:
    """Return the on-disk index directory for a given codebase root."""
    return (root / config.index_dir_name).resolve()
